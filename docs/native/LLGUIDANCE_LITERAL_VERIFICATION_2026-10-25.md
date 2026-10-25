# Finite SDK constraints: verification, 2026-10-25

Refs #9 (M05.01/M05.02/M05.05), #5 (M01.05 supporting). Root claim
[6400786067](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6400786067).
Implementation05527059, audited receipt APK pin3efe84df, based on090a8694/#173.
This is a locally verified implementation awaiting owner acceptance. It does
not complete M05 or qualify a physical phone.

## Reproduced defect and correction

The pinned LLGuidance1.3.0 depends on derivre0.3.8. Its `JsonQuote`
`Expr::ByteConcat` branch builds a quoted byte prefix and returns it without
appending the mapped tail when that prefix needs escaping. The internal
byte-concat limit is31. Exact primary-source paths and public SDK interface
research are retained in [literal research](LLGUIDANCE_LITERAL_RESEARCH_2026-10-25.md)
and [SDK mask-path research](LITERT_MASK_PATH_RESEARCH_2026-10-25.md).

Actual native observations with the already verified Windows wheel:

| Control | Observed result |
| --- | --- |
| Original quote/backslash/Unicode/newline text,42 raw UTF8 bytes | Full48-byte JSON rejected at13 by all three JSON paths; wrong shortened prefix accepted |
| Bounded minimization,73 evaluations |32 raw UTF8 bytes remain; full38-byte JSON rejected at3 by all three paths; shortened prefix accepted |
|16 threshold controls, two quotes plus25–40 letters | Raw27–31 bytes pass; raw32 fails at3 with only closing-quote token allowed; later lengths fail at the predicted longer prefix |
| Exact whole-serialized-JSON regex | Original and minimized full strings accepted through EOS; shortened strings and trailing suffixes rejected |

The JSON paths are default JSON, default Lark wrapper and explicit Lark
`no_forcing`. The latter is a failed control, not a remedy. A direct consume
failure alone cannot distinguish grammar mismatch from resource failure;
the source omission plus these full/short-language controls provide the
specific defect evidence. They do **not** diagnose the earlier Android
wrapper-declared INTERNAL13, whose ordinary literal is shorter and unescaped.

The development worker selects the pinned public SDK regex response format
only after complete bounded finite-schema translation. Nonfinite/unsupported
schemas use the existing JSON format. No dependency, Rust semantic schema,
generation budget, gameplay authority, prompt, event or storage format changes.
The [protocol](LLGUIDANCE_ORACLE_PROTOCOL.md) specifies limits and reproduction.

## Actual checks

WindowsAMD64, CPython3.9.12, Rust1.93.1, Java21, installed AndroidSDK/API35;
existing pinned LiteRT-LM revisionbda624851d74be34d4e1f7fac1fc4155939539c7.
No model download, native rebuild or dependency introduction in this packet.
All reported process owners below completed0 with known cleanup unless noted.

| Check | Result |
| --- | --- |
| Offline locked Rust tests |361passed across50suites;4 historical capture-only ignores; new2 literal regression tests pass |
| Offline Clippy, warnings denied |PASS |
| Full Python suite |866passed,0failures/errors/skips |
| Targeted8 Python modules after APK repin |PASS, owner34547ms |
| Receipt JVM |512passed,48XML suites,0failures/errors/skips;81031ms |
| Regular JVM |454passed,43XML suites,0failures/errors/skips;74328ms |
| Receipt APP/test assembly |PASS,69797ms |
| Regular APP/test assembly |PASS,55734ms |
| Receipt lint/dependency/analyzer audits |PASS,80985ms;0errors/19warnings |
| Regular lint/dependency/analyzer audits |PASS,58203ms;0errors/9warnings |
| Receipt/regular APK manifest/native audits |PASS,1047/1046ms; no INTERNET permission; six packaged libraries each,16KiB ELF load alignment |
| Receipt/regular APP+test signatures |PASS,672ms each; same debug certificate SHA2561960a64db1dffe2f173f5cb08601bdad30bcf1285a90c9b9928a4d562c1123d1 |
| Actual Kotlin patterns through native regex |215/215samples plus all sanity controls PASS,703ms |
| Current-source literal replay |Observed defect report,484ms,0stderr bytes |

