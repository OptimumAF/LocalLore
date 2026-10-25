# Independent ordinary local-route review — 2026-10-25

Refs #9 (M05.05), #5 (M01.05), and supporting player-inspection work in #10.
Root claim6398062716; independent review claim6398092446. This review owns only
this document. The coordinator owns integration, authorization and execution.

## Scope and source

Execution source is `edf2ce1ab8ab86a09057f42f7ae32349e4d3dca0`, with Android
compilation source `37507f487e18e35bb41732869ae0b94b3fdc591c`.
The separate review worktree is `review/m05-ordinary-local-scene`, based on
the shared observation-interface commit `a149baac`.

The fixture launches the exact production `LocalModelSetupActivity`, waits for
its own IO verification to reach READY, and clicks the actual Start control.
It captures exact resumed `LiteRtPlayActivity`, its existing production
ViewModel and its already-created transport. There is no test Activity/factory,
ViewModel replacement, manual prewarming or replacement owner. New story,
Action/Dialogue selection, Send and record inspection use production Compose
controls. DocumentsUI/model-picker coverage is separate.

The nullable weak transport getter only observes original construction. Its
returned object remains command-capable; it is not an enforced read-only
capability. The fixture limits its borrowed commands to resume/play_snapshot,
checks the production owner around borrowing and later observations, and closes
through actual Activity/ViewModel teardown. A retained handle cannot override
quarantine. A missing observation, including retained-ViewModel recreation,
refuses without constructing a fallback owner.

The receipt-profile snapshot getter has no reset, setter or observer callback.
It exposes bounded immutable metadata from the actual worker. Null never means
zero. Zero-work checks require zero event/creation counts, null event times and
no saturation; elapsed snapshot time may advance. Positive histories require
director/narrator, optionally one director repair, public drain/close recording
points and no recorded uncertainty. These are historical observations, not
jointly atomic native state, hidden reclamation or future-callback immunity.

Review corrections incorporated before compilation:

- Exercise both hidden Mira and Oren seed beliefs, plus the unknown beacon
  fact, through zero eligible results and the actual empty record UI.
- Bind literal Dialogue to the exact scope, prior revision, Mira audience,
  event/source2, player speaker and unchanged question text.
- Bind the directly used shared cancellation proof/identity/capacity source
  and JVM test explicitly in the new controller.
- Explicitly require null event times for zero-worker sidecars.

The player record is a four-section player lens with typed provenance and
eligibility applied before search/count/paging. It is not a summaries/indexes
debugger or privileged NPC/omniscient inspector. Player-known public seed
`SECRET-TIDE-731` is an expected positive, not a forbidden leak. The literal
question is recorded speech, not a new canonical truth or an NPC answer.

Unlearned ability and duplicate gift inputs are real-route mechanical
preflight refusals before model generation. They do not prove that a model
rejected an adversarial proposal. Current Rust Dialogue skips the Action
compiler, but a newly accepted Dialogue still uses director then narrator;
idempotent replay or early refusal must not be mistaken for a fresh SDK turn.

## Independently checked host evidence

| Gate | Retained result |
| --- | --- |
| Receipt JVM XML |435 tests /41 suites, zero failures, errors or skips |
| Receipt lint |0 errors /19 warnings |
| Regular JVM XML |377 tests /36 suites, zero failures, errors or skips |
| Regular lint |0 errors /9 warnings |
| Final Python suite |774 passed,82.141s; owned83,203ms, known cleanup |
| Artifact audits/signatures |Six retained known-clean returncode0 records; raw hashes match |
| Compilation source |216 Android rows /2,410,032B match execution source |
| Frozen source |1,554 current and snapshot files /19,100,075B, zero mismatches |

The full source comparison was made at admission. After the coordinator's
documents-only verification updates, all996 non-Markdown rows /13,289,118B still
match the frozen execution source independently, with zero mismatches.

Independently hashed receipt APP75,020,368B:
`caf967a0b8ff7daa0775409bb5b7994194ffb1bff36685e55b6b5eb0dff18797`.
Receipt TEST2,056,171B:
`31acce94c98f7c9b59f1beca0764cac0324cb9e759f6a7bf7fdc9f060f5d0043`.
The unchanged pinned SDK/model/worker, offline dependencies and resource
quarantine remain authoritative; no dependency or runtime choice was introduced.

