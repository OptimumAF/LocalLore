# Independent receipt setup helper review — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).

## Scope and current disposition

Independent review under root claim6387585436, subclaim6387603767, from exact
`64f499e090fb48a4b6526b448a3636752d618038`, stacked on unmerged #147.
The reviewer owns only this report, with no implementation edits, builds,
shared-cache changes, SDK/ADB/AVD/model operations or execution authority.

The host process-boundary correction is implemented and its 20 independent
tests and 579-test full suite pass. The new fresh guest attempt stops before a
method completes: the initial instrumentation returns 255 with only its first
START record. No helper is bound and no restart or proof read occurs. The
original emulator supervisor's terminal record is unavailable; later host
identity/preservation observations do not establish its orderly cleanup.

The preceding attempt remains its separate initial three-pass result followed
by an all-processes-quiet refusal. Those historical passes are not adopted into
this new cohort. Full Android helper/restart qualification and existing
model/runtime/device holds remain incomplete.

## Actual source and contract review

The correction adds `ProcessBoundary` around the unchanged strict process
parser. Before and installed observations require no LocalLore processes. The
sole helper-binding point is after initial exact three-pass parsing, at the
expected observation/stage/instrumentation count. APP target absence remains
mandatory. At most one TEST-main row is recorded separately under the already
pinned distinct TEST UID. APP service/provider names, TEST colon processes,
wrong UIDs and other LocalLore rows refuse through the shared parser and exact
name/count checks.

Later observations accept only that exact PID/UID/name tuple or its natural
disappearance. Once an observation sees it absent, its allowance is permanently
revoked; an initially absent helper cannot later appear. Sequence skips,
duplicates, stage/count mismatches or classification failures make refusal
sticky. Returned diagnostic rows are copies, so consumers cannot mutate the
private bound tuple. `target: []` and `test_helper: [...]` explicitly distinguish
APP absence from all-process quietness.

The actual `run_cohort` keeps strict initial transcript parsing before helper
binding and proof inspection. It retains the separate restart invocation and
linked changed APP PID/start proof, exact package/UID/media/capacity checks,
existing client and aggregate budgets, and raw-first evidence. No stop,
arbitrary shell, install replacement, SDK or alternate target capability is
added. No concrete source blocker was found in the initial diff.

PID/UID/name equality is an observation identity. It does not attest process
start time or continuous helper liveness between snapshots; an unobserved
disappearance and same-tuple reuse cannot be detected by this protocol. The
helper is granted no SDK/resource ownership or lifecycle authority. Reports
must say observed disappearance, rather than promise continuous identity.

The coordinator's follow-up `1fd719e4d6f79b7b0352ea7cc50ba242fed89f30`
adds exact observation/count/UID-map types and facts version two. It explicitly
documents this identity limitation; no extra process query or authority was
added.

## Input evidence reviewed

The new disabled prepare proposal SHA-256 is
`043e337ba0d8477ff071b93129c39340d4f8827ea4eabb6e6b0ba951d4ad1429`.
Independent streaming hashes match all 909 bindings plus eight old-registry
metadata records and the read-only existing console token: 918 rows,
5,046,148,411 bytes. Target and authorization were absent at review. The proven
JBR17/helper/installed-tool set, requested 12 GiB userdata/8 GiB SD/2 GiB RAM/two
CPUs, fixed new paths and resource floors are unchanged. Token contents are
neither copied nor reported. Preparation remains distinct from launch or guest
qualification.

For reuse of the actual audited APP/TEST pair, the reviewer independently
compares all 457 relevant app/native/build/script source rows, 5,975,443 bytes:
live sources equal the prior compiled snapshot and recorded digests. Both
retained APK sizes/hashes match their audited records. This is source/artifact
equality, not a fresh Android compilation or a new model/runtime result.

The coordinator confirmed the original full host check completed zero with
known cleanup in 54,953 ms: 579 passes, zero failures/errors/skips, 54.193
seconds. The reviewer checked the 67,403-byte output digest
`24bc3812a68433b86055afc0e462afa7f11e3de7297ac5ac1c5bf914d4a63f98`.
All 1,421 frozen source files, 16,755,487 bytes, independently match commit
`058c796560a433f585e7632d74397bf4ac5ff366` and snapshot index SHA-256
`cf0a678e3ea797ebba8ad0303b3be73a353c081de79229979a495f61809b9c5d`.
The complete Git diff from the previously compiled source contains only this
controller, its tests and documentation; app/native/build files are unchanged.

The coordinator confirmed original preparation completed zero with successful
cleanup/closure and a created prepared record. The separately reviewed,
disabled run proposal SHA-256 is
`980b312ee187c3878988ef3ed2123fa8a5765d14cc7598db519886c9b5aa3513`.
Shared fields and all 909 input rows equal the reviewed preparation. Sixteen
linked prepare/result/prepared, immutable, initial 8 GiB SD, token and old-registry
rows, 8,590,136,613 bytes, independently rehash without mismatch. Actual config
retains the requested sizes and fresh owned paths, with userdata absent;
run authorization was absent at review. The unchanged helper omits the capped
legacy partition-size override. These inputs do not themselves establish
boot, usable guest capacity or setup qualification.

