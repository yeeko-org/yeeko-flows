from django.db import models
from django.db.models import JSONField

from infrastructure.member.models.member import Member
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
        Platform, blank=True, verbose_name='Plataformas',
        related_name='rules_in')

    circles = models.ManyToManyField(
        Extra, blank=True, related_name='rules_in')

    extra = models.ForeignKey(
        Extra, on_delete=models.CASCADE, blank=True, null=True,
        related_name='rules')
    extra_values = JSONField(blank=True, null=True)
    extra_exists = models.BooleanField(
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

    def evalue_platform(self, platform_name: str) -> bool | None:
        platform_names = self.platforms.values_list('name', flat=True)
        if not platform_names:
            return None
        return platform_name in platform_names

    def evalue_circles(self, member: Member) -> bool | None:
        condition_circles_ids = self.circles.all().values_list('id', flat=True)
        if not condition_circles_ids:
            return None

        member_circles_ids = member.extra_values.all()\
            .values_list('extra__id', flat=True).distinct()

        match_conditions = [
            member_cir in condition_circles_ids
            for member_cir in member_circles_ids]

        # quisas sea necesario agregar match_all_circles
        return any(match_conditions)

    def evalue_extra(self, member: Member) -> bool | None:
        if not self.extra:
            return None

        if self.extra_exists:
            return member.extra_values.filter(
                extra=self.extra).exists()
        else:
            return member.extra_values.filter(
                extra=self.extra, value__in=self.extra_values).exists()

    def evalue_roles(self, member: Member) -> bool | None:
        condition_roles_ids = self.roles.all().values_list('id', flat=True)
        if not condition_roles_ids:
            return None

        return member.role_id in condition_roles_ids

    def evalue(self, member: Member, platform_name: str) -> bool:
        evalue_platform = self.evalue_platform(platform_name)
        evalue_circles = self.evalue_circles(member)
        evalue_extra = self.evalue_extra(member)
        evalue_roles = self.evalue_roles(member)

        match_conditions = [
            evalue_platform, evalue_circles, evalue_extra, evalue_roles
        ]

        match_conditions = [
            match for match in match_conditions if match is not None]

        if self.match_all_conditions:
            return all(match_conditions)
        else:
            return any(match_conditions)
