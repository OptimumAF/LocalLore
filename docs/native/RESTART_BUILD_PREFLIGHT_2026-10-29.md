# Restart build preflight: frozen source and offline artifacts

Refs #14 (M10.02), #13 (supporting M09.06). This packet builds and checks the
isolated Android harness. **It does not qualify a guest, phone, model run or
external Android restart.** Full milestone criteria remain unchecked.

## Frozen checkpoint and source change

Executable/build revision: `f1b813639229d7eeac8274e7e1f329142a8de29c`, retained in
`D:/Worktrees/LocalLore-m10-build-v1` on `build/m10-restart-frozen-v1`.
All 2,211 tracked raw files and 971 compiled-prefix entries remain bound to that
checkout. Later report commits are not substituted into those hashes or HEAD.

The only production change advances the code-fixed restart guest root to
`D:/Dev/Experiments/LocalLore/2026-10-29-restart-after-metadata-v1/avd-v1`.
The previous guest and its spent claims remain closed and preserved. No guest
directory is created by the change. Wire version, schemas, source/query/proof
checks, resource floors, time limits and one-shot claims remain unchanged.
Only the matching synthetic fixture constant changes; all 28 existing contract
test method ASTs remain identical. See the [fixed target specification](FRESH_RESTART_TARGET_PROFILE_2026-10-29.md).

Seven original independent cases first record two failures and one error on the
old target: the fixed constant is old, the old-root admission is accepted and
the new-root admission is refused. The exact same seven pass after the change.
They establish pure metadata behavior, no JSON selector, closed source roster,
unchanged limits and import behavior; they do not establish live source
freshness, human permission or actual device state.

## Actual verification

All commands start in physical D worktrees with process-local TEMP/TMP/TMPDIR
set to `D:/Dev/_Temp`. Private source-bound drivers use create-only outputs,
finite owned jobs, exact requests, source-before/after hashes and raw captures.

| Check | Actual result |
| --- | --- |
| Old-source focused host baseline |161 tests pass at 0cbb; owner 123,000ms0. Historical baseline only.|
| Fresh target original seven |Old target:2 failures/1 error; unchanged seven then pass, owner 4,964ms0.|
| Current focused host subset |168 tests pass; owner 136,570ms0, no failures/errors/skips/exclusions.|
| Current full Python suite |2,176 pass in 332.012s; owner 339,047ms0, no failures/errors/skips/exclusions; all 2,211 tracked hashes stable; eight stdlib null-sink opens and no forbidden project writes.|
| Native Android helper compile |NDK29 x86_64/API35; owner 2,743ms0, empty streams, known capture/cleanup. ELF 13,848B, PIE64/machine62/linker64, libc/libdl. Never executed.|
| Fixed native-helper file reader |Passed with actual source/tool/request/output paths and explicit cross-worktree byte equality; no tool/ELF execution by reviewer.|
| Offline APK/JVM build |Owner286,683ms0, empty parent streams, known capture/cleanup; both signed APKs and all 2,211 inputs stable.|
| JVM tests |588 tests across 58 XML reports; zero failures/errors/skips.|
| Fresh lint |Actual same build job; analyzer 32.4.1, analysis_did_work=true, zero Error/Fatal and 10 warnings. No separate lint phase was invented or rerun.|
| Independent closed build/lint replay |Distinct v3 receipts pass: full raw/index maps,98 artifact roster, JVM XML, captured package/signature audits, ZIP/manifest/JNI contracts and actual defined instrumentation methods.|
| Actual-build-bound host simulation |All five checks pass; owner 53,804ms0, known capture/cleanup, empty streams, stable 2,211-source map.|

Lint warnings are UsableSpace7, GradleDependency1, ObsoleteSdkInt1 and
OldTargetApi1. These remain warnings, not waived errors. Existing pins are
Gradle 8.11.1, Rust 1.93.1, Android SDK36/build-tools35.0.0, NDK29.0.14206865 and
LiteRT-LM0.18.1. The configured Java21 installation is byte-pinned; no fresh
Java patch-version query is claimed. No dependency/model version changed or
download occurred.

