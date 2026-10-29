# D06 live selected-attempt narration diagnostic proposal

2026-10-29. **Proposed, source-only; not an accepted API or runtime qualification.**
Refs #28 D06.03/D06.07, allocation [6504003520](https://github.com/OptimumAF/LocalLore/issues/28#issuecomment-6504003520).
Inspected source: `54603e31281b23010e040e3eab002fa0a260fef0`, including accepted main.
This document is separate from the comparison-reader PR. Root must accept the
interfaces and freeze independent FIRST tests before production edits.

## Bounded purpose and existing interfaces

Add an explicit read of the retained narration validation decision for the live
debugger's selected original player attempt. Display actual recorded metadata or
honest absence/refusal. Do not infer a cause from the transcript or final receipt.
This is a small supporting slice; it does not complete D06's contextual explanation,
raw proposal/diff, memory-maintenance, real-model or full exit gates.

Source anchors below are relative to the inspected commit, not moving `main`:

| Existing seam | Source and consequence |
| --- | --- |
| Validated trace and selected attempt | `apps/desktop/ui/controller.ts:919`, `:969`, `:1057`, `:1065`; `ui/trace-model.ts:141`, `:198`. The trace binds scope/current head/base/lens and original player identity. Existing trace refresh can select its last returned attempt; the new action cannot independently select latest. |
| Head reconciliation and current UI gap | `ui/controller.ts:791`, `:828`; `ui/App.tsx:466`. Thin/scene routes currently clear V1 play and disable this debugger, although the existing thin snapshot and Host metadata operations supply the required identity. |
| Context and teardown | `ui/controller.ts:734`, `:908`, `:1618`, `:1638`, `:2159`. Trace clearing, session/view/lens/head transitions and disposal already invalidate private presentation. |
| Existing render and receipt boundary | `ui/TurnDebugger.tsx:8`; `ui/controller.ts:1073`. Stage outcome and final accepted evidence are separate; the existing receipt helper is Play-only. |
| Existing typed request | `ui/host.generated.ts:172`; `crates/locallore/src/host.rs:232`. No request/schema generation change is needed. |
| Native permission and exact lookup | `crates/locallore/src/host.rs:1078`, `:1253`, `:1291`. The native Story Lab guard precedes Host state/admission probes; authorized lookup validates current head, converts attempt, then uses the existing exact Core selector. |
| Transport boundary | `apps/desktop/src-tauri/src/main.rs:73`, `:115`; `ui/model.ts:338`. Existing `host_call` uses the window lease, can initialize workspace before Host admission, and the frontend gateway returns Host data after checking the envelope. |
| Finite frontend decision codec | `ui/comparison-reader-model.ts:1356`, `:1524`, `:1551`. Its closed tuple rules already cover this Host metadata inside stored comparison observations; reuse their semantics without importing historical artifact authority. |
| Thin/Domain2 identity and actual boundary | `ui/v2-view-model.ts:36`; `crates/locallore/src/host.rs:1420`, `:1949`. PlaySnapshotV2 supplies scope/revision/player; both trace reads use the generic Engine/player. Legacy Inspect alone has an explicit Domain2 refusal at `host.rs:1903`; literal scene generation has its separate restriction at `:2586`. |

Paths beginning `ui/` in this table are under `apps/desktop/`.

## Proposed frontend API and ownership

Reuse `Gateway.call(Command)` / native `host_call`; add no Tauri command, capability,
grant setter, worker, store, arbitrary inspection selector or new Host operation.
Use the already-generated request type:

```ts
type NarrationValidationQueryV1 = Extract<Command, {
    op: "trace_narration_validation_read_v1"
}>;
```

Proposed narrow shared frontend module: `ui/narration-diagnostic-model.ts` exports
`NarrationValidationQueryV1`, the closed decision/data types, and:

```ts
checkedNarrationValidationDecisionV1(value: unknown): NarrationValidationDecisionV1;
checkedNarrationValidationDataV1(value: unknown, query: NarrationValidationQueryV1):
    NarrationValidationDataV1;
```

