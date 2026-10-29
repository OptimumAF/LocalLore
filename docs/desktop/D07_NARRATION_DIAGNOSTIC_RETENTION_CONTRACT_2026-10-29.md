# Native narration diagnostic retention: proposed contract

2026-10-29. Refs #29 **D07.04**, supporting #9 **M05.03/M05.04** and D06.
**CONTRACT ONLY / PROPOSED / NO IMPLEMENTATION / UNCOMPILED / UNRUN.**
Base: `223b6a3f22eb35d9c2d1aedb7b6ed4e5c7f8ea19`.
Branch: `plan/d07-narration-diagnostic-retention`, reusing the released physical-D
`source-d07-reader-native-qualification` checkout; previous branches preserved.
Claims before editing: [#9 comment6492157343](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6492157343)
and [#29 comment6492157703](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6492157703).
This author owns only this new document. Root owns interface acceptance, later
allocations, integration and execution. Phase1 must finish its qualification gate
before later production. This proposal authorizes no implementation or model run.

## Dependency and purpose

The [Phase1 contract](D07_SCENE_NARRATION_DIAGNOSTICS_CONTRACT_2026-10-28.md)
defines the opaque Copy `NarrationValidationDiagnosticV1`, three finite reason
codes and default-no-op `TraceSink::narration_validation`. Production is present
at the stated base; broader qualification is Root-owned and not inferred here.
Phase1 emits one actual precommit decision after the original stage callback and
before the existing Scene4 cancellation poll. RingSink currently discards it.

This slice proposes retaining that actual callback under the existing native
attempt identity. It does not diagnose text independently, prove semantic safety
or report final commit/fallback. Historical 30 generic narration rejections have
no detailed runtime causes: preserve them as unavailable, without backfill,
revalidation, replay-for-diagnosis, capture repair or another model cohort.
Both negative human assessments remain unchanged; no quality acceptance follows.

## Existing seams and compatibility boundaries

`crates/locallore/src/turn_trace.rs` already supplies RingSink's best-effort lock,
opaque `AttemptHandle`, private `LiveAttempt`, `TraceOwner`, `Reader`, `Selection`,
owner-filtered reads, clear/disable and bounded eviction. Reuse these identities;
do not create a second registry, handle, map, owner, clock or authority.

Keep serialized `Attempt`, `Snapshot`, `StageRecord` and trace version1 unchanged.
The exact-key decoder in `apps/desktop/ui/trace-model.ts` rejects extra fields.
Keep PlayRecord, Host commands/schema, Report4 and their default behavior unchanged.
Do not add an artifact to capture-v1: `scene_capture_v1.rs` rejects unknown kinds,
and `ui/capture-model.ts` freezes the same seven kinds. Provider recording sees
requests/outputs, not the later validator decision; it cannot supply its cause.

## Proposed native collection

Add exactly one private `Option<NarrationValidationDiagnosticV1>` to each existing
`LiveAttempt`, initialized to None. No serialized field or allocation-growing
history is added. Freeze `size_of::<Option<NarrationValidationDiagnosticV1>>() <= 32`
bytes, so retained diagnostic payload is at most `32 * MAX_ATTEMPTS` (1,024 bytes
at the current 32-attempt ceiling). This separate fixed payload does not change
the old serialized byte budget, stage budget or any eviction policy.

Proposed private method on `TraceRing`:

```rust
fn record_narration_validation(
    &mut self,
    handle: &AttemptHandle,
    diagnostic: NarrationValidationDiagnosticV1,
) -> HookStatus;
```

RingSink overrides only the new hook, obtains its existing `try_lock` and calls
this method. Busy/poisoned lock or rejected metadata is a passive drop; it never
changes an Engine Result, retries a callback or invokes a provider/cancel poll.
Preserve the existing hook panic isolation and overhead accounting in Play.

A first write requires enabled collection, the current opaque handle, a retained
attempt with a live existing `Some(TraceOwner)`, Running/nontruncated state and
an empty slot. Unowned `begin` attempts do not gain diagnostic access. The last
retained stage must be the actual NarrationValidation measurement with identical
outcome/error. A missing/dropped/mismatched stage cannot be synthesized or repaired.
No Engine validation, text scan, stage append, timing update or extra poll occurs.

First valid write wins. Duplicate or late writes return existing Dropped status,
leave the first value unchanged and add no loss counter. Stage mismatch returns
InvalidMetadata; disabled/stale/foreign/truncated cases use existing hook statuses.
Hook statuses remain diagnostic only and never become gameplay outcomes.

## Proposed separate native read interface

Names and signatures below require Root acceptance before independent test work:

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum NarrationValidationReadV1 {
    Unavailable,
    Recorded(NarrationValidationDiagnosticV1),
}

pub fn read_narration_validation_for_owner(
    &self,
    owner: &TraceOwner,
    selection: &Selection,
    reader: &Reader,
) -> Result<NarrationValidationReadV1, ReadError>;
```

The method belongs to TraceRing. Neither result nor existing diagnostic gains
Serde, public field construction, raw text, path or serialized proof authority.
The exact selected attempt supplies attribution; the result creates no identity.
Require both `selection.turn` and `selection.attempt`; otherwise InvalidSelection.
Reuse existing scope/observer/selection validation and owner filtering before any
availability probe, preserving Scope/Forbidden/InvalidSelection errors. A foreign
owner's data must be indistinguishable from absent data under an authorized read.
No fallback from an owned read to unowned/global data is permitted.

Recorded requires enabled collection, live matching owner, retained nontruncated
attempt and a stored callback. It remains readable after ordinary finish, including
a later Cancelled/Failed result: the earlier finite decision is not relabeled.
Writes after finish are refused. Any truncation, disable, clear, owner retirement,
eviction, stale/foreign handle, busy/drop or absence yields Unavailable through
the authorized native integration; it never means Unclassified, accepted, no
fallback, or "validation did not run". Actual stored Unclassified remains valid
only when Phase1 emitted that classification for an actual Narration error.

No independent retention period is introduced. The slot follows the existing
attempt's bounded lifetime and teardown. Clear/disable/owner cleanup/eviction
remove it with that attempt; retired-owner and truncated reads refuse it even
before cleanup. No new forensic-erasure, OS paging or TTL guarantee is made.
Read locking remains the caller's bounded native concern; busy means unavailable,
never permission to block/retry indefinitely or weaken authorization.

## Independent deterministic freeze required before production

Root first accepts the exact interface and lifecycle decisions, then allocates
new original synthetic tests to a different author before production edits.
Missing APIs or registration are SETUP/UNCOMPILED, never behavioral RED. Required
oracles exercise actual Engine/Play -> RingSink -> native read, not a mocked
diagnostic or provider-derived explanation:

1. Accepted, both finite refusals, first-predicate precedence, generic Narration
   and other actual errors retain their exact Phase1 outcomes/errors/reasons.
2. Matching stage first; mismatched/missing stage refuses; first write wins;
   duplicate/late/foreign writes cannot replace, revive or transfer a value.
3. Read after finish succeeds; truncation, disable/re-enable, clear, owner cleanup
   and retirement, eviction, stale/unowned handles, busy/poisoned locks and absence
   stay unavailable. Scope/observer/owner isolation applies before disclosure.
4. Fixed slot size and attempt ceiling hold without changing old count/byte
   budgets. Test pressure/eviction and complete old trace-v1 serialized key sets.
5. Stage/new-hook panic and cancellation keep existing fallback, canonical bytes,
   calls and polls. Accepted diagnostic followed by cancellation is not a commit.
   Recorded retries and prevalidation refusals fabricate no diagnostic event.
6. Synthetic secret sentinels never enter metadata. Existing receipts, PlayRecord,
   report/capture wire fixtures and observer/generation authority remain unchanged;
   normalize only previously agreed independent elapsed-time measurements.

Root owns later focused/broad Rust and compatibility execution, strict lint/format,
independent source review and qualification evidence. No model/device/render
acceptance can be manufactured by these deterministic collector tests.

## Later adapters, separately contracted and claimed

After this native slice's gate, propose a versioned opt-in Host read using current
session/head/owner checks and conservatively Story Lab privilege. It must not
redefine existing trace-v1/capture-v1 responses or grant character knowledge.
Then contract a bounded, source/attempt-bound Eval companion format and explicit
legacy absence; closed RecordingFile/StoredTurn4/Report4 stay unchanged unless an
explicit replacement version is accepted. Existing `private_read` and
`turn_execution::execute` are the actual Host observation seams before teardown.
Do not use the provider recorder or an opaque JSON field as a schema bypass.

A later D06 adapter must retain the existing validated read capability, access
refusal before source probing, integrity/budget checks and generation_grant=false.
Typed frontend decoding and the selected-row context may display actual metadata
only after a separate contract and render gate. Hashes and typed metadata establish
consistency, not authenticated origin, semantic validity or inspection privileges.

Author checks: current public ticket/claim reads, source/interface audit, clean
base/branch preservation, document-only diff/whitespace/path checks. No production,
tests, compiler, Cargo, Node, formatter, app, model, assets, phone or desktop action.
Handoff is this proposed contract commit; ownership is released to Root afterward.
Root must resolve/record acceptance of names, slot/status rules and test allocation.
D07.04/M05.03/M05.04 remain unchecked; no full cause-reporting completion is claimed.
