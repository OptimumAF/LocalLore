# D04 initial-world Author lane: frozen packet A contract

**Packet A frozen by Root; implementation and checks pending.** Refs #25 D04.02, supporting D04.04, shared #9 and
#21. [Documentation-only claim](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6539800717).
Base: accepted `eab64f7625de48b8d18e139226223fb4c6f11791`, including PR299's
generation-admission seam. This document grants no implementation or execution
authority. The existing owner assignment authorizes code work. Independent FIRST
must freeze before a different production author changes behavior. Packet B's
artifact, capability and adoption decisions remain open.

## Existing authority and missing consumer

Initial-world authoring is creation of a new original story. It is distinct from
the existing Story Lab correction operation. Shared Rust already validates input,
generates a proposal, requires edited review and explicit creation, materializes
the seed and resolves exact creation retries. The provider must not implement any
of those canonical operations, accept a renderer-supplied seed or acquire existing
story knowledge. No UI or new provider is proposed here.

The accepted source has these separate boundaries:

| Layer | Current source behavior | Consequence |
| --- | --- | --- |
| Shared request | `PROFILE` model profile; `initial-world-v1` schema; role `author`; revision0; `author-draft-{job}/draft`; output1024 tokens/8192 bytes;24000 polls; deadline120000ms | Reuse the actual request constructor and proposal schema |
| Runtime adapter | Only director/narrator, at most350 tokens; first call must be director | An Author request is refused before worker generation |
| LocalRuntime | `Role` has two variants; request and reply metrics each cap output at350 | Adapter-only admission would still fail |
| Application worker | Only director/narrator at most350; the existing generation path applies the grammar and chat template | A newly admitted Rust role cannot make the current worker support it |
| Profile and model owner | Profile declares350 per role; native manager pins the reviewed worker and records its digest/profile provenance | No existing artifact may be relabeled Author-capable |
| Role observations | Every non-director is presently labeled Narrator | Author must bypass that branch and report honest unavailability or a separately designed Author record |

Current shared prompt provenance is `initial-world-v1.1`; schema provenance is
`initial-world-v1`. Historical prompt-v1 records retain their original identity.
Do not conflate those values or invent a new descriptor family for this proposal.
The request's `model_profile` is the passed runtime `PROFILE`, currently
`qwen3-0.6b-q8-cpu-v1`; it is never the schema ID or prompt version.

Source anchors at the accepted base:

