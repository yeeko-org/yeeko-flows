# Deuda técnica — yeeko-chat-flow

Pendientes conocidos y decisiones diferidas. Se anotan aquí (no en
comentarios de código) para no perderlos entre sesiones.

## Abierto

### `default_text` no está sembrado

`TextProcessor` invoca el behavior `default_text` cuando un texto no
corresponde a nada (ni comando, ni botón, ni captura escrita). No existe
ningún `ApplyBehavior` con ese nombre, ni una clase en
`services/behavior/`.

Desde el 14/07/2026 la llamada es tolerante (`call_behavior(...,
optional=True)`, que atrapa solo `BehaviorNotFound`): el bot **calla** y
deja constancia en el `ApiRecord`, en lugar de reventar el webhook.

Pendiente: sembrar un `ApplyBehavior` llamado `default_text` en CACEH con
una pieza tipo «no te entendí». No requiere tocar código: en cuanto exista
el registro, empieza a responder solo.

### El trabajo pesado bloquea la respuesta del webhook

`ManagerFlow.__call__` hace `response.send_messages()` **dentro** del ciclo
de la petición. Si el envío tarda (sospechoso natural: el PDF de CACEH),
Meta corta por timeout y reenvía el mismo webhook.

Desde el 14/07/2026 el síntoma está contenido —`record_interaction` es
idempotente (`get_or_create` por `mid`) y la vista siempre responde 200—,
así que un reenvío ya no provoca `duplicate key` ni un bucle de reintentos.
Pero la causa sigue viva: **si un mensaje se registra y el usuario nunca
recibe respuesta, es esto**. El reenvío de Meta se descarta por duplicado y
nadie contesta.

Arreglo real: sacar el envío del ciclo del webhook (tarea en segundo
plano). Se deja como deuda consciente para la demo.

### Suite de pruebas floja por diseño previo

Ya documentado en `CLAUDE.md` (Gotchas): `ApiRecord.__del__` guarda en el
GC y envenena la conexión compartida; varias factories desbordan
`User.phone`. Correr los módulos en aislamiento para conocer el estado
real. Vive aquí como recordatorio de que **es deuda**, no una peculiaridad
aceptable.

## Resuelto

- **14/07/2026 — Fall-through a `default_text`.**
  `TextProcessor.process()` no devolvía nada y `TextMessageProcessor`
  ignoraba el resultado, así que tras atender un `/reset` o un `Hola`
  seguía de largo y llamaba `default_text` igualmente. Ahora el padre
  devuelve `True` cuando ya atendió el mensaje.
- **14/07/2026 — `profile` ausente en webhooks de `statuses`.**
  Meta manda `contacts` sin `profile` en los acuses de recibo;
  `_full_contact` asumía que siempre venía.
