import json

from abc import abstractmethod, ABC
from typing import List

from infrastructure.box.models import (
    Fragment, Piece, PlatformTemplate, TemplateParameter
)
from infrastructure.member.models import MemberAccount
from infrastructure.place.models import Account
from infrastructure.service.models import ApiRecord, InteractionType
from infrastructure.talk.models import BuiltReply, Interaction, Trigger
from services.response.models import ReplyMessage
from services.user_manager import MemberAccountManager
from utilities.standard_phone import standard_mx_phone


class MessageTemplateOutAbstract(ABC):
    piece: Piece
    account: Account
    fragment: Fragment
    template: PlatformTemplate
    template_parameters: List[TemplateParameter]

    member_account: MemberAccount | None = None
    phone_to: str | None = None

    marked_values: dict = {}
    reply_uuids: list = []
    api_record: ApiRecord | None = None

    message_display: ReplyMessage = ReplyMessage(body="")

    def __init__(
            self,
            account: Account,
            piece: Piece | None = None,
            template: PlatformTemplate | None = None,
    ) -> None:
        self.account = account
        if not piece and not template:
            raise ValueError("Piece or template are required")
        if piece:
            self._init_by_piece(piece)
        if template:
            self._init_by_template(template)

        self._get_fragment()

        self.template_parameters = list(
            self.template.parameters.all().order_by("order"))

    def _init_by_piece(self, piece: Piece):
        self.piece = piece
        try:
            self.template = PlatformTemplate.objects.get(piece=self.piece)
        except PlatformTemplate.DoesNotExist:
            raise ValueError(f"Piece {self.piece} must have a template")

    def _init_by_template(self, template: PlatformTemplate):
        self.template = template
        if not self.template.piece:
            raise ValueError(f"Template {self.template} must have a piece")
        self.piece = self.template.piece

    def _get_fragment(self):
        query_fragment = Fragment.objects.filter(piece=self.piece)
        query_fragment_count = query_fragment.count()
        if query_fragment_count != 1:
            raise ValueError(
                f"Piece {self.piece} must have one fragment, found {query_fragment_count}")
        fragment = query_fragment.first()
        if not fragment:
            raise ValueError(f"Piece {self.piece} must have a fragment")
        self.fragment = fragment

    @abstractmethod
    def make_message(self) -> dict:
        """Make the message from the piece"""
        raise NotImplementedError

    @abstractmethod
    def send_message(self, phone_to: str | None) -> str | None:
        raise NotImplementedError

    def set_member_account(self):
        if self.member_account:
            return

        if not self.phone_to:
            raise ValueError("Phone to is required")
        try:
            self.phone_to = standard_mx_phone(self.phone_to)
        except Exception as e:
            raise ValueError(f"Phone {self.phone_to} error: {e}")

        member_account_manager = MemberAccountManager(
            account=self.account,
            sender_id=self.phone_to,
            phone=self.phone_to
        )

        self.member_account = member_account_manager.get_member_account()

    def record_interaction(self, mid):
        self.set_member_account()

        interaction_type = InteractionType.objects.get_or_create(
            name="invite",
            wey="out"
        )

        self.message_display.replace_text(self.marked_values)

        message_display = json.loads(self.message_display.model_dump_json())

        trigger = Trigger()
        trigger.is_direct = True
        trigger.template = self.template
        trigger.save()

        interaction = Interaction.objects.create(
            mid=mid,
            interaction_type=interaction_type,
            member_account=self.member_account,
            is_incoming=False,
            api_record_out=self.api_record,
            fragment=self.fragment,
            raw_data=message_display,
            trigger=trigger
        )

        BuiltReply.objects.filter(uuid__in=self.reply_uuids).update(
            interaction=interaction)
