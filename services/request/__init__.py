from abc import abstractmethod
import time
from typing import List, Optional

from django.utils import timezone
from yeeko_abc_message_models import request as y_request

from infrastructure.member.models import MemberAccount
from infrastructure.place.models import Account
from infrastructure.service.models import ApiRecord, InteractionType, Platform


from services.request.message_model import (
    InteractiveMessage, EventMessage, MediaMessage, TextMessage)
from services.user_manager import MemberAccountManager


def get_member_account(
    sender_id: str, account: Account, member_data: dict
) -> MemberAccount:
    member_manager = MemberAccountManager(
        account=account,
        sender_id=sender_id,
        **member_data.get("contact", {})
    )
    try:
        member_account = member_manager.get_member_account()
    except Exception as e:
        raise ValueError(f"MemberAccount {sender_id} problem: {e}")

    return member_account


class InputSender(y_request.InputSender):
    member: MemberAccount
    messages: List[TextMessage | InteractiveMessage |
                   EventMessage | MediaMessage]

    def __init__(
            self, sender_id: str, account: Account, member_data: Optional[dict]
    ) -> None:
        self.member = get_member_account(
            sender_id, account,  member_data or {}
        )
        super().__init__(sender_id, member_data or {})


class InputAccount(y_request.InputAccount):
    account: Account
    api_record: ApiRecord

    def __init__(
        self, account: Account, raw_data: dict,
        api_record: Optional[ApiRecord] = None
    ) -> None:
        self.account = account
        self.api_record = api_record or self._create_api_record()

        super().__init__(raw_data, account.pid)

    def _create_api_record(self) -> ApiRecord:
        return ApiRecord.objects.create(
            platform=self.account.platform,
            body=self.raw_data,
            is_incoming=True,
            created=timezone.now(),
            interaction_type=InteractionType.objects.get(
                name="default", way="in")
        )

    def create_input_sender(
        self, uid: str, sender_data: dict
    ) -> InputSender:
        member = InputSender(
            sender_id=uid, member_data=sender_data, account=self.account)
        self.members.append(member)
        return member


class RequestAbc(y_request.RequestAbc):

    platform_name: str
    api_record: ApiRecord
    input_accounts: List[InputAccount]

    def __init__(
            self, raw_data: dict, platform_name: str = "",
            debug: bool = True
    ) -> None:
        """
        The implementation of the class must be set platform_name by super
            super().__init__(raw_data, platform_name="whatsapp")
        Args:
        """
        self.platform_name = platform_name
        self._contacts_data = {}
        self._use_global_api_record = False

        self.record_request()
        super().__init__(raw_data, debug=debug)

        self._record_metadata()

    def _record_metadata(self) -> None:
        # Post init method, when all the accounts, users and messages are
        # already available, if the service allows it, the message statuses
        # are sent here and the media is downloaded.
        pass

    def record_request(self):
        self.timestamp_server = int(time.time())

        default_interactiontype, _ = InteractionType.objects.get_or_create(
            name="default", way="in")

        platform = Platform.objects.get(name=self.platform_name)

        self.api_record = ApiRecord.objects.create(
            platform=platform,
            body=self.raw_data,
            is_incoming=True,
            created=timezone.now(),
            interaction_type=default_interactiontype
        )

    def create_input_account(self, pid: str, raw_data: dict) -> InputAccount:
        api_record = self.api_record if self._use_global_api_record else None
        try:
            account = Account.objects.get(pid=pid)
        except Account.DoesNotExist:
            raise ValueError(f"Account {pid} not found")

        input_account = InputAccount(
            account=account, raw_data=raw_data, api_record=api_record
        )
        self.input_accounts.append(input_account)
        return input_account

    def data_to_class(
        self, data: dict
    ) -> TextMessage | InteractiveMessage | EventMessage | MediaMessage:
        # for a implentated class y_request.RequestAbc
        message = super().data_to_class(data)  # type: ignore

        # this return de Custom models with more methods
        if isinstance(message, y_request.TextMessage):
            return TextMessage(**message.dict())
        elif isinstance(message, y_request.InteractiveMessage):
            interactive = InteractiveMessage(**message.dict())
            interactive.get_built_reply()
            return interactive
        elif isinstance(message, y_request.EventMessage):
            return EventMessage(**message.dict())
        elif isinstance(message, y_request.MediaMessage):
            return MediaMessage(**message.dict())

        raise ValueError("Message not found")
