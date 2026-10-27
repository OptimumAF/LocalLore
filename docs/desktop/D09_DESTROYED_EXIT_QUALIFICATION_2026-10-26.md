# Observed window destruction before exit: bounded qualification

Scope: D09.03/.06/.07 supporting work under #31. Source-bound baseline and
corrected native lifecycle results and final regression gates are recorded below.
This is not full D09 acceptance. Root executed checks and reconciled this final
record; the independent document author read source only. The independent visual
reviewer inspected generated synthetic images without running an application.

## Finding and implementation boundary

Earlier app cohorts retained a115-byte Chromium/WebView message about failure to
unregister `Chrome_WidgetWin_0` with error1412. Microsoft defines1412 as
`ERROR_CLASS_HAS_WINDOWS`; its [UnregisterClass documentation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-unregisterclassa)
requires class windows to be destroyed first. See the
[Windows error definition](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--1300-1699-).
The warning is an observed diagnostic, not by itself proof of a persistent leak,
privacy/data-loss bug, benign shutdown or a particular underlying cause.

The old app exit continuation could issue coded exit once app-owned cleanup was
confirmed, without requiring a separate observed native window destruction.
Window-only destroy issuance could also allow a later window epoch before a
Destroyed acknowledgement. Exit0 and passing UI assertions did not establish
WebView/controller teardown ordering.

At corrected source `f1fe1e3c`, `CloseGate::destroyed(epoch)` is called from the
actual `WindowEvent::Destroyed` handler. It is separate from a request to destroy
and from trusted manager cleanup confirmation. The gate controls lease completion
only after both manager proof and the current epoch's destruction observation.
An early Destroyed event can start cleanup, but cannot substitute for it. Stale,
duplicate or invalid epochs do not authorize a later window or exit.

`shutdown.rs` retains the existing evaluation/archive/model/Host draining and
unknown-owner retention. Native destroy/exit effects run outside the coordinator
mutexes. Exit code intent remains native-owned; renderer data cannot acknowledge
cleanup or destruction. This change adds no canonical history, inference,
storage, model-owner or alternate cleanup authority.

## Frozen FSM evidence

The independent three current-API oracles were frozen before implementation.
At `5c2e6297`, Root compiled and executed them: **0 passed/3 behavioral failures**.
They demonstrated Exit before Destroy, duplicate premature Exit, and admitting a
new epoch after destroy issuance without an observed event. This is a behavior
RED, not a missing-method compile failure.

The additional six acknowledgement tests were frozen at `8c809cbf` against the
new trusted `destroyed` contract. They were first compiled with the implementation;
their absent API is not claimed as an executed behavioral RED. At `f1fe1e3c`,
all20 CloseGate tests passed with0 failures. These are owner-free Rust FSM tests
using synthetic trusted-manager/event calls. They do not exercise HWNDs,
WebView2/Chromium, OS process cleanup or universal teardown ordering.

## Instrumented native baseline

Root ran the fixed development launcher at `9a7b635e`. It uses the existing D02
controller journeys, actual native IPC and hidden/unfocused app-owned WebView
CapturePreview. Initial and reopened windows produced21 images in one app
process. Root inspected all21. The app elapsed6.403s and exited0.

The final native epoch3 trace recorded cleanup confirmation, Exit issuance and
Exit permission, with **no observed NativeDestroyed before exit**;
`destructionBeforeExit=false`. The baseline launcher intentionally expects this
ordering failure when `--baseline` is selected. A successful baseline launcher
does not turn the exposed lifecycle gap into corrected behavior.

The app stderr was211 bytes: a96-byte PostMessage invalid-HWND diagnostic plus
the115-byte class-unregistration1412 diagnostic. No canonical/inference/storage
or resource-owner change was made to create this baseline.

## Corrected native cases

Root reports these terminal app cases at immutable `f1fe1e3c`:

| Fixed case | App result | App elapsed | CapturePreview PNGs |
|---|---|---:|---:|
| `zero` | PASS; exit0 |6.148s|21|
| `seven` | PASS; expected exit7 |6.048s|21|
| `window` | PASS; exit0 |6.168s|21|

Every case records the final epoch3 order:

```text
cleanup_confirmed -> destroy_issued -> native_destroyed
                  -> lease_closed -> exit_issued -> exit_permitted
```

The early epoch1 path also records actual destruction before cleanup starts,
then cleanup confirmation, lease completion and creation of epoch3. This tests
the early-event route rather than assuming all Destroyed events follow cleanup.
The `seven` case preserves the requested code; its nonzero exit7 is expected by
the fixed launcher, not an application-test failure.

