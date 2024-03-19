from abc import ABC, abstractmethod
import time
from typing import List, Optional
from infrastructure.member.models import MemberAccount
from infrastructure.place.models import Account
from infrastructure.service.models import ApiRequest, InteractionType


from services.request.message_model import (
    InteractiveMessage, EventMessage, TextMessage
)
from services.user_manager import MemberAccountManager
from django.utils import timezone


class MemberMessages:
    messages: List[TextMessage | InteractiveMessage | EventMessage]
    member: MemberAccount
    errors: List[tuple[str, dict]]

    def __init__(self, member: MemberAccount) -> None:
        self.member = member
        self.messages = []
        self.errors = []


class AccountMembers:
    account: Account
    members: List[MemberMessages]
    errors: List[tuple[str, dict]]
    raw_data: dict

    def __init__(self, account: Account) -> None:
        self.account = account
        self.members = []
        self.errors = []

    def get_member(self, sender_id: str) -> Optional[MemberMessages]:
        for member in self.members:
            if member.member.uid == sender_id:
                return member
        return None


class RequestAbc(ABC):
    raw_data: dict
    data: dict
    accounts: List[AccountMembers]
    errors: List[tuple[str, dict]]

    def __init__(
            self, raw_data: dict, platform: Optional[str] = None,
            set_messages: bool = True
    ) -> None:
        self.raw_data = raw_data
        self.platform = platform
        self.data = {}
        self.accounts = []
        self.errors = []
        if not set_messages:
            return
        self.record_request()
        self.sort_data()
        self.get_accounts()

        self.get_members()
        self.set_messages()

    def get_account_members(self, pid: str) -> Optional[AccountMembers]:
        for account in self.accounts:
            if account.account.pid == pid:
                return account

        return None

    def record_request(self):
        self.timestamp_server = int(time.time())
        default_interactiontype, _ = InteractionType.objects.get_or_create(
            name="default", way="in")
        self.api_request = ApiRequest(
            platform_id=self.platform,
            body=self.raw_data,
            is_incoming=True,
            created=timezone.now(),
            interaction_type=default_interactiontype
        )
        self.api_request.save()

    def get_accounts(self):
        delete_keys = []
        for pid in self.data.keys():
            try:
                self.data[pid]["account"] = Account.objects.get(pid=pid)
            except Account.DoesNotExist:
                self.errors.append(
                    (f"Account {pid} not found", self.data[pid].copy())
                )
                delete_keys.append(pid)
        for key in delete_keys:
            del self.data[key]

    def get_account(self, pid: str) -> Account:
        try:
            return Account.objects.get(pid=pid)
        except Account.DoesNotExist:
            raise ValueError(f"Account {pid} not found")

    def get_members(self):
        for pid in self.data.keys():
            account = self.data[pid]["account"]
            for member_data in self.data[pid]["members"]:
                self.get_member_account(account, member_data)

    def get_member_account(self, account, member_data: dict):
        sender_id = member_data.get("sender_id", "")
        member_manager = MemberAccountManager(
            account=account,
            sender_id=sender_id,
            **member_data.get("contact", {})
        )
        try:
            member_account = member_manager.get_member_account()
        except Exception as e:
            self.errors.append((
                f"MemberAccount {sender_id} problem: {e}",
                member_data.copy()
            ))
            del member_data
            return
        member_data["member_account"] = member_account

    def set_messages(self):
        for pid in self.data.keys():
            account_members = AccountMembers(account=self.data[pid]["account"])
            self.accounts.append(account_members)

            for member_data in self.data[pid]["members"]:
                member_messages = MemberMessages(
                    member=member_data["member_account"]
                )
                account_members.members.append(member_messages)

                for message_data in member_data["messages"]:
                    try:
                        message_class = self.data_to_class(message_data)
                    except Exception as e:
                        self.errors.append((
                            f"Message {message_data} problem: {e}",
                            message_data.copy()
                        ))
                        continue
                    if self.message_check_v4(message_class):
                        # "Recibimos otra vez algo que ya estaba registrado"
                        continue
                    member_messages.messages.append(message_class)

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
