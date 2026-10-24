# Future V2 native author authority review

2026-10-23. Partial #12 M08.03 / #30 D08.05. **Source review, not runtime,
human approval, model quality or app-feature acceptance.** This future stack is
separate from merged foundation PR131 (`2a9a5e6`).

Reviewed source: `5c39be6d1fac03fd89502e0803515b53b4a51be8`, separate branch
`review/m08-v2-native-authority`, worktree `source-v2-native-authority-review`.
Initial sole NEW report claims: [#12 6379015068](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6379015068),
[#30 6379015221](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6379015221).
Root explicitly extended ownership BEFORE the regression edit to append ONLY
`apps/desktop/src-tauri/src/author_commands_review.rs`:
[#12 6379037542](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6379037542),
[#30 6379037700](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6379037700).
No existing production path was edited. All14 existing broker tests/assertions
are preserved. The decoder authored by this reviewer is **excluded** from
independent review; existing scoped-query producer work is described only as a
boundary fact, not independently self-approved.

## Concrete finding: shared worker owner is not bound

At `author_commands.rs:210`, `AuthorManager::new` captures Weak Host and
WindowLease identities plus epoch, but does not capture the designated
`Arc<ArchiveBroker>`. `check_owner` checks only Host/lease/epoch. Every start
method (`prepare_start:296`, `commit_start:332`, `lookup_start:374`) accepts an
arbitrary broker argument and invokes `start` on that argument.

Demonstrable source sequence:

1. Construct the normal manager and obtain an actual valid Host preparation.
2. Hold the designated workspace ArchiveBroker with a bounded operation.
3. Pass `Arc::new(ArchiveBroker::default())` with the correct Host, lease, epoch
   and raw input to an author start method.
4. That fresh broker has no running job, so its `start` bypasses the designated
   broker's ArchiveBusy exclusion and can admit another worker. A foreign
   `commit_start` also removes the valid capability before that admission.

This violates the frozen **same Arc ArchiveBroker / one shared worker** contract.
It is not a claimed Store transaction or canonical-validation bypass: Host's
state lock and real Store still serialize/revalidate the actual write. The
module is currently `#[cfg(test)]` in main.rs with no Tauri author registration,
so this is a native API ownership gap, not a demonstrated renderer exploit.
Root accepted it as fix-required before exposure.

Minimal agreed repair for Root: bind Weak ArchiveBroker at manager construction,
then check pointer identity on all starts **before parsing/capability
consumption/admission**. Foreign broker refusal must preserve the valid cap;
genuine valid attempts on the bound Busy broker still consume under the approved
policy. Updating the constructor fixture after the actual pre-fix test run is
an explicit API closure, not a changed behavioral assertion.

## Frozen regression, before any repair

Commit `e72f63849a4685b43bbc80d51c76303d170ba94d` appends the fifteenth test,
`foreign_archive_broker_cannot_bypass_shared_busy_or_consume_a_valid_capability`,
76 lines. Full test-file SHA-256:
`4ffdb8b88623223aa7342e93e36c9337b47e42f5c7b0ae10e6311a3a0c8a525c`.

It uses the existing actual Repository/Store/Host Fixture, obtains a real preview,
holds the designated broker, attempts foreign-broker prepare/commit/lookup with
otherwise matching ownership/input, and requires Integrity for all three. Owned
foreign workers are retired/drained before assertions even on the predicted
pre-fix admission path. It verifies the designated operation remained running,
parent bytes/children unchanged, and the original valid cap can subsequently
commit through the designated broker. This distinguishes foreign rejection from
the intentional consumed-on-genuine-Busy behavior of the existing test.

**UNCOMPILED/UNRUN by this reviewer.** No behavioral RED/GREEN is inferred from
source. Root owns the first actual frozen RED, production fix, unchanged GREEN
and broad compatibility checks. No duplicate implementation test, fake receipt,
canonical SQL fixture, model/provider or general runtime hook was introduced.

## Remaining finite source audit

No separate concrete native authority blocker was identified in these inspected
paths; this is a bounded result, not a blanket approval:

- Host preparation requires native Story Lab construction, exact live selected
  session/parent, durable port, no active Queued/Running/Ready parent work across
  this Host, fresh resumed head and full accepted-history basis. A native port's
  actual prepared basis must match before returning the exact bounded preview.
- Host capability is non-Serde/non-Clone, Weak-bound to the exact Host state,
  session and work-owner incarnation. Apply checks those identities before any
  exact-result lookup. Replacement Open rotates the work owner; passive exact
  append/Open follows the already accepted source contract.
- Unknown fresh apply checks cancellation with a panic-safe latched callback,
  parent Busy/head/full source and the opaque port plan. Existing exact committed
  lookup deliberately precedes fresh creation/cancel checks; recorded success
  wins late cancellation. Apply does not relabel a committed Store return.
- Explicit lookup is privileged and read-only. It does not require the original
  parent/session to survive; exact full input is checked by actual Store lookup,
  including kind, retained ancestry, missing child and tombstone behavior. A
  result must be version1, exact child/parent/fork, author revision=fork+1 and
  valid head; lookup cannot claim `created:true`.
- Repository's private StorePreparation downcast wraps the real
  PreparedStoreAuthorCorrection. It uses the existing Repository Store, whose
  incarnation guard/full basis/IMMEDIATE transaction/rebuilt exact preview and
  final cancellation checkpoint remain authoritative. No alternate writer or
  reconstructed renderer plan is introduced.
- Broker raw parsers reuse Core bounded unique-key JSON parsing (65536), exact
  keysets, safe unsigned integers, closed operation, Core input validation and
  separate first/second consent. Caps bind exact session/input/preview SHA/bytes,
  are bounded4 and expire600 seconds. Invalid/mismatched/foreign consent attempts
  preserve caps; a valid matching second attempt consumes even on genuine Busy
  or spawn refusal. Discard only removes a same-owner/session unused cap.
- Explicit manager retirement generation and TTL enter fresh apply cancellation;
  window invalidation enters Work cancellation and broker publication fences.
  Retired in-flight fresh apply cannot write through the intended callback path;
  late cancellation after actual commit cannot demote success. Generation
  exhaustion closes admission. No reentrant callback or provider runs under
  Host/Store from these fixed native methods.
- Publication still uses the existing ArchiveBroker operation/epoch identity
  and WindowLease; inactive windows cannot publish. Future controller context
  changes must retain their own request/selection epoch fences and clear private
  presentation. Manager retire clears capabilities; it is not a promise that
  every retained latest-operation preview byte is physically erased. Known-ID
  status is latest-operation recovery, while lost whole-start acknowledgment
  requires explicit exact-input read-only lookup after worker settlement.

The thin snapshot returns exactly actual selected player state and owned items
after durable refresh/head/session checks; it does not serialize knowledge,
ordinary/private canonical records or author preview. V2 messages carry actual
receipt request scope and complete supporting event IDs after the existing
whole-eligible-receipt gate. Neutral markers serialize only kind/revision,
literal Player + History only, using the selected retained canonical prefix.
No marker enters NPC/Omniscient history, compiler actor rows or narrator evidence.
No legacy Query1 byte or canonical-record representation is changed here.

## Evidence and limits

Root supplied actual results of13 Host-port,14 broker and46 query/thin tests
passing at this future source. These are **Root executions**, not executed by
this reviewer and not evidence for the newly frozen fifteenth test or the future
frontend/controller/render integration. Native Rust broker tests are not actual
WebView/Tauri IPC, Android JNI/device or correction UI acceptance.

Reviewed source SHA-256:

| Path | SHA256 |
| --- | --- |
| crates/locallore/src/host/author_port.rs |e6ba269db36ad64561965744992ed2d0fdbfb62f915cb36d3cc7111b6b4e1224 |
| crates/locallore-workspace/src/author_port.rs |0ba8a20851952f6446e9ccf9b147f0869e5f41015305f99e2a56f8973e713d51 |
| apps/desktop/src-tauri/src/author_commands.rs |643a8ab5fe0e265a8a9e4756dc8d9cb88451bc53edbf4d291c9da66739a73f36 |

Actual review checks: source/Git reads, SHA256 calculation,
`rustfmt --edition 2021 --check apps/desktop/src-tauri/src/author_commands_review.rs`
and `git diff --check` succeeded. Rustfmt is a standalone source parser/formatter,
not type-check or execution. No Cargo/Node/Gradle/app/provider/model/device/ADB/
CUA/desktop/protected-resource action, production edit, PR/merge or settings
change occurred. Root owns repair and future exposure; claims release at handoff.
