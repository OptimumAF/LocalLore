# Current ordinary phone artifacts: offline verification

M10.03 / issue #14, 2026-10-29. Locally verified for review; full privacy,
device and release gates remain unchecked. This follows the
[paired backup guard](PHYSICAL_APK_BACKUP_LINKAGE_2026-10-29.md) and resolves
its missing-artifact prerequisite. No application, dependency, runtime, model,
manifest, rules XML or public build-system code changes.

## Frozen source and profile

Actual build source: 9c4bae86be6f6cd150b999b9b635e8e85b05abbd at
D:/Worktrees/LocalLore-m10-physical-build-v1. The checkout remains frozen,
clean, with its ignored build outputs retained. Its2238 raw tracked hashes
and989 compiled-prefix input hashes match before/after. The later report
commit changes only README and this document; old778f build results are
not retagged.

Ordinary packages: org.locallore.app.phoneverify and its .test package.
Select exactly localLorePhysicalModelVerification=true,
localLoreLiteRtVerification=true and localLoreModelSetupVerification=true,
with exclusive .gradle-physical-model cache/app/build-physical-model output.
No optional private setup fixture is present or selected. Old receipt,
volume, picker and unrelated experiment selectors stay absent.

Existing locked tools: JDK21, Gradle8.11.1, AGP8.10.1, Kotlin2.4.0, SDK36,
build-tools35.0.0, NDK29.0.14206865, Rust1.93.1, LiteRT-LM0.18.1,
Gson2.14.0 and coroutines1.11.0. No version change, dependency/model choice,
download, SDK installation or global setting change. Read-only preflight
rechecks407 locked crate archives,129 runtime/analyzer artifacts, six cached
descriptors, distribution/tool hashes and both Rust Android targets.

## Actual commands and ownership

From the physical frozen checkout, with process-local
TEMP/TMP/TMPDIR=D:/Dev/_Temp:

```powershell
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-current-physical-artifacts-v1/android/build-sdk-v6.py sdk-build-v1
```

The source-bound wrapper invokes GradleWrapperMain from apps/android with
--offline --no-daemon --no-build-cache --max-workers=2 --console=plain,
explicit existing D Gradle/Cargo/Android caches, D Java temporary output,
the existing signer read in place, the three selectors and exclusive project
cache above. It sets Cargo offline/jobs2, disables SDK/Java downloads and
Kotlin incremental compilation, and preserves the requested lint selector
-Pandroid.experimental.lint.version=9.4.1.

