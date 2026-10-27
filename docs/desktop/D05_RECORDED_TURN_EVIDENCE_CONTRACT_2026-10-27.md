# Recorded narration to historical changes

Refs #26 D05.03/.06/.07. SOURCE-ONLY freeze on accepted `6f6608bf`, before
production implementation or execution. This packet owns only this document
and `apps/desktop/check-v2-recorded-turn-review.mjs`; the existing 60-case receipt
checker and contract remain unchanged. Root owns production wiring, all checks,
actual native cold-reopen journeys, rendering and integration.

## Shared source authority

`crates/locallore/src/inspection_query_v2.rs::history` obtains actual canonical
receipts, requires all their events to be visible to the selected actor lens,
then copies **every** actual receipt event ID into its `scoped_message` rows.
The narration row keeps the receipt's actual original scope and turn. The API
does not group a partial visible event page or fabricate a base revision.

The same shared Query2 `TurnDiff` implementation uses its completed-boundary
catalog to select the preceding historical state and derives a comparison under
the selected observer. It preserves child ancestry. This new frontend action
must consume that established contract, not infer a previous head, reconstruct a
raw Receipt or call unfiltered `turn_status` to obtain one.

The existing `traceReceipt` action remains available for a current in-process
receipt. A fresh controller after process restart has no such receipt. An actual
recorded narration row in a checked History page is a separate read-only route
to the same Rust historical comparison. This packet does not invent persistence
of the process-local receipt or change the Host/storage schema.

## Frozen controller API

Add to the existing `V2PlayController` only:

```ts
traceRecordedTurn(
    row: Extract<RowV2, {kind: "scoped_message"}>,
    from: V2BoundPage,
): Promise<V2BoundPage | null>;
```

Both arguments are actual objects selected from current controller state.
Require all of the following before any native dispatch:

- The controller is live, in explicit `view:"play"` with
  `observer:{kind:"player"}`. A Character lens using the same player ID is not
  the Player role; a Player or omniscient Lab lens is not Play.
- Current selected session/scope/head/player, structural context key and native
  thin Player snapshot are coherent. No snapshot, mismatched revision, player
  or scope means refusal.
- `from` is exactly the current `get().history` or `get().inspection` object,
  with checked `query.view` and `page.view` both `history`, Player observer,
  `player_visible` privacy, selected scope/current expected head and consistent
  query/page inspected revision. The page remains bounded by current head.
- `row` is the exact object in that actual bound page's rows, with
  `kind:"scoped_message"`, `message_kind:"narration"`, recorded-message origin
  and a same-story original scope. Original-input rows and cloned row/page
  objects are ineligible. A native-returned ancestor original branch remains
  eligible; do not relabel it as the selected child.
- The recorded event IDs are nonempty positive safe integers, strictly
  contiguous, bounded by the inspected page revision and current selected head.
  Use their actual final ID. The existing transport decoder checks ascending
  IDs but does not itself require contiguity, so this action must check it.
  These controller checks do not replace Rust's completed-boundary validation.

Revalidate the transport-shaped current objects as appropriate instead of
assuming that once-decoded mutable JavaScript fixtures cannot change. No caller
can supply a base revision, turn receipt, new scope, observer, query or privilege
to this method. Invalid or stale input returns null without dispatch.

Dispatch through the existing actual query method, using selected session/scope,
current `expected_head`, explicit Player observer, `view:"turn_diff"`,
`atRevision:row.event_ids.at(-1)`, empty search and normal size limits. Preserve
pending-notification, post-await, result-notification and final-busy-notification
context/channel-sequence fences. A subscriber can change selection, dispose or
start another read synchronously. No retired read may dispatch after retirement,
publish old evidence, or return a formerly current bound object as usable.

The successful return is the actual still-current checked
`get().inspection` bound. It is not a reconstructed diff. Current History is
not converted into a new canonical event or an inspection grant. No submit,
prepare, commit, generation, model load, session switch or `turn_status` is part
of this route. Inspector privileges never change character knowledge.

## Actual panel behavior

Add the exact action label **Inspect recorded turn changes** beside eligible
recorded narration rows in the real `V2PlayPanel`. Its callback captures the
actual rendered row/bound/context and passes the actual objects to the new
controller method. An old rendered callback must refuse after context or bound
retirement. Preserve current receipt inspection and all existing source links.

