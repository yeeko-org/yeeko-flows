from infrastructure.box.models import Fragment, Piece
from services.processor.behavior import BehaviorProcessor
from services.processor.destination_rules import destination_find
from services.processor.fragment import FragmentProcessor
from services.processor.base_mixin import DestinationProcessorMixin
from services.response import ResponseAbc


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
        if self.piece.insistent:
            self.add_insistent_notification()

        if self.piece.piece_type == "destinations":
            self.process_destination()
            return

        fragments = self.piece.fragments.order_by('order')
        for fragment in fragments:
            try:
                self.process_fragment(fragment)
            except Exception as e:
                self.response.add_error({}, e)

    def get_destination(self) -> None:
        self.destination = destination_find(
            self.piece.get_destinations(),
            self.response.sender.member,
            self.response.platform_name,
            raise_exception=False)

    def process_fragment(self, fragment: Fragment):
        fragment_processor = FragmentProcessor(
            fragment, self.response, self.parameters)
        fragment_processor.process()

    def add_insistent_notification(self):
        self.response.notification_manager.add_notification(
            "insistent", self.response.sender, piece=self.piece.pk
        )