## Admission review

Exact preparation proposal `72cc6210…4930aa` and RUN proposal
`7f9d66db…3ec56` passed independent typed-policy, linkage and preservation
checks. Each review hashed905 non-image tool/source bindings; four public SDK
images were checked by metadata/size only. No reviewer image, model or VM-disk
content read occurred. Eight existing registry/config metadata records and the
private console-token hash remained equal; token contents were not disclosed.
An initial reviewer import-context refusal used an older host-module path;
the corrected check pinned both package root and cwd to the coordinator source.

The fresh C-root profile retains12GiB userdata,8GiB SD,8GiB guest RAM,4 cores,
C/D40GiB floors,12GiB host available RAM, fixed5592/5593 ports and1800s owner
lifetime. Prepared linkage, three immutable metadata files, own paths, absent
userdata and boot-unverified state were checked. The blank SD was metadata-only
for this reviewer. The coordinator performs the full stock/disk checks.

Preflight proposal `f66cfd6d…03de7`: all105 current and archived nonweight
inputs /87,264,306B matched. Actual preflight was independently replayed:
44 returncode0 known-clean client records, one exact passing method,12 true
checks /198ms, no SDK or model copy. Raw proof SHA:
`689d876b241f8bee995fd338c915d6c9c02c815d366571a39abc01a8940bd027`.
The outer result was known-clean child0 /41,266ms. The observed CPU count was4;
the installed APP/TEST map, distinct UIDs and volume/capacity facts matched.

Candidate proposal `3b0c7a04…3fd212`: all109 current and archived nonweight
inputs /87,270,547B matched. The actual old-family preflight links and direct
human local-copy/inference consent were bound; model contents were excluded
from generic bindings and archives. The cached prelaunch review plus cheap
live identity/prepared/deadline check found three exact live host identities,
no stop/result and sufficient remaining lifetime. This is an input review,
not authority to grant execution or proof of boot/inference.

The fixed new controller preserves its own grammar/namespace, exact selectors,
old prerequisite contracts, raw-first evidence, strict120s runner gate,
170/170/120s proof caps,870/900s aggregate/outer and920s entry gate. Failure,
unknown client cleanup, owner loss, malformed proof, drift or exhausted budget
must stop later dispatch. No worst-case completion guarantee is implied.

## Runtime disposition

This is a partial result: **56 of122 planned protocol checks qualified**.
There were three passing selected methods (preflight, IMPORT, START), one
failed DIALOGUE method and no REOPEN attempt. The candidate has46 completed
returncode0, known-clean client records; a successful instrumentation client
exit does not turn its failed JUnit transcript into a passing method.
All44 preflight and46 candidate client stdout byte counts and hashes were
independently replayed, with status/cleanup checked separately.

| Phase | Durable result | Whole-test observation |
| --- | --- | ---: |
| SOURCE_PREFLIGHT |1 PASS /12 true checks, SDK false |198ms |
| IMPORT |1 PASS /16 true checks, SDK false |94,338ms |
| ORDINARY_START |1 PASS /28 true checks, revision1 /one receipt |80,930ms |
| ORDINARY_DIALOGUE |1 FAIL, no43-check proof |Runner35.764s |
| ORDINARY_REOPEN |Unrun, no23-check proof |— |

These durations are not inference latency, Start-button latency, cancellation
latency or evidence of a causal resource speedup.

IMPORT has actual independent verification and production import counts of
one open/one close/2,588,147,712B for each source pass. Its raw proof hash is
`bf005fc82f71b602a5a6584b3f884d618b6d4b1135182cf5aad5a5e23781dca2`.
START links this proof and a changed process identity, actual ordinary setup
READY/Start/exact play Activity, visible accepted gift, canonical revision1,
one receipt, full accepted-model postcheck and actual Activity/owner closure.
Its raw proof hash is
`188d88670773f87783cd96bf5307ffb707a7316ccedc3e05e0b1427979bef27b`.
The gift receipt hash is
`4aabf29e6d3eb12b1eb0b2bf56c27ef64c71b7494bb1e9f677103accf0171304`.
The hash-linked START trace records D,N, two DONE/public drain/conversation
close observations, one known engine close and zero uncertainty. Repairs0,
fallback false were observed. After-import/after-start facts retain the pinned
pair, distinct UIDs, public volume, absent APP and separately classified TEST
helper; they do not establish continuous liveness or absence between samples.

