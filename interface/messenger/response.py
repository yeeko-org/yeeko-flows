
from typing import Optional
from infrastructure.service.models import ApiRecord
from services.response import ResponseAbc
import requests

from yeeko_abc_message_models.messenger import response


class MessengerResponse(ResponseAbc, response.MessengerResponse):

    def _base_data(
            self, recipient_id: str, message_body: dict,
            fragment_id: Optional[int] = None, **kwargs
    ) -> dict:
        data = super()._base_data(recipient_id, message_body)
        data["_fragment_id"] = fragment_id
        return data

    def send_message(
        self, message_data: dict
    ) -> ApiRecord:

        url = f"{self.base_url}/me/messages"
        headers = {
            "Authorization": f"Bearer {self.account_token}",
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
