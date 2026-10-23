# Explicit Android cache-volume harness, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.05), claim
`6370637648`. This is a separate development experiment, not production runtime
selection or evidence of model/device success.

The opt-in package is `org.locallore.runtimebench.litert.cacheprobe`. Its only
declared instrumentation is
`org.locallore.runtimebench.litert.CacheProbeInstrumentation`, targeting that
package. The existing SDK experiment's default package, instrumentation,
`SpikeInstrumentation`, `PlayRunner`, and frozen APK are not replaced. Dependencies
and permissions remain unchanged: the new APK requests no permissions.

## Explicit request and result

Instrumentation extras are `operation` (`inspect`, `mmap`, or `play`),
`volume_uuid` (exact framework FAT UUID or GUID), and `session` (32 lowercase hex
characters). Only `play` accepts `play_case` (`gift`, `dialogue`, `unlearned`,
`spent`, `cancel`) and `profile_base64` (existing bounded Rust profile contract).
The caller selects the UUID; enumeration never chooses a fallback.

The terminal bundle's `cache_result` is JSON with `version:1`, `operation`,
`status` (`completed` or `error`), and a fixed-category `error` or null. An
instrumentation finish alone does not establish a successful operation. No raw
exception, filesystem path, model output, or story prose is emitted.

`volumes` contains framework-discovered metadata: `volume_uuid` (possibly null
for the primary volume), `mounted`, `primary`, `emulated`, `writable`,
`cache_device`, `cache_free_bytes`. Selected `sample` and later `post_sample`
add `userdata_device`, `userdata_free_bytes`, and `cache_bytes`. The latter counts
only this harness's marked session directories, with bounded traversal and no
link following. UUID/device values are private control evidence; public reports
must alias/hash-bind them. Host backing identity, capacity and preservation are
independent controller attestations, not Android measurements.

Selection requires one exact UUID, mounted writable nonprimary nonemulated
storage, app cache and external-files directories on the same device, and a
device distinct from userdata. This does not prove which host image backs the
volume. Writes require at least 2 GiB available there and 1 GiB plus 64 MiB on
userdata. The coordinator's stricter current host/image admission also applies.

`inspect` calls the framework's `getExternalCacheDirs()` and
`getExternalFilesDirs(null)`. These APIs can create or fix package directories;
this operation is **not allocation-free or strictly read-only**. It creates no
session directory, opens no model, initializes no SDK engine and writes no
synthetic probe file.

`mmap` exclusively creates a marked cache child for this session and one
65,536-byte synthetic file. It writes, fsyncs, independently reads and verifies
the file, maps with public `Os.mmap`, unmaps with `Os.munmap`, closes the FD and
removes only that new file. Its `probe` contains fixed booleans for each
completed step, `bytes:65536`, and `mapped_pointer_read:false`. It proves mapping
lifecycle plus independent content verification, not a read through a mapped
pointer. The marker directory remains. Unknown mapping/FD ownership terminates
only this experiment's own process and produces no graceful success result.

`play` opens only `gemma4-e2b.litertlm` in the selected volume's framework-returned
app external-files directory. It does not copy, provision, search for or fall
back to any other model. Canonical synthetic saves remain in a fresh marked
no-backup session child. Immediately before engine construction/initialization,
the adapter repeats UUID/device/capacity/marker checks. The SDK receives the
explicit fresh selected cache directory. Results contain the existing redacted
`play_result` and resource `metrics`, not generated prose. The unchanged Rust
play pump retains its 60-second budget, 350/220 director/narrator limits,
cancellation/drain behavior, and canonical validation. The package watchdog is
90 seconds; watchdog/process termination is not graceful drain evidence.

## SDK and filesystem boundary

