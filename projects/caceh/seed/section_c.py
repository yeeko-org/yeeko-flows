"""§C · Antigüedad, pago y lugar."""
from infrastructure.box.models import Piece

from projects.caceh.seed.textos import NO_ENTENDI_DATO, PREGUNTA_FECHA
from services.seeder import FlowSeeder


def wire(sdr: FlowSeeder, p: dict[str, Piece]) -> None:
    # "Ya trabajábamos" (retroactivo): captura la fecha de inicio y sigue a
    # pago. La fecha alimenta la cláusula SEGUNDA del PDF (genera_pdf usa
    # fecha_inicio si es_retroactivo).
    # TODO(E1 calcula_vacaciones): las vacaciones retroactivas
    # proporcionales (LFT 2023) dependen de la fórmula y de la redacción de
    # la cláusula por el abogado; pendiente.
    sdr.buttons(p["c_relacion_previa"], (
        "¿El trabajo empieza ahora, o quieren poner por escrito una "
        "relación que ya existía antes?"), [
        # Borra la fecha de un «Ya trabajábamos» previo: solo sale en el
        # resumen de un contrato retroactivo.
        ("Empieza ahora", p["c_pago_abierta"],
         {"es_retroactivo": "no", "fecha_inicio_texto": None}),
        ("Ya trabajábamos", p["c_fecha_inicio"], {"es_retroactivo": "si"}),
    ])

    # Que la fecha exista y ya haya pasado lo decide el esquema Fecha; la
    # fecha tiene solo dos repreguntas.
    sdr.unit(p["c_fecha_inicio"], "open_question", slots={
        "question": PREGUNTA_FECHA,
        "recap": (
            "La fecha en que empezó este trabajo quedó así: "
            "{{fecha_inicio_texto}}."),
        "correction_request": (
            "Por favor, escribe de nuevo la fecha en que empezó este "
            "trabajo."),
        "give_up": NO_ENTENDI_DATO,
    }, params={"schema": "fecha", "max_reasks": 2})
    sdr.link(p["c_fecha_inicio"], p["c_pago_abierta"])

    # El salario diario y el tabulador silencioso salen en los derivados
    # del pago, así que una corrección posterior los deja al día.
    sdr.unit(p["c_pago_abierta"], "open_question", slots={
        "question": (
            "Hablemos del sueldo 💵 ¿Cuánto es el pago y cada cuándo se da? "
            "Ej.: \"350 al día\", \"2,500 a la semana\"."),
        "recap": (
            "El pago quedó así: ${{monto_texto}} {{frase_periodicidad}}."),
        "correction_request": (
            "Por favor, escribe de nuevo de cuánto es el pago y cada cuánto "
            "tiempo se paga."),
        "give_up": NO_ENTENDI_DATO,
    }, params={"schema": "pago"})
    sdr.link(p["c_pago_abierta"], p["c_modo_pago"])

    sdr.buttons(p["c_modo_pago"], "¿Y cómo se le paga?", [
        ("En efectivo", p["c_salario_diario"], {"modo_pago": "efectivo"}),
        ("Transferencia", p["c_salario_diario"],
         {"modo_pago": "transferencia"}),
        # ("Mixto", p["c_salario_diario"],
        #  {"modo_pago": "mixto"}),
    ])

    # C8 ⚙️ calcula_salario_diario (proyecto): monto+periodicidad+días.
    sdr.behavior_step(
        p["c_salario_diario"], "calcula_salario_diario",
        p["c_lugar_abierta"])

    # Calle, número, colonia, municipio y estado son obligatorios: el
    # esquema arma la repregunta con lo que falte.
    sdr.unit(p["c_lugar_abierta"], "open_question", slots={
        "question": (
            "Por favor, escribe la dirección del lugar de trabajo 🏠\n"
            "Incluye calle, número, colonia, municipio o alcaldía y estado. "
            "Si puedes, también el código postal."),
        "recap": (
            "La dirección del lugar de trabajo quedó así: {{lt_texto}}."),
        "correction_request": (
            "Por favor, escribe de nuevo la dirección del lugar de "
            "trabajo."),
        "give_up": NO_ENTENDI_DATO,
    }, params={"schema": "domicilio"})
    sdr.link(p["c_lugar_abierta"], p["d_actividades"])
