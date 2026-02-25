# Modelos de Infraestructura

Los modelos Django del proyecto están organizados en módulos dentro de `infrastructure/`. Cada módulo representa un dominio específico del sistema.

---

## place — Espacios y Cuentas

### Space

Unidad organizativa de más alto nivel. Agrupa cuentas y recursos compartibles entre diferentes plataformas.

    Space:
        name: str
        description: str

### Account

Representa una página o número de mensajería asociado a una plataforma. Es la entidad que recibe mensajes entrantes y envía respuestas.

    Account:
        pid: str           # Identificador de la plataforma (ej. número de WhatsApp)
        name: str
        space: Space
        platform: Platform

---

## service — Plataformas y Registro de API

### Platform

Registra las plataformas soportadas (ej. `whatsapp`, `messenger`).

    Platform:
        name: str   # primary key
        token: str
        pid: str
        app_id: str

### InteractionType

Catálogo de tipos de interacción (ej. `default / in`, `default / out`).

    InteractionType:
        name: str
        way: str   # "in" | "out"

### ApiRecord

Registro de cada llamada de API, tanto entrante (webhook recibido) como saliente (respuesta enviada). Funciona como trazabilidad de todas las comunicaciones.

    ApiRecord:
        platform: Platform
        body: JSONField          # Cuerpo completo del mensaje
        is_incoming: bool
        created: datetime
        interaction_type: InteractionType
        errors: JSONField        # Lista de errores registrados

Métodos clave:

- `add_error(data, e)` — Agrega un error al campo `errors` sin interrumpir el flujo.

---

## users / member — Usuarios y Miembros

### User (users)

Usuario del sistema Django estándar.

### Member

Perfil de usuario en una plataforma de mensajería. Un mismo usuario puede ser miembro en múltiples plataformas.

    Member:
        uid: str          # Identificador único en la plataforma

### MemberAccount

Asociación de un `Member` con un `Account`. Es la entidad que participa activamente en conversaciones y sobre la que se registran interacciones, extras y notificaciones.

    MemberAccount:
        member: Member
        account: Account
        interest: int     # Nivel de interés para filtros de notificaciones

---

## flow — Flujos y Contenedores

### Flow

Flujo conversacional: agrupa un conjunto de crates/campañas temáticamente.

    Flow:
        name: str
        space: Space
        description: str
        has_definitions: bool

### CrateType

Tipo de contenedor (campaña). Categoriza las crates.

    CrateType:
        name: str   # primary key
        public_name: str

### Crate

Contenedor de piezas. Equivale a una campaña o agrupación de mensajes dentro de un flujo.

    Crate:
        name: str
        crate_type: CrateType
        flow: Flow
        has_templates: bool

---

## box — Piezas, Fragmentos, Respuestas y Destinos

Es el módulo central de contenido de mensajes.

### Piece

Una pieza es la unidad de contenido principal: representa un mensaje o conjunto de mensajes que el sistema puede enviar. Está compuesta por uno o más fragmentos.

    Piece:
        piece_type: str    # "content" | "destinations" | "template"
        name: str
        crate: Crate
        behavior: Behavior
        insistent: Notification
        order_in_crate: int
        deleted: bool

**piece_type:**

- `content` — Contiene mensajes a enviar.
- `destinations` — Solo declara destinos para evaluar y redirigir el flujo.
- `template` — Pieza reutilizable en múltiples crates.

### Fragment

Unidad mínima dentro de una pieza. Un fragmento puede ser un mensaje de texto, un bloque de botones, una pieza embebida o multimedia.

    Fragment:
        fragment_type: str   # "message" | "behavior" | "embedded" | "media"
        piece: Piece
        header: str
        body: str            # Texto principal del mensaje
        footer: str
        media_type: str      # "image" | "video" | "audio" | "file" | "sticker"
        media_url: str
        order: int
        deleted: bool

### Reply

Botón o respuesta que el usuario puede seleccionar desde un fragmento.

    Reply:
        reply_type: str     # "payload" | "quick_reply" | "url"
        fragment: Fragment
        title: str          # Texto visible del botón
        destination: Destination
        section_title: str  # Para agrupar botones en listas
        order: int
        is_jump: bool       # Si true, evita mostrar la pregunta
        deleted: bool

### Destination

