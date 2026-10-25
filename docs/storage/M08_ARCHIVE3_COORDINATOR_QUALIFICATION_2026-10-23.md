# Archive3 coordinator qualification — 2026-10-23

This is a partial qualification record for #12 M08.03/.04/.06 and #30
D08.01/.02/.05/.07. Archive3 remains unmerged at this checkpoint. Shared Store
tests, the scripted Host transfer and the explicit combined-budget case have
passed. Desktop synthetic consumer and acknowledgement failures were retained
and corrected. Subsequent native broker/authorization tests, integrated frontend
checks, the original four-process transfer cohort and the corrected six-process
app-owned IPC/WebView continuation cohort have passed at their exact sources
below. Native unit continuation also passed. The first app cohort's missing
UI continuation and two visual findings are addressed by the later immutable
cohort, not relabeled as original success. Final serialized compatibility and
Android/runtime/platform gates remain pending.
No milestone acceptance, device support,
release approval or human review is inferred.

Root performed the executions reported here. The documentation agent read
source and completed logs, calculated hashes and checked its isolated Git
diff; it ran no build, test, formatter, provider, application or device.
Raw logs and synthetic databases stay local. Basenames and SHA256 identify
them below without publishing private absolute paths.

## Source and historical evidence

- Executed shared source: `9884a1727b17fb318eb79aa0dc301c2f6fe22684`
  on `qual/m08-archive3`, reconciled with accepted main `c6d0088`.
- Documentation checkpoint base: `8df48905cc12b2816234f684883bebb241a1bd0f`.
  Its only difference from `9884a17` is the two new consumer test files. Root's
  subsequent Host transfer and first desktop consumer execution use this exact
  clean source, as distinguished below.
- Shared implementation: `f0f7c5fd61ddad206902a5f6191b7a7194f17b20`;
  original source-only handoff: `0c640c50238c72ad3b5597ea18277fa34a1ec25c`.
  Reconciliation retained accepted main changes; do not replace main with the
  old producer tree. This report supplements the dated
  [source handoff](M08_ARCHIVE3_SOURCE_IMPLEMENTATION_2026-10-23.md) and
  [frozen oracles](M08_ARCHIVE3_FROZEN_ORACLES_2026-10-23.md), preserving their
  original source-only status rather than rewriting it as execution evidence.
- Original roundtrip test freeze `b85b917` and imported `ddc51a5` precede
  implementation. The later historical-asset fixture correction is imported
  as `b749479`. The original hostile file's frozen hash remains unchanged.
- Combined-budget test: `a64e3be`, formatted in `900a041`; actual Host Play2.5
  transfer test: `d115e54`, accessor/serialized-preview fixture correction
  `a8c7eeb`, formatted in `cdd6626`; pressure source: `0e2b7fc`, registered
  and formatted in `9884a17`. These source preparations are not executions.
- Consumer correction `f240579f701134fa4bc8e3f9718c703339d30287` changes only
  the allocated TS/Kotlin preview decoders, record labels and the old future
  version-negative fixture. Frozen acknowledgement tests `32b27f76e94767c91db5381398378779b062ef4f`
  precede the strict-string correction in `230b4baec3358f4d466fa2231ab8a0368a36bf1c`.
  Source formatting and frontend-check registration in the latter are not
  additional test executions.

Actual executed-file SHA256, also read at the documentation base:

| Path relative to `crates/locallore-storage` | SHA256 |
| --- | --- |
| `src/playable_archive.rs` | `355b57e88a5d3772a79f674a052f6b3750674591c0e68cc4731b764fcdcce363` |
| `src/turns.rs` | `a4c8f52a2a8dc7b5ea21f09808a689c7b2fa8fa6e2e0ee82d9603776214dea20` |
| `src/author_correction.rs` | `305500d839ef3e9f3fc264fe81b5e4982f84f5b997048c4f8bc8dc8c1d6e959b` |
| `tests/m08_archive3.rs` | `e43d5b96c8555ac4b34c39063060b8ad2028605bf5bb5a01056579e0bdefdf10` |
| `tests/m08_archive3_hostile.rs` | `643b16a93c406c37f88407e3a1f7f0cd9dfdb0b7c3f02b8fcb3d95c3be6fea67` |
| `src/archive3_pressure_tests.rs` | `8dcdb8a86717112198f70be526d4e86b9b4f04eea717e401c181c1886efea137` |

## Retained first failures

The original coordinator runs compiled but returned **0 passed / 7 failed**
and **0 passed / 6 failed**. Six roundtrip cases and all six hostile groups
stopped while constructing a genuine mixed fixture because preimplementation
export returned `Unsupported`. Those setup failures do not demonstrate that
each hostile mutation reached its semantic validator.

The seventh roundtrip failure was an incorrect fixture expectation:
`parent-retention-v1.json` is immutable archive1, not archive2. Its pinned
bytes/hash were already correct and were not replaced. The subsequent narrow
correction expects1, retains the byte/hash assertions and adds a real public
Store retirement fixture proving version2 selection. The hostile test source
was frozen after that metadata correction; its original actual RED still
failed at the mixed fixture setup. Neither failure is hidden or called a
successful negative test.

| Local log | Bytes | SHA256 | Actual result |
| --- | ---: | --- | --- |
| `archive3-original-red.log` | 4173 | `7bc3d982248dee1fb8f0b91377b092206ec9e11cd228b36f2557761c765bc9c9` | Compile1.38s; 0/7, tests0.53s |
| `archive3-hostile-original-red.log` | 3431 | `27ee11855f157491883e28ea8a406e7c19ec5a1b94998e2a826ba78576fdf51e` | Build0.21s; 0/6, tests0.33s |

