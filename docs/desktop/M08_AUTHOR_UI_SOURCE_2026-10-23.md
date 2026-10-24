# M08 author UI: frozen source contract

2026-10-23, M08.03 / D08.05 / D05 partial. Separate source packet based on
`5c39be6d1fac03fd89502e0803515b53b4a51be8`. Exact new paths: `author-model.ts`,
`author-controller.ts`, `AuthorPanel.tsx`, standalone
`apps/desktop/check-author-controller.mjs`, and this document. Existing app,
global broker retention, native wrappers, schemas, styles and dependencies are
coordinator-owned. No existing application imports this packet yet.

## Native and presentation contract

The injected `AuthorPort` has fixed `prepareStart(raw)`, `commitStart(raw)`,
`lookupStart(raw)`, `status(operationId)`, `cancel(operationId)` returning unknown
native data, and `discardPreview(session,token) -> Promise<boolean>`. Root adapts
these through the SAME ArchiveBroker/global retention and fixed native wrappers;
this packet registers no command or worker. Native status is exactly
`{version:1,operation_id,running,phase,error,result}`, phases starting,
author_preparing, author_applying, author_lookup, completed, error. Native commit
attempts consume a fully verified cap even on Busy/spawn refusal; new preview is
required afterward. Invalid/foreign/mismatched input cannot retire a native cap.

Raw request DTOs exactly match the native broker: prepare has version/session/
input/author_consent; commit has version/session/input/preview_token/
preview_sha256/confirmed; lookup has version/input/author_consent. Closed author
input is native version 1 parent/expected_parent_revision/fork_revision/
child_branch/replace_fact_proposition operation/reason. Strings preserve valid
controls and Unicode; Core limits remain 2048 UTF-8 bytes per prose field,
65536 per raw native request/private preview and 262144 per envelope. IDs use
Core syntax and numbers are safe nonnegative integers. Frontend shape checks do
not grant permission, establish facts, validate ancestry or replace Core replay.

Preview envelope is exactly version/kind/session/preview_token/preview_sha256/
preview_json/expires_seconds. Eleven-field Core preview is version/input/child/
before/creation_revision/retained_knowers/excluded_suffix_events/
excluded_suffix_records/original_preserved/downstream_replayed/
new_child_requires_fresh_derivatives. Check native SHA-256 against exact UTF-8
preview_json using WebCrypto, then exact captured input/session/scope/child/f+1,
before fact/expected value, suffix H-f and supported flags. Before-source is a
closed private seed_fact or scoped author reference, never passed into NPC/model
data. A small bounded unique-key structural scan precedes JSON.parse on this raw
preview string; no generic canonical JSON parser/evaluator is added. Parsed
objects are copied/frozen; accessor/prototype/cycle/duplicate/lone-surrogate data
fails closed. A digest binds display bytes; native held plan remains authority.

Commit output is version/kind/session/outcome, lookup is
version/kind/found/outcome. Native outcome has version/scope/parent/fork_revision/
author_revision/head_revision/created. Exact scope/input/fork identity, safe head
and created=false for lookup are required. No missing child becomes success or
triggers a write. Errors are fixed categories, not raw private text.

## Consent, context and recovery

Root supplies actual `AuthorContext`: rootIncarnation, selectionEpoch, session,
scope, head, player, observer, view, persistent, spoilerGranted, pending,
brokerUncertain. New author operations require persistent Story Lab, explicit
spoiler grant, omniscient lens, and no pending gameplay/global broker uncertainty.
This frontend gate does not mint the independent Host/native grant. Read-only
status/cancel can inspect an already-owned pending operation. New lookup starts
only after Root's shared-owner uncertainty disposition, using exact same-window
memory-only full input; it may inspect a retired/advanced original parent.

Controller API: contextChanged, setDraft, setAuthorConsent, setPreviewRead,
prepare, confirm(true), inspectOperation, cancel, lookup, openConfirmed, dispose,
get/subscribe. Draft fields are completed fork revision, fixed child identity,
fact, expected proposition, replacement and reason. Parent and expected head
come only from captured context. Core validates completed boundary/eligibility.
First author warning consent is separate from Lab acknowledgment. Preparing is
readonly. Exact private preview is displayed as React text; a read acknowledgment
and separate explicit confirmation are required before one commitStart call.
No Enter/default submit, chat, retry, refresh, lookup or preview can apply.

Every context/form change clears both consent stages, clears private preview,
discards unused native token and cancels a known pending operation. A stale
prepare completion is discarded, never shown under another context. Same-root
uncertain full input stays only in controller memory for explicit readonly lookup;
root/window disposal clears it. No localStorage/private journal or restart
recovery claim. Unknown commit outcomes block editing/recommit until inspection
or explicit missing-child disposition. Known operation ID can re-read retained
status until replaced; lost whole start acknowledgment has no invented latest ID
and requires explicit readonly lookup after shared worker settles. No auto-retry.
Late committed outcome wins cancellation; a cancel request is not rollback.
Opening a confirmed child is a separate user action through Root's coherent
resume callback; context mismatch cannot open a stale child automatically.

Panel labels authoring out of story/private, original preservation, no downstream
replay, no new character observation, fresh derived data required and unavailable
automatic memory rebuilding honestly. Current story/observer/head, native pending
operation, receipt/outcome and fixed visible error are semantically inspectable.
Plain React text only, no innerHTML, prose logs or hidden inference.

## Independent checker freeze and verification limits

Standalone checker uses synthetic async fake port only. Freeze before decoder,
controller and panel: closed DTOs, exact bytes/hash/private source, duplicate/
unknown/numeric/prototype/Unicode/caps, both consents, form/context invalidation,
native discard, foreign/stale completion, same-root uncertain lookup, root disposal,
known/lost ack, Busy fresh preview, pending cancel and late actual-shaped success.
These are presentation/controller oracles, NOT actual Store/native/IPC/WebView
rendering evidence. Root separately reported native Host13, scoped46, decoder99
and broker14 passes; those do not execute this frontend packet.

All source, checker, TypeScript, React render, formatter and runtime checks are
initially UNRUN here. No Node/Cargo/Gradle/SQLite/app/model/browser/device/ADB/CUA/
desktop/protected-resource execution. Root owns actual standalone checker,
strict type/format/build checks, global retention/native wrapper/teardown closure,
coherent application wiring, semantic/native render harness and final acceptance.

Pre-production source review additionally freezes three asynchronous boundaries:
a known committed cancellation response cannot be demoted by an older failed
status read; status inspection cannot rebind a stale private prepare to a new
context; cancel before a prepare start acknowledgment must discard a later
successful preview. These are independent synthetic oracles, UNRUN, not observed
native/behavioral failures. Production uses private per-operation completion and
cancellation latches, not a second native operation owner.

Further bounded source review freezes detached envelope/expected-input snapshots
before asynchronous SHA verification, so caller mutation cannot change a checked
preview while digest awaits. Context identity is semantic field identity, not
object-property insertion order. Two new independent synthetic oracles freeze
these seams before their focused source fix; no observed runtime RED is claimed.
