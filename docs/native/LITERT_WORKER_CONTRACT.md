# LiteRT worker candidate contract

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 prerequisite
and M05.04 supporting; [#5](https://github.com/OptimumAF/LocalLore/issues/5),
M01.02 supporting. This is an opt-in debug candidate, not a production runtime
selection or reference-phone qualification. It depends on the
[external workspace owner](EXTERNAL_INFERENCE_OWNER_CONTRACT.md).

## Trusted construction and authority

`LiteRtWorkerConfig.createOwner()` constructs the native profile and concrete
`LiteRtRoleWorker` together. Configuration supplies the existing model/cache
paths, expected model bytes and SHA256, provenance hashes and bounded budgets.
The model cannot select these inputs. The fixed SDK revision is
`bda624851d74be34d4e1f7fac1fc4155939539c7` (LiteRT-LM 0.18.1).
The profile retains the existing `android-litert-play-probe-v1` wire identity;
complete provenance and budgets distinguish the concrete configured owner.
Configured-native-owner status and `loaded=null` do not prove successful load.

Before allocating an SDK engine, the worker checks existing confined canonical
paths, exact size, complete SHA256 and post-read file metadata on IO. It creates
no directories, downloads, copies, fallback provider or model. Trusted expected
hashes establish equality to configuration; they do not independently establish
publisher identity. Path-based SDK opening cannot authenticate hostile OS file
replacement after verification. Original saves and previous benchmark caches
are outside the candidate fixture scope.

Rust owns scope/branch/revision/turn identity, context construction, schema,
proposal validation and canonical commit. Kotlin forwards the exact prompt,
schema and request token budget, with the trusted context limit and four CPU
threads. It implements no inventory, progression, epistemic or story rules.

## SDK lifecycle

One initialized Engine serves fresh sequential director/narrator Conversations
within a turn; each turn closes that Engine. Automatic tool calling, tools,
channels, thinking and speculative decoding are explicitly disabled. JSON
response format receives the original Rust schema. SDK-exposed wrong roles,
non-text content, channels, tool calls, invalid UTF-16, oversized cumulative
UTF-8 and thinking tags fail closed. Output is bounded to 16,384 UTF-8 bytes.

The SDK privately normalizes roles and drops some raw content kinds before
callbacks. Checking exposed Message fields is not lossless raw-native content
validation or a guarantee against hidden reasoning. Rust remains the authority
for consequential output. Narrative quality requires separate real-model tests.

Preparation, initialization, send, cancellation and close run off Main.
The adapter counts callback bodies and waits for terminal callback, returned
send and cancellation operations before reporting drain. Calls cannot overlap
role/Engine close or reuse an uncertain owner. Partial open/start errors retain
unknown resources; a timeout or cancelled waiter is not proof of teardown.

Uncertainty is sticky across subsequent initialization attempts. The paired
factory immediately fences its same application owner when an observed late
callback or other uncertainty arrives, including after a previously returned
Ready. Native invalidation runs asynchronously; scheduling it is not completion.
Accepted commits that already won remain canonical. Neither a stale callback
nor cleanup failure can trigger scripted inference or another commit attempt.

A successful public SDK close is the adapter's observable close contract.
The pinned native implementation destroys owned pools and invokes joins, but
public close does not expose every native wait/join status. Zero callback-body
count is not evidence about the later JNI callback epilogue. Synthetic resource
tests do not establish active-model/native ownership qualification. Real-model
admission and measurements remain separate gates.

## Explicit build profile

`localLoreLiteRtVerification=true` selects Kotlin/Compose compiler 2.4.0,
LiteRT-LM 0.18.1, Gson 2.14.0, reflection 2.4.0 and coroutines 1.11.0. It uses
Java 21 tooling/tests targeting Java 17, Gradle 8.11.1 and AGP 8.10.1. The
ordinary graph retains Kotlin 2.2.21/coroutines 1.10.2 and no SDK dependency.

The candidate has its own package, output, project cache and dependency lock.
Release, mixed verification/capacity modes, wrong cache, missing analyzer pin
and automatic Java-toolchain downloads are refused. The official analyzer-only
9.4.1 override selects lint 32.4.1; exact analyzer classpath equality, hashes,
dependency checking and the serialized SDK/reflection/stdlib models are audited.
This does not upgrade AGP/D8 or suppress metadata diagnostics.

The build verifies the publisher AAR hash and copies its complete root LICENSE
and THIRD_PARTY_NOTICE texts into generated candidate assets. APK audit requires
the exact SDK binaries and full notice bytes, six aligned native libraries and
the sole app-owned signature receiver permission. No network capability is
added. Keeping the full mixed-component notice is not complete redistribution
clearance; component obligations and release qualification remain separate.

See [verification](LITERT_WORKER_VERIFICATION_2026-10-23.md),
[independent source/compatibility review](LITERT_WORKER_REVIEW_2026-10-23.md)
and [device evidence](LITERT_WORKER_DEVICE_2026-10-23.md). No model or production
UI is selected by enabling this developer qualification profile alone.
