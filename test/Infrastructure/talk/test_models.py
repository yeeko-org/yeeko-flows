
from django.test import TestCase
from infrastructure.talk.models import (
    Trigger, Interaction, BuiltReply, Event, ExtraValue
)
from infrastructure.talk.factories import (
    TriggerFactory, InteractionFactory, BuiltReplyFactory, EventFactory,
    ExtraValueFactory
)


class TriggerTestCase(TestCase):
    def test_create_trigger(self):
        trigger_instance = TriggerFactory()
        self.assertIsInstance(trigger_instance, Trigger)


class InteractionTestCase(TestCase):
    def test_create_interaction(self):
        interaction_instance = InteractionFactory()
        self.assertIsInstance(interaction_instance, Interaction)


class BuiltReplyTestCase(TestCase):
    def test_create_built_reply(self):
        built_reply_instance = BuiltReplyFactory()
        self.assertIsInstance(built_reply_instance, BuiltReply)


class EventTestCase(TestCase):
    def test_create_event(self):
        event_instance = EventFactory()
        self.assertIsInstance(event_instance, Event)


class ExtraValueTestCase(TestCase):
    def test_create_extra_value(self):
        extra_value_instance = ExtraValueFactory()
        self.assertIsInstance(extra_value_instance, ExtraValue)
