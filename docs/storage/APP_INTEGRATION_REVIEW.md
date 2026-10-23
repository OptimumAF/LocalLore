# Shared app storage integration review — 2026-10-22

Independent review used `review/app-storage`, beginning at `eac0b99`, with its
own Cargo output and synthetic temporary databases. Production files were read
or copied from coordinator/app commits; this reviewer authored only this report
and `crates/locallore-workspace/tests/ownership_review.rs`. No desktop control,
input injection, desktop capture, ADB, emulator/model execution, global Gradle
operation, or changes to the protected runtime-control chat/worktree were used.

## Demonstrated findings and disposition

| Finding at `eac0b99` | Concrete effect | Resolution inspected and tested |
|---|---|---|
| Stale local Engine after a different Host commits | Existing-session resume returned revision 0; observing the exact committed receipt still left player snapshot at revision 0. | Coordinator `cbc2baa` reloads validated persisted Engine on resume, submit and observed terminal outcomes. |
| New valid request checked against stale local Engine | Store accepted a request at revision 1, then stale preview rejected it and persisted `failed`. | Same refresh change; valid revision-1 request remains queued. |
| Worker completion ignored another owner's cancellation | A delayed preparation returned `ready` after another real Host had cancelled the same key. | `cbc2baa` checks persisted status and refreshes before worker publication. |
| Failed cancellation write exposed a local terminal outcome | Injecting `Busy` at the persistence port left a durable draft but preparation claimed `cancelled`. The first fix rejected that response, but a subsequent status lookup still claimed cancellation. | Coordinator `f0030f5` restores provisional queued cache state after failed terminal write; both immediate response and later lookup now avoid false cancellation. |
| Catalog admission was outside the writer transaction | At 255 synthetic stories, two simultaneous Host creates both succeeded, admitting 257 and making the bounded catalog unreadable. | `cbc2baa` rechecks the cap under the IMMEDIATE insertion transaction. Exactly one final slot is admitted and the library remains readable. |
| Transient post-generation status error stranded a worker lease | A fixed `Busy` injection left local phase `running` after worker count reached zero, preventing another prepare. | Coordinator `7bf5b7e` resets only an unfinished running cache entry to queued on the failed observation; original-key retry can prepare/commit one effect. |

The cancellation fault adapter delegates all successful calls to the real Store;
only a fixed acknowledgement/cancel failure is injected. The lost-commit-ack
test commits through real SQLite, drops only the response, then verifies original
key recovery and one receipt/effect after reopening. It does not simulate every
filesystem failure. Existing storage crash/disk-full checks remain separate.

## Executed verification

Final independent tree includes coordinator fixes `cbc2baa`/`f0030f5`/`7bf5b7e` (local
cherry-picks `26cf1e8`/`0d82a88`/`5a5bbee`) and Android handoffs
`0f30185`/`f7d3955`/`2eeacbd`, which align the locked dependency graph. Commands:

```powershell
$env:CARGO_TARGET_DIR = Join-Path (Get-Location) 'target-review'
cargo test -p locallore-workspace --locked --offline
cargo clippy -p locallore-workspace --all-targets --locked --offline -- -D warnings
```

Both returned exit 0. The suite passed 3 existing durable-Host tests and 15
independent ownership tests. The latter run with the default Rust test runner;
a fixture mutex serializes expensive database setup across these tests while
preserving the multiple real Hosts and worker threads raced within each case.
This avoids a 255-story setup starving the bounded delayed fake provider.
No elapsed-time or performance qualification is inferred from the test.

Covered behaviors include interrupted draft restart without automatic effects;
exact committed-request retry; cross-story/session and Play-observer isolation;
external commit cache refresh; external terminal versus running preparation;
12 real independent-connection cancel/commit races; close during preparation;
no Host/database writer lock retained during fake generation; lost commit
acknowledgement; enum-only foreign/unopenable database failure without replacement;
and concurrent final-slot catalog admission. This is finite adversarial evidence,
not a proof of all interleavings or production/device qualification.

## App integration read review

Android `0f30185`/`f7d3955` opens the shared owner in the app's no-backup directory
on IO workers. The bounded JNI registry removes closed handles and fences captured
control calls with a native lease gate. Preparation bypasses that gate and is
fenced by Host session closure. Kotlin retains uncertain operation keys, validates
the complete returned request, obtains transcript from persisted player snapshots,
and preserves cancellation intent during recovery. No additional concrete Android
defect was found in this read review. This reviewer did not run Android builds or
instrumentation; coordinator/app-agent evidence must identify those separately.

Desktop `75a30d5` had a native lifecycle finding handed to the coordinator:
`host_call` awaits lazy initialization and a blocking dispatch without a window
lease. `Destroyed` skips cleanup while the OnceCell is empty; a pending Create or
Resume can then allocate after destruction. Even with an initialized Host,
asynchronous `close_all` alone cannot fence a captured later Create. Required
resolution is a window lifetime/epoch invalidated synchronously at destruction
and checked before dispatch, including calls waiting for initialization.
App-agent fix `bddfa0d` now supplies that fence. Initialization and ordinary
control dispatch run through the same native lease gate; Destroyed invalidates
the epoch synchronously before cleanup waits on that gate. Captured old calls
cannot allocate after cleanup, and reopening waits for the closed epoch before
granting a new window lease. Preparation remains outside the gate and is covered
by Host close/session fences. Window labels and the Tauri capability pattern
both use `main-*`; exact epochs are checked natively, not granted by renderer text.
No further concrete lifecycle defect was found in the final source read review.

The two native lease unit tests were independently compiled and executed from
the final desktop agent source, with output in this review's dedicated target:

```powershell
rustc --edition 2021 --test '../LocalLore-desktop-durable/apps/desktop/src-tauri/src/lease.rs' -o target-review/lease-tests.exe
& ./target-review/lease-tests.exe
```

Both passed (exit 0): captured Create after destruction cannot dispatch/write;
delayed initialization is fenced and reopen waits for cleanup. These are native
lease tests, not a new actual-window or packaged-app execution claim. Coordinator
and desktop-agent evidence must separately identify full native harness runs.

Both app startup paths currently select the first story in stable opaque-ID order;
they do not persist a last-selected story preference. Explicit library selection
supports other saves. Interrupted draft metadata does not imply automatic replay,
free-text recovery, durable branch forks, imports, readable exports, encryption,
power-loss qualification or real-model inference.

Owner acceptance and merge remain pending. This review grants neither.
