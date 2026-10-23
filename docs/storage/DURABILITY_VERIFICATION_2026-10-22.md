# Shared durability verification — 2026-10-22

Scope: #8 M04.02/.03 and applicable .04/.05/.06 root-history slice. Not whole
milestone acceptance. Branch `impl/m04-durable-turns` depends on unmerged #38
(`75abe3900bb4d3100c86daac81534431a2f1aae8`) and its #35 prerequisite. Dependent
PR targets `impl/m04-sqlite-schema`; neither prerequisite is merged by this work.
Source production fixes end at `6873bc8`; independent test integration `c0c9ca5`;
final host gate ran at `2192ab4` with only documentation edits in the working
tree. Later handoff changes documentation/results only. Exact PR/head is on #8.

## Bounded task evidence

| Task | Implemented / observed | Remaining boundary |
|---|---|---|
| M04.01 dependency | Reused the same Store/schema1/migrations/FKs/online backup from #38; no new dependency, lockfile change or migration. Module registration only after M04.01 handoff. | #35/#38 owner acceptance/landing still required. |
| M04.02 | Strict bounded `Engine::restore`, complete canonical-byte and receipt equality, context equality for every observer, 384 seeded attempted-prefix checks plus existing 10,000 rule attempts. Nine new core tests. | Deterministic v1 root history only. Future random mechanics require a versioned recorded-outcome contract; persistent forks/import not added. |
| M04.03 | Durable explicit draft, scoped unique turn ID/request, expected revision, exact receipt/status retry; events/witnesses/projection/response/status/head share one transaction. No provider in Store. | App adapters must call this API on an owning IO worker; existing UI is not switched to durable sessions. |
| M04.04 | Seven error-injection stages, seven subprocess exits without SQLite destructors, actual SQLITE_FULL, real-thread cancel/commit and multi-owner stale/Busy tests; either old or complete new canonical state. | No hardware power-loss, storage-device failure, mobile lifecycle execution or UI branch-switch qualification. |
| M04.05 | Same names/item/turn IDs in separate stories remain isolated; unknown branches rejected; restored observer contexts stay scoped. Composite schema constraints reused. | Persistent alternate branches are explicitly unsupported. |
| M04.06 | Resume validates receipts/head/all normalized event/witness rows, ignores missing/stale/wrong projection, and repairs only derived cache. Existing consistent backup resumes the same canonical bytes. | No new archive/export format, cryptographic authentication, history migration fixture or large-history acceleration claim. |

The root turn API lives in `crates/locallore-storage/src/turns.rs`. Receipt and
AcceptedEvent remain non-Deserialize with read-only getters. Restore privately
checks duplicate keys, complete resolved envelopes and sequential request replay;
no accepted event can be constructed by parsing an arbitrary proposal. Full
receipt history is compared with normalized storage rows and persisted head,
so a valid prefix cannot hide an omitted committed suffix. Internal normalized
event bytes must match the owner's canonical serialization exactly.

## Exact commands and observed results

Windows 11 x64; Rust/Cargo 1.93.1; existing MSVC/Windows SDK. Bundled SQLite
3.53.2 through #38's pinned rusqlite 0.40.2/libsqlite3-sys 0.38.2. No model,
tokenizer, GPU backend, new dependency or permission. All following commands
exited 0 unless an expected fixture refusal is stated.

| Command | Result |
|---|---|
| `python scripts/check.py host --offline` | Final pass: **89 Cargo test entries**, including one auxiliary child-test entry; 88 substantive entries. Breakdown: 26 domain, 9 restore, 5 runtime example, 10 JNI ownership/boundary, 39 storage (10 unit including child helper, 14 schema adversarial, 9 durability review, 6 public durability). Four fixture comparisons, **63 Python tests**, three native-linker tests, format and all-target Clippy also pass. Raw log stays ignored at `target/checks/durability-host-final.log`. |
| `cargo test -p locallore --features host --locked --offline` | 9 host + 26 domain + 9 restore + 5 runtime-spike tests pass. No D02 PlaySnapshot test is inferred: that independent #36 is not this branch's base. |
| `cargo clippy -p locallore --all-targets --features host --locked --offline -- -D warnings` | Pass. |
| `cargo test -p locallore-storage --locked --offline` | All storage tests pass, including private fault stages and actual subprocess exits. Final full host gate includes the same cases plus reviewer tests. |
| `cargo run -p locallore-storage --example durable_smoke --locked --offline -- --directory target/durability-host-verified` | Actual on-disk synthetic spend/reopen/retry/observer/consistent-backup proof; complete receipt and canonical bytes equal, revision 1, zero model calls, FK true, SQLite 3.53.2. |
| `python scripts/storage_android_smoke.py --sdk <existing-sdk> --example durable_smoke --output target/durability-android-final` | Both x86_64 and ARM64 final durability binaries build/audit offline; Android PIE, only libc/libdl/libm needed, SQLite bundled, 16 KiB load alignment. No ADB/device execution. |
| `python scripts/check.py android --offline --clean` | Fresh-checkout clean invocation: **79 tasks, 78 executed/1 up-to-date**; both Rust JNI ABIs, app/test APKs, **31 JVM tests**, zero failures/errors/skips; lint and APK permissions/ABI/16 KiB ZIP+ELF audit pass. |
| Android lint readback | Zero errors; one unsuppressed GradleDependency warning for reviewed coroutines pin versus cached newer metadata, matching #38. No pin changed. |
| `git diff --check` / staged equivalent | Pass. |

