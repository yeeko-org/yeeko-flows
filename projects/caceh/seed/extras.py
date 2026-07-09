"""Variables (extras) del flujo CACEH: (nombre, formato|None).

Fuente de diseño: `bot_caceh/flows/variables_v3.md`.

Format: listas y los historiales transitorios = json; monto_pago = int; el
resto str (default). salario_diario queda str a propósito: el behavior
escribe round(diario, 2) (float) y get_value haría int("350.0") -> 0.
"""

EXTRAS = [
    # --- enrutamiento + captura conversacional (WP6)
    ("operador", None),
    ("operador_nombre", None),
    ("contraparte_nombre", None),
    ("etiqueta_contraparte", None),
    ("pregunta_mayor_edad", None),
    ("mayor_edad", None),
    ("tipo_contrato", None),
    ("respuesta_jornada", None),
    ("respuesta_descanso", None),
    ("ia_completed", None),
    ("ia_pregunta", None),
    ("es_retroactivo", None),
    ("fecha_inicio", None),           # captura C2 / normalizada por C3
    ("fecha_valida", None),           # valida_fecha_pasada (C3) -> "si"/"no"
    ("fecha_error", None),            # valida_fecha_pasada (C3) -> reedición
    ("respuesta_pago", None),
    ("modo_pago", None),
    ("respuesta_lugar", None),
    ("actividades", "json"),
    ("tabulador_activo", None),
    ("salario_sugerido", None),       # calcula_tabulador (D5): max de items
    ("salario_bajo", None),           # calcula_tabulador (D5) -> "si"/"no"
    ("enviar_contacto_caceh", None),  # botón "Sí, contactar" (D7)
    # --- salidas de los behaviors de WP5 + campos de los esquemas de IA que
    # ia_extrae escribe (nombre de campo Pydantic = clave del extra).
    ("trab_nombre_completo", None),   # asigna_partes (A5)
    ("empl_nombre_completo", None),   # asigna_partes (A5)
    ("telefono_operador", None),      # asigna_partes (A5)
    ("hora_entrada", None),           # ia_extrae jornada (B2)
    ("hora_salida", None),            # ia_extrae jornada (B2)
    ("dias_laborables", "json"),      # ia_extrae jornada (B2)
    ("_hist_jornada", "json"),        # historial transitorio de B2
    ("descanso_tiempo", None),        # ia_extrae descanso (B7)
    ("comidas_incluidas", "json"),    # ia_extrae descanso (B7)
    ("_hist_descanso", "json"),       # historial transitorio de B7
    ("monto_pago", "int"),            # ia_extrae pago (C5)
    ("pago_periodicidad", None),      # ia_extrae pago (C5)
    ("frase_periodicidad", None),     # derivado en el esquema Pago (C6)
    ("_hist_pago", "json"),           # historial transitorio de C5
    ("lt_calle", None),               # ia_extrae domicilio (C10)
    ("lt_ext", None),
    ("lt_int", None),
    ("lt_colonia", None),
    ("lt_cp", None),
    ("lt_municipio", None),
    ("lt_estado", None),
    ("ciudad_firma", None),           # derivado en la misma llamada de C10
    ("_hist_domicilio", "json"),      # historial transitorio de C10
    ("salario_diario", None),         # calcula_salario_diario (C8)
    ("pdf_contrato", None),           # genera_pdf (E5) -> pk del Media
    ("registro_id", None),            # registra_contrato (E6) -> folio
    ("flujo_completado", None),       # registra_contrato (E6) -> "completo"
]
