# D05 native inspector integration source review

Refs #26 D05.01/.03/.04/.06/.07; reviewer claim6358158160 and UI handoff6358123197.
Review baseline4db7e5d, the nine-commit UI slice after shared integrationdb3e6ed.
The reviewer owns only this document on review/d05-native-boundary. No app/native,
shared query, schema, storage or fixture implementation was edited here.

This is independent UI integration/source review, not independent approval of
the original query module authored by this reviewer. The separate shared review
and its observer-leak corrections retain their own authorship/evidence. No score,
human acceptance, complete D05 exit gate or release follows from this report.

## Scope and actually performed checks

Read query-model.ts, QueryInspector.tsx, controller changes, App/modal/navigation,
model/main/journey glue, native harness label/initialization changes, trusted
launchers, public native evidence and the relevant frozen Host/query behavior.
Checked source status/history/net diff, generated-schema value equivalence,
source hashes and whitespace. No build/test/model call, app/browser launch,
process control, CUA/device operation or protected resource operation occurred.

The reviewer used view_image on four existing app-owned captures from the
reported native81/14 run: d05-diff, d05-npc, d05-knowledge and d05-narrow. No new
capture or desktop read occurred. They show the selected historical potion
before/after, a clearly private Mira History lens, separately labelled statement/
belief/truth, and wrapping narrow history rows. Four inspected images are not an
independent verification of every assertion, privacy case, layout or assistive
technology behavior in the reported run.

The baseline changes22 files, all under apps/desktop and docs/desktop/D05_NATIVE*.
Native changes only add fixed development labels/driver selection; the frozen
inspection_query command uses existing Host IPC. There is no new production
filesystem/process endpoint, database writer or model pipeline in this slice.
30827e1 reformats the root-owned generated schema; semantic JSON equality must be
distinguished from byte equality and the earlier executed build hash.

## Concrete findings

**Removed-field Why path loses the actual historical record at4db7e5d.**
QueryInspector offers Why is this true? for every selected Row.
whyInspection(change) chooses after or before, then searches Provenance while
retaining the inspected after revision. For the accepted potion transfer,
before contains player/item/potion and after is absent. That field cannot exist
in after-head state_rows, so the requested provenance page is empty. The user
cannot follow that button from the disappearance to prior provenance and its
completed-turn cause. The native test exercises Why for an extant profile field,
not the selected removed-potion comparison. The viewed d05-diff capture confirms
the removed-field state and the offered generic button, but is not execution of
the failing navigation.

The same generic path uses a History/message key that is not a state Provenance
row key. Appropriate behavior is type-aware: prior provenance at before_revision
for a removed field plus an explicit completed-turn/event path; accepted event
source navigation for History, or an honest unavailable action. No shared
provenance or new causal fact should be fabricated locally. This source finding
was sent before acceptance and confirmed by the coordinator, who assigned the
scoped UI correction to the existing app writer.

**Return-to-Play label preserves the private Lab lens at4db7e5d.**
The table's Return to play control calls showQuery(false) only. With a Lab/
omniscient or character lens selected, that closes the table but retains Lab and
shows the legacy private inspector. The control must either actually restore the
Player/Play lens or honestly say Return to chat/Close inspector. This is a
product/privacy-label issue, not a bypass of the Host's trusted grant. Reported
to the coordinator for the same scoped UI handoff.

**Narrower retained-state/text observations.** clearQuery removes rows, selection
and cursor history but preserves search and historical revision across story/
lens changes. A private-derived Why search key can therefore remain visible in
the search input under a new Player lens even though the new page is correctly
filtered. This is retained query text, not a backend search/count leak. The
coordinator was asked to clear or clearly scope it. The acknowledgement source
also contains a replacement glyph in its separator; that text-only defect was
reported. These observations do not imply that discarded private rows reappear.

