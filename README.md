# Yeeko Chat Flow

Motor de flujos conversacionales multicanal basado en Django. Permite configurar y ejecutar flujos de mensajería de forma declarativa para plataformas como **WhatsApp** y **Messenger**, con soporte para procesamiento de mensajes de texto, interactivos, multimedia y eventos de estado.

---

## Documentación

| Documento | Descripción |
|---|---|
| [arquitectura.md](arquitectura.md) | Arquitectura de capas del sistema (Presentación, Interfaz, Servicios, Infraestructura) |
| [modelos.md](modelos.md) | Modelos de base de datos: Place, Flow, Box, Talk, Assign, Xtra, Notification |
| [procesadores.md](procesadores.md) | Pipeline de procesamiento de mensajes y lógica de procesadores |
| [ExtraValues y sessions.md](ExtraValues%20y%20sessions.md) | Sistema de variables extra y sesiones por usuario |
| [notificaciones.md](notificaciones.md) | Configuración de notificaciones y su modelo |
| [notification _flow.md](notification%20_flow.md) | Flujo de ejecución y cálculo de tiempos de las notificaciones |
| [Trigger.md](Trigger.md) | Registro de origen de interacciones y lógica de trazabilidad |
| [interface.md](interface.md) | Capa de interfaz: implementaciones para WhatsApp y Messenger |
| [instalacion.md](instalacion.md) | Instalación, configuración y puesta en marcha del sistema |
| [TESTS.md](TESTS.md) | Suite de pruebas automatizadas: estructura y guía de ejecución |
| [compatibilidad.md](compatibilidad.md) | Notas de compatibilidad entre plataformas y casos especiales |

---

## Inicio rápido

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd yeeko-chat-flow

# 2. Crear entorno virtual y activarlo
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno (ver instalacion.md)
cp .env.example .env

# 5. Aplicar migraciones
python manage.py migrate

# 6. Levantar servidor de desarrollo
python manage.py runserver
```

Consulta [instalacion.md](instalacion.md) para la configuración completa del webhook de Meta y la integración con WhatsApp.

---

## Estructura del proyecto

```
yeeko-chat-flow/
├── infrastructure/     # Modelos Django (persistencia)
│   ├── assign/         # Comportamientos y reglas de asignación
│   ├── box/            # Piezas, fragmentos, respuestas y destinos
│   ├── flow/           # Flujos conversacionales y contenedores
│   ├── member/         # Usuarios, miembros y cuentas
│   ├── notification/   # Modelo de notificaciones
│   ├── place/          # Spaces y cuentas (Account)
│   ├── service/        # Registros de API y plataformas
│   ├── talk/           # Interacciones, triggers y eventos
│   ├── tool/           # Herramientas y configuraciones auxiliares
│   ├── users/          # Usuarios del sistema
│   └── xtra/           # Extras y ExtraValues
├── services/           # Lógica de negocio y procesadores
│   ├── manager_flow/   # Orquestador principal del flujo
│   ├── processor/      # Procesadores por tipo de mensaje
│   ├── request/        # Parseo y homologación de entradas
│   ├── response/       # Acumulación y envío de respuestas
│   ├── behavior/       # Comportamientos especiales (start, reset, insistent)
│   └── notification/   # Servicio de notificaciones
├── interface/          # Implementaciones por plataforma
│   ├── whatsapp/       # Request, Response y utilidades WhatsApp
│   └── messenger/      # Request y Response Messenger
├── presentation/       # Webhooks, APIs y Django Admin
│   ├── webhook/        # Endpoints de entrada de mensajes
│   ├── api/            # APIs REST
│   └── admin/          # Configuración del administrador
├── utilities/          # Utilidades generales del sistema
└── test/               # Suite de pruebas automatizadas
```

---

## Ejecutar pruebas

```bash
python manage.py test test
```

Ver [TESTS.md](TESTS.md) para más detalles.
