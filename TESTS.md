# Tests — Yeeko Chat Flow

Resumen y propósito de la suite de pruebas automatizadas del proyecto.

---

## Estructura general

```
test/
├── infrastructure/
│   └── assign/
│       └── test_cr_evalue.py
├── interface/
│   └── whatsapp/
│       ├── test_flow_status.py
│       ├── test_manager_flow.py
│       ├── test_request.py
│       ├── test_send_message.py
│       └── test_written.py
├── presentation/
│   └── views/
│       └── test_whatsapp.py
└── services/
    └── request/
        └── test_init.py
```

---

## Descripción por archivo

### `infrastructure/assign/test_cr_evalue.py`

**Propósito:** Verifica la lógica de evaluación del modelo `ConditionRule`.

Prueba los métodos de evaluación que determinan si una regla de condición se cumple para un miembro dado:

| Test | Qué verifica |
|---|---|
| `test_evalue_platform` | La regla pasa solo si la plataforma del mensaje coincide |
| `test_evalue_circle` | La regla pasa si el miembro pertenece a los círculos requeridos |
| `test_evalue_extra` | La regla pasa según el valor de un campo extra del miembro |
| `test_evalue_roles` | La regla pasa si el rol del miembro está en la lista permitida |
| `test_evalue_any` | La regla pasa si **al menos uno** de los criterios se cumple |
| `test_evalue_all` | La regla pasa solo si **todos** los criterios se cumplen (`match_all_conditions=True`) |

---

### `interface/whatsapp/test_flow_status.py`

**Propósito:** Test de integración del flujo completo de un mensaje entrante de WhatsApp.

Verifica que al procesar un mensaje con `ManagerFlow` se creen correctamente en base de datos:

- `MemberAccount` del remitente.
- `ApiRecord` de salida (respuesta).
- `Interaction` vinculada al `ApiRecord` entrante.

Usa `WhatsAppResponseNoSend` para simular el envío sin llamadas reales a la API.

---

### `interface/whatsapp/test_manager_flow.py`

**Propósito:** Verifica el pipeline completo `request → procesamiento → response` de `ManagerFlow`.

Comprueba que al ejecutar el flujo con un payload de tipo `"started"` se genere al menos una respuesta en `response_list`.

---

### `interface/whatsapp/test_request.py`

**Propósito:** Verifica el parseo de un payload de WhatsApp en `WhatsAppRequest`.

Comprueba que la jerarquía de objetos resultante sea correcta:

- Un `input_account` con un `member` con un `message`.
- El mensaje es de tipo `TextMessage` con texto, `message_id` y `timestamp` correctos.

---

### `interface/whatsapp/test_send_message.py`

**Propósito:** Verifica la construcción de payloads para todos los tipos de mensaje de `WhatsAppResponse`.

| Tipo de mensaje | Descripción |
|---|---|
| Texto | Estructura básica con `messaging_product`, `to`, `type`, `text` |
| Multimedia | Imagen con URL y caption |
| Botones interactivos | Hasta 3 opciones (`message_few_buttons`) |
| Lista de botones | Más de 3 opciones (`message_many_buttons`) |
| Secciones | Categorías agrupadas (`message_sections`) |

---

### `interface/whatsapp/test_written.py`

**Propósito:** Verifica el flujo de respuesta a un mensaje de texto para un `MemberAccount` preexistente.

Usa fixtures de cuenta básica y una pieza escrita (`written_piece`). Aísla la lógica de negocio de la API mediante `WhatsAppRequestNoSend` / `WhatsAppResponseNoSend`.

---

### `presentation/views/test_whatsapp.py`

**Propósito:** Test de integración del endpoint webhook de WhatsApp (`webhook_meta_whatsapp`).

| Test | Método HTTP | Qué verifica |
|---|---|---|
| `test_get_subscribe` | GET | Responde correctamente al challenge de Meta con HTTP 200 |
| `test_post_started` | POST | Crea `User`, `Member` y `MemberAccount` al recibir un mensaje válido |

---

### `services/request/test_init.py`

**Propósito:** Verifica el comportamiento de la clase abstracta base `RequestAbc`.

Usa una implementación mínima concreta (`RequestBase`) para probar:

- **Inicialización:** `raw_data`, `platform` e `input_accounts` se asignan correctamente.
- **Registro de petición:** `record_request()` persiste un `ApiRecord` en base de datos con la plataforma y el cuerpo correctos.

---

## Cómo ejecutar los tests

```bash
python manage.py test test
```

Para un módulo específico:

```bash
python manage.py test test.infrastructure.assign.test_cr_evalue
```
