# Current Director forwarded-context budget: contract and frozen oracles

2026-10-23. Refs #29 D07.03/.04; #11 M07.01 prerequisite.
**Original frozen contract / source-only tests.** Base:
`0fd803bcba50fa700efc27072861a51dc6ea3be3`. Coordinator approval of this
specific contract and a subsequent bounded production allocation were received
after the initial03308ea freeze. The initial packet owned only this document and
`crates/locallore/tests/d07_forwarded_budget_review.rs` and changed no production.
The source-only implementation follow-up is recorded at the end. **No passing
post-fix execution or task acceptance is claimed by this reviewer.**

## Demonstrated failure and diagnosis

Coordinator execution of `comparison_runner` at the base produced 5 PASS / 4 FAIL
in 55.47 seconds. `memory_comparison` and `memory_comparison_v2` were not run when
Cargo stopped at the first failing target. The earlier E0061 was corrected only
by supplying the existing character-context call its actual scope/head. Neither
failure is a model-quality result. This reviewer ran no tests or providers.

The retained reference has 8 accepted turns, 3 expected guard rejections and 16
role calls. At head 8, courier-11 passes intent/finite validation, then retrieval
fails TooLarge before any provider role. Courier-12 is **Action**, exactly
`I wait for one tide tick.`; an earlier diagnostic message incorrectly called it
Dialogue. The unchanged suite is authoritative for every kind/text/punctuation.

`play.rs` requests context4096 with reserve512. `context_compiler::fits` charges
the serialized **whole ContextPackage**, including selected IDs, outer sources,
reasons/scores/mandatory flags, diagnostics and accounting. Its token estimate
is ceil(UTF8 bytes / 4), so this permits at most 14,336 full-package bytes.
The distinct full-package byte cap remains24,576; selected-record cap128.

Actual retained head-7 capture:

| Object | Actual UTF8 bytes |
|---|---:|
| Full diagnostic ContextPackage | 14,294 |
| Actual Director `input.context` | 9,189 |
| Actual context-data JSON envelope including player text/inventory/nearby/routes | 9,578 |
| Actual complete Director prompt | 10,121 |
| Actual Director schema | 438 |

The actual generation-request context has only
`compiler_version, observer, revision, records`; each record has only
`kind, source_revision, payload`. All records equal the exact projection of the
captured selection. Payload-internal eligible provenance **is** forwarded; only
outer diagnostic metadata is absent. This is checked against the actual saved
GenerationRequest, not inferred from a mock or reconstructed prompt.

At head 8, recent source8 joins5,6,7, while source4 remains supporting current
energy and source2 supports the learned ability. Mandatory sources are therefore
2,4,5,6,7,8. Replacing an event or dropping supporting evidence is not a fix.
Read-only arithmetic using the actual head-7 package and actual persisted Event8
predicts26 mandatory records /14,886 bytes /3,722 estimated tokens; plus512 is
4,234, over4096 by138. These are **derived numbers, not a newly executed compiler
measurement**. Action11 has no referenced actor alias; proof expansion and the
candidate caps do not explain the failure. The failure occurs before context,
schema, worker or model execution.

Evidence SHA256 bindings (existing local synthetic artifacts, not copied here):

| Artifact | SHA256 |
|---|---|
| `d07-comparison-focused-corrected.log` | `6cd717ec796c40a711ec426585e0d78b141cde8a3b5f8406eb85178ee1a1447e` |
| `reference/reference.json` | `3d1ce67d26f2a0c67415a667e60d217f8c9b30a573e43550572f551980178367` |
| `reference/attempt-07-capture.json` | `2b337e21649834b1194df9f4b8c7f8deaa5558a0bd196c1d8f5ea075b643cda5` |
| Unchanged original suite serialization | `6e7172c6c8bedb4b82b703aac30b7b92c5a924d0203578cb2f027611d7def21a` |

## Proposed closed typed seam

This is a fresh current **Play2.5 Director** admission refinement. Preserve the
existing public `compile`, `compile_cancelled`, `compile_verified_cancelled` and
`compile_policy_cancelled` full-wire contracts, generic Character behavior,
compiler1 bytes/order and every historical Play2.1–2.4 replay/receipt.
Do not globally reinterpret `Budget.estimated_tokens` or repurpose its metrics.