Candidate original35971 ended with outer tool exit1 and retained inner worker2,
known cleanup/capture,347,172ms. Its466B stdout SHA is
`0594dbb14c7cad1770dcf6adbb4f3a69c48cf8462b4a76bb5201dcc1b6819b85`;
outer stderr0. Command46 DIALOGUE completed returncode0/known cleanup but its
strict selected runner contains one FAIL, not a timeout at the120s runner cap.
The5,365B runner SHA is
`bff70fa2b5ce00c6b1fb0f6272efbcb3498c5fbc989b45c691f44c7d606ca4d3`.
The check failed in `settled` after the real Dialogue Send. Source order shows
the inspector and mechanical-control checks were reached first; it does not
publish an independently qualified43-check result or zero-worker sidecar.

The bounded failure trace records one returned DIRECTOR creation, send
admission returned and SEND_ENTERED, but no SEND_RETURNED, message/terminal,
drain or known-close observation. UNCERTAIN2 is compatible with the same inner
failed-start and outer catch notifications, not two independently identified
SDK errors. The original exception is discarded by the existing send catches.
No grammar, cancellation, model/container, resource or native cause is proven.
There was no post-uncertainty model/canonical reread, forced commit or retry;
accepted Dialogue/canonical revision2, no-SDK reopen and full122-check flow
remain unqualified.

## Closure and sealed evidence

Original owner19051 ended with outer tool exit0 and retained stop_requested,
699,594ms, worker1 from requested job drain, cleanup/capture/closure true.
Retained owner stdout11,237B and stderr1,084B match the sealed files. The copied
post-stop observation records all three host process identities absent and
ports free. Guest flush is explicitly false; this is not a disk-integrity,
power-loss or hidden native reclamation guarantee.

Every entry and exact file set in all four create-only inventories was
independently checked, with zero mismatches. No model or VM image is included.

| Inventory | Files /bytes | Index SHA256 |
| --- | ---: | --- |
| Host |1693 /174,517,836 |`af671aa81741551fcc5690b5810d3e99bf758a2802406b0001308d94963ddf3b` |
| Environment |27 /390,090 |`033ac2f6c7615d6e91a7a3235463b83588ba11dfaf7d0249b39952f797851371` |
| Preflight |212 /87,384,286 |`5f94dd3b289a11980055a7b9b8909337fa02bcd960ef94c0b049a1cb5e81d3f3` |
| Candidate |226 /87,414,512 |`72669e3ee481436d935021fb1a9b46efc1c31d40ebf157001669c4b2c9d54ba3` |

Total2158 files /349,706,724B. Private evidence stays sealed and local. The
reviewer performed no SDK, ADB, AVD, model-content or cache operation.

## Remaining gate and next bounded work

The actual ordinary Start route and real gift are positive evidence. The new
dialogue/inspection/reopen family remains partial. No phone, DocumentsUI,
NPC secrecy, model prompt-resistance, sustained-quality or full milestone
completion follows from this run or the earlier synthetic/API/UI successes.

The next useful observation should distinguish fixed response-format/argument
construction from actual async SDK-call entry, return and synchronous throw.
Current SEND_ENTERED is outside that wrapper; ResponseFormat construction is
evaluated before the SDK call. Use closed bounded stages/categories without
raw exception text/class/stack/cause, schema or prompt. Preserve the original
uncertainty/fence priority, quarantine, deadlines, owner lifecycle and privacy.
Injected argument-construction failure, synchronous async-call failure and
callback-error cases should remain distinct and must not gain reuse authority.
This recommends a measurable follow-up, not a diagnosis or permission to weaken
the guarded runtime. No additional experiment was performed by this reviewer.

The coordinator's [dated verification](RECEIPT_ORDINARY_ROUTE_VERIFICATION_2026-10-25.md)
and draft [PR168](https://github.com/OptimumAF/LocalLore/pull/168) preserve the
partial result and remaining gates. Technical review does not grant merge or
replace owner acceptance; the review claim is released separately with this
document's exact commit.
