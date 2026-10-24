# V2 app views and author controls: proposed minimum consumer contract

Date: 2026-10-23. Refs #12 M08.03, #30 D08.05, #26
D05.01/.03/.04/.06/.07. **SOURCE-ONLY PROPOSAL; coordinator decisions below are
required before interface implementation or app exposure.** No feature, device,
model, UI rendering or whole-milestone acceptance is implied.

Base `5638c0d1eeefcd03053384778f5fbbf74ac117df`, branch
`design/m08-v2-app-views`, worktree `source-v2-app-views`. Own ONLY this NEW
document. Claims: [#12 6378174399](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378174399),
[#30 6378174566](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6378174566),
[#26 6378174799](https://github.com/OptimumAF/LocalLore/issues/26#issuecomment-6378174799).
All production/schema/Store/platform ownership remains with Root.

## Actual source, not historical feature descriptions

| Actual source | Available behavior / consumer gap |
| --- | --- |
| `crates/locallore/src/author_correction.rs` | `CharacterContextV2` contains actor self-state, actual observed facts with safe observation provenance, eligible ActorEventV2 observations and beliefs. `actor_receipts_v2` contains only original_scope, turn and actor-eligible event subsets, never Request/Proposal/narration. `CanonicalRecord` also contains private author records and private truth bindings; it is not an app actor DTO. |
| `crates/locallore/src/inspection_query.rs` / `inspection_query_v2.rs` | Exact Query.version2 dispatch already exists. Query2 returns Page2/cursor namespace2, `known_as_observed` and `scoped_event`. Player messages require every supporting receipt event to pass the lens; NPC history is event-only. Omniscient knowledge reads actual effective truth, with withheld provenance. Author records are absent from ordinary history. Completed boundaries drive historical reads/diffs. |
| `crates/locallore/src/context_compiler` and `play.rs` | Current compiler2/Play2.5 use safe observed knowledge; current Domain2/Recent old-cache refusal is separate from native source fallback. Inspector grants are not generation arguments. This proposal adds no compiler, provider or context permission. |
| `crates/locallore/src/host.rs:659` | Existing `inspection_query` reloads one durable Engine and passes exact query version through shared query dispatch. No new query2 operation is needed. |
| `host.rs:1359/1395` | Legacy Inspect/PlaySnapshot use old character context/receipts and refuse Domain2; the omniscient legacy path explicitly returns Version. Keep these typed refusals. There is no author HostCommand or author Persistence port. |
| `crates/locallore-storage/src/author_correction.rs` | Real prepare/apply/lookup exist. PreparedStoreAuthorCorrection is opaque to serialization, bound to one Store incarnation and full parent basis; exact preview bytes are rechecked transactionally. Lookup validates actual retained child history and exact full input, not a fork catalog match. |
| Desktop `ui/model.ts`, `query-model.ts`, `controller.ts`, `App.tsx` | PlayView assumes legacy Context facts as strings and receipts. Query decoder accepts Page1 and only seed/event/withheld sources and old origins. App chat/receipt panel enumerates `play.receipts`. Controller requests legacy play_snapshot/inspect and uses epochs for publication. Raw inspection JSON is not a V2 decoder. |
| Android `DurableGateway.kt`, `StoryRecord.kt`, `StoryRecordWire.kt` | Play snapshot uses legacy receipts. StoryRecordWire hardcodes query/page1, cursor1, old origins/sources, event sequence Long references, and selected-branch equality. It rejects valid V2 inherited original scopes and known_as_observed. Physical schema5 admission alone cannot close these gaps. |
| Desktop `src-tauri/src/main.rs`, `lease.rs`, `archive.rs`, `fork_commands.rs` | Existing WorkspaceState/Host, WindowLease and ArchiveBroker serialize native lifetime/worker registration. Fork is native-only and does not create a second Store. These owners must be reused, not copied into a second author worker or authority. |

Stable earlier contracts remain relevant: M08_CORE_IMPLEMENTATION_CONTRACT,
M08_CONSUMER_IMPLEMENTATION_CONTRACT, M08_STORE_IMPLEMENTATION_CONTRACT and
M08_PLAY25_STAGING_PROPOSAL, all dated2026-10-23. Their historical unrun status
does not describe the current source; current qualification stays in ticket
comments and verification reports. No new execution is inferred here.

## Version and surface choices

Keep Host envelope protocol1 and all existing operations/DTOs unchanged. Do not
globally bump query1 constants or reinterpret legacy snapshots. Proposal:

1. Add explicit read-only `play_snapshot_v2`, with fixed request version2 and
   explicit result version2. Keep legacy
   `play_snapshot` intact, including its Domain2 refusal. Both new read paths
   may support Domain1 as well as Domain2 using actual V2 actor semantics.
2. Reuse existing `inspection_query` with Query.version2 for paged transcript,
   events, facts and inspection. Its existing bounded Page2 is the minimum
   player/character/omniscient inspector; do not add a player_history_v2/query2
   operation, full observations/receipts array or raw
   omniscient Engine/state dump or duplicate Query2. Legacy `inspect` remains
   legacy. The app switches inspection rendering to typed Page2 after closure.
3. Author prepare/commit/lookup are trusted-native methods plus narrowly named
   desktop IPC, **not** new generic HostCommands, model tools, JSON edit routes
   or granted query booleans. No Android author-editing UI is proposed in the
   first read/resume slice; Android must decode/read/resume authored stories.
4. Capabilities advertise exact view versions only when those producer and app
   decoder/render paths are qualified. A capability is availability metadata,
   not an inspection/author grant. Missing support returns Version/Unsupported,
   never successful empty history. Root must approve the capability field shape
   before regenerating the existing request schema/types.

Proposed fixed requests, inside the existing envelope1:

```text
play_snapshot_v2 {
  version:2, session, scope, expected_revision
}
inspection_query { session, query:{version:2, ...existing exact Query fields} }
```

Unknown fields/versions fail closed. Native reads reload and validate one actual
Store Engine before comparing expected head. Scope/session/source identity and
accepted-history basis must remain coherent; matching numeric head is not proof
that an imported/recreated scope has the same history. No read mutates selected
engine, time, knowledge, drafts or generation state. Mixed-read advances result
in Stale and clear the old page before fresh publication.

## Proposed thin snapshot and existing paged Query2 history

```text
PlayerSnapshotV2 {
  version:2, domain_version:1|2, scope, revision, rules,
  player:{version:2, scope, revision, observer, self_state:actual player Actor},
  inventory: actual player-owned items
}
AuthorBoundaryV2 {
  kind:"author_correction", revision
}
```

This is proposed transport data, not existing Rust types. The thin player data
comes from actual V2-safe actor state; do not serialize the full
CharacterContextV2.observations/facts/beliefs or all receipts. Query2 Profiles,
Knowledge and History pages provide those supported details explicitly at the
same expected head. Original input/narration use existing Message rows; typed
actions have no invented original prose. Never expose a full accepted
Request/Proposal merely to get chat text. Event identity is original scope plus
sequence. No frontend rewrites ancestor scope to the selected child. Receipt
inspection groups actual eligible History rows by captured original event scope
and turn, without treating a partial page as an entire accepted receipt.

The actual existing shared Query2 History implementation already applies
owning-player **whole-receipt eligibility** before emitting original input and
narration: every supporting event must pass at the selected completed head.
A partial actor event view cannot authorize whole-receipt prose. Reuse that
selector; do not implement permissions in TypeScript/Kotlin or create another
transcript filter/ledger/evaluator. Display-only grouping does not change state.
A displayed receipt view is not the private persisted CanonicalPlayV2 wrapper.

Root approves a **player-only neutral out-of-story marker** for an included
AuthorV1 revision, not an actor observation. Its ONLY serialized fields are
revision and constant kind author_correction: no original_scope/source, fact ID,
before/replacement/reason, retained-knower count, TruthSource or private binding.
Label "Author correction; no character observation was created" and distinguish
it from a played turn. Do not claim the receipts-only ordinary feed is full
canonical history or invent a narrator turn, witness, story-time advance or
discovery at that revision. Excluded parent suffix/sibling/retired child data
must not appear. The marker must not enter NPC history, model context or actor
knowledge. An ungranted NPC query has no marker count/author metadata channel.
Proposed transport location is an explicit Query2 History-only marker row,
player observer only, using existing pagination. Exact enum/internal sorting-key
representation still needs Root's next interface freeze: existing Row normally
has key/origin, so those must not leak onto this exception's two-field wire shape.
The UI derives a display-only stable key from captured page scope plus revision.
No marker enters Query1, NPC/omniscient history, CharacterContextV2 or compiler
rows. No producer/render exposure before that exact variant is independently
frozen and tested; do not infer implementation approval from the marker policy.

Reuse actual caps without expansion: Host MAX_INPUT24576/MAX_OUTPUT262144;
Query MAX_ROWS64/MAX_PAGE_BYTES65536/MAX_CURSOR_BYTES128/MAX_SEARCH_BYTES256;
Core MAX_RECEIPT_BYTES65536. Query2 keeps its existing4096-byte page envelope
reserve, sorted rows/cursor2 and oversized-row rejection. A page may separate
input, narration and event rows; never relabel one page as a full receipt or
silently omit unsupported gaps. Snapshot emits thin state/inventory only, bounded
by existing output cap, or TooLarge. Query2 facts/history/transcript are explicit
follow-up reads with the same expected head; a changed source/head invalidates
the combined presentation. No unbounded full context or new history budget is
introduced. No long-history performance qualification follows from this proposal.

## Observer and provenance closure

NPC inspection uses existing Query2 Character lens under trusted native Story
Lab grant; its history comes from actual ActorReceiptViewV2 events only. It must
never serialize raw player input/narration, Request/Proposal, private AuthorV1,
TruthSource, observation binding or current world replacement as NPC knowledge.
`CharacterContextV2` actor-safe values may be used internally; do not substitute
omniscient query results or forward a grant into generation.

Both apps must explicitly decode Page2, Source::ScopedEvent and
ValueOrigin::KnownAsObserved, rendering "Known as observed" separately from
world truth, statement, belief and discovery. Root-scoped evidence navigation
must carry `{original_scope,sequence}` end-to-end; a naked sequence Long is
insufficient. Validate story identity, original branch syntax and revision bound,
but leave actual lineage membership/eligibility to Rust. Do not reject a valid
inherited event solely because its original branch differs from the selected
branch, and do not accept a different story. Why/source links requery the same
captured scope/head/observer with exact scoped reference; missing/withheld
evidence stays withheld. Query2's withheld omniscient world-fact provenance must
not be replaced with private TruthSource from a canonical wrapper.

Required truth scenario: actor observed A; author changes world to B in a new
child; actor still sees A as observed, while granted omniscient view sees B.
Only an actual accepted re-observation changes that actor's known value to B.
No inspector selection, page search, author preview, grant, app refresh or
generator policy can perform that observation. Historical pages use actual
completed boundaries, reject mid-turn/nonexistent/prebirth revisions and exclude
future parent/sibling state. TurnDiff at an author interval must not invent
actor changes or expose private author provenance absent from Query2.

## Native-only staged author operations

Proposed trusted methods (names/types subject to the explicit port decision):

```text
Host::prepare_author_correction(session, &AuthorCorrectionInputV1, cancel)
  -> opaque HostAuthorPreparation
HostAuthorPreparation::preview() -> &AuthorCorrectionPreviewV1
HostAuthorPreparation::preview_bytes() -> &[u8]
Host::apply_author_correction(session, &HostAuthorPreparation, cancel)
  -> WorkspaceAuthorOutcomeV1
Host::lookup_author_correction(&AuthorCorrectionInputV1, cancel)
  -> Option<WorkspaceAuthorOutcomeV1>
WorkspaceAuthorOutcomeV1 {
  version:1, scope, parent, fork_revision, author_revision, head_revision, created
}
```

Use the existing Host Persistence owner and Store's actual prepare/apply/lookup.
No Store is opened ad hoc by a Tauri command and no second transaction, writer,
prepared-plan evaluator, durable ledger or model is introduced. The Core/Host
crate cannot name storage-crate PreparedStoreAuthorCorrection without a cycle;
Root must choose a bounded opaque native port implementation. The actual Store
plan must stay retained in its existing Store adapter and owner incarnation,
never reconstructed from renderer preview bytes/token/hash or cloned Engine.
Default unsupported Persistence implementations stay closed.

Root accepts a native prepared-plan trait-object abstraction as feasible. A
string handle may only key a fixed bounded registry owned by this same Store
adapter; it cannot be an author record, serialized plan or portable capability.
Suggested minimum is one live author preparation per existing workspace
operation owner. Root's next freeze must define exact handle type, native
preview accessors, owner/downcast proof, release/cancel semantics and registry
bound before any independent test source or production edit. This document
records feasibility, not approval of a specific implementation.

The native owner must independently require author capability. A Story Lab
inspection grant is necessary for private preview but insufficient for commit;
a renderer boolean, model text or successful private query cannot mint either
grant. Suggested fixed desktop IPC names: `author_preview`, `author_commit`,
`author_lookup`, `author_discard`, with existing broker status/cancel lifetime
ownership, not a new worker/service. Preview and apply remain separate actions:

1. Enter separate Author controls after deliberate private spoiler/edit warning.
   No chat action or generated claim can open an authorized commit path.
2. Capture exact full input, selected parent/head/fork/child identity and native
   root/window/session/Store incarnation. Reject active/unsettled parent work
   before creating a fresh plan; never overwrite a pending gameplay key.
3. Native prepare calls Store and retains its actual opaque plan. Return only a
   bounded private exact-preview DTO and opaque random native token. No commit
   happens while preparing or acknowledging preview display.
4. Display the exact Core preview, including supported before/replacement,
   reason, fork/new-child revision, retained knowers, excluded suffix records
   and events, original preservation/no downstream replay/fresh derivatives.
   Do not invent affected cache/job counts or promise automatic summary rebuild.
   All actually displayed impact metadata must be revalidated by Store or Stale.
5. A second explicit confirmation invokes commit with that same token and exact
   displayed preview digest. Native owner checks both capability and lifetime;
   the digest binds display bytes only and is never authority. Store rechecks
   full parent basis and preview inside its transaction. Any form edit, scope,
   observer, head, root or window change invalidates the displayed confirmation.
6. On committed outcome, return it even if cancellation arrives afterward.
   Refresh the catalog and select/resume the actual child with V2 views only
   after current controller epoch checks. Preserve parent and never replay its
   excluded suffix. No preview or pending token survives root/window teardown.

Use Core-validated closed input construction; the current input is Serialize-
only, not permission to deserialize plans or author receipts. Valid2048-byte
control-containing strings can exceed generic Host MAX_INPUT24576 after JSON
escaping. Keep this fixed private native parser bounded by proposed Core
MAX_RECEIPT_BYTES65536 instead of broadening generic host_call or stripping
valid input bytes. Core still owns operation/string/reference validation.
Preview bytes also remain within the existing receipt cap. IDs/revisions must
remain safe in JS; unsupported integer ranges fail before publication.

Do not share/export/trace private preview contents by default. The exact preview
may serialize private before-source and full input/reason; it belongs only in
the deliberately granted Author view, never player/NPC DTOs or model input.
Escape display as text. Bound memory/logs; error evidence uses fixed categories,
not raw personal text. Do not add a debug server or arbitrary execution hook.

## Lifetime, cancellation, recovery and stale completion

The same existing WindowLease and broker registration gate must fence native
prepare, consent, apply, status, cancel and cleanup. Capture and verify actual
native root/Host/Store incarnation, not just path string or renderer epoch.
An imported/recreated same scope/head cannot reuse an old preparation. Root
incarnation representation is a design decision below, not an asserted existing
ArchiveBroker capability. Serialize with the existing same-workspace operation
owner; do not allow author commit to race import/deletion/fork ownership.

Controller state must capture root incarnation, session ID, scope, expected head,
view/observer, operation identity, exact input and preview token/digest. Every
completion rechecks these before publication. Changing a session, hiding Author
tools, returning to Play, window destruction or workspace replacement invalidates
private previews and prevents stale selection/notice restoration. Late committed
work is recovered from Store, never relabeled canceled or blindly resubmitted.

Lost acknowledgement uses Store lookup with the **exact full original input**.
An existing ordinary fork, changed reason/replacement/expected proposition or
other identity field returns RetryMismatch; parent catalog/fork equality is not
proof of correction success. Lookup remains read-only after parent advance or
retirement while the actual child source survives; missing child returns None
and never creates it. Tombstoned children do not resurrect. A None result does
not authorize automatic apply; require a fresh current preparation and second
confirmation for any new commit. Preserve the original identity until terminal
status is known. No automatic regeneration, child rename or model rerun.

Process restart destroys the preview capability and every author permission;
it cannot reconstruct an authorized plan from a journal. Root selects a
non-authoritative **workflow hint**, identifiers plus full-input fingerprint
only, for proposed outcome inspection. Never persist author prose/reason or a
prepared capability in a renderer store or add a canonical journal/schema.

Proposed hint shape, subject to exact native-operation/root binding freeze:

```text
AuthorRecoveryHintV1 {
  version:1, parent, expected_parent_revision, fork_revision, child_branch,
  native_operation_id, input_sha256
}
```

`input_sha256` is SHA256 of the exact deterministic shared serde serialization
of the entire Core-validated AuthorCorrectionInputV1, computed natively before
dispatch. The format/hash bytes must be frozen before writers exist. The hint
contains no fact/proposition/reason, is untrusted availability metadata, and
cannot authorize commit or prove that a correction exists.

On explicit recovery inspection under fresh native privilege, the **same Store
owner** loads the actual retained child through validated Core canon. A narrow
native proposed `recover_author_outcome(hint)` locates its actual AuthorV1,
checks every hint identifier including the full original H/f/child identity,
recomputes the full-input fingerprint, and only then calls the existing exact
`lookup_author_correction(actual_input)`. It returns bounded outcome metadata,
never author input/prose. No write, preparation, generation, permission renewal,
automatic retry or child selection follows from a hint. Missing/tombstoned child,
kind mismatch, fingerprint mismatch and unavailable actual full input remain
closed outcomes; missing/full-input-unavailable requires manual exact re-entry
or explicit discard after inspection, not fabricated success. An ordinary fork
at that child is not a recovered correction. Parent advance/retirement does not
invalidate an otherwise exact retained child's read-only lookup.

Actual existing hint machinery inspection:

- Desktop `ui/main.tsx:204–227` stores the fixed fork input in app-origin
  localStorage key `locallore-fork-recovery-v1`; load is bounded to1024 characters
  and ForkController.restore decodes it before lookup-only recovery. Its
  prepare/save callback runs before native dispatch and rechecks context afterward.
  This is an existing **renderer** workflow hint owner, not native private atomic
  persistence. Reuse its callback/order/lookup-only pattern with a separately
  versioned strictly decoded metadata-only hint; do not overwrite the fork key,
  broaden its decoder, treat origin storage as trust or write author prose there.
  Its corruption/tamper/write-failure/context-change tests must extend to hints.
- Android `ForkRecoveryStore.kt` already owns a fixed noBackup AtomicFile,
  process-wide writer gate, bounded reads, compare-before-write, fd/directory
  sync and immutable pending fork identity. Its parser is fork-only. Do not
  broaden it casually or claim it supplies desktop native private persistence.
  Android author controls are outside the minimum slice; any later typed author
  hint extension requires its own owner claim/tests and native recovery closure.

Thus metadata-only desktop hint reuse is a feasible extension to the existing
workflow owner, with a prerequisite: approve the closed hint/root/native-op
identity format and same-Store privileged recovery method, then independently
freeze tamper/stale/missing/read-only/no-auto-write oracles. If the desired gate
requires native noBackup/atomic desktop hint persistence rather than existing
origin storage, that is a separate explicit prerequisite; no such desktop owner
exists in the inspected code. Until this closes, advertise same-process
lost-ack lookup only and honest manual restart recovery. No new journal/schema
or automatic post-restart commit is proposed.

## Proposed path ownership and closure gate

No paths below are claimed for editing by this document. Root must allocate
exclusive implementation/test claims before any existing file changes.

| Owner / exact candidate paths | Responsibility |
| --- | --- |
| Shared Core: NEW `crates/locallore/src/app_views_v2.rs`; existing `inspection_query.rs`, `inspection_query_v2.rs` only allocated marker/typed integration | Thin bounded player snapshot and exact player-only marker variant; reuse existing paged Query2 eligibility, no duplicate transcript/permissions. |
| Root Host/Store adapter: existing `crates/locallore/src/host.rs`, `crates/locallore-workspace/src/lib.rs`; NEW `crates/locallore-workspace/src/author_correction.rs` if approved | Versioned reads and opaque native author port on the actual existing Store. Existing storage author implementation remains owner/authority. |
| Desktop native Root: NEW `apps/desktop/src-tauri/src/author_commands.rs`; existing `main.rs`, `archive.rs`, `lease.rs` only allocated integration | Fixed private commands, same operation/lifetime owner and native grant/preview fencing. No second Store/window broker. |
| Desktop consumer: NEW `ui/app-view-v2.ts`, `ui/author-controller.ts`, `ui/AuthorPanel.tsx`; existing `model.ts`, `query-model.ts`, `controller.ts`, `App.tsx`, `main.tsx` under exclusive allocation | Closed DTOs, scoped source navigation, honest history markers, safe stage/confirm/recovery and private-state clearing. |
| Generated request closure: `apps/desktop/host-v1.schema.json`, `ui/host.generated.ts`, `check-contract.mjs`; source generator `crates/locallore/examples/host_schema.rs` | Additive generated command union only, preserve old schema/fixture acceptance. Generation does not itself validate output DTOs. |
| Android consumer: existing `DurableGateway.kt`, `StoryRecord.kt`, `StoryRecordWire.kt`, `StoryRecordController.kt`, `ShellViewModel.kt`; NEW `AppViewV2Wire.kt` if approved | Play/read/resume2, known-as-observed/scoped evidence references (actual event-source controller is inside StoryRecordController.kt), player-only fixed lens, same existing NativeWorkspace lease; no Android author UI in minimum slice. Reconcile #9 ownership before edits. |
| Independent frozen tests before implementation | NEW shared actual-Host app-view/author-port tests; NEW desktop decoder/controller/native harness journeys; NEW Android JSONObject instrumentation tests. Exact names assigned when interfaces are approved. |

## Required frozen acceptance oracles before production exposure

1. Actual Store author child then fresh Host V2 resume/snapshot/history/Query2;
   compare actual Core canonical basis, projection and actor values. Domain1
   remains usable in the same Host. Legacy PlaySnapshot/Inspect/Query1 Domain2
   still return Version/Unsupported and never Internal/incomplete success.
2. A→B correction: player and uninformed/old-knower NPC do not learn B from
   inspection or author preview; granted world lens sees B; later real Discover
   updates only its actor. Search/counts/pages/cursors contain no excluded
   parent/sibling/future text. NPC serialized bytes contain no player transcript,
   narration, author reason, private binding or current hidden truth.
3. Actual eligible whole player receipts disclose exact original prose+narration
   and original scoped event references. Partially visible receipts disclose
   neither input nor narration. Query2 pagination does not weaken that owning
   predicate. Author intervals have the exact two-field player marker, never a
   source/fact/reason, fake actor event or full canonical-history claim.
4. Malformed/unknown versions, scoped references, origins, page bounds, cursor
   namespace, unsafe integers, duplicate IDs, foreign story and cross-head data
   fail closed in both app decoders; supported inherited original scope works.
5. Actual author prepare does not mutate Store. No grant, inspection-only grant,
   first acknowledgement alone, foreign-window token, changed form/digest,
   stale full basis or replaced root/Store cannot commit. Repeated full input
   returns exact actual child; changed identity/ordinary-fork collision refuses.
6. Cancel before preparation/apply, cancel panic, busy/full/rollback and lost
   commit acknowledgement preserve exact source/identity. Late committed result
   wins cancel; lookup never writes or resurrects. Metadata-only recovery hint
   tamper/hash/H/f/child/native-op mismatch, missing/full-input-unavailable child
   and restarted window never authorize prepare/commit; actual validated child
   fingerprint+exact lookup can recover outcome only. Test every hint save/load
   context boundary and retain manual recovery if its prerequisite is unavailable.
7. Controller switches session/observer/Play/lab/root/window at every pending
   boundary: no stale private preview, source page, child selection, receipt or
   error restoration. Same native lease/root gate prevents dispatch after close.
8. The app-owned harness exercises actual controllers and native IPC, captures
   semantic state plus application-owned renders, and verifies story/observer/
   revision/pending/receipt/error coherence, long/control text and narrow layout.
   Separate headless, actual native WebView, IPC and engine-only results. Android
   JVM/APK checks do not substitute for JSONObject/JNI instrumentation; protected
   devices remain untouched without their independent admission.

Rust/frontend/native/Android existing compatibility checks and original legacy
bytes remain required. No model is needed for accepted-history replay. Synthetic
provider execution must be labeled; no quality/physical-device/long-history
performance claim follows. Until these producer/decoder/render/consent gates
close, author IPC stays unregistered and apps retain honest unsupported states.

## Decisions requested from Root before implementation claims

| Decision | Recommended minimum / unresolved boundary |
| --- | --- |
| V2 operations | Root selects thin play_snapshot_v2 + existing inspection_query(version2) transcript/facts/history; no new query2/history operation, full observations or all-receipt array. Freeze exact thin DTO/capability field next. |
| Player history marker | Root approves ONLY revision+constant kind author_correction, player-only/out-of-story. Freeze exact Query2 History variant/sorting representation next; no source/fact/reason/key/origin on its wire shape, NPC/model/context marker. |
| Budgets/capabilities | Reuse actual24576 Host input/262144 output, Query64 rows/65536 bytes/128 cursor/256 search/4096 envelope reserve. Root accepts separate private author input/preview cap65536; generic Host limits unchanged. |
| Opaque native port | Root accepts trait-object/Store-owned bounded registry feasibility; exact handle/cancel/accessor/lease/owner proof remains for next freeze. Actual Store plan stays in same adapter/incarnation; no Core→storage dependency or renderer plan authority. |
| Author consent/lifetime | Approve distinct native author capability and second confirmation bound to exact preview/window/root/session/Store; choose native root-incarnation representation using current owners. |
| Recovery scope | Root selects metadata-only identifiers+full-input SHA256 hint and same-Store privileged validated-child fingerprint+exact lookup for OUTCOME inspection only. Existing desktop origin-storage hint pattern needs closed format/native recovery prerequisite; native atomic desktop privacy would require separate prerequisite. No new journal/schema or auto commit; missing/full input unavailable requires manual re-entry/discard. |
| Android scope | Root selects read/resume/StoryRecord2 and roundtrip parity first, existing native transport/lease; no Android author UX acceptance claim. Full D08 runtime remains separately qualified. |

Source inspection, Git isolation and diff checks only were performed. All
proposed APIs, tests, harness journeys and renders are unimplemented/unrun. No
production/test/schema file changed; no Cargo/Node/Gradle/native/app/model/device/
ADB/CUA/desktop/protected-resource/settings/PR/merge action was performed. This
document releases its sole path at handoff; it is not implementation permission.
