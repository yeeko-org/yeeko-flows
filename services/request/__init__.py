from abc import ABC, abstractmethod
import time
from typing import List, Optional
from infrastructure.member.models import MemberAccount
from infrastructure.place.models import Account
from infrastructure.service.models import ApiRecord, InteractionType


from services.request.message_model import (
    InteractiveMessage, EventMessage, TextMessage
)
from services.user_manager import MemberAccountManager
from django.utils import timezone


class InputSender:
    member: MemberAccount
    messages: List[TextMessage | InteractiveMessage | EventMessage]

    def __init__(self, member: MemberAccount) -> None:
        self.member = member
        self.messages = []


class InputAccount:
    account: Account
    members: List[InputSender]
    statuses: List[EventMessage]
    raw_data: dict
    api_record: ApiRecord

    def __init__(
        self, account: Account, raw_data: dict,
        api_record: Optional[ApiRecord] = None
    ) -> None:
        self.account = account
        self.raw_data = raw_data
        self.members = []
        self.statuses = []
        if api_record:
            self.api_record = api_record
        else:
            self.api_record = self._create_api_record()

    def _create_api_record(self) -> ApiRecord:
        return ApiRecord.objects.create(
            platform=self.account.platform,
            body=self.raw_data,
            is_incoming=True,
            created=timezone.now(),
            interaction_type=InteractionType.objects.get(
                name="default", way="in")
        )

    def get_input_sender(self, sender_id: str) -> Optional[InputSender]:
        return next((
            member for member in self.members
            if member.member.uid == sender_id
        ), None)


class RequestAbc(ABC):
    raw_data: dict
    input_accounts: List[InputAccount]

    api_record: ApiRecord

    def __init__(
            self, raw_data: dict, platform: Optional[str] = None,
            set_messages: bool = True
    ) -> None:
        self.raw_data = raw_data
        self.platform = platform
        self.input_accounts = []

        self._contacs_data = {}
        self._use_global_api_record = False

        if not set_messages:
            return

        self.record_request()
        try:
            self.sort_data()
        except Exception as e:
            self.api_record.add_error(
                {
                    "error": str(e),
                    "method": "sort_data"
                },
                e=e
            )

    def record_request(self):
        self.timestamp_server = int(time.time())

        default_interactiontype, _ = InteractionType.objects.get_or_create(
            name="default", way="in")

        self.api_record = ApiRecord.objects.create(
            platform_id=self.platform,
            body=self.raw_data,
            is_incoming=True,
            created=timezone.now(),
            interaction_type=default_interactiontype
        )

    def get_account(self, pid: str) -> Account:
        try:
            return Account.objects.get(pid=pid)
        except Account.DoesNotExist:
            raise ValueError(f"Account {pid} not found")

    def get_input_account(
        self, pid: str, raw_data: dict
    ) -> InputAccount:
        for input_account in self.input_accounts:
            if input_account.account.pid == pid:
                return input_account

        api_record = self.api_record if self._use_global_api_record else None

        input_account = InputAccount(
            account=self.get_account(pid), raw_data=raw_data,
            api_record=api_record
        )

        self.input_accounts.append(input_account)
        return input_account

    def get_input_sender(
            self, sender_id: str, input_account: InputAccount
    ) -> InputSender:
        input_sender = input_account.get_input_sender(sender_id)
        if input_sender:
            return input_sender

        member_data = self._contacs_data.get(sender_id, {})
        member = self.get_member_account(
            sender_id, input_account.account,  member_data
        )
        input_sender = InputSender(member=member)
        input_account.members.append(input_sender)
        return input_sender

    def get_member_account(
            self, sender_id: str, account: Account, member_data: dict
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

    @abstractmethod
    def sort_data(self):
        raise NotImplementedError

    @abstractmethod
    def data_to_class(
        self, data: dict
    ) -> TextMessage | InteractiveMessage | EventMessage:
        raise NotImplementedError
