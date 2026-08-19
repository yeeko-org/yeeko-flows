"""Harness de simulación del flujo CACEH sobre el motor (WP7).

Mete payloads de webhook de WhatsApp por `ManagerFlow` sin tocar red y deja leer
la respuesta del bot y los extras resultantes. Lo comparten el test e2e
(`tests/test_flow_e2e.py`) y el stepper de CLI
(`management/commands/step_flow.py`).

Mecánica clave (el motor no guarda sesión): la "pieza actual" se reconstruye desde
la última interacción de SALIDA persistida (`context_mixin.calculate_context_piece`).
Por eso se corre el ciclo completo `ManagerFlow.__call__()` con un `send_message`
que no toca red pero SÍ persiste la interacción de salida con un `mid`
(`WhatsAppResponseNoSend`). Encadenar turnos = mandar el siguiente payload con el
mismo `wa_id`.

Los botones se contestan mandando el TÍTULO como texto: el motor lo matchea contra
los `Reply` de la pieza (`text.py::check_buttons_text`,
`standar(title) == standar(text)`), así no hace falta el id generado del botón.
"""
import base64
import json
import secrets
import time
from contextlib import ExitStack, contextmanager
from typing import Optional
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone

from infrastructure.persistent_media.models import Media
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import Interaction
from interface.whatsapp.request import WhatsAppRequest
from interface.whatsapp.response import WhatsAppResponse
from services.manager_flow import ManagerFlow

PID_DEMO = "103571329211620"  # pid del Account del fixture/demo


# --- payloads de webhook -------------------------------------------------

def _wamid() -> str:
    raw = secrets.token_bytes(24)
    return "wamid." + base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _envelope(pid: str, wa_id: str, message: dict) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "112795704944207",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": pid,
                                 "display_phone_number": "15550578839"},
                    "contacts": [{"wa_id": wa_id,
                                  "profile": {"name": "Prueba WP7"}}],
                    "messages": [message],
                },
            }],
        }],
    }


def text_payload(wa_id: str, body: str, pid: str = PID_DEMO,
                 context_id: Optional[str] = None) -> dict:
    msg = {
        "id": _wamid(),
        "from": wa_id,
        "timestamp": str(int(time.time())),
        "type": "text",
        "text": {"body": body},
    }
    if context_id:
        msg["context"] = {"id": context_id}
    return _envelope(pid, wa_id, msg)


# --- respuesta/petición sin red (persisten, no envían) -------------------

class WhatsAppResponseNoSend(WhatsAppResponse):
    """No pega a graph.facebook.com; devuelve un ApiRecord de salida con un
    `mid` para que `save_interaction` persista la interacción (de ahí cuelga el
    resume entre turnos)."""

    def send_message(self, message_data: dict,
                     api_request: Optional[ApiRecord] = None) -> ApiRecord:
        return ApiRecord.objects.create(
            platform=self.sender.account.platform,
            body=message_data,
            interaction_type_id="default",
            is_incoming=False,
            response_status=200,
            response_body={"messaging_product": "whatsapp",
                           "messages": [{"id": _wamid()}]},
        )


class WhatsAppRequestNoSend(WhatsAppRequest):
    def _set_status_read(self, message_id, pid, token) -> None:
        pass


# --- parches offline (PDF/Media a WhatsApp, Gemini) ----------------------

# Storage en memoria para el FileField del Media: el default del proyecto es
# S3 (storages.backends.s3boto3), y `Media.save()` escribiría a AWS.
_INMEMORY_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@contextmanager
def media_offline():
    """Saca la red del PDF: (1) el archivo se guarda en memoria, no en S3;
    (2) `upload_media_file` (subida a WhatsApp, requests.post desde
    `Media.save()`/`get_media_id()`) solo finge el id."""
    def _fake_upload(self, save=True):
        self.media_id = "FAKEMEDIAID-WP7"
        self.uploaded_media_id_at = timezone.now()

    with override_settings(STORAGES=_INMEMORY_STORAGES), \
            patch.object(Media, "upload_media_file", _fake_upload):
        yield


# Datos canónicos por esquema para el fake de Gemini (fallback offline del
# stepper; el e2e usa Gemini real). Campo Pydantic = clave del extra.
_FAKE_EXTRACT = {
    "Jornada": {
        "hora_entrada": "08:00", "hora_salida": "16:00",
        "dias_laborables": ["lunes", "martes", "miércoles", "jueves",
                            "viernes"],
        "ia_completed": "si", "ia_pregunta": None},
    "Pago": {
        "monto_pago": 2500, "pago_periodicidad": "semanal",
        "ia_completed": "si", "ia_pregunta": None},
    "Domicilio": {
        "lt_calle": "Av. Reforma", "lt_ext": "100", "lt_int": None,
        "lt_colonia": "Juárez", "lt_cp": "06600",
        "lt_municipio": "Cuauhtémoc", "lt_estado": "Ciudad de México",
        "ciudad_firma": "Cuauhtémoc", "ia_completed": "si",
        "ia_pregunta": None},
}


