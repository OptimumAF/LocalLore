# Opt-in ordered reliability cohorts

`scripts/android_app_reliability_smoke.py` investigates the unexplained renderer
cleanup abort retained in [framework evidence](FRAMEWORK_VERIFICATION_2026-10-22.md).
It runs only on an explicitly selected, authorized target with the expected
app and instrumentation APKs already installed. It never installs, clears data,
provisions tools, downloads models or changes device settings. Default host
checks exercise synthetic transports and protocol fixtures only.

From the repository root, after building/installing the reviewed APK pair and
selecting the authorized target:

```powershell
python scripts/android_app_reliability_smoke.py --adb <adb-executable> --serial <authorized-target> --apk <app.apk> --test-apk <test.apk> --repetitions 2 --output <new-journal.jsonl>
```

The journal's parent directory must already exist. The output is created
exclusively; an existing file is an error before any device operation. Keep
each attempt journal rather than replacing a failure with a later success.
An interrupted journal with a start but no finish records an unknown outcome.
Exit zero requires every planned cohort to pass, verified final app absence,
and cleanup of all owned local ADB clients. Other outcomes return nonzero.

## Fixed bounded plan

The default plan runs these cohorts serially, once or twice as explicitly
selected by `--repetitions` (default one, maximum two):

| Cohort | Selection and required observed order |
|---|---|
| `cancel_only` | Only `ShellInstrumentedTest#cancelAndResetDuringDelayCannotPublishOldResult` |
| `framework_then_cancel` | All three `FrameworkInterruptionTest` cases, then that Shell case |
| `cancel_then_framework` | That Shell case, then all three framework cases |

Optional repeated `--cohort` arguments select an ordered subset of these fixed
names. Arbitrary class/method selections, duplicates and larger repetition
counts are rejected. Two full repetitions mean six cohorts and eighteen case
executions per target, involving four unique test cases. These are repetitions,
not eighteen independent scenarios. Method order within the framework class is
not assumed. [Pinned runner review](GRAPHICS_REVIEW_2026-10-22.md) explains class
selection ordering; actual start/terminal records must verify it on every run.

Before each cohort the runner checks local and installed app/test SHA-256,
hash-guards the selected app's force-stop and explicitly verifies process
absence. It rechecks identities before instrumentation and afterwards, then
hash-guards final stop and absence. It does not erase a saved workspace. The
framework fixtures create and clean up their own synthetic private roots.
Every instrumentation call uses the existing bounded process owner with a
180-second deadline and 128-KiB output cap. No watchdog, renderer, animation,
inference delay or platform setting is adjusted.

## Evidence and failure semantics

The exclusive UTF-8 JSONL journal is append-only, flushed and fsynced. A plan
records hashes and counts. `attempt_started` is durable before any device call;
`attempt_finished` follows cleanup. `complete` aggregates all attempts, including
failures. An unwritable finish record stops dispatch, leaving the prior start
as unknown. Unknown ADB-client ownership or failed app absence stops the plan.
Test/protocol failures can continue only through the remaining predeclared plan
after cleanup; there are no automatic success-only retries.

The strict parser validates matching test starts/terminals, identity, count,
unique membership, required endpoints and final AndroidJUnitRunner success.
Unknown names, malformed/truncated output, duplicates, skips, aborts, nonzero
transport exits and missing final status cannot pass. Partial validated counts
are retained on failures/timeouts. `case_passes` includes valid individual
passes in failed cohorts; only `cohorts_passed` and overall status establish
cohort success. Explicit abort always revokes `final_success`.

Only fixed categories, hashes, counts and expected test IDs leave the parser.
Raw output stays bounded in memory and is not written by this runner. Journals
omit serials, paths, exception messages, unknown test names and story content.
The watchdog flag recognizes three fixed fragments in validated stack fields;
unparsed failures remain unclassified. It identifies a signature, never a root
cause. A passing matrix reports `cause_fixed=false`: bounded nonreproduction
does not erase the original abort or qualify graphics reliability.

Synthetic host coverage includes forged success, explicit abort, partial
results, wrong order, changed APKs, missing return status, timeout/cancellation,
unknown client ownership, cleanup failure, interrupted journal writes, exclusive
creation and private canaries. See the [dated run report](GRAPHICS_VERIFICATION_2026-10-22.md)
for actual emulator execution and limits.
