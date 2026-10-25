# Real SDK cancellation and recovery — 2026-10-25

Refs #9 (M05.05 support), #5 (M01.05). PR165 is stacked on unmerged
PR164/162/161/160. Execution source: `1ce40ae394892e1849aabe21d9a8cbd85a475e5b`.
Later verification/review commits are documentation only. No merge or release.

## Defect and implementation

The native cancel acknowledgement could return while the captured prepare still
owned SDK cleanup. `DurableGateway.cancelSaved()` immediately refreshed through
`open` and `branches`, which correctly refused that still-active owner as Busy.
The UI also starts cancellation refresh without joining its old caller job.

The deterministic regression holds engine close and observes the early ACK:
one actual JVM test fails before the fix. `LocalInferenceOwner` now captures
that active run and waits for its known-clean finish before acknowledging
cancel. One unchanged cleanup deadline covers both native ACK and cleanup;
finish signals after native/SDK join and active clearing, and cancel rechecks
admission. Failed/unreturned cleanup still quarantines. The active-operation
whitelist is unchanged. This orders the captured run, not arbitrary separately
initiated concurrent prepares; gateway Main-thread sequencing remains required.

The new [protocol](RECEIPT_REAL_CANCELLATION_PROTOCOL.md) preserves existing
source preflight/import and adds a separate closed cancellation proof namespace.
Its Main-confined gateway calls use actual production transport, without forcing
an I/O wrapper or injecting SDK callbacks/results/delays. The test joins the
original response; cancelling a test coroutine is never release evidence.
After the model recheck it repeats the existing owner guard and publishes a
fresh validated trace after close, rejecting observed late uncertainty.

## Actual emulator result

All **82 checks across five selected JUnit methods pass** on a fresh isolated
four-vCPU emulator. Cancellation samples returned output with an unfinished
original request and no observed terminal callback, invokes the actual gateway
cancel API once, then joins its `Rejected("Cancelled")` result and known cleanup.
Canonical revision stays0, no receipt exists, and the player retains one potion.
A new app process verifies that state before one actual local SDK turn commits
the gift. A third process reopens revision1 and the unchanged receipt without
reopening the staged import source or invoking the SDK. Recovery repairs0/fallbackfalse.

| Phase | Whole proof observation | Checks | Selected method |
| --- | ---: | ---: | --- |
| Source preflight |183ms|12/12|1PASS|
| Full import |93955ms|16/16|1PASS|
| API cancellation |69695ms|21/21|1PASS|
| New-process recovery/gift |62381ms|19/19|1PASS|
| New-process reopen |32128ms|14/14|1PASS|

These are whole-method/proof observations including setup/model rechecks,
waiting for output and teardown. They do not measure cancellation latency,
isolated generation or first final-response latency. Trace and test clocks have
different origins. This exercises the API on Main, **not a Compose Cancel-button
click**; UI-style caller cancellation is separately covered by JVM tests.

The sample records one returned message and no DONE/ERROR/cancel/close
observations. Final cancellation records two returned messages, ERROR1/DONE0,
SDK cancel entered/returned1, drain1, conversation-close known1, engine-close
known1 and uncertainty0. Its returned DIRECTOR creation is identical in both
snapshots, with nondecreasing counts/times. Recovery records fresh DIRECTOR and
NARRATOR creations. These are historical public recording points and known
logical close gates, not atomic native state, future-callback immunity or hidden
native reclamation. Zero uncertainty alone never proves a healthy owner.

| Raw proof | SHA-256 |
| --- | --- |
| Preflight |`e996f7f085bff5522a5f6690dedfc7b08879cfff6f82bf84759790929700cfc1`|
| Import |`7b2d2aa2c179ff21cbd08b1f6c6ef2d6a00bc6876d1a2df1bdb3ebac151a4baf`|
| Cancel |`1a9922f515e865756122e6d292b4bbddba0635ac069ff7f6704f3c652997cd04`|
| Recover |`c54c11a586a9a32d2879d37239a351cee74284945c19da233f8858ad4a083050`|
| Reopen |`5dda96188d8f40acfc185e09a3cc7ea8c624fc6071d4b66ae34e9aa8bffaab0f`|