The native finite corpus contains13schemas/215samples:119positive and96negative.
It retains all original8 engine schemas/199samples and three provider-free
refusals, adds five original literal regression cases and one nested truncated
negative. All semantic choices in the engine corpus remain; no known failure
was removed. The Kotlin export8237bytes has SHA256
`d2989fa17c242bf58e7ff902e3267b05d87401a0dbe6abc4de637c6f9a13918e`;
input37029bytes SHA256
`aac94a0ca1de3222a4774dd0a404b44f867d9712e6919c1a4ece553fdc7fc1a2`.
The native report35809bytes SHA256
`02708b00f2da25a0a17068ae6f8170b14109fe3dcb15f3050a0a8d702e9619a5`.
The original JSON mismatch remains documented separately.

Core reproduction uses the same pinned commands (choose a new private target):

```powershell
cargo +1.93.1 test --frozen --offline -p locallore --features host --all-targets --target-dir C:/private/new-core-target
cargo +1.93.1 clippy --frozen --offline -p locallore --features host --all-targets --target-dir C:/private/new-core-target -- -D warnings
cargo +1.93.1 fmt --all -- --check
```

Actual Gradle task sets were `cleanTestDebugUnitTest testDebugUnitTest`,
`assembleDebug assembleDebugAndroidTest`, and
`lintDebug auditLiteRtDependencies auditLintAnalyzer`. Both profiles used
`localLoreLiteRtVerification=true`, `localLoreModelSetupVerification=true`,
offline/no-daemon, max-workers2, Kotlin incrementalfalse, analyzer9.4.1,
Java21 and disabled automatic SDK/JDK downloads. Receipt additionally used
`localLoreModelVolumeVerification=true` and
`localLoreModelReceiptVerification=true`. Its JVM task exported actual patterns
using the two environment paths specified in the oracle protocol. Exact
argument arrays and source/command workers are retained with the local results.
Native `literal` and `finite` calls use the public commands in that protocol;
neither loads a model. APK audit commands used `--litert-verification
--model-provisioning`, plus `--model-volume-verification
--model-receipt-verification` for receipt, followed by installed35.0.0
`apksigner verify --print-certs` on each APP/test pair.

Raw JVM XML, command arrays, source captures, bounded process reports,
compiler reports and artifacts remain in private local evidence. The first
JVM attempt512tests/12failures is preserved: Android's unmocked `org.json`
stub caused nine direct failures and three downstream assertions. Replacing
it with already pinned Gson corrected the implementation; the successful
run used actual parsing, not mocks. An initial isolated Python worker import
failure and the initial APK audit missing ANDROID_HOME were retained and
corrected. A collection step targeting a nonexistent regular build directory
was refused, then corrected without claiming another test run.

## Frozen artifacts and source identity

| APK | Bytes | SHA256 |
| --- | ---: | --- |
| Receipt APP |75041504|83797af66672e5bab89e17d53339478eb7c57bee66773c9c72edd13466911a8a|
| Receipt test |2056615|e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d|
| Regular APP |74975720|9ba3e59b2f8d3ed8ae71b3c7601d47c1039b194b9850c443541b4d2118bf5357|
| Regular test |1869719|8c14c03502faee7661b58a6862c5b35e9fec6e6371e40b9c2718daadd56ad1e5|

All six corresponding APP native libraries are byte-identical between variants.
ARM64 packaging is not ARM64 execution. Normalized codec source SHA256
`b89ba9aa332529a629e0f532f5d8e55997eef8f68229665f898eae53010af96f`
is bound into worker source SHA256
`db4d5f18318b7b5d67fbeb33bddee7781ddce7adc41477d9c17808e92c23df27`.
The original schema's425-byte trace field does not report regex payload size.

## Resource housekeeping and remaining gates

