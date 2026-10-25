# Comparison reader qualification — 2026-10-24

Refs #29 D07.01/.02/.05/.06, partial prerequisite. This is a bounded record of
Root's actual Rust integration checks and retained failures, not a completed
comparison GUI, selected-run implementation, model evaluation, native IPC,
WebView render or JNI qualification. No score, human approval, milestone
acceptance or publication readiness is claimed.

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
pass is **not yet recorded here**; the later two authorization passes are
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

## First selective-snapshot boundary tests: optimization still pending

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
new green result is predicted from the proposed reduction in repeated replay.
Future selected-run planning must independently fresh-preflight both full source
prefixes before reservations/assets; this read capability grants no execution.

## Commands, environment and immutable evidence inventory

All five recorded commands use the source-owned
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

Root must first freeze the fourth oracle, implement the selected validation
with its fresh Query2 guards, and execute the unchanged baseline/corrected
desktop, authorization and snapshot targets, preserving any new failures.
Genuine historical reader execution, broad evaluator/shared/native lint and
compatibility, native grant/lease adapter, strict frontend decoder/controller,
actual IPC/WebView source navigation/render inspection and isolated selected
rerun/cancel/resume/restart remain pending. No Android/JNI/device, model-quality
or human-rubric acceptance follows from these Rust checks. D07.06 stays incomplete.

This sole-document claim
[#29 comment6393653372](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6393653372)
returns to Root at handoff; adoption waits for its active immutable checks.
No existing contract, source, test, artifact or milestone checkbox is modified.
