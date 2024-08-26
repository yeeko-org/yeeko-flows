import re
from typing import Optional

from infrastructure.box.models import Piece, Written
from infrastructure.member.models import MemberAccount
from infrastructure.service.models import ApiRecord
from infrastructure.talk.models import Interaction
from infrastructure.xtra.models import Extra
from services.processor.base_mixin import Processor
from services.request.message_model import MediaMessage
from services.response import ResponseAbc


class MediaProcessor(Processor):
    sender: MemberAccount
    api_request: ApiRecord
    request_message_id: str
    message: MediaMessage
    response: ResponseAbc
    written: Optional[Written] = None
    default_extra: Optional[Extra] = None
    last_interaction_out: Optional[Interaction] = None

    def __init__(
            self, message: MediaMessage, response: ResponseAbc
    ) -> None:
        self.message = message
        self.sender = response.sender

        self.response = response
        self.set_written_context()

    def set_written_context(self):
        context_piece = None
        self.context_direct = False
        if self.message.context_id:
            context_piece = Piece.objects.filter(
                fragments__interaction__mid=self.message.context_id).first()
            self.context_direct = True
        else:
            context_interaction = Interaction.objects.filter(
                member_account=self.sender, is_incoming=False)\
                .order_by("created").last()
            self.last_interaction_out = context_interaction

            if context_interaction and context_interaction.fragment:
                context_piece = context_interaction.fragment.piece

        self.written = getattr(context_piece, "written", None)
        self.default_extra = getattr(context_piece, "default_extra", None)

    def process(self):
        self.response.message_text(
            message="media recibido y guardado"
        )
        if not self.message.interaction:
            return
        media_in = self.message.interaction.media_in
        if not media_in:
            return

        media_in_url = media_in.url
        self.response.message_multimedia(
            url_media=media_in_url, media_type=self.message.media_type)
