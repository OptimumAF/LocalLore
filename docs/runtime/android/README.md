# Isolated Android runtime experiment

M01.02 with supporting M01.03/M01.05 preparation. This is development tooling,
outside the Compose application. Both candidate runtimes use local model files
and the existing Rust oracle on two Android15/API35 x86_64 emulators. No backend,
phone tier, prose quality or production minimum OS is selected.
Python on the development host orchestrates ADB and transient IPC; inference and
the Rust oracle execute on the emulator. A standalone gameplay adapter remains
future work.

The new opt-in [current Rust play experiment](PLAY_PROTOCOL.md) exercises the
guarded free-text pipeline through a bounded JNI request pump instead of the
older fixture oracle. Its [dated verification](PLAY_VERIFICATION_2026-10-23.md)
currently establishes build/host and missing-model cleanup only; model-backed
acceptance and active SDK cancellation remain pending. It adds no production
backend or Compose inference dependency.
The separate [compatibility follow-up](PLAY_COMPAT_VERIFICATION_2026-10-23.md)
verifies the captured newer accepted main plus the same experimental source.

The earlier [dated verification](VERIFICATION_2026-10-22.md) and
[all-attempt aggregate results](RESULTS_2026-10-22.json) distinguish successful
turns, cancellation, expected rejection, uncertain cleanup and follow-up checks.
The original Qwen3.5-4B conversion and M01 physical-device gate remain pending.

## Inspect model integrity without inference

The explicit local utility `benchmarks/model_integrity.py` opens a regular model
file read-only and makes two complete passes. It emits only size, whole-file and
ordered 32MiB chunk hashes, plus a before/after identity-stability flag. It does
not run ADB, initialize a runtime, copy/repair a model or change inference gates.
Keep receipts local; inspect status 0 means stable observed reads, not approval of
the model. Compare against the approved source size/hash separately:

```powershell
python benchmarks/model_integrity.py inspect --model <verified-local-model>
python benchmarks/model_integrity.py compare --reference <source-receipt.json> --observed <observed-receipt.json> --expected-bytes 2588147712 --expected-sha256 181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c
```

The second command exits 0 only for a complete stable identity match, 2 for a
stable content/size mismatch, 1 for incomplete, malformed, changed or failed
inspection. The library accepts complete device hash receipts collected under
separate authorized process/package/transport guards. A full-file digest is a
separate observed read; it cannot be reconstructed from the list of chunk hashes.
Different chunk digests identify intervals containing differences, not an exact
changed-byte count or cause. This trusted-local check does not defeat adversarial
filesystem races, force backend writeback, or establish historical integrity.
Leaf symlinks are refused; ancestor links are not comprehensively audited.
The [dated investigation](MODEL_INTEGRITY_VERIFICATION_2026-10-23.md) records
actual device observations, retained failures, storage gates and limitations.

## Admit a play control

For a new real-model play control, use the explicit
`android_probe_admission.run_play_probe_with_admission` entrypoint around the
entire existing controller, including its initial SDK stop. Its trusted sampler
must collect fresh, bounded, read-only measurements with exact fields `version`
(1), `host_free_bytes`, `evidence_free_bytes`, `guest_free_bytes`, `cache_bytes`.
The caller still owns fresh model/APK/process identity and exclusive device
admission. This wrapper does not change legacy direct `run_probe` callers.

The fixed development policy requires host 4GiB reserve plus 1GiB growth,
guest 1GiB reserve plus 1GiB growth, and 10GiB evidence space before dispatch.
After a known-clean controller return it checks remaining reserves and the
1GiB observed cache/net host/net guest consumption budgets. These are admission
and later observations, not filesystem quotas or a proven SDK cache maximum.
Unknown cleanup or a raised probe suppresses the post sampler; callers must also
suppress other dependent device probes until ownership is resolved.

For policy assessment of an already captured local sample only:

```powershell
python benchmarks/android_probe_admission.py --sample <private-storage-sample.json>
```

Exit 0 means that sample meets the policy, 2 means insufficient headroom, and 1
means an invalid/failed sample. The CLI neither measures freshness nor dispatches
a probe. The guarded Python entrypoint samples at its call boundary. Its
`storage_checks_passed` describes storage only: keep the original probe result,
accepted receipt or exception separately, and require the original probe checks
plus independent post-model identity for experiment acceptance. A post-storage
failure cannot roll back an accepted turn. See
[dated qualification](CACHE_ADMISSION_VERIFICATION_2026-10-23.md) for actual
refusals, preserved data and the cache-placement prerequisite.

## Build explicitly

