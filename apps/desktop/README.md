# Desktop Play & Story Lab

The [bounded native shutdown qualification](../../docs/desktop/D09_DESTROYED_EXIT_QUALIFICATION_2026-10-26.md)
records destruction-before-exit and early-destruction/reopen checks through the
existing app-owned harness. Reproduce with `node shutdown-harness.mjs zero`,
`seven` or `window` using the documented external output/target environment.
The native gate requires both confirmed cleanup and an actual current-window
Destroyed event. SDK diagnostics and full D09 packaging/privacy gates remain
separate; the source-bound record retains failures and remaining limitations.

A native Windows shell over the shared Rust engine. The original Lantern Quay
fixture supports giving the last potion to Mira, waiting, attempting an
unlearned ability and explicit typed dialogue. Finalized Rust receipts populate
the transcript; the inspector shows accepted events, requests and player-state
differences. Play uses player context. Story Lab explicitly reveals spoilers and
can inspect character or omniscient context without granting author mutations.

Fake inference remains explicit. The production app stores accepted turns in
`stories-v1.sqlite` under Tauri's app-local data directory, outside the source
checkout. Startup resumes the first stable saved story; the library can resume
any listed story. The saved workspace details show its actual path and schema.
Close releases a live session and retains its save. New and Reset create distinct
saved stories and retain earlier history. Up to four sessions can be open.
Unsubmitted composer text remains session-local; submitted uncommitted requests
are durable but are never automatically committed or cancelled on resume.
Storage/replay errors appear explicitly with no temporary-memory fallback.

**Alternate timeline** creates a saved child at a completed accepted-turn
boundary. Review the original parent/head, fork point and stable child identity,
then confirm. The original and later choices remain intact; opening the child is
a separate explicit action. Replacing a committed turn means choosing the
boundary before it, then writing a new turn on the child. A small
application-local recovery record saves the exact
fork identity before dispatch. Lost acknowledgements retain that identity;
same-session retry is explicit, and restart recovery only checks existing saved
children. Cancellation never claims an earlier commit was rolled back.

The fixed synthetic fork harness exercises these controls through the actual
frontend controller/native IPC and captures only the hidden application-owned
WebView. It never activates or captures the desktop:

```powershell
$env:LOCALLORE_D08_FORK_ARTIFACT_ROOT='<task-owned-local-output>'
$env:LOCALLORE_D08_TARGET_DIR='<task-owned-ordinary-Rust-target>'
node apps/desktop/fork-harness.mjs
```

This builds the development frontend/native binary and uses two processes with
one synthetic workspace and private test WebView profile. The normal bundle
excludes the fixed fault/fixture journeys. Build/static/controller-mock checks,
actual native IPC, native WebView rendering and device execution are separate
evidence classes; consult the dated fork verification report for executed results.
See [fork verification and limits](../../docs/desktop/D08_FORK_NATIVE_VERIFICATION_2026-10-23.md).

Memory & evidence opens a read-only typed inspector for profiles, accepted
history, directed relationships, knowledge, promises and evidence. It supports
completed historical heads and before/after replay without changing the live
player. Statement, belief and truth labels remain distinct; NPC lenses exclude
private player display messages. Story Lab requires a spoiler acknowledgement.
Summaries and semantic retrieval remain unavailable in this inspector. Saved
timeline selection and prefix replay use the shared ancestry rules. See [D05 native inspection](../../docs/desktop/D05_NATIVE_INSPECTION.md)
and [verification](../../docs/desktop/D05_NATIVE_VERIFICATION_2026-10-22.md).

**Derived memory** reads the selected saved story's shared maintenance status.
Preparing derived data requires consent; **Process one chunk** performs one
bounded step. Cancel a stale job before pruning it, then explicitly prepare a
new job. These controls preserve canonical events and character knowledge.
They never run background steps or generate model summaries. A lost reply stays
unresolved across selection changes: read status in the original selection or
explicitly acknowledge the uncertainty. Acknowledgement neither cancels nor
undoes saved work; native storage still enforces Busy.

For the fixed synthetic native maintenance journey, set
`LOCALLORE_M07_MEMORY_ARTIFACT_ROOT` and `LOCALLORE_M07_MEMORY_TARGET_DIR` to
task-owned local directories, then run `node apps/desktop/memory-harness.mjs`.
It uses the same controllers and native IPC, hidden app-only WebView2 rendering
and an actual process restart. Run `node apps/desktop/verify-frontend.mjs`
afterward to restore the normal frontend and check test-hook exclusion.