Extract the existing finite decision predicate for both the comparison decoder and
live decoder. Keep comparison-specific envelope, artifact/hash/source checks,
8-KiB response bound, statuses and public reader APIs unchanged. This is a frontend
codec reuse proposal, not a new validator or a shared Rust/Host change. Existing
trace-v1 decoder/response remains unchanged. Independent compatibility tests must
show extraction preserves all existing decision acceptance/rejection cases.

Proposed controller methods: `readTraceNarrationValidation()` and
`cancelTraceNarrationValidation()`. Add a separate typed substate under the existing
trace state: `status` (`idle`, `pending`, `recorded`, `unavailable`, `refused`,
`cancelled`), `query` (nullable exact latch), `reply` (nullable checked Host data),
and `error` (nullable existing sanitized category). No serialized persistence.
An internal monotonic read ticket is display-lifecycle ownership, not engine authority.

Later proposed production paths are the new codec, `ui/trace-model.ts`,
`ui/controller.ts`, `ui/TurnDebugger.tsx`, `ui/App.tsx`, and the narrow existing comparison codec
call site. Tests and a fixed development-only native harness allocation are separate.
Root must approve exact ownership first. No Core/Host/schema/native transport changes
are currently required; return any newly demonstrated prerequisite for review.

## Exact live selection and admission

Before dispatch, require an undisposed controller, shown debugger, acknowledged
Story Lab view with omniscient lens, a selected session and validated current play
snapshot, no trace read/control pending, and no live gameplay
operation or unresolved submission. Otherwise clear the diagnostic and show the
specific local unavailable condition; dispatch nothing.

Resolve the selected attempt only from the current checked trace reply and selected
key. Require that reply's scope/head/base/lens still equal the current trace query,
and the attempt's scope/base/observer equal that tuple and actual snapshot player. Do not
reconstruct identity from receipts, guessed turn numbers or an absent trace.
Validate safe nonnegative integer revisions and attempt within native u32, existing
bounded ID rules and exact scope/session before constructing the request.

Use a narrow trace-only context from validated `state.play ?? state.playV2`:
session ID, matching scope, safe revision and actual player observer. V2 transport
version is not domain version; its supported `domain_version:1|2` is not a reason to
invent an unsupported Host trace limitation. No shared identity field is missing.
If neither snapshot is valid/current, no trace identity or diagnostic is inferred.

The minimal prerequisite frontend adjustment admits that context in existing trace
read/configure/clear guards, checkedTrace's player argument, base input bounds and
current-head display. Enable only the existing Turn debugger button for a valid thin
snapshot; keep Memory/evidence and snapshot-export controls' existing restrictions.
On thin refresh, reconcile head and synchronously retire old diagnostic/trace data
when changed; preserve the user's trace visibility/base selection where valid and
use the existing optional trace refresh, rather than clearing the debugger solely
because `play` is null. No automatic diagnostic read. Existing V1 behavior stays
covered; thin metadata does not acquire receipts or enable legacy Inspect.
Audit disposition: the preliminary V1-only restriction was rejected before this
proposal freeze because the actual thin snapshot/Host provide the required identity.
This admits existing metadata support; it does not promise unsupported Domain2 play.

Latch `{session, scope, expected_head: snapshot.revision, base_revision:
attempt.identity.base_revision, turn: attempt.identity.turn, attempt:
attempt.identity.attempt}`. The **current head** is independent of the attempt base.
For an attempt prepared at r4 and committed at r5, read with expected_head=5,
base_revision=4. If current gameplay later reaches r6, reconcile a fresh trace/head
first and explicitly read at 6. Never reuse the Eval companion's precommit-head
harvest assumption, change base to current head, or retry a stale query automatically.

No frontend native-grant snapshot currently exists in this controller. Lab/Omni
admission limits UI access; it does not create native authority. The existing Host
`story_lab` grant remains authoritative and may return Forbidden. Tests must exercise
that refusal, not inject a frontend grant that bypasses it. Host early denial is
zero Host StoragePort/admission/lifecycle probes; `WorkspaceState::get` may already
initialize workspace, so this is not transport-wide zero filesystem activity.
Preserve Host parse/version and exact session/scope/storage/head error precedence;
checked u32 attempt conversion precedes selector validation. Authorized existing
NotFound reconciliation may retire/cancel an invalid attachment. Do not promise the
whole Host call has no lifecycle side effects, or bypass that reconciliation. No new
canonical, trace-configuration, attempt, provider or knowledge mutation is introduced.

