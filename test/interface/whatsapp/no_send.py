import secrets
import base64

from typing import Optional

from infrastructure.service.models import ApiRecord
from interface.whatsapp.request import WhatsAppRequest
from interface.whatsapp.response import WhatsAppResponse


def random_wamid():
    prefix = "wamid."
    random_bytes = secrets.token_bytes(32)
    base64_str = base64.urlsafe_b64encode(
        random_bytes).decode('utf-8').rstrip('=')
    return prefix + base64_str


class WhatsAppResponseNoSend(WhatsAppResponse):

    def send_message(
        self, message_data: dict, api_request: Optional[ApiRecord] = None
    ) -> ApiRecord:

        response_body = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "525555555555", "wa_id": "5215555555555"}],
            "messages": [
                {"id": random_wamid()}
            ]
        }

        return ApiRecord.objects.create(
            platform=self.sender.account.platform,
            body=message_data,
            interaction_type_id="default",
            is_incoming=False,
            response_status=200,
            response_body=response_body,
        )


class WhatsAppRequestNoSend(WhatsAppRequest):
    def _set_status_read(self, message_id, pid, token) -> None:
        pass
