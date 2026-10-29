# Scene narration diagnostics v1: first contract freeze

2026-10-28 local date. Refs #29 **D07.04**, supporting #9 **M05.03/M05.04**.
**CONTRACT ONLY / NO IMPLEMENTATION / UNCOMPILED / UNRUN.**
Base: `11d82d61226b52c8873ddcd1e902aebdf6466dcb`.
Branch: `plan/d07-scene-narration-diagnostics`, reusing the separately released
`source-d07-comparison-native-ui` checkout on physical D:. The previous
`stack/d07-scene-native-desktop-base` remains at `d3852269`.

Claims before editing:
[#29 comment6489816251](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6489816251)
and [#9 comment6489819816](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6489819816).
The author owns **only this new document**. Root accepts interfaces and owns all
later integration/production allocations. Independent test and implementation
authors must use separate owned checkouts and claims. No production change may
precede Root's separate retained-native-render gate or its acceptance of this
contract. A contract is neither task acceptance nor permission for another model
cohort, validator relaxation, tuning sweep, sample-specific keyword patch or
retrospective repair.

## Current evidence and the named bottleneck

Current public ticket metadata and recent claims were read for #3, #9 and #29.
Their full task checkboxes remain unchecked. The latest negative human feedback
is **needs improvement**; the original negative assessment is also unchanged.
No case-specific/dimensional scores, human approval or competitor claim exists.

The frozen native report has 48 rows: 30 committed rows with mechanical fallback,
6 committed rows without fallback, and 12 failed rows. Its 36 NarrationValidation
stages contain 30 `rejected/narration` and 6 accepted decisions. Selected raw
responses satisfy explicit finite first-person refusals, but the historical
trace does not record which validator branch was first. Source-derived
sufficient violations are not measured earliest runtime causes.

An accepted unsupported environmental scene claim demonstrates the finite
validator's semantic limit. The literal comparator also lacks current legal
actor vocabulary and schema constraints supplied to the relevant-memory arm.
Those are separate quality/comparison findings, not counterfactual causal proof
that another input would improve the model. Preserve literal-v1 and its original
results. Changing that comparator needs a separate version/claim/contract.

This slice advances **observability of actual validation decisions**. It does
not solve semantic grounding, alter model inputs, judge prose, or make accepted
narration semantically safe. Private prose, prompts, packets and absolute local
paths are excluded from this public contract.

## Existing source surfaces inspected

`crates/locallore/src/turn_trace.rs` currently declares:

```rust
pub trait TraceSink {
    fn matches(&mut self, scope: &Scope, base_revision: u64,
               observer: &str, turn: &str) -> bool;
    fn record(&mut self, measurement: StageMeasurement);
    fn capture(&mut self, _artifact: crate::turn_capture::Artifact<'_>) {}
}
```

`StageMeasurement`, `StageRecord`, `Attempt` and `ErrorCategory` are existing
metadata. `Trace::run/counted` in `play.rs` receives `Result<T, Error>` and emits
only its coarse `ErrorCategory::from_engine`. Each direct `Error::Narration`
return has already lost its rule identity. A malformed Narrator response has an
existing Parsing measurement before its empty document enters validation.

The source-owned `NarrationPreparation::validate` dispatches Scene4 through
`scene_narration::validate_record`. That routine checks native binding/context
and ordinary record contents before generated-only
`scene_narration/renderer.rs::validate_generated`. The latter has two existing
finite refusals: first-person tokens and listed player-movement phrases without
an accepted player Move. No general semantic-entailment checker exists.

At present the actual precommit `Stage::NarrationValidation` call returns once;
its existing stage callback can cancel, then the Scene4 cancellation check runs
before fallback. Fallback uses the exact approved mechanical narration. Final
commit revalidates its legitimate source capability. Those call counts, order,
authority and cancellation boundaries must remain unchanged.

## Proposed smallest additive API — Root acceptance pending

Add exactly one **provided default no-op** method to the existing `TraceSink`:

```rust
fn narration_validation(
    &mut self,
    _diagnostic: NarrationValidationDiagnosticV1,
) {}
```

Proposed native Rust metadata types in the existing `turn_trace` module:

```rust
#[non_exhaustive]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum NarrationRejectionReasonV1 {
    Unclassified,
    SceneFirstPerson,
    SceneUnapprovedMovement,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct NarrationValidationDiagnosticV1 {
    // Private fields; construction stays crate-owned.
}

impl NarrationValidationDiagnosticV1 {
    pub fn version(&self) -> u16; // Always 1.
    pub fn outcome(&self) -> Outcome;
    pub fn error(&self) -> Option<ErrorCategory>;
    pub fn reason(&self) -> Option<NarrationRejectionReasonV1>;
}
```

The signatures above are a proposal, not existing compilable code. Types have
no `Serialize`/`Deserialize`, public field constructor, text, scope/actor/turn
ID, prompt, path, collection, timestamp, model counter or renderer constructor.
The existing matched sink/opaque attempt namespace supplies attribution; do
not invent another owner, identity registry or global/thread-local last reason.
`#[non_exhaustive]` allows later append-only reason variants with explicit
consumer handling. This freeze adds only the three listed variants.

Decision semantics:

| Actual validation result | outcome | error | reason |
| --- | --- | --- | --- |
| Ok | Accepted | None | None |
| Existing first-person branch reached | Rejected | Narration | SceneFirstPerson |
| Existing unapproved-movement branch reached | Rejected | Narration | SceneUnapprovedMovement |
| Other actual Error::Narration | Rejected | Narration | Unclassified |
| Actual Cancelled / Stale | existing Cancelled / Stale mapping | existing category | None |
| Any other actual error | existing rejected mapping | existing category | None |

`Accepted` describes only that finite validation call, never semantic safety,
final commit, model origin, privacy acceptance or human enjoyment. A rejection
is not itself proof that fallback later happened: a stage/diagnostic callback
can cancel before fallback. Existing receipt/report fields, not this callback,
own eventual fallback/commit/turn status. Historical missing diagnostics remain
**unavailable**, not a guessed `Unclassified` runtime event.

### Single-pass internal propagation

Proposed internal names (not new public entry points):

- `NarrationValidationFailureV1` retains the exact existing `Error` and optional
  reason. `From<Error>` records `Unclassified` only for actual Narration and None
  for other existing errors; `into_engine_error(self) -> Error` returns it
  unchanged. No second call, policy guess or string analysis occurs here.
- `NarrationPreparation::validate_detailed` has the same existing engine,
  record, presentation, literal and cancellation arguments, returning
  `Result<(), NarrationValidationFailureV1>`. Legacy dispatch maps its existing
  error once. Scene dispatch propagates the same detailed result once.
- `scene_narration::validate_record_detailed` and renderer
  `validate_generated_detailed` retain their existing checks and exact order.
  Only the two existing generated-scene return branches choose specific codes.
  Earlier/uninstrumented binding, profile, content, presentation or other
  failures remain their actual category with honest generic classification.
- Existing compatibility validation functions remain thin projections of a
  single detailed call to their original `Result<(), Error>` signatures. They
  do not first run old validation and then run detailed validation. Existing
  commit revalidation still occurs only where it already occurred.

Root may refine internal placement/visibility during interface acceptance, but
must amend this contract before changing the proposed public names, getters or
semantics. Do not add a second validator, infer causes by replaying a failing
record, call cancellation predicates again for diagnosis, derive a detailed
reason from a generic returned Error, or re-evaluate a passed check.

### Exact emission and isolation boundary

Only the existing actual precommit NarrationValidation invocation emits the new
callback, at most once per invocation. Derive both the unchanged coarse result
and optional reason from that single validation pass. Keep the original stage
measurement/callback first, then emit the new diagnostic if the sink remains
live, then run the **existing** Scene4 postvalidation cancellation check before
any fallback. Add no cancellation polls, caller clocks or callback probes.

Use the existing `Trace` panic isolation and measured diagnostic-overhead
accounting. A new-hook panic disables that sink as current trace hooks do; it
cannot replace the validation result, create a fallback, admit another request,
change a budget/deadline or bypass the existing cancellation poll. A hook that
cancels the actual token is observed at that existing boundary. No sink,
default-no-op, disabled/mismatched/retired sink and supported successful sink
must retain the same canonical/error/fallback/provider behavior apart from the
explicit side effects of a test's cancellation callback.

No allocation-growing reason history is added in Core. The value is fixed-size
native metadata with exactly one optional enum code. No extra provider/SDK,
consent, reservation, resource owner, model request or repair is introduced.
The hook carries no decision authority; a consumer cannot supply a reason to
request, validate, resume, commit or replay a turn.

## What this hook does and does not expose

- Exposes an actually reached first-person or unapproved-player-movement return
  in generated Scene4 validation, or honest generic classification of another
  actual precommit validation failure. It does not scan raw text separately.
- Existing Parsing measurements remain the source of malformed JSON evidence.
  This hook must not label parsing failure as an invented scene-specific cause.
- Provider/Director/repair, binding/preparation errors before this validation,
  postvalidation cancellation, post-fallback story-presentation refusal and
  final commit/revalidation failures retain their current boundaries. This
  phase adds no new detailed reason for those separate failures.
- Legitimate final commit revalidation must not produce a second event for the
  earlier NarrationValidation stage. Recorded retries that do not run that
  stage emit no fabricated decision and call no provider.
- Phase1 leaves `RingSink`'s new provided method as no-op. It does **not** yet
  retain or display detailed reasons in `TraceRing`, Host, Eval, Report4, native
  IPC or the UI. No historical report or capture is rewritten. Test sinks can
  observe the actual new callback only through the existing matched API.

## Frozen compatibility and authority invariants

Keep all existing engine `Error` variants/values, validation order and public
results. Keep exact accepted events, receipts, PlayRecord fields and serialized
bytes, fallback text, replay/idempotency, observer/inspection access, staged
source binding and canonical append rules. No mutable or serialized diagnostic
proof can become an accepted record.

Keep SceneFrame v1, schema IDs, narrator recipe/prompt versions 2.9/2.10 and
`grounded-prose-v2.4-scene-frame-v1`; keep literal-v1 rendering/packing and legacy
policies/prompts byte-for-byte. Keep old trace-v1 wire fields, collector limits,
request/host/native commands, Report4 and renderer decoders unchanged. Do not
make hidden actor labels, excluded phrases, matched words or secret counts
observable through a reason. Preserve unknown/generic cases honestly.

Do not read/rewrite the original negative human packet, captured raw model
responses, input prompts, fallback results or report human0 fields to create a
new pass. No new model cohort or near-duplicate capture is part of this slice.

## Independent deterministic oracle freeze before production

A different author must freeze **new original synthetic** fixtures/test source
before production. Root owns registration, first compilation and independent
review. Public provider tests may use NEW
`crates/locallore/tests/scene_narration_diagnostics_v1.rs`; a separate NEW private
unit child under `play/scene_narration` may verify single-pass cancellation/check
counts if external APIs cannot do so. That child's registration stays Root-owned.
These are future allocations, not paths owned by this document's author.

Proposed finite cases, using actual Engine/Play + a recording synthetic provider:

1. Default provided method compatibility, no sink and disabled/mismatched sink
   produce identical canonical records/error/fallback, provider prompt/schema/
   identity bytes, fixed budget limits and call counts. Naturally elapsed
   remaining-deadline values are measured bounds, not byte-equality oracles;
   forbid a reset/extension and add no clock hook to force equality. Existing
   implementers need not add a method. No callback for a
   generation guard refusal, absent validation stage or exact recorded retry.
2. Both Scene recipes: existing finite first-person refusal emits exactly one
   SceneFirstPerson, keeps the exact mechanical fallback and existing calls.
   Use original synthetic wording, not private captured model text.
3. Nonmovement + a listed player-travel phrase emits SceneUnapprovedMovement;
   an actual accepted Move and a valid second-person control preserve their
   existing results. A string satisfying both finite predicates keeps the
   original first-person-first order; do not run the movement check afterward.
4. Generic envelope/event-ID/speaker/content/presentation failures remain the
   original Error/category and Unclassified where this phase does not tag a
   branch. A non-Narration failure gets no invented Narration reason.
5. Malformed Narrator JSON retains its original Parsing error measurement and
   the actual generic validation decision/fallback. No second parse or provider
   call is introduced to explain the failure.
6. Hook cancellation after validation preserves the current postvalidation
   cancellation-before-excluded-fallback boundary. Hook panic/default/no-op and
   stage-record panic/disabled sink cannot change canonical results or invent a
   reason. Extend the existing cancellation/exclusion oracles, not their limits.
7. Instrument native check/cancellation callbacks in a synthetic unit fixture:
   detailed propagation invokes each existing check exactly once in the same
   order; no rerun or extra cancellation callback occurs to determine a reason.
8. Recorded retries, stale/closed source, exact mechanical fallback and legacy
   policy controls preserve existing errors/bytes/observer authority and zero
   unexpected provider calls. Legacy first-person behavior must not acquire the
   new Scene4 policy. Core synthetic tests cannot manufacture native SDK/consent/
   reservation evidence: source/callsite checks and Root's separately attributed
   compatibility checks cover those unchanged interfaces.
9. Fixed-size content-free getter/enum contract, one event per actual validation,
   absence of prompt/text/actor/path payload and default consumer exhaustiveness
   handling. Native synthetic secret sentinels never enter diagnostic metadata.
10. An independent generic unsupported environmental assertion characterizes the
    **existing finite semantic gap** without claiming safety. Diagnostic-only
    implementation must not change that acceptance rule or insert a keyword
    fix derived from the private failed sample.

Missing proposed APIs/module registration are **setup/compile prerequisites**,
not a behavioral RED. No test, compilation, formatter or native/model execution
is claimed by this document. Root must retain actual setup failures separately,
review the unchanged frozen assertions and run appropriate focused/broad Rust,
format/strict lint and compatibility checks only after the render-only gate and
separate production claim. Source intent or a new callback alone is not GREEN.

## Allocation, acceptance and next boundary

Future proposed production paths are limited to existing `turn_trace.rs`,
`play.rs`, `play/scene_narration.rs` and `play/scene_narration/renderer.rs` under
`crates/locallore/src`. Root owns those paths and their interface acceptance.
Engine/source-frame/compiler/Host/Store/native/Android/UI/Eval implementations
are outside phase1. The independent test author owns only its separately claimed
new test files; Root handles registrations. No dependency/SDK/model change.

A later **separately claimed Eval/Host/native/UI adapter** must specify bounded
private retention, optional wire/version compatibility, observer filtering,
actual causal labels versus unavailable historical metadata, and appropriate
native/render evidence. It cannot infer reasons for older captures, treat
Accepted as semantic safety, or overwrite reports. Until that work is accepted,
D07.04 cause reporting and full M05.03/M05.04 remain in progress/unchecked; this
contract/API slice does not finish them. The legal-ID baseline confound and
semantic-grounding policy each require their own explicit follow-up scope.

Author verification for this allocation: current public metadata/claim reads,
existing signature/source review, exact branch/base preservation and Git
whitespace/path/diff checks only. No Node, Cargo, compiler, formatter, tests,
application, model, SDK/assets, phone, desktop control, merge or release.
Handoff is the contract commit/SHA256, proposed interfaces, affected paths and
finite cases to Root. Ownership of this document is released after handoff;
Root records acceptance or amendments before any dependent work.
## Independent FIRST test-source freeze — 2026-10-29

Root accepted the proposed public hook/type/getter/three-code interface after
`5a4bdaa5`; Core production still waits for its retained-native-render gate.
Claims before editing:
[#29 comment6490112979](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6490112979)
and [#9 comment6490113271](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6490113271).
The independent author reuses the released source checkout on NEW
`test/d07-scene-narration-diagnostics` from exact `5a4bdaa5`.

This freeze changes only NEW
`crates/locallore/src/play/scene_narration/diagnostics_review_tests.rs` and this
append. The new child is explicitly test-only and **unregistered**; Root owns
`#[cfg(test)] mod diagnostics_review_tests;` in the parent, missing API setup,
production code, formatting, execution and acceptance. No existing test body,
production path, Cargo file or renderer/native source is changed here.

Ten test functions use the real Domain1 Engine/Play pipeline, a queued recording
synthetic provider, actual generated requests and a real TraceRing-backed sink:

1. Provided default-method implementer, explicit no-op, actual disabled and
   cleared-owner RingSink handles, and mismatched attempt identity preserve
   semantic outcomes/request limits. No synthetic Engine/status/report stub.
2. Actual reached first-person/unapproved-movement branches, a both-predicate
   first-failure case, and accepted real Move control; exactly one reason event
   after the existing stage record, exact fallback and two provider calls.
3. Earlier ordinary dialogue/speaker/event-ID/text failures and actual malformed
   JSON retain generic classification and the earlier Parsing measurement; an
   actual hidden-actor Knowledge refusal keeps its category and no scene code.
4. Valid accepted control and an original unsupported environmental assertion
   both report Accepted/None under the **existing finite semantic limitation**;
   this is characterization, never a new quality or safety approval.
5. Existing stage-record callback cancellation and new-hook cancellation retain
   Cancelled before an independently excluded exact mechanical fallback, with
   actual rejected validation metadata and exact unchanged source bytes.
6. Cancellation after an accepted validation decision prevents commit without
   relabeling that earlier decision; exact unchanged source bytes.
7. Original stage and new diagnostic observer panics disable later callbacks;
   fallback, request/call limits and canonical semantic outcomes remain.
8. One justified private helper case: public Cancellation token APIs cannot count
   predicate polls. An actual source-bound synthetic Memory record is borrowed
   by existing `validate_record` and proposed `validate_record_detailed`, with
   `into_engine_error` preserving the result. The existing Memory source calls
   the cancellation predicate twice for a valid record, once before a finite
   generated-prose refusal, and twice when the final predicate cancels. Each
   separate control invocation has these exact counts; no production validator
   is rerun to infer a reason. Source remains byte-for-byte unchanged.
9. Actual invalid-ability/stale guards, exact recorded retry after cancellation,
   exact replay, and legacy Memory/Literal first-person behavior retain their
   established boundaries. Retry/replay use exact canonical/receipt bytes, not
   normalized copies; absent stages do not fabricate diagnostics.
10. Copy/Eq/fixed-size metadata getters, content-free synthetic-sentinel checks,
    forward-compatible consumer match, exact old PlayRecord/trace-v1 key sets
    and unchanged scene policy/prompt/frame versions. Absence of Serialize and
    public constructors also remains a Root source/API review requirement;
    these unit tests do not claim a negative trait proof.

### Pre-execution timing calibration

Source inspection, before any test execution, shows that actual receipts embed
measured `PlayRecord.stages[].elapsed_ms`. Root accepted the following explicit
parity calibration: across independently executed controls, normalize **only**
those measured elapsed values and compare exact remaining receipt fields,
events/projection/identities and stage names/order/count. Assert actual elapsed
values remain within existing bounds. Compare exact provider prompt/schema/
identity/fixed-cap/count fields, while checking actual remaining deadline values
against their unchanged profile bound; do not equate independent wall-clock
measurements or add a fake clock. No captured record is modified. Same-Engine
cancellation/retry/replay oracles retain exact `canonical_bytes` and receipt
bytes. This is a source-derived fixture design, not a weakened failed assertion.

The private helper case uses the proposed internal name already in this
contract; its API/module visibility absence is setup, not behavior. Core tests
cannot establish native SDK/consent/reservation counts, window retirement,
whole-app rendering or device/model execution. No such evidence is fabricated.

Author checks are source/API/fixture review and Git whitespace/path/hash checks
only. **No Cargo/compiler/test/Node/formatter/app/model/assets/SDK/phone/desktop
execution.** The accepted public types/method and private detailed helper do not
exist on this frozen base. Missing imports/module/API therefore mean
UNCOMPILED/SETUP, never behavioral RED. A filter finding zero tests is not a pass.

After the retained-render gate and Root's independent source review, Root may
register the unchanged child, implement its separate four-file production scope
and run the exact ten-function filter with one test thread, preserving original
setup failures and actual results. Existing scene recipe/legacy/cancellation
and appropriate broad checks remain required. No adapter/Eval/UI reporting,
model rerun, historical report rewriting or full D07/M05 completion follows.
The author hands off the first source commit/hash and releases these two paths;
Root records interface/fixture amendments explicitly before changing them.