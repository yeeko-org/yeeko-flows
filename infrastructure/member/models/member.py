from typing import Any, TYPE_CHECKING
from django.db import models

from infrastructure.place.models import Space
from infrastructure.users.models import User
from .extra_manager import ExtraManager

if TYPE_CHECKING:
    from infrastructure.talk.models import ExtraValue, Session


class Member(models.Model, ExtraManager):
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="members")
    active = models.BooleanField(default=True)
    role = models.ForeignKey("member.Role", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    subscribed = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    role_id: int
    pk: int
    extra_values: models.QuerySet["ExtraValue"]
    sessions: models.QuerySet["Session"]

    def __str__(self):
        return f"{self.user} ({self.space})"

    class Meta:
        verbose_name_plural = "Integrantes"
        verbose_name = "Integrante"
