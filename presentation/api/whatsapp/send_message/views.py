from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from infrastructure.member.models import MemberAccount
from infrastructure.place.models import Account
from interface.whatsapp.send_message_simple import SendWhatsappSessionMessage
from utilities.storage_file import upload_file_to_storage
from utilities.standard_phone import standard_mx_phone

from .serializers import MessageBasicSerializer


class WhatsappSendSimpleMessage(ViewSet):
    serializer_class = MessageBasicSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        account = data.get("account")
        if not isinstance(account, Account):
            raise ValueError("Account must be an instance of Account")

        phone_to = data.get("phone_to")
        try:
            valid_phone = standard_mx_phone(phone_to)  # type: ignore
        except Exception as e:
            raise ValidationError(f"Phone {phone_to} error: {e}")

        try:
            member_account = MemberAccount.objects.get(
                account=account, uid=valid_phone)
        except MemberAccount.DoesNotExist:
            raise ValidationError(
                f"Account {account} and phone {phone_to} not found")
        file = data.get("file")
        file_type = data.get("file_type")
        file_url = None
        if file:
            path = f"whatsapp/free_message/{phone_to}"
            file_url = upload_file_to_storage(data.get("file"), sub_path=path)

        response_class = SendWhatsappSessionMessage(
            phone_to=valid_phone,
            account=account,
            message=data.get("body") or "",
            file_link=file_url,
            file_type=file_type
        ).send_message()

        api_record = response_class.api_record_in

        return Response({"message": "Message sent successfully"})
