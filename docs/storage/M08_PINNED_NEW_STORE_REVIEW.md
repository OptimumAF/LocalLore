# Independent integration review — Windows staging Store

## Corrected sidecar contract and independent recheck

The initially blocked leaf-only implementation is superseded by author source
`9ed53a4af0ec83da2050d12a3ca0fd07ac3ee932` (root integration `9c8634d`), with
the retained regression `a2add43` (root `17d5f56`) and corrected author report
`192d5ce` (root `3aa885e`). Root independently read the complete correction.
All four exact names are atomically reserved **before any SQLite call**:
main/-journal/-wal/-shm. Existing entries fail before connection. Sidecar guards
deny WRITE and DELETE sharing, so their owned empty bytes cannot become recovery
input; the main guard shares READ/WRITE for SQLite. Connection drops before all
guards. Staging alone selects and verifies MEMORY journal before normal
configuration/initialization. A pragma-only fix would be too late because its
preparation can trigger schema/hot-journal checks.

This is disposable staging, not a crash-durable active workspace. Ordinary Store
open and destination import keep their normal durable journaling. Constructor
errors can leave exclusively owned placeholders/partial staging files, without
deleting or reopening paths. Trusted retained ancestor handles remain required;
same-user modification of main-file contents is outside this namespace guarantee.
No ATTACH/multi-database executor is exposed. Non-Windows calls fail closed.

Root independently executed the corrected workspace: 297 passed/2 privileged
ignores at `9c8634d`; explicit ignored cases both passed, strict all-feature
Clippy passed. After accepted main through Android #46 was reconciled, clean
`e8228f0784d45e384d56e1b43848bf4478dec3dc` passed 298 workspace tests/2 ignores,
strict workspace Clippy, 9 evaluation tests, 30 native module+2 contract tests
(1 existing native ignore), strict native Clippy. Tests include all sidecar
refusals/outside-byte preservation, no-connect hooks, pre-SQLite and lifetime
write/delete/replace denial, actual archive import/turn/reopen and MEMORY-to-normal
DELETE mode distinction. Logs use `pinned-sidecar-*` under the task target.

Separate root desktop-caller execution on clean `fd6ae858` passed the exact
formerly failing journal regression, all 44 native modules+2 contracts and an
actual five-process archive UI cohort: 62 distinct assertions, 17 application-owned
WebView captures, true restart, no unexpected frontend/render errors. This is
evidence of corrected caller adoption, not attribution to the shared API author.
Artifacts are local `d08-archive-artifacts/archive-native-6355c29e-099c-4753-ae43-dc4e47e4ae22`;
summary SHA256 `23ff4585eb1cc3bdb0d2eb1a1ccbaffb1eb2255a03e6924caf294f03f3e919a9`.
Pickers use fixed development doubles; no system dialog/desktop control, model
generation or device execution is claimed. Final native UI evidence and review
belong in the separate D08 adapter PR.

No blocking finding remains in the corrected shared constructor. Final accepted
base compatibility and exact PR/check/merge status are recorded below when run.

Final shared integration reconciles accepted main `0b96d42` (including concurrent
Android PRs accepted by their owner) in clean tested tree
`8c51cc5eb4af9cedfa78f2143001c106b69756bf`. Full workspace all-feature tests:
**311 passed, 0 failed, 2 explicit privileged ignores**; strict all-target,
all-feature workspace Clippy passed. The earlier separate explicit run executed
both privileged reparse cases successfully; their constructor source is unchanged.
No concurrent Android source was edited by this integration.

### Final current-main gate

After the concurrent owner accepted Android archives, deletion, catalog and SDK
bridge work, root reconciled accepted `884cf3fe7ec144b8da082bef9a726d426d4aaf4c`
in clean tested tree `0e9d9a389bcbc6bdd185788e2fcd9107a3770673`.
This final combined source passed:

- Workspace all-feature tests: **371 passed, 0 failed, 4 explicit qualifiers
  ignored**. The two new staging reparse qualifiers were already explicitly run
  and passed on unchanged corrected constructor source; two other accepted
  workspace qualifiers remain unrun here.
- Strict all-target/all-feature workspace Clippy; native dev-harness tests
  **30 modules + 2 contracts**, 0 failed/1 existing ignore; strict native Clippy.
