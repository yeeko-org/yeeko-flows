
# Configuración de una Notificación

El sistema de notificaciones está definido por 4 aspectos principales:

- Nombre y configuración de límites
- Comportamiento "**Destino**"
- Activación de notificaciones a los usuarios
- Control de tiempos de envío

## Nombre y límites

Similar al "**Behavior**", la entidad "**Notification**" es solo la declaración de existencia sin implementación, configurando límites de tiempos mínimos y envíos máximos.

    Notification:
        name: str
        account: Account | None
        limit_timing: int | None
        unlimited_timing: bool = False
        not_chosen_reconsidered_time: int = 120
        last_interaction_out_min_time: int = 120
        timings: List[NotificationTiming]

- **account**: Declara la exclusividad de uso para esa cuenta, siendo global si no se establece.
- **limit_timing**: Límite de envíos, puede ser menor o mayor al número de timings.
- **unlimited_timing**: Sin límite de envíos.
- **not_chosen_reconsidered_time**: Si en el tiempo indicado para enviar la notificación, existen otras de mayor prioridad y estas son enviadas, esta notificación no se considera fallida; simplemente se reagendará con este tiempo de espera adicional.
- **last_interaction_out_min_time**: Tiempo mínimo entre la última interacción de salida. Tiene mayor prioridad que el tiempo agendado.
- **timings**: Lista de configuraciones y tiempos. Cada elemento es la configuración individual de un turno; si el turno a enviar es mayor al total de timings, se toma el último de la lista.

Los "**Timings**" establecen principalmente el tiempo entre reenvíos de la misma notificación.

    NotificationTiming:
        notification: Notification
        timing: int
        minimum_interest: int = 0
        degradation_to_disinterest: int = 0
        index: int = 0

- **timing**: Tiempo entre el reenvío de notificaciones del mismo tipo.
- **minimum_interest**: Interés mínimo requerido del usuario (**member_account**). Si no se cumple, se considera un intento fallido.
- **degradation_to_disinterest**: Si una notificación falla porque no cumple los requerimientos, se degrada el interés del usuario (**member_account**) en términos de porcentaje; acepta degradación negativa.
- **index**: Número explícito del turno.

## Implementación del Destino

El destino utiliza la misma lógica que los "**Replay**". Se emplean los modelos "**Destination**" para declarar los posibles flujos de mensajes a enviar, utilizando la lógica de "**ConditionRule**" para evaluar si un destino cumple las condiciones para ser enviado.

    Destination:
        notification: Notification | None
        message_flow: Piece | Behavior | Url

    ConditionRule:
        destination: Destination | None
        conditions: Extras | Roles | Platform
        rules

Consultar la documentación sobre la declaración de destinos y la lógica de su evaluación.

## Activación de la notificación a usuarios MemberAccount

Las notificaciones se consideran activadas cuando existen registros "**NotificationMember**" con `next_at` establecido, relacionando un usuario (**MemberAccount**) con una notificación (**Notification**).

    NotificationMember:
        member_account: MemberAccount
        notification: Notification
        next_at: datetime

Actualmente, existen 3 implementaciones que activan las notificaciones:

- **Piece.insistent**
- **Add ExtraValue**
- **Add Extra Masivo**

La activación por **Piece.insistent** activa la notificación estática "**Insistent**", colocando en `NotificationMember.parameters` el ID de la pieza que se pretende insistir.

La activación por **ExtraValue** es más dinámica. Usando los evaluadores de "**ConditionRule**", se pueden configurar notificaciones y activarlas si se cumplen todas las evaluaciones, siguiendo el siguiente comportamiento:

1. Al agregarse un ExtraValue, se buscan en "**ConditionRule**" todas aquellas que tengan relación con el Extra.
2. Se obtienen todas las notificaciones relacionadas con la lista obtenida de "**ConditionRule**".
3. Por cada notificación, se evalúan sus condiciones bajo la lógica de "**ConditionRule**" y, si aplica, se activa la notificación para el usuario.

La activación por agregar un nuevo **Extra** depende más concretamente de si se agregan "**ConditionRule**" relacionados con el nuevo extra. Es preferible la ejecución por script o comando, ya que si se piensa declarar varios "**ConditionRule**", se tiene que esperar a que estén configuradas todas las condiciones para seguir con el siguiente comportamiento:

1. Obtener todos los usuarios que tengan relación con las condiciones y extras de "**ConditionRule**", por query manual.
2. Por cada extra, se aplicarán las lógicas de activación por **ExtraValue** descritas anteriormente.

## Control de tiempos de envío

Para el envío final de notificaciones, se espera un método periódico que, cada cierto tiempo, consulte si existen notificaciones pendientes de envío, definidos por `NotificationMember.next_at <= datetime.now`.

    NotificationMember:
        member_account: MemberAccount
        notification: Notification

        controller: ExtraValue
        parameters: ExtraValue | None

        last_sent: datetime = now()
        next_at: datetime | None

        actual_timing: NotificationTiming | None
        next_timing: NotificationTiming | None

### Número de intentos

Las siguientes condiciones determinan si el intento de reenvío de la notificación es válido:

- **Notification.unlimited_timing**: Sin restricción en el número de intentos.
- **Notification.limit_timing**: Si el intento es menor o igual al "**limit_timing**", sin importar el número de timings.
- **Notification.timings.count()**: Si no se establecieron "**unlimited**" o "**limit**", el nuevo intento tiene que ser menor o igual al total de timings.

### Timing

El timing en turno será dado por la posición del turno en la lista de `Notification.timings`.

Si el nuevo número de intento es mayor al número de timings, se toma el último timing de la lista; esto aplica tanto para `actual_timing` como para `next_timing` (intento actual + 1).

Si no existen timings configurados, se usará el tiempo global configurado en `settings.DEFAULT_NOTIFICATION_LAPSE_MINUTES`.

## Evaluación de Notificación

Se obtiene por cada **MemberAccount** una lista de **NotificationMember** y se aplican dos evaluaciones para determinar si se envía o se considera fallida. La primera es la evaluación de condiciones para la notificación, usando la lógica de **ConditionRule**, buscando cumplir los requerimientos para su envío, incluyendo la evaluación de interés mínimo.

La segunda evaluación es la obtención de su destino, aplicando nuevamente la lógica de **ConditionRule**, pero ahora para la obtención del destino, con el cual se puede enviar su flujo de mensajes y terminar con las operaciones comunes.

Si no se cumplen las dos condiciones, se considera fallida. Además, si aplica, se degrada el interés del usuario en base a **NotificationTiming.degradation_to_disinterest**.

### Operaciones sobre notificaciones enviadas/fallidas comunes

Independientemente de si una notificación es enviada o fallida, se aplican algunas operaciones comunes. Se omiten aquí las notificaciones ignoradas.

Una notificación solo es exitosa cuando el usuario interactúa con ella, desactivando el resto de notificaciones del tipo interactuado. Mientras tanto, se agenda una nueva notificación.

1. El controlador guarda el número de intento realizado.
2. Se calculan los siguientes timings.
3. Se calcula el nuevo `next_at` en base al `actual_timing` en turno y el `Notification.last_interaction_out_min_time` respecto a la última interacción enviada.

### Notificación ignorada

Si después de enviar una notificación aún existen **NotificationMember** en la lista, estas no se consideran fallidas; solo se recalcula su nuevo `next_at` en base a `Notification.not_chosen_reconsidered_time` y `Notification.last_interaction_out_min_time` respecto a la última interacción enviada. No se degrada el interés ni se cuenta en el controlador.
