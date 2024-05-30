from django.db import models
from django.db.models import JSONField

from infrastructure.service.models import Platform
from infrastructure.xtra.models import Extra


class ConditionRule(models.Model):
    appear = models.BooleanField(
        default=True, verbose_name='Aparece/Desaparece')
    match_all_rules = models.BooleanField(default=False)
    match_all_conditions = models.BooleanField(default=False)

    # ---------------------------------Origin---------------------------------
    fragment = models.ForeignKey(
        "box.Fragment", on_delete=models.CASCADE,
        blank=True, null=True, related_name='rules')
    reply = models.ForeignKey(
        "box.Reply", on_delete=models.CASCADE,
        blank=True, null=True, related_name='rules')

    destination = models.ForeignKey(
        "box.Destination", on_delete=models.CASCADE,
        blank=True, null=True, related_name='rules')
    # -------------------------------end Origin-------------------------------

    # --------------------------------Condition-------------------------------
    platforms = models.ManyToManyField(
        Platform, blank=True, verbose_name='Plataformas')

    circles = models.ManyToManyField(
        Extra, blank=True, related_name='rules_in')

    extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE, blank=True, null=True,
        related_name='rules')
    extra_values = JSONField(blank=True, null=True)
    extra_exits = models.BooleanField(  # Puede usarce circle
        blank=True, null=True, verbose_name='Existe extra')

    roles = models.ManyToManyField("member.Role", blank=True)
    # ------------------------------end Condition-----------------------------

    addl_params = JSONField(blank=True, null=True)

    def __str__(self):
        fragment_name = self.fragment.body if self.fragment else ""
        reply_name = self.reply.title if self.reply else ""
        return f"{fragment_name} - {reply_name}"

    class Meta:
        verbose_name = 'Regla de condición'
        verbose_name_plural = 'Reglas de condición'