- Android offline build/lint/unit-test command above: **BUILD SUCCESSFUL in
  2m31s**, 78 tasks/33 executed/45 up-to-date; both JNI ABIs and both debug/test
  APKs built; **128 JVM tests, 0 failures/errors/skips**; APK permission/16KiB ELF
  audit passed. Existing JDK17.0.6, Gradle8.11.1/AGP8.10.1/Kotlin2.2.21,
  SDK36/NDK29.0.14206865; all build/Gradle outputs and TEMP/TMP task-owned.
- Formatting/whitespace checks passed. No frontend source changes are in this
  shared prerequisite; actual adapter/frontend execution is separately described
  above and belongs to the subsequent D08 PR.

Final local logs: `pinned-sidecar-current-workspace.log`, `-clippy.log`,
`-native.log`, `-native-clippy.log`, `-android.log`, `-apk-audit.log` under the task
target. The Android constructor's non-Windows refusal is compiled but not called
by Android; no device or native Windows dialog was operated. Earlier intermediate
source counts remain historical, not the final integrated test total.

## Historical leaf-only review — superseded

The following section describes the initial candidate. Its successful checks
did not cover the subsequently demonstrated journal-sidecar corruption and do
not alone establish current acceptance.

2026-10-23; M08.04/.06 and D08/D09 prerequisite, partial acceptance only.
Coordinator claim #12 comment 6361918794. Reviewed author source
`889cbfbd2de905ec5bb5e2b27ac749afa19ee44c` and documentation `7839c445` against
accepted main `a2bb6639eacaa9ac416788caf2fc7a6b70bf1392`. Integrated implementation
`cdd89e5`; tested clean tree `7cf24c7` on `impl/m08-archive-publication`.

## Finding and review

The native archive staging review found that retaining directory handles did
not protect a newly reserved SQLite leaf after its reservation handle closed.
SQLite subsequently opens a pathname. The new constructor retains its exclusive
creation handle across that open and the entire Store lifetime. Existing valid
databases, hard links, file reparses and dangling reparses fail at CREATE_NEW
before SQLite opens them. The fixed post-reservation test targets the actual
previous gap and proves rename/delete/replacement attempts fail there.

Independently read the complete two-file implementation/test diff and caller
contract. Connection is declared before the optional guard, so it closes first.
Error-path locals also drop Connection before the earlier guard. READ/WRITE
sharing permits bundled SQLite's normal handle, while omitting DELETE sharing
blocks leaf replacement. Requesting DELETE access would conflict with SQLite's
sharing contract. Existing normal open/upgrade behavior is only factored into
the common initializer. No schema, dependency or memory-wrapper behavior changes.

The initial leaf-only review found no additional leaf blocker. The guarantee requires retained trusted
ancestors and a private staging namespace. It is not protection against a
same-user writer modifying contents through compatible WRITE sharing or
planting sidecars. Failure can leave the constructor's own partial leaf; cleanup
belongs to the staging owner. No path-based deletion is attempted here.
Non-Windows calls fail closed; compilation on Android does not mean this Windows
constructor was executed there. Desktop caller adoption and UI evidence remain
separate acceptance work.

## Coordinator execution

Windows, Rust/Cargo 1.93.1, locked/offline; DEV/TEST debug=0, incremental=0,
task-owned TEMP/TMP and `desktop-publication-target`. Synthetic fixtures only.

```text
cargo +1.93.1 test --workspace --all-features --locked --offline --target-dir <target>
296 passed, 0 failed, 1 explicitly privileged reparse test ignored.
cargo +1.93.1 test -p locallore-storage --test pinned_new_store --locked --offline --target-dir <target> -- --ignored
1 passed, 0 failed: actual Windows file/dangling symlinks.
cargo +1.93.1 clippy --workspace --all-targets --all-features --locked --offline --target-dir <target> -- -D warnings
PASS
cargo +1.93.1 fmt --all -- --check
PASS
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <target>
9 passed, 0 failed.
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <target>
30 native module tests + 2 harness contracts passed; 1 existing test ignored.
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <target> -- -D warnings
PASS
git diff --check
PASS
```

These are Rust/native IPC module tests, not a new WebView/model/UI execution.
Local logs: `pinned-new-workspace.log`, `pinned-new-reparse.log`,
`pinned-new-clippy.log`, `pinned-new-eval.log`, `pinned-new-native.log`,
`pinned-new-native-clippy.log`, under the task target. Author's separate default
and all-feature storage suites each passed 91 tests plus the explicit privileged
case; see the implementation report for their exact commands.

No desktop control, protected chat/resources, device use, model access, system
installation, repository settings, concurrent Android changes or release.
Owner-authorized merge follows exact-head checks; no independent human approval
is fabricated. Full D08/D09/M08 checkboxes remain open.