## Completed shared checks

Root ran locked, offline, one-job Rust tests on Windows using the serialized
shared target directory. The log reports the unoptimized test profile. Root
confirms the reused, already verified Rust/Cargo1.93.1 installation, with no
upgrade or fresh `--version` invocation in this phase. Its completed-test
environment was `CARGO_BUILD_JOBS=1`, `CARGO_PROFILE_DEV_DEBUG=0`,
`CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`, `LIBSQLITE3_FLAGS=''`,
`TEMP`/`TMP=<task-root>/memory-controls-temp`, and
`<shared-target>=<task-root>/memory-jobs-target`. Manifests and lockfiles were
unchanged. Existing host qualification identifies Windows11 Pro10.0.26300 x64,
i7-12700K and approximately64GiB RAM; no fresh OS/hardware query was made for
these checks. Commands below use local placeholders rather than private paths
and are run from the repository root.

```text
cargo test --locked --offline --jobs 1 --target-dir <shared-target> -p locallore-storage --test m08_archive3 --test m08_archive3_hostile -- --test-threads=1
cargo test --locked --offline --jobs 1 --target-dir <shared-target> -p locallore-storage --lib archive3_pressure_tests:: -- --nocapture --test-threads=1
```

| Local log | Bytes | SHA256 | Actual result at `9884a17` |
| --- | ---: | --- | --- |
| `archive3-corrected-original13-first.log` | 2067 | `867d090f97d38a53484f0aff81f4725786a77a3de96081ff427ba6d97b81c236` | Compile10.89s; roundtrip7 passed in1.91s; hostile6 passed in3.84s; no failures/ignores/filters |
| `archive3-pressure-first.log` | 10437 | `3cb6061e1ad533675da2d5de7d4ee6d0dcc0d9bc027a626f4172b607c349757e` | Compile3.99s; 3 passed,0 failed,0 ignored,26 filtered,16.08s |

These are two focused commands, not an unfiltered Store/workspace pass. The
13 tests cover mixed canonical roundtrip/recovery, original source identities,
private observation bindings, retirement, conflict/no overwrite, escaped
author fields, legacy byte continuity and the six frozen hostile groups.
Checksums do not authenticate an author's intent; strict replay and closed
record/lineage validation remain necessary.

The three pressure cases use actual accepted author+typed-play history and
the actual Store connection. Failure assertions compare complete logical
raw-table state, canonical fingerprints and source-story absence, including
nonempty derived-job state and `sqlite_sequence`, then check cold reopen.
This is logical rollback evidence, not bitwise SQLite-file identity.

- **Busy:** a separate connection holds `BEGIN IMMEDIATE`; import returns
  `ArchiveError::Busy`. After release, restoring the test connection's timeout
  and reopening, a freshly validated token imports successfully and preserves
  the destination's existing story.
- **Full:** measured target26 pages ×4096 bytes, freelist0, scoped quota106496
  bytes; incoming native canonical/index text872923 bytes, archive668749 bytes.
  Both import attempts return actual `ArchiveError::Full` at observed callback
  poll1. Exact failing SQL is not observed; this does not establish failure
  after author insertion. Only that connection's prior `max_page_count` is
  restored to relieve capacity, followed by exact retry/cold-state checks.
  No deletion, physical ENOSPC, power loss or global SQLite change is claimed.
- **Cancellation/panic:** the successful fixed mixed import exposes33 callback
  polls. All33 cancellation positions and all33 panicking positions execute:
  **66 targets**, including the final precommit poll33. Each returns the
  expected closed cancellation, leaves complete logical state unchanged across
  reopen and admits a fresh exact retry. The emitted panic messages are the
  intentionally caught callback cases; the final test result is passing.
  This is exhaustive for this observed fixture path, not every possible SQL
  schedule or an operating-system process-kill experiment.

## Completed scripted Host transfer

At exact clean `8df48905cc12b2816234f684883bebb241a1bd0f`, Root ran:

```text
cargo test --locked --offline --jobs 1 --target-dir <shared-target> -p locallore-workspace --test m08_archive3_play25 -- --test-threads=1
```

`archive3-host-play25-first.log`: 902 bytes, SHA256
`3d743e4bb0e76483e0ef7c459d653ec831ee740ebeb26c9f61323ea991d59ebe`.
Compile15.16s; **1 passed,0 failed,0 ignored,0 filtered**, tests0.42s. This
executes `durable_play25_discovery_archive3_roundtrip_preserves_observation_sources_and_zero_call_retry`.

Two scripted Structured roles prepare the actual Play2.5 discovery before
transfer. Actual Host/Store commit and Archive3 export→validate→import→cold
reopen preserve full canonical records, native bases, corrected per-event
player observation B, Mira's prior observation A and original ancestor scope.
Imported exact retries through free_text/prepare/commit/status/cancel return
the original committed reply with **zero provider factories/polls**; disabling
the provider still permits the exact retry. A changed original input yields
`RetryMismatch`, and cold source/destination state remains exact. This is
shared-port/durable scripted-provider evidence, not real inference, desktop
UI/WebView, JNI or Android transfer execution.

## Completed explicit combined-budget boundary

At clean `8df48905cc12b2816234f684883bebb241a1bd0f`, Root explicitly opted
into the otherwise ignored expensive test:

```text
cargo test --locked --offline --jobs 1 --target-dir <shared-target> -p locallore-storage --test m08_archive3_combined_budget actual_records_cross_only_combined_response_and_native_index_archive_budget -- --ignored --exact --nocapture --test-threads=1
```