After await, update local view/revision/search controls only if context and the
returned inspection still match current state. Use the existing readable
derived before/after table. Original scope/turn/recorded IDs and selected
child/current head/inspected revision remain distinct labels. A former value's
source is prior provenance, not proof of which event removed it. Keep narrative
text inert; no HTML, remote image or script interpretation.

The action is absent or disabled on original-input rows and outside coherent
Player Play. UI disabling is not the authorization boundary: the method must
independently refuse direct calls with the same ineligible arguments.

## Frozen headless oracles and evidence limits

The new checker compiles the actual controller and actual panel. It follows the
existing accepted SSR review mechanism: real React server rendering plus capture
of actual JSX-created handler props; a narrow test import adapter supplies the
existing getter as the otherwise-missing `useSyncExternalStore` server snapshot
only for the client-only panel's React import. Other hooks/exports and actual
panel/controller decisions remain real. The adapter is a test prerequisite,
not a production patch or mounted subscription proof.

Synthetic Gateway responses contain a coherent snapshot and a real-DTO-shaped
History narration row. The actual existing refresh/decoder path must install
them. No turn is submitted; the fixture begins with `receipt:null`, representing
the controller condition after reopen, not evidence that an OS process actually
restarted. Query2/Host/Core privacy/receipt correctness remain separately owned
native assertions. The same fixture supplies a bounded synthetic diff response;
its rows are not proof that Rust generated a canonical comparison.

The 25 focused cases cover:

- Existing decoder/panel calibration, including inert hostile narration, and
  existing decoder acceptance of ascending gapped IDs before action-specific
  contiguity assertions.
- Current and historical inherited narration, multievent last ID/current head,
  actual current Inspection History bound, and absence of a raw receipt.
- Cloned row/page, replaced bound, original-input row, foreign story, explicit
  Player versus Character/Lab, missing/incoherent snapshot, malformed event IDs
  and mutated bound view/privacy/head/revision refusal before dispatch.
- Pending/result/final-busy notification retirement, a held actual controller
  read across head/session/lens/dispose, newer same-context query supersession,
  and disposed-context refusal.
- Actual panel button dispatch and no write/grant/receipt creation, actual old
  callback retirement, ineligible action rendering and a held panel action
  across session retirement.

Mutation cases intentionally alter already-decoded synthetic JavaScript objects
to test the controller's public boundary. They do not claim that native Rust
returned malformed transport values. The synthetic transport rejects unexpected
operations, and assertions forbid every operation except the existing snapshot
and inspection reads. A matching query is not native authorization evidence.

Cases classify missing new API/UI as `new-api-absent`/`new-ui-absent`; these are
not behavioral RED. Fixture/decode/SSR errors are `fixture-calibration-failure`.
Only actually executed assertions after calibration can establish behavioral
results. A bundle/compiler failure is a setup prerequisite failure, not a passed
or failed runtime case. This allocation executes neither bundle nor checker.

Root's reproducer, from `apps/desktop` using already locked dependencies:

```powershell
& $taskNode check-v2-recorded-turn-review.mjs
```

Create-only JSON/bundle artifacts default to gitignored `artifacts/checks` or
the existing `LOCALLORE_CHECK_OUTPUT_DIR`. Each report records actual source
hashes, synthetic transport, adapter scope, per-case classifications and explicit
limits. The existing receipt checker's source bytes and 60 assertions must stay
unchanged; Root can register this new checker separately after review.

## Native follow-up and handoff

Root must separately verify actual process restart/cold reopen with no retained
raw receipt, the real mounted narration action, native IPC/Player Query2,
historical comparison and original-source navigation. Use the same application
controllers and Rust service, synthetic workspace, bounded error records and
app-owned hidden/unfocused rendering. Inspect every generated render. Restore
normal build/test-hook exclusions and run appropriate frontend/native/shared/
Android-host compatibility checks after integration.

Headless SSR handler tests do not qualify mounted React post-await control
updates, real cold restart, Main subscriptions, actual native privacy, Store,
WebView, clipboard or accessibility. No model/device/desktop-control execution,
new authority/storage/inference implementation, quality claim or full D05
acceptance follows from this source packet. Author activity is source/Git/issue
reads, these two new paths, diff checks and the first frozen commit only. All
new checks remain **UNCOMPILED/UNRUN** until Root executes them.
