# Independent send-boundary and portable-schema review — 2026-10-25

Refs #9 (M05.05), #5 (M01.05), with M01.04 support. Root claim 6398576419, review
claim 6398587584, compatibility-plan extension 6398696909. Reviewer owns only
this report on `review/m05-send-boundary`, from `2c16e157`. Integration,
authorization and actual execution belong to the coordinator.

## Source findings

The final/internal receipt trace holds six closed argument/call-site counters,
bounded private monotonic times and immutable snapshots. It has no request,
prompt, schema, path, role, Throwable or caller clock input. The independent
v1 status is 1338/`locallore_receipt_send_v1`, 2048 B including its prefix; old
worker v2, positive 122-check proofs and budgets remain separate. Missing
observation never means zero or a healthy/reusable owner.

`observedLiteRtSend` passes the exact prepared object once, suppresses observer
errors and rethrows the identical preparation/dispatch failure without adding
causes/suppressed exceptions or inspecting private error accessors. Production
accepts only the final bounded trace; arbitrary observer injection is a pure
test seam. A blocked arbitrary observer is not covered. THROWN is recorded
before the original exception reaches the existing failedStart/quarantine
catch; there is no fence-before-every-diagnostic claim. Existing callback-fence
priority and resource cleanup/quarantine authority remain unchanged.

The production wrapper constructs typed prompt/callback/token/thinking/response
arguments before the literal original public SDK invocation. The pinned
[ResponseFormat implementation](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/ResponseFormat.kt)
returns plain ResponseFormat, parses JSON syntax and retains its schema string;
it does not validate decoder vocabulary. The pinned
[Conversation overloads](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt)
perform further conversion/checks before JNI. ASYNC_CALL_ENTERED therefore
means an application public-call site, not SDK-body/JNI/native entry. RETURNED
is synchronous invocation return, not async success, terminal/drain or close.
A callback can precede a return or throw; the host must not invent contradictory
cross-channel lifecycle rules or compare independent clock origins.

The Candidate getter is nullable and receipt-build-only, backed by the actual
admitted owner's private trace. There is no reset, setter, replacement factory,
SDK option, model choice or callback injection. Actual ordinary setup/play
Activity, VM and controls remain unchanged. Failure-only worker/send status
delivery is independently guarded and cannot replace the original test failure.
The strict host decoder preserves raw-first evidence, separate channels,
exact framing, privacy/bounds and original runner/proof refusal. A diagnostic
cannot satisfy the positive proof grammar; persistence uncertainty stops work.

Independent primary-source review identified a known-but-unimplemented
`uniqueItems` mismatch in the pinned strict LLGuidance compiler. The portable
representation now enumerates every canonical nonempty eligible nearby living
nonplayer listener set of size ≤ 4 using supported exact-array enums. It does not
drop listeners, choose only Mira, weaken uniqueness, use lenient/regex/null
fallback or expand a budget. Incremental checked-byte construction refuses
without publishing a partial catalog. Existing prompt/token limits still apply.

Typed Say audiences remain BTreeSets: ordering/duplicate normalization stays
unchanged. Schema exclusion of self/duplicates is not a newly claimed engine
refusal. Genuine literal-intent, size, location/liveness, narrator, canonical
commit and replay authority remain in the engine. See the reviewed
[portable-schema contract](PORTABLE_DIALOGUE_SCHEMA.md) for exact primary pins.
This source mismatch does not identify the discarded cause of the earlier run.

## Independently replayed final host checks

Execution source `e1d6b26797ddfc61772349403345cbd986c255ba`; actual final Android
and Rust compilation source `8258698398889ebdd5f9ec589b36a22608bcbc9f`.

| Gate | Retained result |
| --- | --- |
| Rust fmt/clippy | Locked/offline corrected host-feature and Android model-provisioning commands pass |
| Core Rust | 351 passed / 4 historical capture tests ignored / 0 failed |
| Android bridge Rust | 90 passed / 0 ignored / 0 failed |
| New portable-schema cases | 9 passed, synthetic providers; not SDK/LLGuidance execution |
| Receipt JVM/lint | 454 tests / 42 suites, 0 F/E/S; 0 errors /19 warnings |
| Regular JVM/lint | 396 tests / 37 suites, 0 F/E/S; 0 errors /9 warnings |
| Final Python | 788 passed / 67.578s; owned 68,453ms, known cleanup |
| Audits/signatures | All six known-clean returncode 0 records and raw hashes match |
| Source | 218 Android rows /2,439,317B and 302 Rust rows /4,764,876B match actual compiled source |
| Frozen source | 1563 current/snapshot files / 19,203,534 B matched at admission |

