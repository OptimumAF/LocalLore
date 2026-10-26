# Selected2 desktop consumer: app cohort evidence

Scope: D07.03/.04/.06 supporting work under #29. **Corrected literal and legacy
app cohorts completed at `6a195f85`; final regression gates remain pending.**
All execution results below are coordinator-provided Root evidence. The document
author inspected tracked source only and ran no test, build, application or model,
and read no generated artifacts, private prompts or images.

The implemented desktop service and frontend use the existing selected workflow
for source protocol2/selected1 and source protocol3/selected2. This is not a new
full-comparison desktop producer or a D07 acceptance/quality record.

## Prior shared evidence is separate

- PR202's [scripted selected2 qualification](D07_LITERAL_SELECTED_SCRIPTED_QUALIFICATION_2026-10-26.md)
  covers the shared isolated Rust producer over actual protocol3 histories.
- PR204's [native selected2 qualification](D07_LITERAL_SELECTED_NATIVE_QUALIFICATION_2026-10-26.md)
  covers shared owned runtime cleanup, actual fixed-child tests and one approved
  model two-arm Move, including completed and committed-checkpoint-loss recovery.
- PR205's [selected2 read capability qualification](D07_SELECTED2_DESKTOP_READ_QUALIFICATION_2026-10-26.md)
  covers bounded metadata, actual Store/Query2 and retained native history.
- [Full-comparison model evidence](D07_LITERAL_NATIVE_MODEL_QUALIFICATION_2026-10-25.md)
  belongs to the separate native full-comparison Rust producer. It is not an
  execution result for this desktop selected2 UI.

The new service/controller tests, headless markup and app-owned WebView cohort
below do not inherit those model measurements or turn them into UI model proof.

## Interface and ownership

`evaluation_selected` retains the existing closed command parser. Renderer JSON
contains bounded client/run/plan/read tokens, source identity, arm and existing
inspection requests. It cannot supply a source/destination path, model path,
provider, full Request, canonical Engine, execution consent or cleanup proof.
Native code captures the current window lease and Story Lab permission.

`evaluation/selected/versioned.rs` dispatches through a closed native enum:
source protocol2 selects the existing selected1 Core plan/read capability;
source protocol3 selects the actual selected2 Core plan/read capability. Metadata
tags must agree with Core-derived prepared metadata, native index and opened
summary. A version tag alone is not an authority or a conversion between plans.
`fb0ef042` boxes both enum payloads to satisfy strict lint; these private payloads
are not serialized and the boxing does not change their wire representation.

Preparation consumes the exact native-owned source capability only inside the
existing admission gate. Fresh shared Core validation binds both actual source
prefixes and full original requests. Native execution consent follows that
validation. Execution consent and private inspection consent remain distinct;
completion supplies a durable run ID, not an automatically promoted read grant.
Opening results explicitly obtains the independent native read capability.

The existing evaluation Job, registered worker and ModelManager remain the only
owners. Unknown cleanup retains the actual reservation/runtime pair, or its exact
same-manager witness/slot, until positive cleanup. No second owner list, runtime,
cache, canonical Store or persistence layer is introduced by the adapter.
Retirement revokes publication/read permission without discarding uncertain
ownership. Inspection lenses do not change the generation actor or rekey/cancel
captured work merely because the observer changes.

Selected2 writes an isolated manifest, two actual Stores, checkpoints and resource
ledgers. It neither imports experiment state into live gameplay nor rewrites its
source. Native prepared/read tokens are in-memory capabilities; durable completed
results can be explicitly reopened. Completed shared resume is read-only;
missing committed workflow evidence stays unknown rather than becoming invented
capture or role-call proof. Full failed/cancelled attempts are not silently retried.

The controller's private attempted-source-token mark is set after local admission
guards but before the pending-state notification and native dispatch. It requires
a fresh reader token even if reentrant context retirement prevents dispatch, or
the acknowledgement is unknown. This conservative presentation fence is not
evidence that native consumption happened.
Rust still checks actual capability, source, index and plan bindings. No automatic
picker, inference retry or regeneration is implied.

## Source-bound executed checks

These counts are test/check entries, not independent quality judgements. All
results in this section were executed by Root, not the document author.

| Evidence | Exact source/result reported by Root |
|---|---|
| Frozen native service baseline | `4b8c5e1c`: compile23.52s; 0 passed/5 failed in32.94s, all `NativeUnavailable` |
| Typed Core adapter correction | `3966f8ff`: the same5 service tests passed in142.47s |
| Frozen frontend baseline | `7295b595`: 85 passed/16 failed,101 synthetic checks |
| Intermediate frontend | `cdd82c78`: 99 passed/2 failed |
| Controller/oracle-order correction | `eab809b2`:101 passed; diagnostics assertions/render moved before the subsequent receipt read, because `beginRead` intentionally clears diagnostics |
| Full frontend | `0d6c4921`:PASS,12.99s command wall |
| Full frontend after capture/CSS changes | `fda87fc7`:PASS,13.28s command wall |
| Frozen source-token freshness review | `7c24399c`, adopted `fbab4821`:4 passed/6 failed across10 checks |
| Source-token fence correction | `592e865b`:10 passed;4 React SSR HTML outputs, not four app renders |
| Native strict lint after UI changes | `fda87fc7`:FAIL, two large-enum-variant findings |
| Boxed private native variants | `fb0ef042`:all-feature/all-target native strict lint PASS;9.94s compiler time,10.21s command wall |