[Official Kotlin configuration](https://kotlinlang.org/docs/compiler-execution-strategy.html)
supports the per-run in-process compiler/fallback-disabled properties.
They keep compilation inside the owned build process; no global properties
file or another project's compiler service is changed.

Exact task list:

```text
:app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug
:app:auditLiteRtDependencies :app:auditLintAnalyzer
:app:cleanPackageDebug :app:cleanPackageDebugAndroidTest
:app:assembleDebug :app:assembleDebugAndroidTest
```

The build also executes its existing buildRustAndroid prerequisite.
Limits remain600seconds per captured command/900seconds for the owned parent;
cleanup can add time. The actual started receipt binds the exact request and
worker identity before dispatch and remains unchanged afterward.

One actual build attempt: owned session89482 exits0, worker0, **373875ms**,
known descendant cleanup/complete output capture, empty parent streams,
all source/tool/environment pins stable. Gradle reports successful completion
in5m58s,87 actionable tasks/84 executed/3 up-to-date; this does not label
every task as freshly executed. Result SHA256:
774eb41f827b3bd232467e75ebeac62357ad1903f383a53889109c293287d89c.

## Tests, analysis and complete paired audit

Independent source assessment first reconciles588 common methods/58classes
against their prior actual XML and unchanged Kotlin sources, plus18 physical
methods/two classes. An unannotated helper is not counted. Actual new XML
matches **all606 unique class/method IDs across60 reports**, zero failures,
errors or skips. These tests actually run in this build; a count-only or
UP-TO-DATE result is not substituted.

Fresh same-job lint analysis uses actual analyzer32.4.1,
analysis_did_work=true/check_dependencies=true and four retained lint-model
XMLs. It records10Warnings: UsableSpace7, GradleDependency1, ObsoleteSdkInt1,
OldTargetApi1; zero Error/Fatal. Console/compiler warnings remain in raw
captures. No suppression, analyzer fallback or lint rerun is used. Runtime
and analyzer graphs remain locked; duplicate variant rows are retained.

The actual complete paired command runs after assembly:

```powershell
python -I -S -B scripts/audit_physical_model_apk.py --app <retained-phone-product.apk> --test <retained-phone-tests.apk>
```

There is no --physical-setup-fixture flag or generic litertverify replacement.
The nine-key verdict passes both package identities/signing, all six exact
physical test definitions, six native library entries, ABI/alignment/notices,
permissions/launcher/service checks and the actual manifest-selected
resource/default XML/five-domain backup rules. APK bytes and inputs remain
stable across the audit.

| Retained APK | Bytes | SHA256 |
|---|---:|---|
| Product | 78439956 | e56003dec335a707c69e78e23beac8b6e3be0d7b3f6272fa3c931650a66e54b3 |
| Tests | 2242907 | 4e0ea7ac8e5875cffaf9e3eb8a295186bb63b86640e5f6753d75aad15f3780f9 |

Both actual native targets execute: x86_64-linux-android and
aarch64-linux-android. Retained task/per-target logs and file hashes connect
release output to generated/AGP merged libraries, then separately connect
AGP stripped output to retained copies and APK entries. Installed llvm-strip
is byte-bound; no separately recorded per-strip argv is invented. The owned
JNI libraries have three LOAD segments at16384-byte alignment per ABI.
This is cross-compilation/static artifact evidence, not ARM64 execution.

Independent file-only closed readback exits0 in7982ms, checking all106
artifact pins,2238/989 inputs, request/started/owner joins, exact JVM roster,
signatures/paired verdict, ELF bytes/stages and fresh analysis.
It invokes no project parser, auditor, compiler, test, SDK or device command.
Build receipt:
71add8db561f91cb3370e778e40d5ac1d7a4022c6cb36d9635e1c3c078cb42fc.
Lint receipt:
64db44cf28298abb0ea1a7462ae16d7f6c3279fa457ffc825fc4880dbf362cec.
Artifact index:
18ab05740b13c2c8e8d1a2d2ff8bc5bfd97e975e72ba83c8a6cdf53a20aa88e1.

## Preserved preparation, storage and remaining gates

All v1-v5 private preparation drafts remain UNRUN. Before dispatch, both
reviewers reject generated==APK as an invalid oracle because AGP strips the
app library. V6 preserves both legitimate stages instead. Earlier compiled
input count985 is replaced by the actual989 inventory before dispatch.
These are preparation corrections, not fabricated failed builds or RED tests.
The standalone x86/API35 author-process probe is unrelated to this ordinary
phone artifact case and is neither rebuilt nor qualified.

The previous2308-host-test result stays attributed to its original847a source;
it is not reported as a new run. This packet changes only documentation after
the actual9c4 build and needs no product-code regression rerun.

Before execution: expected8–12GiB/max14GiB inclusive worktree, build/cache,
captures and <=0.3GiB recovery. Observed named-root logical growth before
recovery is913619548B (about0.851GiB). Shared/non-atomic metadata is neither
exclusive attribution nor a quota. Original source, APKs, JNI stages,
ignored builds, caches and preparation records remain intact.

Private output:
D:/Dev/Experiments/LocalLore/2026-10-29-current-physical-artifacts-v1.
Matching D recovery includes exact source, closed evidence and built APK/JNI
copies within the0.3GiB allowance. No signing-key, model-weight, save or guest
image is copied; no private artifact is uploaded.

No phone installation, instrumentation method, JNI library, inference,
model import, emulator, ADB, socket, ledger or backup/restore is executed.
No other emulator is stopped, no shared service/system setting changes,
cleanup, merge or release occurs. This is artifact qualification, not a
supported-phone declaration, device privacy result or model-performance claim.

Next runnable task: fresh read-only admission of the previously authorized
phone against these verified artifacts; only an eligible, authorized target
can proceed to bounded local-model tests. The existing buffered-emulator
approval remains unanswered and is not inferred from this host build.
