
from typing import Any, Dict, Optional
from django.conf import settings
from infrastructure.service.models import ApiRecord
from services.response import ResponseAbc
import requests

from services.response.models import Message, Section, SectionsMessage, ReplyMessage

FACEBOOK_API_VERSION = getattr(settings, 'FACEBOOK_API_VERSION', 'v13.0')


class WhatsAppResponse(ResponseAbc):
    base_url: str = f'https://graph.facebook.com/{FACEBOOK_API_VERSION}'

    def _base_data(self, type_str: str, body: Optional[dict] = None) -> dict:
        uid = self.sender.uid or ""
        if uid.startswith("521"):
            uid = "52" + uid[3:]
        return {
            "messaging_product": "whatsapp",
            "to": uid,
            "type": type_str,
            type_str: body,
        }

    def text_to_data(self, message: str) -> dict:
        if not isinstance(message, str):
            raise ValueError(
                f'Message {message} must be a string, not {type(message)}'
            )
        return self._base_data("text", {"body": message})

    def multimedia_to_data(
        self, url_media: str, media_type: str, caption: Optional[str] = None
    ) -> dict:
        if media_type not in ["image", "video", "audio", "file"]:
            raise ValueError(
                f"Media type {media_type} must be in "
                "['image', 'video', 'audio', 'file']"
            )
        body = {"link": url_media, "caption": caption}
        return self._base_data(media_type, body)

    def _message_to_data(
            self, message: Message, header_supp_media=False
    ) -> dict:
        data: Dict[str, Any] = {
            "body": {"text": message.body}
        }
        if message.header:
            if isinstance(message.header, str):
                value = message.header
                type = "image" if value.startswith("https") else "text"
            else:
                value = message.header.value
                type = message.header.type

            if not header_supp_media:
                type = "text"

            if type == "text":
                value = value[:60]
            else:
                value = {"link": value}

            data["header"] = {
                "type": type,
                type: value
            }
        if message.footer:
            data["footer"] = {"text": message.footer}
        return data

    def few_buttons_to_data(self, message: ReplyMessage) -> dict:
        buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": button.payload,
                    "title": button.title,
                }
            }
            for button in message.buttons[:3]
        ]
        interactive = self._message_to_data(message, header_supp_media=True)
        interactive.update({
            "type": "button",
            "action": {
                "buttons": buttons
            }
        })
        return self._base_data("interactive", interactive)

    def _section_to_data(self, section: Section) -> dict:
        return {
            "title": section.title,
            "rows": [
                {
                    "id": item.payload,
                    "title": item.title,
                }
                for item in section.buttons[:10]
            ]
        }

    def sections_to_data(self, message: SectionsMessage) -> dict:

        sections = []
        for section in message.sections[:10]:
            sections.append(self._section_to_data(section))

        interactive = self._message_to_data(message)
        interactive.update({
            "type": "list",
            "action": {
                "button": message.button_text[:20],
                "sections": sections,
            }
        })
        return self._base_data("interactive", interactive)

    def many_buttons_to_data(self, message: ReplyMessage) -> dict:

        interactive = self._message_to_data(message)
        interactive.update({
            "type": "list",
            "action": {
                "button": message.button_text[:20],
                "sections": [
                    self._section_to_data(
                        Section(title="buttons", buttons=message.buttons)
                    )
                ],
            }
        })
        return self._base_data("interactive", interactive)

    def get_mid(self, body: Dict | None) -> str | None:
        if not body:
            return None
        messages = body.get("messages") or []
        if not messages:
            return None
        return messages[0].get("id")

    def send_message(
        self, message_data: dict, api_request: Optional[ApiRecord] = None
    ) -> ApiRecord:

        url = f"{self.base_url}/{self.sender.account.pid}/messages"
        headers = {
            "Authorization": f"Bearer {self.sender.account.token}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, json=message_data)
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"body": response.text}

        return ApiRecord.objects.create(
            platform=self.sender.account.platform,
            body=message_data,
            interaction_type_id="default",
            is_incoming=False,
            response_status=response.status_code,
            response_body=response_body,
        )
