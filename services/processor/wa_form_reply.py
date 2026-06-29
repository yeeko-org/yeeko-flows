from typing import Optional

from infrastructure.box.models import Piece
from infrastructure.talk.models import BuiltReply
from infrastructure.xtra.models import Extra
from services.processor.piece import PieceProcessor
from services.request.message_model import WaFormReplyMessage
from services.response.abstract import ResponseAbc


class WaFormReplyProcessor:
    """Handle a WhatsApp Flows ("WaForm") completion (``nfm_reply``).

    Looks up the ``BuiltReply`` that ``MultipleSelectBehavior`` created
    (via ``flow_token``), writes the chosen ids into the target JSON
    extra as a list, and advances to the destination piece. No separate
    confirmation step: writing and advancing happen in one shot.
    """

    def __init__(
            self, message: WaFormReplyMessage, response: ResponseAbc
    ) -> None:
        self.message = message
        self.response = response

    def process(self) -> None:
        built_reply = BuiltReply.objects.filter(
            uuid=self.message.flow_token, is_for_write=True).first()
        if not built_reply:
            self.response.add_error(
                {"processor": "wa_form_reply",
                 "error": "BuiltReply no encontrado",
                 "flow_token": self.message.flow_token}
            )
            return

        params = built_reply.params or {}

        extra = self._get_extra(params.get("extra"))
        if not extra:
            return

        self._validate_count(params)

        self.response.set_trigger(
            built_reply, is_direct=True,
            interaction_in=self.message.interaction)

        self.response.add_extra_value(
            extra, self.message.selected, self.message.interaction,
            origin="payload")

        self._process_destination(params.get("dest_piece_pk"))

    def _get_extra(self, extra_name: Optional[str]) -> Optional[Extra]:
        if not extra_name:
            self.response.add_error(
                {"processor": "wa_form_reply",
                 "error": "El BuiltReply no tiene 'extra' en params"}
            )
            return None

        extra = Extra.objects.filter(
            name=extra_name, space=self.response.sender.account.space,
            deleted=False,
        ).first()
        if not extra:
            self.response.add_error(
                {"processor": "wa_form_reply",
                 "error": f"No se encontró el extra '{extra_name}'"}
            )
        return extra

    def _validate_count(self, params: dict) -> None:
        # Non-blocking: the published Flow already enforces required/min/max
        # client-side; this is a server-side safety net that only logs.
        count = len(self.message.selected)
        min_items = params.get("min") or 0
        max_items = params.get("max")

        if count < min_items or (max_items is not None and count > max_items):
            self.response.add_error(
                {"processor": "wa_form_reply",
                 "error": "Cantidad de opciones fuera de rango",
                 "count": count, "min": min_items, "max": max_items}
            )

    def _process_destination(self, dest_piece_pk) -> None:
        piece = Piece.objects.filter(pk=dest_piece_pk, deleted=False).first()
        if not piece:
            self.response.add_error(
                {"processor": "wa_form_reply",
                 "error": "Pieza destino no encontrada",
                 "dest_piece_pk": dest_piece_pk}
            )
            return

        PieceProcessor(piece, self.response).process()
