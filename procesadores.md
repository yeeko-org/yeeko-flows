# Procesadores de Mensajes

Los procesadores son la capa de lógica de negocio dentro de `services/processor/`. Reciben un mensaje homologado y una instancia de `Response`, y producen mensajes de salida o desencadenan acciones del sistema.

---

## Pipeline general

El flujo completo desde la recepción del webhook hasta el envío de respuestas:

```
Webhook POST
    └── RequestAbc (parsing + registro)
            └── InputAccount
                    └── InputSender
                            └── messages[]

ManagerFlow
    ├── process_messages(input_sender)
    │       ├── record_interaction()  ← registra interacción entrada
    │       └── process_message(message, response)
    │               ├── TextMessage      → TextMessageProcessor
    │               ├── InteractiveMessage → InteractiveProcessor
    │               ├── EventMessage     → StateProcessor
    │               └── MediaMessage     → MediaProcessor
    │
    └── response.send_messages()  ← envía todo al final
```

---

## ManagerFlow

**Archivo:** `services/manager_flow/__init__.py`

Orquestador principal. Recibe un `RecordRequestAbc` (resultado del parseo) y un `ResponseAbc` (clase de respuesta de la plataforma).

```python
ManagerFlow(request_record, response_class)()
```

1. Itera cada `InputSender` del `request_record`.
2. Por cada mensaje del sender, registra la interacción de entrada y crea una instancia de `Response`.
3. Llama al procesador correspondiente según el tipo de mensaje.
4. Una vez procesados **todos** los mensajes, ejecuta `response.send_messages()` para cada response acumulado.

> Los mensajes se acumulan antes de enviarse para optimizar las llamadas a la API de cada plataforma.

---

## TextProcessor / TextMessageProcessor

**Archivo:** `services/processor/text.py`

Procesa mensajes de texto. `TextMessageProcessor` hereda de `TextProcessor` y añade validación de intervalo de tiempo.

### Flujo de decisión (`process()`)

```
1. ¿El texto comienza con "/"?
   → command_handler() → BehaviorProcessor(texto[1:])

2. ¿Existe contexto directo y pieza de contexto?
   → process_written() → WrittenProcessorFull

3. ¿El texto contiene "admin"?
   → intent_to_contact_administrator() → BehaviorProcessor("admin_contact")

4. ¿No hay interacción de salida previa?
   → BehaviorProcessor("start")

5. ¿El texto coincide con algún botón de la pieza de contexto?
   → check_buttons_text() → ReplyProcessor

6. (TextMessageProcessor solamente) ¿Intervalo válido de tiempo?
   → process_written()

7. Fallback
   → BehaviorProcessor("default_text")
```

### Métodos principales

| Método | Descripción |
|---|---|
| `command_handler()` | Interpreta `/comando` y llama al behavior correspondiente |
| `intent_to_contact_administrator()` | Detecta intención de contactar al admin (regex "admin") |
| `process_written()` | Busca un `Written` en la pieza de contexto y guarda la respuesta |
| `check_buttons_text()` | Compara el texto con los títulos de botones de la última pieza enviada |
| `call_behavior(behavior, parameters)` | Instancia `BehaviorProcessor` con el behavior indicado |

---

## BehaviorProcessor

**Archivo:** `services/processor/behavior.py`

Resuelve y ejecuta un comportamiento nombrado (`Behavior`).

```python
BehaviorProcessor(behavior="start", response=response).process()
```

1. Busca en `ApplyBehavior` el registro que coincida con el nombre del behavior y el space de la cuenta (con fallback a global si no existe específico para el space).
2. Registra el `Trigger` de la respuesta.
3. Si `apply_behavior.main_piece` existe → `PieceProcessor`.
4. Si no → `process_behavior_code()`: busca en `services/behavior/` una clase con el nombre del behavior y la instancia.

**Behaviors especiales disponibles:**

| Behavior | Clase | Descripción |
|---|---|---|
| `start` | `services/behavior/start.py` | Primera interacción del usuario |
| `reset` | `services/behavior/reset.py` | Reinicio de estado |
| `insistent` | `services/behavior/insistent.py` | Reenvío insistente de una pieza |

---

## InteractiveProcessor / ReplyProcessor

**Archivo:** `services/processor/interactive.py`

Procesa mensajes interactivos (botones presionados por el usuario). El payload del botón es un UUID que identifica a un `BuiltReply`.

### InteractiveProcessor

Recibe un `InteractiveMessage`. Busca el `BuiltReply` por UUID y delega en `ReplyProcessor`.

### ReplyProcessor

Recibe un `Reply` y la interacción origen. Verifica los `Destination` del reply usando `ConditionRule` y ejecuta el destino que corresponda:

- **piece** → `PieceProcessor`
- **behavior** → `BehaviorProcessor`
- **url** → Agrega respuesta con URL

---

## PieceProcessor

**Archivo:** `services/processor/piece.py`

Procesa una `Piece` completa. Itera sus fragmentos y delega en `FragmentProcessor`.

Si la pieza es de tipo `destinations`, evalúa los destinos disponibles y redirige al primero que cumpla las condiciones del usuario.

---

## FragmentProcessor

**Archivo:** `services/processor/fragment.py`

Procesa un `Fragment` individual y construye el mensaje de salida correspondiente:

| `fragment_type` | Acción |
|---|---|
| `message` | Crea mensaje de texto/botones y lo agrega a `response.message_list` |
| `behavior` | Llama a `BehaviorProcessor` con el behavior configurado en el fragmento |
| `embedded` | Llama recursivamente a `PieceProcessor` con la pieza embebida |
| `media` | Busca el media persistente y agrega mensaje multimedia |

También es responsable de crear el `BuiltReply` para cada botón (`Reply`) del fragmento, registrando el UUID que servirá de payload en el mensaje interactivo.

---

## WrittenProcessorFull

**Archivo:** `services/processor/written.py`

Maneja respuestas de texto libre esperadas por la pieza de contexto activa. Guarda el valor en el `ExtraValue` correspondiente al `Written` de la pieza y avanza el flujo al siguiente destino.

---

## MediaProcessor

**Archivo:** `services/processor/media.py`

Procesa mensajes de tipo multimedia (`MediaMessage`). Evalúa si hay texto de caption y si aplica lo procesa como texto; de lo contrario, invoca `BehaviorProcessor("default_media")`.

---

## StateProcessor

**Archivo:** `services/processor/state.py`

Procesa eventos de estado (`EventMessage`) como `read`, `delivered`, `failed`. Registra el evento en la base de datos y aplica lógica de notificaciones si corresponde.

---

## ContextMixin

**Archivo:** `services/processor/context_mixin.py`

Mixin utilitario compartido por `TextProcessor` y otros. Calcula:

- `context_piece` — La última pieza enviada al usuario (pieza de contexto activa).
- `context_direct` — Si el mensaje es una respuesta directa a esa pieza.
- `last_interaction_out` — La última interacción de salida del usuario.