`archive3-combined-budget-first.log`: 1169 bytes, SHA256
`fc6ab0e37d88de3363dfd50c2d566e5979e8298016bde5dbaf13282c8b517997`.
Compile0.92s; **1 passed,0 failed,0 ignored,0 filtered**, tests107.83s. The
test's ordinary default status remains ignored; this invocation actually ran it.

| Measured quantity | Last accepted below cap | Next accepted crossing |
| --- | ---: | ---: |
| Canonical response bytes | 12855480 | 12884019 |
| Native request-index bytes | 3913290 | 3921972 |
| Combined bytes, cap16777216 | 16768770 | 16805991 |
| Canonical records | 480 | 481 |
| Physical branches | 31 | 31 |

The below total is8446 bytes short of16MiB, not exact equality. Its actual
export is12867586 bytes. The next real accepted record adds28539 response and
8682 index bytes, crossing the combined cap by28775 bytes. The separately
assembled hostile envelope is12896126 bytes. All history was accepted through
actual Engine/Store APIs; read-only SQL measures the real native index rather
than fabricating canonical rows or a duplicate index generator.

The below source exports→validates→imports→cold-reopens exactly. Above-cap
export and validation of a separately assembled archive from those same actual
accepted records both return `TooLarge`; the destination remains unchanged.
Response-only16MiB, per-record/request/proposal, record/branch, projection, seed
and wire caps remain independently legal. This qualifies the demonstrated
combined accounting boundary, not exact equality, every boundary permutation,
physical storage exhaustion, or app/native transfer.

## Consumer packet: retained desktop failures and corrected synthetic gates

This subsection retains the earlier consumer-only source checkpoints. Native
advertisement, authorization and actual App exposure were still pending then;
the later source-bound native/app results below record their subsequent work.

Original producer `145086afe93f92cc8c2b4aef97e67d98ef37af38` is imported as
`8df48905cc12b2816234f684883bebb241a1bd0f`:

| New path | Frozen coverage | Status |
| --- | --- | --- |
| `apps/desktop/check-archive-v3.mjs` | 82 synthetic decoder/controller/headless-panel source cases | First70 passed /12 failed at `8df48905`; corrected82 passed |
| `apps/android/app/src/androidTest/java/org/locallore/app/ArchiveV3WireTest.kt` | 9 actual Android decoder/JSONObject instrumented test methods | UNCOMPILED / UNRUN |

Root ran Node24.22.1 with the existing D09 dependency junction from
`apps/desktop`, setting
`LOCALLORE_CHECK_OUTPUT_DIR=<artifacts>/archive3-consumer-frozen`:

```text
node check-archive-v3.mjs
```

Actual exit1: **70 passed /12 failed**, all82 frozen cases collected. Six
version3 preview positives fail `Wire` (import/export, omitted/nonempty/explicit
empty retirement). Three version1 unknown/private-field negatives fail because
the decoder does not throw. Version3 maximum-bound acceptance, imported
completion and controller/headless-panel positive cases also fail `Wire`.
Version3 negative cases passing under blanket rejection do not independently
qualify their intended field guards; they must rerun after version3 admission.
The corrected run does rerun all82 cases and passes them all, including the
previously blocked version3 positives and their field guards. Root's source
record binds this run to `f240579f701134fa4bc8e3f9718c703339d30287`.

| Local artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `archive3-consumer-first-red.log` | 5717 | `549aa050be655fba7366c15083e4b6266acabfc83d7a3769f36488d4b4efb201` |
| `archive-v3-07d8ed38-509e-4c94-b3e6-e1426ca788c8.json` | 7508 | `b03c8e88ccfbd8f26a4480bd6f6cee0677dbc0460a02128574dab00c68579798` |
| `archive3-consumer-first-corrected.log` | 4954 | `7ce17b0f1fb85406de6573a9224c15ba8af2e68089bec77b158d8eb44e6d9f2e` |

Root also executed the separately frozen29 acknowledgement cases with
`node check-archive-v3-ack.mjs`. The first actual result is **16 passed /13
failed**, exit1: array-valued statuses/phases/kinds were accepted through
coercion, and malformed imported/exported acknowledgements could incorrectly
resolve retained uncertainty and admit competing work. The narrow production
correction requires literal strings before closed-value membership tests.
The unchanged semantic cases then report **29 passed /0 failed**. Correct
native-shaped cancellation resolves only the original operation; invalid
acknowledgements retain its uncertainty. These are synthetic actual-decoder
and broker-retention checks, not native execution or an actual hostile IPC run.
Root binds the first failure to `32b27f76e94767c91db5381398378779b062ef4f`.
The29-pass run used the coordinator's working correction immediately before
commit `230b4ba`, not a clean committed `230b4ba` tree. Subsequent formatting
and commit produced exact clean `230b4baec3358f4d466fa2231ab8a0368a36bf1c`,
which is the source of the full frontend execution. Source chronology is
coordinator-attributed, not inferred from process timestamps or commit dates.

| Local log | Bytes | SHA256 | Actual result |
| --- | ---: | --- | --- |
| `archive3-ack-first-red.log` | 3827 | `a0965008fbd9e227c6e99142817958502355026810182f72290f9b8009015fd7` | 16 passed /13 failed |
| `archive3-ack-first-corrected.log` | 2802 | `b818526163d3fa75b1a14cee41d3e8c9e139fd6c8c8568f0a2b4668cdfba0f88` | 29 passed /0 failed |
| `archive3-full-frontend-first.log` | 19107 | `c203a3281da69721755364a56506adfedfc2acad206b7a22febd080261f289f5` | Full frontend gate PASS at `230b4ba` |