Service tests use the actual native manager/service and shared Core/Store APIs
with synthetic inference fixtures; they are not app IPC, OS-dialog or model runs.
The101 frontend checks use synthetic DTOs/mock gateways, the actual controller
and React SSR. The corrected oracle asserted/rendered diagnostics before reading
a receipt: `beginRead` intentionally clears diagnostics. That ordering correction
was not a product permission failure. Existing assertions and failure chronology
must remain attributable to their original sources.

## First actual app cohort, retained with defects

Root reports a completed app-owned cohort at clean `0d6c4921`:

| Stage | Recorded checks | CapturePreview PNGs | App elapsed |
|---|---:|---:|---:|
| Initial process |205|24|574.54s|
| Restart process |213|25|471.79s|

This is418 recorded check entries and49 app-owned images, not418 distinct tests.
Root reports total cohort elapsed1071.12s and native compilation23.72s; do not
derive a model or whole-application benchmark from these harness durations.
The runs use actual normal controllers, native IPC and hidden/unfocused WebView2
CapturePreview with only scripted fake inference and fixed consent/picker doubles.
No desktop input, screen capture, browser automation/debug server or model is used.

Both stages preserve all626 source fixture files byte-for-byte. Each deliberately
loses one acknowledgement, classified as Transport; Root reports zero unexpected
transport errors. That is not a claim of zero deliberate errors or zero stderr.
Each process also emitted one115-byte Chromium/WebView shutdown message:
`Failed to unregister class Chrome_WidgetWin_0. Error = 1412`.
This SDK diagnostic is separate from the bounded frontend/native-IPC error buffer.
Exit0 and passing journeys do not establish clean SDK teardown or absence of
transient windows/processes. D09 #31 retains the unresolved investigation.
Root visually inspected all49 images and confirmed the626-file source hashes.
The actual reduced UA is Chrome/Edg155.0.0.0; the exact installed runtime patch
was not separately measured. Captures cover1280x900 and620x900 at
DPR1; these are bounded app areas, not a universal layout/accessibility review.

The first cohort is retained with three findings: the Checkpoint header breaks,
the right/lower literal proof is outside the inspected viewport, and Resume can
be offered with a consumed source token. Passing journey assertions did not erase
these findings or qualify the later corrections.

`592e865b` adds the conservative attempted-token/fresh-source presentation fence.
`fda87fc7` adds focused literal/Relevant proof captures, an explicit fresh-source
completed UI resume journey and the header CSS correction. The completed corrected
cohort at `6a195f85` is recorded below. The first cohort is not that rerun.

The first corrected attempt at `fb0ef042` did execute completed fresh-source
resume and both focused proof captures, but failed later: the selected harness's
internal600s watchdog fired, the window lease closed, and the denial journey
reported `Closed` after222 checks/24 images. The app exited2 after625.215s,
including shutdown; the launcher exited1 and never started its restart stage.
Its bounded stderr contains the watchdog message and the same class-unregister
diagnostic. This is a retained failed cohort, not a corrected UI pass.

The launcher had already been extended to900s while the app watchdog remained
600s. The next source uses the existing fixed900s app bound (also used by D04)
and960s launcher bound to permit bounded shutdown. This applies only to the
multi-journey development harness. Product turn, consent, cancellation, resource
ownership and cleanup deadlines are unchanged; these times are not latency
acceptance criteria. The completed corrected rerun below retains this failed
attempt as its own earlier evidence.

## Corrected literal and legacy app cohorts

Root reports both completed cohorts at immutable source `6a195f85`. They use the
actual controllers, native IPC and hidden/unfocused app-owned WebView2 captures,
with scripted fake inference and fixed picker/consent doubles throughout.

| Literal protocol3/selected2 stage | Recorded checks | CapturePreview PNGs | App elapsed |
|---|---:|---:|---:|
| Initial process |252|27|733.468s|
| Restart process |261|28|684.905s|

The corrected literal cohort has513 recorded check entries and55 images, not513
distinct tests. It covers the added focused proof captures and explicit completed
UI resume after a fresh source selection. Root inspected all55 images and found
no further visible defects within the captured areas. The626 source fixture
files remain identical to this cohort's baseline after each stage. Each stage
records exactly one deliberately lost acknowledgement as a Transport buffer
error; no unexpected frontend-buffer error is reported.

