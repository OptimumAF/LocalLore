# D07 deterministic evaluation local evidence

Refs #29 D07.01/.02/.04/.06/.07 **partial, in_review**. Claims on #29
[6359021674](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6359021674),
#6 comment6359021923 and #14 comment6359022164 preceded implementation. Isolated
impl/d07-deterministic-eval/source-eval started at acceptedad586889, then fast-forwarded
before implementation to accepted **228c482c6a3bcfef7bec6a6769ed2207ee054b69**.
Only new standalone crates/locallore-eval/**, fixtures/eval/** and these D07_EVAL*
documents are submitted. No existing core/Host/storage/app/workspace/CI file changed.

## Actual environment and checks

Windows11Pro10.0.26300 x64; Rust1.93.1; Cargo locked/offline;
DEV/TEST_DEBUG=0, INCREMENTAL=0; dedicated D: target and temp paths. No real model,
weights, runtime worker, app, browser/CUA, device/ADB, hosted inference or protected
chat resources were used. No dependency/model download, OS/settings change or
release occurred. The new crate's lock was initially resolved **offline** from
already provisioned reviewed dependencies; subsequent commands used --locked.

Actual commands from the source-eval checkout (task prefix abbreviated):

```powershell
cargo +1.93.1 fmt --manifest-path crates/locallore-eval/Cargo.toml
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --target-dir <task>/d07-eval-target -- --nocapture
cargo +1.93.1 clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <task>/d07-eval-target -- -D warnings
cargo +1.93.1 run --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --target-dir <task>/d07-eval-target -- run <task>/d07-eval-final --max-cases 1
cargo +1.93.1 run --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --target-dir <task>/d07-eval-target -- resume <task>/d07-eval-final
git diff --check
```

Eight runner tests passed, zero failed/ignored. They exercise all built-ins through
actual shared Host/Store/Engine/compiler, scripted production Play, deterministic
retrieval omission failure/restoration, pause/resume/no repeated case, cancellation
before a scenario plus abandoned-DB isolation, future/mismatched/tampered checkpoints,
unknown case/existing output/competing OS-lock owner, invalid suite before execution,
and inert HTML/output limits. Strict all-target Clippy passed. Tests completed in
2.71s in this run; this is a unit-suite observation, **not** gameplay/model/phone
latency or a percentile/performance qualification.

Normal non-test CLI execution first paused with1 completed case, completed=false;
resume produced **12 results:9 passed,0 failed,3 unsupported**, completed=true.
There are **190 checks**,42 declared step inputs including32 accepted Wait turns,
plus the separate lifecycle probes. The scripted production gift made2 fake
provider calls (director+narrator), recorded fallback=false and repairs=0, and
committed the original input with potion owner Mira. No real model was loaded.
The three unsupported results are same-name collision in this frozen Host seed,
playable archive transfer, and production summary/maintenance/fault-injection scope.
They have no pass assertions and are not counted as supported successful cases.

Local artifacts remain outside Git under <task>/d07-eval-final:

| Artifact / binding | Actual |
|---|---|
| report.json |75,172bytes; SHA256 `21a9e4b3406614f1b230c04b86c4e5b6e118164be98939b9361f8d07b9dd9663`|
| report.html |106,887bytes; escaped inert JSON, no browser/render execution|
| run binding SHA256 |`4f8e2fe6adef7e5f289eab5127821fb4ea594e758d5de13f9f723498682496dc`|
| original seed canonical JSON SHA256 |`08794dfdb60eb2fcd33eeb5746dd19e3809259d44d72b61f3fcc9ce69c08c648`|

The report/run manifest contains all exact compiled public source-input/scenario/
schema fingerprints and prompt/policy versions, plus relative names only. The
machine report records model/runtime/hardware as unknown/null, quality_accepted=false,
Android parity not_run, and unsupported quality/baseline/device/offline lanes.
Generated story/session scope IDs are run-specific; deterministic semantic checks
do not promise byte-identical reports or generation across machines. Build-time
source/lock binding makes resume refuse a changed evaluator or pipeline.

## Deliberate failure and preserved earlier failures

The actual test log <task>/d07-eval-tests.log records:

```json
{"id":"old-obligation-target-0","turn":"seed:lantern-quay-v1","stage":"retrieval","status":"failed","expected":{"present":true,"target":{"contains":"return-key","kind":"commitment","source":{"kind":"seed","value":"lantern-quay-v1"}}},"actual":{"present":false,"target":{"contains":"return-key","kind":"commitment","source":{"kind":"seed","value":"lantern-quay-v1"}}}}
```

The cfg(test)-only seam drops Commitment rows from the **actual compiler result**;
no alternate compiler/filter is used and no production fault flag/CLI is exposed.
The same case in a fresh directory without omission then reports passed. This is
finite evidence that the evaluator detects a specified missing retrieved source,
not a claim about model usefulness or an undiscovered production regression.

First local CLI run <task>/d07-eval-run-01 deliberately remains available with
**5 failed cases/nonzero exit**. Those failures were not suppressed or relabelled:
three scenario phase expectations had guessed failed, while source inspection
confirmed durable typed invalid Inventory/Ability/Resource requests are correctly
rejected at submit without mutation; fixtures now expect rejected and retain the
same error and atomic-state assertions. A replay/resume probe incorrectly compared
against a snapshot from before its preceding stale-winner probe; the runner now
loads the current source before replay. The statement retrieval target was asked
under an empty query where the optional duplicate statement row was not selected;
the revised predeclared scenario explicitly queries royal heir and still requires
typed Event1 statement provenance, no power grant, no canonical truth for Mira and
no hidden canary. No shared engine/compiler behavior or gate was relaxed. A later
intermediate run <task>/d07-eval-run-02 passed; final evidence above is from the
frozen source-binding/metadata version, not that earlier schema.

## Open work

Independent source/test review of this runner is required before coordinator
integration. No review score or owner acceptance is asserted by its author.
D07 remains unchecked: same-name/branch/archive/summary/fault cases need their
actual supported shared interfaces; 1,000-event compiler stress is separate;
real-model/baseline quality, human review, whole-turn performance, GUI results/
reruns/D05-D06 navigation, Android/emulator/physical parity and offline observations
remain unrun. The original10,000-transition suite was not duplicated or claimed
as newly executed. Next: independent review, integration, then explicit consumer
and supported-version parity work using these fixed scenarios.
