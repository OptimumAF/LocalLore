# D05 memory inspection native UI harness

Status: frozen SOURCE-ONLY contract, Root-approved before implementation.
Base `88873c51ea3470e4c3ed639031453348645673a5`. Supporting D05.05/.06/.07
and D06.04/.07; no full task or milestone acceptance. All new source and
journeys are UNCOMPILED/UNRUN at this handoff.

## Scope and ownership

This is an optional closed `memory-harness.mjs --inspect` journey. The existing
12-initial/2-restart memory journey remains unchanged. It uses the real Main
Controller, MemoryMaintenanceController, MemoryInspectionController, mounted
MemoryInspectionPanel, native command, Host, Repository and Store. It introduces
no alternate transport, packet builder, canonical writer, provider or query API.

The leaf owns only:

- New `apps/desktop/ui/memory-inspection-native-journeys.ts`.
- New `apps/desktop/src-tauri/src/memory_inspection_harness.rs`.
- Existing `apps/desktop/src-tauri/src/memory_harness.rs`, fixed routing only.
- This new contract, committed before implementation.

Root owns launcher, Main/config/App props, module declaration, native
`before_read` injection, verifier, builds, execution and image inspection.
The native injection is immediately before the actual Host read with its real
nonwaiting ReadPermit already held. No transaction or Host/Store lock is held
by the harness gate. Normal bundles and native handlers exclude this module.

## Fixed native interface

```rust
pub fn active() -> bool;
pub fn before_read(lease: &WindowLease, epoch: u64) -> Result<(), String>;
pub fn case(path: &Path, action: &str) -> Result<Value, String>;
```

`active` requires the dev-only module, D02 harness active, existing M07 memory
harness active, and `LOCALLORE_D05_MEMORY_INSPECTION_HARNESS=1`. Before any fixture
flag access, resolve the native environment workspace, require an absolute exact
`stories-v1.sqlite` path under `memory-native-<canonical lowercase UUID>`, reject
dot components, and retain the existing `archive::pin(parent)` ordinary-ancestor
handles for that access. `case` also requires its native path equals this exact
environment path. There is no path in the JavaScript action request.

Only `hold-read`, `release-read`, `read-state` are new action strings through
existing `harness_memory_case`. Existing hold/release/lose-ack actions are not
changed. All three return exactly:

```json
{"version":1,"kind":"memory_inspection_fixture","synthetic":true,"held":false,"entered":false}
```

The booleans report actual gate state; `held` includes an armed or entered read.
One armed read changes to entered only inside the actual native read path.
An RAII entered guard resets its own entered state. Release is explicit; lease
closure returns `Closed`; 10 seconds of held native waiting returns
`MemoryInspectionHarnessDeadline`. Inactive `before_read` returns immediately.
No arbitrary timing, action, query, execution, callback or provider input exists.
The production read slot remains the sole concurrency admission mechanism.

## Journey interface and controls

```ts
memoryInspectionNativeJourneys({
  controller, maintenance, inspection, brokerRetention, gateway, errors,
  invoke, dispose, config: {stage}
}): Promise<void>
```

The other arguments retain the existing `memoryNativeJourneys` types;
`inspection` is the actual MemoryInspectionController. Only `initial` and
`restart` stages are accepted. Fixed controls use actual controller methods and
native IPC. The gateway is the existing scripted/fake fixture path, not a new
provider and not genuine model inference.

Initial resumes existing `memory-controls-synthetic/main`, head 1 with the real
`memory-original-mira-receipt`. Before maintenance an explicit read must report
raw fallback/missing with no packets. Explicit maintenance consent, admit and
step build the real packet; inspector reads do not admit jobs or write caches.
The checked entries must retain the original Said text and exact SourceRef.
Source drill-down uses the actual returned Page2 at the packet through revision,
with a matching original scope/sequence. No substitute page is constructed.

Capture coherent Player, Mira and Sable states. Mira's ordinary inspection must
include the original witnessed statement; Sable's must exclude it. Non-Player
lenses disable and clear packet inspection. A held read followed by lens change
must never publish its late reply. A second held read followed by an actual
other-story session switch exposes real nonwaiting `Busy`, then release permits
a fresh explicit read; old source/entry data must remain cleared.

Compare actual player snapshot/receipts and actual ordinary Player/Mira/Sable
inspection results before and after inspection-only work. Maintenance is
separately explicit. After those checks, one ordinary typed Wait via `c.send()`
advances head to 2 through the existing fake fixture path. The head-1 packet must
remain a verified prefix with raw delta after 1, not be labeled complete current
history. Subsequent reads must not change the new actual canonical snapshot.
Same-head cache replacement/binding invalidation is not asserted by this slice;
its Core/Store tests remain distinct.

Restart reopens the same real database and saved head 2, observes the saved
packet/entries/source at through revision 1, and performs passive maintenance
status only. It must not admit, step, prune, generate, replay a new receipt or
claim author-operation recovery. No Domain 2 fixture or visual claim is added.

## Capture and evidence contract

Exactly 12 initial labels, each prefixed `memory-inspection-native-`:
`empty`, `packets`, `entries`, `source`, `mira`, `sable`, `held-lens`,
`other-busy`, `session-return`, `prefix`, `narrow`, `final`.
Exactly 4 restart labels: `reopened`, `restart-entries`, `restart-source`,
`restart-narrow`, with the same prefix. Root freezes/validates these labels in
the existing app-owned hidden/unfocused CapturePreview path and views all PNGs.
No desktop screenshot, activation, input automation or OS control is used.

Each snapshot has `semanticVersion:2`, selected story/scope/session, actual
observer and revision, separate gameplay/inspection/maintenance pending values,
displayed receipt, visible error, actual checked inspector DTO/state, bounded
semantic DOM, exact ErrorBuffer and native fixture state. Controller semantic
data remains labeled separately. Workspace paths are replaced with a synthetic
placeholder. DOM overflow, selected identity and visible error/status/source
labels are checked at wide/narrow viewport presets; semantics are not pixels.

Successful reports include all checks, stage, exact error records and
`realModelGeneration:false`. No broad error allowlist hides failed native work.
The deliberate Busy is checked at its exact controller operation. A deliberate
direct denial is recorded only if actually invoked; normal lens suppression is
not mislabeled a measured native Forbidden. Any unexpected Stale, Binding,
Transport or harness deadline fails. The read gate is released on failure before
disposal; failure reports remain failure, never converted to success.

## Qualification limits and Root checks

No execution occurs in this source allocation. Root separately compiles/types,
runs focused and full frontend/native checks, invokes the optional closed
launcher against fresh owned UUID output, verifies exact source/normal-build
exclusion/restoration, inspects every image and records both process stages.
Unknown native cleanup, truncated logs, missing snapshots or failed assertions
cannot pass. Source-defined waits are observation bounds, not latency claims.

Actual native IPC/Store/render/restart proof is pending. This packet does not
qualify models, narration quality, semantic summaries, Domain 2 maintenance,
Android, physical devices, offline networking or general accessibility. D2
Core/Store refusal and Main collision fixtures are separate evidence; a future
existing author journey may qualify its actual D2 visual state.
