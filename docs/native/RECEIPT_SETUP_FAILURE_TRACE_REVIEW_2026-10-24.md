# Independent receipt setup failure-trace review — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).

## Scope and current disposition

Independent review under root claim6388192705, subclaim6388203823, from unmerged #149 head
`683c3fd34c200f0f663e3d0d4cd6c5627dc894d7`. The reviewer owns only this report;
no implementation edits, builds/shared-cache changes, SDK/ADB/AVD/model work or
execution authority are included. Existing targets and all attempts remain.

The preceding first-import READY timeout has no qualified phase/error/source
snapshot and remains unexplained. This packet implements bounded observations
without timeout or state/resource changes. The new fresh synthetic setup cohort
passes three initial methods plus a separate-process reopen, all eight proof
reads and 44 checks. No failure marker is emitted, so actual failure-status
delivery remains unexercised. This pass does not diagnose or demonstrate a fix
for the earlier timeout; model/runtime/device gates remain separate.

## Concrete design boundaries

The trace must use only closed case/phase/error/event enums and bounded
synthetic-source counters. Fixed ASCII serialization makes a 2,048-byte UTF-8
limit auditable. No caller strings, Throwable text/class/stack/cause/toString,
path/URI, model/story bytes or device identity belongs in the marker. Saturation
or refusal semantics for counters must be explicit. Return copies of the
16-event ring; a diagnostic consumer must not modify observed state.

Capture and emission must do no file/native/SDK work. They observe actual
inherited lifecycle/controller/source behavior without changing cancellation,
READY, receipt acceptance, owner admission or the ten-second wait. Preserve and
rethrow the original wait failure if tracing itself fails; a diagnostic error
cannot become success or silently replace the original outcome.

Independent atomic counters do not constitute one atomic source snapshot. A
consumer must not infer cross-field causal ordering or reject a legitimate
sample merely because its reads straddle updates. The trace is evidence of
bounded observations, not a resource-release or model-verification oracle.

Host extraction must reject duplicate/malformed markers, unknown keys/enums,
wrong types, Boolean-as-integer counters and oversized payloads. Retaining a
valid marker from a failing transcript must never satisfy the original three
passes, restart proof or 44 checks. A failure marker on a passing transcript
must not be silently accepted. Packaging must confine trace/fixtures to the
explicit debug receipt profile and exclude them from ordinary/other profiles.

## Source review and corrections

The actual frozen core at
`618ea2beb14abacfdaec26837951956c97fb99d6` uses synchronized ring operations,
closed enums, immutable progress values and a copied event list. It categorizes
only trusted Throwable types and the final local failure enum, with no message,
cause, stack or string conversion. JSON contains printable ASCII only and the
complete instrumentation prefix plus UTF-8 payload is bounded to 2,048 bytes.
The receipt-only JVM source set is gated with the explicit receipt profile.
No concrete core source blocker was found.

Subsequent API-bound review finds one separate bound hole: a directly supplied
mutable event list can pass snapshot construction, then grow beyond 16 before
serialization. The initial encoder checks ASCII/total wire bytes but does not
revalidate ring size/total at that point. The actual trace producer copies its
ring, so this is not evidence of the earlier timeout or an observed fixture
failure. The snapshot API nevertheless needs defensive storage or serialization
revalidation, with a caller-list mutation regression, before its bounded-wire
claim is complete.

The coordinator's correction
`ec092993cf8ded92b1b2b3a7c28aabc0ae82c6e5` gives the snapshot private owned
storage, copies at most 16 entries during construction, returns a copy and
serializes only its private list. The new regression mutates both caller and
getter views without changing the receipt. No remaining list-bound defect was
found in the actual fix.

Review raised an actual framing hazard: the preceding runner repeats its
exception across status/stack/final summary. Embedding a marker in assertion
text could therefore produce duplicates. The frozen interface instead defines
one dedicated instrumentation status field `locallore_receipt_failure_v1` and
fixed status code 1337, leaving the original exception unchanged. Host parsing
and actual transport must still establish that shape; core serialization alone
does not prove it.