Inspection snapshots now provide structural diagnostics by default, explicit
private Player/Full readable views, and a separate private consistent SQLite
copy for deliberate inspection. Preview identifies scope, revision, included
files and privacy. A native folder picker saves the exact captured bytes without
overwriting existing files; existing readable inspection folders open as untrusted,
read-only text within this app. Reveal storage shows app-owned location metadata.
See [D03 native inspection](../../docs/desktop/D03_NATIVE_EXPORT.md) and
[verification](../../docs/desktop/D03_NATIVE_VERIFICATION_2026-10-22.md).

An explicit experimental local CPU profile now imports and verifies the approved
Qwen3-0.6B Q8_0 artifact through a native picker. Action and Dialogue free text use
the shared director, engine validation and narrator; accepted v2 receipts record
provenance, timing and any safe narration fallback. Supported actions are limited
to single English scene commands; unclear text asks for clarification. Quality
and network-blocked qualification remain pending. Arbitrary model choice, story
generation remains unavailable. See
[D04 native integration](../../docs/desktop/D04_NATIVE_INTEGRATION.md) and
[verification](../../docs/desktop/D04_NATIVE_VERIFICATION_2026-10-22.md).
Save files and the imported model are local app data; OS-level backup, access
control and device security still apply.

If local worker cleanup cannot be confirmed, the app keeps that worker reserved
and blocks import/load. Choose **Unload model** to retry cleanup; a failed or
retired window does not grant permission to start a replacement. This uses the
same runtime and model manager, with no automatic inference retry or fake-provider fallback.
The [cleanup qualification](../../docs/desktop/D07_OWNED_RUNTIME_CLEANUP_QUALIFICATION_2026-10-25.md)
separates fixed-worker Rust tests, synthetic frontend checks and unrun native/model gates.

Story Lab also provides an explicit author correction preview and confirmation
for replacing a fact's proposition on a new saved timeline. The original history
and private correction reason are retained; later choices are not replayed
automatically. Corrected timelines use scoped native Play and inspection views.
Legacy debugging, readable inspection exports, timeline navigation and derived
memory maintenance remain unavailable for that domain version. See the
[author/scoped-Play verification](../../docs/desktop/M08_AUTHOR_NATIVE_UI_QUALIFICATION_2026-10-23.md).

**Playable story archive** in Story Lab transfers a full private snapshot of a
saved story. Review and consent precede native file selection. Archive3 preserves
corrected canonical history, author provenance and private discovery bindings;
ordinary stories keep Archive1/2 selection. These files include hidden facts and
all retained timelines. They exclude weights, caches, private traces and pending
work. Import validates and stages the file before one atomic application. An
existing story identity conflicts without overwrite or merge. Later play changes
the saved story, while a published file retains its captured history. Manual
transfer provides no live synchronization.

The fixed synthetic Archive3 harness runs six actual native processes for
export/import, cancellation, lost acknowledgement, conflict, cold reopen,
observer isolation, one typed fixture Wait and a further process restart:

```powershell
$env:LOCALLORE_D08_ARTIFACT_ROOT='<absolute-task-owned-local-output>'
$env:LOCALLORE_D08_TARGET_DIR='<absolute-task-owned-Rust-target>'
node apps/desktop/archive-v3-harness.mjs
```

It exercises the mounted controllers and native IPC with fixed picker doubles,
hidden/unfocused application-owned WebViews and bounded semantic/PNG evidence.
It does not operate system dialogs or the desktop. The continued turn uses the
synthetic provider, with no model execution. Inspect the generated images and
restore the normal frontend/native build afterward. See the
[Archive3 qualification and exact limits](../../docs/storage/M08_ARCHIVE3_COORDINATOR_QUALIFICATION_2026-10-23.md).
Android's Archive3 decoder/labels are implemented. Corrected-timeline Android
opening remains unavailable; bidirectional runtime parity is not demonstrated.

See [ADR-0006](../../docs/adr/0006-desktop-host.md),
[host-v1](../../docs/desktop/HOST_V1.md),
[D02 harness](../../docs/desktop/D02_HARNESS.md) and
[original D02 verification](../../docs/desktop/D02_VERIFICATION_2026-10-22.md) and
[current-main gate](../../docs/desktop/D02_CURRENT_GATE_2026-10-22.md).

## Build and run

Tested on Windows 11 x64 with Rust 1.93.1, MSVC/Windows SDK, installed WebView2,
Node 23.10.0 / npm 11.2.0. Development dependency provisioning uses network;
subsequent locked builds use the cache. Fake fixtures need no model or API key.
The later Archive3 native cohort used the already available Node24.22.1 and
Rust/Cargo1.93.1; it installed or upgraded no dependencies.
Real local play additionally requires the verified worker resource and an explicit
approved-model import, as described in D04 integration.
Other OS targets and installers remain unqualified.

