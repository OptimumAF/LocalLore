# Author / V2 application-owned native harness contract

2026-10-23. Refs #12 M08.03 / #30 D08.05. **Proposed source contract and
frozen journey oracles, before source implementation. UNCOMPILED / UNRUN.**
No app launch, native execution, render, device or acceptance is inferred.

Base `b39139a814d765402a2bd9828d48a6d6ceb91d1c`, branch
`impl/m08-author-native-harness`, worktree `source-author-native-harness`.
Exact claims: [#12 6379429683](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6379429683),
[#30 6379429827](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6379429827).
Own ONLY these NEW paths:

- `apps/desktop/ui/author-native-journeys.ts`
- `apps/desktop/author-harness.mjs`
- `apps/desktop/src-tauri/src/author_harness.rs`
- this contract

Root owns existing main/App/controller/broker/native registration and harness
files. The protected chat and its worktrees, processes, devices and outputs are
excluded. No desktop control, injected input, activation or desktop capture.

## Actual source seams and proposed integration

At this base, main.tsx already constructs the actual AuthorController from
`invoke(author_prepare_start/author_commit_start/author_lookup_start)`, uses the
actual ArchiveBroker status/cancel and BrokerRetention, and constructs the
actual V2PlayController with the same Gateway as the root Controller. Native
author_ipc obtains the manager for the SAME WorkspaceState Host, WindowLease,
epoch and Arc ArchiveBroker. AuthorManager uses actual opaque Host preparation
and Repository.store; no new canonical writer is needed.

The existing memory harness demonstrates the fixed fixture, two-process
launcher and native CapturePreview path. Its global gate cannot pause author
apply. AuthorManager's existing test gates are `cfg(test)` only, so a hidden
WebView run cannot honestly claim deterministic native pre/post-commit cancel
coverage without a narrowly gated integration hook. Proposed Root additions:

1. `#[cfg(feature="dev-harness")] mod author_harness;` and the fixed
   `author_harness::harness_author_case` command registration. Setup calls
   `author_harness::seed(&path)` only when `active()` and not restart, before
   opening the WorkspaceState Host. The launcher supplies the fixed fresh path.
2. Add `authoring:bool` to dev-only window config, derived solely from
   `LOCALLORE_M08_AUTHOR_HARNESS=1`. Main selects `authorNativeJourneys` before
   other journeys and passes `{controller,author,v2,brokerRetention,gateway,
   errors,invoke,dispose,config,transport}`. Normal build has no import or hook.
3. NEW journey module exports `AuthorHarnessTransport`; instantiate only for
   explicit native author harness config. Inside the existing invoke function,
   replace only its `native()` body with `transport ? transport.native(command,
   args,()=>window.__TAURI__.core.invoke(command,args)) : originalNative()`.
   Every dispatch still reaches the existing native command and outer global
   retention wrapper. The transport may withhold/drop an ACTUAL returned ack;
   it may not fabricate statuses, previews, receipts or successful results.
4. Root adds two dev-only calls in its owned AuthorManager commit worker:
   `author_harness::before_apply(&work)?` immediately before the existing
   pre-apply `work.check()`, and `author_harness::after_apply(&work)` immediately
   AFTER successful `host.apply_author_correction`, before returning the real
   completion. The after hook never returns a cancellation error or replaces a
   recorded outcome. Both no-op unless `active()`. Existing cfg(test) gates and
   production cancellation/validation remain unchanged. This is the only
   requested production-owner source extension beyond registration.
5. Add the exact capture labels below to existing HarnessState admission and
   preserve its JSON/PNG/count budgets. No new capture API. Author's native
   helper exports `LABELS` for Root's membership check if preferred. Add
   authoring to the existing frontend window-config type. Root's frontend
   verifier must exclude this new journey and faults from the normal bundle.

Root must approve these seams before source implementation. No existing path
is edited by the harness agent. A hook requiring broader authority is a
reported integration gap, not permission to add a debug server or SQL route.

## Closed fixture and fault interface

The launcher uses the existing owned build target and task-owned artifact root
(`LOCALLORE_M07_MEMORY_TARGET_DIR` / `LOCALLORE_M07_MEMORY_ARTIFACT_ROOT`) to
avoid building or using another track's resources. A new `author-native-UUID`
leaf owns `stories-v1.sqlite`, an app WebView profile and `initial`/`restart`
capture directories. Both mode flags are required: D02 harness and M08 author.
Builds are offline/locked, one job, ordinary uncapped SQLite; nonempty
LIBSQLITE3_FLAGS is refused. Spawn shell=false, windowsHide=true; existing
hidden/unfocused native harness window behavior remains authoritative.

`seed(path)` accepts only the exact launcher environment path, fixed basename
and new owned `author-native-UUID` directory, rejects existing DB, parent/cur
components and reparse/symlink traversal using existing pin guards. It uses
Store::create_new_pinned/create_story and an actual Core-approved
begin_turn/commit_prepared receipt, never raw SQL. Fixed synthetic seed:

- story `author-controls-synthetic`, branch `main`, relic-location proposition
  `AUTHOR_OBSERVED_A`, known by actual player and Mira, discoverable at quay;
  absent Sable has no such observation.
- original single dialogue turn `author-parent-message`, literal
  `AUTHOR_PARENT_MIRA_ONLY`, audience Mira. Parent head 1.
- unrelated saved story `author-controls-other`, branch main, head 0.
- primary child `author-saved`, fixed input H=1/f=1 replacing that proposition
  with `AUTHOR_WORLD_B`, reason `AUTHOR_PRIVATE_REASON`. Author boundary r2;
  later fixture gameplay must use the actual UI pipeline.
- separate fixed child identities `author-cancelled`, `author-late`,
  `author-unknown`, `author-known-ack`, `author-stale`; same closed operation.

Native IPC `harness_author_case({action})` accepts ONLY a closed string enum:
`hold-before`, `hold-after`, `release`, `gate-state`, `oracle`. It captures the
actual window lease. No renderer path/scope/input/seed/SQL/provider/shell/code
arguments. One process-local gate, one armed mode, no second worker. Gate
entry is observable and capped at 30 seconds. Before-apply waiting checks
actual work cancellation/lease and returns Cancelled; after-apply waiting
releases on cancellation/deadline but preserves the already real success.

`oracle` reads ONLY the fixed app-owned DB via bounded read-only Store, and
reports fixed parent/child summary checks (real revision, canonical digest,
record counts and exact lookup result), not full canonical/private state.
The primary parent must retain its exact seed and original accepted history;
fixed cancelled/stale children must be absent. It never opens a new Store for
author confirmation and never writes after fixture setup. The SAME live
Repository remains the only author apply owner. Fresh and restarted oracle
checks use actual retained records, not a persisted expected-result journal.

The dev-only transport exposes closed local controls to the journey, not IPC:
drop the next author commit-start ack after real admission; drop the next
terminal archive-status reply after real native execution; hold an actual
author preparation ack until release. Handshakes prove entry before switching
context. All controls reset after one use, have bounded deadlines and are
absent from the normal bundle. Existing FaultGateway handles gameplay/query
ack holds through actual Gateway calls. No fake native receipt is accepted.

## Frozen fresh-process oracles

Each action invokes the same controller method used by UI handlers; no DOM
mouse/keyboard events. A deliberate direct native malformed request is labeled
an IPC rejection probe, not a frontend action test. Every async assertion has
a bounded entry/completion deadline, not an arbitrary microtask sleep.

| Journey / capture label | Required assertions |
| --- | --- |
| `author-native-consent` | Start actual root Controller, resume fixed parent, persistent head1. Story Lab acknowledgement alone is not author consent. Play/character lens author unavailable. Omniscient Lab + actual native spoiler grant enables form. Prepare without first author consent yields AuthorConsentRequired and no child. |
| `author-native-preview` | Actual prepare yields exact Core JSON, SHA verified by existing decoder, input/session/parent/child/H/f bound. Parent digest unchanged, no child. Confirm before exact-preview read yields ReadPreviewRequired; no mutation. Render before/replacement/reason, retained-knowers, excluded suffix, preservation/no replay and SHA visibly. |
| `author-native-rejected` | Fixed raw IPC extra/duplicate field or false consent is rejected by real native parser; token/input mismatch cannot consume valid preview. Form edit invalidates both consents and discards unused cap; native old-token reuse refuses. No fabricated success. |
| `author-native-pending` | Arm before gate, confirm after explicit second consent, await actual native gate entry. Native operation running author_applying, visible pending; other shared archive start refused Busy and gameplay admission unavailable. |
| `author-native-cancelled` | Request cancel through controller/archive_cancel, release gate, require actual terminal Cancelled and no cancelled child. No claim that cancellation undoes a commit. Prepare again requires fresh explicit consent. |
| `author-native-saved` | Primary actual commit creates child r2, original parent still exact. Native oracle confirms one canonical author interval and no fabricated actor observation. Saved outcome visible; no auto-open or auto-retry. |
| `author-native-history` | Open confirmed child through actual root resume. Thin snapshot domain2, coherent selected scope/head/player. Player history has inherited scoped message origin main and EXACT neutral `{kind:author_correction,revision:2}`; no private author reason or new truth in transcript. Receipt-only history is not advertised as entire canon. |
| `author-native-observer` | In child Lab, Mira knowledge retains observed A after omniscient world B; Sable has neither A nor B nor original Mira-only message. Character history event-only, no player input/narration/author marker/reason/source. Omniscient inspection does not change those actor reads or generation permissions. |
| `author-native-receipt` | Return Play; actual V2 send Give succeeds and saves real receipt/inventory transfer, same original scope identity. A repeated Give rejects without further revision/inventory change. Displayed receipt/status/error matches selected child; player history includes actual accepted scoped prose. Fake inference explicitly labeled. |
| `author-native-turn-cancelled` | Existing FaultGateway holds actual ready Prepare ack; V2 pending shown, author blocked. Cancel original native gameplay turn, release ack and inspect terminal; no new accepted receipt/head. Native status/retry inspection must remain exact original turn. |
| `author-native-stale-context` | Hold actual author prepare ack, switch observer/session to other saved story, release. Late preview never installs in new context and is discarded. Original input cannot become a new-context apply. Visible other story/head0 has no old receipt/private preview. Return parent only explicitly. |
| `author-native-late-cancel` | Separate fixed child, after-apply gate proves actual commit already completed. Cancel while native terminal reply is held; release yields actual saved outcome, not fake Cancelled/rollback. Exact lookup later returns created=false, same child/head and no extra author record. |
| `author-native-unknown` | Drop entire real commit-start ack with before gate. Controller/global retention retain honest unknown and original input; no ID invented, no automatic apply or status-latest. Context switch cannot clear barrier. Release and fixed native oracle observes completion. Only after explicit unresolved acknowledgement may readonly exact lookup admit. |
| `author-native-recovered` | Actual exact lookup confirms existing unknown child, created=false, one canonical author record; changed input is RetryMismatch, not success. Known-ID terminal status ack-loss case resolves only by explicit known-ID inspect, using real shared archive_status; no second apply. |
| `author-native-narrow` | Fixed capture-narrow viewport, coherent scope/observer/revision/pending/receipt/error, no horizontal document overflow; controls/errors/private preview readable without raw HTML injection. |

All captures use the mounted real React UI in the native WebView, app-owned
CapturePreview and bounded semantic snapshots. Snapshot contains selected root
Controller state, AuthorController state, V2 state, shared retention, displayed
receipt/error, viewport/userAgent, text <=48,000 chars and semantic form/control
structure. Replace workspace location with a synthetic placeholder. Native
helper oracle output is separately labeled, never presented as a visible UI
fact merely because a lower-level assertion passed. Unexpected frontend/native
error categories fail the report; expected deliberate rejection/cancel probes
are enumerated, not filtered away.

## Restart, capture, process and evidence boundaries

Restart is a second actual application process on the SAME owned DB. It does
not seed again. Require no author preview/input/consent/outcome/operation
restored, no auto-apply/lookup/model load. Resume primary saved child, verify
Domain2 r3 after accepted Give, actual parent preserved and scoped history /
marker / player inventory retained. Captures `author-native-restarted` and
`author-native-reopened` show saved child read/resume and honest "restart
recovery is unavailable" author behavior. No fullinput localStorage or invented
author hint is added. Process-restart author-outcome recovery remains unavailable.

Expected capture allocation: 15 fresh + 2 restart = 17 app-owned images, below
the existing per-process40 checkpoint budget. Each must be accompanied by JSON
and `.capture.json`, with rendering exactly `native-webview2`. Root will inspect
ALL generated images for layout/visible-state defects after actual execution.
Native setup/oracle checks, frontend control checks, actual native IPC, native
WebView renders, headless checks and engine-only tests must be reported apart.

Launcher caps stdout/stderr separately at262,144 bytes, logs truncation and
exit/signal/deadline, rejects missing/duplicate/extra capture labels and failed
reports, requires both stages, and records source HEAD/dirty plus hashes of
actual controller/view/native/Host/Store/harness inputs and binary/dist. Child
processes shell=false with no broad process kill. Cargo deadline15min, native
stage4min; no polling of unrelated processes/windows. Drain owned Host sessions
and ArchiveBroker workers before harness_finish; failed report exits nonzero.
No private real story or model input, downloads, new persistence layer or
general remote-debugging endpoint is introduced.

Actual build/run commands and tool/runtime versions, bounded error evidence,
source/binary/image/summary hashes and limitations will be appended only after
Root's authorized execution. This frozen contract is not evidence that any
of its journey assertions currently pass.
