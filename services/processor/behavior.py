
from importlib import import_module
from typing import Optional
from infrastructure.assign.models import ApplyBehavior

from infrastructure.talk.models import Interaction
from services.response import ResponseAbc

from django.db.models import F, Q

from utilities.parameters import update_parameters


# What a behavior reports back by setting `result` on its instance. A
# behavior that sets nothing is treated as before: the engine does not move.
#   FINISHED: its work on the piece is done; the engine follows the piece's
#     «next».
#   HANDLED: it took care of the message and the piece stays where it is.
#   NOT_MINE: the text it was offered is not for it; the engine goes on
#     down its usual chain.
FINISHED = "finished"
HANDLED = "handled"
NOT_MINE = "not_mine"


class BehaviorNotFound(Exception):
    """No hay `ApplyBehavior` para ese nombre en el space (ni global). Se
    distingue de cualquier otro fallo para que un llamador pueda tratar
    un behavior como opcional sin tragarse errores reales del behavior."""


class BehaviorProcessor:
    behavior: str
    response: ResponseAbc
    apply_behavior: ApplyBehavior
    parameters: dict

    def __init__(
            self, behavior: str, response: ResponseAbc, parameters: dict = {},
            context_direct: bool = False,
            interaction_in: Optional[Interaction] = None,
    ) -> None:
        self.behavior = behavior
        self.response = response

        apply_behavior = ApplyBehavior.objects\
            .filter(behavior__name=behavior)\
            .filter(
                Q(space=response.sender.account.space) |
                Q(space__isnull=True)
            ).order_by(F('space').desc(nulls_last=True)).first()

        if not apply_behavior:
            raise BehaviorNotFound(
                f"No se encontró el comportamiento implementado: {behavior}"
            )

        self.apply_behavior = apply_behavior
        self.parameters = update_parameters(
            self.apply_behavior.values, parameters)  # type: ignore

        self.response.set_trigger(
            apply_behavior.behavior, context_direct,
            interaction_in=interaction_in)

    def process(self) -> Optional[str]:
        from services.processor.piece import PieceProcessor
        if not self.apply_behavior.main_piece:
            return self.process_behavior_code()

        # A behavior backed by a piece shows it, and the piece follows its
        # own «next»: nothing to report upwards.
        piece_processor = PieceProcessor(
            piece=self.apply_behavior.main_piece, response=self.response,
            parameters=self.parameters
        )
        piece_processor.process()
        return None

    def process_behavior_code(self) -> Optional[str]:
        behavior_class = self._resolve_behavior_class()
        if not behavior_class:
            raise Exception(
                f"No se encontró la clase de comportamiento: {self.behavior}")

        self.parameters['response'] = self.response

        instance = behavior_class(**self.parameters)
        return getattr(instance, "result", None)

    def _resolve_behavior_class(self):
        """Localiza la clase del behavior: primero entre los genéricos del
        motor (services.behavior); si no está, en la app de su Collection vía
        `app_label` (p. ej. projects.caceh.behaviors). Así el motor no importa
        los proyectos de forma estática: el código de dominio se ubica por el
        `app_label` que la colección declara en la BD."""
        from services import behavior as generic
        behavior_class = getattr(generic, self.behavior, None)
        if behavior_class:
            return behavior_class

        collection = self.apply_behavior.behavior.collection
        app_label = collection.app_label if collection else None
        if not app_label:
            return None
        module = import_module(f"{app_label}.behaviors")
        return getattr(module, self.behavior, None)
