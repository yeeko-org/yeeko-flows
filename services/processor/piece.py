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
        # self.parameters no actualiza porque values es un posible valor
        self.parameters = parameters

    def process(self):
        if self.piece.piece_type == "destinations":
            self.process_destination()
            return

        fragments = self.piece.fragments.order_by('order')
        for fragment in fragments:
            try:
                self.process_fragment(fragment)
            except Exception as e:
                self.response.api_record_in.add_error({}, e)

    def get_destination(self) -> None:
        self.destination = destination_find(
            self.piece.get_destinations(),
            self.response.sender.member,
            self.response.platform_name,
            raise_exception=False)

    def process_fragment(self, fragment: Fragment):
        if fragment.fragment_type == "message":
            fragment_processor = FragmentProcessor(
                fragment, self.response, self.parameters)
            fragment_processor.process()

        elif fragment.fragment_type == "behavior":
            if not fragment.behavior_id:  # type: ignore
                raise Exception(
                    f"El fragmento {fragment} no tiene un comportamiento asociado"
                )
            behavior_processor = BehaviorProcessor(
                fragment.behavior_id, self.response)  # type: ignore
            behavior_processor.process()

        elif fragment.fragment_type == "embedded":
            if not fragment.embedded_piece:
                raise Exception(
                    f"La pieza embebida en {fragment} no existe"
                )
            piece_processor = PieceProcessor(
                fragment.embedded_piece, self.response, self.parameters)
            piece_processor.process()

        elif fragment.fragment_type == "media":
            if not fragment.persistent_media:
                raise Exception(
                    f"El fragmento {fragment} no tiene un multimedia "
                    "persistente asociado"
                )
            media_id=fragment.persistent_media.get_media_id()
            if not media_id:
                raise Exception(
                    f"El media persistente asociado al fragmento {fragment} "
                    "no tiene un id asociado")
            self.response.message_multimedia(
                media_type=fragment.persistent_media.media_type,
                media_id=media_id,
                fragment_id=fragment.pk
            )