The unchanged default protocol2/selected1 route was exercised separately at the
same source, not inferred from the literal cohort:

| Legacy protocol2/selected1 stage | Recorded checks | CapturePreview PNGs | App elapsed |
|---|---:|---:|---:|
| Initial process |207|23|709.229s|
| Restart process |215|24|621.422s|

This legacy cohort has422 recorded check entries and47 images. Root inspected
all47; its626 source fixture files remain identical to its own baseline after
each stage. Each stage records one deliberate Transport buffer error. These
scripted native UI results do not qualify native-model UI execution or story
quality. Neither cohort's elapsed time is a product performance threshold.

Each of these four app processes still emits the115-byte SDK1412
class-unregistration diagnostic. It is separate from the controlled frontend
error buffer and remains unresolved under D09 #31. Root also reports a late,
profile-scoped observation of zero matching WebView processes at16:25:10UTC.
That point-in-time process observation is not proof of controller destruction
order, clean SDK teardown, absence of transient windows or a universal no-leak
property. Passing app journeys/exit codes do not resolve the1412 diagnostic.

These corrected and legacy results do not replace the original49-image cohort
or the failed watchdog attempt. Final source-bound regression/normal-restoration
results and artifact hashes are still awaiting the coordinator's terminal packet.

## Reproduce with existing dependencies

These are reproduction templates, not commands run by the document author.
Use pinned cached dependencies, a clean checkout and source-owned external
targets/TEMP. Serialize heavy work. Do not install dependencies or change assets
to reproduce the synthetic checks. From repository root:

```powershell
$env:CARGO_BUILD_JOBS='1'; $env:CARGO_INCREMENTAL='0'
$env:CARGO_PROFILE_DEV_DEBUG='0'; $env:CARGO_PROFILE_TEST_DEBUG='0'
$env:LIBSQLITE3_FLAGS=''
$env:TEMP='<task-temp>'; $env:TMP=$env:TEMP
$taskNativeTarget='<absolute-external-target>'
cargo test --locked --offline --jobs 1 --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --target-dir $taskNativeTarget --bin locallore-desktop-spike evaluation::selected::tests::literal_selected_review:: -- --nocapture --test-threads=1
cargo clippy --locked --offline --jobs 1 --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --all-targets --target-dir $taskNativeTarget -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
```

From `apps/desktop`, using the existing approved Node executable/dependencies:

```powershell
$env:LOCALLORE_CHECK_OUTPUT_DIR='<artifact-root>/selected2-checks'
node check-literal-selected-evaluation.mjs
node check-selected-source-freshness-review.mjs
node verify-frontend.mjs
$env:LOCALLORE_D07_SELECTED_ARTIFACT_ROOT='<artifact-root>'
$env:LOCALLORE_D07_SELECTED_TARGET_DIR=$taskNativeTarget
node selected-evaluation-harness.mjs --literal
# Separately, the default protocol2/selected1 route creates its own cohort:
node selected-evaluation-harness.mjs
```

The harness accepts only the closed `--literal` switch, builds the harness
frontend/native executable, creates its own UUID fixture workspace and launches
only its hidden/unfocused app processes. Existing dev-harness/env gates enable
fixed synthetic consent, picker, lost-acknowledgement and capture cases. They do
not expose arbitrary code, files, commands, models or runtime failure control.
The harness target contains a development build; restore a normal build afterward:

```powershell
node build.mjs
# From repository root, replace the harness build in the same explicit target:
cargo build --locked --offline --jobs 1 --manifest-path apps/desktop/src-tauri/Cargo.toml --target-dir $taskNativeTarget
```

Environment supplied by Root: Rust/Cargo1.93.1, PowerShell7.6.5, Node24.22.1,
Windows NT10.0.26300 x64. Source pins React/react-dom19.3.1, esbuild0.28.2,
TypeScript7.0.2, Prettier3.9.10 and Tauri2.12.5; lockfiles remain the authority.
These are existing dependencies, not downloads or an upgrade performed here.

## Pending coordinator completion

- Final source-bound Rust regressions and native formatting: **PENDING**.
- Final Android Rust host tests/dependency-graph exclusion: **PENDING**; this is
  not a pending Android device/JNI/ABI qualification claim.
- Final normal build/frontend/format/artifact restoration: **PENDING**.
- Exact terminal cohort/log/hash and final artifact inventory references:
  **PENDING Root evidence append**, not inferred here.

UI real-model execution, real OS dialogs, mid-provider process death, paused
incomplete UI resume, human story quality, whole-app RAM/performance and phone
parity remain unqualified. Full native-comparison **desktop execution** remains
separate; the shared full-comparison native Rust producer already has its own
qualification. This packet neither revokes that evidence nor claims its UI gate.
Raw logs, generated images, workspaces and private diagnostic content remain
local/ignored. No D07 checkbox, epic closure, publication or human acceptance is
awarded by this record. Root owns final evidence reconciliation and integration.
