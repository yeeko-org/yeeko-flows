from typing import Optional

from django.conf import settings
import requests
from services.request import InputAccount, RequestAbc
from services.request.message_model import (
    InteractiveMessage, EventMessage, TextMessage
)


def set_status_read(
    message_id: str,
    phone_number_id: str,
    token: Optional[str],
) -> None:
    if not token:
        return

    FACEBOOK_API_VERSION = getattr(settings, 'FACEBOOK_API_VERSION', 'v13.0')
    base_url = f'https://graph.facebook.com/{FACEBOOK_API_VERSION}'
    url = f"{base_url}/{phone_number_id}/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    message_data = {
        "message_id": message_id,
        "messaging_product": "whatsapp",
        "status": "read",
    }
    _ = requests.post(url, headers=headers, json=message_data)


class WhatsAppRequest(RequestAbc):
    raw_data: dict
    data: dict

    def __init__(self, raw_data: dict) -> None:
        super().__init__(raw_data, platform="whatsapp")
        self._contacs_data = {}

    def _get_input_account(self, change: dict) -> Optional[InputAccount]:
        value = change.get("value", {})
        metadata = value.get("metadata", {})
        pid = metadata.get("phone_number_id")

        try:
            input_account = self.get_input_account(
                pid, raw_data=change)
        except Exception as e:
            self.api_record.add_error(
                {"method": "get_input_account", "change": change}, e=e
            )
            return

        try:
            self._full_contact(change)
        except Exception as e:
            self.api_record.add_error(
                {"method": "_full_contact",  "change": change}, e=e
            )

        return input_account

    def _full_contact(self, change: dict) -> None:
        value = change.get("value", {})
        contacts = value.get("contacts", [])
        for contact in contacts:
            profile = contact.get("profile")
            sender_id = contact.get("wa_id")
            profile["phone"] = contact.get("wa_id")
            profile["user_field_filter"] = "phone"
            self._contacs_data.setdefault(
                sender_id, {
                    "sender_id": sender_id,
                    "contact": profile
                }
            )

    def _set_messages(
        self, change: dict, input_account: InputAccount
    ) -> None:
        value = change.get("value", {})
        messages = value.get("messages", [])
        for message in messages:
            sender_id = message.get("from")
            member_data = self._contacs_data.get(sender_id, {})

            try:
                input_sender = input_account\
                    .get_input_sender(sender_id, member_data)

            except Exception as e:
                data_error = {
                    "method": "get_input_sender",
                    "value.messages.message": message
                }
                input_account.api_record.add_error(data_error, e=e)
                continue

            message_class = self.data_to_class(message)
            set_status_read(
                message_class.message_id, input_account.account.pid,
                input_account.account.token
            )
            input_sender.messages.append(message_class)

    def _set_statuses(self, change: dict, input_account: InputAccount) -> None:
        value = change.get("value", {})
        statuses = value.get("statuses", [])
        for status_data in statuses:
            sender_id = status_data.get("recipient_id")
            status_data["type"] = "state"
            member_data = self._contacs_data.get(sender_id, {})
            data_error = {"status_data": status_data}

            try:
                input_sender = input_account\
                    .get_input_sender(sender_id, member_data)

            except Exception as e:
                input_account.api_record.add_error(
                    data_error | {"method": "get_input_sender"}, e=e
                )
                continue

            try:

                input_sender.messages.append(
                    self._create_state_notification(status_data)
                )
            except Exception as e:
                input_account.api_record.add_error(
                    data_error | {"method": "create_state_notification"}, e=e
                )

    def sort_data(self):
        entry = self.raw_data.get("entry", [])
        self._use_global_api_record = False if len(entry) > 1 else True
        for current_entry in entry:

            for change in current_entry.get("changes", []):
                input_account = self._get_input_account(change)
                if not input_account:
                    continue

                self._set_messages(change, input_account)
                self._set_statuses(change, input_account)

    def data_to_class(
        self, data: dict
    ) -> TextMessage | InteractiveMessage | EventMessage:
        type = data.get("type")
        if type == "text":
            message = self._create_text_message(data)
        elif type == "interactive":
            message = self._create_interactive_message(data)
        elif type in ["state", "reaction"]:
            message = self._create_state_notification(data)
        else:
            raise ValueError(f"Message type {type} not supported")

        if context := data.get("context", {}):
            message.context_id = context.get("id")
        return message

    def _create_text_message(self, data: dict) -> TextMessage:
        text = data.get("text", {}).get("body")
        message_id = data.get("id", "")
        timestamp = data.get("timestamp", 0)
        return TextMessage(
            text=text,
            message_id=message_id,
            timestamp=int(timestamp)
        )

    def _create_interactive_message(self, data: dict) -> InteractiveMessage:
        interactive = data.get("interactive", {})
        button_reply: dict = interactive.get(interactive.get("type"), {})
        interactive = InteractiveMessage(
            message_id=data.get("id", ""),
            timestamp=int(data.get("timestamp", 0)),
            title=button_reply.get("title"),
            payload=button_reply.get("id", ""),
        )
        interactive.get_built_reply()
        return interactive

    def _create_state_notification(self, status_data: dict) -> EventMessage:
        type_status = status_data.get("type")

        if type_status == "reaction":
            reaction_data: dict = status_data.get("reaction", {})
            message_id = reaction_data.get("message_id")
            emoji = reaction_data.get("emoji")
            status = "reaction"
        else:
            message_id = status_data.get("id") or ""
            status = status_data.get("status") or ""
            emoji = None

        timestamp = status_data.get("timestamp") or 0
        return EventMessage(
            message_id=message_id,
            timestamp=timestamp,
            status=status,
            emoji=emoji
        )
