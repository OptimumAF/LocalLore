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

## Second attempt: staging verified, import times out

Fresh `real-window` namespaces use frozen source `58b9ef1` and the same original
audited APKs. PREPARE proposal
`a30afb50c0859f18ed9913f534f2b32f440cf5c65ae6b928787ae3da1215f2cf`
passes full root/independent checks; original9951 terminal0, SDK child0 with
known cleanup3,859ms and verified prepare closure. RUN proposal
`ddb21a18cbd7db95ad751711a6659659dc42378dfa9556f54eeae7d301a20c83`
is independently checked before launch; its lifetime is exactly1,800s.

Preflight proposal
`d2fdaaae1ea33a6a3475139055b237477dbdff0ed4a016b1c285dc2d28984ccf`
binds75 nonweight inputs/87,338,625B. Original74243 terminal0; owned worker0,
cleanup/capture true67,953ms, stdout416B/stderr0. All43 clients complete0
with known cleanup; one source-preflight method passes12 checks. Proof SHA-256
`712cec51adf224a0084cf98eaf3ebce21f6f5e337553e1cbc4cb64aac7808349`.
Actual total memory8,332,292,096B, available before6,096,777,216B; external
free8,573,059,072B, userdata before11,525,132,288B. No weights/SDK in preflight.

Candidate proposal
`1f680794dc7b474df4ef3f8335a0d458fe70be0bdc632fffc981a62deb55ba9b`
binds79 nonweight inputs/87,344,872B and explicit human consent to the same
successful live preflight. Independent check observes1,622s remaining; the
unchanged production entry guard is satisfied. Separate copy/SDK flags are true.
Client13 completes the held-FD full source hash and local stream: expected
2,588,147,712B, client0, known cleanup. Its record deliberately still says
remote exit unknown and destination unverified. Actual IMPORT then reaches the
READY wait *after* the preceding independent staged-source fullhash assertion
and source-close check returned. That source-order evidence verifies staging;
it does not establish successful receipt import or acceptance.

Original candidate15627 terminates1. Owned worker2/known cleanup and capture
265,906ms, stdout455B/stderr0. All14 clients complete0/known cleanup, but the
single IMPORT method **fails**,130.335s: ComposeTimeoutException waiting READY
after120,000ms at frozen fixture lines410/484. Raw runner2,798B SHA-256
`e05ff5f8b55df1d3a97b3e9346acada258c971d2f4abbc86a62c865a676a4cfe`.
ADB exit0 is not a test pass. No IMPORT proof, SDK call, PLAY or REOPEN follows.
The test did not record whether the controller was FAILED or still IMPORTING
at timeout, or how much the importer had consumed. Do not invent those facts.

Exact owner77768 stops, original terminal0; cleanup/capture/preservation closure
true491,500ms, worker1 from requested drain, guest flush false. Actual recorded
processes are absent and owned ports free. Source and any partial/accepted data
remain inside the retained virtual disks; their contents were not inspected,
adopted, cleaned or claimed durable after power loss.

## Import observation and bounded I/O correction

The failed READY wait now uses the existing debug failure reporter to capture
only closed expected/actual phase and independent capped import-source counts
before teardown. It preserves the identical original throwable even if reporting
fails, sends at most one existing1337 record and performs no diagnostic I/O.
The ACCEPT carrier labels the intended flow, not a successful acceptance;
events stay empty and error NONE because no production events/cause were observed.
Read/byte Long values are clipped before narrowing; saturation flags distinguish
clipped counts. Verification counts stay separate. Timeouts are unchanged.

The transaction's old64 KiB buffer caused39,492 chunks per model pass, with full
Context/volume/path/capacity admission before each actual read/write. That is
source cost amplification, **not a proven explanation of the emulator timeout**.
A one-constant change uses a fixed1 MiB buffer; every guard, cancellation check,
byte limit, full hash, stamp, force, lock and acceptance boundary remains in
the same place. No cache stamp substitutes for a full hash.

Five original synthetic bulk tests exercise exact8 MiB import/full reopen,
short reads, mid-read cancellation and volume revocation before another write,
oversize-by-one and wrong digest. On the old constant, actual targeted JVM run
original44573 terminal1:28 tests, one intended failure, zero errors/skips;
the other27 pass. Captured metrics are129 source reads,643 import guards,
193 reopen guards and65,536B maximum request. Owned completion1/known cleanup
44,140ms, stdout4,699B SHA-256
`ae8e1b1cdf00fe723ac7e95a3fbe8f9dede513b755d9a143b7ffc8ca2208ffad`.
Original XML and output are copied before the next clean test task.

After only the constant change, the same test oracle passes as part of the
actual receipt build:367 JVM tests/36 suites, zero failures/errors/skips;
lint0 errors/19 warnings, dependency/analyzer audits pass. This verifies nine
copy-source reads,1 MiB maximum request and guard ceilings200 import/100 reopen
for the synthetic8 MiB case; it is not an Android speed measurement. Original
90838 terminal0; owned completion0/known cleanup151,094ms, stdout9,903B SHA-256
`afc387ffd9bf5a597505c45a66952a1ebf6ac6aa57e6463e0587a81a5d2b8ee4`.
Compilation source `002419f356b09b6c62e42e59018daa35c99798c2` includes the
passive real failure observation and the unchanged test oracle.

New receipt APP75,279,861B SHA-256
`06e43a1eae05b9c53b348c8f6a783039513081ade8804d9e392fafeb900283b5`;
TEST2,807,151B SHA-256
`06fe284b04d0ef507d84c7f1cc49d2f494dcaaad6cfecb9d7021346cf85725cc`.
Only one APP DEX payload differs from the old APP; all other uncompressed ZIP
entry contents match. The fresh regular-profile build also passes345 JVM
tests/35 suites with zero failures/errors/skips, lint0 errors/9 warnings and
dependency/analyzer audits. Original97030 terminal0; known cleanup148,610ms,
stdout9,157B SHA-256
`2d0b59f8873192f8fef3b90396b7a099cee831722ba5c919a5315951467ab836`.
Its APP SHA-256 is `b022da251d0753c93293165c667f30b0c9d3f6b797f59ba37f1ad40176aa43e9`.
Ordinary-profile source/build inputs remain unchanged; its existing audited
artifact is reused without a fresh ordinary build/JVM claim.

Actual receipt/new regular/reused ordinary APP audits and both receipt APK
signature checks pass with known cleanup; TEST manifest matches the previous
audited bytes6,244B SHA-256
`ded72dbadcabfb44c776d00b37f24a642bcc2541a2416334580b75f25abb4d83`.
The current pinned-artifact host suite passes668 tests in76.987s, zero
failures/errors/skips, original94746 terminal0; known cleanup78,125ms,
stdout78,824B SHA-256
`90500af8e502db80e42e1a0f5c832295d0b233e7d686c1f226a1aed7525f9e9f`.
No real-device performance or successful SDK result follows from these builds.

## Remaining gates

The second attempt verifies local staging but fails receipt import verification;
SDK gift and restart remain unrun. The corrected build needs a fresh admitted
target and another actual import/play/reopen run, with all limits intact.
The exact existing Gemma4-E2B/LiteRT-LM0.18.1 pins and publisher/container
verification remain unchanged; no new dependency or runtime choice is made.
Full M05.05/M01.05, physical phone, ARM64/16KiB execution, DocumentsUI,
cache/privacy, power loss, sustained inference and narrative quality remain
pending. Consent for the fresh receipt destination is now granted; do not ask
for it again merely because the scheduling prerequisite needs correction.
