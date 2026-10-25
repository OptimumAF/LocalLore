# Independent real receipt execution review — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting), #152 and follow-up
[#153](https://github.com/OptimumAF/LocalLore/pull/153).

## Disposition

**Real production import is verified; the SDK ownership gate remains unresolved.** On
the fourth fresh target, preflight passed all 12 checks and IMPORT passed all 16 checks.
Independent source verification and production import each opened/closed once and
accounted for the exact 2,588,147,712-byte model. The accepted-model full recheck and
receipt/owner checks passed.

The subsequent PLAY test failed with `LocalInferenceUncertain` at
`LocalInferenceOwner.kt:228`. There is no Prepared/PLAY proof, qualified canonical
commit or REOPEN execution. That protective fence does not identify the lower-level SDK
stage, generation result, terminal/drain/close condition or cause. Known client/host-job
cleanup does not establish SDK resource completion. Full M05.05/M01.05 remain unchecked.

## Authority and independence

Review subclaim6391521878 is under root6391515831. Separate branch
`review/m05-real-receipt-execution` starts at
`b442704257bb54381090ea440e9a5ba0b9b757df`; only this new report and a private review
namespace are owned. Root alone executes. Reviewer reads source, nonweight inputs and
retained evidence; no SDK/ADB/AVD/build execution, model-byte read/copy or cache access
occurs in review.

The direct human instruction explicitly permits local model copy to the fresh
receipt-test emulator, import, real inference, restart verification and ticket/PR
updates, and forbids merging. Another copy-permission question is unnecessary. Old
A/#117/#119 models, caches and holds remain separate. PR152 was merged outside this run;
no merge is performed by these agents or inferred as a model qualification.

The artifact remains SHA-256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`; LiteRT-LM
remains0.18.1, with the existing worker, CPU four
threads/context4096/director350/narrator220/repair1. Production turn60 seconds/cleanup5
seconds remain unchanged. No dependency/runtime choice, native/Rust behavior, legacy
adoption, fallback storage, owner release seam or resource-floor reduction is
introduced.

## Four bounded attempts

All model transfers are separately admitted after successful same-owner tiny preflight
and explicit consent linkage. The 61-byte preflight is never treated as model/SDK
qualification. Raw exec-in zero remains destination-unverified until app-domain
verification.

| Attempt | Observed result | Ownership/limits |
| --- | --- | --- |
| Initial execution | Preflight43 clients/1PASS/12 checks, worker0/107,484 ms. Candidate admission refused at903.599 seconds remaining; no candidate dispatch authorization, copy or SDK attempt. | Original1200-second owner76624 stops with known cleanup/capture/closure296,563 ms. |
| Fresh window,64 KiB IO | Preflight43/1PASS. Candidate14 clients/one IMPORT failure, worker2/265,906 ms. READY wait120000 ms; no import proof or failure-time phase. | Fresh1800-second owner77768 stops with known closure491,500 ms. |
| Fresh1 MiB IO | Preflight43/1PASS. Candidate14 clients/one IMPORT failure, worker2/260,968 ms. Bounded1337 snapshot observes READY expected/IMPORTING actual, source opened1/closed1/active0/reads2470; bytes capped1,000,000 with saturation. | Empty events/errorNONE: no cause invented. Owner63329 stops with known closure531,532 ms. |
| Fresh4 MiB IO | Preflight43/1PASS; candidate28 clients, IMPORT1PASS then PLAY1FAIL, worker2/300,344 ms. No candidate installs; only preflight installs the fresh pair. | Owner76889 stops with known closure588,969 ms. REOPEN remains unrun. |

All retained clients in these observed cohorts have matching raw sizes/digests,
completed-zero transport status and known client cleanup. A zero instrumentation-client
exit can carry a failed test. Coordinator-attributed original candidate tool exits are1
for15627,64927 and39202; each owned worker exits2. All four original owners are
coordinator-attributed consumed terminal zero. These attributions are distinct from
subsequent local metadata reads.

The scheduling correction changes only explicit8 GiB owner default/ceiling1200→1800
seconds; default2 GiB stays1200. It applies to fresh targets, never extends the stopped
owner. Candidate entry920/outer900/aggregate870, IMPORT150/READY120/client180 and all
other phase/SDK limits remain unchanged. Larger windows do not explain away failed
gates.

The first two model-import attempts (64 KiB/1 MiB) reached the same original READY
timeout; the1 MiB source snapshot narrows that attempt's observations but does not
retrospectively diagnose either timeout. Counter/phase sampling is independent, not a
jointly atomic resource state or exact persisted-byte report. None of the old failed
roots is reused, adopted, cleared or inspected for model contents.

## Tested IO correction and artifact boundaries

Actual source inspection identifies full guarded IO call amplification, not a proven
device timeout cause. The production changes are exact buffer constants64 KiB→1 MiB→4
MiB. Every guard before each actual read/write/hash chunk, cancellation/EOF/oversize
check, full hash, lock, force, owner, stamp and capacity check remains in the same
position. Partial channel writes retain their individual guard checks. The fixed4 MiB
allocation is bounded; source/candidate integrity and acceptance ordering are unchanged.

The new synthetic8 MiB tests retain exact bytes/hash/reopen, short provider returns,
oversize-by-one/wrong-hash preservation, and cancellation/volume revocation inside
read2. The second consumed chunk must not be written or accepted; close1/no read3 and
pending first-chunk preservation are checked. Only the explicit buffer/read-count
oracles change for4 MiB, including the truthful requested-length bound before the
provider's127 KiB cap. Guard ceilings200/100 and all other protection assertions stay
fixed.

| Durable host evidence | Actual result |
| --- | --- |
|64 KiB red baseline |28 tests/one intended metrics failure/27 pass,0 errors/skips; source reads129/import guards643/installed guards193/max request65,536. Owned1/known44,140 ms; raw4,699B SHA `ae8e1b1cdf00fe723ac7e95a3fbe8f9dede513b755d9a143b7ffc8ca2208ffad`. |
|1 MiB green |367 JVM/36 suites,0 failures/errors/skips; receipt28/28 pass; lint0 errors/19 warnings. Owned0/known151,094 ms; raw9,903B SHA `afc387ffd9bf5a597505c45a66952a1ebf6ac6aa57e6463e0587a81a5d2b8ee4`. |
|1 MiB tests-first red for4 MiB |28/one intended failure/27 pass,0 errors/skips; source reads9/import guards163/installed guards73/max request1,048,576. Owned1/known73,203 ms; raw4,776B SHA `b536daaa754590da72901ce0362bd3bb7701b461de1b579db51dfd27ff0a83ad`. |
|4 MiB green |367 JVM/36 suites,0 F/E/S; all28 receipt tests pass, including three copy-source reads/max4 MiB and unchanged200/100 ceilings. Owned0/known154,672 ms; raw9,815B SHA `6fcde56d34563b656a6ef24a9330394af737010951f97279d30de895df7837de`. |

These are deterministic host observations, not Android throughput or causal
measurements. The actual4 MiB import passes under the unchanged budget; that does not
establish the unique cause of earlier failures.

Current regular build independently has345 JVM/35 suites,0 F/E/S, lint0/9, known132,828
ms. Current full host run has668PASS/70.291 seconds,0 F/E/S, known72,344 ms; raw78,824B
SHA `c8907b79bbefc0294e9d58cae9bc7f478675ef59b37efabd61749138b1a794b9`. Receipt/regular
runtime graphs have62 rows and analyzer67/version32.4.1/did-work true. Three APP audits
(including reused unchanged ordinary) and both receipt signature/raw digests pass; TEST
manifest remains byte-identical6,244B/SHA
`ded72dbadcabfb44c776d00b37f24a642bcc2541a2416334580b75f25abb4d83`.

Final execution freeze `f942f790c2fbaad35ef5496c64cc4424c864ce8a` matches all1,445
live/copied source rows/17,169,839B, including924 non-Markdown rows. Android/Rust/build
source matches actual compilation `f90a55e968031befc1e31ff8cdce3c253148e1c6`. Current
APP74,884,112B SHA `17f41d2bb3560a600ca80ce03346020431d639ed1f8bd2b2a895a6e095b59283`;
TEST1,963,339B SHA `28918767790e357f5adb5e1f0f148d81037d1c18bf6df21d50dde45a4f7d4b7d`.
Actual TEST DEX definitions contain all four exact selectors with concrete methods; APP
does not. Against the1 MiB pair, uncompressed TEST entries are identical and only one
APP DEX differs. Container byte reproducibility is not claimed.

## Independent final admission and outcome replay

Every fresh PREPARE/RUN receives full independent909-file tool/source rehash before
launch, successful preparation/closure/initial8 GiB SD/three immutable-file checks,
unused target/userdata/output checks, preserved registry/token metadata, free ports and
resource-floor checks. After launch, review explicitly reuses that full verification and
applies the unchanged cheap production descriptor/prepared/process guard; it does not
claim another full constructor rehash. Weight contents are excluded from generic
bindings/archives and never read by reviewer.

Final exact PREPARE is
`e50ef36b8c7c3289535b548804696db6ba9b342d2fe0878febb62d332637d011`; RUN is
`042816c339034a90a3ff0b87cc09ed976b8145bae5b4b3b40307e5edcf0ddb71`. Final descriptor is
`49371ef266ade37e70caaa3b32a6a7173c455aa2e43160a95c4c7f95d5dbaf07`. Preflight
`ee079065cd0170fc027bf46c08cc081cc9db032355f5f04fec3d404f13d83273` passes79 nonweight
bindings/86,476,050B; candidate
`3e8710f6c9adae14b9266b8b5e8253721a1a9c8c7fddd0dd5feb2bdf068756ba` passes83/86,482,291B,
explicit consent, model metadata and same-owner successful preflight links. Independent
candidate review sees1615 seconds remaining, above920. Root alone creates the separate
six-key copy/SDK grant.

Final IMPORT runner800B SHA
`d26bd7d44b44b59d1eca628cf98186e3653918808ca80358b4afe45138c0750d` parses one pass.
Proof1,350B SHA `df5a67a62372865be631819a4c524c223dadb3d59d1306a526ab3c7238c1ee93` links
exact preflight process/start/hash+UID, all16 checks and89,805 ms. Verification/import
streams each1/1/2,588,147,712B; SDK false. First27 client/raw records and
before/after-import package hashes, distinct UID map, volume/storage and helper boundary
replay correctly: APP absent at those observations; TEST helper absent→one bound row. No
continuous-liveness or unobserved PID-reuse guarantee follows. External free
bytes8,573,050,880→5,984,890,880 satisfy the retained floors.

Final PLAY raw6,023B SHA
`16420829f64550f63e901c09e9525990592b6289c3dde8a8423f0948997421a3` records one
failure/Time80.445, `LocalInferenceUncertain` at line228. Strict success parsing refuses
it. Outer453B SHA `1bc75a1030c588c5912288b238daf56a950ff504f8c802ea0792c6da5950e762`,
stderr zero, matches worker2/known cleanup/capture300,344 ms. There is no PLAY proof,
post-PLAY facts or REOPEN. No generation, SDK-entry/terminal/drain/returned-close or
final guest-process boundary is qualified beyond the observed stack/control flow. No
model/cache reads or additional guest calls follow the uncertainty fence. The import
proof establishes state before the SDK attempt; it is not a post-uncertainty model/cache
integrity claim.

## Closure and preserved evidence

All four owned stops have cleanup/capture/preservation-closure true, requested-drain
worker1 and guest-flush false. Retained post-stop checks record the three original host
identities absent and ports free. The final original owner76889 is consumed terminal
zero; its588,969 ms result is distinct from the failed candidate's worker2. Host
process/job termination is not a graceful guest flush, virtual-disk integrity, SDK close
or native-heap-reclamation proof.

All16 sealed inventories independently rehash:7,369 recorded rows/1,080,631,919 bytes,
zero mismatches. Repeated archive rows are not unique data. No model weights or
virtual-disk contents are included/read. The exact index hashes below bind the retained
source, raw/proof, terminal and closure records.

| Namespace | Files / bytes | Index SHA-256 |
| --- | --- | --- |
| real-execution-host | 1456 / 17,499,649 | `1f0e700d10b6ff847a7021e74fb9eda186d9c8fb6089f80b604673d005b3b7b1` |
| real-execution-environment | 23 / 381,784 | `e0af567ff134082ee13da2ba2f9ebc85c1addf8214b09ea8f5a572c4d3907e97` |
| real-execution-preflight | 173 / 87,344,373 | `a2dc5f860896ca5b5c7d37a71fdb868a26dcbadb6d458a5f6708ec495f69ffe6` |
| real-execution-candidate | 78 / 87,287,619 | `6bf0789d1960389faac3005a82e97dff05d72fa1aa6afb01bbdea9d2b874cf0e` |
| real-window-host | 1450 / 17,423,208 | `f9e96df40e708b9ef420ab378a68c8ec3c3316b1a15400c9a0474fbc2b9ff773` |
| real-window-environment | 22 / 376,923 | `c78ca9149daf026d667de7b0472015644609eb1ca674c4192561f4b36240d93e` |
| real-window-preflight | 178 / 87,438,998 | `dd7f6f7136928f62ce2be749f557bc35f132a5d3dfb4298e8c9cced560c174dc` |
| real-window-candidate | 119 / 87,405,937 | `a0b3e2d2244337cdb248932c8ac7687f0aeb2b31beece6e490ee1178485bff05` |
| real-io-host | 1591 / 173,589,472 | `654f1799b7284434316e1878c8b790bf644c97a89ea25f0410d2a0ff1a9eaec2` |
| real-io-environment | 22 / 381,266 | `3b0f581ae3ec50ed1893673b9f2bcd7914be72538b2c041d764fa7618ca6d14e` |
| real-io-preflight | 182 / 87,815,821 | `3ac8a4005d7155386f70e757f85c16ca992b2c784b96057c0719c61d9cd5a755` |
| real-io-candidate | 124 / 87,784,951 | `3eb3244a5e2da044cd32fbed90e9e39800994151b9ad2d6de867ee109724638c` |
| real-bulk-host | 1592 / 172,371,061 | `2c5803ed52614861d630979383039573ac161154cd664ec5b5b55f9817f64620` |
| real-bulk-environment | 22 / 381,516 | `185a4a94363fde7aec023fb0fca6a22e9deaec3a6801a94c28bc6512db5ebff5` |
| real-bulk-preflight | 182 / 86,577,926 | `3ed3e7e45b2c57fadbe24abb3ca239672369183d57cdea2a2578306958c23a38` |
| real-bulk-candidate | 155 / 86,571,415 | `5f724c2e8eceb7e101a2d242ba118b4af11eae069d5ee8f0ccb972e089762fab` |

## Remaining gate and next task

The next bounded prerequisite is closed worker-stage/ownership observation that
preserves the existing default SDK path and uncertainty fence. Determine the actual
lower-level stage/terminal/close disposition before a fresh PLAY/reopen attempt. Do not
force commit, bypass close/ownership, reuse an uncertain owner, or treat API source
inspection as an observed SDK cause.

Real receipt import is an achieved slice, not completed real inference/restart or full
M05.05/M01.05. Old A/#117/#119 holds, reference phone/ARM64/16 KiB execution,
DocumentsUI coverage, power loss, cache/privacy, sustained inference and narrative
quality remain separate. Earlier synthetic timeout causes remain unknown. Ticket/PR
status must retain these limits; no milestone checkbox or merge follows this review.