Two reversible build-output compression operations preserved every logical
file hash. A later complete code-build archive preserves11305files/8476815696
logical bytes in1900763069archive bytes, SHA256
`0af883ad0f0947b3af071650a5f41b1ae978061b204570a09715d5ba76bf1e0a`.
Archive member readback and a subsequent full source rehash passed. Removal
of the four archived generated directories was rejected before dispatch by
automatic approval review, again after explicit owner permission; the only
reported reason was "blocked by policy". Nothing was deleted or bypassed.
Models, saves, emulator data and earlier evidence remain outside that archive.

The [independent device preparation](FINITE_REGEX_DEVICE_ADMISSION_2026-10-25.md)
records a dated capacity snapshot and a small NTFS experiment. Neither is a
VM, SDK or model result. Fresh source/APK/lease/storage admission, local receipt
import, actual Android inference, canonical gift/dialogue, process restart and
no-inference replay still require a separately observed run. Existing
quarantined targets are not reusable evidence. Physical-phone M01.01, ARM64
execution, model quality, latency tiers and the complete M05 exit gate remain
unqualified. No merge, release or access change is performed by this packet.

## First fresh D-root attempt: import runner passed, controller stopped

The later sampled D: free space rose to83.46GB while the rejected cleanup
remained unexecuted. A separately reviewed plain D-root admission retained
40GiB on **both** drives, with an additive sampled2-second monitor. Its
private outer grant bound the unchanged inner environment proposal, grant
and guard source. Independent review corrected sticky stop/final-status
issues before boot. This was observed reserve protection, not a disk quota
or an all-times guarantee. No compression was used for the new VM.

PREPARE's owned SDK child completed12390ms/0/known cleanup. Boot metadata
showed the8GiB raw SD **and** a growing SD overlay, userdata base/overlay,
and an8.59GB RAM backing despite the no-snapshot flags. The conservative
full12GiB userdata+8GiB raw SD+8GiB SD overlay+8GiB RAM budget is36GiB,
plus filesystem/cache/other overhead; model copies are inside those guest
backings. No RAM-image/snapshot-content or guest-flush claim follows.

The exact audited receipt pair was installed on fresh API35/x86_64, four
guest CPUs. SOURCE_PREFLIGHT passed1method/12checks. All44 command records
had known cleanup; outer82157ms/worker0/output complete/0stderr. Independent
review verified raw runner, proof, source/UID/package/descriptor links and
stronger postguards. Full weights and SDK were absent during preflight.

A separate ordinary grant bound those successful raw records, unchanged
source/APKs, consent and the same healthy live lease. The once-only held-FD
local stream verified2,588,147,712 source bytes and the expected SHA256, then
reported client0 with destination/remote-completion explicitly unverified.
The app's IMPORT runner subsequently reported **OK1 in134.086seconds**.
Raw802bytes SHA256
`f740c18399a14de4a78a1a331eb8c32bd028a4db9eac9da5908f501b03d0eab6`.
Its client completed0 with known cleanup. However, the controller rejected
that result before reading the app-domain proof: the inherited synthetic
runner parser hard-capped summaries at120seconds, while the already defined
IMPORT phase permits150000ms. Ordinary START/DIALOGUE similarly define170000ms
but used the same inherited parser. This is a demonstrated harness mismatch,
not evidence of a failed app import or a slow inference call.

The outer ordinary driver stopped at `instrument-IMPORT`,310047ms/worker2,
known cleanup/output complete/0stderr,15commands/one instrumentation method.
**No import proof was read; no SDK, gift, Dialogue or reopen was dispatched
or qualified.** The target was stopped through its exact proposal-bound
owner:600328ms/known cleanup/output complete/preservation closure verified.
The guard ended healthy with no monitor failure. The target, source, model
copies and raw failure remain preserved; there was no target retry or proof
salvage. Host closure does not establish graceful guest flush.