## Closed Host data and meaning

Accept only the existing version-1 data shape with common fields:
`version`, `session`, `scope`, `head`, `base_revision`, `turn`, `attempt`,
`observer:"player"`, `generation_grant:false`, and `status`.
All binding fields must equal the latched request; `head` equals expected_head.
`status:"unavailable"` has no decision key. `status:"recorded"` requires exactly
`decision:{version:1,outcome,error,reason}` with required nullable fields.

Preserve the existing finite 25 decision tuples: accepted/null/null;
cancelled/cancelled/null; stale/stale/null; rejected/narration with one of
unclassified, scene_first_person, scene_unapproved_movement; or rejected with one
of the existing 19 other error categories and null reason. Never widen this list
from future Core variants. Unsupported or malformed frontend data is Wire/refused;
do not convert it into unavailable or unclassified. Native unsupported metadata
already projects to the actual Host unavailable response.

Reuse descriptor-based bounded detachment/closed-key checks: reject getters without
invoking them, symbols, custom prototypes, inherited/extra/missing fields, unsafe
numbers, foreign tuples and oversized values. Plain and null-prototype JSON records
may be supported consistently with the accepted shared codec. Do not stringify raw
objects before detachment or claim parsed objects detect duplicate wire JSON keys.
Rust enforces **4096 total envelope bytes**, including rejection, without truncation.
The gateway has stripped that envelope; the live decoder additionally bounds detached
data to 4096 bytes and cannot claim it independently measured the total envelope.

Unavailable means the exact optional retained metadata is unavailable, including
disabled/evicted/busy/poisoned/unfinished conditions the API does not distinguish.
Do not assign a specific cause. Host refusal uses the existing gateway/category
projection; unknown categories remain Transport, including categories not in the
current gateway allowlist. No raw exception text or new global error policy.

Recorded outcome concerns that validator decision. Accepted may later cancel;
rejected may commit mechanical fallback. It does not prove final commit, canonical
effects, privacy, semantic grounding, quality, authenticated origin or generation
permission. Keep existing stage outcome/receipt display separate, and do not broaden
the Play-only receipt helper to manufacture canonical evidence in Lab.

## Pending, cancellation and stale completion

An explicit read clears prior diagnostic synchronously and dispatches once. Repeated
read while pending dispatches nothing. Rendering, trace refresh, attempt selection,
observer changes and unrelated updates never start diagnostic reads automatically.
Recorded/unavailable/refused completion publishes only if the read ticket and entire
latched tuple still match current supported context and selected checked attempt.

Changing session/scope/head/base/attempt/view/lens, closing/refreshing the trace,
trace enable/disable/clear, starting/retrying/cancelling gameplay, entering an
unsupported route, or disposal clears the reply/error and retires the ticket before
any asynchronous work. Existing context reconciliation and gameplay behavior remain
unchanged. Re-reading the same tuple is an explicit user action after settlement.

Local cancel retires the display ticket, clears content and labels cancellation;
it does not cancel a turn, clear/disable traces, kill a worker or claim native abort.
The already-issued passive Host call may finish and must be observed without late
publication/unhandled rejection. Existing native window lease rejects retired windows.
No new polling, deadline reset, provider request or automatic retry. Pending is an
outstanding metadata read, not model execution or proof a validator has run.

## Display and independent gates before implementation

Use an explicit “Read selected narration validation” action in the eligible debugger.
Keep artifact-local context visible before details: story/branch, current head,
original base, turn/attempt, original player observer, and no generation grant.
For thin/Domain2 snapshots, label canonical receipt comparison unavailable through
this debugger; do not call the legacy Inspect path or guess an accepted receipt.
Label pending, locally cancelled, recorded, unavailable and refused distinctly.
Show finite decision/error/reason verbatim as metadata codes with plain explanations;
do not label them the final turn failure or repair historical absent causes.

Independent FIRST tests must freeze at least:

