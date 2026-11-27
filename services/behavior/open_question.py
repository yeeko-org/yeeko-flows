"""open_question — the capture unit: one piece asks for one datum in free
text, extracts it with Gemini, re-asks, validates, recaps it with a
«Corregir» button and lets it be corrected later, returning to whatever was
pending.

Every message it sends leaves through one of its piece's slot fragments, so
the role of the last outgoing message (question, reask, recap...) is read
back from the interaction history; nothing else is stored per message.

Modes, by how it is invoked:
- shown by its piece: sends `question` (or, with `action=correct`, the
  `correction_request` of a «Corregir» press);
- text addressed to one of its slots (`slot_fragment` given): an answer to
  the question, a re-ask or a correction request, or a quoted recap.
"""
import json
from typing import Any, Literal, Optional

from pydantic import ValidationError, create_model

from infrastructure.box.models import Fragment
from infrastructure.talk.models import Interaction
from infrastructure.tool.models import Parameter
from services.behavior.extraction import (
    CONTROL_FIELDS, DERIVATIONS, PREGUNTA_GENERICA, SCHEMA_REGISTRY,
    ExtrasMixin, validation_message)
from services.processor.behavior import FINISHED, HANDLED, NOT_MINE
from services.response.abstract import ResponseAbc
from services.response.models import ReplyMessage
from utilities.gemini_client import GeminiClient

NOTICE_TEXT = 'Si quieres corregir este dato, presiona el botón "Corregir".'
CORRECTION_FAILED_TEXT = (
    'No logré entender la corrección que necesitabas. El dato queda como '
    'estaba originalmente; si requieres la corrección, presiona "Corregir" '
    'nuevamente.')
FIRST_RECAP_HINT = 'Si quieres ajustar algo, presiona el botón "Corregir".'
# How the first-recap hint is joined to the recap body (same message).
RECAP_HINT_SEPARATOR = "\n\n"
# Extra that records that this conversation already showed the hint. The
# contract reset wipes extras, so the next contract shows it again.
FIRST_RECAP_MARKER = "_first_recap_sent"
# Value the «Corregir» destination passes in the `action` parameter.
ACTION_CORRECT = "correct"

ASKING_SLOTS = ("question", "reask", "correction_request")
# Messages that are about a datum already captured, never what is pending.
META_SLOTS = ("recap", "notice", "correction_request", "give_up",
              "correction_failed")
# How far back the pending message is looked for.
PENDING_LOOKBACK = 50

Intent = Literal["request", "confirm", "correct", "other"]

CORRECTION_INSTRUCTIONS = (
    "\nThis is a correction of data already captured. You receive the "
    "CURRENT VALUES as JSON and what the person wrote. Return only the "
    "fields the person asked to change and leave every other field null; "
    "never repeat a current value nor invent data. Set ia_completed='si' "
    "when there is at least one clear change; otherwise set it to 'no' and "
    "write in ia_pregunta one short question, in the person's language.\n")

QUOTE_INSTRUCTIONS = (
    "\nThe person replied to a RECAP of data already captured, whose "
    "CURRENT VALUES you receive as JSON. Classify the REPLY in `intent`:\n"
    "- 'request': they want to correct this data but did not give the new "
    "value.\n"
    "- 'confirm': they agree with it ('sí', 'ok', 'correcto').\n"
    "- 'correct': they give the new value of some part of it. Fill only the "
    "fields that change, leave the others null, set ia_completed='si'.\n"
    "- 'other': anything else.\n"
    "Unless the intent is 'correct', leave every data field null.\n")


def as_flag(value: Any, default: bool) -> bool:
    """A ParamValue arrives typed; the defaults (`Parameter.default_value`
    and the class's own) are still text."""
    if isinstance(value, bool):
        return value
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in ("true", "1", "yes", "si", "sí")


