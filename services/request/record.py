"""
La intencion de esta clase, no es sobreescribir ni extender la clase RequestAbc

Se tomara la respuesta de la libreria como base y se reajustaran los datos para
realizar los registros apropiados y proporcionarle a flowmanager una estructura
mas adecuada para el manejo de los datos.
"""


from abc import ABC, abstractmethod
import time
from typing import List, Optional

from django.utils import timezone
from yeeko_abc_message_models import request as y_request

from infrastructure.member.models import MemberAccount
from infrastructure.place.models import Account
from infrastructure.service.models import ApiRecord, InteractionType, Platform

from services.request.message_model import (
    EventMessage, InteractiveMessage, MediaMessage, TextMessage, model_to_model)
from services.user_manager import MemberAccountManager


class InputSender:
    member: MemberAccount
    messages: List[
        TextMessage | InteractiveMessage | EventMessage | MediaMessage]

    api_record: ApiRecord

    def __init__(
            self, sender_id: str, account: Account, api_record: ApiRecord,
            member_data: y_request.SenderData,
            user_field_filter: Optional[str] = None
    ) -> None:
        member_manager = MemberAccountManager(
            account=account,
            sender_id=sender_id,
            name=member_data.name,
            phone=member_data.phone,
            email=member_data.email,
            user_field_filter=user_field_filter
        )
        try:
            self.member = member_manager.get_member_account()
        except Exception as e:
            raise ValueError(f"MemberAccount {sender_id} problem: {e}")

        self.messages = []
        self.api_record = api_record


class RecordRequestAbc(ABC):

    platform_name: str
    api_record: ApiRecord
    input_senders: List[InputSender]
    request: y_request.RequestAbc

    def __init__(
            self, request: y_request.RequestAbc, platform_name: str = ""
    ) -> None:

        self.platform_name = platform_name
        self.request = request
        self.input_senders = []
        self._use_global_api_record = len(request.input_accounts) == 1

        self._api_record_request()

        if request.errors:
            self.api_record.add_errors(request.errors)

        for input_account in request.input_accounts:
            try:
                account = Account.objects.get(pid=input_account.pid)
            except Account.DoesNotExist:
                self.api_record.add_error({
                    "error": "pid not found, Account.DoesNotExist",
                    "pid": input_account.pid})
                continue
            self._process_input_account(input_account, account)

    def _api_record_request(self):
        self.timestamp_server = int(time.time())

        default_interactiontype, _ = InteractionType.objects.get_or_create(
            name="default", way="in")

        platform = Platform.objects.get(name=self.platform_name)

        self.api_record = ApiRecord.objects.create(
            platform=platform,
            body=self.request.raw_data,
            is_incoming=True,
            created=timezone.now(),
            interaction_type=default_interactiontype
        )

    def _get_api_record(self, input_acount: y_request.InputAccount):
        if self._use_global_api_record:
            return self.api_record
        else:
            return ApiRecord.objects.create(
                platform=self.api_record.platform,
                interaction_type=self.api_record.interaction_type,
                body=input_acount.raw_data,
                is_incoming=True,
                created=timezone.now(),
            )

    def _process_input_account(
            self, input_acount: y_request.InputAccount, account: Account
    ):
        api_record = self._get_api_record(input_acount)
        messages_ids = []  # for mark as read
        senders_ids = []  # for mark as read

        for member in input_acount.members:
            input_sender = InputSender(
                sender_id=member.uid,
                account=account,
                api_record=api_record,
                member_data=member.sender_data
            )

            senders_ids.append(member.uid)

            for message in member.messages:
                messages_ids.append(message.message_id)

                try:
                    message = model_to_model(message)
                except ValueError as e:
                    api_record.add_error({"error": "model_to_model"}, e=e)
                    continue

                if isinstance(message, MediaMessage) and account.token:
                    self.get_media_content(message, account.token)

                input_sender.messages.append(message)

            self.input_senders.append(input_sender)

        senders_ids = list(set(senders_ids))
        messages_ids = list(set(messages_ids))

        if account.token:
            self.mark_as_read(
                account.pid, account.token,
                messages_ids=messages_ids,  uids=senders_ids
            )

    @abstractmethod
    def get_media_content(self, message: MediaMessage, token: str):
        raise NotImplementedError

    @abstractmethod
    def mark_as_read(
            self, pid: str, token: str,
            messages_ids: List[str] | None = None, uids: List[str] | None = None
    ):
        raise NotImplementedError
