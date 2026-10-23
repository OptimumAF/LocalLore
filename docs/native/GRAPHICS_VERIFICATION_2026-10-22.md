# Ordered renderer-abort investigation — 2026-10-22

Scope: bounded M04.04 reliability investigation / M03.05 reproducible checks,
[#8 claim6356499310](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6356499310).
This packet is stacked on open [#45](https://github.com/OptimumAF/LocalLore/pull/45),
head `6ffd1b0`, itself dependent on #44. No merge was performed.
It adds an opt-in Python runner and strict instrumentation parser, their
synthetic host tests, independent review and sanitized execution evidence.
Android/Rust production code, Kotlin tests, dependencies, permissions, inference
delay and device settings remain the exact prerequisite versions.

## Question and fixed controls

The earlier combined A run passed three framework cases and then aborted in
the first Shell cancellation case with a reference-queue watchdog signature
involving `HardwareRenderer$DestroyContextRunnable`. That failed attempt and
its unreached cases remain in [the prior all-attempt artifact](FRAMEWORK_RESULTS_2026-10-22.json).
Subsequent complete runs did not establish a root cause or fix. Official-source
inspection identified the cleanup/watchdog mechanism, not an exact upstream
issue or a demonstrated application defect.

Before device execution, the ticket declared two serial repetitions of each
fixed cohort per selected target: cancellation alone, three framework cases
then cancellation, and the reverse order. A runs to termination before B starts.
Each cohort starts after verified absence of the matching app process. This
controls class order and earlier in-process fixture exposure within a limited
matrix. It does not control all emulator/OS load, GC scheduling or host activity,
and does not sample every surrounding regression from the earlier sixteen-case
selection. No concurrent test/model workload was launched by this packet.

The [independent review](GRAPHICS_REVIEW_2026-10-22.md) inspects the actual pinned
Runner1.6.2/JUnit4.13.2 bytecode. Comma-separated distinct class selections retain
insertion order. Each observed start/terminal pair, exact membership and required
first/last Shell position must nevertheless validate before a cohort can pass.
No declaration-order assumption is made for the three framework methods.

The exact unchanged production/test APK SHA-256 pair is:

```text
app   56ec9d0c20736a772ed7bda9372cdccb300ed8ef1ce609a3158c926e75839ebb
test  e4d57cf5d735f642ea474f0ecbf3a098849377e559181e7eabf50134452024d3
```

The Kotlin test source is the prerequisite's `dd11ab2` revision. The runner
source was committed at `25c6d6f` before device execution; integrated parser
correction is `ad173d9`. No APK was rebuilt or installed in this packet.
Both selected targets are Android15/API35/x86_64 emulators. The other three
emulators and isolated runtime/model experiments were untouched. Prior inventory
found no authorized physical phone; no phone or ARM64 execution is inferred.

## Commands and host verification

```powershell
python scripts/check.py host --offline
python -m unittest discover -s scripts/tests -p test_android_instrumentation_result.py
python -m unittest discover -s scripts/tests -p test_android_app_reliability_smoke.py
python -m py_compile scripts/android_app_reliability_smoke.py scripts/android_instrumentation_result.py scripts/tests/test_android_app_reliability_smoke.py scripts/tests/test_android_instrumentation_result.py
git diff --check
```

Full host gate passed:123 Rust workspace test entries plus3 native-linker tests;
252 Python tests across the six host suites (116/10/14/20/13/79); formatting,
strict Clippy and Rust-generated Android fixture comparison.
The scripts suite includes22 parser and19 runner cases, independently rerun
after integration. Neither host suite invokes ADB or loads/downloads a model.
Python compilation and diff checks passed. No Android build/JVM/lint gate was
rerun: APKs and all relevant Android/Rust source are unchanged from #45, whose
38 JVM, both-ABI build, lint and packaging checks remain separate dated evidence.

The reviewer first reproduced a reporting inconsistency: an explicit abort
followed by a forged success summary could yield `status=aborted` while retaining
`final_success=true`. Overall cohort acceptance already rejected that result.
The new regression reproduced the inconsistency before correction; the parser
now revokes final success while retaining valid preceding counts and order.
Additional tests cover failed/partial/unknown outcomes, changed identities,
timeout/cancellation, cleanup, journal failures and private canaries.

Actual emulator commands use the following form, once for each explicitly
selected target with a different new journal path:

```powershell
python scripts/android_app_reliability_smoke.py --adb <existing-adb> --serial <authorized-target> --apk target/checks/framework/final-apks/app.apk --test-apk target/checks/framework/final-apks/test.apk --repetitions 2 --output <new-A-or-B-journal.jsonl>
```

Each attempt checks local/installed identities, bounded execution, actual test
order, final success, hash-guarded stop, explicit app absence and host ADB-client
cleanup. A start is fsynced before device calls; finish follows cleanup. Raw
protocol remains bounded in memory; public evidence contains only fixed metadata
and expected test IDs. See [runner semantics](GRAPHICS_RUNNER.md). No private
save, raw diagnostic, serial, path, model or credential is published.

## Observed matrix

Both CLI invocations exited zero. All twelve started cohorts have terminal
records; none were discarded, retried, skipped or left unknown. Each target
ran two complete serial cycles of the three controls:

| Target | Cancel only | Framework then cancel | Cancel then framework | Case executions |
|---|---|---|---|---|
| A |2/2 cohorts passed |2/2 passed |2/2 passed |18 passed |
| B |2/2 cohorts passed |2/2 passed |2/2 passed |18 passed |

All12 cohorts passed actual order, unique case membership and final protocol
success. All36 repeated case executions passed, with zero failures/skips and
zero recognized graphics-watchdog signatures. These involve four unique case
identities, not36 independent scenarios. Every cohort verified app absence
before/after, installed APK identities and ADB-client cleanup. Both final plans
record app process absent, all clients cleaned and zero unexecuted attempts.
No install, data clear, emulator reboot or platform-setting change occurred.

[All-attempt results](GRAPHICS_RESULTS_2026-10-22.json) retain the complete
sanitized JSONL contents for A and B, their original journal SHA-256, exact
observed test order and the prior abort reference. Aggregate/count/order/privacy
validation and final diff checks passed. This bounded matrix did not reproduce
the original failure. It provides no demonstrated root cause or production fix.

## Interpretation and remaining gates

Every new started attempt belongs in the dated result artifact, including a
failure, abort, missing finish or unexecuted remainder. Later passes cannot
rescue a failed overall plan. Individual `case_passes` alone do not establish
cohort success. The original graphics abort remains unexplained and unfixed;
`cause_fixed=false` is explicit even if this bounded matrix does not reproduce it.

These cases exercise real framework lifecycle, Kotlin IO/native ownership,
Rust Host and SQLite with deterministic fake inference. They do not qualify
physical-device performance, ARM64 execution, real models, graphics/heap
reliability, hardware power loss, storage exhaustion, complete M04 acceptance
or hosted CI. M01.01 remains blocked on an authorized physical phone. Full M04
fault/exhaustion/recovery gates remain separate, with active D03 storage/workspace
ownership preserved. Local evidence awaits owner review; no accepted checkbox
was added. Next runnable work is deterministic M04.04 storage-failure coverage,
coordinated with the current shared-storage claims.
