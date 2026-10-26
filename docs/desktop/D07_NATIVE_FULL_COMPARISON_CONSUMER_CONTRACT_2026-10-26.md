# Native full-comparison consumer contract

Supporting D07.03/.06/.04 under #29, coordinator claim6425826959.
**FROZEN INTERFACE BEFORE IMPLEMENTATION / IMPLEMENTATION AND CHECKS UNRUN.**
Root reviewed drafts `c6bf05ed`, `d996d641`, `9d0280fd` and `bf316d9b`, resolved
their choices, and promotes them on service implementation base
`84eb739f372be2befe5ddfc1ce82aabcb300287d` (PR214, not yet accepted), with accepted
scripted base `6099135e`. Root owns integration. This freeze itself allocates
neither production/test edits nor execution; those require path-specific claims.

The [service/IPC contract](D07_NATIVE_FULL_COMPARISON_SERVICE_CONTRACT_2026-10-26.md)
owns the native wireV2 and unchanged reader wireV1. Its
[qualification record](D07_NATIVE_FULL_COMPARISON_SERVICE_QUALIFICATION_2026-10-26.md)
owns measured results and pending gates. Service and non-generating IPC/scripted
render evidence do not qualify this new native-model UI or real OS dialogs.
The ordinary frontend remains scripted until this consumer passes its own gates.

## One implementation, immutable transport

Preserve the existing two-argument constructor and its scripted behavior. Add
only a closed constructor option plus a native convenience factory. Frozen
public signatures below are absent at the inspected source:

```ts
type ComparisonRunMode = "scripted_baseline" | "approved_native";
type NativeComparisonRunOptions = Readonly<{ mode: "approved_native" }>;
type NativeComparisonRunState = Omit<ComparisonRunState,
    "status" | "catalog" | "error"> & {
    mode: "approved_native";
    status: NativeComparisonRunStatus | null;
    catalog: NativeComparisonRunCatalog | null;
    error: NativeComparisonRunError | null;
    cleanup: SelectedCleanup | null;
    cleanupPending: "status" | "retry" | null;
    cleanupUncertain: boolean;
    cleanupError: NativeComparisonRunError | null;
};
type ComparisonRunConsumerState =
    | (ComparisonRunState & { mode: "scripted_baseline" })
    | NativeComparisonRunState;

class ComparisonRunController {
    constructor(invoke: ComparisonRunInvoke,
        onError?: (error: ComparisonRunError) => void);
    constructor(invoke: ComparisonRunInvoke,
        onError: ((error: NativeComparisonRunError) => void) | undefined,
        options: NativeComparisonRunOptions);
    readonly mode: ComparisonRunMode;
    get(): Readonly<ComparisonRunConsumerState>;
    subscribe(listener: () => void): () => void;
    setContext(key: string, allowed: boolean): void;
    loadCatalog(): Promise<void>;
    start(kind: ComparisonRunKind, batch: number): Promise<void>;
    lookup(): Promise<void>;
    open(runId: string): Promise<void>;
    status(): Promise<void>;
    resume(batch: number): Promise<void>;
    cancel(): Promise<void>;
    close(): Promise<void>;
    cleanupStatus(): Promise<void>;
    retryCleanup(): Promise<void>;
    dispose(): void;
}
function createNativeComparisonRunController(invoke: ComparisonRunInvoke,
    onError?: (error: NativeComparisonRunError) => void):
    ComparisonRunController;
```

These local state unions use the actual V1/V2 discriminated DTOs, not
new wire fields. Existing V1 type names remain available; the default constructor
signature is unchanged. The native factory selects the required native option.
There is no optional generic type argument that can claim native behavior while
omitting that option, `setLane`, caller-supplied decoder, command or provider.

Inside the controller, copy the closed option once into one of two immutable,
code-owned descriptors. Do not retain a mutable caller options object:

| Descriptor | Command | Decoders |
|---|---|---|
| Scripted /V1 | `evaluation_comparison_run` | Existing exact V1 status/catalog decoders and error set |
| Native /V2 | `evaluation_comparison_native` | New exact V2 status/catalog decoders and bounded native error/cause sets |

Capture that descriptor in every `Owner` alongside its current identities and
in-flight bookkeeping. `ownedCall`, token binding, unknown-ACK lookup, cold-open
catalog recovery, late response and `release` all use **owner.descriptor**.
Neither the visible mode nor a later controller instance can redirect an old
close to the other command. Requests remain `{action, query}` with an object
query and the existing4096-byte compact UTF-8 guard; never send encoded JSON
text in place of the object.

