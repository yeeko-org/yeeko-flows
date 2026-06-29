# projects/caceh

Módulo específico del proyecto **CACEH** (bot que llena contratos modelo de
trabajo del hogar) montado sobre el motor `yeeko-chat-flow`. Aislado a propósito
para poder extraerse como plugin más adelante sin desenredarlo del motor.

## Qué va aquí

- **Seeds** (`management/commands/`): scripts idempotentes que construyen en la BD
  el flujo conversacional de CACEH a partir de los `.md` de diseño del repo
  `bot_caceh` (fuente de verdad del diseño).
  - `seed_welcome` — pieza de bienvenida desechable del demo + apunta el behavior
    global `start` a ella. (Se reemplaza cuando entre el flujo real.)
- **Pendiente (WP4–WP6):**
  - `behaviors.py` — behaviors específicos de CACEH (`genera_pdf`,
    `calcula_salario_diario`, `asigna_partes`, `registra_contrato`…).
  - `schemas.py` — esquemas Pydantic para la extracción con `ia_extrae` (Gemini):
    jornada, pago, domicilio, actividades.
  - `seed_flow` — siembra del slice mínimo (§A,§B-planta,§D,§E,§F,§H).

## Qué NO va aquí

El behavior genérico de extracción `ia_extrae` (Gemini) es **del motor**, no de
CACEH: vive en `services/behavior/` y se parametriza por esquema. Igual el comando
genérico `setup_wa_account` (alta de cuenta WhatsApp), que vive en
`infrastructure/place/management/`.

## Notas de despliegue

- Rama de demo: `caceh-demo` (base `9b86f94`, conocida-buena). Deploy:
  `git fetch && git checkout caceh-demo` en `~/yeeko/yeeko-flows` del EC2.
- DB del demo: RDS `yeeko_chat_flow` (cargada vía symlink `.env`→`config/.env`).
- Diseño y hoja de ruta: repo `bot_caceh` (`hoja_de_ruta_demo.md`, `flows/`).
