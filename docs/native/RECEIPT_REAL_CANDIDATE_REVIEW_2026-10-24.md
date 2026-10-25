# Independent real receipt candidate review — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).

## Scope and disposition

Independent reviewer subclaim6389016608 under root6389003300, branch
`review/m05-real-receipt`, exact unmerged #151 base
`d8aa83d84628da839d6e6b1109a448cb0b7da866`. The reviewer owns only this report.
No reviewer build, shared-cache, SDK/ADB/AVD/model operation, weight read or copy
is performed. Source and small official-document research are read-only.
The runnable preparation is compiled and host-tested; the fresh 8 GiB emulator
passes the actual tiny staging preflight, one method/12 checks. No model is
copied and no SDK is invoked. The original owner falls below the frozen
candidate remaining-time gate before consent, so it is stopped without budget
relaxation. A future authorized candidate must use a fresh admitted target and
repeat preflight; it cannot borrow this used owner. Known owner stop/closure
and all final evidence inventories independently verify. Full real import/
gift/reopen, milestone and reference-phone gates stay unchecked.

## Pinned model and runtime facts

The existing runtime remains LiteRT-LM Android0.18.1, source
`bda624851d74be34d4e1f7fac1fc4155939539c7`. The current official
[release](https://github.com/google-ai-edge/LiteRT-LM/releases/tag/v0.18.1)
and [pinned Kotlin guide](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/docs/api/kotlin/getting_started.md)
support the existing Android Engine/Conversation API, CPU backend, local
`.litertlm` model path and explicit writable cache directory. Initialize belongs
off Main; resource closure remains necessary. This does not guarantee a
particular model's memory, latency, cleanup or semantic behavior.

The exact prepared publisher revision remains
`a790a852d433991c0c0a41c1154cf9b3850300fa`, file
`gemma-4-E2B-it.litertlm`. The independently fetched small
[publisher tree](https://huggingface.co/api/models/litert-community/gemma-4-E2B-it-litert-lm/tree/a790a852d433991c0c0a41c1154cf9b3850300fa?recursive=true)
records 2,588,147,712 bytes and LFS SHA-256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
This is publisher metadata, not a fresh hash of local weight bytes.
The [pinned prepared card](https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/blob/a790a852d433991c0c0a41c1154cf9b3850300fa/README.md)
identifies the Gemma4 E2B base, LiteRT-LM container and mixed mobile
quantization. Other web, GPU and hardware-specific NPU variants are different
artifacts and cannot substitute for this hash.

The [pinned upstream card](https://huggingface.co/google/gemma-4-E2B-it/blob/3e22461f65e89153144f8adb70e3b8c2cc9845a7/README.md)
and prepared card declare Apache-2.0. Google's current
[Gemma license page](https://ai.google.dev/gemma/apache_2) presents that license.
These support the existing local experiment; notices/provenance still matter
for any redistribution. No model redistribution, new dependency, conversion,
runtime upgrade or backend selection follows from this review.

## Human copy authorization

The coordinator supplies the trusted original human question/reply from its
history, question item `call_06b75caf43b843f5b62d61c2fe9f96c6`. The question
asked to copy the already verified 2.59 GB local Gemma into **both selected
emulators' isolated benchmark app**, with no download/external upload. The
human answer was: “Allow local copies to both test emulators”. Existing copy
records identify those two destinations as A/B and package
`org.locallore.runtimebench.litert`.

That is evidence for those selected installations. A new fresh owned emulator
and `org.locallore.app.modelvolumeverify` are new destinations, so this review
does not widen that answer into unrestricted future local-copy authority.
Agent reports or a synthetic pass cannot supply the missing destination scope.
Prepare the concrete build, fresh target and tiny nonweight staging test first;
then obtain the owner's explicit answer for that exact new copy if no newer
direct authorization supersedes the original. Do not ask again merely to repeat
an unchanged already authorized A/B operation; no such operation is proposed.

The final reviewable request should identify one fresh emulator/package, the
same exact model size/hash, the retained staged and receipt copies and SDK
experiment, with no old-cache reads, downloads or external uploads. Earlier
A/#117/#119 failures and preservation holds survive merging their source PRs.

Current GitHub readback confirms [#117](https://github.com/OptimumAF/LocalLore/pull/117)
merged at `bffc14215cb9ab06ae5bb2f898c944724f3889b8`: its measured gift timed
out and its cohort failed host-consumption/final old-cache metadata checks.
[#119](https://github.com/OptimumAF/LocalLore/pull/119) merged at
`ac952cebd75bad4e7cf62c87c66953870d4f81f0`: canonical/journal comparisons
matched, but cache metadata differed and preservation remained false. Those
observations are retained failures, not repaired by code merge. A new isolated
destination cannot authorize reads, retries, evictions or reinterpretation of
their old model/cache state.

## Staging boundary and minimum plan

Official Android15
[run-as source](https://github.com/aosp-mirror/platform_system_core/blob/android-15.0.0_r1/run-as/run-as.cpp)
checks an installed debuggable application and data-directory ownership,
changes UID/groups and enters its SELinux context before executing a command.
It does not make a shell-owned temporary file readable merely because Unix
mode bits are changed. The
[runas_app policy](https://android.googlesource.com/platform/system/sepolicy/+/refs/tags/android-15.0.0_r1/private/runas_app.te)
and [app policy](https://android.googlesource.com/platform/system/sepolicy/+/refs/tags/android-15.0.0_r1/private/app.te)
are relevant constraints; no app-domain access to a proposed shell-temp source
should be assumed without a tiny actual check. `adb push` alone proves neither
that access nor destination identity.

A file-backed stdin transfer into an exact `run-as` command avoids the extra
shell-temp duplicate and custom Python buffering of 2.59 GB. Android15's
[ADB client implementation](https://android.googlesource.com/platform/packages/modules/adb/+/refs/tags/android-15.0.0_r1/client/commandline.cpp)
implements `exec-in` by copying stdin to its raw exec connection, then returning
zero. It does **not** report the remote command's exit status. Thus client zero
is transfer evidence only. A later app-domain exact-size/full-hash check is
mandatory before source adoption/import; remote early exit, partial file,
symlink or wrong bytes must never qualify from client status alone.

Use the same exact binary tiny source and fixed create-only private stage path
for preflight, without model access. Prove bytes/length/hash from the application
domain, preserve refusal/partial evidence and refuse existing destinations.
Do not overwrite a file, relax SELinux, use privileged ADB, add a provider or
fallback to an unreviewed copy path after failure. The trusted transfer worker
and its child must remain in the original WindowsJob before the barrier is
released; no breakaway/new-session child, unbounded capture or whole-file Python
request buffer. Pin the actual source descriptor and verify source identity
around the separately authorized transfer. A local transfer terminal alone is
not remote-write completion or SDK cleanup proof. Observe any remaining owned
guest process before importing; uncertainty preserves the partial destination
and stops further mutation rather than authorizing a retry.

Capacity must account for concurrent copies on their actual devices: retained
internal staging consumes 2,588,147,712 bytes of userdata, and receipt import
consumes that much on the admitted external filesystem while retaining its
2,147,483,648-byte floor. The existing external pre-import requirement remains
4,735,631,360 bytes, excluding uncalibrated future SDK cache growth. Internal
staging needs its model bytes **in addition to** the controller's existing
userdata reserve and installation/OS overhead. A shell-temp copy plus a second
internal app staging copy would require another full model's userdata; do not
count those as one or treat nominal 12 GiB/8 GiB images as measured capacity.

The proposed closed environment pair is 8,192 MiB guest RAM with 12 GiB
available host RAM before launch, preserving the default 2,048 MiB/4 GiB pair,
12 GiB userdata, 8 GiB SD and two CPUs. Source review of the actual three-file
profile diff finds exact typed paired validation, plan-only selection, matching
config/launcher RAM and bound-prepare downgrade refusal. Nine new test methods
cover boundaries and zero-child refusal. Their actual retained host receipt
and output independently agree: nine passes, 0.308 seconds, owned completed
zero/known cleanup in 547 ms, stdout 1,348 bytes SHA-256
`8b011ce3f4eee7844abb15af734e0177d6b8c0fadc99717bfd7dd8d9b9f0bb80`.
Root integrates the three-file change as `f51fd87`; wider integration tests and
fresh actual resource observations remain separate. Assigned RAM is not model
support.

## Fixture and controller review

The frozen intended fixture has four exact selectors: tiny SourcePreflight,
real Import, one guarded Play and separate-process Reopen. PLAY must obtain a
fresh full `installed()` verification in its own process before constructing
the candidate transport. PID/start provenance links must not assume that four
ordinary instrumentation invocations share one process. Reopen reads accepted
state and canonical gift/receipt without reading the staged source or invoking
SDK/free-text again. A fixture-written marker alone cannot attest that gift.

The existing `LocalInferenceOwner` returns a prepare reply only after its
bounded finish path reports role drain/close and Engine close known; uncertainty
poisons and refuses. A Prepared result can therefore establish that public
contract, not hidden native-thread reclamation. The plan also requires full
accepted-model verification after SDK completion and before canonical commit,
only after that public close/drain boundary. Unknown ownership preserves and
stops; it does not authorize a model read or a replacement owner.

Declared observation budgets are preflight30/import150/play170/reopen120
seconds, with the existing production turn60/cleanup5 seconds unchanged. A
distinct source-bound one-shot 900-second aggregate controller may compose
these phases and bounded transfer; legacy controllers retain their own limits.
Actual file/hash timing still must fit those explicit bounds. A timeout cannot
fabricate READY, accepted state or successful cleanup.

Actual fixture review found and corrected three concrete issues before
integration: a redundant post-commit full-file rehash for profile comparison
(reuse the verified post-SDK files instead); duplicate source-open assertion
after raw descriptor acquisition (claim the phase before acquisition); and
IMPORT predecessor-key mismatch between Kotlin and Python (the exact key is
`prior_preflight_sha256`). Latest reread confirms these corrections and a
NonCancellable request for Main-side close scheduling. This remains source
review, not proof of completed cleanup or a compiled/device pass. Actual
closed keysets total 56 checks: 12/16/15/13 across the four phases.

The initial controller draft retains the legacy selected-runner wrapper and
hardcoded default dispatch, sharing framing through a private implementation.
Its new fixed selections do not introduce a proposal-selected class or command.
Preflight and candidate have distinct phases and six-key grants; preflight
cannot authorize weight transfer or SDK work. The candidate additionally names
the new human consent reference and links successful preflight on the same live
owner. The source is excluded from generic byte-buffered bindings/archives.
Initial review requires worker replay/parent binding, budget and failure-retention
tests before admission: an in-memory one-attempt flag alone does not bind a
separately invokable stream worker. The actual correction and tests follow.

Root initially adds persistent parent/worker claims, then the independent
regression suite exposes a missing actual-parent check: a live recorded parent
was accepted even when `os.getppid()` differed, including after source hashing.
The retained old-source attempt genuinely runs 14 tests with two failures;
it is not recast as a pass. Root fix `d104024` checks actual ancestry before
claim and before spawn. The unchanged 14 tests then pass, with tiny original
data only, 2.978 seconds and owned completed zero/known cleanup in 3,281 ms;
stdout SHA-256 is
`886bc6da7ac0bde51e9a9eb01080c5aa027ef604b82b1833aae5b6a5d22b52b8`.
The old red output SHA-256 is
`ab85715dec1a6d9bf169479054fe65753f5fb04b45d233ae20baee0d1435c5ff`.
Both output digests and result metadata independently match.

These tests reach valid candidate/preflight lineage before testing absent or
wrong consent, avoiding an earlier masked negative that rejected the tiny
source size first. They also exercise actual mocked IMPORT/PLAY/REOPEN ordering
without reinstall, stop after failed phases, held-FD mutation, one-shot claims,
180/900-second wrapper selection and capture/cleanup refusal. Such mocked
passes do not grant copy consent or establish a device outcome. The held
transfer descriptor is now hashed once; other source validation is cheap
path/shape/size checking, without generic weight buffering or archiving.

## Central checks and preparation inputs

The retained central receipt build independently matches 362 JVM tests across
36 XML suites with zero failures/errors/skips, lint zero errors/19 warnings,
and completed zero/known cleanup in 117,500 ms. Its 9,242-byte output SHA-256 is
`f19073b945cbc7bc5808bf6849813848b4354e67f38cf00065bd870b2acc4b3c`.
The initial central host suite independently matches 645 passes in 67.166 s,
owned completed zero/known cleanup in 68,000 ms; output SHA-256 is
`c25c9732f888f8c8ade0f1b12c39ab83f1159f96176083d6d5f9c8c8b7b9410b`.
Those checks precede the ancestry fix/new independent test integration; final
host integration checks remain separate.

The final integrated host suite independently matches 659 passes in 64.821 s,
owned completed zero/known cleanup in 65,531 ms. Its 77,729-byte output SHA-256
is `8b717b0dc6ddd183f07b67c60c6ab42ae5fe63c141fcea9a363b5a15bef7cd15`.
The coordinator confirms original handle65546 consumed terminal zero. Final
execution source is `67576c0f4255d52abbbfde573832238311f3526b`:
all 1,443 snapshot files/17,098,302 bytes and 924 live non-Markdown rows/
11,927,269 bytes independently match source-index SHA-256
`fbd148fe5b8d6f04ded710554e459eccb675eff9922341b242bb4bfcf0220e8d`.
The compilation-equality record separates actual Android compile `03ee127`
from later host-controller/tests/pins/docs; no new Android build is inferred.

The coordinator explicitly attributes source-integrity-v1 to a new full held-FD
read of the local host source this packet (tool54d294), with expected size/hash
and stable identity. The reviewer checks that metadata as producer evidence and
never hashes or reads weight content. This does not authorize its new destination.

Copied artifacts independently hash to APP 74,884,112 bytes
`f261d301d0cf97f06170fe94b868ffb313063d8b363928826f12809e32436aa0`
and TEST 2,804,892 bytes
`568e30443b4045abe0c4689368ed4da8694e8102c1b6e97696cb66d2560fd16a`.
The APP equals the preceding artifact; four new Android tests are compiled,
not executed by that host build. Independent read-only DEX class-definition and
encoded-method inspection confirms all four selected classes and code-bearing
methods in TEST, none in APP. All five current audit/signature receipts and
retained output digests independently match completed zero/known cleanup. TEST
manifest remains the preceding audited 6,244 bytes. No fresh regular/ordinary
build or inference follows merely from artifact reuse.

The disabled PREPARE proposal SHA-256 is
`fd35092c5fdc20c57020476e2f2c474b24aa341be0c8e602fd8eee6ed9b34c0d`.
All 909 inputs (5,046,138,747 bytes), eight existing registry records and the
token record independently rehash: 918 rows/5,046,152,229 bytes, no mismatch.
Fresh target/authorization are absent at review. The exact typed 8,192 MiB/
12 GiB host-memory profile, 12 GiB userdata/8 GiB SD/two CPUs, proven JBR17,
fixed owned D paths and create-only argv match. There is no force/wipe/snapshot
or capped partition override. Review performs no SDK execution, and this
prepare-only input check grants no model-copy or candidate runtime authority.

Actual preparation is separately coordinator-attributed to original36445
consumed zero, SDK child completed zero/known cleanup in 3,812 ms and successful
closure. The linked disabled RUN SHA-256 is
`7e5b1c59fa4ff4a29f2522e262ebf7b1996fdaa2a9a7e1f08fc43147cda17659`.
Its common 909 inputs exactly equal reviewed preparation; independent initial
prepared/config/three immutable files/8 GiB SD and successful prepare-result
links pass, as do preserved registry/token checks. Fresh userdata, run output
and authorization are absent at review. Corrected local read-only inspection
completes zero; an earlier inspection used a nonexistent helper name and stopped
without an SDK/device call. The actual selected RAM/disk/CPU/owned-path argv
remain unchanged. Root separately observes installed inputs, ports and fresh
host resource floors. A running descriptor or input review is not boot or
staging evidence; only tiny preflight may be separately admitted next.

The subsequent disabled tiny-preflight proposal SHA-256 is
`95e565aecc1145be9c224c7408ebfd0bc3a6d0dbe175b6bb20acf0900aa6c38e`.
Its exact closed phase/source/grant shape, all 69 bound hashes (87,190,915 bytes)
and live owner lease independently pass. Source is the fixed 61-byte probe;
human consent and prior-preflight fields are null, with no weight file bound.
The separate authorization/cohort are absent at review, and device flags remain
false/pending. This is input review for preflight only. Candidate execution
still requires direct new-destination human consent and the full remaining
owner lifetime; expiration cannot be bypassed by extending or reusing a run.

## Actual tiny preflight

The coordinator attributes original preflight handle71104 consumed terminal
zero (chunk a24a91). Independent retained-result/output checking agrees:
child_exited, worker zero, known cleanup and complete capture in 47,891 ms,
416 stdout bytes SHA-256
`341bc27e60feff673224b66ad5492486870905dfec4c8237dff529c6d5548066`,
outer stderr zero. All 43 client metadata/raw counts and digests independently
match completed zero/known cleanup, with two fresh installs and one exact
SourcePreflight selection. Install stderr counts are 132/143 bytes; no
all-client-empty-stderr claim is made.

The 805-byte runner SHA-256
`e7201d46439e1976987512a788c6da6792e5a590e429e856253b383ed8c42069`
strictly reparses one pass/zero failures. The 1,057-byte app proof SHA-256
`b674b79a0925564e30f0b7938de6a9fdb01f7d1a61bc997792efbc0858081890`
strictly reparses all 12 checks and equals the saved observation. Its
61-byte probe matches through the actual file-backed stdin/run-as path, source
owner and exact whitelist. The transfer record correctly retains remote-exit
unknown/destination-unverified; the independent application proof supplies the
tiny destination check. Model source counts remain zero, SDK/native publication
flags false, and candidate control/data roots and staged model are absent at
that observation. Expected model identity in the proof is not a model read.

Actual app MemoryInfo reports total 8,332,292,096 bytes and available-before
6,280,585,216 bytes. Context userdata free is 11,266,945,024 bytes and external
free 8,573,050,880 bytes before/after the test. These exceed the declared copy/
import floors at that time, without calibrating SDK peak cache or memory use.
The saved after-preflight host userdata observation is 11,266,936,832 bytes.
Independent raw fact reparsing verifies empty inventory before, exact audited
pair/distinct UIDs installed and unchanged after, same volume, correct identity
profile, and target/helper zero at all three observations. This is not a later
post-stop guest-state attestation.

The coordinator observes only 917 seconds remaining on the owner, below the
candidate's required 920 before consent/transfer setup. No candidate grant,
model copy, import, Play or Reopen follows. Preserve that used target; do not
extend the owner deadline or relabel the tiny pass as real-model qualification.

## Anticipated Compose-helper boundary

Before any candidate run, the coordinator identifies a concrete control-state
mismatch from the actual topology: SourcePreflight has no Compose Activity and
observes no TEST helper, but IMPORT is the first Compose path. The initial
continuation immediately retired an absent helper, so a legitimate first TEST
helper after successful IMPORT would be refused. This is not a measured model
failure or an explanation of earlier setup failures.

Review agrees with a narrow real-scope correction: only if preflight and fresh
continued-before both have no helper may the exact IMPORT pass plus linked
proof open one binding point. Empty after-IMPORT closes that opportunity.
An existing prior helper keeps its exact observed identity or permanent
retirement; PLAY/REOPEN never create or rebind one. APP, service/provider,
wrong-UID, foreign or multiple rows remain forbidden. The ordinary setup
controller and resource budgets stay unchanged. Literal red/green and complete
mocked-flow evidence must accompany that correction; no new model operation is
needed to expose this state-machine issue. Archive the original 69 execution
inputs before changing live source, and bind corrected code only to a future
fresh admitted run.

The retained first red helper run has one assertion failure plus a misspelled
test-selector loader error; it is not evidence for two tested paths. Corrected
red-v2 runs the actual two methods with three failing subcase observations,
owned completed one/known cleanup in 1,188 ms, output SHA-256
`d242ee65e88455ddc4bb414bcdbabcfa014d6e272d5669a30b9ddfd3145bb566`.
The same two methods pass after correction, 1.359 seconds, known zero/cleanup
in 1,640 ms. Independent output/result checks retain both failures and green
separately. Current full host checks pass 660 tests in 58.026 s, zero failures/
errors/skips, owned zero/known cleanup in 58,797 ms; 77,842-byte output SHA-256
`bb0202d038ede0f54411a0bc62a9d3534b9d3f0c7ec5d28801db9a6f75b1cc58`.
The coordinator confirms original40442 consumed zero. The actual full host
command is `python -B -E -m unittest discover -s scripts/tests -v`; receipt
build command is `python -B -E D:/LocalLore-real-candidate-host-20261024/run_build.py receipt`.
The reviewer executes neither command.

Final source is `44b15eac3d812e72d8e424a8359be4dd71633a8c`. The independent
final-snapshot check covers 1,443 files/17,106,332 bytes and all 924 current
non-Markdown rows/11,929,386 bytes, index SHA-256
`0e38970c0c1d7569c52bb3fd4d4bc52730f7e115fb0de67072d62ba6cc567421`.
Compared with actual guest execution67576c0, only the real controller/two
controller test files and documentation change. Android/Rust/build inputs stay
equal to compilation03ee127. The prospective helper change has no Android
execution claim; the measured preflight remains attributed to its old source.

## Known closure and final inventory

The coordinator confirms original owner86848 consumed terminal zero, chunk
ab1152. Retained owner result records stop_requested in 349,016 ms, cleanup,
capture and preservation closure true, worker one from requested forced drain,
guest flush false. Independent actual output hashes match stdout13,847 bytes
`9958ec534034bc0c319ce2905e3027942352f9909a1314a93429c44c4d2f1980`
and stderr1,062 bytes
`37ad0e2d49371e1867c5dfd0b1890813033624dbf59ec3ca6c010c77925f4f11`.
The separate post-stop host record verifies the three recorded identities
absent and owned ports free. This supplies no guest flush, disk-content
integrity, old-cache content or post-stop guest-process snapshot guarantee.

Every file in all final inventories independently rehashes without mismatch:

| Inventory | Files | Bytes | Index SHA-256 |
|---|---:|---:|---|
| Host | 2,987 | 113,106,408 | `d0a6e5e73d13a70c27d06d483ede589c647ba2ce8a55164b36919c8334c86d35` |
| Environment | 25 | 394,664 | `f47427ef40c4688a8037dbd39bf5caf1dfc32e2a42549bc90ebc5a18044750bd` |
| Preflight | 172 | 87,290,684 | `3774795180e9a8a5d726b8e3b95c26f59d590771635d40e0cf4a33999329bfaa` |

All 69 original admitted inputs/87,190,915 bytes independently match their
archived bytes and proposal bindings, frozen-input index SHA-256
`d82d4d0628816334c2950224f641fa2fc8868302e2ecd0bc80954dcc47b34b29`.
Execution and later corrected source snapshots are distinct and retained.
Inventory sets may overlap; none includes weight bytes or final virtual-disk
content as immutable evidence. Private raw evidence stays outside Git.

## Next action and limits

The compiled artifacts and measured tiny preflight make a concrete final copy
request reviewable. Request the owner's explicit new-destination scope for one
fresh 8 GiB receipt-debug emulator, the fixed model and bounded SDK experiment.
After that consent, a future packet must independently admit fresh preparation,
run and tiny preflight with sufficient lease before copying. It must not use
this expired/used owner, relabel old A/B permission, or infer a model pass from
the 61-byte observation.

Then inspect actual weight/import/SDK/reopen results, original owned terminals
and final evidence without touching prior targets or caches. Preserve missing/
corrupt, capacity, volume, receipt and owner fences. The unchanged worker must
full-hash before SDK load and use bounded runtime admission. No manual accepted
marker, fake inference, second reducer, budget relaxation, merge/release or
supported backend/phone decision follows from this preparation. Real generation,
canonical gift/reopen, old integrity/consumption holds, physical phone, ARM64/
16 KiB, cache/privacy, power loss, quality and sustained-runtime gates remain.
