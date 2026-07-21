"""§A · Entrada: partes y modalidad."""
from infrastructure.box.models import Piece

from services.seeder import FlowSeeder


def wire(sdr: FlowSeeder, p: dict[str, Piece]) -> None:
    # A5 ⚙️ asigna_partes (proyecto): reparte nombres por rol + teléfono.
    sdr.behavior_step(
        p["a_asigna_partes"], "asigna_partes", p["a_bifurca_operador"])

    sdr.buttons(p["a_saludo"], (
        "¡Hola! 👋 Soy Dignas firma, la asistente de CACEH para ayudarte "
        "a hacer tu contrato de trabajo del hogar.\n\nTe llevaré de la mano, "
        "paso a pasito; al final de nuestra conversación te lo entregaré "
        "listo para firmar."), [
        ("¿Qué es CACEH?", p["a_acerca"], None),
        ("¡Empecemos!", p["a_quien_eres"], None),
    ])

    sdr.msg(p["a_acerca"], (
        "CACEH es una organización de la sociedad civil que busca mejorar "
        "las condiciones laborales de las personas trabajadoras del hogar. "
        "Dignas firma te ayuda a crear un contrato con validez legal solo "
        "contestando unas preguntas."))
    sdr.embedded(p["a_acerca"], p["a_quien_eres"])

    sdr.buttons(p["a_quien_eres"],
                "¿Eres la persona trabajadora o quien emplea?", [
        ("Trabajadora", p["a_nombre_operador"], {
            "operador": "trabajadora",
            "etiqueta_contraparte": "empleadora",
            "pregunta_mayor_edad": "tienes 18 años o más"}),
        ("Empleadora", p["a_nombre_operador"], {
            "operador": "empleadora",
            "etiqueta_contraparte": "trabajadora",
            "pregunta_mayor_edad":
                "la persona trabajadora tiene 18 años o más"}),
    ])

    sdr.capture(
        p["a_nombre_operador"],
        "¿Cuál es tu nombre completo? (Tu nombre y tus dos apellidos)",
        "operador_nombre", p["a_nombre_contraparte"])

    sdr.capture(
        p["a_nombre_contraparte"],
        "Gracias {{operador_nombre}} \n Ahora ayúdame escribiendo "
        "el nombre completo de la persona {{etiqueta_contraparte}}",
        "contraparte_nombre", p["a_asigna_partes"])

    sdr.bifurcation(
        p["a_bifurca_operador"], "operador",
        [("empleadora", p["a_tipo_empleadora"])],
        default_dest=p["a_mayor_edad"])

    sdr.buttons(p["a_mayor_edad"],
                "Una pregunta importante: ¿{{pregunta_mayor_edad}}?", [
        ("Sí", p["a_num_empleadoras"], {"mayor_edad": "si"}),
        ("No", p["a_menor"],
         {"mayor_edad": "no", "flujo_completado": "abandonado"}),
    ])

    sdr.msg(p["a_menor"], (
        "Para personas menores de 18 años la ley pide cuidados especiales "
        "y este asistente todavía no puede hacer ese contrato. Acércate a "
        "CACEH para que te acompañen. 💚"))

    # Varias empleadoras -> por fuerza entrada por salida; salta "¿duermes?"
    # y entra a §B vía el link A10 (que retoma con el nombre de la parte).
    sdr.buttons(p["a_num_empleadoras"],
                "Además de {{a_nombre_contraparte}} ¿Trabajas con más personas?", [
        ("Solo con esa persona", p["a_duerme"], None),
        ("Trabajo con más pers", p["a_link_es"], {"tipo_contrato": "entrada_salida"}),
    ])

    sdr.buttons(p["a_duerme"], "¿Duermes en la casa donde trabajas?", [
        ("Sí, duermo ahí", p["b_jornada_abierta"],
         {"tipo_contrato": "planta"}),
        ("No duermo ahí", p["b_jornada_abierta"],
         {"tipo_contrato": "entrada_salida"}),
    ])

    # A10 link tras entrada por salida (rama varias): retoma hacia §B.
    sdr.msg(p["a_link_es"], (
        "Bien, sigamos con los datos para el contrato con "
        "{{contraparte_nombre}}."))
    sdr.embedded(p["a_link_es"], p["b_jornada_abierta"])

    sdr.buttons(p["a_tipo_empleadora"], (
        "¿Qué tipo de contrato necesitan?\n*🏠 De planta:* la persona vive "
        "en la casa.\n*🚪 Entrada por salida:* llega y se va el mismo día."), [
        ("🏠 De planta", p["b_jornada_abierta"], {"tipo_contrato": "planta"}),
        ("🚪 Entrada por salida", p["b_jornada_abierta"],
         {"tipo_contrato": "entrada_salida"}),
    ])
