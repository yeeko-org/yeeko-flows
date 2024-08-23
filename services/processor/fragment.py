from typing import List, Optional
from infrastructure.box.models import Fragment, Reply
from infrastructure.talk.models import BuiltReply
from services.response.abstract import ResponseAbc
from services.response.models import Button, Header, ReplyMessage, SectionHeader
from utilities.parameters import replace_parameter, update_parameters


def fragment_reply(
        reply: Reply
) -> Button | SectionHeader | None:
    title = reply.title or f"Opción {reply.order}"

    if reply.is_header_section:
        return SectionHeader(title=title)

    built_reply = BuiltReply.objects.create(
        reply=reply,
        is_for_reply=True,
    )

    return Button(
        title=title,
        payload=str(built_reply.uuid),
        description=reply.description
    )


class FragmentProcessor:
    fragment: Fragment
    response: ResponseAbc
    parameters: dict
    reply_message: List[Reply]

    def __init__(
            self, fragment: Fragment, response: ResponseAbc,
            parameters: dict = {}
    ) -> None:
        self.response = response
        self.fragment = fragment
        self.parameters = update_parameters(
            fragment.values, parameters)  # type: ignore
        self.reply_message = list(fragment.replies.order_by("order"))

    def _header_from_fragment(self) -> Optional[Header | str]:
        if self.fragment.media_type:
            value = (
                self.fragment.file.url if self.fragment.file
                else self.fragment.media_url
            )
            if value:
                return Header(type=self.fragment.media_type, value=value)

        if self.fragment.header:
            return self.fragment.header

        return

    def _process_reply_message(self):
        header = self._header_from_fragment()

        footer = self.fragment.footer if self.fragment.footer else None

        message = ReplyMessage(
            header=header,
            body=self.fragment.body or "",
            footer=footer,
            fragment_id=self.fragment.pk
        )

        for reply in self.reply_message:
            button = fragment_reply(reply)
            if not button:
                continue
            message.buttons.append(button)

        if message.has_sections() or len(message.buttons) > 3:
            self.response.message_many_buttons(message)
        else:
            self.response.message_few_buttons(message)

    def _process_media(self):
        url_media = (
            self.fragment.file.url if self.fragment.file
            else self.fragment.media_url)
        if not url_media:
            return

        url_media = url_media
        self.response.message_multimedia(
            url_media=url_media,
            media_type=self.fragment.media_type or "image",
            fragment_id=self.fragment.pk)

    def process(self):
        if not self.fragment.fragment_type == "message":
            self._process_other_type()
            return

        if self.reply_message and self.fragment.body:
            self._process_reply_message()

        elif self.fragment.media_type:
            self._process_media()

        elif self.fragment.body:
            self.response.message_text(
                self.fragment.body, fragment_id=self.fragment.pk)

    def _process_other_type(self):
        from services.processor.behavior import BehaviorProcessor
        from services.processor.piece import PieceProcessor

        if self.fragment.fragment_type == "behavior":
            if not self.fragment.behavior_id:  # type: ignore
                raise Exception(
                    f"El fragmento {self.fragment} no tiene un comportamiento asociado"
                )
            behavior_processor = BehaviorProcessor(
                self.fragment.behavior_id, self.response, self.parameters)  # type: ignore
            behavior_processor.process()

        elif self.fragment.fragment_type == "embedded":
            if not self.fragment.embedded_piece:
                raise Exception(
                    f"La pieza embebida en {self.fragment} no existe"
                )
            piece_processor = PieceProcessor(
                self.fragment.embedded_piece, self.response, self.parameters)
            piece_processor.process()

        elif self.fragment.fragment_type == "media":
            if not self.fragment.persistent_media:
                raise Exception(
                    f"El fragmento {self.fragment} no tiene un multimedia "
                    "persistente asociado"
                )
            media_id = self.fragment.persistent_media.get_media_id()
            if not media_id:
                raise Exception(
                    f"El media persistente asociado al fragmento {self.fragment} "
                    "no tiene un id asociado")
            self.response.message_multimedia(
                media_type=self.fragment.persistent_media.media_type,
                media_id=media_id,
                fragment_id=self.fragment.pk
            )
