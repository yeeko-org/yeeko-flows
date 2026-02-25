from typing import List, Type
from infrastructure.service.models import ApiRecord
from services.manager_flow.manager_flow_abc import AbstractManagerFlow
from services.processor.interactive import InteractiveProcessor
from services.processor.media import MediaProcessor
from services.processor.state import StateProcessor
from services.processor.text import TextMessageProcessor
from services.request import RequestAbc
from services.request.record import RecordRequestAbc, InputSender
from services.response import ResponseAbc

from services.request.message_model import (
    InteractiveMessage, EventMessage, MediaMessage, TextMessage
)


class ManagerFlow(AbstractManagerFlow):

    def __init__(
            self, request_record: RecordRequestAbc,
            response_class: Type[ResponseAbc]
    ) -> None:
        self.request_record = request_record
        self._response_class = response_class
        self.response_list: List[ResponseAbc] = []

    def __call__(
            self
    ) -> None:
        for input_sender in self.request_record.input_senders:
            self.process_messages(input_sender)

        for response in self.response_list:
            response.send_messages()

    def process_messages(
            self, input_sender: InputSender
    ) -> None:
        """
        Se requiere implementar una funcion que limpie y determine el mensaje
        principal o la intencion en caso de recibir varios mensajes.

        aquellos mensajes que se procesen se les registrara el record_interaction
        """
        for message in input_sender.messages:
            if type(message) in [TextMessage, InteractiveMessage, MediaMessage]:
                message.record_interaction(  # type: ignore
                    input_sender.api_record, input_sender.member)

            response = self._response_class(
                sender=input_sender.member,
                api_record_in=input_sender.api_record,
                platform_name=self.request_record.platform_name

            )

            self.response_list.append(response)

            try:
                self.process_message(message, response)
            except Exception as e:
                data_error = {
                    "method": "process_messages",
                    "message": message.model_dump(),
                }
                input_sender.api_record.add_error(data_error, e=e)

    def process_message(
        self, message: TextMessage | InteractiveMessage | EventMessage | MediaMessage,
        response: ResponseAbc
    ) -> None:
        if isinstance(message, TextMessage):
            text_processor = TextMessageProcessor(message, response)
            text_processor.process()
        elif isinstance(message, InteractiveMessage):
            interactive_processor = InteractiveProcessor(message, response)
            interactive_processor.process()
            pass
        elif isinstance(message, EventMessage):
            event_processor = StateProcessor(self, message, response)
            event_processor.process()

        elif isinstance(message, MediaMessage):
            media_processor = MediaProcessor(message, response)
            media_processor.process()

        else:
            raise ValueError(f"Message type {type(message)} not supported")
