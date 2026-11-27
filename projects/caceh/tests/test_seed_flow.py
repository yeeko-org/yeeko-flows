"""Arnés del cableado de WP6B: siembra el flujo y confirma que un paso ⚙️
dispara su behavior por el MOTOR REAL (FragmentProcessor -> BehaviorProcessor),
no llamando la clase a mano, y que cada captura de texto libre quedó como
unidad de `open_question` con su esquema por ParamValue de fragmento.

Sin WhatsApp real ni Gemini.

Correr: .venv/bin/python manage.py test projects.caceh
"""

from types import SimpleNamespace

from django.core.management import call_command
from django.test import TestCase

from infrastructure.box.models import Destination, Fragment, Piece, Reply
from infrastructure.member.factories import (
    MemberAccountFactory, MemberFactory)
from infrastructure.place.factories import SpaceFactory
from infrastructure.service.factories import (
    ApiRecordFactory, InteractionTypeFactory)
from infrastructure.talk.models import Interaction
from infrastructure.xtra.models import Extra

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

    def test_capturas_son_unidades_de_open_question(self):
        # Cada captura de texto libre es una pieza de unidad: su behavior
        # con el esquema por ParamValue de su fragmento y sin Written; las
        # piezas de extraer, bifurcar, repreguntar y confirmar ya no existen.
        unidades = {
            "a_nombre_operador": "nombre_operador",
            "a_nombre_contraparte": "nombre_contraparte",
            "b_jornada_abierta": "jornada",
            "b_descanso_abierta": "descanso",
            "c_fecha_inicio": "fecha",
            "c_pago_abierta": "pago",
            "c_lugar_abierta": "domicilio",
        }
        for name, schema in unidades.items():
            with self.subTest(pieza=name):
                piece = Piece.objects.get(
                    crate__flow__space=self.space, name=name)
                self.assertIsNone(piece.written_id)
                frag = self._behavior_fragment(name)
                self.assertEqual(frag.behavior.name, "open_question")
                values = dict(frag.values.values_list(
                    "parameter__name", "value"))
                self.assertEqual(values["schema"], schema)
                question = piece.fragments.get(slot__name="question")
                self.assertEqual(question.order, 0)
        retiradas = Piece.objects.filter(
            crate__flow__space=self.space,
            name__in=("b_ia_jornada", "b_confirma_jornada",
                      "c_valida_fecha", "c_confirma_pago",
                      "c_confirma_lugar", "c_repregunta_lugar",
                      "c_checa_estado", "c_estado"))
        self.assertFalse(retiradas.exists())


class SeedIdempotencyTests(TestCase):
    """El seed es upsert, no rebuild: resembrar conserva los PKs de
    Piece/Fragment/Reply (sobreviven el historial de Interaction, los
    BuiltReply de mensajes ya enviados y las sesiones en curso) y regresa
    la BD al estado declarado."""

    @classmethod
    def setUpTestData(cls):
        cls.space = SpaceFactory()
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
        self.assertIn("menores de edad", frag.body)