LiteRT-LM 0.18.1's pinned
[Config.kt](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Config.kt)
has the eight-argument Java `EngineConfig` constructor used here, including
`cacheDir`; the pinned engine/JNI route it into executor settings. Android's
[app-specific storage](https://developer.android.com/training/data-storage/app-specific)
supports these framework-owned directories without storage permissions.
[Os](https://developer.android.com/reference/android/system/Os) supplies the
explicit mapping and FD lifecycle APIs. No hidden APIs or new dependencies are
introduced. Cache storage is disposable and is not a canonical-save location.

Real-directory, linked-ancestor, fixed-leaf and create-new checks detect ordinary
misconfiguration or stale ownership. They are not immunity to a hostile OS or
same-UID concurrent path replacement. Mounted storage, native SDK cache-file
compatibility, real model quality, FAT32 limits and performance require actual
separate qualification.

## Isolated build and qualification

`cache_build.py --java21 <installed-JDK21> --output <fresh-D-directory>` is the
only build helper for this identity. It uses pinned offline Rust 1.93.1 and NDK
29.0.14206865 to build both current `play-probe` ABIs, explicit D Gradle outputs,
project cache and temporary files, and existing locked dependency caches. It
never cleans or adopts prior output, installs an APK, or invokes a model.
Capacity is rechecked before each bounded job-owned stage. Per-stage logs and
cleanup results stay under that private output. Unknown process cleanup fails
closed; there is no automatic retry. Source revision, actual package/manifest,
zero requested/declared permissions, exact native ABI set/ELF alignment, ZIP
alignment, locked analyzer graph/dependency model and lint are audited before a
separate `verified/cacheprobe-debug.apk` is frozen.

From the repository root, the full reproducible offline build template is:

```powershell
python -B benchmarks/spike/android/litert/cache_build.py --java21 "<installed-JDK21>" --output "D:/<fresh-owned-output>"
```

The output's parent must already be a real directory. The helper creates the
new output itself and refuses an existing directory. It checks all ancestors
for Windows reparse points, not merely the lexical drive. Direct opt-in Gradle
properties also require absolute real D paths. Existing locked compiler/tool
caches remain in use; temporary, project, app and root-project outputs are
explicitly placed on D. Python bytecode output is disabled.

After the coordinator has separately admitted setup, installed the audited new
APK, and verified the intended mounted volume, the operation templates are:

```powershell
adb -s "<explicit-authorized-target>" shell am instrument -w -r -e operation inspect -e volume_uuid "<framework-UUID>" -e session "<new-32-lowerhex>" org.locallore.runtimebench.litert.cacheprobe/org.locallore.runtimebench.litert.CacheProbeInstrumentation
adb -s "<explicit-authorized-target>" shell am instrument -w -r -e operation mmap -e volume_uuid "<same-framework-UUID>" -e session "<different-new-32-lowerhex>" org.locallore.runtimebench.litert.cacheprobe/org.locallore.runtimebench.litert.CacheProbeInstrumentation
```

These templates do not authorize device changes or model execution. A favorable
sample JSON is not authorization or proof of backing identity, model integrity,
or sufficient host capacity. No command stops or replaces the legacy SDK
experiment. `play` requires a separate admitted model-provision/integrity/runtime
experiment; this harness contains no model-copy or provisioning operation.

## Actual host/build evidence

Source `44cd85f7f21b600e1762eceb7007849d0b8948ab` qualified the new APK:

| Check | Result |
|---|---|
| Complete Python SDK-helper test directory | 33 passed; includes 11 new cache-build tests |
| Actual JVM XML | 62 passed, 0 failed/errors/skips; includes 9 CacheVolume cases |
| JVM suites | CacheVolume 9, PlayRunner 10, Request 10, Stream 5, WarmExchange 13, WarmRunner 15 |
| Gradle assembly/JVM/lint/analyzer | 50 tasks executed; successful in 47 seconds |
| Actual Java compiler | 21.0.4; existing Java 17 launcher |
| APK package/instrumentation | Exact new identity and only the explicit cache runner |
| Capability/native audits | Zero requested/declared permissions; exact two-ABI/four-library set; ELF and ZIP 16 KiB alignment; five required Rust play JNI exports per ABI |
| Dependencies/analyzer | Existing binary hashes, exact locked analyzer graph, SDK/Kotlin model, lint passed |
| Frozen APK | 63,598,424 bytes; SHA256 `50e6e60cfdb2194272d31cf651805f34452ae09a04443558049020664f60d107` |

All attempts remain in private task-owned evidence. The first build compiled
both Rust ABIs but failed during Gradle configuration because the `java` extension
shadowed `java.io.File`. The second compiled/audited both ABIs but failed Java
compilation on an incorrect SDK logging-class import. Neither reached JVM tests.
The final Java-only build copied the exact second attempt's native pair into
fresh output, verified hashes/alignment/exports again, and recorded that the
intervening changes touched only this Java/Gradle/build harness: no Rust, Cargo,
fixtures or native-linker inputs changed. It did **not** compile Rust a third time.
The normal CLI above still builds both current Rust ABIs.

An actual isolation gap in the failed builds is retained: Gradle's root-project
problems report used the legacy C checkout output before root-project output was
explicitly redirected. The observed report was 127,166 bytes, SHA256
`8561edc08c5973d589daf3588ac6edb856584b8101dca7e2abd2f3ecec40c748`;
its prior identity is unknown. It was copied/recorded, not deleted. The final
build uses explicit D app and root-project outputs. Two earlier Python attempts
also failed while improving tests/guard error handling; their logs are retained.

No agent-side ADB/device, model read/copy, AVD change, inference or installation
occurred. API 26 source compatibility compiled, but actual runtime qualification
is a separate gate. No Android mapping, cache growth, model correctness,
physical-device or production-runtime success follows from these build checks.
