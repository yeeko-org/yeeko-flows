from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, field_serializer

from infrastructure.member.models import MemberAccount
from infrastructure.place.models import Account
from services.response.abstract import ResponseAbc
from services.response.models import Message
from utilities.standard_phone import standard_mx_phone


class SendOpenSessionMessageAbstract(ABC, BaseModel):
    phone_to: str
    account: Account
    message: str
    file_link: str | None = None
    file_type: str | None = None

    def get_member_account(self) -> MemberAccount | None:
        self.phone_to = standard_mx_phone(self.phone_to)
        try:
            return MemberAccount.objects.get(
                account=self.account, uid=self.phone_to)
        except MemberAccount.DoesNotExist:
            return None

    @abstractmethod
    def get_response(self) -> ResponseAbc:
        raise NotImplementedError

    def send_message(self) -> ResponseAbc:
        response = self.get_response()
        if not self.file_link:
            response.message_text(self.message)
        else:
            response.message_multimedia(
                self.file_type or "",
                url_media=self.file_link,
                caption=self.message)

        response.send_messages()

        return response

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        original_dump = super().model_dump(*args, **kwargs)
        if self.account:
            original_dump["account"] = str(self.account)
        return original_dump

    @field_serializer('account')
    def serialize_dt(self, account: Account | None, _info):
        if isinstance(account, Account):
            return account.pid
        return account

    class Config:
        arbitrary_types_allowed = True
