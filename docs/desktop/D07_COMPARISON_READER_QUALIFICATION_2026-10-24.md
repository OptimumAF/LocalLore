# Comparison reader qualification — 2026-10-24

Refs #29 D07.01/.02/.05/.06, partial prerequisite. This is a bounded record of
Root's actual Rust integration checks and retained failures, not a completed
comparison GUI, selected-run implementation, model evaluation, native IPC,
WebView render or JNI qualification. No score, human approval, milestone
acceptance or publication readiness is claimed.

Latest recorded selective-reader source `ddcecbbc` passes14 Rust integration
tests across three targets, with one genuine historical opt-in still ignored.
The source-bound update below supplements every original failure and baseline;
it does not turn these checks into native GUI or real-model evidence.

Documentation base: `32755d70ac9e5fd1453da0fdb87fd255f097cc59`, on isolated
`docs/d07-reader-qualification` / `source-d07-reader-qualification`. Only this
new document is owned. The documentation agent read source, completed logs and
process metadata, calculated hashes and checked its Git diff; it ran no build,
test, formatter, provider, application, model or device. Raw evidence stays
local; basenames and hashes below avoid private absolute paths.

## Contract, source and evidence boundaries

The frozen coordinator Gate1 addendum in
[D07_COMPARISON_GUI_CONTRACT_2026-10-24.md](D07_COMPARISON_GUI_CONTRACT_2026-10-24.md)
owns exact API/JSON shapes, caps and authority boundaries. Its earlier selected
execution/native/GUI proposals are not approved by reader implementation.
Gate1 was frozen at `ac9966f58c017642323efe4b7144616c5cccc21a`, with the
actual Query2 edge-cut clarification at
`3758f5a980661e331b1f62df230200936382e772`. Accepted Archive3 main
`a06109893d678bc8b3b28c5d5ca9d1a4529fdf54` is a dependency only. Its30 PNGs,
795-test cohort and Android results are not this reader's qualification.

The native-only opaque `OpenedComparison` owns directory pins, an existing
exclusive cooperative `run.lock` and an immutable last-validated summary.
Summary/evidence require a native inspection grant; raw receipt/capture/outputs
also require Omniscient. Query evidence uses actual Core Query2 filtering on
`Engine::at_revision(edge)`, with page.head/revision equal to that edge. Returned
data has no generation grant and cannot become a gameplay/accepted-history
capability. Summary is capped at2MiB/48 rows, evidence256KiB, Query2 page64KiB,
private capture196608 bytes. Missing optional evidence stays distinguishable
from present corrupt required evidence; opening creates no lock or run.

Independent frozen desktop tests are original
`b9b10a8a4c596449f8680b69ec526ece1e8354ce`, imported as
`2c00614796f8f34117f3c9d0338d7f0c77d765ed`, then formatted. Actual producer
fixtures use the existing scripted paired/rollout runners, real Engine/Store
and actual recorded captures/outputs. They are synthetic Rust integration
fixtures, not freshly measured native model or GUI artifacts. The reader has
no provider/assets/execution arguments; flags such as `execution_available:false`
are not numerical measurements of zero provider calls. Inventory assertions
check durable nonmutation; no zero-role count is inferred merely from flags.

At the exact documentation base, directly read source-file SHA256 values are:

| Path | SHA256 |
| --- | --- |
| `crates/locallore-eval/src/local_lane/comparison/desktop_api.rs` | `9cd97e921e5b3a3deae85ca9d0f27f9cdab55e8c99c43d157dfb8dcbaa8e2015` |
| `crates/locallore-eval/tests/comparison_desktop_review.rs` | `b81fe0fb5923af9faa6e852f9b4a9d5607f3116d70785091bd4dafab8b0128ff` |
| `crates/locallore-eval/tests/comparison_reader_authorization_review.rs` | `dab706454c70073d4dd9f9156cfb0f9c625cdb7dad0da1ff68a95680af11c6d2` |
| `crates/locallore-eval/tests/comparison_reader_snapshot_review.rs` | `4e6d9d6d3d1bd811d109d6a566c24277e07729fd2fdf1c74ccb4563f4f740e7b` |
| `docs/desktop/D07_COMPARISON_GUI_CONTRACT_2026-10-24.md` | `bf955798ea420cafb34ebbb6c93eff60d2b52de7e14e436da6c6232649beea4b` |

These describe that base, not replacement hashes for earlier immutable test
sources. In particular, the desktop fixture correction below is preserved as
a distinct source change rather than silently changing the first failed run.

