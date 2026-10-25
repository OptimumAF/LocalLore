# Proposed native comparison reader — 2026-10-25

Refs #29 D07.06, partial prerequisite. **FROZEN READ-ONLY INTERFACE / IMPLEMENTED.**
The dated sections preserve the design and test freeze. Exact executed sources,
results, retained failures and remaining gates are recorded in the
[native qualification](D07_COMPARISON_READER_NATIVE_QUALIFICATION_2026-10-25.md).
This document does not claim GUI acceptance, selected rerun, model execution or
approval of the shared reader. The sole owned new file is this document, on
`docs/d07-comparison-native-reader-contract` / `source-d07-comparison-native-reader-contract`,
based exactly on `ddcecbbc81c08f2340b9076aa063160652df1c49`.
[Claim 6393763021](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6393763021).
No build/test/formatter/Node/Cargo/app/device/model/desktop commands were run.

## Actual source boundary

- [Shared reader](../../crates/locallore-eval/src/local_lane/comparison/desktop_api.rs)
  already exports `open_read_only`, `summary(&OpenedComparison, bool)` and
  `evidence(&OpenedComparison, binding, &RowId, EvidenceRequest, bool)`.
  Keep these signatures and actual JSON unchanged. `OpenedComparison` privately
  owns directory pins, an existing exclusive cooperative `run.lock`, manifest,
  validated turns and last-validated summary. Opening validates the whole cohort;
  summary clones that snapshot. Evidence compares the full manifest and selected
  checkpoint and revalidates selected Store/recording/capture. Query2 binds the
  exact before/after engines through actual input/output/mechanical fingerprints.
  It is not a live whole-cohort health assertion or an execution capability.
- [EvaluationManager](../../apps/desktop/src-tauri/src/evaluation.rs) owns
  registration, one worker, native run/token/job state, retirement/drain and model
  execution cancellation. Current status dispatch covers built-in and curated
  kinds. No persistent comparison-reader slot exists. Existing tokens expire
  after 900 idle seconds, and existing token limits must remain bounded.
- [Curated adapter](../../apps/desktop/src-tauri/src/evaluation/curated.rs) and
  [IPC](../../apps/desktop/src-tauri/src/evaluation_commands.rs) show the owner,
  `spawn_blocking` and captured `WindowLease` pattern, but curated evidence is a
  different wire contract and currently has no native Host grant argument.
  Do not copy that omission into this private comparison adapter.
- [author_ipc.rs](../../apps/desktop/src-tauri/src/author_ipc.rs) obtains the
  real Host from `WorkspaceState` and exposes `Host::story_lab_granted()` metadata.
  `WorkspaceState::get` in main currently constructs `Host::new(true)` in the
  memory harness or `locallore_workspace::open(path, true)` for durable use.
  [workspace::open](../../crates/locallore-workspace/src/lib.rs) forwards that
  native boolean to `Host::with_persistence`; the readonly getter at line94 of
  [host/author_port.rs](../../crates/locallore/src/host/author_port.rs) returns it.
  This is trusted eligibility, not proof of explicit user consent for this reader.
  At this source no `OpenSession`/`SetInspectionAccess` APIs exist in Core/apps/docs;
  do not describe them as current reusable authorization calls. Host JSON cannot
  change the construction grant. Renderer metadata is presentation only.
  [lease.rs](../../apps/desktop/src-tauri/src/lease.rs) fences each `main-epoch`
  window; [main.rs](../../apps/desktop/src-tauri/src/main.rs) invalidates before
  retirement/drain and calls `finish_close` only after cleanup.
- [exports.rs](../../apps/desktop/src-tauri/src/exports.rs) has the Windows-owned
  `IFileOpenDialog` folder picker with filesystem/existing-folder/no-recent flags.
  Its title currently describes an inspection export destination. Reuse its COM
  picker mechanics through a minimal title/purpose extraction; do not tell users
  that selecting a comparison source saves an inspection snapshot.
- [evaluation-controller.ts](../../apps/desktop/ui/evaluation-controller.ts),
  [evaluation-model.ts](../../apps/desktop/ui/evaluation-model.ts) and the existing
  panels target version1 built-in/curated reports. Main's current evaluation
  context key is selected session/view/observer only. App's `LabAcknowledgement`
  calls `Controller.acknowledgeLab`, which updates frontend state and `setView`;
  it does not mint native consent. Comparison replies need a dedicated decoder,
  explicit native consent and stronger root/window/head/selection epochs.

This slice opens an **existing cohort directory** through the application's own
native picker. It does not copy/import it, browse arbitrary files, create output,
reserve models, call a provider, execute a runner, or expose a selected-rerun button
as usable. Full comparison start/resume and isolated selected-case rerun remain
plainly labelled unavailable, including when `report.source_matches` is true.

