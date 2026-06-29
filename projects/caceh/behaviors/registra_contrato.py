"""registra_contrato — crea el Contract (la constancia) y cierra el flujo
(pieza E6).

Es el núcleo del producto: guarda un snapshot de todos los extras del miembro
con fecha y hora como prueba de que la relación laboral existió. Escribe el
folio en {{registro_id}} y fija {{flujo_completado}}=completo (lo que cancela N1
y dispara N2).
"""
from infrastructure.persistent_media.models import Media
from projects.caceh.models import Contract
from projects.caceh.behaviors.base import CacehBehaviorBase


class RegistraContratoBehavior(CacehBehaviorBase):
    behavior_name = "registra_contrato"

    def run(self) -> None:
        tipo = self._read("tipo_contrato")
        trab = self._read("trab_nombre_completo")
        empl = self._read("empl_nombre_completo")

        if not tipo or not trab or not empl:
            self.response.add_error({
                "behavior": self.behavior_name,
                "message": "faltan tipo_contrato, trab o empl_nombre_completo"})
            return

        # genera_pdf (E5) corre antes; si dejó el Media, lo ligamos a la
        # constancia. Si falta, el contrato igual se registra (pdf=None).
        pdf_pk = self._read("pdf_contrato")
        pdf = Media.objects.filter(pk=pdf_pk).first() if pdf_pk else None

        contract = Contract.objects.create(
            member=self.member,
            account=self.account,
            tipo_contrato=tipo,
            trab_nombre=trab,
            empl_nombre=empl,
            data=self.data,
            pdf=pdf,
        )

        self._write("registro_id", contract.folio)
        self._write("flujo_completado", "completo")
