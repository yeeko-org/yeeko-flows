# Preguntas de selección múltiple (WhatsApp Flows)

El behavior `multiple_select` presenta al usuario un formulario de
**selección múltiple** (checkbox) dentro de WhatsApp, vía **WhatsApp
Flows** de Meta, y guarda las opciones elegidas en un extra como **lista
JSON de ids**. Sirve para preguntas con una lista cerrada demasiado larga
para la lista interactiva nativa (máx. 10 filas) y donde capturar por
texto libre sería un desperdicio.

> En el código, toda la capa de integración con WhatsApp Flows usa el
> prefijo **`WaForm`** (`WaFormMessage`, `WaFormReplyProcessor`, …) para
> no confundirse con el modelo `Flow` (flujo conversacional).

## Arquitectura (dos fases)

1. **Envío** — `MultipleSelectBehavior` (`services/behavior/multiple_select.py`):
   arma el mensaje `interactive` de tipo `flow`, crea un `BuiltReply`
   cuyo `uuid` se usa como `flow_token`, y guarda en su `params` el extra
   destino y la pieza a la que avanzar.
2. **Recepción** — `WaFormReplyProcessor`
   (`services/processor/wa_form_reply.py`): al llegar el `nfm_reply`,
   localiza el `BuiltReply` por `flow_token`, escribe la selección en el
   extra (lista JSON) y avanza a la pieza destino. Sin confirmación
   aparte.

## Paso 0 (una sola vez): publicar el Flow

1. En **WhatsApp Manager → Flows**, crea un Flow nuevo y pega el JSON de
   `assets/flow_json/wa_form_multiselect.json`. Es **genérico y
   reutilizable**: las opciones, la etiqueta y el `flow_token` se inyectan
   por pregunta vía `flow_action_payload.data`, así que **un solo Flow
   publicado sirve para todas las preguntas de selección múltiple**.
2. Publícalo y copia su **Flow ID**.

No se necesita endpoint `data_exchange`: es un Flow estático con
navegación (`flow_action: "navigate"`) y datos dinámicos. Costo operativo
≈ el de un mensaje interactivo normal.

## Agregar una pregunta a un flujo

1. **Extra destino**: crea un `Extra` con `format = json` (guarda la
   selección como lista). Ej.: `actividades_contrato`.
2. **Pieza destino** (`dest`): la pieza a la que el usuario avanza tras
   responder. Puede ser un mensaje normal o una pieza de tipo
   `destinations` con ruteo condicional.
3. **Pieza de la pregunta**: agrégale un **fragmento de tipo `behavior`**
   con `behavior = multiple_select`. Como la lista de opciones no cabe en
   un `ParamValue` (máx. 255 caracteres), la configuración va en
   **`Fragment.addl_params`** (JSON):

```json
{
  "flow_id": "1234567890",
  "body": "¿Qué actividades realizarás en el contrato?",
  "label": "Actividades",
  "extra": "actividades_contrato",
  "dest_piece_pk": 42,
  "min": 1,
  "max": 10,
  "options": [
    { "value": "act_01", "label": "Limpieza de oficinas" },
    { "value": "act_02", "label": "Vigilancia" }
  ]
}
```

4. **Registrar el behavior** (una vez por entorno): corre el comando que
   ejecuta `CheckBehaviorRecord` para dar de alta la fila
   `Behavior(name="multiple_select", in_code=True)` y su `ApplyBehavior`.

## Parámetros

| Param | Req | Default | Descripción |
|---|---|---|---|
| `flow_id` | ✓ | — | ID del Flow publicado en Meta |
| `body` | ✓ | — | Texto de la burbuja del mensaje |
| `extra` | ✓ | — | Nombre del extra JSON destino |
| `dest_piece_pk` | ✓ | — | Pieza a la que avanza al terminar |
| `options` | * | — | Lista estática `[{value,label}]` |
| `options_extra` | * | — | Nombre de un extra (lista JSON) como origen dinámico |
| `label` | | `body` | Etiqueta del grupo de checkboxes |
| `header` / `footer` | | — | Opcionales |
| `flow_cta` | | `"Seleccionar"` | Texto del botón que abre el Flow |
| `screen` | | `"SELECT"` | ID de pantalla del Flow publicado |
| `min` / `max` | | `0` / `—` | Mínimo y máximo de opciones |

(*) Usa **exactamente uno** de `options` / `options_extra`.

## Qué se guarda

En el extra destino queda la lista de **ids/values** seleccionados, p.
ej. `["act_01", "act_07"]`. Recupéralo en plantillas con
`{{actividades_contrato}}` y su tamaño con `{{actividades_contrato.count}}`.
Los labels se reconstruyen desde el catálogo de la pregunta cuando se
necesiten.

## Validación min/max

El Flow publicado exige `required: true` (al menos una opción). El
`min`/`max` se valida además **del lado servidor** en
`WaFormReplyProcessor` como red de seguridad: si la cantidad queda fuera
de rango se registra un error, pero no se bloquea el avance.

## ¿Cuándo sí necesitaría un endpoint?

Solo si las opciones deben **consultarse o filtrarse en vivo** (catálogos
enormes, búsqueda incremental) o dependen de un cálculo del backend en
medio del formulario. En ese caso se cambia a `flow_action:
"data_exchange"` y se expone un endpoint público con verificación de
firma. Para listas cerradas de ~15-20 opciones, el Flow estático es más
simple y barato.
