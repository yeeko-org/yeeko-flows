from django.test import TestCase

from infrastructure.place.factories import SpaceFactory, AccountFactory
from infrastructure.place.models import Space, Account


class SpaceTestCase(TestCase):
    def test_create_space(self):
        space_instance = SpaceFactory()
        self.assertIsInstance(space_instance, Space)


class AccountTestCase(TestCase):
    def test_create_account(self):
        account_instance = AccountFactory()
        self.assertIsInstance(account_instance, Account)
