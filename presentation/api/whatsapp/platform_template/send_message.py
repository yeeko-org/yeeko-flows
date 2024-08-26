from infrastructure.box.models import Piece, PlatformTemplate
from infrastructure.place.models import Account
from interface.whatsapp.message_template import MessageTemplate
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

from .serializers import MessageTemplateSerializer


class WhatsAppSendMessageTemplate(ViewSet):
    serializer_class = MessageTemplateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        account_id = data.get("account_id")
        account = Account.objects.get(pk=account_id)

        template_id = data.get("template_id")
        piece_id = data.get("piece_id")
        if not template_id and not piece_id:
            raise ValueError("Template or piece is required")

        template = None
        if template_id:
            template = PlatformTemplate.objects.get(pk=template_id)

        piece = None
        if piece_id:
            piece = Piece.objects.get(
                pk=piece_id, crate__flow__space=account.space)

        message_template = MessageTemplate(
            account=account,
            piece=piece,
            template=template,
        )
        message_template.markeds_values = data.get("markeds_values", {})
        mid = message_template.send_message(data.get("phone_to"))

        if not message_template.api_record:
            raise ValueError("Message not sent")

        return Response({
            "response_body": message_template.api_record.response_body,
            "response_status": message_template.api_record.response_status,
            "mid": mid,
        })