## First compile and implementation run

At clean `2c00614796f8f34117f3c9d0338d7f0c77d765ed`, before the new child
API exists, the first command exits101 on compiler `E0603`: the imported
`desktop_api` resolves to the inherited private curated module. Two `E0282`
type-inference diagnostics follow. **No test behavior executes.** The process
record spans `04:02:39.1487966Z`→`04:03:18.9899097Z` on2026-10-25:
39.8411131 seconds for the compile-only failing command, not a printed compiler
duration or test result.

Root implementation `77b56f690cc6773c9a2def5600da05d261e7a5a9` adds the new
comparison child API and its module declaration; the curated change is only
`pub(super)` visibility for its reused pin helper. The first actual desktop
test run then finishes **6 passed,2 failed,1 historical ignored,0 filtered**,
tests1097.48s, compilation8.37s. Process timestamps record
`04:13:14.8704249Z`→`04:31:41.4694768Z`. It finishes naturally; Root's guarded
stop attempt finds PID99104 already gone. **No process was stopped and no stop
record file exists.** No invented stopped/terminated run replaces this result.

Both failures are fixture assumptions, retained verbatim:

- A guard-only row can retain a real capture envelope with empty artifacts.
  The test expected `capture_unavailable` despite actual bytes. The corrected
  oracle preserves the absent receipt, actual empty capture bytes when present,
  missing only when absent, and empty recorded outputs. It does not invent a
  generation context or accepted guard receipt.
- The Windows lock test tried to read `run.lock` through another handle while
  its mandatory byte-range lock was held, yielding OS error33 during inventory.
  The correction compares the complete inventory after releasing the lock;
  it does not omit the file from the final byte comparison.

Tests-only `beb12165b801bb280a5554fe34f2f2ee0a32bcc7` corrects those fixture
assumptions and the authorization fixture's analogous Windows inventory
handling. Production remains the77 reader. A full corrected desktop-suite
pass was **not yet recorded at that checkpoint**; the later two authorization passes are
their own target, not a substitute for rerunning all eight normal groups.
The genuine historical33356-cohort test remains ignored without its explicit
authorized local opt-in; no historical cohort is manufactured by relabeling.

## Demonstrated authorization ordering defect and narrow fix