Recovery/reopen receipt SHA agrees:
`e685bb45b3588507d29bdf485f2a6e50831ba6c10cd00f1206534d2b8493712b`.
Raw sample/final cancellation and recovery trace SHA values are respectively
`22bd89898e30a32e60994c1c49124c34523f4886e2c956d621409dc521b48a57`,
`928f26042b551b72947ea898bce75687c59c1172eb07223e98b1f23dcbcbb17f`,
`ef410348ca90423b0bfbc5f27685bb219085b990334128dccbadf21421d90703`.
No failure worker record was emitted on this passing control.

## Host, build and artifact evidence

The first repro attempt85228 exits1/known cleanup19750ms with **zero tests**:
the ordinary profile correctly refused its use of the exclusive LiteRT cache.
Corrected attempt18108 exits1/known84297ms with1 test/1 expected early-ACK
assertion failure. XML and source hashes are retained. The initial fix's owner
suite passes25 tests/0 failures/errors/skips, original48668 terminal0/known39125ms.
The full suites also execute the stronger held-close Busy assertions.

Final `python -B -E -m unittest discover -s scripts/tests -v`: **742PASS/59.377s**,
original57591 terminal0, owned completed0/known60188ms. Raw87591B SHA
`c93981d74a6ae4bf21bcfcc0e922d47ba2df142cd6ec8c898ae26fe2bf8f2a93`.
The combined controller target passes48 cases; full742 includes all of them.

Offline Gradle receipt and regular tasks:

```text
:app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest
:app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies :app:auditLintAnalyzer
```

Existing JBR/JDK21/NDK29, max-workers2, no daemon/downloads, nonincremental
Kotlin, audited lint9.4.1 and explicit verification flags/cache are retained.
Final receipt92385 terminal0/known142891ms: **412 JVM tests/39 suites**, no
failures/errors/skips, lint0errors/19warnings. Regular31026 terminal0/known135890ms:
**377/36**, no failures/errors/skips, lint0errors/9warnings. Both dependency/
analyzer and APP audits pass; receipt APP/TEST signatures pass.

Receipt compilation source is `4f43ac5e7b03f562e68f30eea23f6a10f5094c82`;
execution adds only Python APK-pin metadata. All209 refined Android source rows
match. Regular source is `45aae5cf1a44228c946d3d5a57ea781150ae0c9b`; its only
Android delta is excluded receipt-only instrumentation, so regular inputs are
unchanged. The1537-file/18825755B final source snapshot matches execution1ce.

| Audited final artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Receipt APP |75003952|`038c192f12a43fc055b232d5cd33b192bb955a366b24a2d9fadbeef226de8699`|
| Receipt TEST |2003207|`04ddfe88176b9a09110881d48ae490ace27ff1fd819fb4ab28de5889c76f8431`|
| Regular APP |74954584|`b8dcb3adb105175d5dbba7edfde560079de87b75cffa0e3daa2aab1facca59f3`|

An initial collector mistakenly selected the ordinary build directory, retaining
stale25-test/24MB artifacts. That collection is explicitly unqualified and was
never used for grants/install. Corrected variant-specific collections and final
receipt refinement are retained separately; no earlier evidence was overwritten.
Author-side initial host-test oracle failures were corrected and disclosed; all
final central host tests pass. See [independent review](RECEIPT_REAL_CANCELLATION_REVIEW_2026-10-25.md).

## Exact admission, runtime and closure

Private prefix `C:/Users/Avery/LocalLore-receipt-cancellation-`, followed by
`host`, `environment`, `avd`, `preflight`, `candidate`, then `-20261025`.
Existing public prepare/run commands are used; preflight uses
`benchmarks/receipt_real_candidate.py run`, candidate uses
`benchmarks/receipt_real_cancellation.py run`, each with exact `--proposal`,
`--authorization` and `--evidence`. Create-only planning grants no execution.

