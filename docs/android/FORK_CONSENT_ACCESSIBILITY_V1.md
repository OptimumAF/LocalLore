# Accessible fork-consent rows

Refs #13 M09.05/M09.06, supporting #14 M10.02. Implemented for review;
runtime accessibility qualification remains pending.

Each fork consent label and its checked state belong to one toggleable Row
with `Role.Checkbox`. The visual Checkbox has no independent click callback.
The unchanged visible label supplies the merged text; fixed consent text adds
no private story or hidden native state. This follows
[Android's Compose accessibility pattern](https://developer.android.com/develop/ui/compose/accessibility/api-defaults).

The **entire interactive Row** is inside `key(delivery)`. Moving only the
passive child inside that key would leave the new parent's event controller
outside the existing retirement fence. Each value change still runs through
`act`; `!state.busy`, remembered consent reset and current-view identity checks
are unchanged. Tags `fork-consent` and `fork-forget-consent` identify the parent
action nodes, preserving existing callers and test selectors.

Toggling a label changes consent only. Create, Retry and Forget remain separate
explicit actions with their existing captured input/review and native controller
checks. Kotlin adds no gameplay or persistence authority and does not clear a
recovery hint from the consent callback.

The Row is full-width with a48dp minimum height; the passive checkbox retains
48dp layout and the weighted label wraps without a line limit. These source
constraints are not measured device touch/glyph/keyboard/TalkBack results.
No permission, dependency, model, runner, guest or protocol changes are added.

Five real-Compose regression methods assert intended merged label/role/state,
one checkable action, separate confirmation, busy touch rejection and2× font
scroll/reachability. They are compiled but **0/5 executed**. Existing fork scope
and component test files remain unchanged. Host JVM regressions cannot prove
these Android assertions; full M09.05 criteria remain unchecked.
