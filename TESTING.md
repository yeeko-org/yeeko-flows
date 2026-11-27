# TESTING

Qué se prueba, cómo se corre y qué ruido es normal. La referencia larga (mecánica del arnés, punto ciego conocido, scripts contra WhatsApp real) es la reference `2026-08-18-arnes-e2e-y-como-correr-las-pruebas` de bot_caceh.

## Niveles montados (`projects/caceh/tests/`)

- **Unitario, sin red**: behaviors deterministas (`test_behaviors.py`, `test_calcula_tabulador.py`), esquemas y behaviors de IA con Gemini fake (`test_ia_extrae.py`, `test_corrige_por_ia.py`), texto por defecto (`test_default_text.py`), render del PDF con WeasyPrint (`test_pdf.py`).
- **Cableado del seed**: `test_seed_flow.py` siembra el flujo, confirma que un paso dispara su behavior por el motor real y que cada captura de texto libre es una unidad de `open_question` con su esquema.
- **Las capturas por el motor, con Gemini fake guionizable** (`test_captura.py`): los textos de validación tal cual, la dirección con el estado obligatorio (si falta entra en la repregunta de la dirección), mes y año con día 1 y el recálculo del salario al corregir la jornada, el recorrido de planta con el hueco en el PDF, y los nombres que nunca se sueltan. `gemini_fake()` entrega el `FakeGemini`: lo que se ponga en su `script` sale primero, en orden; sin guion contesta datos canónicos por esquema (los nombres, partiendo el texto). `FlowDriver.at_slot()` dice en qué mensaje de la unidad quedó la persona (`question`, `reask`, `recap`…), porque `at_piece()` da la misma pieza para todos.
- **E2E por el motor in-process**: `test_flow_e2e.py` mete payloads de WhatsApp por `ManagerFlow` con `projects/caceh/flow_driver.py`; los botones se contestan por título, leído del seed con `tests/seed_titles.py::title_of`. Gemini es real: la clase lleva `@skipUnless(bool(settings.GEMINI_API_KEY), …)` y se salta entera sin la clave.
- **§A y cierre por el motor, con Gemini fake** (los nombres pasan por la unidad): `test_seccion_a.py` (la explicación de CACEH desde el saludo, A8 con el nombre de la contraparte, la línea de modalidad que solo oye la trabajadora) y, en `test_default_text.py`, la modalidad en palabras en el resumen y el orden del cierre (PDF, seguridad social, despedida). Un botón de una pieza que ya no es el contexto se pulsa con `FlowDriver.press` (payload real del `button_reply`), no con `tap`.
- **Entrega del PDF**: `test_pdf_delivery.py`, tramo E5→E7 (genera, registra, entrega) con Gemini fake y subida a Meta mockeada.

## Comando

```bash
cd ~/dev/yeeko/yeeko-chat-flow && .venv/bin/python manage.py test projects.caceh --noinput
```

Línea base al 2026-11-26, con la captura nueva y la fecha corregible desde el resumen: 89 pruebas, OK, ~14 s sin clave de Gemini (10 se omiten: las de Gemini real); con la clave, las 89. Las del motor (`test.services` y `test.utilities`) son 15, todas OK; la de `test.utilities` es la del renglón que se omite cuando todas sus variables quedan vacías. Para saltarse las de Gemini real aunque `config/.env` tenga la clave (`load_dotenv` no pisa una variable ya puesta):

```bash
cd ~/dev/yeeko/yeeko-chat-flow && GEMINI_API_KEY= .venv/bin/python manage.py test projects.caceh --noinput
```

Gotchas del entorno:

- Base de pruebas en Postgres; `--noinput` evita el prompt de destruir la base anterior (sin él, en terminal no interactiva, `EOFError`). `--keepdb` es opcional, solo ahorra segundos.
- No sourcear `config/.env` a mano: `settings.py` ya hace `load_dotenv()` y el archivo tiene CRLF, así que un `source` exporta `TIME_ZONE=UTC\r` y rompe Django.
- WeasyPrint se instala con `uv pip`, no con `pip`; sin él las pruebas del PDF fallan por import.
- Al final de la corrida aparecen varios `Exception ignored in: ApiRecord.__del__` con un `IntegrityError` de `service_apirecord`: es ruido de `test_pdf_delivery` (el `__del__` del modelo hace `save()` al recolectar basura), no un fallo; la suite termina en `OK`.

## Credenciales

Solo `GEMINI_API_KEY` en `config/.env`. WhatsApp siempre va mockeado (`media_offline`).

## Flujos e2e cubiertos (`test_flow_e2e.py`)

- p1: trabajadora de planta hasta el PDF.
- p2: empleadora de planta hasta el PDF.
- p3: menor de edad, el flujo termina.
- p4: varias empleadoras, entrada por salida.
- p5: no duerme en el trabajo, entrada por salida.
- p6: empleadora, entrada por salida.
- p7: repregunta de jornada dentro de su unidad.
- p8: relación previa, contrato retroactivo (la fecha relativa se repregunta).
- p9: corrige por texto en el resumen.

## Pruebas del motor fuera de `projects/caceh`

Viven en `test/` (modelos de `infrastructure`, `interface/whatsapp`, `presentation/views`, `services/request`, `test/services/processor/` (la unidad `open_question` y el «next» de la pieza), `test/services/behavior/test_multiple_select.py` y `test/utilities/test_replacer_from_data.py`). Se corren con `.venv/bin/python manage.py test --noinput` (toda la suite) o `.venv/bin/python manage.py test test.interface.whatsapp --noinput` por paquete. Son flaky por diseño previo (ver «Gotchas» en `CLAUDE.md`): confirmar el estado real corriendo módulos aislados.
