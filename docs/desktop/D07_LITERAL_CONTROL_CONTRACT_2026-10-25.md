# Proposed literal conversation control and first read-only oracle

Source inspected: accepted PR180 merge `5608b72c34477ee110b771c675bc1d0afd06bd6e`.
Scope: D07.04 / M07.01, with M06.04/.06 eligibility ownership.
Status: **Native literal execution and Host durability are qualified with explicitly
scripted providers. The linked slices cover source, renderer, execution/replay and
native Host selection. Evaluator/UI exposure and real-model literal comparisons
remain unqualified.**
See [source API and qualification](D07_LITERAL_TRANSCRIPT_SOURCE_QUALIFICATION_2026-10-25.md).
See [literal renderer and packing qualification](D07_LITERAL_DIRECTOR_RENDER_QUALIFICATION_2026-10-25.md).
See [guarded native execution and replay qualification](D07_LITERAL_GUARDED_PLAY_QUALIFICATION_2026-10-25.md).
See [native Host and durability qualification](D07_LITERAL_HOST_QUALIFICATION_2026-10-25.md).
The candidate runtime signature remains a proposal. Root's narrower first
allocation observes original validated diagnostic Values only in cfg(test).
GitHub #29/#11 retain task status; no criterion is checked by this document.

## Definition

The proposed literal control supplies the player Director with **actual recorded,
player-eligible conversation text**: original player input and accepted narration,
in chronological complete units. It excludes structured accepted-event
dictionaries, current projections, retrieved/supporting memory, summaries, author
records/reasons and other observers' private prose. The current attempted input
is supplied separately and preserved exactly; it is not an accepted past event.

Static role instructions and a fixed output grammar are not historical memory.
They must not become hidden channels for current world facts, resolved actions,
inventory, nearby IDs or routes. Exact grammar and future prompt versions need
separate review before execution. This is not permission to weaken Engine rules.

There is **no invented or reconstructed opening**. A seed, current state,
author correction, diagnostic summary or freshly rendered event description
cannot stand in for an absent original conversation entry. At an initial empty
history, the literal history is empty, explicitly reported as such. Comparisons
must disclose that the memory arm can contain seed-derived current facts which
the recorded transcript does not contain; identical scenarios do not imply
identical information channels.

The first scope is the **player Director**, not an NPC speaking role. NPC literal
prose remains unavailable until M06.04/.06 owns and qualifies an appropriate
observer-safe source contract. Omniscient inspection permission never grants
generation access. This first oracle targets the existing Domain1 comparison
producer; Domain2 literal execution/audit support is not implied.

## What exists at the inspected source

| Source | Actual behavior and consequence |
|---|---|
| `crates/locallore/src/context_compiler/policy.rs` | Only `StateRecentTranscriptV1` and `StateRelevantMemoryV1` exist. These are state-bearing policies, not literal controls. |
| `context_compiler.rs:719–782` | Both include mandatory fields, known truth/as-observed values, beliefs, open commitments, relationships, recent/referenced/supporting events. |
| `context_compiler.rs:881–984` | Recent changes optional selection to complete transcript units; it does not remove the mandatory channel. |
| `context_compiler/policy.rs:114` | `transcript_candidates` uses `Engine::actor_receipts_v2`; player prose attaches only after exact whole-event equality with the actual ordinary receipt. Its current `TranscriptUnit` also contains structured events, so serializing it verbatim is not the proposed literal text projection. |
| `context_compiler/verified.rs:237` | Recent and Domain2 refuse old packet coverage before inspecting it and use raw/Unsupported provenance. Relevant may use verified coverage or fallback; a policy name alone proves neither. |
| `play/director_budget.rs:154–218,252–287` | The actual Director frame adds current inventory, nearby actors and routes independently of compiler records. |
| `play.rs:938–1014` | Action schemas can encode all fields of the already-guarded command as constants; other schema branches carry inventory/nearby/audience choices. Removing prompt records alone does not remove these channels. |
| `play.rs:1215–1232` | The normal action guard compiles and stages the attempt before model work. It stays authoritative. |
| `play.rs:1409` | Narration uses approved evidence rather than an unrestricted historical character conversation. Current success cannot establish causal memory use or NPC voice quality. |
| `crates/locallore-eval/src/local_lane/comparison.rs:19,865–867` | Left/right are the two current policies through the existing Host provider configuration. `ScriptedBaseline` describes a provider lane, not a transcript-only policy. |

