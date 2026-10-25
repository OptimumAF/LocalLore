# Real receipt cancellation and recovery: independent review

Status: **in_review**, M05.05 prerequisite / M01.05 support. Root claim
`6396416584`; independent claim `6396430614`. This review does not complete either
milestone or authorize execution or merge.

The reviewer owned only this report, on `review/m05-real-cancellation` from
`b23f100b8c91b1c09a69b362043ffa727f98d100`. Reviewed execution source was
`1ce40ae394892e1849aabe21d9a8cbd85a475e5b`. The coordinator performed all builds,
environment and device operations. The reviewer read source and retained
evidence, without SDK/ADB/AVD execution, model-byte reads, or disk-image reads.

## Findings and corrections

1. **Cancel acknowledgement preceded owned cleanup.** `cancelSaved()` immediately
   refreshes saved state after native acknowledgement, but `open`/`branches`
   remain Busy while the SDK run is active. A retained JVM test held engine close
   and reproduced early acknowledgement: one executed test, one expected failure.
   The preceding attempt ran zero tests because the ordinary profile correctly
   refused the exclusive LiteRT cache; it is not reproduction evidence.
   `90c9c19a059900568432f9d602d2ff7c96b9a08a` waits for the captured run's known
   cleanup after acknowledgement, within the existing shared cleanup deadline.
   It clears active ownership before completing that signal and rechecks
   admission before returning. Failed, unreturned and late cleanup retain the
   refusal. The retained green owner suite passed 25 tests, including UI-style
   caller cancellation, blocked refresh and no-active-run cases.
2. **Sample/final traces needed same-history checks.** Kotlin and host validation
   now require nondecreasing snapshot time, event counts and previously observed
   event times, plus the identical already-returned DIRECTOR creation. Negative
   tests reject earlier or mismatched histories. These are trace consistency
   checks, not jointly atomic native-state observations.
3. **The positive trace could become stale during model verification.** The final
   fixture repeats the production owner guard after the full model recheck, then
   resnapshots and validates the trace after native-handle close. Recovery also
   refreshes its final trace after close. Commit
   `4f43ac5e7b03f562e68f30eea23f6a10f5094c82` was compiled into the final test APK.
   This rejects observed late fencing through the final observation; it does not
   promise immunity to unseen later callbacks or hidden JNI epilogues.

No remaining concrete blocker was found in the reviewed source or this bounded
qualification. The original four-phase harness remains separate. The new
candidate-only controller preserves the actual old preflight lineage, fixed
selectors, fixed stream-worker module, exclusive evidence creation, raw-first
retention, sticky process refusal and no later dispatch after failure. The shared
stream body remains behind each fixed authorizer and barrier; proposals cannot
select an executable path. No global controller monkeypatch was introduced.

The response task uses an independent Main scope and is joined without the test
cancelling it. Gateway calls enter on Main and delegate directly to the production
transport; no test IO wrapper masks its own off-Main guard. Cancellation sampling
requires a returned first message before an observed terminal, and the final
trace must record actual public SDK cancel entry/return and known drain/close.
A missed window fails. The test does not call recovery early or manufacture a
successful cancellation by cancelling its response Deferred.

## Verification replay

The final receipt build passed **412 JVM tests / 39 suites**, zero failures,
errors or skips; lint had zero errors and 19 warnings. The regular profile passed
**377 / 36**, zero failures/errors/skips; lint had zero errors and nine warnings.
The final host suite passed **742 tests** in 59.377 seconds, with known cleanup.
The independent codec and controller cases are included in those central runs.

The reviewer rehashed all **1,537 source rows / 18,825,755 bytes**, both current
source and frozen snapshot, and all **209** refined Android source rows with no
mismatch. Receipt compilation was at `4f43ac5e`; execution differs only in the
recorded APK pin metadata. The sole subsequent regular-profile Android difference
is excluded receipt instrumentation. Final receipt artifacts independently match:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| App | 75,003,952 | `038c192f12a43fc055b232d5cd33b192bb955a366b24a2d9fadbeef226de8699` |
| Test | 2,003,207 | `04ddfe88176b9a09110881d48ae490ace27ff1fd819fb4ab28de5889c76f8431` |

App audits and both receipt signature checks passed with known cleanup. The
incorrect initial collector selected an ordinary-profile output directory; its
preserved results were explicitly unqualified and unused for grants or installs.
The prior valid receipt artifact and the refined final artifact remain distinct.