The full frontend result includes strict TypeScript, current request/schema
checks, the normal frontend build and exclusion of development journey/control
hooks. It runs the current frontend synthetic/controller/headless suites,
including both Archive3 checkers. Their counts overlap the focused runs and
are not added into a fictional aggregate. The Node logs do not contain elapsed
suite timings; none are invented. This frontend build is not a native binary
build, WebView render cohort or Android test execution.
Root invoked the already approved Node24.22.1 executable directly from
`apps/desktop`, with `verify-frontend.mjs` as its argument (locally represented
as `<node24-executable> verify-frontend.mjs`); no npm install/run was involved.

The desktop fixtures are synthetic transport shapes, not newly generated native
responses. Headless React checks are not native WebView execution. Consumer
production correction has synthetic evidence, but native supported-version
advertisement closure is not established here. Kotlin source correction is
not Android compilation or runtime evidence.
Android's host-JVM `JSONObject` stub cannot qualify this decoder: the tests
are deliberately in `androidTest`, using the actual platform implementation.
Instrumented compilation alone will not establish runtime behavior. No
Android device/emulator/ADB execution is authorized for this cohort.

The public archive2 constant and catalogs listing `[1,2]` are not a reliable
exposure fence: shared export/import can already produce/accept genuine3 on
this future stack. The initially executed app decoders rejected3; the corrected
TS decoder now has the synthetic evidence above. Root must still close the
native preview/completion DTOs, strict TS/Kotlin version dispatch, omitted
empty versus nonempty retirement fields, canonical-record count labels,
consent/token/recovery and supported-version advertisement before accepting
Domain2 app transfer. Counts include author records; calling all of them
gameplay turns would misdescribe the archive.

## Current remaining gates and next runnable work

The later native/app results below supersede the earlier source-only status
of the frozen broker/authorization/harness packets. This does not relabel any
earlier failed or unexecuted source as passing. Existing archive compatibility,
Full/checkpoint/interruption and broader Rust/Workspace/native qualification,
formatting and strict lint checks still need final source-bound disposition.
This reproduction command is pending here, not a reported result:

```text
cargo test --locked --offline --jobs 1 --target-dir <shared-target> -p locallore-storage --test playable_archive --test branch_retention_archive --test archive_interruption -- --test-threads=1
```

Root separately observed shared Cargo target contamination in another Core
source cohort. Future final checks will use source-owned target directories.
That observation is not evidence that these previously source-bound Archive3
executions used a wrong artifact, nor is it a new execution of them; retain
their exact sources/logs and record final target/source ownership explicitly.

From `apps/android`, compilation-only is
`./gradlew.bat --offline :app:compileDebugAndroidTestKotlin`. Preserve the first
actual fixture/compile/behavior failures before any narrow correction, and
record exact source and results for each rerun. The nine Android instrumented
methods remain uncompiled/unrun in this packet. Real OS-picker interaction,
Android instrumented runtime, desktop↔Android roundtrip, physical-phone
qualification and owner acceptance remain unavailable. The native cohort uses
fixed picker doubles, not automation of system dialogs or the desktop. D07
model/timing cohorts are separate evidence and are not relabeled here.

The corrected snapshot notice, visible knowledge-row capture and six-stage
actual-UI continuation/cold-reopen cohort now have the later evidence below.
Root's final serialized source-owned Rust/native/Android compatibility pipeline
is still running; no partial output is reported as its terminal result. Next
runnable work is completion and exact attribution of that pipeline, followed
by authorized platform checks. This is
qualified native transport evidence within the synthetic fixture, not Android
Domain2 opening support or whole M08/D08/publication readiness.

## Selected Domain2 panel action addendum — 2026-10-24

This subsection preserves the earlier source-preparation checkpoints. Its
pending assertions describe those sources; the later results below explicitly
record their execution and integration without changing this history.

Root adopted the independent frozen eleven-case checker `801adfc` as
`a5f45c7`, after preserving accepted main `beb1587` in merge `88fbab7`.
The first actual command, `<node24-executable> check-archive-v3-selection.mjs`
from `apps/desktop`, returned five passes and six failures. All six failures
stopped at missing JSX-captured button elements, including ordinary Play1.
They do not demonstrate six product defects. The project automatic JSX
configuration bypassed the checker's classic JSX capture function. The narrow
test-only `tsconfigRaw` correction was committed as `91ec2b0`; it preserves
all assertions and delegates element creation to actual React.

The corrected test fixture then measured **seven passes and four failures**:
both selected Domain2 positives found the actual disabled export button, and
retained real callbacks dispatched after selection or same-session head changes.
Ordinary Play1, denied/stale panel rendering, held-reply disposal and explicit
V3 consent/record labels passed. That behavioral run used the test-only working
patch immediately before `91ec2b0`, not a clean committed tree.

Root changed only the panel to select the coherent `play ?? playV2` snapshot
and recheck its captured context/session/scope/head against the current controller
before dispatch. The same eleven cases then passed with zero failures, using
the working correction immediately before formatting/commit `b080b73`.
The checker is now registered in the full frontend gate; a new full-gate result
is still pending at this addendum. Root has not yet exposed this panel in the
Domain2 App mount: actual native authorization and application-owned rendering
must be qualified separately.

| Local log | Bytes | SHA256 | Actual result |
| --- | ---: | --- | --- |
| `archive3-selection-first-red.log` | 2432 | `6338fca16bee8b1c36cd665f5b9729c3583d7e75295c2a3ae10e1163701b46db` | 5 pass / 6 fixture-capture failures |
| `archive3-selection-first-behavioral.log` | 2763 | `72a1278cf578dcbedd3d8b40c5d618ff7519f08b0e1612e3f8902fea15dee2a1` | 7 pass / 4 product behavioral failures |
| `archive3-selection-first-corrected.log` | 1451 | `102512fc642c8428ba9281bca9b922f6892bb939a1cfe8b1da936ca836ed8dee` | 11 pass / 0 failure |

