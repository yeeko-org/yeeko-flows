# yeeko-chat-flow — `rebuilding` branch

Django engine for WhatsApp/Messenger conversational flows, defined in the DB (`Flow → Crate → Piece → Fragment → Reply → Destination`), with message primitives from the sibling `yeeko_abc` library. This branch is the ground-up rebuild of the engine, started 2026-07-21 from `develop`.

## Process docs (`docs/`)

The rebuild is documented with the `documenter` skill: `docs/tasks/` (sessions and pending work), `docs/decisions/` (ADRs), `docs/reference/` (how the engine is today, incl. the design-essence manifesto `esencia`), `docs/records/` (logbooks, reports), `docs/notes/` (Ricardo's notes). Nodes link by `[[id]]`; a pre-commit hook runs the validator.

- **Start of a rebuild session:** run the documenter `pending` command to see what's open, then read the session's task (its body is the brief) and the references it links. The essence hub is `docs/reference/esencia.md`.
- **Work:** extended design dialogue → Ricardo's explicit decision → implementation. No code lands without his full understanding.
- **Close:** decisions, tasks and records go through `documenter`; nothing provisional stays in prose (no "under construction" markers).

## Commands

- `python manage.py test --noinput` — run tests (Postgres test DB; `--noinput` auto-drops a leftover test DB).
- `python manage.py runserver` — also registers in-code behaviors on boot (`CheckBehaviorRecord` in `infrastructure/tool/apps.py`).

## Architecture

- Layered: presentation → interface → services → infrastructure; imports only point inward. Full docs at repo root: `arquitectura.md`, `modelos.md`, `procesadores.md`, `interface.md`, `Trigger.md`, etc.
- `services/manager_flow/` routes each inbound message by type to processors in `services/processor/`; `services/behavior/` holds in-code behaviors referenced by name from the DB (`ApplyBehavior`).
- `interface/whatsapp/`, `interface/messenger/` — platform adapters over the generic request/response models of `yeeko_abc`.

## Context & boundaries

- The sibling checkout `../yeeko-chat-flow` (branch `caceh-demo`) is the **live client demo** — never edit it from rebuild sessions.
- Features from `caceh-demo` (FlowSeeder, WaForm, PDF delivery, replacer line-break fix…) are NOT on this branch yet; they get ported re-designed per their tasks in `docs/`. Their gotchas and skills live in that checkout's `CLAUDE.md`, `../yeeko-chat-flow/.claude/skills/` and `../yeeko-chat-flow/.claude/deuda-tecnica.md` — consult them when porting a feature, then migrate the relevant skill here.
- Product-of-CACEH documentation lives in `../bot_caceh/docs/`; only engine matters are documented here, and cross-repo mentions are plain text, never `[[links]]`.
