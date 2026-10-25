# Authorized receipt experiment — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting), PR #152.

The owner explicitly authorized copying the verified local model into a fresh
receipt-test emulator and running import, actual inference and restart checks.
This supersedes the previous pending-consent gate for this destination. It does
not authorize a merge, release, external upload or supported-phone decision.
Execution claim: [6391515831](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6391515831).

## First authorized attempt: staging passes, candidate never enters

Source `b442704257bb54381090ea440e9a5ba0b9b757df`, unchanged Android/Rust/build
inputs from actual compilation `03ee127`. Reused audited receipt APP SHA-256
`f261d301d0cf97f06170fe94b868ffb313063d8b363928826f12809e32436aa0`
and TEST `568e30443b4045abe0c4689368ed4da8694e8102c1b6e97696cb66d2560fd16a`.
No new Android build or JVM run is claimed. Prior 362 JVM and 660 host results
remain attributed to their original sources in the preparation report.

Create-only private namespaces `D:/LocalLore-real-execution-{host,environment,
avd,preflight,candidate}-20261024` preserve this attempt. Neither these raw
records nor weights are public Git artifacts. Independent review checked the
disabled proposals before execution. Source snapshot has 1,444 tracked files;
all non-Markdown runtime/build inputs equal the previously verified source.

| Actual operation | Result |
|---|---|
| PREPARE proposal `6cf74a7b85c46b09595f2d67b6e6e64d2b8710e174ad789334e1fb54eac21ef4` | 909 pinned installation/tool bindings, exact 8 GiB/12 GiB host profile; root and independent checks pass |
| `receipt_avd_environment.py prepare` | Original session98369 terminal0; SDK child0, known cleanup3,781ms; prepare/result/preservation closure verified |
| RUN proposal `e87fa8bebcae847e198391011bfbbed2b475dd10088b28eed3b3b8240049f0ed` | Fresh disks, full prelaunch root/independent checks; original owner76624 launched |
| Preflight proposal `5a1a94ea3ba88eab90b9980f45895874a1058ac9d98f5cbcdefcfdb5685f0958` | 70 nonweight bindings/87,243,321B, separately archived; local-copy/SDK flags false |
| `receipt_real_candidate.py run` (preflight) | Original58663 terminal0; owned worker0, cleanup/capture true107,484ms; stdout416B, stderr0 |
| Guest source preflight | One method PASS/12 checks; all43 clients0/known cleanup, two installs and one61-byte probe transfer |
| Candidate proposal `9d9c7881d9833e9bccff065c79daa23c94e34c86bf2bac4fb235b0db51109cf0` | 75 nonweight bindings/87,253,061B and explicit consent/proof links validate; no candidate grant created |
| Candidate entry | Root observed903.599s remaining versus required920s; independent lifetime check also refuses. No copy, import, SDK call or reopen |
| Exact owner stop | Original76624 terminal0; requested stop, cleanup/capture/preservation closure true296,563ms, worker1 from forced drain; guest flush false |

Guest is Android15/API35 Google APIs x86_64, emulator35.3.12/build12990079.
Source preflight raw proof SHA-256
`9a5a4b6916188228499d8fbc6d7ccd748dd95c3569add6b6cb5b847b1c141f68`.
Actual total memory8,332,296,192B; available before6,136,332,288B and
after6,135,353,344B. Userdata free before/after11,477,131,264B; external free
before/after8,573,050,880B. All model-source counters are zero and SDKfalse.
Expected model identity in a preflight proof does not establish model presence.
Post-stop actual process enumeration finds all three recorded identities absent;
owned ports are free. This is no guest-flush, disk-integrity or native SDK claim.

## Discovered scheduling prerequisite

The fixed1,200s emulator envelope cannot reliably cover the measured296.4s
boot/revalidation/preflight/admission work plus the unchanged900s candidate
and20s entry margin. The candidate was never admitted. The inference itself
was not slow or failing: no inference ran. The metadata-only second candidate
builder avoids an unnecessary duplicate full installation rehash while the
production dispatch guard remains unchanged; its new path/bytes are bound in
the candidate proposal and its original helper is preserved.

[Plan adjustment6391618186](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6391618186)
calls for a separately tested, closed longer owner envelope for the explicit
8 GiB profile, preserving the old2 GiB profile, all model/per-phase limits,
candidate900/870s and920s entry, capacity and ownership/closure fences.
That correction requires a new source admission and another fresh target.
The stopped owner and its proof cannot authorize a new target.

The implemented correction keeps `MAX_SECONDS=1200`, adds a closed1,800s
real-profile ceiling and absolute supervisor ceiling, and makes `plan_run`
derive its default from the already admitted RAM profile. Explicit shorter
windows remain valid; booleans, baseline windows above1,200s and real windows
above1,800s refuse. No arbitrary RAM or CLI lifetime selector is added.
Independent three-file author commit `76cc5fba48c25f1e732901ab458902b75d25b428`
integrates as `82cd94b`. Its actual targeted9 tests pass, known cleanup2,203ms.
Root updates the absolute supervisor over-limit regression to1,801s; a separate
profile regression still rejects2 GiB/1,800s. Independent source review finds
no concrete blocker. Actual full command
`python -B -E -m unittest discover -s scripts/tests -v` passes668 tests in
87.324s, zero failures/errors/skips; original34090 terminal0, owned completion0
and known cleanup90,125ms. Captured stdout78,824B SHA-256
`58a61c75ec1cbed6e0594c1a56275d972ca230e2162f0584a635ed88ab21c50e`.
All candidate/per-phase/SDK limits remain unchanged.

## Remaining gates

Real model import, SDK gift and restart remain unrun in this first attempt.
The exact existing Gemma4-E2B/LiteRT-LM0.18.1 pins and publisher/container
verification remain unchanged; no new dependency or runtime choice is made.
Full M05.05/M01.05, physical phone, ARM64/16KiB execution, DocumentsUI,
cache/privacy, power loss, sustained inference and narrative quality remain
pending. Consent for the fresh receipt destination is now granted; do not ask
for it again merely because the scheduling prerequisite needs correction.