Android used existing JDK17/SDK variables (no download/license prompt):

```powershell
$env:JAVA_HOME='C:\Program Files\Android\Android Studio1\jbr'
$env:ANDROID_HOME="$env:LOCALAPPDATA\Android\Sdk"
python scripts/check.py android --offline --clean
```

JDK 17.0.6, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21, SDK36 / Build Tools35 /
NDK29. Android APK components do not link the storage crate yet. The separate
cross-build exercises actual storage/core code; build success is not Android
execution. No new emulator, phone, model, desktop window or other application
was controlled or captured. No injected input, activation or screenshot used.

## Failure and adversarial disposition

The unit fault stages are before writes, first event, all events/witnesses,
projection, completed response/status, head update, and after successful commit.
Error tests let Rust unwind/rollback. Subprocess tests instead exit 77 without
running destructors, reopen the journaled database, and reconcile/retry. The
after-commit case deliberately loses the acknowledgement and returns the original
receipt on retry. Both events of the give+wait turn appear together or neither
does. SQLITE_FULL is induced with SQLite `max_page_count`, not a generic mock
error. It leaves the persisted draft and old canonical bytes/head intact.

Independent reviewer in a separate worktree reproduced four concrete gaps and
provided regressions before correction:

1. Generic JSON Value parsing collapsed duplicate fields in normalized events.
   `a2f502d` requires exact canonical event bytes.
2. Draft enumeration could substitute another row's embedded request key.
   `a2f502d` directly matches selected row ID/revision with request data.
3. An oversized unused retry narration rejected before resolving a winning
   recorded request. `bb1e9f9` resolves committed receipt first, matching Engine
   request-based idempotency. New provisional output cannot hide/replace it.
4. An already-open store missed a scoped orphan witness inserted via external
   FK bypass. `6873bc8` counts all scoped witnesses as well as checking each
   expected event. Reopening already caught the FK violation; live reads now
   also reject it without repairing evidence.

Final nine independent tests pass, including 12 canonical-table tampering cases,
count/byte admission limits, rejected-output budget, terminal reopen/retry,
projection repair and fixed error privacy. Full report:
[DURABILITY_REVIEW](DURABILITY_REVIEW.md). Core restore specialist contributed
`7ef4fe8` → `6bc1ec1`; independent tests `51fbb4f` → `50af2b3`, orphan regression
`bfec3c2` → `c0c9ca5`, final review `de72af7` → `2192ab4`. Coordinator owns
production/storage integration. No review grants owner acceptance.

The first integration compile correctly exposed rusqlite's signed integer API;
explicit checked revision conversion replaced unsupported u64/usize SQL bindings.
An initial reviewer FK-protected fixture setup was corrected before the final
tampering matrix. Failed probes are not claimed as passes.

## Artifact identity and limits

[Sanitized results](DURABILITY_RESULTS_2026-10-22.json) contain source-input,
canonical projection and example/Android artifact SHA-256 values, plus observed
counts. Raw logs/databases/binaries remain ignored in `target/`; no private text,
home path, transport/device identifier or story dump is published. Hashes bind
synthetic evidence, not cryptographic authenticity of an editable database.
Canonical encoding is the Engine's ordered-map/set, fixed-struct JSON, with no
floats; it excludes transient diagnostics entirely. Resume compares complete
bytes and complete receipts, not only hashes.

Root replay is bounded to 4,096 retained turns and 16 MiB combined stored
request/receipt data; receipt 64 KiB, projection 256 KiB. No eviction conceals
idempotency. Full validation inside the writer transaction is bounded correctness
work, not a measured long-history performance claim. No inference runs there.
All Store calls are blocking; UI integration must move them to its owning IO
worker and preserve cancellation/session/revision guards.

M04 remains open: no UI durable workspace/library/resume wiring, persistent
fork/rewind, general recorded-random outcome reducer, archive import/export,
future history migration, model, power-loss simulation, ARM64 execution,
physical phone, API26/36/16KiB-OS execution or hosted-CI qualification. Existing
M04.01 Android seed-smoke executions are historical evidence, not executions of
this new durability binary. Next runnable slice after prerequisite review is
shared native/app adapter save/resume using this Store, with D03 owning desktop
workspace discovery and readable inspection export. No merge, release or
repository-settings change was performed.
