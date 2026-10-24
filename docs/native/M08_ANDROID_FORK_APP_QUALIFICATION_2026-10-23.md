# Android fork app: current-baseline qualification, 2026-10-23

Refs #12 (M08.01/.02 partial), #30 (D08.04 partial). Implemented and locally verified host/build slice; independent integration review/owner acceptance and Android runtime/device gates remain pending. No full milestone acceptance.

## Frozen source and ownership

Integrated baseline `c9c61285513971c097a581c2e959132384c91fb0` contains accepted Shared M07 `a14c899` and the original frozen Android fork library/app packet. All 13 author paths match `a30a963`; original 22 controller/library cases and all 13 new VM cases are unchanged throughout this qualification. Later accepted desktop-only PR #121 was not merged into this cohort. No author-Core candidate or newer desktop memory UI is included.

Task-owned `source-android-fork-app`, branch `qualify/d08-android-fork-current`; final tested production source **`6636ff61072a9b75e4c922ccaf5b0a419a6786f6`**. Only production difference from the integrated baseline is the narrowly transferred `ForkRecoveryStore.syncDirectory` helper. Mappable commits: `b565425dee314ab9804e2b8bb4102f854d26a3dc` then `6636ff61072a9b75e4c922ccaf5b0a419a6786f6`. No Core/Store/Host/schema/JNI/runtime/other Kotlin production changes.

Coordinator integration claims [M08](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6376341630), [D08](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6376343987); delegated qualification [M08](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6376826950), [D08](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6376827122). Narrow SDK correction claims [initial](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6377011259), [API26 followup](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6377105510). All heavy checks ran sequentially under explicit coordinator allocation; the slot was released immediately after checks, before writing this report.

The actual app path and remaining feature limits are documented in [the source freeze](M08_ANDROID_FORK_APP_2026-10-23.md). One NativeWorkspaceTransport owns the workspace and supplies its existing handle allocator to the native fork gateway. Exact four-field recovery is saved synchronously before registration; startup is lookup-only. Creation and resume are explicit, and shared Rust owns fork completion/history/permission rules. This packet adds no author corrections or model backend.

## Failures retained before correction

1. Initial retained checkpoint **`0a55e714c599ddf7cafb8dd59ddeae880a8856a9`** reverses only the explicit-resume fix on the current baseline. The first run failed production Kotlin compilation: public SDK36 has no `OsConstants.O_DIRECTORY`. No new test executed; stale prior XML was explicitly excluded. Both ordinary Rust JNI ABIs did compile freshly: x86_64 **1m34s**, ARM64 **1m37s**. Total runner wall time 218.10s. Log SHA256 `1a3db9bf04177e8c6aadb8140941894786b30a98132235e146da003f9e310cf2`.
2. `b565425` replaces that flag with public readonly/cloexec open followed by opened-descriptor `fstat`/`S_ISDIR`, `fsync`, and unconditional finally-close. Applied identically to the retained pre-resume-fix source **`a56910782053b256ff59341b3d1ad65c8d90df7f`**, the unchanged thirteenth VM test actually runs and **fails 1/1**, zero errors/skips: explicit resume expected one catalog refresh, observed zero (`BranchForkShellTest.kt:286`). Wall 48.30s; fresh XML retained. Log SHA256 `1cbfab8fcef7c7360df87adb9d9fe0de55b3a0145679c8315396855ab5476c1d`. Restoring the resume correction at `b565425` passes the focused **35/35** and full **182/182** JVM cohorts. This is the measured regression, distinct from the earlier compile failure.
3. APK/testAPK assembly succeeds at `b565425`, but lint fails **one error/one warning**: unconditional `O_CLOEXEC` is public only from API27 while minSdk is26. Log SHA256 `311fcd394f83eeb5022325cf3d46d64e53d30a41ac4a3da19a678ed8443614a5`; original text/XML reports retained. The proposed `fcntlInt` substitute was rejected **before implementation**, because the installed SDK's API-version metadata marks it API30.

Final `6636ff6` guards the public modern flag at API27+, uses readonly open on API26, and keeps the same descriptor-directory validation/sync/finally-close on both paths. No magic constants, lint suppression, SDK bump or dependency upgrade. API26 close-on-exec behavior is **unasserted**: this helper holds a short-lived readonly directory descriptor and launches no child process. File/directory sync failure still prevents native admission; exact readback and uncertain-write semantics remain unchanged. This was an uncompiled packet's compatibility correction, not a weakening of previously measured Android guarantees. Installed SDK36 `android.jar` signatures and `data/api-versions.xml` are retained in the local evidence. Public [OsConstants](https://developer.android.com/reference/android/system/OsConstants) and [Os](https://developer.android.com/reference/android/system/Os) references describe the SDK methods; actual min-level evidence comes from the installed SDK metadata and lint.

## Actual results and freshness

