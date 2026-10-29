# Narration diagnostic Host read v1: proposed contract

2026-10-29. Refs #9 **M05.03/M05.04**, #29 **D07.04**; may support
#28 D06.01/D06.03/D06.06/D06.07 without claiming those tasks complete.
**CONTRACT ONLY / PROPOSED / NO IMPLEMENTATION / UNCOMPILED / UNRUN.**
Base: `ecc9f7dfe52fd6402284a44774e6532d20e0637c`, after the independently
reviewed native retention slice in [PR #253](https://github.com/OptimumAF/LocalLore/pull/253).
Branch: `plan/d07-narration-diagnostic-host-read-v1`, reusing the released
physical-D selected-case source checkout. Claims before editing:
[#9 comment6494633505](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6494633505),
[#29 comment6494633900](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6494633900).
The author owns only this new document. Root accepts interfaces and allocates
independent FIRST tests before any production. This is no merge/model-run grant.

## Existing seams and the early refusal boundary

Read [HOST_V1](HOST_V1.md), the [Phase1 contract](D07_SCENE_NARRATION_DIAGNOSTICS_CONTRACT_2026-10-28.md),
[native retention contract](D07_NARRATION_DIAGNOSTIC_RETENTION_CONTRACT_2026-10-29.md)
and [retention qualification](D07_NARRATION_DIAGNOSTIC_RETENTION_QUALIFICATION_2026-10-29.md).
Actual source supplies an owned in-memory slot and exact native read; no Host
operation, wire DTO, Eval companion or UI display exists for it at this base.

`Host::call` first checks input bytes, deserializes the closed Envelope/command,
then checks Host version. Add the new operation's native `!story_lab` guard
**immediately after those checks**, before special dispatch, `state.lock`,
`get_session`, `dispatch_traced`, persistence or any source/availability probe.
For a valid new command, a non-Story-Lab Host returns Forbidden even with an
unknown session, stale head, missing source or poisoned State. Preserve existing
TooLarge → Malformed → Version precedence before this guard. Unknown fields,
missing required fields, bad JSON/UTF-8/numeric types and unknown ops remain
Malformed; malformed input is not a valid command for this refusal guarantee.
Existing operations keep their current dispatch and permission behavior.

This promises zero **Host-level StoragePort/source probes and lifecycle changes**
for a denied valid new command. It does not promise zero desktop transport I/O:
`host_call` invokes `WorkspaceState::get` before Host; cold initialization can
create directories, reap previews and open the workspace. The outer transport,
window lease and initialization remain unchanged and outside this contract.

## Proposed command and authorized admission order

Add `HostCommand::TraceNarrationValidationReadV1`, exact wire op
`trace_narration_validation_read_v1`, inside the existing version1 Envelope.
All fields below are required; no JSON observer, owner, handle, privilege,
path, configuration or optional latest-attempt selector is accepted.

| Field | Type and meaning |
| --- | --- |
| `session` | Existing opaque live session ID |
| `scope` | Existing exact Scope |
| `expected_head` | u64 exact current authoritative revision |
| `base_revision` | u64 exact recorded attempt basis; not a current-head assertion |
| `turn` | Exact required turn ID; Core selector rules apply |
| `attempt` | u64 wire integer, checked to native u32; no rounding or fallback |

Keep the existing frontend schema checker's safe-integer policy. Host u64
parsing and exact revision fences do not establish a new Host-wide JavaScript
precision guarantee; no broader numeric contract is changed.

For an authorized Story Lab Host, preserve this order:

1. Existing `get_session` admission: Closed/Scope and StoragePort
   `validate_scope` errors remain distinct. Capture that session's existing
   opaque TraceOwner. Durable mode resumes the exact scope authoritatively;
   fixture mode uses its engine. A different revision returns Stale. Storage
   errors are not converted to diagnostic Unavailable.
2. Check attempt u64→u32, returning InvalidRequest on overflow. Derive the
   actual player identity from the admitted authoritative engine. Construct the
   exact Selection with both required selectors and a native Story Lab Reader.
3. Invoke existing Core `TraceRing::validate_selection` before locking/probing
   trace availability. Preserve Scope/Forbidden/InvalidSelection precedence.
4. Plain `try_lock` on the existing trace: busy or poisoned means an authorized
   Unavailable reply. Do not use `trace_control`, recover a poisoned guard,
   clear poison, disable/configure/clear collection or retry the lock.
5. Call existing `read_narration_validation_for_owner` with the captured owner
   and exact selector. Preserve Core read errors and lifecycle rules. Never
   select the last attempt or fall back to unowned/global/another session data.

Root's explicit reuse refinement permits **only** making the existing
`TraceRing::validate_selection` `pub(crate)`, with its signature/body/semantics
unchanged. No second selector validator, temporary ring, owner or public Core API
is introduced. Overflow precedes selector validation; admission precedes both.
This also prevents invalid selectors becoming Unavailable under busy/poison.

Read-only scope is precise: no new canonical/provider/trace-configuration/attempt
write, enable, generation, validation pass or callback replay. Authorized existing
`get_session` reconciliation can retire/cancel an invalidated attachment on
NotFound; preserve that safety behavior. Whole-Host side-effect freedom is not
promised for authorized admission. No new nonmutating lookup seam is proposed.

## Separate closed response v1

Keep ordinary Host `{version:1,status:"ok",data:...}` and rejected envelopes.
Use separate bounded **serialize-only** DTOs, mapping opaque Core getters through
fixed code matches. Do not make Core metadata Deserialize/Serde or serialize a
future Core enum automatically into this wire version. Proposed `data` shapes:

```text
Bound = {version:1, session, scope, head, base_revision, turn, attempt,
         observer:"player", generation_grant:false}
Unavailable = Bound + {status:"unavailable"}
Recorded = Bound + {status:"recorded",
                    decision:{version:1, outcome, error, reason}}
```

`session` is the exact admitted opaque request ID; `head` is the checked current
authoritative revision; native u32 `attempt` and the remaining binding fields
identify that exact selection. `observer` is the literal player label; the
actual actor identity is derived natively. No owner/handle or new capability is
returned. Unavailable has **no decision key**; Recorded has exactly the four
decision keys above, including required nullable error/reason. No extra fields.
Cap the **entire new-operation Host reply**, including envelope, at 4,096 bytes;
otherwise TooLarge with no truncation. Existing global MAX_OUTPUT is unchanged.

Only diagnostic version1 and actual Phase1 tuple semantics can be Recorded:

| Outcome code | Error code | Reason code |
| --- | --- | --- |
| `accepted` | null | null |
| `cancelled` | `cancelled` | null |
| `stale` | `stale` | null |
| `rejected` | `narration` | `unclassified`, `scene_first_person` or `scene_unapproved_movement` |
| `rejected` | Other allowed actual engine category below | null |

Other allowed rejected error codes are `malformed`, `version`, `scope`, `rule`,
`agency`, `deadline`, `retry_mismatch`, `too_large`, `author_ui_required`,
`clarification_required`, `unknown_reference`, `dead_actor`, `location`,
`inventory`, `resource`, `ability`, `knowledge`, `provider`, `corrupt_history`.
These fixed lower-case codes project the current `ErrorCategory::from_engine`
mapping. Failed/Committed/Running/Unknown and other nondecision outcomes,
unsupported versions/categories/reasons or inconsistent tuples yield Unavailable;
never rewrite a missing/unsupported cause as Unclassified. No arbitrary strings,
text scan, exception detail, excluded actors/counts, prompt or model data enter it.

Recorded reports an actual retained finite decision, not authenticated origin,
final commit/fallback, semantic grounding, privacy or human-quality acceptance.
Unavailable never proves validation did not run. Both negative human assessments
remain **needs improvement**; historical absent causes are not backfilled.

## Independent FIRST oracles and later owned paths

A separate author freezes original synthetic tests before production. Missing
operation/DTO/helper visibility/schema are SETUP/UNCOMPILED, not behavioral RED.
Minimum finite oracles must cover:

1. Real Host → synthetic Engine/Play → RingSink → exact read for both recipes,
   accepted/two finite refusals/precedence/generic/non-Narration decisions.
2. Non-Lab valid-op refusal with spy StoragePort counters and poisoned State:
   zero admission/source calls or lifecycle changes; malformed/oversized/version
   precedence and unchanged existing operations, including Android player Host.
3. Authorized Closed/Scope/storage/NotFound/Stale before selectors; overflow
   before invalid selectors; invalid selector parity under live/busy/poison/
   disabled trace; owner/session/scope/revision/turn/attempt isolation.
4. Busy/poison passive drop without recovery/clear/configure; disabled/retired/
   truncated/cleared/evicted/missing data Unavailable; ordinary finished decisions
   remain distinct from commit; exact retry/prevalidation refusals invent none.
5. Closed bound reply/key sets, missing decision on Unavailable, tuple projection,
   constructible unsupported-metadata controls, 4,096-byte cap and no private
   sentinel leakage. No hypothetical future-version or negative-trait test claim.
6. Unchanged provider/cancellation/canonical/receipt/replay behavior, existing
   trace/capture/PlayRecord/Report4 bytes and observer/generation authority;
   schema regeneration/types and relevant default-Core/Android-host checks.

Future production scope: `crates/locallore/src/host.rs`, the visibility-only line
in `crates/locallore/src/turn_trace.rs`, separately owned NEW
`crates/locallore/src/host/narration_diagnostic_read_review_tests.rs`, regenerated
`apps/desktop/host-v1.schema.json` and `apps/desktop/ui/host.generated.ts`, plus an implementation
update to `docs/desktop/HOST_V1.md` referencing this operation and limits.
Use existing `host_schema` and `build.mjs`; no generator, Tauri command/controller
or Android JNI operation change. Generated types cover requests, not response
decoders. Later frontend decoding and application-owned render tests are separate.

Host/schema edits change Eval source fingerprints: preserve historical
EvaluationSourceMismatch rather than rewrite captures. Eval's existing
`private_read` finds an actual attempt; `turn_execution::execute` reads before
commit/teardown. Future adoption must bind the actual attempt and correct head
at that seam under a separate bounded persistence contract. No Eval persistence,
Report4/StoredTurn4/RecordingFile extension or UI adoption occurs here.

Author checks: source/claims/contract/seam inspection and document scope/whitespace
checks only. No tests, compiler, Cargo, Node, formatter, app, model/assets, device
or desktop operation. Handoff releases only this document; Root records formal
acceptance and allocates independent FIRST tests before implementation. Full
M05.03/M05.04, D07.04 and D06 acceptance remain unchecked.

## Root acceptance for independent FIRST tests — 2026-10-29

Root accepts the exact operation, required fields, bound closed response,
finite tuple/code mapping, admission/error order and 4,096-byte total reply cap.
The original proposal is `3f5f5dc7`, integrated as `801996f2`. Claims:
[#9 comment6494810636](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6494810636),
[#29 comment6494811044](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6494811044).
The only Core change permitted is the existing selector helper's crate-visible
reuse seam; its signature/body/semantics remain fixed. Denied requests must never
enter admission or lock recovery. Authorized existing admission reconciliation
and the outer transport I/O caveat remain explicit.

Allocate independent original synthetic FIRST tests to a different author in
`host/narration_diagnostic_read_review_tests.rs`, with Root-owned test-only
registration later. The production author cannot alter that freeze. Root owns
later execution and integration; no production, schema generation or runtime
operation is authorized before the independent test-source handoff. This is
interface acceptance, not implementation, behavioral RED, milestone or merge
acceptance. Both negative human assessments and unmerged dependencies stand.

## Independent FIRST Host oracle freeze — 2026-10-29

The independent author owns only NEW
`crates/locallore/src/host/narration_diagnostic_read_review_tests.rs` and this
append, on `test/d07-narration-diagnostic-host-read-v1` from exact accepted
`27c2607ac1f80e19eedf49ffd83aa590798d3d66`. Claims before edits:
[#9 comment6494841618](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6494841618),
[#29 comment6494842098](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6494842098).
Root retains registration, separate-author production, generation and execution.
No production, existing test, registration, schema or generated type is changed.

The 555-line source freezes six test functions. SHA256:
`2afb14de702bbcc9ceeeb5519122f6a77750c7324ebb64857b670f4c17a8d94a`.
These are original synthetic fixtures, not private Native4 prose or a model run:

1. Real Host/Engine/Play/RingSink reads for both Scene recipes: accepted, actual
   first-person/movement refusals, first-predicate precedence, earlier generic
   and non-Narration rejection. Read before/after commit preserves the decision;
   provider counts, old trace/private-capture bytes and canonical state remain.
   A synthetic nonliteral player actor ID proves lookup derives the actor while
   the wire observer remains the literal player label.
2. Valid non-Lab requests refuse before poisoned State, admission or trace-poison
   recovery. A real-Engine admission-only spy counts relevant source/lifecycle
   seams; an explicit queued attachment detects owner retirement/cancellation.
   Oversized/malformed/invalid UTF-8, version, required-field, extra-authority,
   numeric-type/u64-overflow and unknown-op precedence remain distinct. Existing
   player-host metadata access is an unchanged-operation control, not Android
   JNI/device execution or a transport-wide zero-I/O assertion.
3. Authorized Closed/Scope, validate/resume failures, NotFound reconciliation
   and Stale precede selector errors. Native overflow precedes the shared Core
   invalid-selector result across disabled/live/busy/poisoned trace states.
   The only proposed visibility dependency is the accepted existing selector
   helper; no new product helper or duplicated authorization predicate is assumed.
4. Exact session/owner/base/turn/attempt binding, returned session, lifecycle,
   ordinary finish versus truncation, count eviction and missing/disabled slots.
   Busy reads use a five-second test-only wait, release the held lock and join
   before asserting, so a blocking regression cannot leave that fixture hanging.
   Poison inspection is test-only: the Host must neither clear poison nor delete
   the retained slot. No app recovery behavior is inferred from a recovered guard.
5. Closed bound/decision fields, nullable keys and generation_grant=false;
   explicit trusted private tuple controls cover all accepted current tuples and
   constructible inconsistent/unsupported outcomes/categories. They are not
   actual Engine failures or authenticated-origin evidence. A long private
   session-map alias tests the 4,096-byte entire-reply cap; it is not a normal
   public session capability. No unsupported future version/reason can be
   constructed with current getters/enums; those branches remain source review.
6. Actual read/no-read provider/request/receipt parity, exact same-Engine retry
   and replay, cancellation after a retained decision, zero-request ability
   guards, unchanged old trace/capture bytes and character knowledge. Separate
   executions normalize only previously accepted receipt stage elapsed values;
   request deadlines remain positive, bounded and nonincreasing. Same-Engine
   receipts/canonical bytes and captured wire objects are never normalized.

The new child is UNREGISTERED; the op/schema and selector visibility are absent
at this base: **SETUP / UNCOMPILED / UNRUN**, never behavioral RED or acceptance.
No hypothetical future-version, negative-Serde-trait, Eval/Report4 execution,
SDK/model, native IPC/render or device proof is manufactured by these tests.
Schema/type generation, existing schema equality/frontend checks, default-Core,
Android-host and broader compatibility checks remain Root-owned and unrun here.
The independent author verifies source/oracles, fixture-path resolution, exact
two-path diff, whitespace and hashes only: no compiler, formatter, Cargo, Node,
browser, app, model/assets, phone or desktop execution. Handoff releases these
two paths to Root with the frozen commit/hash before any production edit.
