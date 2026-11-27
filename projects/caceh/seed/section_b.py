"""§B · Jornada y descanso."""
from infrastructure.box.models import Piece

from projects.caceh.seed.textos import NO_ENTENDI_DATO
from services.seeder import FlowSeeder


def wire(sdr: FlowSeeder, p: dict[str, Piece]) -> None:
    # B1: corregir los días recalcula el salario diario (derivados.py).
    sdr.unit(p["b_jornada_abierta"], "open_question", slots={
        "question": (
            "Hablemos de los días y horarios. ¿Qué días se trabaja y a qué "
            "hora se entra y se sale? Escríbelo con tus palabras. 😉 Ej.: "
            "\"de lunes a viernes, de 8am a 4pm\"."),
        "recap": "La jornada laboral quedó así: {{jornada_texto}}.",
        "correction_request": (
            "Por favor, escribe de nuevo qué días se trabaja y en qué "
            "horario."),
        "give_up": NO_ENTENDI_DATO,
    }, params={"schema": "jornada"})
    sdr.link(p["b_jornada_abierta"], p["b_bifurca_descanso"])

    # B5: el descanso solo se pregunta en entrada por salida; en planta la
    # OCTAVA va fija por ley.
    sdr.bifurcation(
        p["b_bifurca_descanso"], "tipo_contrato",
        [("entrada_salida", p["b_descanso_abierta"])],
        default_dest=p["c_relacion_previa"])

    sdr.unit(p["b_descanso_abierta"], "open_question", slots={
        "question": (
            "Durante la jornada, ¿cuál será el tiempo de descanso y qué "
            "alimentos se le dan en ese rato? Ej.: \"1 hora, y se le da "
            "comida\". ☕"),
        "recap": "El tiempo de descanso quedó así: {{descanso_texto}}.",
        "correction_request": (
            "Por favor, escribe de nuevo cuánto tiempo dura el descanso y si "
            "incluye alimentos."),
        "give_up": NO_ENTENDI_DATO,
    }, params={"schema": "descanso"})
    sdr.link(p["b_descanso_abierta"], p["c_relacion_previa"])
