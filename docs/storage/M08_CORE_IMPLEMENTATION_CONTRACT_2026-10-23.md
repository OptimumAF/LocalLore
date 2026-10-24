# M08 Core implementation contract

2026-10-23. #12 M08.03 / #30 D08.05 prerequisite. **Contract/source proposal; no implementation or executed feature tests.** Coordinator accepted the typed direction before this document was written; that is an implementation allocation, not human acceptance of the feature.

Read against `30735b5d07988bad164b8bba4a22f0c0e705fb8d`, original design `aefddd6baf5702c2d26f22d55d39fd5bc1ae84d1`, and review `34c7f879aa863dd9167b384aaf8e63c9856314b6`. Separate `design/m08-core-contract` / `source-m08-core-contract`; claims #12 `6376228058`, #30 `6376228311`. Sole owned path is this NEW document. Root owns all existing Core/Store/Host/consumer paths and production delegation. Separately reviewed M07 correction `f4860432b4847f664fbcad8750cc08dea16a2732` preserves same-source/append Open refresh; its behavior must survive integration.

## Allocated versions and authority

Freeze domain/history 2, projection 2, schema 5, archive 3, query/actor context/compiler 2 and fresh Play **2.5**. Keep Seed/ordinary Request/Proposal/Profile/Receipt/AcceptedEvent version-1 shapes and bytes unchanged. Old Play 2.1–2.4 remain strict history/retry inputs; 2.4 retains compiler/context 1 and omitted new policy. Do not bump the reused contracts `VERSION=1` globally.

The accepted mixed history alone owns revision, replay, boundaries, source identity and budgets. Model output remains an untrusted ordinary proposal. An author record cannot be passed through `Receipt`, ordinary `commit_prepared`, `Intent::AuthorCorrection`, a JSON flag, or an inspection grant. Store schema 5 later commits fork plus author record atomically; Core creates a pure validated child candidate only.

## Exact types and serialized history

Names below are the frozen target API, not declarations that already exist. All IDs are existing bounded `String` IDs; all accepted records are engine-constructed, Serialize-only with private fields. Public data references are not accepted-history capabilities.

```rust
// New native input, Serialize for the dedicated preview adapter; no Deserialize.
pub struct AuthorCorrectionInputV1 {
    pub version: u16, // exactly 1
    pub parent: Scope,
    pub expected_parent_revision: u64,
    pub fork_revision: u64,
    pub child_branch: String,
    pub operation: AuthorCorrectionOperationV1,
    pub reason: String,
}
pub enum AuthorCorrectionOperationV1 {
    ReplaceFactProposition {
        fact: String, expected_proposition: String, replacement: String,
    },
}
pub struct EventRef { pub original_scope: Scope, pub sequence: u64 }

// Internal canonical provenance; never members of actor/public Receipt DTOs.
enum TruthSource {
    SeedFact { seed_id: String, fact: String },
    Author { source: EventRef },
}
struct ObservationBinding {
    event: EventRef, actor: String, fact: String, truth: TruthSource,
}
pub struct CanonicalPlayV2 {
    receipt: Receipt, observations: Vec<ObservationBinding>,
}
pub struct AuthorCorrectionReceiptV1 {
    version: u16, // exactly 1
    policy: AuthorPolicyV1, // ReplaceExistingFactPropositionV1 only
    scope: Scope, sequence: u64, rules: Profile, seed: String,
    story_time: u64, witnesses: BTreeSet<String>, // always empty
    input: AuthorCorrectionInputV1,
    before: TruthSource,
}
pub enum CanonicalRecord {
    LegacyPlay(Receipt),
    PlayV2(CanonicalPlayV2),
    AuthorV1(AuthorCorrectionReceiptV1),
}
```

Input/operation derive Clone/Debug/PartialEq/Eq/Serialize; the operation uses a closed tagged variant (`op: "replace_fact_proposition"`). A future adapter parses untrusted JSON into its own strict DTO before constructing native input; data parsing cannot grant author permission. Accepted record fields remain private, with read-only native accessors. `TruthSource` may have an opaque public read-only native wrapper where needed for omniscient tooling; no public constructor or actor DTO exposes its inner author reference.

`CanonicalRecord` has custom serialization, not an untagged Deserialize fallback:

```text
LegacyPlay -> exact original Receipt JSON, no wrapper or new default fields
PlayV2     -> {record_version:2,kind:"play",receipt:<unchanged Receipt>,
               observations:[<private ObservationBinding>...]}
AuthorV1   -> {record_version:2,kind:"author_correction",receipt:<Author...V1>}
```

