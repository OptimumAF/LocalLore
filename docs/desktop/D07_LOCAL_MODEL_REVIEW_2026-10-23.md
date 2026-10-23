# Independent review of the bounded curated evaluation lane

Refs #29 D07.01/.02/.03/.04/.05 partial. Reviewer
`/root/resource_metrics_review`, [claim6369054600](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6369054600),
separate `review/d07-local-model` / `source-local-model-review` worktree.
No human prose-quality approval or full D07 acceptance is implied.

## Source and disposition

Started at freshly fetched accepted main
`586e46a0bbcbc0eda9a264762f2b077e40c9944c`, which includes accepted sampler,
private-capture and archive work. Imported unchanged coordinator expected-worker
helper `41f8b70` as `16f9a57`, frozen eval source
`c76d7917cf0cdd4cd17db151dcd8f313709b7b96` as `eaa3366`, and author docs
`4cca5e2` as `593528f`. No duplicate sampler/worker author stack was imported.

One concrete P2 evaluation-coverage defect was reproduced and repaired by the
author before this handoff. No additional blocker found in this finite review.
Author repair `e1f1af2b39941767a00376052197e8f378a9c9c8` is imported as `27d0aab`.
Reviewer owns only NEW `tests/local_model_review.rs` and this document; production
source, frozen fixtures, accepted tests and author tree were not edited by the
reviewer. Final tested source plus independent tests is
`eb796fa2f65041cbdccfd9fe4b73b810babde6cf`; this document follows that execution.
Coordinator owns final integration, publication and acceptance.

### Reproduced director-envelope coverage omission

Frozen c76 checked forbidden text in actual narrator prompts/outputs, but had no
actual-director exclusion flag/assertion. The lineage case asserted a required
ancestor source in the actual director request; its parent/sibling absence checks
used a separate direct compiler invocation. A forwarding-only director leak could
therefore evade the new lane even while that standalone compiler result was clean.

Reviewer regression `8c900f8` compiles the SAME production
`src/local_recording.rs` through a test-only path include. It supplies the existing
public Capture/Target types and a fixed synthetic provider; retrieval targets are
empty, and the unexercised private target-matcher stub is unreachable. It does not
substitute an Engine, context compiler, observer predicate or Host. The probe is
recorder-boundary execution, not a native-model or full-Host leak experiment.

The actual frozen run exited101: **1 passed,1 failed**. Submitted director
requests containing `PARENT-FUTURE-MIST`, `SIBLING-ONLY-SALT` and
`FOREIGN-ONLY-lineage` all lacked a recorded privacy failure. The positive control
passed: the player-known `SECRET-TIDE-731` was allowed in director input and
detected in narrator input. Exact local failure log:
`local-model-review/director-envelope-before.log`, SHA256
`551faabb2fa84b7fb737936a5f472bcfaf8d8c6cb1ac6e0968757c7cf33b1594`.

The author repair adds separate crate-private director/narrator exclusion lists,
a director flag and a distinct per-turn director-context assertion whenever an
actual director request was captured. Director excludes the foreign-story marker
and, for child scope, parent-future/sibling markers. Narrator additionally excludes
the player-only secret. Checks inspect the entire submitted Structured prompt;
standalone compiler checks remain separately attributable. Guard-only turns gain
no fabricated director observation. Only fixed booleans/counts enter results.

Reviewer adaptation `eb796fa` retains the injected requests and asserts the new
specific director flag plus role attribution; all narrator canaries still detect,
and legitimate player knowledge still passes the director lens. The provider's
fixed result stays unchanged. The author also tests policy construction for all
six frozen stories and equality of actual-director turn IDs with new check IDs.
All repaired tests pass. No fixture, core, prompt, profile or model was changed to
hide the original native failures; **no model cohort was rerun**. Historical c76
does not prove actual-director exclusions, and the author documentation now says so.

## Other inspected boundaries

Read the complete lane/recording/CLI/checkpoint/ledger code, six frozen four-turn
stories, original deterministic runner/tests, and source-binding/report wiring.
Native provider construction returns the real RuntimeProvider before scripted
plan construction. Fixture expected commands are assertions, not substitutions
for native output. Both lanes use the production durable Host free-text path,
Play/compiler, validation and Store commit/replay. The recorder is passive; loss
or poison does not select a provider/canonical result. The bounded role-admission
guard can stop an attempted fourth distinct request before provider execution.

Canonical state is read from actual Store replay. Wrong valid proposals are
retained as failures, dependent remaining turns are not run, and other isolated
stories continue. Guard-only cases have zero inference contribution. Accepted
receipt retry is exercised after disabling the provider and reopening the Store.
Original scoped ancestor sources and context checks do not grant character
knowledge or turn inspection data into inference authority.

The native CLI reserves preparation and holds the run lock before hashing/loading
the fixed approved model/worker profile. Expected worker SHA is checked through
the retained opened handle before spawn. Completed checkpoints are checked before
assets are opened on the concrete native CLI path; already-owned native factories
explicitly label startup outside the run. No alternate model/provider/cloud
fallback or renderer-selected execution/path capability is added.

