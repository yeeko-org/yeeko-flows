from typing import Optional

from infrastructure.box.models import Fragment, Piece, Reply
from services.notification.member_manager import NotificationManager
from services.processor.destination_rules import destination_find
from services.processor.fragment import FragmentProcessor
from services.processor.base_mixin import DestinationProcessorMixin
from services.response import ResponseAbc

# Enough for any honest chain of message-only pieces in one reply; past it,
# a «next» is going round in a circle.
MAX_NEXT_HOPS = 10


class PieceProcessor(DestinationProcessorMixin):
    piece: Piece
    response: ResponseAbc
    parameters: dict

    def __init__(
            self, piece: Piece, response: ResponseAbc,
            parameters: dict = {}
    ) -> None:
        self.piece = piece
        self.response = response
        self.parameters = parameters

    def process(self):
        from services.processor.behavior import FINISHED

        if self.piece.insistent:
            self.add_insistent_notification()

        if self.piece.piece_type == "destinations":
            self.process_destination()
            return

        # Slot fragments are sent by the piece's behavior when it needs
        # them, never by showing the piece.
        fragments = self.piece.fragments.filter(
            slot__isnull=True).order_by('order')
        finished = False
        for fragment in fragments:
            try:
                result = self.process_fragment(fragment)
            except Exception as e:
                self.response.add_error({}, e)
                continue
            finished = finished or result == FINISHED

        if finished or self.expects_nothing():
            self.follow_next()

    def expects_nothing(self) -> bool:
        """A content piece with no buttons, capture, behavior or embedded
        piece has nothing to wait for once shown."""
        if self.piece.piece_type != "content" or self.piece.written_id:
            return False
        visible = self.piece.fragments.filter(slot__isnull=True)
        if visible.filter(fragment_type__in=["behavior", "embedded"]).exists():
            return False
        return not Reply.objects.filter(fragment__in=visible).exists()

    def follow_next(self) -> bool:
        """Follows the piece's own destinations, if it has any. Returns
        whether it went somewhere."""
        self.get_destination()
        if not self.destination:
            return False
        if self.response.next_hops >= MAX_NEXT_HOPS:
            self.response.add_error({
                "method": "follow_next", "piece": self.piece.pk,
                "error": f"more than {MAX_NEXT_HOPS} «next» in one reply"})
            return False
        self.response.next_hops += 1
        self._go_to_destination()
        return True

    def get_destination(self) -> None:
        self.destination = destination_find(
            self.piece.get_destinations(),
            self.response.sender.member,
            self.response.platform_name,
            raise_exception=False)

    def process_fragment(self, fragment: Fragment) -> Optional[str]:
        fragment_processor = FragmentProcessor(
            fragment, self.response, self.parameters)
        return fragment_processor.process()

    def add_insistent_notification(self):
        NotificationManager.add_notification(
            "insistent", self.response.sender, piece=self.piece.pk
        )