| Proposal | SHA-256 |
| --- | --- |
| Prepare |`fd627e82990f05430c90c91222bcd185e5ca25efee43c4480dde6c785f6285c6`|
| Run |`05721a83d4095db596be2bf45bf428b7f78a7596f4ea2b09d52627f5424dce4a`|
| Preflight |`1019525bb2561d4dac08e6e1b51ad0c694a0077cb1c97dc07bdb10514a39e7b5`|
| Candidate |`76fe929ed4adc56f732c9f6b06f34dcf72a3286ff0675e1fba0c6de3e7ded90f`|

Root rechecks all909 stock/source bindings and initial disk before boot.
Independent review hashes905 nonimage entries and checks4 installed SDK images
by metadata only. Token contents are privately hash-compared, never output or
copied. Registry/token metadata matched; this experiment issued no operations
against old targets or caches. Prepare31439 terminal0,
SDK0/known5235ms; plan-run64406 terminal0. Run-grant facts are C231946403840B,
D46820155392B, available RAM36310077440B and20 logical CPUs, above unchanged
C/D40GiB/RAM12GiB floors. Descriptor SHA
`e3a378c00233ef09210b7d6f5a818c64398a8014176ae9e57c91498c3bcb0d62`.

Preflight86 nonweight bindings/86938837B and candidate90/86945078B match current
and exclusive archived inputs. Preflight37608 terminal0/known41500ms,44 clients
and1 selected PASS. Candidate review observed1427s remaining, above920s entry.
The separate six-field grant binds standing local-copy/SDK/restart consent;
weights are excluded from generic input reads/archives. The held source FD is
fully hashed/streamed once; IMPORT independently verifies/imports exact bytes,
each1open/1close. Client0 alone is not destination or remote-exit proof.

Unchanged LiteRT-LM0.18.1/source`bda624851d74be34d4e1f7fac1fc4155939539c7`;
Gemma4-E2B publisher`a790a852d433991c0c0a41c1154cf9b3850300fa`,2588147712B SHA
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
Emulator35.3.12/build12990079/API35 GoogleAPIs x86_64 image9/4096-byte pages,
guest8GiB/4CPUs/userdata12GiB/SD8GiB. Model/schema/fresh-context/token limits,
60s turn/5s cleanup,870s aggregate/900s outer/920s entry and1800s owner remain.
The existing selected-runner120s gate is retained separately from170/170/120s
proof caps. No fallback, dependency change or supported-device/backend selection.

Candidate21508 consumes terminal0, owned0/known405750ms, stdout419/stderr0B;
77 actual clients/4 selected PASS. This differs from82 combined checks and5
combined JUnit methods including preflight. Exact stop follows that terminal.
Owner75666 consumes terminal0, stop_requested911969ms, capture/cleanup/closuretrue,
worker1, stdout15836/stderr1082B. All3 tracked host PIDs are absent and ports free.
Guest flush, power loss and hidden-native reclamation are not inferred.

## Sealed evidence and remaining gates

All3787 nonweight files/471309219B independently match. No model/VM disk contents
or raw private diagnostics are uploaded:

| Namespace | Files / bytes | Index SHA-256 |
| --- | --- | --- |
| Host |3287 /296720400|`6a135f4b75dc34a10b17acd4d73f3fc82ff12268606a00711a01b38573c94972`|
| Environment |27 /394638|`3f4da0e4ebe3ead2ee508cdb8f9295a7baac6225bb822b3f8269a382b7050eb6`|
| Preflight |193 /87049525|`d3715365ebc700ce053498f05073f560a8306f0c5bb875dbb6df8fc7bca95567`|
| Candidate |280 /87144656|`49408a0343db32f075be623a2738222cffb00e23eb7176bc91584dc970f06f79`|

M05.05/M01.05 remain partial/in_review pending acceptance and broader criteria.
M01.01 physical reference phone, ARM64/16KiB execution, actual Compose Cancel
clicks, DocumentsUI, backgrounding, sustained quality/thermal/performance,
cache privacy/growth and power-loss qualification remain open. Next runnable
task: exercise real Compose Send/Cancel and visible recovery with the local
backend, retaining this API-level control and unchanged ownership gates.
