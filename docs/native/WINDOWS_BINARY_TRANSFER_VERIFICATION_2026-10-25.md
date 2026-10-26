# Windows binary transfer and resumed local scene verification

Refs #5 (M01.05 supporting), #9 (M05.05 prerequisite), root claim6405512050;
update to PR181. Full milestone acceptance remains pending. GitHub tickets own
status and work-log records; retired Markdown trackers remain pointers.

## Observed problem and correction

The earlier shell prerequisite reported a successful client but only26B of an
original768B source. Its hash exactly identifies bytes0x00 through0x19, ending
before0x1A. The new [Windows CRT control](WINDOWS_STDIN_PROBE.md) explicitly
selects text/binary mode in the same system CRT and reproduces26B versus768B
with the exact original hashes. This establishes the CRT mechanism on the host;
it does not observe the installed ADB binary's actual CRT mode or prove its
executed source path. The historical shell result remains failed.

`binary_stdin_operation` now fixes model/CAT/DD input to `exec-in` and refuses
Windows SHELL_BINARY/SHELL_CAT before dispatch. No shell fallback, escaping,
filtering, alternate payload or destination adoption is allowed. Existing shell
description/qualification adversaries explicitly simulate a non-Windows platform;
separate Windows tests require refusal before lease, claim or client creation.
No platform support is inferred from those mocks.

The earlier model path already used `exec-in`: its timeout is a separate issue.
Its180s parent included admission and a full held-FD hash, reducing the actual
client budget to140.906s in the retained95.49%-host-cursor attempt. That cursor
was never a received-byte proof. Prior original1GiB controls took58.460/58.107s
inside the client, so180s for preparation plus the full model transfer offered
little margin. This is evidence for budgeting, not a throughput guarantee.

The fixed model-only staging parent is now240s, clipped to the existing870s
aggregate remainder. The actual transfer client stays `min(150,parent-left-5)`;
generic process/preflight parents stay180s. SDK60s+5s cleanup, app-phase caps,
candidate870s/outer900s and emulator1800s owner limits are unchanged. This is an
explicit staging-envelope change under fresh source admission, not an extension
of any running owner's deadline.

The adapter reuses the existing durable Job supervisor in a create-only nested
driver directory. Its raw output/start/result are retained before interpretation.
Success requires known cleanup, complete capture, exact typed worker0, no stderr,
at most4096B stdout, actual raw-size binding and the original closed six-field
summary. The durable capture's absolute private cap is262144B; larger output
cannot qualify the4096B summary. Exceptions poison the parent and prevent import.
A failed child may therefore have nested driver evidence without a completed
parent command-N record; no completion is synthesized.

Full source authentication uses bounded1MiB hash blocks, not a complete model
array. Held source identity/postchecks, exact live parent/lease, one-shot claim,
create-only app-private staging, full destination hash and acceptance receipt
remain authoritative. Client0 grants no destination, import or SDK authority.
Preflight lineage also rejects boolean completion counters and noninteger,
out-of-range or duplicate app/test UIDs, including fully rebound metadata.

## Actual host evidence before runtime admission

Python3.14.7/Windows; runtime source47bb4770:

| Check | Actual outcome | Retained stdout SHA256 |
| --- | --- | --- |
| Focused source/preflight/transfer/ordinary suites |96 PASS,19.167s; owned19618ms/0/known cleanup | `52f5e179c92ea465cd1ceabf33fe9fb0be5d28144f557d4e642d3061760177c0` |
| Full `scripts/tests` discovery |1095 PASS,95.132s; owned96488ms/0/known cleanup | `0b1eb97b29f5b4ac8fe10aba11d99487749ac8c82623dfd16f14c871ea0b5978` |
| Independent binary-transfer adversaries |16 PASS,14.293s; owned14774ms/0/known cleanup | `10af568d4476d53ff29cad4457f6c7aed2e2034ea1191a614add5d63f3022bd4` |

Central commands were `python -B -E <private-owned-launcher> focused` and `full`.
The launcher uses the existing Job controller, fixed stdin barrier,180s deadline
and262144B cap. The full child runs
`unittest.defaultTestLoader.discover('scripts/tests')`. Its197292B capture has
zero stderr; all115 captured source pairs match before/after. The full suite
includes17 mocked CRT tests and16 binary-transfer adversaries, distinct from
actual native execution. No Rust/Gradle build or new dependency was introduced.