Independent environment review content-hashed **905** source/tool bindings and
checked **four public SDK images by metadata only**. Initial SD was metadata-only
for this reviewer. The coordinator retained its full stock/initial-disk checks.
Registry/token preservation checks passed without token disclosure. The fresh
8 GiB, four-core profile retained C/D 40 GiB reserves, 12 GiB host RAM minimum,
12 GiB userdata and 8 GiB SD. Owner lifetime remained 1,800 seconds; candidate
870/900-second aggregate/outer limits and 920-second entry guard were unchanged.
SDK turn/cleanup limits remain 60/5 seconds. Phase caps and the conservative
120-second runner gate were not extended. The nominal 790-second phase sum does
not guarantee completion after all overhead; exhausted budget stops later work.

Preflight proposal `1019525bb2561d4dac08e6e1b51ad0c694a0077cb1c97dc07bdb10514a39e7b5`
bound 86 matching nonweight current/archive inputs. Candidate proposal
`76fe929ed4adc56f732c9f6b06f34dcf72a3286ff0675e1fba0c6de3e7ded90f`
bound 90 matching inputs and the standing direct human copy/inference consent.
The model was excluded from generic binding/archive reads; reviewer inspection
was metadata only. The existing fixed model identity was unchanged.
The experiment retains pinned LiteRT-LM 0.18.1 and Gemma4-E2B, SHA-256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`,
on the fresh API 35 x86_64 emulator. Dependencies and `LiteRtRoleWorker` were unchanged.

## Actual fresh-target result

Strict replay verified **44 preflight clients** and **77 candidate clients**,
their stdout lengths/hashes and known completion, five exact selected JUnit
passes, proof hashes, process links, worker sidecars and all **82 protocol checks**.

| Phase | Checks | Whole-method observation, ms | Result |
| --- | ---: | ---: | --- |
| Source preflight | 12 | 183 | Tiny source only; SDK false |
| Import | 16 | 93,955 | Verify/import each opened and closed once; full 2,588,147,712 bytes |
| Cancel | 21 | 69,695 | Original response joined as Cancelled; revision 0, no receipt, potion preserved |
| Recover | 19 | 62,381 | Fresh process, real DIRECTOR/NARRATOR turn, one guarded gift committed |
| Reopen | 14 | 32,128 | Another process, same revision 1 and receipt; no source open or SDK call |

The cancellation sample and final trace share one DIRECTOR creation. The final
trace records cancel entry/return once, paired ERROR terminal, known drain,
conversation close and engine close once, and no UNCERTAIN observation. The
post-join and post-model owner guards passed. Recovery records two returned roles,
no cancel/error/uncertainty, zero repairs and no fallback. Reopen preserves receipt
SHA `e685bb45b3588507d29bdf485f2a6e50831ba6c10cd00f1206534d2b8493712b`.
Sampled facts preserve the exact package hashes/UIDs, show APP absent and the same
permitted TEST helper. They do not establish continuous process liveness.

The coordinator consumed original candidate `21508` at terminal 0, chunk
`7ec7c4`; owned completion was 0 with cleanup/capture true, 405,750 ms. After its
terminal, the exact stop was requested. Original owner `75666` was consumed at
terminal 0, chunk `f78af0`; retained closure is stop_requested, 911,969 ms,
cleanup/capture/closure true. Worker 1 reflects requested job drain. Post-stop
host queries record all three original process identities absent and ports free.
No guest flush is claimed.

## Sealed evidence and limits

The reviewer rehashed every entry of `sealed-inventory-v3.json` under
`C:/Users/Avery/LocalLore-receipt-cancellation-{host,environment,preflight,candidate}-20261025`:
**3,787 files / 471,309,219 bytes**, zero mismatches. Model weights and AVD disks
are excluded. Inventory SHA-256 values are:

| Inventory | SHA-256 |
| --- | --- |
| Host | `6a135f4b75dc34a10b17acd4d73f3fc82ff12268606a00711a01b38573c94972` |
| Environment | `3f4da0e4ebe3ead2ee508cdb8f9295a7baac6225bb822b3f8269a382b7050eb6` |
| Preflight | `d3715365ebc700ce053498f05073f560a8306f0c5bb875dbb6df8fc7bca95567` |
| Candidate | `49408a0343db32f075be623a2738222cffb00e23eb7176bc91584dc970f06f79` |

This qualifies one selected **production gateway cancellation API path on Main**,
known public cleanup, canonical preservation and fresh-process recovery/reopen on
the admitted emulator. It does not click Compose Cancel or establish exact
native-active cancellation timing, hidden native reclamation, generation latency,
a causal four-core speedup, physical-phone/ARM64/16 KiB behavior, DocumentsUI,
power-loss durability, sustained quality, thermal or cache-growth qualification.
Historical failures are not diagnosed or erased by this pass. Full M05/M01 gates
remain unchecked pending their remaining acceptance work and owner disposition.
