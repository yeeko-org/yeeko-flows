from services.processor.processor_base import Processor
from services.request.message_model import EventMessage


class StateProcessor(Processor):

    def process(self, message: EventMessage):
        self.message = message
        return self.message
