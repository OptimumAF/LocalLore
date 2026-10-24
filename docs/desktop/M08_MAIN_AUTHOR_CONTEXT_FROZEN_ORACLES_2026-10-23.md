# Main author/shared-context frozen review oracles

Source-only freeze from Root `9e74028` on 2026-10-23, delegated
`desktop_memory_ui`; partial M08.03/.06, D05 and D08.05. Root owns production.
Only this new document and `apps/desktop/check-main-author-context-review.mjs`
are allocated here. No existing assertions, production files or dependencies change.

## Concrete source findings

F1: Main's root context synchronizer includes retained `inFlight`, unknown,
nonterminal and unconsumed work. Its author subscriber replaces that decision
with `author.busy || retained.unknown`. During Lab-to-Play notifications,
AuthorController invalidation synchronously notifies before installing its new
context. Known shared work can therefore finish with V2 `blocked=false`.

F2: The same author subscriber ignores `acknowledgedUnresolved`. An explicitly
acknowledged unknown operation can finish with V2 `blocked=true`, despite the
root synchronizer releasing its presentation barrier.

Root additionally identified gameplay host-call admission bypass: Domain1's
composer does not share V2's context block; Main forwards gameplay prepare,
submit, free_text and commit without consulting retained shared work or author
busy. Native canonical validation remains authoritative; these findings do not
establish canonical corruption or justify weakening Rust fences.

## Executable frozen shape

The runner reads the actual sibling Main, appends test exports in memory, and
bundles it with existing pinned esbuild. It does not copy the predicate or
assert source strings. Only App, ReactDOM rendering and JSX element construction
are substituted. All actual controllers, broker retention, IpcGateway and Main
subscriptions execute. Fresh unique module instances isolate cases. A bounded
synthetic native bridge handles startup, metadata, snapshots and Query2; all
inputs are synthetic. Author grant TRUE is the positive baseline, matching
the current native owner. Denied and malformed metadata are separate negatives.

The fixed tests cover: true/denied/malformed native context; known shared work
through Lab-to-Play; explicitly acknowledged unknown; acknowledged but in-flight
passive memory recovery; sticky malformed terminal; Domain1's four mutative
operations during known, unknown, recovery-in-flight and author-busy work;
acknowledged-unknown explicit next admission; readonly/status/cancel/context
switch positives; own author pending preservation and actual terminal preview
consumption only after the author controller consumes it. The preview uses
native-shaped serde DTOs, an exact SHA256 of synthetic preview JSON and the
actual request captured from Main, rather than a copied canonical validator.

The Domain1 checks call the actual Controller's public Gateway with closed,
valid Host envelopes, and count transport calls. A native Busy reply does not
satisfy a zero-dispatch guard. The acknowledged-positive case explicitly expects
synthetic native Busy after admission; it does not claim an accepted turn.
The running native author request is held to observe own-pending behavior; its
terminal response exercises the actual broker and controller decoders together.

Desired Root correction: one closed retained-work predicate, bounded coherent
application synchronization, and narrow gameplay dispatch admission using the
existing bounded IpcGateway Host envelope. Preserve readonly, status, cancel,
session selection, explicit acknowledgement and native canonical authority.
No general command endpoint, persistence or new native capability is needed.

## Reproduction and evidence limits

From `apps/desktop`, Root should run:

```powershell
node check-main-author-context-review.mjs
```

The runner prints bounded per-case results and the exact Main SHA256. Retain the
baseline RED before production changes and the unchanged-oracle GREEN afterward.
This freeze has NOT been compiled or executed by its author. Only Git/path/diff
and source/hash inspection is permitted in this allocation. esbuild executes
only when Root runs the checker. All startup fixtures and imports remain subject
to first actual execution; a fixture or harness error must be attributed and
corrected transparently without changing behavioral expectations.

This is synthetic Main/controller/subscription execution, not native IPC,
Rust/Core/Store execution, a browser/headless render, native WebView rendering,
model execution or owner acceptance. Window/document/localStorage are in-memory
stubs; no desktop or unrelated application is observed or controlled. No runtime
latency claim, restart persistence or author recovery acceptance follows.
