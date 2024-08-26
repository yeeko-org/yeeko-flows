from abc import ABC, abstractmethod
from typing import List, Type

from services.request import RequestAbc
from services.request.message_model import InteractiveMessage, EventMessage, TextMessage
from services.response import ResponseAbc


class AbstractManagerFlow(ABC):
    request: RequestAbc
    response_list: List[ResponseAbc]

    @abstractmethod
    def __init__(
            self, raw_data: dict, request_class: Type[RequestAbc],
            response_class: Type[ResponseAbc]
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def __call__(
            self
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def process_message(
        self, message: TextMessage | InteractiveMessage | EventMessage
    ) -> None:
        raise NotImplementedError