The selected first-device evidence index covers177files/581977bytes, SHA256
`488a433dde912c0254878d6471d930dce81d4213f815d2d3520f0897e29531b9`.
It explicitly excludes images, weights, caches and keys. A separate host
selection covers204files/308644390bytes, indexSHA256
`759c7c8a1df06ebe0088e3bc2c64fa0bd694497efe33ede88bb833e453c4a1be`.
All93 executed controller/source dependencies were captured before correction;
six Android compilation source crossbindings remain exact. Private evidence
is retained locally, not uploaded.

The next correction binds each runner parser to its **existing fixed phase
budget**, preserves synthetic120000ms, tests exact/beyond limits and original
framing, and replays this original raw result offline. It raises no worker,
generation, client, profile or acceptance deadline. A newly frozen source
and fresh target/preflight are required before repeating the ordinary cohort;
the old target remains retained. Checkboxes and physical/quality gates stay open.

## Phase-duration correction and second admission

Correctionb7508016 adds keyword-only `phase_budget_ms=120000` to the shared
runner framing parser. Only exact integers30000/120000/150000/170000 are
accepted; booleans, floats and arbitrary larger limits are refused. Real and
ordinary selectors supply their existing `PHASES` constant. Other/synthetic
callers retain120000. Class/method/start/end/result framing, source proof,
client/SDK/aggregate/lease limits and cleanup checks remain unchanged.
Tests include exact and one-nanosecond-beyond summaries, invalid budget types,
default120, fixed forwarding, CRLF and malformed framing. The original
134.086-second raw IMPORT now parses under150000ms and still refuses under
the default120000ms. This is offline parser evidence, not a retroactive import
proof or SDK run. The author's72 targeted tests passed; their stdout remains
in the original tool transcript, not an invented separate raw log.

The broader repeat on the host-selected CPython3.14.7 ran871tests with one
failure: the preexisting fake-symlink test patched only `Path.lstat`, whereas
the newer `Path.is_symlink` can use `os.path.islink` directly. The deliberately
nonexistent fake path therefore reached `missing_path` instead of its intended
`unsafe_path`. Raw failed output is retained, SHA256
`a819d38f5fa5ba70efac56a539863dba1f3142acf1d09c8c57c0fd3396936276`,
owner80910ms/return1/known cleanup. Fix7fac8a9c explicitly models both synthetic
link observations without creating a link or changing production path guards.
Its focused test passes. A new full owned run passed **871tests,0failures,
errors or skips**,73.038s runner/74100ms owner0/known cleanup/0stderr,
rawSHA256`2a44167beaf7dd2bd11bccd4552c161ab16cb7c8a085d43c415ed34d9521ac08`.

The new93-source indexv2 SHA256
`b998728c0a23b52bd5e7aa642e26bd935c2838f04e445824aee7d8664a5dcc29`
binds7fac8a9c and the observed Python3.14.7 executable/version. All six Android
compilation crossbindings and the audited receipt APK pair remain byte-identical;
they are reused with that explicit evidence, not described as newly rebuilt.
The earlier source index and failed raw reports remain intact.

A second **new** plain D-root was separately prepared, owned SDK child7688ms/0/
known cleanup, same8GiB RAM/4CPU/12GiB userdata/8GiB SD. After871passes, source
readback, unchanged APK verification and40/40 resource checks, a separate
1800-second BOOT-only grant was frozen. The old target was not adopted,
resumed, retried or queried for its unread proof. At this dated admission,
second preflight, full local stream/import, real SDK and reopen remain pending
actual results; no success is inferred from the corrected parser.

## Second fresh attempt: import and real gift pass; Dialogue still fails

Executed controller source24b4b800 has the same93 bound source bytes as the
7fac8a9c source indexv2; its later change is this unbound evidence document.
The separately admitted new API35/x86_64 four-core target passed preflight:
1method/12checks,44 known-clean commands, outer52087ms/worker0/output complete/
0stderr. Independent review matched the raw805-byte runner, all command hashes,
source/proof/UID/package links and stronger40/40 postguard. Its descriptor is
distinct from the first attempt. No full weights or SDK entered preflight.

The separate ordinary grant bound all four successful preflight records,
the same live owner, consent, source and audited APKs. Its once-only full
held-source transfer completed with the expected size/hash and client0;
destination authority still came from the subsequent app proof.

