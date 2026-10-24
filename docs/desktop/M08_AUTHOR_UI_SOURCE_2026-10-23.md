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

Invalid form edits also revoke the displayed preview and both consent stages;
validation refusal cannot leave an earlier confirm armed. An independent frozen
NaN-boundary edit case covers native discard and absence of commit calls before
the focused controller fix. Uncertain-operation input remains immutable instead.

## Source handoff

Branch `impl/m08-author-ui`, isolated `source-author-ui`, exact base above.
Claims #12 `6379011122`, #30 `6379011301`, #26 `6379011483`. Five NEW files only;
no existing app, shared broker, model, schema, dependency or test-runner edits.

Freeze/implementation chronology:

- `a4bb009`: independent synthetic checker and exact contract before all modules.
- `0bef92e`: three additional asynchronous ordering oracles before modules.
- `4827ff6`: isolated decoder/controller/plain React panel source.
- `a3d4bb3`: detached async digest and semantic context identity oracles;
  `999deec`: focused model fix, assertions unchanged.
- `8377c57`: invalid-edit revocation oracle; `30ae663`: focused controller fix,
  assertions unchanged. These source-detected seams are not executed REDs.

Actual checks were Git/source inspection and `git diff --check` (exit 0), with
clean status. No JavaScript/TypeScript parser, checker, formatter, bundler, test,
React render or native/app execution was run by this agent. In particular,
compressed source has NOT passed Prettier and TypeScript is NOT yet qualified.
No generated artifacts were produced. SHA-256:

| New source | SHA-256 |
| --- | --- |
| `ui/author-model.ts` | `8f3ddc8f088995d9e7d18e64ded37b8edf3ff062fc9fb09af2ae4835eed64226` |
| `ui/author-controller.ts` | `4136bc4976a0becea489e7c3a2bf12ad9a01d59a481430ca271da535e0d342b7` |
| `ui/AuthorPanel.tsx` | `5e249e7ecf328b6b2207a68a7841ddcff38d2ee21f900de21a8c584aefca6383` |
| `check-author-controller.mjs` | `72ab36ca316431135f4afbd99d7630e6e715001172bf810426d4a3616ba5324b` |

Next coordinator commands, from `apps/desktop` in the authorized heavy slot:

```text
node check-author-controller.mjs
node node_modules/typescript/bin/tsc --noEmit
node node_modules/prettier/bin/prettier.cjs --check ui/author-model.ts ui/author-controller.ts ui/AuthorPanel.tsx check-author-controller.mjs
```

Use the task's pinned bundled Node/runtime; preserve first compile/checker/format
failure separately and keep frozen assertions. The standalone checker writes its
synthetic compiled artifact only under the existing gitignored artifacts/checks
directory (or explicit caller-owned LOCALLORE_CHECK_OUTPUT_DIR). No package script
or automatic runner is changed here. A synthetic pass proves presentation logic,
not actual native execution, current UI import, layout or observer-safe generation.

After checks, Root must close global broker retention, fixed native wrappers for
the approved port (including owned preview discard), actual root/window teardown,
selection/observer/head fencing, main/App navigation and V2 resume. Then run the
application-owned semantic/render/native IPC harness and inspect its artifacts.
No UI/headless/native screenshots or desktop capture/control was performed here.
Restart hint recovery, private input persistence, Android author UI and Archive3
are separate prerequisites, not implicitly completed by this packet. M08/D08/D05
whole milestone acceptance remains pending.

## First actual checker result and fixture correction

Root's Node 24 first standalone checker on adopted `30ae663` failed with an
unhandled rejected synthetic `gate` promise in the older-failed-status case
(`check-author-controller.mjs` line 88 there). Log `author-ui-first.log` remains
local under the task artifacts. No passing count was claimed. The fixture used
only two Promise.resolve turns as an assumption that the controller had entered
the status request; this was not a deterministic scheduling guarantee.

Source-only correction replaces those drains in BOTH deferred-status cancel
cases with an explicit status-entry handshake bounded to two seconds. Rejection
or completion now happens only after the fake port's status function has returned
that pending promise to the actual controller. Every behavioral assertion and all
production source remain unchanged. The correction is UNRUN by this agent; Root
owns the actual rerun. The original failure is a synthetic scheduling/unhandled
promise failure, not proof of a native or production cancellation defect.

Correction commit `cb67511d4ad8c6f0353bc86337ac62a1f8896776`; corrected checker
SHA-256 `5a3afbc17cd435bc2080f46ae54432425654f80054671dddc28e1ed802a9b887`
supersedes the pre-correction checker hash in the source table. Model/controller/
panel hashes there remain unchanged. No passing checker count, type/format pass
or app/render execution is inferred from this source correction.
