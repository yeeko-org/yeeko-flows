# Yeeko Chat Flow  
  
Yeeko Chat Flow es un motor de flujos conversacionales **multicanal** basado en **Django**, diseñado para configurar y ejecutar flujos de mensajería de forma **declarativa** en plataformas como **WhatsApp** y **Messenger** (y extensible a otras como Telegram).  
  
El sistema se apoya en una **arquitectura de capas** y en **modelos genéricos** altamente tipados para mensajes de entrada y salida, de modo que el equipo pueda concentrarse en la lógica conversacional y el “qué” del flujo, mientras los intérpretes por plataforma resuelven el “cómo” (transformación a/desde JSON).  
  
**Idea clave (homologación):**  
  
- `json -> RequestModel (genérico)`  
- `ResponseModel (genérico) -> json`  
  
Incluye soporte para procesamiento de mensajes **texto**, **interactivos**, **multimedia** y **eventos de estado**, además de trazabilidad y notificaciones.  
  
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
  
## Flujo principal (visión general)  
  
El flujo general se divide en 4 etapas, orquestadas por **ManagerFlow** (no es una etapa por sí misma, sino el coordinador donde se gestionan estados, datos y persistencia):  
  
1. **Webhook**  
- Punto más externo (acceso público) por donde llegan los mensajes.  
- Enruta el payload hacia el manejador del flujo.  
  
2. **Request**  
- Convierte diccionarios/JSON en **clases instanciadas** (modelo genérico homologado).  
- Verifica existencia/creación de usuarios.  
- Registra el histórico de entrada.  
  
3. **Process**  
- Procesa el mensaje en **procesadores especializados** por tipo/situación:  
- texto  
- botones / interactivos  
- reglas de visualización y destinos  
- multimedia  
- estados/eventos  
  
4. **Response**  
- Recibe mensajes resultantes como **modelos genéricos** y los transforma a diccionarios por plataforma.  
- Calcula primero todos los mensajes y luego hace el envío en la etapa final.  
- Registra la interacción de salida y sus disparadores.  
  
> Nota: el diagrama del “main flow” debe vivir en `docs/` o en la wiki del proyecto (referencia en la documentación).  
  
---  
  
## Inicio rápido  
  

		# 1. Clonar el repositorio  
		git clone <repo-url>  
		cd yeeko-chat-flow  
		  
		# 2. Crear entorno virtual y activarlo  
		python -m venv venv  
		venv\Scripts\activate # Windows  
		source venv/bin/activate # Linux/Mac  
		  
		# 3. Instalar dependencias  
		pip install -r requirements.txt  
		  
		# 4. Configurar variables de entorno (ver instalacion.md)  
		cp .env.example .env  
		  
		# 5. Aplicar migraciones  
		python manage.py migrate  
		  
		# 6. Levantar servidor de desarrollo  
		python manage.py runserver

Consulta instalacion.md para la configuración completa del webhook de Meta y la integración con WhatsApp.

----------


Consulta `instalacion.md` para la configuración completa del webhook de Meta y la integración con WhatsApp.

----------

## Estructura del proyecto

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

----------

## Ejecutar pruebas

	python manage.py test test

Ver `TESTS.md` para más detalles.