These execute the actual React SSR component handlers and ArchiveController
against a synthetic gateway. They are not native IPC, DOM event dispatch,
WebView render evidence, an App-mount test or proof of the native private grant.
The four actual Store/Host authorization groups are independently frozen at
`ac71e22`, adopted as `3dff85a` in the new `archive_authorization_tests.rs`.
Their intended private helper is absent and the module unregistered; all four
remain uncompiled/unrun. No Android runtime or whole M08/D08 acceptance is added.

Subsequent source preparation: Root adopted all three fixed app-owned harness
files from `de00f2e` as `d85c13c`, after reading their complete source. They remain
unregistered/uncompiled/unrun; no image count or native success is inferred.
The orchestrator additionally refuses success if the source revision, listed
inputs, binary/frontend hashes or clean working-tree state change by the end
of the final app stage. This is source hardening, not measured qualification.

Root `73ce67a` subsequently registered the four authorization test groups and
factored the existing `inspection_snapshot(Full)` call into their private
helper. That preserves the old implementation and its Domain2 limitation,
so the first actual tests can measure the old authorization path. Query2
authorization is still unimplemented. All nine new native broker/authorization
groups remain uncompiled/unrun; Domain2 App exposure/catalog3 and the actual
hidden application-owned IPC/render/visual review gates remain pending.

## Native authorization, transport and integrated frontend — 2026-10-24

The five frozen broker groups (`ab43563c`, adopted `d1f65d3`, registered
`53928c9`) first ran at clean
`5262d3be8e4db007b13696fc79eba9e272b02bd7`. Actual result: **4 passed /1
failed**,93 filtered,1.19s after3m43s compilation. The failing catalog case
observed archive2 instead of3; the other four groups exercised real mixed
capture/publish/staging/cold reopen, stale-head refusal, committed lost-ack
recovery/conflict and preapply cancellation. The retained process record has
exit101 and that exact source, not an app/render execution.

The four authorization groups first ran at the same source: **2 passed /2
failed**,94 filtered,0.72s (build1.07s). Both failing Domain2 paths returned
`Version` through the old legacy `inspection_snapshot(Full)` authorization.
False native grants and unknown/closed/cross-scope sessions were rejected as
expected. Root's narrow correction uses the actual Host Query2 Omniscient
Profiles request, limit1, with exact session/scope/head and the existing native
grant; it does not materialize legacy Full or grant actor generation knowledge.

The corrected four authorization groups passed in0.89s, compile20.60s. Source
is coordinator commit `2a7c274a50d05d14e9953f1ae33d57409d6e11c2` plus its
module-order formatting working patch, later committed as
`9444a0bbad11be13a6795fbb6f174fc31b565b51`; do not label that execution a
clean `2a7c274` tree. Root advertised exact native catalog3/[1,2,3] at
`abaa67eb2a836e192e30db92bb2e1782e3d2d62a`; all five unchanged broker groups
then passed in1.15s, compile16.08s,93 filtered. Actual legacy archive1/2
selection remains separate from this native advertisement.

Root's integrated frontend command passed with the working integration patch
immediately before `1b14449b51dc9a98d7167f6eaa03781f297759c0`. It includes
82 consumer,29 acknowledgement and11 selected-panel cases, strict TypeScript,
normal frontend build, current schema checks and normal-hook exclusion. These
overlap prior focused cohorts; no aggregate of independent tests is invented.
The dev-harness native `--no-run` check subsequently compiled both the main
unit-test executable and `harness_contract` in22.43s. That compile is not a
test run, app launch, render or device result.

From the repository root, native group reproduction uses the owned target and
the already documented one-job/offline/debug0/incremental0 environment:

```text
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --jobs 1 --target-dir <archive3-native-target> --bin locallore-desktop-spike archive::archive_v3_tests:: -- --nocapture --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --jobs 1 --target-dir <archive3-native-target> --bin locallore-desktop-spike archive_commands::archive_authorization_tests:: -- --nocapture --test-threads=1
```

The integrated frontend command is the approved Node executable directly
running `verify-frontend.mjs` from `apps/desktop`, not npm installation.

| Local artifact | Bytes | SHA256 | Result |
| --- | ---: | --- | --- |
| `archive3-native-frozen-first.log` | 11115 | `4ecbe493cfd5d3ef301f9ba4a19e918a36bf0770d1a4fe5ae926330cc6757ad4` | 4 pass /1 catalog failure |
| `archive3-native-frozen-first-process.json` | 253 | `37936a74851f7cf66f4eb724c9975a0e6dfb92da56ea26745e3b01e3031c11c9` | Exact5262 source, exit101 |
| `archive3-authorization-first-red.log` | 1955 | `29a0e759b6588811eaad4a2f665825f9381ce2abcb1d94357e586776c2fe3628` | 2 pass /2 Version failures |
| `archive3-authorization-first-corrected.log` | 1540 | `cd4ffb3c72b9c2631377968a31e6ed875d5265f17dd4db1446f561af7ee4ec4f` | 4 pass /0 fail |
| `archive3-native-first-corrected.log` | 2630 | `35ea12aa0953ac0d9eb414ef250fac60dc21929e5be24851f7832480e1983e0f` | 5 pass /0 fail |
| `archive3-integrated-frontend-first.log` | 20558 | `c10ff273d48b3f1504aa088bfda2dfa158f53b58c440a7368eae12829987bded` | Full frontend PASS, working integration patch |
| `archive3-harness-native-first-compile.log` | 560 | `b559dc85b65f350eef407092c6a35adba568263604eb723e7edcf0625eda2126` | Compile-only PASS |

