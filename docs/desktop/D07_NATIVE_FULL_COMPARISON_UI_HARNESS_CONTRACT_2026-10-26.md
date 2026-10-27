# Native full-comparison UI harness contract

Refs #29 (D07.03–D07.06 supporting verification), #21. Frozen before implementation.
This extends the existing hidden, unfocused app-owned WebView harness. It never
uses desktop input, activation, desktop images or unrelated applications. Root
owns execution and individually inspects every generated CapturePreview PNG.
Only Root holds the heavy-process slot; other checkouts do source-only work.

## Ownership and interfaces

- Root: existing `comparison-run-harness.mjs`, `ui/main.tsx`, harness config type,
  `src-tauri/src/main.rs`, `build.rs`, command permission wiring, normal bundle
  exclusions, documentation and integration. No dependency/schema changes.
- Rust fixture agent: NEW `src-tauri/src/comparison_run_native_harness.rs`,
  existing `comparison_native_commands.rs` and `model_commands.rs` only.
- Journey agent: NEW `ui/comparison-run-native-journeys.ts` only.
- Independent controller reviewer: read-only, existing consumer controller/model.

Launcher has one closed optional argument `--native`; no arbitrary command or
code argument. Native mode sets `LOCALLORE_D07_NATIVE_FULL_HARNESS=1` together with
the existing D02/full-comparison flags. It never sets D04/localplay. Main exposes
only boolean `nativeFullComparing` alongside the existing `fullComparing` config;
route the new journey before the scripted journey, passing the actual stable
`nativeComparisonRun` as `full` and the existing `controller`, `comparison`,
`errors`, `invoke`, `dispose`, and `{stage}`. No production controller exports.
The new function is named `comparisonRunNativeJourneys`.

## Closed native fixture

`active()` requires compiled dev-harness plus active D02 harness, test-memory,
full-comparison and native-full flags. Validate native-owned workspace exactly
matches `LOCALLORE_TEST_WORKSPACE`, has `stories-v1.sqlite` basename and an ordinary
`full-comparison-native-<canonical UUID>` parent. Pin/check its parent using the
established export pin helpers before fixture operations. No renderer paths.

NEW module exports `NativeComparisonHarness: Default`, `active()`,
`model_root(&Path)->Result<PathBuf,String>`,
`approved_model_source(&Path)->Result<Option<PathBuf>,String>`,
`consent(&Path,&NativeComparisonHarness,&Value)->Result<bool,String>`,
`read_consent(&Path,&NativeComparisonHarness)->Result<bool,String>` and
`NativeComparisonHarness::take_lost_ack()->bool`.
Root manages `Arc<NativeComparisonHarness>` in dev builds. The two consent
substitutions occur only under active checked fixture gates. Normal OS consent
functions and the actual Rust comparison/ModelManager owners remain unchanged.
Execution metadata must identify version1/full_comparison_execution/approved_native.
Read consent is independent from execution consent and cannot authorize generation.

NEW command `harness_native_comparison_case(window,workspace,state,scenario)`
accepts only these fixed strings, an object-free string parameter:
`hold-execution-consent`, `release-execution-consent`, `deny-execution-consent`,
`deny-read-consent`, `lose-start-ack`, `consent-status`.
It validates current window lease/workspace/gate. Status returns
`{version:1,kind:"native_full_comparison_fixture",synthetic:true,active:boolean,held:boolean}`.
Hold is bounded by the service's existing preparation deadline; it never alters
runtime owners, grants, providers or result DTOs. Denials and lost ACK are one-shot.
Lost ACK consumes only one successful native start reply after service execution,
returning EvaluationIo; same-client native lookup must recover its actual owner.

Actual model import uses ordinary `model_import`, with ONLY its picker replaced
by the native-owned `LOCALLORE_D07_NATIVE_MODEL_SOURCE` under this fixture gate.
`model_root` derives `parent/model-native-v1`; no renderer supplied root. Existing
ModelManager validates the fixed approved profile/hash and owns actual import.
Never call `model_load`: comparisons reserve their normal isolated owner.
Stage the already approved installed worker with existing `stage-runtime.mjs`.
No download, new backend, alternate model manager or change to approved budgets.
Root verifies approved worker/model hashes before its separately allocated run.

