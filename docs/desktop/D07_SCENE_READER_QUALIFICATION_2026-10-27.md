# Protocol4 retained reader qualification

2026-10-27. Refs #29 D07.06, supporting #25 D04.04. **Supporting Core reader
slice in review; full tasks remain open.** Four independent public reader
controls pass at clean unchanged `bf880f40d86581a7537c8043c266d648804e02af`;
ten existing reader controls pass at `98d80d9e82cf9929bab1ffd20440cc7fa48eebcd`.
This is actual synthetic Rust producer/Host/Store and retained-reader evidence,
not native application, IPC/WebView, model, Android or human-quality execution.
The original **needs improvement** assessment remains unchanged.

The [consumer contract](D07_SCENE_COMPARISON_CONSUMER_CONTRACT_2026-10-27.md)
and independent tests were first frozen at `a94d53b8` before the public facade
existed. That freeze was **UNCOMPILED/UNRUN**, not behavioral RED. Source
implementation `74441afa` is integrated as `90a9f7b0` and formatted at bf880.
Later98 merges only a producer-qualification wording correction: no reader,
test, dependency or runtime byte changes. No reader test/setup/behavior failure
occurred in the first four-test execution. The separate producer and
[Host/capture](D04_SCENE_HOST_CAPTURE_QUALIFICATION_2026-10-27.md) reports retain
their own source/results; their broad tests are not new runs of this reader.

## Read authority and fresh evidence

`scene_v4/desktop_api.rs` adds one retained adapter over the actual strict
Protocol4 loader and existing shared comparison evidence renderer. Its public
`OpenedComparison` has private fields, no serialization/constructor and no
execution method. `open_read_only`, `summary` and `evidence` do not create a
provider, import a story, repair a checkpoint or convert report JSON into an
Engine/accepted Receipt. Existing Protocol2/3 readers/defaults remain separate.

Open retains existing ordinary-path ancestor/arm/reference pins and opens the
existing `run.lock` read-only with exclusive locking; a missing lock is not
created. Root entries are bounded at512, recognized subdirectories remain
left/right/reference, summary is capped at2MiB and shared evidence at256KiB.
Existing ordinary/pin checks refuse symlinks/reparse points. Strict inspection
reconstructs the actual report, pairs its rows with loaded checkpoints in exact
turn-index/arm order, rejects duplicates/unmatched rows and normalizes at most
48 rows without inventing absent artifacts or receipts.

The version1 summary envelope explicitly identifies protocol4 and retains the
complete actual V4 report. Its binding hashes the typed manifest, report and
normalized rows. It states `read_only:true`, `execution_available:false` and
`selected_protocol4_rerun_not_implemented`; retained metadata grants no selected
execution. Report source/evidence/quality statuses are preserved losslessly,
including human0/not_reviewed/qualityfalse. Artifact availability is not source,
privacy or quality acceptance.

`summary(false)` refuses. An authorized summary is an immutable last-validated
snapshot, **not live status or a new source-integrity check**. Each evidence
request first applies the shared native-grant/raw-observer guard, before
binding, row or source probes. Actor raw receipt/capture/output requests return
`Forbidden` even with stale binding, unknown row or corrupt source. Queries use
actual Rust Query2 observer filtering; privileged inspection does not change
what a character knows or what generation may access.

Evidence then revalidates the manifest, reloads the selected actual checkpoint
against its Store database and compares the complete checkpoint with the
retained one. The shared renderer obtains actual before/after prefixes,
receipt/capture/recording/output hashes and query edges. Its envelope remains
read-only with `generation_grant:false`. A cached summary cannot authorize a
changed selected source or repair it; reopening performs strict source checks.
Hash consistency does not authenticate model-output origin or provider
execution. These distinctions are preserved rather than treating a metadata
snapshot as canonical or live authority.

## Executed coverage and setup history

The four new tests use an actual scripted one-scene V4 producer and private
ordinary copies of a closed immutable template. Each live reader owns a
different copy/lock. Whole inventories include every file, directory and lock
byte after reader drop. They verify:

- Lossless/hash-bound actual report summary, normalized rows, explicit no
  execution/quality grant, cold reopen and unchanged source inventories.
- Actual Store receipt/scene provenance and Query2 before/after edges, with
  early native-grant/actor-raw denial ahead of identity/source probes.
- Manifest drift after open refusing fresh evidence and reopen without repair,
  while the old authorized summary remains explicitly immutable.
- Mutual refusal of genuine Protocol3 and Protocol4 sources by the other
  version's reader, without relabeling historical reports.

A preceding package-clean command uses the isolated Eval manifest but names
Android/Desktop workspace IDs. It exits101 with `locallore-android` unmatched;
this is an operational setup refusal, **not test RED**. The corrected clean
uses the root workspace manifest and the verified task-owned target, removes
216 files/381.9MiB in2.4667822s, and changes no source. It is retained as cache
history, not a general instruction to clean an occupied target.

