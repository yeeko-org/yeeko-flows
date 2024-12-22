from abc import ABC, abstractmethod
import time
from typing import List, Optional
from infrastructure.member.models import MemberAccount
from infrastructure.place.models import Account
from infrastructure.service.models import ApiRecord, InteractionType, Platform


from services.request.message_model import (
    InteractiveMessage, EventMessage, MediaMessage, TextMessage
)
from services.user_manager import MemberAccountManager
from django.utils import timezone


class InputSender:
    member: MemberAccount
    messages: List[TextMessage | InteractiveMessage |
                   EventMessage | MediaMessage]

    def __init__(
            self, sender_id: str, account: Account, member_data: Optional[dict]
    ) -> None:
        self.member = self.get_member_account(
            sender_id, account,  member_data or {}
        )

        self.messages = []

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

    def get_input_sender(
            self, sender_id: str, meta_dict: dict
    ) -> InputSender:
        input_sender = self.find_member(sender_id)
        if input_sender:
            return input_sender

        input_sender = InputSender(sender_id, self.account, meta_dict)
        self.members.append(input_sender)
        return input_sender

    def find_member(self, sender_id: str) -> Optional[InputSender]:
        return next((
            member for member in self.members
            if member.member.uid == sender_id
        ), None)


class RequestAbc(ABC):
    raw_data: dict
    input_accounts: List[InputAccount]
    platform_name: str
    api_record: ApiRecord

    def __init__(
            self, raw_data: dict, platform_name: str = "",
            set_messages: bool = True
    ) -> None:
        """
        The implementation of the class must be set platform_name by super
            super().__init__(raw_data, platform_name="whatsapp")
        Args:
        """
        self.raw_data = raw_data
        self.platform_name = platform_name
        self.input_accounts = []

        self._contacts_data = {}
        self._use_global_api_record = False

        if not set_messages:
            return

        self.record_request()
        try:
            self.sort_data()
        except Exception as e:
            self.api_record.add_error({"method": "sort_data"},  e=e)

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

    @abstractmethod
    def sort_data(self):
        raise NotImplementedError

    @abstractmethod
    def data_to_class(
        self, data: dict, pid, token
    ) -> TextMessage | InteractiveMessage | EventMessage | MediaMessage:
        raise NotImplementedError
