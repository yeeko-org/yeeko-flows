from typing import Optional

from infrastructure.box.models import Piece
from infrastructure.member.models import MemberAccount
from infrastructure.talk.models import Interaction


class ContextMixing:
    context_direct: bool
    context_piece: Optional[Piece] = None
    last_interaction_out: Optional[Interaction] = None

    def calculate_context_piece(
            self, sender: MemberAccount, context_id: Optional[str] = None
    ):
        if self.context_piece:
            return
        self.context_piece = None
        self.context_direct = False
        if context_id:
            self.last_interaction_out = Interaction.objects.filter(
                mid=context_id, member_account=sender).first()

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
