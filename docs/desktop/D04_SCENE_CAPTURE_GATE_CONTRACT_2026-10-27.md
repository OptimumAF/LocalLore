# Scene narrator capture gate V1: first frozen contract

2026-10-27. Refs #9 (M05.03), #25 (D04.04), supporting #28/#29.

This is an independently authored, source-only test contract frozen before the
new Eval gate implementation. At first handoff the public gate is absent and
the test is **UNCOMPILED/UNRUN**, not behavioral RED. No compiler, test, model,
Host, Store, UI, device or desktop execution is reported by the test author.
The coordinator owns later implementation, review and serial execution.

## Public native interface

Add a separate public `locallore_eval::scene_capture_v1` module. Its borrowed
`SceneCaptureInputV1<'a>` has exactly these public fields:

| Field | Type |
| --- | --- |
| `before`, `after` | `&'a Engine` |
| `request` | `&'a Request` |
| `expected_recipe` | native `SceneRecipeV1` |
| `expected_profile` | `&'a PlayProfile` |
| `attempt` | `u32` |
| `details_reply` | `&'a serde_json::Value` |
| `recordings` | `&'a [Capture]` |

`check_committed_scene_capture_v1(input)` returns
`Result<CheckedSceneCaptureV1, SceneCaptureErrorV1>`. The checked result is opaque,
has no `Deserialize` or execution-authority conversion, and exposes only:
`version() -> u16` (1), `narrator_prompt_sha256() -> &str`,
`narrator_schema_sha256() -> &str`, `receipt_sha256() -> &str`,
`director_calls() -> u8`, and `fallback() -> bool`.

The error enum is `Copy + Debug + Eq`, with closed variants `Unsupported`,
`Unavailable`, `Malformed`, `Budget`, `SourceBinding`, `ReceiptBinding`,
`RecipeBinding`, `CaptureBinding`, `RecordingMismatch`, and
`NarratorForwardingMismatch`. It need not expose private source strings.

## Narrow meaning of success

Success checks the consistency of a claimed private capture against actual
native Engine snapshots for **one immediate Domain1 scene append**. It does not
authenticate snapshot acquisition, persisted files, model outputs, provider
execution, memory compiler/cache execution or prose quality. The caller must
supply the actual native source and after snapshots. No endpoint, filesystem
path, shell, arbitrary query, observer grant or policy JSON is introduced.

1. Both Engines are Domain1. The request exactly matches the before scope/head;
   it is not already recorded there. The after Engine extends the entire before
   accepted-history basis and has exactly one additional canonical record.
2. `after.recorded(request)` supplies the actual final receipt. Expected native
   recipe/profile match its complete new tuple. An old recipe is never relabeled.
3. Regenerate scene staging from the actual before Engine/request/proposal,
   bind the expected native recipe, and render the actual profile through Core.
   Consume/revalidate the bound PlayRecord on a clone and require exact receipt
   equality plus complete resulting accepted-history basis equality to after.
   Core owns frame, context, presentation, narration and fallback validation.
4. Require exactly one parsed proposal, approved plan and accepted-candidate
   artifact matching those actual native values. In particular, compare the
   entire captured candidate to the actual receipt, including stage timings;
   no field normalization or diagnostic receipt constructor is allowed.
5. Require exact capture identity, scope, observer, base, turn and attempt;
   recorded and bounded collector artifacts; valid contiguous ordinals; known
   kinds; and no duplicate structural artifacts. Require complete roles:
   one Director plus at most one repair Director, then one Narrator. The count
   is the actual record's repairs plus one. Match recordings by index, role,
   hashes and multiplicity rather than unordered membership.
6. Compare the actual narrator prompt string and schema Value to the regenerated
   renderer output, then compare recording hashes. Schema bytes mean compact
   serde JSON encoding of captured schema content, not original lexical JSON
   whitespace/order. Rehashing a forged narrator prompt/schema cannot admit it.
7. Verify each generation envelope's exact role token budget from the expected
   profile, output byte limit 16384, pending-poll limit 30000, profile ID and
   existing schema ID. Deadline must be positive and no larger than the profile
   deadline; elapsed remaining time cannot be reconstructed from these inputs.
   This contract positively exercises Director350/Narrator100.

Use the existing full-prefix APIs, public scene stage/bind/render/commit APIs
and bounded collector helpers. Do not duplicate a memory compiler or renderer,
deserialize a Receipt, rebuild a fake approved plan or create a canonical writer.

## Error classification

