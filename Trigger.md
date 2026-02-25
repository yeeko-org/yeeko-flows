# Trigger

El trigger es el registro de una **interacción de entrada origen** relacionado a las interacciones de salida para rastrear el flujo conversacional

Todas las interacciones de entrada registran un trigger, y en consecuencia todas las interacciones de salida deberán estar vinculadas a uno. Bajo esta lógica, la relacion Trigger.interaction_reply siempre será de tipo entrada, lo contrario seria un error de lógica.

La siguiente es la lista de posibles entradas y su consecuente tipo de registro del trigger:

Texto:

- comando: Behavior
- written: Written
- intent_to_contact_administrator: Behavior
- primera interacción: Behavior
- botones textuales: BuiltReply- posible perdida de trigger en check_buttons_text por built_reply opcional
- texto al aire: Behavior

Interacción:

- botón con payload tipo uuid: BuiltReply
- botón sin uuid: Behavior

Media:

- written: Written, media_url o "caption:media_url"
- caption: Procesador de Texto
- solo media: Behavior("default_media")
