import sys
from django.apps import AppConfig


class FlowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.flow'

    def ready(self) -> None:
        from .check_initial_data import CheckInitialData
        _ready = super().ready()
        valid_commands = ["runserver", "shell"]
        if any([command in sys.argv for command in valid_commands]):
            CheckInitialData()
        return _ready
