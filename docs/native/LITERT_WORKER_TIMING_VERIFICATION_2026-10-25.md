# Role-aware worker timing — 2026-10-25

Refs #9 (M05.05 prerequisite), #5 (M01.04/M01.05 support), PR162 stacked on
unmerged PR161. Execution source: `2ea73aa10f549c70d5117dcdac89413de5fb2fcd`.
Later evidence commits are documentation only. No merge was performed.

## Outcome and changed diagnosis

Fresh API35 x86_64 receipt preflight passes12 checks; full authorized local
model import passes16 checks/1JUnit PASS in90.251s. Real PLAY fails1JUnit test
with fixed `LocalInferenceUncertain` in79.531s. No accepted gift, PLAY proof,
commit request or REOPEN follows. Import success does not establish real play.

The [v2 contract](LITERT_WORKER_TRACE_V2_CONTRACT.md) adds closed role labels,
bounded creation ordinals and monotonic offsets without prompt/output/error
strings. Strict host decoding preserves a failure record before rejecting the
failed runner. It cannot turn failure into admission for another phase.

| Observation | Offset from trace creation |
| --- | ---: |
| Admission entered / returned |105 /10130ms|
| Initialization entered / returned |10618 /14210ms|
| Director creation entered / returned |14669 /16536ms|
| Send entered / returned |16963 /16981ms|
| Done callback returned |59138ms|
| Conversation close known |59155ms|
| Narrator creation entered |59580ms|
| Snapshot; narrator return absent |60098ms|

Director creation spans1867ms, while send-to-DONE spans42175ms. Narrator enters
59580ms after trace construction, near the unchanged60s turn deadline; only518ms
pending is observed at the snapshot. Trace and turn timers have different origins,
so these offsets do not establish an exact remaining turn budget. This run does
**not** establish a long second-factory hang or a
tokenizer-cache stall as the dominant cause. Admission spans10025ms and
initialization3592ms. These are historical recording points, not precise native
durations, jointly atomic SDK state, callback delivery or resource reclamation.

Counts: role admission2/2, creation2/1, send1/1, messages24/24, done1/1,
drain1, conversation close1/1; error/cancel/engine-close/uncertainty notifications
all0. No saturation. Zero uncertainty notifications never clears quarantine.
Owned host termination is separate from cooperative SDK release or guest flush.

All schemas, fresh director/repair/narrator histories,60s turn/5s cleanup,
ownership fencing and Rust canonical-state gates remain unchanged. Resources
are retained before post-return diagnostics; failure category is recorded after
the original fence. Fake-native tests cover D→N, D→D→N and late second creation
without a commit or delivery after quarantine.

## Actual host and artifact checks

The coordinator ran both regular and receipt Gradle profiles with existing
JBR/JDK21/NDK29, offline/no-daemon/max-workers2, SDK/toolchain downloads disabled,
and `localLoreLiteRtVerification`/`localLoreModelSetupVerification=true`:

```text
:app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest
:app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies :app:auditLintAnalyzer
```

Receipt additionally enables ModelVolume/ModelReceipt verification. Original
receipt66441 and regular76271 consumed terminal0; bounded owned jobs completed0
with known cleanup162172/159156ms. Actual receipt397tests/38suites and
regular373tests/36suites have0 failures/errors/skips; lint0errors19/9warnings.
Both dependency/analyzer checks, APP audits and receipt APP/TEST signatures pass.
Actual20 trace JVM tests and22 Python parser tests exercise the same2960B dense
wire fixture. Full `python -B -E -m unittest discover -s scripts/tests -v`:
701PASS/72.246s, original76749 terminal0, owned cleanup73969ms. Targeted41PASS.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Receipt APP |74987568|`83d0709efbd9a72266214d526fadc4f435880ea113b942ddada716e3ea82fda3`|
| Receipt TEST |1974471|`6def97ed744cabb5c98a906a37c976c4a33b6bd0973effcbeda09bef282d7d8a`|
| Regular APP |74954584|`2fccf9f51e6acfa36d346ef1012c64b241a0d7f087c1dfe0be206e6d13c35a9d`|

Worker source LF SHA `271d6af5ac1f946b0cd245ac35f7ba5910a097ec49bebe1776448ff4b7885eec`.
Runtime remains LiteRT-LM0.18.1/source
`bda624851d74be34d4e1f7fac1fc4155939539c7`; Gemma4-E2B publisher
`a790a852d433991c0c0a41c1154cf9b3850300fa`,2588147712B SHA
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
Existing emulator35.3.12/build12990079/API35 GoogleAPIs x86_64 image9,
4096-byte pages,8GiB guest/two vCPUs/12GiB userdata/8GiB SD. No dependency,
model download or supported phone tier selected.

