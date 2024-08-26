from infrastructure.box.models import Piece
from services.processor.piece import PieceProcessor
from services.response.abstract import ResponseAbc


class InsistentBehavior:
    def __init__(
            self, response: ResponseAbc, default_message=None,
            piece_pk=None, **kwargs
    ):
        try:
            piece = Piece.objects.get(pk=piece_pk)
        except Piece.DoesNotExist:
            response.add_error(
                {"piece": piece_pk, "message": "No se encontró la pieza"}
            )
            return
        if default_message:
            response.message_text(default_message)
        PieceProcessor(
            piece, response, kwargs
        ).process()
