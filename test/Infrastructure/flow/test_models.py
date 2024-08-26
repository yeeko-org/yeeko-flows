from django.test import TestCase

from infrastructure.flow.factories import (
    CrateFactory, CrateTypeFactory, FlowFactory
)
from infrastructure.flow.models import Crate, CrateType, Flow


class FlowTestCase(TestCase):
    def test_create_flow(self):
        flow_instance = FlowFactory()
        self.assertIsInstance(flow_instance, Flow)


class CrateTypeTestCase(TestCase):
    def test_create_crate_type(self):
        crate_type_instance = CrateTypeFactory()
        self.assertIsInstance(crate_type_instance, CrateType)


class CrateTestCase(TestCase):
    def test_create_crate(self):
        crate_instance = CrateFactory()
        self.assertIsInstance(crate_instance, Crate)
