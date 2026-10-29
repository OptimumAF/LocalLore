# V2 inspector Previous page proposal

2026-10-29. **Proposal only; no implementation, test execution or acceptance.**
Refs #26, bounded D05 inspection/navigation prerequisite, and
[allocation6508338213](https://github.com/OptimumAF/LocalLore/issues/26#issuecomment-6508338213).
Source anchor: accepted main `a6f235ae74c4e3ade80175a499ecd7fc20751314`.
Author branch: `plan/d05-v2-inspector-back-paging-v1` from that exact commit.
Root must accept this contract, claim exact task IDs/paths and freeze independent
FIRST source before production. GitHub owns task status; this document fixes the
proposed behavior and evidence boundary rather than maintaining another tracker.

## Smallest behavior and current shared query

Add **Previous inspection page** to the inspection channel of the actual
`V2PlayController` and `V2PlayPanel`. Reuse the existing `inspection_query` command
and native `host_call`; each Previous fetches and validates its page from Rust.
Keep only a bounded cursor history in frontend memory. Never restore an old row,
page, private body, receipt or source link from a frontend page cache.

The current controller has separate history and inspection channels and sequences.
`readQuery`, accepted/recorded-turn traces and source links start inspection reads;
`page(cursor, channel)` currently accepts only the current page's next_cursor.
The V2 panel has Next inspection page but no Previous. Its Play history pager,
legacy `QueryInspector`, memory-packet inspector and comparison/selected readers
are different surfaces and are outside this change.

Shared `inspection_query::Query` already carries version2/scope/expected_head/
at_revision/observer/view/cursor/limit/search. Domain2 Query2 filters eligible rows
in Rust, sorts them, then seals the query and actual filtered rows into its opaque
continuation. It returns next_cursor only. The cursor detects stale/cross-query
edits; it is not authentication and must never replace native grants. Do not parse
an offset to synthesize a previous cursor or infer a page's rows from an index.

Existing bounds remain 64 rows/request,128 cursor bytes,256 UTF-8 search bytes,
65,536 encoded page bytes and65,536 candidates. Pages can end early at the byte
budget, so do not promise64 rows/page, a reliable total page count or a computed
page number. No Core/Host/schema/Store/provider/model or query-format change is
needed. Rust owns visibility, historical boundaries, actual head and stale refusal.

## Proposed production and test paths

| Path | Proposed scope |
| --- | --- |
| `apps/desktop/ui/v2-play-controller.ts` | Inspector-only cursor ledger, derived presentation metadata, Previous method and reset/freshness fences. |
| `apps/desktop/ui/V2PlayPanel.tsx` | Previous/Next handlers, form-edit invalidation and small honest status/disabled presentation. |
| NEW `apps/desktop/check-v2-inspector-paging-review.mjs` | Independently authored controller and actual panel handler/SSR FIRST; synthetic Gateway explicitly labeled. |
| `apps/desktop/verify-frontend.mjs` | Later register the accepted finite frontend check in the existing normal check entry. |
| NEW `apps/desktop/src-tauri/src/v2_inspection_paging_harness.rs` | Separately accepted fixed development fixture/oracle only, if required for actual native qualification. |
| NEW `apps/desktop/ui/v2-inspector-paging-native-journeys.ts` | Actual app controller/host_call and panel journeys; no replacement page implementation. |
| NEW `apps/desktop/v2-inspector-paging-harness.mjs` | Bounded app-owned native launcher, only after its own frozen policy/FIRST. |
| `apps/desktop/src-tauri/src/main.rs`, `apps/desktop/src-tauri/src/harness.rs`, `apps/desktop/ui/main.tsx` | Only fixed dev-mode registration, finite labels and journey wiring after harness acceptance. |
| `apps/desktop/ui/journeys.ts` | Only a separately accepted fixed post-read-reply delay, if needed for a pending image; no general interception service. |

All these are proposed future allocations. This author owns only this new document.
Refresh current source before exact claims; do not create competing harness modes
or add unused files merely because they appear in the table. Existing tests remain
unchanged unless a specific obsolete behavior assertion is identified, preserved
and explicitly superseded before editing. No new runtime dependency is proposed.

## Exact cursor history and overflow policy

Use one private inspector navigation frame, owned by the current context and
snapshot, not a map of old contexts. Its predecessor stack contains **at most32**
entries of type `string | null`; null means the first page's request cursor.
Only validated successful request cursors enter that stack. Each string remains
bounded by the existing128-byte cursor format; predecessor payload is at most
4,096 UTF-8 bytes. The current request/next cursor may have two separately bounded
128-byte scalar copies for tamper checks. These are logical payload bounds, not
a measured JavaScript heap-size claim.

The frame retains only one bounded query-identity seal and current owner identities:
context key/reference, current snapshot reference and current bound-page reference,
plus scalar request/next cursor values. It stores no preceding bound-page objects,
rows, private bodies, receipts or history responses. Bind the identity to session,
story/branch, selected head, effective player/character/omniscient lens, queried
view, at_revision, limit64 and exact search. Reuse the existing context key and
bounded query fields rather than copying a private snapshot/body into a seal.
Keep head versus inspected historical revision distinct. A Play lens is still
forced to Player by the existing controller; UI metadata cannot change that rule.

On a successful **Next**, append the departing request cursor, then keep the most
recent32 predecessors. If full, discard the oldest cursor and set earlierOmitted.
Continue fetching Next without any page-count limit imposed by this ledger.
Reaching the history cap must never disable valid forward paging, invent a
cursor, clear canonical state, start another story or force a new query.

On a successful **Previous**, pop exactly one predecessor and use it as the new
current request cursor. Its reply supplies the actual next_cursor; moving forward
again refetches normally. There is no separate forward-page cache. Once the frame
has no retained predecessor, Previous is disabled even if earlierOmitted is true.
The user may submit Read permitted view again to start at null and rebuild a chain.
If a genuine null first-page cursor is reached, clear earlierOmitted. Never claim
that a rolling-window boundary is the first page when earlier cursors were dropped.

Push/pop/overflow updates are transactional: validate ownership and checkedPageV2
success before committing the navigation frame and displayed page together.
Do not consume a predecessor when a request fails, returns malformed/wrong-bound
data, becomes stale or loses presentation ownership. A failed navigation leaves
the currently displayed page and its predecessor stack intact, with the existing
finite visible error. An explicit retry reissues that read; it is not generation.
Zero/no predecessor is a local no-op, not an InvalidCursor probe to native code.

## Proposed controller surface and freshness

Add a presentation-only `inspectionPaging` member to `V2PlayState`:

```ts
type V2InspectionPaging = {
    bound: boolean;
    canPrevious: boolean;
    canNext: boolean;
    retainedPrevious: number; // 0..32
    earlierOmitted: boolean;
    navigating: "previous" | "next" | null;
};
previousInspectionPage(): Promise<V2BoundPage | null>;
resetInspectionPaging(): void;
```

This does not change a wire DTO, native schema or persistent state. Derived booleans
are presentation hints; public state mutation cannot create private cursor authority.
`previousInspectionPage` takes no caller cursor. Keep the existing page method and
its history-channel behavior; only its inspection path joins the new ledger.
Do not add Previous to the Play history channel as a side effect.

Before any navigation dispatch, require a live controller, current context and
snapshot, no inspector navigation/readBusy conflict, the exact current bound-page
object and unchanged scalar query identity/current request/next cursor. Revalidate
the bounded current query/page transport where needed, including actual selected
player. Detect in-place mutation and same-head object replacement rather than
accepting a matching head number alone. Retire/reset an invalid frame before any
gateway call; do not silently rebind its cursor stack to the replacement object.
The native Host independently reopens authoritative durable state and may refuse
a stale cursor even when the frontend believed the head was unchanged.

Starting a fresh inspection query, including an identical explicit Read permitted
view, clears the old navigation frame before pending notification. Accepted-turn
trace, recorded-turn trace and seed/event source navigation are fresh queries,
not a way to borrow the old stack. Search/view/at_revision form edits call the
reset method immediately. It advances only inspector freshness, retires its
pending presentation and clears source-link/match navigation metadata; it does
not cancel a native read, a history read or any gameplay/model operation.

Reset on context/lens/player/session/story/branch/head/view changes through the
existing selectedContextChanged path. Also reset when refresh starts/replaces
the current snapshot at the same head, on loss of snapshot, malformed context,
disposal, and any new inspection result published outside the owned navigation
transaction. Existing full-context fences remain at least as strict. No recovery
of old cursors when a prior context or observer is selected again.

Preserve the current body-retention boundary on an unsuccessful fresh query: an
already displayed result may remain visible with its **own bound query/context**,
but its old navigation frame is gone and both paging actions remain disabled
until a fresh successful Read. The panel explains that a new read restarts paging;
it must not attach the pending/failed form's values or a new source link to that old
body. This is retention of the current displayed object, never restoration from
a private-body cache. Context/lens/scope invalidation still clears private results
as the existing controller does. No old body is restored after that clearing.

Use the existing inspector query sequence, current key/context reference and
snapshot/result identities; do not couple this ledger to historySequence. Mark
the private navigation as in flight before notifying subscribers so a reentrant
Previous/Next cannot dispatch a duplicate read. A root query/context reset may
supersede it. Recheck ownership after each notification, before native dispatch,
after the reply/validation, after result publication and after final busy clearing.
Commit private ledger plus public page/paging metadata coherently before the
result notification; a subscriber reset must not be overwritten afterward.
Stale failure/finally handlers cannot clear a newer pending flag or republish an
old count, source link, cursor, body, error or notice. Dispose leaves no live ledger.

## Panel handlers, disabled state, focus and status

Place Previous inspection page beside the existing Next inspection page within
the Read-only V2 inspector. Keep both buttons type button; they must not submit
the query form. Do not change Next history page, receipt-source navigation or the
legacy inspector. Keep the existing current scope/head/inspected revision/privacy
labels and finite error alert coherent with the actual displayed result.

Both paging actions require an owned bound frame, current snapshot/context and
no queryBusy/readBusy/navigation conflict. Previous additionally requires a
retained predecessor; Next requires the current validated next_cursor. Disabled
presentation is not the only check: handlers capture the rendered bound-page and
context, then compare against `controller.get()` and live eligibility before
calling the controller. The controller performs its own independent private check.
An old captured handler after context/same-head page replacement does no I/O.

Query form changes invalidate paging before setting local view/search/revision
drafts, then recheck context ownership after that synchronous notification. A
subscriber may navigate, dispose or start a newer query there. Do not let an old
handler's subsequent setState overwrite a newer context's form. Form submission
also rechecks live context/snapshot and busy state; stale rendered values are not
permission to query the replacement session. Success uses the normal panel effect
that reflects actual inspection.query back into the form.

Use a small `role=status`/polite live message for pending direction and bounded
back navigation. At overflow/boundary, explain: earlier pages are outside the
retained back-navigation window; Read permitted view starts again. Do not claim
an absolute page number or show raw cursors. With an old displayed body after a
fresh-query reset/failure, say a successful read is needed before paging again.
Native errors remain in the current error alert; no optimistic success message.

Keep pager buttons mounted during reads/results. Do not focus a row, receipt or
another inspector automatically after an async result. Avoid any focus operation
from a stale completion. The active control/focus order must remain usable when a
button disables at a boundary, and status must announce the result without stealing
focus. Test actual DOM focus behavior in the application WebView; captured handlers
or SSR do not prove it. Any necessary narrowly scoped focus fallback must be
documented/accepted before implementation, not achieved with desktop input.

## Independent FIRST proposal

An independent author freezes the new source before different-author production.
Record original commits/hashes, enumerated groups and actual setup limits. Missing
methods or registrations are SETUP/unrun; zero matching tests are not a pass.
Author allowance is source/Git/hash only; Root later runs the single heavy slot.

Controller/transport FIRST should cover:

- First page, Next, Previous to null and forward again; exact same query fields
  except cursor, one fresh inspection_query/read per eligible navigation, and no
  stored-body restoration when the fake transport changes returned rows.
- At least35 forward transitions with a rolling32 predecessor cap, dropped-oldest
  notice, continued Next past overflow, back to retained boundary, explicit Read
  restart, and no cumulative page/body cache. Variable-sized pages stay usable.
- Pending duplicate navigation, successful/failed/malformed/stale replies, retry,
  final page, no predecessor, unsupported/empty views,128-byte cursor bounds and
  mutated public current query/page/next cursor/counts. Native authentication is
  not inferred from a fake cursor's shape.
- Session/scope/branch/head, player/lens/Play-Lab, view/search/at_revision changes,
  identical fresh Read, receipt/recorded-turn/source queries, same-head snapshot
  and page replacement, malformed context, refresh and dispose. No old chain is
  restored when selecting the earlier lens/context again.
- Subscribers reentering on pending, error, result and final busy notifications:
  reset, navigation, replacement/new root query and dispose. Count native calls
  and inspect returned/public/private ownership without weakening result checks.
- History channel forward behavior, existing trace/source ownership, pending or
  uncertain gameplay requests and old QueryInspector remain unchanged. Navigation
  invokes no prepare/poll/commit/cancel/retry/model/memory/author/export operation.

Panel FIRST must render the actual V2PlayPanel with only its existing narrow SSR
server-snapshot prerequisite, capture actual JSX handlers and invoke those handlers.
Verify button names/type/disabled states, root form changes, exact live owner guards,
old-handler no-op, pending/failure/boundary/reset status and preserved scope/observer/
head/error labels. Label synthetic Gateway, SSR and captured-handler evidence;
these do not execute Core, native IPC, browser DOM/focus or WebView rendering.
Do not replace the panel's behavior with a separately written view-model test.

## Later actual native qualification

A separately accepted fixed development harness should exercise the actual
V2PlayController, panel action paths, normal Gateway -> host_call -> Host Query2
and normal strict frontend decoder in a hidden/unfocused application WebView2.
Use one newly admitted synthetic workspace and normal shared Engine/Store APIs
to prepare a bounded Domain2 fixture before navigation. It must actually return
more than64 permitted rows for the chosen view/lens at limit64 and reach at least
a second page; prefer a small third page to verify last-page/back behavior.
Do not manufacture serialized query pages, edit canonical SQL or depend on a model.
Existing scoped Domain2/author-correction fixture patterns may be reused through
their public APIs; they are not permission to operate another owner's workspace.

Proposed fixture ceiling is128 fixed validated synthetic commands, at most four
stories/branches and no provider/model construction. Exact fixture recipe and
expected row counts must freeze before execution; desired counts are not measured
results. Include player and distinct NPC visibility sentinels plus a separate-story
sentinel. Rust determines each lens's actual eligible rows; fewer NPC rows must not
be padded with forbidden player narration to force paging.

During the navigation measurement, record zero gameplay/model/provider operations
and unchanged canonical event/state/receipt fingerprints, turn records and observer
knowledge. Fixture-setup commits are counted separately. Normal Store opens may
have runtime metadata effects; do not call an unchanged canonical hash a whole
database byte-equality proof. Distinguish command instrumentation/source review
from independent telemetry of all possible side effects.

Run Next/Previous through actual panel handlers and verify each displayed request
cursor/row identity against actual Rust pages. Read no old private rows when lenses
or sessions switch; clear pending/stale results and source links. Include root query,
search, historical revision and refresh resets, same-head replacement, stale reply,
error/retry and overflow presentation where constructible. A >32-page native cohort
is not required to test a32-cursor frontend cap: finite frontend FIRST can cover it.
If pending/late-read images need a fixed post-IPC reply delay, it follows an actual
completed native read and is labeled a delivery double, not a held Rust worker,
native read cancellation or physical process-death test. No generic debugger or
new arbitrary file/path/command/code/shell execution hook is permitted.

Capture coherent semantic snapshots containing selected story/session/scope,
player/observer, current head/inspected revision/query, actual displayed rows/receipt,
pending read/direction, retained-history count/boundary and visible error. Capture
only application-owned render images; individually inspect every produced image
for clipped/wrapped controls, misleading state, private text, focus and overflow.
Verify narrow/wide layouts and actual150% text scale using state/classes/computed
font sizes. A wide viewport or clamped1.5 input is not150% evidence. No desktop
capture/control, injected input, activation or user click-through is involved.

Keep bounded local frontend/native errors and exact native runtime/user-agent,
source/configuration/command versions, counts/timings, private packet paths and
unavailable checks. Separate shared Rust tests, Rust Host-library transport,
synthetic Gateway/SSR, actual IPC and actual native WebView execution. Review normal
non-harness output for absence of fixture hooks. Run appropriate frontend/native
checks and Rust Android host compatibility only; no SDK/JVM/Gradle/ADB/emulator/
device/model/OS/network probe is admitted. An Android host compile is not runtime
or phone semantic-parity qualification.

## Storage, review and handoff boundary

Only this proposal source is admitted now, below1MiB. No fixture, output root,
build, experiment or runtime execution is admitted by the document. Root must
declare exact cumulative fixture/render/frontend/target budgets, baseline/free
space, output paths, retention and finite launcher policy before later execution.
Use the accepted bounded process-owner rules: exact direct-child handling, output
and deadline bounds, sticky unknown/error/inventory failures, fail-closed storage
admission and safe normal-build restoration. No cap reset, silent repeated roots,
recursive cleanup, lost/frozen capture deletion or automatic evidence expiry.

All project source, commands, temp/cache and generated evidence stay physically
on D; start commands there with process-local TEMP/TMP=`D:/Dev/_Temp`. Preserve
installed tools/global cache contents and all ignored/uncommitted/recovery data.
Root owns the heavy slot. No downloads, dependencies, model assets, SDK/device,
stopped platform probes or protected concurrent chat/resources are involved.

The eventual reviewable gate reports exact FIRST/production/review lineage,
commands/counts/results, retained failures, environment versions, artifact hashes,
individually inspected render findings, native-versus-double limitations and the
next runnable task on #26. Full D05 inspection, unrelated shared memory features,
Android runtime and desktop epic acceptance remain separate. Do not check a task,
merge another owner's work, change repository settings or publish a release from
a proposal, source review or favorable synthetic test alone.