The separately disabled guest proposal SHA-256 is
`7f77564f0d80f7e065a98c63c5709a65a5c353101fed73ecd0e8f7bfac3df9c2`.
All 48 bindings, 86,158,025 bytes, independently match the frozen source,
audited APKs, current host evidence and exact live descriptor. A first read-only
lease check refused because the review invocation imported the host module
from the older review worktree. Pinning the exact central package paths fixes
that review-context error without source changes. The corrected closed
validation and full read-only live lease check complete zero, with about
1,120 seconds remaining, guest authorization/cohort absent. Neither check
invokes a device client. The context refusal is not an actual guest attempt or
evidence of a production defect.

## Independent adversarial tests

The independent sole-test-file handoff is
`639f53d17db7aac237ccb3d9280506439bfab9b9`. Its actual owned run completes zero
with known cleanup in 9,531 ms, 20 passes/zero failures in 9.093 seconds. The
reviewer checked all four before/after source bindings and the 2,815-byte output
digest `8f62305d389254dd2f6825b2775f2b94c35c6b79f7d9c0282c862b28b00e1af1`.
These tests cover helper absence/persistence/revocation, replacement/reappearance,
target/foreign/UID/order drift, diagnostic-copy isolation and sticky refusal.
Actual mocked Owner/cohort paths retain raw evidence and refuse restart on
invalid boundaries; full positives still require all 44 checks. No live
transport is used or inferred from those passes.

## Actual stopped guest and supervisor uncertainty

The coordinator confirms the original guest consumed outer tool terminal one;
the owned worker is separately completed two, known cleanup, 73,265 ms. Its
355-byte output SHA-256 is
`52b689d0cb08ded5316231dfa74c2ccf5e1c34cc1885855d4b4469360fe2b63f`,
outer stderr zero. Independent review of all 28 client records matches exact
order, stdout sizes/hashes and known cleanup. The first 27 return zero; initial
instrumentation returns 255.

Actual before facts report API35/x86_64/4096-byte pages and no LocalLore
packages/processes. After the two exact installs, the fixed pair/UIDs and single
public volume match, with both APP target and TEST-helper observations empty.
Userdata availability is 11,610,693,632 bytes before and 11,510,231,040 installed.
These are observations at those gates, not final capacity or real-model fit.

The initial runner emits only the first method's START, no method-end/result or
final runner record. Its 386-byte output SHA-256 is
`48d997addc4e53aead1474d66fcddddeee7cbd98212c1e88104d1289d6761baa`.
No method completed in this attempt. The controller dispatches no helper-binding
inventory, restart instrumentation or proof read and does not produce an
initial-pass aggregate. The runner's exact failure cause is unknown.

The original emulator supervisor then becomes unavailable to the execution
tool. No final owner result, stdout/stderr record, stop request or original
terminal fact exists. Post-loss host-only checks complete separately and report
the three recorded host identities absent, ports free, and installation,
prepared immutable inputs and old-registry/token metadata preserved. These
checks do not recover the missing terminal or prove cleanup of the supervisor's
entire descendant tree. Do not claim orderly closure, guest flush, saved-disk
integrity, or a causal link between supervisor loss and runner 255.

A proposed bounded four-client read-only diagnostic remains disabled,
authorization absent, with no result/client execution. It was not used after
the live owner lease was lost. No new device calls, fallback supervisor,
fabricated owner result or blind retry follow.

## Final evidence and next task

The reviewer independently rehashes all final inventory rows without mismatch:

| Inventory | Files | Bytes | Index SHA-256 |
| --- | ---: | ---: | --- |
| Host | 1,430 | 93,974,121 | `9d0a22d756aaf5d317f51d0c957d3bc39b9c52de5ab5292fbe036e1a2f88f367` |
| Environment | 19 | 378,584 | `939de1cdaa6d73767fd13733821e2c0e7b927d4aff45c81e7c765e301a4b0eba` |
| Stopped guest | 117 | 86,225,090 | `33938714a27dca1d918677bf6ee77397b62bcc91d44458c52ca75fc7e039a449` |

All 48 original proposal inputs, 86,158,025 bytes, are archived and independently
matched to their admitted hashes. The archive index SHA-256 is
`980e5aa2898aa8071701b494d35833df55e41e2a6314c2af0ff0f44cfb58938d`.
All 912 non-Markdown live source rows, 11,704,627 bytes, still match the frozen
source snapshot; subsequent documentation reports the actual partial result.
The public verification and README accurately preserve this distinction.

This M05.05 prerequisite is implemented/host-tested but remains incomplete on
Android. The next runnable prerequisite is bounded durable supervisor diagnostic
capture with an actual loss-case test before another separately reviewed fresh
qualification. Require three initial passes plus one separate-process reopen,
all eight proof reads/44 checks, final observed identities/capacity and known
owner cleanup. No cause or successful runtime is inferred from this stopped run.
M01.05 gains no model result. DocumentsUI delivery, real weights/SDK, reference
phone, ARM64/16 KiB, cache/privacy, power-loss, quality and sustained behavior
remain separate. Existing A/#117/#119 and full M05/M01 gates remain unchanged.
