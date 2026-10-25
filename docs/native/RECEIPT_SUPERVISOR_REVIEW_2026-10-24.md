# Independent receipt supervisor evidence review — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).

## Scope and current disposition

Independent review under root claim6387844172, subclaim6387854293, from unmerged #148 head
`1cba2c05994a8643ca817fe5796d83e922bedbec`. The reviewer owns only this report;
no implementation, build/shared-cache, SDK/ADB/AVD/model operations or execution
authority are included. Existing targets and failed evidence remain preserved.

The preceding START-only runner 255 and subsequent missing original supervisor
terminal/output records remain unexplained. This packet changes evidence
persistence and tests abrupt owner loss with synthetic host children. Neither
a stronger logger nor a fake-child result identifies that earlier cause or
qualifies an Android retry. The corrected host checks pass; a separately
admitted new Android attempt runs three methods with two passes and one initial
import READY timeout. It does not reach helper binding, restart or proof
validation. Diagnostic results and owner cleanup are recorded separately below.

## Baseline observation and concrete review requirements

The inspected baseline drains both child pipes into memory and writes the
owner output files only in `finally`. Abrupt supervisor loss can therefore leave
no retained output despite data having reached its readers. Reader errors are
also swallowed. The existing shared output cap, owned job assignment before
barrier release, exact stop validation and kill/drain remain separate controls.

Both output files must be create-only and forced before any child spawn or
barrier release. A second-file creation failure must preserve the first file
and prevent spawning; no retry, truncation or fallback may adopt those paths.
Keep the created handles instead of reopening output paths at finalization.

Every retained chunk must be fully written, flushed and forced under one shared
combined-output limit. Short writes, flush/fsync failures, reader exceptions and
final close errors must fail closed. Recheck evidence failure after readers join
and handles close: a trailing failure can race with a nominal child-exited or
stop-requested decision. Successful terminal status cannot be inferred from
that earlier decision if final evidence persistence failed.

Output prefixes, empty precreated files and reader-thread progress never prove
supervisor completion, descendant cleanup, guest flush or saved-disk integrity.
The original owned execution and separate final metadata are still necessary.
No raw diagnostic content, private process identity or token is published.

