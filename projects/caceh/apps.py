from django.apps import AppConfig


class CacehConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "projects.caceh"
    verbose_name = "CACEH (bot de contratos)"

    def ready(self):
        # Importar los esquemas puebla SCHEMA_REGISTRY (vía @register_schema)
        # al arrancar Django, sin que el motor importe este proyecto.
        from . import schemas  # noqa: F401