There is no separate private author journal. A Domain 2 play receipt still contains safe `Effect::Discovered {actor,fact}`; its private observed truth reference belongs only in the canonical wrapper. The bindings are ordered one-for-one with discovery events, including repeated discoveries of the same fact inside a multi-command receipt. Strict replay reconstructs each binding from truth **at that event** and compares the complete wrapper. A forged actor/fact/source, missing/extra/reordered binding, future/sibling reference or injected private field fails replay. No arbitrary persisted binding becomes authority merely because its checksum matches.

The author receipt's `scope` is the child and sequence is `fork_revision+1`; it has no actor witnesses, no fictional participant, no model output/narration and no time advance. The new truth source is its own `(scope,sequence)`, derived rather than separately mutable. Its input supplies the exact old/new proposition and private reason; `before` identifies the actual prior source. A → B → A creates a distinct author source even when text returns to A. JSON-like text remains inert.

## Engine storage and compatibility APIs

```rust
struct Engine {
    seed: Seed, scope: Scope, lineage: Lineage,
    state: Projection,                 // existing mechanical/membership view
    knowledge: KnowledgeProjectionV2,  // derived sparse references, not a ledger
    records: Vec<CanonicalRecord>,     // SOLE accepted-history authority
    receipt_cache: OnceLock<Vec<Receipt>>, // read-only derived compatibility view
}
struct KnowledgeProjectionV2 {
    truth_overrides: BTreeMap<String, EventRef>,
    observed_overrides: BTreeMap<String, BTreeMap<String, EventRef>>,
    // outer actor, inner fact; references actual accepted discovery events
}
```

`state()` keeps its existing `&Projection` signature for mechanics. Domain 1 `canonical_bytes()` remains exact old Projection encoding. Domain 2 canonical bytes serialize an explicit version-2 object containing the mechanical projection and sparse knowledge projection; they are native/private state, never provider input. Absence of overrides does not convert an authored branch back to Domain 1.

Keep `receipts() -> &[Receipt]` using a lazy, immutable derived cache of ordinary play receipts. Clear/invalidate it on accepted append and replay construction. **No canonical Core/Store/Host consumer may use it for revision, replay, prefix equality, count/cap, source hashes, boundaries, archival canonical data or retention.** Do not keep a second writable receipt vector. The cache can duplicate bounded ordinary receipt payloads (up to the existing 16 MiB serialized history ceiling, with additional Rust allocation overhead); cloned Engines may multiply this cost. This is an explicit memory cost, not measured performance or a new cap allowance. Prefer leaving it unmaterialized in canonical operations.

Freeze these methods:

```rust
impl Engine {
    pub fn canonical_records(&self) -> &[CanonicalRecord];
    pub fn canonical_record_count(&self) -> usize;
    pub fn domain_version(&self) -> u16;
    pub fn completed_boundaries(&self) -> Vec<u64>; // bounded; includes 0/head
    pub fn prepare_author_correction(
        &self, input: &AuthorCorrectionInputV1, cancel: &dyn Fn() -> bool,
    ) -> Result<PreparedAuthorCorrection, Error>;
    pub fn apply_author_correction(
        &self, prepared: &PreparedAuthorCorrection, cancel: &dyn Fn() -> bool,
    ) -> Result<AuthorCorrectionOutcome, Error>;
    pub fn replay_records(seed: Seed, records: &[CanonicalRecord]) -> Result<Self, Error>;
}
pub struct PreparedAuthorCorrection { /* private input, parent/fork basis, preview */ }
pub struct AuthorCorrectionOutcome {
    pub engine: Engine, pub receipt: AuthorCorrectionReceiptV1,
}
```

Outcome is native-only, not a wire serialization of an Engine. Plan is non-Deserialize and not an author UI grant; read-only `input()` and `preview()` accessors suffice. It binds the complete typed input, full parent `AcceptedHistoryBasis`, fork-prefix basis, versioned deterministic plan and exact preview. `apply` re-prepares from the actual parent, compares the complete plan/bindings and returns a newly forked child without modifying `self`. It reuses actual `at_revision`/`fork` lineage rules, including supported prebirth/nested boundaries; it does not implement a second fork interpreter. Store later checks its own child-ID catalog/retirement/depth/owner and transaction admission.

Require parent/scope/head exactness for **creation**, a real completed fork boundary, existing fact, exact expected value **at the fork**, nonempty/different replacement, existing ID syntax and 2,048-byte string limits. Do not trim/rewrite stored propositions. Reason may be empty but is bounded/private. New replacement checks must not reject a valid legacy expected proposition merely because it would be disallowed for a new replacement. Check actual escaped JSON bytes against record/preview caps before returning a candidate. Cancellation yields no partial Engine.

