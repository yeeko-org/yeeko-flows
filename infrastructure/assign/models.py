from django.db import models
from django.db.models import JSONField

from infrastructure.box.models import (
    Destination, Fragment, Piece, Reply, Written
)
from infrastructure.member.models import Role
from infrastructure.place.models import Space
from infrastructure.service.models import Platform
from infrastructure.tool.models import Behavior
from infrastructure.xtra.models import Extra


class ConditionRule(models.Model):

    appear = models.BooleanField(
        default=True, verbose_name='Aparece/Desaparece')
    fragment = models.ForeignKey(
        Fragment, on_delete=models.CASCADE,
        blank=True, null=True, related_name='rules')
    reply = models.ForeignKey(
        Reply, on_delete=models.CASCADE,
        blank=True, null=True, related_name='rules')
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE,
        blank=True, null=True, related_name='rules')
    platforms = models.ManyToManyField(
        Platform, blank=True, verbose_name='Plataformas')
    circles = models.ManyToManyField(
        Extra, blank=True, related_name='rules_in')
    extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE, blank=True, null=True,
        related_name='rules')
    extra_values = JSONField(blank=True, null=True)
    addl_params = JSONField(blank=True, null=True)
    extra_exits = models.BooleanField(
        blank=True, null=True, verbose_name='Existe extra')
    opposite = models.BooleanField(default=False)
    roles = models.ManyToManyField(Role, blank=True)

    def __str__(self):
        fragment_name = self.fragment.body if self.fragment else ""
        reply_name = self.reply.title if self.reply else ""
        return f"{fragment_name} - {reply_name}"

    class Meta:
        verbose_name = 'Regla de condición'
        verbose_name_plural = 'Reglas de condición'


class Assign(models.Model):
    circles = models.ManyToManyField(
        Extra, blank=True, related_name='assignments_in')
    extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE, blank=True, null=True,
        related_name='assignments')
    extra_value = JSONField(blank=True, null=True)
    is_remove = models.BooleanField(default=False)
    piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, blank=True, null=True)
    reply = models.ForeignKey(
        Reply, on_delete=models.CASCADE, blank=True, null=True)
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE,
        blank=True, null=True, related_name='assignments')
    written = models.ForeignKey(
        Written, on_delete=models.CASCADE, blank=True, null=True)
    deleted = models.BooleanField(default=False, verbose_name='Borrado')

    def __str__(self):
        extra_name = self.extra.name if self.extra else self.pk
        return f"{extra_name} - {self.extra_value}"

    class Meta:
        verbose_name = 'Asignación'
        verbose_name_plural = 'Asignaciones'


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
