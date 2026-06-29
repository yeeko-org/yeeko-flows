"""Siembra una pieza de bienvenida desechable y apunta el behavior global
`start` a ella, para que cualquier mensaje entrante reciba un saludo.

Idempotente (get_or_create). Es el "hola" del demo; se reemplaza cuando entre
el flujo real de CACEH (seed_flow, WP6).

    python manage.py seed_welcome [--space 1]
"""
from django.core.management.base import BaseCommand, CommandError

from infrastructure.assign.models import ApplyBehavior
from infrastructure.box.models import Fragment, Piece
from infrastructure.flow.models import Crate, CrateType, Flow
from infrastructure.place.models import Space

WELCOME_BODY = (
    "¡Hola! 👋 Soy el asistente de CACEH y te ayudaré a hacer tu "
    "*contrato de trabajo del hogar*.\n\n"
    "Esto es un *demo* en construcción 🛠️. Muy pronto armaremos tu "
    "contrato juntos, paso a pasito. 🙂"
)


class Command(BaseCommand):
    help = "Siembra la bienvenida del demo y la enlaza al behavior 'start'."

    def add_arguments(self, parser):
        parser.add_argument("--space", type=int, default=1,
                            help="id del Space (default 1)")

    def handle(self, *args, **opts):
        try:
            space = Space.objects.get(pk=opts["space"])
        except Space.DoesNotExist:
            raise CommandError(f"No existe Space id={opts['space']}")

        crate_type, _ = CrateType.objects.get_or_create(name="demo")
        flow, _ = Flow.objects.get_or_create(
            name="CACEH demo", space=space,
            defaults={"description": "Demo del flujo CACEH"},
        )
        crate, _ = Crate.objects.get_or_create(
            name="bienvenida", crate_type=crate_type,
            defaults={"flow": flow,
                      "description": "Bienvenida desechable del demo"},
        )
        piece, _ = Piece.objects.get_or_create(
            crate=crate, name="welcome",
            defaults={"piece_type": "content",
                      "description": "Saludo inicial del demo"},
        )
        frag, created = Fragment.objects.get_or_create(
            piece=piece, fragment_type="message", order=0,
            defaults={"body": WELCOME_BODY},
        )
        if not created and frag.body != WELCOME_BODY:
            frag.body = WELCOME_BODY
            frag.save(update_fields=["body"])

        start = ApplyBehavior.objects.filter(
            behavior__name="start", space__isnull=True).first()
        if not start:
            raise CommandError(
                "No existe el ApplyBehavior global 'start'.")
        start.main_piece = piece
        start.save(update_fields=["main_piece"])

        self.stdout.write(self.style.SUCCESS(
            f"Bienvenida lista: flow={flow.pk} crate={crate.pk} "
            f"piece={piece.pk} -> start.main_piece={start.main_piece_id}"
        ))
