# yeeko-chat-flow

Django engine for WhatsApp conversational flows. Flows are defined in the
DB (`Flow → Crate → Piece → Fragment → Reply → Destination`), not in
code; it inherits message primitives from the `yeeko_abc` library.

## Commands

- Testing levels, commands and covered e2e flows: `TESTING.md`.
- `python manage.py test --noinput` — run tests (Postgres test DB; use
  `--noinput` to auto-drop a leftover test DB).
- `python manage.py runserver` — also registers in-code behaviors via
  `CheckBehaviorRecord` (`infrastructure/tool/apps.py`, runs on
  `runserver`/`shell`).

## Architecture

- `services/manager_flow/` — entry point; routes each inbound message by
  type to a processor.
- `services/processor/` — per-message-type processors (text, interactive,
  media, written, behavior, destination).
- `services/behavior/` — in-code behaviors (`start`, `reset`, `insistent`,
  `multiple_select`, …), keyed by name in `__init__.py`.
- `services/seeder/` — `FlowSeeder`: idempotent flow seeding (upsert by
  natural keys + prune; never delete-and-recreate — piece/fragment/reply
  PKs must survive a reseed or interaction history and live sessions
  break). Guide: `.claude/skills/flow-seeder`; consumer:
  `projects/caceh/seed/`.
- `interface/whatsapp/` — WhatsApp send (`response.py`) and receive
  (`request.py`); `*_to_data` methods build the Graph API payloads.
- `infrastructure/` — Django models (box, talk, xtra, tool, assign, …).
- Behavior params: `Fragment.addl_params` (JSON) is merged into behavior
  parameters as the low-priority layer, since `ParamValue.value` is only
  `varchar(255)` and can't hold rich data (e.g. an options list).
  `FragmentProcessor` also injects `fragment_id`; behaviors that send
  messages must forward it (e.g. `WaFormMessage(fragment_id=…)`) or the
  outgoing `Interaction` has no fragment and the user's context piece
  never advances.

## Conventions

- **WhatsApp Flows = `WaForm` namespace.** All Meta-Flows code is prefixed
  `WaForm` (`WaFormMessage`, `WaFormReplyProcessor`, `wa_form_to_data`) to
  avoid colliding with the conversational `Flow` model. Never name a new
  symbol `Flow*`. Author-facing behavior is named by function
  (`multiple_select`), not by transport. Adding a multiple-select question:
  see `docs/wa_form_multiple_select.md`.

## Gotchas

- **Test suite is flaky by pre-existing design**, independent of any new
  code: `ApiRecord.__del__` calls `save()` on GC and poisons the shared
  connection across tests; several factories set `phone` via Faker, which
  overflows `User.phone` (`varchar(20)`). In new tests, pin
  `UserFactory(phone="…")` and `gc.collect()` in `tearDown` of tests that
  exercise `ManagerFlow`. Run modules in isolation to confirm real status.
- **Line breaks in message bodies:** the parameter replacer collapses
  whitespace on every body (text, buttons, sections, WaForm). It must use
  `re.sub(r'[^\S\n]+', ' ', …)` (horizontal-only) so `\n` survives and
  WhatsApp renders line breaks. The old `\s+` ate every `\n` and flattened
  each message to one line — **do not reintroduce it**. There are two twin
  copies to keep in sync: `utilities/replacer_from_data.py` (message render)
  and `utilities/parameters.py` (behavior params). No data-only workaround
  exists from a seed: every whitespace char (incl. NBSP, U+2028) is
  collapsed, and zero-width chars don't break lines — the fix must live here.