Primary documentation agrees with the selected primitives:
[Python exclusive binary creation](https://docs.python.org/3.9/library/functions.html#open)
refuses an existing file; unbuffered mode avoids a Python output buffer.
[Python fsync](https://docs.python.org/3.9/library/os.html#os.fsync) documents the
flush-before-force sequence and Windows `_commit` implementation. This supports
forced-prefix evidence, not an absolute power-loss or storage-hardware promise.
[Windows job documentation](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
describes default child inheritance and termination when the final
kill-on-close job handle closes; actual fake-child evidence is still necessary
to distinguish that from a test's outer cleanup.

## Evidence gates

The actual implementation at
`f3885d977bf834592d593b892af310102bfa7a50` creates and forces both exclusive
files before `Popen`. Shared locked counters advance only after successful
write/flush/fsync. Reader/persistence errors latch failure; final join/close
checks override earlier nominal stop/exit status. Overflow remains one shared
262,144-byte limit across channels. Replay refuses either existing output path.

A stalled reader after bounded joins leaves capture incomplete, cleanup false
and byte counts unavailable. The supervisor avoids acquiring that reader's
potentially stalled sink lock or closing a file still being written. Other
capture failures can leave uncertain partial file bytes, explicitly marked
incomplete rather than reported as successful capture. The existing success
condition still requires exact stop plus known cleanup/preservation closure;
evidence failure cannot become success. No concrete remaining source blocker
was found in this diff. Actual adverse/owner-loss execution remains separate.

Independent test review identified two concrete issues before qualifying its
hard-loss result. The first draft referenced a nonexistent environment `ROOT`
attribute; deriving the exact root from that module's file avoids an early
test-only failure. Its initial death oracle also treated every refused process
identity query as death. Production correctly treats such a refusal as lost
authority, but that inverse is not proof of termination. The test should retain
non-inheritable synchronization handles while captured descendants are live,
then require signaled bounded waits before outer safety-job cleanup. This also
avoids PID-reuse ambiguity. Corrected source/results are checked separately below.

The retained first test attempt records 16 tests with one error at the missing
attribute, owned return one/known cleanup. The second records 16 passes but
uses the weaker identity-refusal death oracle; it is superseded for that proof.
The corrected third attempt records 18 passes, zero failures/errors/skips,
0.911 seconds, owned return zero/known cleanup in 1,250 ms. Its 2,787-byte output
SHA-256 is
`7d62c7d3554ded85404a22e8d860c58c25e399fbb304e0af4b24af2fa9de0f7f`.
The reviewer verified all three output digests and the final three source
bindings. Final helper SHA-256 is
`4e40ebb5f23cce879c731f1e1ac49e8b2c97ca04ce44ff898217d3e558868491`;
final test SHA-256 is
`9eeb5f77503712fba46e771d589b67a62474172d21dc03cca1aab8c2994cafc0`.

The corrected real Windows fake-child case acknowledges both expected prefixes
only after real force calls, verifies captured worker/descendant handles are
initially nonsignaled, kills only its captured synthetic supervisor, then
requires both handles signaled before the outer safety job closes. The prefixes
remain exact and no terminal owner-result is fabricated. The child emergency
timer is longer than this termination check. This is host-only abrupt-process
evidence; it neither reproduces the earlier lost tool handle nor identifies its
cause.

The coordinator confirmed original full-host execution completed zero with
known cleanup in 59,766 ms. Its actual suite records 597 passes, zero
failures/errors/skips, 58.945 seconds. The reviewer checked the retained
69,834-byte output and SHA-256
`2f9b8d9b3b4be8229b84639087c242000125b731c1cdab1b84f4557157e349d1`.
Final source at that gate is
`c2932eac4729d11284ff94179cc64c2d2b7315c1`; no Android compilation or device
execution follows merely from this host result.

These host checks cover the actual integrated sink/supervisor, cap/order/IO
adverse cases, fake-child abrupt-owner loss, inherited job cleanup and existing
stop/ownership regressions. Executed source/evidence are frozen; host-only
outcomes remain distinct from actual SDK/emulator/Android results. All M05/M01,
A/#117/#119, model/reference-phone, privacy, power-loss, ARM64/16 KiB and
sustained-runtime gates remain separate.

## Separate fresh-input review

The new disabled preparation proposal SHA-256 is
`754a00271d74c7df64e05e4dee12633414866c76bf1ae89ce0959c30379dec6c`.
The reviewer streams all 909 bindings plus eight preserved registry/token
records: 918 rows, 5,046,151,583 bytes, zero mismatches. Fresh target and
authorization are absent at review. The proven installed JBR17/tool/image set,
12 GiB userdata/8 GiB SD/2 GiB RAM/two CPUs and resource floors remain unchanged.
No SDK executable is invoked by this review.

All 1,424 frozen source files, 16,801,947 bytes, independently match source
`c2932eac4729d11284ff94179cc64c2d2b7315c1` and index SHA-256
`35ecd1d701f7221109e9cb955dc07cd359e659f3998d6094504060e94ea97146`.
The APK-reuse record SHA-256 is
`2721fb27cc4006173b876ac8f344c2c6f6bda129d9764eaab8ecbc0a09232d2c`.
All 457 relevant source rows, 5,975,443 bytes, match live source and the prior
compiled snapshot; both copied audited APK hashes/sizes match. This is reuse
equality, not a new Android build or device result. Actual preparation, owned
run, guest results and closure remain separate gates.

The coordinator confirms original preparation completed zero with successful
cleanup/preservation closure; actual SDK child duration is 4,172 ms. The
reviewer reads the successful prepared record, three immutable files, exact
8 GiB initial SD and explicit userdata-absent/boot-unverified fields. The
separately disabled run proposal SHA-256 is
`c806a5ef65b6a59998c0c41a6250bedd05efe8e5babb99383b96a286f8575fb2`.
All common fields/909 bindings equal the reviewed prepare proposal; sixteen
linked prepare/result/prepared/immutable/SD/old-registry/token rows,
8,590,136,557 bytes, independently match. Actual size configuration is unchanged.
Userdata, running/result/stop and both live-output names are absent at review;
run authorization is absent. This proves input consistency, not guest boot or
an emulator result.

The separately reviewed disabled guest proposal SHA-256 is
`1f37f13cda358cded81ac8e6f80a342dfca4a73a72692de92c8b2f4d4eeb2041`.
All 49 bindings, 86,184,967 bytes, independently match. Closed validation and
read-only live-owner lease checks pass with roughly 1,128 seconds remaining;
guest authorization and cohort were absent. Both actual live-output files
already exist, totaling 10,121 bytes within the shared cap. That is partial
output evidence, not guest boot, successful capture completion or terminal
cleanup. Exact central-source imports are used; no SDK/device client is run by
the reviewer.

## New actual guest outcome

The coordinator confirms the new original guest consumes outer terminal one;
the owned worker is separately completed two with known cleanup in 86,750 ms,
355-byte output SHA-256
`52b689d0cb08ded5316231dfa74c2ccf5e1c34cc1885855d4b4469360fe2b63f`,
outer stderr zero. All 28 client records independently match exact stdout
sizes/hashes, order, completed-zero status and known cleanup. Two fresh exact
installs occur. Initial userdata availability is 11,604,717,568 bytes and
installed availability is 11,516,420,096 bytes, with empty target/helper facts
at both gates.

This runner transcript is complete: three methods run, two pass and one fails.
The first method times out waiting ten seconds for READY immediately after its
initial synthetic import selection, at test line 129. It does not reach the
later Activity-recreation assertion. Cancellation and disposed-source drain
methods pass. The 4,565-byte runner output SHA-256 is
`9cac5a6bc3254b7480b676d8107122101bb68fcc4352872c5b3a4730fd43a90b`;
status codes are start/failure, start/pass, start/pass, followed by the runner's
normal final record. No three-pass aggregate, helper binding, restart or host
proof read is accepted. The timeout's underlying state/cause remains unknown.

The original environment owner is confirmed live after the failed guest.
A separately reviewed four-client read-only diagnostic is proposed. Review
finds its original exclusive output opens occur after dispatch, allowing a
repeat first client before discovering previous evidence. A new separate
namespace adds an exclusive bound start record before any client; the first
proposal stays unrun. The corrected proposal SHA-256 is
`8aa90e49d2a546a2c2c63378c0905a9e02372f5efb355bbe69e16f6f8b272cf4`;
script SHA-256 is
`ed0996b6d9f1fb1ec5f1cd62e5af7d527b2522d57cbf5ab8f319bd24373362c4`.
It permits only get-state, process inventory, bounded crash-buffer observation
and bounded main/system-buffer observation, each at most 15 seconds with live
lease checks and forced raw retention. All caps are within the existing
262,144-byte per-client limit. At review its authorization/start are absent;
their actual outcomes and final owner closure are checked separately below.

A later two-client metadata/lifecycle proposal is also reviewed separately.
Its first draft checked only the final synthetic child for links; review
requires directory/nonlink guards for the fixed parents before listing, as in
existing proof reads. The corrected new namespace has proposal SHA-256
`a8052c86fc62c3d2dd8f9f41387e5f2828896b92c7a6d2631f1afbfb50a5e03f`
and script SHA-256
`6adcd7928d339ca7641c3933fc6f7f2a47d7527432171607d1249a00693e7b8d`.
It permits only nonrecursive metadata listings of the two fixed synthetic
accept-case roots and a fixed filtered lifecycle-buffer read, at 15 seconds
each with 16 KiB/256 KiB caps. No file contents, model/cache traversal or guest
mutation is exposed. The external-path mapping is diagnostic-only; it does not
qualify a trusted Context root. Prior proposal stays unrun; corrected
authorization/start were absent at review.

The coordinator confirms the corrected four-client diagnostic's original
execution completed zero. The reviewer verifies all four raw hashes and
completed-zero/known-clean records: stdout sizes are 8, 11,867, zero and 53,137
bytes. The crash buffer is empty; the bounded main/system tail contains no
LocalLore or AndroidRuntime entries identifying the timeout's cause. Absence
from this bounded sample is not proof that no fault occurred.

The corrected metadata/lifecycle diagnostic instead stops on its first client:
completed two, known cleanup, 94 ms, stdout/stderr zero. It produces no listing
and does not dispatch the second filtered-log client. No particular guard,
path, file state or storage cause can be inferred from that silent refusal.
Both predecessor diagnostic namespaces remain unexecuted and unauthorized.
There are no retries or further guest actions. Exact owner stop/terminal and
final inventories follow.

## Final owner closure and evidence

The coordinator confirms the original owner execution consumed tool terminal
zero after the exact admitted stop. Its actual result is `stop_requested`,
cleanup and preservation closure true, output capture complete true,
676,875 ms; worker return one reflects owned forced drain. Separately recorded
post-stop checks find all three exact original host identities absent and the
reserved ports free. This differs from the previous missing-owner attempt;
that older completion/cause remains unknown.

Actual retained owner stdout is 13,835 bytes, SHA-256
`01958ad0d86494870b59e878aa518b1a52c7617d01e5fd7d1141d52143c3310a`;
stderr is 1,016 bytes, SHA-256
`1e01aeeacf0c6464ca5d3928d90d1862a31779cd8bc39cf2912f313304808c18`.
Their sizes/hashes match the capture result and final inventory. Complete
capture describes this bounded pipe evidence, not un-emitted child buffers,
guest flush, disk integrity or application success. Saved disks remain retained
with metadata-only observations.

The reviewer independently rehashes every final inventory row without mismatch:

| Inventory | Files | Bytes | Index SHA-256 |
| --- | ---: | ---: | --- |
| Host | 1,433 | 94,023,549 | `bbafecfa8eb59c91791ba8b5e3c8a8404d32becf4e994670359f105bce08ac2d` |
| Environment | 23 | 393,469 | `9bf0dc1881e52c7425e2813e128e0cf730a34c62cdd67632f6519afe245ae1f0` |
| Device | 140 | 86,336,185 | `555298fba504746588785cc291d8db8b7a785bcbf2e1a256bebb8e7e89ff1b6c` |

All 49 original admitted inputs, 86,184,967 bytes, independently match the
create-only archive and proposal mapping; archive index SHA-256 is
`d0efc2529b5fd680d8edb2249b41823300a444aee8185564c3b110d764ad82fa`.
The updated public verification accurately records the partial result, all
diagnostic dispositions and remaining limits. No extra device operation is
needed or performed by this review. All 913 non-Markdown current source rows,
11,728,643 bytes, still match the frozen executed source; subsequent public
documentation updates do not change that implementation.

## Disposition and next task

This supervisor-evidence prerequisite has implemented, host-tested and actual
retained-run evidence. The Android setup/helper gate remains incomplete: the
new initial cohort has two passes/one failure, no accepted helper binding,
separate-process reopen, eight-proof read or 44-check qualification. Earlier
passes remain historical and cannot be combined into this cohort.

Next add a bounded sanitized synthetic-fixture failure receipt capturing actual
phase/error/source progress at a failed READY assertion. Diagnose and fix the
observed failure before another separately admitted fresh qualification; do not
extend the ten-second timeout or infer a storage/lifecycle cause from the
silent metadata refusal. Existing A/#117/#119 and full M05/M01, real-model/SDK,
DocumentsUI, reference-phone, ARM64/16 KiB, cache/privacy, power-loss, quality
and sustained-runtime gates remain unchanged. No release or merge is qualified.
