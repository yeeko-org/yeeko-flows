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

        # get_media_id puede regresar None (subida a WhatsApp fallida);
        # message_multimedia sin id lanza ValueError y NO está envuelto en
        # exception_handler: mataría el resto del turno (E7 y siguientes).
        media_id = media.get_media_id()
        if not media_id:
            self.response.add_error({
                "behavior": self.behavior_name, "pdf_contrato": pk,
                "message": "Media sin media_id: la subida a WhatsApp falló"})
            return

        self.response.message_multimedia(
            media_type="document", media_id=media_id,
            fragment_id=self.params.get("fragment_id"),
            filename="Contrato de trabajo del hogar.pdf")
