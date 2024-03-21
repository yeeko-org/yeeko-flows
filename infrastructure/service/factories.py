from factory.django import DjangoModelFactory
import factory

from infrastructure.service.models import ApiRecord, InteractionType, Platform
from utilities.factory_util import optional_sub_factory, safe_pydict

from .models import Platform, InteractionType, ApiRecord


class PlatformFactory(DjangoModelFactory):
    class Meta:
        model = Platform

    name = factory.Faker('uuid4')  # This is a workaround for the primary key
    public_name = factory.Faker('sentence')
    description = factory.Faker('paragraph')
    config = safe_pydict()
    with_users = factory.Faker('boolean')
    id_field = factory.Faker('word')
    internal = factory.Faker('boolean')
    color = factory.Faker('color_name')
    icon = factory.Faker('word')
    image = factory.Faker('file_path', extension='jpg')
    config_by_member = factory.Faker('boolean')


class InteractionTypeFactory(DjangoModelFactory):
    class Meta:
        model = InteractionType

    name = factory.Faker('uuid4')  # This is a workaround for the primary key
    public_name = factory.Faker('sentence')
    way = factory.Faker('random_element', elements=['in', 'out', 'inout'])
    group_type = factory.Faker(
        'random_element',
        elements=[
            'interactive', 'text', 'reply_button', 'media', 'event',
            'special', 'references', 'other'
        ]
    )


class ApiRecordFactory(DjangoModelFactory):
    class Meta:
        model = ApiRecord

    platform = factory.SubFactory(PlatformFactory)
    body = safe_pydict()
    interaction_type = factory.SubFactory(InteractionTypeFactory)
    is_incoming = factory.Faker('boolean')
    response_status = factory.Faker('random_int', min=100, max=599)
    response_body = safe_pydict()
    repeated = factory.LazyAttribute(
        lambda _: optional_sub_factory(ApiRecordFactory, lazy=True)
    )
    error_text = factory.Faker('text')
    errors = safe_pydict()
    success = factory.Faker('boolean')
    created = factory.Faker('date_time')
    datetime = factory.Faker('unix_time')
