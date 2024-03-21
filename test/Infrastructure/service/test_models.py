from django.test import TestCase
from infrastructure.service.models import Platform, InteractionType, ApiRecord
from infrastructure.service.factories import (
    PlatformFactory, InteractionTypeFactory, ApiRecordFactory
)


class TestPlatformFactory(TestCase):
    def test_platform_creation(self):
        platform = PlatformFactory()
        self.assertIsInstance(platform, Platform)


class TestInteractionTypeFactory(TestCase):
    def test_interaction_type_creation(self):
        interaction_type = InteractionTypeFactory()
        self.assertIsInstance(interaction_type, InteractionType)


class TestApiRecordFactory(TestCase):
    def test_api_request_creation(self):
        api_request = ApiRecordFactory()
        self.assertIsInstance(api_request, ApiRecord)