The root separately ran the integrated actual CRT control. TEXT returned26B/hash
`b858da80d8a57dc546905fd147612ebddd3c9188620405d058f9ee5ab1e6bc52`;
BINARY returned768B/hash
`f3a25aa93aa2fbba28d79260535bbd6a5eb0fc1c24a8b0f04e12b484c1dfe363`.
Both clients completed0 with known Job/pipe/descriptor cleanup and EOF,296/281ms,
zero stderr; source unchanged and fixture not retained. Result3298B SHA256
`cda77691218466859d7e1945dacf39d2f4bd0d0a5ce10982c168035ceace5565`.
This test makes no ADB, server, device or model call.

Original failed checks remain: the first central73-test attempt had three
cohort-mock failures after the process adapter changed; the old mock did not
intercept the new child supervisor. The tiny invalid proposal refused before
device work. The corrected phase-ordering mock and dedicated adapter adversaries
then pass. This first central failure has an explicit operator-observation record
and raw tool transcript, not a fabricated owned result or retained temporary
fixture. Independent16-case attempt1 had one tiny-source fixture seam failure,
then passes unchanged production after correcting that mock. The CRT control's
three ownership/mtime regressions were RED on its first implementation, then
GREEN. Available raw/receipt history is retained, not relabeled successful.

## Fresh environment and preflight

A D-root preparation completed with known closure but was never launched. Its
46,807,965,696B available space left less than two full model copies above the
unchanged40GiB storage guard. Preserve that prepared namespace. Explicitly plan a
different fresh C-root target rather than reducing the guard or deleting files.
The new C-root preparation and plan-run completed with known closure.

Selected installed emulator35.3.12/build12990079, API35/x86_64; unchanged8GiB
RAM/4CPU/12GiB userdata/8GiB SD,1800s owner,2s sampled40GiB C/D guard. Sampling
is not a reservation or continuous hard ceiling. Parent run admission observed
30,888,980,480B available physical memory and14,353,362,944B commit headroom
against10,737,418,240B required by the separately labeled guest+2GiB policy.
Fresh worker checks remain required. No other emulator or system setting changed.

Runtime source47bb4770524c44d166da442bff4e60b8ebb94904 freezes105 required
sources, eight unchanged Android compilation bindings and the same audited receipt
APKs. Manifest SHA256:
`34eb483f98de0eadcdd34c9a0d59a6c60137d299e58eadc14acad9a4ec81bcf4`.
All Android/Rust bytes are Git-identical to audited source44103b8c. Receipt APK
app/test SHA256:
`c9325b6a50483afc0d928ab3d16c14c5a43caebacc4a96d11f16328f976f15fa` /
`e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d`.

Actual preflight passes all12 original checks/44 bounded commands, owner50753ms,
worker0/known cleanup/complete capture/stderr0. It stages only61 trusted bytes,
reads no model and invokes no SDK. Run proposal:
`ac0c2bb1a7e482633193831154ada526b1d185f3cbfa3d8c0a8b10ceb4411d6e`.
The separate ordinary candidate grant
`986b777f6f2e5670071476d64b536d3339708218dfd43ad10d9e1f6a2b134d27`
binds115 inputs, including the manifest, exact four preflight records and same
live owner. Its1618s remaining lease exceeds the920s entry requirement. Current
owner authorization covers this local model copy/import/inference; no additional
human confirmation is inferred necessary from historical document wording.

The selected fixed chain is IMPORT→ORDINARY_START(Gift)→ORDINARY_DIALOGUE→
ORDINARY_REOPEN. It is not stitched onto the incompatible direct-gateway proof
namespace. Each exact class selector, raw runner, app proof, prior hash, process
identity, trace and canonical receipt must qualify before the following phase.

## Actual model transfer and import

The fixed2,588,147,712B model stream completes, nested owner124110ms/worker0,
known cleanup/complete capture/zero stderr,159B original transfer-only summary.
The driver records the240s parent and unchanged150s client cap. Successful output
does not separately report client duration. Changed host/cache/backing conditions
prevent attributing its throughput solely to the parent-envelope correction.

IMPORT then passes its exact method and all16 app checks,98850ms. Verification
and import each open/close exactly once and consume2,588,147,712B. Source full
SHA, accepted receipt/owner, postaccept full recheck, off-Main source close,
setupReady and capacity/memory checks all pass. SDK inference remains false
during this phase. This establishes actual destination/model acceptance, not
merely a host cursor or client return. It does not qualify DocumentsUI,
external-cache confidentiality or physical-phone model performance.

The ordinary Setup→Play Gift method then passes all28 app checks,112504ms,
actual SDK invocation, no repair/fallback, one canonical receipt/revision1.
Full model postcheck and known worker close precede the Rust commit. The
following literal Dialogue method passes all43 checks,81372ms, actual SDK and
no repair/fallback. Rust records a second receipt/revision2. The literal statement
does not become world truth; known truth and the Gift receipt remain unchanged.
Inspector provenance/knowledge checks pass. The invalid ability and duplicate
Gift are rejected with zero SDK workers; their checks cannot be credited as
model generation.

