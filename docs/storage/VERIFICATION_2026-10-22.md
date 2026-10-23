# SQLite foundation verification — 2026-10-22

Scope: M04.01 / [#8](https://github.com/OptimumAF/LocalLore/issues/8). This packet
is explicitly stacked on unmerged ownership follow-up [#35](https://github.com/OptimumAF/LocalLore/pull/35),
base `e5d1c5b`. That prerequisite must be accepted/landed first. Owner-merged
#18/#19/#20/#27/#32 establish the bounded foundations; their criteria and actual
evidence were reconciled in ticket comments. Disabled hosted Actions and an
unavailable physical phone do not create additional criteria for this storage
slice. No full M03/M04 closure or #35 acceptance is inferred.

## Implemented and reviewed

One Rust owner, `locallore-storage`, initializes schema 1, verifies identity and
exact schema shape, enables foreign keys per connection, and persists only
engine-validated root seeds. Composite keys constrain branch/entity/turn/event/
witness/projection references. Accepted-turn append/replay is not exposed yet.
SQLite online backup reserves a new destination, includes committed WAL frames,
and flushes the standalone file. Existing backups are never overwritten.
DDL, migration records and version markers share a short IMMEDIATE transaction;
no inference runs inside a storage call or receives a database handle.

Independent reviewer `review/m04-storage` exclusively supplied adversarial tests
and [review evidence](REVIEW_2026-10-22.md), source commit `73f0f33`, integrated
as `0ab4b27`. Native specialist `research/m04-storage-native` exclusively supplied
the smoke example, cross-build helper and dependency sources, source `67ac933`,
integrated as `e64cacf`. Both used separate worktrees. The coordinator owns
schema/API, manifests/lock, production fixes, integration, emulator runs and tickets.

Review reproduced real failures before correction:

- `LIKE 'sqlite_%'` hid allowed user objects such as `sqliteXprivate`, permitting
  nonempty version-0 adoption and altered version-1 schemas. Two tests failed.
- Reading identity before waiting for a write lock allowed a concurrent future
  version to be overwritten with version 1. The writer-contention regression failed.
- A separate Windows probe showed that flushing a read-only file handle fails;
  final backup flush uses a writable handle.

`7bb5d12` fixes literal-prefix inspection, rechecks identity under the migration
lock before backup/DDL and guards reserved-file cleanup. All regressions pass.
An initial attempt to call an unavailable rusqlite config enum failed to compile;
it was replaced with a supported unit assertion that extension loading remains
unauthorized. No new unsafe FFI or extension-loading API was added. The result
collector initially selected the wrong log encoding, then read the actual UTF-8
logs correctly; no application check was rerun or result replaced because of it.

## Actual checks

Windows x86_64, Rust 1.93.1; bundled SQLite 3.53.2 through exact rusqlite 0.40.2
and libsqlite3-sys 0.38.2. Official source, archive, license and actual compiler
evidence is in [SOURCES](SOURCES_2026-10-22.md) and its JSON manifest.

| Command/check | Actual result |
|---|---|
| `python scripts/check.py host --offline` | Passed: 57 Rust tests including 2 storage unit/14 adversarial tests; 63 Python tests; four fixture comparisons; three linker tests; format/Clippy |
| `cargo +1.93.1 run --locked --offline -p locallore-storage --example storage_smoke -- --directory target/storage-host-final` | Passed: two independent seeds reopened exactly, backed up/reopened, existing backup refused |
| `python scripts/check.py android --offline` with existing JDK17/SDK | Passed from new checkout: 78 executed Gradle tasks, both app-native ABIs, app/test APKs, 31 JVM tests, APK permission/ABI/ELF/ZIP audit |
| Android lint | Zero errors, one unsuppressed GradleDependency advisory for reviewed coroutines 1.10.2 versus cached 1.11.0 metadata; pin retained |
| `python scripts/storage_android_smoke.py --sdk <existing-sdk>` | Actual specialist build of both Android targets with existing NDK29/API26 target; final PIE/system-library/16KiB ELF audits passed |
| Exact final x86_64 smoke binary on emulator A | Passed: real bundled SQLite seed creation/reopen/backup/isolation; repeated output-directory refusal leaves database hash unchanged |
| Same exact final binary on emulator B | Same checks passed |
| `git diff --check` and staged equivalent | Passed |

The app APK hash is unchanged from the prior exact-#35 verification:
`1f2f9a90b0a482a81fb8fb7c269b94b431d9f3cc401bd11f55a38c1565bf1d95`.
No Compose instrumentation suite was rerun in this storage packet. The earlier
60 instrumentation passes belong to [the #35 reverification](https://github.com/OptimumAF/LocalLore/issues/7#issuecomment-6354715308).
The two new emulator observations here execute the standalone storage example,
not UI save/resume. Production Kotlin/JNI sources and permissions are unchanged.

## Reproduce the explicit emulator smoke

Both selected authorized targets report Android15/API35, x86_64,
`sdk_gphone64_x86_64`, 4096-byte pages. Inventory: five emulators, zero physical
phones. The other three were untouched. The example's source matches the final
coordinator API/schema exactly; a source diff against specialist commit `67ac933`
was empty for manifests/lock, API, schema, example and build helper.

From repository root, after the explicit cross-build, set the local transport and
a fresh unique remote path under `/data/local/tmp/locallore-storage-<uuid>`.
Equivalent commands used for each of the two targets:

```powershell
adb -s <authorized-target> shell mkdir -m 700 <fresh-owned-directory>
adb -s <authorized-target> push target/storage-android-smoke/rust/x86_64-linux-android/release/examples/storage_smoke <fresh-owned-directory>/smoke
adb -s <authorized-target> shell chmod 700 <fresh-owned-directory>/smoke
adb -s <authorized-target> shell sha256sum <fresh-owned-directory>/smoke
adb -s <authorized-target> shell -T timeout -k 2 20 <fresh-owned-directory>/smoke --directory <fresh-owned-directory>/case
```

The host selected one target at a time and verified the remote binary hash:
`5fae54a7ffaa415654f8e051285ccba650185e995cea6b77044f1adde6188b32`.
Each actual invocation exited 0 and reported `completed`, schema1, SQLite
`[3,53,2]`, FK enabled, two reopened/two backed-up stories, independent same IDs,
and existing-backup refusal. Repeating with the existing case directory exited
1 with fixed `directory` error before opening the database; before/after database
SHA-256 matched. Only exact known synthetic database/backup/binary files were
removed, then `rmdir` verified both directories empty; no recursive deletion.
Android's existing timeout bounded each invocation; it was not a cancellation
experiment or proof of model-process supervision.

Sanitized hashes, counts, lint messages and complete emulator results are in
[RESULTS](RESULTS_2026-10-22.json). Raw local outputs stay ignored under `target/`.
No weights, private stories, unique device IDs or raw diagnostics are published.

## Limits and handoff

This persists seeds, not accepted gameplay. The Compose engine remains in memory.
Outcome-only reducers, atomic/idempotent turn persistence, branch inheritance,
snapshot rebuilding, disk-full/process-death fault injection and UI save/resume
remain M04.02–.06 and later integration. The current historical migration fixture
is empty version 0 to initial version 1; no existing production save upgrade is
invented. Future schema versions require additional historical fixtures/backups.
WAL backup correctness was exercised on the host; the Android smoke uses default
database journaling. No power-loss, hostile import/filesystem, physical-phone,
ARM64/API26/36/16KiB OS execution, model/thermal/memory or hosted-CI result follows.

M04.01 is implemented/locally verified for review, unchecked pending owner
acceptance. No merge, release, access/protection/settings change or infrastructure
enablement. Claims transfer to the focused stacked PR. Next runnable task is
M04.02 outcome-only replay/reducers against these versioned storage constraints
(already claimed separately in [the follow-on packet](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6354858794));
M04.03 then commits events/projections/response atomically without generation
inside the transaction.
