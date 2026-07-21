# Engine contract: WaForm out / nfm_reply in

Verified against the code. Files involved:

| Concern | File |
|---|---|
| Send the Flow (behavior) | `services/behavior/multiple_select.py` |
| Build the interactive message | `interface/whatsapp/response.py::wa_form_to_data` |
| Outgoing model | `services/response/models.py::WaFormMessage` |
| Parse the completion webhook | `interface/whatsapp/request.py::_create_wa_form_reply` |
| Incoming model | `services/request/message_model.py::WaFormReplyMessage` |
| Handle completion (write extra + advance) | `services/processor/wa_form_reply.py` |

## Outgoing — what the engine sends

`wa_form_to_data` produces an `interactive` message of `type: "flow"`:

```jsonc
{
  "flow_message_version": "3",
  "flow_token": "<BuiltReply uuid>",
  "flow_id": "1308618661432871",
  "flow_cta": "Seleccionar",          // truncated to 20 chars
  "flow_action": "navigate",
  "flow_action_payload": {
    "screen": "SELECT",                // must match the Flow JSON screen id
    "data": {                          // the per-message catalog
      "title": "…",                    // sent, not declared/bound -> ignored
      "label": "…",                    // -> CheckboxGroup / TextBody
      "options": [{"id": "…", "title": "…"}],
      "min": 0,                        // sent, not bound -> ignored client-side
      "flow_token": "<uuid>"           // echoed back on completion
    }
  }
}
```

Only `options`, `label` and `flow_token` are declared in
`assets/multiselect.flow.json` and therefore actually bind; `title`/`min`/`max`
are tolerated extra keys.

## Incoming — what the Flow must return

On submit, Meta posts `interactive.type == "nfm_reply"`. The engine reads
`nfm_reply.response_json` and pulls exactly two keys
(`request.py:220-233`):

```json
{ "flow_token": "<uuid>", "selection": ["id1", "id2"] }
```

- `selection` → `WaFormReplyMessage.selected` (coerced to a list).
- `flow_token` → correlates back to the `BuiltReply` created when sending.

So the terminal screen's `complete` action **must** return both keys. The
published Flow's Footer does exactly:

```json
"payload": { "selection": "${form.selection}", "flow_token": "${data.flow_token}" }
```

## Completion handling

`WaFormReplyProcessor.process`:
1. Look up `BuiltReply` by `flow_token` (must be `is_for_write=True`).
2. Read `params` (set when the form was sent): `extra`, `dest_piece_pk`,
   `min`, `max`.
3. `_validate_count` — non-blocking; only logs if out of range.
4. Write `selected` into the target JSON extra (`origin="payload"`).
5. Advance to `dest_piece_pk` via `PieceProcessor`.

No separate confirmation step: writing the extra and advancing happen in one
shot (the form submit *is* the confirmation).
