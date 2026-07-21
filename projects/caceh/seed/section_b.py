"""§B · Jornada y descanso."""
from infrastructure.box.models import Piece

from services.seeder import FlowSeeder


def wire(sdr: FlowSeeder, p: dict[str, Piece]) -> None:
    # B2 ⚙️ ia_extrae (genérico) esquema jornada -> bifurcación ia_completed.
    sdr.behavior_step(
        p["b_ia_jornada"], "ia_extrae", p["b_checa_jornada"], generic=True,
        params={"esquema": "jornada", "entrada": "{{respuesta_jornada}}"})

    sdr.capture(
        p["b_jornada_abierta"],
        "Hablemos de los días y horarios. ¿Qué días trabajas y en qué "
        "horario? Escríbelo con tus palabras. 😉 Ej.: \"de lunes a "
        "viernes, de 8 a 4\".",
        "respuesta_jornada", p["b_ia_jornada"])

    sdr.bifurcation(
        p["b_checa_jornada"], "ia_completed",
        [("no", p["b_repregunta_jornada"])],
        default_dest=p["b_bifurca_descanso"])

    sdr.capture(
        p["b_repregunta_jornada"], "{{ia_pregunta}}",
        "respuesta_jornada", p["b_ia_jornada"])

    # B5: el descanso solo se pregunta en entrada por salida; en planta la
    # SÉPTIMA va fija por ley y salta directo a confirmar.
    sdr.bifurcation(
        p["b_bifurca_descanso"], "tipo_contrato",
        [("entrada_salida", p["b_descanso_abierta"])],
        default_dest=p["b_confirma_jornada"])

    # B7 ⚙️ ia_extrae descanso -> confirma (el esquema no da ia_completed,
    # así que no hay loop de repregunta; la validación ≥30 min queda como
    # mejora posterior).
    sdr.behavior_step(
        p["b_ia_descanso"], "ia_extrae", p["b_confirma_jornada"],
        generic=True,
        params={"esquema": "descanso", "entrada": "{{respuesta_descanso}}"})

    sdr.capture(
        p["b_descanso_abierta"],
        "Durante la jornada, ¿cuál será el tiempo de descanso y qué "
        "alimentos se le dan en ese rato? Ej.: \"1 hora, y se le da "
        "comida\". ☕",
        "respuesta_descanso", p["b_ia_descanso"])

    sdr.buttons(p["b_confirma_jornada"], (
        "Quedó así, échale un ojo 👀\n🗓️ Días: {{dias_laborables}}\n"
        "🕗 Horario: de {{hora_entrada}} a {{hora_salida}}"), [
        ("Sí, así es", p["c_relacion_previa"], None),
        ("Corregir", p["b_jornada_abierta"], None),
    ])
