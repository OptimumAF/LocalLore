# Player presentation V2

B41. Refs #307; #13 (M09.04/M09.06); #14 (M10.02).
This is a display projection, not another engine, context compiler, save format,
or observer capability. The existing legacy and thin snapshot operations keep
their contracts, including legacy Domain2 refusal.

The new Host operation is `play_presentation_v2`, with exactly `session`,
`scope`, and `expected_revision`. Host envelope version remains 1. The native
owner refreshes persisted state and applies the existing session, scope,
accepted-history and expected-head checks. The caller cannot select an actor or
grant. The observer is the selected engine's actual `seed.player`.

Successful data has exactly these fields:

```text
version: 2
domain_version: actual 1 or 2
scope: selected story/branch
revision: selected accepted head
rules: native rule profile
player: { observer: native player ID, self_state: native player actor }
inventory: native items owned by that player
turns: chronological whole accepted player-visible turns
window: { total, start, end }
```

Each turn has exactly `original_scope`, `turn`, `event_ids`, `intent`, and
`narration`. The intent preserves the original accepted tagged Actions,
Dialogue, or FreeText value, including action parameters, dialogue audience and
input kind. In this display DTO only, Actions `promise.deadline` and
`believe.claim_event` are canonical unsigned decimal strings: ASCII digits,
no sign/exponent/leading zeros, range 0..18446744073709551615, with claim IDs
positive. Core input and accepted receipt serialization remain numeric. This
explicit representation preserves native u64 values beyond Android's signed
integer range. It is never inferred from effects. Narration is the accepted recorded text;
reading it never runs inference. Event IDs are nonempty, ordered, unique
accepted sequences at or before the selected head. Original ancestor scope is
retained, never rewritten to the selected child. Author records, proposal/play
internals, private reasons, truth bindings, other characters' private state,
and unobserved receipts are not part of this projection.

Only whole receipts whose every event is eligible through the existing native
actor/lineage/head read boundary are included. An eligible event from a partly
hidden receipt cannot authorize disclosure of its full intent or narration.
Native filtering precedes selection of the display window, independent of Story
Lab grants. This does not promote narration or character statements to truth.

The window contains the latest twenty whole eligible turns, preserving the old
forty-message chat limit: `end == total`, `start == max(0, total - 20)`, and
`turns.length == end - start`. Total is bounded by the existing 4,096-record
history limit. Omission is explicit in the window. No per-string clipping,
adaptive byte-based omission, blank transcript fallback, operation fallback or
extra query is used to manufacture success. Existing Host 262,144-byte and JNI
65,536-byte reply limits remain; an oversized response honestly refuses. The
inspector's separately paged Query2 history remains available for history reads.

Android strictly checks exact field sets, integer and UTF-8 bounds, selected
scope/head, native observer, actor/item and intent shapes, ordered event IDs,
duplicate turn keys and window arithmetic before publishing. It renders Actions
as the original JSON action array, converting the two decimal-string fields to
standard `BigInteger` numbers in a deep copy for exact numeric display. It never
rounds through Double or mutates the native DTO. Dialogue/FreeText retain the exact
original text, followed by the exact narration. Stable message IDs use the absolute
visible-turn ordinal (`window.start + index`) and role. Kotlin validates the
wire shape; Rust remains the authority for action legality and ancestry.

The reserialized-object allocation bound is 262,144 bytes; individual text
limits remain separate. JNI still enforces the original raw 65,536-byte reply
limit before decoding. Reapplying that raw limit to `JSONObject.toString()` would
incorrectly refuse admitted text because Android escapes slash characters.
The actual native slash fixture measures 41,514 raw envelope bytes versus
77,479 bytes after the same data is slash-escaped. A public Engine accepts the
u64 maximum promise deadline, so narrowing it to signed Long is also incorrect.
These are representation fixes, not new engine authority or larger native caps.
See the official [API35 JSON string encoder](https://android.googlesource.com/platform/prebuilts/fullsdk/sources/+/dc3f885ebe8ddc75bd9cf2d567eef4d1ed433a09/android-35/org/json/JSONStringer.java),
[number reader](https://android.googlesource.com/platform/libcore/+/4ef949a4fc8d9a0fd3c24aeb622e88a4388f6c00/json/src/main/java/org/json/JSONTokener.java),
and [number writer](https://android.googlesource.com/platform/prebuilts/fullsdk/sources/+/refs/heads/androidx-constraintlayout-release/android-35/org/json/JSONObject.java).

The gateway retains its current attachment identity, head, binding, catalog and
close checks across suspensions. A partial read cannot establish a coherent
player snapshot. View-model cancellation/disposal/generation checks and exact
current-timeline object identity remain unchanged. Only the new Domain2 UI
fixture's observation/conservation reads adopt the new operation; legacy
Domain1 controls retain their original endpoint.

The refreshing operation remains blocked while local inference owns resources,
like `open`; the legacy cached-read allowlist is not widened. Cancellation must
drain before refreshing. The older process-proof protocol correctly records
the new operation as `other`: it is not relabeled as a legacy snapshot or hidden
as metadata. That profile needs a separately versioned proof before new-source
process qualification; this archive-profile packet does not claim it.

Implementation, executed checks and limitations are recorded separately in the
packet verification report and tickets. This contract alone is not emulator,
physical-phone, model, accessibility, lifecycle or release qualification.
