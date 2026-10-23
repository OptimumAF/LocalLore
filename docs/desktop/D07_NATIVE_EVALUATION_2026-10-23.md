# D07.06 partial: native built-in evaluation results

Status: implemented and locally verified, in review. Full D07.06 remains unchecked.
Claim: [issue #29, comment 6360113156](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6360113156).

## Scope and authority

The Story Lab can run the fixed built-in synthetic suite, run one built-in case,
stop at a scenario boundary, resume a checkpoint, rerun a selected built-in case
in a new directory, explicitly reopen a retained run, and inspect/copy its JSON.
Expected/actual checks and report-internal turn sources are readable tables.
The runner uses the actual Play/Host/Store/compiler with deterministic fake
providers. This is neither a model-quality measurement nor Android parity.

The desktop additions do not change the runner, fixtures, Host protocol, core,
storage, Android, or generated contracts. The implementation commits are
317dc60, 7fd006a, de7c4af and 78db0da. Final tested integration is
`4a0a859830bb163064d58dddf74352916feb25c4`, merging accepted main
`d5a76d2308a6863e49b3d088041d0eccadf8bb38` (durable forks and compiler
cancellation). The worktree was clean during the definitive native run.
This documentation is a subsequent documentation-only change.

No model was loaded or generated from; no desktop input, activation, desktop
screenshot, CUA, device, protected chat, or protected runtime process was used.
Captures come only from this application's hidden WebView CapturePreview.

## Native boundary

New separate Tauri commands are `evaluation_catalog`, `evaluation_start`,
`evaluation_open`, `evaluation_status`, `evaluation_read`, `evaluation_cancel`,
`evaluation_resume` and `evaluation_rerun`. They use existing main-window
permissions and the actual window epoch/lease. Renderer input is limited to
built-in case IDs, `one`/`all`, UUID run/token IDs and an exact safe-integer
operation ID for cancellation. No renderer paths, database, report bytes,
provider, seed, prompt, SQL, script, executable or HTML are accepted.

Native code chooses private `evaluation-runs-v1/<UUID>` directories beside the
app-owned workspace, writes fixed native selection metadata, and gives the
runner a new `work` directory. Root-to-leaf no-reparse directory handles are
retained with no-delete sharing and opened-handle metadata checked. A test
actually attempts ancestor replacement on Windows. This is a finite local
path policy, not a sandbox against a compromised OS or hostile same-user code.

One worker is allowed per application. Admission, thread registration and
retirement coordinate through a separate registration barrier. The new worker
cannot execute before its handle is registered. Joins run outside window,
state and worker locks. Spawn refusal rolls back its own job; caught worker
panic clears busy state. Publication rechecks the exact window epoch inside
the lease gate. Retirement cancels and drains without permitting late result
presentation; window reopen waits for cleanup.

There are at most four opaque handles per window, with a 15-minute idle TTL;
the active handle remains live. Reaping handles never deletes run files.
Native scans cap retained runs at 32 and scanned entries at 8192/depth 6.
Free-space admission requires 64 MiB. Run/library budgets are 32/256 MiB,
checked at scenario boundaries. These are admission/boundary policies, not
hard per-write quotas; a current scenario may overshoot before the next check.
The runner's report/case limits remain 2 MiB/64 KiB.

Private JSON, inert HTML and synthetic databases remain locally with no
scheduled expiry. Quotas block new work; there is no forever-retention,
secure-erasure or generic-delete promise. Outside copies and OS backups are
separate. The UI exposes this retention policy and actual storage location.
Synthetic capture metadata/visible paths are redacted by the fixed harness.

## Recovery and presentation

Cancel stops after the current scenario; it does not force interruption inside
a turn. Completed immutable checkpoint envelopes are retained. Explicit Open
or recovery calls the runner with its original selection, resume enabled and
a pre-cancelled token, validating the checkpoint without running another
case. This **rewrites derived JSON/HTML reports**, which the UI explicitly
discloses. Poll/status/read use bounded in-memory snapshots and do not recover
or rewrite files. Source/checkpoint or selection mismatch is refused; historical
resume across changed source is unsupported. A fresh run is required.

Story/lens/Play changes synchronously invalidate the evaluation controller
before React presentation. Held catalog/start/read/cancel and clipboard
notices are fenced by context and presentation epoch. Return to play clears
results and source selection. Browsing or running evaluations does not mutate
the selected player story. Generated HTML is never executed or displayed.
All report strings render as inert React text.

Source buttons select only report-internal turn/seed anchors. The report has
no app-session/scope/receipt binding: the **D05 inspector bridge is unavailable**.
The runner does not retain window Host traces: the **D06 trace bridge is
unavailable**. There is no current-story fallthrough or fabricated trace.
These missing bridges keep full D07.06 partial.

## Verification

All commands below ran in `apps/desktop`, except native commands whose manifest
path is relative to the repository. Dependencies were cached/offline. Build
outputs were task-owned on D:, with `CARGO_PROFILE_DEV_DEBUG=0`,
`CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`. The existing read-only
task dependency junction was reused; no dependency installation occurred.

| Check | Result on final tested integration |
| --- | --- |
| `npm run check` | PASS: TypeScript, schema/action checks, normal-hook absence, all existing controller checks and new evaluation controller/SSR check |
| `npm run format:check` | PASS |
| `cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-target>` | 28 passed, 0 failed, 1 existing privilege-dependent ignored test |
| Same with `--features dev-harness` | 30 passed, 0 failed, 1 ignored; 2 harness-contract tests passed |
| `cargo clippy` with same manifest/target, `--all-targets -- -D warnings`, default and dev-harness | PASS both |
| `cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check` | PASS |
| `node evaluation-harness.mjs` | 26 distinct native journey assertions, 14 captures, actual process restart |

The same integrated source also passed fresh native debugger (74 assertions,
12 captures), inspector (93/14), durability (33/11), inspection exports (36/14,
four publications) and reconstructed synthetic-v1 migration (29/8) journeys.
Each summary records `sourceDirty: false` at the tested integration and actual
restart. These five cohorts protect existing behavior; their counts are not a
claim of globally distinct assertions across suites. The legacy fixture is a
reconstructed synthetic v1 save, not a released-app historical save.

Node was 23.10.0; Cargo/rustc were 1.93.1. Native rendering was WebView2 on the
Windows host; its installed runtime version was not measured. Normal assets
were rebuilt and passed their hook-absence scan after all journeys, followed
by a successful offline default native build. Both restored hashes are in the
evidence JSON, separate from each harness binary hash.

Ten native evaluation-manager tests cover boundary cancel/resume, stale
operation/retired lease, exact checkpoint recovery and corruption, malformed
inputs/unsafe catalog, token reaping, run/budget caps, close between admission
and registration, retired publication, spawn failure/caught panic, and pinned
ancestor replacement. The deliberately caught panic prints Rust panic text;
the test succeeds and proves later admission works.

`check-evaluation-controller.mjs` is a deterministic controller/React SSR test
with an explicitly mocked failed result, delayed replies, escaped hostile text
and malformed quality fields. **It does not prove an actual runner failure.**
The actual native suite has 9 passed, 0 failed, 3 unsupported cases and 196
declared checks. Quality accepted remains false, model/runtime/hardware null,
and Android parity `not_run`. No network-blocked or performance claim is made.

The definitive native artifact is
`evaluation-native-18c80080-67b8-40ab-a33e-b13597d60c7e` under the task-owned
`d07-evaluation-artifacts` directory. Its `summary.json` binds source, native
binary, development assets, runner inputs and selected shared source hashes.
The adjacent committed evidence JSON records raw artifact/capture hashes.
Its summary SHA256 is
`54fce6cbb7585bb95b6b029a41446e846f62a9c0aa2e5f30b46ec818112ee69a`.
Native summary errors are empty. Chromium emitted a shutdown class-unregister
warning 1412 after successful child exit; the journeys passed.

Visually inspected final `initial` captures: `initial.png` (counts/privacy),
`receipt.png` (expected/actual), `copy.png` (original source/head/fingerprint),
`failed.png` (unsupported archive and explicit bridge refusal), `narrow.png`
(wrapping), `reopened.png` (paused checkpoint) and `finished.png` (normal Play,
no evaluation results). Columns and hashes wrap without horizontal overflow.
These are bounded checkpoints, not a claim that every possible report/layout
has been visually qualified. The `failed` filename is an existing capture
allowlist label; that case is visibly unsupported, not a failed scenario.

Earlier native runs at 317dc60 (19 assertions/7 captures) and de7c4af
(25/12) remain historical. They do not substitute for the repaired integrated
run. Earlier regression cohorts at de7c4af remain separately attributed.
One later durability build was interrupted before app launch after noticing
missing debug-profile environment settings; it is not counted as a test run.

Final integrated regression cohort results and normal-asset restoration hashes
are recorded in the evidence JSON. These checks protect existing native IPC
flows; they do not extend any model, platform or release acceptance gate.

## Handoff

No PR, merge, release or upstream setting change was performed by this agent.
The coordinator's separate real-model-render investigation belongs to its
own source/artifacts and is not qualified by these synthetic native results.
Coordinator review/acceptance is pending. The next bounded product task is a
shared runner contract for durable session/scope/receipt and trace bindings,
followed by real D05/D06 navigation. The current UI must retain unavailable
labels until that contract and corresponding end-to-end tests exist.