Use the existing pinned Rust1.93.1, NDK29.0.14206865, SDK36/BuildTools35,
CMake3.22.1, JDK17 and cached Gradle8.11.1 dependencies. LiteRT's isolated Java
compiler additionally needs an already installed JDK21. The official AAR is
classfile65; the production Kotlin/Java toolchains are unchanged.

```powershell
python scripts/check.py host --offline
python benchmarks/spike/android/controller/build.py --sdk $env:ANDROID_HOME
python benchmarks/spike/android/llama/build.py --sdk $env:ANDROID_HOME --source <pinned-llama-source>
python benchmarks/spike/android/litert/build.py --java21 <existing-jdk21> --offline
```

The llama source must be exactly `620d2225cc436ab0b001e3200e590e3b286ef9ab`.
Build scripts do not download it, install SDKs, operate devices or load weights.
The isolated LiteRT project pins a newer, separately audited analyzer while
retaining AGP and the production toolchain. Its normal build now returns zero
only after assembly/D8, fourteen JVM tests, APK checks and actual SDK/Kotlin
dependency analysis pass. `--probe-incompatible-analyzer` deliberately uses the
original analyzer and must return **2** for its reproduced metadata failure.
See [analyzer compatibility and limitations](LITERT_ANALYZER_2026-10-22.md),
[SDK sources/build](LITERT_SOURCES_2026-10-22.md) and
[native build](LLAMA_BUILD_2026-10-22.md) for exact pins, hashes and licenses.
No model weight, compiled runtime or APK belongs in Git.

## Run only on authorized targets

Choose one authorized target and repeat on the second. The controller requires
an explicit `--serial` argument; use its local transport ID, never publish it.
Install only the source-built isolated SDK APK, selecting the target explicitly:

```powershell
adb -s <authorized-target> install -r -t benchmarks/spike/android/litert/app/build/outputs/apk/debug/app-debug.apk
```

The model files must match the publisher hashes recorded by the
[host spike](../spike/README.md). Set local paths for these arguments:

```powershell
python benchmarks/android_runtime_spike.py --runtime llama --adb <adb> --serial <authorized-target> --owner target/android-runtime/controller/remote-owner-x86_64 --binary target/android-runtime/llama/x86_64/host-helper/locallore-llama-spike --oracle target/android-runtime/llama/rust/x86_64-linux-android/release/examples/runtime_spike --model <verified-qwen-gguf> --output target/android-llama.json
python benchmarks/android_runtime_spike.py --runtime litert --adb <adb> --serial <authorized-target> --owner target/android-runtime/controller/remote-owner-x86_64 --binary unused --oracle target/android-runtime/llama/rust/x86_64-linux-android/release/examples/runtime_spike --apk benchmarks/spike/android/litert/app/build/outputs/apk/debug/app-debug.apk --model <verified-gemma-litertlm> --output target/android-litert.json
```

`--cancel-after 3` exercises parent-requested process termination and requires a
fresh run afterwards. `--case spent` / `--case unlearned` stop at Rust preflight
before model provisioning or generation. For SDK-specific checks, use
`--sdk-mode metadata`, `missing`, `corrupt` or `cancel`. The latter waits for a
real streaming callback, cancels, drains the terminal callback, closes both
owners and reloads a fresh engine; it is a separate API check, not a story turn.
The SDK may report `generation_failed` for an oversized context; no tokenizer
preflight API is invented. Current CLI process status and `worker_status` are
separate fields; a completed diagnostic process can report an expected model error.

The first valid request copies/hashes files only into the owned benchmark
directory or the isolated package's private files. Gemma provisioning streams
binary bytes through `adb exec-in`, verifies the full device SHA256, then renames
the private staging file. Transfer output is discarded; no model bytes enter
Python memory or public logs. Existing mismatched cache/package identities fail
closed. Provisioning reserves at least 1GiB free storage; do not exhaust a device
to simulate failure. The coordinator removed its verified Qwen cache before
provisioning the larger Gemma model. The benchmark APK and private Gemma files
remain on the two selected emulators for subsequent explicit experiments.

## Exercise control failures without inference weights

Install the exact source-built isolated SDK APK first, then run explicitly:

```powershell
python benchmarks/android_control_probe.py --adb <adb> --serial <authorized-target> --owner target/android-runtime/controller/remote-owner-x86_64 --oracle target/android-runtime/llama/rust/x86_64-linux-android/release/examples/runtime_spike --apk benchmarks/spike/android/litert/app/build/outputs/apk/debug/app-debug.apk --output target/android-control.json
```