Each case has163 distinct UI assertion labels across its snapshots. The final
reopened report contains18 assertions; it is not a163-assertion final report.
Do not add repeated labels across the three cases into an independent-test count.
There are63 corrected app-owned PNGs in total. The independent visual reviewer
viewed every image (21 per case) and found no new visible defect within the
captured regions. All63 snapshots report no horizontal overflow. Baseline21-image
review is separate and complete. The local63-file visual-review manifest SHA256
is `e0816656f7b52c65d6fc8bdb98786ef778674dd5d1256f7b556391bc406a6343`.

All three corrected app processes still emit the same96-byte PostMessage
invalid-HWND diagnostic. The1412 diagnostic was not observed in these three runs.
That change alongside the observed event order is not proof of its root cause,
universal clean SDK exit, absence of transient windows or a no-leak property.
No stderr filter/suppression, registry/OS setting or dependency upgrade is used
to classify the cases as passed. This does not resolve all native diagnostics.

The reused D02 captures have known viewport limits: top-level images can leave
the composer/error area below the viewport, and a disposed blank view is expected
in its corresponding state. These captures are not a new whole-UI, accessibility,
performance or model-quality qualification.

## Reproduce the closed cases

Use the existing pinned dependencies/toolchain, a clean source checkout and
task-owned external directories. These templates were not run by the document
author. From `apps/desktop`, with existing Node and cached native dependencies:

```powershell
$env:CARGO_BUILD_JOBS='1'; $env:CARGO_INCREMENTAL='0'
$env:CARGO_PROFILE_DEV_DEBUG='0'; $env:CARGO_PROFILE_TEST_DEBUG='0'
$env:LIBSQLITE3_FLAGS=''
$env:TEMP='<existing-task-temp>'; $env:TMP=$env:TEMP
$env:LOCALLORE_D09_SHUTDOWN_ARTIFACT_ROOT='<absolute-existing-artifact-parent>'
$env:LOCALLORE_DESKTOP_TARGET_DIR='<absolute-existing-external-target>'
node shutdown-harness.mjs zero
node shutdown-harness.mjs seven
node shutdown-harness.mjs window
```

The launcher accepts only `zero`, `seven` or `window` and the optional closed
`--baseline` flag. It builds the harness frontend and native `dev-harness` binary
with locked/offline Cargo resolution and one job, then creates its own UUID
artifact child and runs only the fixed D02 lane. It disables inherited unrelated
harness selections and accepts no arbitrary executable, code, model or command.
It uses synthetic in-memory stories and no model/weights.

For the preserved **old baseline source `9a7b635e` only**, the reproduction is:

```powershell
node shutdown-harness.mjs zero --baseline
```

Do not use baseline expectations on corrected source, weaken the corrected
order assertion or relabel the old cohort. After a harness run, restore normal
frontend/native output without `dev-harness`; the final restoration record is
below. The build is not evidence that the normal app was launched.

## Final source-bound checks and retained failures

The first final all-feature native test command at `f1fe1e3c` failed to compile
with `E0433` before any tests ran. The standalone `tests/harness_contract.rs`
imports the actual `src/harness.rs` without the app's `shutdown_harness` module.
Root's `18c062cd` adds only three lines: a `cfg(not(test))` guard/comment around
the app-only finish hook. The standalone contract still compiles the actual
harness module; development applications retain the actual hook. This is not a
lifecycle-behavior correction and does not relabel the native cases as18c results.
At clean `18c062cd`, the second full native cohort passed189 tests/0 failures/
5 explicit ignored in561.28s, plus2 harness-contract tests in0.01s. Strict Clippy
then rejected the now-unused app-only `finish` function in the binary test build.
The next source adds the matching `cfg(not(test))` to its definition. This removes
the unused test helper rather than suppressing lint; actual development apps
retain the same hook. Lifecycle/normal-app behavior and test assertions are
unchanged. The follow-up checks below completed at clean
`dc6c3f3b8d616c2be7a18535a295a350f389fd17`; subsequent changes only documentation.
The full suite remains attributed to18c, actual native cases to f1, and final
focused/lint/build results to dc6. These complementary executions are not one
unfiltered full-suite run on the final documentation commit.

| Gate at dc6c3f3b | Actual result |
|---|---|
| All CloseGate tests |20 passed/0 failed; subset of the earlier full suite |
| Standalone harness contract |2 passed/0 failed in0.01s |
| Strict native all-feature/all-target Clippy |PASS,11.68s compiler time |
| Cargo formatting and whole frontend Prettier |PASS |
| Full `verify-frontend.mjs` |PASS: strict TypeScript, controllers/decoders and normal development-hook exclusion |
| Android Rust host |20 passed/0 failed/0 ignored in1.89s |
| Android dependency graph |PASS; no desktop local-runtime/evaluation/Tauri/Wry/llama dependency |
| Normal frontend/native build restoration |PASS; native compile23.60s, normal executable not launched |

