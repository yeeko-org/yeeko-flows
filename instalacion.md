# Instalación y Configuración

Guía completa para poner en marcha Yeeko Chat Flow en entornos de desarrollo y producción.

---

## Requisitos

- Python 3.10+
- Django 4.x
- Base de datos compatible con Django (SQLite para desarrollo, PostgreSQL recomendado para producción)
- Cuenta de desarrollador en [Meta for Developers](https://developers.facebook.com/)
- `ngrok` (o dominio público) para recibir webhooks en desarrollo

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd yeeko-chat-flow

# 2. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con los valores del proyecto (ver sección Variables de entorno)

# 5. Aplicar migraciones
python manage.py migrate

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Cargar datos iniciales (plataformas, tipos de interacción, behaviors)
python manage.py loaddata all_dump.json
# o cargar fixtures individuales si existen

# 8. Levantar servidor de desarrollo
python manage.py runserver
```

---

## Variables de entorno

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Django
SECRET_KEY=tu-secret-key-aquí
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (omitir para usar SQLite por defecto)
DATABASE_URL=postgres://user:pass@localhost:5432/yeeko_db

# Meta / WhatsApp
META_VERIFY_TOKEN=token-de-verificacion-del-webhook
META_APP_SECRET=secreto-de-la-app-de-meta

# Notificaciones
DEFAULT_NOTIFICATION_LAPSE_MINUTES=10

# AWS S3 (opcional, para almacenamiento de media)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
CAN_DELETE_AWS_STORAGE_FILES=False
```

---

## Configuración de WhatsApp (Meta)

### 1. Crear la App en Meta

1. Ir a [https://developers.facebook.com/apps/](https://developers.facebook.com/apps/)
2. Crear una nueva aplicación de tipo **Business**.
3. Agregar el producto **WhatsApp**.
4. En la sección **WhatsApp > Configuración de la API**, obtener:
   - **Phone Number ID** (`pid`) — identificador del número de WhatsApp.
   - **WhatsApp Business Account ID** (`app_id`).
   - **Token de acceso temporal o permanente** (`token`).

### 2. Configurar la Plataforma en Django Admin

1. Acceder al admin: `http://localhost:8000/admin/`
2. En **service > Platform**, crear un registro:
   - `name`: `whatsapp`
   - `pid`: Phone Number ID obtenido en Meta
   - `app_id`: WhatsApp Business Account ID
   - `token`: Token de acceso de la API

### 3. Crear un Space y una Account

1. En **place > Space**, crear un space (agrupa tus cuentas y recursos).
2. En **place > Account**, crear una cuenta vinculada al space y a la plataforma WhatsApp, usando el mismo `pid` que la plataforma.

### 4. Configurar el Webhook

#### En desarrollo (ngrok)

```bash
# Levantar ngrok en el puerto de Django
.\ngrok.exe http 8000
```

La URL pública generada por ngrok (ej. `https://xxxx.ngrok-free.app`) se usará como base del webhook.

#### URL del webhook

```
https://<tu-dominio>/webhook/whatsapp/
```

#### En Meta Developer Console

1. Ir a **WhatsApp > Configuración > Webhook**.
2. Configurar:
   - **URL de devolución de llamada**: `https://<tu-dominio>/webhook/whatsapp/`
   - **Token de verificación**: El mismo valor que `META_VERIFY_TOKEN` en `.env`
3. Suscribirse a los eventos: `messages`, `message_deliveries`, `message_reads`.

---

## Configuración de behaviors iniciales

El sistema requiere que existan `Behavior` y sus respectivos `ApplyBehavior` configurados para funcionar. Los behaviors mínimos requeridos son:

| Behavior | Descripción |
|---|---|
| `start` | Primera interacción del usuario |
| `default_text` | Texto no reconocido |
| `default_media` | Media sin texto |
| `admin_contact` | Intención de contactar al admin |
| `reset` | Reinicio del estado del usuario |

Para cada behavior, crear:

1. En **assign > Behavior**: el registro con el nombre.
2. En **assign > ApplyBehavior**: la implementación para el space, vinculando a una `Piece` si aplica.

---

## Datos iniciales de referencia

- `InteractionType`: Crear al menos `{name: "default", way: "in"}` y `{name: "default", way: "out"}`.
- `CrateType`: Tipos de contenedor básicos (ej. `default`, `notification`).
- `Flow` y `Crate`: Al menos un flujo y contenedor para las piezas de behaviors.

---

## Ejecutar pruebas

```bash
python manage.py test test
```

Ver [TESTS.md](TESTS.md) para detalles de la suite de pruebas.
