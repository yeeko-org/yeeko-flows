"""Da de alta (o actualiza) una cuenta de WhatsApp (place.Account).

Idempotente: re-ejecutar con el mismo `pid` solo actualiza token/app_id.
Uso:
    python manage.py setup_wa_account \\
        --pid 103571329211620 --token EAAG... --app-id 2582913978547626
"""
from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from infrastructure.place.models import Account, Space
from infrastructure.service.models import Platform


class Command(BaseCommand):
    help = "Crea o actualiza una cuenta de WhatsApp (Meta Cloud API)."

    def add_arguments(self, parser):
        parser.add_argument("--pid", required=True,
                            help="phone_number_id de Meta (PK)")
        parser.add_argument("--token", default=None,
                            help="access token de Meta; si se omite, se pide "
                                 "de forma oculta (no queda en el historial)")
        parser.add_argument("--app-id", default=None,
                            help="WhatsApp Business / App ID")
        parser.add_argument("--space", type=int, default=1,
                            help="id del Space (default 1)")
        parser.add_argument("--title", default="CACEH demo",
                            help="título legible de la cuenta")

    def handle(self, *args, **opts):
        try:
            space = Space.objects.get(pk=opts["space"])
        except Space.DoesNotExist:
            raise CommandError(f"No existe Space id={opts['space']}")

        platform, _ = Platform.objects.get_or_create(name="whatsapp")

        token = opts["token"] or getpass("Access token de Meta (oculto): ")
        if not token:
            raise CommandError("Token vacío.")

        account, created = Account.objects.update_or_create(
            pid=opts["pid"],
            defaults={
                "token": token,
                "app_id": opts["app_id"],
                "title": opts["title"],
                "space": space,
                "platform": platform,
                "active": True,
                "init_text_response": True,
                "text_response": True,
                "payload_response": True,
            },
        )
        verb = "creada" if created else "actualizada"
        self.stdout.write(self.style.SUCCESS(
            f"Cuenta {verb}: pid={account.pid} space={space} "
            f"app_id={account.app_id}"
        ))
