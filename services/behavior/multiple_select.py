from typing import List, Optional

from infrastructure.talk.models import BuiltReply
from infrastructure.xtra.models import Extra
from services.response.abstract import ResponseAbc
from services.response.models import WaFormMessage


def _as_int(value, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_options(options: list) -> List[dict]:
    """Turn ``[{value,label}]`` (or ``[{id,title}]``) into the
    ``[{id,title}]`` shape the Flow's CheckboxGroup data-source expects."""
    normalized: List[dict] = []
    for option in options or []:
        if not isinstance(option, dict):
            continue
        option_id = option.get("id", option.get("value"))
        title = option.get("title", option.get("label", option_id))
        if option_id is None:
            continue
        item = {"id": str(option_id), "title": str(title)}
        # Opcional: solo la entienden Flows cuyo schema declare
        # description (p. ej. multiselect_desc.flow.json).
        description = option.get("description")
        if description:
            item["description"] = str(description)
        normalized.append(item)
    return normalized


class MultipleSelectBehavior:
    """Send a WhatsApp Flows ("WaForm") multiple-select form.

    Generic and reusable: the closed list of options and every label
    travel as parameters, so a single published Flow can back any
    multiple-select question. The chosen ids are written later (on the
    ``nfm_reply``) by ``WaFormReplyProcessor``; this class only sends.

    Correlation: a ``BuiltReply`` is created and its uuid is used as the
    ``flow_token``; its ``params`` carry the target extra and the piece to
    advance to once the user submits.
    """

    def __init__(
            self, response: ResponseAbc, flow_id: Optional[str] = None,
            body: Optional[str] = None, extra: Optional[str] = None,
            dest_piece_pk=None, label: Optional[str] = None,
            options: Optional[list] = None,
            options_extra: Optional[str] = None,
            header: Optional[str] = None, footer: Optional[str] = None,
            flow_cta: str = "Seleccionar", screen: str = "SELECT",
            min=None, max=None, fragment_id: Optional[int] = None, **kwargs
    ) -> None:
        self.response = response

        missing = [
            name for name, value in (
                ("flow_id", flow_id), ("body", body),
                ("extra", extra), ("dest_piece_pk", dest_piece_pk),
            ) if not value
        ]
        if missing:
            response.add_error(
                {"behavior": "multiple_select",
                 "error": f"Faltan parámetros requeridos: {missing}"}
            )
            return

        extra_obj = self._get_extra(extra)
        if not extra_obj:
            return

        option_list = self._resolve_options(options, options_extra)
        if not option_list:
            response.add_error(
                {"behavior": "multiple_select",
                 "error": "No se encontraron opciones para el formulario"}
            )
            return

        min_items = _as_int(min, 0) or 0
        max_items = _as_int(max)

        built_reply = BuiltReply.objects.create(
            is_for_write=True,
            params={
                "behavior": "multiple_select",
                "extra": extra_obj.name,
                "dest_piece_pk": _as_int(dest_piece_pk),
                "min": min_items,
                "max": max_items,
            },
        )
        flow_token = str(built_reply.uuid)

        data = {
            "title": label or body,
            "label": label or body,
            "options": option_list,
            "min": min_items,
            "flow_token": flow_token,
        }
        if max_items is not None:
            data["max"] = max_items

        message = WaFormMessage(
            # Liga la Interaction saliente al fragment: sin esto el usuario
            # queda "atorado" en la pieza anterior (at_piece/context).
            fragment_id=fragment_id,
            flow_id=str(flow_id),
            flow_token=flow_token,
            flow_cta=flow_cta,
            screen=screen,
            body=str(body),
            header=header,
            footer=footer,
            data=data,
        )
        response.message_wa_form(message)

    def _get_extra(self, extra_name: str) -> Optional[Extra]:
        extra_obj = Extra.objects.filter(
            name=extra_name, space=self.response.sender.account.space,
            deleted=False,
        ).first()
        if not extra_obj:
            self.response.add_error(
                {"behavior": "multiple_select",
                 "error": f"No se encontró el extra '{extra_name}'"}
            )
        return extra_obj

    def _resolve_options(
            self, options: Optional[list], options_extra: Optional[str]
    ) -> List[dict]:
        if options:
            return _normalize_options(options)

        if options_extra:
            values = self.response.sender.member.get_extra_values_data()
            raw = values.get(options_extra)
            if isinstance(raw, list):
                return _normalize_options(raw)

        return []
