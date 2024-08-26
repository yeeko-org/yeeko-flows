from django.test import TestCase
from infrastructure.tool.models import Collection, Behavior, Parameter
from infrastructure.tool.factories import (
    CollectionFactory, BehaviorFactory, ParameterFactory
)


class CollectionTestCase(TestCase):
    def test_create_collection(self):
        collection_instance = CollectionFactory()
        self.assertIsInstance(collection_instance, Collection)


class BehaviorTestCase(TestCase):
    def test_create_behavior(self):
        behavior_instance = BehaviorFactory()
        self.assertIsInstance(behavior_instance, Behavior)


class ParameterTestCase(TestCase):
    def test_create_parameter(self):
        parameter_instance = ParameterFactory()
        self.assertIsInstance(parameter_instance, Parameter)
