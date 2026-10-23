# D02 current-main review — 2026-10-22

Independent, bounded source review at accepted main
`26120014affc3ba1bd3d82f4cf4beb9fa40ae10c`, which contains D01, D02 and the later
shared app durability integration. Review branch: `review/d02-current-gate`.
This packet does not reimplement the accepted shell, remove storage or infer a
new native journey result from historical evidence.

## Disposition

No new blocking production defect was demonstrated in the reviewed D02 scope.
The shell still submits typed requests through the real shared Rust Host and
Engine, derives its transcript from finalized receipts, and keeps Story Lab
inspection separate from player requests. Current production startup uses the
shared SQLite owner; the original D02 fixture journeys deliberately use a
development-only memory Host. Both remain fake inference, with no real-model or
free-text interpretation capability.

The concrete maintenance gap is current contract documentation that still
describes the original in-memory-only app. The coordinator owns corrections and
the current executable verification packet. Dated D01/D02 evidence remains a
record of its tested source, rather than fresh evidence for current main.

## Requirement trace

| Task | Current implementation inspected | Evidence boundary |
|---|---|---|
| D02.01 | Exact npm/native pins, embedded React/TypeScript assets, Rust-generated request types, normal build with only `host_call` registered. Normal startup opens an application-local workspace through `locallore-workspace`; no server/account/API key/model is required by this shell. | Coordinator must record fresh build and native/headless runs separately. Only the tested Windows target is claimed; installers and other platforms remain separate. |
| D02.02 | Saved-story/session sidebar, finalized chat, collapsible inspector, status for scope/revision/provider/turn/error, Play and explicit spoiler-bearing Story Lab. Supported Lantern Quay creation is distinguished from unavailable arbitrary generation/import/export. Fake inference and storage status remain visible. | Library/resume came from the accepted durability integration; no regression to a fictitious in-memory production app is appropriate. |
| D02.03 | `Controller` → `IpcGateway` → native `host_call` → shared Host/Engine. Typed give/wait/ability/dialogue actions, receipt/event views and presentation-only differences of authoritative player snapshots. Full request comparison precedes committed receipt publication. | A dialogue action is explicit character dialogue, not free-text intent interpretation. Current receipts are player-request receipts; future background/NPC turns need their own observer-policy review. |
| D02.04 | Original-key retry and lookup, repeated-submit promise reuse, operation/session/read/observer fences, per-session unsent drafts, native window leases, bounded workers and cleanup. Generation executes on a clone outside the Host lock/storage transaction. | Window lifetime is native-owned; stale renderer calls cannot grant a fresh lease. Terminal SQLite results win over late preparation. Current storage ownership regressions are accepted tests, not newly executed by this source audit. |
| D02.05 | Native labeled form controls, skip link/focus styling, pane width controls, text scaling, Enter/Shift+Enter/IME policy, receipt pagination, explicit selected-receipt copy. React text renders untrusted dialogue/narration; no raw HTML or URL-opening flow is used. | Programmatic shortcut/DOM checks do not claim injected keyboard traversal, screen-reader qualification or an actual OS clipboard write. |
| D02.06 | Compile-gated fixed journeys use the real controller and native IPC, compare complete receipts with the direct Engine, exercise native close/reopen, and render only the app WebView. Headless journeys use their own Chromium page plus real Rust stdio. | Native and headless evidence must stay distinct. Fresh assertion/capture counts and inspected renders belong in the coordinator's current gate record, not a claim derived from source inspection. |

## Authority and lifecycle checks

The shared Store remains the durable writer. TypeScript supplies typed intent
and renders immutable replies; it does not own a gameplay reducer, accepted-event
constructor, SQL connection, path selector or provider installation API. Play
reads a revision-bound player context and owned inventory. Rust native
construction grants Story Lab; selecting an observer cannot grant authority or
change the request used for generation. Returning to Play clears inspection.

`WindowLease` captures the native `main-N` epoch. Initialization and ordinary
commands pass through its gate. Destruction invalidates the epoch synchronously,
then closes sessions under that gate; a new window waits for completed cleanup.
Preparation bypasses the gate, checks the lease, and relies on Host session fences
for late completion. This preserves cancel/status responsiveness without allowing
a captured old Create/Resume to allocate after window cleanup.

Controller disposal clears subscribers/session-local drafts and closes its
sessions. Window/process teardown retains canonical saves. An explicit close
attempts to cancel locally active durable requests; `close_all` invalidates local
work and leaves interrupted persisted requests as drafts for explicit discovery.
Neither closing a window nor a lost response proves durable rollback. Resume
never automatically applies an orphan draft.

The development driver remains compile-gated and fixed-purpose. Normal frontend
verification checks journey/control marker absence; normal native registration
contains only `host_call`. Development native commands additionally require
activation, their own native app window and launcher-selected artifact paths.
No desktop input, capture of other windows, browser attachment, remote debugging,
general JavaScript/file/shell command or user-managed runtime server is needed.

## Documentation distinctions to preserve

- `HOST_V1.md` must distinguish the ephemeral fixture Host from the production
  persistent Host and document `workspace`/`resume`, durable `open`, local cache
  refresh and save-retaining close/reset behavior.
- Host bounds are 24,576 input bytes, 262,144 reply bytes, four sessions and four
  generation workers. `MAX_TURNS=64` governs new-turn admission in a live session;
  it is not the durable history cap. Storage retains at most 4,096 scoped turn IDs
  and 16 MiB of combined request/receipt history, with further receipt/projection
  bounds. Large inspection replies fail `TooLarge`; DOM pagination does not imply
  wire/history pagination or unlimited session length.
- A durable retry compares the complete persisted request. Fake mode is a
  session-local preparation choice, not a field persisted in the turn identity;
  changing it on an already cached request is rejected locally, while a reopened
  committed exact request still returns its recorded receipt.
- Current native labels/capabilities use `main-*` and validate exact native epochs;
  the old harness guide's literal fixed `main` label is historical.
- Android now depends on `locallore-workspace`, which enables `locallore/host`;
  old claims that Android never enables that feature are outdated. Tauri remains
  a separate desktop workspace and is not an Android dependency.
- `harness:native` and `harness:headless` exercise explicitly ephemeral D02
  fixtures. `harness:durable` separately exercises native save/reopen/restart and
  storage failure. The original fixture harness alone does not establish durable
  app resume, and the production app must retain its accepted storage wiring.

These are contract/evidence corrections, not new product features or a reason to
rebuild accepted work. Startup's first story is deterministic opaque-ID order,
not the most recently used story. Archives, branches, author changes, real
inference, production accessibility, network observation and packaging remain
their owning future gates.

## Independent execution in this review

Only the native lease's focused unit proof was newly run from this review's
clean worktree, using ignored output:

```powershell
New-Item -ItemType Directory -Force target/d02-review | Out-Null
rustc --edition 2021 --test apps/desktop/src-tauri/src/lease.rs -o target/d02-review/lease-tests.exe
& ./target/d02-review/lease-tests.exe
```

Result: exit 0, **2 tests passed**: captured Create cannot dispatch/write after
destruction; delayed initialization is fenced and reopening waits for cleanup.
This is a native lease test, not an actual-window run. The coordinator records
the fresh complete app journey/build results in its separate gate packet.

This reviewer wrote only this document. No Android/native app was launched, no
desktop/device/process automation was used, and no protected chat, shared runtime
checkout, model, emulator or build daemon was changed. Review does not grant
owner acceptance, merge, release or broader platform qualification.