| Built artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Product APK |78,423,520|c8adf07e9ae6802f98108ea8f9d0f061200119203273c95dd6f7e98069bfcd09|
| Instrumentation APK |2,272,447|215731ef23e46f1dd1d97f9fb846672eaa954467332069f8723520f3101a0221|
| Android process helper |13,848|8c9408c4af7ce73d4e39dde712c291dd1d5e042e53ff407414dfa4d864d41972|

The host simulation joins the actual APKs, compiler output, native-helper
manifest, full source maps, actual 588/58 results and independent v3 reports.
It uses the actual fixed controller/client classes, create-only claims,
prerequisites, raw/JUnit/tar readers and third-method proof. Bulk model/probe
inputs, native observations and socket/device IO are explicitly simulated.
Its five checks cover full closed result, wrong external caller, wrong head,
noncanonical result path and 1199-vs1200-second budget refusal. It supplies no
execution authentication, inference quality or guest authority.

| Durable private receipt | SHA256 |
| --- | --- |
| Full Python result |3ca892b42fa954b4aa1a37663574cc00b81530edf4eb70b1d8a27a2caa7f8f48|
| SDK build result |18a411a620b65f02cf4602881585e049201f770a4dc179fc4806fa0386a84eab|
| Native-helper build result |00bf99f9b1e185043cabb1621964c73e1f96eb6c6da312d3287c118a68a7f4d1|
| Independent build replay v3 |0295c6c49bf960bdde58230809082bf4b5e0e53737d9665d106eabc2e06bdc35|
| Independent lint replay v3 |4475c1d5b4ec20b3329ff64c5544229903e761d5fb0e6d227af14d5eeace42f4|
| Joined 12-key build manifest |66af52f1ca8e789b6fc6ae76ad79b14e8eb5705eae172b7508dc085c977788f3|
| Build-bound simulated result |560fcd3f3cd9a882ad321e8300a9c989d09bd03cae35fe992b00163d5a0863fc|

Actual private command entries under
`D:/Dev/Experiments/LocalLore/2026-10-29-restart-build-preflight-v1` are:

```text
python -I -S -B <packet>/check-root-v1.py all root-full-v1
python -I -S -B scripts/build_android_author_process_probe.py --ndk <installed-NDK29> --output <packet>/native-helper-v1
python -I -S -B <packet>/android/build-sdk-v1.py sdk-build-v1
```

The SDK driver runs the installed Java wrapper offline/no-daemon/no-build-cache,
max-workers2, D Gradle/Cargo/Android caches, no SDK/Java downloads and the existing
signer read in place. Tasks are cleanTestDebugUnitTest, testDebugUnitTest,
lintDebug, auditLiteRtDependencies, auditLintAnalyzer, cleanPackageDebug,
cleanPackageDebugAndroidTest, assembleDebug and assembleDebugAndroidTest. No
connected/install/ADB/owner/preparation task runs. The build-bound driver runs
from the frozen build checkout, without patching the controller's source ROOT.

## Preserved failures and exact byte handling