- [Shared constants/schema/request](https://github.com/OptimumAF/LocalLore/blob/eab64f7625de48b8d18e139226223fb4c6f11791/crates/locallore/src/story_authoring.rs#L11), [request construction](https://github.com/OptimumAF/LocalLore/blob/eab64f7625de48b8d18e139226223fb4c6f11791/crates/locallore/src/story_authoring.rs#L768).
- [Adapter compile and identity](https://github.com/OptimumAF/LocalLore/blob/eab64f7625de48b8d18e139226223fb4c6f11791/crates/locallore-local-runtime/src/adapter.rs#L56), [sequence admission](https://github.com/OptimumAF/LocalLore/blob/eab64f7625de48b8d18e139226223fb4c6f11791/crates/locallore-local-runtime/src/adapter.rs#L435).
- [Native generation limits](https://github.com/OptimumAF/LocalLore/blob/eab64f7625de48b8d18e139226223fb4c6f11791/crates/locallore-local-runtime/src/lib.rs#L811), [reply validation](https://github.com/OptimumAF/LocalLore/blob/eab64f7625de48b8d18e139226223fb4c6f11791/crates/locallore-local-runtime/src/lib.rs#L899).
- [Worker admission](https://github.com/OptimumAF/LocalLore/blob/eab64f7625de48b8d18e139226223fb4c6f11791/native/llama-worker/main.cpp#L95), [current profile](../../native/llama-worker/profile-v1.json), [native owner/pin](https://github.com/OptimumAF/LocalLore/blob/eab64f7625de48b8d18e139226223fb4c6f11791/apps/desktop/src-tauri/src/models.rs#L40).
- [Android's bound Author request](https://github.com/OptimumAF/LocalLore/blob/eab64f7625de48b8d18e139226223fb4c6f11791/crates/locallore-android/src/external_inference.rs#L158), [singleton/role ownership](https://github.com/OptimumAF/LocalLore/blob/eab64f7625de48b8d18e139226223fb4c6f11791/apps/android/app/src/main/java/org/locallore/app/LocalInferenceOwner.kt#L274).

Android is a contract precedent, not a transport to copy into desktop. In
particular, desktop currently has350-token director **and** narrator profile
limits; Android's narrower narrator setting must not replace desktop's profile.

## Two reviewable packets and the production adoption gate

Proposed packet A is code-only support in the existing runtime owner. Private
classification/state/reply functions are tested with actual shared requests and
fixed synthetic work. If process coverage is separately admitted, reuse the
existing development protocol fixture, explicitly labeled synthetic. This must
not launch the packaged worker, load a model or enable desktop initial-world UI.

Default production Author access remains disabled. Existing constructors,
packaged worker pin, profile bytes/digest, available-profile metadata and model
manager remain unchanged in A. A private runtime gate refuses Author dispatch
before sending a frame to the current packaged worker. A positive fixture gate
may be constructed only inside the runtime's test build for an exact owned
synthetic fixture; no environment variable, renderer flag, request text, schema
label or editable profile can enable it. Ordinary play uses the same provider
type, owner, worker slot and established constructor behavior.
The shared `authoring_capabilities` response is unchanged; its generic
availability value is not evidence that this desktop worker supports Author.
No new UI consumer may convert that value into a supported desktop creation
claim while the native/runtime adoption gate remains closed.

Packet B is a separately claimed worker/provenance/adoption change. It must
implement the same closed worker validation, qualify new ordinary worker bytes,
review truthful role-specific profile metadata and explicitly adopt the reviewed
identity through the existing native model owner. There is no proposed new hash,
model ID or supported-runtime claim in this document. No caller-supplied expected
hash, capability advertisement alone, second worker owner or fallback enables B.
New runtime/model/native execution needs its own concrete authorization.

## Frozen private seams

These names describe constructible crate-private seams for A, not a new public
wire API. Keep existing public `Generation` fields and constructors compatible;
adding the typed `Role::Author` cannot itself grant production access.
`AuthorAccess` and `ReplyBounds` live at crate root so default-feature runtime
builds do not depend on the optional adapter. `Lane`/`CompiledCall` stay in adapter.

```rust
enum Lane { Play, InitialWorld }
enum AuthorAccess {
    Disabled,
    #[cfg(all(test, feature = "development-worker"))]
    Fixture,
}
struct ReplyBounds { output_tokens: u16, text_bytes: usize }
#[cfg(all(test, feature = "development-worker"))]
enum AuthorFixtureCase { Completed, BlockedGenerationObserved }
struct CompiledCall {
    identity: Identity,       // existing full immutable request identity
    generation: Generation,  // existing native generation value
    lane: Lane,
    reply: ReplyBounds,
}
fn compile(request: &GenerationRequest) -> Result<CompiledCall, Error>;
fn parse_reply(frame: &[u8], id: u64, bounds: ReplyBounds)
    -> Result<Reply, RuntimeError>;
// Existing LocalRuntime, crate-private method; no new public generation fields.
fn generate_bounded(
    &mut self, generation: Generation, bounds: ReplyBounds,
    cancel: impl Fn() -> bool,
) -> Result<GenerationResult, RuntimeError>;
#[cfg(all(test, feature = "development-worker"))]
fn author_fixture(log: Option<RoleMetricsLog>, case: AuthorFixtureCase)
    -> Result<(RuntimeProvider, SharedRuntime, PathBuf), OwnedStartFailure>;
```

`ReplyBounds` travels with the exact active native operation, never a global
last-role variable or a field trusted from the worker. It is computed from the
validated request. Load/status/unload retain their existing validation behavior.
An Author native role may be added to the existing typed generation enum, but
`LocalRuntime::generate` must independently enforce its private access gate and
limits; constructing a role enum must not bypass admission.

For a constructible A implementation, both existing provider construction and
packaged-runtime construction initialize private Author access to `Disabled`.
Only the crate's test-only owned-fixture construction may select `Fixture` for
both ends; no public setter is proposed. Provider admission checks this before
starting work, and native runtime admission independently checks it before a
frame is sent. A future production capability variant/mint is deliberately absent
from A and requires B's reviewed artifact/adoption contract. A forged generation
role or a loaded legacy worker does not satisfy that missing gate.
The fixture helper takes no executable/model path or raw command. It uses the
existing development protocol owner and exactly two fixed cases: the ordinary
empty terminal fixture, or its existing generation-observed blocked case.
Factor a private typed case selector under test configuration; the existing public
`development_protocol_fixture()` remains fixed to its ordinary case. No raw mode,
path, environment capability or process argument is accepted from a caller.
Return the retained directory and preserve `OwnedStartFailure` ownership. Synthetic fixture load and
explicit cleanup are separately visible test steps, not implicit model execution.

Keep public `LocalRuntime::generate` compatible. A crate-private bounded-generation
method may carry compiled Author reply limits to the existing operation. Ordinary
Play and non-generation calls keep their current reply ceilings350/16384, including
when a smaller Play token count was requested. Tightening that legacy behavior
would be a separate change. Author bounds instead use the exact admitted token and
byte budget; native admission rechecks those bounds and its private access gate
before sending a frame. Never use a mutable global last-role/limit variable.

For Author compilation require all of:

1. Actual version1 structured request and the unchanged selected `PROFILE`.
2. Role exactly `author`; schema ID exactly the shared `SCHEMA_VERSION`; schema
   value equal to `story_authoring::proposal_schema()`. Forward the validated
   value unchanged; do not maintain another schema or grammar string.
3. Nonempty bounded job/turn identity with the shared32-byte ASCII identifier
   shape, revision0, branch exactly `draft`, story exactly `author-draft-{turn}`.
4. Nonempty NUL-free prompt at most16384 UTF-8 bytes and within the shared frame
   limits. Never parse
   prompt text to select privileges or load existing story context.
5. Tokens1..1024, output bytes1..8192, pending polls1..24000 and
   deadline1..120000ms; retain the existing32,000-byte
   compiled-request and32,768-byte transport-frame ceilings.

Use an actual `generation_request` positive fixture and mutation controls; this
seam does not revalidate or accept an initial-world proposal. That remains Host
and Core work after generation. There is no operation, path, SQL, model handle,
seed or arbitrary shell capability in the private seam.

Effective desktop inference remains at most60000ms, with the existing cooperative
cancel,2s drain and ownership failure behavior. The shared120s value is a ceiling,
not permission to raise desktop deadlines. Preserve director/narrator350 limits,
one director repair and the current play sequence. No global1024-token change.

## Provider state and replay contract

One `RuntimeProvider` selects its lane on its first admitted native attempt.

| State | Allowed next input | Result |
| --- | --- | --- |
| Unbound | Existing valid director | Existing Play lane |
| Unbound | Fully bound Author with trusted fixture/adopted access | Author lane; one native attempt |
| Unbound | Invalid or unavailable Author | Refuse before native dispatch; no model/worker allocation |
| Author pending | Byte/structurally exact original identity | Poll the same operation |
| Author pending | Different identity or any play role | Cancel/retire through existing owner and fail closed |
| Author terminal | Exact original identity | Existing cached terminal result; no second dispatch |
| Author terminal | Changed Author identity, repair, director or narrator | RetryMismatch; new Host job/provider required |
| Play pending/terminal | Author | Refuse; preserve existing Play cancellation/poison rules |
| Poisoned/unknown cleanup | Any new work | Existing refusal/reserved-owner behavior |

The identity includes scope, revision, turn, profile, role, prompt, schema label
and value, and every byte/token/poll/deadline budget. No refund or replacement
follows native failure, cancellation or timeout. Exact cached polling must not
repeat generation. Preserve the existing provider's behavior for invalid inputs
before admission and its current late-reply/cancellation fences; do not make
failed play eligible for an Author retry.

Finite error policy for A:

| Condition | Existing enum/category |
| --- | --- |
| Legacy/unstructured input | Engine `Provider`, unchanged |
| Invalid Author version/profile/schema/binding/budget/prompt | Engine `Rule` |
| Compiled request above32000 bytes | Engine `TooLarge` |
| Serialization failure | Engine `Malformed`, unchanged |
| Unbound valid Author but provider or native access disabled | Engine `Provider`, private runtime failure `WorkerUnavailable`; no native dispatch |
| Changed valid active/completed identity or cross-lane borrowing | Existing `RetryMismatch`/cancel/poison rules |
| An invalid request while work is active | Preserve existing compile-error cancellation/poison behavior and its original category |
| Pre-cancel/in-flight cancel, timeout, Busy, unknown drain | Existing cancellation/timeout/provider mappings; retain exact owner |
| Native invalid generation or bounds | Runtime `InvalidRequest` |
| Malformed/extra/duplicate/stale/over-bound reply | Runtime `Protocol` |

A disabled unbound Author attempt does not bind a lane or poison a later valid
Director call; it never started native work. A successful fixture admission fixes
the lane even if its operation later fails. Test assertions must not run before
bounded worker release and positive cleanup; setup failures remain distinct.

Author responses are noncanonical proposals. The Host still parses and validates
them, drops the provider before publication, and requires explicit review/create.
The provider cannot apply a proposal, attach a session, insert a seed, write a
receipt, grant character knowledge or automatically retry a creation.

## Metrics and compatibility

Frozen A choice: Author role metrics are explicitly **unavailable**, preserving
the existing D07 Play role vocabulary and report schema. Do not call the existing
non-director-to-Narrator observation branch for Author. Merely calling
`RoleMetricsLog::lost()` is insufficient: the current snapshot may still say
`available:true`. A private Author-unavailable marker must produce an unavailable,
incomplete public snapshot with no falsely attributed Author/Narrator record.
Use the existing snapshot shape: version2, `available:false`, `incomplete:true`,
`turn_sha256:null`, `records:[]`; do not fabricate a new D07 descriptor or version.
If a recorder was wrongly reused, retain its internal earlier records but do not
present them as Author observations; a fresh per-turn recorder remains required.
Ordinary Play snapshots must remain unchanged. A later genuine Author metrics
schema is an explicit separate choice, never a relabeled Narrator record.

Keep model artifact/profile/template/runtime/worker provenance truthful. Old
receipts/origins/reports keep their recorded hashes and descriptor families.
No profile manifest may continue claiming that **every** role is350 after a
production1024-token Author lane is adopted. Resolve B's explicit capability and
profile representation before changing any production pin or advertising support.
No current/legacy Eval tuple, selected-reader policy or Android schema changes
belong to A.

## Independent FIRST before behavior

Freeze original assertions in a separate test-author checkout before a different
author changes production behavior. Missing APIs or compilation failures are
UNRUN_SETUP; they cannot establish behavioral RED. Use the real shared request,
actual adapter/state helpers and actual reply parser rather than copied guards.

Freeze new `src/adapter_author_review.rs` and `src/author_reply_review.rs` first.
The producer then registers those tests and extracts the named call/bounds/gate
seams while preserving old production behavior: compile accepts only the two
Play roles, public constructors disable Author, generation/reply checks remain
350/16384 and Play sequencing stays unchanged. The new enum value and fixed
fixture-only construction cannot enable production access. Mechanical updates to
existing parser calls supply legacy Play bounds without changing assertions.
The compile tuple-to-struct extraction may mechanically replace old adapter-test
`.0.full` with `.identity.full` and tuple destructuring with the same named fields;
preserve every existing fixture, asserted value and predicate. No compatibility
wrapper or second identity implementation is needed.
Root must execute a valid compiled old-behavior baseline before the producer
admits Author or changes Author reply validation. Missing fixture binaries,
registration, types or compilation are setup, never behavioral failures.

Register the adapter review as its `#[cfg(all(test, feature = "development-worker"))]`
child, and the root reply review under test/engine-adapter/development-worker.
Producer owns only `src/adapter.rs`, `src/lib.rs`, `src/role_metrics.rs` and
`ADAPTER.md` in the existing runtime crate. Independent FIRST owns the two new
test files. Root owns this contract, integration and bounded execution. Worker,
profile, model manager, Eval/B34, Host, UI, Android and lockfiles stay unowned by A.

| Group | Required independent controls |
| --- | --- |
| Actual shared request | Current constructor/schema/prompt provenance; valid Author candidate versus old refusal |
| Binding | Wrong version/profile/role/schema label/schema value/turn/scope/revision; operation-looking prompt text grants nothing |
| Limits | Author1024 accepted/1025 refused;8192/8193 bytes; zero/overflow bounds; unchanged Play350/351; full frame bounds |
| Singleton | Exact pending/terminal polls dispatch once; changed prompt/schema/budget/identity refuses; no Author/play borrowing or author repair |
| Ownership | Busy, pre-cancel, in-flight cancel, timeout, drop/join and unknown cleanup; no replacement owner or detached test worker |
| Reply | Wrong ID, duplicate/extra/malformed frame, Author token/byte count above its exact request, existing forbidden thinking markers and unknown tool-frame fields; Play parsing unchanged |
| Availability | Current production gate remains disabled; fixture access cannot be supplied by wire/environment/profile; unsupported worker cannot be relabeled |
| Metrics | Author explicitly unavailable, never Narrator; ordinary three-record Play/repair behavior and D07 tuple/decoder fixtures unchanged |
| Worker source (B) | Pure validator tests for exact role/budgets and grammar forwarding belong to B; worker source is unchanged in A |
| Host authority | Reuse actual shared request/schema fixtures; existing authoring/recovery acceptance stays separate and unchanged; generated text alone cannot create a story |

Rust request/reply tests, controlled-work lifecycle tests, actual development
fixture processes and compiled C++ validator tests are different evidence
classes. Each needs its own explicit roster/resource admission. Test hooks stay
test/development-only and fixed-purpose, with bounded cleanup and preserved
failures. A host test is not desktop native IPC, packaged worker or model proof.

## Future ownership and storage plan

This claim owns only this document. Proposed A production ownership is confined
to the existing runtime adapter/library/role-metrics files and narrow new tests;
Root must post exact files, interfaces, source base and checks before edits.
Worker validator source, synthetic fixture additions and B's profile/package/
native-adoption paths need separate explicit allocations. Do not modify shared
Host/Store/authoring semantics, Android, UI or dependency/lock files incidentally.

Preserve B34/PR297's selected/native-reader/descriptor tests and ownership. The
latest [native consumer claim](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6539360721)
and [D07 follow-up](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6539618634)
remain separate. Coordinate before any newly discovered overlap; do not migrate
their historical/current descriptors in this packet.

Before execution, Root must inventory the relevant retained outputs, state a
small phase budget and use reviewed fail-closed admission. Reuse physical-D
source, pinned offline packages, one job, incremental0/debug0 and process-local
TEMP/TMP on D:. No download, new target to evade limits, cleanup, evidence rewrite
or automatic retry. Existing original target baseline8,259,980,576 plus4GiB
(ceiling12,554,947,872),64MiB group/724MiB joint/1152KiB metadata, old576KiB
physical-and-decoded records and8MiB fixture limits are not reset here. Original
compressed-source decoded charges remain included. These are existing ceilings,
not a declaration that a proposed worker build or test sequence fits.

Any future protocol-fixture namespace, including `locallore-protocol-fixture-*`,
must be explicitly inventoried and charged along with all relevant retained
fixtures and outputs before admission. Do not let an existing helper's temporary
path escape accounting. Start with pure fixed tests; budget compiled fixture
processes/worker builds separately. All failed and unrun cases retain their status.

## Freeze decisions and remaining adoption gate

Root freezes the private, default-disabled gate, two fixed test-only fixture cases,
unavailable version2 metrics, exact errors above, unchanged Play reply ceilings,
and worker-source allocation to B. These are code choices under the existing
assignment; no production authority mint or app/model execution is approved.

- B needs a reviewed truthful capability/profile representation, new actual worker
  identity and separate qualified adoption. There is no proposed hash or assumed
  compatibility with the currently pinned binary.

This packet leaves original-world UI, actual Author inference, native application
execution, model quality, Android/device parity, OS/network isolation, packaging
and release unqualified. All four existing app-run grants remain spent. The
reviewable output here is the frozen code-only A contract. It is not a passing
test result, accepted implementation or permission for another app/model run.