The first Rust command omitted the host feature and failed before tests at an
existing feature-gated inspection import. Its known-clean 101 result/16,140ms
and original log remain preserved. The corrected result is 0 /146,438ms with
56,765B SHA `faaf81fb8e02c3c7fbcb8969cbfc8262e31b773e6eab86e03167ff30cf921591`.
The earlier observer-only 454-test build is historical and was not admitted as
the final portable-schema artifact.

Final receipt APP 82,739,330B SHA
`32ea3fc7bd04df4cad002fb044a4876c2f3e1658d0d90cc525e1eece3df31c9b`;
TEST 2,056,555B SHA
`c94a510a383d8788c5d57375823490dc81182a6f801f994864ca8d32d74e9c12`.
Regular APP/TEST pins also match their copied artifacts. Independently hashing
both APKs' native-engine entries confirms equal ARM64/x86_64 bytes across
profiles; package size alone is not a native-code equality check. Normalized
worker SHA `aa004c6b32782f1f29606942427ace0494e1c29c78fda44c1c2c431b37b8bdb4`
matches the Candidate constant/manifest and Gradle provenance pin.

## Resource preservation and admission

After final check handles ended, the coordinator's retained relocation record
reports 1825 generated ignored host-cache files /3,998,293,757B moved from D debug
output to a fresh C location, with no live source references and old source
absent. This reviewer inspected records only, not cache bytes. The record makes
no content-hash claim; model/SDK caches, held AVD disks and evidence are separate.
Copied artifact/source/binding records have no dependency on that generated
directory. No reserve was reduced to admit work.

PREPARE `910f9e43…ae116` passed independent closed-policy/source checks:
905 non-image tool/source contents /1,332,027,052B match, four public SDK images
are metadata/size-only. Existing registry/config metadata and the private token
hash are preserved without token-content disclosure. Fresh target and grant
were absent, ports free. Current C 134,899,097,600B / D 46,555,369,472B,
available RAM 36,185,829,376B /20 logical CPUs passed unchanged C/D 40GiB and
host 12GiB floors. Profile remains 12GiB userdata /8GiB SD /8GiB RAM /four cores.
The reviewer performs no SDK/guest execution, model-content, AVD-disk-content or
cache-content operation. The four SDK `.img` entries are metadata-only.

RUN `9d4ee2a2…18586` independently preserves that exact proposal/profile,
completed preparation closure, three immutable config/registry files and own
paths. The initial 8GiB SD is metadata-only for this reviewer; userdata is absent,
boot unverified, grant/running descriptor absent and ports free at review.
The fresh facts pass unchanged floors. The known-clean preparation client 0
took 5125ms and its retained output hash matches. No running descriptor alone
will establish boot, SDK entry, success or cleanup.

PREFLIGHT `d0f42bb7…62632` independently matches all 123 current and archived
nonweight bindings /95,351,891B. Its actual 44 owned clients completed 0 with
known cleanup; strict runner parsing establishes one PASS and 12 true checks,
206ms whole-test observation, no SDK invocation or model copy. The outer
known-clean result is 43,140ms. Proof SHA is
`2e16eec007ccb9a152f1732f295a4916723e2659e5227828ce70ce7f4f627764`.

CANDIDATE `f63d0910…ccac1` independently matches 127 current and exclusive
archive bindings /95,358,132B, actual prior proof/facts/results, final APK pins
and standing human consent. The model is metadata-only and excluded from
generic bindings. The cheap cached-prelaunch lease check observed the exact
run/descriptor and three live identities, no stop/result, and 1525.7s remaining
against the unchanged 920s entry requirement. Grant and driver were absent at
that review; the coordinator subsequently admitted the exact proposal.

## Runtime disposition

The fresh candidate stopped at ORDINARY_DIALOGUE. Independent raw replay
confirms 46 completed 0 client records with known cleanup and matching stdout
sizes/hashes. Its outer result is child_exited / worker 2 / 373,187ms, capture and
cleanup true; stdout 466B SHA
`7ec03aebfec2520ad9f212a48d8d2793fc8b715cf838357fcc3597bf3f738f91`.
The coordinator consumed original candidate 64634 with tool terminal 1; that
outer tool code is distinct from retained worker 2.

| Phase | Actual qualified result |
| --- | --- |
| SOURCE_PREFLIGHT | 1 PASS / 12 checks / 206 ms; no SDK/model copy |
| IMPORT | 1 PASS / 16 checks / 94,401 ms; no SDK |
| ORDINARY_START | 1 PASS / 28 checks / 82,875 ms; real SDK gift, revision 1/one receipt |
| ORDINARY_DIALOGUE | 1 FAIL / 51.291s runner; no positive proof |
| ORDINARY_REOPEN | Unrun |

