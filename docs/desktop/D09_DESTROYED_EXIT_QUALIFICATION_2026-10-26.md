# Observed window destruction before exit: bounded qualification

Scope: D09.03/.06/.07 supporting work under #31. Source-bound baseline and
corrected native lifecycle results are recorded below; final regression gates
remain pending. Corrected-image QA is complete. This is not full D09 acceptance.
Root supplied all execution facts. The document author read tracked source only,
ran no checks/application/model and read no generated artifacts or images.

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
frontend/native output without `dev-harness`; Root's final restoration record
is pending below. The build is not evidence that the normal app was launched.

## Pending coordinator evidence and limits

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
unchanged. Follow-up focused tests, strict lint and remaining gates are pending.

- Final source-bound strict Clippy, focused tests and formatting: **PENDING**.
- Full frontend checks and normal frontend/native build restoration:
  **PENDING**.
- Android Rust host tests/dependency graph and final artifact/source/log hashes:
  **PENDING**. No Android device, ABI/JVM or emulator check is implied.

The record covers the fixed app-owned window lifecycle and existing cleanup
coordination. Actual active-model shutdown, arbitrary OS failures, whole-app
RAM/performance, physical-phone parity and universal Chromium/SDK cleanup remain
unqualified here. The residual diagnostic remains visible. Raw logs, generated
images and local workspace paths stay local/ignored; Root will append sanitized
hashes and final terminal evidence. D09's offline/privacy/package acceptance and
owner release authority are unchanged. No whole-milestone checkbox is awarded.