## Strict wire closure and truthful local state

Keep `checkedComparisonRunStatus` / `checkedComparisonRunCatalog` unchanged for
V1. Add `checkedNativeComparisonRunStatus` / `checkedNativeComparisonRunCatalog`
for V2. Reuse private scalar/bounds helpers, not a second parser subsystem and
not conversion of V2 into a fake V1 response.

Native status has exactly the frozen V1 key set with V2/native tags plus required
`cleanup_required`, `cleanup_running`, and nullable `cause`. The two additional
phases and native error categories are accepted only on V2. V2 catalogs retain
the exact existing catalog/metadata keys with native version/lane tags. Reject
mixed tags, wrong lanes, missing required nullables, unknown keys and malformed
categories. Preserve32KiB status/64KiB catalog/32-row and safe-integer bounds.
The exact closed cause set must match the native adapter, using the existing
selected cleanup decoder where applicable; arbitrary diagnostic text is refused.

Completion, report readiness, source matching, execution running and cleanup
remain distinct facts. `awaiting_confirmation` is not proof that a model loaded.
`closed` is not proof that either worker stopped. Current V1 accepts those
independent fields; do not strengthen its decoder with invented correlations.

Retain one UUID allocated before the pending notification for an explicit new
start. An unknown acknowledgement keeps that same client for lookup/status;
it does not automatically repeat start, allocate another run, resume, or change
lane. Recheck captured ownership after synchronous subscriptions, every await
and before dispatch/publication/cleanup, as the existing controller does.

## Cleanup is separate from presentation recovery

Native state has exactly the local fields frozen above; inherited lifecycle
`pending` retains the V1 action shape. Cleanup actions use only `cleanupPending`,
not a forged lifecycle operation/client. Initial `cleanup=null` means **not
checked**, not idle. Initial `cleanupUncertain=false` means no cleanup request
acknowledgement has been lost; it does not turn null into proof of cleanliness.
These are observations of Rust's existing owner, not another runtime registry.
Keep acknowledgement/retired-owner uncertainty separate from global cleanup.

- `cleanupStatus()` and `retryCleanup()` use native actions with empty queries,
  including when `allowed=false`. A valid native window remains mandatory.
  On a scripted instance both methods are no-ops with no IPC or state change.
  Neither action grants inspection or starts/resumes comparison work. Native
  `cleanupPending` is `"status"` or `"retry"` only while that auxiliary request
  is pending; `cleanupError` records only its bounded error and does not replace
  a lifecycle error with a guessed outcome.
- Use a separate `globalAuxEpoch`, distinct from execution serial/context and
  reader-lens epochs. A later auxiliary request supersedes an older reply.
  New admission invalidates older auxiliary presentation replies; it cannot
  cancel an already dispatched native cleanup. Disposal/native-window retirement
  fences publication. Ordinary observer/session eligibility changes do not
  invent a cleanup result or discard the native payload.
- An unknown close response is a presentation-identity recovery problem. An
  exact `UnknownEvaluationRun` can settle that identity when no reply remains
  in flight, but cannot assert global worker cleanup. An actual generic cleanup
  observation must retain its own required/running/unknown status. Conversely,
  generic cleanup success cannot settle an unresolved start identity by itself.
- Do not synthesize `selected_cleanup.running` from native status `running`.
  Native V2 exposes `cleanup_running`; the generic envelope's `running` is a
  separate actual cleanup observation. Retired close must not rewrite a newer
  owner's cleanup flags or present private counts from the retired run.
- Before settling a sent native retired presentation whose close reports
  `running:true`, `cleanup_required:true` or `cleanup_running:true`, or whose
  release returns exact `UnknownEvaluationRun`, obtain
  one bounded read-only `cleanup_status` observation. Install the separate
  auxiliary guard before notifying that the presentation barrier settled.
  Skip unsent/disposed owners. This is neither a timer nor `retry_cleanup`,
  generation, inferred cleanup or an old private-status publication. Fence
  the global reply with its actual auxiliary/window lifetime; a failed read
  retains truthful cleanup uncertainty/error. The real generic payload can
  remain visible outside Lab after the old private run has been cleared.
  A last-known-clear preflight must not be the sole visible observation after
  that actual running/unknown release boundary. Closed/Unknown settles only
  presentation identity; it never manufactures global owner release.