The public [Instrumentation API](https://developer.android.com/reference/android/app/Instrumentation#sendStatus(int,android.os.Bundle))
documents status reports with a result code and Bundle since API 1. Official
[raw reporter source](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/cmds/am/src/com/android/commands/am/Instrument.java)
prints Bundle fields followed by the status code. This supports the framing
choice without a new API dependency; exact pinned-device transport still needs
actual evidence. The source citation is current main, not a claim of independently
retrieved Android 15 tagged source.

The error field is a retained observed operation category, not automatically
the current ViewModel error or a causal diagnosis. Progress saturation flags
must be sampled consistently with their own monotonic counter; independent
cross-field source observations remain non-atomic. These reporting limits do
not require any product authority or timeout change.

Actual fixture review found a Kotlin visibility defect: subclass recreation
code assigned newly private base-harness trace/source members. The author
replaced those assignments with a typed harness capture helper while keeping
the fields private. Compilation remains a separate check.

The inspected hooks record lifecycle before unchanged superclass calls and
fixed check/import events around the original operations. Failure categories
are recorded and the same operation exception rethrown. Source counters use
bounded CAS increments for actual reads/positive returned bytes, sampling
monotonic saturation flags before their counters. The phase wait remains ten
seconds. Its failure path attempts one dedicated status record and rethrows
the identical original failure even if capture/serialization/send fails; it
performs no model/file/native-publication/SDK operation.

The final sampling refinement uses one process-wide atomic emission claim,
without a per-test cleanup reset, so multiple failed methods cannot produce
multiple custom records in one instrumentation. This is one attempt, not a
delivery guarantee: encode/send failure consumes it while leaving the original
failure intact. Later failures still fail normally but have no further custom
trace. The first trace therefore cannot explain every failed method.

After Activity recreation, retained ViewModel dependency closures still refer
to the original Activity trace, while the harness captures the new Activity's
lifecycle trace. The latter is therefore not a complete current-ViewModel
operation history/error. The earlier initial-import timeout occurs before
recreation; tracing does not redirect those closures or introduce a registry
to change their ownership.

The inspected host parser has a closed payload keyset, exact scalar types,
finite enum sets, independent bounded counters and saturation implications.
Extraction requires one adjacent custom status/value pair and rejects duplicate
markers or a passing runner summary. It saves the finite observation before
applying the unchanged strict runner parser to the original raw stream; a
trace cannot supply a pass, READY or proof authority.

Review found a new parser-test mismatch: it expected generic CRCRLF input to
pass, but the unchanged shared normalizer intentionally rejects that framing.
Only the console-name protocol has its separately evidenced special allowance.
Trace tests should retain LF/CRLF positives and CRCRLF/mixed/lone-CR refusals.
Review also requests a full synthetic failed-runner/Owner integration case,
not only standalone marker snippets, before treating framing as exercised.

The first actual Python run is preserved: 606 tests, 605 passes and one
framing-test failure, 66.087 seconds; original execution completed nonzero with
known cleanup in 67,219 ms. The first receipt build separately completed zero
with 352 JVM tests/36 suites, no failures/errors/skips and lint zero errors/19
warnings. It predates the snapshot fix and is not its validation.

The same correction keeps the shared normalizer unchanged, fixes LF/CRLF versus
CRCRLF/mixed/lone-CR tests and adds full synthetic failure/pass transcripts plus
an actual mocked Owner/cohort path. That path retains raw output and a finite
observation before the unchanged runner refusal, with no helper/restart facts.
Review finds no remaining concrete source blocker; corrected host/build
execution is checked separately below.

The corrected copied receipt artifacts independently contain 353 JVM tests in
36 suites, zero failures/errors/skips, including all 13 trace methods. Lint has
zero errors/19 warnings. Both actual APP/TEST digests and sizes match their
records; a pure read-only ZIP audit passes six native/receipt-class checks.
That selected-profile check does not establish exclusion in other APKs.
All 62 runtime and 67 analyzer artifact rows equal the prior retained receipt
graphs; analyzer 32.4.1 reports actual work. No new dependency follows.
Retained receipt/regular/full-Python results are completed zero with known
cleanup; their output digests match. The final Python summary records 608
passes in 68.011 seconds. Original execution attribution and regular/ordinary
artifact exclusions are checked separately below.

The coordinator confirms consumed original terminals zero for corrected
receipt, Python, regular and ordinary executions. Their known-clean owned
durations are 137,875, 69,047, 153,610 and 83,750 ms respectively. Independent
regular/ordinary XML counts are 340/35 and 206/24, zero failures/errors/skips;
lint is zero errors with nine/one warnings. Actual copied APP ZIP audits pass
six/four native checks and exclude all receipt trace classes. Owned audit
output digests/zero returns match.

The corrected receipt APP is 74,884,112 bytes, SHA-256
`dca8db5ef1244e29318f3b5da1044e8468bc82a6b995ac591f0516eae7dd76f7`;
TEST is 1,922,787 bytes, SHA-256
`bc74a8c89c447999a83cee019e37c78186d7e071e03165e8014517e89fefe4ef`.
An intermediate artifact helper refused its badging-field expectation after
three actual clients completed zero. Subsequent XML target/runner verification
and byte equality with the prior audited TEST manifest resolve that helper
assumption; this is not an Android app/test failure or a rerun signature claim.
The reviewer independently verifies the 6,244-byte manifest equality, SHA-256
`ded72dbadcabfb44c776d00b37f24a642bcc2541a2416334580b75f25abb4d83`.

## Separate fresh-input review

All 1,429 final source files, 16,876,263 bytes, independently match commit
`8f522407f1e36fa00850a2214c7b6664de2f4db2` and source index SHA-256
`17dbb6ef34f7f7c5f48d79fba93d28b585c34917941bff19f6979dfc41a423bf`.
The Git diff from actual compilation `ae52ea6` changes only the controller's
audited APK hashes and verification documentation; Android/Rust/build inputs
are unchanged.

The new disabled preparation proposal SHA-256 is
`aa86043cda9d12280b7244166f8f819f36904276d836ecc219e3891b48f0b88c`.
Independent streaming hashes match all 909 bindings plus eight preserved
registry/token records: 918 rows, 5,046,151,583 bytes. Target and authorization
are absent at review; requested 12 GiB userdata/8 GiB SD/2 GiB RAM/two CPUs,
installed JBR17/tool/image set and resource floors are unchanged. This input
review invokes no SDK executable or guest client. Actual preparation, retained
owner, guest trace and final closure remain separate gates.

The coordinator confirms original preparation completed zero with successful
cleanup/preservation closure; the actual SDK child takes 3,922 ms. The separately
reviewed disabled run proposal SHA-256 is
`9657956a6fff2a0f6ed8ddd4c1367d0ecbf7581a70a6b28e31037b22e4fa9a74`.
All common fields/909 bindings equal the reviewed prepare input. Sixteen linked
prepare/result/prepared/immutable/initial-SD/registry-token rows,
8,590,136,599 bytes, independently rehash without mismatch. Actual config has
the unchanged sizes and fresh paths; userdata, running/result/stop and both
live-output files are absent, with run authorization absent at review. These
checks establish input consistency, not guest boot or test results.

The separately reviewed disabled guest proposal SHA-256 is
`d48092898f3c68739f3ec2c8c6522f4560ee8d677aadf35a62111c873c328936`.
All 63 input bindings, 86,197,679 bytes, independently match current source,
actual audited pair, signatures/manifest/build evidence and live descriptor.
Closed validation and read-only exact-owner checks pass with about 1,074
seconds remaining; guest authorization/cohort are absent. Existing live-output
files total 10,252 bytes within the cap, without a boot or terminal claim.
No SDK/device operation is performed by the reviewer.

## Actual fresh synthetic qualification

The coordinator confirms the original guest consumed tool terminal zero;
the owned worker completes zero with known cleanup in 83,109 ms. Its 313-byte
output SHA-256 is
`ea0fa146cf90972e119baab539e069e95bf10cedd58a7f7d0f7d1b730cbd9eff`,
outer stderr zero. The reviewer independently checks all 72 raw client records:
exact order, sizes/hashes/caps, completed-zero status and known cleanup.
Two clients have nonzero bounded stderr counts; no all-client-stderr-zero claim
is made.

Strict offline reparse yields exactly three initial passes and one restart pass,
four bounded JSON proofs plus four empty ready-marker reads and all 44 closed
checks true. Phase source open/close counts are 1/1, 2/2, 1/1 and 0/0. The
reopen proof links to the original APP identity, changes its PID/start pair and
retains the actual UID. All five process observations replay through the exact
boundary; final APP target is absent and one bound TEST helper remains stable.
That observed row is separate from APP absence, not an all-processes-quiet or
continuous-helper-liveness assertion. Package hashes, UIDs and volume stay
fixed; no force-stop or other guest lifecycle management is used.

Actual userdata availability before/install/final is 11,340,242,944 /
11,266,891,776 / 11,265,581,056 bytes. Minimum Context external availability
before/after across proofs is 8,572,993,536 bytes. These establish the admitted
tiny-fixture floors, not real-model/cache/runtime capacity or a production
storage profile. The original 63-byte fixture and direct-callback/SDK-false
limits remain unchanged; DocumentsUI is not exercised.

Neither instrumentation transcript contains a failure-status field and no
failure-trace artifact is produced. Actual `sendStatus` failure transport is
therefore unexercised. Prior failed cohorts remain separate; passing now neither
identifies their cause nor proves that observation hooks fixed it.

## Known owner closure and final evidence

After the guest terminal, the exact owner stop completes. The coordinator
confirms original owner tool terminal zero; its retained result is
`stop_requested`, cleanup/preservation closure/output capture complete true,
294,125 ms, worker return one from owned forced drain. Post-stop records find
the three exact host identities absent and the reserved ports free. This is
known owned cleanup, not graceful guest flush, saved-disk integrity or a
power-loss durability qualification.

Retained owner stdout is 9,233 bytes, SHA-256
`53402e90f705188b3d799ddb944070882780f5443b62d45e179769241c074ce9`;
stderr is 1,019 bytes, SHA-256
`a284a0f051c4720970517d53270781712f442f2252f77ad1f60b34be4c94c164`.
The reviewer matches their sizes/hashes and actual capture result. Mutable
virtual disks remain retained with metadata-only observations.

Every final inventory entry independently rehashes without mismatch:

| Inventory | Files | Bytes | Index SHA-256 |
| --- | ---: | ---: | --- |
| Host | 1,637 | 271,069,839 | `5f8679c8509a7bfeec7e17f0cb822971e4761fa9f43367332587463281ded083` |
| Environment | 23 | 389,003 | `1818cb4a9fc6749e9001db858bbdd6a3cf7bb90ab4cf42f5cd88f17231a16904` |
| Device | 226 | 86,347,718 | `02d605f5a2de00660896959596de7628c5d5a75d70592adf9cbf0a50f3797404` |

All 63 admitted inputs, 86,197,679 bytes, map exactly to the immutable archived
copies; archive index SHA-256 is
`0617dc7ac0fef2976528b2156ebf28022d37af959059d0c1cf10bf32ea0b09c4`.
All 916 current non-Markdown source rows, 11,769,445 bytes, still match the
executed frozen source. Later public documentation updates cannot substitute
for or alter those source/APK bindings.

## Disposition and next task

The bounded trace implementation is source-reviewed and host-tested, with
actual three-plus-one synthetic setup/reopen qualification and all 44 checks.
The actual failure-status emission/transport remains unexercised; the preceding
timeout remains undiagnosed. Do not label this pass a causal fix or combine
earlier failed attempts into it.

Next qualify the failure-only transport with a separately scoped deterministic
synthetic failure and unchanged original failure semantics, then use a genuine
observed receipt to diagnose any reproduced timeout before behavioral changes.
Do not extend the ten-second wait or infer a storage/lifecycle cause. Full
M05/M01 and owner acceptance remain open, as do A/#117/#119, real-model/SDK,
DocumentsUI, reference-phone, cache/privacy, power-loss, ARM64/16 KiB, quality
and sustained-runtime gates. No merge or release is qualified by this review.