| Check | Tested source | Result / runner wall time |
| --- | --- | --- |
| Frozen resume regression | `a569107` | Expected **1 failure/1 test**, 0 errors/skips; 48.30s |
| Focused fork JVM | `b565425` | **35 pass**: original15 + independent4 + lifecycle3 + VM13; 18.26s |
| Full current JVM | `b565425` | **182 pass**, 22 XML classes; 12.16s |
| Final full current JVM | `6636ff6` | **182 pass**, 0 failures/errors/skips, all 22 XML files fresh; 17.96s. Includes the same 35 focused cases. |
| Actual Rust fork registry/Host/Store | `b565425` | **9 pass**, 0 ignored; 41.30s including build, cases0.45s |
| Actual Rust close/cancel lock units | `b565425` | **2 pass**, 0 ignored, 10 filtered; 2.95s including build |
| Strict Rust all-target/all-feature Clippy | `b565425`, final `6636ff6` | Pass; 11.72s initial, final0.49s cached. Rust bytes unchanged. |
| Ordinary final debug APK + testAPK + lint | `6636ff6` | Pass; 59.81s. Lint **0 errors, 1 inherited warning**. |
| Final Rust formatting | `6636ff6` | Pass; 1.70s |
| Actual final APK audit | `6636ff6` | Pass; 0.23s. Both JNI ABIs, reviewed permissions/16KiB library alignment checks. |

Both JNI release libraries were freshly compiled by ordinary `preBuild` in the initial compile-failure cohort. Rust/build-tool inputs remain identical for the SDK-only Kotlin corrections, and subsequent ordinary native tasks correctly report UP-TO-DATE. Final APK was repackaged; testAPK, after its earlier actual instrumentation-source compilation, reports UP-TO-DATE in the final package run. Caching is not new JNI execution.

The one lint warning is the existing GradleDependency suggestion for coroutines1.10.2 vs1.11.0; the pinned dependency is unchanged. Initial instrumentation compilation also retains the existing `FrameworkInterruptionTest.kt:128` AtomicReference<Boolean?> identity warning. Neither is suppressed or described as zero warnings. All nine new app instrumented/component cases compile; none executed on Android. JVM typed-port cases establish controller/VM admission, not SQLite/JNI/AtomicFile/Compose runtime behavior.

Environment: Windows host; JDK **17.0.6+0-b2043.56-10027231**, Gradle **8.11.1**, SDK **36**, NDK **29.0.14206865**, Rust **1.93.1 (01f6ddf75)**, Cargo **1.93.1 (083ac5135)**, Python **3.14.7**. Own D-drive outputs/TEMP; existing offline Gradle cache. Ordinary uncapped SQLite flags, no SDK download, one heavy process at a time.

## Commands and local artifacts

Exact cwd/environment/executable/argv and exits are retained in `android-fork-app-artifacts/final-report.json`, SHA256 **`be8bf5ef28b3e5a59de1f891ac15cfce6f0876e166dff46cbbb73ba814059b2c`**. Original/current/SDK/final plans, run records, stdout/stderr, fresh XML copies, API metadata proof, failed and final lint reports are retained separately. No initial log is overwritten. The task-local output init redirects every Gradle project's build output to the author's own preexisting D-drive cache; it does not modify system/user Gradle configuration.

The executed ordinary commands use this common Gradle prefix from `apps/android`:

```powershell
.\gradlew.bat --offline --no-daemon --max-workers 1 `
  '-Pandroid.builder.sdkDownload=false' --init-script <task-owned-output-init> `
  :app:testDebugUnitTest --tests org.locallore.app.BranchForkShellTest.explicitRecoveredResumeRefreshesCurrentCatalogBeforeSelectingExactConfirmedChild
```

After restoring the corrected source, the same prefix runs `:app:testDebugUnitTest` filtered to BranchForkControllerTest, BranchForkReviewTest, BranchForkRecoveryLifecycleTest, BranchForkShellTest; then unfiltered `:app:testDebugUnitTest`; and `:app:assembleDebug :app:assembleDebugAndroidTest :app:lintDebug`. No `-x buildRustAndroid`, connected/install task, capped compiler flags or network fallback.

From the repository root, each command uses its own existing `--target-dir <task-owned-android-fork-target>`:

```powershell
cargo +1.93.1 test --locked --offline --jobs 1 --target-dir <own-target> -p locallore-android --test branch_fork_native -- --test-threads=1
cargo +1.93.1 test --locked --offline --jobs 1 --target-dir <own-target> -p locallore-android --lib workspace::branch_fork::tests -- --test-threads=1
cargo +1.93.1 clippy --locked --offline --jobs 1 --target-dir <own-target> -p locallore-android --all-targets --all-features -- -D warnings
cargo +1.93.1 fmt --all -- --check
python scripts/audit_apk.py <own-final-app-debug.apk>
```

Final app APK: **23,289,639 bytes**, SHA256 **`601cf9b5f461018f789bc8f3b8ede2a2817bd2c2d072b31d021cf1febf3d5d42`**. Test APK: **1,706,845 bytes**, SHA256 **`ceda52754a72b7e9bd2c183808b15f947d71449a435f1dc36f934cd9f3f95a41`**. Artifact location is the retained task-local `android-fork-artifacts/gradle-output/_app/outputs/apk/` tree, not a published release.

## Limits and next gate

No device/emulator/ADB/install/connected task, actual Android JNI/framework/Compose execution, model/worker/assets, application launch, CUA/desktop control, protected resource, settings, PR or merge action. Runtime sync behavior, process death/power loss, rotation, visual/touch accessibility and physical-phone parity remain unqualified. API26 descriptor caveat is explicit above. Independent integration review and owner acceptance are still required; root coordinates them and further application/device evidence. The accepted Desktop fork journey is separate evidence and is not reattributed here.
