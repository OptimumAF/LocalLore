# Archive interruption and recovery proof

M08.06 bounded follow-up to PR78. Production archive v1, Store/Host/schema,
MainActivity callbacks and the seven NativeArchive JNI calls stay unchanged.
There is no new dependency, model, product fault hook or gameplay authority.

## Android phases

`ArchiveRecoveryActivityTest#processRecovery` is explicitly selected with
`archive_recovery_phase` and `archive_recovery_run` instrumentation arguments.
Phases are `arm-preview`, `verify-preview`, `arm-committed`, `verify-committed`.
Each mode uses a different fresh run matching `[a-z0-9-]{1,48}` under the isolated
app's `no_backup/archive-recovery/<run>` directory. No existing run is adopted,
overwritten, reset or deleted. The owner file contains exactly
`locallore-archive-recovery-v1`. Original synthetic native source bytes are retained
as `archive.json`; `baseline.json` stays private and is not a public report.

An arm launches the real MainActivity, creates a separate original native story,
and selects its archive through the actual DocumentsUI/provider grant. Preview
mode holds the live validated import without consent. Committed mode explicitly
confirms import and holds its success UI without opening the imported story.
The Activity must be resumed with its live archive guard, prior selected state
unchanged, and document descriptors drained. The test creates and flushes a
`ready-v1.json`, then waits up to110 seconds; survival is a test failure.

Ready and verified records have exactly six fields: version1, run, phase, pid,
archive_sha256 (64 lowercase hex), status (`ready` or `verified`). Record size
is at most4 KiB. Source bytes are at most128 KiB. No native token/handle is
persisted. Numeric registry IDs are process-local and may be reused after death;
the product must not use a saved number to recreate consent.

The external owner requires an exclusive local output directory, matching
installed APK identities, a fresh run, a complete scope-bound marker, the exact
source checksum, a still-live owned arm client, and a matching current app PID.
Only then may it force-stop the verified isolated app. It independently confirms
process absence and drains the arm client and provider package before relaunch.
The interrupted arm is recorded as an intentional interruption, never a passing
test. A timeout/ended client is not permission to restart or presume process death.
Unknown client cleanup blocks subsequent device actions.

Verify relaunches MainActivity in a new process. Before allocating a new archive
owner it checks that no old consent, picker, capability, guard or success dialog
revived. The uncommitted source must still be absent, and fresh picker validation
and cancellation must work. The accepted source must exist exactly once and
reexport byte-identically before play. Explicit library opening, one potion gift,
duplicate refusal and native reopen must work. Prior library entries and the
previously selected story's full native player snapshot remain unchanged.
Verification drains/restores its UI and writes `verified-v1.json` before returning
one actual passing test terminal. All raw observations stay private.

## Host transaction boundaries

Independent integration tests terminate an owned native child at existing
`Store::import_archive` cancellation-poll barriers. The original three-branch
fixture holds resource and observer canaries. A reader sees the old catalog and
another actual SQLite writer must be Busy while the interrupted transaction is
held. Kill/reap/reopen must leave no partial imported story and preserve the
retained control story. A separate completed-import/pre-acknowledgement barrier
must survive termination with exact archive replay and same-ID Conflict.
The explicit ignored worker is an IPC entry point invoked by the qualification
tests; it is not counted as a standalone passing qualification test.

## Sources and limits

Official Android [state guidance](https://developer.android.com/topic/libraries/architecture/saving-states)
distinguishes ViewModel configuration retention from process death and complete
user dismissal. The [ADB Activity Manager reference](https://developer.android.com/tools/adb#am)
documents targeted force-stop and instrumentation. This packet tests deliberate
app force-stop and actual host transaction termination, with different claims.
It does not claim Android mid-import transaction termination, low-memory death,
power loss, physical ENOSPC/disk-full, hostile providers, ARM64 execution, real
model or phone qualification, or complete M08/owner acceptance.
