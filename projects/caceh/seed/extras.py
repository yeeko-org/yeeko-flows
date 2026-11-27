"""Variables (extras) del flujo CACEH: (nombre, formato|None).

Fuente de diseño: `bot_caceh/flows/variables_v3.md`.

Format: listas y los historiales transitorios = json; monto_pago = int; el
resto str (default). salario_diario queda str a propósito: el behavior
escribe round(diario, 2) (float) y get_value haría int("350.0") -> 0.
"""

EXTRAS = [
    # --- enrutamiento + captura conversacional (WP6)
    ("operador", None),
    ("operador_nombre", None),         # derivado: pila + dos apellidos
    ("operador_nombre_pila", None),    # unidad nombre_operador (A3)
    ("operador_apellido_paterno", None),
    ("operador_apellido_materno", None),
    ("_hist_nombre_operador", "json"),
    ("contraparte_nombre", None),      # derivado: pila + dos apellidos
    ("contraparte_nombre_pila", None),  # unidad nombre_contraparte (A4)
    ("contraparte_apellido_paterno", None),
    ("contraparte_apellido_materno", None),
    ("_hist_nombre_contraparte", "json"),
    ("etiqueta_contraparte", None),
    ("pregunta_mayor_edad", None),
    ("mayor_edad", None),
    ("tipo_contrato", None),
    ("modalidad_texto", None),        # tipo_contrato en palabras (resumen)
    ("ia_completed", None),
    ("ia_pregunta", None),
    ("es_retroactivo", None),
    ("fecha_dia", "int"),             # unidad fecha (C2)
    ("fecha_mes", "int"),
    ("fecha_anio", "int"),
    ("fecha_inicio", None),           # unidad fecha: 'dd/mm/YYYY', día 1
    ("fecha_inicio_texto", None),     # derivado -> recap ('1 de mayo de…')
    ("_hist_fecha", "json"),
    ("modo_pago", None),
    ("actividades", "json"),
    ("tabulador_activo", None),
    ("salario_sugerido", None),       # calcula_tabulador (D5): max de items
    ("salario_bajo", None),           # calcula_tabulador (D5) -> "si"/"no"
    ("enviar_contacto_caceh", None),  # botón "Sí, contactar" (D7)
    ("respuesta_correccion", None),   # captura E4 (texto libre)
    ("correccion_destino", None),     # corrige_por_ia -> resumen|actividades
    ("_hist_correccion", "json"),     # historial transitorio de E4
    # --- salidas de los behaviors de WP5 + campos de los esquemas de IA que
    # ia_extrae escribe (nombre de campo Pydantic = clave del extra).
    ("trab_nombre_completo", None),   # asigna_partes (A5)
    ("empl_nombre_completo", None),   # asigna_partes (A5)
    ("telefono_operador", None),      # asigna_partes (A5)
    ("hora_entrada", None),           # ia_extrae jornada (B2)
    ("hora_salida", None),            # ia_extrae jornada (B2)
    ("dias_laborables", "json"),      # ia_extrae jornada (B2)
    ("_hist_jornada", "json"),        # historial transitorio de B1
    ("jornada_texto", None),          # derivado -> recap de la jornada
    ("descanso_minutos", "int"),      # ia_extrae descanso (B7)
    ("comidas_incluidas", "json"),    # ia_extrae descanso (B7)
    ("_hist_descanso", "json"),       # historial transitorio de B6
    ("descanso_texto", None),         # derivado -> recap ('1 hora, con…')
    ("monto_pago", "int"),            # ia_extrae pago (C5)
    ("pago_periodicidad", None),      # ia_extrae pago (C5)
    ("frase_periodicidad", None),     # esquema Pago / derivado del pago
    ("monto_texto", None),            # derivado -> recap ('2,500')
    ("_hist_pago", "json"),           # historial transitorio de C4
    ("lt_calle", None),               # ia_extrae domicilio (C10)
    ("lt_ext", None),
    ("lt_int", None),
    ("lt_colonia", None),
    ("lt_cp", None),
    ("lt_municipio", None),
    ("lt_estado", None),
    ("ciudad_firma", None),           # derivado en la misma llamada de C9
    ("_hist_domicilio", "json"),      # historial transitorio de C9
    ("lt_texto", None),               # derivado -> recap y resumen
    ("salario_diario", None),         # calcula_salario_diario (C8)
    ("pdf_contrato", None),           # genera_pdf (E5) -> pk del Media
    ("registro_id", None),            # registra_contrato (E6) -> folio
    ("flujo_completado", None),       # registra_contrato (E6) -> "completo"
    # open_question: ya salió el primer recap (la frase del botón va solo
    # en ese); el reinicio del contrato lo borra.
    ("_first_recap_sent", None),
]