**Source correction reviewed at78e55ff.** Removed-field navigation uses
before_revision, labels prior provenance as a former field and retains an
explicit before/after change trace. A separate completed-turn-history action
first queries the observer-visible boundary event, then its permitted turn.
If the boundary event is hidden it says causal evidence is unavailable; it never
reads raw Player receipts to infer an NPC's hidden turn ID. Several effects in
one turn are not misrepresented as a proven single-event cause. Extant fields
use their inspected provenance, History events/messages route to permitted
accepted sources, and already-Provenance/no-source actions are disabled or
honestly labelled. This addresses the original removed-potion path without a
new causal inference or shared API change.

The correction adds returnToPlay, which closes the query workspace and really
restores Play/Player, clears legacy private inspection and resets search,
historical revision and trace. Story/lens changes use the same context reset.
The minor replacement-glyph text observation remains outside these functional
fixes and is not treated as a publication blocker.

During review of that repair, the reviewer identified another stale-navigation
path: followInspectionSource awaited a fenced query but then selected a record
from whatever page was current. A held StoryA source followed by StoryB with a
coincident Event1 could select B's event and publish an old source notice, even
though A's page was correctly discarded. This is stale selection/notice behavior,
not private-row disclosure.78e55ff returns/captures the query epoch across that
helper and checks it before selection and the caller's notice. Its controlled
actual-Controller regression holds that exact A→B response and asserts no B
selection or old notice. Other new post-query trace updates have matching epoch
checks and reject a Row absent from the current page before navigating.

No remaining substantive UI source blocker was found in this bounded recheck.
The specialist reports a diagnostic native93-assertion/14-capture run and npm
checks passed; a final clean native run was still underway at this handoff. Those
are attributed results, not reviewer execution or fresh visual inspection. The
original clean81/14 evidence alone cannot be reassigned to corrected78e55ff.

## Full-context and privilege audit

Each query captures exact session, scope, current expected head, inspected head,
observer kind/ID, view, search, row limit, cursor, workspace mode and query/session
epochs. stillCurrent compares that context on both success and error. Lens,
story, refreshed head and view changes synchronously clear the old page and
selection, then issue a new query. One current page and a cursor navigation stack
are retained rather than a cache of private pages. A stale expected head clears
results and offers explicit refresh; no stale page is relabelled with a new head.

checkedPage validates matching scope/head/revision/observer/view/privacy,
bounded rows/bytes/cursor, known variants and unique keys. It compares observer
kind/ID rather than JSON object property order. Character-lens Message rows are
rejected even if a malformed response tries to supply one. The consumer is a
wire-integrity/display check; authority still comes from the frozen shared query
filtering eligibility before search/count/pagination. It cannot authenticate a
compromised native process or replace the engine's rules.

The native Host's Story Lab grant is constructed outside renderer JSON. The
modal requires deliberate UI acknowledgement and offers focus/Escape/cancel;
normal Play selects Player. The docs explicitly state that this acknowledgement
is not a hostile-renderer or OS sandbox. Query observer selection never changes
the gameplay actor, generation context or persistent character knowledge. No
inspection method invokes prepare/commit or a provider; fake fixture preparation
in the opt-in journey is separately labelled setup, not inspection behavior.

Historical comparison resolves a receipt's final event boundary, then requests
the actual completed historical revision. It does not relabel today's projection
as an older state or treat each event as a complete turn. The shared API owns
replay and invalid partial/future-boundary rejection. Seed/event/withheld source
types remain distinct, withheld source buttons are disabled, and explicit copying
contains only the selected current page row plus scope/head/revision/observer/
privacy. Clipboard sharing can contain private story text and is documented.
No arbitrary JSON editing, SQL or model administration is added.

## Semantics, UI and native evidence limits

Typed rows retain canonical field/truth, recorded statement, subjective belief,
discovery/observation/message and derived comparison labels. Directed relationship
from/to and independent dimensions are displayed separately. Promise status is
labelled derived at the inspected time; unsupported summaries/retrieval indexes,
branch history and missing profile fields are shown rather than invented.
Duplicate display names retain IDs. Source links remain read-only navigation;
raw JSON is a collapsed selected-record detail, not a competing state authority.

The native entry point adds only a dev-harness inspecting flag and fixed labels.
Normal driver imports remain behind the compile-time harness constant, with
normal-asset hook checks updated for the inspector. Trusted output/target overrides
are launcher-only and do not become renderer path authority. Executable hashing
uses the actual selected regression target and replaces absolute-path keys with
the native-target placeholder. The inspector launcher uses a new synthetic SQLite
workspace through two executable processes; it does not load a real model.

