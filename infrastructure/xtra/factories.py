import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from infrastructure.flow.factories import FlowFactory
from infrastructure.place.factories import SpaceFactory
from infrastructure.xtra.models import ClassifyExtra, Format, Extra, PresetValue

from utilities.factory_util import optional_sub_factory


class ClassifyExtraFactory(DjangoModelFactory):
    class Meta:
        model = ClassifyExtra

    name = factory.Faker('uuid4')  # This is a workaround for the primary key
    public_name = factory.Faker('word')
    description = factory.Faker('text')
    only_developers = factory.fuzzy.FuzzyChoice([True, False])
    user_visible = factory.Faker('word')
    is_public = factory.fuzzy.FuzzyChoice([True, False])
    order = factory.fuzzy.FuzzyInteger(1, 10)
    icon = factory.Faker('word')
    pixel_excel = factory.fuzzy.FuzzyInteger(100, 200)
    settings = {}


class FormatFactory(DjangoModelFactory):
    class Meta:
        model = Format

    name = factory.Faker('uuid4')  # This is a workaround for the primary key
    public_name = factory.Faker('word')
    javascript_name = factory.Faker('word')
    python_name = factory.Faker('word')
    params = {}


class ExtraFactory(DjangoModelFactory):
    class Meta:
        model = Extra

    name = factory.Faker('uuid4') # This is a workaround for the primary key
    classify = factory.SubFactory(ClassifyExtraFactory)
    space = factory.SubFactory(SpaceFactory)
    flow = optional_sub_factory(FlowFactory)
    format = optional_sub_factory(FormatFactory)
    description = factory.Faker('text')
    params = {}
    deleted = factory.fuzzy.FuzzyChoice([True, False])


class PresetValueFactory(DjangoModelFactory):
    class Meta:
        model = PresetValue

    extra = factory.SubFactory(ExtraFactory)
    value = factory.Faker('word')
    deleted = factory.fuzzy.FuzzyChoice([True, False])
