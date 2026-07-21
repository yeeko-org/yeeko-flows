# yeeko-chat-flow — `rebuilding` branch

Django engine for WhatsApp/Messenger conversational flows, defined in
the DB (`Flow → Crate → Piece → Fragment → Reply → Destination`), with
message primitives from the sibling `yeeko_abc` library. This branch is
the ground-up rebuild of the engine, started 2026-07-21 from `develop`.

**Start here:** read `.claude/rebuilding/` (README → decisiones.md →
backlog.md) before any rebuild work. It holds the methodology, ADRs,
session backlog and research reports. Every feature enters through
design dialogue → Ricardo's explicit approval → implementation
(ADR-001); no code lands without his full understanding.

## Commands

- `python manage.py test --noinput` — run tests (Postgres test DB;
  `--noinput` auto-drops a leftover test DB).
- `python manage.py runserver` — also registers in-code behaviors on
  boot (`CheckBehaviorRecord` in `infrastructure/tool/apps.py`).

## Architecture

- Layered: presentation → interface → services → infrastructure;
  imports only point inward. Full docs at repo root: `arquitectura.md`,
  `modelos.md`, `procesadores.md`, `interface.md`, `Trigger.md`, etc.
- `services/manager_flow/` routes each inbound message by type to
  processors in `services/processor/`; `services/behavior/` holds
  in-code behaviors referenced by name from the DB (`ApplyBehavior`).
- `interface/whatsapp/`, `interface/messenger/` — platform adapters
  over the generic request/response models of `yeeko_abc`.

## Context & boundaries

- The sibling checkout `../yeeko-chat-flow` (branch `caceh-demo`) is
  the **live client demo** — never edit it from rebuild sessions.
- Features from `caceh-demo` (FlowSeeder, WaForm, PDF delivery,
  replacer line-break fix…) are NOT on this branch yet; they get
  ported re-designed per the backlog. Their gotchas and skills live in
  that checkout's `CLAUDE.md`, `.claude/skills/` and
  `.claude/deuda-tecnica.md` — consult them when porting a feature,
  then migrate the relevant skill here.
- Known engine debt inherited via develop is summarized in
  `.claude/rebuilding/00-diagnostico.md`.
