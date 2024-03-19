from typing import Type
from urllib import response
from services.processor import text_processor

from services.processor.interactive_processor import InteractiveProcessor
from services.manager_flow.manager_flow_abc import AbstractManagerFlow
from services.processor.state_processor import StateProcessor
from services.processor.text_processor import TextMessageProcessor
from services.request.message_model import (
    InteractiveMessage, EventMessage, TextMessage
)
from services.response import ResponseAbc

from services.request import MemberMessages, RequestAbc


class ManagerFlow(AbstractManagerFlow):

    def __init__(
            self, raw_data: dict, request_class: Type[RequestAbc],
            response_class: Type[ResponseAbc]
    ) -> None:
        self.request = request_class(raw_data)
        self._response_class = response_class

        self.text_processor_class = TextMessageProcessor
        self.interacive_processor = InteractiveProcessor(self)
        self.state_processor = StateProcessor(self)

        self.response_list = []

    def __call__(
            self
    ) -> None:
        for account in self.request.accounts:
            for member in account.members:
                self.process_messages(member)

        for response in self.response_list:
            response.send_messages()

    def process_messages(self, member: MemberMessages) -> None:
        """
        Se requiere implementar una funcion que limpie y determine el mensaje
        principal o la intencion en caso de recibir varios mensajes.
        """
        for message in member.messages:
            response = self._response_class(sender=member.member)
            self.response_list.append(response)
            self.process_message(message, response)

    def process_message(
        self, message: TextMessage | InteractiveMessage | EventMessage,
        response: ResponseAbc
    ) -> None:
        if isinstance(message, TextMessage):
            text_processor = TextMessageProcessor(self, message, response)
            text_processor.process()
        elif isinstance(message, InteractiveMessage):
            self.interacive_processor.process(message)
        elif isinstance(message, EventMessage):
            self.state_processor.process(message)
        else:
            raise ValueError("Message type not supported")
