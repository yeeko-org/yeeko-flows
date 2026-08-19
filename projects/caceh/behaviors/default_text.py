"""default_text — qué contesta el bot ante un texto que no esperaba.

El motor llama a este behavior (`services/processor/text.py`) cuando un mensaje
escrito no casó con nada: ni comando, ni captura pendiente, ni título de botón.
Sin él sembrado, el bot enmudece; con él, el silencio se acaba tanto a media
conversación como al terminar un contrato («Hola» tras la despedida).

**Por qué no basta con una pieza fija.** La forma barata de sembrar
`default_text` es un `ApplyBehavior` con `main_piece`: el motor rinde esa pieza
y ya. El problema es que el motor no guarda sesión — reconstruye «dónde va la
persona» desde su última interacción de salida (`calculate_context_piece`)—, así
que una pieza fija se vuelve el contexto y la pregunta que estaba pendiente deja
de poder contestarse por texto. La cura dejaría varada a la usuaria justo donde
hoy solo hay silencio.

Por eso este behavior avisa y **vuelve a rendir la pieza donde estaba**: la
persona ve otra vez la pregunta (con sus botones) y el contexto queda donde
debía. Si acababa de terminar, lo que se repite es la despedida, con su botón de
empezar otro contrato.

Las capturas de texto libre no llegan aquí: `process_written` corre antes y una
Written acepta cualquier texto (`services/processor/written.py`), así que un
nombre o una jornada se guardan sin pasar por este camino.
"""
from typing import Optional

from infrastructure.box.models import Piece
from infrastructure.talk.models import Interaction
from projects.caceh.behaviors.base import CacehBehaviorBase
from services.processor.piece import PieceProcessor

AVISO = ("No entendí ese mensaje. 🙈\n\n"
         "Te repito lo último que te mandé, para que lo contestes ahí mismo.")


class DefaultTextBehavior(CacehBehaviorBase):
    behavior_name = "default_text"

    def run(self) -> None:
        self.response.message_text(AVISO)
        piece = self._piece_pendiente()
        if not piece:
            # Sin salida previa con fragmento no hay nada que repetir; el
            # aviso solo ya rompe el silencio.
            return
        PieceProcessor(piece, self.response).process()

    def _piece_pendiente(self) -> Optional[Piece]:
        # Misma derivación que calculate_context_piece, pero exigiendo
        # fragmento: un mensaje suelto (p. ej. el PDF) no ubica ninguna pieza.
        last = (Interaction.objects
                .filter(member_account=self.response.sender,
                        is_incoming=False, fragment__isnull=False)
                .order_by("created").last())
        return last.fragment.piece if last else None
