# Native Android storage failure checks — 2026-10-22

Scope: M04.04, [#8 claim6356808717](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6356808717).
Accepted main `bc64200` already has seven commit-error checkpoints, seven
subprocess exits, SQLite page exhaustion and real-writer conflict tests. This
packet executes those tests on Android and adds three last-potion pressure
fixtures. It does not replace the existing tests or claim whole-milestone acceptance.
The independent branch needs no unmerged app/graphics-test prerequisite.

## Changed behavior under test

`turns/storage_pressure.rs` is a private unit-test module; its only parent edit
is `cfg(test)` registration in `turns.rs`. No production API, gameplay code,
schema, dependency, Host wire, Kotlin source or device setting changes.

The eight-action fixture gives the player's sole potion first, then records
seven bounded statements to Mira. SQLite's actual `max_page_count` cap produces
`TurnError::Full`; no injected generic error substitutes for that result. A
rolled-back preflight proves the exact first gift envelope and witnesses fit
under the same cap. The exact later allocating statement is not instrumented.
All eight scoped tables, canonical bytes, draft/head/cache and four observers'
contexts stay unchanged after each failed attempt. An independent story with
the same turn ID stays unchanged as well.

Two commit-pressure variants retain the original request: one recovers on the
same connection; the other drops/reopens immediately after failure, checks
persisted rows/canon/draft, explicitly reapplies the new connection's page cap
and observes Full again. Raising only that synthetic connection's budget lets
the exact request commit once. Subsequent reopen and duplicate retry return the
same receipt without another gift. The third case forces Full during draft
insertion: no partial turn appears, then same-key creation/commit/reopen succeeds.
Claims, unchanged beliefs/discoveries/world facts and Sable's absent observation
are checked separately. Each synthetic fixture stays below2MiB.

Independent review found the missing intermediate-reopen case before execution;
it was added in `8a4abad`. During author-side parallel tests, nanosecond-only
temporary names collided on Windows; an atomic suffix corrected that fixture.
The final three targeted tests passed twice, then the integrated full gate passed.
The [review](ANDROID_FAULT_REVIEW_2026-10-22.md) records source and ownership checks.

## Build and host evidence

```powershell
python scripts/check.py host --offline
python scripts/storage_android_smoke.py --sdk "$env:LOCALAPPDATA/Android/Sdk" --unit-tests --output target/checks/storage-faults
python -m py_compile scripts/storage_android_smoke.py scripts/tests/test_storage_android_smoke.py
git diff --check
```

All commands passed at integrated source `3267aa6`:

| Check | Actual result |
|---|---|
| Offline host gate |125 Rust workspace test entries (includes one auxiliary child entry),3 linker tests,198 Python tests; format/strictClippy/four fixture comparisons passed |
| Storage crate within that gate |42 entries:13 private unit entries,14 schema adversarial,9 durability review,6 public durability |
| New helper coverage |7 synthetic tests within scripts suite25; exact artifact selection, stale/wrong/missing/duplicate refusal, no-run/offline command and mutually exclusive modes |
| Native cross-build/audit |x86_64 and ARM64 unit-test PIEs,16KiB LOAD alignment, only libc/libdl/libm shared dependencies; SQLite remains bundled |
| Python compilation / final diff |Passed |

The helper adds explicit `--unit-tests` and retains existing example defaults.
It invokes Cargo `test --lib --no-run --release --locked --offline`, selects the
single emitted storage test executable rather than a stale glob, checks its
target/deps path and applies the existing ELF audit. It performs no ADB,
provisioning or model action. Default checks run its synthetic tests only.

Existing pins: Rust1.93.1, NDK29.0.14206865/API26 sysroot, rusqlite0.40.2 and
bundled SQLite3.53.2. No dependency or license choice was introduced. Provenance
remains in [storage sources](SOURCES_2026-10-22.md). Official
[SQLite page-limit documentation](https://www.sqlite.org/pragma.html#pragma_max_page_count)
and [Full result definition](https://www.sqlite.org/rescode.html#full) support the
failure mechanism; execution below establishes this implementation's behavior.

| Final binary | SHA-256 |
|---|---|
| x86_64, executed on both targets |`9d998b2f6991764ded0c68c98fc05ae3fe01fe08e561736c4b9e4f3a79c01dc3` |
| ARM64, built/audited only |`cd19d71ba6131e438c757741dd64117971e4959c6af28e83fefb316901ac47a7` |

## Actual emulator procedure and results

The coordinator ran A to completion before B, using the same frozen x86_64
executable. Both selected targets are Android15/API35/x86_64. The production app,
its test APK, private saves, model/runtime packages and other three emulators
were untouched. No emulator was provisioned, rebooted, rooted or reconfigured.

For each target, the bounded process owner ran these explicit operations:

1. Fsync a new sanitized start record. Choose a unique native basename fitting
   Linux's15-byte process name and verify no matching process exists.
2. Create a new synthetic root under `/data/local/tmp/` and its `tmp` child with
   mode700. Push the frozen binary there, set mode700 and verify SHA-256.
3. Execute the PIE directly with that `TMPDIR`,120s remote timeout and150s host
   deadline. Clear the child-helper environment variables first. Run serially
   with `--test-threads=1 --skip turns::tests::crash_child --color never`.
4. Require exact membership of the12 known substantive cases, unique successful
   records, final `12 passed /0 failed /0 ignored /1 filtered` summary, completed
   zero exit and host-client cleanup. The filtered case is only the auxiliary
   child entry; the actual seven subprocess exits still run inside their parent test.
5. Recheck executable hash and process absence. Remove only the hash-matching
   binary, then nonrecursively `rmdir` the owned temporary child/root. Unknown
   clients/processes or nonempty roots prevent a cleanup claim and further dispatch.
   Fsync the terminal record after cleanup. No arbitrary PID signal is used.

The core native invocation is reproducible after an explicit authorized push:

```text
adb -s <authorized-target> shell env TMPDIR=<new-owned-root>/tmp timeout -s KILL 120 <new-owned-root>/<unique-binary-name> --test-threads=1 --skip turns::tests::crash_child --color never
```

Both attempts passed all12 substantive tests: **24 passes**, zero failures,
skips, unfinished cases or retries. Each executes all seven commit-error stages
and all seven process exits (stage6 loses acknowledgement after successful commit),
plus real SQLite Full/recovery, cancel/commit races, writer contention,
migration rollback, configured-connection and canonical integrity cases.
Nested stages are not counted as additional top-level tests.
Both targets verified native process absence and host-client cleanup, and removed
their entire owned roots. No residual synthetic database or executable remains.
[Sanitized all-attempt results](ANDROID_FAULT_RESULTS_2026-10-22.json) retain both
start/terminal pairs, journal hashes, exact cases and binary/source identities.
Raw output stays ignored; no device identifier, temporary path, database or player
content is published. Counts, source hashes, privacy and final diff were checked.

## Limits and handoff

SQLite page limits exercise the real Full error path without filling an emulator
partition. This is not partition ENOSPC, hardware power loss, filesystem fault,
heap/power/thermal qualification, a Compose storage-error journey, physical-phone,
ARM64 execution, real inference or hosted-CI evidence. Existing app-build/JVM/lint
and earlier graphics results are separate; no APK was rebuilt or installed here.
The earlier renderer watchdog abort remains unexplained and unfixed.

M04.04 is locally verified for this bounded native slice and awaits owner review;
no checklist/full M04 gate is checked. M01.01 remains blocked on an authorized
phone. D03/M04.06 and M05 source ownership is preserved. Claims are handed off
on #8 with the PR and next runnable task.
