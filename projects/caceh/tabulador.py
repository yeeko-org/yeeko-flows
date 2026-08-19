"""Tabulador de salarios CACEH 2026: 20 items de trabajo en 6 niveles.

Fuente de diseño: `bot_caceh/tabulador.md`. Única fuente para el seed (las
opciones del multiselect) y para el behavior `calcula_tabulador`: el salario
sugerido es el MÁXIMO de los items marcados y el aviso solo se dispara si el
salario pactado queda debajo por más del margen (decisión 2026-07-08; los
$900 que CACEH mandó en labor_16-18 eran typo, todo el nivel vale $904).
"""

MARGEN_MXN = 100

# Salario del nivel -> name del Media (imagen con salario + IMSS/INFONAVIT)
# y archivo esperado en projects/caceh/assets/tablas/<name>.png.
IMAGENES = {
    342.47: "tabulador_342",
    450.00: "tabulador_450",
    500.00: "tabulador_500",
    600.00: "tabulador_600",
    800.00: "tabulador_800",
    904.00: "tabulador_904",
}

# (id, título ≤30 chars ─ límite de CheckboxGroup ─, labores incluidas
# ≤300 chars ─ viaja como description ─, salario diario del nivel)
ITEMS = [
    ("labor_1", "Limpieza general de la casa",
     "Barrer y trapear, limpieza de superficies, aspirar y sacudir, "
     "limpieza de recámara/baño, limpieza de cocina y electrodomésticos, "
     "limpieza de áreas comunes", 342.47),
    ("labor_2", "Lavado y planchado de ropa",
     "Lavado de prendas (clasificación, ciclos, detergentes, secado), "
     "planchado (preparación, colgar, doblar)", 450.00),
    ("labor_3", "Pisos y superficies a fondo",
     "Limpieza de alfombras y tapicerías, lavado de paredes y techos, "
     "limpieza de zócalos y rodapié", 500.00),
    ("labor_4", "Baños y muebles a fondo",
     "Desinfección de baños (azulejos, moho), limpieza detrás/debajo de "
     "muebles, limpieza de ventanas y persianas", 500.00),
    ("labor_5", "Electrodomésticos y clósets",
     "Limpieza de electrodomésticos por dentro/fuera, organización y "
     "limpieza de armarios y despensas", 500.00),
    ("labor_6", "Jardinería y áreas verdes",
     "Mantenimiento de césped, plantas y flores, áreas verdes, sistemas "
     "de riego, hortalizas y frutales, prácticas sostenibles", 500.00),
    ("labor_7", "Cuidado de mascotas",
     "Trato digno a mascotas según indicaciones, limpieza del área donde "
     "habitan", 500.00),
    ("labor_8", "Planear y comprar alimentos",
     "Planificación y preparación de alimentos, compra de ingredientes, "
     "preparación de ingredientes", 600.00),
    ("labor_9", "Cocina y platillos",
     "Técnicas básicas de cocina, preparación de platos específicos, "
     "montaje y presentación, limpieza y almacenamiento", 600.00),
    ("labor_10", "Chofer y cuidado del auto",
     "Manejo de vehículo familiar, mantenimiento del vehículo", 800.00),
    ("labor_11", "Cuidado básico de niños",
     "Asistencia de necesidades básicas, asegurar entorno seguro y "
     "limpio, procurar seguridad física y emocional", 800.00),
    ("labor_12", "Desarrollo y vínculo con niños",
     "Establecer relaciones de confianza, estimular el desarrollo "
     "integral", 800.00),
    ("labor_13", "Seguridad y avances de niños",
     "Primeros auxilios básicos, informar a padres/tutores del progreso, "
     "registro de bitácora", 800.00),
    ("labor_14", "Administración del hogar",
     "Mantenimiento del hogar, organización, cuidado del hogar, manejo "
     "de emergencias en el hogar", 800.00),
    ("labor_15", "Supervisar personal del hogar",
     "Recibir y supervisar a otros trabajadores de servicio y tareas "
     "administrativas", 800.00),
    ("labor_16", "Contratar y gestionar personal",
     "Supervisión y gestión de personal (amas de llaves, cocineros, "
     "jardineros), reclutar/entrenar/evaluar", 904.00),
    ("labor_17", "Eventos y suministros",
     "Planificar comidas diarias, eventos y cenas formales, gestión de "
     "suministros, atención a huéspedes", 904.00),
    ("labor_18", "Seguridad y patrimonio",
     "Seguridad del hogar y sus ocupantes, administración de tareas del "
     "hogar y tareas administrativas personales", 904.00),
    ("labor_19", "Cuidado del adulto mayor",
     "Principios y trato al adulto mayor, asistencia diaria, cuidado de "
     "la salud (medicamentos, signos vitales, citas), apoyo emocional",
     904.00),
    ("labor_20", "Supervisión de adulto mayor",
     "Supervisión y prevención de caídas, gestión de medicamentos, "
     "comunicación y coordinación, tareas ligeras del hogar", 904.00),
]

SALARIOS = {item_id: salario for item_id, _, _, salario in ITEMS}

# La cláusula CUARTA del contrato tiene sus propias 20 casillas, que NO son
# los 20 items del tabulador: son otro vocabulario y no hay correspondencia
# 1:1 (un item puede marcar varias casillas y varios items pueden marcar la
# misma). Sin esta tabla el PDF sale con todas las casillas vacías.
# Propuesta nuestra, aprobada por Ricardo el 2026-08-18 y PENDIENTE de
# validación con CACEH: las casillas tienen efecto legal.
# Seis casillas de la cláusula no las alimenta ningún item y por diseño
# quedan siempre vacías: recamarera, mantenimiento, vigilancia,
# cuidado_casa, limpieza_mascotas, diversos_domicilios.
CASILLAS_CONTRATO: dict[str, tuple[str, ...]] = {
    "labor_1": ("limpieza_general",),
    "labor_2": ("lavado", "planchado"),
    "labor_3": ("limpieza_profunda",),
    "labor_4": ("limpieza_profunda",),
    "labor_5": ("limpieza_profunda",),
    "labor_6": ("jardineria",),
    "labor_7": ("cuidado_mascotas",),
    "labor_8": ("cocina_sencilla",),
    "labor_9": ("cocina_sencilla",),
    "labor_10": ("chofer",),
    "labor_11": ("cuidado_personas",),
    "labor_12": ("cuidado_personas",),
    "labor_13": ("cuidado_personas",),
    "labor_14": ("ama_llaves",),
    "labor_15": ("ama_llaves",),
    "labor_16": ("mayordomo",),
    "labor_17": ("mayordomo",),
    "labor_18": ("mayordomo",),
    "labor_19": ("cuidado_personas", "acompanamiento"),
    "labor_20": ("cuidado_personas", "acompanamiento"),
}


def opciones() -> list[dict]:
    """Opciones [{id,title,description}] para el multiselect de D1."""
    return [{"id": i, "title": t, "description": d} for i, t, d, _ in ITEMS]


def casillas_contrato(actividades: list[str]) -> list[str]:
    """Casillas de la cláusula CUARTA que marcan los items elegidos en D1.

    Sin duplicados y en el orden en que aparecen los items; un id que no sea
    del tabulador se ignora, para que un vocabulario equivocado se vea como
    casillas vacías y no como una casilla marcada de más.
    """
    casillas: list[str] = []
    for item_id in actividades:
        for casilla in CASILLAS_CONTRATO.get(item_id, ()):
            if casilla not in casillas:
                casillas.append(casilla)
    return casillas
