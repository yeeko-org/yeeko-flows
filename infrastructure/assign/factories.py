from factory.django import DjangoModelFactory
import factory
from infrastructure.assign.models import (
    Assign, ApplyBehavior, ConditionRule, ParamValue
)
from infrastructure.box.factories import (
    DestinationFactory, FragmentFactory, PieceFactory, ReplyFactory,
    WrittenFactory
)
from infrastructure.xtra.factories import ExtraFactory
from infrastructure.tool.factories import (
    BehaviorFactory, ParameterFactory
)
from infrastructure.place.factories import (
    PlatformFactory, SpaceFactory
)
from utilities.factory_util import optional_sub_factory, safe_pydict


class ConditionRuleFactory(DjangoModelFactory):
    class Meta:
        model = ConditionRule

    appear = factory.Faker('boolean')
    fragment = optional_sub_factory(FragmentFactory)
    reply = optional_sub_factory(ReplyFactory)
    destination = optional_sub_factory(DestinationFactory)
    platforms = factory.PostGeneration(factory.SubFactory(PlatformFactory))
    circles = factory.PostGeneration(factory.SubFactory(ExtraFactory))
    extra = optional_sub_factory(ExtraFactory)
    extra_values = safe_pydict()
    addl_params = safe_pydict()
    extra_exits = factory.Faker('boolean')
    opposite = factory.Faker('boolean')

    @factory.post_generation
    def platforms(self, create, extracted, **kwargs):
        if extracted:
            if isinstance(extracted, list):
                self.platforms.set(extracted)  # type: ignore
            else:
                self.platforms.add(extracted)  # type: ignore

    @factory.post_generation
    def circles(self, create, extracted, **kwargs):
        if extracted:
            if isinstance(extracted, list):
                self.circles.set(extracted)  # type: ignore
            else:
                self.circles.add(extracted)  # type: ignore


class AssignFactory(DjangoModelFactory):
    class Meta:
        model = Assign

    circles = factory.PostGeneration(factory.SubFactory(ExtraFactory))
    extra = optional_sub_factory(ExtraFactory)
    extra_value = safe_pydict()
    is_remove = factory.Faker('boolean')
    piece = optional_sub_factory(PieceFactory)
    reply = optional_sub_factory(ReplyFactory)
    destination = optional_sub_factory(DestinationFactory)
    written = optional_sub_factory(WrittenFactory)
    deleted = factory.Faker('boolean')

    @factory.post_generation
    def circles(self, create, extracted, **kwargs):
        if extracted:
            if isinstance(extracted, list):
                self.circles.set(extracted)  # type: ignore
            else:
                self.circles.add(extracted)  # type: ignore


class ApplyBehaviorFactory(DjangoModelFactory):
    class Meta:
        model = ApplyBehavior

    behavior = factory.SubFactory(BehaviorFactory)
    space = factory.SubFactory(SpaceFactory)
    main_piece = optional_sub_factory(PieceFactory)


class ParamValueFactory(DjangoModelFactory):
    class Meta:
        model = ParamValue

    parameter = factory.SubFactory(ParameterFactory)
    apply_behavior = optional_sub_factory(
        ApplyBehaviorFactory)
    fragment = optional_sub_factory(FragmentFactory)
    destination = optional_sub_factory(DestinationFactory)
    piece = optional_sub_factory(PieceFactory)
    reply = optional_sub_factory(ReplyFactory)
    value = factory.Faker('word')
