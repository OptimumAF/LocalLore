# Corrected-timeline resume proof

Refs #30 D08.04/.05, a focused desktop adapter correction. The implementation
has passed the frozen synthetic controller suite; final integrated frontend
and native author-open verification remain pending. This does not complete D08.

## Problem and change

An explicit author correction creates a saved Domain2 child. Main connects
AuthorController's `openChild` effect to the existing `resumeTimeline` helper.
The actual gameplay Controller can successfully select that child, read its
thin snapshot and store it in `playV2`, with `play:null`. The helper previously
accepted only `play`, so it could throw `NotReady` after a successful switch.
AuthorController presented that false failure as `Wire` in the frozen case.

Production commit `6a30c90533f9027a169de3f47eff42a61d738496` changes only
`apps/desktop/ui/timeline-controller.ts::resumeTimeline`: inspect
`s.play ?? s.playV2`, requiring the same requested/selected scope,
requested/projection scope and selected/projection revision equality. The
existing error-category and `NotReady` fallback policy is unchanged. The helper
still calls the existing Controller resume/switch path; it creates no session,
canonical writer, permission or inference implementation of its own.

## Frozen evidence

The independent seven-case checker was frozen at
`c6a2d564dd0983cad612f0f36da58ecbbc9fa95f`, based on accepted
`61431c0e243617e287053dcf3f3b9ebc0d837eef`, before the production change.
Its SHA256 is `b03a341d11de49b1c1127ab360ed1606c64636c02f165543af6c465fe49a8ebd`.
Root ran both cohorts centrally; the source author did not execute the checker.
Both terminal process records report clean source and unchanged terminal source.

| Actual source     | Result             | Command wall time | Exit |
| ----------------- | ------------------ | ----------------: | ---: |
| Frozen `c6a2d564` | 4 passed, 3 failed |            1.063s |    1 |
| Fixed `6a30c905`  | 7 passed, 0 failed |            0.248s |    0 |

The original failures are two `NotReady` outcomes for coherent new/existing
Domain2 child sessions and the false `Wire` author-open error. Legacy Domain1
success and all three negative controls already passed. The checker is unchanged
between RED and GREEN; no expected outcome was retuned.

The seven groups exercise actual Controller, AuthorController and resumeTimeline
code with synthetic Gateway/workflow DTOs:

- New corrected child: exact child session, scope and head in `playV2`, no legacy snapshot.
- Existing corrected-child session: select it without a second native resume request.
- Legacy Domain1 child: retain the original snapshot success path.
- Parent resume reply: reject it as proof of the requested child.
- Wrong snapshot scope: refuse it rather than accept a parent projection.
- Wrong snapshot head: refuse it rather than accept an incoherent revision.
- Author readonly-found outcome and explicit Open confirmed child: use the same
  helper effect composition as Main without a false post-resume error.

The last case uses a synthetic failed preparation followed by readonly lookup;
it does not apply an author correction or fabricate an accepted Core receipt.
The checker does not execute Main's subscriptions, native IPC, Store, WebView,
model inference, DOM rendering or a durable restart. Its report retains these
limits and the actual source hashes. Counts and timings are regression evidence,
not performance qualification.

## Reproduce and retained records

With the existing locked frontend dependencies and pinned Node24.22.1, from
`apps/desktop` the actual command was the task-local Node executable followed by:

```powershell
& $taskNode check-domain2-timeline-resume-review.mjs
```

Equivalent repository-root reproducer and integrated verifier:

```powershell
& $taskNode apps/desktop/check-domain2-timeline-resume-review.mjs
& $taskNode apps/desktop/verify-frontend.mjs
```

The registration beside `check-timeline-controller.mjs` is included in this
packet. The full verifier and formatting have not yet been run on that addition.
Generated JSON reports default to ignored `apps/desktop/artifacts/checks`; the
existing `LOCALLORE_CHECK_OUTPUT_DIR` can select a task-owned local output.
Raw process records and logs remain local under `<TASK_ARTIFACTS>`:

