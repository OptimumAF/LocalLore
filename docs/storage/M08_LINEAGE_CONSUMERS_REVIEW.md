# M08 lineage consumers: source review — 2026-10-23

Reviewed frozen coordinator implementation
`6b243027b5d37e353c7f9def3fa5c162590c7fc6` on accepted main `d5a76d2`, then
source-rechecked the two test-only follow-ups through final source
`0e36a637298913f650ce3f0ce616e71f22cb24ab` (including `cd8e55b`).
Reviewer `/root/app_storage_review`, isolated branch
`review/m08-lineage-consumers`; claims #12 comment 6361024616 and #11 6361024882.
Only this new report was written. No production edits, builds, test execution,
models, app/device/CUA operations or protected resources were used in this review.

## Disposition and independence

No concrete blocking defect was identified in the frozen implementation or its
test-only follow-ups.
This is a bounded source review, not an execution result, human acceptance,
favorable score or full M07/M08/D08 gate. The coordinator owns integrated
workspace/eval/platform execution and publication; their results must be recorded
separately with their exact source version.

The reviewer authored the preceding durable Store-fork slice, the separate
playable-archive implementation and the original query module. This review is
independent of the coordinator's **new** historical snapshot method, fork
refactor, compiler/query integration and new tests; it is not an independent
approval of those authored foundations or of the archive. The archive is frozen
in its separate checkout and is not present in this reviewed commit.

## Source observations

`Engine::at_revision` refuses a future revision or a revision inside a completed
multi-event turn. The current-head path returns a detached clone of an already
validated Engine. Earlier boundaries rebuild from the unchanged seed, retain the
same lineage, switch to each receipt's **original scope** for recorded replay,
compare every rebuilt receipt, and finally restore the target branch scope.
No projection is accepted as historical authority, no receipt is relabelled, and
no inference runs. A failure cannot return a partially reconstructed Engine.

The refactored `fork` validates/adds the new lineage link on a local clone, obtains
the boundary through `at_revision`, then sets only the new child scope/lineage.
Failure does not mutate the source Engine. The current-head clone shortcut is
consistent with validated private Engine fields; it does not establish authority
for arbitrary caller-supplied projection bytes.

Retained lineage is necessary for a child snapshot at a revision before its own
birth: ancestry eligibility caps each link by the requested head and fork
revision. Replaying the visible prefix cannot recover later parent or sibling
receipts, because those receipts are absent from the validated child Engine.
Positive pre-birth nested rewind semantics remain consistent with the prior
Store fixture `root@5 -> a@5 -> b@1 -> c@2`, whose original root and b receipts
are preserved without a's future continuation.

Compiler and query remove their former blanket child rejection only after the
supplied Engine has already been validated. Scope equality and expected **current
head** still precede historical content reads. Historical selection uses the same
`at_revision`; returned packages retain the requested child scope, current head
and selected historical revision as distinct fields. A future or partial-turn
selection remains an error rather than an empty result or nearest-boundary guess.

The compiler's existing actor-only collector and borrowed observation port still
filter lineage/time/witness eligibility before candidate serialization, search,
counts, alias discovery or ranking. Original event scopes remain in event rows.
There is no new raw Player transcript path into NPC generation. The Director
observer restriction, explicit actor validation and role checks remain unchanged.

Query lenses retain trusted-native Story Lab grant checks for other-character and
omniscient views. A grant selects an inspection lens; it does not mutate actor
knowledge or feed omniscient rows into the compiler. History still suppresses
raw input/narrator Message rows for NPC lenses. Promise completion provenance,
knowledge and TurnDiff continue using observer-filtered rows at both boundaries.
Inherited event sequence IDs are unambiguous within one selected lineage, and
History rows retain original branch scopes for source navigation.

Cursors still bind the full request without its cursor (including branch scope,
expected head, historical revision, observer, view, search and limit) and eligible
serialized rows. A sibling/changed observer/changed historical selection cannot
reuse a cursor; a newer actual head is rejected as Stale. The hash is a stale/edit
detector, not an authentication token. No cursor can select a new privileged lens.

Derived-memory `binding()` retains its explicit child `MemoryError::Unsupported`
guard. This change adds no child cache, maintained summary, FTS partition,
Host wire command, app branch selector or schema migration. Query summary/index
views also remain honestly unsupported. Enabling compiler/query on a validated
child does not bypass these independent guards.

