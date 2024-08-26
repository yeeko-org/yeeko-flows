from abc import ABC, abstractmethod
from typing import Optional
from infrastructure.box.models import Destination

from services.response.abstract import ResponseAbc
from utilities.parameters import update_parameters


class Processor(ABC):

    @abstractmethod
    def process(self, message):
        raise NotImplementedError


class DestinationProcessorMixin:
    response: ResponseAbc
    destination: Optional[Destination] = None

    parameters: dict = {}

    @abstractmethod
    def get_destination(self) -> None:
        raise NotImplementedError

    def process_destination(self):
        from services.processor.piece import PieceProcessor
        from services.processor.behavior import BehaviorProcessor

        self.get_destination()

        if not self.destination:
            BehaviorProcessor(
                behavior="destination_fail", response=self.response,
                parameters=self.parameters).process()
            return

        self.parameters = update_parameters(
            self.destination.values, self.parameters)  # type: ignore

        if self.destination.destination_type == "behavior":
            behavior_name = getattr(self.destination, "behavior_id", "")
            BehaviorProcessor(
                behavior=behavior_name, response=self.response,
                parameters=self.parameters).process()

        elif self.destination.destination_type == "piece":
            if not self.destination.piece_dest:
                raise ValueError("Piece not found")
            piece_processor = PieceProcessor(
                response=self.response, piece=self.destination.piece_dest,
                parameters=self.parameters)
            piece_processor.process()
