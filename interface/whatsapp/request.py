from typing import List
from services.request import RequestAbc
from services.request.message_model import (
    InteractiveMessage, EventMessage, TextMessage
)


class WhatsAppRequest(RequestAbc):
    raw_data: dict
    data: dict
    errors: List[tuple[str, dict]]

    def __init__(self, raw_data: dict) -> None:
        super().__init__(raw_data, platform="whatsapp")

    def sort_data(self):
        entry = self.raw_data.get("entry", [])
        for current_entry in entry:
            pid = current_entry.get("id")
            self.data.setdefault(pid, {})
            full_contacs = {}

            for change in current_entry.get("changes", []):
                value = change.get("value", {})
                metadata = value.get("metadata", {})
                pid = metadata.get("phone_number_id")
                self.data.setdefault(pid, {})
                full_contacs =self.data[pid].get("members", {})
                mesages = value.get("messages", [])
                contacts = value.get("contacts", [])

                for contac in contacts:
                    profile = contac.get("profile")
                    sender_id = contac.get("wa_id")
                    profile["phone"] = contac.get("wa_id")
                    profile["user_field_filter"] = "phone"
                    full_contacs.setdefault(
                        sender_id, {
                            "sender_id": sender_id,
                            "contact": profile,
                            "messages": []
                        }
                    )

                for message in mesages:
                    sender_id = message.get("from")
                    full_contacs[sender_id]["messages"].append(message)

                self.data[pid]["members"] = list(full_contacs.values())

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
