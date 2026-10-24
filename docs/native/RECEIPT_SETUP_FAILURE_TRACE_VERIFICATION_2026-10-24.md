# Receipt setup failure observations — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 support). The preceding fresh
[supervisor run](RECEIPT_SUPERVISOR_EVIDENCE_2026-10-24.md) produced two initial
passes and one initial-import READY timeout, with known owner closure. Its cause
is not established. Old attempts, saved targets and holds remain preserved.

## Implementation and boundary

The explicit debug fixture records bounded lifecycle/operation categories and
selected synthetic-source progress, without changing production state, source
ownership, receipt rules, runtime admission or the10-second assertion wait.
One process-wide sampling attempt emits a dedicated instrumentation status1337
record. Original failures are rethrown identically even if diagnostics fail.

The closed ASCII encoder bounds full prefix+JSON UTF-8 to2,048 bytes, stores at
most16 owned event entries, and saturates its total/read/byte counters with
explicit flags. Unknown exceptions become OTHER without reading message, cause,
stack or class names. The error is the last observed operation category; source
counters are independent observations and returned bytes are not persisted
bytes. After Activity recreation, retained ViewModel operations can still belong
to the original dependency trace. No claim of complete current-VM history is made.

Host parsing validates the finite observation separately, preserves raw evidence
and retains the original three-pass/restart/44-check refusal gates. Diagnostics
are not acceptance, READY, ownership or gameplay authority. Root/parser and
per-profile APK audits prohibit arbitrary fields or diagnostic-class leakage.
There is no new dependency, model selection, permission or production authority.

## Attempts actually performed

The first script suite ran606 tests:605 passed and one new framing test failed,
66.087 seconds. It incorrectly assumed generic CRCRLF acceptance; the strict
shared normalizer was correct and remains unchanged. Original53377 consumed
terminal1, owned completion1/known cleanup,67,219ms. Stdout71,791 bytes SHA-256
`25c3ec255a28aa818bfe924b3816748286e8aee54409ebe51a796500c4c94a15`.
The corrected test keeps LF/CRLF positive and CRCRLF/mixed/lone-CR negative.

The intermediate receipt build completes0/known cleanup,186,250ms; original54389
consumed terminal0. It compiles app/instrumentation and passes352 JVM tests in36
suites, zero failures/errors/skips, lint0 errors/19 warnings and dependency/analyzer
tasks. Stdout9,649 bytes SHA-256
`2ce9a06166c63b1a471b0f91acc32ad6cdd64ea1474172df9ced8bafe4196ad8`.
Reports and APKs are retained before subsequent changes; this is not a final
artifact admission or device pass.

Independent review also found a real snapshot API hole: a caller-owned mutable
event list could grow after constructor validation. The corrected snapshot owns
at most16 copied entries and returns copies; a new mutation regression covers
caller and published lists. This is not a demonstrated cause of the older UI
timeout. The test suite also adds a full original synthetic failed-runner status
shape and an actual mocked Owner/cohort path proving raw/observation retention
before refusal and no helper/restart dispatch.

## Corrected host and artifact verification

```text
python -B -E -m unittest discover -s scripts/tests -v
```

All608 script tests pass, zero failures/errors/skips,68.011 seconds. Original47399
consumed terminal0, owned completion0/known cleanup,69,047ms. Stdout71,099 bytes
SHA-256 `f5f13f7b6f46292d53d211fc385f65889650491b12fddbfaaf78a8a3c00dfab8`.
The new failure parser has11 tests, including full synthetic failed-runner and
actual mocked Owner/cohort refusal; no device transport is inferred from mocks.

Central offline builds compile app/instrumentation, run JVM tests and lint:

| Profile | JVM tests / suites | Failures/errors/skips | Lint errors / warnings | Owned ms |
|---|---:|---:|---:|---:|
| Corrected receipt |353 /36|0 /0 /0|0 /19|137,875|
| Regular SDK |340 /35|0 /0 /0|0 /9|153,610|
| Ordinary |206 /24|0 /0 /0|0 /1|83,750|

The receipt profile includes12 independently authored trace tests and the
central caller-list mutation regression. All13 pass; source-only agent handoffs
are not represented as separate test executions. Regular/ordinary exclude the
receipt-only JVM source set. SDK dependency/analyzer tasks pass unchanged; no new
runtime/model/native dependency or license choice is introduced.

Original corrected receipt48197, regular99929 and ordinary16335 are consumed
terminal0; every owned build completes0 with known cleanup. Their stdout hashes:

- Receipt9,947 bytes: `d8dd48d15ba34a236d7df77255a9c80329c6f8c37d1d0586ec95cb5be6b23456`.
- Regular9,157 bytes: `054484bcab5cf55201eb59d4c3c3f4f158675300f4ffe5e5168527554da6a0e0`.
- Ordinary5,842 bytes: `1963000c48b1c064acce5edb5c16499d502ea96acc89de2542b5a60dc486f521`.

