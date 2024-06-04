from typing import List, Optional
from infrastructure.box.models import Fragment, Reply
from infrastructure.talk.models import BuiltReply
from services.response.abstract import ResponseAbc
from services.response.models import Button, Header, ReplyMessage, SectionHeader
from utilities.parameters import replace_parameter, update_parameters


def fragment_reply(
        reply: Reply, parameters: dict = {}
) -> Button | SectionHeader | None:
    title = reply.title or f"Opción {reply.order}"

    if reply.is_section:
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

    def replace(self, text: str) -> str:
        return replace_parameter(self.parameters, text)

    def header_from_fragment(self) -> Optional[Header | str]:
        if self.fragment.media_type:
            value = (
                self.fragment.file.url if self.fragment.file
                else self.fragment.media_url
            )
            if value:
                return Header(type=self.fragment.media_type, value=value)

        if self.fragment.header:
            return self.replace(self.fragment.header)

        return

    def process_reply_message(self):
        header = self.header_from_fragment()

        footer = self.replace(
            self.fragment.footer) if self.fragment.footer else None

        message = ReplyMessage(
            header=header,
            body=self.replace(self.fragment.body or ""),
            footer=footer,
            fragment_id=self.fragment.pk
        )

        for reply in self.reply_message:
            button = fragment_reply(reply, self.parameters)
            if not button:
                continue
            message.buttons.append(button)

        if message.has_sections() or len(message.buttons) > 3:
            self.response.message_many_buttons(message)
        else:
            self.response.message_few_buttons(message)

    def process_media(self):
        url_media = (
            self.fragment.file.url if self.fragment.file
            else self.fragment.media_url)
        if not url_media:
            return

        url_media = self.replace(url_media)
        self.response.message_multimedia(
            url_media=url_media,
            media_type=self.fragment.media_type or "image",
            fragment_id=self.fragment.pk)

    def process(self):
        if self.reply_message and self.fragment.body:
            self.process_reply_message()

        elif self.fragment.media_type:
            self.process_media()

        elif self.fragment.body:
            self.response.message_text(self.replace(
                self.fragment.body), fragment_id=self.fragment.pk)
