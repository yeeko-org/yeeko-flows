"""The capture unit `open_question` on a toy flow driven through
`ManagerFlow`, with a scripted Gemini (no key needed).

Run:
    .venv/bin/python manage.py test test.services.processor --noinput
"""
import gc
from typing import Literal, Optional
from unittest.mock import patch

from django.test import TestCase
from pydantic import BaseModel, field_validator

from infrastructure.box.models import Piece
from infrastructure.place.models import Space
from infrastructure.talk.models import Interaction
from projects.caceh.flow_driver import FlowDriver, text_payload
from services.behavior.extraction import SCHEMA_REGISTRY
from services.behavior.open_question import (
    CORRECTION_FAILED_TEXT, FIRST_RECAP_HINT, NOTICE_TEXT)
from services.seeder.builder import FlowSeeder

WA_ID = "5215500000081"
MUST_BE_POSITIVE = "El monto tiene que ser mayor a cero."


class ToyPay(BaseModel):
    monto: Optional[int] = None
    periodo: Optional[str] = None
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None

    @field_validator("monto")
    @classmethod
    def positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError(MUST_BE_POSITIVE)
        return v


class ToyDays(BaseModel):
    dias: Optional[list[str]] = None
    ia_completed: Literal["si", "no"]
    ia_pregunta: Optional[str] = None


def pay(monto, periodo="semanal", done="si", **extra):
    return {"monto": monto, "periodo": periodo, "ia_completed": done,
            "ia_pregunta": None, **extra}


DAYS_OK = {"dias": ["lunes", "martes"], "ia_completed": "si",
           "ia_pregunta": None}
DAYS_MISSING = {"dias": None, "ia_completed": "no",
                "ia_pregunta": "¿Qué días se trabaja?"}


class ScriptedGemini:
    """Answers each `extract` call with the next scripted dict."""

    def __init__(self):
        self.script: list = []
        self.errors: list = []

    def extract(self, system_prompt, user_text, schema):
        if not self.script:
            raise AssertionError(f"Gemini sin guion para: {user_text!r}")
        return self.script.pop(0)


@patch.dict(SCHEMA_REGISTRY, {"toy_pay": (ToyPay, "pago"),
                              "toy_days": (ToyDays, "días")})
