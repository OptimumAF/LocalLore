# Full Protocol4 narration diagnostic companion v1: proposed contract

2026-10-29. Refs #29 **D07.04**, supporting #9 **M05.03/M05.04**.
**CONTRACT ONLY / PROPOSED / NO IMPLEMENTATION / UNCOMPILED / UNRUN.**
Base: `771904dd5fc1b4573e6ae8008c0ae6cff9ccd988`, sealed Host gate
[PR #255](https://github.com/OptimumAF/LocalLore/pull/255).
Branch: `plan/d07-narration-diagnostic-eval-companion-v1`, released physical-D
selected-case source checkout. Claims before editing:
[#29 comment6496635254](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6496635254),
[#9 comment6496635611](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6496635611).
This author owns only this new proposal. Root must accept names, caps, schema and
ordering, then freeze independent FIRST tests before different-author production.
No generation/cohort, semantic-policy, quality, device or merge grant follows.

## Smallest scope and actual storage seams

Propose an explicitly opt-in **full Protocol4 only** companion artifact protocol1
with its own closed codec and strict native reader. Preserve old Report4,
StoredTurn4, RecordingFile, capture-v1 and trace-v1 schemas/semantics exactly.
No opaque JSON field, new directory, catalog index/version, selected-run feature,
Host operation, UI/controller or provider implementation is added.

Source audit found no `ResultStore` symbol or atomic-rename publisher. Actual
Eval seams are `ordinary`/`read`/`write_new` in `lib.rs` and `saved`/`decode` in
`comparison.rs`. `write_new` uses create_new, write_all and sync_all. Reuse those
bounded create-new/read operations; do not claim atomic publication or invent a
competing persistence engine. Failed writes may leave partial files; preserve
them and refuse their evidence. Existing writer locks, directory pins and
ordinary-file checks remain required; no OS/crash/forensic-erasure guarantee.

Proposed native Rust entries `run_comparison_with_narration_diagnostics_v1` and
`run_native_comparison_with_narration_diagnostics_v1` reuse existing Scene4
execution/reservation ownership and return the unchanged ComparisonReportV4.
Existing entries/defaults opt out: same old wire/behavior and no extra Host,
provider, cancellation/deadline calls or companion probes/writes. New source
fingerprints retain their actual provenance; historical captures are not relabeled.

## Declaration, fixed files and budgets

All following names/caps are proposed for Root acceptance:

| File / limit | Proposed bound |
| --- | --- |
| Root `narration-diagnostics-v1.json` | One create-new closed declaration, at most 4,096 bytes |
| Each arm `narration-diagnostic-v1-{admission:02}.json` | Existing left/right directories; at most 7,168 bytes/file |
| Observations | Admission 0..31 per arm; at most 32/arm, 64/run |
| Entire companion namespace | At most 65 files and 512KiB, including partial files |
| Observed Host reply | Existing 4,096-byte whole Host-envelope cap remains |

The worst valid file caps total 452KiB (4KiB + 64×7KiB), below 512KiB. Existing
Eval MAX_REPORT is 2MiB; desktop boundary quotas are 32MiB/run and 256MiB/library,
with 8,192 inventory entries/depth 6. The development full-inventory helper's
8MiB/file/128MiB scan limit is separate evidence tooling, not a larger runtime
quota. Companion bytes/files count toward existing quotas; these bounds grant
no extra space, admissions, roles, runtime or retries. Refuse insufficient quota;
retain existing ceilings/free-space checks and reject overflow with checked sums.

Create a declaration only for a new run under its existing run lock, after
run.json/arm setup but before invocation/model reservation/start. Main arms must
have no historical checkpoints, admissions or invocations; copied validated
paired-reference inputs do not enroll historical main-arm work. Never retrofit
a declaration to an existing checkpoint set. Opt-in resume requires an existing
valid declaration matching the exact run/source; missing, partial or mismatched
declarations refuse opt-in continuation before provider/reservation activity.
Completed opt-in resume retains the existing zero-generation/reservation path.
Default opt-out remains unaware of companion files: its old behavior is unchanged.
A declaration is not a coverage promise; later missing observations stay missing.

Declaration keys are exactly `version:1`,
`kind:"full_scene_narration_diagnostics_v1"`, `source_protocol_version:4`,
`run_binding_sha256`, `run_manifest_sha256`, `source_sha256`,
`harvest:"first_exact_precommit_host_v1"`, `generation_grant:false`.
Hashes bind existing finite run/source bytes, not a copied profile/source object.
No mutable count/aggregate index, timestamp, owner, path or arbitrary extension.

## One actual harvest, before commit

`comparison.rs::private_read` currently obtains a precommit trace using BEFORE
head and selects an attempt for capture. For opt-in only, validate that first
snapshot and latch its actual exact scope/base_revision/turn/native-player
identity plus native u32 attempt **once**. Selection may use the last matching
entry in that already exact snapshot, never an unfiltered global/latest attempt.
Do not infer attempt from row index, admission, file naming or a later report.
Unconstructible/invalid exact selection means no observation and no new Host call.

At the existing `turn_execution.rs` precommit harvest, call
`trace_narration_validation_read_v1` at most once with that session/attempt,
expected_head=actual BEFORE head and immutable request base revision. Decode the
complete bounded reply against its queried tuple. No polling/retry/second read
to seek a reason. Carry only that immutable result in the live ActualTurn.
Latch malformed/unsupported harvest as a diagnostic-only error; do not return
early from execute or change its existing cancel/commit path. Surface that error
only after the checkpoint/settlement/teardown sequence below.
The existing after-head trace replacement near the end of execute remains for
old reporting; it **must not** reselect an attempt or replace this decision.
No provider recorder, text scan, Core opaque constructor/Serde, replay or Engine
reconstruction supplies the cause. Opt-in overhead stays within existing clocks
and budgets; no exclusion, deadline reset/extension or additional model allowance.

Each observation's exact closed keys are `version:1`,
`kind:"full_scene_narration_observation_v1"`, `declaration_sha256`,
`run_binding_sha256`, `source_sha256`, `arm`, `index`, `admission`,
`checkpoint_sha256`, `host_query`, `host_reply`, `generation_grant:false`.
Index is 0..23; arm is left/right; admission is the actual ledger admission.
Hashes are 64 lower-case hex characters. Session/scope/turn IDs are bounded to
1..64 bytes using the accepted native identifier forms; head/base are exact u64,
attempt u32. The normal opaque session is data, never a restored capability.

`host_query` is its own typed closed single-operation version1 Envelope with all
six required fields. `host_reply` is a separately typed closed Host-v1 envelope:
ok/recorded decision, ok/unavailable with no decision, or rejected/fixed error.
All ok binding fields must equal the query; accepted/rejected/cancelled/stale
decision tuples and nullable fields follow the
[Host contract](D07_NARRATION_DIAGNOSTIC_HOST_READ_CONTRACT_2026-10-29.md) exactly.
Do not deserialize arbitrary HostCommand variants or store opaque serde_json::Value.
No private prose, prompts, exception text, paths or matched words are stored.

Proposed closed rejection codes are TooLarge, Malformed, Version, Forbidden,
Closed, Scope, Stale, InvalidRequest, InvalidSelection, Internal; current fixed
storage/replay codes Io, Database, ForeignDatabase, FutureVersion, SchemaMismatch,
BackupRequired, BackupExists, Busy, InvalidSeed, DuplicateStory, NotFound,
InvalidInput, Integrity, UnknownTurn, RetryMismatch, Cancelled, Full; and current
fixed Engine codes Agency, AuthorUiRequired, ClarificationRequired,
UnknownReference, DeadActor, Location, Inventory, Resource, Ability, Knowledge,
Rule, Provider, Timeout, Narration, CorruptHistory. The existing synthetic Host
admission category Storage may also be represented explicitly. Unknown future
wire fields/versions/codes or inconsistent tuples are companion errors, not
invented Unclassified/HostUnavailable. No arbitrary error-string passthrough.

## Checkpoint, settlement, failure and recovery order

Preserve actual ownership in `ActualTurn::checkpoint_and_settle` and OwnedHost
Drop. Freeze this opt-in order:

1. Existing canonical execution/lookup determines the real receipt/phase; build
   the unchanged StoredTurn4 and save its checkpoint using existing saved bytes.
2. Existing ledger settlement succeeds. No diagnostic write precedes checkpoint
   or settlement. Hash the **exact persisted checkpoint bytes**, not an alternate
   pretty/canonical reconstruction, and bind the actual reservation/admission.
3. Create-new the observation file, if a valid one-time harvest exists. Validate
   any already-present file strictly; identical valid bytes may be reused, never
   overwritten. Conflicting/partial/malformed existing bytes refuse new evidence.
4. Run existing capture revoke/Host close and normal Drop cleanup even if the
   companion write fails. Only then return a companion-evidence error/abort.

A companion failure may stop remaining evaluation evidence; it cannot roll back
a committed receipt, rewrite Report4 phase, refund reservations, re-enter a
provider or reset a deadline. Existing checkpoint/settlement failures retain
their original behavior and teardown. Do not pretend filesystem writes are
hard-time bounded or that this sequence is one atomic transaction.

| Crash/state | Required diagnostic meaning |
| --- | --- |
| No declaration | NoDeclaration, including legacy absence; no inferred runtime cause |
| Declared, no bound observation file | NoObservation; never actual HostUnavailable |
| Actual supported Host unavailable reply retained | HostUnavailable |
| Actual supported Host rejected reply retained | HostRejected; not a validator decision |
| Actual supported recorded reply retained | Recorded finite decision; not final commit |
| Present partial/malformed/unsupported/orphan/mismatched file | Refused companion evidence; preserve bytes |

`ready_turn4` deliberately has no trace/capture/recording/admission. Never open a
Host/model or replay validation to fill recovery gaps. Crash after checkpoint/
settlement but before publication leaves NoObservation. A surviving valid file
is read/reused byte-for-byte only against its original exact checkpoint; a
recovered replacement checkpoint cannot adopt it by turn name. Do not manufacture
new admission/attempt/session metadata or repair a partial file on resume.

## Strict authorized cold reader, separate from old readers

Propose `scene_v4::desktop_api::narration_diagnostic_v1` using the existing
OpenedComparison capability and raw-evidence access seam. Native inspection
grant plus Omniscient are checked **before binding, declaration, file or source
probes**. Any cold-open wrapper performs the same refusal before opening a
source. File declarations never grant access; all results remain read-only with
generation_grant=false. No new registry/owner or renderer path/permission API.

After authorization, revalidate the existing full Protocol4 snapshot/run lock,
source/checkpoint/ledger/receipt integrity and immutable selection as the current
reader does. Reject selected roots and other protocols. Validate all companion
names/counts/bytes with strict closed codec, duplicate-key/field/version checks,
ordinary-file/reparse/pin/single-link protections and bounded post-read lengths.
The generic ordinary helper alone does not establish pinned/single-link safety;
reuse the existing narrow file guards where possible under Root's later scope.
Reject aliases, duplicate arm/admission identities and unknown namespace names.
Bind declaration hashes, current checkpoint digest, arm/index/admission and
actual reservation/settlement. Match the latched attempt to the checkpoint's
exact trace identity and authoritative native player; never select a new latest
attempt. Session equality is query/reply consistency, not independent historical
authentication. Coordinated rewrites are not defeated by unkeyed hashes.

Do not add fields to old summaries/evidence. Full readers currently tolerate
extra ordinary files but do not validate them as new cause evidence; selected
roots whitelist filenames, and catalogs have closed index versions. No selected,
catalog or UI adoption is implicit. New reader errors cannot invalidate/rephase
the old report or mutate any file. Missing evidence never proves validation did
not run or that Host was not called. Rejected narration can commit mechanical fallback; accepted narration
can later cancel. No grounding, privacy, origin or human-quality verdict follows.

## Independent FIRST scope and next gate

Proposed later owned paths: NEW
`crates/locallore-eval/src/narration_diagnostic_companion_v1.rs` closed codec;
narrow registration/private_read in comparison.rs, live harvest/checkpoint hook
in turn_execution.rs, opt-in Scene4/native entry plumbing and the separate
Scene4 desktop reader method. Existing persistence, quotas, provider/factory,
Host/schema, catalog/index and old wire implementations are not replaced.

A different author must FIRST freeze original synthetic actual Host harvest →
artifact → cold-read cases using existing LaneFactory/TestFault, scene inventory
and noncommit/privacy fixtures. Include both recipes and actual recorded/
unavailable/rejected/no-observation outcomes; source/arm/index/admission/
checkpoint/attempt/head/session tampering; unknown fields/versions/duplicate
keys/codes; each file/aggregate/count boundary; existing-byte conflicts and
symlink/alias refusal; all crash boundaries, recovery without backfill, cleanup
on failure, unchanged old wires/default call counts, provider/deadline/canonical
invariants and authorization-before-probe sentinels. Trusted metadata controls
are not actual Engine failures or authenticated-origin proof. Missing APIs/
registration remain SETUP/UNCOMPILED, never behavioral RED.

Root accepts/amends this proposal, then allocates tests and different-author
production plus actual Rust/strict-lint/format/compatibility and independent
review. Author work here is source/claims/Git/whitespace inspection only: no
compiler, formatter, Cargo, Node, app, asset/model, device or desktop operation.
Both human assessments remain **needs improvement**; original 30 absent causes,
literal-v1 comparator limits and the finite semantic gap stay unchanged. Full
D07.04/M05.03/M05.04 and dependency acceptance remain unchecked. Only this
document is released at handoff; no cohort or capture repair is authorized.