## Same owner, bounded capability lifetime

Add a private comparison reader child to the SAME `EvaluationManager`, proposed
`evaluation/comparison.rs`. Store one native `OpenedComparison` capability per
window/root incarnation, plus at most one in-flight reader request. No second
manager, detached worker, persistence journal or copied report engine.

Use existing registration/worker serialization for picker/open and evidence I/O.
An active built-in/curated worker refuses new comparison I/O with `EvaluationBusy`;
an admitted reader I/O task likewise prevents an execution worker from starting.
Extend the existing job kind explicitly; do not route a comparison token through
the current non-built-in-is-curated fallback. Never hold registration/state/lease
gates while showing a dialog, doing filesystem validation or joining a worker.
The read operation is bounded work, not inference; it acquires no model reservation
and creates no admission/role/budget ledger. Passive status and close can inspect
or retire the current reader while I/O is outstanding.

Concretely extend the existing private Job routing with an explicit
`ComparisonRead` kind, retaining its existing epoch/operation/cancellation and
SAME worker handle. The reader child tracks the exact client and phase, never an
execution run manifest. Before every publication require matching job kind,
epoch, operation, client, nonclosing state and valid lease/root. `close` sets the
existing cancellation signal and closing state even before the picker returns;
it does not force the modal dialog shut. A late selected folder or successful
shared open must then be discarded/dropped, not published as ready. Existing
execution `evaluation_cancel` must not guess a read job is curated: reject that
action for reader tokens, and use this slice's exact `close` cleanup instead.

A retained idle reader does not consume the worker, but keeps the shared run lock.
Execution against that cohort must fail `RunBusy`; do not promote the read handle
into a resume token. One active token and at most four bounded client-result
records per epoch are enough for this first slice. Reuse the 900-second idle
expiry, checked on requests; no timer/thread is added. **Access-time expiry is not
a wall-clock handle-release guarantee:** an idle open window can retain the lock
until the next access, explicit close or window retirement. Show that limitation.
On the next access after expiry, retire/drop before returning UnknownEvaluationRun;
do not silently refresh an expired capability. Do not evict an in-flight
or unacknowledged result to admit another picker. Explicit close releases it.

Token identity is native-minted GUID, bound privately to manager/root incarnation,
window epoch, client ID and the capability's immutable summary binding. No path
or native handle is serialized. A new picker requires the prior capability to be
closed; this avoids accidentally holding two independent runs locked. Repeated
status for the same client recovers a lost picker/open acknowledgement without
opening another dialog. A reused client ID with different intent is refused.
These recovery records are in-memory only; after process restart the user selects
the cohort again. There was no canonical write to recover.

On close, detach the capability under the state lock and drop its pins/lock outside
that lock. If an evidence task temporarily owns it, mark closing immediately,
suppress publication, and drop it when the SAME worker returns. No claim of
interrupting a blocking OS dialog/read. On window retirement invalidate authority
first, mark all reader records retired, then existing drain joins the worker and
drops every old capability before `finish_close`. Failed/poisoned cleanup must
still drop handles; ordinary calls fail closed. Test reopen acquiring `run.lock`.

## Proposed closed IPC

One additive command: `evaluation_comparison(action: String, query: Value)`.
Existing command names and historical wires remain untouched. Envelope is a
plain exact-key object, UTF-8 serialized maximum 4096 bytes. Reject unknown actions,
unknown keys, null/array substitutes, enum coercion and unsafe integers before work.
GUIDs use the existing native GUID syntax; bindings are 64 lowercase hex chars;
turn IDs follow the actual frozen suite and are at most 64 UTF-8 bytes.

| Action | Exact query keys | Meaning |
| --- | --- | --- |
| `pick` | `clientId` | Reserve one read operation; owned folder dialog, then shared open. No path argument. |
| `status` | `clientId` | Recover this epoch's exact pending/terminal picker/open result; never reopen. |
| `source` | `runToken` | Return bound source/row availability metadata projected from the cached shared summary, no raw report. |
| `summary` | `runToken` | Return the unchanged private shared summary in a native wrapper. |
| `evidence` | `runToken`, `binding`, `turnId`, `arm`, `request` | Call the shared evidence function with an exact closed request below. |
| `close` | `clientId`, `runToken` | Token is GUID or explicit null for an unacknowledged/pending open. Mark exact client retired, release eventual handles; idempotent for an already closed matching record. |

`request` is exactly one tagged object:

