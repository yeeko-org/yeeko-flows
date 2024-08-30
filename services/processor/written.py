from typing import Optional
from infrastructure.box.models import Written
from infrastructure.xtra.models import Extra
from services.processor.destination_rules import destination_find
from services.processor.base_mixin import DestinationProcessorMixin
from services.request.message_model import TextMessage
from services.response.abstract import ResponseAbc


class WrittenProcessor(DestinationProcessorMixin):
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

        self.response.add_extra_value(
            self.extra, self.message.text, self.message.interaction, "written"
        )

        self.process_destination()

    def get_destination(self) -> None:
        self.destination = destination_find(
            self.written.get_destinations(), self.response.sender.member,
            self.response.platform_name, raise_exception=False)
