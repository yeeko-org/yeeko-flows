from infrastructure.service.models import ApiRecord, InteractionType
from services.message_simple.send_message import SendOpenSessionMessageAbstract
from interface.whatsapp.response import WhatsAppResponse


class SendWhatsappSessionMessage(SendOpenSessionMessageAbstract):
    def _get_interaction_type(self) -> InteractionType:
        interaction_type, _ = InteractionType.objects.get_or_create(
            name="whatsapp open session", way="out")
        return interaction_type

    def get_response(self) -> WhatsAppResponse:
        interaction_type, _ = InteractionType.objects.get_or_create(
            name="whatsapp open session", way="out")

        api_record_in = ApiRecord.objects.create(
            platform_id="whatsapp",
            body={
                "phone_to": self.phone_to,
                "message": self.message,
                "file_link": self.file_link,
                "file_type": self.file_type,
                "pid": self.account.pid,
            },
            interaction_type=interaction_type,
        )

        member_account = self.get_member_account()
        if not member_account:
            raise ValueError("Member not found")

        return WhatsAppResponse(
            sender=member_account,
            platform_name="whatsapp",
            api_record_in=api_record_in
        )
