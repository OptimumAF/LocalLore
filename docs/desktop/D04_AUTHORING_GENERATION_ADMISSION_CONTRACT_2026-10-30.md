# D04 native generation admission: frozen code-only contract

Refs #25 D04.02, supporting D04.04 and #21's supported original-premise creation
workflow. Base `a13172652842fafefcac8a46355b0c9730afd1cb`, after accepted PR290.
This is a narrow prerequisite, not a new provider or original-story UI.

## Observed source gap

The shared Host already exposes the `authoring_*` lifecycle. It handles
`AuthoringGenerate` outside its state lock, and `close_all()` cancels the current
authoring job. Desktop `host_call` currently recognizes only `Prepare` as long
generation. Every other command runs under `WindowLease::dispatch`'s gate.
An authoring generation would therefore hold the gate while doing inference;
status/cancel and `finish_close` could wait behind it. This is a source-derived
risk; no native/model failure has been measured for this path.

Separately, shared initial-world requests use role `author` and1024 output tokens,
while the current runtime adapter accepts director/narrator and at most350. That
requires its own shared #9 contract. This packet leaves adapter roles, tokens,
metrics, profiles, descriptors, runtime, model and UI capabilities unchanged.
Desktop creation still honestly reports arbitrary original creation unavailable.
Concurrent B34/PR297 reader/descriptor ownership is preserved.

## Closed private interface

Add private `apps/desktop/src-tauri/src/generation_admission.rs`:

```rust
pub(crate) fn requires_generation_permit(input: &str) -> bool;
pub(crate) fn dispatch<T>(
    lease: &crate::lease::WindowLease,
    epoch: u64,
    generation: bool,
    action: impl FnOnce() -> Result<T, String>,
) -> Result<T, String>;
```

Classification uses the actual shared host-v1 `Envelope`/`HostCommand`, not
substring matching or a second schema. Malformed/unknown wire is non-generation
and remains the Host's validation responsibility. The existing native MAX_INPUT
check stays before classification. Host version validation remains authoritative
in Host; preserve current Prepare classification for typed envelopes rather than
silently introducing a new native version policy.

Only `Prepare` and `AuthoringGenerate` require the existing one-slot generation
permit. All capabilities/begin/review/create/status/cancel, inspection, ordinary
gameplay/storage operations and other commands retain their existing control
route. No extra permit, worker, transaction, endpoint or renderer authority.
One computed classification value must select both permit acquisition and dispatch.

Generation dispatch checks the captured lease epoch before calling the action,
without holding the lease gate over long work. Control dispatch continues through
the actual `WindowLease::dispatch`; canonical creation/commit keeps that fence.
The existing blocking-worker placement and Busy/Closed/Transport behavior stay.
There is no alteration to `lease.rs`, Host cancellation, Store or canonical rules.

## Independent FIRST and baseline sequence

Independent reviewer owns only NEW `generation_admission_review.rs` on a separate
branch. Freeze tests before a different author changes production behavior.
Producer first extracts EXACT existing Prepare-only classification/dispatch into
the seam and wires the real native caller. Root integrates the frozen tests and
runs that behavior-preserving baseline. A compilation/setup failure is not a
behavioral RED. Only after actual cases execute may the producer add the single
`AuthoringGenerate` classification alternative.

Tests must exercise the actual private seam and real `WindowLease`, with fixed
controlled-work closures and bounded, joined threads. This is admission/lifetime
coverage, not a second inference implementation or a native app/provider test.
The matrix must cover:

- Prepare and authoring generation classification; all relevant controls,
  especially authoring create/cancel/status/review, stay non-generation.
- Typed parsing versus malformed, unknown, duplicate/extra wire fields and
  operation-looking text; no text-based privilege selection.
- A waiting authoring generation does not serialize cancel/status behind the
  lease gate. Preserve the existing Prepare behavior.
- Teardown can finish while long work is waiting; the existing shared Host
  cancellation contract remains unchanged. No exact timing/performance claim.
- Already invalid epochs never execute either action; a queued control action
  cannot write after invalidation, and control mutations remain serialized.
- Actual Main wiring uses one classifier value for the permit and dispatch;
  source-path checks, if used, are labeled source controls.

Every waiting worker must have a bounded cleanup/release path and be joined even
when an assertion fails. Do not detach threads or weaken a timeout to turn a
failed probe into a pass. No app, WebView, model, SDK, device, OS input or network
qualifier runs. Existing four native grants are spent.

## Ownership, storage and reviewable gate

Root owns this contract/integration and bounded execution in existing physical-D
`source-resource-metrics-review`, branch `impl/d04-generation-admission-v1`.
Independent FIRST and production author use their existing isolated source trees
and new branches; preserve all earlier branches and artifacts. No B34 selected,
comparison reader, runtime adapter, schema/lock or Android paths are owned here.

Before tests/builds, Root must measure and state expected incremental target and
record/fixture budgets. Reuse the pinned offline cache and existing target with
TEMP/TMP on D:, one job, incremental0 and dev/test debug0. Never reset the original
baseline, delete output or create another target to evade its limit. Old Native4
products/current normal build and all failed evidence remain preserved.

The gate is a focused source/test PR with a valid old-behavior baseline, green
original regressions, relevant lease/type/native compilation/format checks,
independent source/evidence review and honest remaining limitations. Do not
claim actual author-role inference, original-world creation UI, model quality,
native execution, device/security qualification or full D04 completion. Any later
native/model qualification needs a separate concrete admission and authorization.