- Extend the completed/cancel/status latch only for the same actual owner and
  operation. Root's frozen decision preserves the existing V1 completed latch
  for late non-cleanup cancel/status, including the old completed phase,
  verified source/completion/counters/readiness and latest non-null error.
  V2 must additionally copy the latest `cleanup_required`, `cleanup_running`,
  `cause` and `running`, including a null latest cause; never lose them by
  spreading only the old status. If the latest phase is `cleanup_required` or
  either latest cleanup flag is true, retain the prior verified completion and
  counters but honor the latest phase and force local `report_ready:false`.
  The unchanged V1 behavior is not generalized to erase a V2 cleanup condition.
  Inspection/generation also remain blocked by local cleanup uncertainty.
  Successful cleanup cannot invent report publication or restore readiness;
  explicit same-run status/lookup observes reconciliation. Ordinary native
  readiness must originate in an actual verified report, never an index/count.
  Retained values are labelled **last verified**. This latch is local
  presentation history, not a canonical rewrite or an untouched wire response.
  Strict wire decoders never manufacture these correlations or merge replies.
- Retry is explicit and bounded by the existing controller/native behavior.
  No automatic cleanup retry, inferred rollback, resume or model reload follows
  a lost acknowledgement. Native Rust still owns all cross-evaluation/model
  exclusion, exact Arc/witness checks and positive cleanup proof.

### Explicit native generation preflight

Every explicit native `start` or `resume` must obtain a fresh read-only generic
`cleanup_status` response before dispatching its generation command, even if the
last observation was clear. This is not `retry_cleanup`, asset access, native
confirmation or inference. There is no timer-based automatic reconciliation.

1. Check actual current context eligibility, current/retired owner uncertainty,
   lifecycle pending work and known cleanup blockers. Known required/running or
   `cleanupUncertain` returns blocked, with no implicit status refresh or cleanup
   retry, until the user explicitly calls `cleanupStatus()` or `retryCleanup()`.
   Metadata lookup/status/recovery do not use this generation guard and remain
   available under their normal grants.
2. Capture the immutable descriptor, execution epoch, original owner and request
   inputs. For a new start allocate its one UUID before the first lifecycle
   pending notification. For resume retain the actual existing client/token.
   Install the guard before notifying subscribers. Cleanup has its own auxiliary
   pending/epoch state and must not pretend a native generation ACK exists.
3. Read generic cleanup with its own `globalAuxEpoch`. Recheck execution context,
   owner, pending action, auxiliary epoch and disposal after every notification
   and await, and immediately before generation dispatch. A stale reply cannot
   admit a run or overwrite newer cleanup data. Ordinary execution-context
   changes cannot forge a clean observation. Manual cleanup reads remain usable
   without Lab permission under their separate valid-window fence.
4. Require a decoded fresh response with no cleanup required/running or error,
   and no local cleanup uncertainty. Otherwise retain truthful cleanup state and
   dispatch no generation. If a new provisional client never reached `start`,
   it is known unsent, not an unknown admitted run; no automatic replacement
   start follows. A failed resume preflight retains its existing run identity.
5. Dispatch the captured start/resume only if all guards still hold. Rust repeats
   actual owner, window, source, quota, confirmation and model-reservation fences.
   A clear preflight is a last native observation, not an enduring global grant.

Read-only preflight itself may publish a pending observation; its native RPC
must not mark the comparison Owner as having sent a generation request. An
unknown cleanup acknowledgement blocks generation through `cleanupUncertain`,
without inventing a comparison operation or rekeying an already sent start.
Do not implement preflight by calling a public helper that returns early merely
because this same admission already installed lifecycle pending/busy. It must
perform its captured read, then recheck that admission. Keep inherited `busy`
about lifecycle/execution; cleanup pending/running/uncertainty are separate
admission guards. They do not disable permitted metadata lookup/status/recovery.

Root resolved the procedure choice: initial null or last-known-
clear state allows explicit start/resume to perform its required fresh read-only
preflight; known required/running/`cleanupUncertain` returns blocked until
explicit cleanup reconciliation. After that reconciliation, a later explicit
generation action still performs another fresh read-only preflight. Neither
decision authorizes execution or implementation by itself; independent frozen
source-oracle packets and explicit path ownership precede production edits.

## Stable instances, App routing and independent inspection