The specialist's public evidence records clean49e6413:81 distinct assertions,
14 app-owned captures and restart. It attributes default15 native tests, dev17
plus2 wrappers, strict Clippy/default+dev, frontend checks/format, normal build
and legacy163/native+headless, durable33, export36 regression assertions. Those
are specialist-executed checks, not reviewer reruns. Partial multi-event revision
and unprivileged-grant denial coverage belongs to separate shared tests; the
native future-revision vector is not evidence those other cases ran in the UI.

The source81/14 evidence precedes this review's corrections. Later combined
integration must preserve the independently corrected D04 manager/runtime and
dd3de57 model-status final-refresh fence: the isolated D05 baseline predates those
publication fixes. Reusing the UI's scoped diffs does not establish a new combined
app run or new-binary evidence. Long-history performance, full accessibility,
remaining M06/M07 memory dependencies, quality, offline/package and phone gates
remain open. The coordinator owns final source/evidence reconciliation and
publication, with no whole-D05 acceptance asserted here.

## Narrow recheck of the shared privacy corrections

At the coordinator's request, the reviewer also read the staged query/Host/tests
in source-inspection-core, based on accepted native merge513a770. The query module,
its tests and Host integration matchdb3e6ed; the query Host fixture additionally
uses an atomic unique suffix for its temporary path. The source changes retain
the same shared API. This is a recheck of the coordinator's two fixes identified
by the separate original D05_SHARED_REVIEW, not an independent approval of the
original module authored by this reviewer, and not execution of the tests.

The original NPC History disclosure is corrected: Message rows are created only
for the Player/Omniscient display and an entirely visible receipt. NPCs retain
their individually witnessed Event rows, including actual Said speech, without
receiving the player's raw FreeText prompt or narrator display text. The
historical_v2_replay test retains Player original input, witnessed NPC events and
no NPC Message row. The completed-visible-history test preserves draft exclusion
and uninformed Sable isolation. This fixes the original P1 source path rather
than merely hiding its text in the UI.

The original hidden promise-completion inference is also corrected: collect
first clones the visible promise and filters completed_by through lens.sees.
Both status computation and appended completion source then use that filtered
copy. Unseen completion adds neither fulfilled nor a new Withheld source. The
same filtered rows feed Provenance and both replayed sides of TurnDiff; search,
count, cursor and pagination operate after those rows are constructed. Incoming
terms also require witnessed creation, while an actor retains its own outgoing
promise view. No global completion source is reintroduced by the UI.

The private_promise_completion test compares whole NPC Promise and Provenance
rows before/after hidden completion, asserts zero fulfilled-search matches and
no promise ID in the diff, while Player still sees fulfilled. The facts/
statements/beliefs/discoveries test keeps distinct origins, confidence and event
links, and excludes the unwitnessed claim from Sable. Reading these cases and
the corrected code resolves both original P1 findings at source level. It does
not establish generic semantic privacy beyond the implemented engine/lens rules.
The coordinator reports177 Rust cases and strict Clippy passed, including16
query-module and2 Host/SQLite cases; no result is presented as a reviewer rerun.

Exact reviewed Windows checkout SHA256s for this narrow staged shared recheck:

```text
8e10da900014a73423aab0a0e97174ca925c6dd57d395261b7f671be9c1bf640  crates/locallore/src/inspection_query.rs
20cd1f8e00b486e584fbdc8916699622b703e71c1806f5d577e4b2c7d480bd94  crates/locallore/tests/inspection_query.rs
c572816bb86a323129d64b327193ebe82cdbd79c48e5cbed508abf72f8bda918  crates/locallore/src/host.rs
aaf922f702164385962e56e2392328ef9b6dc37424bb859f7c6d869df6d6f615  crates/locallore-workspace/tests/inspection_query_host.rs
```

## UI source identities and execution disposition

