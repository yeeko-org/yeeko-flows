"""The piece's «next», slot fragments, the real button tap and the quote of
an inactive capture, on a toy flow driven through `ManagerFlow`.

Run:
    .venv/bin/python manage.py test test.services.processor --noinput
"""
import gc
from unittest.mock import patch

from django.test import TestCase

import services.behavior as generic_behaviors
from infrastructure.box.models import Piece, Reply, Written
from infrastructure.place.models import Space
from infrastructure.talk.models import Interaction
from projects.caceh.flow_driver import FlowDriver, text_payload
from services.seeder.builder import FlowSeeder

WA_ID = "5215500000071"


class ToyUnit:
    """Stands in for a capture unit: shown, it sends its question through
    its own fragment and reports nothing, so the piece must stay put."""

    def __init__(self, response, fragment_id=None, **kwargs):
        response.message_text("Pregunta de la unidad", fragment_id=fragment_id)


@patch.object(generic_behaviors, "toy_unit", ToyUnit, create=True)
class PieceNextTest(TestCase):
    # Space 1 + Account (pid 103571329211620) + Platform whatsapp.
    fixtures = ["test/fixtures/account_fixture.json"]

    def setUp(self):
        self.sdr = FlowSeeder(
            Space.objects.get(pk=1), "toy", {"t": "Toy"})
        self.sdr.declare_extras(
            [("nombre", None), ("ciudad", None)], classify_name="toy")
        self.unit_behavior = self.sdr.ensure_behavior(
            "toy_unit", generic=True)
        self.d = FlowDriver(WA_ID)

    def tearDown(self):
        gc.collect()

    def _piece(self, name: str) -> Piece:
        return self.sdr.piece("t", name, name)

    def _capture_without_destination(self, piece: Piece, prompt: str,
                                     extra: str) -> None:
        self.sdr.msg(piece, prompt)
        piece.written = Written.objects.create(
            extra=self.sdr.extras[extra], available=True)
        piece.save(update_fields=["written"])

    def _start_at(self, piece: Piece) -> None:
        self.sdr.wire_global_start(piece)
        self.d.send("hola")

    def test_slot_fragments_are_not_painted(self):
        p = self._piece("p")
        self.sdr.msg(p, "Visible")
        self.sdr.slot(p, self.unit_behavior, "question", "Oculto", order=10)

        self._start_at(p)

        self.assertEqual(self.d.bot_texts(), ["Visible"])

    def test_message_only_piece_follows_next_and_unit_piece_waits(self):
        end = self._piece("end")
        self.sdr.msg(end, "Fin")
        info = self._piece("info")
        self.sdr.msg(info, "Solo aviso")
        self.sdr.link(info, end)

        self._start_at(info)

        self.assertEqual(self.d.bot_texts(), ["Solo aviso", "Fin"])
        self.assertEqual(self.d.at_piece(), "end")

        unit = self._piece("unit")
        self.sdr._fragment(
            unit, 0, fragment_type="behavior", behavior=self.unit_behavior)
        self.sdr.link(unit, end)
        self.d = FlowDriver("5215500000072")

        self._start_at(unit)

        self.assertEqual(self.d.bot_texts(), ["Pregunta de la unidad"])
        self.assertEqual(self.d.at_piece(), "unit")

    def test_capture_without_destination_goes_to_piece_next(self):
        end = self._piece("end")
        self.sdr.msg(end, "Gracias")
        ask = self._piece("ask")
        self._capture_without_destination(ask, "¿Cómo te llamas?", "nombre")
        self.sdr.link(ask, end)
        self._start_at(ask)

        self.d.send("Juana")

        self.assertEqual(self.d.extras().get("nombre"), "Juana")
        self.assertEqual(self.d.bot_texts(), ["Gracias"])

    def test_real_tap_without_destination_goes_to_piece_next(self):
        end = self._piece("end")
        self.sdr.msg(end, "Seguimos")
        ask = self._piece("ask")
        frag = self.sdr.msg(ask, "¿Empezamos?")
        Reply.objects.create(
            fragment=frag, order=0, reply_type="quick_reply", title="Sí")
        self.sdr.link(ask, end)
        self._start_at(ask)

        self.d.press("Sí", piece="ask")

        self.assertEqual(self.d.bot_texts(), ["Seguimos"])
        self.assertEqual(self.d.at_piece(), "end")

    def test_quote_of_inactive_capture_does_not_store_again(self):
        end = self._piece("end")
        self.sdr.msg(end, "Listo")
        city = self._piece("city")
        self._capture_without_destination(city, "¿En qué ciudad?", "ciudad")
        self.sdr.link(city, end)
        name = self._piece("name")
        self._capture_without_destination(name, "¿Cómo te llamas?", "nombre")
        self.sdr.link(name, city)
        self._start_at(name)
        name_question = Interaction.objects.get(
            fragment__piece=name, is_incoming=False)
        self.d.send("Juana")
        self.assertEqual(self.d.at_piece(), "city")

        self.d._run(text_payload(
            WA_ID, "Pedro", context_id=name_question.mid))

        extras = self.d.extras()
        self.assertEqual(extras.get("nombre"), "Juana")
        self.assertNotIn("ciudad", extras)
        self.assertEqual(self.d.at_piece(), "city")
