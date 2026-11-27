from typing import Optional

from infrastructure.box.models import Piece
from infrastructure.member.models import MemberAccount
from infrastructure.talk.models import Interaction


class ContextMixing:
    context_direct: bool
    context_piece: Optional[Piece] = None
    last_interaction_out: Optional[Interaction] = None
    # The message the person quoted, if any, and the last message with a
    # fragment the bot sent, i.e. where the conversation really is. On a
    # quote, `last_interaction_out` is the quoted one, not the active one.
    quoted_interaction: Optional[Interaction] = None
    active_interaction: Optional[Interaction] = None

    def calculate_context_piece(
            self, sender: MemberAccount, context_id: Optional[str] = None
    ):
        self.calculate_interactions(sender, context_id)
        if self.context_piece:
            return
        self.context_piece = None
        self.context_direct = False
        if context_id:
            self.last_interaction_out = self.quoted_interaction

            self.context_piece = Piece.objects.filter(
                fragments__interaction__mid=context_id).first()
            if self.context_piece:
                self.context_direct = True
        else:
            self.last_interaction_out = Interaction.objects.filter(
                member_account=sender, is_incoming=False)\
                .order_by("created").last()

            if self.last_interaction_out and self.last_interaction_out.fragment:
                self.context_piece = self.last_interaction_out.fragment.piece

    def calculate_interactions(
            self, sender: MemberAccount, context_id: Optional[str] = None
    ):
        self.quoted_interaction = None
        if context_id:
            self.quoted_interaction = Interaction.objects.filter(
                mid=context_id, member_account=sender).first()
        self.active_interaction = Interaction.objects.filter(
            member_account=sender, is_incoming=False,
            fragment__isnull=False).order_by("created").last()

    @property
    def active_piece(self) -> Optional[Piece]:
        if not self.active_interaction:
            return None
        return self.active_interaction.fragment.piece  # type: ignore
