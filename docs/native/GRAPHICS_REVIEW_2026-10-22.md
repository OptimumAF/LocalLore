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
