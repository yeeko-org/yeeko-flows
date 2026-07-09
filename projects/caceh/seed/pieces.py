"""Secciones (crates) y piezas del slice mínimo planta.

Se declaran todas antes de cablear para poder apuntar destinos hacia
adelante. Los pasos ⚙️ son piezas 'content' (behavior + embedded de
auto-avance); solo las bifurcaciones ◆ y los pass-through sin cablear son
'destinations'.
"""

SECTIONS = {
    "a": "§A · Entrada: partes y modalidad",
    "b": "§B · Jornada y descanso",
    "c": "§C · Antigüedad, pago y lugar",
    "d": "§D · Actividades y tabulador",
    "e": "§E · Cierre v1: PDF y registro",
    "stub": "Límites del slice (fuera de alcance)",
}

_D = "destinations"

# (sección, nombre, descripción, piece_type)
PIECES = [
    # §A
    ("a", "a_saludo", "A1 saludo y encuadre", "content"),
    ("a", "a_acerca", "A1b qué es CACEH", "content"),
    ("a", "a_quien_eres", "A2 trabajadora o empleadora", "content"),
    ("a", "a_nombre_operador", "A3 nombre de quien opera", "content"),
    ("a", "a_nombre_contraparte", "A4 nombre de la contraparte", "content"),
    ("a", "a_asigna_partes", "A5 ⚙️ asigna_partes", "content"),
    ("a", "a_bifurca_operador", "A6 bifurca por operador", _D),
    ("a", "a_mayor_edad", "A7 mayoría de edad", "content"),
    ("a", "a_menor", "A·menor canaliza y termina", "content"),
    ("a", "a_num_empleadoras", "A8 cuántas empleadoras", "content"),
    ("a", "a_duerme", "A9 duerme en la casa", "content"),
    ("a", "a_tipo_empleadora", "A11 tipo de contrato (empleadora)",
     "content"),
    ("a", "a_link_es",
     "A10 link tras entrada-salida (varias empleadoras)", "content"),
    # §B
    ("b", "b_jornada_abierta", "B1 jornada (captura)", "content"),
    ("b", "b_ia_jornada", "B2 ⚙️ ia_extrae jornada", "content"),
    ("b", "b_checa_jornada", "B3 bifurca ia_completed", _D),
    ("b", "b_repregunta_jornada", "B4 repregunta jornada", "content"),
    ("b", "b_bifurca_descanso", "B5 bifurca tipo_contrato", _D),
    ("b", "b_descanso_abierta",
     "B6 descanso (captura, solo entrada por salida)", "content"),
    ("b", "b_ia_descanso", "B7 ⚙️ ia_extrae descanso", "content"),
    ("b", "b_confirma_jornada", "B8 confirma jornada", "content"),
    # §C
    ("c", "c_relacion_previa", "C1 relación previa", "content"),
    ("c", "c_fecha_inicio",
     "C2 fecha de inicio (captura, solo retroactivo)", "content"),
    ("c", "c_valida_fecha", "C3 ⚙️ valida_fecha_pasada", "content"),
    ("c", "c_checa_fecha", "C3b bifurca fecha_valida", _D),
    ("c", "c_repregunta_fecha", "C3c reedita fecha", "content"),
    ("c", "c_pago_abierta", "C4 pago (captura)", "content"),
    ("c", "c_ia_pago", "C5 ⚙️ ia_extrae pago", "content"),
    ("c", "c_confirma_pago", "C6 confirma pago", "content"),
    ("c", "c_modo_pago", "C7 modo de pago", "content"),
    ("c", "c_salario_diario", "C8 ⚙️ calcula_salario_diario", "content"),
    ("c", "c_lugar_abierta", "C9 lugar de trabajo (captura)", "content"),
    ("c", "c_ia_lugar", "C10 ⚙️ ia_extrae domicilio", "content"),
    ("c", "c_checa_lugar", "C11 bifurca ia_completed", _D),
    ("c", "c_repregunta_lugar", "C12 repregunta lugar", "content"),
    ("c", "c_confirma_lugar", "C13 confirma lugar", "content"),
    # §D
    ("d", "d_actividades", "D1 ☑️ FormWa actividades (multiselect)",
     "content"),
    ("d", "d_check_tabulador", "D4 bifurca tabulador_activo", _D),
    ("d", "d_calcula_tabulador", "D5 ⚙️ calcula_tabulador", "content"),
    ("d", "d_checa_salario", "D6 bifurca salario_bajo", _D),
    ("d", "d_sugerencia", "D7 sugerencia suave", "content"),
    ("d", "d_contacto", "D8 contacto próximo (rama contactar)", "content"),
    # §E
    ("e", "e_resumen", "E3 resumen final", "content"),
    ("e", "e_corrige", "E4 corrige campo (stub)", "content"),
    ("e", "e_genera_pdf", "E5 ⚙️ genera_pdf", "content"),
    ("e", "e_registra", "E6 ⚙️ registra_contrato", "content"),
    ("e", "e_entrega_pdf", "E7 ⚙️ entrega_pdf", "content"),
    ("e", "e_oferta_mejora", "E8 oferta de mejora", "content"),
    ("e", "e_despedida", "E9 despedida y FIN", "content"),
    # Límites
    ("stub", "fuera_alcance", "Rama fuera del slice del demo", "content"),
]
