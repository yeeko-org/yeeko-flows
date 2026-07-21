"""§C · Antigüedad, pago y lugar."""
from infrastructure.box.models import Piece

from services.seeder import FlowSeeder


def wire(sdr: FlowSeeder, p: dict[str, Piece]) -> None:
    # C3 ⚙️ valida_fecha_pasada (proyecto, determinista) -> bifurcación
    # fecha_valida; si rechaza, reedita; si valida, sigue a pago.
    sdr.behavior_step(
        p["c_valida_fecha"], "valida_fecha_pasada", p["c_checa_fecha"])
    # C5 ⚙️ ia_extrae pago (sin loop de repregunta en el slice: -> confirma).
    sdr.behavior_step(
        p["c_ia_pago"], "ia_extrae", p["c_confirma_pago"], generic=True,
        params={"esquema": "pago", "entrada": "{{respuesta_pago}}"})
    # C8 ⚙️ calcula_salario_diario (proyecto): monto+periodicidad+días.
    sdr.behavior_step(
        p["c_salario_diario"], "calcula_salario_diario",
        p["c_lugar_abierta"])
    # C10 ⚙️ ia_extrae domicilio -> bifurcación ia_completed.
    sdr.behavior_step(
        p["c_ia_lugar"], "ia_extrae", p["c_checa_lugar"], generic=True,
        params={"esquema": "domicilio", "entrada": "{{respuesta_lugar}}"})

    # "Ya trabajábamos" (retroactivo): captura la fecha de inicio, la valida
    # y sigue a pago. La fecha alimenta la cláusula SEGUNDA del PDF
    # (genera_pdf usa fecha_inicio si es_retroactivo).
    # TODO(E1 calcula_vacaciones): las vacaciones retroactivas
    # proporcionales (LFT 2023) dependen de la fórmula y de la redacción de
    # la cláusula por el abogado; pendiente.
    sdr.buttons(p["c_relacion_previa"], (
        "¿El trabajo empieza ahora, o quieren poner por escrito una "
        "relación que ya existía antes?"), [
        ("Empieza ahora", p["c_pago_abierta"], {"es_retroactivo": "no"}),
        ("Ya trabajábamos", p["c_fecha_inicio"], {"es_retroactivo": "si"}),
    ])

    sdr.capture(
        p["c_fecha_inicio"],
        "¿En qué fecha empezaron a trabajar juntos? Escríbela como "
        "día/mes/año, por ejemplo 15/03/2023. Si no recuerdas el día "
        "exacto, con el mes y el año basta (03/2023). 📅",
        "fecha_inicio", p["c_valida_fecha"])

    sdr.bifurcation(
        p["c_checa_fecha"], "fecha_valida",
        [("no", p["c_repregunta_fecha"])],
        default_dest=p["c_pago_abierta"])

    sdr.capture(
        p["c_repregunta_fecha"], "{{fecha_error}}",
        "fecha_inicio", p["c_valida_fecha"])

    sdr.capture(
        p["c_pago_abierta"],
        "Hablemos del sueldo 💵 ¿Cuánto es el pago y cada cuándo se da? "
        "Ej.: \"350 al día\", \"2,500 a la semana\".",
        "respuesta_pago", p["c_ia_pago"])

    sdr.buttons(p["c_confirma_pago"],
                "Entonces el pago es de ${{monto_pago}} "
                "{{frase_periodicidad}}. ¿Así es?", [
        ("Sí, así es", p["c_modo_pago"], None),
        ("Corregir", p["c_pago_abierta"], None),
    ])

    sdr.buttons(p["c_modo_pago"], "¿Y cómo se le paga?", [
        ("En efectivo", p["c_salario_diario"], {"modo_pago": "efectivo"}),
        ("Transferencia", p["c_salario_diario"],
         {"modo_pago": "transferencia"}),
        # ("Mixto", p["c_salario_diario"],
        #  {"modo_pago": "mixto"}),
    ])

    sdr.capture(
        p["c_lugar_abierta"],
        "¿Cuál es la dirección del lugar de trabajo? Escríbela completa: "
        "calle, número, colonia, C.P., alcaldía o municipio y estado. 🏠",
        "respuesta_lugar", p["c_ia_lugar"])

    sdr.bifurcation(
        p["c_checa_lugar"], "ia_completed",
        [("no", p["c_repregunta_lugar"])],
        default_dest=p["c_confirma_lugar"])

    sdr.capture(
        p["c_repregunta_lugar"], "{{ia_pregunta}}",
        "respuesta_lugar", p["c_ia_lugar"])

    sdr.buttons(p["c_confirma_lugar"], (
        "La dirección quedó así 👀\n🏠 {{lt_calle}} {{lt_ext}}, col. "
        "{{lt_colonia}}, C.P. {{lt_cp}}, {{lt_municipio}}, "
        "{{lt_estado}}"), [
        ("Sí, es correcta", p["d_actividades"], None),
        ("Corregir", p["c_lugar_abierta"], None),
    ])
