# Retained Native4 review: execution and visible-state qualification

Refs #29 D07.06, supporting D07.03/.04 and #23. This is development/test
qualification of an existing synthetic report, not another inference cohort,
human quality acceptance, platform qualification or release.

## Scope and unchanged authority

The closed `--native-scene-review-v1` launcher opens the existing completed
Native4 comparison through the actual frontend controller, managed reader,
native IPC and Rust service. It does not rebuild an Engine from report JSON.
It uses a fresh UUID output directory and WebView profile while the original
comparison files remain the read source. The original in-memory fixture's
`stories-v1.sqlite` address must remain absent: this is not durable gameplay
evidence. No start, import, model-load or worker-staging action is invoked.

The source-bound report and completed-resume gates remain authoritative. The
contract permits a genuine completed result or the exact historical
`EvaluationSourceMismatch` refusal, without rewriting an index or weakening
source matching. An observed refusal must never be reported as resume success.
The original source, outcomes, raw samples and both human assessments remain
unchanged. Both human packet assessments are **needs improvement**; no scores
or case-specific approval are inferred.

## Boundary checks before execution

Independent source freezes preceded their production corrections. At
`38d1c90882fe736504af012828404fae6524dc74`, the following checks passed with
clean, unchanged source, Rust/Cargo 1.93.1 and Node 24.22.1:

| Check | Result | Command duration |
| --- | --- | --- |
| Native retained-profile matrix | 44 distinct isolated child cases; two metadata controls; 3 parent tests passed, 1 fixed child ignored | 34.0466485 s; test time 1.12 s |
| Launcher syntax | Passed | 0.0957835 s |
| Synthetic child policy and path/environment checks | Original 16 simulations and five boundary groups passed | 0.1124159 s |
| Full frontend verification | Passed | 17.0239792 s |
| Development strict all-target Clippy | Passed | 9.0293466 s |
| Normal Windows native build, unlaunched | Passed | 12.1029032 s |
| Normal strict all-target Clippy | Passed | 7.8724527 s |
| Rust formatting | Passed | 0.5426746 s |

The native matrix uses ordinary synthetic directories and tiny metadata
sentinels. The two metadata controls do not create links. No symlink, junction,
reparse, SDK/profile canary or sandbox probe was performed. Case-insensitive
Windows environment conflicts are refused; launcher children receive a copied
environment with all inherited `LOCALLORE_*` names removed case-insensitively.
Prospective output is checked bidirectionally against the approved publication
and retained packet before packet creation or startup Git. Source, target and
runtime staging destinations must also remain disjoint.

Exact check families, from the physical D: repository root:

```text
node apps/desktop/comparison-run-process-policy-check.mjs
node --check apps/desktop/comparison-run-harness.mjs
node apps/desktop/verify-frontend.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir <owned-D-target> comparison_run_native_harness::review_profile_tests:: -- --test-threads=1 --nocapture
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --all-targets --target-dir <owned-D-target> -- -D warnings
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --all-targets --target-dir <owned-D-target> -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
```

Use the existing owned offline Cargo home/target, one build job, incremental
disabled and development/test debug information disabled. Set `TEMP` and `TMP`
to physical `D:/Dev/_Temp` inside the actual command shell. These checks do not
establish Android/device/model quality or Windows process-tree containment.

## First launch: preserved startup failure

The first review launch at `38d1c908` exited 1 after approximately 0.570 s,
before packet creation or the first child invocation. The existing
`outsideReviewPacket` guard rejected the legitimate immediate artifact parent:
`path.relative` returned exactly `..`, while the guard accepted only longer
parent-relative paths. No app, native IPC, model or rendering ran.

Independent freeze `3cc3e57f`, integrated as `fa4c76e4`, added fifteen pure
ancestry cases in a sixth boundary group. The unchanged checker reproduced the
failure with no setup error; original 16 simulations and five groups still
passed. Correction `1b488462` added only the two exact `..` alternatives.
All fifteen cases and 16+6 groups then passed, including equality/descendant
refusal and strict ancestor refusal in disjoint mode. Initial formatting of
the added checker was flagged and corrected without changing its oracles.
Final `c3c13a2b` policy and formatting checks passed. Independent source review
found no remaining launch blocker; it was not native execution evidence.

## Second launch: actual native pass, visual gate failed

Frozen source: `c3c13a2b4b6fb68ec9ade34afb00005bfb687b5c`.
Packet basename: `full-comparison-native-0b0f9de2-b8ca-43a8-96f4-1063c376b092`.
UTC interval: 2026-10-29 07:38:32.6310332 to 07:40:15.2129231.

- Launcher exited 0 in 102.5818899 s. Actual hidden, unfocused WebView2/native
  IPC passed 244 journey checks with twelve app-owned PNGs and zero error records.
- All 32 recorded children closed with known outcomes; unknown drain was false.
  Normal frontend/native restoration passed and its products were not launched.
  The outer wrapper launched no child after Node returned.
- Completed resume actually returned `completed`; no source-mismatch exception
  was used. UI-only changes had not changed the shared Core source binding.
- Reservation sequence 0, consent calls 0, no owner and retained evaluations 0
  were unchanged. `modelExecution=false`; no start/import/load/staging path was
  invoked. These observations are not independent physical SDK-load counters.
- All 2,072 retained result files had identical whole inventories before and
  after, including after restoration. Digest:
  `f22cd3ec7c40c8870684b025fe1bcd909a4664e34f92f552779f2068bce429e5`.
  The original in-memory SQLite address remained absent.
- Root individually viewed every one of the twelve images. Completed-state
  operation wording and neutral unavailable guidance were readable. Native
  awaiting-confirmation rendering remains unavailable in a no-start review.
- **Visual acceptance failed.** In the eight fixed artifact views and narrow
  reader view, the sticky selected-context header covered the artifact heading
  and source and partly occluded the phase/error line. Raw output and fallback
  disclaimers were readable, but that does not satisfy visible case framing.
  The 244 automatic checks did not detect this vertical overlap.

The image review is retained separately as
`d07-scene-retained-native-second-twelve-root-render-review1.json`, SHA256
`5d02ade6ec5502c17eec094c4a47d04633b07f699f3c64ea3696e75c4aa5f4a7`.
No failed capture was overwritten. Original model samples/results remain frozen.

## Current follow-up and acceptance limit

Development-only source `ff93361b` adds measured artifact heading/source/outcome
rectangles and selection-header overlap to the existing native snapshots. It
records the PNG/semantic checkpoint before asserting visibility, preserving
failure evidence. This added geometry oracle is not yet native verified.

A separate real-component headless geometry freeze and a small reader layout
correction are pending. Headless browser rendering will be reported separately
from actual native WebView2 rendering. The native follow-up must retain all
twelve fixed labels, original checks, whole-file equality, zero new inference
and individual image inspection. The visible-state gate remains open.

PR #247 and its lower draft dependencies remain unmerged. This supporting work
does not complete D07, establish prose quality, qualify physical Android,
validate the stopped D09 sandbox probes, or accept the desktop epic.