## First actual four-process app-owned transfer cohort

The first launcher attempt stopped at clean-source preflight, **before any app
launch**. Root attributes the dirty source to launch working-directory context
and an uncommitted generated fixture-command permission. The retained failure
is `archive3-app-first.log`,575 bytes, SHA256
`f434afbb80502ec657cee9c869cb4fde5c87b662256dd0f5ced733740373683b`.
It is a harness/source-preflight failure, not an app behavior failure. Root
committed the exact generated development permission and reran at clean
`fcbacd8b038d35302da283e3ea11cea3919ee742`.

The actual cohort is
`archive-v3-native-227bab1d-94e2-48a5-95f6-f38b6c22a671`. Root launched from
`apps/desktop` with trusted absolute local placeholders:

```text
LOCALLORE_D08_ARTIFACT_ROOT=<ignored-local-artifacts>
LOCALLORE_D08_TARGET_DIR=<archive3-native-target>
<node24-executable> archive-v3-harness.mjs
```

The launcher builds `build.mjs --harness`, then the existing native app with
`cargo build --manifest-path src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir <archive3-native-target> --jobs 1`.
Four actual app processes run sequentially in hidden, unfocused app-owned
windows, using fixed native picker doubles and real mounted controllers/IPC.
Source, destination and uncertain workspaces are separate; only destination is
reused for the real restarted process. All four exit0 without timeout or
output overflow. No desktop input/window activation/OS screenshot, real
system-picker automation, model generation or Android execution is involved.

| Stage | Recorded check entries | Distinct labels within stage | Native PNG captures | App ErrorBuffer |
| --- | ---: | ---: | ---: | ---: |
| `v3-source` | 45 | 41 | 5 | 0 |
| `v3-import` | 60 | 54 | 6 | 0 |
| `v3-restarted` | 44 | 42 | 5 | 0 |
| `v3-uncertain` | 44 | 39 | 4 | 0 |

The summary contains **193 recorded check entries /72 distinct label strings
across the cohort**, not193 independent tests. Repeated checks include fixed
oracle and snapshot validations. There are20 actual application-owned
WebView2 `CapturePreview` PNG files,1427457 PNG bytes; the recorded artifact
set totals1990538 bytes. These are native render captures, not headless React
or OS desktop screenshots. The documentation agent parsed the manifests but
did not execute the cohort or inspect images itself.

Actual assertions establish selected Domain2 private export, explicit review
and second consent, staged cancellation before target application followed by
fresh-preview success, committed import with lost acknowledgement and read-only
recovery, same-ID Conflict without overwrite, cold process resume/re-export,
foreign canonical-story preservation and empty owned staging directories.
All three published archive files and the unchanged input share SHA256
`64cc6e34b6d471eeffaf41939c91f2ed866cc572a240378aeb02b0bd4c18fe4e`.
Full canonical records, opaque native accepted-history basis equality and all
actor contexts/views agree across all four native fixture oracles. Their
canonical-record digest is
`817d49df34347750dd8bd0213bf1d6df8e8a676658ae410f192d5a48d6866d83`.
Query2 evidence keeps Mira's prior A, the player's current B and Sable unaware;
no private author reason appears in these actor queries. Inspection does not
grant generation knowledge.

The recorded environment is Node24.22.1/win32/x64,
`rustc 1.93.1 (01f6ddf75 2026-02-11)` and
`cargo 1.93.1 (083ac5135 2025-12-15)`. Start and terminal source are identical
and clean; the listed source inputs, native executable and frontend hashes
remain stable. Native executable SHA256 is
`5c1ed5c4412e8d7eac7b1182fd68a58b298b65fe8de0cdb9a95772fa01ac0eed`;
frontend SHA256 is
`88f0fa07f7cdeaf68f78ca44958a83a6f0d47640c2cb5be1afbb74321e2744db`.

**App ErrorBuffer0 does not mean zero native stderr.** Every exited app retains
one115-byte Chromium diagnostic: `Failed to unregister class Chrome_WidgetWin_0.
Error = 1412`. No log is cleared, ignored or relabeled empty. `executions.json`
pins each stdout/stderr hash and exit status. These teardown diagnostics remain
visible evidence rather than an inferred semantic failure or a blanket
zero-native-error claim.

| Local artifact, under the cohort unless specified | Bytes | SHA256 |
| --- | ---: | --- |
| `archive3-app-source-corrected-first.log` (outside cohort) | 235 | `7e9299d207f4230f49dbd4da97b2e3276e84e51e74161977306ca8561745e7f6` |
| `summary.json` | 35948 | `6049fe982a2ea28481355eade86776d9aadc358a6d56777e4568c93f93c31a96` |
| `source.json` | 4350 | `6382ea6cbcba3e10ce27cc133b8328dd961a2f492da36c6de7939f4c9af7ca5a` |
| `binary.json` | 239 | `f4b16112b6a1074b235051b32c9474ec3f617a4714c98e5dfb938b4ee29ff0bd` |
| `executions.json` | 2470 | `0c5a49953f5a330249cac1c25b01dba80ceb4da5a52cdfa319ce99983c744536` |

## Attributed visual review and remaining actual-UI gap

This subsection records the first four-process cohort and its original open
findings. The later six-process section records their correction on a different
source; this earlier cohort and its manifests are preserved unchanged.

