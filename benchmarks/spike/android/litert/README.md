# Isolated LiteRT-LM Android SDK experiment

M01.02 experiment only. This standalone application does not change the Compose
app or select a production backend. It has no Internet permission, activity,
story storage, downloader, account, tool registration or telemetry.

The exact Google Maven SDK is `com.google.ai.edge.litertlm:litertlm-android:0.18.1`.
Its API classes require a Java 21 compiler. Our Java sources target Java 17;
no Kotlin compiler plugin is used. Existing AGP 8.10.1, Gradle 8.11.1, SDK 36,
Build Tools 35.0.0 and minimum Android API 26 are retained inside this project.
The production application's toolchain is unchanged.

With the existing JDK 17 selected in `JAVA_HOME`, Android SDK in `ANDROID_HOME`
and an already installed JDK 21:

```powershell
python benchmarks/spike/android/litert/build.py --java21 'C:/Program Files/Java/jdk-21' --offline --clean
python -m unittest discover -s benchmarks/spike/android/litert -p 'test_*.py' -v
```

Remove `--offline` only when explicitly provisioning the pinned Maven build
dependencies. The runner does not install SDKs, accept licenses, download Java,
install an APK, contact a device or fetch model weights. It verifies the existing
repository Gradle wrapper before invoking Java. The debug APK is at
`app/build/outputs/apk/debug/app-debug.apk` relative to this directory.

The isolated project pins lint 9.4.1 (artifact 32.4.1) through Google's documented
experimental analyzer override, retaining AGP and the production toolchain.
The runner compares the actual analyzer classpath with its locked hash manifest,
checks SDK/Kotlin dependency analysis and rejects metadata/infrastructure errors
even when Gradle returns zero. Normal assembly, JVM tests, lint and APK audits
must all pass. `--probe-incompatible-analyzer` instead reproduces the original
analyzer's metadata failure and deliberately returns 2. Read the
[analyzer evidence](../../../../docs/runtime/android/LITERT_ANALYZER_2026-10-22.md)
and [SDK source review](../../../../docs/runtime/android/LITERT_SOURCES_2026-10-22.md).
No suppression or dependency downgrade masks the old analyzer's limitation.

An authorized coordinator owns installation and every device interaction. The
single APK self-instrumentation component is:

```text
org.locallore.runtimebench.litert/.SpikeInstrumentation
```

Run it explicitly with `am instrument -w -r -e mode MODE COMPONENT`. Modes are
`metadata`, `missing`, `corrupt`, `generate` and `cancel`. `missing` and `corrupt`
exercise actual native initialization against fixed synthetic paths, without
reading the supplied real model. Other modes use exactly
`getFilesDir()/gemma4-e2b.litertlm`. The coordinator must verify model identity
before provisioning it. Do not upload weights, raw results or private prompts.

`generate` and `cancel` consume `getFilesDir()/request.json`, a strict UTF-8
worker request v1: `version`, `role`, `prompt`, `max_tokens`, `context_tokens`,
`threads`, `schema`. The request is at most 32 KiB. Context is exactly 4096 and
CPU thread count exactly four. Director output is capped at 350 tokens and
narrator output at 220. Unknown fields, duplicate keys, malformed Unicode,
excessive nesting, tools, wrong types and nonfinite numbers are rejected before
model initialization. The consumed request is deleted after reading.

`result_base64` in the final instrumentation Bundle contains the exact host
worker v1 JSON shape, Base64-encoded UTF-8. Text is bounded to 16 KiB and must
remain inside the coordinator's memory for Rust validation. Base64 is transport
encoding, not encryption. Never print or publish it. `metrics` contains only
fixed categories, counts, timing values and ownership flags; SDK exceptions and
paths are discarded. Native minimum severity is set to `INFINITY`, and file
descriptors 1 and 2 are redirected during SDK calls. Only synthetic fixtures are
authorized for this experiment.

`cancel` requests native cancellation after the first visible content event,
waits for the terminal callback, closes the conversation and engine, discards
their output, then reloads fresh owners for an eight-token synthetic smoke call.
The returned worker JSON belongs to that reload. Distinct cancel/reload pulse
metrics avoid treating reload responsiveness as cancellation responsiveness.
No cancelled native conversation is reused. Close return values and coordinator
process-absence checks complement callback observations; a callback alone is
not proof that all native work has finished.

SDK calls run on the instrumentation worker, with a Main-looper heartbeat.
An independent 90-second watchdog kills only this benchmark process if a native
call outlives the coordinator. A callback-drain timeout also terminates the
process instead of deleting active owners. The coordinator must separately
enforce its deadline, force-stop only this benchmark package and verify process
absence. Abrupt termination is never reported as cooperative cancellation or
native disposal.

The public SDK separates a `Message.channels` map from `Message.contents`.
This worker rejects any nonempty map before copying content, and rejects literal
`<think>`/`</think>` tags after assembling the final text. However, SDK `jsonToMessage` converts native
content objects using only `type` and `text`, dropping per-item channel metadata
and unknown native content types before the callback. The callback boundary
therefore cannot prove that arbitrary native text was final-channel content or
that no unknown native content was present. Thinking is requested off, not
semantically guaranteed absent. Returned SDK-visible text remains untrusted and
must pass the Rust oracle. This experiment does not claim a general hidden
reasoning filter or lossless native-output validator.

The Android API has no public tokenizer equivalent to the Python API's
`Engine.tokenize`. This spike checks native context/decode limits and actual
benchmark token counts; it does not invent a tokenizer or claim preflight token
counting. No physical-device speed, ARM64 execution, model quality, thermal,
sustained-session or full-turn persistence result follows from compilation or
an emulator smoke test.