@contextmanager
def gemini_fake():
    """Reemplaza `GeminiClient` por un doble que despacha datos canónicos según
    la clase de esquema recibida en `extract(system_prompt, user_text, schema)`.
    Solo para el stepper sin `GEMINI_API_KEY`."""
    def _dispatch(system_prompt, user_text, schema):
        return dict(_FAKE_EXTRACT.get(schema.__name__, {}))

    with patch("services.behavior.ia_extrae.GeminiClient") as mock_g:
        mock_g.return_value.extract.side_effect = _dispatch
        mock_g.return_value.errors = []
        yield


# --- driver --------------------------------------------------------------

class FlowDriver:
    """Conduce una conversación simulada para un `wa_id` contra el flujo
    sembrado. Cada `send`/`tap` es un turno completo (un webhook → la respuesta
    del bot, ya persistida)."""

    def __init__(self, wa_id: str, pid: str = PID_DEMO):
        self.wa_id = wa_id
        self.pid = pid
        self.member_account = None
        self.last_turn: list[dict] = []

    # WhatsApp real solo manda `context` cuando la persona cita el mensaje del
    # bot; `with_context=False` reproduce el caso normal (escribir sin citar).
    def send(self, body: str, with_context: bool = True) -> list[dict]:
        payload = text_payload(
            self.wa_id, body, self.pid,
            context_id=self._last_out_mid() if with_context else None)
        return self._run(payload)

    # Botón = título como texto (lo resuelve check_buttons_text).
    tap = send

    def submit_form(self, selection: list) -> list[dict]:
        """Simula el submit de un WhatsApp Flow (`nfm_reply`). Toma el
        `flow_token` del formulario que el bot acaba de enviar (lo que el Flow
        real devolvería) y manda el payload de finalización con las opciones
        elegidas; el motor lo enruta a `WaFormReplyProcessor`."""
        flow_token = self._last_flow_token()
        if not flow_token:
            raise AssertionError(
                "No hay flow_token en el último turno: ¿la pieza no envió "
                "un WhatsApp Flow?")
        msg = {
            "id": _wamid(),
            "from": self.wa_id,
            "timestamp": str(int(time.time())),
            "type": "interactive",
            "interactive": {
                "type": "nfm_reply",
                "nfm_reply": {
                    "name": "flow", "body": "Sent",
                    "response_json": json.dumps(
                        {"flow_token": flow_token, "selection": selection}),
                },
            },
        }
        return self._run(_envelope(self.pid, self.wa_id, msg))

    def _last_flow_token(self) -> Optional[str]:
        def _walk(node):
            if isinstance(node, dict):
                token = node.get("flow_token")
                if isinstance(token, str):
                    return token
                for value in node.values():
                    found = _walk(value)
                    if found:
                        return found
            elif isinstance(node, list):
                for value in node:
                    found = _walk(value)
                    if found:
                        return found
            return None

        for message in self.last_turn:
            token = _walk(message)
            if token:
                return token
        return None

    def _run(self, payload: dict) -> list[dict]:
        mf = ManagerFlow(payload, WhatsAppRequestNoSend, WhatsAppResponseNoSend)
        mf()
        if mf.response_list:
            self.member_account = mf.response_list[-1].sender
        self.last_turn = [m for r in mf.response_list for m in r.message_list]
        return self.last_turn

    # --- estado ----------------------------------------------------------
    def _last_out(self, with_fragment: bool = False):
        if not self.member_account:
            return None
        qs = Interaction.objects.filter(
            member_account=self.member_account, is_incoming=False)
        if with_fragment:
            qs = qs.filter(fragment__isnull=False)
        return qs.order_by("created").last()

    def _last_out_mid(self) -> Optional[str]:
        last = self._last_out()
        return last.mid if last else None

    def at_piece(self) -> Optional[str]:
        """Pieza en la que el motor dejó al usuario (misma derivación que
        `calculate_context_piece`): la última salida con fragmento."""
        last = self._last_out(with_fragment=True)
        return last.fragment.piece.name if last and last.fragment_id else None

    def extras(self) -> dict:
        if not self.member_account:
            return {}
        return self.member_account.member.get_extra_values_data(refrest=True)

    # --- lectura de la respuesta del bot ---------------------------------
    def bot_texts(self) -> list[str]:
        out = []
        for m in self.last_turn:
            sm = m.get("_standard_message") or {}
            body = sm.get("body")
            if body:
                out.append(body)
        return out

    def bot_buttons(self) -> list[str]:
        """Títulos de botón/fila ofrecidos en el último turno (best-effort:
        rastrea claves 'title' anidadas en los _standard_message)."""
        titles: list[str] = []

        def _walk(node):
            if isinstance(node, dict):
                if isinstance(node.get("title"), str):
                    titles.append(node["title"])
                for v in node.values():
                    _walk(v)
            elif isinstance(node, list):
                for v in node:
                    _walk(v)

        for m in self.last_turn:
            _walk(m.get("_standard_message") or {})
        return titles


@contextmanager
def offline(use_real_gemini: bool):
    """Contexto de ejecución offline del harness: siempre sin red de WhatsApp
    (media); Gemini real o fingido según `use_real_gemini`."""
    with ExitStack() as stack:
        stack.enter_context(media_offline())
        if not use_real_gemini:
            stack.enter_context(gemini_fake())
        yield
