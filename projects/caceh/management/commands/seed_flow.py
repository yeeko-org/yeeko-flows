"""Siembra el esqueleto conversacional del slice mínimo planta del flujo CACEH
(§A→§B→§C→§D→§E, camino feliz) en la BD del motor.

Fuente de diseño: `bot_caceh/flows/flujo_simple_v3.md` + `variables_v3.md`.

Alcance: la estructura conversacional (piezas, fragmentos, botones, capturas,
destinos, bifurcaciones, extras y asignaciones de botón) MÁS el cableado de los
behaviors de WP4/WP5 (WP6B). Cada paso ⚙️ del slice es una pieza `content` con un
`Fragment(behavior)` (order 0) y un `Fragment(embedded)` (order 1) que auto-avanza
al siguiente paso —una pieza `destinations` se saltaría los fragments, por eso no
se usa para los behaviors—. ia_extrae (genérico) recibe `esquema`/`entrada` por
`ParamValue` de fragmento; los 5 de proyecto se resuelven por `app_label`.

Sin cablear (a propósito): D1 MultipleSelectFlow (sesión paralela) y D2
deriva_categoria (solo con tabulador activo); quedan como pass-through.

Idempotente por reconstrucción: en cada corrida borra las piezas de los crates que
administra y las vuelve a crear desde cero, dentro de una transacción. Los nodos
persistentes (Flow, Crate, Collection, Extra) se resuelven con get_or_create.

    python manage.py seed_flow [--space 1]
"""
from collections import deque

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from infrastructure.assign.models import (
    ApplyBehavior, Assign, ConditionRule, ParamValue)
from infrastructure.box.models import (
    Destination, Fragment, Piece, Reply, Written)
from infrastructure.flow.models import Crate, CrateType, Flow
from infrastructure.place.models import Space
from infrastructure.tool.models import Behavior, Collection, Parameter
from infrastructure.xtra.models import ClassifyExtra, Extra, Format

# Crates del slice (un agrupador por sección + uno para los límites).
SECTIONS = {
    "a": "§A · Entrada: partes y modalidad",
    "b": "§B · Jornada y descanso",
    "c": "§C · Antigüedad, pago y lugar",
    "d": "§D · Actividades y tabulador",
    "e": "§E · Cierre v1: PDF y registro",
    "stub": "Límites del slice (fuera de alcance)",
}

# Extras que declara WP6: enrutamiento + captura conversacional. Los extras que
# son salida de behaviors (trab_nombre_completo, salario_diario, registro_id…)
# los declara WP6B, no esta corrida.
EXTRAS = [
    ("operador", None),
    ("operador_nombre", None),
    ("contraparte_nombre", None),
    ("etiqueta_contraparte", None),
    ("pregunta_mayor_edad", None),
    ("mayor_edad", None),
    ("tipo_contrato", None),
    ("respuesta_jornada", None),
    ("ia_completed", None),
    ("ia_pregunta", None),
    ("es_retroactivo", None),
    ("respuesta_pago", None),
    ("modo_pago", None),
    ("respuesta_lugar", None),
    ("actividades", "json"),
    ("tabulador_activo", None),
    # --- WP6B: salidas de los behavios de WP5 + campos de los esquemas de IA
    # que ia_extrae escribe (nombre de campo Pydantic = clave del extra).
    # Format: listas y los historiales transitorios = json; monto_pago = int;
    # el resto str (default). salario_diario queda str a propósito: el behavior
    # escribe round(diario, 2) (float) y get_value haría int("350.0") -> 0.
    ("trab_nombre_completo", None),   # asigna_partes (A5)
    ("empl_nombre_completo", None),   # asigna_partes (A5)
    ("telefono_operador", None),      # asigna_partes (A5)
    ("hora_entrada", None),           # ia_extrae jornada (B2)
    ("hora_salida", None),            # ia_extrae jornada (B2)
    ("dias_laborables", "json"),      # ia_extrae jornada (B2)
    ("_hist_jornada", "json"),        # historial transitorio de B2
    ("monto_pago", "int"),            # ia_extrae pago (C5)
    ("pago_periodicidad", None),      # ia_extrae pago (C5)
    ("_hist_pago", "json"),           # historial transitorio de C5
    ("lt_calle", None),               # ia_extrae domicilio (C10)
    ("lt_ext", None),
    ("lt_int", None),
    ("lt_colonia", None),
    ("lt_cp", None),
    ("lt_municipio", None),
    ("lt_estado", None),
    ("ciudad_firma", None),           # derivado en la misma llamada de C10
    ("_hist_domicilio", "json"),      # historial transitorio de C10
    ("salario_diario", None),         # calcula_salario_diario (C8)
    ("pdf_contrato", None),           # genera_pdf (E5) -> pk del Media
    ("registro_id", None),            # registra_contrato (E6) -> folio
    ("flujo_completado", None),       # registra_contrato (E6) -> "completo"
]