Proposed crate-private signatures (final module placement awaits allocation):

```rust
// Serialize-only borrowed views, private fields. Exact already-forwarded shape.
struct DirectorContextV25<'a> { /* compiler_version, observer, revision, records */ }
struct DirectorRecordV25<'a> { /* kind, source_revision, &Payload */ }

// Opaque pure data, no provider/Host/Store/callback/tool authority.
struct DirectorEnvelopeV25 { /* actual selected player, text/kind, inventory,
                               nearby/routes, current guarded schema, profile */ }
enum DirectorPass { Initial, Repair }
struct RenderedDirectorV25 { /* prompt:String, schema:Value */ }
// Serialize only; public getters for these private finite count fields.
pub struct ForwardedEstimateV1 {
    version: u16, // exactly1
    prompt_bytes: usize,
    schema_bytes: usize,
    repair_extra_bytes: usize,
    actual_prompt_schema_estimated_tokens: u32,
    admission_prompt_schema_estimated_tokens: u32,
    output_tokens: u32,
    template_reserve_tokens: u32,
    estimated_total_tokens: u32,
}
struct DirectorCompilationV25 {
    policy: PolicyCompilation,
    forwarded: ForwardedEstimateV1,
}

impl DirectorEnvelopeV25 {
    // Private builder: actual same Engine+Request+validated Profile and guard
    // result. No caller-supplied prompt/instructions/schema/reserve strings.
    fn render(&self, package: &ContextPackage, pass: DirectorPass)
        -> Result<RenderedDirectorV25, Error>;
    fn estimate_max_pass(&self, package: &ContextPackage)
        -> Result<ForwardedEstimateV1, Error>;
}

// Same compile_inner and mandatory/ranking/whole-unit/budget packing pipeline.
pub(crate) fn compile_for_director_cancelled(
    engine: &Engine, request: &CompileRequest, policy: ContextPolicy,
    proof: Option<&VerifiedCoverage>, frame: &DirectorEnvelopeV25,
    cancel: &dyn Fn() -> bool,
) -> Result<DirectorCompilationV25, CompileError>;

// Public pure arithmetic over actual bytes, not a prompt builder, privilege,
// compiler or provider. Used by the native evaluator after its existing exact
// request/hash/identity checks. The profile is validated by this function too.
pub enum DirectorPassV25 { Initial, Repair }
pub fn director_forwarded_budget_v25(
    profile: &PlayProfile, pass: DirectorPassV25,
    actual_prompt: &str, actual_schema: &serde_json::Value,
) -> Result<ForwardedEstimateV1, Error>;
```

An internal closed `FitBasis::DiagnosticWire | Director(&DirectorEnvelopeV25)`
selects the existing versus new fit check. Existing exported compiler calls
always select DiagnosticWire. Only current fresh Play constructs the opaque
frame and chooses Director; no JSON setting or arbitrary evaluation callback.
The frame is built once from actual current inputs before packing. A small
crate-private pure shared module can avoid a compiler-to-provider dependency;
module placement does not authorize another candidate selector/compiler.

`DirectorCompilationV25` is the separately named **nonpersisted location** of
the admission estimate. Do not add fields to ContextPackage or generic
PolicyCompilation serialization. The estimate type has finite primitive count
fields/closed version1 and Serialize only; it contains no strings, payload or
proof. The public pure helper returns TooLarge on overflow/input bound/admission
failure, rejects Repair when the validated profile permits none, and has no
knowledge/eligibility guarantee. Supply the actual role input, not rebuilt JSON.
Only the opaque frame chooses the existing current Director rendering.

The **one** projection and renderer feed both candidate admission and the actual
GenerationRequest. Do not keep a second independently maintained JSON shape in
Play. Both initial and repair requests use the same rendered frame. Typed actor
eligibility, closed schema and actual same-Engine mandatory data remain Core's
authority. A caller cannot supply a fabricated envelope as a cheaper budget.

