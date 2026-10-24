# Author / V2 desktop UI qualification evidence

2026-10-23 local date; retained checks below ended on 2026-10-24 UTC.
Refs #12 M08.03 / #30 D08.05 and draft PR #135. **Bounded evidence report;
complete native journey and restart qualification remain pending.** No whole
M08/D08, model-quality, Android consumer, installer or release gate is accepted
by this report.

This report is the sole new path on `docs/m08-author-native-ui-qualification`,
based on `dfbe11c5bf57de74345f7c254c2f456a1ea24c55`. Claim:
[#30 6380007479](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6380007479).
The report author read source, logs, reports, capture metadata and hashes only;
it executed no tests, app, provider, model, device or desktop automation.
The coordinator (Root) owns actual execution and visual inspection.

## Current evidence boundary

The app uses actual AuthorController, V2PlayController and root Controller
actions, native IPC, the designated ArchiveBroker worker/status/cancel,
WindowLease, Host, Repository and Store. The fixed synthetic fixture and
fault controls are development-only. Root's native captures use the app's own
hidden, unfocused WebView and CapturePreview, not desktop capture or injected
input. The [frozen harness contract](M08_AUTHOR_NATIVE_HARNESS_CONTRACT_2026-10-23.md)
defines the exact closed setup, before/after-apply gates and journey assertions.

Five actual native cohorts stopped at recorded failures. Their accumulated
checks and 20 images are partial observations, not a completed 17-image
fresh/restart journey. No cohort reached its restart process. The last native
cohort reached 71 checks and eight images, including observed A after author
world truth B and Sable isolation, then continued typed Give failed with native
`Version` and remained at child head 2. These results do not qualify continued
V2 Play, the later lost-ack/recovery/cancellation cases or saved-child restart.

Separate synthetic actual-Main tests now pass 18 cases; actual-controller inert
React recovery-panel rendering passes six cases. The full frontend verifier
passes at `dfbe11c`. These results close their named controller/render defects
but are **not** evidence of native IPC or WebView execution of the fixes.
The coordinator's [PR #135 evidence comment](https://github.com/OptimumAF/LocalLore/pull/135#issuecomment-6379952552)
records the same boundary. Accepted prerequisite PR #133 has its separate
[source-bound qualification](M08_V2_PREREQUISITE_QUALIFICATION_2026-10-23.md).

## Preserved stopped native cohorts

All paths below are relative to the task-owned, gitignored
`<evidence-root>/author-integration-artifacts`. Each cohort has bounded build
and app stdout/stderr/process records, fixed synthetic SQLite and an
`initial/report.json`. Source associations in this table were explicitly
confirmed by Root, who committed each correction before launching it and
recorded the source in the outer tool handoff. **Failed launchers stopped
before writing summary.json/source/binary hash manifests.** The report does
not claim a self-contained source manifest or retained matching executable
for these stopped cohorts, and does not attribute a later executable to them.

| Outer log / cohort suffix | Root-recorded source | Checks / images | Actual stop and disposition |
| --- | --- | --- | --- |
| `author-native-first.log` / `5cdadd04-84f0-4fa8-a239-10d50c65225e` | `da8d150f03328b98f0b6a35e0d0d542e0c51f159` | 2 / 0 | `AuthorDeadline:native-granted-author-context`. Author UI could not acquire native context. Root corrected/tracked generated author command permission files and added bounded context-error evidence in `79c93f1`. The empty error buffer in this first report does not independently prove the permission diagnosis. |
| `author-native-permissions-corrected.log` / `2b050725-6716-45a1-a10d-7183fef699b8` | `79c93f128393bc0a3f8b269b57d1369f0a22754f` | 18 / 2 | Duplicate-key rejection probe expected `InvalidAuthorInput`, while the actual Core parser category was `Malformed`. This was a fixture error, not acceptance of duplicate keys. `7d99fde` corrected only that category and repaired layout observed in the generated form images. |
| `author-native-layout-corrected.log` / `45fb021d-1284-42fe-b910-4a97f6e8c4ed` | `7d99fdedf3f2804f7bc331805b18175f7795dd72` | 30 / 3 | Concurrent archive probe omitted the native command's required session and expected revision. It could not establish ArchiveBusy contention. `5734a08` supplied the real fixed session/scope/head and focused captures on the relevant visible preview/error/pending/outcome sections. |
| `author-native-valid-contention.log` / `d416707c-af39-4256-8a15-bb1d0f7e2b30` | `5734a08535b5abe76ae89e4f56baed5dbed4a904` | 55 / 7 | `actual-knowledge-query-returned`: the journey read immediately after a lens change before the visible query control was ready. `13e92ed` waits for actual snapshot and readBusy=false, matching the UI's readiness, and improves scoped header legibility. |
| `author-native-query-readiness.log` / `5071afe9-f77e-4e07-8a2a-683936a847f4` | `13e92edfdf717727edbcbc4a0d8c5f1e4f403b13` | 71 / 8 | `AuthorDeadline:actual-V2-gift-root-refresh`, with one native `Version` error. The typed fixture inference route still requested legacy character context on Domain2. Shared typed-context support is a separate prerequisite; neither the legacy refusal nor the test's expected saved revision was weakened. |

Each cohort directory is prefixed `author-native-`. Each first and second build
process exited 0, then its initial app process (`run-3`) exited 1 with
`timedOut=false`, `truncated=false` and no spawn error. The outer launcher then
reported `AuthorHarnessChildFailure:run-3`; it never started restart. The
native permissions build log separately records successful compilation in
12.81 seconds; it is not an app success result.

The last report's `failedCheck` is
`author-native-observer-actual-native-WebView2-image`: the harness retains its
most recently successful check until another assertion updates it. Its actual
failure is the subsequent Give deadline and native Version error, **not** a
failed observer image capture. The image exists and its capture metadata says
`native-webview2`.

All five app stderr files contain one bounded Chromium shutdown diagnostic,
`Failed to unregister class Chrome_WidgetWin_0`, error 1412. The first four
report error buffers are empty; the fifth has exactly one native Version.
Neither empty application buffers nor this known shutdown message is described
as zero-error native qualification. Raw bounded stderr remains local.

## Render observations and integrity

There are 0 + 2 + 3 + 7 + 8 = **20 actual app-owned PNGs**, each paired with a
semantic JSON snapshot and `.capture.json` metadata. Every existing image's
capture metadata reports `native-webview2`. Root reports personally inspecting
**all 20** across the five cohorts. This report author inspected metadata and
hashes, **not pixels**, and attributes that visual inspection to Root.
Early form/layout and capture-focus defects produced explicit source fixes;
earlier imperfect images were retained rather than replaced in place.

The last cohort contains consent, exact preview, rejected, pending, cancelled,
saved, history and observer images. It contains no continued-turn receipt,
late-cancel, lost-ack, recovered, narrow, stale-context or restart image. The
existing eight captures must not stand in for those unexecuted assertions.
Their browser-reported userAgent is Windows x64, Chrome/155.0.0.0 and
Edg/155.0.0.0. This is a captured userAgent, not a separately queried loaded
WebView runtime or SDK build version.

| Cohort suffix | `initial/report.json` SHA-256 | Initial artifact count / manifest SHA-256 |
| --- | --- | --- |
| `5cdadd04-84f0-4fa8-a239-10d50c65225e` | `82190b22daf69e7125c4f1696901811639944cda8aca6ffef6cedac82c4d84fc` | 1 / `a4edfd62949a340e595b4cd04cdef7337b22212d61ac7cc9bd19a2490b71d080` |
| `2b050725-6716-45a1-a10d-7183fef699b8` | `7c0a229d3258737478e11f8a6a7779143ab826d87b6f7099dde8259ca621c100` | 7 / `76e20b12475f4619b97f7e26d55b7d4bc28c19aacfca557b3c01b061c6c8a209` |
| `45fb021d-1284-42fe-b910-4a97f6e8c4ed` | `1cbe4367dd3d1a2614fd6cfc98516e3aa98b064920df02e4582aed8ae16f0632` | 10 / `5ade5dd24d92f3f7c66cf031d1f7bd8e2b6ebc8574d97a19094bab4da28e56d6` |
| `d416707c-af39-4256-8a15-bb1d0f7e2b30` | `eab78a619950ef438daabeca72c5b72a1cbbae85aa06bfd7cb786b3a6fc3ac28` | 22 / `b97ba513a73b122890d483381da23341e6edbab29ca340d92822255d420227cb` |
| `5071afe9-f77e-4e07-8a2a-683936a847f4` | `89805c4a97fecb5f307054b88b9aee02ed73c27560932b54f74152c83305dd0a` | 25 / `44ea1c88b4d835a1e66192a3c45683f63bbdacaa4f53acf90b44fa2460590858` |

Each artifact manifest was computed read-only in memory: select all `.json`
and `.png` files under that cohort's initial directory, sort filenames with
ordinal comparison, form UTF-8 LF-terminated lines
`initial/filename|lowercase-file-sha256|bytes`, then SHA-256 the joined bytes.
This covers the report plus all image/snapshot/metadata triples without
publishing raw synthetic private previews. No saved artifact was modified.

## Actual-Main and headless recovery fixes

These are separate from the five native cohorts above and were not validated
by rerunning native WebView journeys yet. Actual-Main checks import the real
Main subscriptions/invoke/retention with controlled synthetic transport. Panel
checks use actual AuthorController and AuthorPanel with inert React server
markup and mocked native outcomes. Neither category invokes the native app.

- The earliest Main checker stopped on a rejected synthetic gate before the
  result collector completed (`main-author-context-original-red.log`). That
  fixture execution failure is not a behavioral pass/fail count. Corrected
  collector execution exposed 10 passes / 4 failures: all four Domain1 write
  routes reached native transport during a shared barrier. The focused Main
  guard then passed all 14 existing cases; both logs remain retained.
- The frozen known-ID status rejection test exposed 15 passes / 1 failure:
  controller uncertainty did not latch shared unknown. The owner/ID-fenced
  status rejection change passed 16 cases.
- A further frozen exact-terminal recovery case then produced 17 passes /
  1 failure: changing only brokerUncertain retired the captured operation ID.
  After selection identity excluded that availability flag, the same 17/1
  result exposed transport uncertainty being treated as a sticky malformed-data
  fault. `c94bf43` preserves identity through that flag-only change and lets
  a validated original terminal result resolve transport uncertainty while
  malformed private-data faults remain sticky. Final actual-Main result:
  **18 passed / 0 failed**.
- After that controller identity correction, frozen original Panel rendering
  produced **2 passed / 4 failed**: availability hid known-ID inspection,
  confirmed outcomes and captured read-only recovery. Panel-only fixes
  `3e49875` / `7c79287` yielded **6 passed / 0 failed**. Recovery shows bound
  operation/child/outcome metadata without private preview, reason or fact
  prose in restricted contexts; it enables no new author start. Lookup/open
  retain their original context gates. Whole-ack loss invents no operation ID.
- At `dfbe11c`, `node verify-frontend.mjs` passed the complete frontend gate,
  including strict TypeScript, schema checks, 99 synthetic V2 decoder checks,
  eight V2 routing cases, 20 V2 scheduling cases, 92 author decoder/controller
  checks, 13 author callback cases, six Panel renders, 76 author retention
  checks, 18 actual-Main cases and the existing legacy suites. These overlap
  other runs and are not summed into a count of unique native tests. The
  verifier also confirms dev journey/control hooks absent from the normal
  frontend bundle.

## Reproduction and retained logs

Commands below describe the existing harness/checkers; this documentation
assignment did not execute them. Use the exact source under qualification,
the existing bundled Node and task-owned absolute existing directories.

```powershell
# apps/desktop, synthetic/headless checks:
node check-main-author-context-review.mjs
node check-author-panel-recovery-review.mjs
node verify-frontend.mjs

# apps/desktop, ONLY after exclusive native execution allocation:
$env:LOCALLORE_M07_MEMORY_ARTIFACT_ROOT = '<owned-artifact-root>'
$env:LOCALLORE_M07_MEMORY_TARGET_DIR = '<owned-native-target>'
node author-harness.mjs
```

The launcher builds `node build.mjs --harness`, then
`cargo build --manifest-path src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir <owned-native-target>`.
It uses one Cargo job, no incremental compilation, dev/test debug info disabled
and ordinary uncapped SQLite; it refuses nonempty LIBSQLITE3_FLAGS. It spawns
only its own hidden processes with shell=false, caps stdout/stderr separately
at 262,144 bytes, records truncation/deadline/exit, and admits only fixed
fixture actions. The native stage deadline is four minutes; build deadline
15 minutes. No desktop input, activation, capture, arbitrary native code,
provider, SQL route, renderer-selected path or new worker/server is introduced.

Outer logs identify Node 24.22.1. Rust is pinned 1.93.1; the previously recorded
Windows 11 Pro x64 build 26300/toolchain baseline is inherited environment
metadata, not a fresh probe by this report. Frontend/native dependency pins
and earlier Android/build evidence are in the prerequisite qualification.
No fresh physical Android or real-model run is part of these observations.

| Relative log | SHA-256 |
| --- | --- |
| `author-native-first.log` | `e810d13368ee93dff625fdf7dc5d126dfd97c18768a41a1304ab5fea4cdb51c8` |
| `author-native-permissions-build.log` | `c539aed93db3068e514c09e24e01d1ace1c4105051a66bfe628f6c14f6714145` |
| `author-native-permissions-corrected.log` | `7d0776470cb56ab6df3a180418b9158e9084f54236ea46711db2fc7d85d76792` |
| `author-native-layout-corrected.log` | `00290c28ecdc44ac51a9c9fd9a21c6597eafbbd47ee353ce09fa91285cac01c0` |
| `author-native-valid-contention.log` | `0a27d637e6bf86b459f70511e11463dc29226a3ce8518080c3c9220b8ed5978f` |
| `author-native-query-readiness.log` | `aebd6cf0ec0c7c48962598feaa5f04649926639f6a4048cf36310caca625b954` |
| `main-author-context-original-red.log` | `c0bf7c101a3d6c2ab09161a2270ae426a7ca295ef932e1465a9565fc8cf0ea32` |
| `main-author-context-corrected-red.log` | `65df9811550f296876e37f04a0729d209a19cd9a188cba4aaea3a967c4e87b94` |
| `main-author-context-first-green.log` | `84ad80edae65a1ff9775dbb8a897091276f16083efe530ec6f4f88f6d1040370` |
| `author-status-transport-original-red.log` | `b372122d122fa6b45f44bb2101eac4d9aa036893a8b68a16d5f618a246c0060e` |
| `author-status-transport-first-green.log` | `0998a02ac53e226bec3f04724b58f66e8c1fd2462b75125e8320f0b2975cca3d` |
| `author-terminal-recovery-original-red.log` | `e67d065b166e09d53fe5868101a550b1c308d45bc20794d2861313fbe26fabf4` |
| `author-terminal-recovery-identity-corrected-red.log` | `2678010ef9b2d890c20563075cef192597cd37b0d82c7f3f6adb9d1fa41844e2` |
| `author-terminal-recovery-corrected-green.log` | `1320e3968c4e42d090d4adfa05dbc459569b7104b7416b4c0997eb015741f1f1` |
| `author-panel-recovery-original-red.log` | `711268de981bd5a63f2a308c23c3c6dc9428315de5b6e4da1ffa008ae9a0ed07` |
| `author-panel-recovery-first-green.log` | `a6d8822bf8ad6ff09179094e1d99e78f8e0a5a87ec024b538f42e6fb98c61f5a` |
| `author-frontend-recovery-corrected.log` | `83061a4c4d1fe3dfb32ebce21a093c6f15ce88730b37c7a5d14cd0dbea8ab13b` |

## Pending final native appendix

This section is deliberately pending until Root's next terminal results.
The author continues evidence work; it is not a completed acceptance record.

| Required final evidence | Status at this report's current source |
| --- | --- |
| Shared typed Domain2 fixture continuation prerequisite | Separate owning PR/checks in progress; no fresh UI qualification inferred. |
| Exact integrated source, clean/dirty state and native binary/dist hashes | Await upcoming source-bound cohort. |
| Complete fresh native journey | Pending; previous cohort stopped before typed Give. |
| Second actual process: saved-child Domain2 read/resume | Unrun; no native restart acceptance yet. |
| All 15 fresh + 2 restart semantic/capture pairs | Planned allocation only; not 17 passing images. |
| Final expected rejection/cancel errors and bounded native stderr | Await completed reports; preserve original Version/shutdown evidence. |
| Root inspection of every final image and visible-state corrections | Pending for upcoming cohort. Earlier 20 inspected images remain separate. |
| Normal frontend/native compatibility and Android checks after shared changes | Await Root's source-bound terminal checks; no in-progress run is counted as passed. |

Author-operation recovery after restart remains explicitly unavailable. Only
saved timeline read/resume is proposed for the restart stage; no persisted
private fullinput, recovery journal or automatic apply is added. Fake inference
must stay visibly labeled; local in-memory progress must not be called durable.
Native inspection never grants knowledge or generation privileges. Missing
Archive3, Android D2 consumer/author UX, model-quality, physical phone,
installed offline journey and release/license/security gates remain with their
owning tasks. No merge, release, repository setting or protected resource is
changed by this report author.
