"""§D · Actividades y tabulador + §E · Cierre v1: PDF y registro."""
from infrastructure.box.models import Piece

from projects.caceh import tabulador
from services.seeder import FlowSeeder

# Flow con description por opción (multiselect_desc.flow.json), publicado
# en Meta el 2026-07-09. Si se vuelve None se cae al Flow genérico (solo
# id/title, inmutable) y se recortan las descripciones, porque su schema
# no las declara.
FLOW_ID_DESC = "2057389525199733"
_FLOW_ID_LEGACY = "1308618661432871"


def wire(sdr: FlowSeeder, p: dict[str, Piece]) -> None:
    # D1 ☑️ los 20 items del tabulador; el submit escribe la lista
    # de ids en {{actividades}} y avanza directo a D4 (deriva_categoria
    # murió: ya no hay categorías, la regla es max en calcula_tabulador).
    options = tabulador.opciones()
    if not FLOW_ID_DESC:
        options = [{"id": o["id"], "title": o["title"]} for o in options]
    sdr.wa_form_step(
        p["d_actividades"], p["d_check_tabulador"],
        flow_id=FLOW_ID_DESC or _FLOW_ID_LEGACY,
        body="¿Cuáles actividades realiza la persona trabajadora? 🧹",
        extra="actividades", min=1,
        options=options)

    # D4: el tabulador nace ENCENDIDO; "no" es el apagador de config.
    sdr.bifurcation(
        p["d_check_tabulador"], "tabulador_activo",
        [("no", p["e_resumen"])],
        default_dest=p["d_calcula_tabulador"])

    # D5 -> D6: el behavior escribe {{salario_sugerido}} y {{salario_bajo}}
    # (y manda la imagen del nivel si está bajo); D6 solo enruta.
    sdr.behavior_step(p["d_calcula_tabulador"], "calcula_tabulador",
                      p["d_checa_salario"])
    sdr.bifurcation(
        p["d_checa_salario"], "salario_bajo",
        [("si", p["d_sugerencia"])],
        default_dest=p["e_resumen"])

    sdr.buttons(p["d_sugerencia"], (
        "El pago que me contaste queda abajo del tabulador de CACEH para "
        "esas actividades: lo sugerido es ${{salario_sugerido}} al día "
        "(arriba te mandé la tabla). 📊\n\n"
        "¿Quieres que una asesora de CACEH te contacte para definir un "
        "sueldo más justo?"), [
        ("Sí, contactar", p["d_contacto"],
         {"enviar_contacto_caceh": "si"}),
        ("Dejarlo así", p["e_resumen"], None),
    ])

    sdr.msg(p["d_contacto"], (
        "Va. 💚 En los próximos días alguien de CACEH te va a escribir "
        "para ayudarles a definir un salario más justo. Sigamos con el "
        "contrato."))
    sdr.link(p["d_contacto"], p["e_resumen"])

    # §E en orden: E5 arma el PDF y deja {{pdf_contrato}}; E6 lo lee para
    # ligar el Media a la constancia y fija flujo_completado; E7 lo envía.
    sdr.behavior_step(p["e_genera_pdf"], "genera_pdf", p["e_registra"])
    sdr.behavior_step(p["e_registra"], "registra_contrato",
                      p["e_entrega_pdf"])
    sdr.behavior_step(p["e_entrega_pdf"], "entrega_pdf",
                      p["e_despedida"])

    sdr.buttons(p["e_resumen"], (
        "Esto es lo que tengo. Échale un último ojo 👀\n"
        "👥 {{trab_nombre_completo}} y {{empl_nombre_completo}}\n"
        "📄 Contrato {{tipo_contrato}}\n"
        "🗓️ {{dias_laborables}}, de {{hora_entrada}} a {{hora_salida}}\n"
        "🏠 {{lt_calle}} {{lt_ext}}, col. {{lt_colonia}}, "
        "{{lt_municipio}}, {{lt_estado}}\n"
        "💵 ${{salario_diario}} al día, pago en {{modo_pago}}\n"
        "🖊️ Se firma en {{ciudad_firma}}, con fecha de hoy"), [
        ("Todo correcto", p["e_genera_pdf"], None),
        ("Corregir algo", p["e_corrige"], None),
    ])

    # E4 corrección por IA (task-27): texto libre -> corrige_por_ia escribe
    # los extras corregidos -> se recalcula el diario y el veredicto del
    # tabulador (sin aviso) -> el resumen se re-pinta. Si la persona quiere
    # cambiar actividades se reabre el Flow de D1, cuya cadena ya desemboca
    # en el resumen.
    sdr.capture(
        p["e_corrige"],
        "Dime qué está mal y cómo debe quedar. Escríbelo con tus palabras. "
        "Puedes incluir todas las correcciones en un solo mensaje: nombres, "
        "montos, actividades, horarios, lugar de trabajo, etc.",
        "respuesta_correccion", p["e_ia_corrige"])
    sdr.behavior_step(
        p["e_ia_corrige"], "corrige_por_ia", p["e_checa_correccion"])
    sdr.bifurcation(
        p["e_checa_correccion"], "ia_completed",
        [("no", p["e_repregunta_correccion"])],
        default_dest=p["e_recalcula"])
    sdr.capture(
        p["e_repregunta_correccion"], "{{ia_pregunta}}",
        "respuesta_correccion", p["e_ia_corrige"])
    # El diario se recalcula siempre (también antes de reabrir actividades,
    # por si en el mismo texto cambió el pago); el tabulador, solo en la
    # ruta de texto: la de actividades ya lo recorre con D4-D6.
    sdr.behavior_step(
        p["e_recalcula"], "calcula_salario_diario",
        p["e_bifurca_correccion"])
    sdr.bifurcation(
        p["e_bifurca_correccion"], "correccion_destino",
        [("actividades", p["d_actividades"])],
        default_dest=p["e_recalcula_tabulador"])
    sdr.behavior_step(
        p["e_recalcula_tabulador"], "calcula_tabulador", p["e_resumen"],
        params={"silencioso": "si"})

    sdr.buttons(p["e_despedida"], (
        "Imprímanlo dos veces y fírmenlo: quien emplea, la persona "
        "trabajadora y un testigo. Guarda bien tu copia: es tu "
        "comprobante. 💚\n\n"
        "Si necesitas otro contrato, con otra persona, aquí sigo."), [
        ("Hacer otro contrato", p["e_reinicia"], None),
    ])

    # E10: el behavior borra los datos del contrato anterior y el embedded
    # rinde el saludo, así que la persona reaparece en A1 desde cero
    # (adr-0013: una sesión, un contrato; nada se acumula).
    sdr.behavior_step(p["e_reinicia"], "reinicia_contrato", p["a_saludo"])
