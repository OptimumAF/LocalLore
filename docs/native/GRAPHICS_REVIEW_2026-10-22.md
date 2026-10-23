# Independent graphics-cohort runner review

Scope: M04.04/M03.05, delegated under #8 comment 6356499310. Baseline:
`6ffd1b0`; separate branch `review/m04-graphics-cohorts`. This reviewer owns
only this report. The coordinator owns the opt-in runner, integration, device
actions and evidence; the independent parser agent owns parser changes/tests.
The prior renderer/reference-queue abort remains unexplained.

## Pinned runner selection and ordering

Read-only `javap -p -c` inspection used the actual cached AndroidJUnitRunner
1.6.2 and JUnit 4.13.2 artifacts already pinned by the project. No dependency
was added or updated.

| Artifact | SHA-256 |
|---|---|
| `runner-1.6.2.aar` | `d8eac6d9864f432b15962b2c2739a7b31685c87777364ac97323c9e4b2c94744` |
| Runner `classes.jar` | `34d09ad45b5b82c04b2e1ec3775b15125e99fbe26a7bbd5663020dce94a9ce9f` |

The inspected execution path preserves first insertion order of explicitly
selected, distinct classes:

1. `RunnerArgs.Builder.parseTestClasses` delegates to `ClassesArgTokenizer`.
   Its class/method states scan comma-separated tokens into an `ArrayList`,
   recognizing both `Class` and `Class#method` tokens in either position.
2. `TestRequestBuilder.addTestClass` and `addTestMethod` both insert the class
   into `includedClasses`, a `LinkedHashSet`. Method selection additionally
   installs a filter for that class only.
3. `build` passes that collection to `TestLoader.getRunnersFor`, which collects
   runners in a `LinkedHashMap` and returns an `ArrayList` of its values.
4. The resulting `ExtendedSuite` delegates to JUnit's list-based `Suite`
   constructor. JUnit's default `ParentRunner` scheduler invokes each child
   synchronously in the list order. This path uses `Request.runner`, not
   `Request.classes`.

Consequently the proposed `FrameworkInterruptionTest,ShellInstrumentedTest#cancelAndResetDuringDelayCannotPublishOldResult`
selection and its reverse are supported by these pinned implementations. The
three framework methods must belong wholly before or wholly after the one shell
method, respectively. Method ordering *within* FrameworkInterruptionTest is a
separate JUnit matter; declaration order is not established by this inspection.
Do not mix a full class and a selected method of that same class as an ordering
control: the per-class method filter can narrow that class.

This is implementation evidence for the inspected versions and ordinary serial
runner, not a universal future ordering guarantee. Custom runners, filters,
sharding, sorting or orchestration could alter execution. The cohort analyzer
must independently validate actual start and terminal events, exact expected
membership, uniqueness and prefix order before accepting a pass. An ADB exit
code alone cannot establish that the selected instrumentation completed.

## Runner acceptance boundaries

The packet is an attempt to reproduce and localize an unexplained abort. A
successful bounded cohort does not establish that the abort is fixed or identify
its cause. Forward/reverse runs need separate records, as do every repetition,
failed run, incomplete run and missing expected test. The interrupted original
attempt must remain in the evidence.

The runner should operate only after explicit invocation, choose fixed cohorts,
verify installed package hashes and process absence, and stop subsequent device
calls when cleanup of a local ADB client is unproven. Sanitized records should
retain fixed stage/error/cohort enums and allowlisted expected test identities;
unexpected test names, raw instrumentation text, serials, paths or exception
messages must not become public journal fields. Fresh-process checks and
append-only flushed records are separate requirements from test pass/fail.

This review performed no ADB, emulator, model, JNI or Gradle action. It inspected
existing local bytecode and the official public AndroidJUnitRunner reference;
the bytecode, rather than a presumed documentation promise, supports the
ordering conclusion. Source review and executed checks of the forthcoming
runner/parser will be recorded separately when available.

## Runner and parser source review

Read-only review used parser commit `1d305cb` and the coordinator's pending
runner snapshot with SHA-256
`eff4d95cb6a78a5540c9f6afb6f2a99abbde7b2c9def9860265309a7e5b70a90`.
No production, parser or runner source was changed by this reviewer.

The runner verifies local and installed app/test hashes, records a durable
attempt start before device commands, checks app absence before instrumentation,
and attempts hash-guarded stop/absence before writing each terminal record.
Unproven local client cleanup stops future clients and prevents an absence
claim. A finish-journal failure occurs after cleanup and prevents another
attempt. Exclusive creation prevents replacement of an earlier journal. The
instrumentation helper retains bounded partial protocol on timeout/nonzero exit;
its execution status and cleanup evidence remain separate from parsed case
outcomes. A mocked `Journal.close` failure with a private exception canary was
also confirmed to produce sanitized failure output rather than expose the
exception message.

The parser rejects unknown identities, duplicates, mismatched start/terminal
pairs, skips, malformed summaries and missing final instrumentation status.
Only expected test identifiers and bounded aggregate evidence leave it. Required
first/last endpoints plus exact unique membership suffice for the fixed
forward/reverse cohorts: there is exactly one shell method and three framework
methods. This does not rely on framework declaration order.

One concrete metadata inconsistency was reproduced and reported for correction:
insert `INSTRUMENTATION_FAILED: synthetic abort` before the final stream in an
otherwise valid four-case synthetic run. At parser commit `1d305cb` the result
was `status=aborted`, `passed=4`, `final_success=true`, `order_verified=true`.
Overall cohort acceptance correctly fails because the runner requires
`status=passed`; there is no cohort false pass. Nevertheless `final_success`
should also require absence of the explicit abort flag. A regression should
retain the four valid preceding case results while keeping final success false.
The coordinator assigned that correction and regression to the exclusive parser
agent. Integration depends on that follow-up; this report does not claim the
correction or its check has already passed.

Reporting limits remain explicit: `case_passes` can include individually passed
tests from a failed/incomplete cohort; only `cohorts_passed` and overall status
qualify cohort completion. `graphics_signature_attempts` counts recognized
signatures in analyzed protocol, not proof that every unparsed transport failure
lacked that signature. A matching public stack identifies the retained signature,
not its cause.

Independent synthetic checks actually run, after inspecting that all transports
were mocks:

```text
python -m unittest discover -s scripts/tests -p test_android_instrumentation_result.py
  21 passed, 0 failed
python -m unittest discover -s scripts/tests -p test_android_app_reliability_smoke.py
  19 passed, 0 failed
```

These suites exercise parser policy, journal ordering and transport control
without invoking ADB. No real device/cohort outcome or graphics fix is claimed
by this review. The concrete additional abort counterexample above was not
covered by those initial passing tests.
