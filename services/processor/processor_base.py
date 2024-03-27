from abc import ABC, abstractmethod
from services.manager_flow.manager_flow_abc import AbstractManagerFlow


class Processor(ABC):
    manager_flow: AbstractManagerFlow

    def __init__(self, manager_flow) -> None:
        self.manager_flow = manager_flow
        self.message = None

    @abstractmethod
    def process(self, message):
        raise NotImplementedError
