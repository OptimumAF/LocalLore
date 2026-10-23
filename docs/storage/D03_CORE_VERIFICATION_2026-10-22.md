# D03 shared snapshot and copy verification

Refs #24 (D03.03–D03.07), #8 (M04.06). Tested shared implementation
`c6f60a2`, with adversarial review cases through `c03b444`.
The final budget correction `e5ad25d` pins/sizes the same read snapshot before
allocating a private database copy; final compatibility runs below include it.
Native UI/filesystem evidence is separate; this report cannot accept that gate.

Windows x64; Rust/Cargo1.93.1, Python3.10; cached locked dependencies only.
Android compatibility: Java17.0.6, Gradle8.11.1, AGP8.10.1, Kotlin2.2.21,
SDK36/build-tools35.0.0, NDK29.0.14206865. No ADB, device, inference,
desktop-control input, desktop screenshot or unrelated-app operation.

| Actual command | Result |
|---|---|
| `cargo test -p locallore-workspace --test inspection_review --locked --offline` | PASS: 11 independent adversarial cases on core26e209f; all included in final full suite |
| `cargo test -p locallore-workspace --test database_copy --locked --offline` | PASS: 2 cases on final helperc6f60a2 |
| `cargo clippy -p locallore-workspace --all-targets --locked --offline -- -D warnings` | PASS |
| `python scripts/check.py host --offline` | PASS: final 137 Rust workspace tests, 191 Python tests (116+10+14+20+13+18), 4 fixture parity cases, 3 native-linker tests; fmt/strict Clippy |
| `python scripts/check.py android --offline` | PASS: both actual Rust JNI ABI rebuilds, app/test APKs, 38 JVM tests (0 failures/errors/skips), lint0errors/1 existing dependency advisory, APK permission/ABI/16KiB ZIP/ELF alignment audit |
| `git diff --check` | PASS |

Android's run reported78 actionable tasks:6 executed,72 up-to-date; both Rust
targets actually rebuilt the new sha2 dependency closure and all changed shared
crates in the first run (x86_64-linux-android14.68s, aarch64-linux-android14.39s).
The final post-budget run rebuilt both changed targets again (7.98s/8.17s),
completed in29s, and passed the same APK/JVM/lint checks. JVM source was
unchanged, so its four suites are incremental results: DiagnosticsController9,
Diagnostics9, DurableShell7, ShellViewModel13. No connected instrumentation,
emulator or physical-phone qualification is inferred. Existing advisory is
kotlinx-coroutines-android1.10.2 versus available1.11.0; no pin was changed.

The Android command used this worktree's isolated `target/gradle-home`, the
existing installed JDK/SDK, SDK-download disabled and offline flags. Required
cached JAR/AAR archives were copied read-only from the existing global cache
into the isolated task cache (747 files/1,285,200,643bytes); shared cache contents,
daemons and protected chat resources were not altered. After successful host
checks, package-scoped Cargo cleanup of this checkout's four shared crate
outputs reclaimed3.1GiB; local log files remained. No build artifact is committed.

The tests exercise coherent capture versus a real independent writer, stable
old capture after a later commit, expected-head rejection, scope/privilege
checks, hidden NPC-sheet/belief/fact/thread canaries across every output byte,
player-known secret retention, draft exclusion/nonmutation, mode/inventory/hash
and size tampering, checksum authenticity limitations, exact source/copy replay,
source read-only behavior and refusal to create/migrate missing/empty/foreign
inputs or overwrite an existing destination. Existing storage adversarial tests
also retain actual WAL-backup coverage and transactional fault/restart tests.
The additional tiny-budget case rejects before any destination is created.

Coordinator frontend `npm run check` and `npm run format:check` also passed on
the integrated D03 source. All23 source inputs in the committed native evidence
match the final app specialist checkout after Git line-ending normalization;
the original source hashes match its exact bytes. Restored normal bundle and
executable are build outputs, not falsely asserted identical to harness builds.

The new read-only Store opener verifies the existing schema and never creates
or migrates a source. The workspace helper calls the unchanged SQLite backup
implementation and reads heads from the resulting copy. Native code must still
approve/pin paths, warn that every story/draft is private, stage/finalize the copy,
and fence cancellation/window epochs. Host passing tests do not establish
those native guarantees or raw-copy privacy review.

See [contract](INSPECTION_SNAPSHOT_V1.md) and
[independent core review](D03_REVIEW_2026-10-22.md). No merge, D03 checklist
acceptance, real-story quality, offline traffic observation, installer or epic
completion is implied by this shared compatibility packet.
