---
name: whatsapp-flows
description: Publish and wire WhatsApp Flows ("FormWa") into the yeeko-chat-flow
  engine via the Meta Graph API. Use when adding a multiple-select (checkbox)
  question, publishing a Flow, getting a flow_id, debugging the multiple_select
  behavior / WaForm / nfm_reply, or anything about CheckboxGroup, flow_token, or
  data_action_payload in this engine.
---

# whatsapp-flows

Operational guide to **publish a WhatsApp Flow on Meta** and **wire it** to the
`multiple_select` behavior in this engine. The design-time notation (when to use
a FormWa piece in a `.md` flow) lives in the `flow-builder` skill; this skill is
the ops + engine-wiring side.

## Key architectural decision (already baked into the engine)

The engine sends Flows with `flow_action: "navigate"` and passes the catalog
**inline** in `flow_action_payload.data` (see
`interface/whatsapp/response.py::wa_form_to_data`). So:

- **No `data_channel_uri` / hosted endpoint is needed.** One **static published
  Flow** serves every multiple-select question; the options travel per-message.
  This keeps hosting cost at zero — important for the CACEH ~15 MXN ceiling.
- Dynamic options are fine: they ride in the navigate payload, not a server.

## The published Flow

The concrete operational data of CACEH's published Flow (flow_id, WABA, account,
Meta's CheckboxGroup limits) is **not kept here** — it lives with the product,
in ~/dev/yeeko/bot_caceh/docs/reference/2026-08-18-whatsapp-flow-publicado.md.
Keeping it in one place avoids the two copies drifting apart.

What is generic and stays here: one **static published Flow** with a single
terminal screen `SELECT`, a `CheckboxGroup` bound to `${data.options}` and a
Footer whose `complete` payload returns `{ selection, flow_token }` — which is
exactly what the engine expects back.

> **Reuse:** a single Flow backs *any* multiple-select question — pass a
> different `options`/`body`/`extra` when wiring. You do not publish a new Flow
> per question.

## Publishing a Flow (script)

`scripts/publish_flow.py` does create-as-DRAFT → fetch `validation_errors` →
publish only if clean (a published Flow **cannot be edited**, only cloned or
deleted). The token is read from `Account.token` by `--pid` and never printed.

```bash
# Validate a draft (no publish):
.venv/bin/python .claude/skills/whatsapp-flows/scripts/publish_flow.py \
  --json .claude/skills/whatsapp-flows/assets/multiselect.flow.json \
  --name "Multiselect genérico" --categories OTHER \
  --waba 3449947368500778 --pid 1128183617053069

# Publish an already-validated draft:
… --flow-id <DRAFT_ID> --waba 3449947368500778 --pid 1128183617053069 --publish
```

Categories must be from Meta's closed list (`OTHER`, `SURVEY`, …). To change a
published Flow, clone it (new id) — you cannot edit in place.

### Checking the token can manage Flows

Publishing needs the scope **`whatsapp_business_management`** (sending only needs
`whatsapp_business_messaging`). Verify with `debug_token` — its
`granular_scopes[*].target_ids` also list the WABA ids the token can act on:

```
GET https://graph.facebook.com/v21.0/debug_token?input_token=TOKEN&access_token=TOKEN
```

The "WP7 code" account token has both scopes; the "stepper" token is a fake.

## Wiring a multiselect question into a flow

Two ends must agree. The engine contract (what `WaFormMessage` sends and what
`nfm_reply` must return) is in
**[references/motor-contract.md](references/motor-contract.md)**. Seed the piece
with `FlowSeeder.wa_form_step`, which deliberately omits the auto-advance
fragment: the piece must send the form and *wait*; `WaFormReplyProcessor` fires
`dest_piece_pk` when the `nfm_reply` arrives.

Short version — the `multiple_select` behavior needs these params:

| Param | Meaning |
|---|---|
| `flow_id` | the published Flow id (see bot_caceh reference above) |
| `body` | the question text (also used as the CheckboxGroup label) |
| `extra` | name of the JSON extra to write the chosen ids into (as a list) |
| `dest_piece_pk` | piece to advance to after submit |
| `options` *or* `options_extra` | `[{id,title}]` list, inline or from an extra |
| `min` / `max` | server-side safety net only (see below) |

## Gotchas

- **min/max are not enforced client-side.** WhatsApp static Flows require
  `min/max-selected-items` to be *static integers*, so the generic Flow uses
  `required: true` (forces ≥1). `WaFormReplyProcessor._validate_count` is a
  non-blocking server-side check that only logs if the count is out of range.
  If you need a hard client-side max, that needs a Flow variant.
- **Extra data keys are harmless.** The behavior also sends `title`/`max` in
  `data`; the Flow ignores keys it doesn't declare. Only `options`, `label` and
  `flow_token` are actually bound.
- **Published Flows are immutable.** Edit `assets/multiselect.flow.json`, then
  publish a *new* Flow and swap the `flow_id` in the wiring.
- **`flow_token` correlation.** The behavior creates a `BuiltReply`; its uuid is
  the `flow_token`. The terminal screen must echo it back or the completion
  can't be matched to the conversation.