| Terminal record                            | SHA256                                                             |
| ------------------------------------------ | ------------------------------------------------------------------ |
| `d08-domain2-timeline-red1.log`            | `a98b7b57d9a0c95487e0a6871aa24e4d2b29f1ede94ee43451edd1d4dcc7289b` |
| `d08-domain2-timeline-red1-process.json`   | `38cd3229c6f816891549d85c5d374a13d6e3715220a5243709281705514de652` |
| `d08-domain2-timeline-green1.log`          | `5e6fe2609489d3796e89f6432b50883d0443f18297ab35c53f3f9bc013ced657` |
| `d08-domain2-timeline-green1-process.json` | `43f47b7fa27623e1d6530620aea3ae66296be7fef0a36b2a24166254943a45ad` |

Process-record UTC dates are October27; these runs occurred on October26 in the
coordinator's America/Los_Angeles timezone. No local personal paths or raw story
outputs are included here.

## Historical handoff gate

Root still owns formatting, full frontend compatibility, integrated source review
and the focused PR. An actual mounted author Open confirmed child/native journey
on the integrated fix remains unrun; older native author/save/restart evidence
must retain its original source attribution. No hidden Domain2 Timeline/Fork UI,
timeline-context behavior, schema, permission, Android decoder or shared memory
maintenance changes are included. Android parity, physical phones, model quality,
packaging, release and whole-milestone acceptance remain separate.

## Current-main integration and native oracle

The prepared packet is now reconciled onto accepted main
`3f75b5d673512b165e18b2b1e34d3deafc69067a` in the separate integration branch.
The three original commits were imported without conflict as `4a9cc55e`,
`88924c2a` and `93c9c55f`. The frozen checker and helper implementation are
unchanged by reconciliation. The RED/GREEN measurements above remain attributed
to their original sources; no new integrated check has run at this handoff.

Current main adds Host StoryTemplate/CreateNamed and exact named-story creation.
Those operations do not replace resume, author correction or player snapshots.
Database schema remains5 and no SQL migration is introduced by this packet.
The Main author `openChild` callback, gameplay Controller and AuthorController
retain the same interfaces; native comparison integration is preserved.

The existing author native journey already awaits the actual Main-bound
`author.openConfirmed()`. Its older assertion checked the loaded V2 head only
after changing view, which could clear the false author error. A new assertion
now runs immediately after that await and before any view/lens change. It requires
author error=null, selected child scope/head2 and the exact Domain2 thin
scope/head2 with play=null. It uses no replacement resume or native response.
The existing `author-native-saved` and `author-native-history` captures remain:
the latter records coherent selected-child identity, empty author error, actual
neutral correction marker and inherited message provenance. Capture labels and
the initial15/restart2 image allocation do not change.

`author-harness.mjs` now includes `ui/timeline-controller.ts` in both its pre-build
and final source-hash inventories. Root must run the existing author harness on
a frozen clean integrated source with its approved isolated artifact/target
directories, inspect all produced images and semantic snapshots, retain bounded
stderr/errors and verify normal frontend/native restoration afterward. This is
a fixed synthetic native/Store/WebView journey, not real-model or Android proof.
The new native assertion and hash additions are source-only and unexecuted;
they do not retroactively strengthen the historical native cohort.

## Accepted-main qualification, October27

The focused correction is now reconciled with accepted main `22beeddd`, including
PR220 and the verified-memory inspection PR226. It preserves their verifier
registrations. At clean unchanged `534eccdbc6b1c839325d81805dbb88119d9f00eb`,
`node apps/desktop/verify-frontend.mjs` passes in21.636s, including strict
TypeScript, all seven Domain2 resume cases, other wired suites and normal-build
hook exclusions. Declared repository Prettier globs also pass.

The existing `author-harness.mjs` now enforces clean source, unchanged commit and
source hashes around every command, pre-launch/final product hashes, fixed
arguments and sanitized inherited test flags. Create-only source/product/failure
records and bounded logs retain failures. This is an execution guard rather than
the earlier inventory-only checkpoint. No new permission, provider or writer is
added. Command from `apps/desktop`, with the existing pinned Node executable:

```powershell
$env:CARGO_HOME = '<existing isolated locked-package cache>'
$env:CARGO_NET_OFFLINE = 'true'
$env:CARGO_BUILD_JOBS = '1'
$env:CARGO_INCREMENTAL = '0'
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:LIBSQLITE3_FLAGS = ''
$env:LOCALLORE_M07_MEMORY_ARTIFACT_ROOT = '<existing owned artifact directory>'
$env:LOCALLORE_M07_MEMORY_TARGET_DIR = '<existing owned native target>'
& $taskNode author-harness.mjs
```

Windows NT10.0.26300 x64, Rust/Cargo1.93.1, Node24.22.1, TypeScript7.0.2,
React19.3.1 and Tauri2.12.5; existing locked offline packages only. One heavy
process at a time, with no source edits during its bound checks.

The fresh actual native cohort `author-native-4384a82a-4f32-41ab-a93e-c85640344828`
passes **124 distinct assertions/17 app-owned WebView2 renders**. Initial has134
cumulative checks/15 renders/4.232s; restart18 checks/2 renders/0.932s. Both exit0,
without timeout or output truncation. The initial bounded error buffer contains
exactly the deliberately exercised Inventory, Cancelled and Cancelled results;
restart has0. These are retained errors, not an arbitrary suppression rule.

The named actual check
`confirmed-child-resume-proof-has-no-false-author-error-before-view-change`
passes immediately after `openConfirmed()`, before changing view. It observes
selected child/head2, real Domain2 scope/head2, legacy play=null and author
error=null. Subsequent actual typed play saves a child receipt at head3;
cold restart reopens the same child/head3 and preserves original parent message
and child narration scopes. Cancel, stale-context, late-cancel and unknown
operation lookup paths remain exercised. Author-operation recovery after restart
is explicitly unavailable; opening an already saved timeline is distinct.

All seventeen PNGs were individually viewed, including narrow mode. Captured
preview, pending, consent, receipt, observer, unknown and restart targets are
legible; frames crop some non-target controls and do not qualify the complete
long form or accessibility. The preview's error phase follows an intentional
unread second-consent rejection; a retained receipt after a later failed turn is
identified by its own turn/revision. No new target layout defect was observed.
Images use hidden/unfocused application-owned CapturePreview, without desktop
capture/control, activation, injected input or OS dialogs. Existing scripted
fixture inference is not real model execution.

| Measured local artifact           | SHA256                                                             |
| --------------------------------- | ------------------------------------------------------------------ |
| Cohort summary                    | `04b12abbd6ab85e87cc2de423d843b75067d2b38c0cec71ef5cb4fd0a64d7332` |
| Individual render-review manifest | `508d2c33a3aa15a085f20bab6a13ea6661e5e8afda7e657c6400661e6a5d5c0e` |
| Preserved tested GUI executable   | `58fa4c29952e3ff5a55a7daf59e123c65058192737494e2de82de64ef7dbd765` |
| Harness frontend                  | `143ec4ef9bcd33e2ab4f141ce17edaac81d5929800ee64f91ecbfa1c63701e69` |

Normal frontend and default locked/offline native build pass at the same frozen
source (18.00s native compiler/18.573s combined command). Default executable is
**unlaunched**. Normal frontend SHA256
`a1b7c1a0e5bfecabbbf15bcdc08c9f712a6e2e1317507a4d3bf472e0bd29c61e`;
normal native SHA256
`d7be49699f26ca23c21fc49507e522fb6525c3be9acf8177616f2806de1c6d4a`.
These are product identities, not a reproducibility comparison.

There are no Rust/native IPC/lock changes from accepted PR226; its shared796,
native246+2 and Android Rust package90 passing checks retain their source
attribution. No additional Rust suite or Android device/JVM/Gradle/ABI run is
invented here. Domain2 Timeline/Fork UI, full debugger/export/memory adapters,
bidirectional Android transfer, physical phones, models, current package/offline
and general accessibility gates remain separate. Full D08 is not closed by this
resume correction. Source, failures and acceptance remain linked from GitHub.
