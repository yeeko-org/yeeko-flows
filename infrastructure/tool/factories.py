
import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from infrastructure.service.factories import InteractionTypeFactory
from infrastructure.tool.models import Collection, Behavior, Parameter
from utilities.factory_util import optional_sub_factory



class CollectionFactory(DjangoModelFactory):
    class Meta:
        model = Collection

    name = factory.Faker('uuid4')  # This is a workaround for the primary key
    public_name = factory.Faker('word')
    is_custom = factory.fuzzy.FuzzyChoice([True, False])
    open_available = factory.fuzzy.FuzzyChoice([True, False])
    app_label = factory.Faker('word')


class BehaviorFactory(DjangoModelFactory):
    class Meta:
        model = Behavior

    name = factory.Faker('uuid4')  # This is a workaround for the primary key
    collection = factory.SubFactory(CollectionFactory)
    can_piece = factory.fuzzy.FuzzyChoice([True, False])
    can_destination = factory.fuzzy.FuzzyChoice([True, False])
    in_code = factory.fuzzy.FuzzyChoice([True, False])
    interaction_type = optional_sub_factory(InteractionTypeFactory)


class ParameterFactory(DjangoModelFactory):
    class Meta:
        model = Parameter

    behavior = factory.SubFactory(BehaviorFactory)
    name = factory.Faker('word')
    public_name = factory.Faker('word')
    description = factory.Faker('text')
    is_required = factory.fuzzy.FuzzyChoice([True, False])
    default_value = factory.Faker('word')
    data_type = factory.fuzzy.FuzzyChoice(
        ['integer', 'string', 'boolean', 'json', 'any', 'foreign_key'])
    customizable_by_piece = factory.fuzzy.FuzzyChoice([True, False])
    addl_config = {}
    rules = {}
    model = factory.fuzzy.FuzzyChoice(
        ['piece', 'fragment', 'yeekonsult', 'reply'])
    order = factory.fuzzy.FuzzyInteger(1, 100)
    addl_dashboard = {}
    deleted = factory.fuzzy.FuzzyChoice([True, False])
