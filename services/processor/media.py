from django.db.models.fields.files import FieldFile

from services.processor.behavior import BehaviorProcessor
from services.processor.context_mixin import ContextMixing
from services.processor.text import TextProcessor
from services.processor.written import WrittenProcessorFull
from services.request.message_model import MediaMessage
from services.response import ResponseAbc


class MediaProcessor(ContextMixing):
    message: MediaMessage
    response: ResponseAbc
    media_in: FieldFile

    def __init__(
            self, message: MediaMessage, response: ResponseAbc
    ) -> None:
        if not message.interaction:
            raise ValueError("MediaMessage must have an interaction")

        if not message.interaction.media_in:
            raise ValueError("MediaMessage must have a media_in")

        self.media_in = message.interaction.media_in
        self.message = message
        self.response = response
        self.calculate_context_piece(response.sender, self.message.context_id)

    def process_written(self):
        if self.message.caption:
            written_text = f"{self.message.caption}:{self.media_in.url}"
        else:
            written_text = self.media_in.url

        if not self.context_piece:
            return False
        try:
            written_processor = WrittenProcessorFull(
                response=self.response, message=written_text,
                context_piece=self.context_piece,
                interaction_in=self.message.interaction
            )
        except Exception as e:
            return False

        written_processor.process()
        return True

    def process(self):

        if self.process_written():
            return

        if self.message.caption:
            TextProcessor(
                text=self.message.caption, response=self.response,
                context_id=self.message.context_id,
                interaction_in=self.message.interaction, do_written=False
            ).process()

        BehaviorProcessor(
            "default_media", self.response, parameters={
                "media": self.media_in.url
            },
            context_direct=self.context_direct,
            interaction_in=self.message.interaction).process()
