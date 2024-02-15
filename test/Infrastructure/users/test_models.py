from django.test import TestCase
from django.contrib.auth import get_user_model
from infrastructure.users.factories import UserManagerFactory, UserFactory


class TestUserManagerFactory(TestCase):
    def test_user_manager_creation(self):
        user_manager = UserManagerFactory()
        self.assertIsInstance(user_manager, get_user_model())


class TestUserFactory(TestCase):
    def test_user_creation(self):
        user = UserFactory()
        self.assertIsInstance(user, get_user_model())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
