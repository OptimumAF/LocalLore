# Archive interruption verification — 2026-10-23

M08.06 partial implementation evidence, stacked on open/unmerged PR78.
Full milestone and owner acceptance remain open. See the
[contract](ARCHIVE_RECOVERY_CONTRACT.md) and
[all-attempt aggregate results](ARCHIVE_RECOVERY_RESULTS_2026-10-23.json).
The [independent review](ARCHIVE_RECOVERY_REVIEW_2026-10-23.md) checks source and
actual retained evidence; it is not another device run or owner acceptance.
The final executable/test source is `8eb3bdf`; later changes are documentation only.
No production engine, Store, Host, schema, provider, dependency or permission changed.

## What was actually interrupted

Android checks deliberately force-stop a live, resumed MainActivity process at
two UI boundaries: validated import preview before consent, and acknowledged
committed import before explicit opening. Each requires a fresh flushed marker,
exact source bytes/checksum, matching current app PID and live owned arm client.
The target process must disappear before client/provider cleanup and relaunch.
These are deliberate app force-stops, not Android low-memory termination or
termination during the native transaction. The arm never returns a passing test;
the expected runner crash signature is classified separately.

After preview interruption, relaunch revives no archive consent/guard/picker or
success state and imports nothing. Fresh actual chooser validation and Cancel
work. After committed interruption, the original ID exists exactly once, native
reexport equals the exact source before play, the actual saved-story UI opens
it, one potion gift succeeds, another is refused, and native reopen retains
exactly the wait and gift receipts. Prior library entries and the previously
selected story's full native player snapshot are preserved; selection is restored.
No native handle/token is persisted or treated as globally unique across processes.

Three independent host tests terminate actual owned child processes at existing
Store import polling barriers: after the story INSERT (poll2), after all three
branches have replayed before commit (poll38), and after commit before the worker
acknowledges completion. Actual reader/catalog and second-writer Busy/free checks
establish the transaction boundary before termination. Owned kill/reap/reopen
leaves old or complete history, never partial rows. Exact reexport, original
receipt retries, all three branch canonical states and player/Mira/Sable/Oren
contexts, hidden/sibling canaries and the retained control story are checked.
Same-ID import conflicts; no identity remapping or duplicate spending occurs.
The fixture's38-poll expectation deliberately fails on source drift.

## Actual checks

- `python scripts/check.py host --offline`: **311 workspace Rust +3 linker
  +223 Python** tests pass, including the three new real-process tests and
  **17 original recovery orchestration fault tests**. Formatting, strict Clippy
  and fixture audits pass. One explicitly ignored IPC worker is invoked by the
  parent qualification tests and is not a standalone qualification pass.
- Isolated Gradle application/test assembly, fresh JVM test rerun and lint:
  **60 JVM**, zero failures/errors/skips,79 tasks (33 executed/46 up-to-date).
- Configured `python scripts/check.py android --offline`: production build/audit
  passes,78 tasks (32 executed/46 up-to-date). Both ABI ELF/ZIP16KiB alignment,
  seven archive JNI exports, receiver-only application permission and exclusion
  of test providers from the application manifest pass. Lint has zero errors
  and one existing version warning in both builds.
- **Final-source two-emulator cycles:** four intentional interrupted arms and
  **four passing relaunch verification tests**, plus **42 ordinary archive
  regression passes** (21 per device). Zero unexpected failures/skips/unfinished
  tests. The initial cycles are retained separately: another four interrupted
  arms and four passing verifications. Totals are **eight interruptions and50
  passing test invocations**, not58 passing tests.

Execution used the two selected API35/x86_64 emulators. Fresh inventory showed
four emulator entries and no available physical phone. App APK SHA-256 remains
`5a058eef62d1e56e9326ac71a959bd1205ae9a96820b42626abda6530e93944f`;
instrumentation APK is
`ffbbaab9b7ebeeb4322904567dfc66308b299463bdffe2b3074520aa1132fa08`.
Artifact/package identity checks precede mutation. Only the isolated pair was
reinstalled with `-r -t`; prior package hashes and app data were preserved.
All cycles/cohorts confirm client cleanup and absence of both owned packages'
processes, including provider subprocesses. No reset, uninstall, emulator
restart, model copy, benchmark, private upload, merge or release occurred.

## Discoveries and retained attempts

Independent source review found a parser accepting a terminal before its start.
A synthetic reordered transcript demonstrably passed pre-fix `bf1fd9a` and is
rejected by the fixed parser with `instrumentation_order`. Exact start/terminal/
runner ordering, duplicate runner codes and interrupted-arm crash signatures
are now checked. Partial case progress is retained if a later relaunch fails;
a failed verification cannot erase an already observed interruption. Sticky
unknown cleanup cannot be overwritten by a concurrent client's later success,
even if evidence logging fails. Missing/stale markers, changed APKs/PIDs, early
arm exit and acknowledged stop with a surviving process all fail closed.

The initial and final emulator cycles all passed and remain separately hashed;
the final rerun followed the parser/accounting correction. The first host run
passed311 Rust+3linker+221Python; the final223 includes the two added regressions.
The native author reported an initial command-name compile collision and one
Clippy style failure, both corrected before integration; final coordinator
host checks independently cover the integrated file. No qualifier test failed
after those author setup/source corrections. Native child output is bounded,
and fresh synthetic directories/logs are retained without filesystem deletion.
Raw Android/SQLite/baseline/PID/run records remain private; public evidence has
only aggregate outcomes, fixed categories and artifact hashes.

## Reproduction

Build the isolated app as in the [chooser procedure](ARCHIVE_CHOOSER_VERIFICATION_2026-10-23.md),
adding the new recovery test source. Configure Java17 and the installed SDK/NDK,
then build without downloads or data reset:

```text
gradlew :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreArchiveVerification=true --offline --no-daemon
cargo test -p locallore-storage --test archive_interruption --locked --offline
```

Verify package identities before installing only the isolated pair. The explicit
runner performs no installation and refuses mismatched artifacts. Use a fresh
output directory per attempt and an authorized selected emulator:

```text
python scripts/archive_recovery.py --serial <selected-serial> --alias A --adb <sdk/platform-tools/adb> --app-apk <isolated-app.apk> --test-apk <matching-test.apk> --output-directory <new-private-directory>
```

Do not manually run an arm without its external owner: it intentionally waits
for termination and fails after its bounded lease. Do not interact concurrently
with the selected app/picker. Ordinary regression selectors and raw terminal
records are distinct from deliberately interrupted arms. Repeated runs retain
synthetic imported stories and consume finite storage/admission capacity.

## Remaining gates

No Android mid-import write interruption, low-memory saved-state restoration,
physical power loss, actual disk-full/partition ENOSPC, arbitrary-provider hard
preemption, ARM64 execution, real-model quality or phone feasibility is qualified.
M01.01 remains blocked on an authorized available physical phone. M08.06 and
owner acceptance stay open. Next runnable work is bounded archive storage-failure
injection with rollback/retry evidence; it must remain distinct from physical
partition exhaustion and reuse the shared Store authority.
