
import factory
from factory.django import DjangoModelFactory

from infrastructure.box.models import (
    Destination, Fragment, MessageLink, Piece, Reply, Written
)
from infrastructure.flow.factories import CrateFactory
from infrastructure.place.factories import AccountFactory
from infrastructure.tool.factories import BehaviorFactory, CollectionFactory
from infrastructure.xtra.factories import ExtraFactory
from utilities.factory_util import optional_sub_factory, safe_pydict


class WrittenFactory(DjangoModelFactory):
    class Meta:
        model = Written

    extra = optional_sub_factory(ExtraFactory)
    collection = optional_sub_factory(CollectionFactory)
    available = factory.Faker('boolean')


class PieceFactory(DjangoModelFactory):
    class Meta:
        model = Piece

    crate = factory.SubFactory(CrateFactory)
    name = factory.Faker('word')
    description = factory.Faker('sentence')
    behavior = optional_sub_factory(BehaviorFactory)
    default_extra = optional_sub_factory(ExtraFactory)
    insistent = factory.Faker('boolean')
    mandatory = factory.Faker('boolean')
    config = safe_pydict()
    written = optional_sub_factory(WrittenFactory)
    order_in_crate = factory.Faker('pyint')
    deleted = factory.Faker('boolean')


class FragmentFactory(DjangoModelFactory):
    class Meta:
        model = Fragment

    piece = factory.SubFactory(PieceFactory)
    order = factory.Faker('pyint')
    deleted = factory.Faker('boolean')
    addl_params = safe_pydict()

    behavior = optional_sub_factory(BehaviorFactory)

    header = factory.Faker('word')
    body = factory.Faker('text')
    footer = factory.Faker('word')
    reply_title = factory.Faker('word')

    file = factory.django.ImageField()
    media_url = factory.Faker('url')
    media_type = factory.Faker(
        'random_element',
        elements=['image', 'video', 'audio', 'file', 'sticker']
    )

    embedded_piece = optional_sub_factory(PieceFactory)


class ReplyFactory(DjangoModelFactory):
    class Meta:
        model = Reply

    fragment = factory.SubFactory(FragmentFactory)
    destination = factory.LazyAttribute(
        lambda _: optional_sub_factory(DestinationFactory, lazy=True)
    )
    title = factory.Faker('word')
    description = factory.Faker('word')
    large_title = factory.Faker('word')
    addl_params = safe_pydict()
    context = safe_pydict()
    order = factory.Faker('pyint')
    is_jump = factory.Faker('boolean')
    use_piece_config = factory.Faker('boolean')
    deleted = factory.Faker('boolean')


class MessageLinkFactory(DjangoModelFactory):
    class Meta:
        model = MessageLink

    account = factory.SubFactory(AccountFactory)
    link = factory.Faker('url')
    message = factory.Faker('word')
    qr_code_png = factory.django.ImageField()
    qr_code_svg = factory.django.ImageField()


class DestinationFactory(DjangoModelFactory):
    class Meta:
        model = Destination

    destination_type = factory.Faker(
        'random_element', elements=['url', 'behavior', 'piece']
    )
    piece = optional_sub_factory(PieceFactory)
    piece_dest = optional_sub_factory(PieceFactory)
    behavior = optional_sub_factory(BehaviorFactory)
    reply = optional_sub_factory(ReplyFactory)
    written = optional_sub_factory(WrittenFactory)
    message_link = optional_sub_factory(MessageLinkFactory)
    addl_params = safe_pydict()
    url = factory.Faker('url')
    is_default = factory.Faker('boolean')
    order = factory.Faker('pyint')
    deleted = factory.Faker('boolean')
