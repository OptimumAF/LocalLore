# Optional per-role output observations, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.04/M01.05), claim
`6375456753`, base `a5a0fae` (#116). This corrects diagnostic coverage; it does not
change gameplay, generation budgets, SDK selection, cancellation policy or Rust
canonical authority. Historical ordinary-play `first_output_observed:false`
receipts from the old runner did not prove absence of output: the old code only
queried `hasOutput()` inside the explicit cancellation case.

## Shared role interface and result fields

`WarmRunner.Role` retains the existing `hasOutput()` default and adds two
backwards-compatible optional methods:

```java
default Boolean observeOutput() throws Exception { return null; }
default RoleObservation observeTerminal() throws Exception { return null; }
```

A null output observation means unsupported/unavailable, false means a successful
observation saw no output, and true means output was observed. Existing adapters
can continue returning unknown without changing their behavior. The existing
WarmRunner execution protocol is unchanged. The coordinator owns the actual
SDK callback implementation and the immutable, validated `RoleObservation` DTO;
this change only calls its fixed `toJson()`.

Each PlayRunner generation adds exactly three fields:

- `output_observation`: `unknown`, `not_observed`, or `observed`.
- `first_output_elapsed_ms`: null until a positive observation, then a finite
  observer-clock duration clamped to 0..180000 ms.
- `terminal_observation`: null or the validated DTO's exact JSON object.

The first-output duration begins immediately before the SDK `start()` call. It
is the time at which this runner first noticed output, an upper bound on first
output arrival under polling; it is **not exact SDK TTFT**, token latency or proof
of a valid final answer. Positive evidence and its first timestamp remain sticky.
A later failed or unavailable output query cannot turn a known positive into a
negative. If there has been no positive, a failed/unavailable output query keeps
the observation unknown for the remainder of that role.

The coordinator's frozen terminal DTO has exactly eight fields: `version`,
`callback_messages`, `buffered_text_bytes`, `callback_error`,
`benchmark_available`, `sdk_input_tokens`, `sdk_output_tokens`, `configuration`.
Callback errors are fixed categories. Raw SDK benchmark counts may be zero or
large; they do not establish successful generation and are not validated gameplay
budgets. A positive buffered-byte count describes the Java buffer, including
output that might later be rejected. Optional configuration describes requested
settings and a nonempty template render, not proof that the runtime enforced
them. No prompt, generated text, arbitrary exception, model data or canonical
story identifiers enter the new observations.

## Polling, cleanup and authority

PlayRunner samples optional output before each ordinary wait's deadline check,
when a wait reports terminal, and after a known cleanup drain immediately before
close. This includes a deadline that expired during start/wait and a start call
that threw after potentially launching work. Metadata is requested only after a
known terminal/drain, while the role remains open. An unknown drain prevents
terminal metadata queries and preserves the existing process-termination fence.
There are no post-close observation calls.

Optional observation exceptions are caught locally. They cannot replace the
original failure, skip cancellation/drain/close, invent an accepted outcome or
stop an otherwise accepted fake test turn. Terminal metadata absence remains
null and does not erase an independent successful output observation. A positive
terminal buffered-byte snapshot also supplies positive output evidence even if
the optional output probe was unavailable or previously saw no output. The existing strict generation-result validation and native responses
continue to decide acceptance. Output observations do not trigger cancellation;
the original cancel-only `hasOutput()` behavior is retained. A successful legacy
cancel-case positive is also recorded in the per-role collector, including
output already terminal when sampled. That terminal case still reports
`cancel_not_observed` and never claims that cancellation happened. The legacy turn
and aggregate `first_output_observed` flag now includes positives from ordinary
roles as well as that legacy cancel path. A false legacy flag alone is still not
an assertion that output was impossible or absent when observation is unknown.

## Actual author verification

The author used installed JDK 21 with `javac --release 17`, existing cached Gson
2.14.0, JUnit 4.13.2 and Hamcrest Core 1.3. Compiler classes, temporary files and
all per-attempt logs used a fresh D-volume evidence directory. No dependencies
were added and no full Gradle, Android/device, native build, SDK inference, model
read or download was performed.

Compilation selected existing `Request`, `WarmRunner`, `PlayRunner`,
`PhaseJournal`, their existing runner/journal tests, plus the coordinator-owned
`RoleObservation.java` and `RoleObservationTest.java` directly from the frozen
`efadff6` source. The coordinator files were read only and were not copied into
this implementation commit. Equivalent commands:

```powershell
javac "-J-Djava.io.tmpdir=$roleTemp" --release 17 -cp $cachedJars -d $roleClasses $selectedSources
java "-Djava.io.tmpdir=$roleTemp" -cp "$roleClasses;$cachedJars" org.junit.runner.JUnitCore org.locallore.runtimebench.litert.PhaseJournalTest org.locallore.runtimebench.litert.PlayRunnerTest org.locallore.runtimebench.litert.RoleObservationTest
```

The first two compilation attempts exited 0 without diagnostics and both focused
runs passed **40 tests**, with no skips: existing journal/runner 27, new runner
observations 9, coordinator DTO 4. The second run took 2.708 seconds. Between runs, a start
failure test was strengthened from a generic IOException to a distinct
`generation_failed` category, proving that a later optional metadata error did
not mask that original category. No failing assertion was relaxed. A third run added the terminal-buffer-positive
regression and passed 41 tests in 2.8 seconds. The fourth/final compile exited 0
without diagnostics and its full selected run passed **41 tests**, no skips, in
2.941 seconds (existing journal/runner 27, new runner observations 10,
coordinator DTO 4). The final change separates a successful legacy output
observation from the active-cancellation condition. The existing terminal-only
cancel test now asserts true output evidence while retaining exactly the prior
`cancel_not_observed`, failed outcome and zero-commit assertions. This corrects
the diagnostic meaning without claiming post-terminal cancellation. All four
compilation/run attempts passed and remain retained.

The ten new runner tests cover ordinary gift observations on both roles,
unsupported versus known negative output, raw zero benchmark metadata without
invented progress, optional query failures without rejecting an accepted gift,
sticky positive evidence and sticky unknown negatives, output first visible at
terminal (including a positive terminal buffer with an unavailable/negative
output probe), expired-deadline cleanup sampling, start-failure primary retention,
no terminal query under unknown ownership, no query after close, and legacy
cancellation compatibility. Existing journal boundary/cleanup tests still pass.

`git diff --check` passed before the source handoff. All logs and synthetic
artifacts remain retained with a separate evidence index. Direct JDK tests do
not qualify the Android API classpath or actual callback/benchmark behavior.
Those remain coordinator-owned compilation/device gates for a new explicitly
pinned artifact; historical APKs and historical receipts are unchanged.

## Integrated offline Android qualification

The coordinator integrated the runner, DTO, actual SDK adapter, bounded callback
observations and Stream tests at
`22f2561497159f6e93a5a6702a8376d9fd9957e7`. An independent offline build qualified
a fresh cacheprobe APK from that exact source, with unchanged per-file Java,
manifest, Gradle and wrapper input hashes before/after the build.

The new APK is **63,666,936 bytes**, SHA256:

```text
655de0c55b27c11d77bf83c505883b3b1e4313ed660d60bfac06aa7246fef58b
```

The exact package is `org.locallore.runtimebench.litert.cacheprobe`; its only
instrumentation is `org.locallore.runtimebench.litert.CacheProbeInstrumentation`.
Manifest permissions are empty. This new hash must be used with the new strict
observation-aware decoder. Equal byte length does not make it interchangeable
with the older `f4d247f3...` APK.

The native pair was extracted only from the hash-verified previously qualified
`f4d247f3e24c302a7e8d2431d7ee8c9fccc476909c0d82789ea1f84083ddfd81`
APK. Its full native inventory matched its frozen prior receipt. Production
native inputs remained identical to the original `ba31932` native compilation
source; the only native-scope delta was a test. Both copied Rust ABI libraries
were checked for byte identity, five expected PlayProbe JNI exports and ELF
alignment. All four final SDK/Rust ABI library entries remained byte-identical
to the prior APK. No native rebuild, runtime upgrade or download was performed.

The explicit offline Gradle invocation ran `:app:assembleDebug`,
`:app:testDebugUnitTest`, `:app:lintDebug` and `:app:auditLintAnalyzer` with fresh
D-volume project/output/temp directories, cacheprobe true, legacy play false,
phaseprobe false, no daemon and downloads disabled. The build reported success
in 37 seconds with **50 tasks, all executed**. The bounded Windows Job controller
completed in 40,640 ms with exit 0, no stderr and known cleanup. A stdin-EOF
barrier preceded all trusted-child work, and the existing maximum 180-second
controller budget was retained. Every stage checked the existing C/D capacity
floors. No attempt in this qualification packet failed or was refused.

Actual JVM XML across 12 suites records **123 tests, 0 failures, 0 errors,
0 skipped**. That includes the ten new runner tests, four coordinator DTO tests,
four new callback Stream tests and all previous Java tests. Lint records
**0 errors and 9 warnings**: OldTargetApi 1, GradleDependency 1 and UsableSpace 7.
UsableSpace remains a nonreserving capacity observation, not a guarantee that
future writes fit. Locked SDK/test binary identities, actual pinned lint analyzer
and dependency metadata, manifest/permission identity, native inventory and
16-KiB ELF/ZIP alignment audits all passed.

The private evidence root retains the qualification script, native provenance,
full stage commands/logs/results, before/after input hashes, JVM XML, lint and
analyzer metadata, staged native libraries and frozen APK. A separate immutable
hash index binds the handoff. Previous evidence roots and artifacts were not
modified. This is offline artifact qualification only: the author ran no ADB,
installation, device operation, model read or SDK inference. Device storage
admission, app-domain model identity and any actual SDK attempt remain separate
coordinator-owned gates.

## Pre-installation source-review correction and supersession

The `655de0c5...` build above remains a genuine successful offline qualification,
but it was **superseded before installation**. Independent source review found
that optional getters caught Exception only: LinkageError could escape, and an
unexpected Error in cleanup diagnostics could bypass Conversation closure. A
second finding identified Error from role/model/native close as uncertain owner
state that also needed the existing process-termination fence. The prior APK was
not installed or exercised; its 123-test build and all bytes remain retained.
It must not be used as the corrected artifact.

Optional output and terminal getters now treat Exception or expected
LinkageError as unavailable diagnostics. Other Errors are not converted into
successful gameplay. Cleanup diagnostics are nested inside a finally that still
closes a known-drained role. The turn preserves the original Throwable, performs
native cancellation/join and known model cleanup, then rethrows an unexpected
Error if ownership remains known. Unknown role, model or native-close ownership
instead produces Undrained with process termination required; original and close
failures remain privately suppressed. Role/model/native close boundaries now
handle Exception or Error explicitly. No diagnostic failure changes a generation
budget, retries a commit or creates canonical authority.

Six new hostile methods exercise output/terminal NoSuchMethodError and
NoClassDefFoundError, retention of a distinct typed start failure, AssertionError
propagation only after known role/model close and native worker join, and Error
from role/model/native close requiring process termination. Uncertain role close
prevents model/Engine close; uncertain model close still permits native joining.
The focused run after the first fix passed 44 tests in 2.983 seconds; after the
close-boundary correction the full selected set passed **47 tests**, no failures
or skips, in 3.018 seconds. Both corresponding javac invocations exited 0.
A fresh integrated Android qualification remains required.

An author evidence-location mistake is retained explicitly: the 44-test followup
added attempt-5 logs and regenerated an unbound compiled-class cache in the
previous author evidence root, instead of starting in a fresh fix namespace.
Readback verified all **23 previously indexed source/log files and the prior
index hash unchanged**. Nothing was deleted or rewritten to hide the additions.
Those new logs and classes were copied into a fresh fix evidence root, where the
47-test run and later records were written. Previously qualified APK/build roots
were untouched. The earlier index binds its listed files; this correction does
not claim that the entire old directory tree remained immutable.

No author ADB, installation, model read, SDK execution, native rebuild or Android
build was performed during these source fixes. The coordinator owns the Stream
first-error correction, integration, new-artifact build and any later device
admission. The final resource tests are host fakes, not real SDK fault injection.

## Corrected artifact qualification 2

After the independent source audit, the coordinator integrated all runner
ownership fixes, SDK-open rollback handling and sticky first callback diagnostics
at `604cb991ade7cb922ef3c89b08e6a296ecab4b4b`. A fresh second build independently
qualified that exact source. The first build and its successful 123-test evidence
remain retained as superseded, not reclassified as a failed build or installed
experiment.

The corrected APK is **63,666,936 bytes**, SHA256:

```text
9417a3e914975918d018c8a7d8954f192c09e40e10320b08c86be8a50fd7217f
```

Its exact cacheprobe package/runner and zero-permission manifest were verified.
The new build used the same hash-verified `f4d247f3...` prior APK native anchor;
production native inputs were unchanged from `ba31932` except a test. Both
staged Rust libraries, all four final SDK/Rust native entry hashes, expected JNI
exports, ABI ELF alignment and 16-KiB ZIP alignment passed. No native rebuild or
runtime upgrade was performed. APK inputs were byte-identical before/after
qualification, including the reviewed Java implementation.

The offline Gradle build ran 50 tasks, all executed, and reported success in
41 seconds. Its bounded stage receipt records 41,937 ms; the complete Windows Job
controller records **44,390 ms, exit 0, no stderr and known cleanup**. The existing
stdin-EOF ownership barrier, maximum-180-second controller budget, separate
D-volume outputs and per-stage C/D capacity gates were retained.

Actual XML across the twelve Java suites shows **132 tests, 0 failures,
0 errors, 0 skips**. Locked dependency identities, actual lint analyzer and
transitive dependency metadata checks passed. Lint had **0 errors, 9 warnings**
(OldTargetApi 1, GradleDependency 1, UsableSpace 7). There were no failed or refused
qualification-2 stages. No test count is inferred from an expected count.

The combined evidence index binds both successful build attempts, their distinct
source inputs and native provenance, original per-stage logs/receipts, JVM XML,
lint/analyzer metadata, both APK identities and the followup source-fix host
checks. The first artifact remains superseded before installation. This author
performed no ADB, model/SDK execution or device action for either qualification.
The corrected artifact's fresh device capacity/model-identity admission and any
actual inference result remain coordinator-owned work.
