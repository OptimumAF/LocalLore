# Desktop narration diagnostic read v1: proposed contract

2026-10-29. Refs #29 **D07.04/D07.06**.
**PROPOSED / DOCUMENT ONLY / NO IMPLEMENTATION / UNCOMPILED / UNRUN.**
Base `272c8bb5d74209d44eb17fcb330e3c59ea9d4f5c`; branch
`plan/d07-narration-diagnostic-desktop-read-v1`. Claim before editing:
[#29 comment6499452729](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6499452729).
Only this new document is owned. Root must accept the interfaces and allocate
independent FIRST tests after the companion gates, before implementation.

## Scope and existing authority

Expose the accepted full Protocol4 companion **reader only** through the existing
desktop comparison reader capability, worker, IPC and selected-turn view. Reuse
the [companion contract](D07_NARRATION_DIAGNOSTIC_EVAL_COMPANION_CONTRACT_2026-10-29.md)
and its closed artifact protocol1, five statuses, finite Host projection and
exact source/checkpoint/attempt binding. Do not reinterpret stored causes.

Preserve old Host/schema, trace-v1, capture-v1, RecordingFile, StoredTurn4,
Report4, ReaderEvidence and existing action/result schemas. Add a separate
closed action/result, not an opaque field in old evidence. No new Host operation,
provider, store, catalog, selected-Protocol4 feature, execution owner or grant.
Normal native execution remains Protocol3; reading an eligible Protocol4 source
does not enable generation. Existing full-run/default start/resume stay unchanged.

Explicitly exclude future-run opt-in and all admission/index changes. Those need
a separate durable client/idempotency/restart contract: current FullComparisonStart
and retry identity bind only client/kind/batch; IndexWire is closed. A transient
checkbox or later declaration cannot safely bind intent before admission.
The current manager's completed-resume early return also precedes Core execution;
any future opt-in adapter must validate its companion before that return. This
proposal neither fixes nor adopts that future execution path.

## Proposed native and IPC interface

Existing seams are `evaluation/comparison.rs::OpenedRead::V4`, Capability,
ReaderGrant, Record and `comparison_launch`; `comparison_commands.rs` already
parses closed actions for `evaluation_comparison`. Reuse these owners. Proposed
new native input and method in the existing evaluation module:

```rust
pub struct ComparisonNarrationDiagnosticRequestV1 {
    pub token: String,
    pub binding: String,
    pub row: locallore_eval::local_lane::comparison::desktop_api::RowId,
    pub observer: locallore::inspection_query::Observer,
}
pub fn comparison_narration_diagnostic_v1(
    self: &Arc<Self>,
    lease: &Arc<WindowLease>,
    epoch: u64,
    granted: bool,
    input: ComparisonNarrationDiagnosticRequestV1,
) -> Result<Value>;
```

The already registered `evaluation_comparison` command gains exactly action
`"narration_diagnostic_v1"` with this closed query:

```text
{runToken:<lower-case UUID>, binding:<64 lower-case hex>,
 turnId:<1..64-byte existing identifier>, arm:"left"|"right",
 observer:{kind:"omniscient"}|{kind:"player"}|{kind:"character",id:<identifier>}}
```

No renderer path, source directory, admission, attempt, session, owner, grant,
protocol switch, model option or execution flag. The observer is a requested
lens, never privilege. Existing native picker/managed-read consent remains the
only way to obtain the read capability. No extra picker or consent is required
for another authorized read of that same live capability.

Request compact UTF-8 bound is **4,096 bytes**, with exact keys/types and current
identifier/UUID rules. Existing transport supplies Value: raw duplicate keys
have already been lost; do not claim duplicate-key detection at this layer.
Bounded envelope parsing may refuse invalid input before authorization.

After valid parsing, manager admission order is fixed:

1. Deny `!granted` or any non-Omniscient observer with `Forbidden`, before input
   binding/row lookup, lease dispatch, expiry, token/source or filesystem probes.
2. Validate native input scalars, then use existing live lease/epoch admission,
   TTL/record pruning and exact same-owner token lookup. Token is scoped to the
   retained reader, not a full-run execution token or a new permission.
3. Transfer the existing Capability to the same admitted comparison worker,
   using the existing busy/operation/cancellation/close lifecycle. No source I/O
   under manager/window metadata locks and no second owner registry or worker.
4. For OpenedRead::V4 only, call the unchanged accepted Core method below.
   V2/V3 return fixed `Unsupported`; do not probe companion files or reopen the
   source with another protocol to seek success.
5. Bound/return the closed result only through the existing current owner,
   epoch/client/token/operation and cancellation completion fences. Retired,
   closed or replaced contexts cannot install private results or resurrect caps.

```rust
scene_v4::desktop_api::narration_diagnostic_v1(
    opened: &scene_v4::desktop_api::OpenedComparison,
    expected_binding: &str,
    row: &RowId,
    observer: Observer,
    native_inspection_granted: bool,
) -> Result<Value>
```

This is the existing function's signature, not a new Core wrapper/variant.
The Core Outputs access check still precedes its binding/row/source probes.
Manager admission does not replace it. Keep existing four-client/900-second
retention, operation bounds, one-worker rule and close-after-revocation behavior.
The 30-second response timeout is not cancellation or a hard I/O deadline;
retain the actual operation for explicit status/close recovery until it finishes.

The access guarantee starts at the new manager/method with an already opened
native read capability. Existing `WorkspaceState::get` can initialize/open
storage before Host permission is read; `open_read_only` itself is not an access
check. No transport-wide zero-filesystem promise or workspace change is implied.

## Closed response, statuses and errors

Proposed successful IPC envelope, compact UTF-8 bound **8,192 bytes**:

```text
{version:1, kind:"comparison_reader_narration_diagnostic_v1",
 run_token:<exact requested token>, diagnostic:<unchanged Core result>}
```

Core result keys remain exactly:

```text
{version:1, protocol_version:4, kind:"narration_diagnostic_v1",
 binding:<exact source snapshot binding>, row:{turn:<exact turn>,arm:<exact arm>},
 generation_grant:false, status:<one status>, [observation:<typed record>]}
```

| Status | Observation key | Meaning |
| --- | --- | --- |
| `no_declaration` | Absent | No declaration; legacy absence is not a cause |
| `no_observation` | Absent | Declared, no bound retained observation |
| `recorded` | Required | Actual stored supported validation decision |
| `host_unavailable` | Required | Stored supported Host unavailable reply |
| `host_rejected` | Required | Stored fixed-code Host rejection, not validation |

The observation is the exact closed validated record from the accepted protocol:
version/kind/declaration/run/source hashes, arm/index/admission/checkpoint hash,
typed host_query/host_reply and generation_grant:false. Nullable decision fields
remain required and finite tuples/codes are exactly those of the accepted
companion/Host contracts. No extension keys, arbitrary errors, prose, raw prompts,
paths, null observation or synthesized summary. Rust owns integrity and binding.
Hashes establish consistency; they do not authenticate historical origin/session.

Keep failures as fixed-code ResultErr, never successful unavailable data. Use a
new narrow diagnostic error projection without changing old action semantics:

| Source error | Desktop error |
| --- | --- |
| Forbidden / InspectionForbidden | Forbidden |
| DiagnosticWire / DiagnosticBinding / SnapshotMismatch | EvaluationIntegrity |
| DiagnosticBudget / bounded envelope overflow | EvaluationBudget |
| DiagnosticIo / Io | EvaluationIo |
| Reparse / AliasedDestination / unsafe path | UnsafeEvaluationPath |
| UnsupportedPlatform / wrong supported reader protocol | Unsupported |
| Invalid native input / UnknownRow | InvalidEvaluationInput |
| Lease closed / unknown, foreign, expired or retired token / busy | Existing Closed / UnknownEvaluationRun / EvaluationBusy |
| Existing strict source/receipt/checkpoint/ledger failures | Existing fixed failure projection |
| Unrecognized internal failure | EvaluationIo; never pass through text |

No partial result on overflow/error. A present malformed/orphan/conflicting file
is an integrity refusal; do not display it as NoObservation. Read permission
grants no generation, knowledge, retry, replay, validation, mutation or resume.

## Frontend controller and presentation

Propose `ComparisonReaderController.inspectNarrationDiagnosticV1(): Promise<void>`
and `diagnostic: ReaderNarrationDiagnosticV1 | null` state, separate from existing
evidence/summary. Store the immutable whole checked IPC envelope, including its
token; do not discard that binding or retain arbitrary JSON. Proposed decoder:

```typescript
function checkedReaderNarrationDiagnosticV1(
    raw: unknown, token: string, source: ReaderSource, row: RowId,
): ReaderNarrationDiagnosticV1;
```

`ReaderNarrationDiagnosticV1` is exactly the new IPC envelope above. Its diagnostic
uses a discriminated closed union: the two absence statuses prohibit observation;
the other three require the accepted typed observation and matching Host branch.
Use the
existing selected row, source snapshot and beginRead/live ticket lifecycle;
refuse non-Omniscient/currently ineligible/other-protocol requests before dispatch.
No caller-supplied binding/row bypass, auto-retry or diagnostic polling.

The decoder rejects unknown/prototype/accessor/symbol keys, wrong envelope/status/version,
foreign token/binding/row/scope, query/reply disagreement, invented grants and
invalid finite tuples. Query head equals the selected source BEFORE head; scope
and turn match the selected row. Do not reselect an attempt, infer a reason from
old trace/prose, or authenticate a session string. Require every numeric field
to be a finite nonnegative safe integer; attempts fit u32, index<24/admission<32.
Unsafe u64 heads/base revisions refuse the frontend reply rather than round or
change existing wire numbers. Exact Core validation remains authoritative.

Clear diagnostic data synchronously in clearPrivate, observer/row/query/source/
permission/context changes, pending reads, close, failed binding and dispose.
Use the existing request/context/lifecycle fences after every await and pending
notification; old delayed replies cannot refill a cleared character/player lens.
Returning to Omniscient requires an explicit fresh read. No change to any actor's
Engine knowledge, Query2 eligibility or generation context.

In ComparisonReaderPanel, an Omniscient-only Protocol4 button requests the new
read. Keep selected story/branch/arm/source, before/after revision, observer,
pending read and fixed error visible before metadata. Display the immutable base
and actual attempt when present. Label validation decision separately from final
phase/receipt/fallback/scenario/quality. NoDeclaration and NoObservation do not
mean validation was not run; HostRejected is not narration rejection. Preserve
both human needs-improvement assessments and the original missing historical
causes. Use existing evidence-context layout; do not reintroduce sticky-header
overlap or hide a failed/no-receipt case below a raw JSON body.

## FIRST and application-owned proof gate

Proposed owned implementation paths: comparison_commands.rs; evaluation.rs
exports and evaluation/comparison.rs only; comparison-reader-model/controller,
ComparisonReaderPanel; narrow developer documentation. No full-run/index,
selected, Host/schema/generator or provider path is owned by this slice.
Root allocates separate independent FIRST tests before implementation.

The smallest finite roster is:

1. Rust parser/manager: exact closed requests, early denied/bad-source/bad-token
   precedence; all statuses/errors/caps; V2/V3 refusal; live and foreign lease/
   epoch/token; busy/close/timeout/retirement and late completion. Preserve old
   read actions and worker/lock behavior; inventory only after releasing locks.
2. Actual frontend controller with mocked IPC: exact dispatch/decoder, unsafe
   numbers, delayed result across observer/row/source/dispose, pending/error and
   no automatic retry. Headless actual component wide/narrow structure, positive
   visible context boxes/hit tests and no private actor-lens text. Label mocks
   and headless output explicitly; neither is native IPC/render evidence.
3. Extend only the existing fixed development comparison-reader fixture/journey
   (`comparison_reader_harness.rs`, comparison-reader-journeys.ts and
   comparison-reader-harness.mjs). Generate new synthetic scripted Scene4 inputs
   using accepted Core entries, plus a legacy fixture. Actual Recorded and
   absence paths are separate from explicitly labeled trusted stored-envelope
   HostUnavailable/HostRejected/malformed controls. Labels/provenance belong in
   local external evidence, not new artifact fields. No new provider or model.
4. Run that same controller -> native IPC -> manager -> accepted Core reader in
   actual hidden, unfocused WebView2. Capture bounded semantic state and app-owned
   PNGs for all five statuses, visible refusal and cleared actor lens; include
   wide/narrow selected context, receipt/fallback distinction and visible errors.
   Inspect every image individually and check nonzero context geometry/no header
   overlap. Preserve original bytes, all expected refusals and unexpected errors.
5. After capability/process release, compare the complete synthetic fixture
   inventory byte-for-byte. Record zero model execution/import/copy/reservation,
   bounded local errors, known child closure/unknown states, exact source/runtime
   versions and unavailable checks. Observation counters are not SDK-load proof.

Any needed held-read test seam must be explicitly frozen before production;
existing provider faults are not I/O/latency hooks. No arbitrary action/path,
code/file/shell execution, general debug server, desktop control/capture or
unrelated application automation. Outputs stay local/gitignored on physical D:;
TEMP/TMP remain process-local D:/Dev/_Temp. No private cohort or protected owner
resource is read, modified, regenerated or uploaded.

This author performed source/Git/whitespace inspection only. No implementation,
test, registration, compiler, formatter, Cargo, Node, browser/app, model/assets,
device or desktop execution. Next: Root accepts/refines this proposed contract
after companion gates, then allocates independent FIRST source. This note grants
no merge/release authority or full task, quality, device or dependency acceptance.

## Interface precision before acceptance — 2026-10-29

This normative append resolves the earlier shorthand; the original 264-line
proposal remains intact. Claim before editing:
[#29 comment6499719137](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6499719137).
The proposal remains unaccepted pending companion gates. No implementation or
independent FIRST source is allocated by this append.

Request compact UTF-8 overflow **above 4,096 bytes** preserves the existing
parser's `InvalidEvaluationInput` and may precede authorization. The error-table
envelope-overflow entry refers **only to the new response**: total serialized
UTF-8 bytes above **8,192** return `EvaluationBudget`, without truncation or a
partial reply. No old-action limit or error behavior changes.

The distinct new frontend envelope is checked with `detached(raw, 8192)` and
its exact `comparison_reader_narration_diagnostic_v1` kind. Do not reuse the
old evidence wrapper or its separate 4,096-byte allowance; 8KiB is the entire
new envelope, not the payload plus another wrapper allowance.

Reader snapshot `diagnostic.binding` and companion `run_binding_sha256` are
different hashes; equality between them is **not** an invariant. Frontend checks
only context actually available: token, snapshot binding, selected row, scope,
BEFORE head, query/reply equality, closed fields and hash shapes. The accepted
Rust reader owns exact manifest/source/checkpoint/ledger/base-revision/attempt
binding. Do not invent a Source run key or derive an attempt/base from a new
latest lookup. Safe-number refusal and generation_grant:false still apply.

Existing `cfg(test)` before_publish barriers suffice for deterministic held-
completion close/retirement/stale tests. No new held-I/O seam is required or
authorized. Keep the existing **30-second response timeout** unchanged: it is
neither cancellation nor a hard filesystem deadline. No shortened-timeout seam
is authorized or needed; exercise the actual 30-second boundary once or label
that check unrun. Mock/headless, native component and actual WebView evidence
retain their separate meanings and limitations.

Only document/source/Git/prefix/hash/whitespace checks were performed here.
No compiler, formatter, Cargo, Node, app, model/assets, device, desktop or probe
execution. Release this document to Root for acceptance after the companion
gate; all task, dependency, quality and execution-admission limits still stand.

## Root acceptance for isolated independent FIRST source — 2026-10-29

Root accepts the proposal and precision for source-only independent tests.
Claim: [#29 comment6500337073](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6500337073).
All eleven companion groups have passed within the current broad run at
`272c8bb5`; complete Eval/native qualification remains pending. Refine only
the earlier scheduling restriction: isolated test authoring may proceed while
the coordinator's exact source and heavy commands remain unchanged. This grants
no production integration, second heavy workload, execution or acceptance.

Accepted native input/method, action string, frontend method/type/decoder and
closed request/result/caps/access/fencing rules are those above. Freeze the
private parser case as `Action::NarrationDiagnosticV1` carrying the proposed
native request. Existing `before_publish` barriers only; no new I/O, timeout,
clock, global, environment-driven fault or arbitrary callback/path test seam.
Use the actual 30-second timeout once if feasible, otherwise identify it unrun.

Independent author owns only these NEW test files and a handoff append here:

- `apps/desktop/src-tauri/src/evaluation/comparison/scene_read_review/narration_diagnostic_review_tests.rs`
- `apps/desktop/src-tauri/src/comparison_commands/narration_diagnostic_review_tests.rs`
- `apps/desktop/check-narration-diagnostic-reader-review.mjs`

The nested manager child may reuse its unchanged parent Fixture/inventory
helpers. Root later registers both Rust children and the frontend checker;
missing registration/APIs are setup, not behavioral RED. Freeze actual synthetic
producer/native-manager cases separately from trusted stored-envelope controls;
preserve full post-release inventories, permission/role/canonical assertions and
old actions. Do not reopen held run.lock during a full inventory or hash a
generic JSON Value as though it were original typed Receipt bytes.

The frontend checker freezes actual model/controller and Panel static-HTML
checks with synthetic transport fixtures. It may propose a closed headless
geometry mode using the same actual component, local files and existing pinned
browser; author does not execute it. No desktop/input injection or network server.
Freeze all five statuses, malformed/unsafe-number refusals, context clearing,
pending/errors, no dispatch during rendering and visible selected context.
Any additional native-journey fixture/control API must return to Root for an
exact finite acceptance before source, never become an arbitrary action hook.
Actual hidden-WebView/IPC/render/geometry and image inspection remain required
later gates, not satisfied by these mocks/static HTML or this source freeze.

Root retains later implementation ownership for the proposed adapter/frontend
paths and the existing fixed development files `comparison_reader_harness.rs`,
`ui/comparison-reader-journeys.ts`, `comparison-reader-harness.mjs`, and narrow
checker registration in `verify-frontend.mjs`. No full-run/index/selected/Host
schema/provider changes. Every author check is source/Git/hash/whitespace only;
no formatter/compiler/Cargo/Node/browser/app/model/assets/device/OS-probe or
desktop execution. Full task, dependency and negative human-review gates remain.

## Independent FIRST source handoff — 2026-10-29

Agent `model_guard_review`, exact accepted base `4bdf9c24`, branch
`test/d07-narration-diagnostic-desktop-read-first-v1`. Claim:
[#29 comment6500395518](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6500395518).
Own only the three NEW files allocated above and this handoff append. Existing
fixtures/helpers/registrations, production, companion code and its corrected
immutable test SHA256 `eaa714033d023d0892602abd668bf08687b97db843ed6410b9b85550cac8788b`
are unchanged. Root registers the children/checker later.

The nested native-manager child authors **six test functions**. One ordinary
opted-in scripted one-scene/12-row template is produced through accepted Core
entry/actual Host harvest; every test copies bytes before opening a capability.
Both recipe reads retain the exact actual observation. Legacy NoDeclaration is
actual default output; NoObservation moves one retained fixture file outside
the run. Stored HostUnavailable/HostRejected are explicitly trusted metadata
controls, not claims of those actual Engine outcomes. No new provider is added.
Native envelopes are checked for exact keys and <=8,192 serialized bytes.

The other groups freeze permission before invalid scalars/lease/expiry/corrupt
source, authorized expiry, V2/V3 refusal despite a corrupt companion filename,
foreign owner/epoch/token, invalid selector, integrity/budget errors, cached old
summary stability, busy/close/retirement and held completion. The existing
before_publish barriers are the only hold seam. The sixth function waits the
**actual unchanged 30-second response timeout** once, observes the still-owned
worker, then explicitly closes/releases/drains it. This function is authored
but unrun; it is not a shortened clock, cancellation or hard I/O-deadline proof.
Complete inventories are compared only before capability acquisition and after
release/drain; known fixture mutations are retained or restored explicitly.

The parser child authors **three test functions**: exact action/three requested
lenses, closed fields/types/identifiers and refusal of execution/path/grant
selectors, and unchanged existing action/overflow behavior. The future private
variant is exactly `Action::NarrationDiagnosticV1`. >4,096-byte compact queries
remain InvalidEvaluationInput; no raw duplicate-key proof is asserted for Value.

The independent frontend checker authors **151 source-enumerated cases**:
five status round-trips, 25 finite decision tuples, 43 fixed Host rejection
codes, closed nested shapes/foreign tuples/unsafe numbers/prototypes/getters/
symbols/cycles, actual controller dispatch and lifecycle clearing, and actual
Panel static HTML. This is an authored roster, not an executed count. It keeps
the entire distinct checked envelope, and deliberately uses different snapshot
and run-binding hashes. Old Source/Summary/Status DTOs have a separate fixture
calibration; missing APIs or bad calibration are SETUP, not behavioral RED.
Subscriber observations are asserted outside callbacks so existing subscriber
exception isolation cannot hide a failed clearing assertion.

The controller cases cover five statuses, exact closed dispatch, immutable data,
pending/error display, no automatic retry, synchronous pre-dispatch observer
switch, delayed results across observer/row/context/permission/dispose/close,
query/ordinary-read/clear clearing and unsupported Protocol3 refusal. Static
Panel checks require selected source/turn/arm/revisions/observer/phase, distinct
diagnostic status, fallback and unreviewed quality, with no dispatch during
render and no private diagnostic text after switching to an actor lens.
The intended output is bounded local JSON plus up to13 static HTML documents;
there is no browser/geometry mode, PNG, native IPC or WebView claim here.

Constructibility limits are preserved. No arbitrary Value/accounting seam forces
a native8KiB overflow for a valid finite closed record. The oversized frontend
DTO also violates the identifier bound: it is an adversarial refusal control,
not an isolated8KiB boundary proof. Exact response-cap enforcement still needs
source review. No new companion-specific link/reparse/isolation probe, model,
device or desktop operation is authored. Existing unrelated OS-guard regression
fixtures in broad suites do not qualify this new companion boundary.

Original unformatted test-source SHA256 values:

| Source | Lines / authored roster | SHA256 |
| --- | --- | --- |
| Nested manager child | 256 / 6 functions | `606cf2c8c226fa71c047d55aac84f5c5332ddb65006b91ede651545f4aee3b14` |
| Parser child | 56 / 3 functions | `797a6e24c148f837f2976a3c3e954810d41136326d57b5a8c72a0314cbddc5f4` |
| Frontend checker | 275 / 151 cases by source enumeration | `46e7f0cecdb15cfeaf9de2d16b9f2965c4118b54a9470ed7f32214b40375a92f` |

All author checks are source/Git/line/function/hash/whitespace inspection only.
**UNREGISTERED / UNCOMPILED / UNRUN**: no syntax checker, compiler, formatter,
Cargo, Node, app/browser, assets/model, device, new OS probe or desktop execution.
Missing methods/decoder/state/action/registration remain setup prerequisites.
This frozen source releases the four owned paths to Root for registration,
format-equality proof, separate-author production and actual verification after
the companion gate. Actual hidden-WebView/IPC, wide/narrow geometry/images and
individual image inspection remain later gates. Both needs-improvement human
assessments, historical absent causes and dependency/merge restrictions stand.

## Root allocation after immutable FIRST handoff — 2026-10-29

Root accepts source freeze `99b400c6` from `4bdf9c24` for separate-author
implementation. Claim and exact original hashes/counts:
[#29 comment6500763519](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6500763519).
The nine Rust groups and 151 authored frontend cases remain unregistered,
uncompiled and unrun; their existence is not a pass or behavioral RED.

Refine scheduling only for isolated production source authoring while the
coordinator's broad companion checks still run at unchanged `272c8bb5`.
All eleven companion groups have passed inside that run, but complete Eval and
desktop component gates remain required. No second heavy workload, desktop
integration/execution or qualification is authorized by this scheduling choice.

Root owns only `ui/comparison-reader-model.ts`,
`ui/comparison-reader-controller.ts` and `ui/ComparisonReaderPanel.tsx` on
`impl/d07-narration-diagnostic-desktop-frontend-v1` in the released selected
checkout. Different author `main_window_backport_review` owns only
`comparison_commands.rs`, `evaluation.rs` and `evaluation/comparison.rs` on
`impl/d07-narration-diagnostic-desktop-native-v1` in the released reader checkout.
These paths are relative to their existing desktop UI/native directories.
No tests, fixtures, schemas, contracts, old action semantics, Host/provider,
full-run/index/selected paths or timeout/held-I/O seams may change.

Root retains registrations, reconciliation, formatter-equality proof, actual
checks, later explicitly frozen finite development-harness controls and evidence.
Source authors perform source/Git/whitespace checks only: no compiler, formatter,
Cargo, Node, browser/app, assets/model, device, new OS probe or desktop execution.
Independent review and full native IPC/render/geometry/image gates remain later.
No task, quality, dependency, security or merge acceptance follows.