## Exact fresh admission and closure

Private namespaces: `C:/Users/Avery/LocalLore-receipt-timed-` plus
`host`, `environment`, `avd`, `preflight`, `candidate`, then `-20261025`.
The existing public CLI prepare/run and receipt_real_candidate run commands
are those in the [preceding execution](RECEIPT_C_ROOT_EXECUTION_VERIFICATION_2026-10-25.md),
using the new exact proposals/authorizations, never old target adoption.

| Proposal | SHA-256 |
| --- | --- |
| Prepare |`2e2376a31fb3b2b86c39ab01231e56b06570dc80ce706d6d039051c655379f57`|
| Run |`6005113fa5e1de2dfaa6efb7a17d72494d3aa2ee78fc73d7d9d03ee93e9005c7`|
| Preflight |`194324fde74f1a64a92e5bcdb1aa08848c20c4b41b8ad1c9ea07fbdaeee61f9e`|
| Candidate |`c15582461a34f9c8bc3c71915f241cdc6105d646fb932c19133e9e4889256b54`|

Root verifies909 stock/source bindings; reviewer rehashes905nonimage entries
and metadata-checks4 installed images. Token contents are privately hash-compared,
never output or copied; reviewer reads no model/AVD disk bytes.
Prepare16583 terminal0; SDK client0/known5344ms. Run admission verifies
C282497691648B/D47162138624B/available RAM35815112704B, unchanged40GiB C/D
floors and12GiB RAM floor. Owner78972 confirmed live before calls.

Preflight59475 terminal0, owned0/known42687ms;43clients0/known. Proof SHA
`562cd9d340187c767440f510f99e4c30a327f909e4362950548826ef6eb7c2f3`.
79nonweight inputs86689589B match source/archive; SDKfalse/modelsource0.
Candidate83nonweight inputs86695830B match;1478s remained at review, above920s.
Held source FD fully hashes/streams once; IMPORT independently verifies exact
bytes and each verify/import1open/1close. Proof1350B SHA
`19dfb5ff3daa3af2dd344641d8f0f791f5cc7d200b0c725a4b05eb8346bc96d0`.
Transfer-client0 alone is never destination or remote-exit proof.

PLAY transcript8018B SHA
`784f3fad3c19399a01409abd7b17aa171cf233d4151076e9d3e2a375e133020f`;
retained trace2429B SHA
`bed993d98882ecff40273c799c3f84cd02bc5b19ff579aa9bb4176fc16368f76`.
Candidate15475 terminal1; owned2/known294875ms, stdout453/stderr0B;
28clients0/known are distinct from IMPORT PASS/PLAY FAIL. Exact stop consumes
owner78972; retained stop_requested983531ms, closure/cleanup/capturetrue,
worker1, stdout13948/stderr1075B. Recorded owner/worker/launcher identities are
absent and ports free. No guest-flush or SDK-reclamation claim. No post-failure
model/VM-disk reads, forced retry, accepted-model full recheck or reopen was attempted.

## Sealed evidence and next task

No weights/private raw diagnostics/VM disks are uploaded. These private
nonweight inventories are frozen after closure,2012files/345777229B:

| Namespace | Files / bytes | Index SHA-256 |
| --- | --- | --- |
| Host |1649 /171799158|`225a7a2f6d90c7538e3d3e7f6a85ec5ad11a2dff44ccafa062dedea9d084eb53`|
| Environment |25 /391828|`5fa85f5441f20f637ce958f9632b63cf35076147ad7a1396ee7ed45fbcc84a18`|
| Preflight |182 /86795246|`9c877f4e8d529ce752f7e2d791cdbee787e88190bba61057eb08eac26514d6de`|
| Candidate |156 /86790997|`37e84eb251760bd4e9d32d94497cedb2b527a6b60da42ba29ea5c05be57e49e3`|

See [independent review](LITERT_WORKER_TIMING_REVIEW_2026-10-25.md).
M05.05/M01.04/M01.05 remain partial/in_review; accepted real gift/restart and
physical-phone/ARM64/16KiB/quality/sustained qualification remain unverified.
Copy permission persists. Next: separately admitted explicit four-vCPU resource
experiment matching existing four SDK threads; preserve schemas, fresh contexts,
budgets and all gates. Speedup is unproven. Independently audit prompt workload
before considering an SDK fork; no public fresh-history tokenizer-sharing API
or established offline native-fork build was found in the pinned inspected SDK.