```text
{kind:"query", edge:"before"|"after", observer, view}
{kind:"receipt"|"capture"|"outputs", observer}
observer = {kind:"player"} | {kind:"character",id:actual bounded actor ID}
         | {kind:"omniscient"}
view = profiles|history|relationships|knowledge|promises|provenance|turn_diff
     | summaries|retrieval_indexes
arm = "left"|"right"
```

No scope/head/cursor/search/file/profile/provider/code field is accepted. Source
scope and completed edges come from the selected validated row, not the gameplay
session or renderer. The frozen API currently returns only Query2's first page,
limit64, empty search, cursor null. If the returned page has a next cursor, display
“More rows exist; paging is unavailable in this reader.” Do not add a nonfunctional
page button or silently claim a complete view. A future shared paging API needs
separate frozen tests/allocation.

Every action captures `WindowLease` from the actual window label, obtains the real
current Host/root, and checks `host.story_lab_granted()` in native code. Missing
eligibility is `Forbidden` before private token/source existence or file probing.
Recheck lease and root before publication, even after a successful dialog/open.
Never accept JSON `grant`, `root`, `windowEpoch`, `path` or authoritative session
metadata. This foreign evaluation Store is not authorized by querying its scope
against the user's gameplay Host. The trusted Host flag is only the eligibility
ceiling. Source validation and filtering remain in the shared reader; per-source
native consent below is also required.

Native consent is **not a renderer boolean**. Add a narrowly named
`choose_comparison_directory(owner)` using the existing folder-picker COM
mechanics, with fixed native text warning that original inputs, private character
truth, prompts and outputs may contain spoilers, and affirmative button label
“Inspect private evidence”. Cancellation returns None and grants nothing. The
actual successful native picker affirmation, eligible Host and current root/window
create an in-memory private `ReaderGrant` (no serde) for that selected source.
After shared open/summary validation, bind it to the actual capability/binding
before any private publication. Every summary/evidence call derives its boolean
from this native-owned conjunction, never `query.consent` or Main's Lab boolean.
No Core inspection-access mutation, Host reconstruction, generation grant, actor
knowledge change or matching gameplay session is needed. On close/expiry/root or
window retirement revoke the ReaderGrant alongside its capability. Tests alone
may inject a closed native picker outcome; normal IPC cannot supply a path or
affirmation. Cleanup `close` may release its exact caller-owned reader after grant
revocation, returning only closed status; it never reads private data.

Full summary is private and available only in the UI's omniscient view; clear it
on actor-lens transition. Native cannot infer a renderer's actual visual lens,
so this presentation rule is not claimed as security against a modified renderer.
Native always enforces the real private grant. Raw receipt/capture/outputs requests
with player/character observer must hit the shared early `Forbidden` path before
row/binding/file integrity probes. Query evidence is Rust-filtered for the selected
observer; never send raw capture to an actor view and hide it with CSS.

### Reply shapes and bounds

Proposed status exact keys:

```text
{version:1,kind:"comparison_reader",client_id,operation_id:safeInteger|null,
 phase:"choosing"|"opening"|"ready"|"cancelled"|"closing"|"closed"|"failed",
 running:boolean,run_token:GUID|null,binding:hash|null,error:closedCategory|null,
 read_only:true,execution_available:false}
```

Operation IDs use existing positive safe-integer allocation while admitted/running;
idle closed/unknown-terminal state may use null, never invent zero. `cancelled` means
the picker actually returned no selection; `closing` is an explicit abandonment,
not a promise that native I/O stopped. `ready` requires token+binding and no error;
failed requires a category and no usable capability. Close completion is `closed`.
Retain terminal status until explicit close/acknowledgement; no automatic retry.

Summary/evidence wrapper exact keys:
`{version:1,kind:"comparison_reader",run_token,snapshot}` or the same
with `evidence` instead of `snapshot`. Copy the shared value unchanged. Source
wrapper exact keys are `{version:1,kind:"comparison_reader",run_token,source}`,
where `source:{binding,protocol_version:2,rows,read_only:true,
execution_available:false}` comes from that same cached summary; no private full
report, filesystem path,
basename or invented new `source_matches` measurement. Row availability metadata
is private despite lacking prompt text. Bind every reply to request token/client,
operation and immutable summary binding.

Existing shared bounds remain authoritative: summary <=2MiB, <=48 rows; evidence
<=256KiB, capture <=196608 bytes; raw role output <=16384 bytes; Query2 page
<=65536 bytes, <=64 rows. Permit only a small fixed wrapper overhead (4096 bytes)
above shared caps and reject oversized whole replies. Status <=4096 bytes, source
<=65536 bytes; if the source projection cannot fit, return `EvaluationBudget`,
never truncate and label it complete. No renderer pagination/slicing of raw bytes.

