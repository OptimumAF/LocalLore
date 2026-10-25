# Closed SDK callback observations — 2026-10-25

Refs #9 (M05.05), #5 (M01.05 support). [PR170](https://github.com/OptimumAF/LocalLore/pull/170)
is stacked on unmerged [PR169](https://github.com/OptimumAF/LocalLore/pull/169),
base `11d3fc1e994de151799e0747cac27d7655209216`. Root claim6399434479;
final independent review6399531875. Full tasks remain partial/in_review and
unchecked pending complete criteria and owner acceptance. No merge or release.

## Actual result

**56/122 planned checks qualify: three methods pass, Dialogue fails, ordinary
REOPEN is unrun.** The full local model transfer/import and actual ordinary
setup READY/Start → existing LiteRtPlayActivity/current ViewModel → real SDK/Rust
gift pass again. The gift has revision1/receipt1, repairs0/fallbackfalse.

| Phase | Result | Qualified checks | Whole observation |
| --- | --- | ---: | ---: |
| SOURCE_PREFLIGHT |1 PASS|12|485ms proof|
| IMPORT |1 PASS|16|93010ms proof|
| ORDINARY_START |1 PASS|28|82066ms proof|
| ORDINARY_DIALOGUE |1 FAIL|0 of43|51.239s JUnit method|
| ORDINARY_REOPEN |UNRUN|0 of23|None|

The failed method reaches its settled assertion after actual Dialogue Send.
No accepted Dialogue, revision2, post-failure canonical read, unchanged truth
set, completed inspector phase or ordinary-route reopen is qualified. The last
qualified canon is the Start gift. Earlier independently qualified cancellation/
recovery/reopen controls remain dated evidence, not this route's restart result.
Whole-method/proof times include UI, verification and teardown; they are not
generation/cancellation latency, calibrated phone performance or a causal speedup.

## New observation and interpretation

The actual failure transports and the host persists separate status1339 /
`locallore_receipt_callback_v1`, in addition to unchanged worker1337 and send1338.
The new record contains one DIRECTOR request, with no omission or saturation:

| Closed metadata | Actual value |
| --- | ---: |
| Configured context/output caps |4096 /350 tokens|
| Prompt/schema UTF-8 lengths |6811 /425 bytes|
| Worker-validated output |21 accepted chunks /61 UTF-8 bytes|
| DONE /CANCELLED /SDK_JNI /OTHER |0 /0 /1 /0|

Configured caps/byte lengths and accepted output bytes/chunks are **not** native
input/output token usage, complete generated output, EOS, context exhaustion,
output-cap exhaustion or a diagnosed cause. SDK_JNI means the callback received
the pinned SDK exception type. No numeric status, message, class name, cause,
stack, schema/prompt text, path or identifier enters this channel. This packet
does not access or parse Throwable.message, collect logcat or call native token
getters. It does not promise that the third-party SDK itself never logs text.

The independent send record shows argument construction and the public SDK call
both returned: arguments19084→19090ms, call19090→19099ms, snapshot34414ms. The
worker observes one DIRECTOR creation16840→18665ms,21 paired MESSAGE callbacks,
one paired ERROR, one paired CANCEL and UNCERTAIN2; no DONE, drain, known child/
engine close or narrator creation. CANCEL can be cleanup, not a user Cancel
click or cause. Trace clocks/snapshots are independent and not joint lifecycle
state; call-site return proves neither native entry nor async completion.

The original error(Boolean) path runs first. Category notification follows its
callback bookkeeping/fence; category failures cannot replace an original error
callback Throwable. DONE accounting likewise follows the original callback body.
A snapshot can fall between old ERROR_RETURNED and category recording. Missing
category is not OTHER, healthy state or release authority. Original ownership,
quarantine, no-reuse and child-before-parent close rules remain authoritative.

Request observations begin after original validation/admission and before
conversation creation, not proof of SDK send. A final handle attaches only to
its original call. Output accounting follows the existing field, strict UTF-8,
buffer and think-marker checks. Rejected/late chunks earn no accepted bytes;
partial writes from a rejected chunk are not counted. A bounded trace retains
first3 requests with explicit total/overflow, copied immutable snapshots and no
reset/owner replacement. See [wire contract](LITERT_CALLBACK_TRACE_CONTRACT.md)
and [pinned official-source research](LITERT_CALLBACK_RESEARCH_2026-10-25.md).

## Implementation and exact checks

Frozen execution source: `f4af26e50aff2a9a031b03c669ca7007241cff1d`.
Receipt/Rust compilation: `c4f032e8d00f9bb64978b1a389ed9b359b08eda8`;
regular compilation: `d57429ceeb04b1e50ad1d0f221d1ec8ce624b163`.
All221 Android source rows match both builds at execution. Of the broader303
Rust/fixture/script inventory, only one host-test fixture line changed after
receipt/Rust compilation: `owner.methods=1` for the already-completed IMPORT.
All actual Rust/native build inputs match. Admission explicitly records that
exact c4f→d574 line, and the final host-suite source index matches current bytes.
Do not describe all303 receipt inventory rows as unchanged. Later report edits
are documentation only.

- `cargo +1.93.1 fmt --all -- --check` passes.
- `cargo +1.93.1 clippy --locked --offline -p locallore --features host --all-targets -- -D warnings`
  and `cargo +1.93.1 test --locked --offline -p locallore --features host` pass:
 351 core tests,4 explicit historical capture-only ignores,0 failures.
- Corresponding locked/offline Android adapter clippy/test commands use
 `-p locallore-android --features model-provisioning`;90 tests pass,0 ignored.
 Rust owned93344ms/completed0/known cleanup,58201B stdout SHA
 `bc8a1d90fa13cd36c149fed0dc89379c44123805bb2d8be5cbf0ff75e84fdbde`.
- Receipt476 JVM/44 suites and regular418/39 pass,0 failures/errors/skips.
 Lint0errors19/9warnings. The22 new methods include15 pure codec tests and7
 actual-worker/fake-resource tests: exact error identity/ordering, hostile
 accessors, UTF-8/empty chunks, malformed/rejected/late chunks, requested cancel,
 quarantine before category and zero delivery/commit/reuse/unsafe closes.
- Both Gradle profiles run assembleDebug/AndroidTest, cleanTest/testDebugUnitTest,
 lintDebug, auditLiteRtDependencies and auditLintAnalyzer, offline/no-daemon/
 max-workers2, SDK/Java auto-downloadfalse, Kotlin incrementalfalse, lint9.4.1,
 installed JBR/JDK21. Receipt selects LiteRT/setup/volume/receipt; regular LiteRT/
 setup. Owned builds171312/129047ms complete0/known cleanup. Stdout SHAs:
 `a14149e3012478622dd3a08a97b5acb3cd2698cd931a9896b8a536126e1beea4` /
 `29bb1779104d4f5b5e47d1c97f7194fcd25d37e3e9b6efa580c21fe82087b742`.
- Independent decoder16 tests pass. Central combined36 targeted tests pass
 2.943s/owned3390ms0known cleanup;4952B SHA
 `33918ba2af21e834a27930ad691763be0e1a804487f50438f2bf2aa57a977226`.
 Three-channel combinations, raw-first capture, malformed data and persistence
 failure stop before the unchanged runner/proof gate.
- First full806 Python attempt has1ERROR: the new malformed-stream fixture
 omitted its simulated prior IMPORT and refused before dispatch. Original
85422ms/known1/96335B SHA
 `ca6bc7ede00d9b9742184cdcb0020a9aa03d97add8b2244902ae7b4a916b6877`
 is retained. Only that fixture line was corrected; production gates remain.
- Final `python -B -E -m unittest discover -s scripts/tests -v` after APK pins:
 **806 PASS/64.321s**,0 failures/errors/skips; owned65094ms0known cleanup,
95203B SHA `ddd8e904cab38384c8d612703a1a5b093ffa57290e64b7ec927360124d1f8a92`.
- Both actual APP audits and all4 APP/TEST signatures pass,6known0 results.
 New tests are excluded from APP. Both APPs' actual Rust ZIP entries match:
 ARM64 6891152B/`c07df3af727f42b4f07318de02af7249303c63971849283e9cdbcd2776847ded`;
 x86_64 7714856B/`2e5b644146b68f0cb29120a9a495f18c78a7e2567746768029584a8cae5ca867`.
 This is packaging, not ARM execution. Diff checks pass.

| Final artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Receipt APP |75025120|`75639fa0097f0267249780c3c9caec3e81edcbdc59b9bf382cb985eb85583ebb`|
| Receipt TEST |2056611|`a1ccef7bf35f758092af1780e53b5748c733b71cb272427c007867bd7aa7dee5`|
| Regular APP |74975720|`7611df237c4b845e1ec4733c68a4cad949b0c758770e7cae50dc920dcade4b10`|
| Regular TEST |1869531|`f18b6c36631370cbe1825ea09e97bf85384df27c1c6a3d6283c77cdf33a558a1`|

## Admission, failure retention and closure

Standing user authorization covers this local copy to the isolated receipt app.
Gemma4-E2B/a790a852d433991c0c0a41c1154cf9b3850300fa remains2588147712B/SHA
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`;
LiteRT-LM0.18.1/revisionbda624851d74be34d4e1f7fac1fc4155939539c7 is unchanged.
Normalized worker source/provenance is
`d25b7d5a370c15dd858227a3298ff60edaf1559d2684a9279af677e0530d128a`.
No dependency/backend selection, schema/prompt-policy/storage version, profile,
350/220 caps,60s turn/5s cleanup or storage-reserve change.

Fresh emulator35.3.12/build12990079, API35 GoogleAPIs x86_64/image9,4096-byte pages,
8192MiB/4vCPU/12G userdata/8G SD. Root verifies909 installation/initial bindings;
independent review verifies905 nonimage contents plus4SDK-image/blank-SD metadata,
not a second image-content audit. C/D40GiB and host12GiB reserves and20hostCPU
checks pass. Existing generated host Cargo cache is reused; no new data relocation.
Source snapshot1572files/19310999B is exact at execution, with weights excluded.

| Exact admission | SHA256 |
| --- | --- |
| PREPARE |`ab1628e8a5f0c0d765438c6d4a88e1fc1420d7ebd731a00b5afcb158a91807ce`|
| RUN |`39e2221ad5026403044a2e144fc30d34acd963c9929da4ad4b52aa38413dd036`|
| Preflight |`4929eeb190fde6e05b5d0e0a85200f0bc244eb42a9b0332e25c7294d0ab891c9`|
| Candidate |`1ca87c3bcf7df8b5a25670a2703565ebba35234fad2153dbec7c8cab8909e052`|
| Running descriptor |`be8650a855e3c382da10a0f37237020c7a20aba526c9f5977bb6c00f91ef0397`|

The initial candidate builder refuses131bindings before grant/transfer/SDK entry.
Four complete compiled-input indexes are consolidated into one bound JSON,
retaining every path/hash/value and the four originals. Candidate128bindings /
87743209B pass under the unchanged128limit. Preflight127archived bindings /
87709213B remain exact. Its current builder-self binding has one declared drift
because of that later consolidation; all required runtime/source/APK inputs
remain unchanged. Do not claim all127 current preflight bindings still match.
Two earlier coordinator preparation refusals (Python3.9 write_text newline API
and literal HEAD instead of exact commit) occurred before build/SDK dispatch;
their corrections/dispositions are retained without hiding the failures.

Actual entry points are receipt_avd_environment.py prepare/run,
receipt_real_candidate.py run for P, then receipt_ordinary_scene.py run, with
exact proposal/authorization/evidence arguments. Private create-only helper
prefix: `LocalLore-receipt-callback-observation-*-20261025.py`; argv, sources,
results and hashes remain local. SDK/client processes use the Windows Job/stdin
barrier. Quiet output never caused another launch.

P original69270 consumed0/child0/known cleanup+capture47407ms,44closed clients.
Candidate2600 consumed1/child2/known cleanup+capture368078ms,466Bstdout/stderr0,
46closed clients with known shell0/cleanup; a failed JUnit method remains FAIL.
After consuming that terminal, root requests only owned emulator61132 stop.
Original owner consumed0/statusstop_requested705782ms/forced worker1,
known cleanup/capture/preservation closure,11213Bstdout/1090Bstderr. All3tracked
host identities are absent and ports free. Guest flush is not claimed. This is
host preservation closure, not hidden SDK reclamation or disk-integrity proof.
No retry, native token query, post-quarantine model/canonical read or forced commit.

| Retained runtime record | SHA256 |
| --- | --- |
| P proof |`9d9f0cf9a306e94ab5df85beb9f597add3b47f97f8235e276ccbc017221d5767`|
| Import proof |`06460a8a2069017c533c6298aa612d5af06556a5cd1357bf416ef20b4753ab23`|
| Start proof |`db41ee8aead54a952c50e873759c3ceffa07cda5c5ea57dd0600ee0f72e44f59`|
| Gift receipt |`c885026d098ebd56f0b319f5658cad64a95ae88329fad2f2d76eb72c50795447`|
| Receipt array |`2ad6ce36645ed289567f0faedb9c3b770a9246ac51e3bf63bca5ad8f60d5e22b`|
| D raw runner6226B |`8f231ad10c450233a8342cf7f3fa92dbdf8244c1e181cf838dca9a8eae0f77ff`|
| D callback450B |`cf62bdc4b176c7d89f747b2d79bebaaca97ec96e4981f27ddb4ccb60a4efa41e`|
| D send490B |`857b762be338144fd0057b44d83812957b9116b5882071b313dfe8a24ce8d06c`|
| D worker2268B |`1199f4e84ff4d114a841513bcd503262de1a7cce6fccd77222ef920f69dad3d1`|

Sealed prefix `%USERPROFILE%/LocalLore-receipt-callback-observation-` plus
`{host,environment,preflight,candidate}-20261025`. No writes after sealing.
Only17fixed closed owner/config metadata files are copied, excluding disks.

| Root | Indexed files | Bytes | Index SHA256 |
| --- | ---: | ---: | --- |
| host |1740|175541437|`ad4dbf108ce1fe02a9935ef1bcebd28bd4637ef38e78d829d096f3f884e04b84`|
| environment |27|390231|`ef6c4f6e3c88047155961b8319a80b896db8c15f7f462f0f4ba14934eab17431`|
| preflight |234|87839024|`2bc2d710dc93a4dc2c28f2d8aa17940e311e6e82e5e8b97288b70de3fb7dd9d8`|
| candidate |247|87897317|`f9571857508a77bebc2123785207d99ba2755134281720d876e02a9790f96767`|

Total2248indexed files/351668009B, excluding the four index documents themselves.
Models, SDK caches, VM disks and earlier attempts remain local/preserved; no model
download or model/private-diagnostic upload. Independent review is linked from
PR170 and is not owner acceptance.

Next runnable M05.05/M01.05 prerequisite: investigate safe retention of the SDK's
finite native error status without exporting or retaining its private payload.
The pinned JNI supplies an int separately; Kotlin discards that property and
wraps noncancellation errors in a fixed text prefix. A structured upstream seam
versus a bounded prefix-only bridge requires a separately claimed/reviewed
design; **neither is implemented here**. Never parse arbitrary private prose or
query an unknown native owner. Preserve fences/deadlines and then freshly admit
the complete Dialogue/reopen sequence. Physical M01.01, ARM64/16KiB execution,
NPC secrecy/prompt resistance, quality/sustained/thermal/latency, DocumentsUI/
physical touch/IME and broader pressure/privacy/full M05/M06 gates remain open.
