# Wiring a multiselect into the CACEH seed

Target: replace the **D1 stopgap** in
`projects/caceh/management/commands/seed_flow.py::_wire_section_d_e` (the native
single-select `_buttons(p["d_actividades"], …)`) with the real `multiple_select`
behavior pointing at the published Flow.

## The gotcha: do NOT use `_behavior_step`

`_behavior_step` appends an embedded fragment that **auto-advances** to `dest`
right after the behavior runs. That is wrong for a Flow: the piece must **send
the form and then wait** for the user to submit. The advance happens later, when
the `nfm_reply` arrives, via `WaFormReplyProcessor` → `dest_piece_pk`.

So wire it with a behavior fragment **without** the embedded auto-advance:

```python
def _wa_form_step(self, piece_name, dest_piece, *, params):
    """Like _behavior_step but the piece WAITS for the Flow submit:
    no embedded auto-advance. WaFormReplyProcessor fires dest_piece_pk
    when the nfm_reply arrives."""
    piece = self.p[piece_name]
    piece.piece_type = "content"
    piece.config = {}
    piece.save(update_fields=["piece_type", "config"])
    behavior = self._ensure_behavior("multiple_select", generic=True)
    frag = Fragment.objects.create(
        piece=piece, fragment_type="behavior", behavior=behavior, order=0)
    full = dict(params, dest_piece_pk=dest_piece.pk)
    for pname, pvalue in full.items():
        ParamValue.objects.create(
            parameter=self._ensure_param(behavior, pname),
            fragment=frag, value=pvalue)
```

Call it in place of the stopgap:

```python
self._wa_form_step(
    "d_actividades", p["d_deriva_categoria"],
    params={
        "flow_id": "1308618661432871",
        "body": "¿Cuáles actividades realiza la persona trabajadora?",
        "extra": "actividades",
        "options_extra": "catalogo_actividades",  # see below
        "min": 1,
    })
```

## Open detail to resolve when wiring: how `options` reach the behavior

`ParamValue.value` is a text field, so a literal `options` *list* may not round-
trip cleanly. Two clean paths:

1. **`options_extra` (recommended):** pre-seed a JSON extra
   (e.g. `catalogo_actividades`) with the `[{id,title}]` list of the ~15-20
   activities from clause CUARTA, and pass its name. The behavior resolves it via
   `member.get_extra_values_data()`.
2. **Inline `options`:** only if `ParamValue.value` can hold JSON / the behavior
   tolerates a JSON string — verify before relying on it.

`multiple_select` is a **generic** behavior (`generic=True` → resolved in
`services.behavior`, no Collection). Confirm it is registered (the seed already
reports `multiple_select` among registered behaviors).

## `extra` must be JSON

The `actividades` extra is declared `("actividades", "json")` in the seed — good,
the chosen ids are written as a list.