All final commands used locked/offline dependencies, jobs1 and terminal clean,
unchanged source checks. Local evidence prefixes: `d09-destroyed-frozen-red1`,
`d09-destroyed-first-green1`, `d09-destroyed-final1`, `...final2`, `...final3`.
Four model tests and the Windows symlink-privilege test were explicitly ignored
in the full native suite. No Android JVM, JNI/ABI, emulator or device run occurred.

Exact native commands from repository root, using an external `$taskNativeTarget`:

```powershell
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir $taskNativeTarget -- --nocapture --test-threads=1
# Final focused rerun after the matching test-only guard:
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir $taskNativeTarget --bin locallore-desktop-spike close_gate:: -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir $taskNativeTarget --test harness_contract -- --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --all-targets --jobs 1 --target-dir $taskNativeTarget -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
cargo test --locked --offline --manifest-path crates/locallore-android/Cargo.toml --jobs 1 --target-dir $taskNativeTarget --lib -- --nocapture --test-threads=1
cargo tree --locked --offline --manifest-path crates/locallore-android/Cargo.toml --edges normal,build,dev --prefix none
```

From `apps/desktop`: `node node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}'`
and `node verify-frontend.mjs`. Restore with `node build.mjs` and a native
`cargo build --locked --offline --jobs 1 --manifest-path apps/desktop/src-tauri/Cargo.toml --target-dir $taskNativeTarget`
from repository root. These are source-controlled entrypoints; external local
orchestrators captured the terminal command/source records.

Environment: Windows NT10.0.26300 x64, PowerShell7.6.5, Rust/Cargo1.93.1,
Node24.22.1, React/react-dom19.3.1, TypeScript7.0.2, esbuild0.28.2,
Prettier3.9.10, Tauri2.12.5, Wry0.57.0 and Tao0.37.1. Lockfiles are authoritative;
no dependency/model download or upgrade occurred. Installed WebView patch version
was not separately measured by this packet.

### Local artifact identification

Native cohort suffixes under the local artifact root are baseline
`shutdown-zero-166d3a61-2d9d-4ea9-ac87-2cbcd29745d2`, corrected zero
`shutdown-zero-5ad40c6a-875f-445b-b5aa-1913200b4cb6`, seven
`shutdown-seven-5a77cc94-95b7-4b14-afc1-a8a1d02ad666`, window
`shutdown-window-e6940902-8692-4126-86c4-92be20d37b94`.

| Local qualification.json | SHA256 |
|---|---|
| Baseline |`7cee782ad03fc8c0bc5de26b5029fe02da6a5fb6496af3d236327cde9eee6198`|
| Corrected zero |`971b22ce0e67af7efdb9b3b3bc7252a86f67c6fe22c17e9122bfe53e78ef12f5`|
| Corrected seven |`534507ba596d1ee3c89b2c9a515eb7a8eab8c4d22cbc3adef5bf450fbf074238`|
| Corrected window |`b1c51550e353ab3d7f4ab64ffb682ed26f856e4c9a8a38512b268a44694b1fdc`|

The corrected stderr SHA256 is identical across cases:
`66c94918ecdee43a9ce5bfcaea6655fba60bb0343d86dbebb32ba202db89db77`.
Each native build has its own executable hash in its qualification record; no
byte reproducibility is inferred from an unchanged source revision.

Source-only follow-up located the exact PostMessage text in both Wry0.57's
WebView dispatcher and Tao0.37.1's event-loop dispatcher. `harness_reopen` destroys
its window before its IPC response returns, which is a plausible explanation,
not a measured cause. A future bounded control can compare otherwise equivalent
runs with and without intermediate reopen, retaining fixed native stage markers.
No current reverse lock order was found: future callbacks must not acquire the
CloseGate mutex while holding a WindowLease dispatch lock.

## Remaining limits

The record covers the fixed app-owned window lifecycle and existing cleanup
coordination. Actual active-model shutdown, arbitrary OS failures, whole-app
RAM/performance, physical-phone parity and universal Chromium/SDK cleanup remain
unqualified here. The residual diagnostic remains visible. Raw logs, generated
images and local workspace paths stay local/ignored; sanitized hashes and terminal
evidence are recorded above. D09's offline/privacy/package acceptance and
owner release authority are unchanged. No whole-milestone checkbox is awarded.
