# Live narration diagnostic native harness contract

2026-10-29. Refs #28 (D06.01/D06.03/D06.06/D06.07, supporting slice).
Root allocation after frozen frontend FIRST `62f2a642`, accepted contract
`dcc4b07b` and Controller/Main/App source review of `7b7ee1d0` + `293868fa`.
This is a source contract, not native execution or full task acceptance.

## Closed scope and ownership

Independent FIRST author owns only new `apps/desktop/live-narration-harness.mjs`
and `apps/desktop/ui/live-narration-native-journeys.ts`. Root later owns narrow
wiring in existing `ui/main.tsx`, `ui/journeys.ts`, `src-tauri/src/main.rs`,
`src-tauri/src/harness.rs` and verification/docs. No old oracle, scene fixture,
provider, Host, engine, storage, schema, permission or observer semantics change.

Use the existing `scene_harness` **literal** fixture, its original Store proof
and fixed `scene-native-fixture-v1` provider. One fresh task-owned synthetic
`scene-native-<uuid>/stories-v1.sqlite`, initial process then cold restart.
No model assets, new provider or parallel gameplay implementation. The existing
scene fixture seeds a Domain1 parent and corrected Domain2 child; this journey
generates only on the supported literal Domain1 parent. Domain2/nonliteral actor
coverage remains the separate public Host/frontend tests, unless constructible
through an existing supported public path without fixture changes.

Add one compile-time development-only boolean `liveNarrationDiagnostic`, set
only from launcher `LOCALLORE_D06_LIVE_NARRATION_HARNESS=1`, ahead of existing
scene journey dispatch while retaining its fixture bootstrap. No runtime script,
file, shell, URL, provider or query selector is accepted. `FaultGateway` may add
one `heldNarrationValidation` gate **after** its real base call plus a bounded
list of detached diagnostic command tuples for assertions. No response invention,
native-cancel injection, arbitrary callback or general debugging endpoint.

## Required real paths and distinctions

Use actual mounted button handlers/controller methods and existing `host_call`.
Initial metadata enable is explicit. Perform one accepted free-text scene turn
through the existing V2 controller and fixed provider; select its exact retained
attempt, enter acknowledged Lab/Omni and read the actual accepted validation.
Current head and original base must remain distinct. Capture receipt/state
separately from diagnostic metadata; neither a decision nor ready candidate is
proof of canonical commit or narrative quality.

Verify actual native reply delayed after IPC: pending UI, duplicate read no-op,
local cancel/no native gameplay cancel, explicit retry, and late reply after
observer/session retirement. No unbounded wait: use bounded settle predicates
and always release gates on failure. Reentrant teardown is additionally covered
by frozen actual-Main headless FIRST, not a private-state native simulation.

Show native unavailability without guessed cause by clearing metadata through
the existing Host command as an explicitly labeled external action while the
frontend still retains its previously checked selection, then explicitly reading
that tuple. Show native Stale refusal by a labeled external typed wait/commit
through the same Host, before refreshing the displayed head. These are actual
Host outcomes, not malformed/replaced replies. Player/character lenses clear and
refuse local diagnostic reads without IPC; a changed lens alone is not proof of
native grant denial. Rust grant-denial evidence remains separate.

Compare existing Store canonical/observer hashes and provider factory/poll
counters around read/cancel/retry/lens/clear operations. Explicitly account for
each intended canonical commit, including the external stale-head trigger.
Do not claim counter invariance across intentional generation. Restart must
preserve canonical data, show default-disabled/empty private trace and no
reconstruction, and perform no generation. Unsupported rejected-narration-native
coverage remains unqualified; the Host FIRST and real TurnDebugger SSR cover
recorded rejected tuples. Never replace that distinction with fake native data.

## Evidence, bounds and lifecycle

Reuse the existing hidden/unfocused application WebView2 CapturePreview, fixed
viewport command and checkpoint IPC. No desktop control, input injection, window
activation, desktop screenshots, new OS/SDK/network probes or emulator work.
New fixed checkpoint allowlist (each at most once per process):
`d06-live-ready`, `d06-live-recorded`, `d06-live-pending`,
`d06-live-local-cancel`, `d06-live-unavailable`, `d06-live-refused`,
`d06-live-observer`, `d06-live-switched`, `d06-live-enlarged`,
`d06-live-restarted`, `d06-live-failure`. At most eleven images total across
initial/restart. Every generated image is individually inspected by Root.

Each checkpoint includes coherent session/story/branch, observer, current head,
selected base/turn/attempt, pending operation, receipt, visible error, nested
diagnostic state, semantic DOM text/structure and geometry/visibility evidence.
Wait for the actual DOM commit before asserting or capturing. Keep bounded
sanitized frontend/native errors and owned-process logs; preserve failures.

Launcher requires physical D source/artifact/target/temp paths, clean committed
source and immutable source/product hashes. Reuse accepted runner closure rules:
bounded child output/time, await owned close, latch unknown drain before another
command, no process-tree containment claim. Restore normal frontend/build only
after known closure, including failure; do not launch normal app. Never execute
the offline qualifier. Explicitly select `--bin locallore-desktop-spike`.

Storage admission before execution: reuse the existing D Cargo cache and target;
allow at most 2 GiB target growth and 256 MiB new retained synthetic artifacts
for this run, besides the already declared 128 MiB source/frontend budget.
Check free D space and source/tool ownership before running; measure retained
bytes after closure and stop additional runs on a budget breach. No deletion or
fresh replacement roots to evade a failure. Frozen raw FIRST, failed packets,
original render images, hashes, logs and final reports stay local and retained.
Actual execution requires Root's later explicit run allocation; this contract
does not establish that these budget/closure/render checks have passed.

## Accepted construction amendment before FIRST freeze

Independent source inspection found the original external **typed** wait trigger
above is incompatible with the existing unchanged scene Store proof: every
postbaseline receipt must retain the exact free-text scene recipe/provenance.
A typed receipt fails `SceneRecord`, including cold-restart configuration. Do not
weaken or modify that proof. Instead, Root authorizes exactly one additional
**external free-text scripted scene turn**, using the same existing fixed literal
provider and exact fixture text/recipe, then normal Host prepare/commit. Use the
fixed valid synthetic turn ID `d06-live-external-wait`. The original UI turn
commits baseline r1 to r2; this explicit external trigger commits r2 to r3 while
the UI remains at r2 for its real Stale diagnostic read. Retain the original
selected attempt/base r1 and read head r2. Account for two provider factories and
four role polls after these intentional generations; nongeneration operations
must leave those counts unchanged. Restart performs zero factories/polls. This
amendment supersedes only the typed-trigger/no-extra-generation wording above;
all real outcome, unchanged proof, lifecycle, storage and evidence gates remain.

Root also authorizes the development-only `FaultGateway.gameplayCancelCalls`
numeric counter (maximum 64 increments, then fail the test), incremented only for
`command.op === "cancel"` immediately before the real base call. It observes
attempted dispatch, not successful completion, and adds no response/control hook.
A zero delta across local metadata cancel proves no attempted gameplay Cancel
through this exact gateway. Successful capture roster is nine initial labels and
one restart label; the eleventh label is failure contingency, not a success image.
