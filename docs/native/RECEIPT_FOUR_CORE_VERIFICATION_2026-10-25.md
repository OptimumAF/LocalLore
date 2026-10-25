# Fresh four-core receipt execution — 2026-10-25

Refs #9 (M05.05 prerequisite), #5 (M01.04/M01.05 support), PR164 stacked on
unmerged PR162/161/160. Execution source:
`bbf3628d14ba6061e20015649de1b859779121a3`; later evidence commits are
documentation only. No merge, release, dependency/model download or model upload.

## Actual result

The fresh isolated four-vCPU emulator passes all four selected instrumentation
methods and **56 protocol checks**: preflight12, import16, play15, reopen13.
Production receipt setup imports the verified local Gemma file. One actual
local SDK free-text request prepares through the existing close gates; Rust
validates and commits one potion gift to Mira. A distinct app process reopens
revision1 and the same receipt without opening the source or calling inference.
Repairs0, fallbackfalse. No schema drop, context reuse, scripted response,
deadline extension or ownership bypass was added.

| Phase | Proof observation elapsed | Checks | Selected JUnit |
| --- | ---: | ---: | --- |
| Source preflight |200ms|12/12|1PASS|
| Import |101237ms|16/16|1PASS|
| Real SDK play |95363ms|15/15|1PASS|
| Separate-process reopen |35766ms|13/13|1PASS|

These durations cover whole test/proof observations, **not** isolated generation,
first response or complete player-turn latency. PLAY includes full model rechecks,
setup, SDK preparation, commit and teardown. The60s turn/5s cleanup and170s PLAY
observation cap are unchanged. One success does not prove four cores caused the
change from the preserved [two-core failure](LITERT_WORKER_TIMING_VERIFICATION_2026-10-25.md);
host load/cache/scheduling were uncontrolled. No phone/profile is selected.

Both preflight and candidate independently observe four online CPUs before work.
The fixed `cat /sys/devices/system/cpu/online` response is `0-3` plus line ending,
5B SHA `5673d827d554439943a513b6a2cc7dbbc730ce668740cf1db297f7b32f114a34`.
Both closed records contain requested4/observed4 with known client cleanup.
No failure trace is emitted on this passing run; its stage times are unmeasured.

## Implementation and actual host checks

The [closed profile](RECEIPT_FOUR_CORE_PROFILE.md) adds only an explicit
4cores/8192MiB/12GiB host-RAM combination. At least8 reported logical host CPUs
are required before parent and worker SDK dispatch. Valid two-core profiles and
their fact shapes remain unchanged. A one-shot CPU guard stops before work on
mismatch, owner loss, unknown cleanup or evidence-retention failure. All model,
schema, fresh-role-context, token, deadline, canonical and storage gates remain.

Actual `python -B -E -m unittest discover -s scripts/tests -v`: **718PASS/102.066s**.
Original91635 terminal0; owned completed0/known cleanup102828ms, stdout84620B SHA
`6acbadb5065ca49a35d71961656e002ff5c3475aff7250f50780ceb2cec4d7d5`.
Author88 targeted tests pass13.060s (owned0/known13297ms); controller24 pass1.567s.
The first author attempt also exits0/known but retains stderr count only; an
unchanged-source repeat retains full output. Both are preserved, not extra cases.
Diff checks pass. See [independent review](RECEIPT_FOUR_CORE_REVIEW_2026-10-25.md).

No new Android/Rust build execution is claimed.206 Android entries/2245718B and
the actual APKs match compiled2ea73aa index SHA
`658778ac1b4091a28ec43ed2fa199f0816786c8b891a54ed9cdc3f4871ea4fdd`.
Git comparison contains9 changes, none Android/Rust/build sources. Prior actual
[397receipt/373regular JVM, lint/dependency/analyzer/APK/signature checks](LITERT_WORKER_TIMING_VERIFICATION_2026-10-25.md)
are reused evidence. Rehashed artifacts:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Receipt APP |74987568|`83d0709efbd9a72266214d526fadc4f435880ea113b942ddada716e3ea82fda3`|
| Receipt TEST |1974471|`6def97ed744cabb5c98a906a37c976c4a33b6bd0973effcbeda09bef282d7d8a`|
| Regular APP |74954584|`2fccf9f51e6acfa36d346ef1012c64b241a0d7f087c1dfe0be206e6d13c35a9d`|

Unchanged LiteRT-LM0.18.1/source`bda624851d74be34d4e1f7fac1fc4155939539c7`,
Gemma4-E2B publisher`a790a852d433991c0c0a41c1154cf9b3850300fa`,2588147712B SHA
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
Emulator35.3.12/build12990079/API35 GoogleAPIs x86_64 image9/4096-byte pages,
8GiB guest/12GiB userdata/8GiB SD. Four SDK threads and worker SHA
`271d6af5ac1f946b0cd245ac35f7ba5910a097ec49bebe1776448ff4b7885eec`
are unchanged.

## Exact admission, execution and closure

Private namespace prefix `C:/Users/Avery/LocalLore-receipt-four-core-`, followed
by `host`, `environment`, `avd`, `preflight`, `candidate`, then `-20261025`.
Create-only planning calls `plan_prepare(...real_candidate=True,
four_core_candidate=True)` and `plan_run`; it grants no execution.
Root rechecks all909 stock/source bindings and the initial disk before boot;
reviewer rehashes905 nonimage entries and metadata-checks4 installed images,
never model/AVD disk bytes. Token contents are privately hash-compared, never
output/copied. Old targets/caches/default-registry state remain preserved.

