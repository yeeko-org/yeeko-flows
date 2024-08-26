from django.test import TestCase
from infrastructure.box.models import (
    Written, Piece, Fragment, Reply, MessageLink, Destination
)
from infrastructure.box.factories import (
    DestinationFactory, FragmentFactory, ReplyFactory, WrittenFactory,
    PieceFactory, MessageLinkFactory
)


class WrittenTest(TestCase):
    def test_create_written(self):
        written_instance = WrittenFactory()
        self.assertIsInstance(written_instance, Written)


class PieceTest(TestCase):
    def test_create_piece(self):
        piece_instance = PieceFactory()
        self.assertIsInstance(piece_instance, Piece)


class FragmentTest(TestCase):
    def test_create_fragment(self):
        fragment_instance = FragmentFactory()
        self.assertIsInstance(fragment_instance, Fragment)


class ReplyTest(TestCase):
    def test_create_reply(self):
        reply_instance = ReplyFactory()
        self.assertIsInstance(reply_instance, Reply)


class MessageLinkTest(TestCase):
    def test_create_message_link(self):
        message_link_instance = MessageLinkFactory()
        self.assertIsInstance(message_link_instance, MessageLink)


class DestinationTest(TestCase):
    def test_create_destination(self):
        destination_instance = DestinationFactory()
        self.assertIsInstance(destination_instance, Destination)
