from typing import List
from infrastructure.assign.models import ApplyBehavior, ParamValue
from infrastructure.box.models import Fragment, Piece, Reply
from infrastructure.member.models import MemberAccount
from infrastructure.service.models import ApiRecord
from services.processor.behavior_processor import BehaviorProcessor
from services.processor.fragment_processor import FragmentProcessor
from services.processor.processor_base import Processor
from services.response import ResponseAbc

from django.db.models import Q

from utilities.parameters import update_parameters


class PieceProcessor(Processor):
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
        fragments = self.piece.fragments.order_by('order')

        for fragment in fragments:
            try:
                self.process_fragment(fragment)
            except Exception as e:
                self.response.api_record_in.add_error({}, e)

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
