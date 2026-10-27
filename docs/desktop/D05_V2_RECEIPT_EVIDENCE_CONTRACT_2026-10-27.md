# V2 receipt to historical field evidence

Refs #26 D05.03/.06/.07 and supporting #28 D06.03/.07. Frozen SOURCE ONLY on
accepted `23e41879`, before production implementation. No checker, formatter,
compiler, native application or model ran in this allocation. The only owned
files are this contract and `apps/desktop/check-v2-receipt-evidence-review.mjs`.
Root owns all production wiring, execution and review. Full tasks stay open.

## Minimal existing-controller API

Add to the existing `V2PlayController`, without a new controller or Host command:

```ts
traceReceipt(candidate: V2Receipt): Promise<V2BoundPage | null>;
```

Only the exact current `get().receipt` object is eligible, with a coherent native
thin snapshot and current session/scope/head/player, explicit `view:'play'` and
`observer:{kind:'player'}`. Character (even with the same player ID) and every Lab
lens are ineligible. No Lab transition, inspection privilege or knowledge grant
is introduced. The receipt's actor/request scope is provenance of an accepted
gameplay operation; it is not an authority to select another inspection observer.
Query2 remains Player-filtered by the current selected session and Rust.

Reuse the existing transport receipt validation. Events must be nonempty, safe
integer, contiguous from the safe nonnegative request base, and bound to the
receipt's scope and turn. The positive final revision cannot exceed the coherent
current head. No arbitrary caller revision, turn ID, query, record or JSON is
added to this API. Malformed or ineligible input returns null without dispatch.
The Rust completed-boundary catalog independently owns historical validity.

The method invokes the existing query path with `view:'turn_diff'`,
`atRevision:receiptEnd`, empty search and current `expected_head`. It returns only
the actual still-current checked bound page, never a reconstructed change list.
A retained prior receipt remains inspectable after a later current-head advance;
the historical completed end and today's expected head are distinct labels.

## Reentrancy and source membership

The existing query method currently announces pending state synchronously before
its native call. Add current-key/channel-sequence checks after that notification,
before dispatch, after await and after result notification before returning the
bound page. A subscriber may change head/session/lens, dispose or start a newer
read at either notification. Retired reads must not dispatch or return a usable
bound page. Existing newer-query and stale-publication fences stay intact.

Every new source button passes the actual current `V2BoundPage`. The existing
`source(source, from)` must reject a stale bound page or a source not present in
that page's checked rows, including recursive before/after sources of `change`
rows. Compare the complete seed/scoped-event identity, not sequence alone. A
withheld source performs no query. No new source membership or authority is
inferred from receipt text. This packet's source membership tests use the bound
form; existing unbound direct-source compatibility is not redefined here.

Follow scoped sources through the existing actual Query2 History path in the
selected child and observer. A successful match needs exact original scope AND
sequence in an actual returned event. A different same-sequence branch, missing
source or unavailable result is not a match. Prior seed navigation still means
seed-era profiles, without asserting a specific cause or an exact seed row match.

## Actual panel behavior

Add one button beside the existing actual Player receipt:
`Inspect accepted turn changes`. Its callback captures rendered context and
receipt identity. Check both against current controller state before invoking
`traceReceipt`; check context/receipt/current returned bound again before
updating local view/revision controls after await. The same receipt object can
legitimately survive head advance: an old rendered callback must refuse, while
a newly rendered button can inspect that retained historical receipt.

No Main view transition or retained private Lab receipt is required. The panel
must not grant, generate, resume another session or write a canonical event.
Keep the existing generic manual query controls and D1 inspector behavior.

The actual shared row variant is `kind:'change'`, not `field_change`:

```ts
type Change = Extract<RowV2, {kind:'change'}>;
// key; before_revision; after_revision; before:RowV2|null;
// after:RowV2|null; origin:'derived_comparison'
```

Replace JSON-only change presentation with a readable semantic before/after
table, including exact historical revisions, typed values and explicit absence.
Raw JSON may remain in a collapsed detail. Place each side's actual source links
beside that side. For removed fields, label the former value's source as prior
field evidence/provenance; do not claim it caused the removal. A before/after
comparison does not identify a unique causal event. Render all text inertly,
including long and Unicode strings. Source navigation continues to show selected
scope/head separately from original event scope/sequence and inspected revision.

## Frozen source checks and limits

The checker compiles the ACTUAL controller and panel. Real React server rendering
captures the panel's actual JSX-created callback props using the existing archive
review pattern; production source decisions are not replaced by a test component.
Fixture setup calls the real controller send/status/receipt parser against a
synthetic Gateway, then tests reads only. The synthetic DTOs do not establish
accepted Rust outcomes, Store durability, actual native IPC or permission proof.

Cases cover current and retained historical receipts; old rendered callbacks;
scope/session/lens/snapshot coherence; empty/fractional/unsafe/future/gapped event
boundaries; pending/result reentrancy; late replies; removed/inherited/seed/
withheld/wrong-scope sources; nested after-source membership; actual panel handler
dispatch; readable table revisions/absence/prior-source labels and inert text.
Checks also assert that evidence navigation performs no write/generation/grant.
The additional hostile-text row is explicitly a presentation-only DTO fixture,
not an invented canonical field change.

The baseline has no new trace API/button. Their absence is reported separately
as `new-api-absent` / `new-ui-absent`, never behavioral RED. Setup or DTO decode
failures are separately classified `fixture-calibration-failure`. Existing query/source
oracles can establish behavioral failures only when Root actually executes them
after their valid DTO calibration succeeds. Compilation failure is not a
behavioral result. No tests have run at this source freeze.

Root's unexecuted reproducer, from `apps/desktop` with the existing pinned Node
and locked dependencies:

```powershell
& $taskNode check-v2-receipt-evidence-review.mjs
```

Create-only JSON and bundle outputs default to gitignored `artifacts/checks` or
the existing `LOCALLORE_CHECK_OUTPUT_DIR`. Reports keep actual source hashes,
per-case classification and explicit evidence limits. They prove neither native
rendering nor mounted React local-state rerender after await. Root separately
owns full TypeScript/frontend checks and the fixed actual author/Domain2 native
journey, including all generated-image review, current Player Query2 behavior,
canonical/read invariance and normal-build restoration. No new model, Android,
screen-reader, full D05/D06, privacy-universality or release claim follows.
