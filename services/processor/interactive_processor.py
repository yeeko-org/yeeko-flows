from typing import Optional
from infrastructure.box.models import Destination, Piece, Reply
from services.processor.behavior_processor import BehaviorProcessor
from services.processor.destination_rules import destination_find
from services.processor.piece_processor import PieceProcessor
from services.request.message_model import InteractiveMessage
from services.response.abstract import ResponseAbc


class InteractiveProcessor:
    message: InteractiveMessage
    response: ResponseAbc
    destination: Optional[Destination] = None
    reply: Optional[Reply]

    def __init__(
        self, message: InteractiveMessage, response: ResponseAbc
    ) -> None:
        self.message = message
        self.response = response
        self.reply = message.built_reply.reply if message.built_reply else None

    @property
    def piece(self) -> Piece | None:
        if not hasattr(self, "_piece"):
            self._piece = self.get_piece()
        return self._piece

    def get_piece(self) -> Piece | None:
        if not self.message.built_reply:
            return None

        replay_interaction = self.message.built_reply.interaction
        if not replay_interaction:
            return None

        fragment = replay_interaction.fragment
        if not fragment:
            return None

        return fragment.piece

    def process(self):
        built_reply = self.message.built_reply
        if not built_reply:
            self.process_behavior()
            return
        if not built_reply.reply:
            return
        
        built_reply.reply.set_assign(
            self.response.sender.member, self.message.interaction)

        self.destination = destination_find(
            built_reply.reply.get_destinations(), self.response.sender.member,
            "self.response.platform_name", raise_exception=False)

        if (
            not self.destination and built_reply.interaction
            and built_reply.interaction.fragment
        ):
            print("---------------------destination_find---------------------")
            self.destination = destination_find(
                built_reply.interaction.fragment.piece.get_destinations(),
                self.response.sender.member,
                "self.response.platform_name", raise_exception=True)

        if not self.destination:
            self.process_behavior("destination_fail")

        elif self.destination.destination_type == "behavior":
            self.process_behavior(
                getattr(self.destination, "behavior_id", ""))

        elif self.destination.destination_type == "piece":
            if not self.destination.piece_dest:
                return
            piece_processor = PieceProcessor(
                response=self.response, piece=self.destination.piece_dest)
            piece_processor.process()

    def process_behavior(self, behavior_name: Optional[str] = None):
        if not behavior_name:
            behavior_name = self.message.payload

        BehaviorProcessor(behavior=behavior_name,
                          response=self.response).process()