## Independent caps and token estimate

Every fit check, including initial mandatory floor, optional addition/removal and
final ordering, must apply both independent conditions:

1. Measure full ContextPackage as today. Preserve its24,576-byte cap,128-record
   cap, candidate limits and bounded omission diagnostics. Leave its
   `serialized_bytes`, `estimated_tokens`, `reserved_tokens` and
   `token_accounting` meaning unchanged: full diagnostic wire, not model tokens.
2. Render the same actual complete Director prompt and schema for the largest
   permitted pass and require its separately labelled estimate <=4096.

For the unchanged pinned profile350 output /repair_limit1, proposed estimate:

```text
ceil((initial_prompt_utf8_bytes + schema_json_utf8_bytes
      + permitted_repair_suffix_utf8_bytes) / 4)
  + actual_output_budget350 + explicit_template_estimate_reserve162 <=4096
```

The reserve remains512 total:350 actual output plus162 explicitly unmeasured
template/envelope reserve. This is a proposed documented attribution of the
existing reserve, not a measured template bound or an increased context limit.
For a smaller supported output budget, preserve total reserve512 rather than
silently admit more data. For the lowest valid context512, preserve existing
`min(512, context_tokens-1)` reserve511; the template estimate is that reserve
minus actual validated Director output tokens (at most350). Validated context
is512..4096, output1..350 and repair0..1, so subtraction is checked and cannot
underflow. Do not widen any public profile bound. No user-configurable reserve
or override.

The exact current repair suffix is114 UTF8 bytes, including its leading newline:

```text
\nPrevious output was malformed. Repair exactly once using the schema. Do not change the player's requested intent.
```

Its incremental estimate is not a separately rounded29-token subtraction:
include its bytes before rounding the whole prompt+schema once. Reserve this
largest permitted pass **before** the first provider role. With repair_limit0
the suffix is absent; no second schema/old output transcript is added today.
Future repair prompt changes must update the one renderer and source-bound tests.

Inventory, nearby actors/routes, instructions, JSON escaping, duplicated original
text and the fixed final request line are already in the rendered prompt and
must be counted exactly once. Schema JSON is separately counted because the
native worker consumes it. GenerationRequest identity/deadline/bookkeeping is
not an extra prompt unless an actual adapter forwards it. Do not accidentally
count only the `context` child, or count the whole textual input envelope twice.
Existing input/prompt/schema byte bounds also remain enforced before provider.
The raw narrator evidence path/output cap is unchanged by this Director-only fix.

`ForwardedEstimateV1` is labelled count-only diagnostics, not proof or gameplay
knowledge. Keep it in the new nonpersisted Director result above rather than
changing historical ContextPackage/receipt DTOs. If current Play's retrieval
`Counts.input_tokens` reports the actual prompt/schema input estimate, use
`TokenBasis::Estimated` and document that source-bound transition from the old
diagnostic-wire count; never use Measured. The full-wire count stays in actual
ContextPackage capture. No generic or historical trace reconstruction is changed.

### Actual capture / D07 validation closure

At0fd, `memory_comparison_v2::CapturedContext::from_host_capture` already checks
request identity, scope/head/observer, output350, deadline, recording prompt/schema
hash equality, and selected-package→actual-forwarded-projection equality. It has
**no** full-package token-fit check to remove. The report builder in
`local_lane/comparison.rs` copies package `estimated_tokens` into
`estimated_context_tokens` only; preserve that field's full-wire meaning.

Required narrow future integration, subject to separate path claim:

- After those unchanged capture/recording/forwarding checks, validate **actual**
  Director initial and repair prompt/schema with the public pure helper. For the
  captured ordered role set, director ordinal0 is Initial and the second Director
  is Repair; do not infer pass from arbitrary player text ending with a suffix.
  Confirm the actual output cap matches the validated profile, and the second
  prompt equals first prompt plus the exact fixed114-byte suffix. Preserve all
  existing privacy/capture availability gates and raw-output hashes.
