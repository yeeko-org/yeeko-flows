"""Constructor idempotente de flujos conversacionales (siembra en BD).

Traduce un flujo diseñado en .md (notación del skill flow-builder) a las
primitivas del motor. Cada método hace upsert por clave natural y registra lo
declarado; `finalize()` poda lo que quedó fuera de la declaración dentro de
los crates administrados ("declara todo, poda el resto").

Por qué upsert y no rebuild: borrar piezas cascadea a `Interaction.fragment`
(historial de conversación) y a `BuiltReply.reply` (botones ya enviados), y
el motor ubica al usuario por su última interacción — un rebuild rompe
sesiones en curso y borra evidencia. El upsert conserva los PKs de Piece,
Fragment y Reply entre corridas.

Claves naturales: Piece (crate, name), Fragment (piece, order),
Reply (fragment, order), Destination (reply | written | piece+order).
Assign, ConditionRule y ParamValue se recrean por dueño: nada de runtime los
referencia y no tienen clave natural clara.
"""
from typing import Callable, Optional

from django.db.models import Model, Q

from infrastructure.assign.models import (
    ApplyBehavior, Assign, ConditionRule, ParamValue)
from infrastructure.box.models import (
    Destination, Fragment, Piece, Reply, Written)
from infrastructure.flow.models import Crate, CrateType, Flow
from infrastructure.place.models import Space
from infrastructure.tool.models import Behavior, Collection, Parameter
from infrastructure.xtra.models import ClassifyExtra, Extra, Format

# WhatsApp corta el título: 20 en botón, 24 en fila de lista. Pasarse hace
# que Meta rechace TODO el mensaje (400 131009) y el bot enmudezca, así que
# se caza al sembrar en vez de en runtime.
BUTTON_TITLE_LIMIT = 20
ROW_TITLE_LIMIT = 24


