# Android cancellation recovery presentation checks

Refs #9 (M05.04 partial), #8 (M04.04 supporting).

The unchanged seven-method suite reproduced five failures on the baseline and
passed all seven methods after the coordinator's correction. This packet
exercises the actual `ShellViewModel`, `DurableGateway`, Android
`JSONObject` and main dispatcher using an independent synthetic
`WorkspaceTransport`. Its seven frozen instrumentation methods do not launch an
Activity, invoke JNI, open SQLite, read a save/model or run inference. Packaged
native libraries do not establish native execution.

The selected second emulator is the only permitted device for this packet.
The first emulator remains blocked by its previously observed userdata capacity;
this packet neither queries nor qualifies it. The preceding cancellation
acknowledgement packet and all its stopped preparation cohorts remain retained.

## Bounded admission

The new private evidence namespace copies the previous reviewed controller and
Windows Job owner. Initial admission requires all 23 original second-target
LocalLore package hashes plus the exact preceding isolated cancellation app and
test pair. Both new baseline APKs replace only that isolated pair with
`install -r`; candidate admission requires the exact newly observed baseline
pair. Installed, after-test and final complete maps must preserve all 23 original
hashes and match the admitted pair. These maps do not inspect canonical save or
model/cache contents.

Unchanged admission floors are 4 GiB plus 128 MiB on the host userdata volume,
10 GiB on the private evidence volume, and 1 GiB plus 128 MiB in emulator
userdata. Boot completion, API 35, x86_64, 4096-byte pages and absence of every
LocalLore process namespace are required before work and at each final boundary.
The fixed `/data` query may display `/data/user/0` only with captured matching
same-device `stat -L` identities. No floor is relaxed.

The selected invocation is:

```text
am instrument -w -r -e class org.locallore.app.CancelPresentationTest org.locallore.app.cancelack.test/androidx.test.runner.AndroidJUnitRunner
```

The frozen source SHA-256 is
`29024f68c30e44307a8c115830b39c95b4b03545a53e23a32ceb7a6838b229a1`.
The strict parser requires each of its seven exact method identities, sequential
counters, paired starts/terminals, no skips/aborts/unfinished methods and final
runner completion after every pair. Assertion failures are retained as failed
tests even if instrumentation exits zero. LF or consistent CRLF framing is
required; vertical-tab, form-feed, mixed framing and records after the runner
terminal are refused. Baseline and candidate are separate admissions.

The outer owner uses the existing `runtime_spike.run_process` Windows Job with a
180-second bound and stdin-EOF barrier before dispatch. Instrumentation has a
45-second bound and 128-KiB output limit; each client has its own deadline and
sticky cleanup status. Raw stdout is flushed durably before interpretation.
The helper retains stderr byte counts, not stderr content. Any unknown cleanup,
retention failure or identity/capacity/process/protocol mismatch stops later
actions. A surviving Android process would stop the cohort; host Job cleanup
alone cannot establish Android process exit.

No download, emulator lifecycle/reset, root, clear-data, uninstall, force-stop,
model operation, save access or old evidence mutation is part of this admission.

## Source preparation

Coordinator review caught a wrong output-root literal in the first copied
controller and owner before any device dispatch. The preparation script had
compared a Windows-backslash path against slash-separated source literals. Both
wrong-root drafts remain in the new private namespace; both constants were
corrected to that namespace before admission. No old evidence was modified.

Twenty pure host fixtures passed against the corrected controller, covering
all-seven success, retained assertion failures, missing/duplicate/foreign/skipped
or aborted records, runner completion ordering, framing, storage alias proof,
known install-success forms, exact pair maps, sticky unknown cleanup and retention
failure. The earlier run of the same 20 fixtures overlaps this run; it is not
40 unique tests. These fixtures do not qualify Android execution or native
cancellation. Their corrected-source raw log SHA-256 is
`9a180147c9495dd752b3ca58a5e2f6ac1f694eda23609d1ff70ad03ffbcd725f`.

## Actual baseline result on the second emulator

The separately reviewed baseline admission completed in 10,125 ms with child
return code zero and known host Job cleanup. All 42 bounded commands completed
with return code zero and known client cleanup. Both isolated APKs were installed
with `-r`; no old package was changed. Before, installed, after-test and final
maps each contained the exact 23 original package hashes plus the expected pair.
Final available userdata was 1,622,237,184 bytes, above the unchanged
1,207,959,552-byte floor. Final LocalLore process absence passed and the exclusive
device dispatch lease was released.

All seven exact method starts/terminals and the final runner marker were
observed: **two passed and five failed**. This is an assertion result; the
instrumentation command's zero exit status does not convert failures to success.

