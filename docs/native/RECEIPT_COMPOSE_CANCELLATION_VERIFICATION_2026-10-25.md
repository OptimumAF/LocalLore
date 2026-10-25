# Real Compose cancellation, recovery and reopen — 2026-10-25

Refs #9 (M05.05), #5 (M01.05). [PR167](https://github.com/OptimumAF/LocalLore/pull/167)
is stacked on unmerged PR165/164/162/161/160. Corrected execution source:
`b1e4437d3e6aaa2a97ec9c579fe83e1d5f88cd43`; Android compilation source:
`8db49a32f3701c99951185df61e93389f26a77de`. Later verification/review commits
are documentation only. No merge, release, model download or upload.

## Actual result and scope

The corrected fresh emulator passes **95 protocol checks across five selected
JUnit methods**. It imports the full local model, clicks production Compose
New story/Send/Cancel, preserves revision0/no receipt/the player's potion, then
in another app process sends one real local gift and commits revision1/one
receipt. A third process displays the accepted player/narrator transcript and
reopens that same receipt without SDK inference. Recovery repairs0/fallbackfalse.

The receipt-only, nonexported `ReceiptComposeCancellationActivity` overrides only
the production `MainActivity` transport factory to attach the real candidate and
an instance-owned trace. MainActivity constructs its normal `ShellViewModel`,
gateway, screen and callbacks. Setup/admission occur off Main before manual
launch. No test gateway create/Send/Cancel/commit call substitutes for a UI
action; no SDK callback/result/delay or replacement ViewModel is injected.
The ordinary model-setup Start entry route and DocumentsUI remain separate gates.

| Phase | Checks | Whole proof observation | SDK invoked | Result |
| --- | ---: | ---: | --- | --- |
| Source preflight |12/12|197ms|false|Tiny source and fresh capacity |
| Full import |16/16|96632ms|false|Verify/import each opened/closed once;2588147712B |
| UI_CANCEL |26/26|76535ms|true|Actual buttons; unchanged canonical revision0 |
| UI_RECOVER |24/24|66054ms|true|Fresh process; real gift, revision1/receipt1 |
| UI_REOPEN |17/17|18283ms|false|Another process; same receipt and visible transcript |

These include setup, UI scrolling/synchronization, model verification and
teardown. They are **not cancellation latency, isolated generation, first final
response latency or calibrated phone performance**. Trace/test clocks have
different origins. Neither a causal resource speedup nor native-active timing
at the exact click is inferred from a historical public callback sample.

UI_CANCEL samples a returned DIRECTOR message with no observed terminal before
the actual click, while the Activity remains RESUMED and the ViewModel preparing.
Its settled success notice and accepted history must appear before disposal,
with busy/preparing/checkingCancellation/recoveryRequired all false. The real
ViewModel cancels its private caller Job; this control uses the actual public
SDK cancel/drain/known-close trace and production borrowable-owner guard rather
than transplanting the earlier API test's original-Deferred rejection oracle.
Activity.onStop/disposal cannot earn those earlier UI checks.

The accepted model is rechecked and the owner guard repeated before close;
a fresh post-close trace must still satisfy the predicates. Recovery uses the
production ViewModel's automatic commit: its full model rehash is **after that
commit**, not a new test-controlled precommit hash gate. Existing runtime
admission/worker guards remain unchanged. Reopen has no worker events or Send/
Cancel action. These are known public close gates and historical observations,
not hidden-native reclamation, atomic native-state reads or future-callback immunity.

## Initial partial run and correction

Initial execution `89a335df2480bc6041c652c46b8085bb23a2bd1b` passed preflight12,
import16/94346ms and real UI_CANCEL26/75713ms, then UI_RECOVER failed its selected
method after52.435s with the fixed error `Accepted transcript is not visible`.
Visible accepted notice/revision1/spent potion/two message state had passed;
canonical receipt inspection, posthash proof and reopen had not. No recovery
proof or restart was emitted/dispatched. Its SDK trace records returned DIRECTOR/
NARRATOR, paired DONE2, drain2, known conversation/engine close and UNCERTAIN0;
that does not qualify the unperformed canonical/reopen checks.

