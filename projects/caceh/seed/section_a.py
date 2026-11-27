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
    ])
    sdr.embedded(p["a_saludo"], p["a_quien_eres"])

    sdr.msg(p["a_acerca"], (
        "CACEH es una organización de la sociedad civil que busca mejorar "
        "las condiciones laborales de las personas trabajadoras del hogar. "
        "Dignas firma te ayuda a crear un contrato con validez legal solo "
        "contestando unas preguntas."))
    # La pregunta de rol ya salió con el saludo; se repite a propósito: el
    # contexto es la última salida con fragmento, y sin ella un rol tecleado
    # después de esta explicación ya no casaría con ningún botón.
    sdr.embedded(p["a_acerca"], p["a_quien_eres"])

    sdr.buttons(p["a_quien_eres"],
                "¿Eres la persona trabajadora o quien emplea?", [
        ("Trabajadora", p["a_nombre_operador"], {
            "operador": "trabajadora",
            "etiqueta_contraparte": "empleadora",
            "pregunta_mayor_edad": "tienes 18 años o más"}),
        ("Empleadora", p["a_nombre_operador"], {
            "operador": "empleadora",
            "etiqueta_contraparte": "trabajadora"}),
    ])

    # Los nombres nunca se sueltan: el esquema (never_drop) insiste una vez
    # por los apellidos y la unidad acepta lo que haya a la segunda. Sin
    # recap: el nombre completo se revisa en el resumen final.
    sdr.unit(p["a_nombre_operador"], "open_question", slots={
        "question": (
            "¿Cuál es tu nombre completo? (Tu nombre y tus dos apellidos)"),
    }, params={"schema": "nombre_operador", "with_confirmation": False,
               "max_reasks": 1})
    sdr.link(p["a_nombre_operador"], p["a_nombre_contraparte"])

    sdr.unit(p["a_nombre_contraparte"], "open_question", slots={
        "question": (
            "Gracias, {{operador_nombre_pila}}. Ahora escríbeme el nombre "
            "completo de la persona {{etiqueta_contraparte}}."),
    }, params={"schema": "nombre_contraparte", "with_confirmation": False,
               "max_reasks": 1})
    sdr.link(p["a_nombre_contraparte"], p["a_asigna_partes"])

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

    # Salida por minoría de edad: era terminal y dejaba a la persona sin
    # ninguna acción posible. Lleva el mismo botón que la despedida para
    # que un contrato con otra persona no exija reescribir a un bot mudo.
    sdr.buttons(p["a_menor"], (
        "En el trabajo del hogar laboran muchas menores de edad como tú, "
        "pero se requiere una atención especial para crear un contrato "
        "específico. Por favor, escribe a CACEH para recibir atención "
        "personal."), [
        ("Crear otro contrato", p["e_reinicia"], None),
    ])

    # tipo_contrato es la clave que leen templates y bifurcaciones;
    # modalidad_texto es la misma modalidad dicha a la persona (resumen).
    # Planta borra el descanso: un botón viejo pulsado tras capturarlo en
    # entrada por salida lo dejaría en el resumen.
    planta = {"tipo_contrato": "planta", "modalidad_texto": "de planta",
              "descanso_texto": None}
    entrada_salida = {"tipo_contrato": "entrada_salida",
                      "modalidad_texto": "de entrada por salida"}

    # Varias empleadoras -> por fuerza entrada por salida; salta "¿duermes?"
    # y entra a §B vía el link A10 (que retoma con el nombre de la parte).
    sdr.buttons(p["a_num_empleadoras"], (
        "Además de {{contraparte_nombre}}, ¿trabajas con más personas?"), [
        ("Solo con esa persona", p["a_duerme"], None),
        ("Con varias personas", p["a_modalidad_es_varias"], entrada_salida),
    ])

    sdr.buttons(p["a_duerme"], "¿Duermes en la casa donde trabajas?", [
        ("Sí, duermo ahí", p["a_modalidad_planta"], planta),
        ("No duermo ahí", p["a_modalidad_es"], entrada_salida),
    ])

    # Solo la trabajadora oye por qué le toca su modalidad: a la empleadora
    # ya se la explica la pregunta de A11.
    sdr.msg(p["a_modalidad_planta"], (
        "Entonces tu contrato es de planta 🏠: vives en la casa donde "
        "trabajas."))
    sdr.embedded(p["a_modalidad_planta"], p["b_jornada_abierta"])

    sdr.msg(p["a_modalidad_es"], (
        "Entonces tu contrato es de entrada por salida 🚪: trabajas en una "
        "sola casa y duermes en la tuya."))
    sdr.embedded(p["a_modalidad_es"], p["b_jornada_abierta"])

    sdr.msg(p["a_modalidad_es_varias"], (
        "Entonces tu contrato es de entrada por salida 🚪: cada casa lleva "
        "su propio contrato."))
    sdr.embedded(p["a_modalidad_es_varias"], p["a_link_es"])

    # A10 link tras entrada por salida (rama varias): retoma hacia §B.
    sdr.msg(p["a_link_es"], (
        "Bien, sigamos con los datos para el contrato con "
        "{{contraparte_nombre}}."))
    sdr.embedded(p["a_link_es"], p["b_jornada_abierta"])

    sdr.buttons(p["a_tipo_empleadora"], (
        "¿Qué tipo de contrato necesitan?\n*🏠 De planta:* la persona vive "
        "en la casa.\n*🚪 Entrada por salida:* llega y se va el mismo día."), [
        ("🏠 De planta", p["b_jornada_abierta"], planta),
        ("🚪 Entrada por salida", p["b_jornada_abierta"], entrada_salida),
    ])
