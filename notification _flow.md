# Flujo de las notificaciones

## NotificationMember.next_at

Las notificaciones asignadas a un usuario son aquellos registros en _NotificationMember_ que tienen un valor de `next_at`. Una notificación pendiente con un `next_at` posterior a `datetime.now()` indica que aún no es el momento de procesarla.

Si el `next_at` es anterior o igual a `datetime.now()`, está lista para ser procesada. Los _NotificationMember_ "rezagados" entran en las listas a considerar. Por lo tanto, la fecha de procesamiento dependerá más del método procesador que del `next_at`, el cual no es una agenda exacta.

El procesador de notificaciones pendientes dependerá de la implementación escogida, siendo la opción clásica un _loop_ que corre cada 10 minutos.

Cuando un _NotificationMember_ se considera finalizado o completado, su `next_at` pasa a ser `None` y se considera inactivo.

## Calculo del next_at

Cuando se asigna una notificación a un usuario, se busca o crea su registro en _NotificationMember_ para esa notificación. Este registro es persistente y se reutiliza si se reactiva el mismo tipo de notificación para el mismo usuario.

Las configuraciones generales se encuentran en el modelo _Notification_, que indica las reglas para todas las asignaciones de este tipo. [Consulta los detalles del modelo _Notification_](https://github.com/yeeko-org/yeeko-flows/wiki/Notificaciones#nombre-y-l%C3%ADmites).

Un _Notification_ con `name="name"` y `account=None` se considera una notificación global, mientras que `Notification(name="name", account=account)` es exclusiva para la página de esa _Account_. Esta última tendrá prioridad si existen ambas.

### Ejemplo de notificación

Para visualizar mejor el flujo de datos, describamos un ejemplo utilizando una notificación con las siguientes configuraciones:

    Notification
        name = "insistencia"
        account = None
        limit_timing = 3
        unlimited_timing = False
        not_choisen_reconsidered_time = 60
        last_interaction_out_min_time = 30
        timings = [
            {
                timing = 60
                minimum_interest = 0
                degradation_to_disinterest = 0
                index= 0
            },
            {
                timing = 120
                minimum_interest = 0
                degradation_to_disinterest = 10
                index= 1
            }
        ]

Supongamos que esta notificación se activa por la asignación de una interacción. Esto ocurre al instante, por lo que la última interacción de entrada (_request_ del usuario) y la última interacción de salida (_response_ del sistema) tienen la misma fecha:

    interaction_in.created = 01/01/2020 12:00
    interaction_out.created  = 01/01/2020 12:00

El objeto _NotificationMember_ se inicializa independientemente de si es nuevo o reutilizado. [Consulta los detalles del modelo _NotificationMember_](https://github.com/yeeko-org/yeeko-flows/wiki/Notificaciones#activaci%C3%B3n-de-la-notificaci%C3%B3n-a-usuarios-memberaccount).

#### Inicialización de datos

- **controller**: Se asignará o reiniciará a `0`, indicando el turno actual del timing.
- **parameters**: Si aplica, se setearán los nuevos valores de referencia. Para insistencia, es el ID de la pieza (mensajes) a insistir: `{piece: 1}`.
- **actual_timing**: Se asigna el primer _timing_ de la lista (`index=0`).
- **next_timing**: La referencia del siguiente _timing_ (`index=0`).

### next_timing

Para determinar el `next_timing`, primero se revisará si el `limit_timing` permitirá un siguiente evento. Luego, se verificará si la lista tiene elementos para ese turno; en caso contrario, se tomará el último elemento.

### next_at

Es importante notar que `last_interaction_out_min_time = 30` y `timing = 60`. El _timing_ siempre tiene que ser mayor; si no lo es, se ignorará. El tiempo más grande entre ambos se tomará para el cálculo. Sin embargo, si `last_interaction_out.created` es menor a `datetime.now()`, el cálculo sigue este procedimiento:

    elapsed_time = datetime.now() - last_interaction_out.created

Si el tiempo transcurrido es mayor a los indicadores, se agenda inmediatamente:

    if elapsed_time > last_interaction_out_min_time and elapsed_time > timing
        next_at = datetime.now()

En este caso, el valor de `last_interaction_out_min_time` es obligatorio, y puede prevalecer sobre el _timing_. Por lo tanto, la forma más fácil de entender esto es que siempre se tomará el tiempo mayor:

    longer_time = timing
    if timing < last_interaction_out_min_time:
        longer_time = last_interaction_out_min_time
    
    remaining_time = longer_time - elapsed_time
    next_at = datetime.now() + remaining_time

## Flujo de los timing

### Primera intento

Con el contexto de `next_at`, la inicialización de datos quedaría de la siguiente forma:

    elapsed_time: 01/01/2020 12:00 - 01/01/2020 12:00 = 0
    longer_time = 60
    remaining_time = 60 - 0

    NotificationMember:
        controller = 0
        parameters = {piece: 1}

        next_at = 01/01/2020 13:00

        actual_timing: Timing(index=0)
        next_timing: Timing(index=1)

### Segunda vuelta seleccionada

Dependiendo del tipo de procesador, si la notificación es seleccionada, se agenda el siguiente intento. En este caso, ya no se toma en cuenta el `elapsed_time`:

    longer_time = 120

    NotificationMember:
        controller = 1
        parameters = {piece: 1}

        next_at = 01/01/2020 15:00

        actual_timing: Timing(index=1)
        next_timing: Timing(index=1)

En este ejemplo, `limit_timing = 3` permite una tercera vuelta, pero solo hay dos elementos en los _timings_. Por lo tanto, `next_timing` se asigna al último, que es `Timing(index=1)`.

### Vuelta no seleccionada

Cuando se calculan las notificaciones, pueden surgir otras de mayor prioridad. Para no saturar al usuario, las notificaciones no seleccionadas no se consideran como una vuelta. La mayoría de sus campos seguirá igual, pero su `next_at` se actualiza:

    new_next_at =  01/01/2020 13:00 + Notification.not_choisen_reconsidered_time

    NotificationMember:
        next_at = 01/01/2020 14:00