1. Shared codec's complete finite tuple matrix, exact binds/current-head versus base,
   closed keys/types/caps, unsafe integers, hostile descriptors/prototypes/symbols,
   unsupported versions and no getter invocation; unchanged comparison decoder and
   old trace behavior. Impossible valid-envelope overflow is source coverage, not a
   fabricated runtime negative using an arbitrary payload seam.
2. Actual controller with synthetic Gateway replies: exact selected nonlatest attempt,
   committed current-head query, no selector when absent/foreign/unsupported; duplicate
   click, explicit local cancel, delayed success/error across every lifecycle boundary,
   synchronous content clearing, no auto-read/retry and unchanged gameplay call counts.
3. Actual Host/Core scripted gameplay: collection on/off canonical receipts/state
   equal, actual recorded decision and honest absence; early Forbidden, current-head
   Stale, exact owner/session/attempt isolation and no new trace configuration/provider
   calls. Trusted metadata controls cover otherwise unconstructible finite cases and
   stay labeled controls. Do not alter production rules to manufacture a reason.
   Exercise actual Domain2 TraceRead/current-head/player identity through existing
   APIs, with empty/available/refused framing as constructible. Do not seed private
   controller state or run unsupported generation to force a diagnostic result.
4. Actual TurnDebugger rendering with the real controller: local tuple/status/error,
   separate stage/canonical evidence, Play/character/unsupported privacy and no dispatch
   during render. SSR/static HTML is not pixel/native-WebView qualification.
5. A separately accepted fixed scripted native journey through mounted controls,
   controller and existing host_call: recorded/unavailable/refusal, stale reconciliation,
   selected-attempt/session/observer switches, pending/local cancel/late completion and
   window retirement. Capture bounded app-owned semantic state/errors and WebView images;
   inspect all images and artifact-local context/geometry. No desktop control or model
   import/load or real inference; measure only the scripted pipeline actually exercised.

Missing APIs, registrations or fixture setup are setup/unrun, not behavioral RED.
Preserve all original negative evidence; Root owns serialized execution, independent
review and the focused PR gate. This proposal performs none of these checks.

No new persistence, inference, validation rules, trace-v1/capture wire, Eval artifact,
catalog, export, character knowledge or generation access. No historical cause backfill,
new real assets/cohort, SDK/device/OS probe or D09 promotion. Both retained human quality
reviews remain “needs improvement”; this display slice cannot change that verdict.

## Independent review precision — proposed amendment before acceptance

The original 234-line proposal above is preserved. These clarifications supersede
any conflicting inference from it; all remain proposed and unrun.

### Caller-specific shared-codec errors

At this source, `ui/comparison-reader-controller.ts:75` recognizes malformed data as
`ComparisonReaderWire`; a bare `Wire` otherwise becomes `EvaluationIo`. Extraction
must not change that policy or the existing 156 reader/error-category oracles.
Freeze the shared helper's finite malformed-input failure as `Error("Wire")`.
The live decoder retains that Wire category. The comparison model's narrow call-site
adapter maps that shared Wire failure to `Error("ComparisonReaderWire")` before it
can reach the existing reader controller. Keep other existing reader/native error
handling unchanged. Do not route all reader errors through the live category helper.
Independent FIRST must exercise malformed decision data through both real controller
call paths and assert the exact distinct visible categories, not just decoder throws.

### Actual thin-view mount and context display

`ui/App.tsx:831` selects the V2 branch before the branch containing TurnDebugger at
`:849`. Enabling its toolbar button alone cannot display it. The proposed App change
must explicitly mount **only TurnDebugger's metadata surface** inside the validated
thin/V2 branch, using the same Controller/State props and shown-state behavior.
Do not mount CapturePanel, legacy InspectionPanel/QueryInspector, receipt comparison,
timeline navigation, export, maintenance or generation controls through that change.
The existing supported V2 Play panel remains its own surface.

