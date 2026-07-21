"""Arnés del cableado de WP6B: siembra el flujo y confirma que un paso ⚙️
dispara su behavior por el MOTOR REAL (FragmentProcessor -> BehaviorProcessor),
no llamando la clase a mano. Así se ejercita lo que WP6B agrega: la resolución
del behavior (genérica para ia_extrae; por app_label para los de proyecto) y la
inyección de esquema/entrada por ParamValue de fragmento.

Sin WhatsApp real, sin Gemini real (mockeado como en test_ia_extrae).

Correr: .venv/bin/python manage.py test projects.caceh
"""

from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from infrastructure.box.models import Destination, Fragment, Piece, Reply
from infrastructure.member.factories import (
    MemberAccountFactory, MemberFactory)
from infrastructure.place.factories import SpaceFactory
from infrastructure.service.factories import (
    ApiRecordFactory, InteractionTypeFactory)
from infrastructure.talk.models import Interaction
from infrastructure.xtra.models import Extra, Format

from services.processor.fragment import FragmentProcessor


class StubResponse:
    """Response mínimo para el motor: delega add_extra_value en el member, junta
    errores y absorbe set_trigger/message_multimedia (que el ResponseAbc real
    usa para trazas y envío) sin tocar esa maquinaria."""

    def __init__(self, member, space):
        self.sender = SimpleNamespace(
            member=member, account=SimpleNamespace(space=space))
        self.errors = []
        self.media_messages = []

    def set_trigger(self, *args, **kwargs):
        pass

    def message_multimedia(self, **kwargs):
        self.media_messages.append(kwargs)

    def add_extra_value(
            self, extra, value=None, interaction=None,
            origin="unknown", list_by=None):
        return self.sender.member.add_extra_value(
            extra, value, interaction, origin, list_by)

    def add_error(self, data, e=None):
        self.errors.append(data)


