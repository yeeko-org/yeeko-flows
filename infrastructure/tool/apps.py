import sys
from django.apps import AppConfig


class ToolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.tool'

    def ready(self) -> None:
        from .check_basic_record import CheckBehaviorRecord
        _ready = super().ready()
        if 'runserver' in sys.argv:
            CheckBehaviorRecord()
        return _ready
