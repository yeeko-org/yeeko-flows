
from infrastructure.assign.models import ApplyBehavior

from services.response import ResponseAbc

from django.db.models import Q

from utilities.parameters import update_parameters


class BehaviorProcessor:
    behavior: str
    response: ResponseAbc
    apply_behavior: ApplyBehavior
    parameters: dict

    def __init__(
            self, behavior: str, response: ResponseAbc, parameters: dict = {}
    ) -> None:
        self.behavior = behavior
        self.response = response
        self.parameters = parameters

        apply_behavior = ApplyBehavior.objects\
            .filter(behavior__name=behavior)\
            .filter(
                Q(space=response.sender.account.space) |
                Q(space__isnull=True)
            ).order_by('-space').first()

        if not apply_behavior:
            raise Exception(
                f"No se encontró el comportamiento implementado: {behavior}"
            )

        self.apply_behavior = apply_behavior

    def process(self):
        from services.processor.piece_processor import PieceProcessor
        if not self.apply_behavior.main_piece:
            self.process_behavior_code()
            return

        piece_processor = PieceProcessor(
            piece=self.apply_behavior.main_piece, response=self.response
        )
        piece_processor.process()

    def process_behavior_code(self):
        from services import behavior
        behavior_class = getattr(behavior, self.behavior, None)
        if not behavior_class:
            raise Exception(
                f"No se encontró la clase de comportamiento: {self.behavior}")

        parameters = update_parameters(
            self.apply_behavior.values, self.parameters)  # type: ignore
        parameters['response'] = self.response

        behavior_code = behavior_class(**parameters)