Main may hold exactly two stable controller instances: existing scripted and
native factory-created. This reuses one implementation without adding a JS
job/model owner registry. A mode selector only chooses presentation; it does not
mutate either transport. Keep outstanding work/cleanup visible rather than
silently abandoning the inactive controller.

For an explicit idle mode switch, capture the old instance and a mode-switch
epoch, close its captured presentation, then recheck before changing the visible
mode. Keep unknown close recovery visible and block competing admission until
the presentation barrier is reconciled. An acknowledged closed response is
still not worker cleanup. Never dispose/recreate a controller as a shortcut to
clear uncertainty. Reset only mode-local form/saved-ID selection, for example
with a keyed View; do not carry a scripted saved ID into native open.

The native view reuses the existing form/status/saved-runs layout, with distinct
IDs if both views mount. Preserve the scripted labels. Native copy states that
it requests the approved installed local model, never fake fallback, and that
human quality is not established. Native availability is unknown or explicitly
last reported until Rust admission; `model.imported`/`loaded` and frontend Lab
eligibility are not execution grants. `NativeUnavailable` and
`EvaluationModelBusy` remain honest terminal/admission states.

Show `awaiting_confirmation` as waiting for native confirmation, with no invented
percentage, model-load claim or deadline guarantee. Stop requests may remain
pending until the native dialog returns; do not claim to dismiss it. Retain
generic cleanup refresh/retry controls outside the Lab-only eligibility gate,
without exposing private report data there. This can be a small exported cleanup
view in the same view module, mounted independently by App.

Keep the existing Root-owned execution key: actual window/root, permission,
selected live story/scope/head, surface and disposal. **Exclude observer,
inspector controls, active mode, model status, busy and cleanup observations.**
Those changes must not rekey/cancel generation. Actual session/root retirement
still fences private publication and releases only captured capabilities.

Proposed reader extension:

```ts
type ManagedComparisonIdentity = Readonly<{
    runId: string; mode: "scripted_baseline" | "approved_native";
}>;
// Existing pick() and pick(runId) retain their scripted behavior.
pickManaged(source: ManagedComparisonIdentity): Promise<void>;
```

Only the initial `managed` dispatch chooses the scripted or native command;
scripted `pick(runId)` and scripted `pickManaged` retain the existing
`evaluation_comparison` command with action `managed`. Native `pickManaged`
uses `evaluation_comparison_native` with action `managed`. The execution
descriptor's `evaluation_comparison_run` command has no `managed` action and
must never be used for this reader entry.
both use the frozen `{clientId,runId}` query. Returned reader wireV1 then uses
the existing `evaluation_comparison` status/source/summary/evidence/close paths.
Execution tokens are never reader tokens and completion never auto-opens a
private report. App's Inspect callback captures mode/controller/context/run
identity AND the separate reader context, allowed state and observer before
awaiting reader close and rechecks them afterward. An observer/lens retirement
must not be bypassed by re-admitting from an older held callback. It must not
read a new active mode and route an old native run through scripted managed.
Held reader replies remain fenced by the existing context/lens/request epochs;
actor raw refusal precedes dispatch, and observer changes clear private bodies
without cancelling the comparison.

Semantic frames retain actual selected-live `selectedStory`, observer and
revision together. Report scope/head/lens belong in separate `inspectedStory`,
`inspectedRevision`, `inspectedObserver` and reader metadata. Pending identifiers
come from the actual controller/native acknowledgement, or remain explicitly
unknown; a receipt from an isolated experiment cannot supply the live header's
revision. No whole canonical history is reconstructed in JavaScript.

## Frozen oracle and qualification slice

Scoped production paths are the existing comparison-run model/controller/view,
reader controller managed-entry seam and Root App/Main wiring. Freeze these
**NEW** checkers before any production consumer edits:

- `apps/desktop/check-comparison-run-native.mjs`: strict V2 DTO, actual shared
  controller/mock transport, native preflight/cleanup and View headless cases.
- `apps/desktop/check-main-comparison-run-native.mjs`: actual application
  mode/Inspect/context callbacks with bounded test-only module substitutions,
  using existing esbuild/React patterns; no source-string predicate checks or
  production debugging/execution hook.
- `apps/desktop/check-comparison-reader-native.mjs`: actual existing reader
  controller with mocked transport, native managed-entry routing, unchanged
  readerV1 subsequent calls, held reply/epoch and actor raw-refusal boundaries.

Root still owns path allocation. Existing
`apps/desktop/check-comparison-run.mjs` and its56 cases remain unchanged. API
absence/compile refusal must remain distinct from actual behavior RED. Freeze:

