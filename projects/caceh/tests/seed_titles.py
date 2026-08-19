"""Resuelve títulos de botón contra el seed ya sembrado.

Los e2e contestan un botón mandando su título como texto, así que cualquier
pasada de copy los tumbaba. Aquí el test declara la INTENCIÓN (de qué pieza a
qué pieza, o con qué extra asignado) y el título se lee del `Reply` que el
seed dejó en la BD; el copy puede cambiar sin tocar las pruebas.
"""
from infrastructure.box.models import Reply


def title_of(piece: str, dest: str | None = None, **assigns: str) -> str:
    """Título del botón de `piece` que lleva a `dest` y/o asigna `assigns`
    (nombre de extra = valor). Exige un único match: dos botones a la misma
    pieza (a_duerme) se distinguen por lo que asignan."""
    qs = Reply.objects.filter(fragment__piece__name=piece, deleted=False)
    if dest:
        qs = qs.filter(destinations__piece_dest__name=dest)
    for name, value in assigns.items():
        qs = qs.filter(assignments__extra__name=name,
                       assignments__extra_value=value)
    titles = sorted(set(qs.values_list("title", flat=True)))
    if len(titles) != 1:
        raise LookupError(
            f"title_of({piece!r}, {dest!r}, {assigns}) -> {titles}")
    return titles[0]