Repeat on the second authorized target. This issues actual native/SDK operations
and six deliberately injected host-control failures, checking fail-closed results
and fresh recovery; three additional corrupt-file SDK diagnostics need no model
weights. Every attempted check is retained before recovery. Successful fault
assertions are not successful generations. No ADB invocation enters default
checks. The [control verification](CONTROL_VERIFICATION_2026-10-22.md) preserves
the earlier unexplained transients separately from this follow-up.

## Bounds and authority

The separate [cache-volume experiment](CACHE_VOLUME_VERIFICATION_2026-10-23.md)
adds an opt-in cache destination and a volume-aware policy. It has a different
package/artifact identity; it is not the original installed SDK control. Keep
its model and generated cache on an explicitly selected framework-returned
independent volume, with canonical saves in app-private userdata. No automatic
internal-directory fallback is allowed. Merely choosing an external-looking
path does not prove independent storage.

For policy assessment only:

```powershell
python -B benchmarks/android_cache_volume.py --sample <fresh-private-storage.json> --volume-uuid <exact-selected-uuid> --model-copy-bytes 0
```

Exit0 means the supplied sample meets this experiment's budgets; exit2 means a
policy refusal and exit1 means invalid/failed input. This command does not collect
evidence, start a controller, provision weights or authenticate a backing-volume
assertion. The trusted caller must map actual guest/host filesystems and sample
once per host filesystem, preserving fresh APK/model/owner evidence separately.
`run_with_admission` wraps one whole callback with pre/post observations; unknown
ownership suppresses every post read and must fence later dependent work. Preserve
the original result/accepted receipt independently of the storage verdict. The
new budgets do not retroactively pass the old userdata/host admission gate.

The [explicit-cache SDK controller](CACHE_SDK_CONTROL_HARNESS_2026-10-23.md)
keeps artifact identity, model integrity, accepted play receipts and storage
verdicts separate. Its strict decoder preserves a valid committed receipt even
when a later volume or cleanup check fails. A new app-domain
[`verify_model` operation](CACHE_MODEL_VERIFY_HARNESS_2026-10-23.md) reads only
the fixed model leaf in the framework-selected external-files directory, through
one no-follow descriptor. This closes the gap between shell provisioning and
the file the app actually reads; `run-as` access is not a substitute. It creates
no SDK engine and returns no model text or filesystem path. Use the separately
qualified artifact and trusted live callbacks described in those documents;
default checks do not provision models or run devices.

The [explicit-cache control verification](CACHE_SDK_CONTROL_VERIFICATION_2026-10-23.md)
records the qualified app-domain integrity operation, actual local model-copy
checks, retained transport/setup failures and the bounded emulator observation.
Its aggregate keeps accepted Rust receipts separate from storage and cleanup
verdicts. The actual gift request was rejected by the action intent guard with
unchanged canon; typed canonical events remain authoritative.

The native [process owner](../../../benchmarks/spike/android/controller/README.md)
owns/reaps one trusted direct child. An ADB-client exit is never native cleanup
evidence. Package termination is limited to the hash-verified isolated SDK app;
its reviewed manifest/runtime uses a single process and threads, not arbitrary
descendants. Unknown or disconnected cleanup remains unverified. Do not reuse
this controller as a sandbox for arbitrary programs.

The cold entrypoint above uses a fresh process/engine per role. The separate
[warm exchange](WARM_VERIFICATION_2026-10-22.md) retains one Engine across fresh
director/narrator Conversations, with Rust validation between them and verified
shutdown before commit. Run it explicitly on authorized targets:

```powershell
python benchmarks/android_warm_spike.py --adb <adb> --serial <authorized-target> --owner <built-native-owner> --oracle <built-rust-oracle> --apk <frozen-source-built-sdk.apk> --model <verified-gemma-litertlm> --output target/android-warm.json
```

Use `--cancel-after 8` for cancellation, then a new invocation for fresh-session
recovery. Its [versioned private protocol](WARM_PROTOCOL.md) is development IPC,
not a gameplay or SQL API. All attempts and exact limits are retained in the
linked report. No warm multi-turn session or phone performance is qualified.

One model is active at a time. Director<=350/narrator<=220 tokens, 4096 context,
four CPU threads and the shared 60-second turn budget are development limits.
Hashing/provisioning are outside inference timing; OS file cache and host load
are uncontrolled. Independent native/Java watchdogs bound abandoned work, but
an uninterruptible kernel task cannot promise graceful reclamation.

Only an accepted director proposal reaches the narrator. Rust on the emulator
checks exact narration, commits one event, retries idempotently and verifies
recipient/absent-observer context. Oracle processes reconstruct an ephemeral
fixture, so this is no durable or Compose-integrated inference proof. Model text
is transient IPC only; public reports contain fixed categories and numeric/bool
metadata. Default host checks use synthetic fixtures/mocks, never models or ADB.
