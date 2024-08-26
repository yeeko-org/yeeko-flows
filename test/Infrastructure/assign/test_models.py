from django.test import TestCase

from infrastructure.assign.factories import (
    ApplyBehaviorFactory,
    AssignFactory,
    ConditionRuleFactory,
    ParamValueFactory,
)
from infrastructure.assign.models import (
    ApplyBehavior,
    Assign,
    ConditionRule,
    ParamValue,
)


class ConditionRuleTest(TestCase):
    def test_create_condition_rule(self):
        condition_rule_instance = ConditionRuleFactory()
        self.assertIsInstance(condition_rule_instance, ConditionRule)


class AssignTest(TestCase):
    def test_create_assign(self):
        assign_instance = AssignFactory()
        self.assertIsInstance(assign_instance, Assign)


class ApplyBehaviorTest(TestCase):
    def test_create_apply_behavior(self):
        apply_behavior_instance = ApplyBehaviorFactory()
        self.assertIsInstance(apply_behavior_instance, ApplyBehavior)


class ParamValueTest(TestCase):
    def test_create_param_value(self):
        param_value_instance = ParamValueFactory()
        self.assertIsInstance(param_value_instance, ParamValue)