Independent source review
[#29 comment6393363506](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6393363506)
identified that raw actor requests revalidate private source before checking
their lens. The separately frozen authorization packet is adopted as
`0e654b3249d785aae22cf0e1c77c0d8b2db451c7` and
`e9104783cd573e5f73c75fd3709a20503b46c5a6`, then the tests-only formatting/
inventory correction at `beb12165`. The actual first run at cleanbeb reports
**0 passed /2 failed**,0 ignored/filtered, tests40.78s, compile0.83s.

The two tests collect42 denial probes:18 stale-binding/unknown-row identities
and24 live required-evidence loss/corruption cases. They observe
`SnapshotMismatch`/`UnknownRow`/`Io`/`CheckpointMalformed`/`CheckpointOrder`
instead of `Forbidden` for ineligible raw lenses. This demonstrates a closed
admission/error-order defect, not a proven payload leak or Core authority bypass.

Root fix `7c1d7bdaf2ff84aa51005fdb6ab3c5ab3cac06e2` classifies raw observer
eligibility immediately after the native grant, before identities or source
I/O. The same two tests then actually pass: **2 passed,0 failed,0 ignored,
0 filtered**,27.46s, compile5.59s, clean source unchanged through termination.
All42 denial expectations remain, along with permitted Query2 corruption
refusal and full post-release inventory equality. Legitimate raw Omniscient
requests still validate actual evidence rather than hiding corruption as missing.

## First selective-snapshot boundary tests: pre-optimization checkpoint

The frozen three-case snapshot source is original `c5aaf382`, adopted as
`32755d70ac9e5fd1453da0fdb87fd255f097cc59`. Root runs it against unchanged
whole-replay production7c. Actual result: **2 passed /1 failed**,0 ignored/
filtered,40.98s, compile0.86s. Manifest drift refusal and selected checkpoint/
capture corruption refusal pass. The unselected-diagnostic case fails with
`CheckpointMalformed`: rereading the entire cohort on each evidence request
prevents serving a valid selected row from the retained last-validated snapshot.
This is an actual baseline failure for the explicitly revised snapshot contract,
not a claim that selected corrupt data should be ignored.

Bounded independent source recommendation
[#29 comment6393602802](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6393602802)
supports the proposed selective design only within its stated limits: whole
cohort validation at open; private cached native manifest/key/validated rows;
fresh manifest equality and selected `load_turn` plus complete encoded-checkpoint
identity; and fresh before-input/after-output/mechanical fingerprint checks on
the same immutable Store engine cuts used for Query2. Selected raw artifacts
retain their immediate byte/hash/cap checks and early actor denial. Summary
remains an immutable last-validated snapshot, not live whole-cohort health.
The retained run lock is a cooperative writer contract, not global OS immutability.

At this document's32755 checkpoint the selective optimization is not implemented
or measured. A fourth coherent selected timing/checkpoint-drift oracle is being
frozen before implementation; it has no execution result here. No speedup or
new green result was predicted from the proposed reduction in repeated replay.
The later executed update below records the actual implementation and results.
Future selected-run planning must independently fresh-preflight both full source
prefixes before reservations/assets; this read capability grants no execution.

## Commands, environment and immutable evidence inventory

All recorded commands use the source-owned
`<task-root>/d07-comparison-view-eval-target`, existing locked/offline dependencies,
one job and serial tests. Root's wrapper sets `CARGO_PROFILE_DEV_DEBUG=0`,
`CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`, `CARGO_BUILD_JOBS=1`,
`LIBSQLITE3_FLAGS=''`, and `TEMP`/`TMP=<task-root>/memory-controls-temp`.
It refuses to overwrite prior logs/process records and checks clean source at
entry and unchanged source at termination where present in the recorded metadata.
No toolchain version is newly queried for this documentation task.

From repository root, exact argument templates (private target path replaced):

```text
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <d07-comparison-view-eval-target> --test comparison_desktop_review -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <d07-comparison-view-eval-target> --test comparison_reader_authorization_review -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <d07-comparison-view-eval-target> --test comparison_reader_snapshot_review -- --nocapture --test-threads=1
```

`local-model` is a compilation feature for these actual scripted fixtures,
not evidence of executing a real model or opening approved native model assets.
The first template was used for both initial compile and implementation runs;
the second for both authorization runs. Exact sources and exits are in each
paired process record, all of which report terminal status:

| Local artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `d07-reader-first-before-api.log` | 4245 | `8c2982f6e2d8ae12cc82828f1106bcb701c292d5e2ee013170f50aac10c05611` |
| `d07-reader-first-before-api-process.json` | 664 | `46e64849989147fde26e8ded1daf95498bcc42a7ebf00ada422012a701496620` |
| `d07-reader-first-implementation.log` | 3319 | `935f374b80ed07ede0a69ac08b36b4c89532370456e224c95e680feb39dc5930` |
| `d07-reader-first-implementation-process.json` | 664 | `9688d94b3e748fb4631e3d59f920b37a95d5e468340c03d40bac6d10b18c260a` |
| `d07-reader-auth-first-red.log` | 2890 | `c916e162a714c1a145a488fefb30d4268d4901735cff926b82497e7b78b98088` |
| `d07-reader-auth-first-red-process.json` | 710 | `f057bbcda33cf2ef80ac2d3229641437758f2a0748a5671d279954b3c5eb599b` |
| `d07-reader-auth-first-corrected.log` | 753 | `231a1aba6d17b35dd85a33411702350196143e5dc16608850d21fe32c2bcb4e8` |
| `d07-reader-auth-first-corrected-process.json` | 708 | `26394a223d1daca5c5f0e4b385fd43f286bbc9201b99c13529a9fd2baa4836f3` |
| `d07-reader-snapshot-first-red.log` | 1414 | `ffafbfb747a1cac96478b03037953c9970bbebdc29c641a519bb0b4e6f540502` |
| `d07-reader-snapshot-first-red-process.json` | 705 | `ec9a0573ea02f7cfab9a2b0391072d60a13ccad4d24ff74799aab95943fd35fe` |

## Remaining gate and handoff

The fourth oracle, selective implementation and three-target execution were
pending at the initial handoff and are now recorded below. Genuine historical
reader execution, broad evaluator/shared/native lint and
compatibility, native grant/lease adapter, strict frontend decoder/controller,
actual IPC/WebView source navigation/render inspection and isolated selected
rerun/cancel/resume/restart remain pending. No Android/JNI/device, model-quality
or human-rubric acceptance follows from these Rust checks. D07.06 stays incomplete.

This sole-document claim
[#29 comment6393653372](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6393653372)
returns to Root at handoff; adoption waits for its active immutable checks.
No existing contract, source, test, artifact or milestone checkbox is modified.

## Executed selective-reader update — 2026-10-24

Root first freezes the fourth snapshot oracle at exact
`ad11481ee86659530022451b49fb455c077028d0`, before changing production7c.
The actual old-code baseline runs just
`coherently_changed_selected_checkpoint_is_valid_now_but_not_the_original_opened_snapshot`:
**1 passed,0 failed,0 ignored,3 filtered**,15.65s, compile0.96s. It deliberately
updates selected checkpoint elapsed time and its actual admission settlement
together, proves the existing producer inspector accepts the internally
consistent diagnostics, then requires the old opened binding to refuse them.
This is a passing preservation oracle, not an invented defect or RED.

Root implements selective validation at clean
`ddcecbbc81c08f2340b9076aa063160652df1c49`. Source inspection shows:

- Full cohort/report/reference validation still occurs at open under retained
  directory pins and the cooperative exclusive run lock. Native manifest, key
  and validated `StoredTurn` arrays are retained privately with the immutable
  summary; no public serialized capability or execution API is added.
- Evidence preserves early native/raw-lens authorization, binding and known-row
  checks. It freshly validates the entire manifest and requires full equality,
  calls existing `load_turn` for the selected actual index/arm/policy/key/path,
  then compares the complete encoded checkpoint, including timing/diagnostics,
  to its captured value. Receipt/capture/recording/raw hashes and caps stay fresh.
- Query2's separate Store read uses `checked_edges`: actual before-input,
  after-output and mechanical fingerprints must match that validated selected
  row. The returned page is built from those same immutable checked engines.
  No alternate resolver, context authority, persistence or provider is introduced.

The contract gains the explicit selective-validation decision. The opaque
summary is the last fully validated snapshot, not refreshed whole-run health.
Unselected diagnostics may change behind a noncooperating writer without
invalidating independently unchanged selected evidence; reopening still checks
and rejects the whole damaged cohort. Prefix Play diagnostics are deliberately
outside actor semantic fingerprints; no global private-history freshness is
claimed. Future execution still requires its own fresh full two-arm preflight.

Root's actual combined command finishes at the same clean source with exit0
and `terminalSourceUnchanged:true`:

| Target | Passed | Failed | Ignored | Filtered | Test time |
| --- | ---: | ---: | ---: | ---: | ---: |
| `comparison_desktop_review` | 8 | 0 | 1 | 0 | 241.40s |
| `comparison_reader_authorization_review` | 2 | 0 | 0 | 0 | 15.94s |
| `comparison_reader_snapshot_review` | 4 | 0 | 0 | 0 | 34.09s |

Compilation is6.92s. Process timestamps are
`2026-10-25T05:01:09.5104188Z`→`2026-10-25T05:06:09.2448971Z`,299.7344783s
for the whole three-target command. These are14 passing tests/one historical
ignore across3 targets, not a broad workspace qualification or real-model run.
No elapsed-time pass/fail threshold was relaxed. Comparing this run to the
original1097.48s target is not a controlled speed benchmark: fixture corrections,
the clarified snapshot behavior and combined target selection differ. Report
the exact durations without a generalized throughput or model-speed claim.

The eight desktop groups now include the corrected real empty guard capture
and full post-release Windows lock inventory cases. Authorization retains all42
denials, permitted-query corruption refusal and nonmutation. All four snapshot
groups pass: manifest drift, selected source/evidence corruption, unrelated
diagnostic isolation with whole-cohort rejection on reopen, and a currently
valid but changed selected checkpoint versus its old binding. Earlier first
compile, fixture failures, authorization RED and unrelated-diagnostic baseline
failure remain above; this success does not erase or reclassify them.

At exact executeddd, directly read file SHA256 values are:

| Path | SHA256 |
| --- | --- |
| `crates/locallore-eval/src/local_lane/comparison/desktop_api.rs` | `dd18d79147ad8fc41a08409bafdb3fe9577a639fd749172a3285d9fc54d162ac` |
| `crates/locallore-eval/tests/comparison_reader_snapshot_review.rs` | `5ff953c46371e903a7b34e6d42c47f2cbe848691fae912bd57e3775f1690b89b` |
| `docs/desktop/D07_COMPARISON_GUI_CONTRACT_2026-10-24.md` | `5ece5b797f96db42d25594a071ac5ebeaeeffc4f11c00492399c4a8972c2a1b32` |

The documentation agent verifies the source delta and reads these exact files;
it does not independently execute the tests or declare a human approval.
Commands use the same source-owned target and environment as above:

```text
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <d07-comparison-view-eval-target> --test comparison_reader_snapshot_review -- coherently_changed_selected_checkpoint_is_valid_now_but_not_the_original_opened_snapshot --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <d07-comparison-view-eval-target> --test comparison_desktop_review --test comparison_reader_authorization_review --test comparison_reader_snapshot_review -- --nocapture --test-threads=1
```

| Immutable local artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `d07-reader-snapshot-coherent-first.log` | 644 | `bdd17fb3628ab71ce88421b65c5841f856059b779ddacc9536a3b152e0ad3e6d` |
| `d07-reader-snapshot-coherent-first-process.json` | 800 | `cde94e3c72df68eab3b0c3cb1a4dc577e35fae4e0b36b2de9d6c205bf473fe66` |
| `d07-reader-selective-first.log` | 2800 | `fc8e958f27f6636cfd72c169df01c48e5a9b233f6098169d14cb5869361b31ec` |
| `d07-reader-selective-first-process.json` | 814 | `883d59869d03a2c799327c7a34d7daab49caadaaa7b1c414f93751220843dcc41` |

Remaining limits are unchanged: genuine historical opt-in is not executed;
numeric new provider-role counts are not inferred from summary flags; new
native IPC/WebView/JNI/GUI/source-navigation and selected execution gates are
not satisfied. Broad evaluator/shared/native checks and final integration
review remain pending. No old Archive3 execution is relabeled as this reader's
qualification, and no model-quality or D07 milestone completion is claimed.

The follow-up sole-document claim
[#29 comment6393755038](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6393755038)
returns to Root. The commit chain stays on the isolated documentation branch
above `f1117632`; the documentation agent does not cherry-pick into Root.

## Root follow-up qualification — 2026-10-25

The historical test is no longer merely ignored: Root explicitly opts into the
genuine retained original33356 rollout, without generating, repairing, relabeling
or executing it. At clean `a9c95e6bccecd2087d95f5a65fc774f9bf367611`:

- `comparison_desktop_review --ignored`: **1 passed**, 8 filtered, 11.16s.
  The new capability's summary preserves the original report and every original
  file byte, reports historical source mismatch, and grants no execution.
- `comparison_historical_readonly --ignored`: **1 passed**, 0 filtered, 3.19s.
  The older pre-forwarded-budget report remains viewable and cannot resume.
- Whole command compilation7.60s; actual process05:26:57.4527322Z→05:27:20.5902598Z.
  This is historical read validation, not new historical-model generation.

Preserved regressions at unchanged clean `ddcecbbc` also pass:

| Target | Passed | Ignored | Test time |
| --- | ---: | ---: | ---: |
| `comparison_resume_basis_review` | 5 | 0 | 592.00s |
| `comparison_runner` | 9 | 0 | 253.41s |
| `memory_comparison` | 12 | 0 | 11.64s |
| `memory_comparison_v2` | 3 | 0 | 0.03s |
| `comparison_historical_readonly` default | 0 | 1 | 0.00s |
| `curated_integration_review` default | 0 | 1 | 0.00s |

Thus29 actual passes and2 explicit opt-in ignores, across6 targets. Build4.04s;
process05:08:57.8135867Z→05:23:21.7882664Z. The first default historical ignore
is subsequently exercised above. The separate historical curated-v2.2/schema2
test remains unrun by this cohort; its old fixture is not synthesized here.

Independent frozen private edge guards `6d0cb83f` are adopted as `8dbed0f0`,
registered at `a9c95e6b`, then actually pass **4/4**, 47 other library tests
filtered, 4.22s/build5.72s. The positive obtains actual producer Store engines,
cuts actual before/after revisions and queries those immutable engines. Three
negative cases use genuinely Core-accepted alternative histories to isolate
the input-prefix, semantic-output and mechanical fingerprints independently.
They do not deserialize an accepted receipt or plant canonical SQL.

The first formatter check at clean `a9c95e6b` exits1 for this newly frozen
unformatted test file. Formatting-only `23c769b7` preserves its assertions.
First strict Clippy then exits101 on its `.err().expect()` helper. Root fixes
that helper with an explicit result match at
`b582f501bf0b4d89975ecfc915a1f88c3596cbe2`, preserving the same failure oracle
and avoiding any new Debug requirement or lint allowance. Corrected formatter
and all-target/local-model strict Clippy both exit0; Clippy finishes5.71s.

At the same cleanb582, the **entire evaluator library** runs **50 passed,
0 failed,1 ignored,0 filtered**,52.12s. This includes all4 private edge tests,
clock/admission/unknown-reservation/forwarded-budget checks, curated reader,
actual deterministic regression injection and restoration. The expected caught
synthetic poison panic and injected retrieval/forwarding failures appear in the
retained log and their tests pass. They are not unhandled product failures.
The one ignored test needs explicitly approved pre-owned native assets; no new
model assets, provider execution or ownership qualification is inferred here.

All commands below are actual, locked/offline, one-job, serial-test commands
using the same owned target/environment described earlier:

```text
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <owned-target> --test comparison_runner --test memory_comparison_v2 --test comparison_resume_basis_review --test comparison_historical_readonly --test curated_integration_review --test memory_comparison -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <owned-target> --lib local_lane::comparison::desktop_api::tests:: -- --nocapture --test-threads=1
# Explicit LOCALLORE_D07_HISTORICAL_COHORT points at the genuine retained original.
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <owned-target> --test comparison_desktop_review --test comparison_historical_readonly -- --ignored --nocapture --test-threads=1
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml -- --check
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <owned-target> --all-targets -- -D warnings
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --target-dir <owned-target> --lib -- --nocapture --test-threads=1
```

Every following completed process record reports clean start, terminal status,
unchanged source and the exact command/source/timestamps/exit. Logs and records
remain local and immutable:

| Log stem | Exit | Log bytes | Log SHA256 | Process-record SHA256 |
| --- | ---: | ---: | --- | --- |
| `d07-reader-preserved-regressions` | 0 | 4843 | `9bf904c75368532b82995ccf66e045d813b52010a6516a9d7f59a7bcca923d38` | `0e491cd19d42fa2c3d62c2782113571852a8d0d89b18beeb01403dc7d0bd55b9` |
| `d07-reader-edges-first` | 0 | 1042 | `0034fefc759de590cac1323578d2398a1b4ff89df37abd7805ca865c15db57b0` | `a5dc8525d7cfb101726af5b339ce8b8e333b71238bf2df12f20bc2164be10557` |
| `d07-reader-historical-first` | 0 | 1035 | `444c30ed3332026353ff4e4b7b0cd8d3625c2a4691edd7f4a11a885af72d86c4` | `aeef03dcad881aca3dc1ae35078f0dc2e2c82885ef0c96a7e2250c2a22a64d9a` |
| `d07-reader-format-first` | 1 | 15988 | `f9ee3592367fc862508ac063d48933a3c240062d799ae9022f8c4487fb535f5c` | `0e6bc040ff6eb28ae8e8a60bf203cc0b5e2c6f8d1462fceb44925ac0d886c407` |
| `d07-reader-clippy-first` | 101 | 2141 | `91a37ae3fe7ea2b6b480d2fdf4896a0c3d9e1b9ef5acaff14469addf5aff9531` | `91ad7b2de7854794104c50f4ae9fc0c6fe6b1c945e2826432b70d47a2aa2db1c` |
| `d07-reader-clippy-corrected` | 0 | 211 | `3756fea9b302b3b850d71f89678b459bbe2376246a7329abedaec77f94697ed3` | `9f2b718126bf10ae8a4ca48e4676714c5fd7bf0edf53035400c1f8c2f489c9f2` |
| `d07-reader-format-corrected` | 0 | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `445b135acf4987a1d02de4a35784f1e1811ffefbccbf4091db1d3db677947c6a` |
| `d07-reader-library-final` | 0 | 7352 | `ea457f6ef5139bdb27c501bb6c3eb28507fb425ef42de4e1b36714a3e824270c` | `801bc1ec0a5c2eb1bb8fdf004302ef879ad5b046d92446582208f6765c5c2ad8` |

Root subsequently integrates the separately frozen native/frontend contract on
`impl/d07-comparison-native-ui`. Its frontend checker first reports67 checks,
normal build and TypeScript pass; the full frontend verifier subsequently passes
at clean `034905ca81b698d9429af4d691f5c06177de231c`. These synthetic transport,
decoder/controller and existing headless checks are not native IPC/render proof.
The first native reader compilation is currently pending there. Native ownership,
IPC, images, Android compatibility, final review and selected execution remain
separate gates; this reader qualification closes no D07 checklist item.
