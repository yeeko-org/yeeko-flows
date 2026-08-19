"""calcula_tabulador — salario sugerido y aviso de salario bajo (pieza D5).

Regla cerrada con CACEH (2026-07-08): el salario sugerido es el MÁXIMO de
los items marcados en D1 y el aviso solo se dispara si el salario pactado
queda debajo por más de MARGEN_MXN. La comparación numérica vive aquí
porque el motor solo bifurca por igualdad (ConditionRule): se escribe
{{salario_bajo}} = "si"/"no" y D6 enruta por ese valor.

Cuando hay aviso, este mismo behavior manda la imagen del nivel (patrón de
entrega_pdf). El Media se crea perezosamente desde
projects/caceh/assets/tablas/<name>.png la primera vez; si el PNG aún no
está en el repo, se registra el faltante sin romper el turno (la
sugerencia de D7 sale igual, solo sin imagen).
"""
from pathlib import Path

from django.core.files.base import ContentFile

from infrastructure.persistent_media.models import Media
from projects.caceh import tabulador
from projects.caceh.behaviors.base import CacehBehaviorBase

_ASSETS = Path(__file__).resolve().parents[1] / "assets" / "tablas"


class CalculaTabuladorBehavior(CacehBehaviorBase):
    behavior_name = "calcula_tabulador"

    def run(self) -> None:
        actividades = self._read("actividades") or []
        salarios = [tabulador.SALARIOS[a] for a in actividades
                    if a in tabulador.SALARIOS]
        if not salarios:
            # Sin actividades reconocidas: no hay referencia -> sin aviso.
            self._write("salario_bajo", "no")
            return

        sugerido = max(salarios)
        # :g evita el "904.0" en el copy de D7 y conserva el 342.47.
        self._write("salario_sugerido", f"{sugerido:g}")

        try:
            diario = float(self._read("salario_diario"))
        except (TypeError, ValueError):
            self.response.add_error({
                "behavior": self.behavior_name,
                "message": "salario_diario ausente o no numérico"})
            self._write("salario_bajo", "no")
            return

        bajo = diario < sugerido - tabulador.MARGEN_MXN
        self._write("salario_bajo", "si" if bajo else "no")
        # silencioso="si" (E4 recálculo tras corregir): el veredicto se
        # reescribe pero el aviso no se muestra, y la imagen es parte de él.
        if bajo and self.params.get("silencioso") != "si":
            self._envia_imagen(sugerido)

    def _envia_imagen(self, sugerido: float) -> None:
        name = tabulador.IMAGENES.get(sugerido)
        media = Media.objects.filter(
            account=self.account, name=name).first()
        if not media:
            media = self._crea_media(name)
        media_id = media.get_media_id() if media else None
        if not media_id:
            self.response.add_error({
                "behavior": self.behavior_name, "imagen": name,
                "message": "imagen del tabulador no disponible"})
            return
        self.response.message_multimedia(
            media_type="image", media_id=media_id,
            fragment_id=self.params.get("fragment_id"))

    def _crea_media(self, name: str) -> Media | None:
        png = _ASSETS / f"{name}.png"
        if not png.exists():
            return None
        media = Media(
            account=self.account, media_type="image", name=name,
            file=ContentFile(png.read_bytes(), name=png.name))
        media.save()
        return media