The fresh checkout initially differs from the coordinator in eight CRLF/LF
files despite an equal Git commit. Those original files and the failed raw
comparison are preserved. Only this new checkout is aligned to the coordinator's
exact bytes before freezing; no prior capture or coordinator file is normalized.
Git then reports eight modified paths while semantic diffs are empty. An
ordinary add of exactly those paths refreshes the index: actual porcelain becomes
empty, HEAD/tree and index flags stay unchanged, and all 2,211 raw hashes remain
identical. The original index and failed alignment are preserved; no assume-
unchanged/skip-worktree flag, config change or guard exception is used.
See [Git add](https://git-scm.com/docs/git-add) for the index operation.

Independent replay v1 incorrectly requires unique runtime coordinates. The
actual locked audit retains 62 rows/61 coordinates, including two identical
androidx.core:core:1.13.1 bindings. V2 then chooses the lint report model directory
instead of the actual analysis model directory. Both failed verifiers/receipts
remain unchanged. V3 retains all duplicate rows, checks every coordinate against
the selected lockfile and exact binding consistency, and rehashes the actual
analysis XML files. No artifact, captured result or build is altered or rerun to
correct these verifier assumptions.

## Storage and remaining gates

Before the large build, expected growth is 8–12GiB with a 14GiB allowance and a
retain-all-outputs plan. Observed aggregate logical growth is 0.81234GiB:
789,914,789B in the worktree, 211,652B shared Gradle-cache growth and 82,117,863B in
the private packet; Cargo/Android-user growth is zero. These are non-atomic
observations, not a quota, physical allocation measurement or exclusive process
attribution. New recovery has a separate 0.3GiB allowance. Ignored build outputs
remain in the frozen checkout; source/APKs/reports/captures are preserved on D.

Create-only recovery at
`D:/Dev/Recovery/LocalLore/2026-10-29-restart-build-preflight-v1/checkpoint-v1`
preserves 2,475 original/copy/readback/after entries: 2,211 frozen raw source
files, 262 closed packet files and two actual named native source/builder files.
Raw original bytes total 119,510,867B; complete generated recovery including
bundle/metadata is 135,721,273B, within 0.3GiB. Exact rosters, source/context maps
and the explicit frozen branch bundle verify. Ignored compiler caches remain
in place; no model, virtual disk, credential or installed-tool bytes are copied.
Recovery manifest SHA256
`8f651e422587ba9cbf0c845fc7f7b5abbd6596be0abe0284bd9a8bdf9fcdda8d`;
bundle 13,122,286B SHA256
`802169eddc482eb7c4a3f059a9dcab9fe7ab89c8b72ce6ac707ada8a771f1499`.
Independent readback rehashes all 2,475 original/copy/after entries and exact
copy rosters, joins the actual request/source maps, and verifies the fixed
bundle/ref. Its 5,919ms owner exits 0 with known capture/cleanup and empty streams.
Readback SHA256
`d466f50282d27baf943632929c96a09f6c561e72904ebd8343484105f203bc6f`;
terminal receipt
`61b3c29cbee4b4e90d61e31ef631ef73587e1c0818e2e7ca699657459af3d8db`.
The first verifier incorrectly expects a separate Root sources-after file;
that KeyError/helper/capture remains preserved. Its distinct continuation uses
the actual Root request source map and recorded equality, without changing any
artifact or weakening the raw-copy comparisons.

The subsequent operator storage policy is an additional hard gate. The frozen
checkpoint lacks the shared AVD guard and is **ineligible for any guest work**.
The guard was observed as uncommitted work in another checkout and later in the
named coordinator checkout, after the frozen host checks completed. It is left
untouched; its uncommitted files and results are not part of this qualification.
Reporting moved to a separate worktree to preserve that work.

Before any guest preparation or SDK4/SDK5 owner execution, integrate and review
the shared storage tooling, reconcile its added source-closure/tests, and produce
fresh exact source/build/admission bindings. Use only
`D:/Dev/_Migration/LocalLore-AVD-Storage`, at most two unretired roots and 64GiB
accounting, with 40GiB per preparing/live guest. Do not create another registry
or run copied older owners. Retired October 27 record roots remain records-only.
Guest images, RAM mappings and current recovery need applicable authorization
before retirement; stopping is not disk reclamation.

M10.02/M09.06 remain partial/in_review. Actual Android restart, mid-generation
cancellation, full journeys/accessibility, phone/ARM64 and model quality/
performance remain unqualified. Phone availability is not assessed here. No
guest, service, device, model, system-setting, other-emulator, merge or release
action occurs. Next runnable prerequisite is reviewed storage-guard integration
and updated source/build checks, followed by a separately approved guest case.
