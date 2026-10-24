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

Corrected final builds, parser checks and actual device observations remain
pending in this draft. Source-only agent checks are not execution evidence.

## Remaining gates

Diagnose the actual observed failure from a separately admitted fresh run before
changing behavior; do not extend the wait or infer a storage/lifecycle cause.
Require the complete three-plus-one setup/reopen, eight proofs/44 checks and
known final owner cleanup. Real-model/SDK, DocumentsUI, reference phone,
ARM64/16 KiB, cache/privacy, power loss, quality and sustained behavior remain
open, including existing A/#117/#119 holds. Full milestone checkboxes stay
unchecked pending complete criteria/owner acceptance. No model transfer,
inference, merge, release or repository access change.
