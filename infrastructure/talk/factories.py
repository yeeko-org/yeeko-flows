
import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from infrastructure.assign.factories import ApplyBehaviorFactory
from infrastructure.box.factories import MessageLinkFactory, ReplyFactory
from infrastructure.member.factories import MemberAccountFactory, MemberFactory
from infrastructure.service.factories import ApiRecordFactory, InteractionTypeFactory

from infrastructure.talk.models import BuiltReply, ExtraValue, Interaction, Trigger, Event
from infrastructure.xtra.factories import ExtraFactory
from utilities.factory_util import optional_sub_factory, safe_pydict


class TriggerFactory(DjangoModelFactory):
    class Meta:
        model = Trigger

    interaction_reply = factory.LazyAttribute(
        lambda _: optional_sub_factory(InteractionFactory, lazy=True)
    )
    built_reply = factory.LazyAttribute(
        lambda _: optional_sub_factory(BuiltReplyFactory, lazy=True)
    )
    message_link = optional_sub_factory(MessageLinkFactory)
    is_direct = factory.fuzzy.FuzzyChoice([True, False])


class InteractionFactory(DjangoModelFactory):
    class Meta:
        model = Interaction

    mid = factory.Faker('uuid4')
    interaction_type = factory.SubFactory(InteractionTypeFactory)
    is_incoming = factory.Faker('boolean')
    member_account = factory.SubFactory(MemberAccountFactory)
    trigger = optional_sub_factory(TriggerFactory)
    api_record_out = factory.SubFactory(ApiRecordFactory)
    persona = optional_sub_factory(MemberAccountFactory)
    created = factory.Faker('date_time_this_year')
    timestamp = factory.Faker('unix_time')
    raw_payload = factory.Faker('text')
    reference = safe_pydict()
    apply_behavior = optional_sub_factory(ApplyBehaviorFactory)


class BuiltReplyFactory(DjangoModelFactory):
    class Meta:
        model = BuiltReply

    interaction = factory.SubFactory(InteractionFactory)
    is_for_reply = factory.fuzzy.FuzzyChoice([True, False])
    is_for_write = factory.fuzzy.FuzzyChoice([True, False])
    params = {}
    payload = factory.Faker('text')
    reply = optional_sub_factory(ReplyFactory)


class EventFactory(DjangoModelFactory):
    class Meta:
        model = Event

    event_name = factory.fuzzy.FuzzyChoice(
        ['received', 'sent', 'delivered', 'read', 'optin', 'referral', 'failed', 'deleted', 'warning', 'reaction'])
    api_request = optional_sub_factory(ApiRecordFactory)
    timestamp = factory.fuzzy.FuzzyInteger(1, 100)
    emoji = factory.Faker('word')
    interaction = factory.SubFactory(InteractionFactory)
    date = factory.Faker('date_time')
    content = {}


class ExtraValueFactory(DjangoModelFactory):
    class Meta:
        model = ExtraValue

    extra = factory.SubFactory(ExtraFactory)
    member = optional_sub_factory(MemberFactory)
    origin = factory.fuzzy.FuzzyChoice(
        ['payload', 'written', 'dictionary', 'assigned', 'unknown'])
    modified = factory.Faker('date_time')
    value = factory.Faker('text')
    list_by = factory.LazyAttribute(
        lambda _: optional_sub_factory(ExtraValueFactory, lazy=True)
    )
    value_bool = factory.fuzzy.FuzzyChoice([True, False])