Actual CLI commands use those exact namespaces:

```text
python -B -E benchmarks/receipt_avd_environment.py prepare --proposal <environment>/prepare-proposal-v1.json --authorization <environment>/prepare-authorization-v1.json
python -B -E benchmarks/receipt_avd_environment.py run --proposal <environment>/run-proposal-v1.json --authorization <environment>/run-authorization-v1.json
python -B -E benchmarks/receipt_real_candidate.py run --proposal <preflight>/proposal-v1.json --authorization <preflight>/authorization-v1.json --evidence <preflight>
python -B -E benchmarks/receipt_real_candidate.py run --proposal <candidate>/proposal-v1.json --authorization <candidate>/authorization-v1.json --evidence <candidate>
```

| Proposal | SHA-256 |
| --- | --- |
| Prepare |`32ebf859d2e470d66966bba3f0ec5c55466237140d11dab351db5e0b203aeb82`|
| Run |`aeb41ca08550f12402ba6d409bab4a8a0558ca776c90205e817dda488055107b`|
| Preflight |`be2d6df9ff09e9c33fbde74e20c662ae5878b659d265394fd2662492a14ab073`|
| Candidate |`010122fafcc7c4b8afb9e96c595af616f6a7be937cd72457f1eb47aaddfb3cce`|

Frozen tracked source1529files. Prepare42779 terminal0; SDK0/known5375ms,
stdout87/stderr645B, prepared/success/closure/cleanup links pass. Plan-run93621
terminal0; prepared SHA `406bd88c872351019c7968dd4d1cd77c26f9a7459859d5ecf18570b2e31d5bf3`.
Run-grant facts C257450471424B/D47086030848B/RAM35895562240B/logicalCPU20;
unchanged C/D40GiB and RAM12GiB floors. These are observations, not reservations.
Owner55581 announces running/boot initially unverified, descriptor SHA
`77edab80272cb8fb8bd37717fe82ef2163e2a29c70ebcc0af1c55ff6c28b56b6`.

Preflight81 nonweight bindings/86722433B match current files and exclusive
archives. Original84014 terminal0, owned0/known43328ms, stdout416/stderr0B;
44clients0/known,1PASS/12true/source0/SDKfalse. Candidate85 bindings/86728674B
match;1547s remained at review, above920s. Separate grant binds standing human
local-copy/SDK/restart consent. The held source FD is fully hashed/streamed once;
client0 alone never proves destination validity. IMPORT independently verifies
and imports exact bytes with each1open/1close.

| Raw proof | SHA-256 |
| --- | --- |
| Preflight |`c59ff1e088a4ad9b3474bd56c112748e9e410467770a74e040458f8e9374f68f`|
| Import |`b56ec2f6e47fdce245c4b66fb6f3b8a9072c34da11caaf02eab1f5c656738d84`|
| Play |`45cf3bbfece212ff90390e6ff4949ef0a66da656256361b176522fa25093fce0`|
| Reopen |`9d623fea2372ebbed8821200fba4982151e7f2169b21ead3671ad9d6bfbf19c4`|

Play/reopen agree on receipt SHA
`3ef744f27ce40a10e35dd80dbc88af00cbd4009389981723bae7e060a691fb2e`.
Linked proofs require changed app process instance, revision1, one unchanged
gift receipt and no source/inference call on reopen. Candidate75519 terminal0;
owned0/known380500ms, stdout416/stderr0B;56clients0/known and3 selected JUnit PASS.
Client count56 is distinct from56 combined checks and4 combined JUnit methods.

Exact stop follows consumed candidate terminal. Owner55581 then consumes
terminal0: stop_requested735500ms, capture/cleanup/preservation closuretrue,
worker1, stdout15825/stderr1079B. All3 recorded host PIDs are absent and ports
free. Host termination is verified; guest flush/power loss/hidden-native
reclamation are not inferred.

Retained planning errors: short commit reference refused before proposal/SDK
(empty metadata directories only), then builder syntax error before any write
or SDK. Corrected create-only helper checks existing empty directories/full
commit; neither failure consumes a grant or starts an emulator. Prior two-core
SDK failures remain preserved; this success does not explain or erase them.

## Sealed evidence and next task

Nonweight evidence1980files/193173659B, no weights/VM disks/raw private
diagnostics uploaded:

| Namespace | Files / bytes | Index SHA-256 |
| --- | --- | --- |
| Host |1542 /19075064|`c793e2564a752e3553d11957ce3279c04b18c137c54bdf090bbf97f149a8fd6d`|
| Environment |27 /394542|`0df2085dd673b9c3c5d3200dad8fe1de9a89b373f2b7f8cec3ab3c1e5dc4df3d`|
| Preflight |188 /86832481|`36d3380c888f33fdcad5bf96333c72003a6ea4eed154ef41adcc8fe67d2b02f9`|
| Candidate |223 /86871572|`b0b576628547df1d2566cd72f2db092883bea6554319d60361a7fe52a0a82950`|

M05.05/M01.04/M01.05 remain partial/in_review pending owner acceptance and
broader criteria. M01.01 physical reference phone, ARM64/16KiB execution,
DocumentsUI, cache privacy/peak growth, power loss, real-model cancellation,
sustained narrative/latency/thermal qualification remain unverified. Next runnable
task: separately admitted bounded real-model cancellation/recovery on this
working profile, preserving receipt/canon and original deadlines.
