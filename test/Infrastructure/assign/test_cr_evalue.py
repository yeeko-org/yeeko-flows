"""
Tests para la evaluación de reglas de condición (ConditionRule).

Verifica el método `evalue` y sus variantes en el modelo `ConditionRule`,
cubriendo los siguientes criterios de evaluación:
  - Plataforma (`evalue_platform`): comprueba si la plataforma del mensaje
    coincide con las plataformas configuradas en la regla.
  - Círculos (`evalue_circles`): comprueba si el miembro pertenece a alguno
    de los círculos (extras de tipo círculo) requeridos.
  - Extras (`evalue_extra`): comprueba si el miembro tiene asignado el valor
    de extra esperado, o simplemente que el extra exista.
  - Roles (`evalue_roles`): comprueba si el rol del miembro está entre los
    roles permitidos por la regla.
  - Evaluación combinada en modo "any" (`evalue`): la regla se cumple si al
    menos uno de los criterios anteriores es verdadero.
  - Evaluación combinada en modo "all" (`evalue` con `match_all_conditions`):
    la regla se cumple solo si todos los criterios configurados son verdaderos.
"""
from django.test import TestCase

from infrastructure.assign.models import ConditionRule
from infrastructure.member.models import MemberAccount, Role
from infrastructure.member.models.member import Member
from infrastructure.service.models import Platform
from infrastructure.talk.models import ExtraValue
from infrastructure.xtra.models import ClassifyExtra, Extra


class TestConditionRuleEvalue(TestCase):
    fixtures = [
        "test/fixtures/whatsapp_basic_data/basic_memberaccount.json",
    ]

    def setUp(self) -> None:
        member_account = MemberAccount.objects.first()
        if not member_account:
            raise Exception("MemberAccount not found")
        self.member = member_account.member
        self.role = member_account.member.role
        self.platform = member_account.account.platform
        self.space = member_account.account.space
        self.classifyextra, _ = ClassifyExtra.objects.get_or_create(
            name="test"
        )

        self.extra_circulo = Extra.objects.create(
            name="test circle",
            classify=self.classifyextra,
            space=self.space
        )

        self.extra = Extra.objects.create(
            name="test extra",
            classify=self.classifyextra,
            space=self.space
        )

        self.admin_test_role = Role.objects.create(name="admin_test_role")

    def test_evalue_platform(self):
        self.conditionrule_platform = ConditionRule.objects.create(appear=True)
        self.conditionrule_platform.platforms.add(self.platform)
        self.assertTrue(
            self.conditionrule_platform.evalue_platform(self.platform.name))

        self.assertFalse(self.conditionrule_platform.evalue_platform("other"))

    def test_evalue_circle(self):
        conditionrule_circle = ConditionRule.objects.create(appear=True)
        conditionrule_circle.circles.add(self.extra_circulo)

        self.assertFalse(
            conditionrule_circle.evalue_circles(self.member))

        self.member.add_circles([self.extra_circulo])

        self.assertTrue(conditionrule_circle.evalue_circles(self.member))

    def test_evalue_extra(self):
        valid_value = "value_test"
        optional_valid_value = "value_optional_test"
        conditionrule_extra = ConditionRule.objects.create(
            extra=self.extra,
            extra_values=[valid_value, optional_valid_value],
        )

        # non extra in member
        self.assertFalse(conditionrule_extra.evalue_extra(self.member))

        # other extra value in member
        self.member.add_extra_value(self.extra, "value_error")
        self.assertFalse(conditionrule_extra.evalue_extra(self.member))

        # valid extra value in member
        self.member.add_extra_value(self.extra, valid_value)
        self.assertTrue(conditionrule_extra.evalue_extra(self.member))

        # optional valid extra value in member
        self.member.add_extra_value(self.extra, optional_valid_value)
        self.assertTrue(conditionrule_extra.evalue_extra(self.member))

        # just extra exists
        conditionrule_extra.extra_exists = True
        self.member.add_extra_value(self.extra, "vale_error")
        self.assertTrue(conditionrule_extra.evalue_extra(self.member))

    def test_evalue_roles(self):
        conditionrule_role = ConditionRule.objects.create(appear=True)
        conditionrule_role.roles.add(self.admin_test_role)
        self.assertFalse(conditionrule_role.evalue_roles(self.member))

        conditionrule_role.roles.add(self.role)
        self.assertTrue(conditionrule_role.evalue_roles(self.member))

    def test_evalue_any(self):
        conditionrule = ConditionRule.objects.create(
            extra=self.extra,
            extra_values=["value_test"],
        )
        conditionrule.platforms.add(self.platform)
        conditionrule.circles.add(self.extra_circulo)
        conditionrule.roles.add(self.admin_test_role)

        self.assertFalse(conditionrule.evalue(self.member, "other"))

        self.assertTrue(conditionrule.evalue(self.member, self.platform.name))

        self.member.add_circles([self.extra_circulo])
        self.assertTrue(conditionrule.evalue(self.member, self.platform.name))

        self.member.remove_extra(self.extra_circulo)
        self.member.add_extra_value(self.extra, "value_test")
        self.assertTrue(conditionrule.evalue(self.member, self.platform.name))

        self.member.remove_extra(self.extra)
        conditionrule.roles.add(self.role)
        self.assertTrue(conditionrule.evalue(self.member, self.platform.name))

    def test_evalue_all(self):
        conditionrule = ConditionRule.objects.create(
            extra=self.extra,
            extra_values=["value_test"],
            match_all_conditions=True
        )
        self.assertFalse(conditionrule.evalue(self.member, self.platform.name))

        self.member.add_extra_value(self.extra, "value_test")
        self.assertTrue(conditionrule.evalue(self.member, self.platform.name))

        conditionrule.platforms.add(self.platform)
        self.assertTrue(conditionrule.evalue(self.member, self.platform.name))

        self.member.remove_extra(self.extra)
        self.assertFalse(conditionrule.evalue(self.member, self.platform.name))

        conditionrule.circles.add(self.extra_circulo)
        self.member.add_circles([self.extra_circulo])
        self.assertFalse(conditionrule.evalue(self.member, self.platform.name))

        conditionrule.roles.add(self.role)
        self.assertFalse(conditionrule.evalue(self.member, self.platform.name))

        self.member.add_extra_value(self.extra, "value_test")
        self.assertTrue(conditionrule.evalue(self.member, self.platform.name))