Core preview is a bounded Serialize-only native DTO: exact input/child/fork/current head, prior source/value and replacement, retained-knower count, excluded parent suffix event/record counts, preserved-original/no-replay labels and `new_child_requires_fresh_derivatives=true`. Core has no descendant/job catalog and must not fabricate its counts. Store can enrich its final 64 KiB preview from one coherent catalog read; all parent/descendant histories and derivatives remain unchanged and no jobs/caches are copied to the new child. Refuse over-budget preview rather than truncate consent or claim semantic impact analysis.

## Replay, source identity and budgets

Existing `restore(seed, &[String])` and `restore_continuation(&[String])` dispatch private persisted DTOs after recursive duplicate-key/structural bounds checks. Absence of `record_version` means strict legacy Receipt only; presence means exact supported wrapper/kind, never fallback to legacy parsing on failure. Replay validates and fully compares each actual regenerated canonical record. History-only author application bypasses live UI consent only inside this private reconstruction path; ordinary fresh commit cannot invoke it.

Bare legacy records are valid only before Domain 2 semantics begin. The first valid author record transitions the child; inherited authored prefixes keep Domain 2. New ordinary commits on Domain 2 append PlayV2 wrappers. Forking before the first authored record retains Domain 1. `replay(seed, &[Receipt])` remains an explicitly legacy-history API and cannot silently reconstruct authored history from the filtered compatibility view; authored replay uses `replay_records`/strict serialized restore.

`revision`, request preflight, `recorded` lookup, `at_revision`, `fork`, continuation replay, accepted-history basis/matches/extends and history budgets traverse **records**. Every record supplies native `original_scope()`, `first_revision()`, `last_revision()` and `kind()` accessors. Legacy multi-event turns and new private author intervals both contribute actual completed boundaries. Bound source hashing includes all private author/binding bytes and original lineage, not public receipts. Preserve exact old accepted-basis/canonical/receipt encoding for Domain 1; use a distinct mixed-domain hash tag for Domain 2.

Existing caps remain: 4,096 **all** canonical records, 16 MiB accepted serialized history, 64 KiB per record, seed 128 KiB, projection 256 KiB; author input/preview are bounded too. Store's combined request/response cap is separate and remains enforced. No eager actor×proposition copies, silent truncation or cap increases. Sparse overrides are replay-derived references; canonical history remains the source even if an index/cache is missing or corrupt.

## Actor values and safe views

```rust
pub enum ObservationSource {
    SeedKnowledge { seed_id: String, actor: String, fact: String },
    Event(EventRef),
}
pub struct ObservedFactView {
    pub fact: String, pub proposition: String, pub observation: ObservationSource,
}
pub struct ActorEventV2 {
    pub version: u16, // 2
    pub event: AcceptedEvent, // unchanged safe event, never the private wrapper
    pub discovery: Option<ObservedFactView>, // value observed at this event
}
pub struct ActorReceiptViewV2 {
    pub version: u16, pub original_scope: Scope, pub turn: String,
    pub events: Vec<ActorEventV2>,
}
```

These views Serialize only; their construction is from actual Engine eligibility, not caller-supplied view data. NPC/actor receipt views contain **no raw player Request, Proposal or narration**. Filter events and remove empty records before content extraction, search, counts, paging and ranking. Player-own receipt views may expose unchanged Receipt plus sanitized observations only under existing owning-player eligibility. Never serialize CanonicalPlayV2/AuthorV1/private TruthSource through ordinary snapshots, candidates, provider approved outcomes or capture contexts.

Add `observed_facts(observer, scope, revision) -> Result<BTreeMap<String,ObservedFactView>,Error>` and `character_context_v2(observer,scope,revision) -> Result<CharacterContextV2,Error>`. CharacterContextV2 keeps current self-state/beliefs, scope/revision/observer/seed identity, uniformly typed known-as-observed values and eligible ActorEventV2 observations. It contains no current hidden truth, author ID/digest, truth version/comparison or stale flag. A native `effective_fact(fact) -> Result<EffectiveFactView,Error>` is for trusted omniscient/author tooling only; it is not a model/context API.