From a clean checkout at the repository root:

```powershell
npm --prefix apps/desktop ci --ignore-scripts --no-audit --no-fund
npm --prefix apps/desktop run build
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked
# Subsequent cached build/run; opens this application's normal window.
cargo run --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline
```

Always rebuild the normal frontend with `npm run build` after using a development
harness, then rebuild the native executable without `--features dev-harness`.
Node, Playwright and a dev server are not shipped runtimes. React and CSS bundle
into local assets; the executable uses the installed WebView2. The desktop is a
member of the repository Cargo workspace and uses the root `Cargo.lock`. The four
portable packages remain default members; portable `--workspace` test/Clippy
commands must explicitly exclude `locallore-desktop-spike`, as `scripts/check.py`
does. Android selects its JNI crate and does not depend on Tauri. Runtime and
evaluation crates retain their separate workspaces and locks. See the
[workspace alignment evidence](../../docs/desktop/D09_WORKSPACE_ALIGNMENT_2026-10-23.md).

Enter submits the selected typed action; Shift+Enter adds a newline, and IME
composition does not submit. Native form controls support keyboard navigation;
a skip link and visible focus lead to the composer. Layout & text exposes two
pane-width sliders and 100–200% text. The inspector can collapse, and transcript
pages contain at most 12 receipts. Copy receipt writes only the selected
finalized receipt after an explicit button press. Untrusted dialogue renders as
text; it cannot execute HTML, load external images or grant debug privileges.

## Verify without desktop control

From `apps/desktop`, `node check-model-cleanup-panel.mjs` exercises the actual
controller and renders four synthetic model states to local, ignored HTML/JSON.
It checks resident-worker controls, explicit cleanup retry and pending unload.
This is headless React markup, not native IPC, WebView pixels or a model run;
`verify-frontend.mjs` includes this check in the normal frontend verification.

Story Lab also provides a dedicated [memory comparison reader](../../docs/desktop/D07_COMPARISON_READER.md)
for actual protocol2/3 paired/rollout cohorts. The app's native picker explicitly
asks to inspect private evidence. Rust retains source validation, actual Query2
observer filtering and read-only locks; valid historical reports stay viewable.
The reader shows actual source revisions, expected/actual results, accepted
receipts, retained captures and recorded role outputs. Missing evidence stays
unavailable. Reader progress is in memory. A dedicated selected-case experiment
panel now prepares and starts an original case in two isolated Rust-owned
Stores, then explicitly opens saved results for inspection. Full-comparison
execution remains separate. The linked guide gives exact fixed native
harness commands and distinguishes synthetic frontend checks from IPC/rendering.

