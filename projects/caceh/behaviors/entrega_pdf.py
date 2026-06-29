"""entrega_pdf — manda el PDF ya generado por WhatsApp (pieza E7).

Behavior thin: el fragmento `media` del motor apunta a un persistent_media fijo,
pero este PDF es por-usuario. Lee {{pdf_contrato}} (pk del Media que dejó
genera_pdf), recupera el Media y lo envía como documento.
"""
from infrastructure.persistent_media.models import Media
from projects.caceh.behaviors.base import CacehBehaviorBase


class EntregaPdfBehavior(CacehBehaviorBase):
    behavior_name = "entrega_pdf"

    def run(self) -> None:
        pk = self._read("pdf_contrato")
        if not pk:
            self.response.add_error({
                "behavior": self.behavior_name,
                "message": "no hay pdf_contrato que entregar"})
            return

        media = Media.objects.filter(pk=pk).first()
        if not media:
            self.response.add_error({
                "behavior": self.behavior_name, "pdf_contrato": pk,
                "message": "Media no encontrado"})
            return

        self.response.message_multimedia(
            media_type="document", media_id=media.get_media_id())
