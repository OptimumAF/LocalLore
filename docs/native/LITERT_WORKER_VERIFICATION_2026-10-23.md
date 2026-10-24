# Concrete LiteRT worker verification, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 prerequisite
and M05.04 supporting; [#5](https://github.com/OptimumAF/LocalLore/issues/5),
M01.02 supporting. Partial implementation is in review, not accepted milestone
completion. This packet is stacked on unmerged [#129](https://github.com/OptimumAF/LocalLore/pull/129),
head `327c99226cc2f7a3b53b203da50670ad4c4c5413`.

## Working implementation

The concrete SDK adapter implements the same production workspace owner's
`LocalRoleWorker` boundary. Trusted immutable configuration derives its native
profile and worker together; model responses cannot select paths, profiles,
commands or a fallback. Full size/hash/confinement admission precedes SDK
allocation on IO. One Engine serves fresh sequential role Conversations, with
exact Rust schema/token/context budgets and four CPU threads. Observed unknown
ownership is sticky and immediately fences the same owner, including late
callbacks after Ready; accepted commits remain saved.

The actual SDK path compiles against LiteRT-LM 0.18.1. The ordinary app graph,
provider selection and MainActivity remain scripted. Only an explicit debug
candidate profile includes the SDK/source set. This is not a production runtime
selection, model picker, model import UI or real storytelling demonstration.
See the [contract](LITERT_WORKER_CONTRACT.md) and
[independent review](LITERT_WORKER_REVIEW_2026-10-23.md).

## Official sources and compatibility

Fresh publisher metadata/POM and pinned source confirm the existing 0.18.1
candidate, release revision `bda624851d74be34d4e1f7fac1fc4155939539c7`.
The AAR SHA256 is `05c6bdc8acda834efcca12c0ad5d06d2cd8c83e60770f056d8d222f699f3012b`;
its Java classes are major 65. The POM declares Gson 2.14.0, reflection 2.4.0
and coroutines Android 1.11.0. Official Kotlin/Compose/Gradle/AGP compatibility
sources support the separately pinned candidate graph; exact links and licensing
limits are recorded in the independent report. No metadata skip or dependency
suppression is used.

The candidate uses Kotlin/Compose compiler 2.4.0, Java 21 tools/tests targeting
Java 17, Gradle 8.11.1 and AGP 8.10.1. The daemon remains Java 17. Installed
toolchains are used; automatic Java/Android toolchain downloads are disabled.
The official analyzer-only override 9.4.1 selects lint 32.4.1. The build compares
its actual 67-artifact classpath exactly to the locked audit graph and hashes
all artifacts. `checkDependencies=true` is required, and actual serialized lint
models contain SDK 0.18.1 plus reflection/stdlib 2.4.0.

## Actual build and tests

The reproducible full command is in the [Android README](../../apps/android/README.md#concrete-litert-worker-candidate).
It builds app/test APKs, runs fresh JVM tests/lint and dependency/analyzer audits
with `localLoreLiteRtVerification=true`, the exclusive project cache and exact
analyzer/toolchain flags. The final offline owned build completed in **78,844 ms**,
child zero with known Windows Job cleanup. Its 9,091-byte stdout SHA256 is
`00fb6bbd5c348d747538ebafc369634e4f6b4bc2b8176af24f8d6e882dc956a1`.

- **231 JVM tests passed** across 24 XML suites, including **28 concrete worker
  tests**, zero failures/errors/skips. Synthetic resources exercise exact
  request/schema forwarding, off-thread admission, malformed exposed content,
  size/confinement/hash failures, partial initialization/start, terminal/body
  drain, blocking cancellation, role/Engine close, late callbacks and sticky
  uncertainty during a subsequent initialization.
- Paired-owner tests cover Ready, accepted commit retention, observed late
  callback admission fencing and separately observed same-port invalidation.
  These use injected SDK resources and JVM native ports, not real models/SQLite.
- Both Rust Android ABIs were freshly compiled in the initial compatibility
  build and reused unchanged. No Rust source changed from #129 in this packet;
  its full host suite is supporting prior evidence, not a new execution here.
- All **189 script tests passed** under an owned bounded process, zero failures;
  this includes ten APK audit cases with hostile SDK library/notice variants.
- Final lint reports **zero errors and eight advisories**: six dependency,
  one target-API and one AGP-version warning. Existing Kotlin source warnings
  and the current KGP warning about a future minimum Gradle version remain
  visible. No warning or infrastructure diagnostic was suppressed.

Final Main lint analysis was UP-TO-DATE from the first adapter candidate's
successful dependency analysis; its production source/model inputs were unchanged
by the test-helper fix. AndroidTest/Unit analysis and report/audit tasks ran.
`analysis_did_work=false` is retained rather than described as fresh Main analysis.
The SDK/reflection/stdlib model references and exact analyzer hashes were checked.

Ordinary `debugRuntimeClasspath` resolution separately completed in 17,656 ms,
child zero/known cleanup: SDK absent, Kotlin 2.2.21 and coroutines 1.10.2 retained,
and its existing lock is unchanged. This is a graph check, not another ordinary
APK build. Six configuration probes returned their exact intended errors:
release, mixed timeline, mixed capacity, wrong cache, missing analyzer pin and
missing Java auto-download refusal flag. No release build or device action ran.

## Retained failures and corrections

The initial script compilation rejected qualified `java.security`/`java.util`
names shadowed by Gradle's `java` extension. Explicit imports corrected this;
original script and failure are retained. Dependency resolution then succeeded,
and an initial candidate/Compose compatibility build passed 203 existing JVM
tests in 322,125 ms, before the concrete adapter and stronger analysis gate.
It is partial baseline evidence, not the final SDK qualification.

The first actual adapter build compiled production and all three JNI methods,
then ran 231 JVM cases with 14 failures. Every failure was the same helper
`assertNull(exception.cause)`. Coroutine 1.11.0 stack recovery creates a copy of
the same fixed exception with the original as cause. The minimal test-only
correction requires an acyclic chain of at most eight identical final exception
classes/messages ending in null; private/unrelated causes still fail. Recovery
was not disabled and production errors/ownership assertions were unchanged.
All later lifecycle assertions actually passed in the final rerun. The original
231/14 XML, source, APKs and raw result remain retained.

Source review separately found and corrected late callback proof propagation,
post-Ready same-owner fencing and poisoning overwritten during later initialize.
These are source-derived findings, not relabelled measured test failures.

## Final artifact audit

The final package-output-only clean repack completed in **12,531 ms**, child zero
with known cleanup. The preceding incremental APP was 100,099,682 bytes despite
73,695,753 compressed payload bytes; its TEST was 2,390,629 bytes. Cleaning both
package tasks removed the excess. Independent ZIP entry comparison found all
156 APP and 121 TEST entry names/decompressed bytes identical before/after;
source, compiled code and test coverage were unchanged. Earlier APKs are retained.

| Final artifact | Bytes | SHA256 |
|---|---:|---|
| APP `org.locallore.app.litertverify` | 73,776,528 | `945b368f66b90e1788b235dd8f7d692a804538da4a3d29d3cab4ee13dc0d437b` |
| TEST `org.locallore.app.litertverify.test` | 1,744,113 | `6a76dd65b3c9ae9869e6a045a4966e0aff7c230343734acca73b30340a1dee83` |
| Worker source, LF | 17,672 | `e4545d4f01b6e2b825be478bc9944162ee364b077d66a752e2020b97ab95e9bb` |
| Three-method JNI source, LF | 12,516 | `dd5ef28b3dd5cfb7d77ed5822e0fd68ee831b969bf18b8fa3d5ca68fe46e529d` |

The APP audit checks the exact six native entries, including both unmodified
publisher SDK libraries, stored ZIP data and 16 KiB ZIP/ELF alignment. Both SDK
root notice texts are packaged in generated assets with exact hashes: LICENSE
`ec40a2da15ab0e8b44a9f787ab210203d3cad32572f5f99744a88eb90ff9ba4e`
and THIRD_PARTY_NOTICE
`52a70c82685debf85d4ea9d677615b8636ffd3b75435ce71f247bf5982fb2ba2`.
The APP requests only its own signature receiver permission; no network
capability is added. TEST runner/target and expected test permission are checked.
Neither manifest has sharedUserId. Separate actual apksigner verification of
both final APKs succeeded **before** emulator admission.

Full mixed third-party notices are preserved; this does not establish complete
component redistribution clearance or permit a release. No SDK binary, APK,
weight, signing key, private story or raw diagnostic is uploaded in this PR.

## Evidence and remaining gates

Closed private host/build evidence contains **306 files / 358,364,451 bytes**;
its 65,310-byte index SHA256 is
`10753184862cf68a24aeacee7e08e972cf69e2296fb793efcbf9f443c7fc6e4a`.
It selects closed scripts/source/results/models/logs/APKs, excluding live/temp/
build/cache trees. Raw XML/diagnostics and binaries remain local. Root and the independent reviewer
rehash the selected files; a closed selection is not a claim that every live
workspace/cache tree is immutable.

The source-bound B cohort passed all three JNI methods with a 13,063 ms owned
outer execution and 44 completed/clean clients. No force-stop was needed. SDK
library loading and synthetic admission through actual JNI/Host/SQLite were
exercised; **no Engine.initialize or model generation ran**. Final userdata
availability was 1,542,373,376 bytes, above the unchanged 1,207,959,552-byte floor.
Independent root audit rehashed all 134 closed device files (226,678 bytes),
all 44 client records and paired PASS output, with zero mismatch. Before had
27 packages; installed/after/final maps had exactly 29 and preserved all prior
27 hashes. The 22,677-byte device index SHA256 is
`ae7c26282f95cf52725f3ca0ca6ffe4ff38d34c29043b580771239872e7ed71e`.
Successful install clients recorded stderr counts of 174 and 196 bytes; their
content is unavailable under the existing count-only capture. No cause or
zero-stderr claim is inferred. The outer process recorded zero stderr. A local
post-run audit's extra zero-stderr assumption was corrected with the failure
retained; no device gate, retry or query changed.
See the [device report](LITERT_WORKER_DEVICE_2026-10-23.md) for raw-record hashes,
complete package-map comparison, closed selection and exact fixture limitations.

M01.01 physical-phone work remains blocked. Existing A/cache/consumption/
preservation holds remain unchanged; no A query, real model/cache operation,
new copy or repair occurred. SDK-visible public lifecycle tests do not establish
actual model cleanup, every hidden native wait/join status, quality, ARM64
execution, sustained performance or two-emulator qualification. Tasks remain
unchecked pending full acceptance and owner merge.

Next runnable product task: trusted model/profile provisioning and app
construction wiring around this paired owner, with recovery that preserves
accepted canon and keeps unknown runtime ownership quarantined. Real-model
initialization/generation requires its separately unresolved admission gates.
