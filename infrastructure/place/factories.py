from factory.django import DjangoModelFactory
import factory.fuzzy
from infrastructure.service.factories import PlatformFactory
from infrastructure.place.models import Space, Account


class SpaceFactory(DjangoModelFactory):
    class Meta:
        model = Space

    title = factory.Faker('word')
    bot_name = factory.Faker('word')
    test = factory.fuzzy.FuzzyChoice([True, False])
    params = {}


class AccountFactory(DjangoModelFactory):
    class Meta:
        model = Account

    pid = factory.Faker('uuid4')
    space = factory.SubFactory(SpaceFactory)
    platform = factory.SubFactory(PlatformFactory)
    title = factory.Faker('word')
    token = factory.Faker('word')
    config = {}
    active = factory.fuzzy.FuzzyChoice([True, False])
    init_text_response = factory.fuzzy.FuzzyChoice([True, False])
    text_response = factory.fuzzy.FuzzyChoice([True, False])
    payload_response = factory.fuzzy.FuzzyChoice([True, False])
    notif_enabled = factory.fuzzy.FuzzyChoice([True, False])
