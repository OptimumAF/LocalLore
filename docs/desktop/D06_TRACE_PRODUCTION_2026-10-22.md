# Optional passive tracing of the production preparation path

Refs #28 D06.01/.06/.07 partial, claim
[6357871884](https://github.com/OptimumAF/LocalLore/issues/28#issuecomment-6357871884).
Isolated branch `impl/d06-production-hooks`, based on coordinator-frozen D04/D05 shared
integration `db3e6ed51871662036120d9ea2c97d85d04107b4`, plus collector cherry-pick
`129d54f` (original `4a52456`). This packet changes the exclusively transferred
play implementation, trace module/tests, library module line and D06 evidence.
Host/schema/native UI/store and other agents' application paths are untouched.

## Production interface

`play::execute` remains the existing entry point and delegates to:

```rust
pub fn execute_traced(
    engine: &mut Engine,
    request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized),
    cancel: &Cancellation,
    profile: &PlayProfile,
    sink: Option<&mut dyn TraceSink>,
) -> Result<Receipt, Error>;
```

Existing callers pass None through the wrapper and keep capture disabled. There
is one production compiler/generator/validator/clone-commit path, no copied debug
context builder, changed inference protocol, gameplay Result or persisted Receipt
schema. Existing nondeterministic StageTiming fields retain their meaning.

`StageTimer::start().finish(stage,outcome,counts,error)` produces an opaque
StageMeasurement with an actual start and end. `TraceRing::record_measured`
anchors that interval to attempt start and rejects overlapping/stale measurements.
Idle gaps do not become stage duration. The earlier convenience `record` remains
available for simple hook-boundary marks; production play uses explicit intervals.

`RingSink::new(Arc<Mutex<TraceRing>>, handle)` implements TraceSink. At entry the
pipeline calls `matches` with exact request scope/base revision, actual gameplay
player and turn. A mismatched handle disables capture rather than receiving
another turn's counts. RingSink checks the bound attempt, uses try_lock, and drops
busy/poisoned/cleared/evicted/terminal/truncated metadata without a gameplay error.
The read Selector still is not authorization; Reader remains trusted and separate.

Unwinding failures from trusted sink matching/recording are caught; a failed sink
is disabled for the rest of the call. Callback durations are measured and excluded
from the existing whole-turn budget and StageTiming clocks. A synthetic hook that
sleeps80ms at each record exceeds a500ms wall budget yet preserves a valid turn's
actual gameplay budget. This does not promise termination of arbitrary blocking
Rust callbacks or recovery from allocator/abort/OS failures. Production RingSink
performs bounded metadata work with nonblocking lock acquisition. No raw gameplay
data is passed to a hook, and hooks must not hold or mutate gameplay/cancellation
authority through other trusted application references.

## Observed stages and honest limits

- Intent records actual recorded-retry lookup, profile validation, preflight and
  supported input checks. Cached replay emits only this real lookup; it neither
  calls a provider nor fabricates the old generation stages.
- Validation records the existing pre-generation action guard/preview, including
  missing Ability/Inventory rejection before any provider work. Later Validation
  records actual generated proposal preview. Fixed core error categories survive.
- Context surrounds the existing observer-filtered context/input compilation and
  byte-budget check. Counts sum only the eligible self/fact/observation/belief,
  owned inventory, visible nearby and route entries actually supplied to that
  compiler. There are no omitted/excluded record identifiers or counts. No token
  count is fabricated: unmeasured tokenizer fields remain null.
- Director or Repair surrounds the actual role request/generation. Parsing
  separately records real strict parsing of director and narrator output.
  Repair remains at most the existing profile allowance; parse failure cannot
  become a claimed semantic/rule repair.
- Narration surrounds construction of the approved-outcome-only prompt and real
  generation. NarrationValidation reports the actual validation failure separately
  from its existing transparent safe fallback. It does not claim a semantic oracle.
- AcceptedCandidate surrounds the existing final deadline/cancellation fence and
  Engine::commit_play in the worker's clone. Accepted is **not** a durable atomic
  Host/Store commit and never emits Committed here. Attempt stays Running until
  its owning Host lifecycle records the actual terminal outcome.
- Retrieval and MemoryMaintenance are explicit NotRun/Unsupported metadata: the
  shared production path has neither semantic retrieval nor summary maintenance.
  No retrieval miss explanation or stale-summary success is fabricated. Those
  injections await the actual #10/#11 capabilities and remain outside this gate.

Existing32-attempt/24-stage/64KiB complete-JSON bounds, default disable/clear,
unknown provenance, private read controls and full-capture Unsupported remain.
Trace fields never enter the model prompt or canonical Receipt. No raw input,
context, output, model path or exception text enters metadata. Trace stages cannot
establish that a field is true or change character knowledge. Metadata-only debug
traces do not satisfy D06's future opt-in artifact/context/maintenance UI scope.

## Exact Host integration recommendation

1. From the real production prepare worker, begin one attempt with trusted exact
   scope, base_revision, player, retained original turn and unique attempt number.
   Populate known model/worker/profile hashes and runtime revision from the actual
   selected native profile; profile/prompt/schema labels must be trusted software
   versions, engine revision a trustworthy build identity. `prompt_sha256` should
   identify the shared static prompt template if measured; do not silently pair a
   native chat-template hash with the application's unrelated prompt-version label.
   The selected profile identity already binds its known native template metadata.
   Keep unknown config/schema/static-template identities null rather than hashing
   arbitrary private text or inventing a constant. Full prompt/output capture
   remains Unsupported.
2. Retain an optional handle for that exact worker lease. Create RingSink and call
   execute_traced on the same coherent Engine clone/provider/cancellation path
   currently used by prepare_local. Do not hold Host/store/trace mutexes across
   generation. RingSink is Send through its owned Arc/handle, but the short sink
   reference only lives within that worker call. A failed begin means no sink;
   never reject valid gameplay because recording was unavailable.
3. After preparation, leave successful candidate attempts nonterminal while the
   real Host awaits commit. Record failed/rejected/cancelled/stale terminals from
   the actual production result. On atomic commit, start an explicit StageTimer
   outside the diagnostic lock around the actual durable operation, emit its
   real Committed/Rejected/Failed/Stale/Cancelled result, then finish the attempt.
   An ignored trace status must never roll back or fail the durable transaction.
   No second trace-specific transaction or inferred later reconstruction.
4. Carry the same attempt handle through the existing turn lease, not a global
   current observer or a turn-name-only map. Switching/closing invalidates leases;
   a stale handle drops. A truncated trace remains truncated even if canonical
   commit later succeeds; UI uses the actual receipt for gameplay truth.
5. For read/clear commands, apply trusted session/scope/current-head/privacy
   checks independently. Query base_revision identifies the original attempt
   basis; it is not a freshness promise. Construct Reader from trusted Play actor
   or acknowledged native Lab privilege, never wire JSON. No trace in an NPC or
   narrator context. Use short best-effort locks for diagnostics and detached
   bounded snapshots, keeping default capture disabled and clear/delete explicit.

The coordinator owns implementing/verifying these Host lifecycle recommendations;
they are not source claims about current Host integration.

## Verification and remaining work

Windows x64 / rustc1.93.1 / cargo1.93.1, locked cached offline dependencies, no
new manifest/dependency. Separate approved D: target; dev/test debug0 and
incremental0. Actual final commands from this worktree:

```powershell
cargo +1.93.1 test -p locallore --test play_v2 --test turn_trace --test production_turn_trace --locked --offline --target-dir D:\CodexLocalLore\01a165d9-ff25-7500-a550-1099087d4e37\d06-trace
cargo +1.93.1 clippy -p locallore --test play_v2 --test turn_trace --test production_turn_trace --locked --offline --target-dir D:\CodexLocalLore\01a165d9-ff25-7500-a550-1099087d4e37\d06-trace -- -D warnings
rustfmt +1.93.1 --check --edition 2021 crates/locallore/src/lib.rs crates/locallore/src/play.rs crates/locallore/src/turn_trace.rs crates/locallore/tests/turn_trace.rs crates/locallore/tests/production_turn_trace.rs
git diff --cached --check
```

Final focused result: **42 passed, zero failed/ignored**:12 existing play tests
(0.01s),20 collector tests (3.51s) and10 new production tests (0.97s).
Strict Clippy passed (2.06s); formatting and staged diff checks passed. Focused suites cover
unchanged play behavior, the collector and new
production-path tests. The golden compares the same scripted-provider production
entry with tracing on/off: identical Result, accepted events, canonical state,
original request/proposal/narration/profile/fallback/repair metadata and Receipt
semantic payload, normalizing **only existing StageTiming.elapsed_ms**. Cases
include success, invalid ability, finite malformed repair/failure, unfaithful
narration fallback, cancellation, stale start, recorded retry, wrong-bound handles,
observer/privacy/base isolation, hidden-record count noninterference, exact stage
intervals, default disabled/drop/truncate/busy/poison and panicking/slow hooks.

The first new-test compile caught a test-local helper shadowed by a variable; it
was corrected before execution. An initial library pass warned about an unused
temporary timer, removed before strict Clippy. No assertion/acceptance criterion
was weakened. These are shared production-play tests with a synthetic provider,
not Host/native IPC/UI rendering or actual model execution. No app/Android/device,
real model, storage write, merge or release was operated. Next: coordinator wires
and tests actual Host worker/commit/read lifecycle, then the native debugger UI.
Full D06/task acceptance and memory-dependent debugger gates remain open.
