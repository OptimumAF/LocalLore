# Guard-bound Android SDK integration, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5), M01.03/M01.05 partial,
claim `6373018837`. This packet is stacked on unmerged
[#108](https://github.com/OptimumAF/LocalLore/pull/108). That artifact's real
`Agency` rejection remains a failure; its generated command was not retained
and its specific cause remains unestablished.

## Accepted prerequisite and precise source

Inspection found that owner-merged [#104](https://github.com/OptimumAF/LocalLore/pull/104)
already fixes the mismatch between the finite intent guard and the director
schema. This packet carries that accepted code into the experimental Android
SDK stack. It does not reimplement the guard or claim that the old response is known.

Source `ba31932665eab2079c54a02a0182857f598fa0c4` combines #108 head `b85d1d4`
with exact original implementation `5138427`, pre-change captured Play v2.2
receipt `43bc8cb`, and independent core tests `f2adbd5`. Independent Git-blob
comparison verified all six carried files against those original commits.
A trial merge of accepted main was clean but would import 235 unrelated paths;
it was aborted before committing. This is the stated narrow source combination,
not qualification of all current-main desktop/storage changes.

The same action Command that passes Engine preflight constrains the director
and repair grammar. Actual provider bytes are still parsed, intent-checked and
mechanically validated; no expected proposal or effect replaces output. Supported
finite English gains no new meaning. Fresh prompt2.3 is required; recorded
2.1/2.2 histories retain strict restore/replay/fork/exact-retry compatibility.
Dialogue, narration policy, engine authority and profile budgets are unchanged.

The new [public bridge tests](GUARDED_SDK_BRIDGE_TESTS_2026-10-23.md) exercise
this grammar through actual ProbeRegistry/Host byte operations using explicitly
synthetic replies: exact arguments, rejected substitutions, identical repair
grammar, cancel/close ticket ownership, noncanonical preparation, durable gift,
retry/reopen, inventory and observer boundaries. Their original author failures
and corrections remain documented. Fake responses do not qualify LiteRT-LM.

## Artifact and compatibility

The new APK is **63,650,552 bytes**, SHA256
`0cf4c253c41483973fd1578837d0ba147a7ed3d6d6cd8eb5818a989e185c09dd`.
Both native libraries were freshly compiled from the stated source with
Rust1.93.1/NDK29.0.14206865 and the development `play-probe` feature. Raw inputs:

| ABI | Bytes | SHA256 |
| --- | ---: | --- |
| x86_64 | 7,672,232 | `515e4d25c99b0b428203407c1c6671784827fa16352b3f6348f1ae5dd6719f62` |
| arm64-v8a | 7,519,000 | `f6a3f1714557658cb321d63da6163191f1d07e574b72d2c818a4571db81cda9a` |

These unstripped inputs differ from AGP's packaged stripped-library hashes;
the build result binds those separately. JNI exports, both ABI/16 KiB ELF and
ZIP alignment, zero-permission manifest, dependency and analyzer audits passed.
Actual fresh Java qualification passed **73 JVM tests**, zero failures/errors/skips;
lint had zero errors and nine existing warnings. Java source was unchanged from
#108; no runtime/model/dependency upgrade or production backend selection occurred.

LiteRT-LM remains Android0.18.1 at `bda624851d74be34d4e1f7fac1fc4155939539c7`.
The official pinned [ResponseFormat implementation](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/ResponseFormat.kt)
accepts a JSON-schema string; its Kotlin constructor checks JSON syntax, not all
native schema-feature support. The pinned [Apache-2.0 license](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/LICENSE)
was rechecked. Earlier llama converter tests are not Android LiteRT compatibility
proof. Actual SDK behavior must be measured with this new artifact.

`android_cache_control` retains the old `04eef96b...` pin and adds exactly this
second qualified pin. Each lifecycle owns a read-only selected identity; initial,
post-model and final checks all require that same APK. Both recognized hashes
cannot substitute for each other during a run. Unknown hashes are refused before
sampling or device operations. The selected hash also binds the worker/profile
manifest. Existing helper clients default to the old pin; new trusted callbacks must use
`_Client(device, apk_sha=GUARDED_APK_SHA256)` explicitly. No runtime-selectable
path, model-generated artifact ID, generic configuration override or silent
fallback was added. Five original artifact tests cover these distinctions.

## Actual host checks and retained failures

On Windows with Rust/Cargo1.93.1, locked/offline dependencies, separate D: output
and temporary roots, debug information and incremental compilation disabled:

```powershell
cargo test --workspace --features locallore-android/play-probe --locked --offline
cargo clippy --workspace --all-targets --features locallore-android/play-probe --locked --offline -- -D warnings
cargo fmt --all -- --check
python -B -m unittest discover -s scripts/tests -v
python -B -m unittest discover -s benchmarks -v
python -B -m unittest discover -s benchmarks/spike/android/litert -v
```

The final integrated workspace passed **423 tests**, zero failures and four
existing explicit ignores. Strict Clippy and formatting passed. Python passed
**264 script**, **140 benchmark**, **33 SDK-helper** tests; SDK helpers used
their required D: temporary root. Focused cache selection passed **76**, overlapping
the script count. An earlier 418-test source-only workspace pass preceded the five
new bridge cases; it is not an additional independent integrated cohort.

The first new artifact test run had one fixture setup error from passing an
already-defined sample keyword twice; the corrected run passed all 76. No product
policy was changed to correct that test.

Two private qualification launcher errors started no build: an unsupported `cwd`
argument and an outer deadline beyond the runner's supported maximum. The actual
documented build then reached its 180-second native-stage timeout with confirmed
cleanup. All logs and partial compiler outputs were retained. One identical-command
continuation used only that owned Cargo target and the same source/per-stage bounds:
x86_64 completed in 24,734 ms, ARM64 in 155,375 ms, then Java and all artifact audits
passed. No timeout or gameplay budget was increased.

After writing both the successful qualified build result and continuation result,
the private wrapper's final print used the wrong metadata key (`sha256` instead
of `apk_sha256`) and exited 1. That reporting failure is retained. Independent
artifact/hash/XML/stage readback verifies qualification; it is not called a
successful launcher exit, and no rebuild or inference retry was performed for it.

## Actual guarded SDK attempt

The qualified APK updated only the authorized isolated package on emulator B,
preserving its UID, app data, model and prior cache metadata. Two full host-model
passes and an app-domain full hash verified the existing 2,588,147,712-byte model,
SHA256 `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
The controller and trusted adapter bound the new APK throughout this lifecycle.

Exactly one gift attempt returned only `shortMsg=Process crashed.` and
`INSTRUMENTATION_CODE: 0`, without a cache/play result. The strict controller
correctly reported `invalid_terminal` at `terminal_parse`, `check_passed=false`.
Its 97,719 ms wall interval is not complete-turn latency. SDK generation,
schema acceptance, owner balance and the canonical outcome cannot be inferred
from this terminal. There was no inference retry.

Pre/post storage admission passed separately. Cache bytes grew from 788,412,804
to 1,576,825,574; cache growth does not prove generation success. Prior caches
were retained, while the new run used its fresh per-session cache path. This
does not qualify compiled-cache reuse or controlled cold-start performance.
Final package absence and host-client cleanup were known. Model re-verification
used a separate zero-SDK operation; its counters do not establish SDK cleanup
inside the crashed process. See the [device report](GUARDED_SDK_DEVICE_2026-10-23.md)
for read-only recovery, preservation and final evidence.

The one bounded read-only recovery cohort stopped at its binary transport
control: 1,101 bytes arrived where 262 exact bytes were expected, despite a
zero client exit and known cleanup. No source database metadata, hash, copy,
SQLite open or crash-log read followed. The controller did not relax transport
validation or retry inference. The canonical outcome and crash cause remain
unknown. A later diagnostic packet must first qualify exact transport bytes
before inspecting the retained session; no blind replay or new generation is
authorized by this result.

The recovery helper retained the mismatching output's length/SHA256 and client
status/cleanup metadata, but did not save the actual 1,101-byte payload. This
logging gap limits transport diagnosis; no retry was made to replace that
attempt. The original SDK crash terminal itself was retained in full.

Private immutable host evidence binds 66 selected logs/artifact files,
79,096,924 bytes, index SHA256
`07f87229f0187228f38cd036941023fa5fbc59733d9f52197b419e6cee226528`.
The bridge author index binds 25 files, 15,309 bytes, SHA256
`629d920b6daec7d9f1bd89a52f15908eeea620d9e48ed21f4a1e8eb154eeb028`.
Both selected sets were independently rehashed. These bindings retain local
evidence; no private payload, model weights, session identity or diagnostic
log is published. The [safe aggregate](GUARDED_SDK_RESULTS_2026-10-23.json)
and [independent review](GUARDED_SDK_BRIDGE_REVIEW_2026-10-23.md) separate host
passes from the failed actual run.

## Device gate and remaining work

The fixed experiment remains CPU4, 4096 context, 350/220 role tokens, one repair,
60,000 ms turn budget, 90-second app watchdog and 110-second instrumentation bound.
The existing model hash and bytes are unchanged. A remains outside write/inference
admission unless fresh evidence changes that gate. No physical-phone, ARM64 execution,
quality, sustained memory/thermal or full M01 acceptance follows from host/build tests.
New device observations and ownership/storage verdicts are recorded separately;
the old artifact's failure and all earlier private payloads remain preserved.