| Actual command/check | Clean unchanged source | Result / command seconds |
| --- | --- | --- |
| First owned cache clean, isolated-manifest mismatch | bf880f40 | FAILED setup, exit101;0.2160254 |
| Corrected owned root-workspace cache clean | bf880f40 | PASS;2.4667822 |
| Four public V4 reader controls | bf880f40 | 4 passed/0 failed/0 ignored;41.3576902, including14.11s tests |
| Strict Eval all-target/local-model Clippy | bf880f40 | PASS;19.4848618 |
| Rust formatting | bf880f40 | PASS;4.1200163 |
| Existing authorization/snapshot/literal reader controls | 98d80d9e | 2+4+4=10 passed/0 failed/0 ignored;43.2703350 |

The final row runs `comparison_reader_authorization_review`,
`comparison_reader_snapshot_review` and `literal_desktop_read`; their test times
are13.33s,14.75s and11.58s. They retain early raw denial, actual Store evidence,
cached-summary/fresh-selected-evidence separation, selected checkpoint/capture
loss/corruption refusal and manifest drift behavior. This is a focused existing
reader regression set, not a new full workspace/native/selected-execution gate.

## Reproducible command forms

From the repository root, use the already provisioned isolated exact-lock cache,
owned target and task TEMP/TMP. Eval is addressed by its own manifest, not a
root-workspace `-p locallore-eval` assumption. These forms replace private paths:

```powershell
$env:CARGO_HOME = '<existing isolated exact-lock package cache>'
$env:CARGO_NET_OFFLINE = 'true'
$ownedTarget = '<owned Rust target directory>'
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test scene_comparison_reader_v4 --locked --offline --jobs 1 --target-dir $ownedTarget
cargo clippy --manifest-path crates/locallore-eval/Cargo.toml --features local-model --all-targets --locked --offline --jobs 1 --target-dir $ownedTarget -- -D warnings
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml --all -- --check
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test literal_desktop_read --test comparison_reader_authorization_review --test comparison_reader_snapshot_review --locked --offline --jobs 1 --target-dir $ownedTarget
```

Windows NT10.0.26300 x64, Rust/Cargo1.93.1 and the existing locked dependencies;
no upgrade or model download. Feature `local-model` compilation is not evidence
of loading/running a model. All process records report clean unchanged source
and retain exact commands, UTC times and exits in local gitignored
`d07-scene-v4-reader-*` files. No private raw prompt/save/path is published here.

## Source/evidence hashes and remaining gates

Source hashes below are at98; reader code/tests are byte-identical to executed
bf880. Retained log hashes identify actual saved command output, not a complete
artifact seal or authenticated evidence origin.

| Public source / retained local file | SHA-256 |
| --- | --- |
| `crates/locallore-eval/src/local_lane/comparison/scene_v4/desktop_api.rs` | `c4c64c5c616484184760a5acbabd225828aaf3152bf000690078571da6b8c2d3` |
| `crates/locallore-eval/tests/scene_comparison_reader_v4.rs` | `2f2f7a04b6bf461623ec1359c0a4bc66cf3858ee1b4369c822feaefdf2f99266` |
| Shared `comparison/desktop_api.rs` | `733a4f0e86d73ae0c5669530217eee2d075e3c1bb0d90ad361d766c059ffd7c5` |
| Unchanged `Cargo.lock` | `4fb7c498ca0ecc62c4ea1f65c63b370ab4336eb75133d08b3a71f5664156cf93` |
| `d07-scene-v4-reader-first-four1.log` | `ff78ecb5fb5d0102d951eae3da275cd3e121b96a5ff8c1b8b92b8d73bd79ddc1` |
| `d07-scene-v4-reader-first-four1-process.json` | `ce4a4d95d28393ae3da0c10383b98e30c302821e06776ccc2b3f618be7dbcc40` |
| `d07-scene-v4-reader-old-reader-controls1.log` | `d721410aed9e4b79c57b1b9b659263c5e1ad0de28784433dcc241f369c863a6e` |
| `d07-scene-v4-reader-old-reader-controls1-process.json` | `9c896b07bd8c343b2046ef1569376f6cc568d7a73f4ba07b4fd4133ba82a8c0d` |

This facade adds no native manager/IPC dispatch, frontend decoder/panel,
selected4 runtime or model grant. Native UI and rendered-image verification
are separate next work; no render artifact exists in this Rust-only packet.
Protocol4 evidence retains its fresh Domain1 Narrator-input and finite-sentinel
limits, not Director/output authentication or universal privacy. Model quality,
actual native runtime cleanup, offline containment, Android/phone and human
review remain unqualified here. Next runnable slice is the separately frozen
native reader dispatch and strict typed UI consumer through existing grant,
binding/context-retirement and close ownership, preserving selected4 as
unavailable and old readers unchanged. No full-task checkbox, merge, release or
settings change follows from these supporting results.
