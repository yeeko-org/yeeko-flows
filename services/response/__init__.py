from abc import ABC, abstractmethod
from pprint import pprint
from typing import Optional

from pydantic import BaseModel

from infrastructure.member.models import MemberAccount
from infrastructure.service.models import ApiRecord
from typing import List, Optional

from infrastructure.talk.models import Interaction
from services.response.models import SectionsMessage, ReplyMessage

from typing import Callable


def exception_handler(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            self.api_record_in.add_error(
                {
                    "error": str(e),
                    "method": func.__name__,
                },
                e=e
            )

    return wrapper


class ResponseAbc(ABC, BaseModel):
    sender: MemberAccount
    api_record_in: ApiRecord
    message_list: List[dict] = []

    class Config:
        arbitrary_types_allowed = True

    @exception_handler
    def message_text(self, message: str):
        message_data = self.text_to_data(message)
        self.message_list.append(message_data)

    @exception_handler
    def message_multimedia(
        self, url_media: str, media_type: str, caption: str = ""
    ):
        message_data = self.multimedia_to_data(url_media, media_type, caption)
        self.message_list.append(message_data)

    @exception_handler
    def message_few_buttons(self, message: ReplyMessage):
        message_data = self.few_buttons_to_data(message)
        self.message_list.append(message_data)

    @exception_handler
    def message_many_buttons(self, message: ReplyMessage):
        message_data = self.many_buttons_to_data(message)
        self.message_list.append(message_data)

    @exception_handler
    def message_sections(self, message: SectionsMessage):
        message_data = self.sections_to_data(message)
        self.message_list.append(message_data)

    def send_messages(self):
        for message in self.message_list:
            try:
                api_record_out = self.send_message(message)
            except Exception as e:
                self.api_record_in.add_error(
                    {
                        "error": str(e),
                        "method": "send_message",
                        "message": message
                    },
                    e=e
                )
                continue
            try:
                self.save_interaction(api_record_out, message)
            except Exception as e:
                self.api_record_in.add_error(
                    {
                        "error": str(e),
                        "method": "save_interaction"
                    },
                    e=e
                )

    @abstractmethod
    def text_to_data(self, message: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def multimedia_to_data(
        self, url_media: str, media_type: str, caption: str
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def few_buttons_to_data(self, message: ReplyMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def many_buttons_to_data(self, message: ReplyMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def sections_to_data(self, message: SectionsMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def send_message(
        self, message_data: dict
    ) -> ApiRecord:
        raise NotImplementedError

    @abstractmethod
    def get_mid(self, body: Optional[dict]) -> Optional[str]:
        raise NotImplementedError

    def save_interaction(
        self, api_record_out: ApiRecord, message_data: dict
    ) -> None:

        if api_record_out.response_status != 200:
            # a quien oertenece el error?
            self.api_record_in.add_errors(
                [
                    {
                        "error": "Error en la respuesta de salida",
                        "method": "save_interaction",
                        "status": api_record_out.response_status,
                        "body": api_record_out.response_body
                    }
                ]
            )
            return
        mid = self.get_mid(api_record_out.response_body)

        if not mid:
            self.api_record_in.add_errors(
                [
                    {
                        "error": "No se pudo obtener el mid",
                        "method": "save_interaction",
                        "status": api_record_out.response_status,
                        "body": api_record_out.response_body
                    }
                ]
            )
            return

        interaction = Interaction.objects.create(
            mid=mid,
            interaction_type_id="default",
            is_incoming=False,
            member_account=self.sender,
            # api_record_in=self.api_record_in,
            api_record_out=api_record_out
        )
        interaction.api_record_in.add(self.api_record_in)
