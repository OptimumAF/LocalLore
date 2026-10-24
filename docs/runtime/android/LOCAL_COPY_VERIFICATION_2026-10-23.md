# Authorized local model copies and bounded play experiment, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.03/M01.05;
M01.04 evaluation remains incomplete). Both authorized emulator copies passed
initial full-file identity checks. The sole admitted real-model case failed with
a timeout and committed nothing. A later checksum on target A differed from the
source; its cause is unestablished. Target B's planned control was blocked before
launch by host storage. All inference is held and task acceptance remains pending.

The [structured results](LOCAL_COPY_RESULTS_2026-10-23.json) retain every copy,
case/setup attempt, owner observation and private evidence digest. This follows
the earlier [play verification](PLAY_VERIFICATION_2026-10-23.md), whose
missing-model observations and copy-permission status describe an earlier packet.
This report records the subsequent explicit authorization to copy the already
verified local model into both isolated benchmark caches. It does not revise
those earlier measurements or qualify a production runtime.

## Frozen identity and scope

The actual controller and preserved APK came from clean harness commit
`e7beb858b271aa4636f2f5e7b34deedda1fc3f21`. The APK below differs from the
earlier verification document's build. These observations apply only to this
exact experimental APK, not to later application or archive changes.

| Artifact | SHA256 |
|---|---|
| Local Gemma 4 E2B LiteRT-LM container, 2,588,147,712 bytes | `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c` |
| Preserved opt-in benchmark APK; installed identity matched on A/B | `715a6c4521592256b1ee6e1bf9ec4d0f3f1974dcdde040781269163efbc534a6` |
| `benchmarks/android_play_probe.py` | `2895a279e504db912104f542d7b9761938bec01954e1db89510b34748235a4cd` |
| `benchmarks/android_runtime_spike.py` | `cafc6afa267c98331f4379c36a57c5fcdb5d0cf9e6518bf466629e1a0eced4dc` |

Targets A/B are aliases for two authorized, already running Android 15/API 35
x86_64 emulators with 4,096-byte pages. The package was
`org.locallore.runtimebench.litert`. The existing LiteRT-LM Android 0.18.1 CPU
runtime remained pinned to `bda624851d74be34d4e1f7fac1fc4155939539c7`, with four
threads. The [experimental profile](PLAY_PROFILE_V1.json) retained 4,096 context
tokens, director/narrator limits of 350/220, one permitted repair, a 60,000 ms
native deadline, a 90-second SDK watchdog and a 110-second controller deadline.
No schema, prompt, template, validation, dependency or budget was relaxed.

Operations used only the benchmark app's private model cache and its marked
synthetic probe workspace. No model was downloaded or externally uploaded. No
weights, generated prose, prompts, private paths, transport identifiers or raw
logs are published here. No physical phone or ARM64 execution was measured.

## Copy and case record

The existing bounded helper streamed the verified local file without another
host weight copy. Each successful copy checked source/destination full SHA256
and size, exact installed benchmark APK, prior installed package hashes,
benchmark process absence and terminal transfer clients. Both caches were absent
before provisioning; each destination initially matched the source hash above.

| Operation | Actual result |
|---|---|
| Copy A | Verified source/destination, 2,588,147,712 bytes; guest data free afterward 1,948,651,520 bytes |
| Storage hold after A copy | Host system volume observed full after the transfer completed; attribution unestablished. B copy and inference paused. |
| Copy B | Verified source/destination, same bytes/hash, after coordinator storage relocation and a fresh 8,361,631,744-byte host gate; guest data free afterward 1,905,745,920 bytes |
| A gift, initial | Real model initialized; failed `timeout`; two director admissions, zero narrator calls; revision and receipts stayed 0 |
| A dialogue, initial | Failed `model_identity` setup before instrumentation/model initialization or workspace creation |
| B gift, planned control | Host gate required 4,294,967,296 bytes free; observed 3,024,314,368. Stopped before a device command, case journal or harness call. |

During the storage hold the coordinator relocated known generated build outputs
intact to another host volume and preserved original access paths. The model
source, A cache and other project data were not evicted or recopied. The observed
host-full incident does not establish what changed the A model file.

The A gift controller reported `check_passed=false`, `canon_unchanged=true`,
`reopen_equal=true`, `exact_retry=false` and `owner_drained=true`. One Engine and
two Conversations opened and closed. Timeout cancellation reached a terminal
callback, workers ran off the main thread, the benchmark process was absent,
clients were terminal, and the owned synthetic workspace was removed after
cleanup proof. The SDK's earlier `workspace_retained=true` field describes its
pre-cleanup result; the controller's later `workspace_removed=true` records the
subsequent removal. A dialogue's `workspace_removed=false` means no workspace
was created, rather than an uncollected workspace.

Every admitted SDK role is retained below; unavailable metrics remain null in
the JSON. The report's repair counter was 0 and has not been inferred from the
number of director attempts.

| SDK attempt | Status | Load ms | Generation ms | Input/output tokens |
|---|---|---:|---:|---|
| Director 1 | completed | 3579.945983 | 33713.165071 | 1855 / 350 |
| Director 2 | error: timeout | 0 | 17091.925382 | unavailable / unavailable |