| Frozen method | Baseline | Candidate |
|---|---|---|
| `cancellationDoesNotCompleteBeforeAcknowledgement` | Failed | Passed |
| `cancellationDoesNotCompleteBeforeAcceptedSnapshotReconciliation` | Failed | Passed |
| `invalidAcknowledgementsRetainHistoryBlockSubmissionAndRecoverOriginalKey` | Failed | Passed |
| `explicitTransportFailureRecordsUnknownWithoutRawPayload` | Failed | Passed |
| `committedCancellationRaceDisplaysAcceptedHistoryWithoutStoppedClaim` | Failed | Passed |
| `lateNoncooperativePreparationCannotPublishOrCommitAfterCancellation` | Passed | Passed |
| `disposalDuringDelayedAcknowledgementCannotPublishOrRecordCompletion` | Passed | Passed |

The malformed-acknowledgement and explicit transport-failure tests failed at
their diagnostic assertion: the baseline recorded `COMPLETED` instead of
`UNKNOWN`. Earlier assertions in those methods already confirmed history and
recovery-state retention. The two delayed tests found completion recorded before
acknowledgement or accepted snapshot reconciliation. The committed-race test
found a stopped-response notice despite an accepted outcome. The late preparation
and disposal tests passed on the baseline; they are retained regression coverage,
not newly discovered failures.

The application APK remained byte-identical to the preceding corrected-gateway
packet: 22,524,075 bytes, SHA-256
`342d71e5d68913af1ec16f3f4789723f082739e4836b101b716d78906f36a1cd`.
The new test APK was 2,312,557 bytes, SHA-256
`1161ac649721f22dab3d812364b4f92711c53969dfe67cff214bd4c3cbb49b8e`.
The baseline `ShellViewModel` SHA-256 was
`1cfe225a31c407fa28056a17b03491758ab716d7113664471871f4cae0430bac`;
the gateway retained the preceding correction. The coordinator owns build and
APK audits.

Private raw instrumentation stdout was 27,161 bytes, SHA-256
`bf2da61f42ebab3659c94fbad15687552519cf9f48f0425f15661fcba97bbb4d`.
The local audit independently rehashed every command stdout length/hash,
reparsed the method results and checked all four maps before recording this
result. Raw diagnostics and private identifiers remain local.

## Actual candidate result on the second emulator

After the coordinator's correction and separate artifact audit, the candidate
admission completed in 10,703 ms with child return code zero and known host Job
cleanup. The controller, owner, frozen seven-method source and test APK were
unchanged. Both isolated packages were replaced with `install -r`; no source or
build mutation occurred during either admitted cohort.

All seven exact starts/terminals passed, with no skips or unfinished methods.
All 42 candidate clients completed with return code zero and known cleanup.
The candidate before map equalled the baseline final map. Installed, after-test
and final maps retained every original package hash and matched the candidate
pair. Final process absence passed; available userdata was 1,599,746,048 bytes,
above the unchanged floor. All device calls stopped and the lease was released.

The candidate application was 22,524,394 bytes, SHA-256
`d8b82930934304a3352b8cbab415c69b490fafa189364815d71e6d88382fc94d`.
The test APK remained exactly `1161ac64…49b8e`. Candidate `ShellViewModel` SHA-256
was `8a8075478029cbefbdcb0a286805b2bc53b5a487f36c3295fa643ddc9e34c948`.
The gateway and seven-method test source were unchanged. The coordinator
separately verified all four packaged native library hashes matched baseline;
these transport tests do not execute or qualify those libraries.

Private candidate instrumentation stdout was 5,026 bytes, SHA-256
`b7ef41c4f26e214d322cd06c11a089999ae3cb8031beea2ff125cba249865a83`.
The local audit rehashed every one of the 84 baseline/candidate command stdout
records, confirmed their completed/zero/known-cleanup status, reparsed both
transcripts and checked all observed maps. No additional cohort or original
nine-method gateway test rerun is claimed.

## Retention and limits

The new closed private selection contains 224 files totaling 297,843 bytes.
Its 38,037-byte index SHA-256 is
`f0b1057eab86815c74fa2c5121bb9480c7b721b915a6352d3ab815148ad14cba`.
It includes the incorrect-root drafts, corrections, overlapping host fixture
runs, source/artifact authorizations, lease records, all raw stdout/status
metadata and terminal audits. The preceding final cancellation-acknowledgement
selection's 207 files were rehashed against its original index with zero
mismatches. Raw diagnostics, identifiers and APKs remain local.

This establishes cancellation recovery presentation with actual Android
ViewModel/gateway/main-dispatcher handling and synthetic transport on one API 35
x86_64 emulator. It does not qualify Activity/Compose rendering, real native
resource ownership or cancellation, SQLite canon/replay, process restart,
real-model behavior, ARM execution or a physical phone. The first emulator's
storage gate and the physical-phone gate remain blocked. Full milestone
acceptance remains separate; no checklist acceptance, merge or release follows
from this evidence.