Thus 56 of 122 planned checks are qualified, with three selected method passes
and one failed method across preflight and candidate. The 46 candidate clients
are separate from 44 preflight clients. START proof SHA
`77af7deaebb8cdf48dab8a174906eb8d4f0ff78521978621d23981790655d4a2`
links the import process to a new ordinary setup/Start process; its gift receipt
SHA is `e828ebbb70f19466c99c8a162a800bcdf1df3044bdd248f66aa397f6fd540014`.
Phase clocks are whole-test observations, not generation or UI latency.

The failed Dialogue raw 5847B SHA
`69d38b407614fe9d71a2d6d1fcf71a1c3b44277c6141b24323d659069e5b5919`
contains both actual custom status channels. Strict independent extraction
matches both persisted sidecars, while the unchanged positive runner refuses
the failure. The send trace records argument construction returned and the
application SDK invocation returned, each once, with neither THROWN event.
Their own times are 19,067–19,074ms and 19,074–19,083ms; snapshot 34,215ms.
The independent worker trace records 21 paired MESSAGE callbacks, then one
paired ERROR, one paired cancel and two UNCERTAIN observations; no DONE,
settled drain, known conversation/engine close or Narrator creation. Counts
are historical callback observations, not token counts or atomic native state.
No Dialogue/reopen proof exists. No model recheck or canonical Dialogue
inspection is inferred safe after uncertainty.

This run actually exercises the failure-only send transport. It differs from
the earlier nonreturning call-site observation, but does not prove the cause
of either failure, successful constrained Dialogue completion, or native
cleanup. The portable-schema source correction remains independently justified
by compiler support; this failed attempt does not establish an error cause.

## Known closure and sealed evidence

The coordinator consumed original owner 89792 with tool terminal 0 after the
exact admitted stop. Its retained result is stop_requested / 760,047 ms,
worker 1 from requested job drain, capture/cleanup/closure true and guest flush
false. The independently hashed copied captures contain 11,234 stdout bytes and
1,083 stderr bytes. The post-stop host record observes all three recorded
owner/worker/launcher identities absent and ports free. These host checks do
not establish guest filesystem flush or final disk integrity.

Every listed row was independently content-hashed, size-checked and compared
against the exact current file set, excluding the inventory itself. No row is
a weight or virtual-disk file; no private sealed namespace was modified.

| Namespace | Files / bytes | Inventory SHA-256 |
| --- | --- | --- |
| Host | 1777 /260,185,030 |`b483041d352ffe87e18c521f972b026bc420688b5dd687e25a14866e5895879e` |
| Environment | 27 /390,063 |`c416f047fb572ae691ee47d2f7a91a16a451efd70dd1bd5b259e77d407be1c2c` |
| Preflight | 230 /95,480,004 |`9f9a999997bbf71cd9ccc40bf02ccdb50b4f553521f5191d085b7cf773b3a628` |
| Candidate | 245 /95,508,939 |`15df00ab75f7a6ee7f910ba960d90218ddb5b868209222b374e0982b2621cfb7` |

Total 2279 files / 451,564,036 B. At final review, all 1001 non-Markdown source rows
/ 13,352,106 B still equal execution freeze `e1d6b267`; only later public
documentation may differ. The failed send sidecar SHA is
`349f35de9a169fc6441506b588d241efa300fdedf87b9664c309b0fd47141563`;
worker sidecar SHA is
`46e5f624744a5fce452b3d37801c98ac2ca0b4faa438db75dcac7564e6054c51`.
Sidecar formatting hashes are distinct from the compact status JSON and full
runner capture hashes.

## Remaining gate

The next useful bounded experiment is a privacy-safe observation of the
configured request token budget and callback terminal category at existing
application boundaries, retaining original fences, deadlines and fresh-owner
admission. The pinned
[SDK callback adapter](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt#L623-L628)
maps cancellation separately but otherwise puts status and text into a
message-only exception. It provides no public numeric status property.
Parsing exception messages would violate this packet's privacy boundary;
callback counts must not be relabeled token counts. No native getter or
post-uncertainty model/cache inspection is justified by these observations.

Dialogue completion/receipt, inspector-family qualification and reopen remain
incomplete. Earlier passed product families remain historical evidence, not a
substitute for this failed family. No physical-phone/ARM64 execution, 16 KiB
runtime, DocumentsUI, NPC secret resistance, generated-text quality, pressure
qualification or full milestone completion is claimed. This packet makes no
causal performance or decoder-error diagnosis and authorizes no merge.