| Actual phase | Result | Evidence |
| --- | --- | --- |
| IMPORT |PASS,16checks; runner106.623s/app105845ms |Full source hash/size, one opened/closed verification and import stream, accepted receipt/owner/full recheck; SDKfalse |
| ORDINARY_START |PASS,28checks; runner94.872s/app94468ms |Actual production setup Start/New story/Send; local SDK director+narrator; canonical revision1/one gift receipt, repairs0/fallbackfalse, full model postcheck and native handle closed |
| ORDINARY_DIALOGUE |FAIL, runner57.102s |Wrapper-declared CODE13/INTERNAL after15validated chunks/58UTF8bytes; no accepted Dialogue proof |
| ORDINARY_REOPEN |Not dispatched |The failed prior phase prevents continuation; no restart qualification |

Together with preflight this is **56 qualified checks across three passing
methods**. This does not qualify all122 checks or the complete M05 scene.
The gift worker trace has two DONE/two settled drains/two known conversation
closes/one known engine close and zero uncertainty. The recorded gift receipt
SHA256 is`cdf0e1ca6d08195dd40e30603249e6e611c1dead6a3c647f0b13d80df51ef695`.
It remains the last qualified revision/receipt observation; no post-failure
canonical/model state was queried or inferred. Fixture/runner timings are
not a physical-phone performance tier or isolated generation benchmark.

The failing Dialogue raw runner is6565bytes, SHA256
`9b64efd6` (full hash is retained in its command record and selected index).
Its trace observes only DIRECTOR creation, SEND returned,15callbacks then
one wrapper status13. DONE and settled drain remain0, conversation/engine
known close remain0, uncertainty2. These are chunks/bytes, **not token counts**.
The original425-byte engine-schema trace field remains unchanged. It is not
the generated regex size, schema hash or an authenticated observation of the
actual selected SDK response format. Compiled codec/selector/source evidence
does not replace that missing runtime observation. The ordinary INTERNAL13
cause is still unknown; the separately reproduced escaped compiler-tail
defect must not be claimed as its explanation or cure.

The ordinary controller stopped at`instrument-ORDINARY_DIALOGUE`:46 known-clean
client commands/three instrumentation attempts, outer413566ms/worker2/output
complete/0stderr. No subsequent guest/model/cache/proof read, SDK retry or
REOPEN was issued after uncertainty. Only the exact proposal-bound host owner
was stopped. Its receipt records735332ms, stop_requested, known cleanup,
complete output and preservation closure; no graceful guest-flush claim.
The sampled guard ended healthy with no monitor failure. All targets, source
and failures remain retained.

The final second-device selection binds253files/666792bytes, indexSHA256
`b1dc72119690d2a3d35b5684def3549c856daa2c8f6127048404ec28ac4b0b64`;
owner receiptSHA256
`2aa36ed9b8b856b8dde71a3b4765f5bbdfab19ac04c0e505915bb1248b740ead`.
The follow-up host selection binds12files/77439687bytes, indexSHA256
`3e4281d6880b458ae369070c97e45e42ff6284981a6cd73708ada3b2ec376eac`.
Original93 source files are captured separately. An initial index construction
refused the1910-byte original`start-worker-v2.json.raw` suffix; the corrected
explicit bounded allowance preserved those exact bytes, with no result
regeneration. Images, weights, caches and keys remain excluded. Nothing was
uploaded from these private selections.

PR175 was externally merged atf1709713/a7feb420 while execution continued;
this packet performed no merge. Later phase validation, both D-root attempts
and their evidence belong to [PR176](https://github.com/OptimumAF/LocalLore/pull/176).
M05.05 remains partial/in_review, with real Dialogue/restart blocked on this
reproducible SDK failure. M01.01 reference-phone and ARM64/16KiB execution,
quality, sustained and full milestone gates remain unqualified. The next
runnable source/host task is a bounded response-format selection observation
and actual-model-tokenizer mask comparison for this original ordinary schema;
no further call or read on the quarantined target is authorized by its failure.
