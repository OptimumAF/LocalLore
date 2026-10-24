# Author / V2 desktop UI qualification evidence

2026-10-23 local date; retained checks below ended on 2026-10-24 UTC.
Refs #12 M08.03 / #30 D08.05 and draft PR #135. **First complete native journey
and actual restart passed; final-candidate confirmation/build checks remain pending.** No whole
M08/D08, model-quality, Android consumer, installer or release gate is accepted
by this report.

This report is the sole new path on `docs/m08-author-native-ui-qualification`,
based on `dfbe11c5bf57de74345f7c254c2f456a1ea24c55`. Claim:
[#30 6380007479](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6380007479).
The report author read source, logs, reports, capture metadata and hashes, and
viewed two saved app-owned PNGs; it executed no tests, app, provider, model,
device or desktop automation.
The coordinator (Root) owns actual execution and visual inspection.

## Current evidence boundary

The app uses actual AuthorController, V2PlayController and root Controller
actions, native IPC, the designated ArchiveBroker worker/status/cancel,
WindowLease, Host, Repository and Store. The fixed synthetic fixture and
fault controls are development-only. Root's native captures use the app's own
hidden, unfocused WebView and CapturePreview, not desktop capture or injected
input. The [frozen harness contract](M08_AUTHOR_NATIVE_HARNESS_CONTRACT_2026-10-23.md)
defines the exact closed setup, before/after-apply gates and journey assertions.

Eight actual native cohorts stopped at recorded failures. Their accumulated
checks and 49 images are partial observations, separate from the ninth
cohort's first complete 17-image fresh/restart pass. None of those eight
stopped cohorts reached its restart process. The sixth reached 75 checks and
eight images: real typed Give saved child head 3,
removed the player's potion and retained the child receipt's original scope.
Repeated Give then produced actual native Inventory rejection, but the
subsequent phase-only durable status erased its displayed cause. A focused
controller correction passes 21 synthetic cases. The seventh captured the
accepted r3 receipt, honest failed-turn cause display and visible old-A
knowledge, then hit the app-owned watchdog before writing its report. Its
fixture omitted a refresh before Wait and never entered the intended gate.
The eighth reached 112 checks and 12 images: cancellation, late cancellation
and known-ID terminal-response loss with explicit status recovery passed.
Whole-acknowledgement-loss lookup then failed when transient loading cleared
its in-memory input. The correction passes 100 synthetic controller checks;
the ninth actually passed exact lookup, subsequent cases and saved-child
restart. Two additional loading-boundary regressions are now being frozen;
the owner requires their fix and another native confirmation before PR-ready
status. The first full pass is preserved rather than attributed to later code.

Earlier separate synthetic actual-Main tests passed 18 cases; actual-controller inert
React recovery-panel rendering passes six cases. The full frontend verifier
passes at `dfbe11c`. These results close their named controller/render defects
but are **not** evidence of native IPC or WebView execution of the fixes.
The coordinator's [PR #135 evidence comment](https://github.com/OptimumAF/LocalLore/pull/135#issuecomment-6379952552)
records the same boundary. Accepted prerequisite PR #133 has its separate
[source-bound qualification](M08_V2_PREREQUISITE_QUALIFICATION_2026-10-23.md).
Typed Domain2 fixture support was subsequently accepted in PR #137 at main
`cfbe84ec4c78a0537a03b7a88c87a14c1e026717`; the sixth native cohort includes it.

## Preserved stopped native cohorts

All paths below are relative to the task-owned, gitignored
`<evidence-root>/author-integration-artifacts`. Each cohort has bounded build
and app stdout/stderr/process records, fixed synthetic SQLite and an
`initial/report.json`. Source associations in this table were explicitly
confirmed by Root, who committed each correction before launching it and
recorded the source in the outer tool handoff. **The first five failed
launchers stopped before writing summary.json/source/binary hash manifests.**
The sixth launcher writes source-manifest.json before its build; it binds
clean `42cb0069ade357c52321db2d084ad1a5529f6c68`, Node 24.22.1 and the input
file hashes, including inference.rs. It still stopped before its final
summary/binary manifest. The seventh also has a clean pre-build manifest,
but no initial report or final summary. The eighth again has both a clean
pre-build manifest and failed initial report. No later executable is
attributed to a stopped run.

| Outer log / cohort suffix | Root-recorded source | Checks / images | Actual stop and disposition |
| --- | --- | --- | --- |
| `author-native-first.log` / `5cdadd04-84f0-4fa8-a239-10d50c65225e` | `da8d150f03328b98f0b6a35e0d0d542e0c51f159` | 2 / 0 | `AuthorDeadline:native-granted-author-context`. Author UI could not acquire native context. Root corrected/tracked generated author command permission files and added bounded context-error evidence in `79c93f1`. The empty error buffer in this first report does not independently prove the permission diagnosis. |
| `author-native-permissions-corrected.log` / `2b050725-6716-45a1-a10d-7183fef699b8` | `79c93f128393bc0a3f8b269b57d1369f0a22754f` | 18 / 2 | Duplicate-key rejection probe expected `InvalidAuthorInput`, while the actual Core parser category was `Malformed`. This was a fixture error, not acceptance of duplicate keys. `7d99fde` corrected only that category and repaired layout observed in the generated form images. |
| `author-native-layout-corrected.log` / `45fb021d-1284-42fe-b910-4a97f6e8c4ed` | `7d99fdedf3f2804f7bc331805b18175f7795dd72` | 30 / 3 | Concurrent archive probe omitted the native command's required session and expected revision. It could not establish ArchiveBusy contention. `5734a08` supplied the real fixed session/scope/head and focused captures on the relevant visible preview/error/pending/outcome sections. |
| `author-native-valid-contention.log` / `d416707c-af39-4256-8a15-bb1d0f7e2b30` | `5734a08535b5abe76ae89e4f56baed5dbed4a904` | 55 / 7 | `actual-knowledge-query-returned`: the journey read immediately after a lens change before the visible query control was ready. `13e92ed` waits for actual snapshot and readBusy=false, matching the UI's readiness, and improves scoped header legibility. |
| `author-native-query-readiness.log` / `5071afe9-f77e-4e07-8a2a-683936a847f4` | `13e92edfdf717727edbcbc4a0d8c5f1e4f403b13` | 71 / 8 | `AuthorDeadline:actual-V2-gift-root-refresh`, with one native `Version` error. The typed fixture inference route still requested legacy character context on Domain2. Shared typed-context support is a separate prerequisite; neither the legacy refusal nor the test's expected saved revision was weakened. |
| `author-native-typed-v2-corrected.log` / `de295ff7-302f-46ac-bd3d-03e1ff6c8914` | `42cb0069ade357c52321db2d084ad1a5529f6c68` (clean, pre-build manifest) | 75 / 8 | `repeated-gift-is-rejected-by-actual-Rust-rules`: actual typed Give saved r3 and removed the player's potion. Repeated Give emitted native Inventory; durable turn_status deliberately retained only failed phase/error=null and the UI lost the observed cause. `6786d94` preserves original-operation presentation evidence separately, without inventing a durable cause. Full native rerun remains pending. |
| `author-native-rejection-corrected.log` / `95eb81b7-5075-4f18-9dc6-2688d9d1fb6e` | `48fba074567d9b7a734abdaad09ab02187c9f974` (clean, pre-build manifest) | No terminal check count / 9 | App-owned 180-second watchdog: `D02_NATIVE_HARNESS TIMEOUT`, exit 2. The fixture immediately changed action to Wait, resetting thin reads, then waited unboundedly for a gate after send returned SessionRequired; no actual prepare reached it. `e0ebdaf` waits for refreshV2 and bounds gate readiness to 25 seconds. Existing native cancellation assertions remain unchanged. |
| `author-native-stale-disposal-corrected.log` / `22780deb-ba64-4b19-b7b3-603d88187e6c` | `e0ebdafcecfdd3427bbd284ed3d7b12ad877e852` (clean, pre-build manifest) | 112 / 12 | `same-window-exact-lookup-recovers-lost-whole-ack-without-apply`: transient null context during actual session resume cleared AuthorController's input, so lookup was Unavailable. Global unknown stayed honest. `1f4ab5f` preserves only the native root identity across null/loading, with availability false and no actions; actual foreign/malformed root or dispose clears it. `bd18d76` separately fixes the unknown-ack button's inline overlap. |

Each cohort directory is prefixed `author-native-`. The first six first and second build
process exited 0, then its initial app process (`run-3`) exited 1 with
`timedOut=false`, `truncated=false` and no spawn error. The outer launcher then
reported `AuthorHarnessChildFailure:run-3`; it never started restart. The
native permissions build log separately records successful compilation in
12.81 seconds; it is not an app success result.
The seventh's two builds also exited 0; its app exited 2 with signal/error=null,
timedOut=false and truncated=false. The 180-second **app-owned** watchdog fired
before the launcher's 240-second stage deadline. It produced nine snapshot/
capture triples, no initial/report.json, no aggregate check count and no restart.
The eighth again exited 1 with signal/error=null, timedOut=false and
truncated=false; it wrote its failed initial report but did not start restart.

The fifth report's `failedCheck` is
`author-native-observer-actual-native-WebView2-image`: the harness retains its
most recently successful check until another assertion updates it. Its actual
failure is the subsequent Give deadline and native Version error, **not** a
failed observer image capture. The image exists and its capture metadata says
`native-webview2`.

All eight app stderr files contain one bounded Chromium shutdown diagnostic,
`Failed to unregister class Chrome_WidgetWin_0`, error 1412. The first four
report error buffers are empty; the fifth has exactly one native Version,
and the sixth exactly one native Inventory. The sixth reports phase=failed,
receipt=null and native status.error=null at expected_revision=3. Its failing
check names the actual repeated-Give assertion, unlike the fifth's retained
last-successful capture label. The eighth error buffer contains native
Inventory and two native Cancelled entries, with no invented lookup success.
Neither empty application buffers nor this known shutdown message is described
as zero-error native qualification. Raw bounded stderr remains local.

## Render observations and integrity

The eight stopped cohorts contain 0 + 2 + 3 + 7 + 8 + 8 + 9 + 12 = **49 actual
app-owned PNGs**, each paired with a
semantic JSON snapshot and `.capture.json` metadata. Every existing image's
capture metadata reports `native-webview2`. Root reports personally inspecting
**all 49** across those eight, plus **all 17** of the first full pass below:
**66 images across nine cohorts**. This report author additionally viewed the
fifth cohort's `author-native-preview.png` and `author-native-observer.png`
through local file inspection only; the other 64 images' visual review is
attributed solely to Root.
Early form/layout and capture-focus defects produced explicit source fixes;
earlier imperfect images were retained rather than replaced in place.

The viewed preview shows legible before/replacement/private reason, two
retained knowers, zero excluded suffix, a wrapped digest, the unchecked exact
preview-read checkbox and disabled confirmation. The viewed observer image
shows selected author-saved at r2, Character Mira and separately labeled
Gameplay actor player, player resources and the inherited event-only history.
The knowledge inspector is below that image's fold: its semantic query proves
Mira's observed A, but this particular PNG does not show A itself. A final
capture intended to demonstrate visible old-A knowledge must focus that
inspector; the existing screenshot is not credited with unseen content.

The fifth and sixth cohorts contain consent, exact preview, rejected, pending, cancelled,
saved, history and observer images. It contains no continued-turn receipt,
late-cancel, lost-ack, recovered, narrow, stale-context or restart image. The
existing eight capture labels must not stand in for those unexecuted assertions.
Root's sixth-cohort observer review still found A below the fold; the next
capture anchor targets the actual known_as_observed row. In the seventh,
Root inspected that corrected observer capture and reports the actual
AUTHOR_OBSERVED_A value is visible. Its ninth capture, author-native-receipt,
shows the accepted r3 receipt and preserved observed Inventory/Rule alongside
the native failed/error=null status and missing-durable-cause notice. These
partial captures are credited separately from the unfinished full journey.
The eighth adds turn-cancelled, late-cancel and unknown captures to those nine
labels. Root inspected all 12, including the unknown acknowledgement button's
inline overlap; its separate CSS fix is not yet credited with a native render.
There is still no completed recovered/narrow/stale/restart capture sequence.
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
| `de295ff7-302f-46ac-bd3d-03e1ff6c8914` | `19823bb368fd0daa1f2f32a79af23529fb1e7fa15dc8bfd23bb0f29fe0b30279` | 25 / `a86d4ca43989b8693725e78934cd332e51134710a81982ad0d981ef4f4cddfa0` |
| `95eb81b7-5075-4f18-9dc6-2688d9d1fb6e` | Unwritten after app watchdog; no report hash | 27 / `864466f46daefa582e1cfd9dcf3847ee0e34ba126f2482af1210596852b92ef0` |
| `22780deb-ba64-4b19-b7b3-603d88187e6c` | `c452c2e30f5a222ce535a69963f9a09e2873da32d42c625e04196874e48b276f` | 37 / `eb4c30a051d6ed1ca6513d6a387c7752108af4d6022e84fb1000b4232ffd9318` |

The sixth pre-build source-manifest.json is 1,443 bytes, SHA-256
`73eccd4743ef8ccd0f43c64887a7cf4b0f6123c9b10403dd2cc5feeec981e3da`.
It is separate from the initial-directory artifact digest above and still
labels qualification pending.
The seventh's 1,443-byte pre-build source manifest has SHA-256
`5e0bcffddebaf60984612136545f157a1bb3380e2f581d2fbc7f3fbe5e1947bb`.
The eighth's 1,443-byte pre-build source manifest has SHA-256
`3e3694222c8d5f755c233944108d2af638e314b1aab0bc378099f3a35682c382`.

Each artifact manifest was computed read-only in memory: select all `.json`
and `.png` files under that cohort's initial directory, sort filenames with
ordinal comparison, form UTF-8 LF-terminated lines
`initial/filename|lowercase-file-sha256|bytes`, then SHA-256 the joined bytes.
This covers the report plus all image/snapshot/metadata triples without
publishing raw synthetic private previews. No saved artifact was modified.

## Actual-Main and headless recovery fixes

These are separate from the native cohorts above; the latest controller
correction has not completed its native rerun. Actual-Main checks import the real
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
- Following the sixth native failure, a new V2 scheduling oracle initially
  observed SessionRequired because its fixture omitted the actual thin
  refresh. The accessor-only fixture correction then exposed **20 passed /
  1 failed**, with displayed `failed` instead of the original observed
  Inventory. `6786d94` passes **21 / 21** and the full frontend verifier.
  The native assertion now requires failed phase, unchanged native error=null,
  original observed Inventory/Rule, bounded native error-buffer evidence and
  an explicit missing-durable-cause notice. This preserves the native status
  contract and rejection oracle rather than fabricating a persisted cause.
- Separate frozen actual-Main stale-prepare disposal cases exposed **18 passed /
  2 failed** for player-lens and Play-view changes. `e0ebdaf` passes **20 / 20**
  plus the full frontend verifier. It waits for a positive exact session/token
  native discard acknowledgement before clearing only the same active retired
  prepare. It does not resolve unknown work or a commit. This synthetic result
  is not a native stale-disposal pass until the rerun reaches that assertion.
- After the eighth native stop, frozen null-to-same-root loading-gap regression
  `f59d7be` actually failed the input-preservation assertion. Its checker
  terminated at that assertion, so no completed baseline total is inferred.
  `1f4ab5f` passes **100 synthetic decoder/controller checks** plus the full
  frontend verifier. It remembers only native root identity through temporary
  context absence, keeps author availability false/no actions, and clears on
  actual root replacement, malformed root or disposal. Recovery stays
  memory-only and explicit; this is not restart recovery or automatic apply.

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
| `author-native-typed-v2-corrected.log` | `4b582909a123725eebfedda45ddd4cf067b5f57a3a6cb4fe5d98674517332c76` |
| `author-native-rejection-corrected.log` | `6df6b01134d801933230a20dde365bece72501657a3a3ea231c5ced3bc08576a` |
| `author-native-stale-disposal-corrected.log` | `8ac6c390dfdfbb5721d10643a1467bdd427c4fb47b3e054d840ccffb83189518` |
| `author-native-loading-gap-corrected.log` | `c02b7388cc732895ac052c32eaadc6be6d2a51a7a30c241dc4a357acc7c34b15` |
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
| `v2-native-error-retention-original-red.log` | `ec7ed6b02ae559e82284441d18412d5e7dd3a422d3be307a836bc829d74cf752` |
| `v2-native-error-retention-fixture-corrected-red.log` | `2198b5c6ae4004b8521b30a8c88b3ccbf840e6ce2bc20141a5cb7395ac65c301` |
| `v2-native-error-retention-first-green.log` | `6cc7d1ef6d69ab293b6de56fdf55b2d4b0db935b2af618f8f9161b6883c88b8a` |
| `author-frontend-native-error-corrected.log` | `188d97670dfb13560c8c0c7f562df4b7ec0418307360f0d1be82e093d53fc4ef` |
| `author-stale-disposal-original-red.log` | `819ecb18af7723b1208cd3c746e7d1d05e8dc31c2e6c65227091e2792d6d29fb` |
| `author-stale-disposal-first-green.log` | `3845b209de25e85e57a83a95c07576e90286b2b92fe3441b823136a0276d8c51` |
| `author-frontend-stale-disposal-corrected.log` | `3bcf6b4b3d5585e9e78009d171a755ff4a02609ffdb7f436030ff79f95d58630` |
| `author-loading-gap-original-red.log` | `02c082b1f8b3b546d8232a1c30529dcaa5d3630036e136e005efcfd801af318e` |
| `author-loading-gap-first-green.log` | `4c86bfdadfaf90a058d79d7661384dee85b046bc06bda9d82dbc4e40aa24aaaa` |
| `author-frontend-loading-gap-corrected.log` | `9d9620a00799d5029d890c61b9c50414af5afd1f471315a5bc02d6f798eb00ac` |

## First complete actual native and restart pass

The ninth cohort, `author-native-a690f157-6bcc-43b8-aa64-cc4b3c54858f`, passed
at clean source **bd18d76b781e981098814c8a718e180e90e7afc9**. Both builds and
both actual app processes exited 0, without process timeout, spawn error or
log truncation. The pre-build manifest binds the source; summary.json binds
the actual executable, bundle, inputs and all captured files. This is native
IPC and actual WebView2 rendering, with an actual second-process restart;
it is not a headless render or a mock/native equivalence claim.

| First complete cohort metric | Actual result |
| --- | --- |
| Distinct assertion names | 123; not the sum of overlapping raw checks |
| Raw stage checks | Initial 133; restart 18 |
| App-owned captures | Initial 15; restart 2; all native-webview2 |
| Artifact files in summary | 53: 17 semantic/image/metadata triples plus two reports |
| Verified artifact bytes | 1,850,025; every summary file hash/length independently matched read-only |
| Initial error buffer | Native Inventory, Cancelled, Cancelled, exactly as deliberately exercised |
| Restart error buffer | Empty |
| Native stderr | One bounded Chromium shutdown error 1412 per process; not zero-error qualification |
| Model / author restart recovery | realModelGeneration=false; authorRestartRecovery=false |

The actual journeys exercise separate author and Lab acknowledgements, exact
Core preview digest, second consent, strict malformed/false-consent/hash
refusals, form-edit revocation, pending shared-broker contention, preapply
cancellation and unchanged parent/no cancelled or stale child. Successful
correction creates the actual child author interval with no character
observation; the player marker contains only constant kind and revision.
Actual Query2 verifies inherited original scope, player private-history
exclusion, omniscient B, Mira's observed A and Sable isolation; inspection
privilege does not mutate knowledge. Real typed Give saves r3; rejected
repeat preserves its receipt, head and inventory while distinguishing
observed rejection from missing durable cause. Actual V2 cancellation,
postcommit late cancellation, known-ID status recovery, whole-ack loss with
explicit exact lookup, changed-input mismatch and stale-preview disposal
all pass through the same controllers/native ports, not a competing writer.

The restart process reopens the actual saved child at r3 with the potion gone,
retains the neutral author boundary and player-filtered history, starts with
empty private author input/capability/consents and never auto-prepares,
looks up or applies. It demonstrates **saved-timeline read/resume**, not
author-operation recovery after restart.

Root inspected all 17 images and reports no remaining visible layout defect:
the acknowledgement label/button no longer overlap, Mira's observed A is
visible, the narrow view wraps, and reopened r3/inventory and empty author
request are visible. The snapshot userAgent reports Chrome/155.0.0.0 and
Edg/155.0.0.0; this remains a major-only browser-reported value, not the full
loaded runtime version. The report author has not independently viewed these
17 pixels and attributes their visual assessment to Root.

| First complete cohort artifact | Bytes / SHA-256 |
| --- | --- |
| source-manifest.json | 1,443 / `9fe056eb3cd1ac5eefe2b7ca63998870395edeb4f20e86bc09f3571e003c61f0` |
| summary.json | 31,412 / `919d1f5edd8baab4c0f72b3e78890ee0727816653626b572f983804b0fd26fad` |
| initial/report.json | 8,697 / `b66f46fbb52bc47065a765b490f4bb8a09aa825128c2241eeafb91821e3f5024` |
| restart/report.json | 1,238 / `402641e8cb8cb7cb6c05876585c5eebf52024fbf778b9e685e638aeef53bd22a` |
| Aggregate of all 53 relative artifact rows | `93cb98558a804ca4a97d539352f8e9f20642985b78b16cbc80da208eac314a7f` |
| Dev-harness executable hash recorded by summary | `f41ce6e0add1b9b55dd112655301eb2aaa902ab7e5065603ca98816c71731eae` |
| dist/app.js hash recorded by summary | `4f564f27152d890584792ed8132f0047b73640e44df588f5cd7936670ad8f8cf` |

The aggregate uses the same ordinal UTF-8 LF row format described above,
this time with each complete initial/restart relative path. No later binary
is substituted for this recorded harness executable. Commands and environment
are the reproduction block above; the actual outer log is
author-native-loading-gap-corrected.log (539 bytes, hash in the log table).

## Pending final-candidate appendix

This section is deliberately pending until Root's next terminal results.
The author continues evidence work; it is not a completed acceptance record.

| Required final evidence | Status at this report's current source |
| --- | --- |
| Shared typed Domain2 fixture continuation prerequisite | PR #137 accepted; actual sixth-cohort Give saved r3. Complete UI qualification remains pending. |
| Exact integrated source, clean/dirty state and native binary/dist hashes | First full-pass bd18d76 hashes above; final candidate pending two loading-boundary regressions. |
| Complete fresh native journey | First full pass 123 distinct assertions; repeat after final loading fix pending. |
| Second actual process: saved-child Domain2 read/resume | First actual process restart passed at bd18d76; repeat final candidate pending. |
| All 15 fresh + 2 restart semantic/capture pairs | All 17 passed at bd18d76; not yet final candidate's images. |
| Final expected rejection/cancel errors and bounded native stderr | First full pass has Inventory+Cancelled twice / restart empty; both stderr shutdown lines retained. Final candidate pending. |
| Root inspection of every final image and visible-state corrections | All first-full-pass 17 inspected, 66 across nine cohorts; final-candidate images pending. |
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
