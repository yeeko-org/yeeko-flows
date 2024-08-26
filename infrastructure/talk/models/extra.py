import json
import re

from django.db import models

from infrastructure.member.models import Member
from infrastructure.talk.models.models import Interaction
from infrastructure.xtra.models import Extra
from utilities.json_compatible import ensure_json_compatible


ORIGIN_CHOICES = (
    ("payload", "Payload"),
    ("written", "Escrito"),
    ("dictionary", "Diccionario"),
    ("assigned", "Asignado"),
    ("notification", "Notificación"),
    ("unknown", "Desconocido"),
)


class ExtraValue(models.Model):
    extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE)
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name='extra_values',
        blank=True, null=True
    )
    interactions = models.ManyToManyField(Interaction, blank=True)
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES)
    modified = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    value = models.TextField(blank=True, null=True)
    list_by = models.ForeignKey(
        'self', on_delete=models.CASCADE, related_name='children',
        blank=True, null=True,
    )

    def __str__(self):
        return f"{self.extra} - {self.value or 'True'}"

    def get_value(self):
        if not self.value:
            return None

        if self.extra.format_id == 'json':
            try:
                return json.loads(self.value or "{}")
            except json.JSONDecodeError:
                return {}

        if self.extra.format_id == 'int':
            try:
                return int(self.value)
            except ValueError:
                return 0

        return self.value

    def set_value(self, value):
        if self.extra.format_id == 'json':
            if not isinstance(value, (dict, list)):
                value = {
                    "value": value
                }
            try:
                self.value = json.dumps(value)
            except json.JSONDecodeError as e:
                value = {
                    "data": ensure_json_compatible(value),
                    "set_value_error": str(e)
                }
                self.value = json.dumps(value)
        else:
            self.value = str(value)

    def addition(self, adder: int = 1, save: bool = True):
        if not self.extra.format_id == 'int':
            raise ValueError(
                f'Just for int format, extra format is {self.extra.format_id}')

        if not self.value:
            self.value = "0"

        if not bool(re.fullmatch(r"-?\d+", self.value)):
            raise ValueError(f'Value is not a number: {self.value}')

        self.value = str(int(self.value) + adder)

        if save:
            self.save()

    class Meta:
        verbose_name = 'Valor extra'
        verbose_name_plural = 'Valores extra'
        unique_together = ('extra', 'member', 'list_by')
        ordering = ['-modified']