The immutable cohort summary intentionally still says visual review pending.
Root subsequently inspected **all20 images** and wrote the separate
`archive3-app-first-visual-review.json`,4629 bytes, SHA256
`dc122d2921337a5ef43666c7f63e1384003c72e5a4b69a6cd06d6b7c3a6d18e7`.
It pins every image hash. Root reports readable layouts without observed
clipping, overlap or horizontal overflow at1280×900 and680×900; vertical
scrolling remains necessary. This is Root's inspection, not the doc agent's.

Two findings remain open: the export receipt incorrectly says the original
story is unchanged by later play, although the exported snapshot is the frozen
object; and the observer images show lens/scope/head while the knowledge values
are below their viewport. Semantic Query2 assertions passed, but those images
do not yet visibly demonstrate A/B isolation. Root will correct the notice and
capture/verify the actual visible knowledge rows in a new source-bound cohort.
The first cohort remains immutable; it is not overwritten as the corrected run.

No post-import continued turn is executed through the mounted UI in this first
cohort: all four final native oracles retain3 canonical records. Root's planned
six-stage continuation/cold-reopen journey is pending. The next native unit
check below covers the shared commit boundary, not that missing UI journey.

## Executed native post-transfer continuation prerequisite

Independent source `154b5b7b47386881ff6fa8dd7e3972c4730be093` is adopted as
`662041bb3f84071829eb428e35fe0866eff0c53d`; Root registers it at exact
`20c75c42c7e71ccfcd7d3bb76b1341e219b81484`. Root's actual test passes:
**1 passed,0 failed,0 ignored,98 filtered**,1.05s after13.51s compilation.
It executes two fixture loops: the corrected child and a live descendant with
a retained retired author parent. Actual native broker import is followed by
Host/Repository scripted Play2.5 Wait, canonical3→4 once, cold reopen and exact
retry with0 new provider factories/polls; changed same-key input is
`RetryMismatch`. Both loops total4 scripted Structured roles, not model calls.
Original history/observation provenance, Player B/Mira A/Sable unaware,
source/archive/foreign story and cold continued-export bytes are checked.

```text
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --jobs 1 --target-dir <archive3-native-target> --bin locallore-desktop-spike archive::archive_v3_tests::continuation_tests:: -- --nocapture --test-threads=1
```

`archive3-continuation-native-first.log`:1010 bytes, SHA256
`d1a25985495962317eb122e99eee99950fb019ee084623bbaa1d5a2897e685ea`.
This is an actual Rust native-broker/shared-port test, not WebView/JNI/Android,
post-import UI execution or model-quality evidence.

