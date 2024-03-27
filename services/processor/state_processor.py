from typing import Optional
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import Event
from services.processor.processor_base import Processor
from services.request.message_model import EventMessage
from services.response import ResponseAbc
from django.utils import timezone


class StateProcessor(Processor):
    message: EventMessage
    response: ResponseAbc
    api_record: Optional[ApiRecord] = None

    def __init__(
            self, manager_flow, message: EventMessage, response: ResponseAbc
    ) -> None:
        self.manager_flow = manager_flow
        self.message = message
        self.response = response
        self.api_record = self.response.api_record_in
        self.request_message_id = self.message.message_id

    def process(self):

        Event.objects.create(
            event_name=self.message.status,
            interaction=self.message.interaction,
            api_request=self.api_record,
            timestamp=self.message.timestamp,
            emoji=self.message.emoji,
            date=timezone.now(),
        )

        self.message.interaction.api_record_in.add(self.api_record)
