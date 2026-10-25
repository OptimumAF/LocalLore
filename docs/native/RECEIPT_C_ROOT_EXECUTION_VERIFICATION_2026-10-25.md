# Explicit C-root real receipt execution — 2026-10-25

Refs #9 (M05.05 prerequisite); #5 (M01.05 supporting). PR161 is stacked on
unmerged PR160. Execution source is `daad3b598a43b0fe862d894c5633a7ce77892ead`;
Android/Rust/build sources are unchanged from the verified
`ea924a2c2cd7db78e342062225e0aaff52ff7b05` observation APKs. Later evidence and
research commits are documentation only. This session performs no merge.

## Actual outcome

The explicit fresh C-root prepares and boots successfully, retains all resource
floors, and passes preflight12 checks plus production model-import16 checks.
The following real PLAY fails `LocalInferenceUncertain` in80.392s. No Prepared
result, gift-commit request, PLAY proof or REOPEN follows. Both passed methods
establish28 successful checks, not the complete56-check protocol.

The new closed trace records a returned initialization and one call reaching
terminal/body-drain/conversation-close observations. The next conversation
creation has an entered observation without a matching return at the snapshot.
It does not identify director/repair/narrator, a valid proposal, a native hang
or its cause. It does not qualify engine release or a successful gameplay turn.
The exact owner was stopped after the failed candidate terminated; all recorded
host identities were absent and owned ports free. SDK cooperative reclamation
and guest flush remain unproven.

## Capacity change and source verification

The previous D-only helper could not allocate another8GiB SD image above the
unchanged40GiB D reserve. The new policy accepts only an explicitly supplied,
absent C: or D: root; it never probes/selects/falls back to another drive.

| Explicit root | Required C free | Required D free |
| --- | ---: | ---: |
| D: |16GiB|40GiB|
| C: |40GiB|40GiB|

Both prepare and run bind the exact integer floor pair to the chosen drive.
Existing normalized/nonlinked/absent-root checks, source bindings, external-state
preservation, stdin barriers, live leases, one-shot claims, ownership/cleanup and
stop/expiry checks remain. Guest RAM8GiB, host available RAM minimum12GiB,
userdata12GiB, SD8GiB, two cores and the real-profile1800s owner are unchanged.
No old target/copy/cache was moved, deleted, adopted or repaired.

The coordinator ran
`python -B -E -m unittest discover -s scripts/tests -v`: **690 PASS/57.839s**,
original27648 terminal0, owned completed0/known cleanup58,547ms. Raw81,314B SHA
`737f845d1e5e36542546cb0fae0b376afba7b499081a8092d7898d24c8bc3ff4`.
The author passed11 targeted tests after correcting one expected fixture-binding
order; its earlier failure remains retained. Independent review passed15
synthetic C-root/lease/replay variants. See the
[source review](RECEIPT_C_ROOT_REVIEW_2026-10-25.md).

All1,522 tracked source files/18,539,289B matched the frozen snapshot and current
tree. The206 tracked Android entries/2,216,712B also match the previously compiled
index. No new Android build/test execution is inferred: reused exact receipt
APP `fea69522642c5562134eab602cce55d006632fa451b40e55a247ce6a649c6140`
(74,987,568B), TEST
`7a8a32bedc574b4b3d57e476be54518d05dc641d6952c01ac8f70def2a326eb9`
(2,867,979B). Their385 receipt/361 regular JVM, lint, dependency/analyzer,
APK/signature checks are [recorded separately](LITERT_WORKER_TRACE_VERIFICATION_2026-10-25.md).

Runtime/model remain LiteRT-LM0.18.1 /
`bda624851d74be34d4e1f7fac1fc4155939539c7`, Gemma4-E2B revision
`a790a852d433991c0c0a41c1154cf9b3850300fa`,2,588,147,712B SHA
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
Worker SHA `aaf476a9ad3928c0a21168c0949776abbcf876bcbb20180ba4da82eae067db29`.
Emulator35.3.12/build12990079, existing API35 GoogleAPIs x86_64 image9;
4096-byte guest pages. No dependency/model download or production tier choice.

## Exact admissions and execution

Private namespaces use `C:/Users/Avery/LocalLore-receipt-worker-stage-` followed
by `host`, `environment`, `avd`, `preflight` or `candidate`, then `-20261025`.
The target is outside repository/sync-default directories. Source/metadata-only
builders and independent review precede every exact root grant. Human permission
for local model copy, SDK and restart persists; it is not a remaining gate.

Planning used the retained private bootstrap helper calling `plan_prepare` and
the existing `plan_run` API. Actual public CLI invocations were:

```text
python -B -E benchmarks/receipt_avd_environment.py prepare --proposal <environment>/prepare-proposal-v1.json --authorization <environment>/prepare-authorization-v1.json
python -B -E benchmarks/receipt_avd_environment.py run --proposal <environment>/run-proposal-v1.json --authorization <environment>/run-authorization-v1.json
python -B -E benchmarks/receipt_real_candidate.py run --proposal <preflight>/proposal-v1.json --authorization <preflight>/authorization-v1.json --evidence <preflight>
python -B -E benchmarks/receipt_real_candidate.py run --proposal <candidate>/proposal-v1.json --authorization <candidate>/authorization-v1.json --evidence <candidate>
```

Angle-bracket prefixes denote the exact namespaces above. Proposal SHA-256:

| Phase | SHA-256 |
| --- | --- |
| Prepare |`b2e6ffe58295fb6749a07e951bf0a116c179d873903072d104e312f0f81c4b3b`|
| Run |`f0e9cc5807bca0fbc530fa91bfbb7be07cae77b4e912ab8cb324d80dbfa4fd86`|
| Source preflight |`dc0305da7e9770e5c57f0b63b3550ffec1527fbf87b00be4ee18a18b5075fdfe`|
| Candidate |`579ce9f139fd88598b6855f1535c89ea68490b0ecb2751250b36eca30c2b7d92`|

The coordinator verifies all909 installation/source bindings. Independent review
content-rehashes905/1,332,025,888B; four installed SDK `.img` entries are
metadata-only in that review. Console token content and new/old AVD disk contents
are not read by the reviewer. Primary authorization repeats the full stock
installation/external/capacity/absence checks. Independent metadata is observation,
not a capacity reservation or execution authority.

Preparation: original30852 terminal0, SDK client completed0/known28,172ms,
stdout87B/stderr645B; successful preparation/child cleanup/preservation closure.
Run admission observed C307,623,010,304B free, D47,466,352,640B and host available
RAM35,096,199,168B. The original owner54784 confirmed running with boot initially
unverified; descriptor SHA
`a4661abe376e5b680234248a18cbdd7e3faea70496b3ebfc2b07306585dae1c2`.

Preflight:79 nonweight inputs/87,570,455B independently match current files and
archives. Original62751 terminal0; owned child0/known capture+cleanup41,797ms,
stdout416B/stderr0; all43 clients completed0/known, one actual JUnit PASS/12true
checks. Fixed61B staging only; SDK/model copy false. Proof SHA
`5e89dd5b731889328415429835949c40d1dbdd06d14cc6fa8cafa47be5ce9b63`.

Candidate:83 nonweight inputs/87,576,696B independently match;1,506s remained at
review, above the unchanged920s entry requirement. The held source FD is fully
hashed and streamed once. Transfer-client0 is not remote-exit or destination
proof; the source-domain test independently verifies the actual staged model.
IMPORT passes all16 checks in91,750ms, verification and import each1open/1close/
exact2,588,147,712B. Accepted full recheck/runtime admission and linked post-import
UID/package/volume/process/storage facts pass. Proof SHA
`c7e511a67370caea7067e776f09b8ee2bb6fdb3ea5acc247476cc6d66f0d9c38`.

## Failed PLAY and ownership observations

Actual selected PLAY fails in80.392s with fixed `LocalInferenceUncertain`.
Command0028 raw6,867B SHA
`55a430931ab5dc65c8104db7294e7ef7f1dbe23dce910546ea84b6d9b0371502`.
The strict failure-only decoder preserves the trace and rejects that runner.
Trace SHA `ba097fabf578886923a402bc7af46d6f48b0d07d4ec413ca6f5c0518775d0610`:

| Historical observation | Counts |
| --- | --- |
| Admission, engine creation, init admission, initialization |each entered1/returned1|
| Role admission |entered2/returned2|
| Conversation creation |entered2/returned1|
| Send admission and send |each entered1/returned1|
| Message callback bodies |entered24/returned24|
| Done callback body |entered1/returned1|
| Drain settled branch |1|
| Conversation close |entered1/known1|
| Error, cancel, engine close and uncertainty notifications |all0|
| Saturation |none|

These are the [contracted Kotlin recording points](LITERT_WORKER_TRACE_CONTRACT.md),
not jointly atomic SDK state. Zero uncertainty notifications does not clear the
owner quarantine. No generation role/schema validity, native entry/hang/cause,
engine release or reclamation is inferred. The first close is a historical
public-return gate, not hidden-native completion. No Prepared result/commit
request, post-SDK model hash, retry or REOPEN is forced after uncertainty.

Original candidate14270 terminal1; owned child2/known capture+cleanup292,672ms,
stdout453B/stderr0. All28 clients complete0/known, distinct from JUnit results:
one IMPORT PASS and one PLAY FAIL. Exact stop then consumes original owner54784
terminal0: stop_requested, cleanup/capture/preservation closure true749,297ms,
worker1, stdout13,777B/stderr1,908B. Actual three recorded host identities absent
and owned ports free. No guest-flush/power-loss or SDK cooperative-close claim.

## Sealed evidence and handoff

All old targets/copies and this stopped C target are retained. Four private
nonweight inventories include bounded closure metadata, never model weights or
AVD disks; they are read-only after sealing:

| Namespace | Files / bytes | Index SHA-256 |
| --- | --- | --- |
| Host |1533 /18,921,195|`7adedfd65f9d982a162250965a095ae8ae6ac69e9adc548c6919c2d67319849f`|
| Environment |25 /392,813|`fd56e6950748d0818d0f56fcf5b0a2c5a57c1cf8d840a0508fa4f189b03b4070`|
| Preflight |182 /87,674,800|`8c09a6669f3028d13bc1026bf0e4c8054659d20117e9d2bcfff41702316f35f2`|
| Candidate |156 /87,669,188|`ce29463cedcd886a6600f041a8ec53fe4d4845a54bdb5cc49b17821dbf8aa7e8`|

Independent execution review checks all1,896 files/194,657,996B with zero
mismatches,206 Android source entries and17 original/copied closure records.
No raw private diagnostics, weights or disks are uploaded.

Implemented/in-review: explicit host-volume policy and real worker observation
transport. Still unqualified: accepted real gift/restart, full M05.05/M01.05,
reference phone/ARM64/16KiB execution, quality/sustained, DocumentsUI/cache/privacy/
power-loss and old integrity holds. The next runnable task is a bounded
role-aware, timed two-structured-conversation investigation/fix against the exact
pinned SDK. Keep all role schemas, fresh context,60s/5s, quarantine and canonical
gates; source-backed hypotheses must not be promoted to a proven cause.