1. Original56 scripted mock/SSR checks unchanged; separate V2 exact shape,
   required-nullable, category, bounds and mixed-lane negatives.
2. Actual controller start/status/retired-close endpoint logs, including held
   replies after mode/context switches and synchronous subscriber reentrancy.
   Unknown ACK keeps one original client; no automatic start/resume/fallback.
3. Initial null cleanup cannot assume idle; explicit native start/resume sends
   fresh read-only cleanup preflight before generation and rechecks reentrant
   guards. A failed/held/stale preflight sends no generation. Known blockers,
   retired close unknown versus actual cleanup-required/running/unknown;
   cleanup with `allowed=false`; late auxiliary replies and completion/cancel
   latches cannot clear a newer owner or discard V2 cleanup cause.
4. Native managed initial routing with unchanged readerV1 subsequent calls;
   held inspect callback/mode change, independent denial and observer/private
   reply fencing. Current scripted `pick(runId)` compatibility remains exact.
5. Actual View headless wording and control states for scripted, native unknown
   availability, awaiting confirmation, cleanup required, unavailable model,
   saved native metadata and last verified report counts. Headless/mock evidence
   is explicitly labelled and is not native IPC/render/model evidence.

The first new checker must log exact action/object-query sequences for both
`start` and `resume`: initial-null and last-known-clear state perform
`cleanup_status` before generation; known required/running/cleanup-unknown state
performs neither generation nor implicit auxiliary IPC. Explicit reconciliation
then a new explicit generation action produces a second fresh status preflight,
never `retry_cleanup` automatically. A held preflight retired by synchronous
notification/context change must issue zero generation calls. Unsent provisional
UUIDs and actual admitted unknown-ACK clients must remain distinguishable.

Freeze auxiliary cases for older false replies held across newer required/running
observations, admission and disposal. Check exact `cleanupPending`,
`cleanupUncertain`, `cleanupError`, unchanged inherited lifecycle pending, and
empty native cleanup query objects. Metadata status/lookup under a cleanup block
still use the captured native endpoint. A generic cleanup success issues no
generation/open/read and cannot restore report readiness or clear an unresolved
comparison acknowledgement.

Freeze separate latch cases: same-operation completed followed by non-cleanup
paused/failed cancel/status retains the V1 completed/source-verified counts and
latest non-null error; V2 always copies latest cleanup flags/cause/running.
A latest cleanup-required phase, required flag or running flag retains verified
completion/counters but honors latest phase with local readiness false. DTO
decoding itself remains strict and unmerged; these assertions concern the actual
controller's local presentation history. No new source counts, source-matching
proof or readiness may come from catalog metadata or auxiliary cleanup success.

After service eligibility and consumer source freeze, Root separately allocates
strict frontend/type checks, scripted compatibility, actual application-owned
native action/IPC/WebView captures and all-image inspection. Fixed consent/ACK
doubles establish plumbing only. Approved installed-model UI/service invocations,
real OS-dialog behavior and quality need their own bounded admission/provenance;
no extra invocation is authorized by this contract. Keep source matching,
current/historical runs and retained failures explicit. No desktop control,
OS screenshots, provider replacement, model download or phone gate is proposed.

## Type and reentrancy source audit and frozen constraints

A source-only caller audit at `d9fd9443` found `ComparisonRunState` references
only within its controller. App, View and the scripted journey accept the class
and consume common fields. Main's callback is inferred as
`code => errors.add("native", code)`. The existing56 checker verifies exact
wire/query DTOs and individual controller fields, not the complete local-state
key set. These observations are not a TypeScript or checker execution.

Recommend the nongeneric class and overloads above. Add literal
`mode:"scripted_baseline"` to the actual default instance's frozen state;
the native state carries `mode:"approved_native"`. `get()` returns the union.
Keep the old exported `ComparisonRunState` alias and all old model types/checker
signatures V1-only. Native state uses the actual V2 status/catalog types and
its own cleanup fields. A future explicit assignment of an un-narrowed `get()`
result to `ComparisonRunState` would need a `state.mode` guard; no such caller
was found in this source. It must not be repaired by pretending V2 is V1.

View can continue using common fields; native-only accesses narrow
`state.mode` or `status.version`. The separate class `mode` property does not
by itself narrow a previously fetched state. Preserve the state discriminator
through every patch and refuse cross-descriptor DTOs before publication. Do not
make mode patchable or use a broad state cast to bypass that invariant. Existing
scripted journey wiring continues to receive the default instance and retains
its explicit V1 native command/decoder calls; it is not a native-model journey.

