# Shared root-turn durability and resume

This follow-on to M04.01/[#38](https://github.com/OptimumAF/LocalLore/pull/38)
implements the bounded deterministic-v1 root-history slice of #8 M04.02/.03 and
related .04/.05/.06 recovery/isolation checks. It uses the same Rust `Store`,
schema 1, bundled SQLite and Engine. No second database owner or Kotlin/desktop
ledger is introduced. The dependent PR targets `impl/m04-sqlite-schema`; #35 and
#38 must be accepted/landed first. Checklists are not self-accepted.

## Run and verify

From repository root with pinned Rust 1.93.1 and the locked dependencies cached:

```powershell
python scripts/check.py host --offline
cargo test -p locallore-storage --locked --offline
cargo test -p locallore --features host --locked --offline
cargo run -p locallore-storage --example durable_smoke --locked --offline -- --directory target/my-fresh-durability-proof
```

The example refuses an existing directory. It writes only a synthetic database
and consistent SQLite backup there. It spends the last potion, drops/reopens
the store, compares full canonical bytes/receipts, checks Sable's isolation,
retries without another effect, then resumes the backup. Output contains only
fixed categories/counts/booleans/versions. It uses no model or UI. Choose a new
directory for each run; `target/` remains ignored. Do not use private stories.

Explicit Android cross-build/audit, with existing SDK/NDK and installed targets:

```powershell
python scripts/storage_android_smoke.py --sdk "$env:LOCALAPPDATA\Android\Sdk" --example durable_smoke --output target/durability-android
python scripts/check.py android --offline --clean
```

The helper builds both x86_64 and ARM64 PIE examples, audits bundled/system
dependencies and 16 KiB ELF load alignment, and never invokes ADB. Neither
cross-building nor an app APK build proves execution of durable turns on Android.
[Dated results](DURABILITY_VERIFICATION_2026-10-22.md) distinguish them.

## Ownership and API

All Store calls are blocking and belong on an app-owned IO worker. The native
adapter selects its private database path. Models and frontend text receive
neither a path/SQL interface nor a connection. API inputs are typed domain
requests/proposals and bounded narration; errors expose enum categories only.

| Method | Meaning |
|---|---|
| `begin_turn(request)` | Persist an explicit request as a draft after scoped preflight; exact duplicate returns the stored phase/receipt before stale checks. Releases the transaction before returning. |
| `resume(scope)` | Read one coherent root-branch snapshot, validate/replay complete receipts and normalized ledger, return Engine plus `projection_needs_rebuild`. Never loads cached projection as canon. |
| `drafts(scope)` | Discover interrupted explicit inputs; does not apply them. Checks row key/revision against embedded request before returning. |
| `turn_status(request)` | Exact-request lookup; changed payload with the same scoped turn ID yields `RetryMismatch`. |
| `commit_turn(request, proposal, narration)` | Require an existing draft, recheck status/head, validate with the shared engine, atomically append events/witnesses/projection/complete receipt/status/head. A committed exact request returns its recorded receipt before considering unused new output. |
| `cancel_turn` / `fail_turn` | Transition a draft only. Canon is unchanged. A winning committed turn stays committed and returns its receipt. |
| `rebuild_projection(scope)` | Validate canonical history under the writer lock and replace only its derived projection cache. |

Generation occurs between calls, outside any write transaction. No provider is
invoked inside Store. Cancel and commit serialize on SQLite's IMMEDIATE writer
lock; a stale draft is marked `stale`, without effects. Terminal failed/cancelled/
stale IDs remain terminal; a deliberate new attempt needs a new ID. Exact retry
after a lost commit acknowledgement returns the same full receipt after reopen.
The API holds no mutable in-memory Engine across calls, so a failed transaction
cannot leave an ahead-of-disk canonical cache.

History consists of validated seed plus complete receipts, cross-checked against
the branch head, normalized accepted events and every witness row. Missing suffix,
extra event, wrong turn/revision/scope/version/provenance/effect/witness or
inconsistent request fails closed. The owner writes normalized event JSON in
canonical byte order; altered encodings, including duplicate keys, are rejected.
Complete receipt restore allows reordered object keys but rejects duplicate keys
recursively. Receipt/AcceptedEvent remain Serialize-only, with read-only getters;
there is no arbitrary accepted-event deserializer or public constructor.

`Engine::restore` reconstructs deterministic v1 rules and compares every complete
recorded resolved envelope. It calls neither inference nor RNG. Current v1 has
no random rule draws. This is not a generic outcome reducer for future random
mechanics: those must add a versioned recorded-outcome contract instead of
rerolling during restore. Root branches only; persistent forks/ancestry/import
need explicit contract evolution, not silently flattened history.

Limits: 4,096 retained turn IDs per root branch; 16 MiB combined request/receipt
ledger; 65,536 bytes per receipt; 262,144-byte projection cache, existing request
and seed limits. No idempotency record is silently evicted. Reaching a cap
refuses new data; pagination/retention/schema evolution is future work.
SQLite signed revisions use explicit checked conversion from domain `u64`.

Full replay validation occurs inside the bounded commit transaction before its
writes. It is correct for this small slice, not a large-history latency claim;
future validated accelerators may reduce that work without replacing history.
Current cache bytes are compared exactly. Missing/stale/wrong cached state can
be ignored and repaired; corrupt canonical history is an error, never fabricated
or overwritten from a cache. Byte equality is stronger than comparing a digest;
dated smoke evidence also records SHA-256 of the canonical projection encoding.

## Failure checks and remaining integration

Tests inject errors at seven commit boundaries, exit child processes without
running SQLite destructors before/after commit, force actual `SQLITE_FULL` with
SQLite page limits, and race real independent connections/threads. They check
old-or-complete-new state, exact retry and receipt/head/normalized-row agreement.
Fault hooks compile only into private unit tests, with no production environment,
remote control, SQL or general execution API. This does not simulate power loss,
hostile filesystems or every possible OS/storage failure.

The [native Android fault follow-up](ANDROID_FAULT_VERIFICATION_2026-10-22.md)
executes these private tests on two selected emulators and adds actual
last-potion page-exhaustion/reopen/retry cases. The cross-build helper's explicit
`--unit-tests` mode builds audited native test executables without operating a device.

Databases/backups are plaintext app-local data, subject to existing OS/backup
policy. No upload occurs. Consistent backup uses the existing SQLite backup API,
including WAL handling; no live main-file copy is introduced. No new dependency,
migration or permission is added by the turn layer.

The subsequent [application adapter slice](APP_INTEGRATION.md) opens this Store
on background workers and routes Compose JNI and desktop begin/status/commit/
resume through it, with saved-story library/path policy and native lifecycle
tests. The original core turn layer remains independently testable. Readable
inspection exports, archive formats and author corrections are separate work;
current acceptance remains on #8 and #24.

Primary behavior references checked 2026-10-22:
[SQLite transactions](https://www.sqlite.org/lang_transaction.html),
[atomic commit](https://www.sqlite.org/atomiccommit.html),
[rusqlite 0.40.2 rollback/commit](https://docs.rs/rusqlite/0.40.2/rusqlite/struct.Transaction.html).
Implementation tests establish this crate's behavior; upstream guarantees alone
do not qualify a device or filesystem. Existing pin/license/native provenance is
in [M04.01 sources](SOURCES_2026-10-22.md).
