import re
from typing import Optional

from infrastructure.box.models import Piece, Reply
from infrastructure.talk.models import BuiltReply, Interaction
from services.processor.behavior import (
    FINISHED, NOT_MINE, BehaviorNotFound, BehaviorProcessor)
from services.processor.context_mixin import ContextMixing
from services.processor.interactive import ReplyProcessor
from services.processor.written import WrittenProcessorFull
from services.request.message_model import TextMessage
from services.response import ResponseAbc
from utilities.standar_str import standar


class TextProcessor(ContextMixing):

    text: str
    response: ResponseAbc
    interaction_in: Optional[Interaction] = None

    def __init__(
            self, text: str, response: ResponseAbc,
            interaction_in: Optional[Interaction] = None,
            context_piece: Optional[Piece] = None,
            context_id: Optional[str] = None,
            do_written: bool = True
    ) -> None:
        self.text = text
        self.response = response

        self.interaction_in = interaction_in
        self.context_piece = context_piece
        self.do_written = do_written
        self.calculate_context_piece(self.response.sender, context_id)

    def process(self, call_default_text=True) -> bool:
        """Devuelve True si el mensaje ya quedó atendido, para que una
        subclase no vuelva a procesarlo (ver TextMessageProcessor)."""
        if self.command_handler():
            return True

        if self.dispatch_to_slot_behavior():
            return True

        # A quote of a capture that is no longer the active one is loose
        # text: answering it again would rewrite the datum and send the
        # flow back there.
        if (self.context_direct and self.quote_is_active()
                and self.process_written()):
            return True

        if self.intent_to_contact_administrator():
            return True

        if not self.last_interaction_out:
            self.call_behavior("start")
            return True

        if self.check_buttons_text():
            return True

        if call_default_text:
            return self.call_behavior(
                "default_text", parameters={"text": self.text}, optional=True)

        return False

    def command_handler(self):
        if self.text.startswith("/"):
            self.call_behavior(self.text[1:])
            return True

    def quote_is_active(self) -> bool:
        active = self.active_piece
        return bool(active and self.context_piece
                    and active.pk == self.context_piece.pk)

    def dispatch_to_slot_behavior(self) -> bool:
        """The single door through which typed text reaches a behavior that
        sends its messages through slot fragments. The quoted message wins
        over the active one; the behavior may answer NOT_MINE and the text
        goes on down the usual chain."""
        from services.processor.fragment import fragment_parameters
        from services.processor.piece import PieceProcessor

        slot_fragment = next(
            (i.fragment for i in (
                self.quoted_interaction, self.active_interaction)
             if i and i.fragment and i.fragment.slot_id), None)
        if not slot_fragment:
            return False

        piece = slot_fragment.piece
        behavior = slot_fragment.slot.behavior  # type: ignore
        owner = piece.fragments.filter(
            slot__isnull=True, fragment_type="behavior",
            behavior=behavior).order_by("order").first()
        if not owner:
            return False

        parameters = fragment_parameters(owner, {
            "fragment_id": owner.pk,
            "text": self.text,
            "slot_fragment": slot_fragment,
            "quoted_interaction": self.quoted_interaction,
            "active_interaction": self.active_interaction,
            "interaction_in": self.interaction_in,
        })
        try:
            processor = BehaviorProcessor(
                behavior.name, self.response, parameters=parameters,
                context_direct=self.context_direct,
                interaction_in=self.interaction_in)
        except BehaviorNotFound as e:
            self.response.add_error(
                {"method": "dispatch_to_slot_behavior",
                 "behavior": behavior.name}, e=e)
            return False

        result = processor.process()
        if result == NOT_MINE:
            return False
        if result == FINISHED:
            PieceProcessor(piece, self.response).follow_next()
        return True

    def intent_to_contact_administrator(self) -> bool:
        if not bool(re.search(r"admin", self.text, re.IGNORECASE)):
            return False

        self.call_behavior("admin_contact")
        return True

    def call_behavior(
        self, behavior, parameters={}, optional: bool = False
    ) -> bool:
        try:
            behavior_processor = BehaviorProcessor(
                behavior, self.response, parameters=parameters,
                context_direct=self.context_direct,
                interaction_in=self.interaction_in)
        except BehaviorNotFound as e:
            if not optional:
                raise
            # Sin `default_text` sembrado el bot calla; se deja constancia
            # para que la falta de configuración no pase inadvertida.
            if self.response.api_record_in:
                self.response.api_record_in.add_error(
                    {"method": "call_behavior", "behavior": behavior}, e=e)
            return False

        behavior_processor.process()
        return True

    def process_written(self):
        if not self.do_written:
            return False
        if not self.context_piece:
            return False
        try:
            written_processor = WrittenProcessorFull(
                response=self.response, message=self.text,
                context_piece=self.context_piece,
                interaction_in=self.interaction_in
            )
        except Exception as e:
            return False

        written_processor.process()
        return True

    def check_buttons_text(self):
        # estandarizar texto, buscar normalizador de texto
        if not self.context_piece:
            return False

        replays = Reply.objects.filter(
            fragment__piece=self.context_piece)

        reply_by_text = None

        for replay in replays:
            if not replay.title:
                continue
            if standar(replay.title) == standar(self.text):
                reply_by_text = replay
                break

        if not reply_by_text:
            return False

        interaction_origin = Interaction.objects.filter(
            fragment__piece=self.context_piece,
            # Todo configurar el related_name despues de merge con notifications
            builtreply__reply=reply_by_text,
            member_account=self.response.sender
        ).first()

        built_reply = BuiltReply.objects.filter(
            interaction=interaction_origin,
            reply=reply_by_text
        ).first()
        if built_reply:
            self.response.set_trigger(
                built_reply, interaction_in=self.interaction_in)

        reply_processor = ReplyProcessor(
            reply=reply_by_text, response=self.response,
            interaction_origin=self.last_interaction_out
        )
        reply_processor.process()
        return True


class TextMessageProcessor(TextProcessor):

    message: TextMessage

    def __init__(
            self, message: TextMessage, response: ResponseAbc
    ) -> None:
        self.message = message
        super().__init__(
            text=message.text, response=response,
            context_id=message.context_id, interaction_in=message.interaction
        )

    def process(self):
        if super().process(call_default_text=False):
            return

        # Captura de texto tecleado SIN `context` de WhatsApp (Meta solo manda
        # context en taps/reply-to). Con context, el padre ya resolvió
        # process_written por la vía context_direct (text.py arriba), así que el
        # hijo solo cubre el caso sin context y evita doble proceso.
        if not self.context_direct and self.process_written():
            return

        self.call_behavior(
            "default_text", parameters={"text": self.text}, optional=True)
