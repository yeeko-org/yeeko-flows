# Notas de Compatibilidad

Este documento detalla las diferencias de comportamiento y limitaciones técnicas entre las diferentes plataformas de mensajería (WhatsApp y Messenger), así como casos especiales de manejo de datos.

---

## Mensajes Multimedia

### Adjuntos y Texto

En varias plataformas, los mensajes con archivos adjuntos se comportan de forma diferente al texto:

- **WhatsApp:** Los archivos adjuntos permiten un comentario (`caption`) opcional en el mismo mensaje. Si se envían varios archivos, WhatsApp los trata como mensajes individuales, cada uno con su propio comentario.
- **Messenger:** Envía todos los archivos como un solo mensaje. El comentario se trata como un mensaje de texto separado que se envía en una solicitud (POST) aparte.

### Metadatos de Media

Los metadatos varían según la plataforma. En Messenger, algunos campos comunes en WhatsApp no están presentes:

| Campo | WhatsApp | Messenger |
|---|---|---|
| `mime_type` | Sí | No siempre disponible |
| `sha256` | Sí | No |
| `media_id` | Sí | No |

El sistema maneja estos campos como opcionales para evitar errores en el flujo de procesamiento.

---

## Tipos de Mensajes Especiales

### Stickers

Los stickers tienen una estructura de payload específica. Ejemplo de payload recibido:

```json
"attachments": [{
    "payload": {
        "sticker_id": 380422049561830,
        "url": "https://scontent.xx.fbcdn.net/..."
    },
    "type": "image"
}]
```

El procesador de media los identifica como tipo `image` pero con metadatos extendidos.

---

## Limitaciones de Botones e Interactividad

| Característica | WhatsApp | Messenger |
|---|---|---|
| Botones rápidos | Máximo 3 | Hasta 13 |
| Listas (Menús) | Hasta 10 opciones | No nativo (se emula con botones) |
| Títulos de botones | Cortos (20-40 caracteres) | Más largos permitidos |
| Secciones | Soportadas en Listas | No soportadas |

---

## Notas de Implementación

- **Interpretación de datos:** Se separó la lógica de mensajería interpretativa en una librería externa (`yeeko_abc_message_models`) para facilitar el mantenimiento y desacoplar el sistema principal de los cambios frecuentes en las APIs de Meta.
- **Sobreescritura en Flow:** Aunque la librería es independiente, los métodos que interactúan con los modelos de infraestructura (como guardar una interacción en DB) se reimplementan en la capa de interfaz local.
