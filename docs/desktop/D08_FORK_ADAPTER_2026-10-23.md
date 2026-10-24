# D08.04 fixed-identity desktop fork adapter

Status: partial implementation awaiting coordinator integration/native verification.
This section records the original47ab8d7 packet; subsequent real UI/native
integration and actual checks are in [the follow-up verification](D08_FORK_NATIVE_VERIFICATION_2026-10-23.md).
Refs #30 D08.04 and #12 M08.01–.02. The full milestones remain unchecked.

Coordinator delegated `/root/desktop_fork_adapter` from frozen
`5e44ea91bfa9e93ecf583e31a26937efdfa96366`. Claim comments:
[#30](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6374324675),
[#12](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6374324959).
Isolated branch `impl/d08-desktop-fork`, task-owned `source-desktop-fork` worktree.
Native `git worktree add` fallback used because app registration was unavailable.

Production/controller source froze at `3817f81`; additional unexecuted native
unit cases are in `af70904b0ea015b8f5b9082d06b626880dde0b51`.
Only the three new adapter/controller/check files and this new report are owned.
No existing main/UI/Host/Store/schema/Android file was edited.

## Behavior and boundary

`fork_start(session,input,consent)` accepts only the four-field immutable
`WorkspaceForkRequest`: parent scope, stable child branch, expected parent head,
completed fork revision. Consent is explicit. Native code constructs the accepted
PR109 typed Host request; Host and Store own live-session admission, pending-turn
refusal, canonical replay/boundaries, stale creation guards, cancellation and
immutable child retry. No author, observer, path, SQL or provider fields exist.

The adapter **reuses the existing `Arc<ArchiveBroker>`** worker, registration
barrier, operation counter, status/cancel and window retirement/drain. It opens
no Store. Archive and fork jobs therefore share one application worker admission
slot; archive activity may produce `ArchiveBusy`. Successful fork result is
`{kind:"fork",outcome: WorkspaceForkOutcome}` within existing operation status.
The worker's committed result wins a late cancellation. No child is selected,
session rewritten, downstream choice replayed, inspection grant changed or model
called by the adapter.

`fork_lookup(input)` is a separate read-only recovery endpoint. It calls the
existing bounded Host branches catalog, never `fork_branch`, and matches child
ID + original parent + fork point. It reports the current child head. Missing is
an honest catalog snapshot, mismatched identity fails, retired child fails Closed.
Parent advancement does not invalidate lookup. This is already-public branch
metadata: lookup does not require or mint a session/inspection capability.
Window lifetime and frontend selected-context fences still apply.

The frontend retains a frozen copy, calls an injected synchronous recovery-save
callback **before** any native dispatch, and keeps that exact request across an
uncertain acknowledgement. Save failure prevents dispatch. Exact retry requires
explicit confirmation in the original controller/context incarnation. Restoring
an identity or changing session/scope/head/view/observer makes it lookup-only;
lookup absence never recreates the child. Cancellation before a start response
latches until its operation ID arrives. Context switch/disposal cancels a known
operation and cancels late acknowledged pending work; stale completions never
change displayed result or selection. Commit can win cancellation, so neither
Cancelled nor a lost acknowledgement is represented as rollback proof.

Polling is bounded to 200 iterations at 25 ms between status requests. A still
running job becomes uncertain, retaining identity for explicit lookup/retry.
The UI owns no canonical data and does not infer a completed boundary from a
numeric revision: Rust validates it on confirmation.

## Exact minimal coordinator integration

1. In existing native `main.rs`, add `mod fork_commands;`. Register
   `fork_commands::fork_start` and `fork_commands::fork_lookup` in **both** normal
   and dev-harness invoke-handler lists. No new managed state is required.
   Keep the existing archive managed broker, status/cancel registration and
   synchronous retire + blocking drain before Host close unchanged. This shared
   broker already supplies fork teardown when registered.
2. Instantiate `ForkController(invoke, refreshSavedLibrary, saveRecovery)` once
   per window/controller lifetime. The refresh callback refreshes metadata only;
   it must not resume/select/create. The synchronous save callback must store
   the exact request in application-local recovery storage or fail closed before
   dispatch. This packet does not implement another persistence service.
3. Feed the same `timelineContext(controller)` into `contextChanged` whenever
   selection/revision/view/observer/lifetime changes. Call `dispose` on teardown.
   Restore saved identity with `restore`, which enables lookup only.
4. Show parent, selected head, fork boundary, stable child identity, pending
   operation, error and returned child head. Explain new timeline vs committed
   replacement, preserve original, require explicit confirm, offer cancel and
   lookup, and offer exact retry only when `lookupOnly` is false. Generate a fresh
   stable child ID only for an explicit new request, never as error recovery.
   Incomplete/uncertain identity replacement is refused by `prepare`.
5. Resume a confirmed child through existing `resumeTimeline`/main controller,
   only after explicit user selection. No resume helper is added here. Existing
   archive UI must not interpret the shared broker's fork status as archive data;
   its existing exact operation ID/result decoder remains authoritative.
6. Run the actual integrated module's `fork_adapter_tests`, native strict checks,
   full frontend type/schema checks, actual native IPC and application-owned
   render journeys. Include pending/cancel/retry, midturn boundary rejection,
   stale completion/session switching and observer isolation. This unregistered
   module packet alone cannot establish native command availability or rendering.

Suggested integrated Rust command (NOT executed by this subagent):

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked fork_adapter_tests -- --test-threads=1
```

Six module tests are written: closed/no-author inputs, ephemeral refusal, actual
SQLite lost-ack close/reopen/lookup + advanced parent/child exact retry, actual
Store stale/closed/pre-cancel no child, existing broker held-worker Busy + cancel
then real commit/late-cancel, existing broker window retirement/drain cancellation.
They use the production adapter functions/Host/Store/broker directly. They remain
**uncompiled and unexecuted** until real module integration. Synthetic databases
are bounded local test evidence retained under caller-owned TEMP, with no cleanup
of unrelated paths. No copied native owner or synthetic include-context was used.

## Executed evidence

Windows 11 Pro 10.0.26300, Node **24.22.1**, Rust/Cargo **1.93.1** installed.
Only formatting uses Rust here; no Rust compile/test was launched. Root retained
the compiler slot for other work. Existing pinned esbuild/Prettier were reused
through a local ignored node_modules junction; no dependency/pin/download change.

From `apps/desktop`, with the existing Node binary on PATH:

```powershell
$env:LOCALLORE_CHECK_OUTPUT_DIR='<task-owned-output>/desktop-fork-artifacts/frozen'
node check-fork-controller.mjs
node node_modules/prettier/bin/prettier.cjs --write ui/fork-controller.ts check-fork-controller.mjs
rustfmt --edition 2021 src-tauri/src/fork_commands.rs
git diff --check
```

Actual controller suite ran once before native-test additions and again at
`af70904`, both **56 assertions PASS, zero failures**, output explicitly says
**MOCK native IPC; no native/WebView execution**. It exercises the actual
TypeScript controller through esbuild, with a synthetic invoke transport:
accepted/consent refusal; seven error categories without automatic retry;
immutable complete-request exact retry/current child head; restored found/missing
lookup-only; four selected-context changes with late-start cancellation; pending
cancel before acknowledgement and committed result winning; operation-ID change;
six malformed/mismatched outcomes; six hostile request shapes; recovery-save
failure; in-memory refusal; disposal. No initial failing run is concealed: both
executed suites passed. Source-only audit corrected a mutable Store binding
before any Rust compilation; that is not an executed RED/GREEN result.

Frozen local summary:
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/desktop-fork-artifacts/frozen/fork-controller-summary.json`.
SHA256 `84941a58e4232483901006cb3424ff1bdfcd7971f2f0f9c4d358037d1eae1b92`.
It contains only synthetic test labels/counts. Generated bundles/summary stay
local, outside Git. Prettier/rustfmt/Git whitespace checks passed.

Unrun: full TypeScript checking, integrated Rust compilation/tests/Clippy, native
IPC, WebView rendering/images, real model, Android/device/round trips. No app,
worker, approved model, device, ADB, desktop control or protected-chat resources
were used. No PR/merge/release/settings change. Root owns independent review,
integration, actual native UI evidence and eventual task acceptance.
