# Explicit cache-volume experiment, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.05, supporting
bounded M01.03). This is a new development experiment, stacked on unmerged
[#100](https://github.com/OptimumAF/LocalLore/pull/100), base
`91f32dfdeb3267a2c0cd5fd80e6ff6f3f651c441`. It does not change the preserved
715/e7 control or retrospectively pass its storage gate. Full task and owner
acceptance remain pending. The new harness is built and locally checked; one
model-free cache-volume primitive passed on B. A remains capacity-blocked. No
inference or SDK-generated cache compatibility result is established here.

See the [aggregate](CACHE_VOLUME_RESULTS_2026-10-23.json),
[harness/build evidence](CACHE_VOLUME_HARNESS_2026-10-23.md),
[device evidence](CACHE_VOLUME_DEVICE_2026-10-23.md) and
[independent review](CACHE_VOLUME_REVIEW_2026-10-23.md).

## Authoritative storage boundary

The Python policy `benchmarks/android_cache_volume.py`, qualified source
`4e431a808332311ac26e7d48a98dd7210e1252e8`, accepts one exact version1 sample.
It requires a caller-selected exact volume UUID, mounted writable nonprimary,
nonemulated storage and a distinct guest filesystem. A different `st_dev` alone
can be a FUSE view over userdata, so the trusted caller must independently map
the actual guest volume/image to its physical host backing and attest that
mapping. A structurally valid JSON boolean is not evidence of that mapping.
The CLI only assesses supplied samples; it collects no device evidence and
cannot authorize an inference, model copy or ownership recovery.

| Resource | Before an admitted attempt | After known-clean completion |
|---|---:|---:|
| Guest userdata | 1GiB reserve + 64MiB planned writes | 1GiB reserve; net consumption <=64MiB |
| Selected cache filesystem | 1GiB reserve + 1GiB cache allowance + explicit model-copy bytes | 1GiB reserve; net consumption <=1GiB + admitted copy bytes |
| Generated cache bytes | Existing bytes are not free space | Nondecreasing; growth <=1GiB |
| Each host backing filesystem | 4GiB reserve + writes mapped to that filesystem | Reserve retained; net consumption <=mapped writes |
| Evidence filesystem | 10GiB reserve, combined with any mapped writes | 10GiB reserve |

For shared host volumes, the reserve is the maximum applicable floor and growth
is the sum of independent planned writes. Cache and evidence on one host volume
therefore need 11GiB; userdata on that same volume adds another 64MiB. The
sampler must take one free-space measurement per actual host filesystem and reuse
it for aliases; inconsistent same-volume values fail closed. Different drive
names do not prove different backing, particularly through junctions/mounts.
The full model byte count is added when provisioning a new model on the selected
volume, without counting it as generated cache growth. Actual source identity,
exclusive absent destination, staging/rename ownership and later integrity proof
remain separate requirements; this policy does not implement provisioning.

This 64MiB userdata allowance belongs to the new experiment with independently
mapped external model/cache writes. It does not redefine the original 2GiB
userdata/5GiB system-volume policy. All allowances are development budgets, not
proven maxima, quotas or reservations. Post observations include unrelated OS
activity; a negative net delta does not prove causal SDK consumption. Explicit
guest cache-consumption checks also catch writes into a preallocated image that
do not reduce host free space.

Identity includes UUID, guest devices, host mappings and all availability flags.
A changed identity blocks before consumption comparison. Invalid types, missing
or extra fields, boolean-as-integer values and bounded-byte overflow are rejected.
Public metadata omits raw UUIDs, host aliases, private paths, raw results and
exception text. Original objects/exceptions remain available privately to the
trusted caller.

`run_with_admission` fences the whole caller callback. Refused or failed preflight
never calls it; an admitted attempt invokes it once. Unknown process/client
cleanup or any callback exception suppresses every post sample. The caller must
fence later dependent work until ownership is resolved; this one-attempt wrapper
is not recovery or a global backport to old controllers. A separate post verdict
cannot overwrite the original result, promote a failed probe or roll back a Rust
accepted receipt. The callback's result still needs its own gameplay validation.

## Compatibility and evidence

The pinned SDK remains LiteRT-LM Android0.18.1, commit
`bda624851d74be34d4e1f7fac1fc4155939539c7`, CPU. No new runtime or native
dependency is selected. Its official Apache-2.0
[Config.kt](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Config.kt)
defines an explicit writable cache directory. Existing dependency byte locks
remain required by the build audit. Android's
[Context API](https://developer.android.com/reference/android/content/Context#getExternalCacheDirs())
and [StorageVolume API](https://developer.android.com/reference/android/os/storage/StorageVolume)
define framework-owned directories and volume metadata. Directory discovery can
create/fix package directories, so app inspection is bounded setup plus metadata,
not a claim of read-only/no-allocation behavior. Canonical saves never live in
the disposable external cache.

## Verification actually performed

| Command | Result |
|---|---|
| `python -B -m unittest discover -s scripts/tests -p test_android_cache_volume.py -v` | 25 focused passes |
| `python -B -m unittest discover -s scripts/tests -p 'test_*.py'` | 213 passes, including those 25 |
| `python -B -m unittest discover -s benchmarks -p 'test_*.py'` | 140 passes |
| `python -B -m unittest discover -s benchmarks/spike/android/litert -p 'test_*.py'` | 33 build-helper passes at final harness44cd85f; earlier32/33 runs retained |
| Offline Android qualification / actual JVM XML | 62 passed; no failures/errors/skips; includes9CacheVolume tests |
| Lint / actual analyzer and dependency model | 0errors/8warnings; pinned binary/classpath/model audits pass |
| Actual APK/manifest/native audits | Separate.cacheprobe package/runner, zero permissions, twoABIs/fourlibraries,16KiB ELF/ZIP alignment |
| B install + three framework inspections + one wrapped mmap callback | Pass; no model/engine/conversation; A blocked |

These Python checks use original synthetic samples/mocked callbacks, not SDK or
model execution. They cover grouping and double-counted space, exact byte
boundaries, full model-copy accounting, emulated/FUSE refusals, changed identity,
preallocated-image consumption, no-dispatch/one-dispatch ordering, strict cleanup
and preservation of accepted receipts after post failure. Model cancellation,
undrained SDK ownership and post-exhaustion scenarios in these tests are mocks;
no actual SDK/OS failure of those kinds was injected by this packet. Negative
Gradle configuration executions were not run; Python/source guards do not prove
an actual runtime configuration refusal.

## Preserved device preparation

Read-only emulator-console queries resolved the actual selected AVD directories,
which the previous default-home inventory had not found. The running A/B
executables are different: emulator37.2.12 and35.3.12 respectively. Both initially
advertised only private/emulated storage, with effective `hw.sdCard=false` and no
existing SD image. Emulated storage mapped to userdata; it was not extra capacity.

The coordinator reviewed a reversible **B-only** preparation. Exact original
configuration/hardware/registry bytes and hashes were preserved privately. A
fresh exclusive 8GiB image was created on the independently identified host
secondary volume, with capacity checks before creation. B was gracefully stopped
and its single existing SD hardware configuration value enabled; it relaunched
once with the same35.3.12 executable, original flags/environment and new image.
No wipe, userdata path change, resize, snapshot load or format of existing data
was used. The original configuration remains recoverable byte-for-byte; the
current configuration is intentionally different and hardware metadata was
regenerated. The original userdata stayed in place.

During the single bounded startup, the new public volume first reported
unmounted/null UUID, then became mounted during a diagnostic recheck. No manual
mount/format or reboot retry occurred. The mounted public vfat backing, image
size and effective hardware path agree; its FUSE app view is separate from
userdata. Observed external free space was8,573,059,072 bytes and userdata
free1,799,946,240 bytes. These are time-specific observations, not reservations
or proof of SDK cache compatibility.

Both sets of21 original installed APK identities and protected model/cache
metadata matched preflight after this preparation. This is not a full model or
userdata-content integrity claim. Nonzero diagnostic commands and initial boot
polls are retained separately; they are not represented as successful queries.
Final journals contain615metadata/attachment and146app commands:761 completed
with known cleanup,753exit0 and8nonzero. The8 are three stat-format quoting
failures, four initial boot-property poll failures and one unavailable sysfs
read. Initial boot stderr text was not retained, so its exact cause is not
established. Successful mounted-volume queries and final preservation checks
remain separate from those failures. No model was read,
repaired, copied or evicted. A remained unchanged and was not admitted for writes:
its userdata free1,053,560,832 bytes is already below the1GiB reserve. There was
no arbitrary cleanup or reduced reserve to obtain a pass.

The new card and enabled configuration remain attached to B with the private
restoration map retained. The QEMU-created SD overlay is also retained on that
same secondary host volume. The live image, overlay and emulator logs are
explicitly excluded from the immutable evidence index; bounded snapshots and
configuration backups are included. No immutability claim is made for live storage.

The first harness build rebuilt both native ABIs successfully, then failed at
Gradle configuration before Java/JVM tests: the Java extension shadowed a fully
qualified `java.io.File` reference in Kotlin DSL. The fix uses an explicit import.
The same narrow follow-up also canonicalizes the trusted framework userdata
alias, fences descriptor cleanup uncertainty even during exception suppression,
checks resolved Gradle output paths and audits the exact five play-probe JNI
exports. The second attempt rebuilt/audited both ABIs, then failed Java compilation
on an incorrect SDK logging import. Neither failed attempt reached JVM tests.
Final source44cd85f uses the existing working Engine logging API; source-equivalent
integration is018747f219a74cfe19ca79ddb4de73d0881e3ff1. The third qualification
copied the second attempt's audited native inputs into fresh output after proving
unchanged Rust/Cargo/fixture/linker inputs. It rebuilt Java/APK and all62JVM tests;
it did not rebuild Rust a third time. Unstripped input and AGP-stripped packaged
library identities are recorded separately.

Final APK:63,598,424bytes, SHA256
`50e6e60cfdb2194272d31cf651805f34452ae09a04443558049020664f60d107`.
The frozen SDK remains0.18.1/CPU; profile60sec/350director/220narrator is unchanged
and unexecuted. Lint's8warnings are OldTargetApi1, GradleDependency1 and UsableSpace6.
Sampled usable bytes are observations, not reservations or a maximum-cache proof.
No target/dependency policy was silently changed to suppress warnings.

The failed builds also exposed a root-output isolation gap: a127,166-byte Gradle
problems report landed in the legacy checkout output. Its prior identity is
unknown; the observed file was copied/hash-bound rather than deleted. Final
app/root/project/temp outputs are on the separately checked secondary volume.
All build attempts, seven author Python attempts (including two failures),
source/identity corrections and cleanup results remain in the private evidence.

## Actual model-free B operation

Installation used its own512MiB planned allowance, independently of the64MiB
inspection budget. Preconditions were userdata>=1.5GiB, system host>=4.5GiB,
secondary host>=11GiB and APK<=64MiB. Measured net installation consumption was
63,655,936userdata bytes and1,912,832system-host bytes, with reserve floors
retained. These net deltas include unrelated OS activity; they are not causal
installer accounting. Each framework inspection separately checked current
setup capacity and actual attachment identity before its possible directory setup.

The trusted private controller then used the frozen Python wrapper around one
actual mmap callback. The sampler used the app's namespace and independently
proven backing graph, with one host measurement per physical filesystem. Exactly
three inspect operations and one mmap operation ran; no play operation ran.
The instrumentation's own post sample and wrapper's later sample remain separate.

| Wrapper sample | Before callback | After known-clean callback |
|---|---:|---:|
| Cache-volume free bytes | 8,573,046,784 | 8,573,038,592 |
| Userdata free bytes | 1,738,305,536 | 1,738,305,536 |
| System host free bytes | 4,970,168,320 | 4,969,926,656 |
| Cache/evidence host free bytes | 103,778,148,352 | 103,777,955,840 |
| Owned cache bytes | 0 | 34 |

Both verdicts admitted; the callback dispatched exactly once with no callback
exception or unknown cleanup. The65,536-byte synthetic file was written, read and
verified through its descriptor, mapped/unmapped, closed and removed. Only the
34-byte ownership marker remains. **No mapped-pointer or tensor read** was
performed. This proves finite descriptor/mapping lifecycle on this volume, not
SDK cache-file compatibility, model initialization or inference. Engines and
conversations remained zero. No SQLite play/commit operation occurred.

Final package census: A21original identities; B22identities, consisting of the
same21original hashes plus the exact new APK. Protected model/cache metadata
matched, both old/new benchmark processes were absent, selected/inventory ADB
clients were zero and the one server remained. Device/build leases are released;
all issued operations are terminal. No full model hash was refreshed.

The public aggregate binds66sealed device files and84coordinator/build evidence
entries, including original failure logs, actual JVM/lint/analyzer reports,
native-input provenance and private recipe. Counts describe bindings, not a
claim of distinct files across overlapping evidence sets. The private device
index SHA256 is79350e0f99a4d7abae7075e6c2228ece1c2909c546351cd1e3294e3001902d4a;
its sanitized handoff SHA256 is92fa5815136ec9520a7b4f954358c1c592319942ff4d195e56e0895994af2039.
Raw paths, UUIDs, serials, arguments and diagnostics remain private.

## Remaining gates and next runnable task

M01.05 is implemented/locally checked for this bounded B slice, pending owner/full
task acceptance. A's userdata capacity blocks its install/write tests. The original
715/e7 policy and its refusal remain unchanged. M01.01 remains blocked without
an authorized physical phone. Actual ARM64 execution, SDK cache generation,
quality, latency/memory/thermal, sustained sessions and M01.03/.04/.05/.06 full
gates remain incomplete. Cancellation/unknown-owner protections reviewed in the
new adapter are not actual model-failure or OS-descriptor-failure measurements.

Next runnable M01.03/M01.05 work: under this distinct APK/profile, refresh source
model integrity, admit a fresh fixed-leaf copy into B's new app-owned external
files directory including all model bytes in the budget, verify the entire copy,
then run the bounded explicit-cache SDK control with fresh ownership and capacity.
Existing permission for local copies remains valid; it does not establish current
integrity or capacity, permit overwriting A's mismatch, or grant a performance
pass. Preserve all attempts and accepted Rust outcomes; no cloud fallback,
merge, release, access or repository-setting change is part of this packet.
