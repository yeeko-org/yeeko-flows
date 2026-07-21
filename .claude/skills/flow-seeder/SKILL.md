---
name: flow-seeder
description: Sembrar (seed) un flujo conversacional en la BD del motor
  yeeko-chat-flow con services.seeder.FlowSeeder. Úsalo al escribir o
  modificar un management command de siembra, al traducir un flujo .md
  (notación flow-builder) a piezas/fragments/replies en BD, al agregar
  piezas o secciones a un flujo existente, o al depurar idempotencia,
  poda, PKs que cambian, o historial borrado tras resembrar.
---

# flow-seeder

Guía para **traducir un flujo diseñado en .md** (notación del skill
`flow-builder`) **a la BD del motor** con `services.seeder.FlowSeeder`.
El diseño (piezas, íconos, límites de WhatsApp) vive en `flow-builder`;
este skill es el lado de inserción: API, idempotencia y receta para un
proyecto nuevo. Referencia viva: `projects/caceh/` (primer consumidor).

## Idempotencia: upsert + poda ("declara todo, poda el resto")

Cada corrida del seed **actualiza en su lugar** por clave natural y al final
`finalize()` **poda** lo que quedó fuera de la declaración, solo dentro de
los crates que el seeder administra. Nunca borra-y-recrea.

Por qué importa (no lo cambies a rebuild):

- `Interaction.fragment` es CASCADE: recrear fragments **borra historial**
  de conversación (constancia fechada).
- `BuiltReply.reply` es CASCADE: recrear replies **enmudece los botones**
  de mensajes ya enviados.
- El motor ubica al usuario por su última interacción saliente con
  fragment (`calculate_context_piece`): PKs nuevos = sesiones rotas.

Claves naturales: `Piece (crate, name)` · `Fragment (piece, order)` ·
`Reply (fragment, order)` · `Destination (reply | written | piece+order)`.
`Assign`/`ConditionRule`/`ParamValue` se recrean por dueño (nada de runtime
los referencia). `Flow`/`Crate`/`Collection`/`Behavior`/`ApplyBehavior` son
persistentes (`get_or_create`); `Extra` es `update_or_create` (un cambio de
format/classify sí se aplica).

Consecuencia práctica: los **nombres de pieza son la identidad**. Renombrar
una pieza = borrar la vieja y crear una nueva (PK nuevo); cambiar su texto,
botones o destinos conserva el PK.

## Mapeo ícono (flow-builder) → método (FlowSeeder)

| Ícono .md | Método | Notas |
|---|---|---|
| 🤖 mensaje | `msg(piece, body)` | `\n`/`\n\n` sí rinden en WhatsApp |
| 🔘 botones / 📋 lista | `buttons(piece, question, options)` | valida 20/24 chars al sembrar (si se pasa, Meta rechaza TODO el mensaje: 400 131009) |
| 📝 captura | `capture(piece, prompt, extra, dest)` | crea/actualiza la `Written` |
| ◆ bifurcación | `bifurcation(piece, extra, branches, default)` | pieza `destinations`; el default es fallback, no se evalúa |
| ⚙️ mini-función | `behavior_step(piece, behavior, dest, generic=, params=)` | pieza `content`: fragment behavior (order 0) + embedded de auto-avance (order 1) |
| ☑️ FormWa | `wa_form_step(piece, dest, options=, flow_id=, …)` | SIN auto-avance: espera el submit; avanza por `dest_piece_pk`. Publicación del Flow: skill `whatsapp-flows` |
| 🧩 sub-flujo / auto-avance | `embedded(piece, dest)` | renderiza `dest` en línea |
| pass-through | `link(origin, dest)` | pieza `destinations` que pasa de largo |
| `{{var}}` | `declare_extras(pairs, classify)` | pairs: `[(nombre, formato\|None)]` |
| entrada | `wire_global_start(piece)` | apunta el `start` global (space NULL) |
| cierre | `finalize()` | **obligatorio al final**: poda + stats; conectividad aparte con `seeder.audit.connectivity(pieces, "pieza_inicial")` |

## Receta: seed de un proyecto nuevo

Estructura (copiar de `projects/caceh/`):

```
projects/<proy>/seed/
    extras.py       # EXTRAS = [(nombre, formato|None), …]
    pieces.py       # SECTIONS = {clave: nombre_crate}; PIECES = [(sección,
                    # nombre, desc, piece_type), …]  ('content' salvo ◆/link)
    section_*.py    # def wire(sdr, p): cableado con el copy inline
projects/<proy>/management/commands/seed_flow.py   # command delgado
```

El command (ver `projects/caceh/management/commands/seed_flow.py`):
`@transaction.atomic` → `FlowSeeder(space, nombre, SECTIONS)` →
`ensure_collection` (si hay behaviors de proyecto) → `declare_extras` →
crear todas las `piece()` (para poder apuntar destinos hacia adelante) →
`wire()` por sección → `wire_global_start` → `finalize()` + reporte.

El copy (textos) va **inline en el cableado**: el canónico vive en el .md
de diseño del flujo; no crear un `copy.py` (tercera copia).

## Gotchas

- **`Piece.written` es CASCADE invertido**: borrar una `Written` borra su
  `Piece`. El seeder ya lo maneja (desreferencia antes de podar); si tocas
  la poda, conserva ese orden.
- **`ParamValue.value` es varchar(255)**: data rica (lista de opciones del
  FormWa) va en `Fragment.addl_params` (JSON), que se mezcla como capa de
  baja prioridad en los parámetros del behavior.
- **`fragment_id` en behaviors**: `FragmentProcessor` inyecta el pk del
  fragment a los parámetros; un behavior que envía mensajes debe pasarlo al
  message (p. ej. `WaFormMessage(fragment_id=…)`) o la Interaction saliente
  queda sin fragment y el usuario se "atora" en la pieza anterior.
- **Behaviors genéricos vs de proyecto**: `generic=True` → sin Collection,
  se resuelve en `services.behavior`; `generic=False` → Collection con
  `app_label` (p. ej. `projects.caceh` → `projects/caceh/behaviors`, alias
  snake_case). Requiere `ensure_collection()` previo.
- **Entrypoint global**: `wire_global_start` usa el `ApplyBehavior` con
  `space=None`; el motor ordena con `nulls_last` explícito — no crear
  ApplyBehaviors `start` por space para el mismo flujo.
- **No sourcear `config/.env`** antes de `manage.py` (CRLF rompe
  `TIME_ZONE`); los tests e2e con Gemini real sí necesitan
  `GEMINI_API_KEY` en el entorno (ver docstring de `test_flow_e2e.py`).
- **Correr dos veces** tras cambiar un seed: la segunda corrida debe dar
  `creados=0 podados=0`; si no, hay una clave natural inestable (típico:
  `order` calculado distinto entre corridas).

## Tests

Patrón en `projects/caceh/tests/test_seed_flow.py`: (1) el arnés WP6B
dispara un fragment behavior por el motor real; (2) `SeedIdempotencyTests`
— resembrar conserva PKs, conserva una `Interaction` ligada y regresa a la
BD al estado declarado. Replicar ambos en proyectos nuevos.
