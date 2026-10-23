# Durable memory job integration tests — 2026-10-23

Refs #11 **M07.03/.04**, supporting #29 prerequisites; in progress, **uncompiled**.
Claims [#11 comment6373133015](https://github.com/OptimumAF/LocalLore/issues/11#issuecomment-6373133015)
and [#29 comment6373133453](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6373133453).
Coordinator-delegated author `/root/resource_metrics_review`, isolated
`test/m07-memory-jobs` / `source-memory-jobs-tests`, accepted base
`e534f01e107a48642370fa0a976fa25c747baba9`. Own only new
`crates/locallore-storage/tests/memory_jobs_integration.rs` and this document.
All production, migrations, schema, existing tests and integration remain
coordinator-owned. No milestone acceptance, PR or merge by this author.

## Initial oracle freeze before execution

The first test revision is frozen before compiler/test execution. It imports
coordinator production `e98ff6a0f98bb8b561db8da1b26b2f9d7a99417c` as local
dependency `83f33d7`; none of those production files was authored/changed here.
The initial frozen test includes 21 parent tests and one deliberately ignored,
parent-spawned helper. The helper is invoked only by the bounded child checkpoint
test; it is not an ignored qualification gate. Source and oracle follow-ups must
preserve this initial revision and explain any contract correction before first
execution. No passing execution is claimed for any revision yet.

The public native API under test is `MemoryJobRequest`, opaque cloneable
`MemoryJobHandle::id`, `MemoryJobInfo`, status/failure enums and Store methods
`ensure_memory_job`, `memory_job_status`, `prepare_memory_job_step`,
`publish_memory_job_step`, `cancel_memory_job`, `prune_memory_job`, and
`context_snapshot`. Tests obtain all opaque handles/prepared tokens from actual
Store calls, never deserialize or construct them. No model, provider, app or
alternate cache implementation exists in this test.

### Fixed synthetic sources

Each primary lifecycle fixture creates an original garden seed with player,
present agent and absent same-name actor. Ordinary typed Engine/Store
request/proposal/preview/begin/commit accepts exactly **384 events /96 receipts**
in four-event turns. Event1 is a promise, event2 player-only speech, remaining
events ordinary observations. Every Store receipt must equal both actual preview
and an ordinary Engine commit. No SQL creates or modifies canonical history,
seeds, projections, witnesses, scopes or receipts. Maintenance always compares
strictly replayed canonical bytes and actual receipts to the unchanged Engine.

The expected packet content/closure/cursor is independently rebuilt by existing
pure Core `memory_coverage::build_chunk`, fixed production caps and original
source scopes. At least two packets are required for 384 events. Private speech
is excluded from the agent and included for the player; the absent actor's empty
eligible span must still advance the completed boundary. Core byte equality is
an extractive cache/canonical-source oracle, not model use or quality.

Head/branch cases append four actual events per branch; parent, child and sibling
share head388 and observer, so a numeric revision alone cannot satisfy isolation.
The quota case is separately labeled: up to86 original small zero-event seeds,
three distinct observer partitions each, public ensure/cancel only. It attempts
the 257th retained Store job after256, then explicitly prunes one terminal job
and requires a higher nonreused ID. It does not pretend to be another384-event
corpus. The schema's unique scope/observer/method partition permits one row, so
the nominal eight-per-partition admission ceiling is not independently fillable
through the present API; no forged handles/SQL admission will manufacture it.

### Frozen outcome matrix

- Prepare does not advance cursor or canon; publish one packet and cursor
  atomically; complete reaches the actual head and rejects further preparation.
- Same-basis ensure reuses the persisted ID; exact checkpoint fields survive
  close/reopen. Cancel persists generation, prevents obsolete publication,
  rejects prepare and never resurrects under ensure. Explicit terminal prune
  removes the row; later ensure receives a higher ID. Ready pruning is Busy.
- Two actual owners prepare at the same cursor; one publication wins, the other
  is Stale and cannot duplicate/advance a packet. Canonical head change also
  rejects old prepared work. Retarget reuses ID with generation advance and only
  independently reverified sealed prefix, discarding old open tail.
- New branches do not copy jobs or proof. Original ancestor scopes remain intact;
  later parent/sibling text and player-only speech stay absent from child/agent.
  Retiring a parent clears its job, preserves live child's own verified cache and
  canonical prefix. Deleting a story clears jobs without reusing IDs.
- Wrong scope/actor, stale request, pre-cancel and unsupported workflow states
  refuse. A deliberately hostile derived Blocked row rejects prepare and is
  explicitly prunable; that is not evidence of a valid corpus hitting a budget.
- A held actual SQLite IMMEDIATE writer allows preparation's reader but causes
  publication Busy; no cursor/cache/canonical change. Actual derived-table
  insertion/cursor triggers raise ABORT and must roll back packet+cursor+job
  fields together. These are actual SQL transaction failures, **not SQLiteFull**.
- Packet schema/source/extra-field/player-packet/foreign-scope tamper and missing
  prefix require whole-set fallback; read-only context does not repair rows.
  Ensure should safely rebuild rather than trust damaged JSON. Existing v1
  invalidation does not erase/relabel v2 jobs. Playable archive bytes exclude
  jobs/cache; import has identical canon and no copied proof.
- Own current integration-test executable only: fixed before-publication and
  after-committed-first-checkpoint barriers, parent kills only its returned
  child, then reopens. Expected durable cursor is exactly0 or Core first boundary,
  persisted job identity is unchanged and completion can resume. This proves
  process death at those barriers, not power loss, ENOSPC, or death inside commit.

## Static findings and pending contract corrections

No tests have run. Source inspection found the same-basis ensure branch in e98
calls `prefix(...)?`: corrupt/missing cached packets return Integrity instead of
the promised reset/rebuild. The regression's reset oracle is preserved for the
coordinator to reproduce/fix, not relaxed to accept that error.

The initial test also contains two overstrong assertions identified before any
execution: job lineage digest bytes need not equal Core packet lineage digest
bytes (the encodings differ), and valid Core packets may remain safely Verified
after only a derived job source-hash field is corrupted if actual Engine recheck
still proves the packets. Follow-up must replace those assumptions with actual
binding stability/format, explicit proof recheck and unchanged canonical-state
assertions. Packet-content/schema/scope/observer forgery still must fallback.

Independent production review additionally found native handle cross-Store
collision risk (same persisted ID/scope/actor in two databases). Coordinator
announced a Store-instance owner binding, without schema change: opaque native
handles expire on close/reopen; ensure on the reopened Store reissues a handle
for the same durable ID/cursor/generation. The initial test assumes old handles
can be used after reopen and across owners in several lifecycle cases. Preserve
that revision, then explicitly add old/foreign-owner handle NotFound tests and
reissue handles with ensure before resumed work. This is a clarified native
capability lifetime, not permission to reset persisted progress or resurrect a
cancelled job. No oracle will be quietly edited after a failure.

Retired targets map existing `MemoryError::NotFound`; obsolete generation/head/
source publication is Stale. The coordinator confirmed the actual DDL names
`memory_jobs` and `memory_job_packets(packet_json)`, source binding fields and
failure variants Budget/PacketLimit/Integrity. Adversarial SQL is confined to
those derived tables and their test triggers. No production writer/hook exists.

## Execution gate and unavailable checks

The coordinator's verified compiler build currently owns the build slot. No Cargo
compile/test/check/Clippy, process launch, model/assets/app/device/ADB/CUA/desktop,
protected resource, OS/settings/download or release action has occurred here.
Only source/Git/ticket reads, test/document edits, formatting and diff checks.

After a new frozen module hash and explicit slot: preserve this source, compile
the corrected follow-up against that hash, run the selected test sequentially
default/all-features, then strict selected Clippy/fmt in own D target/UUID TEMP,
debug0/incremental0, locked/offline/jobs1. Record exact counts, ignored helper
invocation, process-death phases, failures and hashes. Full Store/native/Android
compatibility remains coordinator work; no app or inference is part of this test.

Actual SQLiteFull cannot be imposed on the private Store connection through the
present public integration API: `max_page_count` is connection-local. Do not fake
it with an ABORT string or fill a real volume. Existing coordinator-owned private
unit fixtures may qualify Full separately. Same-snapshot overlapping-writer
evidence still needs a bounded schedule against the frozen implementation; no
claim is made from the mere presence of the snapshot return type.

## Explicit pre-execution follow-up

Immutable initial freeze `9e8b84f1b6e77d18ca6ef5b7e63202aaf18809ba`, test
SHA-256 `da6c4398f69f6575dbd7546f210cb5c5c0fbc2f1dbb4d114d78af621fc36d16a`,
was never compiled or executed. The next revision implements the coordinator's
approved native capability lifetime clarification and documented oracle
corrections **before** first execution; the original source remains in history.

- Reopen cases now explicitly reject an old owner handle with NotFound, call
  ensure to reissue a native handle, and require the exact previous durable
  ID/cursor/generation/status. Cancelled jobs remain cancelled. Both owners in a
  competing-step case call ensure themselves; actual CAS still permits only one
  publication from the two prepared tokens.
- A new collision case creates two real independent databases with identical
  seed/history/Scope/observer and matching actual AUTOINCREMENT ID. Status,
  prepare, cancel, prune and a prepared publication from one Store must refuse on
  the other. Each owner's own handle still works. No opaque token is fabricated.
- Job digest format/stability is tested without assuming Core and SQL lineage
  digests use identical serialization. If actual Core packets still verify after
  only a job source-hash metadata field is corrupted, they must recheck against
  the returned actual Engine; canon stays unchanged. Ensure repairs the binding
  and completion still exactly equals pure Core output. Missing-prefix/packet
  schema/actor/scope/source corruption still requires whole-set fallback and
  generation-advanced safe prefix reset; no existing failure expectation was
  relaxed to accept the coordinator's same-basis Integrity result.
- A new bounded overlapping-writer case uses an explicit synthetic SQLite WAL
  fixture, as existing derived-memory snapshot tests do. It signals another Store
  after strict source replay inside the reader, lets that owner actually commit
  four new events, retarget and complete the job, then requires the returned old
  Engine **and old complete coverage** from the same read snapshot. A new request
  with old expected head must subsequently reject. The callback checkpoint is
  source-audited at e98: outer context check, memory_engine entry, post-strict-
  replay check. Re-audit that position at the final module freeze before running;
  no production hook or alternate snapshot is added. The canonical/proof oracle
  is fixed regardless of a later checkpoint-position adjustment.
- `cache_rows` materializes its iterator before returning to avoid a potential
  Rust tail-expression borrow-lifetime issue; no compiler error is invented for
  this static correction.

The follow-up contains **23 parent tests plus one intentionally parent-spawned
ignored helper**. It still has not been compiled, run, or used to launch a child.
Source formatting/Git whitespace checks are the only local executable checks so
far. Root will provide the owner-bound/reset-corrected module hash and resource
slot; production remains entirely outside this author's ownership.
