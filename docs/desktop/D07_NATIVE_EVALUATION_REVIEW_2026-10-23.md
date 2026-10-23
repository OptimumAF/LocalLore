# Native evaluation results integration review

Refs #29 D07.06, partial. Root review/integration claim6361117493 follows the
author's explicit release. Independently read implementation317dc60 and repair
7fd006a, final defensive validation78db0da and integrated4a0a859. Root did not
author this panel/manager. No concrete blocking source finding remains.

Earlier review found a gap between admitting work and registering its thread,
possible late publication after retirement, infallible thread-spawn assumptions,
and path pins acquired in the wrong order. The repair serializes registration,
holds the worker behind a start channel until its handle is retained, drains
outside the lease/state/worker locks, fences publication through the captured
window lease, handles fallible spawn/panic cleanup, and pins from root to leaf
using opened-handle reparse metadata. Deterministic manager cases cover these
interleavings, including real Windows ancestor rename refusal. Inspection of
the code and cases supports the stated fixes; this is not a human approval.

Commands accept fixed built-in IDs, bounded UUID handles, one/all batches and
exact operation IDs. They expose no arbitrary path, provider, code, report HTML
or shell execution. Status/read use memory; only explicit recovery validates
checkpoints and rewrites derived reports. Source mismatch fails closed. Native
retention limits and boundary quotas are clearly distinguished from hard write
quotas. Report text renders inertly. Story/lens/Play changes revoke controller
presentation before React observes the new context. Inspector authority is not
fed into generation, nor does running a synthetic case mutate the player story.

Root read the controller/decoder/Panel/command boundary, registration cleanup,
context subscription and lifecycle integration. Root visually inspected final
application-owned `initial`, `copy` and `finished` images from
`evaluation-native-18c80080-67b8-40ab-a33e-b13597d60c7e`: run counts/privacy and
fake-provider labels are visible; report sources remain internal; Return to
Play clears evaluation content. Root also viewed the earlier repaired cohort's
narrow, expected/actual and unsupported captures. The author inspected all seven
final initial-stage images. No sampled layout/visible-state blocker remained.
These are hidden WebView2 CapturePreview images, not desktop captures.

Executed tests are attributed to the implementation agent in
`D07_NATIVE_EVALUATION_2026-10-23.md` and its evidence JSON: definitive clean
source4a0a859, 26 distinct native assertions/14 images with actual window/process
restart; built-in runner9 passed/0 failed/3 unsupported,196 checks. The same
source passed five native regression cohorts, frontend/format, default28 native
units/1 existing privilege-related ignore, dev30/1 ignore plus2 harness contract
tests, and both strict Clippy checks. Root did not rerun those author executions
or label its source review as execution. The subsequent changes are docs only.

Full D07.06 remains open: D05/D06 cross-view bridges are explicitly unavailable,
and mocked failure-row SSR evidence is distinguished from actual native runner
results. There is no model-quality, Android parity, traffic-blocked, hosted CI,
performance, signed-package or release acceptance. The separate candidate-worker
checkout's duplicate-React blank-render failure is retained in that owning
packet and is not validated by this source's synthetic cohorts.

Next: merge this reviewed bounded panel slice, then implement the missing report
bindings and actual quality/parity evaluation lanes under their owning tasks.