Destino al que redirige un `Reply` o una `Notification`. Puede apuntar a una pieza, un behavior o una URL. Usa `ConditionRule` para evaluar si aplica para el usuario actual.

    Destination:
        destination_type: str   # "piece" | "behavior" | "url"
        reply: Reply
        notification: Notification
        piece: Piece
        behavior: Behavior
        url: str
        order: int
        deleted: bool

### Written

Opción escrita asociada a una pieza. Permite que el usuario responda con texto libre y que el sistema lo procese como una respuesta esperada formalmente.

    Written:
        extra: Extra          # Extra donde se guarda la respuesta
        collection: Collection
        available: bool

---

## assign — Comportamientos y Reglas

### Behavior

Nombre de un comportamiento especial del sistema (ej. `start`, `default_text`, `reset`, `insistent`). No contiene implementación directa; es una declaración de existencia.

    Behavior:
        name: str   # primary key
        description: str

### ApplyBehavior

Implementación de un `Behavior` para un `Space` específico. Vincula el comportamiento a una pieza principal (`main_piece`) y a parámetros iniciales.

    ApplyBehavior:
        behavior: Behavior
        space: Space
        main_piece: Piece
        values: JSONField    # Parámetros por defecto del comportamiento

### ConditionRule

Regla de condición evaluable para determinar si una `Destination` aplica para un `MemberAccount` dado. Permite filtrar por plataforma, rol, círculo o valor de un `Extra`.

    ConditionRule:
        destination: Destination
        conditions: JSONField   # Lista de condiciones a evaluar
        match_all_conditions: bool  # AND (true) vs OR (false)

Métodos de evaluación:

- `evalue_platform(platform_name)` — La plataforma de la cuenta coincide.
- `evalue_circle(member)` — El miembro pertenece al círculo requerido.
- `evalue_extra(member)` — El valor del extra del miembro cumple la condición.
- `evalue_roles(member)` — El rol del miembro está permitido.

---

## talk — Interacciones, Triggers y Eventos

### Interaction

Registro de cada interacción individual, ya sea entrante (mensaje del usuario) o saliente (respuesta del sistema). Es la unidad de trazabilidad fundamental del sistema.

    Interaction:
        mid: str               # Message ID de la plataforma (primary key)
        interaction_type: InteractionType
        is_incoming: bool
        member_account: MemberAccount
        api_record: ApiRecord
        fragment: Fragment     # Fragmento que generó esta interacción (si es saliente)
        created: datetime

### Trigger

Registro del origen de una interacción de entrada. Vincula cada mensaje entrante con el comportamiento o respuesta origen que lo provocó.

    Trigger:
        interaction_reply: Interaction   # Interacción de entrada relacionada
        behavior: Behavior
        built_reply: BuiltReply
        notification: Notification
        is_direct: bool   # Si fue en respuesta directa (contexto activo)

Ver [Trigger.md](Trigger.md) para los detalles de cada tipo de trigger.

### BuiltReply

Instancia de un `Reply` que fue enviado a un usuario en una `Interaction` saliente. Registra el payload único (UUID) que permite identificar exactamente qué botón presionó el usuario.

    BuiltReply:
        uuid: UUID   # primary key
        interaction: Interaction
        reply: Reply
        params: JSONField
        payload: str   # Payload legacy

### Event

Evento de estado asociado a una `Interaction` (ej. entregado, leído, fallido).

    Event:
        event_name: str    # "sent" | "delivered" | "read" | "failed" | etc.
        interaction: Interaction
        api_request: ApiRecord
        timestamp: int
        emoji: str
        date: datetime

---

## xtra — Variables Extra

Ver [ExtraValues y sessions.md](ExtraValues%20y%20sessions.md) para documentación completa del sistema de Extras y Sessions.

**Modelos principales:**

- `Extra` — Declaración de variable con formato y pertenencia a un Space.
- `ExtraValue` — Valor concreto registrado para un `MemberAccount`.
- `Session` — Controlador global de sesión por usuario.

---

## notification — Notificaciones

Ver [notificaciones.md](notificaciones.md) y [notification _flow.md](notification%20_flow.md) para documentación completa.

**Modelos principales:**

- `Notification` — Declaración de una notificación con límites y timings.
- `NotificationTiming` — Configuración de tiempos por turno.
- `NotificationMember` — Asignación de una notificación a un `MemberAccount`.