## Compatibility and bounded-work limits

Recorded-history replay uses `commit_recorded`, preserving accepted historical
Play 2.1 rather than rewriting its policy/timing or granting fresh prepared 2.1
commits. The new golden-receipt source case checks original JSON in the snapshot;
existing authority regressions remain relevant to integrated execution.

The unsupported-package diagnostic changes from `Durable branch history` to
`Branch-scoped derived caches`. This is six more UTF-8 bytes. The compiler budgets
the entire serialized package, so the change can alter byte/token estimates,
optional selection or a MandatoryBudget result at a tight boundary. `play.rs`
excludes diagnostic text from model data, but selected records can still differ
because of that budget effect. Do not claim old root package/prompt byte equality
or transfer old prompt fingerprints to this source. This is not a change to
accepted canonical receipt bytes or a replay regeneration requirement.

Historical replay and query row collection remain synchronous work. Compiler
cancellation checks bracket snapshot creation but cannot interrupt one replay;
the current-head query path clones the Engine. These are existing bounded-source
work limits, not a new immediate-cancellation or zero-copy guarantee. Repeated
historical/TurnDiff requests can cost repeated replay. No new hard latency or
peak-memory measurement is claimed here.

## Tests inspected and follow-up source recheck

The source adds six core tests and one actual Store-reopen integration case.
They assert original receipt scopes/current-head equality, zero/historical/partial
and future boundaries, future-parent/sibling/hidden canaries across views, actor
grant nonmutation, cursor fences, historical 2.1 preservation, and a 1,024-local-
turn child retaining old mandatory promise evidence within budget. The Store case
feeds a reopened durable child into compiler/query while checking cache Unsupported.
These are meaningful assertions inspected in source; **the reviewer did not run
them** and does not infer outcomes from their existence.

The review's optional positive pre-birth consumer vector is now addressed in
source by `0e36a63`: `root5 -> a@5(+local6) -> b@1(+local2)`, selected at b
revisions 0/1/2. The new test checks compiler inclusion/exclusion, original root
receipt scope, child-bound query metadata and exclusion of later parent/local
canaries across History, Profiles, Knowledge and TurnDiff, plus nonmutation.
This adds a seventh core test; it is no longer an outstanding review suggestion.
The reviewer inspected the new assertion source and did not execute it.

`cd8e55b` changes only the older durable-branch test's now-superseded compiler
and query Unsupported expectations to successful child-bound results. It retains
the actual derived-cache Unsupported assertion. This reconciles an obsolete test
contract with the intended capability, without changing implementation or
weakening the cache guard. The coordinator reported a full-run failure on the
old expectations before the repair; this review does not replace that actual
failure with an inferred pass. Final execution remains coordinator-owned.

## Exact frozen file hashes

SHA-256 of original frozen checkout bytes below; production source and the new
Store integration test are unchanged through final `0e36a63`. The core test hash
below belongs to the initial six-test source, not the seven-test follow-up.

| File under crates/ | SHA-256 |
| --- | --- |
| locallore/src/engine.rs | `1142ee0942068617e1ddf44ff1d66a6e71bce3685e11def060ac62bee270c59b` |
| locallore/src/context_compiler.rs | `d59f997c7b003b64f76fb01a2ee78499b634fd454e8892fc85603c9f8fb5ae88` |
| locallore/src/inspection_query.rs | `ba2f2fafb80cfa6e6d1d7feea35bcd3e025eddc6336d5c89a9ae19b7fd4a1626` |
| locallore/tests/lineage_consumers.rs | `c06e93d7fb590449151d12591ad041f9af4fc6faff6ae531cf2667628ad66d0a` |
| locallore-storage/tests/lineage_consumers.rs | `324753b263fd7026d086d7f8c77cfff16e72ca726ab26b9a955aff7e3c80fc19` |

Final follow-up Git blob identities, read directly from `0e36a63` without
altering the frozen implementation checkout:

- `locallore/tests/lineage_consumers.rs`: `8ec12d407bddc95e16c2ded04d9ec157228a4b65`.
- `locallore-storage/tests/durable_branches.rs`: `193079475be95f987939265c13679f73c5a3f6f7`.

Next gate: coordinator's source-bound integrated checks and owner disposition.
Maintain pending native/Android branch-session, cache-maintenance and portability
gates independently; this source review does not complete them.
