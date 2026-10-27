# Versioned Android component-verification driver

Supporting M10.02/M08.05. Source:
`benchmarks/android_process_verification.py`, `android_process_client.py` and
`android_instrumentation_evidence.py`. These are developer tools for Windows,
not app gameplay dependencies. No new runtime, model or package is introduced.

The driver replaces generated host logic lost during the
[retained-parent verification interruption](ANDROID_RETAINED_PARENT_VERIFICATION_2026-10-26.md).
Its source belongs in Git; raw records, binaries, device identities, model files
and application data stay private. Every execution needs a new evidence folder
outside the checkout. Existing destinations and installed target packages refuse
reuse. Keep private evidence locations out of concurrent cleanup.

## Build and admission

From the repository root, with existing JDK21/SDK components and cached Gradle
and Rust dependencies:

```powershell
python -I -B benchmarks/android_process_verification.py build --out "$evidence/build" --sdk "$sdk" --java "$java"
```

Supply absolute paths; the parent evidence directory must already exist. The
build selects only the existing isolated input-process debug profile and its
exclusive project cache. It cleans the controller and JVM test results, reruns
the JVM tests, assembles the product/test/controller APKs and checks both lint
reports. Eleven separate audit/signature/manifest commands verify the APKs,
including one matching signer and the exact instrumentation target and runner.

An EOF-barrier worker runs inside the existing Windows Job supervisor. Inputs,
driver bytes and tracked source maps bind before dispatch and after completion.
Every command opens exclusive binary output files before spawning, drains short
chunks with a shared 4MiB limit, and treats overflow/timeout/capture failure as
failure even if the direct child later exits zero. An incomplete worker relies
on its enclosing Job to close descendants; direct-child exit is not tree closure.
The owner record is saved before subsequent validation. A `passed` field alone
does not admit a build: records, raw hashes, APKs, source maps, executed JVM
results, lint and audit outputs are checked again before installation.

## Existing server and fresh owned emulator

Use the existing `benchmarks/receipt_avd_environment.py` plan/prepare/run protocol
to create a new standard API35 Google APIs/x86_64, 2GiB/two-CPU guest. Its
proposal, authorization, prepared and running records remain private. The
unchanged 4GiB host-memory floor and existing storage/commit floors still apply.
The driver does not prepare or adopt a physical phone or a previously used
application fixture.

Observe the already running ADB server without starting or replacing it:

```powershell
python -I -B benchmarks/android_process_verification.py server --out "$evidence/server" --sdk "$sdk" --powershell "$powershell"
```

This records the native process identity, sorted loopback5037 listeners and ADB
hash. The SDK client pins that initial server, PowerShell/ADB bytes, optional
owned launcher identity and first selected transport. It refuses global server
and connection commands. Any deadline, identity, stderr, return-code, cleanup or
persistence failure closes further dispatch. Raw stdout and command metadata
are forced before an output can count as successful. Native kernel FILETIME
avoids rounding a process identity through a higher-level date conversion.

After the owned emulator is running:

```powershell
python -I -B benchmarks/android_process_verification.py components --out "$evidence/components" --sdk "$sdk" --powershell "$powershell" --build "$evidence/build/result-v1.json" --proposal "$runProposal" --running "$runningReceipt" --server "$evidence/server/server-v1.json"
```

The full existing live-owner lease checks deadline, stop/result markers,
prepared configuration and owner/worker/launcher identities. User0 and fixed
emulator5592/transport are required. All three fixed packages must be absent
before installation; APK hashes are checked before install and after device
readback. No clear-data, uninstall, force-stop or partial-fixture adoption path
exists here. Instrumentation runs explicitly as user0 through binary `exec-out`.

## Exact component scope

Three fixed classes must pass all ten original methods:

| Class | Methods |
|---|---:|
| `RetiredSelectionFixtureInstrumentedTest` | 4 |
| `RetainedParentFixtureInstrumentedTest` | 4 |
| `RetainedParentFallbackNativeTest` | 2 |

Source names and raw runner status bundles must agree. Each method needs one
start/pass pair in the correct class, coherent counters when present, and one
complete runner footer. Skips, duplicates, missing/extra tests, mixed classes,
partial output and trailing runner errors refuse success. LF/CRLF framing does
not change the raw hash. Parent validation rereads component outputs and every
SDK-client record before publishing success.

These ten methods establish loader/refusal and native retained-parent component
behavior only. They do not run the external root/active-child/retired-leaf or
[retained-parent two-death case](ANDROID_RETAINED_PARENT_PROTOCOL.md), broad
Android regressions, real inference or phone/ARM64 qualification. Do not upgrade
a partial component result into those gates. Close only the owned emulator
through its existing proposal-bound stop protocol after clients terminate.

Host regressions:

```powershell
python -B -m unittest scripts.tests.test_android_process_verification scripts.tests.test_android_process_client scripts.tests.test_android_instrumentation_evidence
```
