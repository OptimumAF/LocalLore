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
