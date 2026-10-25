# Portable Dialogue schema and SDK send observations — 2026-10-25

Refs #9 (M05.01/M05.05), #5 (M01.05). [PR169](https://github.com/OptimumAF/LocalLore/pull/169)
is stacked on unmerged [PR168](https://github.com/OptimumAF/LocalLore/pull/168),
base `2c16e1571de7e3a72bce05028d7ee6f33d75cd27`. Root claim6398576419;
plan discovery6398696909; independent review6398587584. Full tasks stay partial,
in review and unchecked pending their complete criteria and owner acceptance.
No merge, release, access change, model download or private-data/model upload.

Frozen execution source: `e1d6b26797ddfc61772349403345cbd986c255ba`.
Both final Android profiles and corrected Rust checks use source
`8258698398889ebdd5f9ec589b36a22608bcbc9f`. All 218 Android rows and 302 Rust,
fixture and build-script rows match at execution; APK pins are the intervening
host-only change. Later verification/review edits are documents only.

## Actual result

**56 of 122 planned checks qualify: three methods pass, Dialogue fails,
ordinary-route REOPEN is unrun.** The full local model copy/import and actual
ordinary setup READY/Start → exact LiteRtPlayActivity → real Rust-committed gift
pass. Gift revision1/receipt1, repairs0/fallbackfalse, accepted visible transcript,
full model postcheck, guarded transport and actual Activity/ViewModel native
teardown pass. This packet does not complete Dialogue or restart qualification.

| Phase | Result | Qualified checks | Whole observation |
| --- | --- | ---: | ---: |
| SOURCE_PREFLIGHT |1 PASS|12|206ms proof|
| IMPORT |1 PASS|16|94401ms proof|
| ORDINARY_START |1 PASS|28|82875ms proof|
| ORDINARY_DIALOGUE |1 FAIL|0 of43|51.291s JUnit method|
| ORDINARY_REOPEN |UNRUN|0 of23|None|

The failed method reaches its `settled` check after actual Dialogue Send, at
`ReceiptOrdinaryRouteTest.kt:457` in the frozen source. Earlier inspector,
provenance, hidden-belief/unknown-fact searches and no-SDK mechanical refusals
were reached in source order. No final 43-check proof or guards sidecar was
published; reaching that line does not award a completed inspector/Dialogue
phase. No accepted Dialogue, revision2, post-failure canonical count, unchanged
truth set or reopen is claimed. The last qualified canon is the Start gift.

The earlier separately qualified controls in PR164/165/167 remain dated evidence;
they do not establish this ordinary route's unrun restart. Whole-method/proof
times include UI, verification and teardown, not isolated generation latency,
cancellation latency, calibrated phone performance or a causal speedup.

## Compatibility correction and its limits

Pinned-source review found a concrete compatibility counterexample: our Dialogue
audience emitted `uniqueItems`, a known but unimplemented keyword rejected under
LLGuidance1.3.0's strict default. The pinned LiteRT-LM build selects that library.
Array-valued `enum` alternatives are supported by its constant-array compilation.
This is primary-source evidence; the host tests below do not execute LLGuidance.
Sources: [pinned LiteRT build](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/BUILD),
[implemented vocabulary and array constants](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/json/schema.rs),
[keyword checks](https://github.com/guidance-ai/llguidance/blob/v1.3.0/parser/src/json/shared_context.rs).

The replacement covers every eligible nonempty nearby nonplayer audience SET of
size1–4 in canonical sorted order. It preserves existing items/enum and min/max
constraints and literal speech. Raw array permutations narrow to canonical
ordering, while every typed BTreeSet choice remains representable. Incremental
construction accounts for the complete schema's existing 16384-byte limit before
each choice; it returns TooLarge without publishing a truncated enum. Existing
prompt/token admission remains. No listener is dropped and no new smaller cap,
lenient mode, regex, null schema or one-listener special case is introduced.

The engine remains authoritative over proposed bytes, effects, eligibility and
history. Its existing typed BTreeSet normalizes raw duplicate/permuted arrays;
the schema excludes those representations, not a newly introduced engine rule.
Do not claim the unchanged engine independently rejects player-as-listener.
Unknown/dead/noncolocated actors and existing interpretation checks retain their
actual existing behavior. See [representation contract](PORTABLE_DIALOGUE_SCHEMA.md).
Commands/events/storage and current prompt `locallore-play-v2.5` / narration
policy `grounded-prose-v2.2` are unchanged.

The older discarded exception in PR168 remains unidentified. A changed schema
and a later run that advances further are not proof of its exact cause. This
run also fails later, so full runtime compatibility remains unqualified.

## New bounded send record and observed asynchronous error

An independent optional failure-only channel, `locallore_receipt_send_v1` /1338,
records six fixed argument/public-call-site stages. Existing worker v2 and the
ordinary proof/root/selector/check/budget contracts remain intact. No prompt,
schema, message body, exception text/class/stack/cause, path or caller clock enters
the final trace. Production supplies only a final bounded in-memory trace; an
arbitrary observer is available only at the internal SDK-neutral unit seam.

The production adapter constructs typed original arguments, including unchanged
ResponseFormat, before the literal same SDK call. Diagnostic recording errors are
suppressed and the original construction/dispatch Throwable is rethrown unchanged
to the existing failedStart/quarantine path. New THROWN recording is before that
caller catch, not a claim that every diagnostic follows the fence. A malicious
blocking test observer is not a supported production configuration. Original
callback, cancellation, close and ownership logic stays unchanged.

| Independent send v1 observation | Actual Dialogue failure |
| --- | --- |
| ARGUMENTS_ENTERED /RETURNED /THROWN |1 /1 /0; 19067→19074ms|
| ASYNC_CALL_ENTERED /RETURNED /THROWN |1 /1 /0; 19074→19083ms|
| Snapshot |34215ms, no saturation|

The public Kotlin call returned. This marker is at the application call site,
not inside the SDK method body/JNI/native code, and return is not async completion.
The separate worker v2 trace records one DIRECTOR creation, SEND_RETURNED1,
21 paired MESSAGE callbacks, one paired ERROR at34194ms, one paired CANCEL at
34204ms, UNCERTAIN2, and no DONE, drain or known conversation/engine close. No
NARRATOR creation is observed. Message callbacks are **not token counts**.
Trace clocks have independent origins; do not invent cross-trace atomic timing.

Both actual status records are retained and strictly decoded before the unchanged
failed JUnit gate. This exercises the new1338 transport on a real failure. It
differs from PR168's send-wrapper nonreturn, but does not identify context
exhaustion, grammar/EOS, token budget, cancellation, model or native resource cause.
SDK CANCEL may be cleanup after another failure; it is not evidence of a user
Cancel click. Two uncertainty notifications are not two independent SDK errors.

Next runnable prerequisite: bounded callback-error classification and noncontent
request/output accounting on a fresh known owner, preserving quarantine and the
existing deadlines. Verify the pinned SDK API before choosing fields. Its public
error callback exposes Throwable, with cancellation separated and other native
status values embedded in a message-only exception; there is no public numeric
status field. This packet neither parses that message nor exports it. A native
token-count call is a new operation and must not be made after unknown ownership.
No EOS/token/context cause may be inferred from chunk or byte counts alone.
See [pinned callback mapping](https://github.com/google-ai-edge/LiteRT-LM/blob/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt#L623-L628)
and [send-record contract](LITERT_SEND_TRACE_CONTRACT.md).

## Checks actually run

- Rust1.93.1 fmt `--all --check` and Clippy `-D warnings` pass. Core Clippy/test
  use `--locked --offline -p locallore --features host`; Android-adapter Clippy/test
  use `-p locallore-android --features model-provisioning`, Clippy all-targets.
  **351 core PASS, zero failures, four explicit historical-only ignores; 90 adapter
  PASS, zero failures/ignores.** All nine new portable-schema integration tests
  pass, including independent bitmask coverage for1–6 listeners, complete sets
  through size4, grammar exclusions versus typed normalization, actual engine
  receipts/knowledge/replay and budget refusal before provider/canon changes.
  These use synthetic providers, not a native grammar compiler or model.
- Four ignored cases require historical head8/v2.3/v2.4 source captures and are
  not silently skipped new tests. First standalone core Clippy omitted the host
  feature and failed an existing host-only test import before tests. That
  completed101/known-cleanup attempt is preserved (16140ms,1620B,
  `891ed27bf93ddecc39b64e47d6af7631634433722bc907a853a70101d90c4505`).
  Corrected commands use unchanged source and complete0/known cleanup146438ms,
  56765B SHA `faaf81fb8e02c3c7fbcb8969cbfc8262e31b773e6eab86e03167ff30cf921591`.
- New send/controller focused **30 host PASS/2.461s**; owned2734ms/known0,
  stdout3993B SHA `f87a77858c258b346d415fa08d650e6c347bc159c5ca7c43bbc47ba183dea662`.
  Full `python -B -E -m unittest discover -s scripts/tests -v`: **788 PASS/67.578s**,
  zero failures/errors/skips, owned68453ms/known0,93092B SHA
  `04c81f5706ad386bd94cd68eb5d670e1c59e2c56ade75ef62f630095bc5d1630`.
- Receipt **454 JVM tests/42 suites**, regular **396/37**, zero failures/errors/
  skips, lint0errors19/9warnings. The19 new send tests include the real worker and
  owner with four-byte synthetic resources, checking construction/dispatch throw,
  synchronous terminal-then-throw, callback error and throwing observers: no
  deliveries/commits/reuse/unsafe child or parent close. First observer-only build
  also passed454 tests; a test parameter-name warning was fixed before final builds.
- Both final Gradle profiles run assembleDebug/AndroidTest, cleanTest/testDebugUnitTest,
  lintDebug, dependency/analyzer audits offline/no-daemon/max-workers2, no SDK or
  Java auto-download, Kotlin incrementalfalse, lint9.4.1, fixed installed JBR/JDK21.
  Receipt includes LiteRT/setup/volume/receipt verification; regular LiteRT/setup.
  Rust JNI was rebuilt for both ABIs in both profiles. Owned receipt/regular builds
  complete0/known cleanup196328/246547ms. Source rows match at execution.
- Both actual APP `scripts/audit_apk.py` profiles and all four APP/TEST
  `apksigner verify --verbose` checks complete0/known cleanup. New JVM test classes
  cannot leak into APP. Both APPs' extracted Rust library bytes independently
  match for ARM64 and x86_64; this is packaging, not ARM execution. Diff checks pass.

| Final artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Receipt APP |82739330|`32ea3fc7bd04df4cad002fb044a4876c2f3e1658d0d90cc525e1eece3df31c9b`|
| Receipt TEST |2056555|`c94a510a383d8788c5d57375823490dc81182a6f801f994864ca8d32d74e9c12`|
| Regular APP |74959336|`e6003e49dae820802738e82c303672005bf9b0bae5a51fb6f3ffad3eb5206a44`|
| Regular TEST |1869695|`89cec9467a363f3f2fed9e8435c3f42b3430d57efceb080262bdd45780904e99`|

## Admission, capacity and preservation

Standing explicit user consent covers this local copy to the fresh receipt test
package. Model2588147712B/SHA
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`, Gemma4-E2B
publisher `a790a852d433991c0c0a41c1154cf9b3850300fa`, LiteRT-LM0.18.1/revision
`bda624851d74be34d4e1f7fac1fc4155939539c7` remain fixed. Worker provenance changes
to normalized source SHA `aa004c6b32782f1f29606942427ace0494e1c29c78fda44c1c2c431b37b8bdb4`,
paired in Candidate constant/manifest and the Gradle build guard. No new dependency,
model/runtime version or supported production backend/profile is selected.

Fresh emulator35.3.12/build12990079, Android15/API35 Google APIs x86_64 image9,
4096-byte pages,8192MiB/four vCPUs,12G userdata/8GiB SD. Actual CPU count4 is
recorded. Existing60s turn/5s cleanup, P30/I150/S170/D170/R120 seconds,180s transfer,
870s aggregate/900s outer/920s entry/1800s owner and separate120s runner gate remain.
Nominal phase sums are not worst-case completion guarantees. No caps are widened.

Host Rust builds brought D free space below the existing40GiB floor; no emulator
admission was performed while below it. After all check handles were consumed,
native PowerShell moved only1825 generated ignored host-cache files/3998293757B
to a new C cache. Exact paths, no reparse/model-shaped entries, zero live debug
references, C capacity and destination absence were checked. Generated cache files were
moved individually across drives, counts/byte totals checked, then only empty
source directories removed nonrecursively. Failure would preserve both paths.
No cache-content hash claim; SDK/model caches, source, evidence and VM disks were
not moved/deleted. Future host Rust wrapper scopes CARGO_TARGET_DIR to the new cache
parent. C/D restored134935560192/46555893760B; all later fixed-floor admissions pass.
This retains artifacts rather than lowering reserves. Microsoft documents the
[cross-drive file/directory distinction](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/move-item).

At admission, all1563 tracked source files/19203534B matched the then-current source
and snapshot. After documents-only reporting, independent review verifies all1001
non-Markdown rows/13352106B still match frozen execution. Root fully verifies909
stock bindings and initial blank SD; independent review rehashes905 non-image
contents and checks four SDK images/blank SD by metadata only. P/C current and
exclusive archive bindings123/127 (95351891/95358132B) match; weights are excluded
from generic bindings/snapshots. No model/cache/VM image enters sealed inventories.

| Exact admission | SHA256 |
| --- | --- |
| PREPARE |`910f9e4339aa1fd4da43001422637f24d0220333420f52690d3b3bb491dae116`|
| RUN |`9d4ee2a2921ac174c99ac061847a7424019af6a9c0392e8e0336f7be0ff18586`|
| Source preflight |`d0f42bb7a6d20071c16285eb69633f6583666a5b14b2202318456d39e2c62632`|
| Candidate |`f63d0910fc94924c331876f6c0dee3014a95a8a441bb9cf110ba758f6d3ccac1`|
| Running descriptor |`dbcc74564ad0cbd238c422a5ec7ee05aa209c19987d6dbf9ae87743ce734c74d`|

Actual repository entry points are receipt_avd_environment.py prepare/run,
receipt_real_candidate.py run for P, then receipt_ordinary_scene.py run, with exact
proposal/authorization/evidence arguments. Local create-only helper prefix:
`LocalLore-receipt-send-boundary-*-20261025.py`; commands, workers, source indexes,
argv, raw results and hashes are retained. Every SDK/client process is behind the
existing Windows Job/stdin barrier. Quiet output did not cause another dispatch.

## Runtime records and closure

| Record | SHA256 |
| --- | --- |
| Preflight raw |`2e16eec007ccb9a152f1732f295a4916723e2659e5227828ce70ce7f4f627764`|
| Import raw |`ff97909ecfe8e27eea570e7fa68ef25b6dd99f5cdfac8cf5764e115d09004fc1`|
| Start raw |`77af7deaebb8cdf48dab8a174906eb8d4f0ff78521978621d23981790655d4a2`|
| Start worker raw |`142c510112a5f0bcc178467ff7efdccd26c0a74ab31cbe97c835cb9c61c65e96`|
| Gift receipt |`e828ebbb70f19466c99c8a162a800bcdf1df3044bdd248f66aa397f6fd540014`|
| Accepted receipt array |`2f46d3b813c9f5e91d845a93d38c0b713944bfc90e96581e7a642ebfdd289909`|
| Dialogue runner raw |`69d38b407614fe9d71a2d6d1fcf71a1c3b44277c6141b24323d659069e5b5919`|
| Parsed failure worker |`46e5f624744a5fce452b3d37801c98ac2ca0b4faa438db75dcac7564e6054c51`|
| Parsed failure send |`349f35de9a169fc6441506b588d241efa300fdedf87b9664c309b0fd47141563`|

Original P driver terminal0/child0/known cleanup/capture43140ms. All44 P clients
and46 candidate clients retain matching stdout/status/known cleanup. Candidate
original terminal1/inner2,373187ms,466B stdout/stderr0, known cleanup/capture.
Dialogue command46 is shell0/known cleanup with5847B runner output; JUnit FAIL
cannot become PASS because the shell exited0. No retry, post-quarantine model/
canonical read, forced commit or later dispatch occurred.

Only after consuming that terminal did root request the exact owned emulator stop.
Original owner terminal0, stop_requested760047ms, worker1 from requested job drain,
known cleanup/capture/preservation closure. Retained11234B stdout/1083B stderr;
all three tracked host identities absent and ports free. Guest flush is false.
This is host ownership/preservation closure, not hidden SDK reclamation, virtual
disk integrity or power-loss qualification. Model, cache and VM disks are retained.

Sealed evidence prefix: `%USERPROFILE%/LocalLore-receipt-send-boundary-` plus
`{host,environment,preflight,candidate}-20261025`. No writes after sealing.
Only17 fixed owner/config metadata files are copied after closure, excluding disks.

| Root | Files | Bytes | Inventory SHA256 |
| --- | ---: | ---: | --- |
| host |1777|260185030|`b483041d352ffe87e18c521f972b026bc420688b5dd687e25a14866e5895879e`|
| environment |27|390063|`c416f047fb572ae691ee47d2f7a91a16a451efd70dd1bd5b259e77d407be1c2c`|
| preflight |230|95480004|`9f9a999997bbf71cd9ccc40bf02ccdb50b4f553521f5191d085b7cf773b3a628`|
| candidate |245|95508939|`15df00ab75f7a6ee7f910ba960d90218ddb5b868209222b374e0982b2621cfb7`|

Total2279 files/451564036B, independently rehashed with zero mismatches.
[Independent review](LITERT_SEND_BOUNDARY_REVIEW_2026-10-25.md) is technical review,
not owner acceptance. Full Dialogue/reopen, physical M01.01/reference phone,
ARM64 execution/16KiB, NPC secrecy/prompt resistance, quality/sustained/thermal/
latency, DocumentsUI/physical touch/IME and broader pressure/privacy gates remain
unqualified. Full M05/M06 exit gates have not passed.