- Retain separately named `director_estimates: Vec<ForwardedEstimateV1>` on the
  checked private context. Add optional, bounded `forwarded_director_estimates`
  to **new-source** report rows, each derived from actual retained request bytes
  (for example `Option<Vec<Value>>` compared strictly to fresh serialization of
  the checked Serialize-only counts, not a new Deserialize constructor).
  It is not a field to trust from raw saved JSON or a waiver of source binding.
  There are at most two such estimates because repair_limit<=1.
- Preserve old report bytes and viewability using explicit absent-field/history
  dispatch (`serde(default)` and omission for None where appropriate). Old rows
  do not gain invented evidence/estimates, and old source mismatch still refuses
  execution/resume. New-source admitted rows must have verified actual request
  estimates; removing or tampering them must fail current evidence validation.
  Do not force new-source derived Some fields into old None rows during strict
  report reopening and thereby make historical reports unreadable.

Existing frozen Core tests assert actual GenerationRequest byte projection and
complete estimate independently, including successful head8 packages whose
**full-wire** tokens+512 exceed4096. The unchanged actual Host/Store comparison
runner must prove this path also passes the capture bridge. A separately allocated
eval regression must mutate the actual prompt/schema/output or erase a required
new-source estimate and require refusal, while old-source missing estimates stay
viewable. This NEW-Core-file allocation does not authorize edits to that bridge,
report DTOs or their tests; those closure changes remain coordinator-owned.

No promise of true tokenizer/template fit follows from UTF8/4 plus a reserve.
The approved worker's actual tokenizer/template context accounting can still
refuse a role; an authorized source-bound native cohort remains necessary.
Do not claim speed, savings, memory quality, phone behavior or human enjoyment.

## Fresh admission versus historical compatibility

Prompt text, projected payload fields, schema, grounded-prose-v2.2 and the
Play2.5/compiler2/context2/policy tuple need not change. The fresh packing
criterion changes, so execution source fingerprints must change; old reports
remain viewable and cannot resume against a new source binding. Do not relabel
historical raw/verified reports as these policy comparisons.

Historical replay reconstructs accepted commands/evidence and validates the
recorded tuple; it must **not** rerun the new selector/budget rule. Exact recorded
retry precedes fresh configuration/cancellation/admission as before. Current
PlayContextRecord contains no serialized byte/token estimate, so no mandatory
receipt field is required by this proposal. The metadata/provenance closure
already enforced for Domain2/Recent RawUnsupported remains unchanged. Source
fallback labels remain independent from construction policy/cache use.

## Frozen source oracles

The NEW integration test file path-includes the unchanged existing **pure**
`locallore-eval/src/memory_comparison.rs` so it does not duplicate/retune the24
texts or expectations and introduces no dependency or second runner. Its suite
hash is asserted. Synthetic proposal outputs pass through real Play parsing,
finite intent validation, Engine staging/narration validation/commit. No SQL,
forged receipt, direct application of a failed generated outcome or real model.

| Frozen case | Required behavior |
|---|---|
| Generic compiler at actual first8 receipt head | Both policies, original courier11/12 still MandatoryBudget under unchanged direct full-wire API; no canonical mutation |
| Ignored historical baseline-only probe | Run explicitly on0fd before fix: same Play attempts TooLarge,0roles,noCanon; preserve result separately, never rerun as a post-fix acceptance test |
| Fresh current Play at same head | Both policies admit exact original courier11/12,2roles; all six mandatory sources and13current/2known/3relationship/1commitment/1rules rows retained |
| Actual initial and repair GenerationRequests | Exact selection→projection equality; complete envelope/schema+114-byte repair+350output+162 reserve <=4096; same actual repair suffix,3roles with malformed-first synthetic output |
| Original24 through both actual Core policy chains | Each chain21accepted/3exactguards/42roles,head21; no changed text,expected command, guard or zero-role oracle |
| Real mandatory payload too large | Eight independently valid2048-byte player-known propositions alone exhaust4096estimate; before envelope/output, so stillTooLarge/0roles/noCanon |
| Old accepted2.1–2.4 golden histories | Exact receipt Value and recorded retry,0provider calls even cancelled/invalid fresh profile; original2.4 compact bytes/SHA retained |

