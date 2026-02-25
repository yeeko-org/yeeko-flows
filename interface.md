# Capa de Interfaz

La capa `interface/` contiene las implementaciones específicas de cada plataforma de mensajería. Su función es adaptar los formatos propietarios (JSON de Meta) al modelo estándar interno del sistema y viceversa.

La separación en esta capa permite que la lógica de negocio en `services/` sea agnóstica a la plataforma.

---

## Librería externa: yeeko_abc_message_models

El proyecto depende de la librería `yeeko_abc_message_models` que provee:

- **Clases abstractas** para `Request` y `Response` (modelos base y métodos abstractos).
- **Modelos de datos** de entrada y salida (`TextMessage`, `InteractiveMessage`, `MediaMessage`, `EventMessage`).
- **Implementación para WhatsApp** (`whatsapp_message`): parseo de payloads de Meta y construcción de payloads de respuesta.

La capa `interface/` de este proyecto **sobreescribe** selectivamente los métodos que requieren acceso a los modelos de Django (base de datos), ya que la librería está desacoplada del ORM.

```
yeeko_abc_message_models
    ├── Clases abstractas (request/response)
    └── whatsapp_message/
            ├── request.py    → Parseo de webhook de Meta
            └── response.py   → Construcción de JSON para envío

interface/whatsapp/
    ├── request.py   → WhatsAppRequest + RecordWhatsAppRequest (con Django ORM)
    ├── response.py  → WhatsAppResponse (con Django ORM)
    └── whatsapp.py  → Clase completa de respuesta con formato JSON de Meta
```

---

## WhatsApp

### request.py

#### `WhatsAppRequest`

Subclase de `_WhatsAppRequest` (de la librería). Pre-inicializa `_contacts_data` antes de llamar a `super().__init__()` para corregir un bug de orden de inicialización.

```python
WhatsAppRequest(raw_data: dict, debug=False)
```

#### `RecordWhatsAppRequest`

Subclase de `RecordRequestAbc`. Envuelve un `WhatsAppRequest` y lo registra en base de datos vinculándolo a la plataforma `"whatsapp"`.

```python
RecordWhatsAppRequest(request: WhatsAppRequest)
```

Métodos adicionales:

| Método | Descripción |
|---|---|
| `get_media_content(message, token)` | Descarga el contenido de un mensaje multimedia usando la API de Meta |
| `mark_as_read(pid, token, messages_ids, uids)` | Marca mensajes como leídos en WhatsApp |

---

### response.py / whatsapp.py

La clase de respuesta de WhatsApp implementa `ResponseAbc` y construye los payloads JSON en el formato esperado por la API de Meta.

#### Tipos de mensaje soportados

| Tipo | Descripción |
|---|---|
| Texto simple | `{"type": "text", "text": {"body": "..."}}` |
| Multimedia | `{"type": "image/video/audio/document", ...}` con URL y caption |
| Botones interactivos (≤3 opciones) | `{"type": "interactive", "interactive": {"type": "button", ...}}` |
| Lista de botones (>3 opciones) | `{"type": "interactive", "interactive": {"type": "list", ...}}` |
| Secciones agrupadas | Lista con `section_title` para agrupar opciones |

#### Clases de prueba (NoSend)

Para tests de integración, existen variantes que **no realizan llamadas reales a la API**:

- `WhatsAppRequestNoSend` — Parseo sin marcar mensajes como leídos ni descargar media.
- `WhatsAppResponseNoSend` — Acumula mensajes de salida sin enviarlos realmente.

---

### Templates de WhatsApp

**Archivos:** `interface/whatsapp/account_template.py`, `message_template.py`

Permiten enviar mensajes de plantilla (templates aprobados por Meta) a usuarios. Se usan principalmente para iniciar conversaciones o enviar notificaciones fuera de la ventana de 24 horas.

- `account_template.py` — Gestiona el envío de un template para una cuenta específica.
- `account_template_by_file.py` — Variante que lee el template desde un archivo JSON.
- `message_template.py` — Construcción y envío de payloads de template.
- `ejemplos_template.json` — Ejemplos de estructuras de templates.

---

### send_message_simple.py

Utilidad de bajo nivel para enviar un mensaje de texto simple directamente a la API de WhatsApp sin pasar por el flujo completo. Útil para scripts y herramientas de mantenimiento.

---

## Messenger

**Directorio:** `interface/messenger/`

Implementación equivalente para Facebook Messenger. Extiende las mismas clases abstractas que WhatsApp pero adapta los formatos y comportamientos específicos de la plataforma.

> Ver [compatibilidad.md](compatibilidad.md) para diferencias de comportamiento entre WhatsApp y Messenger (multimedia múltiple, tipos de adjuntos, stickers, etc.)

---

## Relación entre capas

```
presentation/webhook/
    └── POST /webhook/whatsapp/
            ├── 1. WhatsAppRequest(raw_data)          ← interface/whatsapp
            ├── 2. RecordWhatsAppRequest(request)      ← interface/whatsapp
            ├── 3. ManagerFlow(record, WhatsAppResponse)() ← services/manager_flow
            └── 4. WhatsAppResponse.send_messages()    ← interface/whatsapp
```