Reviewed UI correction78e55ff changes five existing files from the original
22-file D05 slice: check-inspection-controller.mjs, QueryInspector.tsx,
controller.ts, query-journeys.ts and query-model.ts. The intervening50946f8 is a
separate D04 model-status regression file, not a new D05 feature or evidence that
the isolated UI branch incorporates the root's later D04 production fixes.
The coordinator retains responsibility for combining the scoped diffs safely.

The following22 SHA256s identify actual reviewed Windows checkout bytes at
78e55ff, including checkout line endings. The source commits identify canonical
Git blobs; the hashes are neither package signatures nor a binary reproducibility
claim. The three original D05_NATIVE documents remain historical81/14 evidence
pending the specialist's separate final correction handoff. No corrected native
result is claimed by hashing their unchanged bytes.

```text
0dbf8c27dd2c358d03f72adb9f9809d6c3de4efacdc2285289ab0f32a3493555  apps/desktop/README.md
688f74cf88612f172d816396763d5faf73ed62c7d944ab83d92995b1c198bd21  apps/desktop/check-inspection-controller.mjs
248ffe5c06d7e986a876d83851fa9472cdba23fed419699549a9baf1a5f19bbd  apps/desktop/durable-harness.mjs
b67f3d05b82b2b1bb1fe39823d433d0f5c0c1dcc39ca14ba87ee44d9f732bda7  apps/desktop/export-harness.mjs
280bc29654719a89aa82236a5b8b69e22b181095eb6b4d0ba421db5a8b59b6e5  apps/desktop/harness.mjs
b6ac394e1d82c8e7d21a573b32284cb62d46b0f4411d95e9d400b75c1ccc6c89  apps/desktop/host-v1.schema.json
1b99bf617ba193433de8eff3b2c8cf33de6da77df1424ef9ca95ae322c483ce4  apps/desktop/inspector-harness.mjs
5fc7d0d7ede3182c43adf5790d5f8263801ab0fc56d990602caf85a09b930763  apps/desktop/src-tauri/src/harness.rs
ec636c202a0c32b12507d99711dcf1f225df238a0f606b94dd41df755afaee7b  apps/desktop/src-tauri/src/main.rs
6582ebc54bead5d37da20e57e43cc4c290866a64e46f19235e64d341e08fc57b  apps/desktop/ui/App.tsx
9664a9b2bfb12cbb6bef7480e6d2ae2adccc7e9266b0d5f0affbc48e32ce42fc  apps/desktop/ui/QueryInspector.tsx
195d7f3c3f316add3b6c52c340125035aa37ab2f90042189bb21167148ebf39d  apps/desktop/ui/controller.ts
1aea170c9e2330487cccd12ff494e1f1fdcd674a11ec9d4c2413c68ad259c9c6  apps/desktop/ui/journeys.ts
b7f999d7db4ae19c93257bc6669aec4d9deb4dbf260d751b9de4392ff8527720  apps/desktop/ui/main.tsx
8460854e13673ced0e55215296e7b47faec63835a39d824045610e8605df6b87  apps/desktop/ui/model.ts
85ca50befbabf903b30e7db2f2aa31eb6c8cb5c9b8050d36b081e09bb3599a8b  apps/desktop/ui/query-journeys.ts
f56879bd45ee228bfd5e7764927b110ba628151fc6617936517c9e005ce3dff1  apps/desktop/ui/query-model.ts
d91a7a941dc0878603556415946494ea57a30959dcfa67a6266194fac54c61bd  apps/desktop/ui/style.css
9d7c738f00fa4089d591d211ef6f4136e045a06f8a8dae20afcd3bf5e9b36b87  apps/desktop/verify-frontend.mjs
39c2031de581afca433de218c8d91ab76b3e1cc6c0f882d55012fc52c6b9fb56  docs/desktop/D05_NATIVE_EVIDENCE_2026-10-22.json
95314f47c995ae9ed5c4dfa1162375a873738b4ec4eeef2d0eebcfed762223b5  docs/desktop/D05_NATIVE_INSPECTION.md
762ab70c6bbe77d0bf503db3a874ace459ffd3d4afe294c70b69c2f1282426b8  docs/desktop/D05_NATIVE_VERIFICATION_2026-10-22.md
```