Use the validated trace-only `play ?? playV2` source for the debugger's actual-head
label, base-input bound and stale-context banner. Show the latched read head and
current head distinctly if stale; clear old decision data before showing the banner.
Missing/changed source is unavailable, not head zero. Preserve the thin-view notice
for still-unsupported surfaces, updating only its claim that all debugger metadata is
unavailable. Mounted App FIRST must prove the debugger appears for a real checked thin
snapshot and that those other surfaces remain excluded. Metadata inspection must
never change a character's knowledge, prompt eligibility or generation identity.

### Main-owned read-only V2 lifecycle fence

Add `ui/main.tsx` to the **future proposed frontend ownership**, alongside the earlier
paths. Root acceptance and separate production allocation are still required.
No `v2-play-controller.ts` change is presently needed: its public `get/subscribe`
at `:451–461` notify synchronously. `start()` at `:1096` installs its operation and
queues drive in a Promise microtask, then synchronously patches pending. Both initial
send and nonterminal retryExact use it. `cancel()` at `:1224` synchronously patches
cancelling/uncertain before its first possible native control. Terminal/no-operation
returns perform no native cancellation. Thus the existing subscriber can retire the
diagnostic before those native admissions; a React effect cannot provide that fence.

Proposed Controller adapter (presentation lifecycle only):

```ts
setTraceGameplayFence(value: Readonly<{
    session: string; story: string; branch: string;
    head: number; player: string; pending: boolean; uncertain: boolean;
}> | null): void;
```

Main derives only these primitives from the selected session, validated Root snapshot
and the existing public V2 pending/uncertain state. No operation/request object,
native grant, provider/configuration, callback or arbitrary field selector crosses
the seam. The Controller validates primitive shapes and exact equality against its
current selected snapshot; absent/malformed/mismatched/null is fail-closed. Root's
own pending/unresolved checks still apply. Any V2 pending or uncertain operation
blocks new diagnostic reads, including a retained operation from a different selection.
Never infer quiescence from an empty active/pending slot while uncertain is retained.

Keep a detached primitive tuple, not a mutable V2 state reference. A changed tuple or
entry into blocked/absent state synchronously retires the read ticket and clears its
reply/error. Equal tuples are no-ops, preventing subscriber reentrancy loops and
avoiding diagnostic invalidation for unrelated draft/render notifications. Unblocking
does not reread. This is not a source of canonical state or an authorization grant.

Extend actual Main source synchronization, not duplicated test-only glue:

- In the existing Root subscription/context synchronization (`main.tsx:478`), update
  this fence with the current validated snapshot and public V2 busy state before
  returning. Keep normal Root context/head invalidation in the Controller as well.
- Extend the existing V2 subscription (`:588`), which currently only updates Author,
  to synchronously update this fence before returning from V2's notification. Preserve
  the Author synchronization. The fence callback must not call V2 context setters,
  native methods, cancel, trace control or gameplay refresh.
- Subscriptions do not deliver an initial value. Perform one explicit initial sync
  after wiring and before exposing the read action; no initial sync means no admission.
  On Main disposal (`:660`), retire/set the fence null synchronously **before** removing
  either subscription or awaiting V2 disposal. V2 dispose clears listeners without a
  final notification (`v2-play-controller.ts:1255`); relying on it is insufficient.

Independent FIRST must execute this actual Main wiring with real public Controller
and V2PlayController instances plus a fixed synthetic Gateway. Observe cleared state
inside the first native-call stub for send, nonterminal retry and submitted cancel;
verify uncertain-only blocking, initial sync, source/session/head changes, disposal,
equal-tuple no-op and no added gameplay calls. Include a nonliteral player ID from an
actual checked thin snapshot and a selected checked trace; never seed private fields.
Keep V2's Play-only send/retry admission intact. Calibrate Main's independent blocking
with a genuinely pending/uncertain public V2 operation and a later otherwise-eligible
Lab diagnostic attempt; an already-empty reply alone does not prove this new fence.
Deferred native replies after retirement must not refill the debugger. Source review
of Promise ordering alone is not a runtime pass. If the real Main setup cannot be
constructed with existing finite harness facilities, report the missing setup for
allocation before adding a hook; do not substitute a copied subscriber implementation.

These refinements add no native permission or gameplay cancellation path. The earlier
independent Host/Core, strict codec, mounted UI, scripted native and nonmutation gates
remain required. No production, test, schema, runtime or acceptance result is added by
this document amendment.