class SeedFlowBehaviorHarness(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.space = SpaceFactory()
        # Los Format que el seed asigna a los extras de lista/entero; en la BD
        # de test no vienen por defecto (los crea get_or_create, como en los
        # demás tests). Deben existir ANTES de sembrar.
        Format.objects.get_or_create(name="json")
        Format.objects.get_or_create(name="int")
        call_command("seed_flow", space=cls.space.pk)

    def setUp(self):
        self.member = MemberFactory(space=self.space)
        self.response = StubResponse(self.member, self.space)

    # --- helpers -----------------------------------------------------------
    def _extra(self, name):
        return Extra.objects.get(name=name, space=self.space)

    def _set(self, name, value):
        self.member.add_extra_value(self._extra(name), value, None, "test")

    def _behavior_fragment(self, piece_name):
        piece = Piece.objects.get(
            crate__flow__space=self.space, name=piece_name)
        return piece.fragments.get(fragment_type="behavior")

    def _data(self):
        return self.member.get_extra_values_data(refrest=True)

    # --- tests -------------------------------------------------------------
    def test_a5_asigna_partes_se_dispara_por_app_label(self):
        # Behavior de proyecto: el motor lo resuelve por la Collection caceh
        # (app_label projects.caceh). Sin params.
        self.member.user.phone = "5215551234567"
        self.member.user.save()
        self._set("operador", "trabajadora")
        self._set("operador_nombre", "Juana Pérez López")
        self._set("contraparte_nombre", "Marcela Ruiz Soto")

        FragmentProcessor(
            self._behavior_fragment("a_asigna_partes"), self.response).process()

        data = self._data()
        self.assertEqual(data["trab_nombre_completo"], "Juana Pérez López")
        self.assertEqual(data["empl_nombre_completo"], "Marcela Ruiz Soto")
        self.assertEqual(data["telefono_operador"], "5215551234567")
        self.assertEqual(self.response.errors, [])

    @patch("services.behavior.ia_extrae.GeminiClient")
    def test_b2_ia_extrae_se_dispara_con_esquema_de_paramvalue(self, MockG):
        # Behavior genérico reusado: el esquema correcto ("jornada") y la
        # entrada ({{respuesta_jornada}}) llegan por ParamValue de ESTE
        # fragmento, no del ApplyBehavior (compartido por B2/C5/C10).
        MockG.return_value.extract.return_value = {
            "hora_entrada": "8:00", "hora_salida": "16:00",
            "dias_laborables": ["lunes", "martes", "miércoles", "jueves",
                                "viernes"],
            "ia_completed": "si", "ia_pregunta": None}
        self._set("respuesta_jornada", "de lunes a viernes de 8 a 4")

        FragmentProcessor(
            self._behavior_fragment("b_ia_jornada"), self.response).process()

        data = self._data()
        self.assertEqual(data["hora_entrada"], "8:00")
        self.assertEqual(data["hora_salida"], "16:00")
        self.assertEqual(data["dias_laborables"][0], "lunes")
        self.assertEqual(data["ia_completed"], "si")
        self.assertEqual(self.response.errors, [])

        # el esquema jornada y la entrada resuelta llegaron a Gemini
        args = MockG.return_value.extract.call_args.args
        self.assertEqual(args[2].__name__, "Jornada")          # schema
        self.assertIn("de lunes a viernes de 8 a 4", args[1])  # entrada


class SeedIdempotencyTests(TestCase):
    """El seed es upsert, no rebuild: resembrar conserva los PKs de
    Piece/Fragment/Reply (sobreviven el historial de Interaction, los
    BuiltReply de mensajes ya enviados y las sesiones en curso) y regresa
    la BD al estado declarado."""

    @classmethod
    def setUpTestData(cls):
        cls.space = SpaceFactory()
        Format.objects.get_or_create(name="json")
        Format.objects.get_or_create(name="int")
        call_command("seed_flow", space=cls.space.pk)

    def _snapshot(self) -> dict[str, set]:
        pieces = Piece.objects.filter(crate__flow__space=self.space)
        frags = Fragment.objects.filter(piece__in=pieces)
        return {
            "pieces": set(pieces.values_list("id", flat=True)),
            "fragments": set(frags.values_list("id", flat=True)),
            "replies": set(Reply.objects.filter(fragment__in=frags)
                           .values_list("id", flat=True)),
            "destinations": set(
                Destination.objects.filter(piece_dest__in=pieces)
                .values_list("id", flat=True)),
        }

    def test_resembrar_conserva_pks_y_no_duplica(self):
        before = self._snapshot()
        call_command("seed_flow", space=self.space.pk)
        self.assertEqual(self._snapshot(), before)

    def test_resembrar_conserva_interacciones(self):
        # Interaction.fragment es CASCADE: con el rebuild viejo esta
        # interacción moría en cada resiembra.
        frag = Piece.objects.get(
            crate__flow__space=self.space,
            name="a_saludo").fragments.first()
        # A mano (InteractionFactory está desactualizada: pasa raw_payload,
        # campo que ya no existe en el modelo).
        interaction = Interaction.objects.create(
            mid="wamid.test-idempotencia", is_incoming=False,
            interaction_type=InteractionTypeFactory(),
            member_account=MemberAccountFactory(),
            api_record_out=ApiRecordFactory(), fragment=frag)
        call_command("seed_flow", space=self.space.pk)
        self.assertTrue(
            Interaction.objects.filter(pk=interaction.pk).exists())

    def test_resembrar_regresa_al_estado_declarado(self):
        frag = Piece.objects.get(
            crate__flow__space=self.space,
            name="a_menor").fragments.get(fragment_type="message")
        frag.body = "texto editado a mano en la BD"
        frag.save(update_fields=["body"])
        call_command("seed_flow", space=self.space.pk)
        frag.refresh_from_db()
        self.assertIn("menores de 18", frag.body)