The independent tests use isolated faults with specific errors. Domain checks
precede ordinary binding so Domain2 is always `Unsupported`; top-level capture
size refusal is `Budget`. Native request/prestate/retry/nonprefix/two-append
mismatch is `SourceBinding`. A missing commit/zero append is `Unavailable`.
An actual old recipe or wrong expected native recipe/profile is `RecipeBinding`.
Changed captured proposal/approved/candidate is `ReceiptBinding`. Missing required
capture artifacts or disabled/expired/not-retained/truncated detail is
`Unavailable`. Unknown kinds, bad ordinals or duplicate structural artifacts are
`Malformed`. Identity and generation-envelope fields/budgets are `CaptureBinding`.
Indexed recording hashes/role counts/order/multiplicity are `RecordingMismatch`.
A hash-consistent narrator input different from the regenerated input is
`NarratorForwardingMismatch`. Multi-fault inputs do not acquire authority from
which error wins; where tests isolate a fault, retain the documented category.

## Genuine Core collector fixture and explicit limits

`crates/locallore-eval/tests/scene_capture_v1.rs` calls actual
`execute_traced_with_scene_recipe_v1` with an ordinary deterministic provider.
The provider records actual `GenerationRequest`s at `poll` and returns synthetic
bounded replies; it does not construct prompt/context/schema. It uses actual
`TraceOwner`, `TraceRing::configure_details`, `begin_for_owner`, `RingSink`, and
`read_details_for_owner` with a native Story Lab Reader. Only the outer
`status/data/details` wrapper is manually written around the real DetailSnapshot.

This is actual Core in-memory canonical append and opt-in collector plumbing,
**not Host dispatch, Store durability, native WebView, Android or model execution**.
Separate actual Host integration tests must later obtain snapshots/captures from
the production native scene-selection path. Test-mutated copies are diagnostic
adversarial inputs and are never described as actual forwarded inputs.

`details.exact_reconstruction` remains false, including genuine complete captures.
The new result states its own narrow check and neither requires nor rewrites
that old flag. Existing `capture_envelope::generation` hardcodes 350 tokens for
both roles; preserve its historical semantics and use a separate role-aware
checker here. Existing Protocol3 descriptors, gates, producers and reports remain
unchanged. No historical gate becomes scene-source evidence retroactively.

The two new scene arms deliberately share the narrator renderer. Identical
proposal/frame/presentation can yield identical narrator bytes, and that is a
positive test. Cross-arm refusal binds expected recipe to the actual receipt's
construction/context tuple, not an invented arm-specific narrator tag.

Director envelopes are checked for identity, budgets, schema ID, order and
recording hashes only. Director prompt and schema content are not regenerated
from source. The contract deliberately admits a self-consistent
Director prompt suffix forgery when all narrator/native bindings remain valid;
it does not claim to reconstruct Director source. It also admits a self-consistent
replacement raw-output diagnostic. These positive limit tests make clear that
neither output origin nor a model-to-receipt causal chain is authenticated.
Memory provenance counts and selected-context claims do not prove compiler or
cache execution. A later stronger Director gate needs its own reconstructible
source contract and tests. Mechanical fallback remains explicitly labeled and
does not imply generated prose passed validation or human quality review.

## Frozen checks and later command

The initial source contains seventeen test functions, including a sixteen-case
positive matrix: both recipes × presentation absent/present × repair/no repair ×
generated/mechanical fallback. Additional cases cover exact unequal role budgets,
identical cross-arm narrator inputs, rehashed narrator forgeries, actual old
recipe, mismatched expected profile/policy, full candidate/proposal/approved
binding, missing/altered scene provenance, changed seed at equal scope/head,
different full prefixes with equal seed/scope/head/projection, zero/two appends
and retry basis, failed/cancelled generation, unavailable captures, actual
Domain2 correction, identity/envelope faults, recording order/multiplicity,
unknown/duplicate artifacts, budgets and explicit Director/raw-output limits.

After implementing the frozen API, the coordinator can run:

```powershell
cargo test --manifest-path crates/locallore-eval/Cargo.toml --test scene_capture_v1
```

Record source hashes, actual command/results, compilation/setup failures and
subsequent calibration separately. A missing API or fixture/API mistake is a
compilation/setup prerequisite, not behavioral RED. Keep previous independent
assertions intact when calibrating against actual public Core APIs. No new model,
quality, native, Android, performance or release gate is satisfied by this source
freeze or by later deterministic Core test success alone.
