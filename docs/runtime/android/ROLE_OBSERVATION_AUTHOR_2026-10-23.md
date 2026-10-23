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
