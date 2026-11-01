# Query2 unsigned deadline integration correction

Refs #13 (M09.04), #14 (M10.02). Prepared during the owner-authorized PR-stack
integration from `bedffe4ecc140df4deba89a5bb71b9cc2021714c`.

A native accepted promise can have deadline `u64::MAX`. Query2 previously
serialized that field as a JSON number, while the Android inspector accepted
only signed Int/Long values. The Promises page and its witnessed History event
therefore refused an otherwise valid accepted history. The newer player
presentation DTO had already addressed this representation issue separately.

Query2 now serializes only promise deadlines as canonical decimal strings,
including nested TurnDiff values. Native typed rows, engine state, requests,
receipts and Query1 bytes retain their existing numeric values. A typed row
serializer supplies both Page output and Query2 search/cursor/byte accounting;
it preserves the field order used by exact same-lens scoped-event lookup.
The Android decoder checks the full unsigned decimal range without floating
point or narrowing, and keeps exact Int/Long compatibility for frozen older
Query2 fixtures. The existing negative case for string `120` becomes `0120`:
canonical decimal strings are now specified valid input, while leading zeros
remain invalid. Other negative assertions remain.

## Executed checks

All commands ran in physical
`D:\Worktrees\LocalLore-merge-promise-deadline-20261101`, with TEMP/TMP/TMPDIR
and Java temporary output on D:, task-local Rust/project build output, existing
D: Cargo/Gradle caches, and installed Java21/Android SDK unchanged.

- Final unchanged Rust regressions on the original implementation: two tests,
  one expected numeric-versus-decimal-string failure and one Query1 pass.
- Final unchanged JVM regressions on the original implementation: three tests,
  one expected canonical-string decoding failure, no errors/skips.
- `cargo +1.93.1 test --locked --offline -p locallore --features host --test
  query2_unsigned_deadline --test inspection_query --test m08_query_v2 --test
  m08_query_v2_message_identity_review -- --nocapture`: 34 pass, zero failures.
  The new tests use actual accepted Engines with deadlines 120, signed maximum,
  signed maximum+1 and unsigned maximum, verify Promises/History/TurnDiff,
  same-lens event search, native state/request conservation and Query1 numeric
  row byte compatibility.
- `:app:testDebugUnitTest` with selectors `PromiseUnsignedDeadlineTest`,
  `PromiseStoryRecordTest`, `Query2StoryRecordTest`, offline and
  `-x :app:buildRustAndroid`: 38 pass / three XML suites, zero failures/errors/
  skips. Production Kotlin and all ordinary unit-test sources compile.
- Warnings-denied Clippy for the host-feature library and new Rust test passes.
  Scoped rustfmt and `git diff --check` pass.

Raw logs and baseline XML remain under the worktree's `.verify` directory.
Earlier failures remain separate: a PowerShell Gradle argument tokenization
error, initial native fixture deadlines preceding the Lantern Quay clock, and
an assertion accidentally counting the seed's separate same-deadline promise.
The corrected final baseline and green use unchanged final test bodies.

These are native host and JVM checks. JNI, Android JSON parser execution,
Compose journeys, emulator/device/model work, full combined-stack gates and
owner acceptance are not established by these results. No SDK/global cache,
signing, model, emulator, production ledger or private-story action occurred.
The parent coordinator owns combined checks and final merge decisions.
