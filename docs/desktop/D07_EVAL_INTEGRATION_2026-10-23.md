# Deterministic evaluation integration review

Refs #29 D07.01/.02/.04/.06/.07, partial; #6 original fixtures and #14 gates.
No D07.03 real-model implementation or milestone acceptance is claimed here.
Coordinator root independently reviewed author commits `f69cb8e` and `94848db`,
integrated as `9b84539` and `9eb9c75` on Store2 integration `f5ac344`.
The implementation authors did not approve their own work as human reviewers.

## Review conclusions

Read the runner, CLI, source-binding build script, complete tests, declared
scenario data and documentation. No concrete blocking defect remained in this
bounded deterministic lane. Expected projection values, observation exclusions
and retrieval targets are declared independently before execution. Actual shared
Host/Play/Engine/Store operations supply outcomes; the fake scripted provider
does not grant a canonical bypass. The compiler assertions and production
director-envelope assertions are distinct. Their deliberate omission probes
fail and restore at the specified assertion boundaries, with source attribution.

Scope/revision/observer filtering remains shared code. This runner does not add
an inspector privilege or a second eligibility rule. Read-only Store resume and
recorded Engine replay validate actual state/receipts. Exact retries disable the
provider; cached results must remain identical without another inference call.
Cancellation and stale-writer probes check terminal behavior and canonical state.

New output directories and isolated case attempts are bounded; completed cases
are immutable checkpoints under one file-lock owner. Resume requires exact
source/suite/version binding and consistent case fingerprints. Changed sources
need a new run. Abandoned attempts are retained and never reused as databases.
Report checksums establish consistency, not authenticity or trusted provenance.
The synthetic, developer-owned directory is not a hostile-filesystem sandbox;
concurrent malicious same-user filesystem replacement is outside this proof.

HTML report source is escaped text with no JavaScript/remote assets and a
default-src-none CSP. Bounds and negative cases are tested. The report does not
claim native rendering, model quality, hardware measurements, network blocking
or Android execution. Unsupported scenarios remain explicit unsupported results,
including same-name eligibility, portable archives and summary maintenance.

## Commands actually executed

Windows x64, Rust/Cargo1.93.1, locked offline dependencies, debug0/incremental0,
task-owned D target/temp/output; no model, GUI, device or desktop control.
Source `9eb9c75` has the exact compiled public inputs used below. Subsequent CI
and documentation changes do not alter the runner's compiled-source binding.

```powershell
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <task>/m07-derived
cargo +1.93.1 clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <task>/m07-derived -- -D warnings
cargo +1.93.1 fmt --manifest-path crates/locallore-eval/Cargo.toml -- --check
cargo +1.93.1 run --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --target-dir <task>/m07-derived -- run <task>/d07-eval-store2-final --max-cases 1
cargo +1.93.1 run --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --target-dir <task>/m07-derived -- resume <task>/d07-eval-store2-final
```

All commands passed. Nine tests passed, zero failed/ignored, 2.46s test execution;
strict all-target Clippy and formatting passed. The initial command was not run
because its redirected log directory did not yet exist; creation of that owned
directory preceded the actual successful execution above.

CLI first run completed one case and reported completed=false. Resume reported
12 cases: **9 passed, 0 failed, 3 unsupported**, completed=true,
quality_accepted=false. Report inspection counted **196 checks**, 42 declared
turn inputs (including 32 distractor Wait turns) and two scripted provider calls.
Storage binding is2. The director capture includes compiler_version1, exact
original player-text SHA256 and the required seed commitment source; its presence
flag is true. The narrator's null compiler fields are not fabricated measurements.

Local report JSON SHA256:
`86ff41739c79b1c78e2acca35f77ee49a233c7f4261dea47c3578a9c64e2133d`.
Run binding SHA256:
`a46797008f6f1cb76f740b94380e59c54b12f404f82180610084fb3cff8d8837`.
Raw reports/checkpoints remain task-local; logs are gitignored under
`target/eval-integration-*.log` and `target/eval-cli-*.log`.

The desktop workflow now explicitly checks this standalone workspace. Its source
policy parser verifies pinned read-only tools, ordered evaluation/runtime tests
and strict Clippy, and the final normal native link without development features.
No hosted Actions execution, settings change, app launch or model download is
claimed. Workflow checks use pinned Node24.22.1 and existing locked YAML tooling.

## Remaining work

Story Lab results UI/reruns and D05/D06 navigation remain pending, as do supported
migrations/faults/branch/archive/parity scenarios, real-model and transcript-only
comparisons, measured whole-turn performance and human quality review. This lane
is a tested prerequisite, not full D07 or desktop epic completion. Existing
1,000-event compiler and 10,000-transition property evidence remain separate;
neither is relabeled as newly executed by these commands.