Current `ContextPolicy`, compiler defaults, Host defaults, historical validators,
Play2.1–2.5 serialization/retry bytes and existing mandatory-production behavior
must remain unchanged in the first oracle slice. No current capture/report is
renamed literal and no existing comparison result is turned into a baseline.

## Smallest useful first code seam: inspect what was actually forwarded

Propose a **private pure channel auditor**, inside the existing evaluator's
current-comparison code. It observes `inference::GenerationRequest`, whose
`Input::Structured` contains the actual role, prompt and schema and whose budget
is the actual admitted request budget. It must not run a compiler, reconstruct
an expected prompt/schema, call a provider, open a database, alter a report or
authorize a turn.

Candidate signature shape, **not a frozen Rust API**:

```text
audit_literal_control_channels(
    actual: &GenerationRequest,
    recorded_prompt_version: &str,
    profile: &PlayProfile,
    pass: DirectorPassV25,
    initial_director_prompt: Option<&str>
) -> Result<LiteralChannelAudit, LiteralAuditError>
```

`recorded_prompt_version` and the profile come from trusted native execution or
validated retained receipt/recording bindings, not renderer input. The caller
must bind scope, turn, player, base revision, model profile and attempt. The
auditor is not a substitute for that caller's authority/validation.

Two actual observation routes need no new execution pipeline:

1. A bounded passive test recorder observes the exact request at the existing
   `RecordingProvider`/`InferenceProvider::poll` boundary, delegating unchanged
   to the existing scripted provider. It does not choose commands or prompts.
2. For retained evidence, reuse
   `memory_comparison_v2::CapturedContext::from_host_capture(before, request,
   attempt, reply, captures, profile, forwarded_budget_version)` first. This
   already binds real Host artifacts to recording prompt/schema hashes,
   identity, package forwarding and current forwarded-budget/repair checks.
   It retains prompts/package but **not schemas**. Borrow the original validated
   `generation_request.input.schema` artifact; do not fabricate a schema from
   its hash, policy enum or compiler package. Do not deserialize an approval
   object or expose the private validator as a renderer capability.

Parsed `Value` evidence cannot prove that original raw JSON had no duplicate
keys. Preserve existing raw-decoding boundaries; do not claim the new auditor
adds that guarantee.

### First audit result and refusal boundary

The first slice has **no positive conforming/approved/execution-permitted result**.
Its bounded manual result can identify the current forwarded input as
`current_non_literal`, with fixed reason codes, or return `unavailable` for an
unsupported/missing/unrecognized source. It does not certify a future literal
renderer that does not exist yet.

Proposed fixed diagnostic reasons are structural, not prose word searches:

- `structured_context_records`: forwarded context carries state/event/memory
  payloads rather than the defined conversation-text-only history.
- `inventory_frame`, `nearby_frame`, `routes_frame`: current known frame fields
  remain, even if a particular request happens to have empty values.
- `resolved_action_schema`: the schema fixes the whole already-resolved command.
- `state_dependent_schema`: item/audience/nearby choices convey current state.

Do not flag every JSON `const`: static operation names and exact preservation of
the player's text are not by themselves evidence of memory access. Distinguish
the current resolved-action construction from ordinary output grammar. Channel
presence is an ablation/classification fact, not a production privacy violation.

Recognize the actual known current envelope structurally; never infer compliance
by deleting fields from a capture or scanning for secret words. Parsing the
known `Context data:` JSON frame must not discard the rest of the actual prompt
from byte-budget accounting. Unknown framing/version/role, typed legacy inputs,
missing schema/recording, and missing repair predecessor are unavailable/refused,
not a passing baseline. A guard with zero provider requests has no forwarded
Director input to classify; report not-applicable/missing input, never literal
success. Initial support should require current2.5/current budget provenance;
historical evidence without it remains inspectable under its existing contract.

Proposed auditor output is fixed enums/counts/hash references, at most4096 encoded
bytes, without prompt/schema/text/paths. This is a proposed diagnostic cap, not
a change to production input/output limits. It must not enter canonical records,
grant objects, immutable report keysets or a model prompt.

## Bounds, packing and evidence remain shared

Reuse current capture limits: private artifact set at most196,608 bytes,
at most16 artifacts, bounded Host reply, prompt at most32,000 UTF-8 bytes and
at most3 recorded role requests for the current one-repair pipeline. Existing
per-artifact/schema/output limits continue to apply. Do not inflate limits to
make either control fit.

