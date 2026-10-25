# Finite-regex fresh-device execution review, 2026-10-25

Refs #9 (M05.05), #5 (M01.05 supporting); independent evidence-review claim [6402033074](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6402033074). **Tiny source preflight passed; the subsequent ordinary controller stopped before validating import. No real SDK scene success is established by this attempt.** This reviewer performed only source/retained-evidence reads, not device, SDK, model, cache or image operations. The coordinator owns execution and future grants.

## Source and authority bindings

The final-source manifest is 13,982 bytes, SHA-256 `7ea5fbb220fb1cb874e8e803b7aeea92fc39cb86dda1e2516c0087e024a6e409`. I independently matched all93 source byte hashes and six Android compile-source cross-bindings. Its build/source attribution is `3efe84dfeb22aa7a314a7a3ce91a35a2106df0a3`; the execution proposals separately name `6cb810e410fc650efd47211fd4ced244d424d6c0`. These are not interchangeable claims about all current-main code.

Both proposals pin receipt app SHA-256 `83797af66672e5bab89e17d53339478eb7c57bee66773c9c72edd13466911a8a` and test `e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d`. Installed facts match those pins with distinct, stable app/test UIDs. Preflight grants device calls with copy/SDK false; the later ordinary grant separately permits copy/SDK and hashes its exact proposal. All four prior preflight records match their retained hashes and ordinary binding entries. Both cohorts bind the same fresh live-owner descriptor. No old target or earlier failure evidence was adopted.

## Actual observations

| Cohort | Owned duration / child | Commands | Instrumentation observation | Qualified result |
| --- | --- | ---: | --- | --- |
| Real-source preflight |82,157 ms /0|44|One paired method, terminal0, runner completion;12 proof checks true|Passed tiny preflight |
| Ordinary candidate |310,047 ms /2|15|IMPORT method reports terminal0/OK1 at134.086s|Stopped at host runner parser; import proof absent |

Both outer records report known Job cleanup, complete output capture and zero stderr bytes. All59 command raw stdout sizes/hashes match their records; every retained command completed with client0 and known cleanup. Client0 alone was not treated as a test, transfer, import or scene pass.

Preflight raw runner output is805 bytes, SHA-256 `58f58dcd036882faa39e5ff276b5609d6328e78075892b810cd67d19824169a6`. Its raw proof is1,057 bytes, SHA-256 `e782fa911a682a302a554d01595ddd4252ff745ac2351303425077d3de281764`. I inspected the exact class/method/start/terminal/final-runner order, actual four-CPU observation, empty→exact-two-package map, stable UID/mount linkage and target absence. The proof records all12 checks true, SDK false and zero full-model source-read/import counters. Only the fixed61-byte probe was transferred. Its stream record explicitly preserves unknown remote exit status and unverified destination; the later app proof establishes the probe/owner result independently.

Ordinary command14 retains a159-byte stream result, SHA-256 `d97889efded606850a244e1c90d23274a568a321bb1a1a8961afe024c5fbbabd`: held source verified2,588,147,712 bytes, client0, **remote exit unknown/destination unverified**. Command15 is the802-byte IMPORT runner output, SHA-256 `f740c18399a14de4a78a1a331eb8c32bd028a4db9eac9da5908f501b03d0eab6`, with one paired exact method, terminal0, `Time: 134.086`, OK1 and final runner code. The controller result is nevertheless stopped at `instrument-IMPORT`, with `result=null`; no import proof or subsequent START/DIALOGUE/REOPEN command was captured. Do not count its body-reported pass as a validated import, accepted gift, restart, SDK compatibility or owner-count result.

## Concrete failure and scope of correction

Source inspection confirms the diagnosis: shared `receipt_setup_qualification._parse_selected_instrumentation` requires runner Time≤120s. `receipt_real_candidate.parse_runner` called it without a phase limit even though existing IMPORT proof/test budget is150,000ms. The observed134.086s is greater than120 but below150. This is a demonstrated host observation-contract mismatch, not evidence of an Android import assertion failure or finite-regex/SDK failure.

The ordinary parser also directly inherited that120s default despite existing START/DIALOGUE170,000ms caps. I flagged that additional path for the assigned correction. The fix must use each fixed phase's existing bound, preserving generic/synthetic120s and method/frame checks; a blanket180s client timeout is not the phase oracle. Another agent owns the correction/tests. This report does not claim those changes executed or qualify a later attempt. No post-failure proof salvage or continuation on this target was used.

## Storage and lifecycle qualifications

The independently read **metadata-only** boot observation shows why full backing accounting mattered: an8 GiB allocated raw SD plus its QCOW2 overlay; a small raw userdata base plus growing overlay; and an approximately8 GiB fully allocated RAM backing despite the no-snapshot flags. The RAM file is not proof of saved guest state or an ignored flag. Cache/encryption backings and metadata are additional. A36 GiB primary-growth calculation leaves approximately1.85 GB of the original D: headroom for other files; that is planning arithmetic, not a hard QCOW2-allocation ceiling or continuous reservation. Model bytes inside userdata/SD overlays must not be added again to full-volume budgets.

Preflight's additive host post-check reports C:52,302,643,200/D:64,880,312,320 bytes free and a healthy stricter40/40 guard. Those observations do not retroactively establish successful ordinary postconditions. After the failed candidate, the exact owned stop completed at600,328ms: `stop_requested`, known cleanup, complete output capture and `closure_verified=true`; worker return1 is retained, and no graceful guest flush is claimed. Owner-result SHA-256 is `c952e9d0b903f4ddd25a25bf8e936835950b6e0e565a10c5a0655c1e0634c979`. The final linked guard is healthy with `monitor_failed=false`. No raw disk, RAM, private-key or model contents were read or archived by this review; the boot file included only metadata for those objects.

I independently rehashed all177 files /581,977 bytes selected by the first-attempt device index, with zero size/hash mismatches. The44,222-byte index SHA-256 is `488a433dde912c0254878d6471d930dce81d4213f815d2d3520f0897e29531b9`. This verifies that bounded selected metadata/raw evidence, not every possible live output or the host's separate packaging index. The failing attempt remains distinct from any future corrected-source/fresh-target attempt.

The useful next step is the narrowly tested phase-bound parser correction and a separately admitted fresh attempt, retaining this failed attempt. Existing finite-codec host/native proof does not establish successful on-device director/narrator generation. Full milestones, narrative quality, phone/ARM execution and sustained/runtime performance remain unqualified.
