"""Siembra el esqueleto conversacional del slice mínimo planta del flujo CACEH
(§A→§B→§C→§D→§E, camino feliz) en la BD del motor.

Fuente de diseño: `bot_caceh/flows/flujo_simple_v3.md` + `variables_v3.md`.
La data vive en `projects/caceh/seed/` (extras, piezas y cableado por
sección); las primitivas generales en `services.seeder.FlowSeeder`.

Idempotente por upsert: cada corrida actualiza en su lugar (claves
naturales) y poda lo que ya no esté declarado. Los PKs de Piece/Fragment/
Reply se conservan entre corridas, así que resembrar NO borra historial de
interacciones ni rompe sesiones en curso (ver services/seeder/builder.py).

Sin cablear (a propósito): D2 deriva_categoria (solo con tabulador activo);
queda como pass-through.

    python manage.py seed_flow [--space 1]
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from infrastructure.place.models import Space
from projects.caceh.seed import (
    EXTRAS, PIECES, SECTIONS, section_a, section_b, section_c, section_de)
from services.seeder import FlowSeeder, connectivity


class Command(BaseCommand):
    help = "Siembra el esqueleto del slice mínimo planta del flujo CACEH."

    def add_arguments(self, parser):
        parser.add_argument("--space", type=int, default=1,
                            help="id del Space (default 1)")

    @transaction.atomic
    def handle(self, *args, **opts):
        try:
            space = Space.objects.get(pk=opts["space"])
        except Space.DoesNotExist:
            raise CommandError(f"No existe Space id={opts['space']}")

        sdr = FlowSeeder(space, "CACEH demo", SECTIONS,
                         flow_description="Flujo del demo CACEH")
        sdr.ensure_collection("caceh", "projects.caceh", "CACEH")
        sdr.declare_extras(
            EXTRAS, "caceh", "CACEH",
            "Variables del flujo de contratos CACEH")

        for section, name, desc, piece_type in PIECES:
            sdr.piece(section, name, desc, piece_type)

        p = sdr.pieces
        for module in (section_a, section_b, section_c, section_de):
            module.wire(sdr, p)
        sdr.wire_global_start(p["a_saludo"])

        stats = sdr.finalize()
        self._report(sdr, stats)

    def _report(self, sdr: FlowSeeder, stats: dict):
        unreached, dangling = connectivity(sdr.pieces, "a_saludo")
        self.stdout.write(self.style.SUCCESS(
            f"Sembrado: flow={sdr.flow.pk} crates={len(sdr.crates)} "
            f"piezas={len(sdr.pieces)} extras={len(sdr.extras)} | "
            f"creados={stats['created']} actualizados={stats['updated']} "
            f"podados={stats['pruned']}"))
        if dangling:
            self.stdout.write(self.style.WARNING(
                f"Destinos colgados (sin piece_dest): {dangling}"))
        if unreached:
            self.stdout.write(self.style.WARNING(
                "Piezas no alcanzables desde a_saludo: "
                + ", ".join(sorted(unreached))))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Conectividad OK: todas las piezas alcanzables desde "
                "a_saludo."))