Map errors into a frozen bounded native category set, never paths/raw OS messages:
`InvalidEvaluationInput`, `Forbidden`, `Closed`, `EvaluationBusy`,
`UnknownEvaluationRun`, `EvaluationTokenLimit`, `PickerUnavailable`,
`Unsupported`, `EvaluationSourceMismatch`, `EvaluationIntegrity`,
`UnsafeEvaluationPath`, `EvaluationBudget`, `EvaluationIo`, `EvaluationInternal`.
Preserve missing evidence as the shared successful `body.kind="missing"`, not an
I/O failure. Map SnapshotMismatch/checkpoint/recording/capture/raw/replay integrity
errors to integrity; RunBusy to busy; Reparse/unsafe directory to unsafe path;
shared budget errors to budget. Unknown internal strings fail closed as Io or
Internal, not successful empty data. Source mismatch in a valid historical report
is its actual `source_matches=false`, not an error or an execution waiver.

## Frontend integration and visible behavior

Proposed new `comparison-reader-model.ts`, `comparison-reader-controller.ts` and
`ComparisonReaderPanel.tsx`. Mount beside existing evaluation panels in Story Lab;
leave all version1 decoders and Play2.5 routes untouched. Decode actual shared
summary/report2 and evidence variants with strict primitive types/key sets,
existing UTF-8 caps and exact cross-bindings. Do not clone canonical validation
into TS or claim JSON.parse detects duplicate raw keys. Reuse `checkedPageV2` for
query pages with exact row scope, selected edge head, observer/view and original
scoped sources; never cast Query1 or fabricate a gameplay Context.

Controller receives coherent Root context: native root/window metadata and grant
availability, selected gameplay session/scope/head, view and observer. These are
presentation fences; native still captures its own authority. Install context key
and increment epochs BEFORE synchronous subscriber notification. Own pending/blocked
updates do not change the key or invalidate their own completion. Fence replies by
context epoch, client/token/operation, binding, row/arm, observer, evidence kind,
edge/view and request epoch. A late close cannot clear a newly opened capability.

On session/scope/head/Lab/lens change, immediately clear private summary/evidence;
retire an old pending read explicitly through exact close, retaining only bounded
client/token metadata until close is confirmed. Do not automatically reopen on
return. Observer change may preserve safe row identity only after discarding raw
presentation, then require an explicit Query inspection. Dispose suppresses late
replies and requests exact close; native window drain is the final release fence.
An unknown picker acknowledgement recovers status with the SAME client; it does
not create another picker, mark canonical cancellation, or block gameplay as if a
write were uncertain. Reader admission still respects manager busy/read lifecycle.

Show actual paired/rollout kind, lane/policies/profile/source match, completed or
partial rows, actual known/unknown roles, optional timing and estimates, and every
producer limitation. Missing null values remain “Unavailable”; estimates are not
measured tokens; scripted fixtures are labelled synthetic. Summary is last-validated,
not freshly validated whole-run health. Evidence failures remain visible while
retaining that labelled summary. Selected row displays original source scope,
before/after head and observer; receipt/capture/output text renders inertly.
No source link calls gameplay `resume`, imports a Store, changes knowledge, or
grants generation access. Display “Selected-case rerun unavailable — shared runner
prerequisite pending” and “Comparison execution unavailable in this reader.”

## First frozen tests and qualification allocation

Root must assign source/test paths after review. Proposed new native module and
tests are children of the existing manager; Root owns IPC registration, permissions,
main/App mounting, picker-purpose extraction and existing retire/drain integration.
No new shared API is needed for this read-only slice. Its desktop-only changes
must not relabel retained source fingerprints or historical model measurements.

Freeze these meaningful oracles before implementing the adapter:

1. Real scripted producer paired and rollout fixtures -> actual shared open ->
   native wrapper -> TS strict decoder. Include partial/guard/missing capture and
   historical source-mismatch fixture. Preserve all report bytes/optional values;
   no manually assembled private capture stands in for producer evidence.
2. Native fake picker returns only a fixed owned fixture path or cancellation.
   Test real Host grant true/false, foreign window/root/epoch/token/client, malformed
   enum/key/type/binding and raw actor denial before source probing. Opening a
   corrupt/locked/reparse/future cohort fails cleanly and releases every handle.
3. Same manager worker busy both directions; no provider/model reservation or
   canonical/run writes on reader actions. Compare complete cohort inventory after
   lock release; do not read Windows mandatory-locked run.lock during the hold.
   Close, expiry, failed open, late publication, lost acknowledgement, destruction
   and reopen must allow actual lock reacquisition with no token resurrection.
