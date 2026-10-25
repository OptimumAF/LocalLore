# Wrapper-declared SDK status — 2026-10-25

Refs #9 (M05.05), #5 (M01.05 support). [PR171](https://github.com/OptimumAF/LocalLore/pull/171)
is stacked on unmerged [PR170](https://github.com/OptimumAF/LocalLore/pull/170),
base `3c808389992f8ddb1f071daf6d2ccbb94d6c8a05`. Root claim6399899218;
independent final review6399987596. Full tasks remain partial/in_review and
unchecked pending complete criteria and owner acceptance. No merge or release.

## Actual outcome

**56/122 checks qualify: three selected methods pass, Dialogue fails, ordinary
REOPEN is unrun.** Full local transfer/import and the existing ordinary setup
READY/Start → LiteRtPlayActivity/current ViewModel → real SDK/Rust gift pass.
The gift is revision1/receipt1, repairs0/fallbackfalse. No accepted Dialogue,
revision2, post-failure canonical read, completed inspector phase or ordinary
restart is qualified. The last qualified canon is the Start gift.

| Phase | Result | Qualified checks | Whole observation |
| --- | --- | ---: | ---: |
| SOURCE_PREFLIGHT |1 PASS|12|324ms proof|
| IMPORT |1 PASS|16|97082ms proof|
| ORDINARY_START |1 PASS|28|89295ms proof|
| ORDINARY_DIALOGUE |1 FAIL|0 of43|53.466s JUnit method|
| ORDINARY_REOPEN |UNRUN|0 of23|None|

The actual failure transports and persists new status1340 /
`locallore_receipt_status_v1`: **CODE_13=1**, all other declared codes and
UNRECOGNIZED=0, no saturation. Code13 is the canonical Abseil INTERNAL value
([official header](https://github.com/abseil/abseil-cpp/blob/master/absl/status/status.h),
[code semantics](https://abseil.io/docs/cpp/guides/status-codes)). This narrows
the SDK wrapper's declared error family; it does not identify its originating
component or root cause. Several native operations can return InternalError.
No grammar, model, thinking, EOS, truncation, context, capacity or cancellation
diagnosis is established, and no limit was changed on that assumption.

The independent callback record has one DIRECTOR, configured context4096/output350,
prompt6811B/schema425B,15 worker-validated chunks/58 UTF-8 bytes, SDK_JNI1,
DONE/CANCELLED/OTHER0, no omission or saturation. These are application byte
lengths, configured caps and validated chunks, not native input/output-token
usage or complete generated output. Earlier21chunk/61byte findings remain dated
evidence; the changed sample does not establish a causal effect of diagnostics.

Send arguments return19418→19424ms; public SDK call returns19424→19434ms;
send snapshot35787ms. Worker creation DIRECTOR16982→18925ms, snapshot35785ms;
15 paired MESSAGE callbacks, one paired ERROR, one paired CANCEL, UNCERTAIN2;
no DONE, drain, known child/engine close or narrator creation. CANCEL may be
cleanup, not a user click or cause. Independent clocks/snapshots are not joint
lifecycle state. Public-call return proves neither native entry nor completion.
Whole-method/proof times include UI, verification and teardown; they are not
isolated generation/cancellation latency, phone performance or causal speedup.

## Explicit new privacy boundary

Unlike the historical no-message-access PR170 packet, this separately claimed
design retrieves the **existing message reference** only after identifying the
pinned final LiteRtLmJniException type. It compares only17 complete fixed literal
prefixes `Status Code: n. Message: ` for n0..16, within an expected header window
of at most26 UTF-16 code units. For a well-formed pinned wrapper it examines no
suffix characters. A malformed or locally constructed message can contain
private characters inside that window; none are retained or exported. There is
no suffix traversal, copying, regex, integer parsing, trim, split, substring, cause,
stack, class-name rendering, logcat or native getter is used. Foreign/wrapped/
cancellation Throwables are not queried for a message and become UNRECOGNIZED.
Malformed, signed, padded or unknown prefixes also become UNRECOGNIZED.

Only the explicit receipt owner receives the optional final in-memory trace.
Null/default/regular construction skips classification and message retrieval.
The original error(Boolean) path/fence runs first, the old category follows,
and the optional new status records last in a suppressed finally. Original
callback exceptions retain exact identity despite diagnostic failures. No
new status decides admission, cancellation acknowledgement, commit or release.

This is **wrapper-declared metadata**, not a structured numeric SDK API or
authenticated native status. An app can construct the final SDK exception with
a spoofed valid prefix, including0/1. Those observations are not success or a
known cancellation. Missing or UNRECOGNIZED observations never imply health.
Counters are historical, not complete callback order or future-callback immunity.
The fixed18counter codec owns no private Strings, exceptions, paths, clocks,
request IDs, callbacks or filesystem resources. Snapshots copy immutable maps,
sets and entries; count overflow alone sets sticky saturation. Dense fixture
532B JSON/584B prefixed fits2048B, SHA
`14007fc5a07f286147fdae2350af4d203b2470d7a9e674d95645dd10e1b574b3`.

The bridge avoids a native SDK fork/rebuild while providing this bounded
diagnostic. A future SDK format change safely becomes UNRECOGNIZED and needs
new compatibility review. It does not promise the third-party SDK never logs
text. See [contract](LITERT_STATUS_TRACE_CONTRACT.md) and
[pinned-source/license/alternative review](LITERT_STATUS_RESEARCH_2026-10-25.md).
Old1337/1338/1339 formats and the122-check positive proof remain unchanged.
The host preserves raw first, then separate1340 JSON before old channels and
the original runner/proof refusal; diagnostics cannot promote a failed test.

## Commands and actual checks

Compile source: `ba2e4830ed2d74f215646cc8db82962bde0b05bd` for receipt, regular
and Rust. Frozen execution after host-only APK pins:
`81a6f43e41618251271d188c486fcd325915ef4d`. All224Android rows/2502145B and
all304Rust/fixture/script rows/4795331B match at execution, without exceptions.
Complete source snapshot1581files/19399110B is exact. Later documentation changes
are Markdown only.

| Actual gate | Result |
| --- | --- |
| Rust fmt/clippy | PASS, locked/offline, warnings denied |
| Core Rust |351PASS/4explicit historical capture-only ignores/0fail|
| Android adapter Rust |90PASS/0ignored/0fail|
| Receipt JVM/lint |496tests/46suites/0F/E/S;0errors19warnings|
| Regular JVM/lint |438tests/41suites/0F/E/S;0errors9warnings|
| Independent status decoder |13PASS/0.082s|
| Central combined host cases |35PASS/9.561s|
| Initial full Python |821PASS/263.564s|
| Final Python after pins |821PASS/130.852s|
| Actual APP audits/signatures |BothAPPaudits+all4APP/TESTsignatures PASS|

Rust1.93.1 commands: `cargo +1.93.1 fmt --all -- --check`;
`cargo +1.93.1 clippy --locked --offline -p locallore --features host --all-targets -- -D warnings`;
`cargo +1.93.1 test --locked --offline -p locallore --features host`;
corresponding clippy/test with `-p locallore-android --features model-provisioning`.
The4ignores explicitly require historical capture sources, not skipped new tests.

Both Gradle profiles run assembleDebug/AndroidTest, cleanTest/testDebugUnitTest,
lintDebug, auditLiteRtDependencies and auditLintAnalyzer offline/no-daemon/
max-workers2, Kotlin incrementalfalse, SDK/Java auto-downloadfalse, lint9.4.1,
installed JBR/JDK21. Receipt selects LiteRT/setup/volume/receipt; regular LiteRT/
setup. The20new JVM methods include15codec/prefix tests and5actual-worker/
fake-resource integrations: every declared code plus unknown preserves original
fencing and zero delivery/commit/reuse/unsafe close; requested cancellation still
drains/closes, and late declared0 cannot restore a closed call's safety.

Python: `python -B -E -m unittest discover -s scripts/tests -v`; targeted runs
select `scripts.tests.test_receipt_ordinary_scene` and
`scripts.tests.test_litert_status_trace`. Four-channel combinations, malformed
data and persistence failures retain actual client raw and stop before proof.
All verification runs above pass; the real Dialogue failure is separate.

| Owned completed0/known cleanup | Elapsed ms | Stdout bytes | SHA256 |
| --- | ---: | ---: | --- |
| Rust |133328|58202|`888282ab8b2947075772fa6b14840cd537871bfb3ac137c39627aeefa16ebc42`|
| Receipt build |309750|9800|`85508698f946b2bcc4ce48f110808f17cf93a78d8fad60d5e9db82c2409045d9`|
| Regular build |143718|9113|`57ac6251e4324a4bc12a2afbb4f04d4250dea0095a8ce1a7f4c914444066610e`|
| Targeted35 |10031|4773|`178332226a362cfd2b592743a7fcbbd332f595e9d3d3e6315e3bd298f16da310`|
| Initial821 |264547|96872|`e00b172e1921d15ec200039a985021f099cc4a65f3907a7a73369e2e24b00402`|
| Final821 |131641|96872|`b5dc22e8c3c5779469552fc3cd025091a90a235abc2e2d3c1e95afbcc9d7eb8b`|

| Final artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Receipt APP |75041504|`ca9692fcd700e0307d9269827f6b4906c28d2c411069d8a4200ab55e85989709`|
| Receipt TEST |2056615|`e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d`|
| Regular APP |74975720|`6dba83bffc50327547dd64dfef8ce8546140a6891103a88d5b7d31dcffacc014`|
| Regular TEST |1869719|`8c14c03502faee7661b58a6862c5b35e9fec6e6371e40b9c2718daadd56ad1e5`|

APP audits exclude the new test classes. Actual Rust ZIP entries match between
both APPs: ARM64 6891152B/SHA
`c07df3af727f42b4f07318de02af7249303c63971849283e9cdbcd2776847ded`;
x86_64 7714856B/SHA
`2e5b644146b68f0cb29120a9a495f18c78a7e2567746768029584a8cae5ca867`.
This is packaging, not ARM execution. Diff checks pass. No dependency or model
download/selection, schema/prompt-policy/storage/profile/cap/deadline change.

## Exact admission and preservation

Standing user authorization covers local copy to the isolated receipt app.
Gemma4-E2B/a790a852d433991c0c0a41c1154cf9b3850300fa remains2588147712B/SHA
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`;
LiteRT-LM0.18.1/revisionbda624851d74be34d4e1f7fac1fc4155939539c7 unchanged.
Normalized worker/provenance SHA is
`c014b6e2df10c39120e4590efcb581185e6ed415c979b0f1a67698e9e72dded9`.
Fresh emulator35.3.12/build12990079/API35 GoogleAPIs x86_64/image9/4096-byte pages,
8192MiB/4vCPU/12Guserdata/8GSD. Host20logicalCPU, C/D40GiB and host12GiB
reserves pass. Root checks909installation/initial bindings; reviewer checks905
nonimage contents plus4SDK-image/blank-SD metadata, not image-content hashes.

| Admission | SHA256 |
| --- | --- |
| PREPARE |`8a6be10658dccec214672c17c4d0c80c9a622ed3cb13736d83177169063788ea`|
| RUN |`5848cde1d01921306cbd317a2028f738a8c12759bdea0706c93461efdabdc38d`|
| Preflight |`2417c7e9b8b3f2992d6eb4ebab50ad8c0e93b8278569c28c3f9ce6fe139a743f`|
| Candidate |`98c277849f03c9a2427a0cefc5d21f4d0e9bee288da4eb4d776dae0d9c42e7b9`|
| Running |`3cd58bbe86c9bb78cf824021fc8740ec36879df78c69a3cb6cae553f7e34cb22`|

Before BOTH builders freeze,23complete selected host-acceptance JSON originals
are bundled with every path/raw SHA/full parsed value; all originals remain.
Runtime SOURCE_FILES, raw logs, XML and APKs remain individual bindings. P111 /
87875411B and C115/87881648B fit unchanged128cap. Both current/frozen archives,
builder bytes and bundle remain exact: no prior-packet self-helper drift or
binding-cap relaxation. SDK/client processes retain the Windows Job/stdin barrier.
Entry points: receipt_avd_environment.py prepare/run, receipt_real_candidate.py
run for P, then receipt_ordinary_scene.py run with exact proposal/authorization/
evidence arguments. Private helper prefix `LocalLore-receipt-declared-status-*-20261025.py`;
sources, argv and original raw/results are retained. Quiet output caused no retry.

P original37231 consumed0/child0/known cleanup+capture52016ms,44closed clients.
C original8077 consumed1/child2/known cleanup+capture386578ms,466Bstdout/stderr0,
46closed clients with known shell0/cleanup. A failed JUnit remains FAIL.
Only after consuming C did root stop exact owner16905. Original owner consumed0,
stop_requested744750ms/forcedworker1, known cleanup/capture/preservation closure,
15803Bstdout/1914Bstderr. All3tracked host identities are absent/ports free.
Guest flush is not claimed. This is host closure, not hidden SDK reclamation,
disk integrity or power-loss qualification. A later review lease correctly
refuses owner_stopped; it is not an unexplained loss or permission to retry.
No post-quarantine model/canonical read, native getter, forced commit or reuse.

| Retained runtime record | SHA256 |
| --- | --- |
| P proof |`e7e604ea0256d79948213837df2a4cf4a301d43f2d5cef02f52cc86eced63021`|
| I proof |`4ff64218c1b62d623499f80d85f8e91b09e14404ee7ab12d9877694bf21227d4`|
| Start proof |`6c404b5c4a64e939e9e9334edf54c45706f7c7318f9af76f51bd44bfa2de3d9c`|
| Gift |`375fb6d1c02712d5e623141dbda131bc17a44b98985fd25abda4d9635c8f1ce4`|
| Receipt array |`ac8e626e0b13625788147200e174ab5ad9b26a016e2dfac01474dacb21499ae0`|
| D runner6565B |`7661748caf623d2be0defea79a6570558d5819b732098548af22ac8420268e95`|
| D status375B |`28b67d53aa4e95557eb954ab737e1a241008ad789c8b59f8c6bf89e7239f0d76`|
| D callback450B |`e7240017b9f4a64f8abf25401b6812cba22ca9b01e5460a255024ee5d870ac10`|
| D send490B |`8e2ef3251e73baeb52086e27aa1fe3f3d16bdb21485444800a6a713bae78df91`|
| D worker2268B |`ee9acb80f4fb2c4bfcdb4664a1c9c7e0d930494a59fe7ef3ef4b839f9ac6a4b2`|

Sealed roots use `%USERPROFILE%/LocalLore-receipt-declared-status-` plus
`{host,environment,preflight,candidate}-20261025`; no writes after sealing.
Only17fixed closed owner/config metadata files are copied, excluding disks.

| Root | Indexed files | Bytes | Index SHA256 |
| --- | ---: | ---: | --- |
| host |1751|176139937|`75285d6be0d800f71dbe564a7cf134e1f904c8a3142144a2181abbee85a568d0`|
| environment |27|395507|`b115111a5296f2f433077a146a4be49b84a4145a253e611955ee518097c14301`|
| preflight |218|87999733|`15484b82433130602e819b8cdd3731ee104e264c43ccd441fe2239463bdc74f1`|
| candidate |235|88031371|`d932b47aeb7bd3fc8d88f06df76d892155495382a1827938c7c93b45cf93cb2e`|

Total2231indexed files/352566548B, excluding4index documents, independently exact.
Models, SDK caches, VM disks, earlier attempts and generated Cargo cache are
preserved locally. No private diagnostic/story/model upload, merge or release.
Independent review is evidence, not owner acceptance.

## Next runnable task and remaining gates

Read-only source investigation6400105962/release6400171918 finds explicit support
for array-valued enum/items/min/max intersection in LLGuidance1.3.0; it establishes
no compiler counterexample. Pinned false/0 thinking configuration reaches
rendering/decode, but embedded-template behavior and native token usage remain
unobserved. Those findings do not diagnose this Internal error.

Next claim M05.01/M05.05/M01.05 host-only grammar oracle: verify/pin official
LLGuidance1.3.0 dev-tool dependencies/licenses, compile the exact generated schema,
then exercise byte-level masks/full acceptance/EOS with original n1–6 audiences
and malformed/duplicate/foreign/empty/>4 controls, preserving documented property
order/outer-whitespace limits. No model/tokenizer file or SDK owner is needed;
that oracle would not prove the actual Gemma tokenizer/SDK path. Dependencies and
oracle are **not introduced here**. Use actual results to choose a fix before
another admitted runtime; do not guess a larger budget or upgrade.

Complete Dialogue/reopen, physical M01.01/reference phone, ARM64/16KiB execution,
NPC secrecy/prompt resistance/quality, sustained/thermal/latency, DocumentsUI/
physical touch/IME and broader privacy/pressure/full M05/M06 gates remain open.
