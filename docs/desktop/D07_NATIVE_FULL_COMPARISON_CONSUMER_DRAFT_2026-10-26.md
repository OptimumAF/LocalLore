# Native full-comparison consumer draft

Supporting D07.03/.06/.04 under #29, coordinator claim6425826959.
**PROPOSED / NOT FROZEN / NOT IMPLEMENTED / UNRUN.** Source inspected:
`d9fd9443e86a290dc41a725e2e0aaf61e7a508b1`, with accepted scripted base
`6099135e`. Root owns interface decisions, future allocation and integration.
This document allocates no UI/test code and authorizes no execution.

The [service/IPC contract](D07_NATIVE_FULL_COMPARISON_SERVICE_CONTRACT_2026-10-26.md)
owns the native wireV2 and unchanged reader wireV1. Its
[qualification record](D07_NATIVE_FULL_COMPARISON_SERVICE_QUALIFICATION_2026-10-26.md)
owns measured results and pending gates. The service port is not native UI,
actual IPC, OS-dialog or render qualification. The ordinary frontend remains
scripted until a separately frozen consumer passes its own gates.

## One implementation, immutable transport

Preserve the existing two-argument constructor and its scripted behavior. Add
only a closed constructor option plus a native convenience factory. Proposed
public signatures below are absent at the inspected source:

```ts
type ComparisonRunMode = "scripted_baseline" | "approved_native";
type NativeComparisonRunOptions = Readonly<{ mode: "approved_native" }>;
type ComparisonRunConsumerState =
    | (ComparisonRunState & { mode: "scripted_baseline" })
    | (NativeComparisonRunState & { mode: "approved_native" });

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

These proposed local state unions use the actual V1/V2 discriminated DTOs, not
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

Native state adds an actual decoded `cleanup: SelectedCleanup | null`, plus
bounded local auxiliary pending/uncertainty bookkeeping. These are observations
of Rust's existing owner, not another runtime registry. Keep the existing
acknowledgement/retired-owner uncertainty separate from global cleanup state.

- `cleanupStatus()` and `retryCleanup()` use native actions with empty queries,
  including when `allowed=false`. A valid native window remains mandatory.
  Neither action grants inspection or starts/resumes comparison work.
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
- Extend the completed/cancel/status latch carefully: retain actual completed
  evidence while retaining newly reported cleanup uncertainty/running/cause.
  The current V1 spread of the old status must not erase V2 fields. Inspection
  and new native admission stay unavailable while cleanup is required, running
  or its acknowledgement is unknown. Never manufacture report publication after
  successful cleanup; explicit same-run status/lookup observes reconciliation.
- Retry is explicit and bounded by the existing controller/native behavior.
  No automatic cleanup retry, inferred rollback, resume or model reload follows
  a lost acknowledgement. Native Rust still owns all cross-evaluation/model
  exclusion, exact Arc/witness checks and positive cleanup proof.

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
both use the frozen `{clientId,runId}` query. Returned reader wireV1 then uses
the existing `evaluation_comparison` status/source/summary/evidence/close paths.
Execution tokens are never reader tokens and completion never auto-opens a
private report. App's Inspect callback captures mode/controller/context/run
identity before awaiting reader close and rechecks it afterward. It must not
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

## Proposed frozen oracle and qualification slice

Future code allocation is limited to the comparison-run model/controller/view,
the reader's managed-entry seam, Root App/Main wiring and focused new checkers.
Existing test oracles remain intact. Before production consumer edits, freeze:

1. Original56 scripted mock/SSR checks unchanged; separate V2 exact shape,
   required-nullable, category, bounds and mixed-lane negatives.
2. Actual controller start/status/retired-close endpoint logs, including held
   replies after mode/context switches and synchronous subscriber reentrancy.
   Unknown ACK keeps one original client; no automatic start/resume/fallback.
3. Retired close unknown versus actual cleanup-required/running/unknown;
   cleanup with `allowed=false`; late auxiliary replies and completion/cancel
   latches cannot clear a newer owner or discard V2 cleanup cause.
4. Native managed initial routing with unchanged readerV1 subsequent calls;
   held inspect callback/mode change, independent denial and observer/private
   reply fencing. Current scripted `pick(runId)` compatibility remains exact.
5. Actual View headless wording and control states for scripted, native unknown
   availability, awaiting confirmation, cleanup required, unavailable model,
   saved native metadata and last verified report counts. Headless/mock evidence
   is explicitly labelled and is not native IPC/render/model evidence.

After service eligibility and consumer source freeze, Root separately allocates
strict frontend/type checks, scripted compatibility, actual application-owned
native action/IPC/WebView captures and all-image inspection. Fixed consent/ACK
doubles establish plumbing only. Approved installed-model UI/service invocations,
real OS-dialog behavior and quality need their own bounded admission/provenance;
no extra invocation is authorized by this draft. Keep source matching,
current/historical runs and retained failures explicit. No desktop control,
OS screenshots, provider replacement, model download or phone gate is proposed.

## Type and reentrancy viability addendum (still proposed)

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
