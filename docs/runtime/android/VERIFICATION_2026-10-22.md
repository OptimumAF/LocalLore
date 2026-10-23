# Android candidate runtime verification — 2026-10-22

M01.02 Android slice, supporting M01.03/M01.05 preparation; [ticket #5](https://github.com/OptimumAF/LocalLore/issues/5).
Baseline main `2c095ea` includes the accepted host spike. This packet is a separate
development experiment, with no production app inference dependency or backend
decision. M03.03 follow-up #35 remains independent. No merge was performed.

## Actual execution

Both selected targets are sdk_gphone64_x86_64, Android15/API35, 4KiB pages. ADB
inventory at handoff has five emulators and zero physical phones; three emulators
were untouched. Host is Windows x86_64 with Rust1.93.1, NDK29.0.14206865,
CMake3.22.1, Gradle8.11.1, AGP8.10.1 and JDK17.0.6. The isolated SDK compiler uses
the already installed JDK21.0.4; production toolchains remain unchanged.

| Cohort, retained separately in the result artifact | Observed result |
|---|---|
| Native process ownership suite, eight cases per emulator | Sixteen passed; success, pre-release cancellation, ignored TERM/KILL escalation, nonzero exit, failed exec, lost ADB client, independent deadline and blocked output |
| llama.cpp/Qwen3-0.6B core turn requests | Four committed gift/reload turns; two pending cancellations; four spent/unlearned preflight rejections with zero model roles |
| llama native boundary requests | Missing, corrupt and long-context rejection on both targets; six rejected workers, all reaped |
| LiteRT-LM/Gemma E2B core turn requests | Three committed turns, two forced cancellations, one oracle startup failure before model invocation |
| SDK cooperative cancellation/reload | Passed on both: cancellation after a real streaming callback, terminal callback drained, cancelled text discarded, two engine/conversation owners closed, fresh engine generation completed |
| SDK metadata/missing/corrupt initial checks | Metadata and missing-file checks passed on both; corrupt returned `model_invalid` on B; A initially reported unverified cleanup |
| Explicit follow-ups | A corrupt-file retry returned `model_invalid` with verified cleanup; long prompts returned bounded `generation_failed` with balanced owners on both; fresh oracle startup passed on both |

The Rust fixture, proposal validation and final commit oracle execute on each
emulator, not only on the host. Every committed turn checks revision1, one event,
exact retry unchanged, recipient observation1 and absent observer0. All seven
committed turns across the two candidates satisfy those checks. Each oracle
invocation reconstructs an ephemeral fixture; no durable save or production
Compose inference integration is claimed.
The Python coordinator still runs on the development host and orchestrates ADB;
these are synthetic development checks, not standalone Android gameplay.

The llama core cohort contains ten turn requests / ten attempted roles; the
four preflight rejections make no model call. Its six separate boundary requests
are additional worker invocations. SDK core has six turn requests / eight
attempted roles, plus separately recorded metadata/invalid-file/cooperative
requests. Do not combine these into a model quality or success-rate ranking.

The [all-attempt result artifact](RESULTS_2026-10-22.json) retains sixteen llama
cohort records, fourteen SDK cohort records, five follow-up observations and
both the initial and committed-entrypoint controller checks. Initial failures
remain failures even though later checks passed. Source/native/API artifact
identities and independent reviews are linked from [run instructions](README.md).
No generated prose, private exception, local model path, device transport ID or
hidden reasoning is published.

## Ownership and failure findings

The C owner releases a checked launch barrier and supervises exactly one trusted
child without blocking on its pipes. Only that native parent signals its unreaped
child, preventing PID reuse from redirecting a signal. It records completion
only after reap. The host separately verifies the original owner is gone and
its ADB client cleaned up. Native deadlines worked even when the client was
terminated or output blocked. Both helper ABIs also retain a constructor that
resets/unblocks SIGALRM and arms 90 seconds before main; ELF/disassembly checks
prove installation, but that particular 90-second alarm was not timed separately.

The SDK APK has zero requested permissions, one process and a background
instrumentation worker. Before package termination the coordinator hashes the
installed APK and compares it with the reviewed build. Force-stop applies only
to that isolated package; PID absence proves process termination for this reviewed
single-process experiment, not arbitrary descendants. A separate Java watchdog
bounds abandoned execution at 90 seconds; its firing was not separately timed.

Cooperative SDK checks report cancel-call return, terminal callback, balanced
owner counts and fresh reload separately. They do not prove instantaneous native
heap release. Main processed hundreds of heartbeat callbacks during the checks;
that is worker/UI-thread evidence, not a Compose interaction latency benchmark.
SDK-visible channels and literal thinking tags are rejected. Per-content channel
metadata may be lost by the public SDK mapping, so no generic semantic
hidden-reasoning filter is promised.

Independent tests first reproduced false acceptance after nonzero exit or failed
cleanup, lost attempt accounting on exceptions, directory-cleanup exceptions,
malformed oracle handling and private transfer cleanup errors. Fixes reject
those outcomes, preserve attempted roles, separate process/directory cleanup,
use strict JSON and discard transfer diagnostics. Twenty reviewer tests and
eight coordinator tests cover these boundaries using synthetic processes/mocks.
One new test initially assumed microsecond Windows clock resolution; a controlled
clock corrected that test harness assumption before the final host gate passed.

Actual development mistakes are retained separately: fixed marker parsing needed
LF/Windows-ADB CRLF handling; two initial helper invocations omitted `--model`
and were rejected before generation; an approved APK changed during private
model provisioning and the identity gate refused the next step. The final APK
is `a74b05b9123d43fda42989814cd57f9a27b95dac44bd66445ac1208250710f25`.
Both model files passed full publisher SHA256 checks after transfer.

Two reliability observations remain unresolved: the initial SDK corrupt-file
cleanup could not be verified, and an initial oracle startup failed. The latter
left an empty setup directory; no owner/done record was present there. Later
explicit package stop/reload and oracle checks passed. Final cleanup confirms
the isolated SDK package is stopped and no owned native benchmark process remains
on either target. No unknown live process was signalled, and only known files or
empty UUID directories were removed. Passing retries do not explain the original
transients or establish sustained reliability.

## Builds and checks actually run

| Command/procedure | Result |
|---|---|
| `python scripts/check.py host --offline` | Passed:39 Rust tests (26 domain/8 FFI/5 example),116 Python tests,4 fixture comparisons,3 linker tests, format/Clippy |
| `python scripts/check.py android --offline` | Production app/test APKs, both Rust ABIs,30 JVM tests, lint and permission/ABI/ELF/ZIP audit passed; no production runtime added |
| `python benchmarks/spike/android/controller/build.py --sdk <installed-sdk>` | Both ABIs built with `-Wall -Wextra -Werror`, PIE and16KiB alignment; system dependencies only |
| `python benchmarks/spike/android/llama/build.py --source <pinned-source> --sdk <installed-sdk>` | Both helper/oracle ABIs built;13 source/ELF/constructor tests passed; ARM64 not executed |
| `python benchmarks/spike/android/litert/build.py --java21 <existing-jdk21> --offline` | Actual assembly/D8,14 JVM tests, dependency hashes, zero-permission/two-ABI/16KiB APK audit passed; deliberately exit2 for incomplete lint dependency analysis |
| `python benchmarks/spike/android/controller/smoke.py ...` per selected emulator | Eight checks each passed through the committed entrypoint; original manual controller checks retained separately |
| `python benchmarks/android_runtime_spike.py ...` and its public Device/NativeWorker/SdkWorker APIs | Full cohorts above; expected diagnostic CLI missing-file check returns exit0 with `worker_error=model_missing`, never an accepted turn |
| `git diff --check` | Passed |

Exact build recipes and runtime arguments are in [README](README.md),
[native build evidence](LLAMA_BUILD_2026-10-22.md) and
[SDK build evidence](LITERT_BUILD_2026-10-22.json). Agent builds used separate
worktrees with identical integrated source; APK hashes identify the actually
installed bytes. Default host tests never install dependencies, load models,
invoke ADB or modify emulators. Hosted Actions were not executed by this packet.

The Kotlin SDK AAR uses Java21 classfile65 and Kotlin2.4 metadata. Existing JDK21
compilation targeting Java17 plus D8 succeeds. The pinned AGP8.10 analyzer expects
older metadata; although its issue report says no issues, the build helper
deliberately returns2 and records incomplete dependency analysis. No compiler
upgrade, downgrade or metadata rewriting is hidden in the production app.
The AAR's third-party notices span multiple license families; SDK/native/model
redistribution requires further review, not merely the POM's license label.

## Scope limits and next work

Each role uses a fresh engine/process; OS file caches and host load are
uncontrolled. Different model sizes, templates and samplers prevent a fair
comparison. The narrator copies an exact accepted description; engaging prose,
repair rate, blind quality, warm role reuse, sustained peak memory/thermal,
physical phones, API26/28/36 execution and16KiB OS behavior remain unmeasured.
The Qwen3-0.6B smoke artifact does not replace original Qwen3.5-4B conversion.

M01.01 remains blocked on an authorized physical phone. M01.02 Android slice is
for review; full M01.02–M01.06 remain unchecked. M01.03/.05 have partial evidence,
not full acceptance. Next runnable work is to instrument/reproduce the two
transient control failures, resolve the isolated SDK lint compatibility gate,
then exercise a warm shared-model role session. Backend/support selection still
requires the physical-device and owner-approved quality/performance gate.

Coordinator owns central contracts, device operations and integration. Independent
llama, SDK and reviewer agents used separate worktrees and exclusive paths; their
claims are handed off to PR review. Material AI assistance is recorded here.
No merge, release, settings/access/protection change, private-story upload or
model-weight publication occurred. The SDK APK/private Gemma cache remain only
on the two selected emulators for subsequent explicit experiments.