class OpenQuestionTest(TestCase):
    # Space 1 + Account (pid 103571329211620) + Platform whatsapp.
    fixtures = ["test/fixtures/account_fixture.json"]

    def setUp(self):
        self.gemini = ScriptedGemini()
        patcher = patch("services.behavior.open_question.GeminiClient",
                        return_value=self.gemini)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.sdr = FlowSeeder(Space.objects.get(pk=1), "toy", {"t": "Toy"})
        self.sdr.declare_extras(
            [("monto", None), ("periodo", None), ("dias", "json"),
             ("_hist_toy_pay", "json"), ("_hist_toy_days", "json"),
             ("_first_recap_sent", None)], classify_name="toy")
        self.d = FlowDriver(WA_ID)

    def tearDown(self):
        gc.collect()

    # -------------------------------------------------------------- flow
    def _build(self, pay_confirmation: bool = True) -> None:
        end = self.sdr.piece("t", "end", "end")
        self.sdr.msg(end, "Fin")
        self.buttons = self.sdr.piece("t", "boton", "boton")
        self.sdr.buttons(self.buttons, "¿Seguimos?",
                         [("Sí", end, None), ("No", end, None)])
        self.days = self._unit("dias", "toy_days", {
            "question": "¿Qué días se trabaja?",
            "recap": "Los días quedaron así: {{dias}}.",
            "correction_request": "Escribe de nuevo los días."})
        self.sdr.link(self.days, self.buttons)
        self.pay = self._unit("pago", "toy_pay", {
            "question": "¿Cuánto es el pago?",
            "recap": "El pago quedó así: ${{monto}} {{periodo}}.",
            "correction_request": "Escribe de nuevo el pago.",
            "give_up": "No logré entender ese dato."},
            with_confirmation=pay_confirmation)
        self.sdr.link(self.pay, self.days)
        self.sdr.wire_global_start(self.pay)
        self.d.send("hola")

    def _unit(self, name: str, schema: str, slots: dict,
              **params) -> Piece:
        piece = self.sdr.piece("t", name, name)
        self.sdr.unit(piece, "open_question", slots=slots,
                      params={"schema": schema, **params})
        return piece

    def _answer(self, text: str, *scripted) -> list[str]:
        self.gemini.script.extend(scripted)
        self.d.send(text, with_context=False)
        return self.d.bot_texts()

    def _quote(self, interaction: Interaction, text: str,
               *scripted) -> list[str]:
        self.gemini.script.extend(scripted)
        self.d._run(text_payload(WA_ID, text, context_id=interaction.mid))
        return self.d.bot_texts()

    def _last(self, piece: Piece, slot: str) -> Interaction:
        return Interaction.objects.filter(
            is_incoming=False, fragment__piece=piece,
            fragment__slot__name=slot).order_by("created").last()

    # ------------------------------------------------------------- tests
    def test_invalid_datum_is_never_stored(self):
        self._build()
        # Answer mode: three re-asks, the fourth failure gives up.
        for _ in range(3):
            texts = self._answer("menos cinco", pay(-5))
            self.assertEqual(texts, [MUST_BE_POSITIVE])
            self.assertNotIn("monto", self.d.extras())
        texts = self._answer("menos cinco", pay(-5))
        self.assertEqual(
            texts, ["No logré entender ese dato.", "¿Qué días se trabaja?"])
        self.assertNotIn("monto", self.d.extras())
        self.assertEqual(self.d.at_piece(), "dias")

        # Correction mode: the stored value survives an invalid correction,
        # and running out of re-asks says so before resending what was
        # pending.
        self.d = FlowDriver("5215500000082")
        self.d.send("hola")
        self._answer("300 a la semana", pay(300))
        self.d.press("Corregir", piece="pago")
        for _ in range(3):
            texts = self._answer("menos cinco", pay(-5))
            self.assertEqual(texts, [MUST_BE_POSITIVE])
            self.assertEqual(self.d.extras().get("monto"), "300")
        texts = self._answer("menos cinco", pay(-5))
        self.assertEqual(
            texts, [CORRECTION_FAILED_TEXT, "¿Qué días se trabaja?"])
        self.assertEqual(self.d.extras().get("monto"), "300")
        self.assertEqual(self.d.at_piece(), "dias")

    def test_hint_only_on_first_recap_and_no_recap_without_confirmation(
            self):
        self._build()
        texts = self._answer("300 a la semana", pay(300))
        self.assertEqual(texts, [
            "El pago quedó así: $300 semanal.\n\n" + FIRST_RECAP_HINT,
            "¿Qué días se trabaja?"])
        texts = self._answer("lunes y martes", DAYS_OK)
        self.assertEqual(texts[0], "Los días quedaron así: lunes, martes.")

        self.d = FlowDriver("5215500000083")
        self._build(pay_confirmation=False)
        texts = self._answer("300 a la semana", pay(300))
        self.assertEqual(texts, ["¿Qué días se trabaja?"])
        self.assertEqual(self.d.extras().get("monto"), "300")

    def test_four_ways_of_quoting_a_recap(self):
        self._build()
        self._answer("300 a la semana", pay(300))
        recap = self._last(self.pay, "recap")
        question = "¿Qué días se trabaja?"

        texts = self._quote(recap, "¿y la hora?", {"intent": "other"})
        self.assertEqual(texts, [NOTICE_TEXT, question])

        texts = self._quote(recap, "sí", {"intent": "confirm"})
        self.assertEqual(texts, [question])

        texts = self._quote(recap, "no, 350",
                            pay(350, periodo=None, intent="correct"))
        self.assertEqual(
            texts, ["El pago quedó así: $350 semanal.", question])
        self.assertEqual(self.d.extras().get("periodo"), "semanal")

        texts = self._quote(recap, "quiero corregir", {"intent": "request"})
        self.assertEqual(texts, ["Escribe de nuevo el pago."])
        self.assertEqual(self.d.at_piece(), "pago")

    def test_corregir_later_returns_to_what_was_pending(self):
        self._build()
        self._answer("300 a la semana", pay(300))
        reask = self._answer("no sé", DAYS_MISSING)
        self.assertEqual(reask, ["¿Qué días se trabaja?"])

        self.d.press("Corregir", piece="pago")
        self.assertEqual(self.d.bot_texts(), ["Escribe de nuevo el pago."])
        texts = self._answer("400", pay(400, periodo=None))
        self.assertEqual(
            texts, ["El pago quedó así: $400 semanal.", reask[0]])
        # The re-ask went out again through its own slot, so the next
        # answer still goes to the days unit.
        self.assertEqual(self.d._last_out(with_fragment=True).fragment,
                         self._last(self.days, "question").fragment.piece
                         .fragments.get(slot__name="reask"))

        self._answer("lunes y martes", DAYS_OK)
        self.assertEqual(self.d.at_piece(), "boton")
        self.d.press("Corregir", piece="pago")
        self._answer("500", pay(500, periodo=None))
        self.assertEqual(self.d.bot_texts(), [
            "El pago quedó así: $500 semanal.", "¿Seguimos?"])
        self.assertEqual(self.d.bot_buttons(), ["Corregir", "Sí", "No"])
        self.assertEqual(self.d.at_piece(), "boton")