4. Selected drift/corruption/integrity errors and unchanged cached summary semantics
   reuse shared existing oracles, not broaden into live health promises. Actor
   Query2 isolation, raw grant denial, actual before/after scope/head and original
   source binding survive IPC. An unavailable next page remains explicitly blocked.
5. Actual Main/controller subscriptions: own pending does not recurse/cancel itself;
   session/head/lens/row changes suppress stale results; exact client recovery does
   not reopen; close for old token cannot clear new state; malformed terminal reply
   keeps pending recovery metadata and visible error. All execution action names
   are rejected, not silently forwarded to curated/built-in commands.

Then an app-owned fixed `comparison-reader-harness` should create/copy only its
synthetic producer fixtures under a task-owned ignored root, substitute native
picker results via `cfg(test)`/dev-harness closed scenario IDs, and exercise actual
same controller+IPC through hidden/unfocused WebView2. No OS dialog automation,
input injection, activation, desktop screenshots or generic path/debug endpoint.
Capture semantic selected run/row/scope/edge/observer/pending/error/receipt state,
normal+narrow app-owned CapturePreview images and bounded error buffers. Inspect
images before acceptance. Test initial and restarted process: restart requires
explicit new pick, old token is invalid, cohort unchanged. Retain source/executable/
fixture hashes and distinguish Rust-only, headless, native IPC and WebView evidence.
Native dialog cancellation is separately unit-tested through its fixed picker
double; the harness must not claim real dialog interaction or real-model quality.

Proposed future commands (targets do not yet exist; **ALL UNRUN** here):

```powershell
cargo test --locked --offline -p locallore-desktop-spike --bin locallore-desktop-spike evaluation::comparison::tests:: -- --test-threads=1
# apps/desktop, after Root supplies actual generated producer fixtures:
node check-comparison-reader.mjs
node verify-frontend.mjs
node comparison-reader-harness.mjs
```

Require nonzero expected native tests, preserve first actual failures and exact
commands/environment. Root then runs affected normal/dev builds, strict checks,
normal-hook exclusion and Android compatibility as warranted. No compilation,
native UI/IPC, rendering, model/device or milestone acceptance is claimed here.
Next runnable task is Root contract freeze and first native/controller oracle
allocation; D07.06's selected rerun remains a separate unmet gate.

## Root freeze and allocation — 2026-10-25

Root adopts proposal `19bdb499` with these narrow clarifications before editing:

- Add `reading` to the status phase enum for admitted evidence I/O. `ready`
  means idle and usable; `choosing`, `opening`, `reading`, and `closing` may
  have outstanding I/O. Every running status has its actual operation ID.
- Changing the comparison panel's own observer clears its full private summary
  and evidence immediately, preserving only source row metadata and its native
  read capability. A subsequent explicit Query2 action may use that capability.
  Changing the surrounding gameplay session/scope/head/Lab/native context closes
  the source. These are distinct controller events; neither alters actor knowledge.
- Opening and evidence use the existing manager Job/worker/registration. New
  `JobKind::{Builtin,Curated,ComparisonRead}` tags prevent implicit fallback.
  Passive status/source/summary clone bounded cached metadata without I/O.
- Root owns existing manager/module registration, picker-purpose integration,
  IPC/main, existing frontend mounting/verification, and the application harness.
  The native contributor owns only new `evaluation/comparison.rs` and its new
  `evaluation/comparison/tests.rs`. The frontend contributor owns only new
  `comparison-reader-model.ts`, `comparison-reader-controller.ts`, and
  `check-comparison-reader.mjs`. Root owns the new panel and CSS integration.
- Native public adapter methods receive the actual `Arc<WindowLease>`, epoch
  and actual Host eligibility; a JSON value never supplies native authority.
  The only picker injection is a Rust closure returning a native-selected path,
  captured by the IPC from the fixed production picker or test-only fixed double.
  No path/closure/code/consent field is added to renderer IPC.
- Native may reject an actor's raw-artifact request with `Forbidden` even before
  token lookup/admission. It need not acquire private source state merely to call
  the shared denial path. Permitted Query/Omniscient evidence still uses the
  unchanged shared reader, whose independent authorization tests remain required.

Implementation worktree: `source-d07-comparison-native-ui`, branch
`impl/d07-comparison-native-ui`, from unchanged reader `ddcecbbc`. The earlier
reader checkout remains immutable during preserved-regression execution.
At this freeze all native/frontend/harness acceptance cases above were UNRUN.
Later execution is attributed separately in the linked qualification; this
interface document does not turn a proposed oracle into an executed test.