ORDINARY_REOPEN passes all23 checks,34543ms, in a distinct process linked to the
prior PID/start/proof hash. It reopens the same two canonical receipts/transcript
at revision2 through Setup→Play, with source unopened and SDK false/worker zero.
This is app-process restart, not emulator power-loss or physical-device proof.

| Phase | Methods | App checks | App elapsed | SDK |
| --- | ---:| ---:| ---:| --- |
| SOURCE_PREFLIGHT |1|12| Separate preflight | false |
| IMPORT |1|16|98850ms| false |
| ORDINARY_START |1|28|112504ms| true |
| ORDINARY_DIALOGUE |1|43|81372ms| true |
| ORDINARY_REOPEN |1|23|34543ms| false |

**All122 app checks pass**, across the separate preflight and four-method
candidate. Candidate owner484402ms/worker0/known cleanup/complete capture,
416B stdout/zero stderr;78 bounded command attempts, zero candidate installs.
The actual ordered chain and prior/receipt/worker-trace hashes are validated.
The current finite spelling codec therefore has actual SDK literal-Dialogue
evidence on this emulator. Earlier INTERNAL13 and transfer failures stay
historical; passing later execution does not establish their causes.

Only the exact new LocalLore host owner receives a verified one-shot stop.
Terminal disposition: `stop_requested`,764302ms, worker1,11165B stdout/1076B
stderr, known cleanup, complete capture and verified host closure. No guest
flush is claimed. The sampled storage guard ends healthy with no monitor failure.
The other emulator and system settings are untouched. All target files are
retained; no failed image/cache is adopted or deleted.

## Diagnostic ownership follow-up after runtime closure

Review found that the host-only CRT control initially continued the second
dispatch/deleted its shared fixture after unproved child cleanup, then still
performed source postchecks after its first correction. Original RED tests,
intermediate source/results and reviewer findings remain. The final correction
stops dispatch, closes the parent descriptor, retains the visible fixture and
skips seek/read/stat postchecks whenever child closure is unknown. Its poisoned
postcheck regression is RED before the fix and GREEN afterward.

This last correction is integrated **after** the emulator owner is terminal;
the live105-file runtime freeze is never rewritten. Exactly three frozen files
then differ: the host CRT probe, its unit tests and its documentation. The model
transfer/controller/Android/Rust bytes remain identical to the executed snapshot.
Post-fix host tests and source freeze are separate evidence, not a new model run.
The final actual root CRT control again observes exact26B/768B, known EOF/closed
descriptors/Jobs, zero stderr,181/184ms, source unchanged/no retained fixture.
Its3298B result SHA256 is
`78c31b831f3c23c9d1e379b11e8a6f878fad049fba5a94c054c649c2ff2d961d`.

Final host-only sourcecf6d991d passes **1096 tests in97.118s**, owned98367ms/0/
known cleanup,197498B stdout/zero stderr, all115 source pairs unchanged. Raw
stdout SHA256:
`5f84f4a47a658814c88d21021e95729fa930bd66ee9a29ee0bf2f51672f37305`.
Its separate105-file host manifest SHA256 is
`99b7e7aa780de5117e2ad51a64714fb803c86a921ee517399196f4470b7b1e92`.
The original47bb runtime manifest remains unchanged. No device/model execution
is inferred from this later host-only snapshot. Final `git diff --check` passes;
no unrelated source or user change is overwritten.

The private evidence seal binds575 metadata/source/output files /4,678,644B;
index176733B SHA256
`eb414ec44e288c1152c370ffc730b044aa553e64b70cc4d62d98d0554a52961e`.
Every entry was reread and matched. Runtime and final host source archives are
separate. This excludes model weights, APK payloads, SDK trees, emulator guest
images and phone identities; none are uploaded. Raw private diagnostics remain
local. Exact aggregate status, counts and hashes are the public evidence.

## Remaining gates

M01.05/M05.05 supporting work remains in_review, with full tasks unchecked until
owner acceptance. This is one original synthetic scene on one API35/x86_64
emulator, not a reference-phone backend/profile decision or quality/performance
acceptance. No phone model was copied or loaded in this packet. Physical model
execution, sustained memory/thermal,16KiB physical-device coverage, DocumentsUI,
broader prose/agency evaluation and production runtime selection remain pending.
Gameplay authority and network/telemetry/account policies are unchanged.

Next runnable task: prepare the bounded ARM64 physical-device model qualification
harness against the already observed phone, rechecking current memory/storage
and destination authority before any local weight copy. Keep the emulator-only
memory/owner assumptions separate and require full source/import/inference/
cancellation/restart evidence; no phone result is inferred from this success.