Documentation claim ownership is handed back after this packet under
[#12 claim6392496259](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6392496259)
and [#30 claim6392496411](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6392496411).
Root retains all implementation, final compatibility, native/Android consumer
acceptance and publication decisions. No whole milestone or readiness claim
is made by this documentation update.

## Six-stage continuation: retained capture failure and corrected cohort

The first six-stage attempt used clean
`63fff4b4e51ef035d6d84bc7eda5350e37ae2c5b` and local cohort
`archive-v3-native-16e068e5-1997-4841-82fb-c06aa901ede1`. Four app processes
completed successfully. The fifth, `v3-continued`, **actually committed the
typed Wait3→4** and passed the exact native Core full-record/basis/actor oracle
before its capture failed; the sixth process was not launched. There is no
successful final summary for this cohort.

Root diagnosed the fixed label `continued` as outside the existing native
checkpoint allowlist: native capture rejects it with `CheckpointInvalid`.
The retained fifth report records generic `ArchiveV3Failure` and the older
`failedCheck` value `continued-no-horizontal-overflow`; that last layout check
is already in its passing-check list. It must not be called an actual overflow
or commit failure. The report still has native revision/record count4,
unchanged foreign control, full native proof and an empty app ErrorBuffer.
The runner exits on that app's exit1. Failed run records remain immutable:

| Local artifact, relative to failed cohort unless specified | Bytes | SHA256 |
| --- | ---: | --- |
| `archive3-six-stage-first.log` (outside cohort) | 630 | `2e90abbe6aa3b4659f90071668b8adef8b7638da7223183d8d4847559192140b` |
| `source.json` | 4350 | `9495b039504a254f744a643f3e5baf5f8928978ffd742520d8c0444ecdf8d70b` |
| `binary.json` | 239 | `4a73abdf7fcacf507549ba9d3bf67dae65eed10a744f3d9748ccdf85dc9084c9` |
| `executions.json` | 2816 | `902dfa27f6673685823f6cac8adc67c053d20ea755656651e83d9e5f3201b714` |
| `v3-continued/report.json` | 1873 | `e69dd05d4b895dda8a16feb189973f7d5187acb7876fcab6276ec63cc8a3b368` |

The source-only correction at exact
`96bca63937d5c4f64fd3a563ca23a21c72820059` changes just five lines in
`ui/archive-v3-journeys.ts`: reuse the existing `play-accepted` capture label,
use that label to target the actual native receipt section, and set
`failedCheck` immediately before invoking native capture. It does not enlarge
the native checkpoint API, alter acceptance assertions or change the committed
Wait. Root reran from a new owned artifact root using the same launcher command
and trusted environment placeholders documented above.

Actual corrected cohort:
`archive-v3-native-b229aaa2-e4ea-478c-96cc-62cf1932e992`, source
`96bca63937d5c4f64fd3a563ca23a21c72820059`. All **six app processes /eight
total child processes**, including frontend/native builds, exit0 with no
timeout or output overflow. Source starts/ends clean and identical; listed
source, binary and frontend hashes remain stable. No script-suite elapsed
times are present in these manifests, so none are invented.

| Stage | Final native head | Recorded check entries | Distinct labels within stage | Native PNGs | App ErrorBuffer |
| --- | ---: | ---: | ---: | ---: | ---: |
| `v3-source` | 3 | 48 | 44 | 5 | 0 |
| `v3-import` | 3 | 63 | 57 | 6 | 0 |
| `v3-restarted` | 3 | 47 | 45 | 5 | 0 |
| `v3-uncertain` | 3 | 47 | 42 | 4 | 0 |
| `v3-continued` | 4 | 54 | 48 | 5 | 0 |
| `v3-continued-restarted` | 4 | 47 | 45 | 5 | 0 |

These are **306 recorded check entries /83 distinct label strings** across
the cohort, not306 independent tests. There are30 actual app-owned WebView2
CapturePreview PNGs,2011434 PNG bytes; the recorded artifact set totals2836342
bytes. All six stderr logs retain one115-byte Chromium
`Chrome_WidgetWin_0` unregister1412 teardown diagnostic each. The empty six
app ErrorBuffers are separate evidence, not a zero-native-stderr claim.
`executions.json` preserves each exit and bounded stdout/stderr hash.

The continued stage uses the actual V2 composer/controller action and native
IPC to submit **one typed `Wait { ticks:1 }` with the synthetic fixture
provider**, not a free-text real model or scripted Play2.5 generation. Actual
receipt/native history move3→4 exactly once. The read-only fixed oracle derives
that exact request/receipt through Core from the original child3, then compares
complete canonical records, projection, opaque accepted-history basis and all
actor contexts/views. Only the two closed continued stages permit this exact
extra record; the restarted-continued stage requires4. The actual controller's
exact-retry action leaves that proof/head unchanged. This UI assertion proves
no duplicate accepted Wait; it does **not** measure zero provider calls. The
separate native scripted Play2.5 test above owns the cold0-call retry evidence.

Three original3-record publications still share the old captured/input hash
`64cc6e34b6d471eeffaf41939c91f2ed866cc572a240378aeb02b0bd4c18fe4e`.
The continued4-record export and its second cold-process re-export share a new,
different SHA256
`aa5dcacf8fed47f751da3c5408fa9eccc60452c05cb22a665fd040f1a88cc5e1`.
The continued and cold-reopened native record digest is
`c408e02c06b2f878cbc5b6af6e759d0019374376777fd4f77f96ad51d39240a3`.
The original input is unchanged, the foreign story's canonical proof remains
identical, all owned staging directories are empty, and no new or overwritten
source history is inferred from matching checksums alone: full replay/basis
comparison remains native authority.

Corrected executable SHA256:
`53f47e7fdaa9d8da964b7afeb5058b6b201065ffd485115213111d2c47524085`;
frontend SHA256:
`f7ae89699311e1701498dd48be6be70ed4b480bd384d766ccfdddef9b20367cc`.
Environment remains recorded Node24.22.1/win32/x64 and Rust/Cargo1.93.1 with
the exact version strings in the first cohort section. All stages keep
`realModelGeneration:false`; only the continued stage marks synthetic fixture
generation activity. No model assets, Android execution, OS-picker automation,
desktop capture/input or general-purpose debug capability is involved.

| Local artifact, relative to corrected cohort unless specified | Bytes | SHA256 |
| --- | ---: | --- |
| `archive3-six-stage-label-corrected.log` (outside cohort) | 235 | `114007e123931d95ed8231963b85458ae67b82851279a85b041d051118831410` |
| `summary.json` | 52755 | `bd78f775b1c2ee77943cce8163798165a5487c5a06b4a74464d3d0d398a4977e` |
| `source.json` | 4350 | `6d0dddfd98337c07242c60be25703bf65040642fefee65f972040c21c89fd544` |
| `binary.json` | 239 | `807b52ac129f49b09588f05fab2d3471a1f2678e8bee25becbb5ee1f9a10ef16` |
| `executions.json` | 3169 | `4277178910af7b49ca5a1b69099303c769188043db911df8c7c1f674b1c27e06` |

## Later attributed visual review and current limit

Root inspected **all30 corrected images via `view_image`**, recorded separately
in `archive3-six-stage-visual-review.json`,6972 bytes, SHA256
`7f1f6e4536806f0750e963d3d603ccf8e44750041e454943de907f8c9f26c3e2`.
The documentation agent read that review/manifest, not the rendered pixels.
The corrected export receipts visibly describe a frozen file while the story
can continue. All six observer images visibly show Mira's prior A at selected
revision3 or4, without current B or the private reason in that inspector.
Separate actual rendered-DOM checks cover Mira, Sable and Player knowledge
isolation. The continued receipt visibly shows3→4 and story time100→101;
the new preview shows4 records and the cold reopened history/resources agree.
Root reports readable1280×900 and680×900 layouts without observed clipping,
overlap or horizontal overflow; long panels require vertical scrolling.

This later source-bound evidence addresses the two visual findings and actual
UI continuation gap from the original20-image cohort. It does not overwrite
that cohort or the failed six-stage attempt. Native full-story transport and
synthetic actual-UI continuation are evidenced; real-model quality, Android
Domain2 opening/bidirectional parity, physical-device behavior, final broad
compatibility, owner acceptance and publication readiness remain outside this
packet. Root's final serialized compatibility pipeline remains pending until
its own terminal results and source ownership are recorded.

Sole-document work is handed back under
[#12 claim6392608340](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6392608340)
and [#30 claim6392608484](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6392608484).
No milestone checkboxes or other source/test paths are changed.
