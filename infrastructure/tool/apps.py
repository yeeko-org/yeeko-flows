import sys
from django.apps import AppConfig


class ToolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.tool'

    def ready(self) -> None:
        from .check_basic_record import CheckBehaviorRecord
        _ready = super().ready()
        valid_commands = ["runserver", "shell"]
        if any([command in sys.argv for command in valid_commands]):
            CheckBehaviorRecord()
        return _ready
