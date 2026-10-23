# Capacity test ownership and lifecycle controls — 2026-10-22

Scope: bounded M04.04 / [#8](https://github.com/OptimumAF/LocalLore/issues/8),
stacked on open #53 at `53956e7`. The parent packet's actual Full tests exposed
an ActivityScenario teardown failure in one native-only method. Its requested
DESTROYED state remained PAUSED. The failure and supplemental cleanup stay in
[the parent evidence](CAPACITY_RESULTS_2026-10-22.json); this packet does not erase
that row or claim a framework fix.

The fixed candidate plan passed **13 method executions in three cohorts**:
five ordered cases on each selected emulator, then three default-discovery
cases on A. There are five unique candidate methods (three original proofs and
two controls), 24 asserted actual Full commit replies and twelve native lifecycle
boundary snapshots. The separate old-B baseline passed three methods, for
16 current-packet passes total, zero failures/skips/unfinished. Baseline and
candidate test APKs intentionally differ; the candidate was frozen throughout
its three cohorts. Finite nonreproduction does not explain the parent's failure.

## Concrete fixture correction

The old class-level `createComposeRule()` launched an Activity for all three
capacity methods. Two need only the production native gateway. They now live
in `SqliteCapacityNativeTest` with no Compose/Activity rule. The original
`SqliteCapacityInstrumentedTest` keeps its real collected UI case and ordinary
rule teardown. `CapacityTestFixture` shares the original transport, identity/root
guards, key/snapshot assertions and bounded cleanup. No gameplay logic, SQL,
runtime fault API, native wire, app dependency, permission or capacity profile
changes. The application APK is byte-identical to #53; only instrumentation changes.

Independent source parity compared all three original test bodies, fourteen
shared/UI function bodies and three transport/owner/fixture class bodies to
`53956e7`, ignoring whitespace. All matched. In particular, actual Full replies,
one original submit/prepare, pending-key checks, accepted player view/receipts,
cancel/disposal/reopen fencing and four-owner/exchange/root cleanup were retained.
Each complete three-proof cohort still requires eight actual Full commits.

Native `@Before` and `@After` hooks query every lifecycle Stage except DESTROYED
on Main and require zero monitor-visible Activities. They print only fixed
stage/count assertions. These are boundary snapshots, not continuous monitoring,
a heap profiler or proof about future model allocations. The existing pinned
monitor dependency supplies this API; no dependency is added.

## Explicit order and normal discovery

The opt-in Suite uses public Kotlin nested classes under an unannotated
`CapacityLifecycleCohort` container. Its explicit binary selector is
`org.locallore.app.CapacityLifecycleCohort$OrderedSuite`. One invocation runs:

1. `Before#emptyComposeBeforeCapacityWorkClosesNormally`.
2. Native `actualReadyFullRetriesKeepOriginalKeyAndCanonThenReopenAsUncommittedDraft`.
3. Native `cancellingActualFullTurnPersistsCancellationAndReopenCannotApplyItsOriginalRequest`.
4. UI `composedActualFullKeepsLastCanonBlocksCallbacksAndRepeatedRecoveryThenFencesDisposal`.
5. `After#emptyComposeAfterCapacityWorkClosesNormally`.

The native pair uses NAME_ASCENDING. Both controls use `createComposeRule`, the
capacity identity guard and `waitForIdle`, with no setContent, Rust owner,
database or ViewModel. Their ordinary rule teardown remains part of the result.
`createEmptyComposeRule` would omit the host Activity and was not substituted.
No lifecycle callbacks are manually invoked, waits enlarged, errors swallowed,
model delay adjusted or device settings changed.

Nested controls/Suite are excluded by the pinned runner's normal class scanner,
while its explicit direct loader accepts their binary names. Consequently default
capacity discovery should run only the original three proof methods, once each.
The old UI-class-only selector now selects just one UI method. A comma-separated
class argument is not used to infer Suite order. The collector compares the full
observed five-case sequence in addition to strict protocol membership/counts.
[Independent review](CAPACITY_LIFECYCLE_REVIEW_2026-10-22.md) records pinned/current
Compose, JUnit, runner/scanner/loader and monitor source/API evidence.

## Predeclared execution and reproduction

The fixed plan was one old frozen B baseline, then one candidate Suite on A,
one on B and one A default-discovery cohort. No automatic retries or a loop to
obtain green results. All host builds finish before candidate device execution.
Raw output/start/terminal journals are retained in ignored
`target/checks/capacity-lifecycle`; public results omit transport IDs, private
paths, tokens and story identifiers.

Fresh preflight observed five emulators and zero physical phones. Only A/B were
operated: Android15/API35/x86_64, `sdk_gphone64_x86_64`, 4,096-byte OS pages.
Both ordinary and old capacity installed hashes and boot/activity/window
readiness were verified. Old APKs were preserved locally before rebuilding.
The old B baseline passed all three original methods, so the earlier failure
did not reproduce in that attempt.

Build/audit from the repository root with the existing SDK/JDK/NDK/cache:

```powershell
python scripts/android_capacity_probe.py build --offline
```

The coordinator updates only the verified capacity test APK using `install -r -t`,
after hash-guarded cap-app stop. The cap application APK and ordinary installed
app/test APKs remain unchanged; existing saves are not cleared. Local/installed
hashes are checked before and after cohorts. Final cap-app absence and host-client
cleanup are distinct requirements. Other emulators/models/packages remain untouched.

The Suite's `$` must survive both host argument processing and the device shell.
For example, Python's argument-array invocation and remote quoting can reproduce
the selection on one explicitly authorized target:

```python
import shlex
import subprocess

selector = "org.locallore.app.CapacityLifecycleCohort$OrderedSuite"
runner = "org.locallore.app.capacity.test/androidx.test.runner.AndroidJUnitRunner"
remote = shlex.join(["am", "instrument", "-w", "-r", "-e", "class", selector, runner])
subprocess.run([adb_path, "-s", authorized_serial, "shell", remote], check=True)
```

For default-discovery verification omit `-e class` and its value. Raw ADB success
alone is insufficient: the collector uses the existing bounded process owner
and strict parser from #46, requires exact expected start/terminal pairs, final
AndroidJUnitRunner success, full Suite order and successful cleanup. Instrumentation
keeps the existing 180-second/128-KiB bounds. No new production runner/framework
or default device action is introduced.

## Verification and scope limits

The [all-attempt artifact](CAPACITY_LIFECYCLE_RESULTS_2026-10-22.json) records the
baseline and each candidate cohort separately, including exact order, hashes and
cleanup. Passing finite controls establishes those observations; it does not
isolate a causal explanation for the earlier teardown failure.

The offline capacity build compiled/packaged the new instrumentation, passed
lint with zero errors/one existing GradleDependency advisory and passed the APK
audit. Native/app tasks and the prior 47/0 JVM XML were reused, not freshly
executed. Two metadata API deprecation warnings remain documented. No new host
unit tests or Rust workspace execution is inferred from unchanged tasks.
`git diff --check` and source/evidence review supplement actual emulator tests.

| Actual command/procedure | Result |
|---|---|
| Old frozen B baseline, original class selection | 3 passed; prior failure not reproduced |
| `python scripts/android_capacity_probe.py build --offline` | Passed: 77 tasks,7 executed/70 up-to-date; new test APK compiled and audited |
| Candidate Suite on A | 5 passed, exact full order, final cleanup verified |
| Same candidate Suite on B | 5 passed, exact full order, final cleanup verified |
| Candidate default discovery on A | Exactly3 original proofs passed once; nested Suite/controls absent |
| Application/local and installed ordinary APK identity checks | Byte-identical cap application; ordinary installed identities unchanged |
| Source parity and diff checks | Passed; original three proof bodies preserved |

Toolchain: Windows x86_64, Python3.9.12, Rust1.93.1, JDK17.0.6, Gradle8.11.1,
AGP8.10.1, Kotlin/Compose compiler2.2.21, NDK29.0.14206865,
compile/targetSDK36/min26, BuildTools35.0.0. Pins/licenses are unchanged.

M04.04 remains partial/in_review pending owner acceptance and wider gates.
No old framework cause is claimed fixed, and no failure-free reliability,
physical-phone/model, ARM64 execution,16KiB OS, API26/36, partition ENOSPC,
capacity-relief recovery, heap/power-loss/performance, hosted CI, merge or release
qualification follows. M01.01 remains blocked on an authorized physical phone.
The next separately scoped M04.04 task is actual same-key recovery after capacity
relief; the fixed immutable N15 test binary cannot provide that transition.