class Command(BaseCommand):
    help = "Siembra el esqueleto del slice mínimo planta del flujo CACEH."

    def add_arguments(self, parser):
        parser.add_argument("--space", type=int, default=1,
                            help="id del Space (default 1)")

    @transaction.atomic
    def handle(self, *args, **opts):
        try:
            self.space = Space.objects.get(pk=opts["space"])
        except Space.DoesNotExist:
            raise CommandError(f"No existe Space id={opts['space']}")

        self.p: dict[str, Piece] = {}
        self.x: dict[str, Extra] = {}

        self._setup_catalog()
        self._setup_flow()
        self._teardown()
        self._declare_extras()
        self._create_pieces()

        self._wire_section_a()
        self._wire_section_b()
        self._wire_section_c()
        self._wire_section_d_e()

        self._report()

    # ------------------------------------------------------------------ setup
    def _setup_catalog(self):
        # Clasificación propia para los extras del flujo; los Format ('json',
        # 'int') ya existen en la BD, el resto queda en null (str por defecto).
        self.classify, _ = ClassifyExtra.objects.get_or_create(
            name="caceh",
            defaults={"public_name": "CACEH", "description":
                      "Variables del flujo de contratos CACEH"})
        self.formats = {f.name: f for f in Format.objects.all()}

        # La crea WP6; los Behavior de proyecto se resuelven por app_label.
        collection, _ = Collection.objects.get_or_create(
            name="caceh",
            defaults={"public_name": "CACEH", "is_custom": True,
                      "app_label": "projects.caceh"})
        collection.spaces.add(self.space)
        self.collection = collection

    def _setup_flow(self):
        crate_type, _ = CrateType.objects.get_or_create(name="flujo")
        self.flow, _ = Flow.objects.get_or_create(
            name="CACEH demo", space=self.space,
            defaults={"description": "Flujo del demo CACEH"})
        self.crates = {}
        for key, name in SECTIONS.items():
            crate, _ = Crate.objects.get_or_create(
                name=name, crate_type=crate_type,
                defaults={"flow": self.flow, "description": name})
            self.crates[key] = crate

    def _teardown(self):
        # Reconstrucción idempotente: borra todo lo que cuelga de mis crates.
        # Las Written se desreferencian aparte porque Piece.written es CASCADE
        # (borrar la Written borraría la Piece).
        pieces = Piece.objects.filter(crate__in=self.crates.values())
        written_ids = list(
            pieces.exclude(written__isnull=True)
            .values_list("written_id", flat=True))
        pieces.delete()
        Written.objects.filter(id__in=written_ids).delete()

    def _declare_extras(self):
        for name, fmt in EXTRAS:
            extra, _ = Extra.objects.get_or_create(
                space=self.space, name=name,
                defaults={"classify": self.classify,
                          "format": self.formats.get(fmt) if fmt else None})
            self.x[name] = extra

    # --------------------------------------------------------------- helpers
    def _piece(self, section, name, desc, piece_type="content", config=None):
        piece = Piece.objects.create(
            crate=self.crates[section], name=name, description=desc,
            piece_type=piece_type, config=config or {})
        self.p[name] = piece
        return piece

    def _msg(self, piece, body, header=None, footer=None, order=0):
        return Fragment.objects.create(
            piece=piece, fragment_type="message", order=order,
            body=body, header=header, footer=footer)

    def _embedded(self, piece, dest, order=1):
        # Auto-avance entre mensajes del bot: renderiza `dest` en línea.
        return Fragment.objects.create(
            piece=piece, fragment_type="embedded", order=order,
            embedded_piece=dest)

    def _dest(self, dest, *, reply=None, written=None, piece=None,
              is_default=True, order=0):
        return Destination.objects.create(
            reply=reply, written=written, piece=piece,
            destination_type="piece", piece_dest=dest,
            is_default=is_default, order=order)

    def _buttons(self, piece, question, options, footer=None):
        # options: [(title, dest_piece, {extra_name: value})]. ≤3 → botones;
        # el motor pasa a lista solo con >3 o secciones.
        frag = self._msg(piece, question, footer=footer)
        for order, (title, dest, assigns) in enumerate(options):
            reply = Reply.objects.create(
                fragment=frag, reply_type="quick_reply",
                title=title, order=order)
            self._dest(dest, reply=reply)
            for ex_name, value in (assigns or {}).items():
                Assign.objects.create(
                    reply=reply, extra=self.x[ex_name], extra_value=value)
        return frag

    def _capture(self, piece, prompt, extra_name, dest):
        self._msg(piece, prompt)
        written = Written.objects.create(
            extra=self.x[extra_name], available=True)
        piece.written = written
        piece.save(update_fields=["written"])
        self._dest(dest, written=written)
        return written

    def _bifurcation(self, piece, extra_name, branches, default_dest):
        # piece es de tipo 'destinations'. Cada rama lleva su ConditionRule;
        # el default (is_default=True) nunca se evalúa, es el fallback.
        extra = self.x[extra_name]
        for order, (value, dest) in enumerate(branches):
            d = self._dest(dest, piece=piece, is_default=False, order=order)
            ConditionRule.objects.create(
                destination=d, extra=extra, extra_values=[value])
        self._dest(default_dest, piece=piece, is_default=True,
                   order=len(branches))

    def _link(self, origin, dest):
        # Paso de largo de una pieza 'destinations' (placeholder ⚙️) al
        # siguiente. Lo usan los pasos aún no cableados (D1 MultipleSelectFlow,
        # D2 deriva_categoria): pasan de largo sin correr behavior.
        return self._dest(dest, piece=origin)

    # ----------------------------------------------------- behaviors (WP6B)
    def _ensure_behavior(self, name, *, generic):
        # Behavior + ApplyBehavior idempotentes. generic=True -> sin Collection:
        # el motor lo resuelve en services.behavior (p. ej. ia_extrae).
        # generic=False -> Collection caceh: lo resuelve por app_label
        # (projects.caceh.behaviors) buscando el alias snake_case.
        behavior, _ = Behavior.objects.get_or_create(
            name=name,
            defaults={"in_code": True,
                      "collection": None if generic else self.collection})
        ApplyBehavior.objects.get_or_create(
            behavior=behavior, space=self.space,
            defaults={"main_piece": None})
        return behavior

    def _ensure_param(self, behavior, name):
        param, _ = Parameter.objects.get_or_create(
            behavior=behavior, name=name,
            defaults={"data_type": "string"})
        return param

    def _behavior_step(self, piece_name, behavior_name, dest, *,
                       generic=False, params=None):
        """Convierte la pieza placeholder ⚙️ en un paso real que corre
        `behavior_name` y auto-avanza a `dest`.

        Una pieza 'destinations' se salta sus fragments (piece.py); por eso el
        paso es una pieza 'content' con dos fragments: el behavior (order 0) y
        un embedded (order 1) que renderiza `dest` en línea —el mismo patrón de
        auto-avance que usa a_acerca—. Así corre el behavior y luego sigue a la
        bifurcación que lee ia_completed o al siguiente paso.

        `params` ({nombre: valor}) crea un ParamValue POR FRAGMENTO (no en el
        ApplyBehavior): ia_extrae se reusa en B2/C5/C10 con distinto esquema, y
        FragmentProcessor inyecta fragment.values en los parámetros. El valor
        '{{respuesta_*}}' lo resuelve IaExtraeBehavior (replace_parameter)."""
        piece = self.p[piece_name]
        piece.piece_type = "content"
        piece.config = {}
        piece.save(update_fields=["piece_type", "config"])

        behavior = self._ensure_behavior(behavior_name, generic=generic)
        frag = Fragment.objects.create(
            piece=piece, fragment_type="behavior", behavior=behavior, order=0)
        for pname, pvalue in (params or {}).items():
            ParamValue.objects.create(
                parameter=self._ensure_param(behavior, pname),
                fragment=frag, value=pvalue)
        self._embedded(piece, dest, order=1)

    # -------------------------------------------------------------- piezas
    def _create_pieces(self):
        # Se crean todas primero para poder cablear destinos hacia adelante.
        d = "destinations"
        defs = [
            # §A
            ("a", "a_saludo", "A1 saludo y encuadre", "content"),
            ("a", "a_acerca", "A1b qué es CACEH", "content"),
            ("a", "a_quien_eres", "A2 trabajadora o empleadora", "content"),
            ("a", "a_nombre_operador", "A3 nombre de quien opera", "content"),
            ("a", "a_nombre_contraparte", "A4 nombre de la contraparte",
             "content"),
            ("a", "a_asigna_partes", "A5 asigna_partes (placeholder)", d),
            ("a", "a_bifurca_operador", "A6 bifurca por operador", d),
            ("a", "a_mayor_edad", "A7 mayoría de edad", "content"),
            ("a", "a_menor", "A·menor canaliza y termina", "content"),
            ("a", "a_num_empleadoras", "A8 cuántas empleadoras", "content"),
            ("a", "a_duerme", "A9 duerme en la casa", "content"),
            ("a", "a_tipo_empleadora", "A11 tipo de contrato (empleadora)",
             "content"),
            # §B
            ("b", "b_jornada_abierta", "B1 jornada (captura)", "content"),
            ("b", "b_ia_jornada", "B2 ia_extrae jornada (placeholder)", d),
            ("b", "b_checa_jornada", "B3 bifurca ia_completed", d),
            ("b", "b_repregunta_jornada", "B4 repregunta jornada", "content"),
            ("b", "b_bifurca_descanso", "B5 bifurca tipo_contrato", d),
            ("b", "b_confirma_jornada", "B8 confirma jornada", "content"),
            # §C
            ("c", "c_relacion_previa", "C1 relación previa", "content"),
            ("c", "c_pago_abierta", "C4 pago (captura)", "content"),
            ("c", "c_ia_pago", "C5 ia_extrae pago (placeholder)", d),
            ("c", "c_confirma_pago", "C6 confirma pago", "content"),
            ("c", "c_modo_pago", "C7 modo de pago", "content"),
            ("c", "c_salario_diario",
             "C8 calcula_salario_diario (placeholder)", d),
            ("c", "c_lugar_abierta", "C9 lugar de trabajo (captura)",
             "content"),
            ("c", "c_ia_lugar", "C10 ia_extrae domicilio (placeholder)", d),
            ("c", "c_checa_lugar", "C11 bifurca ia_completed", d),
            ("c", "c_repregunta_lugar", "C12 repregunta lugar", "content"),
            ("c", "c_confirma_lugar", "C13 confirma lugar", "content"),
            # §D
            ("d", "d_actividades", "D1 MultipleSelectFlow (placeholder)", d),
            ("d", "d_deriva_categoria", "D2 deriva_categoria (placeholder)",
             d),
            ("d", "d_check_tabulador", "D4 bifurca tabulador_activo", d),
            # §E
            ("e", "e_resumen", "E3 resumen final", "content"),
            ("e", "e_corrige", "E4 corrige campo (stub)", "content"),
            ("e", "e_genera_pdf", "E5 genera_pdf (placeholder)", d),
            ("e", "e_registra", "E6 registra_contrato (placeholder)", d),
            ("e", "e_entrega_pdf", "E7 entrega_pdf (placeholder)", d),
            ("e", "e_oferta_mejora", "E8 oferta de mejora", "content"),
            ("e", "e_despedida", "E9 despedida y FIN", "content"),
            # Límites
            ("stub", "fuera_alcance", "Rama fuera del slice del demo",
             "content"),
        ]
        for section, name, desc, ptype in defs:
            config = ({"wp6b_behavior": name.split("_", 1)[1]}
                      if ptype == "destinations" and name not in (
                          "a_bifurca_operador", "b_checa_jornada",
                          "b_bifurca_descanso", "c_checa_lugar",
                          "d_check_tabulador") else None)
            self._piece(section, name, desc, ptype, config)

    # --------------------------------------------------------------- wiring
    def _wire_section_a(self):
        p = self.p
        # A5 ⚙️ asigna_partes (proyecto): reparte nombres por rol + teléfono.
        self._behavior_step(
            "a_asigna_partes", "asigna_partes", p["a_bifurca_operador"])
        self._buttons(p["a_saludo"], (
            "¡Hola! 👋 Soy Dignas firma, la asistente de CACEH para ayudarte "
            "a hacer tu contrato de trabajo del hogar.\n\nLo armamos juntos, "
            "paso a pasito; al final te entrego tu PDF listo para firmar."), [
            ("¿Qué es CACEH?", p["a_acerca"], None),
            ("¡Empecemos!", p["a_quien_eres"], None),
        ])

        self._msg(p["a_acerca"], (
            "CACEH es una organización de la sociedad civil que busca mejorar "
            "las condiciones laborales de las personas trabajadoras del hogar. "
            "Dignas firma te ayuda a crear un contrato con validez legal solo "
            "contestando unas preguntas."))
        self._embedded(p["a_acerca"], p["a_quien_eres"])

        self._buttons(p["a_quien_eres"],
                      "¿Eres persona trabajadora o persona empleadora?", [
            ("Trabajadora", p["a_nombre_operador"], {
                "operador": "trabajadora",
                "etiqueta_contraparte": "empleadora",
                "pregunta_mayor_edad": "tienes 18 años o más"}),
            ("Empleadora", p["a_nombre_operador"], {
                "operador": "empleadora",
                "etiqueta_contraparte": "trabajadora",
                "pregunta_mayor_edad":
                    "la persona trabajadora tiene 18 años o más"}),
        ])

        self._capture(
            p["a_nombre_operador"],
            "¿Cuál es tu nombre completo?, tal como quieres que aparezca en "
            "el contrato. ✍️",
            "operador_nombre", p["a_nombre_contraparte"])

        self._capture(
            p["a_nombre_contraparte"],
            "¿Y el nombre completo de la persona {{etiqueta_contraparte}}?",
            "contraparte_nombre", p["a_asigna_partes"])

        self._bifurcation(
            p["a_bifurca_operador"], "operador",
            [("empleadora", p["a_tipo_empleadora"])],
            default_dest=p["a_mayor_edad"])

        self._buttons(p["a_mayor_edad"],
                      "Una pregunta importante: ¿{{pregunta_mayor_edad}}?", [
            ("Sí", p["a_num_empleadoras"], {"mayor_edad": "si"}),
            ("No", p["a_menor"], {"mayor_edad": "no"}),
        ])

        self._msg(p["a_menor"], (
            "Para personas menores de 18 años la ley pide cuidados especiales "
            "y este asistente todavía no puede hacer ese contrato. Acércate a "
            "CACEH para que te acompañen. 💚"))

        self._buttons(p["a_num_empleadoras"],
                      "¿Cuántas personas empleadoras tienes?", [
            ("Una persona", p["a_duerme"], None),
            ("Varias", p["fuera_alcance"],
             {"tipo_contrato": "entrada_salida"}),
        ])

        self._buttons(p["a_duerme"],
                      "¿Duermes en la casa donde trabajas?", [
            ("Sí, duermo ahí", p["b_jornada_abierta"],
             {"tipo_contrato": "planta"}),
            ("No duermo ahí", p["fuera_alcance"],
             {"tipo_contrato": "entrada_salida"}),
        ])

        self._buttons(p["a_tipo_empleadora"], (
            "¿Qué tipo de contrato necesitan?\n🏠 De planta: la persona vive "
            "en la casa.\n🚪 Entrada por salida: llega y se va el mismo día."),
            [
            ("De planta", p["b_jornada_abierta"],
             {"tipo_contrato": "planta"}),
            ("Entrada por salida", p["fuera_alcance"],
             {"tipo_contrato": "entrada_salida"}),
        ])

    def _wire_section_b(self):
        p = self.p
        # B2 ⚙️ ia_extrae (genérico) esquema jornada -> bifurcación ia_completed.
        self._behavior_step(
            "b_ia_jornada", "ia_extrae", p["b_checa_jornada"], generic=True,
            params={"esquema": "jornada",
                    "entrada": "{{respuesta_jornada}}"})
        self._capture(
            p["b_jornada_abierta"],
            "Hablemos de los días y horarios. ¿Qué días trabajas y en qué "
            "horario? Escríbelo con tus palabras. 😉 Ej.: \"de lunes a "
            "viernes, de 8 a 4\".",
            "respuesta_jornada", p["b_ia_jornada"])

        self._bifurcation(
            p["b_checa_jornada"], "ia_completed",
            [("no", p["b_repregunta_jornada"])],
            default_dest=p["b_bifurca_descanso"])

        self._capture(
            p["b_repregunta_jornada"], "{{ia_pregunta}}",
            "respuesta_jornada", p["b_ia_jornada"])

        # Solo el camino planta está en el slice; entrada por salida queda fuera.
        self._bifurcation(
            p["b_bifurca_descanso"], "tipo_contrato",
            [("entrada_salida", p["fuera_alcance"])],
            default_dest=p["b_confirma_jornada"])

        self._buttons(p["b_confirma_jornada"], (
            "Quedó así, échale un ojo 👀\n🗓️ Días: {{dias_laborables}}\n"
            "🕗 Horario: de {{hora_entrada}} a {{hora_salida}}"), [
            ("Sí, así es", p["c_relacion_previa"], None),
            ("Corregir", p["b_jornada_abierta"], None),
        ])

    def _wire_section_c(self):
        p = self.p
        # C5 ⚙️ ia_extrae pago (sin loop de repregunta en el slice: -> confirma).
        self._behavior_step(
            "c_ia_pago", "ia_extrae", p["c_confirma_pago"], generic=True,
            params={"esquema": "pago", "entrada": "{{respuesta_pago}}"})
        # C8 ⚙️ calcula_salario_diario (proyecto): monto+periodicidad+días.
        self._behavior_step(
            "c_salario_diario", "calcula_salario_diario", p["c_lugar_abierta"])
        # C10 ⚙️ ia_extrae domicilio -> bifurcación ia_completed.
        self._behavior_step(
            "c_ia_lugar", "ia_extrae", p["c_checa_lugar"], generic=True,
            params={"esquema": "domicilio", "entrada": "{{respuesta_lugar}}"})
        # "Ya trabajábamos" (retroactivo) queda fuera del slice (sin antigüedad).
        self._buttons(p["c_relacion_previa"], (
            "¿El trabajo empieza ahora, o quieren poner por escrito una "
            "relación que ya existía antes?"), [
            ("Empieza ahora", p["c_pago_abierta"], {"es_retroactivo": "no"}),
            ("Ya trabajábamos", p["fuera_alcance"], {"es_retroactivo": "si"}),
        ])

        self._capture(
            p["c_pago_abierta"],
            "Hablemos del sueldo 💵 ¿Cuánto es el pago y cada cuándo se da? "
            "Ej.: \"350 al día\", \"2,500 a la semana\".",
            "respuesta_pago", p["c_ia_pago"])

        self._buttons(p["c_confirma_pago"],
                      "Entonces el pago es de ${{monto_pago}} "
                      "{{frase_periodicidad}}. ¿Así es?", [
            ("Sí, así es", p["c_modo_pago"], None),
            ("Corregir", p["c_pago_abierta"], None),
        ])

        self._buttons(p["c_modo_pago"], "¿Y cómo se le paga?", [
            ("En efectivo", p["c_salario_diario"], {"modo_pago": "efectivo"}),
            ("Transferencia o depósito", p["c_salario_diario"],
             {"modo_pago": "transferencia"}),
        ])

        self._capture(
            p["c_lugar_abierta"],
            "¿Cuál es la dirección del lugar de trabajo? Escríbela completa: "
            "calle, número, colonia, C.P., alcaldía o municipio y estado. 🏠",
            "respuesta_lugar", p["c_ia_lugar"])

        self._bifurcation(
            p["c_checa_lugar"], "ia_completed",
            [("no", p["c_repregunta_lugar"])],
            default_dest=p["c_confirma_lugar"])

        self._capture(
            p["c_repregunta_lugar"], "{{ia_pregunta}}",
            "respuesta_lugar", p["c_ia_lugar"])

        self._buttons(p["c_confirma_lugar"], (
            "La dirección quedó así 👀\n🏠 {{lt_calle}} {{lt_ext}}, col. "
            "{{lt_colonia}}, C.P. {{lt_cp}}, {{lt_municipio}}, "
            "{{lt_estado}}"), [
            ("Sí, es correcta", p["d_actividades"], None),
            ("Corregir", p["c_lugar_abierta"], None),
        ])

    def _wire_section_d_e(self):
        p = self.p
        # D1 (MultipleSelectFlow) y D2 (deriva_categoria) NO se cablean en
        # WP6B: el primero es sesión paralela, el segundo solo aplica con
        # tabulador activo (fuera del slice). Pasan de largo.
        self._link(p["d_actividades"], p["d_deriva_categoria"])
        self._link(p["d_deriva_categoria"], p["d_check_tabulador"])
        # §E en orden: E5 arma el PDF y deja {{pdf_contrato}}; E6 lo lee para
        # ligar el Media a la constancia y fija flujo_completado; E7 lo envía.
        self._behavior_step(
            "e_genera_pdf", "genera_pdf", p["e_registra"])
        self._behavior_step(
            "e_registra", "registra_contrato", p["e_entrega_pdf"])
        self._behavior_step(
            "e_entrega_pdf", "entrega_pdf", p["e_oferta_mejora"])
        # Tabulador apagado en el slice: el default salta a §E; la rama 'activo'
        # (D5–D8) queda fuera de alcance.
        self._bifurcation(
            p["d_check_tabulador"], "tabulador_activo",
            [("activo", p["fuera_alcance"])],
            default_dest=p["e_resumen"])

        self._buttons(p["e_resumen"], (
            "Esto es lo que tengo. Échale un último ojo 👀\n"
            "👥 {{trab_nombre_completo}} y {{empl_nombre_completo}}\n"
            "📄 Contrato {{tipo_contrato}}\n"
            "💵 ${{salario_diario}} al día, pago en {{modo_pago}}\n"
            "🖊️ Se firma en {{ciudad_firma}}, con fecha de hoy"), [
            ("Todo correcto", p["e_genera_pdf"], None),
            ("Corregir algo", p["e_corrige"], None),
        ])

        # E4 corrección: stub mínimo que vuelve al resumen (la lista completa de
        # campos editables se afina luego).
        self._buttons(p["e_corrige"],
                      "¿Qué quieres corregir? (por ahora volvemos al resumen)",
                      [("Volver al resumen", p["e_resumen"], None)])

        self._buttons(p["e_oferta_mejora"], (
            "Con esto ya tienen un contrato que vale. 💪 Se puede hacer más "
            "riguroso agregando datos como la CURP o el domicilio. ¿Quieres "
            "mejorarlo ahora?"), [
            ("Sí, vamos", p["fuera_alcance"], None),
            ("Así está bien", p["e_despedida"], None),
        ])

        self._msg(p["e_despedida"], (
            "Imprímanlo dos veces y fírmenlo: quien emplea, la persona "
            "trabajadora y un testigo. Guarda bien tu copia: es tu "
            "comprobante. 💚"))

        self._msg(p["fuera_alcance"], (
            "Esta parte del flujo todavía no está en el demo. 🛠️ Gracias por "
            "tu paciencia; pronto la tendremos lista."))

    # --------------------------------------------------------------- report
    def _report(self):
        ids = {pc.id: name for name, pc in self.p.items()}
        unreached, dangling = self._connectivity(ids)
        n_dest = Destination.objects.filter(
            piece_dest__in=self.p.values()).count()
        self.stdout.write(self.style.SUCCESS(
            f"Sembrado: flow={self.flow.pk} crates={len(self.crates)} "
            f"piezas={len(self.p)} extras={len(self.x)} destinos={n_dest}"))
        if dangling:
            self.stdout.write(self.style.WARNING(
                f"Destinos colgados (sin piece_dest): {dangling}"))
        if unreached:
            self.stdout.write(self.style.WARNING(
                "Piezas no alcanzables desde a_saludo: "
                + ", ".join(sorted(unreached))))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Conectividad OK: todas las piezas alcanzables; "
                "e_despedida llega desde a_saludo."))

    def _connectivity(self, ids):
        # BFS desde a_saludo siguiendo destinos (de pieza, reply y written) y
        # fragmentos embedded. Reporta piezas huérfanas y destinos sin destino.
        dangling = 0
        adj: dict[int, set] = {pid: set() for pid in ids}
        for pid in ids:
            piece = self.p_by_id(pid)
            qs = list(piece.destinations.all())
            for reply in Reply.objects.filter(fragment__piece=piece):
                qs += list(reply.destinations.all())
            if piece.written_id:
                qs += list(Destination.objects.filter(
                    written_id=piece.written_id))
            for dest in qs:
                if dest.destination_type == "piece":
                    if dest.piece_dest_id:
                        adj[pid].add(dest.piece_dest_id)
                    else:
                        dangling += 1
            for frag in Fragment.objects.filter(
                    piece=piece, fragment_type="embedded"):
                if frag.embedded_piece_id:
                    adj[pid].add(frag.embedded_piece_id)

        start = self.p["a_saludo"].id
        seen = {start}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            for nxt in adj.get(cur, ()):
                if nxt in ids and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        unreached = {ids[pid] for pid in ids if pid not in seen}
        return unreached, dangling

    def p_by_id(self, pid):
        return next(pc for pc in self.p.values() if pc.id == pid)
