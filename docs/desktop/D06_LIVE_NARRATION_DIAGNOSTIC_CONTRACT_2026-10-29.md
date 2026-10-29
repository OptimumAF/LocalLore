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
