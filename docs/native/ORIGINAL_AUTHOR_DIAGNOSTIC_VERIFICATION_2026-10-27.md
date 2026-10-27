# Original AUTHOR refusal diagnosis — 2026-10-27

Refs #13 (M09.02/M09.06), #5 (M01.03 support), #14 (M10.02/M10.03 support).
Draft [PR #242](https://github.com/OptimumAF/LocalLore/pull/242) is stacked on
open/unmerged [#236](https://github.com/OptimumAF/LocalLore/pull/236).
Implementation checkpoint: `38e50317a054a94d12fd3798f4f7450c07aad07a`.

The fresh API35/x86_64 experiment passes full binary model transfer and production
import. One actual local AUTHOR response is rejected by Rust. The new private
sidecar captures its exact bytes, and the independently executed offline native
validator identifies the first failure as `character_names` / `InvalidProposal`.
This is diagnostic completion, not a passing author/create/reopen workflow.
No story is created; before/after native library observations are identical and
empty. Full milestone checkboxes remain unchanged pending their criteria and
owner acceptance.

## Implemented boundary

The [diagnostic protocol](ORIGINAL_AUTHOR_DIAGNOSTIC_PROTOCOL_V1.md) adds an
explicit one-shot response collector to fresh test owners. Ordinary owners
install no collector. Capture follows the existing successful native bridge ACK
and current ticket/owner checks; ACK means submission, not semantic acceptance.
The collector retains one defensive copy, bounded to8192 UTF-8 bytes, without
truncation, callbacks, logging, I/O, retries or gameplay authority.

The instrumentation writes a private create-only sibling sidecar after known
ownership and preserves the original v1 proof unchanged. It captures the fixed
original input, raw response, returned native envelope, passive library before
and after generation, and byte bindings. Native refusal does not suppress the
passive empty-library observation. Uncertain ownership still refuses collection.

Rust has one detailed proposal validator; the existing API delegates to it and
retains exactly the previous legacy errors and accepted set. Its offline example
accepts two bounded regular files and emits a nine-field, data-free report.
It opens no gameplay database and invokes no model. The pure Python binder checks
exact sidecar/proof/trace/native-report provenance and never reimplements engine
rules. The old full-roundtrip proof validator still runs separately and rejects
this incomplete workflow.

The SDK worker, model, dependency pins, prompt/schema, native creation consent,
role budgets, resource floors and cancellation/cleanup rules are unchanged.

## Actual host and build verification

| Check | Recorded outcome |
| --- | --- |
| Python diagnostic and legacy proof adversaries |45 passed (21 new plus24 legacy),0 failures/errors/skips; bounded owner6147ms, known cleanup/capture, no stderr,2013 inputs stable. |
| Focused Rust diagnostics/authoring/portability |33 passed,0 failed/ignored; owner43361ms, known cleanup/capture,2012 inputs stable. Includes9 detailed-validator tests and6 CLI tests. |
| Standalone native CLI build | Passed6297ms; same source bindings, no target/model calls. |
| Current Rust regression continuation |972 passed,11 ignored,137 result suites,0 failed; cached owner469684ms, known cleanup/capture, no stderr,2018 inputs stable. Android fixture check passed. |
| Rust format and strict Clippy | Both command records completed0 before the original aggregate owner expired. The aggregate remains failed; the later cached continuation does not replace it. |
| Full LiteRT JVM/build/audits |588 tests/58 suites,0 failures/errors/skips; cleaned unit-test task, unfiltered roster. Includes6 capture,10 owner,27 store and4 AUTHOR worker methods. Offline product/test APK assembly and audits passed; owner377669ms, known cleanup/capture, no stderr,2018 inputs stable. |
| Lint/analyzer |0 errors,10 warnings; analyzer32.4.1 with analysis_did_work:true. Gradle29 tasks executed/58 reused; no all-fresh compilation claim. |
| Diagnostic collection bounds |6 metadata-only synthetic cases passed in882ms, no SDK or payload-copy calls. Actual five-leaf maxima sum798720B; the aggregate-overflow adversary deliberately uses wider synthetic leaf caps. |

Runnable equivalents, from the repository root with the recorded offline toolchain:

~~~powershell
python -B -m unittest scripts.tests.test_original_author_diagnostic scripts.tests.test_original_author_model_proof
cargo fmt --all -- --check
cargo clippy --workspace --exclude locallore-desktop-spike --all-targets --locked --offline -- -D warnings
cargo test --workspace --exclude locallore-desktop-spike --locked --offline
cargo run -p locallore --example android_fixtures --locked --offline -- --check
~~~

From apps/android, with the existing JDK21/SDK/offline dependencies:

~~~powershell
.\gradlew.bat --offline --no-daemon --no-build-cache --max-workers=2 --console=plain --project-cache-dir .gradle-litert-worker -PlocalLoreLiteRtVerification=true -Pandroid.experimental.lint.version=9.4.1 -Porg.gradle.java.installations.auto-download=false -Pandroid.builder.sdkDownload=false -Pkotlin.incremental=false :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies :app:auditLintAnalyzer :app:cleanPackageDebug :app:cleanPackageDebugAndroidTest :app:assembleDebug :app:assembleDebugAndroidTest
~~~

The retained executions additionally use bounded host ownership and before/after
source/output bindings. The broad Rust run uses pinned1.93.1 on Windows, jobs2,
an isolated target directory and offline dependencies. The initial Cargo shim
admission refuses a linked executable before Cargo dispatch. The subsequent cold
aggregate expires600039ms with known closure/capture; its partial tests are not a
pass. The cached continuation explicitly admits a900s host owner with unchanged
600s command bounds. No emulator or inference budget changes.

Product APK:78287936B, SHA256
`48a5324cf7266a10175b1b23d5e3797f6d73e407dc2e34b885a0a6125ef66048`.
Test APK:2251307B, SHA256
`d0afd177355e8931291a0fd20f55fc31597c9af6a64d9d332b672b4893ab1be2`.
Independent audit rechecks the77 admitted build records, both defined JNI
publication exports,588 test XML results and the893 compiled input bindings.
Packaging both ABIs does not establish ARM64 execution.

## Fresh actual model experiment

The dedicated owned guest uses8GiB RAM,4 cores, API35/x86_64,12GiB userdata,
an8GiB generated card and the existing1800s lease. Fresh preflight passes the
actual8GiB guest plus2GiB commit reserve. No18GiB cutoff is introduced.
The main/SDK/stream/JUnit limits remain900/850/180/180s respectively, with a150s
direct binary stream ceiling and4GiB available-memory target floor.

The existing local Gemma container is2588147712B, SHA256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
LiteRT-LM0.18.1/runtime `bda624851d74be34d4e1f7fac1fc4155939539c7`
and the immutable model/profile identities remain those in the
[original protocol](REAL_ORIGINAL_AUTHOR_MODEL_PROTOCOL_V1.md).
No dependency selection, model download or model upload occurred.

The binary control and full model stream owners complete0 in43986/134486ms
with known cleanup/capture. Direct model streaming then receives a full remote
destination size/hash check. Direct client success is not claimed as a separately
observed remote process exit. Production import completes24068ms, reading all
2588147712B off the main thread, one source open/close, and accepting the exact
model hash. Import JUnit passes one method in24.146s. Only passing import
authorizes the owned app's process boundary.

One actual AUTHOR conversation completes353 message callbacks, one DONE and no
SDK error, with observed known conversation/engine closure. Its765-byte response
has SHA256 `47885d1639999fa3de82d4df602889aea68ef09634553d1bdaaa3d0a717c94fa`.
AUTHOR JUnit runs one method in41.164s with one failure. The original v1 proof
refuses generation in41065ms; review/creation IDs and
later creation/reopen artifacts remain unobserved. The sidecar records exactly
one response and identical empty library bytes before/after generation.
Those observed trace closures do not qualify hidden joined callback drain.

The offline CLI runs once, after the SDK owner and guest are known closed.
It completes95ms with exit1, no stderr, and the exact bounded input/response
hashes. The diagnostic supervisor completes587ms/exit0 and validates its
342-byte report against the original refused native envelope. Category
`character_names` denotes the first native name-validity/case-insensitive
uniqueness guard over player plus proposed characters. Independent data-free
analysis confirms all three names are individually valid, but the second of two
proposed NPC names collides with the input player name after lowercase conversion.
Later checks are not thereby qualified. Diagnostic pass always retains
feature_acceptance:false.

The main runtime owner completes597315ms/worker1, known cleanup and complete
capture, with1390B retained stderr. Both2018 tracked and893 compiled input maps
are unchanged. Independent replay verifies all198 measured-SDK2 records and raw
bodies:180 parent plus9 per stream, exact hashes, observer brackets and pinned
server. The180 parent clients comprise60 SDK calls and120 observations; each
stream has2 SDK calls and7 observations. Diagnostic binding
is true, full author binding is false (`ProofRefused/incomplete`). A create-only
duplicate launch requested during a tool timing overlap refuses at mkdir before
SDK/device dispatch; its derived observation is separately retained. It caused
no second model attempt. The first unexecuted runtime helper used overbroad
precollection bounds; corrected V2 enforces exact sidecar limits before copying.
The first unexecuted CLI helper lacked unconditional raw stdout preservation;
V2 preserves that bounded output before checking or parsing it.

The requested owned guest closes823390ms/worker1 with known cleanup/capture,
verified closure and no flush claim. Seven bounded metadata files are copied
unchanged to C:. The final single existing-server observation passes,0 device
calls and0 unrelated-process observations. The existing ADB server is retained;
there is no fresh assertion about an unrelated emulator's presence or identity.

## Preservation and limits

The source bundle at38e50317 is13118623B, SHA256
`e9d5060da5025d611ecc304240134a072f415681722257f6e11e59b0d83b2b43`.
Actual Git verification covers1286 unchanged named refs/1601 bundle heads and all
312 distinct current worktree commit values. Report edits are later commits.
Host recovery independently replays241 originals/copies,242 ZIP members and
244 files/159995002B,0 missing/mismatches. Runtime recovery independently replays
499 originals/copies,500 ZIP members and502 files/4815549B,0 missing/mismatches.
Runtime references the three small host recovery controls rather than copying
the APKs again. Private response, raw evidence and helpers remain local; model
weights, userdata, saves and raw private diagnostics are excluded from public Git.
Earlier failures and sealed recovery sets retain their original status.

| Recovery control | Bytes | SHA256 |
| --- | ---: | --- |
| Host index |143480|`8fc137ec23fe17d22cf432272d3356de5cdc7801d9fc3f14508cb78cc26462a4`|
| Host ZIP |58305260|`d688c3db8d21efc6522a552fb2dd26e6df22ef2b07c670bab6d95a66f0e802de`|
| Host result |958|`de1b8cf34b7a9226c27ee1d5064e76983827c42c5235eba0a121199de38793bf`|
| Host independent replay |5057|`3969c7fdf056c411162bf8134cd4c0d81a61c28f1435e915af3d711dcde631af`|
| Runtime index |293524|`d44bdb12b0c1a84b781e413875598f26135b5575490f69913e3dfcf38964dec4`|
| Runtime ZIP |1211553|`0e3be9eda1558282f2a74acd1c6f56be89d065ac8d6f6acd20cd0c5aa29206b3`|
| Runtime result |968|`a5197aef5493f8f89197f40d5af6e53579eb19164dd1109caf1f6aa9c78faa00`|
| Runtime independent replay |1527|`084562334e4092702a14eed06d439f5019dadfd83158381b37825bc4813b775f`|

The earlier #236 response was not captured: this new response's size or behavior
cannot establish its bytes or retrospectively diagnose its first rule.
This packet does not qualify real-model creation/reopen, narrative quality,
cancellation latency, sustained performance, physical-phone/ARM64 support,
accessibility, joined drain, complete user journeys or release readiness.
The fresh capture-only census has three complete SDK2 clients and no device
rows; no authorized physical identity is established by that capture. Physical
gates remain pending without asserting permanent absence.

Next runnable work: clarify the player/NPC distinction in the bounded AUTHOR
prompt and original fixtures, keeping native validation and
explicit review/create unchanged. Rebuild and admit one fresh owned experiment;
do not repair this captured response or retry it into a passing history.
No merge, release, settings change, global ADB lifecycle operation, unrelated
emulator stop, existing D: removal or private upload was performed.