These are **seven test declarations including the
explicitly ignored historical probe**. They are UNCOMPILED/UNRUN, not RED/PASS.
The new forward-success tests are expected to expose the current fault on0fd;
that expectation is not execution evidence. The actual same Host/Store native
boundary remains covered by unchanged pending evaluator/reference/paired/rollout
tests; this Core file alone is not native IPC, durable Store or UI qualification.
No model execution is authorized by these tests.

Existing compiler1 serialized-byte/golden/verified tests, generic Character
tests, original Play policy/receipt tests and the evaluator's exact runner
oracles must also run unchanged. Do not use this new subset as a replacement.
Suggested coordinator sequence, only after exclusive compiler-slot approval:

```powershell
cargo test --locked --offline -p locallore --test d07_forwarded_budget_review historical_play_head8_refuses_before_any_provider_role -- --ignored --exact
cargo test --locked --offline -p locallore --test d07_forwarded_budget_review
# Preserve baseline output first, approve/allocate production separately, then
# rerun the identical normal test source; keep the historical probe opt-in only.
cargo test --locked --offline -p locallore --test context_compiler_legacy_bytes --test context_compiler --test context_compiler_verified --test m08_context_policy --test m08_context_policy_review --test m08_play25
cargo test --locked --offline -p locallore-eval --all-features --test comparison_runner --test memory_comparison --test memory_comparison_v2
```

Use one job/debug0/incremental0/own target and TEMP per coordinator resource
ownership. Preserve every compile/setup/behavior failure before a narrow fix.
Do not adjust4096/350/caps, weaken mandatory selection, shorten the session,
change expected21+3/42roles or waive actual capture/privacy gates. If the actual
complete mandatory envelope later cannot fit, retain that finite unavailable
protocol/profile result rather than manufacture a successful comparison.

## This packet's checks and remaining gate

Only source reads, bounded existing JSON inspection/read-only SQLite SELECT,
Git operations, and source parser/format/diff/hash checks are permitted here.
No Cargo/Node/Gradle/provider/model/native app/device execution by this reviewer.
The existing executed artifact attribution above belongs to the coordinator.
No task is accepted or checked; no PR/merge/release/desktop-control action.

Next: coordinator review of this precise typed seam/reserve/provenance contract;
then separately claim production paths, execute frozen pre-fix oracles, implement
the smallest shared seam and execute identical tests plus existing compatibility
gates. Native/model and human-quality gates remain separately pending.

## Approved source implementation follow-up

The coordinator approved the typed contract and exclusively allocated existing
`context_compiler.rs`, narrow `context_compiler/policy.rs`, narrow `play.rs`, NEW
`play/director_budget.rs`, and the actual D07 capture/report closure in existing
`memory_comparison_v2.rs` / `local_lane/comparison.rs`. Claims were posted on
#11/#29 before edits. No inference.rs, Engine, Host, Store/schema, runtime,
recording, ledger, scenarios, UI/native or Android path was edited.

The initially requested extra SOURCE_INPUTS entry was unnecessary: actual
`locallore-eval/build.rs` recursively collects every public Rust source under
`locallore/src` (and marks its directories for rebuild). The new module is
therefore included automatically in global evaluation source fingerprints.
No lib.rs/build.rs or duplicate local current-binding entry was changed.

| Ordered commit | Scope |
|---|---|
| `edf4d265f09bf2c1d1d31bbb56b41b75f1d98c84` | Original seven Core test declarations, frozen before production |
| `03308ea14bfa447c0a0f7020db006c01dca3da15` | Original precise contract before production |
| `8c8b74d3e8978c4ad2c810f9899309ba7ff54832` | Four Core paths: one closed frame/projection/renderer, private alternate fit basis, separate nonpersisted estimate, actual forwarding |
| `275483d69cf22d88f56914c4e40544e348250725` | Approved pure exact-repair relation helper; one production suffix constant |
| `83dfd64098344c00f5c36c58e75da41b1db5e957` | Four NEW eval unit oracles frozen before the D07 production delta; existing tests unchanged |
| `c8a8c57a297bd13d1a259de85a7f1f7a7f607727` | Actual checked capture estimates and explicit current/historical report dispatch |
| `d602c476b5d8b94b18b8cf24ee1a3ce715038088` | Explicit collection type annotations, no behavioral/oracle change |
| `8ebdb77ec4b79f88b5a853154044dd05215df131` | Source formatting of those annotations |

