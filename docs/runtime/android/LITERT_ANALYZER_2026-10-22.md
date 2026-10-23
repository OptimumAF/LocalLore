# Isolated SDK lint analyzer compatibility

M01.02/M01.05 development follow-up on baseline `91d2ec2`. This resolves the
earlier analyzer limitation for this experiment; the historical
`LITERT_BUILD_2026-10-22.json` retains its original exit-2 evidence.

## Supported mechanism and exact pin

Android's [lint documentation](https://developer.android.com/develop/ui/compose/tooling/lint)
and the Google-maintained
[newer lint guide](https://googlesamples.github.io/android-custom-lint-rules/usage/newer-lint.md.html)
document `android.experimental.lint.version` for using a newer analyzer while
retaining the Android Gradle plugin. The option remains explicitly experimental.
The published [AGP 8.10.1 sources JAR](https://dl.google.com/dl/android/maven2/com/android/tools/build/gradle/8.10.1/gradle-8.10.1-sources.jar)
confirms `LintFromMaven` resolves an isolated, transitive analyzer classpath and
maps the user version's major number plus 23 to the Maven artifact version.

Only the standalone experiment sets `android.experimental.lint.version=9.4.1`,
selecting `com.android.tools.lint:lint-gradle:32.4.1`. Google Maven's observed
metadata lists this as its newest stable version; newer 32.5 release candidates
and 32.6 alpha are excluded. The production app, AGP 8.10.1, Gradle 8.11.1,
SDK/target 36, SDK dependency 0.18.1 and runtime Java sources remain unchanged.
No toolchain installation or SDK license acceptance occurred.

The exact lint bridge JAR has classfile major 61 (Java 17). Its matched compiler
artifact embeds `META-INF/compiler.version=2.4.0-dev-2631-for-lint`; this is the
compiler packaged by the stable lint release, rather than a separately selected
Kotlin plugin. The existing JBR 17.0.6 runs Gradle and the analyzer; existing
JDK 21.0.4 compiles the application's Java-17-targeted sources because the SDK
API uses major-65 bytecode. Actual assembly, D8 and analysis pass with those
tools. [Source identities](LITERT_ANALYZER_SOURCES_2026-10-22.json) preserve the
retrieved metadata, published artifacts and inspected source hashes.

## Audited dependency and analysis boundary

AGP's analyzer configuration is detached and is not covered by a normal named
configuration lock. The experiment therefore mirrors its exact dependency graph
in a named, locked `analyzerAuditClasspath`. An audit compares this graph's actual
files with `lintAnalyzeDebug.lintTool.classpath`, then records their computed
SHA256 values. The helper requires every entry to match the frozen
[67-JAR analyzer manifest](LITERT_ANALYZER_LOCK_2026-10-22.json). No analyzer JAR
is an application implementation dependency.

`checkDependencies=true` is explicit. The helper verifies the actual analyzed
dependency model contains SDK 0.18.1 and Kotlin reflection/stdlib 2.4.0. It also
checks lint's XML issues and rejects Kotlin metadata/infrastructure diagnostics
from the build log, even if Gradle exits zero. A clean issue report alone cannot
satisfy the gate. Eight additional Python regression cases cover these false
green paths, missing SDK/model evidence, changed analyzer hashes and model path
escape. This proves the recorded tool/dependency combination, not exhaustive
semantic analysis of every possible runtime behavior.

The primary analyzer/compiler POMs declare Apache-2.0. The full build-only graph
has its own per-component license declarations, including permissive licenses,
EDL and JNA's LGPL/Apache alternatives. Exact POM identities, inherited license
sources and declarations are retained in
[POM/license evidence](LITERT_ANALYZER_POMS_2026-10-22.json). These tools are not
redistributed in the APK or this source-only change; no blanket Apache license
or production redistribution clearance is inferred for third-party components.

## Executed red/green verification

With `JAVA_HOME` selecting the existing JBR 17.0.6 and `ANDROID_HOME` the existing
SDK, run from the repository root:

```powershell
python benchmarks/spike/android/litert/build.py --java21 'C:/Program Files/Java/jdk-21' --offline --probe-incompatible-analyzer
python benchmarks/spike/android/litert/build.py --java21 'C:/Program Files/Java/jdk-21' --offline --clean
python -m unittest discover -s benchmarks/spike/android/litert -p 'test_*.py' -v
```

The explicit negative command reruns original lint 8.10.1/31.10.1 against the
unchanged actual SDK dependency. Its Gradle process succeeds, while the analyzer
reports SDK/Kotlin metadata 2.4.0 versus expected 2.1.0. The helper detects this
and returns the expected exit 2. It returns 3 if that required failure is not
observed. An initial metadata-only synthetic JAR appeared in the model without
triggering a diagnostic, so it was rejected as proof and removed from the final
implementation. The retained negative check reproduces the real original gate.

The subsequent fresh clean normal command runs all 51 tasks, passes 14 JVM
tests, performs actual lint 9.4.1 analysis, verifies its SDK dependency model and
hashes, audits the APK and returns exit 0. The final offline run reports
**zero errors and two unsuppressed advisories**: SDK 37 is available and target
36 is older than latest. The initial online pass also advertised a newer
prerelease lint. SDK/target and analyzer pins are
retained within this packet's tested scope; no warning suppression is used.
All 20 Python tests pass. No metadata incompatibility or analyzer infrastructure
failure appears in this final analysis.

The fresh APK's full digest is
`5014b3952bedc4e84787421477fae553ae9fc289df01fb311207353d06535e85`.
It differs from the earlier `a74b05b9...` APK. Read-only ZIP comparison proves
every uncompressed entry payload identical, including all DEX, native, manifest
and resource bytes. The `classes3.dex` entry moved relative to the native
libraries, changing alignment padding and the signing block. This is not an
identical-APK or reproducible-packaging claim. Both ABI libraries, zero requested
permissions and 16 KiB ZIP alignment pass the audit.

[Machine verification evidence](LITERT_ANALYZER_VERIFICATION_2026-10-22.json)
records the exact scope. This agent performed no emulator, phone or model calls;
the coordinator owns all device checks and final integration. Physical-device,
model-quality, performance and production-backend selection gates remain
unchanged.
