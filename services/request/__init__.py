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
    errors: List[tuple[str, dict]]

    def __init__(self, member: MemberAccount) -> None:
        self.member = member
        self.messages = []
        self.errors = []


class InputAccount:
    account: Account
    members: List[InputSender]
    errors: List[tuple[str, dict]]
    raw_data: dict

    def __init__(
        self, account: Account, raw_data: Optional[dict] = None
    ) -> None:
        self.account = account
        self.raw_data = raw_data or {}
        self.members = []
        self.errors = []

    def get_input_sender(self, sender_id: str) -> Optional[InputSender]:
        for member in self.members:
            if member.member.uid == sender_id:
                return member
        return None


class RequestAbc(ABC):
    raw_data: dict
    data: dict
    input_accounts: List[InputAccount]
    errors: List[tuple[str, dict]]

    def __init__(
            self, raw_data: dict, platform: Optional[str] = None,
            set_messages: bool = True
    ) -> None:
        self.raw_data = raw_data
        self.platform = platform
        self.data = {}
        self.input_accounts = []
        self.errors = []
        self._contacs_data = {}
        if not set_messages:
            return
        self.record_request()
        self.sort_data()

    def get_account(self, pid: str) -> Account:
        try:
            return Account.objects.get(pid=pid)
        except Account.DoesNotExist:
            raise ValueError(f"Account {pid} not found")

    def get_input_account(
        self, pid: str, raw_data: Optional[dict] = None
    ) -> InputAccount:
        for input_account in self.input_accounts:
            if input_account.account.pid == pid:
                return input_account
        input_account = InputAccount(
            account=self.get_account(pid)
        )
        input_account.raw_data = raw_data or {}
        self.input_accounts.append(input_account)
        return input_account

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

    def get_input_sender(
            self, sender_id: str, input_account: InputAccount
    ) -> InputSender:
        member_message = input_account.get_input_sender(sender_id)
        if member_message:
            return member_message

        member_data = self._contacs_data.get(sender_id, {})
        member = self.get_member_account(
            sender_id, input_account.account,  member_data
        )
        member_message = InputSender(member=member)
        input_account.members.append(member_message)
        return member_message

    def record_request(self):
        self.timestamp_server = int(time.time())
        default_interactiontype, _ = InteractionType.objects.get_or_create(
            name="default", way="in")
        self.api_request = ApiRecord(
            platform_id=self.platform,
            body=self.raw_data,
            is_incoming=True,
            created=timezone.now(),
            interaction_type=default_interactiontype
        )
        self.api_request.save()

    def message_check_v4(self, message_class):
        return False
        # return UserMessengerCommit.objects\
        #     .filter(mid=message_class.message_id).exists()

    @abstractmethod
    def sort_data(self):
        raise NotImplementedError

    @abstractmethod
    def data_to_class(
        self, data: dict
    ) -> TextMessage | InteractiveMessage | EventMessage:
        raise NotImplementedError