The new module renders the exact existing current Director JSON projection,
instructions, final request line and schema, with the fixed114-byte repair
suffix. The same renderer and pure count helper are used at mandatory/optional/
final packing and immediately before actual provider submission. The old
`compile_inner` entry delegates to DiagnosticWire; only current fresh Play can
construct the opaque frame and choose the private Director fit basis. Every
full diagnostic-wire cap and all mandatory selection logic remain unchanged.

`DirectorCompilationV25` is nonpersisted; its `policy` result has the unchanged
generic DTO. The new public Serialize-only count type and pure
`director_forwarded_budget_v25` helper expose no prompt constructor, native
capability, cache proof, actor grant or alternate selector. The approved pure
`director_repair_matches_v25` only compares actual initial/repair strings to the
one fixed renderer suffix. Retrieval input token counts now carry the actual
prompt+schema **Estimated** basis; ContextPackage still captures/report its full
wire byte and token counts. No measured-token claim or narrator-policy change.

Current comparison bindings additionally carry omitted/defaultNone historical
`forwarded_budget_version`, with currentSome1. This dispatch comes from the
validated manifest, not from a missing row field. HistoricalNone validation
preserves its old stable key and omitted transport fields; current-source resume
still requires exact current binding/source equality. Current checked captures
use the shared pure helper on actual retained role bytes after the unchanged
request/recording/projection/privacy checks, including the exact repair relation.
New-source `forwarded_director_estimates` compare against fresh actual capture
counts during checkpoint validation; report-supplied counts are not authority.
Actual unknown-ack evidence remains unknown rather than fabricated.

Four added eval declarations cover UTF8/schema/repair rounding and reserve
counts, invalid-profile/actual-oversize rejection, historical omitted-field/key
validation without execution admission, and an actual first-scene Host/Store/
ScriptedBaseline capture whose removed/tampered estimates must be refused. The
old transport fixture in that test is labelled synthetic compatibility data,
not relabelled historical execution. These new tests need the subsequent D07
production fields/helper and are **uncompiled/unrun source oracles**, not an
independently executable pre-fix RED. Existing eval tests were not edited.

### Actual qualification attribution and next checks

Coordinator actual baseline at executed source `a082dc8` (unchanged pre-fix
production) ran the original frozen Core seven declarations: **4 PASS /2 FAIL /
1 historical probe ignored**, compilation18.99 seconds/tests0.33 seconds. The
head8 and unchanged24 future-success cases failed TooLarge as predicted.
Regular+repair projection/accounting, historical2.1–2.4 replay, actual oversized
mandatory0roles and generic full-wire behavior passed. Coordinator retains
`d07-forwarded-budget-original-red.log`. No frozen assertion was changed.

Reviewer execution: standalone `rustfmt --edition 2021` parser/format and final
`--check`, `git diff --check`, exact path inventory/hash/clean-tree checks only.
One intermediate format check requested wrapping the explicit estimate-vector
type; the next format-only commit corrected it. This was not a Rust compilation
or behavior failure. No Cargo/Node/Gradle/provider/model/native/app/device
execution by this reviewer. No models, assets, workspaces or OS settings changed.

All post-fix Cargo/Clippy/Core compatibility/evaluator/old-report actual-opening
checks remain pending coordinator execution. In addition to the unchanged
commands above, run the four NEW `forwarded_budget_tests` unit cases, then the
existing actual Host/Store reference/paired/rollout suites. Preserve the original
baseline failures, any actual compile failures, and immutable historical reports.
Do not claim full old-report viewability from the pure transport test alone:
open the retained actual pre-fix failed comparison report read-only as well.
Native tokenizer/template fit and the source-bound real-model/human-review gates
remain unavailable until separately authorized and measured.