## Journeys and artifacts

Use actual App selector callbacks through bounded app DOM interaction, actual
stable frontend controllers and native commands. No copied admission predicates.
Reuse current labels and capture schema: `full-idle`, `full-running`,
`full-denied`, `full-unknown`, `full-cancelled`, `full-switched`, `full-partial`,
`full-completed`, `full-reader`, `full-mira`, `full-sable`, `full-receipt`,
`full-narrow`, `full-finished`; restart uses `full-idle`, `full-restarted`,
`full-reader`, `full-finished`. At most 18 PNGs across the two stages. Failures
retain their bounded report and every emitted PNG for inspection.

Initial journey: select native lane; import approved installed asset without
ordinary load; held/denied execution consent, cancel before reservation and
context retirement; unknown successful start ACK resolves through same-client
lookup without duplicate start; release/positively reconcile each captured owner.
Then real paired batch1, actual partial proof, explicit resume batch3, actual
completed durable proof. Mechanical/narrative scenario failures are recorded, not
reinterpreted as passes. Inspect via native managed entry and existing ReaderV1
commands: actual receipt/capture/output, player/Mira/Sable Query2, actor raw
refusal, independent read denial and narrow render. Preserve live selected
story/observer/revision separate from inspected experiment identity/lens/head.
Use actual generic cleanup observations; closed/running:false alone is not proof.

Restart: same isolated durable evaluation and model roots, new actual process;
cold native catalog/open/completed resume/read; prove inventory unchanged and no
additional generation/confirmation. Do not infer a no-model-call result from
elapsed time; use service/reservation/fixture evidence actually available, and
state unavailable instrumentation honestly.

Reuse existing quiescent full-comparison inventory command. Snapshot semanticVersion2
contains selectedStory/observer/revision/pendingOperation/displayedReceipt/visibleError,
actual native comparisonRun and cleanup DTO, bounded semantic DOM. Report retains
existing inventory fields/checks/captureLabels/errors/stage plus modelExecution
(true only for initial actual-generation stage), nativeIpc:true, synthetic:true,
rendering:"native-webview2", desktopInput:false, nativeDialogsAutomated:false and
explicit consent/picker double labels. No raw private outputs in public evidence.

Native allocation: 2,100-second app watchdog and 2,160-second launcher watchdog,
four scenes total genuine admitted work, actual fixed per-arm worker budgets
unchanged, one heavy process. Source must be frozen/clean throughout. Normal
frontend/native build restored and hook exclusion checked after qualification.
No test here qualifies OS dialog interaction, human quality or physical phones.

First actual cohort d614ca73 demonstrated that a 60s presentation wait may end
during deterministic reference/setup construction, before native confirmation.
The bounded pre-confirmation observation allowance is 240s (reference work plus
the unchanged native preparation deadline); terminal service errors fail early.
No service/model clock, deadline or budget changes. Retain at most 96 deduplicated
scalar controller transitions and the pre-cleanup failure state, with any dropped
count explicit. This is observational test-only evidence, no execution/debug RPC.
On a held-consent failure, close the captured controller identity before releasing
consent, then dispose. Independent review tightens this below. Preserve the
original failure check separately from cleanup.

On failure with held consent, the development-only abort helper first arms
`deny-execution-consent` and requires its exact version1 closed fixture ACK
with synthetic=true, Boolean active and held=true. Only that acknowledged denial
permits attempting captured close and then releasing the hold. A resolved close
is not proof: controller uncertainty/cleanup errors are conservatively retained.
Unknown/invalid denial ACK never releases consent; disposal is always attempted.
No native consent deadline, production owner or model budget changes. This
failure path has actual-controller/mock-IPC RED/GREEN evidence, separately from
the successful source960 native initial/restart cohort. It is not an actual
native-worker failure injection or a new native cleanup proof.