The narrow callback overloads need deliberate implementation normalization.
Do not store a union of callback types and invoke it with a native-wide error,
or cast a legacy callback to a native one. A correlated constructor rest tuple
allows the callback and required native option to narrow together:

```ts
type ComparisonRunConstructorArgs =
    | [invoke: ComparisonRunInvoke,
       onError?: (error: ComparisonRunError) => void]
    | [invoke: ComparisonRunInvoke,
       onError: ((error: NativeComparisonRunError) => void) | undefined,
       options: NativeComparisonRunOptions];
// Implementation signature behind the public overloads:
constructor(...args: ComparisonRunConstructorArgs);
```

In the `args.length === 3` branch, choose the closed native descriptor once,
capture that branch's native callback, and install a private wide reporter
which categorizes through the native descriptor before invoking it. The other
branch captures the legacy callback and categorizes through the unchanged V1
set. This keeps both public callback contracts intact without callback casts,
`any`, a public generic or a fake protocol conversion. The factory calls the
required three-argument overload. Compiler verification remains a future gate.

Before a mode-switch handler notifies React/subscribers or awaits anything,
install its switch epoch/in-progress guard and capture old instance, requested
mode and actual execution context. Reentrant handlers must not start a second
switch. After close, recheck all of those identities immediately before changing
presentation. Likewise, an Inspect handler must capture the originating instance
and mode rather than consult active mode after awaiting reader closure.

For the first consumer slice, disable explicit mode switching/new admission
while either stable instance has pending/active work, acknowledgement uncertainty
or known cleanup activity/uncertainty. Keep close, exact identity lookup and
generic cleanup usable. A closed response with `running:true` leaves running
work visible; exact same-client read-only recovery can observe its drain. It is
not a reason to enable another start or silently hide the old operation. A
context change may retire presentation independently, but native cleanup remains
visible outside that presentation. Neither the UI guard nor a prior false
cleanup observation proves that every other model/evaluation owner is absent.

Do not translate blocked admission into `setContext(..., false)`: that would
retire the operation which produced its own busy/cleanup state. Eligibility,
execution identity and admission guards remain separate. A global auxiliary
reply cannot clear a newer native status's cleanup requirement; actual owner
status and generic cleanup observations remain separately labelled until fresh
Rust status reconciles them. No callback, mode change or cleanup action grants
inspection, automatically resumes inference or supplies a model-ready promise.

## Closed export and integration names

The model exports `NativeComparisonRunMetadata`, `NativeComparisonRunCatalog`,
`NativeComparisonRunStatus`, `NativeComparisonRunError`, and the two native
checkers named above. `nativeComparisonRunErrors` extends the unchanged V1
`comparisonRunErrors` with exactly `EvaluationModelBusy` and `Cleanup`. Native
status `error` and nullable `cause` use that closed native set; local
`ComparisonRunWire` remains a consumer error, not a native wire cause. Strict
wire bounds and fields come from the frozen service contract, including the two
additional phases `awaiting_confirmation` and `cleanup_required`.

Keep `ComparisonRunView({controller, onInspect})` and its `(runId:string)`
callback intact. Add optional `admissionAllowed:()=>boolean`, defaulttrue,
as a presentation guard supplied by App from BOTH stable controllers. Recheck
it at render and immediately in retained Start/Resume handlers; it neither
grants native authority nor disables metadata/close/cleanup recovery. Do not
use execution eligibility/context mutation to implement this guard.
Add `ComparisonRunCleanupView({controller})` in the same view
module; it renders only for the native instance and remains usable outside Lab.
The native run section ID is `comparison-run-native`; the existing scripted
section keeps `comparison-run`. App retains optional `comparisonRun` and adds
optional `nativeComparisonRun`, both stable controller instances supplied by
Main. The mode selector's accessible name is `Full comparison inference lane`.
The selected mode changes only presentation. Root owns App/Main wiring, mode
reentrancy and independent reader routing; no agent may infer a new grant from
these props or mutate the execution context from its own busy/cleanup state.

The frozen API is a small extension to the existing implementation. There is no
second controller implementation, provider, engine, SQL writer or model-owner
registry. New native methods on the existing class do not grant cleanup or
inspection authority; Rust validates every call again.
