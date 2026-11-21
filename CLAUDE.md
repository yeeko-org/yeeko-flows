# yeeko-chat-flow — `rebuilding` branch

Django engine for WhatsApp/Messenger conversational flows, defined in the DB (`Flow → Crate → Piece → Fragment → Reply → Destination`), with message primitives from the sibling `yeeko_abc` library. This branch is the ground-up rebuild of the engine, started 2026-07-21 from `develop`.

## Process docs (`docs/`)

`docs/` is a submodule of the **private** repo `yeeko-org/yeeko-flows-docs`: the engine's documenter graph, shared with the sibling worktree `../yeeko-chat-flow` (the `caceh-*` line). Every engine decision is documented there, whichever branch it is born on; the design-essence manifesto is the `esencia` reference. This repo is public: nothing of the graph is committed outside `docs/`.

- **Submodule routine:** `docs/` always stays on `main`. Each worktree has its own clone, so before creating nodes run `git -C docs pull --ff-only` (offline: `git -C docs fetch sibling && git -C docs merge --ff-only sibling/main`) or two sessions mint the same task id. Doc commits go inside `docs/`, where a pre-commit hook runs the validator from this root; a doc-only change does not pin the pointer here.

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

- The sibling checkout `../yeeko-chat-flow` (the `caceh-*` line) is the **live client code** — never edit its code from rebuild sessions.
- Features from `caceh-demo` (FlowSeeder, WaForm, PDF delivery, replacer line-break fix…) are NOT on this branch yet; they get ported re-designed per their tasks in `docs/`. Their gotchas and skills live in that checkout's `CLAUDE.md`, `../yeeko-chat-flow/.claude/skills/` and `../yeeko-chat-flow/.claude/deuda-tecnica.md` — consult them when porting a feature, then migrate the relevant skill here.
- The CACEH product is documented in the sibling repo `../bot_caceh`; only engine matters are documented here. Shared topics have one home node and at most one mirror (`## Espejo`), per the frontier-and-mirror decision in `../bot_caceh/docs/decisions/`. Cross-repo mentions are plain text in a fixed form — «task-N de bot_caceh», «adr-N de yeeko-chat-flow» — never `[[links]]`. When a task touches CACEH, one single opening explorer reads both graphs. At close, grep the touched nodes for `bot_caceh` and update the home or the mirror on that side.