The first role reported schema/thinking/template configuration flags as true;
the second reported false. These flags do not establish semantic acceptance.
The full controller wall time was 82,438 ms, including identity/control work;
it is not an inference-only latency or performance qualification. Cancellation
was timeout cleanup, not the planned first-output cancellation experiment:
`first_output_observed=false`, with zero explicit first-output cancel observations.
No gift, dialogue or narrative-quality success is claimed.

## Later integrity observation and bounded diagnosis

A separate read-only full-file recheck confirmed a same-size A mismatch:
`59d70767f8f7a8710fb2d1427e3cf94917ca5b6847fdbfd11f1fcf2617f0eb4d`.
The host source and unexecuted B control still matched
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
This was an actual checksum difference, not a diagnosis inferred from a command
timeout. Both caches and the original source were retained unchanged afterward.

Eight fixed 1 MiB hash-only samples matched the source in seven positions;
the final MiB differed. Sixteen further 64 KiB samples across that final MiB
all differed and none matched the all-zero-block digest. No weight bytes were
returned. These 9 MiB of sparse observations neither locate every changed byte
nor prove equality of unsampled regions. B was only an unexecuted identity
control, so it cannot establish whether an SDK run would repeat the difference.

Fixed-prefix metadata showed a separate 788,412,736-byte XNNPACK cache on A;
the base model's exposed modification time preceded that cache's by 777 seconds
and matched the copy window. This limits, but does not settle, hypotheses about
when or how the base file changed. No cache was replaced, evicted or repaired.

Pinned official source review found:

- The five-argument Java `EngineConfig` call matches model/backend/vision/audio/
  token arguments; an unset cache directory defaults to the model's parent.
  [Config.kt](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Config.kt)
- Normal memory mapping uses writable `MAP_PRIVATE`; the separate mutable path
  uses `MAP_SHARED`.
  [POSIX mapping implementation](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/support/util/memory_mapped_file_posix.cc)
- The inspected model section loader uses normal `Create`; no `OpenWritable`
  or `CreateMutable` call was found in that loader.
  [Model loader](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/util/litert_lm_loader.cc)
- CPU weight-cache naming adds an identifier and suffix rather than selecting
  the bare model path.
  [Executor settings](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/executor/executor_settings_base.cc)
- The inspected cache identifier implementation reads file size and modification
  time; it does not write the model.
  [File utilities](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/util/file_util.cc)

Two explanations remain hypotheses: host/backend writeback trouble associated
with the full host volume might become visible after an earlier guest-cache
hash read, or an uninspected native runtime path might modify model content.
The inspected source paths do not audit all linked prebuilt AAR behavior. No
experiment isolated either explanation, so neither host storage nor SDK model
mutation is an established cause.

## Commands, evidence and completion limits

Private wrappers selected target aliases and create-only local evidence sinks,
then called the existing APIs. The following records argument sequences with
private wrapper locations redacted; these are not literal runnable paths:

```text
python <private-copy-wrapper> A
python <private-copy-wrapper> B
python <private-case-wrapper> A gift initial
python <private-case-wrapper> A dialogue initial
python <private-case-wrapper> B gift initial
```

The copy invocations called `device.provision_private_model(verified_local_model)`.
The A cases called
`play.run_probe(device, frozen_apk_sha256, "gift", False, retain_raw)` and the
same API with `"dialogue"`. The planned B invocation stopped at its initial host
storage assertion before constructing a device client. No direct controller CLI
invocation or successful B case is implied. Full checksums, sizes, package
identities and hash-only sampling used bounded read-only helper calls. The
existing controller/helper source paths and SHA256 values above identify the
implementation; no new build or dependency installation occurred in this packet.

The JSON identifies 13 retained private evidence files by logical basename,
length and SHA256, including the only actual instrumentation raw capture
(`A-gift-initial.raw.txt`, 2,245 bytes,
`2fdd872b7784d40abe62066ad8807642fd0cf1ea7670abd0657d4e7bcd9f23ac`).
Those raw files remain private. Publishing their digests does not publish or
independently reproduce their contents.

All admitted native/SDK owners drained; all started transport clients were
terminal. Benchmark process absence and prior package APK hashes were checked
at the captured operation checkpoints. This is not a byte-for-byte audit of
every pre-existing save database. Operations did not reset, clear, uninstall or
mutate other apps, and the two devices were explicitly released to the
coordinator. No further device operations were performed for this documentation.

The initial copy gate is satisfied. Stable A identity and the B inference gate
are blocked; M01.03/M01.05 acceptance and M01.04 evaluation remain pending. The
other fixed unlearned/spent/cancel cases and fresh recovery gift were not run.
There is no phone, model-quality, profile-acceptance or production-backend pass.
The next runnable work is read-only integrity investigation and stable host
storage verification while preserving both caches. All inference remains held;
later execution requires fresh coordinator admission and unchanged gates.

Documentation checks validate JSON consistency, all retained evidence hashes,
local links, sanitization and whitespace. They do not rerun builds or devices.
