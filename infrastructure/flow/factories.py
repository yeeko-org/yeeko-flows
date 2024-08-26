import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from infrastructure.flow.models import Crate, CrateType, Flow
from infrastructure.place.factories import SpaceFactory


class FlowFactory(DjangoModelFactory):
    class Meta:
        model = Flow

    name = factory.Faker('word')
    space = factory.SubFactory(SpaceFactory)
    description = factory.Faker('text')
    has_definitions = factory.fuzzy.FuzzyChoice([True, False])
    deleted = factory.fuzzy.FuzzyChoice([True, False])


class CrateTypeFactory(DjangoModelFactory):
    class Meta:
        model = CrateType

    name = factory.Faker('uuid4')  # This is a workaround for the primary key
    public_name = factory.Faker('word')
    description = factory.Faker('text')


class CrateFactory(DjangoModelFactory):
    class Meta:
        model = Crate

    name = factory.Faker('word')
    description = factory.Faker('text')
    crate_type = factory.SubFactory(CrateTypeFactory)
    flow = factory.SubFactory(FlowFactory)
    has_templates = factory.fuzzy.FuzzyChoice([True, False])
