from django.db import models


from infrastructure.box.models import (
    Destination, Fragment, Piece, Reply, Written)
from infrastructure.member.models.member import Member
from infrastructure.place.models import Space
from infrastructure.tool.models import Behavior
from infrastructure.xtra.models import Extra

from .condition_rule import ConditionRule  # noqa


class Assign(models.Model):
    circles = models.ManyToManyField(
        Extra, blank=True, related_name='assignments_in')
    extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE, blank=True, null=True,
        related_name='assignments')
    extra_value = models.TextField(blank=True, null=True)
    is_remove = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False, verbose_name='Borrado')

    # ---------------------------------Origen---------------------------------
    piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE,
        blank=True, null=True, related_name='assignments')
    reply = models.ForeignKey(
        Reply, on_delete=models.CASCADE,
        blank=True, null=True, related_name='assignments')
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE,
        blank=True, null=True, related_name='assignments')
    written = models.ForeignKey(
        Written, on_delete=models.CASCADE,
        blank=True, null=True, related_name='assignments')
    # -------------------------------end Origen-------------------------------

    def __str__(self):
        extra_name = self.extra.name if self.extra else self.pk
        return f"{extra_name} - {self.extra_value}"

    class Meta:
        verbose_name = 'Asignación'
        verbose_name_plural = 'Asignaciones'

    def to_member(self, member: Member, interaction):

        circles = self.circles.all()

        if self.is_remove:
            member.remove_extras(circles)
            member.remove_extra(self.extra)
        else:
            member.add_circles(circles, interaction, "assigned")
            member.add_extra_value(
                self.extra, self.extra_value, interaction, "assigned")


class ApplyBehavior(models.Model):
    behavior = models.ForeignKey(Behavior, on_delete=models.CASCADE)
    space = models.ForeignKey(
        Space, on_delete=models.CASCADE, blank=True, null=True
    )
    main_piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        related_name='apply_behavior')

    def __str__(self):
        return str(self.behavior)

    class Meta:
        verbose_name = 'Aplicar Función'
        verbose_name_plural = 'Aplicar Funciones'
        unique_together = ('behavior', 'space')


class ParamValue(models.Model):
    parameter = models.ForeignKey("tool.Parameter", on_delete=models.CASCADE)
    # --------------------------------related--------------------------------
    apply_behavior = models.ForeignKey(
        ApplyBehavior, on_delete=models.CASCADE,  blank=True, null=True,
        related_name='values')
    fragment = models.ForeignKey(
        Fragment, on_delete=models.CASCADE, blank=True, null=True,
        related_name='values')
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, blank=True, null=True,
        related_name='values')
    # ------------------------------end related------------------------------

    # ---------------------------------valor---------------------------------
    value = models.CharField(max_length=255, blank=True, null=True)
    piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True,
        related_name='values')
    reply = models.ForeignKey(
        Reply, on_delete=models.CASCADE, blank=True, null=True,
        related_name='values')
    # -------------------------------end valor-------------------------------

    def __str__(self):
        return f"{self.parameter} - {self.value or 'Sin valor'}"

    class Meta:
        verbose_name = '    '
        verbose_name_plural = 'Valores de Parámetros'