Add a range/cancelled visitor with the exact old admission parameters and `visitor: &mut dyn FnMut(&ActorEventV2)->bool`, named `visit_actor_observations_v2`. Preserve scope/head/range checks and bounded cancellation checks including hidden records. Canonical author records yield **zero** actor callbacks. For legacy contexts/borrowed `&AcceptedEvent` visitors on Domain 2, return existing `Error::Version` (consumers map to Unsupported); there is no current Core `Error::Unsupported` and no new global version bump. Domain 1 legacy API behavior stays exact.

Initial known values resolve from seed `known_by` and strictly replayed eligible legacy discoveries. Later observations resolve their accepted binding's truth at observation time. Corrections never change those values or beliefs. Uniform Domain 2 `Discover` accepts both same-value/source reconfirmation and changed-value observation when ordinary player/location/evidence/agency/budget checks permit; only the observing player gets a new observation reference. No source-equality admission oracle, NPC learning, invented discovery location or dialogue-as-truth conversion is added.

## Compiler/query/Play closure and public boundaries

Query 2 and compiler 2 consume actual actor-safe V2 views. Known values are mandatory `KnownAsObserved`, not `CanonicalTruth` or `Belief`; current facts/mechanics, beliefs, relationships and unresolved promises retain their separate types/mandatory role. Actor filtering precedes lexical matching and counts; private world truth is never searched then redacted. Narration's changed observed-fact semantics need explicit policy dispatch while preserving old recorded policy; do not reinterpret old receipts under a new prose validator.

Freeze **two requested construction policies** for Play 2.5 provenance:

```rust
pub enum PlayContextPolicy {
    StateRecentTranscriptV1,
    StateRelevantMemoryV1,
}
// New optional field on PlayContextRecord, serde default + skip None:
// context_policy: Option<PlayContextPolicy>
```

RelevantMemory is the actual exact/lexical selector using raw or verified representation, **not** a raw-versus-verified ablation. Coverage mode/source/compiler fallback remain independent actual diagnostics. RecentTranscript is Unsupported until the same compiler has its real policy seam; do not label current lexical context transcript-only. Play 2.5 requires context version 2/compiler 2/Some supported policy; 2.4 requires original version 1/compiler 1/omitted policy; 2.1–2.3 keep omitted context. Unknown labels/combinations fail strict replay. Reserved Recent is not fresh-admitted until implemented. No third StateLexical enum arm is added.

Initial Domain 2 old method-v2 proofs/jobs are Unsupported and compilation is actual raw actor-safe fallback; no renamed proof, copied cache or competing memory consumer. Domain 1 old proofs/history remain unchanged. A future packet format/maintenance bridge requires its own complete mixed-source contract. No author feature becomes reachable through current wire/UI until all consuming paths below either support V2 safely or fail closed.

Canonical completed boundaries have their own bounded native read DTO, `CompletedBoundaryCatalogV2 {version,scope,head,boundaries:Vec<u64>}` derived from actual history, never from ordinary receipt last-events. It contains no record kind, author reason, affected fact or truth source. Private author intervals consume public head/boundaries but produce zero actor records. Fork UIs may select this metadata and still require Rust validation; an actor-filtered receipt list cannot establish whether the current author head is a legal fork boundary.

## Required actual callsite migration inventory

All paths are under `crates/`; these are coordinator-owned dependencies, not claims on existing files.

| Current file/group | Mandatory closure |
|---|---|
| `locallore/src/engine.rs`, `scope.rs` | One records vector; commit/replay/restore/at_revision/fork/recorded/revision/caps; source basis and exact lineage; sparse values and safe visitor |
| `locallore/src/contracts.rs` | Keep Receipt/Effect bytes; new private accepted types and actor/public DTO versions, no broad VERSION replacement |
| `locallore/src/inspection.rs`, `inspection_query.rs` | Private canonical export separated from actor/event views; knowledge/search/count/page/history/turn-diff use observed values and original scope |
| `locallore/src/context_compiler.rs` and verified compiler | Typed mandatory observed values; policy seam and V2 row sources; no old seed lookup beside V2 values |
| `locallore/src/memory_coverage.rs` | Old packet shape refuses Domain 2; canonical completed intervals include private author records even when actor set is empty |
| `locallore/src/play.rs`, `inference.rs`, `intent_guard.rs` | Exact current/historical dispatch, guarded discovery and safe provider/narrator inputs; fresh author intent still AuthorUiRequired |
| `locallore/src/host.rs`, `turn_capture.rs`, `turn_trace.rs` | Public Play/inspection/history/candidate/trace serializers safe; source-bound Work/commit/cleanup and snapshot use complete records; grant/owner lifecycle; safe boundary catalog |
| `locallore-workspace/src/lib.rs`, `maintenance.rs` | Actual coherent snapshot/fallback and complete-source binding; no silent legacy port support or automatic job admission |
| `locallore-storage/src/turns.rs`, `lib.rs`, branches | Strict kind-first row loader, schema-5 physical child row expected_revision=fork; actual atomic fork+author record; no public separately committed fork inside writer |
| Store `memory_jobs.rs`, `derived_memory.rs`, `branch_retention.rs` | Full mixed-source/budget/retention hashes, canonical head/cutoffs, no copied jobs/caches or v2 certification of Domain 2 |
| Store `playable_archive.rs`, capacity fixtures | Archive 3 mixed canonical validation/local-record export/import; old 1/2 strict paths and old receipt bytes; new capacity qualification |
| `locallore-eval/src/lib.rs`, `local_lane.rs`, `local_lane/desktop_api.rs` | Report replay/receipt hashes vs canonical source fingerprints; old reports immutable and unsupported versions honest |
| `locallore-android/src/lib.rs`, `workspace.rs`, `archive.rs` | Canonical counts/head/source compatibility or fail closed; normal adapters/UI/JNI wire versions and fork-boundary input cannot drop author records |

