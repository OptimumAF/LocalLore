# M08 author shared-broker retention: frozen source contract

2026-10-23, partial M08.03 / D08.05 / D05. Base
`b1c5c7eaadd02382793584e04eb37fd485667522`; separate
`impl/m08-author-broker-retention` / `source-author-broker-retention`. Own ONLY
existing `ui/broker-retention.ts`, NEW `ui/author-broker-binding.ts`, NEW
`check-author-broker-retention.mjs`, and this document. Root owns native/main/App,
author controller/model, consumers and actual qualification. No other old tests
or production files change. Freeze independent checker before implementation.

## Closed binding and exact result validation

Add BrokerSurface author and optional BrokerIdentity.author EXACT
`{action:"prepare"|"commit"|"lookup",session,input:AuthorInput}`. Validate actual
closed input through existing checkedAuthorInput; copy/freeze the full binding.
Outer action must equal binding action; optional session/story/branch/head/child/
at metadata must match captured input/session exactly. Author cannot carry archive
or token metadata; other surfaces cannot carry an author binding. Private input
is memory-only identity, never serialized to localStorage, diagnostics or journal.
Root must keep private binding out of public broker summaries.

New helper checkedAuthorBrokerBinding and async checkedAuthorBrokerOperation reuse
existing checkedAuthorStatus, checkedAuthorPreview (exact bytes/raw unique JSON/
native SHA) and checkedAuthorCompletion. Running phase must match captured action
or starting. Completed prepare must match full input/session and private preview;
commit must match actual captured input/session/outcome; lookup is exact readonly
outcome or null, created=false. Lookup native output contains no session field;
its native root/grant and captured invocation remain authoritative, not an
invented transport session proof. No canonical validation/writer is duplicated.

Commit/lookup outcomes also do not echo private reason/replacement or original
parent H. Retention binds the immutable full invocation and native operation ID,
checks all actual outcome identity/revision fields, and relies on the existing
Host/Store exact-input authority for fields absent from the response. It does not
invent transport evidence or claim an independent canonical/full-input replay.

Only this reservation's awaited start acknowledgment may establish operation ID.
An external unknown-ID response cannot adopt an unacknowledged operation. Exclude
a known different positive safe operation ID before decoding against the current
binding. Minimal ID read uses an own data descriptor, never a getter. Invalid
same-ID/status/result/kind/input/session/hash fails closed as global unknown.

## Asynchronous admission, uncertainty and consumption

Author start awaits full validation BEFORE known terminal/consumption. Add async
observeAuthor(value):Promise<void>; Root must await it for author status/cancel.
Existing synchronous observe on an author reservation is conservative unknown;
it cannot accidentally treat private preview or ordinary completion as verified.
Memory/fork/archive start/observe/recovery semantics and assertions stay intact.

A private WeakMap keyed by a fresh frozen per-admission identity tracks native
admission pending, concurrent async validators and sticky validation fault. The
existing exposed inFlight flag stays true until admission and ALL author checks
settle; no cross-surface start or unresolved acknowledgment bypasses a pending
SHA check. Capture the retained identity before validation, recheck it after every
await, and patch only that same reservation. An old reply cannot poison a new
surface/reservation. No new worker, native operation, persistent ledger or server.

Malformed terminal/private preview/hash mismatch latches unknown for that author
reservation. Callback consumption or controller/context reset cannot clear it;
even a later partial/valid same-ID update cannot silently forgive a validation
fault. A deliberate acknowledgeUnresolved(true) may allow a NEW explicit
admission after all validators settle; it does not prove the old write failed or
authorize automatic retry. Fresh exact readonly lookup is the recovery action,
not reconstructed commit. Invalid observation remains unknown until explicit
disposition/new reservation. Lost whole-start acknowledgment cannot adopt an
arbitrary externally supplied ID. ArchiveBusy is the only specially known
no-admission start throw; other start throws conservatively retain unknown.

Author waiting-for-consumption is the existing Root-supplied callback. A fully
validated terminal result still blocks another surface until consumed. Native
Cancelled and committed terminal results preserve their actual meaning; no
context reset/cancel request fakes rollback. No author private data persists.

## Frozen independent source oracles

Standalone synthetic checker freezes: closed detached binding/outer identity;
async SHA pending admission blocks other surfaces and acknowledgment; malformed
status/kind/full input/private hash/session; concurrent valid/invalid checks;
old ID/cross-surface/unknown whole acknowledgment; controller consumption reset
cannot clear fault; valid native-shaped cancel/commit and explicit later
admission; ArchiveBusy vs conservative other throws; synchronous observe remains
closed. Reuse existing actual decoder source, synthetic native-shaped fixtures
and bounded fake digest handshake. These are NOT native execution or UI renders.

All Node/checker/TypeScript/format/build/app/native/model/device/desktop checks
are UNRUN by this source-only agent. Root owns actual new checker and ALL old
retention regression execution. No old assertion or input calibration is changed.
No main/App/native/author-model/Host/Store/schema/dependency edit is authorized.

Source review also freezes terminal monotonicity for this author reservation:
a late same-ID running status/cancel snapshot cannot demote a fully validated
terminal result. Recheck the latest same-identity terminal flag after async
validation, before recording progress. This is an additional independent UNRUN
oracle before the focused source fix, not an executed production failure.

## Source handoff and coordinator execution attribution

Exact claims #12 `6379192232`, #30 `6379192431`, #26 `6379192745`. Frozen
contract/checker `d53a7597778c4500cee0abc074124ed8874639c6` precedes production
`a85fb830470562f1bd562ebb1b9edad6c9cacd40`. Coordinator reported actual first
standalone run on adopted `a562097`: **75 synthetic checks PASS**, no native or
render execution. This is Root's execution, not this source-only agent's check.
No claim is made that an unrun old implementation failed these tests.

Additional monotonic terminal oracle `febd04f` precedes focused author-only guard
`5db3f9b9b06f05e896bc75945428d2f887390f89`. That extra case/final source remains
UNRUN at this handoff. All old retention checker assertions are unchanged. The
only old-file edits are additive author handling and logically equivalent
non-author blocked-expression grouping; legacy record/start/recovery bodies
remain intact. No old test/calibration change or full regression pass is inferred.

This agent actually ran only Git/source/hash inspection and `git diff --check`
(exit 0), with clean branch status. Node/TypeScript/Prettier/bundler/old retention
tests/native/app/model/device/desktop execution are UNRUN by this agent. Root
owns formatter/type qualification and all existing broker regression runs.

Coordinator next commands, from `apps/desktop` in its authorized heavy slot:

```text
node check-author-broker-retention.mjs
node node_modules/typescript/bin/tsc --noEmit
node node_modules/prettier/bin/prettier.cjs --check ui/broker-retention.ts ui/author-broker-binding.ts check-author-broker-retention.mjs
```

Then execute the unchanged existing broker-retention, incarnation, surface,
fork-error, archive, fork, memory and controller checks. Root main must await
observeAuthor for author status/cancel, construct exact full binding on starts,
provide author consumption callback, and avoid exposing/persisting private full
input through generic broker summaries. No actual global UI closure is established
until those separate main/App/native wrapper/harness tasks are executed. Root
retains all of those paths. No competing worker, Store, journal or recovery write
has been added here; no milestone acceptance is claimed.
