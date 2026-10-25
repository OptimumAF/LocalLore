# Setup launch failure and held admission

Refs #9 (M05.05 provisioning prerequisite; M05.04 supporting). This follows
the pending-result fixture in PR #139. The implementation and execution are
separate obligations. See the [dated verification](MODEL_SETUP_RECOVERY_VERIFICATION_2026-10-23.md),
[device report](MODEL_SETUP_RECOVERY_DEVICE_2026-10-23.md) and
[independent review](MODEL_SETUP_RECOVERY_REVIEW_2026-10-23.md) for actual results.

## Existing authority

The real setup Activity calls `beginPlay`, invokes its immutable `openPlay`
dependency and catches an exception with `playLaunchFailed`. A launch failure
therefore leaves READY and requires fresh verification before Start can retry.
The production `CandidateOwnerAdmission` claims before construction and retains
that claim after a construction failure. No Activity finish, apparent close or
timeout releases a possibly uncertain predecessor. Only a new process gets a
fresh candidate reservation. Gameplay remains under the Rust engine; setup
cannot apply events or repair a story.

## Explicit synthetic boundary

Only the existing `localLoreModelPickerVerification=true` debug profile includes
the non-exported `ModelSetupRecoveryFixtureActivity`, with no intent filter.
It inherits the actual setup screen, button handlers, ViewModel and store.
Its immutable dependencies select `synthetic-setup-recovery-v1`, the original
63-byte fixture and only `no_backup/model-setup-recovery-v1`. The new root must
be absent; the fixture offers no reset. No Intent, URI, filename, model content
or saved bundle selects its identity or failure mode.

The fixture owns one instance of the production admission class. Its first
`openPlay` throws a private synthetic canary before claiming that instance.
Its second call claims it, counts one attempted synthetic construction and
throws another private canary. Neither path launches a play Activity, constructs
an inference owner, initializes an SDK or accesses a story workspace. This is
injected failure at the real UI catch boundary, not a measured Android launcher
or real-model construction failure. It adds no production release/reset seam.

## Same-process method

`ModelSetupRecoveryTest#startFailuresRequireVerificationAndHoldAdmissionAcrossRecreation`
first seeds the owned root through actual native no-clobber publication on IO.
It establishes a cache sentinel, captures bounded hashes for fifteen fixed older
files, and launches the private Activity explicitly. Actual READY precedes Start.

The first Start must produce the fixed redacted FAILED notice and disable Start.
Actual Check must perform a second full rehash before another Start is enabled.
The second injected construction failure also first shows FAILED. Actual Choose
then detects the held reservation before any OPEN_DOCUMENT request and enters
SESSION_HELD. Disabled control attempts cannot start more work. Closing and
reopening the Activity in the same process must retain the held admission, with
a new controller and unchanged file/check/start/construction counts.

Expected counts are one seed import, zero UI file imports, two full checks, two
Start callbacks and one construction attempt. Model, cache sentinel and the
fifteen older file hashes remain unchanged. No staging file remains. The first
method publishes a bounded primitive process/counter/hash receipt only after
these observations. File work runs on IO; raw canaries, paths and exception
messages never enter UI or public diagnostics.

## Separately selected fresh-process method

`ModelSetupRecoveryTest#freshProcessRechecksHeldSessionModelWithoutImport`
requires the first receipt and a different actual process identity. It verifies
the published bytes, sentinel and older hashes before launching an Activity.
The new fixture admission and counters must initially be fresh. Actual READY
then requires one controller full check, with zero seed imports, file imports, Start calls
or constructions. Rehashing after observation must still match. No test resets
the old admission to manufacture this result. Controller check counters are
separate from the independent direct native-store reopen and fixed proof hashes.

The two methods use separate ordinary selected instrumentation invocations.
Their actual process receipts, rather than runner flags or Activity recreation
alone, must prove the process boundary. The external owner serializes the exact
clients to known terminal states, binds source/signed APKs and fresh installed
identities, preserves other packages and data, and checks capacity and absence
of the real-model root. It does not launch the normal setup launcher or use host
UI automation. A failure stops the cohort without an automatic method retry.

## Evidence and limits

APK audits require the private implementation only in the explicit profile and
exclude TEST code from APP; regular setup and ordinary APKs reject the helpers.
The tests preserve selected older proofs without claiming a complete private-data
byte audit. Raw process identifiers and diagnostics remain local. Failed attempts
are retained. Physical-phone, real-model quality/performance, active SDK teardown,
ARM64/16 KiB execution and power-loss durability require separate evidence.
M05.04/M05.05 and M01 gates remain subject to their full criteria and owner review.
