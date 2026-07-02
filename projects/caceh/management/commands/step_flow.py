"""Stepper interactivo del flujo CACEH contra la BD local (WP7).

Avanza el flujo sembrado a mano, turno a turno, imprimiendo lo que el bot
respondería —sin tocar WhatsApp ni subir media (offline)—. Doble uso: probar la
lógica del flujo y servir de demo manual antes de WP8.

    .venv/bin/python manage.py step_flow --phone 5215500000001 --reset
    .venv/bin/python manage.py step_flow --gemini fake   # sin GEMINI_API_KEY

Comandos dentro del stepper: escribe el TÍTULO de un botón para elegirlo (o su
número), texto libre para las capturas, y `/salir` para terminar.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from infrastructure.member.models import Member, MemberAccount
from infrastructure.place.models import Account, Space
from infrastructure.service.models import Platform
from projects.caceh.flow_driver import PID_DEMO, FlowDriver, offline


class Command(BaseCommand):
    help = "Stepper interactivo del flujo CACEH (sin WhatsApp real)."

    def add_arguments(self, parser):
        parser.add_argument("--phone", default="5215500000001",
                            help="wa_id del usuario de prueba")
        parser.add_argument("--space", type=int, default=1)
        parser.add_argument("--reset", action="store_true",
                            help="borra el member de prueba antes de empezar")
        parser.add_argument("--gemini", choices=["real", "fake"],
                            default="real")

    def handle(self, *args, **opts):
        wa_id = opts["phone"]
        if opts["reset"]:
            n = self._reset(wa_id)
            self.stdout.write(self.style.WARNING(
                f"Reset: {n} member(s) borrado(s) para {wa_id}."))

        use_real = opts["gemini"] == "real"
        if use_real and not settings.GEMINI_API_KEY:
            self.stdout.write(self.style.WARNING(
                "Sin GEMINI_API_KEY: uso --gemini fake."))
            use_real = False

        pid = self._ensure_account(opts["space"])
        driver = FlowDriver(wa_id, pid)

        self.stdout.write(self.style.SUCCESS(
            f"Stepper CACEH · phone={wa_id} · gemini="
            f"{'real' if use_real else 'fake'} · /salir para terminar\n"))

        with offline(use_real):
            driver.send("hola")          # arranca el flujo (behavior start)
            self._render(driver)
            while True:
                try:
                    line = input("tú> ").strip()
                except EOFError:
                    break
                if line in ("/salir", "/exit", "/quit"):
                    break
                if not line:
                    continue
                line = self._resolve_button(driver, line)
                driver.send(line)
                self._render(driver)

    # ------------------------------------------------------------ helpers
    def _resolve_button(self, driver, line):
        """Permite elegir un botón por número (1..N) además de por título."""
        if line.isdigit():
            buttons = driver.bot_buttons()
            idx = int(line) - 1
            if 0 <= idx < len(buttons):
                return buttons[idx]
        return line

    def _render(self, driver):
        for body in driver.bot_texts():
            self.stdout.write(self.style.HTTP_INFO("bot> ") + body)
        buttons = driver.bot_buttons()
        for i, title in enumerate(buttons, 1):
            self.stdout.write(f"      [{i}] {title}")
        piece = driver.at_piece()
        if piece:
            self.stdout.write(self.style.MIGRATE_HEADING(f"      ({piece})\n"))

    def _ensure_account(self, space_id):
        """Bootstrap idempotente: el stepper offline necesita un Account con un
        pid en el space (en local no existe; en RDS lo creó WP1). Token dummy:
        no se envía nada a WhatsApp."""
        account = Account.objects.filter(space_id=space_id).first()
        if account:
            return account.pid
        space = Space.objects.get(pk=space_id)
        platform = Platform.objects.get(name="whatsapp")
        Account.objects.create(
            pid=PID_DEMO, space=space, platform=platform,
            title="CACEH demo (stepper)", token="OFFLINE-STEPPER")
        return PID_DEMO

    def _reset(self, wa_id):
        member_ids = list(
            MemberAccount.objects.filter(uid=wa_id)
            .values_list("member_id", flat=True))
        if not member_ids:
            return 0
        deleted, _ = Member.objects.filter(id__in=member_ids).delete()
        return len(member_ids)