def as_integer(value: Any, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


class OpenQuestionBehavior(ExtrasMixin):
    behavior_name = "open_question"
    extra_origin = "open_question"

    # The behavior's contract. The seeder materializes these rows (creating
    # the missing ones by name, never overwriting); from then on their
    # content, the defaults included, belongs to the DB.
    # name -> (data_type, initial default_value)
    PARAMETERS = {
        "schema": ("string", None),
        "with_confirmation": ("boolean", "true"),
        "max_reasks": ("integer", "3"),
        "first_recap_hint": ("string", FIRST_RECAP_HINT),
        "action": ("string", None),
    }
    # slot name -> initial default text; the order is the fragments' order.
    SLOTS = {
        "question": None,
        "reask": PREGUNTA_GENERICA,
        "recap": None,
        "correction_request": None,
        "notice": NOTICE_TEXT,
        "give_up": None,
        "correction_failed": CORRECTION_FAILED_TEXT,
    }
    SLOT_RULES = {"recap": {"required_if": "with_confirmation"}}
    # Replies a slot fragment carries; each one's destination is the unit's
    # own piece with these parameter values.
    SLOT_REPLIES = {"recap": [("Corregir", {"action": ACTION_CORRECT})]}

    def __init__(
            self, response: ResponseAbc, fragment_id: Optional[int] = None,
            slot_fragment: Optional[Fragment] = None, text: str = "",
            quoted_interaction: Optional[Interaction] = None,
            active_interaction: Optional[Interaction] = None,
            client: Optional[GeminiClient] = None, **kwargs):
        self.result: Optional[str] = None
        self.response = response
        self.member = response.sender.member
        self.params = kwargs
        self.text = (text or "").strip()
        self.slot_fragment = slot_fragment
        self.quoted_interaction = quoted_interaction
        self.active_interaction = active_interaction
        self._client = client

        owner = Fragment.objects.filter(pk=fragment_id).first()
        self.schema = self._param("schema")
        if not owner or self.schema not in SCHEMA_REGISTRY:
            response.add_error({
                "behavior": self.behavior_name, "fragment": fragment_id,
                "schema": self.schema, "message": "esquema no registrado"})
            return
        self.piece = owner.piece
        self.schema_cls, self.system_prompt = SCHEMA_REGISTRY[self.schema]
        self.slots = {
            f.slot.name: f for f in self.piece.fragments.filter(
                slot__behavior_id=self.behavior_name).select_related("slot")}

        if slot_fragment is None:
            self.result = self._on_show()
        else:
            self.result = self._on_text()

    # ------------------------------------------------------------ settings
    def _db_defaults(self) -> dict:
        if not hasattr(self, "_defaults"):
            self._defaults = dict(Parameter.objects.filter(
                behavior_id=self.behavior_name, deleted=False)
                .values_list("name", "default_value"))
        return self._defaults

    def _param(self, name: str) -> Any:
        value = self.params.get(name)
        if value is None or value == "":
            value = self._db_defaults().get(name)
        if value is None or value == "":
            value = self.PARAMETERS[name][1]
        return value

    @property
    def with_confirmation(self) -> bool:
        return as_flag(self._param("with_confirmation"), True)

    @property
    def max_reasks(self) -> int:
        return as_integer(self._param("max_reasks"), 3)

    @property
    def never_drop(self) -> bool:
        return bool(getattr(self.schema_cls, "never_drop", False))

    @property
    def data_fields(self) -> list[str]:
        return [name for name in self.schema_cls.model_fields
                if name not in CONTROL_FIELDS]

    @property
    def client(self) -> GeminiClient:
        if self._client is None:
            self._client = GeminiClient()
        return self._client

    # ----------------------------------------------------------- dispatch
    def _on_show(self) -> str:
        if self.params.get("action") == ACTION_CORRECT:
            return self._start_correction()
        # Shown again while it is still what is pending (a «No entendí»
        # re-render, a photo during the capture): the pending message goes
        # out again as it was, and the answers so far still count.
        last = self._last_outgoing()
        if last and last.fragment.piece_id == self.piece.pk \
                and self._role(last) in ASKING_SLOTS:
            self._resend(last)
            return HANDLED
        self._remove(self._hist_name(self.schema))
        self._send_slot("question")
        return HANDLED

    def _on_text(self) -> str:
        role = self.slot_fragment.slot.name  # type: ignore
        quoted = bool(self.quoted_interaction and (
            self.quoted_interaction.fragment_id == self.slot_fragment.pk))
        if quoted and role == "recap":
            return self._on_quoted_recap()
        if quoted and role not in ASKING_SLOTS:
            return NOT_MINE
        active = self.active_interaction
        active_role = self._role(active)
        if not active or active.fragment.piece_id != self.piece.pk \
                or active_role not in ASKING_SLOTS:
            return NOT_MINE
        correcting = active_role == "correction_request" or (
            active_role == "reask" and self._in_correction())
        return self._on_answer(correcting)

    # ------------------------------------------------------------- answer
    def _on_answer(self, correcting: bool) -> str:
        hist = self._append_hist(self.text)
        if correcting:
            raw = self.client.extract(
                self.system_prompt + CORRECTION_INSTRUCTIONS,
                self._with_current_values("\n".join(hist)), self.schema_cls)
        else:
            raw = self.client.extract(
                self.system_prompt, "\n".join(hist), self.schema_cls)
        complete, values, message = self._evaluate(raw, merge=correcting)

        if complete:
            return self._accept(values, correcting)
        if len(hist) <= self.max_reasks:
            self._send_slot("reask", message)
            return HANDLED
        if self.never_drop:
            if values and any(v is not None for v in values.values()):
                return self._accept(values, correcting)
            self._send_slot("reask", message)
            return HANDLED

        self._remove(self._hist_name(self.schema))
        if correcting:
            # The previous value stays; the person goes back to what was
            # pending.
            self._send_slot("correction_failed", required=False)
            self._resend_pending()
            return HANDLED
        self._send_slot("give_up", required=False)
        return FINISHED

    def _accept(self, values: dict, correcting: bool) -> str:
        self._store(values)
        self._remove(self._hist_name(self.schema))
        self._send_recap()
        if correcting:
            self._resend_pending()
            return HANDLED
        return FINISHED

    def _evaluate(self, raw: Optional[dict], merge: bool
                  ) -> tuple[bool, Optional[dict], str]:
        """(complete, validated data fields, re-ask text). Only what passed
        the schema's validation comes back as values."""
        generic = self._slot_text("reask") or PREGUNTA_GENERICA
        if raw is None:
            return False, None, generic
        data = dict(raw)
        if merge:
            data = {**self._current_values(), **{
                k: v for k, v in raw.items()
                if k in self.data_fields and v is not None}}
            for name in CONTROL_FIELDS:
                data[name] = raw.get(name)
        try:
            dump = self.schema_cls(**data).model_dump()
        except ValidationError as e:
            own = validation_message(e) or raw.get("ia_pregunta")
            return False, None, own or generic
        values = {k: dump.get(k) for k in self.data_fields}
        if dump.get("ia_completed") == "si":
            return True, values, ""
        return False, values, dump.get("ia_pregunta") or generic

    # --------------------------------------------------------- quoted recap
    def _on_quoted_recap(self) -> str:
        recap = (self.quoted_interaction.raw_data or {}).get(  # type: ignore
            "body", "")
        user_text = self._with_current_values(
            f"RECAP:\n{recap}\n\nREPLY:\n{self.text}")
        quote_cls = create_model(
            f"{self.schema_cls.__name__}Quote", __base__=self.schema_cls,
            intent=(Intent, ...))
        raw = self.client.extract(
            self.system_prompt + QUOTE_INSTRUCTIONS, user_text, quote_cls)
        intent = (raw or {}).get("intent")

        if intent == "request":
            return self._start_correction()
        if intent == "confirm":
            self._resend_pending()
            return HANDLED
        if intent == "correct":
            self._set_hist([self.text])
            complete, values, message = self._evaluate(raw, merge=True)
            if complete:
                return self._accept(values, correcting=True)  # type: ignore
            # The re-ask opens a correction: the next answer is read as one.
            self._send_slot("reask", message)
            return HANDLED
        self._send_slot("notice")
        self._resend_pending()
        return HANDLED

    def _start_correction(self) -> str:
        self._remove(self._hist_name(self.schema))
        self._send_slot("correction_request")
        return HANDLED

    # ------------------------------------------------------------ storing
    def _current_values(self) -> dict:
        extras = self.member.get_extra_values_data(refrest=True)
        return {k: extras[k] for k in self.data_fields
                if extras.get(k) not in (None, "")}

    def _with_current_values(self, text: str) -> str:
        current = json.dumps(self._current_values(), ensure_ascii=False)
        return f"CURRENT VALUES:\n{current}\n\n{text}"

    def _store(self, values: dict) -> None:
        for name, value in values.items():
            if value is not None:
                self._write(name, value)
        self._derive()

    def _derive(self) -> None:
        for derivation in DERIVATIONS.get(self.schema, []):
            extras = self.member.get_extra_values_data(refrest=True)
            try:
                derived = derivation(self.response, extras) or {}
            except Exception as e:
                self.response.add_error({
                    "behavior": self.behavior_name, "schema": self.schema,
                    "derivation": getattr(derivation, "__name__", "")}, e=e)
                continue
            for name, value in derived.items():
                if value is None:
                    self._remove(name)
                else:
                    self._write(name, value)

    def _append_hist(self, text: str) -> list:
        """The answers of the current attempt: the extraction reads them
        together, and their count is the number of failures so far."""
        hist = self.member.get_extra_values_data(refrest=True).get(
            self._hist_name(self.schema)) or []
        if not isinstance(hist, list):
            hist = []
        if text:
            hist.append(text)
        self._set_hist(hist)
        return hist

    def _set_hist(self, hist: list) -> None:
        self._write(self._hist_name(self.schema), hist)

    # ------------------------------------------------------------ sending
    def _slot_text(self, name: str) -> Optional[str]:
        fragment = self.slots.get(name)
        if fragment is not None and fragment.body:
            return fragment.body
        if fragment is not None and fragment.slot.default_value:
            return fragment.slot.default_value
        return self._db_defaults().get(name) or self.SLOTS.get(name)

    def _send_slot(self, name: str, body: Optional[str] = None,
                   required: bool = True) -> None:
        text = body or self._slot_text(name)
        fragment = self.slots.get(name)
        if not text:
            if required:
                self.response.add_error({
                    "behavior": self.behavior_name, "piece": self.piece.pk,
                    "slot": name, "message": "slot sin texto"})
            return
        if fragment is None:
            self.response.add_error({
                "behavior": self.behavior_name, "piece": self.piece.pk,
                "slot": name, "message": "la pieza no tiene ese slot"})
            self.response.message_text(text)
            return
        self._send_fragment(fragment, text)

    def _send_fragment(self, fragment: Fragment, body: str) -> None:
        from services.processor.fragment import fragment_reply

        replies = list(fragment.replies.order_by("order"))
        if not replies:
            self.response.message_text(body, fragment_id=fragment.pk)
            return
        message = ReplyMessage(
            body=body, header=fragment.header or None,
            footer=fragment.footer or None, fragment_id=fragment.pk)
        for reply in replies:
            button = fragment_reply(reply)
            if button:
                message.buttons.append(button)
        if message.has_sections() or len(message.buttons) > 3:
            self.response.message_many_buttons(message)
        else:
            self.response.message_few_buttons(message)

    def _send_recap(self) -> None:
        if not self.with_confirmation:
            return
        text = self._slot_text("recap")
        if not text:
            self._send_slot("recap")
            return
        if not self.member.get_extra_values_data().get(FIRST_RECAP_MARKER):
            hint = self._param("first_recap_hint")
            if hint:
                text = f"{text}{RECAP_HINT_SEPARATOR}{hint}"
            self._write(FIRST_RECAP_MARKER, "true")
        self._send_slot("recap", text)

    # ------------------------------------------------------------ history
    @staticmethod
    def _role(interaction: Optional[Interaction]) -> Optional[str]:
        if not interaction or not interaction.fragment:
            return None
        slot = interaction.fragment.slot
        return slot.name if slot else None

    def _outgoing(self):
        return Interaction.objects.filter(
            member_account=self.response.sender, is_incoming=False,
            fragment__isnull=False).select_related(
            "fragment__slot", "fragment__piece").order_by("-created")

    def _last_outgoing(self) -> Optional[Interaction]:
        return self._outgoing().first()

    def _in_correction(self) -> bool:
        """A re-ask belongs to a correction when the datum was already
        recapped since its question was last asked."""
        last = self._outgoing().filter(
            fragment__piece=self.piece,
            fragment__slot__name__in=("question", "recap")).first()
        return self._role(last) == "recap"

    def _resend(self, interaction: Interaction) -> None:
        body = (interaction.raw_data or {}).get("body") \
            or interaction.fragment.body  # type: ignore
        if body:
            self._send_fragment(interaction.fragment, body)  # type: ignore

    def _resend_pending(self) -> None:
        """Sends again what the person had pending before this datum was
        revisited: a question or re-ask word for word, or the whole piece
        (e.g. a buttons piece)."""
        from services.processor.piece import PieceProcessor

        candidates = self._outgoing().exclude(
            fragment__piece=self.piece)[:PENDING_LOOKBACK]
        for interaction in candidates:
            role = self._role(interaction)
            if role in META_SLOTS:
                continue
            if role:
                self._resend(interaction)
            else:
                PieceProcessor(
                    interaction.fragment.piece,  # type: ignore
                    self.response).process()
            return