The [shared scripted selected-case Rust API](../../docs/desktop/D07_SELECTED_CASE_SCRIPTED_CONTRACT_2026-10-25.md)
is implemented and has passed its source-bound checks. See [D07 #29](https://github.com/OptimumAF/LocalLore/issues/29) for acceptance status.
The [qualification record](../../docs/desktop/D07_SELECTED_CASE_SCRIPTED_QUALIFICATION_2026-10-25.md)
records exact commands, results, retained failures and unavailable checks.
Desktop IPC/controller selected start, explicit resume and result controls are
implemented; qualification and remaining limits are recorded below.
Reader handles/progress remain in memory; the shared selected runner writes durable
isolated `selected.json`, Stores, checkpoints, ledgers and local diagnostic reports.
It uses the original case index and both actual full requests/prefixes in new disjoint
Stores; it does not import experiment state into a source or live gameplay story.
Completed resume is read-only; a finished failed/cancelled attempt needs a new
destination/client to try again. Lost-checkpoint committed recovery is model-free
and leaves missing call/capture/timing evidence unknown. Inspection grants no knowledge.

The additive [shared native selected-case API](../../docs/desktop/D07_SELECTED_CASE_NATIVE_CONTRACT_2026-10-25.md)
uses the same Rust turn path and approved local worker. Its
[qualification record](../../docs/desktop/D07_SELECTED_CASE_NATIVE_QUALIFICATION_2026-10-25.md)
distinguishes actual worker/model tests, model-free history, static headless
export images and unrun desktop UI/IPC checks. Native startup occurs only after
both-arm/source preflight and one native reservation callback; uncertain cleanup
retains the actual owner and conservative charges. This is a developer Rust API,
also used by the desktop's approved-native lane. Opt-in runs require the already approved assets
locally; they never fetch a model or worker.

The additive shared `selected::desktop_read` Rust capability provides bounded
metadata and actual observer-filtered before/after evidence for isolated selected
runs, including supported native history without loading assets. Its
[qualification](../../docs/desktop/D07_SELECTED_CASE_DESKTOP_READ_QUALIFICATION_2026-10-25.md)
records source-specific checks. It never exposes the full report as an actor
summary, repairs missing checkpoints or grants execution.

The earlier [selected1 desktop consumer qualification](../../docs/desktop/D07_SELECTED_CASE_DESKTOP_CONSUMER_QUALIFICATION_2026-10-25.md)
records its source-bound hidden/unfocused WebView2 and native IPC:154 initial checks/20
app-owned images, then160 checks/21 images in a new process reopening the same
workspace. These runs use scripted fake inference and fixed consent/picker
doubles. All41 images were inspected. The panel separates execution and private
read permission, preserves same-request recovery after an unknown acknowledgement,
and shows actual before/after scopes, Rust receipts and observer-filtered Query2.
Inspection never changes generation permissions or character knowledge.

From `apps/desktop`, with already provisioned dependencies, an absolute local
`LOCALLORE_D07_SELECTED_ARTIFACT_ROOT` and optional
`LOCALLORE_D07_SELECTED_TARGET_DIR`, run `node selected-evaluation-harness.mjs`.
It uses only app-owned hidden WebViews and fixed development-only hooks; no
desktop input, activation, screenshot, debugging server or model is needed.
Paused/incomplete UI resume, native-model UI execution, real OS dialogs, human
story quality, whole-app performance and physical-phone parity remain unqualified.
The guide distinguishes service tests, mock transport and native execution,
preserves earlier failures and provides commands for restoring normal builds.

The [literal conversation control definition and oracles](../../docs/desktop/D07_LITERAL_CONTROL_CONTRACT_2026-10-25.md)
make a separate limit explicit: both existing v2 comparison policies include state;
`ScriptedBaseline` names the fake provider lane. It is not a transcript-only
memory policy. The first model-free input-channel tests and genuine historical
read checks alone do not enable a literal control or establish quality.

A separate [scripted protocol3 developer CLI](../../docs/desktop/D07_LITERAL_COMPARISON_PRODUCER_QUALIFICATION_2026-10-25.md)
now runs the actual literal-player/Relevant pair through the shared Host and
durable Store, with bounded scenes, cold inspection and resume. Its literal
metrics remain separate from memory metrics. This CLI uses fake inference.
The [trusted native Rust entry](../../docs/desktop/D07_LITERAL_NATIVE_OWNER_QUALIFICATION_2026-10-25.md)
now has model-free ownership/cancellation/cleanup qualification using the
existing resource port. [Approved-model paired and rollout qualification](../../docs/desktop/D07_LITERAL_NATIVE_MODEL_QUALIFICATION_2026-10-25.md)
now records 96 outcomes, 153 actual role calls, cold reads and zero-reservation
completed-native resume using the desktop manager. Failures and 28 narration
fallbacks remain visible; no human quality acceptance. Native3 CLI and
full-comparison native-model desktop execution remain unqualified; the shared full native
comparison Rust producer is separately qualified.
Accepted [PR202 scripted selected2](https://github.com/OptimumAF/LocalLore/pull/202),
[PR204 native selected2](https://github.com/OptimumAF/LocalLore/pull/204) and
[PR205 selected2 read capability](https://github.com/OptimumAF/LocalLore/pull/205)
provide the typed shared execution and inspection paths for protocol3 sources.
Their source-bound records separate actual native-model Rust evidence from
scripted plumbing and desktop rendering.
The [protocol3 Rust read capability](../../docs/desktop/D07_LITERAL_DESKTOP_READ_QUALIFICATION_2026-10-25.md)
now validates cold report/receipt/capture/state reads with observer restrictions,
including retained real-model data without the optional runtime. The
[desktop protocol3 reader qualification](../../docs/desktop/D07_LITERAL_DESKTOP_UI_QUALIFICATION_2026-10-26.md)
adds actual controller/native IPC,30 inspected app-owned WebView images and
restart/observer/refusal/recovery checks using synthetic inference. That earlier
reader-only cohort refused protocol3 source transfer without consuming its
capability; this is historical evidence, not the current selected-case limit.

The current selected-case panel routes protocol2 sources to selected1 and
protocol3 sources to the actual typed selected2 Rust plan/read capability. It
supports explicit prepare/start, separate consent to read results and completed
verification/resume with a freshly chosen matching source. A locally attempted
source token stays unavailable in the controls until a fresh reader token is
supplied, including after an unknown acknowledgement. Rust remains authoritative
for both source prefixes/requests, observer filtering, plan bindings and worker
ownership; this presentation fence is not proof of native source consumption.

The [current literal selected desktop qualification](../../docs/desktop/D07_LITERAL_SELECTED_DESKTOP_QUALIFICATION_2026-10-26.md)
tracks final coordinator gates. At clean source `6a195f85`, Root reported the
scripted protocol3/selected2 UI cohort passing 252 initial and 261 restart check
entries, with 27 initial and 28 restart actual hidden/unfocused app-owned
WebView2 CapturePreview images. Root inspected all 55 images with no further
visible layout findings; all 626 source fixture files remained byte-identical
in each stage. Each stage retained exactly one deliberate Transport-buffer error
from the lost-acknowledgement journey.
The cohort uses the normal
controllers/native IPC and fixed picker/consent doubles, with fake inference
and no desktop input. These counts do not establish independent quality claims.
From `apps/desktop`, use `node selected-evaluation-harness.mjs --literal` with
the same task-owned output/target environment above to reproduce that path.
Legacy compatibility, native tests/lint/format, frontend checks, Android Rust
host/graph checks and normal-build restoration passed at the same source; exact
counts, commands and retained failures are in the linked record. SDK shutdown error
1412 remains observed and tracked separately in [D09 #31](https://github.com/OptimumAF/LocalLore/issues/31);
this is not a clean-SDK-exit, RAM, performance, human-quality or phone claim.
Native-model UI execution, real OS dialogs and selected-case paused/incomplete
UI resume remain unqualified.

Story Lab also provides **Run full comparison** for the fixed scripted fake
inference lane. Choose paired snapshots or separate-arm rollout, then1..4 new
scenes per chunk. Resume is explicit; lookup, status and saved-run opening never
start inference. Saved output is durable; window capabilities and progress
presentation are in memory. **Inspect report** asks for separate native read
consent and opens the existing observer-filtered reader. Close that reader before
resuming its run. These comparisons use isolated shared Rust histories and do not
modify live stories or establish model quality.

The [full scripted desktop qualification](../../docs/desktop/D07_FULL_COMPARISON_DESKTOP_QUALIFICATION_2026-10-26.md)
separates service tests, frontend doubles and actual hidden WebView/native IPC
execution. From `apps/desktop`, run `node comparison-run-harness.mjs` with existing
absolute `LOCALLORE_D07_FULL_COMPARISON_ARTIFACT_ROOT` and
`LOCALLORE_D07_FULL_COMPARISON_TARGET_DIR` directories; the target must be outside
the checkout. The closed synthetic initial/restart journey uses no CLI arguments,
desktop control, model downloads or model execution. Exact commands, versions,
retained failures and unavailable gates are in the qualification record.

Run these developer checks from the repository root; the qualification record
identifies the executed source, target directories and results:

```powershell
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --test comparison_selected_review -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --test comparison_selected_alias_review -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --lib local_lane::comparison::selected:: -- --nocapture --test-threads=1
# Optional only with LOCALLORE_D07_HISTORICAL_COHORT naming the genuine retained cohort:
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --test comparison_selected_historical_review -- --ignored --nocapture --test-threads=1
```

```powershell
npm --prefix apps/desktop run check
npm --prefix apps/desktop run format:check
npm --prefix apps/desktop run harness:export
npm --prefix apps/desktop run harness:durable
npm --prefix apps/desktop run harness:native
npm --prefix apps/desktop run harness:headless
python scripts/check.py host --offline
cargo test -p locallore --features host --locked --offline
cargo clippy -p locallore --all-targets --features host --locked --offline -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --features dev-harness -- -D warnings
# Restore and check the normal frontend/native configuration.
npm --prefix apps/desktop run check
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline -- -D warnings
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline
```

First headless provisioning only: from `apps/desktop`, run
`node node_modules/playwright/cli.js install chromium`. It downloads a public
development browser. Native harness rendering requires only installed WebView2.
The harness commands launch their own hidden native app or headless browser,
exercise the same controller. The durable native journey uses one synthetic SQLite
database through app-owned WebView close/reopen and a separate executable process
restart. The legacy D02 journeys explicitly retain memory fixtures. All runners save synthetic JSON plus app-only PNGs under
ignored `artifacts/`. They never activate a window, inject desktop input or
capture the desktop. Native and headless evidence are labeled separately.

Tauri 2.12.5 / tauri-build 2.7.4 remain pinned. The build-only public-icon temp
copy works around tauri-winres 0.3.7 apostrophe escaping; an apostrophe in TEMP
itself remains an upstream limitation. `bundle.active=false`: these commands
produce a native executable, not an installer or release. No app data or raw
error text is uploaded automatically.
