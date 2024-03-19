from abc import ABC, abstractmethod
from pprint import pprint
from typing import Optional

from pydantic import BaseModel

from infrastructure.member.models import MemberAccount
from infrastructure.service.models import ApiRequest
from typing import List, Optional

from services.response.models import SectionsMessage, ReplayMessage

from typing import Callable


def exception_handler(func: Callable) -> Callable:
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            self.errors.append(str(e))
    return wrapper


class ResponseAbc(ABC, BaseModel):
    sender: MemberAccount
    message_list: List[tuple[dict, Optional[ApiRequest]]] = []
    errors: list = []
    api_request: Optional[ApiRequest] = None

    class Config:
        arbitrary_types_allowed = True

    def _add_message(self, message: dict):
        self.message_list.append((message, self.api_request))

    @exception_handler
    def message_text(self, message: str):
        message_data = self.text_to_data(message)
        self._add_message(message_data)

    @exception_handler
    def message_multimedia(
        self, url_media: str, media_type: str, caption: str = ""
    ):
        message_data = self.multimedia_to_data(url_media, media_type, caption)
        self._add_message(message_data)

    @exception_handler
    def message_few_buttons(self, message: ReplayMessage):
        message_data = self.few_buttons_to_data(message)
        self._add_message(message_data)

    @exception_handler
    def message_many_buttons(self, message: ReplayMessage):
        message_data = self.many_buttons_to_data(message)
        self._add_message(message_data)

    @exception_handler
    def message_sections(self, message: SectionsMessage):
        message_data = self.sections_to_data(message)
        self._add_message(message_data)

    def send_messages(self):
        for message, api_request in self.message_list:
            try:
                response = self.send_message(message)
                self.save_interaction(response, message, api_request)
            except Exception as e:
                self.errors.append(str(e))

    @abstractmethod
    def text_to_data(self, message: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def multimedia_to_data(
        self, url_media: str, media_type: str, caption: str
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def few_buttons_to_data(self, message: ReplayMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def many_buttons_to_data(self, message: ReplayMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def sections_to_data(self, message: SectionsMessage) -> dict:
        raise NotImplementedError

    @abstractmethod
    def send_message(
        self, message_data: dict
    ) -> dict:
        raise NotImplementedError

    def save_interaction(
        self, response: dict, message_data: dict,
        api_request: Optional[ApiRequest] = None
    ) -> None:
        pprint(response)


"""
posibles mensjaes de whatsapp
https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#mensajes-interactivos

mensajes de productos y multiproductos y catalogos (catalogo de ventas de whatsapp bussines)
mensajes de flujos


mensjae de listas
mensajes de respuesta

mensaje de plantillas

"""


"""
para los interpretes generales seran:

mensaje simple
mensaje media
mensaje de 3 botones
mensaje de 10 botones
mensaje de secciones


"""
