

from abc import ABC

from infrastructure.member.models import InviteExtension
from services.message_templates.template_out import MessageTemplateOutAbstract
from utilities.standard_phone import standard_mx_phone


class InviteExtensionManagerAbstract(ABC):
    invitation: InviteExtension
    message_template_manager: MessageTemplateOutAbstract
    marked_values: dict = {}

    def __init__(
            self, invitation: InviteExtension,
            message_template_manager: MessageTemplateOutAbstract,
            marked_values: dict = None
    ) -> None:
        if marked_values is None:
            self.marked_values = {}
        else:
            self.marked_values = marked_values.copy()
        self.invitation = invitation
        self.message_template_manager = message_template_manager

    def make_invitation_by_phone(self):
        if not self.invitation.phone:
            raise ValueError("Phone is required")

        try:
            phone = standard_mx_phone(self.invitation.phone)
        except Exception as e:
            self.add_error(f"Phone {self.invitation.phone} error: {e}")
            return

        self.message_template_manager.marked_values = self.marked_values
        send_mid = self.message_template_manager.send_message(phone_to=phone)

        api_record = self.message_template_manager.api_record

        if not send_mid:
            self.invitation.phone_error_request = api_record
            self.invitation.save()
            return

    def add_error(self, error: str):
        if isinstance(self.invitation.other_data, dict):
            self.invitation.other_data.update({"error": error})
        elif isinstance(self.invitation.other_data, list):
            self.invitation.other_data.append({"error": error})
        else:
            self.invitation.other_data = {"error": error}  # type: ignore

        self.invitation.save()
