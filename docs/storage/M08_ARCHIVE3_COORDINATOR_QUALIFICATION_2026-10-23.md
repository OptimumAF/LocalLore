# Archive3 coordinator qualification — 2026-10-23

This is a partial qualification record for #12 M08.03/.04/.06 and #30
D08.01/.02/.07. Archive3 remains unmerged at this checkpoint. Shared Store
tests, the scripted Host transfer and the explicit combined-budget case have
passed. Desktop synthetic consumer and acknowledgement failures were retained
and corrected; the frontend gate passed at `230b4ba`. Actual native transfer,
Android runtime and the remaining compatibility gates below are pending.
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

## Pending gates and next runnable work

Items below remain pending at this checkpoint; commands are reproduction
instructions, not results. Use Root's serialized target/TEMP environment.

```text
cargo test --locked --offline --jobs 1 --target-dir <shared-target> -p locallore-storage --test playable_archive --test branch_retention_archive --test archive_interruption -- --test-threads=1
```

New native broker transfer oracles are frozen at
`ab43563c3097966c295e761fca2779b80fd2ed82`, sole new source
`apps/desktop/src-tauri/src/archive_v3_tests.rs`. Root adopted them as
`d1f65d3` and registered them as `53928c9`; they remain uncompiled and unrun
at this addendum. No native success is inferred from
their source. Existing Full/checkpoint/interruption and broader Rust,
Workspace/native compatibility, formatting and strict lint checks remain
Root-owned and pending on the final integrated source.

Root separately observed shared Cargo target contamination in another Core
source cohort. Future final checks will use source-owned target directories.
That observation is not evidence that these previously source-bound Archive3
executions used a wrong artifact, nor is it a new execution of them; retain
their exact sources/logs and record final target/source ownership explicitly.

From `apps/android`, compilation-only is
`./gradlew.bat --offline :app:compileDebugAndroidTestKotlin`. Preserve the first
actual fixture/compile/behavior failures before any narrow correction, and
record exact source and results for each rerun. Actual Android instrumented
runtime, native picker/IPC transfer, desktop↔Android roundtrip, app-owned render
inspection, physical-phone qualification and owner acceptance are not supplied
by this report. D07 model/timing cohorts are separate evidence and are not
relabeled as Archive3 qualification.

Documentation ownership remains open under
[#12 claim6381144573](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6381144573)
and [#30 claim6381144716](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6381144716)
for later coordinator results. Next runnable task is Root's native broker
oracle adoption/execution and source-owned compatibility qualification,
followed by authorized consumer/platform closure; no milestone checkbox changes
at this checkpoint.

## Selected Domain2 panel action addendum — 2026-10-24

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
