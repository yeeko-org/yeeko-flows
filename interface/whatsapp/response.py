
from typing import Any, Dict, Optional
from django.conf import settings
from infrastructure.service.models import ApiRecord
from services.response import ResponseAbc
import requests

from services.response.models import Message, Section, SectionsMessage, ReplyMessage

FACEBOOK_API_VERSION = getattr(settings, 'FACEBOOK_API_VERSION', 'v13.0')


class WhatsAppResponse(ResponseAbc):
    base_url: str = f'https://graph.facebook.com/{FACEBOOK_API_VERSION}'

    def _base_data(
            self, type_str: str, body: Optional[dict] = None,
            fragment_id: Optional[int] = None
    ) -> dict:
        uid = self.sender.uid or ""
        if uid.startswith("521"):
            uid = "52" + uid[3:]
        return {
            "messaging_product": "whatsapp",
            "to": uid,
            "type": type_str,
            type_str: body,
            "_fragment_id": fragment_id,
        }

    def text_to_data(
            self, message: str, fragment_id: Optional[int] = None
    ) -> dict:
        if not isinstance(message, str):
            raise ValueError(
                f'Message {message} must be a string, not {type(message)}'
            )
        return self._base_data("text", {"body": message}, fragment_id)

    def multimedia_to_data(
        self, url_media: str, media_id: str, media_type: str, caption: Optional[str] = None,
        fragment_id: Optional[int] = None
    ) -> dict:
        if media_type not in ["image", "video", "audio", "file", "document", "sticker"]:
            raise ValueError(
                f"Media type {media_type} must be in "
                "['image', 'video', 'audio', 'file']"
            )
        
        if not url_media and not media_id:
            raise ValueError("You must provide either url_media or media_id")

        body = {"caption": caption} if caption else {}
        if media_id:
            body["id"] = media_id
        if url_media:
            body["link"] = url_media

        return self._base_data(media_type, body, fragment_id)

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
            for button in message.get_only_buttons()[:3]
        ]
        interactive = self._message_to_data(message, header_supp_media=True)
        interactive.update({
            "type": "button",
            "action": {
                "buttons": buttons
            }
        })

        whatsapp_data_message = self._base_data(
            "interactive", interactive, fragment_id=message.fragment_id)

        whatsapp_data_message["uuid_list"] = [
            button.payload for button in message.get_only_buttons()[:3]]

        return whatsapp_data_message

    def _section_to_data(self, section: Section) -> dict:
        return {
            "title": section.title,
            "rows": [
                {
                    "id": item.payload,
                    "title": item.title,
                    "description": item.description or "",
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
        return self._base_data(
            "interactive", interactive, fragment_id=message.fragment_id)

    def many_buttons_to_data(self, message: ReplyMessage) -> dict:

        interactive = self._message_to_data(message)

        sections = message.get_section(
            default_title="Opciones:", available_button_space=10
        )
        interactive.update({
            "type": "list",
            "action": {
                "button": message.button_text[:20],
                "sections": [
                    self._section_to_data(section)
                    for section in sections[:10]
                ],
            }
        })

        whatsapp_data_message = self._base_data(
            "interactive", interactive, fragment_id=message.fragment_id)

        whatsapp_data_message["uuid_list"] = []

        for section in sections[:10]:
            for item in section.buttons:
                whatsapp_data_message["uuid_list"].append(item.payload)

        return whatsapp_data_message

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