Use **the existing** `director_forwarded_budget_v25` over every actual full prompt
and actual encoded schema. Include the exact possible repair suffix on initial
admission; charge repair bytes once on repair, and verify the initial/repair
relation with `director_repair_matches_v25`. At the existing4096-context,
350-output, repair1 profile, the total512 reserve includes the explicitly
unmeasured162 template reserve. Bytes/4 is an estimate, not a measured tokenizer
or backend-template fit. Preserve current profile validation and full deadline,
role, admission and invocation accounting.

A future literal packer must reuse the existing compiler's bounded cancellation,
whole-unit selection and actor eligibility. Select a deterministic bounded suffix
of eligible whole recorded units; never split a unit, backfill omitted facts or
silently insert retrieved events. Keep original scope/turn/sequence and source
fingerprints as private provenance, separate from the text-only model projection.
Typed action receipts with no original text do not get invented utterances.
Actual accepted narration may be present without an original-input field; do not
manufacture the missing half. The exact unit DTO/packing API is a later freeze.

## Predeclared model-free oracle packet

The following is the original proposed packet; it is not an assertion that every
item has run. The qualified subset and remaining work are recorded below. Do
not weaken assertions or alter immutable fixtures to force a label.

1. Produce real current accepted Action and Dialogue requests through existing
   Core/Host/Store plus scripted provider. Observe both current policies' actual
   requests, validate normal capture/recording bindings first, then identify
   mandatory-record/frame/schema channels. Their captures remain valid current
   captures while a literal-control claim is refuted, regardless of policy name.
2. Make actual schema observations separately from context records. Confirm the
   whole resolved action and current audience/item choices; static grammar
   constants alone must not create a false state-channel reason. Changing only a
   requested policy label cannot change the observed-channel diagnosis.
3. Replay stored evidence and audit repeatedly with zero new provider/asset
   access, unchanged full canonical basis/receipts/actor contexts and complete
   source/report byte inventory. Missing guard capture is not a positive case.
4. Exercise actual first/repair requests, Unicode and escaped input. Keep current
   forwarding/budget/repair validators authoritative: trailing prompt bytes,
   oversized schema or altered repair suffix are refused, not ignored by a
   JSON-substring parser. Tampered/rehashed mismatched recording is not repaired.
5. Reject/unavailable non-Director role, unknown framing/version, absent schema,
   absent recording, wrong scope/head/turn/profile/attempt and historical missing
   budget provenance through their owning existing validator boundaries.
6. Independently freeze the future transcript source projection: exact eligible
   recorded input/narration, complete-unit cuts, empty initial history, typed
   action missing input, repeated bare turn IDs with original scope, hidden/partial
   player receipts and source corruption. No current projection, author reason,
   actor-private prose or generated opening can fill a missing source.

The first five groups can establish a useful negative channel audit without
implementing or executing a literal policy. Group6 freezes the later source seam;
it does not create an execution permit. Proposed ownership: #29 evaluator-local
auditor/actual-recording tests; #11 M07.01 shared compiler/Director source and
packing contract; #10 M06.04/.06 observer/prose eligibility review. Root owns all
existing source registrations, APIs, version decisions and integration. No Store
schema, derived-memory maintenance, embedding or new inference pipeline is needed
for this first read-only slice.

## Later execution prerequisites and provenance

Only after the model-free oracle/source contract is reviewed may Root allocate a
real literal-input renderer through the same compiler and Director. It must
remove all disallowed channels, including frame/schema channels, without removing
Engine preflight/validation/atomic commit, observer filtering, cancellation,
idempotency, receipts or budget authority. Keep ordinary production policy behavior
unchanged. New literal policy/prompt/compiler/record semantics need explicit
versions and replay/consumer closure; do not smuggle new behavior under recorded
Play2.5 or relabel its receipts.

Run the same original scenario attempts on actual isolated prefixes with the same
profile, budgets and role/repair rules, and record precisely which inputs differ.
Use existing comparison reference/paired/rollout machinery, Store and ownership.
Preserve full source/model/template/runtime/profile, scenario, requested policy,
actual channel/projection and forwarded-input provenance. Unknown role/timing or
missing capture stays unknown. No automatic inference retry, source repair or
hash-as-authority. The desktop cannot advertise a literal lane until its shared
producer and closed native/TS report consumers are implemented and qualified.