All three actual APP APK capability/native/manifest audits pass. The receipt
APK contains all diagnostic classes; regular and ordinary exclude them. SDK
binary/notice hashes, native ABI alignment and fixed private activities remain
checked. This is packaging, not ARM64 or16 KiB execution. Both new receipt APK
signatures verify with known child cleanup. An initial private artifact helper
incorrectly expected an instrumentation field in `aapt2 dump badging` after its
three child checks all completed0; that helper assertion is retained. A separate
XML-tree check verifies the exact target/runner and byte-identical6,244-byte
instrumentation manifest against the previously audited APK. No signature or
application failure is inferred from that helper's assumption.

| Frozen corrected APK | Bytes | SHA-256 |
|---|---:|---|
| App |74,884,112|`dca8db5ef1244e29318f3b5da1044e8468bc82a6b995ac591f0516eae7dd76f7`|
| Instrumentation |1,922,787|`bc74a8c89c447999a83cee019e37c78186d7e071e03165e8014517e89fefe4ef`|

After compilation source `ae52ea6`, only the controller's two APK pins and this
verification document change before frozen execution source
`8f522407f1e36fa00850a2214c7b6664de2f4db2`. All Android/Rust/build implementation
inputs remain identical. Old targets are not reused.

## Fresh emulator observation and closure

Separate PREPARE, RUN and GUEST proposals and authorizations bound a newly
created Android 15/API35 Google APIs x86_64 target, emulator35.3.12/build12990079,
image revision9/extension13, with12 GiB userdata,8 GiB SD,2 GiB RAM and2 CPUs.
An independent reviewer rehashed the closed inputs before each admission. The
guest archive contains63 frozen inputs,86,197,679 bytes; its index SHA-256 is
`0617dc7ac0fef2976528b2156ebf28022d37af959059d0c1cf10bf32ea0b09c4`.

The actual bounded guest run completes0 with known client cleanup in83,109ms;
original56717 is consumed terminal0. All72 clients complete0 with known cleanup,
including exactly two installs and two instrumentation invocations. The initial
three methods pass and the separate-process reopen method passes. Four JSON
proofs and four empty ready-file reads satisfy all44 unchanged checks. Restart
matching verifies a changed app process/start with the same app UID. Five process
boundary observations replay successfully: the app is absent at required
boundaries and the exact permitted test helper remains stable. This is not an
all-processes-quiet claim. Independent review replays the raw outputs, proofs and
checks without mismatch. Guest stdout313 bytes SHA-256:
`ea0fa146cf90972e119baab539e069e95bf10cedd58a7f7d0f7d1b730cbd9eff`.

Neither instrumentation transcript contains a failure record. Consequently,
actual failure-status delivery remains unexercised. This positive run neither
diagnoses the preceding timeout nor demonstrates that diagnostics fixed import.
No timeout, lifecycle, storage, ownership or production behavior was relaxed.
No model copy, model inference or extra diagnostic ADB call occurred.

The exact owned stop follows guest success. Original owner37975 is consumed
terminal0; the owner reports stop_requested, cleanup_complete, closure_verified
and output_capture_complete,294,125ms. Its worker exit1 reflects the requested
job drain, separately from the completed guest run. Owner stdout9,233 bytes
SHA-256 `53402e90f705188b3d799ddb944070882780f5443b62d45e179769241c074ce9`;
stderr1,019 bytes SHA-256
`a284a0f051c4720970517d53270781712f442f2252f77ad1f60b34be4c94c164`.
Post-stop enumeration finds the recorded owner, worker and launcher absent and
both owned ports free. Guest flush is not claimed. The saved target and disk
metadata remain retained; no raw disk hash or power-loss durability is inferred.

Private evidence stays outside Git. Final create-only inventories were rehashed
with zero mismatches:

| Inventory | Files | Bytes | Index SHA-256 |
|---|---:|---:|---|
| Host |1,637|271,069,839|`5f8679c8509a7bfeec7e17f0cb822971e4761fa9f43367332587463281ded083`|
| Environment |23|389,003|`1818cb4a9fc6749e9001db858bbdd6a3cf7bb90ab4cf42f5cd88f17231a16904`|
| Guest |226|86,347,718|`02d605f5a2de00660896959596de7628c5d5a75d70592adf9cbf0a50f3797404`|

The executed source snapshot contains1,429 files/16,876,263 bytes; its index
SHA-256 is `17dbb6ef34f7f7c5f48d79fba93d28b585c34917941bff19f6979dfc41a423bf`.
Final documentation and review changes do not imply another build or guest run.

## Remaining gates

Next qualify dedicated failure-status delivery and original-failure preservation
through a separately scoped deterministic negative instrumentation experiment.
The earlier timeout's cause remains unknown; do not extend the wait or infer a
storage/lifecycle cause. The fresh three-plus-one setup/reopen, eight proofs/44
checks and final owner cleanup above passed for this synthetic fixture only.
Real-model/SDK, DocumentsUI, reference phone,
ARM64/16 KiB, cache/privacy, power loss, quality and sustained behavior remain
open, including existing A/#117/#119 holds. Full milestone checkboxes stay
unchecked pending complete criteria/owner acceptance. No model transfer,
inference, merge, release or repository access change.
