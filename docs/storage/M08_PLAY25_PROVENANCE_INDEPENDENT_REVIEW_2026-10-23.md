# Current Play provenance: independent source finding and frozen oracles

Date: 2026-10-23. Scope: M08.03/M08.06 source review under coordinator
allocation; this is neither feature acceptance nor runtime qualification.

Claim: [#12 comment 6378010882](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378010882).
Separate branch `review/m08-play25-provenance`, worktree
`source-play25-provenance-review`, based on
`ff5872780de4403a01f40a9c6e7581be8b5e2893`. Only the new test file and this
document are owned. The coordinator retains all production and integration paths.

## Concrete source finding

The reviewed current pipeline is `976b9096ca430bfc81bebf4a22950bfe0bfe3860`;
consuming stage implementation is
`f5b86d2275f8489728136b3abb03cc2aaf44ac5b`. These production sources are present
in the worktree base above. In `crates/locallore/src/play.rs:495`, current
`validate_record_v25` requires a requested context policy and generic
`PlayContextRecord::valid_v2` validation. `valid_version` at line 376 checks
finite counts, scope/head/observer bindings and generic Raw/Verified consistency,
but does not check the current policy/domain's actual supported coverage shape.

In `context_compiler/verified.rs:237`, current construction with Domain2 **or**
Recent policy returns before proof inspection/recheck/hash. It constructs
`ObservationInput::raw(Unsupported, 0)` then appends actual actor-filtered V2 raw
events. Therefore this branch always produces:

| Field | Actual value |
| --- | --- |
| mode | Raw |
| set_fallback_reason | Unsupported |
| packets_used | 0 |
| packets_fell_back | 0 |
| timespan_fallback_packets | 0 |
| mandatory_fallback_packets | 0 |
| covered_through | 0 |
| raw_delta_after | 0 |
| cached_event_candidates | 0 |

`raw_event_candidates` remains an actual bounded actor-filtered count. It need
not be zero or equal the head. `source_fallback_reason` independently records
the native source's reason; the compiler's Unsupported must not overwrite it.

The generic validator admits three impossible current tuples derived from a
genuine record: Raw/Missing with all other fields unchanged; Raw/Unsupported
with one claimed rejected packet; or finite Verified coverage claiming one
used packet and cached event, without a source-fallback claim. The selected
compiler branch cannot produce any of these. The consuming commit passes this
metadata validator, and strict restore reuses that path before exact regenerated
record comparison, so the source predicts both fresh acceptance and persisted
replay of these impossible metadata claims.

This is a provenance consistency defect. It is **not** evidence of a character
knowledge leak, canonical truth mutation, authenticated cache proof, or actual
cache savings. The coordinator confirmed strict current provenance as intended
and owns the narrow validator correction after frozen execution.

The focused recommendation is an additional current2.5-only shape check for
Domain2 or Recent policy, preserving all existing generic binding/count checks,
native source reason independence, and finite raw-event counts. Leave accepted
historical2.1–2.4 validation/bytes unchanged. Do not reinterpret these counts as
proof or rebuild a second compiler/authority.

## Frozen independent oracles

Test source: `crates/locallore/tests/m08_play25_provenance_review.rs`, commit
`fe97fa94b4a26df2c967637b4d7e95a49d62b5b8`, SHA256
`291a1e4d1c23558afc6bf2e669496ed3d8606b5960a86f370615a8087803a555`.

Two tests cover actual authored Domain2 with Relevant policy and Domain1 with
Recent policy. Each starts with real engine history and executes the actual
bounded Play pipeline using a clearly synthetic scripted provider. A valid
Director Wait command passes actual parsing/mechanics; malformed narrator JSON
uses actual mechanical fallback. Exactly Director/Narrator roles are required.
No accepted Receipt is forged or deserialized. The genuine pipeline record first
has its real Raw/Unsupported tuple, independent native Missing reason, and strict
restore success asserted.

For each of the three closed metadata mutations above, the tests require:

1. Strict restoration of mutated untrusted canonical JSON returns CorruptHistory.
2. Fresh stage/consume refuses the altered public PlayRecord, preserving exact
   accepted-history basis and canonical record count. No extra error-category
   precedence is invented for this fresh refusal.
3. A fresh genuine stage succeeds afterward. Exact recorded retry with canceled
   generation returns the actual receipt with zero provider calls.

The persisted hostile JSON changes only Play metadata in the actual last legacy
receipt or Domain2 wrapper receipt, retaining canonical events/observations and
actual narrative text. It is an untrusted restore input, not construction of an
accepted receipt. The tests share a helper but retain two independently named
policy/domain cases. An early expected refusal failure may stop later assertions;
the coordinator must retain actual logs and rerun the unchanged packet after its
production correction.

## Verification and handoff

Actually performed here: source/Git inspection; `rustfmt --edition 2021` parser
formatting; `rustfmt --edition 2021 --check` and `git diff --check`, all passed.
The new assertions are **UNCOMPILED/UNRUN**. No behavioral RED is claimed.
Git 2.33.0.windows.2, PowerShell 7.6.5 and rustfmt 1.8.0-stable are the inherited
source-work environment. No Cargo/Node/Gradle, model/provider runtime, native
app, device, CUA, desktop control, protected-thread resources, PR, merge or
settings operation was run by this reviewer.

The scripted-provider code is test source only, not a measured model or UI.
Other stage, privacy, budget and legacy checks remain their existing owners'
qualification; source inspection found no additional concrete failure suitable
for a frozen regression in this bounded review.

Next runnable work: coordinator imports this frozen source, executes the focused
test target before modifying production, attributes any compile/fixture failure
honestly, then applies and qualifies its narrow current2.5 provenance check.
The reviewer releases these two new paths at handoff; no production ownership or
milestone acceptance is implied.