Audit existing examples/tests and desktop generated schemas/controller decoders alongside that source inventory. `locallore/src/main.rs` is presentation-only ordinary receipts; it must not become a canonical serializer accidentally. Original generic receipts remain useful for UI compatibility, never for whole-history equivalence or author recovery.

## Frozen test-oracle inventory before implementation execution

1. Legacy canonical/receipt bytes, compact Play 2.1–2.4 history/retry, root/fork/restore/continuation and fresh historical-prepared refusal remain exact. Missing/new metadata cannot be laundered under an old label.
2. Actual known player and known NPC A → B retain A, exact eligible observation source, beliefs/claims/mechanics/time; omniscient truth becomes B. A → B → A retains distinct private sources without stale flags/source-version acceptance oracle.
3. Uniform eligible same-source/value and changed-source discovery, repeated same-fact commands, exact retry with zero duplicate event, wrong location/no location/agency/cancel refusal, only player observation updated; no NPC learning from Say.
4. Author reason/new hidden value/reference canaries absent from actor contexts, NPC receipt views, searches/counts/pages, compiler selected rows, both role requests, public candidates/receipts and permitted captures. Player-own and omniscient outputs are tested separately. Event filtering precedes grouping/counts.
5. Actual foreign/sibling/parent-future/prebirth refs, wrong actor/fact/truth binding, missing/extra/reordered observations, bad kind/version/sequence/witness/time, malformed/duplicate JSON and rehashed tampering fail complete replay; full valid imported rewrite is not cryptographic proof of historical author consent.
6. Multi-event and private-author completed boundaries, fork before/after author, inherited original scopes and nested/prebirth rewind; canonical revision/source/count/caps include authors while actor record count remains zero for them. Derived receipt cache cleared/rebuilt and corruption cannot change canon.
7. Plan substitution/stale parent/changed prefix/seed/lineage/fork expected value, wrong scope/ID, partial boundary, no-op, escaped-string record/preview/projection budget and cancellation all leave parent unchanged/no partial child. Retained-knower cap test prevents eager text multiplication.
8. Store-owned later tests: same fixed child exact-input unknown-ack recovery after heads advance; atomic rollback/Busy/Full/CAS/owner/grant/late cancel, no child without author record, no parent/sibling/descendant mutation; schema4→5 and archive3 roundtrip with old fixtures immutable. Core pure outcome is not durability evidence.
9. Domain2 actual Unsupported raw fallback, no old-proof/job admission, mandatory observed-value context and fail-safe budget refusal; requested policy distinct from actual fallback. Recent policy remains Unsupported until implemented. No fabricated savings or model quality.
10. Existing M07 same-source/extension Open refresh preserves work/trace; nonextension retires cache/owner. Core author selection cannot bypass source-bound Work/commit/cleanup or confer inspection/generation knowledge. Platform native UI/JNI/device/model gates remain separate actual evidence.

No Rust test source or production file was changed for this packet; the numbered oracles are a source proposal to freeze before later code/tests. Actual document checks are source/Git/issue reads and whitespace/owned-path/clean-tree verification only, using Git 2.33.0.windows.2 / PowerShell 7.6.5. No build/model/app/device/native execution or acceptance is implied. Next runnable task: coordinator delegates exact Core production and new test paths under this contract, with Store/compiler/Host ownership serialized and fresh source/oracles frozen before execution.
