# Fresh path metadata checks: host verification, 2026-10-29

Refs #14 (M10.02), #13 (supporting M09.06). This is a host-side boundary and
cost improvement. Full mobile lifecycle and physical/model gates remain open.

## Change and boundaries

`benchmarks/receipt_avd_environment.py::safe_path` now calls `lstat()` once for
each target/ancestor and ignores only `FileNotFoundError`. Previously it called
`exists()` and, when false, `is_symlink()` before `lstat()`. Python 3.14's boolean
queries can suppress metadata errors; the previous optional-path loop could
therefore skip an inaccessible ancestor. Permission and IO errors now fail
closed. The final required target existence/file/directory checks remain.

Fresh symlink/reparse rejection, lexical normalization and every ancestor check
remain. There is no cache. Full source/tool hashes, query frames, the three
before-connect/before-send/after-response trust positions, and deadlines are
unchanged. Neither implementation makes checking and opening atomic. Missing
paths and racing disappearance have different observation sequences; low-level
errors can surface earlier, including a nonzero traceback from callers without
a top-level error translator. This is not a promise of identical error tags.

Installed Python was 3.14.7 on Windows. The [official lstat documentation](https://docs.python.org/3.14/library/pathlib.html#pathlib.Path.lstat)
and [pinned CPython source](https://raw.githubusercontent.com/python/cpython/v3.14.7/Lib/pathlib/__init__.py)
explain the no-follow query and boolean/error behavior. No dependencies changed.

## Original adversarial checks

The 12 original Windows tests in `scripts/tests/test_safe_path_metadata.py`
were committed independently before the fix. Against baseline they produced
nine failing assertions/subcases: seven redundant-call expectations and two
synthetic PermissionError/EIO fail-open cases. The exact unchanged 12 then
passed against candidate `010e4bcaa91537a2c2eb5fe577581b75a55efd0f`.
A subsequent Windows-only class guard retained all assertions and also ran all
12, with zero skips, failures or errors. Each finite owner completed in
263–264 ms with known capture/cleanup, empty stderr and four stable input hashes.

Coverage includes real D files/directories/missing paths, relative and parent
traversal refusal, synthetic ordinary/broken symlinks and Windows reparse
attributes, ancestor metadata errors, replacement between separate calls, final
target kinds, and one fresh no-follow query per ancestor. No privileged real
symlink creation or timing threshold is required.

## Fixed benign host sample

The independently frozen protocol runs 10 batches ×25 cycles ×4 cases, or
1,000 calls per phase. Existing file, existing directory, optional absent path
and required absent path yield exactly 750 accepted/250 expected refusals in
both sources and phases. Delegating wrappers count Python methods and add
overhead to both phases; cProfile adds overhead only to its separate phase.

| Phase | Baseline ms | Candidate ms |
| --- | ---: | ---: |
| Unprofiled perf_counter |388.3926|217.2651|
| Separately profiled |480.3754|277.3271|

| Calls per phase | Baseline | Candidate |
| --- | ---: | ---: |
| exists |9000|750|
| is_symlink |500|0|
| lstat |7750|8250|
| is_file |250|250|
| is_dir |250|250|

`lstat` increases because absent nodes are now queried directly. Total counted
calls decrease from 17,750 to 9,500. One fixed sample per source establishes no
distribution or general speedup, OS IO bytes, Android/model latency, or runtime
deadline improvement. The helper/protocol/dataset/fixture metadata and two other
source pins match before/after. Both owners complete with status 0, known capture
and cleanup, empty streams and stable inputs (baseline 1,070 ms; candidate 665 ms).

The old closed runtime case pins the old environment source. Its admission must
reject these changed bytes; its proof was neither repinned nor requalified.
No SDK/device/model operation or emulator boot occurs in this packet.

Private helpers and raw receipts remain under
`D:/Dev/Experiments/LocalLore/2026-10-29-single-lstat-v1` (outside Git):

| Artifact | SHA256 |
| --- | --- |
| Baseline environment source |683886477a040c29595e0737cda4c879a6c0564eeda590c10a3878b484f3a39b|
| Candidate environment source |4faaaa9609d54c050cc5b06dd7606cad7bf38512c2d2cba2d1e5c2e4ecc065c7|
| Fixed helper |e983fe3ee7318e41e9c15ecf734e65dc0db98656abd3110aa161f41ad15d00b8|
| Frozen protocol |d9ada80b7fd6a303d0f5dfea111d7678d8968f6a6987095ccce9a5a60569b936|
| Baseline measurements |f788227ddf6b39ca87720ec681ddc3fce11e7b53356c12a69a5b833dd4ea9d10|
| Candidate measurements |31c90ab6ad7b2e5502f98338054cbf596091ad42ccafba8a05cf80db2f49062f|
| Comparison |17f9fe6a71cedbffc4512e6e93cd4bd0d902065c1a5b519d7e6e00c3b21acc0f|

Actual private commands were `python -I -S -B measure-fixed-v1.py init`, then
`run baseline-v1 <baseline source SHA>` and `run candidate-v1 <candidate source SHA>`
from the physical D measurement worktree, with the same D-resident helper.
`TEMP`, `TMP` and `TMPDIR` were set to `D:/Dev/_Temp` before project tools.

## Broader regression and storage prerequisite

At executable/test source `dcf5b6fa`, the finite Root command
`python -I -S -B <packet>/check-host-v1.py run` discovers 2,151 tests and
executes 2,145 after asserting the exact six exclusions below. All 2,145 pass in
199.603s: zero failures/errors/skips. The owner completes in 204,000 ms with
status 0, known cleanup/capture, empty stderr, zero recorded C-write attempts and
all 2,205 tracked source hashes stable. This includes the 12 new tests; counts
are not additive. No Rust/Android build or device suite was rerun for this
Python-only change.

Private host result SHA256
`420ece118c5f3e81c69721faf06211ff8f9631199cacc1f519bb579715e4fcf5`;
source-bound driver SHA256
`2058af19f1279cb691d44230bbcc17cd8e06e488c9436f874a7df530d1873d29`.
The selected test IDs and exact unrun IDs are retained in its selection receipt.


Six unchanged legacy tests use `c_root()` in
`scripts/tests/test_receipt_avd_environment.py`, which explicitly allocates in
`LOCALAPPDATA/Temp` and asserts C:. Changing TEMP/TMP does not redirect that
allocation. These exact tests remain **unrun**, excluded with a six-match roster
assertion before execution:

- `test_explicit_c_plan_binds_stronger_floors_without_changing_d_plan`
- `test_root_drive_and_floor_pair_are_closed_in_prepare_and_run`
- `test_c_root_preexisting_and_symlink_metadata_refuse_without_adoption`
- `test_c_root_path_shape_cannot_escape_its_explicit_root`
- `test_c_root_capacity_keeps_both_40gib_reserves`
- `test_c_run_preserves_floor_binding_owner_window_and_refuses_replay`

All belong to `test_receipt_avd_environment.EnvironmentTests`. Their original
code and criteria remain unchanged. A Python audit hook rejects and records C
write/mutation attempts in the selected test process; this is not an OS/native
filesystem sandbox. Source review is also not exhaustive IO tracing.

Next runnable prerequisite: migrate these actual-C fixture allocations to
independently reviewed synthetic-C metadata with all real fixture IO on D,
preserving drive/floor/binding/replay assertions and original failure evidence.
Fresh source-bound Android restart qualification still needs its own admission;
the spent guest/run is closed. Physical-phone/ARM64, model quality/performance,
mobile memory/storage pressure and full milestone acceptance remain separate.

M10.02 and supporting M09.06 are **in_review** for this bounded host slice;
full task checkboxes and acceptance criteria remain unchanged.