The old helper searched globally by message text. The composer intentionally
retains the player's draft after acceptance, so the accepted player Text and
editable input can match the same selector. The [Compose API](https://developer.android.com/reference/kotlin/androidx/compose/ui/test/package-summary)
includes editable text in text matching. The helper's broad catch discarded
whether this run failed through ambiguity, absence or geometry. **The actual
discarded failure cause remains unproven; a passing correction does not diagnose it.**

Root commit6b0f4443 adds row/body semantic tags from existing accepted message
IDs; it changes no contents, IDs, lazy keys, callbacks or provider routing.
Author443ba8ef, integratedb8721f75, uses the exact body ID for both scroll and
lookup, requires one body and exact accepted Text, and preserves the same
clipped visibility check. Fixed LOOKUP/MISSING/DUPLICATE/SCROLL/TEXT/VISIBILITY
categories preserve privacy. No input clearing, first/last/text fallback or
visibility relaxation is used. The missing semantics extension import was
caught before build and added8db49a32. Corrected APP/TEST DEX tags/diagnostic
categories and source hashes were independently checked before guest execution.

The initial host grant40135 also refused `host_capacity` **before authorization
creation or guest dispatch**. Its failing resource values were not captured;
later passing facts do not establish a cause. The unchanged, unconsumed proposal
was rechecked and its first actual preflight passed. This was not an SDK-phase
retry. Both that refusal and the subsequent UI failure are retained.

Initial candidate60146 consumed terminal1: worker2, known cleanup360640ms,
stdout471/stderr0B,47 clients/three candidate methods attempted. Failure client47
has9452B raw stdout SHA
`61d102d69907deaf5c09b81a72b319ca5f174841f5cd7bff0e5f62bfc2aaafb7`.
After that terminal, exact stop was requested; owner29812 consumed terminal0,
stop_requested758687ms, capture/cleanup/closuretrue, worker1, stdout11256/
stderr1090B. Tracked host PIDs were absent and ports free. This target/model/cache
was retained; the corrected flow used a separately admitted fresh namespace.

## Corrected source, host and artifact checks

Both profiles compiled source8db49a32. All213 Android source rows still match
executionB1; the execution delta is only Python APK-pin metadata. The final
1546-file/18951108B source snapshot independently matched frozen B1 execution
and current inputs at admission; later changes are documentation only.

Actual offline Gradle commands for receipt and regular profiles:

```text
:app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest
:app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies :app:auditLintAnalyzer
```

Flags retain `--offline --no-daemon --console=plain --max-workers=2`,
`android.builder.sdkDownload=false`, `kotlin.incremental=false`, lint9.4.1,
`org.gradle.java.installations.auto-download=false`, explicit JDK21 and the
exclusive `.gradle-litert-worker` cache. Both enable LiteRT/model setup; receipt
also enables model-volume/model-receipt verification. No dependency was added.
Existing JBR/JDK21/NDK29 and both packaged native ABIs were retained; ARM64 was
not executed.

Receipt20226 consumed terminal0, known151828ms: **423 JVM tests/40 suites**,
0 failures/errors/skips, lint0 errors/19 warnings. Regular83480 terminal0,
known132813ms: **377/36**,0 failures/errors/skips, lint0 errors/9 warnings.
Dependency/analyzer tasks, actual APP audits and both profiles' APP/TEST
signatures pass. The eleven new pure codec methods are included in423.

`python -B -E -m unittest discover -s scripts/tests -v`: **758PASS/77.453s**,
original46928 consumed terminal0, owned0/known78750ms. Raw89623B SHA
`a41cd488ba3a79dcfbd7067d81480313615eebd07d97a9d98fba721f2fb080ab`.
The new controller's16 targeted methods also passed independently; the existing
APK audit's25 methods include the new exact private activity/class boundaries
and forbidden test packaging cases. Earlier build/test records are retained.

| Final audited artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Receipt APP |75003984|`501d3ddf86430f6c0ddd19f0e88a94e189656fa5c243d3a0657458e4dd4520df`|
| Receipt TEST |2025483|`7075dc1104f95e0e58e64d9e01c9bfa7007e4b4ffc4d942cd52246ccf99cbfd6`|
| Regular APP |74954584|`7a457be8af1fa7562c68ad00504a228f7e0eee925ec48e30ef7b537e32acd281`|

## Exact corrected admission and closure

Corrected private prefix: `C:/Users/Avery/LocalLore-receipt-compose-identity-`,
then `host`, `environment`, `avd`, `preflight`, `candidate`, followed by `-20261025`.
Initial prefix substitutes `compose-cancellation-` for `compose-identity-`.
No weights, VM disks or raw private diagnostics are uploaded.

| Corrected proposal | SHA-256 |
| --- | --- |
| Prepare |`179b9de11ae275707893e59652a77a9a19d942489393870d887fc9cd2709dadf`|
| Run |`57b04e770cdfc7df26e4469cfcf2994580ba8d25ae734879f28357ed2368d363`|
| Preflight |`e43b2ea32da2f8e49cece2a0c812bec93fe03590744c537605b884a931c39045`|
| Candidate |`0442cba7544b8c97a75dfe88d559ee58c61976f06585b9d013fe4cc9ebc223ad`|

Root rechecks909 source/stock bindings and initial disk; reviewer independently
hashes905 nonimage bindings and checks four installed SDK images by metadata
only. Registry/token metadata checks pass without token disclosure. No operations
target old devices/caches. SDK prepare70618 terminal0, client0/known5375ms;
prepared/cleanup/closuretrue. Read-only plan-run88369 terminal0. Preflight101
nonweight bindings/87135191B and candidate105/87141432B match current/exclusive
archives. Model bytes are excluded from generic bindings and archives; the held
source FD is hashed/streamed once under the exact separate copy/SDK grant.

Descriptor SHA
`6d98efd743e434d3fff433b2e9536886d75d6c115f8487812ee27b0b87ee4f0c`.
Candidate grant observed1467s remaining and host C170889592832B/D46510141440B,
available RAM28491952128B/20 logical CPUs, above unchanged40GiB/12GiB floors.
Preflight94488 terminal0, child0/known41297ms,44 known clients/one selected PASS.
Actual candidate99962 consumed terminal0, child0/known409640ms,
stdout422/stderr0B/capturetrue:77 known clients/four selected PASS, no failure
worker record, statusobserved/failurenull/clients_cleaned+owner_livetrue.

Only after that terminal did root request exact stop. Original owner89350
consumed terminal0: stop_requested860718ms, capture/cleanup/closuretrue,
worker1 from requested job drain, stdout15845/stderr1086B. All three tracked
host PIDs are absent and ports free. Guest flush, power loss and hidden-native
reclamation are not inferred.

Configuration remains emulator35.3.12/build12990079, API35 GoogleAPIs x86_64
image9/4096-byte pages, guest8GiB/four CPUs, userdata12GiB/SD8GiB.
LiteRT-LM0.18.1/source`bda624851d74be34d4e1f7fac1fc4155939539c7`;
Gemma4-E2B publisher`a790a852d433991c0c0a41c1154cf9b3850300fa`,2588147712B SHA
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
Model/schema/fresh contexts/token budgets/worker threads remain unchanged;
60s turn/5s cleanup,870s aggregate/900s outer/920s entry/1800s owner and the
separate conservative120s selected-runner gate remain. No production-supported
backend/profile selection.

## Proofs, seals and remaining work

| Corrected raw proof | SHA-256 |
| --- | --- |
| Preflight |`7aff7d2edd86c8042a3a8aca713bbc1cf0ad376534dd685239cca2bce7b61934`|
| Import |`dea205e4208b5899ed62d9de47ae44f1c173ed593707e7a5b22630041da87d7e`|
| UI_CANCEL |`ed91a0c7e93d44925fbbf4325242e87f4d8fd9b9b508825d2597bac14d243a15`|
| UI_RECOVER |`177992002498213959598cbb31a11898d62f277a8d9efec208bd8e352db04c12`|
| UI_REOPEN |`70c5938d0315d113a445d8edc450f50b371dd729e234e3ad0818038b82db2fbb`|

Recovery/reopen receipt SHA agrees:
`869cca72512c85edd49dda53c27ce6d813b5fa4c38fa96eddf45e1c02a849145`.
Raw sample/final cancellation/recovery trace SHA values respectively:
`515576d12b157f8f6e9448b9fcaef964f619fb3181449e78fa06f038b1345103`,
`54d40ea0102f1f0fda4d2c30d1a6a9b7096e7c73399835d0626dac23ad381dd0`,
`04cd416444bb95e7462b169a2d95e18390059c75ad900608afdc1de012fea83c`.
Pretty JSON hashes differ from these bound raw sidecars.

Corrected2207 nonweight files/349178336B independently match; initial2139/
352365338B also match. Combined4346files/701543674B, zero mismatches. Both
sets are immutable; only17 fixed closed owner/config metadata files were copied
out of each AVD root. Model/cache/VM disk contents are retained and excluded.

| Corrected sealed namespace | Files / bytes | Inventory SHA-256 |
| --- | --- | --- |
| Host |1677/174179254|`e54ed0869742e8210dd0f575c317a16b756c1a67077c85fca94a2d985a9429bc`|
| Environment |27/394754|`bebf39eefdfae3233323243e0e718be6f0be8fc6010f044baeeb3e1044a6d9ea`|
| Preflight |208/87253421|`88942af8dc10cb401449ff7d77b422347d16a237093b2ff35f778e52bdae5135`|
| Candidate |295/87350907|`d18141be11aff320d348513ae9cb8ec78d458cd652b7b15b7fc0c4b6d32318a6`|

Initial inventory SHA values in Host/Environment/Preflight/Candidate order:
`940027f3590208562325bc50e32957136f39d805e3a7059e9a94a0a45d13941e`,
`97a11b2fe3b48cba0b7ec2c5227fa9a20526204bab448d0ad53698ab4beb18d4`,
`b790fb1674bb42c5e1c76ae92b5048c3073da2c3f443eb411fcb52c2bc74d31a`,
`3f38619851da464d3d349c6b6c9bd963ce958d044702b6c839f2fb4589312bbf`.
See [independent review](RECEIPT_COMPOSE_CANCELLATION_REVIEW_2026-10-25.md).

M05.05/M01.05 stay partial/in_review pending full criteria and owner acceptance;
checkboxes remain unchanged. M01.01 physical reference-phone gate is blocked.
Phone/ARM64/16KiB, actual model-setup Start/DocumentsUI route, physical touch/IME, backgrounding,
memory pressure, sustained quality/thermal/latency, privacy/cache-growth and
power-loss qualification remain open. Next runnable task: the real entry route,
memory inspector and invalid-action/secret sequence against the same local backend.