Admissions, role reservations and invocation charges persist across resume.
Unknown interrupted work remains charged; only completed settlements replace
reserved amounts. An incomplete story uses a fresh private DB attempt. File locks
coordinate cooperative owners, and checkpoint/source/raw-size/path/digest checks
refuse inconsistent input. Hashes are consistency checks, not authentication of
files writable by a hostile same-user process. This review did not test OS process
death during an individual ledger write, storage-full faults or filesystem races.

The watchdog requests cancellation and is joined; cleanup is cooperative and
does not promise a hard60-second stop during an arbitrary OS stall. Output caps
are encoded-file/record limits, not hard heap/RSS quotas or per-write storage
reservations. Fixed raw filenames, per-role bounds, case/report caps and escaped
CSP-restricted HTML keep the published report inert. Canonical state, original
raw candidate, displayed fallback and unreviewed human rubric remain distinct.

## Independently executed checks

Windows x64 OS10.0.26300.0; Rust/Cargo1.93.1. New task-owned D:
`local-model-review/target`; TEMP/TMP in `temp-977fea09`; debug0/incremental0,
locked/offline. No model assets were opened or model calls made by this reviewer.

```powershell
$env:TEMP="$reviewRoot/temp-977fea09"
$env:TMP=$env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir "$reviewRoot/target"
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --all-targets --locked --offline --target-dir "$reviewRoot/target"
cargo +1.93.1 clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir "$reviewRoot/target" -- -D warnings
cargo +1.93.1 clippy --manifest-path crates/locallore-eval/Cargo.toml --features local-model --all-targets --locked --offline --target-dir "$reviewRoot/target" -- -D warnings
cargo +1.93.1 fmt --manifest-path crates/locallore-eval/Cargo.toml -- --check
git diff --check
```

Before the new regression, frozen source on the accepted main passed19 default
and20 feature tests plus strict Clippy/fmt. That pass did not cover the reproduced
director omission. After repair, **23 default tests passed** (20lib+3review) and
**24 feature tests passed** (21lib+3review),0failed/ignored; the binary unit target
has0 tests. Both strict all-target Clippy variants, fmt and diff passed. Logs:
`final-tests-default.log`, `final-tests-local-model.log`,
`final-clippy-default.log`, `final-clippy-local-model.log` and `final-fmt.log`.

The third independent case (`0567402`) uses the public runner and a fixed
synthetic unknown-admission ledger fixture. Reusing a completed story keeps its
checkpoint unchanged, retains the extra admission/+3roles/+60s charge, and creates
no new story attempt, later admission or invented settlement. This simulates the
post-reservation/pre-settlement boundary; it is not an actual process-kill test.

Also ran the repaired standalone CLI with **scripted fake inference only**:

```powershell
cargo +1.93.1 run --manifest-path crates/locallore-eval/Cargo.toml --features local-model --bin locallore-eval --locked --offline --target-dir "$reviewRoot/target" -- curated run "$reviewRoot/scripted-standalone" --lane scripted
& "$reviewRoot/target/debug/locallore-eval.exe" curated resume "$reviewRoot/scripted-standalone" --lane scripted
```

Both exits0:6/6stories,24/24turn-cases,390/390checks,18actual-director checks,
17fake-generation commits,6guard-only,1cancel,35roles,0fallback,qualityfalse.
Resume preserved all six checkpoint hashes and24admissions/35roles; no new story
attempt was needed. Reports and `standalone-summary.json` remain private/local.
This is headless synthetic shared-Host execution, not native worker inference or
native IPC/WebView rendering.

The Git fixture content was unchanged. This review checkout materializes LF bytes
(52924B, SHA256 `7133133b8bf34a76438c62cc67a2eb34a98453433edbcccca6c0e21959572a85`),
whereas the author's measured checkout
uses CRLF (55027B, SHA256 `007d71afd310569150012fcf09d1c4d42235625a3b47c0b4c76dcca59d640993`).
The strict source/fixture fingerprints bind actual build bytes; historical
checkpoints are not claimed compatible with this changed source or checkout.

## Historical native evidence and limits

Read source-binding and initial/cached report summaries locally without executing
the native cohort. Initial SHA256 matches
`17b09b316d405a1a00d3d6df9c9bd1e497b34ddeb2157494fe5441a9e660f5fd`;
cached report matches
`30e4db2a2d25be02b08d09903795f8a68f41a3214dce9f4d2b60b26a8dae7a74`.
The supplied c76 evidence agrees with the author report:2/6stories passed,
21/24turns executed,3dependent turns not run,10generation commits,
4wrong-proposal failures,20/297failed checks,7fallbacks and3unreviewed nonfallback
candidates.25roles are15director/10narrator;24completed and1cancelled; qualityfalse.
Read-only totals/peaks and cached startup/no-native-load labels also match.

Those model runs are historical author execution, not this reviewer's or repaired
source execution. No human quality assessment, real old-promise/discovery-dependent
journey or repaired actual-director native exclusion claim is inferred. Preserve
that failed cohort. No device, desktop control, network-block observation,
packaging, performance comparison or release action occurred in this review.

Next runnable task: coordinator reconcile the repaired lane and review tests with
current main, publish a focused partial PR, then separately improve the retained
wrong-action/narration failures before qualifying uncovered real-model journeys.
Full D07 remains open; agent review is not owner acceptance.
