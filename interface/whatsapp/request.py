from typing import List
from services.request import InputAccount, InputSender, RequestAbc
from services.request.message_model import (
    InteractiveMessage, EventMessage, TextMessage
)


class WhatsAppRequest(RequestAbc):
    raw_data: dict
    data: dict
    errors: List[tuple[str, dict]]

    def __init__(self, raw_data: dict) -> None:
        super().__init__(raw_data, platform="whatsapp")
        self._contacs_data = {}

    def _get_request_account(self, change: dict) -> InputAccount:
        value = change.get("value", {})
        metadata = value.get("metadata", {})
        pid = metadata.get("phone_number_id")
        return self.get_input_account(pid)

    def _full_contact(self, change: dict) -> None:
        value = change.get("value", {})
        contacts = value.get("contacts", [])
        for contac in contacts:
            profile = contac.get("profile")
            sender_id = contac.get("wa_id")
            profile["phone"] = contac.get("wa_id")
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
        mesages = value.get("messages", [])
        for message in mesages:
            sender_id = message.get("from")
            try:
                member_message = self.get_input_sender(
                    sender_id, input_account=input_account
                )
            except Exception as e:
                self.errors.append(
                    ("Error getting input sender", {"error": str(e)})
                )
                continue

            member_message.messages.append(self.data_to_class(message))

    def sort_data(self):
        entry = self.raw_data.get("entry", [])
        for current_entry in entry:

            for change in current_entry.get("changes", []):
                try:
                    input_account = self._get_request_account(change)
                except Exception as e:
                    self.errors.append(
                        ("Error getting request account", {"error": str(e)})
                    )
                    continue
                self._full_contact(change)
                self._set_messages(change, input_account)

    def data_to_class(
        self, data: dict
    ) -> TextMessage | InteractiveMessage | EventMessage:
        type = data.get("type")
        if type == "text":
            return self._create_text_message(data)
        elif type == "interactive":
            return self._create_interactive_message(data)
        elif type == "state":
            return self._create_state_notification(data)
        else:
            raise ValueError(f"Message type {type} not supported")

    def _create_text_message(self, data: dict) -> TextMessage:
        text = data.get("text", {}).get("body")
        message_id = data.get("id", "")
        timestamp = data.get("timestamp", 0)
        return TextMessage(text=text, message_id=message_id, timestamp=int(timestamp))

    def _create_interactive_message(self, data: dict) -> InteractiveMessage:
        raise NotImplementedError

    def _create_state_notification(self, data: dict) -> EventMessage:
        raise NotImplementedError
