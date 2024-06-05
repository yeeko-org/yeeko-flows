from typing import Optional
from infrastructure.box.models import Written
from infrastructure.xtra.models import Extra
from services.processor.behavior_processor import BehaviorProcessor
from services.processor.destination_rules import destination_find
from services.processor.piece_processor import PieceProcessor
from services.request.message_model import TextMessage
from services.response.abstract import ResponseAbc


class WrittenProcessor:
    response: ResponseAbc
    message: TextMessage
    written: Written
    extra: Extra

    def __init__(
            self, response: ResponseAbc, message: TextMessage,
            written: Written, default_extra: Optional[Extra] = None
    ):
        self.response = response
        self.message = message
        self.written = written
        self.written.set_assign(
            self.response.sender.member, self.message.interaction)
        _extra = self.written.extra or default_extra
        if not _extra:
            raise ValueError("Written must have an extra")
        self.extra = _extra

    def process(self):

        self.response.sender.member.add_extra_value(
            self.extra, self.message.text, self.message.interaction, "written"
        )

        destination = destination_find(
            self.written.get_destinations(), self.response.sender.member,
            "self.response.platform_name")

        if not destination:
            raise ValueError("Destination not found")

        elif destination.destination_type == "behavior":
            behavior_name = getattr(destination, "behavior_id", "")
            if not behavior_name:
                raise ValueError("Behavior not found")
            behavior_processor = BehaviorProcessor(
                behavior=behavior_name, response=self.response)
            behavior_processor.process()

        elif destination.destination_type == "piece":
            if not destination.piece_dest:
                raise ValueError("Piece not found")
            piece_processor = PieceProcessor(
                response=self.response, piece=destination.piece_dest)
            piece_processor.process()
