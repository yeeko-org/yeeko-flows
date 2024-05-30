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

    # -----------------------------Extra manager-----------------------------

    def add_extra_value(
            self, extra,  value: str | None = None,
            interaction=None,
            origin: str = "unknown", list_by=None
    ):
        from infrastructure.talk.models import ExtraValue
        if not extra:
            return
        extra_value, _ = ExtraValue.objects.get_or_create(
            extra=extra,
            member=self
        )

        extra_value.value = value
        extra_value.origin = origin
        extra_value.list_by = list_by  # type: ignore
        extra_value.save()

        if interaction:
            extra_value.interactions.add(interaction)

    def add_circles(
        self, circles,
            interaction=None,
            origin: str = "unknown", list_by=None
    ):
        for circle in circles:
            self.add_extra_value(circle, None, interaction, origin, list_by)

    def remove_extra(
            self, extra
    ):
        from infrastructure.talk.models import ExtraValue
        if not extra:
            return
        ExtraValue.objects.filter(extra=extra, member=self).delete()

    def remove_extras(self, extras):
        from infrastructure.talk.models import ExtraValue
        ExtraValue.objects.filter(
            extra__in=extras,  member=self
        ).delete()
    # ---------------------------end Extra manager---------------------------
