from typing import Any
from django.db import models

from infrastructure.place.models import Space
from infrastructure.users.models import User


class Member(models.Model):
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="members")
    active = models.BooleanField(default=True)
    role = models.ForeignKey("member.Role", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    subscribed = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    role_id: int

    def __str__(self):
        return f"{self.user} ({self.space})"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        from infrastructure.talk.models import ExtraValue
        self.extra_values: models.QuerySet[ExtraValue]
        super().__init__(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Integrantes"
        verbose_name = "Integrante"