class FlowSeeder:
    """Siembra y actualiza un flujo completo dentro de sus propios crates.

    Uso: instanciar, declarar extras/colección, crear piezas, cablear con
    los métodos de contenido y cerrar SIEMPRE con `finalize()` (ahí ocurre
    la poda de lo no declarado y se arma el reporte).
    """

    def __init__(self, space: Space, flow_name: str,
                 sections: dict[str, str], crate_type_name: str = "flujo",
                 flow_description: str = ""):
        self.space = space
        crate_type, _ = CrateType.objects.get_or_create(name=crate_type_name)
        self.flow, _ = Flow.objects.get_or_create(
            name=flow_name, space=space,
            defaults={"description": flow_description or flow_name})
        self.crates: dict[str, Crate] = {}
        for key, name in sections.items():
            crate, _ = Crate.objects.get_or_create(
                name=name, crate_type=crate_type,
                defaults={"flow": self.flow, "description": name})
            self.crates[key] = crate

        self.pieces: dict[str, Piece] = {}
        self.extras: dict[str, Extra] = {}
        self.collection: Optional[Collection] = None
        # PKs declarados en esta corrida, por modelo; finalize() poda el resto.
        self._keep: dict[type[Model], set] = {
            Piece: set(), Fragment: set(), Reply: set(),
            Destination: set(), Written: set()}
        self.stats = {"created": 0, "updated": 0, "pruned": 0}

    # ------------------------------------------------------------- tracking
    def _track(self, obj: Model, created: bool) -> Model:
        keep = self._keep.get(type(obj))
        if keep is not None:
            keep.add(obj.pk)
        self.stats["created" if created else "updated"] += 1
        return obj

    # -------------------------------------------------------------- catálogo
    def ensure_collection(self, name: str, app_label: str,
                          public_name: str = "") -> Collection:
        # Los Behavior de proyecto se resuelven por app_label (alias
        # snake_case dentro de <app_label>.behaviors).
        collection, _ = Collection.objects.get_or_create(
            name=name,
            defaults={"public_name": public_name or name, "is_custom": True,
                      "app_label": app_label})
        collection.spaces.add(self.space)
        self.collection = collection
        return collection

    def declare_extras(self, pairs: list[tuple[str, Optional[str]]],
                       classify_name: str, classify_public: str = "",
                       classify_description: str = "") -> dict[str, Extra]:
        """Declara las variables del flujo. `pairs`: [(nombre, formato|None)].

        update_or_create: un cambio de format o classify en la declaración
        SÍ se aplica a extras ya existentes (get_or_create lo ignoraría).
        """
        classify, _ = ClassifyExtra.objects.get_or_create(
            name=classify_name,
            defaults={"public_name": classify_public or classify_name,
                      "description": classify_description})
        # The Format catalogue does not travel in fixtures: a missing row used
        # to seed the extra with format=None silently, breaking the flow later,
        # when the value was read.
        for fmt_name in {fmt for _, fmt in pairs if fmt}:
            Format.objects.get_or_create(name=fmt_name)
        formats = {f.name: f for f in Format.objects.all()}
        for name, fmt in pairs:
            if fmt and fmt not in formats:
                raise ValueError(f"Format '{fmt}' no existe ni pudo crearse")
            extra, _ = Extra.objects.update_or_create(
                space=self.space, name=name,
                defaults={"classify": classify,
                          "format": formats.get(fmt) if fmt else None})
            self.extras[name] = extra
        return self.extras

    def ensure_behavior(self, name: str, *, generic: bool) -> Behavior:
        # generic=True -> sin Collection: el motor lo resuelve en
        # services.behavior (p. ej. ia_extrae). generic=False -> con la
        # Collection del proyecto (requiere ensure_collection previo).
        if not generic and self.collection is None:
            raise ValueError(
                "Behavior de proyecto sin Collection: llama "
                "ensure_collection() antes")
        behavior, _ = Behavior.objects.get_or_create(
            name=name,
            defaults={"in_code": True,
                      "collection": None if generic else self.collection})
        ApplyBehavior.objects.get_or_create(
            behavior=behavior, space=self.space,
            defaults={"main_piece": None})
        return behavior

    def ensure_param(self, behavior: Behavior, name: str) -> Parameter:
        param, _ = Parameter.objects.get_or_create(
            behavior=behavior, name=name,
            defaults={"data_type": "string"})
        return param

    # --------------------------------------------------------------- piezas
    def piece(self, section: str, name: str, desc: str,
              piece_type: str = "content",
              config: Optional[dict] = None) -> Piece:
        piece, created = Piece.objects.update_or_create(
            crate=self.crates[section], name=name,
            defaults={"description": desc, "piece_type": piece_type,
                      "config": config or {}})
        self.pieces[name] = piece
        return self._track(piece, created)

    # ------------------------------------------------------------ contenido
    def _fragment(self, piece: Piece, order: int, **fields) -> Fragment:
        # Upsert por (piece, order). Los defaults resetean SIEMPRE todos los
        # campos que el seeder usa: si un fragment cambia de tipo entre
        # corridas (mensaje -> behavior), no quedan restos del tipo anterior.
        defaults = {"fragment_type": "message", "body": None, "header": None,
                    "footer": None, "behavior": None, "embedded_piece": None,
                    "addl_params": None}
        defaults.update(fields)
        frag, created = Fragment.objects.update_or_create(
            piece=piece, order=order, defaults=defaults)
        return self._track(frag, created)

    def msg(self, piece: Piece, body: str, header: Optional[str] = None,
            footer: Optional[str] = None, order: int = 0) -> Fragment:
        # 🤖 `\n`/`\n\n` en `body` sí rinden como salto/párrafo en WhatsApp:
        # el motor conserva los `\n` (replacer_from_data).
        return self._fragment(piece, order, body=body, header=header,
                              footer=footer)

    def embedded(self, piece: Piece, dest: Piece, order: int = 1) -> Fragment:
        # 🧩 Auto-avance entre mensajes del bot: renderiza `dest` en línea.
        return self._fragment(piece, order, fragment_type="embedded",
                              embedded_piece=dest)

    def _dest(self, dest: Piece, *, reply: Optional[Reply] = None,
              written: Optional[Written] = None,
              piece: Optional[Piece] = None, is_default: bool = True,
              order: int = 0) -> Destination:
        # Clave natural según el dueño: un reply o una written tienen UN solo
        # destino; una pieza 'destinations' distingue por order.
        lookup = ({"reply": reply} if reply else
                  {"written": written} if written else
                  {"piece": piece, "order": order})
        d, created = Destination.objects.update_or_create(
            **lookup,
            defaults={"destination_type": "piece", "piece_dest": dest,
                      "is_default": is_default, "order": order})
        return self._track(d, created)

    def buttons(self, piece: Piece, question: str,
                options: list[tuple[str, Piece, Optional[dict]]],
                footer: Optional[str] = None) -> Fragment:
        """🔘/📋 options: [(title, dest_piece, {extra_name: value} | None)].

        ≤3 opciones -> botones; el motor pasa a lista solo con >3.
        """
        limit = (BUTTON_TITLE_LIMIT if len(options) <= 3
                 else ROW_TITLE_LIMIT)
        for title, *_ in options:
            if len(title) > limit:
                raise ValueError(
                    f"Título '{title}' ({len(title)}) excede {limit} "
                    "caracteres (límite WhatsApp)")
        frag = self.msg(piece, question, footer=footer)
        for order, (title, dest, assigns) in enumerate(options):
            reply, created = Reply.objects.update_or_create(
                fragment=frag, order=order,
                defaults={"reply_type": "quick_reply", "title": title})
            self._track(reply, created)
            self._dest(dest, reply=reply)
            # Sin clave natural: se recrean por dueño (borra las obsoletas).
            reply.assignments.all().delete()
            for ex_name, value in (assigns or {}).items():
                Assign.objects.create(
                    reply=reply, extra=self.extras[ex_name],
                    extra_value=value)
        return frag

    def capture(self, piece: Piece, prompt: str, extra_name: str,
                dest: Piece) -> Written:
        # 📝 Captura libre -> extra. La Written se actualiza en su lugar:
        # borrarla borraría la Piece (Piece.written es CASCADE invertido).
        self.msg(piece, prompt)
        written = piece.written
        if written:
            written.extra = self.extras[extra_name]
            written.available = True
            written.save(update_fields=["extra", "available"])
        else:
            written = Written.objects.create(
                extra=self.extras[extra_name], available=True)
            piece.written = written
            piece.save(update_fields=["written"])
        self._keep[Written].add(written.pk)
        self._dest(dest, written=written)
        return written

    def bifurcation(self, piece: Piece, extra_name: str,
                    branches: list[tuple[str, Piece]],
                    default_dest: Piece) -> None:
        # ◆ piece es de tipo 'destinations'. Cada rama lleva su
        # ConditionRule; el default (is_default=True) nunca se evalúa, es el
        # fallback.
        extra = self.extras[extra_name]
        for order, (value, dest) in enumerate(branches):
            d = self._dest(dest, piece=piece, is_default=False, order=order)
            d.rules.all().delete()
            ConditionRule.objects.create(
                destination=d, extra=extra, extra_values=[value])
        d = self._dest(default_dest, piece=piece, is_default=True,
                       order=len(branches))
        d.rules.all().delete()

    def link(self, origin: Piece, dest: Piece) -> Destination:
        # Paso de largo de una pieza 'destinations' (placeholder ⚙️) al
        # siguiente, sin correr behavior.
        return self._dest(dest, piece=origin)

    def behavior_step(self, piece: Piece, behavior_name: str, dest: Piece,
                      *, generic: bool = False,
                      params: Optional[dict] = None) -> Fragment:
        """⚙️ Pieza 'content' que corre `behavior_name` y auto-avanza a
        `dest`.

        Una pieza 'destinations' se salta sus fragments (piece.py); por eso
        el paso son dos fragments: el behavior (order 0) y un embedded
        (order 1) que renderiza `dest` en línea.

        `params` ({nombre: valor}) crea un ParamValue POR FRAGMENTO (no en
        el ApplyBehavior): un behavior genérico se reusa con distinto
        esquema por paso y FragmentProcessor inyecta fragment.values en los
        parámetros."""
        behavior = self.ensure_behavior(behavior_name, generic=generic)
        frag = self._fragment(piece, 0, fragment_type="behavior",
                              behavior=behavior)
        frag.values.all().delete()
        for pname, pvalue in (params or {}).items():
            ParamValue.objects.create(
                parameter=self.ensure_param(behavior, pname),
                fragment=frag, value=pvalue)
        self.embedded(piece, dest, order=1)
        return frag

    def wa_form_step(self, piece: Piece, dest_piece: Piece, *,
                     options: list[dict], flow_id: str, body: str,
                     extra: str, min: int = 1) -> Fragment:
        """☑️ Pieza que MANDA un WhatsApp Flow multiselect y ESPERA el
        submit.

        A diferencia de behavior_step, NO lleva embedded de auto-avance: la
        pieza termina tras enviar el formulario y se queda esperando. El
        avance a `dest_piece` lo dispara WaFormReplyProcessor (vía
        `dest_piece_pk`) cuando llega el `nfm_reply`. La lista de opciones
        va en `fragment.addl_params` (JSON) porque no cabe en el ParamValue
        (CharField 255)."""
        behavior = self.ensure_behavior("multiple_select", generic=True)
        return self._fragment(
            piece, 0, fragment_type="behavior", behavior=behavior,
            addl_params={
                "flow_id": flow_id, "body": body, "extra": extra,
                "dest_piece_pk": dest_piece.pk, "options": options,
                "min": min,
            })

    # -------------------------------------------------------------- entrada
    def wire_global_start(self, piece: Piece) -> None:
        """Hace 'entrable' el flujo: cualquier mensaje de un usuario nuevo
        dispara el behavior `start` (text.py), que debe rendir `piece`. Se
        apunta el ApplyBehavior **global** (space__isnull): el motor
        resuelve `start` con order_by('-space') y en Postgres los NULL
        ordenan primero, así que prefiere el global sobre cualquier scoped.
        Sin esto, el global con main_piece vacío recursiona."""
        behavior, _ = Behavior.objects.get_or_create(
            name="start", defaults={"in_code": True, "collection": None})
        apply, _ = ApplyBehavior.objects.get_or_create(
            behavior=behavior, space=None,
            defaults={"main_piece": piece})
        if apply.main_piece_id != piece.id:
            apply.main_piece = piece
            apply.save(update_fields=["main_piece"])

    # ----------------------------------------------------------------- poda
    def finalize(self) -> dict:
        """Poda lo no declarado dentro de los crates administrados y regresa
        el reporte (conteos + los sets para auditoría externa)."""
        crates = list(self.crates.values())
        pruned = 0

        # Piezas no declaradas: borrarlas cascadea a sus hijos. Sus Written
        # se borran DESPUÉS y por id: borrar la Written primero borraría la
        # Piece (CASCADE) y el conteo mentiría.
        stale = Piece.objects.filter(crate__in=crates).exclude(
            id__in=self._keep[Piece])
        stale_written_ids = list(
            stale.exclude(written__isnull=True)
            .values_list("written_id", flat=True))
        pruned += stale.delete()[0]
        pruned += Written.objects.filter(id__in=stale_written_ids).delete()[0]

        # Piezas que dejaron de capturar: desreferenciar antes de borrar.
        for piece in (Piece.objects.filter(
                crate__in=crates, written__isnull=False)
                .exclude(written_id__in=self._keep[Written])):
            written_id = piece.written_id
            piece.written = None
            piece.save(update_fields=["written"])
            pruned += Written.objects.filter(id=written_id).delete()[0]

        pruned += (Fragment.objects.filter(piece__crate__in=crates)
                   .exclude(id__in=self._keep[Fragment]).delete()[0])
        pruned += (Reply.objects.filter(fragment__piece__crate__in=crates)
                   .exclude(id__in=self._keep[Reply]).delete()[0])
        owned = (Q(piece__crate__in=crates)
                 | Q(reply__fragment__piece__crate__in=crates)
                 | Q(written__piece__crate__in=crates))
        pruned += (Destination.objects.filter(owned)
                   .exclude(id__in=self._keep[Destination]).delete()[0])

        self.stats["pruned"] = pruned
        return dict(self.stats)