Evaluator `build.rs` fingerprints source under its existing src trees. Adding a
private auditor changes the current source identity even when execution semantics
are untouched. Generate fresh source-matching fixtures after final API freeze.
Old cohorts remain historical read-only, retain exact bytes, and cannot be
relabelled or resumed under the new source. No existing report format mutation is
required for the first auditor.

## Quality boundary and next gate

[PR180's consumer qualification](D07_SELECTED_CASE_DESKTOP_CONSUMER_QUALIFICATION_2026-10-25.md)
retains a separate quality defect: power-claim narration wandered into an unrelated
library scene, undetected by69 finite checks. That is neither literal-control
evidence nor proof of a retrieval cause. This proposal does not fix or excuse it.
Keep that defect and its narrative-quality/human-review work separate.

Current exact-action preflight/schema and approved-evidence narration severely
limit causal recall and NPC-voice conclusions. A future ablation may expose
information-channel differences without demonstrating that a model used memory
well. Actual model samples, narrative assessment and human review require a
separate bounded admission. No LLM judge can waive mechanical/privacy failures.

Next runnable task: freeze the literal transcript-source projection and its
eligibility/whole-unit packing oracles through the existing compiler. Then
allocate the separately versioned renderer and execution closure. No quality,
performance, native/UI, Android/device or D07/M07 completion is claimed.

## Frozen first allocation and actual qualification

Root freezes #29 comments6405094586/6405120351. Sole new cfg(test) child:
`crates/locallore-eval/src/local_lane/comparison/literal_control_oracle_tests.rs`;
the existing comparison module adds only its cfg(test) registration. Private
helpers consume actual original `generation_request` diagnostic Values after
`CapturedContext::from_host_capture`; there is no new runtime observer, public
auditor API, report field, policy enum, provider, compiler or Store writer.
The only outcomes are `CurrentNonLiteral` and `Unavailable`.

The six original fixtures are produced by existing `execute_turn`/Host/Store/
Scripted machinery: two policies times Action/Dialogue plus a genuine malformed
first Director followed by repair for Dialogue under both policies. Original
capture identity, recording hashes, context forwarding and whole-request budget
are validated first. Actual schemas are borrowed from those artifacts. Full
fixture inventories, original capture bytes and in-memory canonical basis stay
equal during observation. Altered diagnostic copies are explicitly separated
from actual Host evidence and never reattributed to it.

The oracle identifies structured record categories, inventory/nearby/routes
frame presence, resolved non-speech action schemas and state-dependent schema
choices. Empty frame fields still identify the current envelope, not leaked
facts or a production privacy failure. Static rules, operation discriminants
and exact player-text constants alone do not establish a state channel. This
is a finite structural observer, not a general JSON Schema validator or a proof
that another input is clean.

### Retained review failures and correction

Initial source `6c0945ada60cdf18b800f46b148c76d1ee3ae7b2` passed five groups
with and without the local-model compile feature. Bounded source review then
found two test-oracle gaps: Initial JSON-substring parsing ignored unknown
prefix/trailing bytes, and schema recognition accepted an unsupported nested
type or duplicate required-field entry. No positive conformity/permission path
existed, and no production or actual Host input failure was demonstrated.

New frozen regressions at `3a5f2120` produced **1 pass/4 failures**,1.08 test
seconds /10.37 compilation seconds: the non-string required-field case was
already refused; bounded suffix, prefix, duplicate required field and unknown
nested type were not. Original failures remain local and are not relabeled.

Fix and final executable source:
`d373f7984ccacfac753aa6aac3338212d4f1141d`. The observer now compares both the
prefix and exact post-JSON tail against the validated recorded Initial/Repair
pass, using the JSON stream byte offset. Explicit frame-only copy experiments
still preserve that known framing. Exact repair relation and full forwarded
budget remain authoritative. Known schema types and required-field string/
uniqueness/field-set checks close the observed malformed forms. The independent
follow-up review found no further counterexample within those two seams.

| Executed gate at d373 | Exact result | Test / command wall seconds |
|---|---|---:|
| Ten oracle groups, local-model compile feature |10 passed,0 failed,0 ignored; no actual model execution|1.22 test;10.42 compilation|
| Same ten groups, default features |10 passed,0 failed,0 ignored|1.24 test;11.746 command|
| Explicit genuine historical read opt-in, matching local-model compile feature |1 passed,0 failed|20.07 test;28.608 command|
| Eval all-feature/all-target Clippy | Exit0, warnings denied|10.997 command|
| Eval workspace rustfmt check | Exit0|2.481 command|

The repeated feature runs are the same ten tests, not20 independent invariants.
Source was clean and unchanged through each command. Default tests are fake
provider/real Rust Host/Store evidence, not native IPC/WebView/model/device
execution. No frontend/native application, Android JVM/ABI/emulator or physical
device check was repeated for this test-only slice; earlier PR180 evidence
retains its own source IDs. Rust/Cargo1.93.1 on Windows x64, debug information0,
incremental0 and one build job reuse the existing approved environment.

### Genuine old-data compatibility

`crates/locallore-eval/tests/literal_control_historical_review.rs` is an ignored,
explicit developer opt-in reading the genuine preserved PR180 UI5 comparison
and selected run. It does not manufacture old JSON. Fixed SHA256 sentinels pin
the original `run.json` to
`38a27208bf361fbb70450d87a0431435b0e335f08bd43362088c0dc584f85018`
and `selected.json` to
`56caa018f2a0ffab78aa1110eb3293fc501c79edcfbf29db6fe452c275e8f0a3`.
Both supplied absolute paths must refer to those preserved synthetic data.

The registered src module advances the evaluator's source fingerprint; the
integration test file under tests/ alone does not. The command uses the same
local-model compile feature as UI5, so a feature-set difference cannot stand in
for this source boundary. The old full comparison correctly reports
`source_matches=false` while remaining inspectable. Original and both selected
Move receipts retain4→5; inspection grant denial and selected read-only/no-
execution metadata pass. After all capabilities/locks drop, complete original
source and selected file/empty-directory inventories are byte-identical. No
provider, assets, model, writer or native app is invoked. This is historical
read compatibility, not a new UI run or permission to resume old source.

### Reproduce with existing cached dependencies

From repository root, substitute task-owned absolute target/data paths. Serialize
these commands with other heavy work; no install or model is needed.

```powershell
$env:CARGO_BUILD_JOBS='1'; $env:CARGO_INCREMENTAL='0'
$env:CARGO_PROFILE_DEV_DEBUG='0'; $env:CARGO_PROFILE_TEST_DEBUG='0'
$env:LIBSQLITE3_FLAGS=''
$env:TEMP='<task-temp>'; $env:TMP=$env:TEMP
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --lib local_lane::comparison::literal_control_oracle_tests -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --jobs 1 --target-dir <eval-target> --lib local_lane::comparison::literal_control_oracle_tests -- --nocapture --test-threads=1
$env:LOCALLORE_LITERAL_HISTORICAL_COMPARISON='<preserved-UI5-comparison-directory>'
$env:LOCALLORE_LITERAL_HISTORICAL_SELECTED='<preserved-UI5-selected-work-directory>'
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <eval-target> --test literal_control_historical_review -- --ignored --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --all-features --all-targets --jobs 1 --target-dir <eval-target> -- -D warnings
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml --all -- --check
```

The historical opt-in is unavailable without those genuine local artifacts;
ordinary default checks exclude it. These commands neither download nor execute
a model merely because the compile feature is named local-model.

| Local evidence log | SHA256 |
|---|---|
| review-red-first |9e665862e8295e781dde2a6e9e0ae36ef8e822d6a90ff26adcea97016882adec|
| review-green-first |c15460e4c37761f575286278c87a63dbabfd25f161a5813cf5844cd973d8b953|
| default-final |1e12202c398ed6d54c6c436bf7b581d2e6f6adcf4d417103c0baec2888f4953e|
| historical-final |6c1af28b26d5cfbd507ad69949f28662c921985fe890e11b0c10678824885027|
| clippy-final |5e7d35877f0292f8ae2484e71f408787c7c1574844659991f1b0db6ee0d3aa34|
| format-final |e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855|

Names use the local `d07-literal-control-` prefix. Raw generated databases,
captured text, paths and diagnostics stay local. Broader Unicode/escaped input,
consumer closure and real-model literal comparisons remain unimplemented or
unqualified here. Source extraction, rendering/packing and guarded native
execution/replay are qualified in the linked later slices. No D07.04 completion
or human quality gate is awarded.