## Root accepted frontend contract v1 — 2026-10-29

Root accepts the proposal and precision above, with these final public names
and lifecycle rules. Inspected/accepted production base is merged main
`f4d2de0cb25fcc8dc2db48558fb489701f251fd8`; its production source is identical to
the inspected `54603e31`. Original 234-line proposal and 107-line precision are
retained unchanged. This acceptance authorizes independent FIRST source only;
it is not an implemented API, runtime pass, Host/schema change or full D06 gate.

`TraceState.narrationValidation` is the sole new public nested read state.
Export `TraceNarrationValidationState` from `trace-model.ts`, with exactly:

```ts
type TraceNarrationValidationState = Readonly<{
    status: "idle" | "pending" | "recorded" | "unavailable" | "refused" | "cancelled";
    query: NarrationValidationQueryV1 | null;
    reply: NarrationValidationDataV1 | null;
    error: string | null; // Existing sanitized category only; never raw exceptions.
}>;
```

Initial/reset state is idle with query/reply/error null. A locally ineligible
explicit read clears private content and settles unavailable without a query,
reply or invented Host cause. Native unavailable instead retains its exact
query and checked unavailable data. Refused retains only a still-current query
and sanitized error. Recorded means checked Host metadata, including a recorded
cancelled/stale validation decision; it is not local display cancellation.
Store detached immutable query/data copies, with no reference to mutable caller
or notification inputs. The private pending latch includes the original player
identity as well as the exact generated command.

The parameterless, side-effect-free public UI helper is:

```ts
type TraceNarrationValidationEligibility = Readonly<{
    allowed: boolean;
    reason: "disposed" | "hidden" | "not_story_lab" | "not_omniscient"
        | "source_unavailable" | "fence_unavailable" | "gameplay_unresolved"
        | "busy" | "trace_unavailable" | "selection_unavailable"
        | "context_changed" | null;
}>;
traceNarrationValidationEligibility(): TraceNarrationValidationEligibility;
readTraceNarrationValidation(): Promise<void>;
cancelTraceNarrationValidation(): void;
```

Export that eligibility type from `trace-model.ts`. `allowed:true` requires
reason null; `allowed:false` requires one listed reason. Evaluate reasons in
the listed order. These are known local presentation/admission conditions,
not a native grant snapshot or an explanation of Host unavailability. UI may
derive its disabled state and local explanation from this single helper;
rendering the helper never dispatches. Admission repeats authoritative context
checks; a previous UI eligibility value is not a reusable authorization.

Keep the Main-owned primitive fence private to the Controller. A changed
detached fence is assigned before notifying subscribers. It must notify even
if the previous diagnostic payload was already idle, so actual button state
updates. Compare equal tuples before notification, preserving the no-op rule
and avoiding Main/Root subscription cycles. Null/malformed/foreign fence is
fail-closed. No public top-level State/native authority field is added.

An explicit duplicate read while this read is pending is a no-op **before**
clearing or incrementing the ticket; it preserves the original pending request.
Publish pending/cleared state synchronously, then recheck liveness and the
complete eligible context before the gateway call: a synchronous subscriber can
change selection, lens, source, fence or dispose during that notification.
Do not dispatch the retired query. Completion checks may ignore **only** their
own pending-read status; all real metadata/control/gameplay/fence gates still
apply. Never use a broad busy bypass to publish a stale result.

Local cancel acts only on an outstanding pending read. It retires the ticket,
clears query/reply/error, and labels cancelled. Otherwise it is a no-op. Observe
the already-issued promise after cancellation without publication or unhandled
rejection. No gameplay Cancel, metadata clear/disable, worker abort or native
cancellation is implied. Context/lifecycle invalidation resets the read to idle.

No production paths are allocated by this append. FIRST owns new test sources
only, must use real public Controller/Main/V2/Host paths where claimed, preserve
the existing reader/trace oracles, and report missing construction as setup.
Subscriber assertions must not disappear into notification exception handling;
capture observations and assert them outside the callback. Independent native
harness scope and exact production ownership follow a separate Root allocation.
