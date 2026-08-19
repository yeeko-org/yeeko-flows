# TESTING

Qué se prueba, cómo se corre y qué ruido es normal. La referencia larga (mecánica del arnés, punto ciego conocido, scripts contra WhatsApp real) está en el repo `bot_caceh`: `docs/reference/2026-08-18-arnes-e2e-y-como-correr-las-pruebas.md`.

## Niveles montados (`projects/caceh/tests/`)

- **Unitario, sin red**: behaviors deterministas (`test_behaviors.py`, `test_calcula_tabulador.py`), esquemas y behaviors de IA con Gemini fake (`test_ia_extrae.py`, `test_corrige_por_ia.py`), texto por defecto (`test_default_text.py`), render del PDF con WeasyPrint (`test_pdf.py`).
- **Cableado del seed**: `test_seed_flow.py` siembra el flujo y confirma que un paso dispara su behavior por el motor real.
- **E2E por el motor in-process**: `test_flow_e2e.py` mete payloads de WhatsApp por `ManagerFlow` con `projects/caceh/flow_driver.py`; los botones se contestan por título, leído del seed con `tests/seed_titles.py::title_of`. Gemini es real: la clase lleva `@skipUnless(bool(settings.GEMINI_API_KEY), …)` y se salta entera sin la clave.
- **Entrega del PDF**: `test_pdf_delivery.py`, tramo E5→E7 (genera, registra, entrega) con Gemini fake y subida a Meta mockeada.

## Comando

```bash
cd ~/dev/yeeko/yeeko-chat-flow && .venv/bin/python manage.py test projects.caceh --noinput
```

Línea base al 2026-08-19: 75 pruebas, 75 verdes, ~24 s (9 llaman a Gemini real).

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
- p7: loop de repregunta de jornada.
- p8: relación previa, contrato retroactivo.
- p9: corrige por texto en el resumen.

## Pruebas del motor fuera de `projects/caceh`

Viven en `test/` (modelos de `infrastructure`, `interface/whatsapp`, `presentation/views`, `services/request` y `services/behavior/test_multiple_select.py`). Se corren con `.venv/bin/python manage.py test --noinput` (toda la suite) o `.venv/bin/python manage.py test test.interface.whatsapp --noinput` por paquete. Son flaky por diseño previo (ver «Gotchas» en `CLAUDE.md`): confirmar el estado real corriendo módulos aislados.
