from services.processor.processor_base import Processor
from services.request.message_model import InteractiveMessage


class InteractiveProcessor(Processor):

    def process(self, message: InteractiveMessage):
        self.message = message
        return self.message
