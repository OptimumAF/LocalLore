# Curated evaluation integration and cancellation repair

Refs #29 (D07.01–.06 partial), #28 (D06.03/.06/.07 partial), #25
(current shared Play compatibility). These are adapter and lifecycle results;
the broad desktop, memory comparison, human quality and Android parity gates
remain open. Original author evidence is separately attributed in
[D07_CURATED_UI_2026-10-23.md](D07_CURATED_UI_2026-10-23.md).

The coordinator integrated the packet onto accepted main
`a13b80b8f7e37c1fb2aad714f5ba931f7bf37941`. Production source measured after the
retirement repair is `82c0297af4ed14cc01eb406e6bf239884753d3fe` (clean).
The preceding clean integration `3a0aae28e2409834e248ebe895d56e8808aee09b`
also passed the scripted native cohort; its artifacts remain historical.

## Integration and concrete review finding

Accepted main owns the root Cargo workspace lock. The adapter's one new
eval-to-local-runtime dependency edge was transferred there, with no package
version/checksum/identity change and no revival of the retired desktop lock.
Actual locked/offline metadata passed. Harness provenance now inventories
`../../Cargo.lock`.

The independent review provided unchanged actual-admission tests for a real
registered scripted evaluation job. Root ran them before the repair: **two
failures**, because window retirement used `state.try_lock()` and therefore
missed cancellation when presentation state was contended or poisoned. The
tests hold the existing real worker publication barrier, capture its actual
cancellation token, retire the lease, then release and drain the worker before
asserting. No real model, fake Job replacement or desktop control was used.

The repair gives both evaluation lanes a separate cancellation ownership slot.
Its mutex covers only clone/cancel/replace operations, never I/O, a join, or
acquisition of another manager/lease lock. Retirement cancels matching epoch
ownership before optional nonblocking presentation cleanup. Admission registers
the token and then rechecks the atomically invalidated lease, closing the race
where retirement observed an empty slot immediately before registration.
Completion and spawn-failure cleanup clear only the exact epoch/operation.
Cleanup recovers poison; ordinary presentation operations continue failing
closed. Registration/drain and late-publication fencing remain authoritative
in native Rust. Cancellation remains cooperative.

The original two tests then passed. A further test covers registration after
empty-slot retirement and old-operation cleanup preserving a newer owner.
Original RED log SHA-256:
`2214cb4336474bb5fc5d2c2c29cc4a8b6a3d252d7a9c54693015a35787e76c65`.

## Root-executed checks

Windows 11 Pro 10.0.26300, Rust/Cargo 1.93.1, Node 24.22.1, existing pinned
frontend dependencies. MSVC toolset 14.34.31933 / SDK 10.0.19041.0. Installed
WebView2 versions were present; the exact selected runtime loader version was
not recorded. No model assets were loaded, changed or downloaded.

| Layer | Actual result |
| --- | --- |
| Eval default / local-model feature at integrated 3a0 | 26 / 27 PASS, synthetic only |
| Eval strict all-feature Clippy at 3a0 | PASS |
| Focused native evaluation tests after repair | 16 PASS, including unchanged two regressions |
| Native default after repair | 54 PASS, one existing symlink-privilege ignore |
| Native dev-harness after repair | 56 PASS, same ignore; 2 harness-contract PASS |
| Native strict all-target/all-feature Clippy after repair | PASS |
| Full frontend verifier / Prettier at 3a0 | PASS; strict TS, schema, actual-controller MOCK checks, normal hook exclusion |
| Actual native scripted cohort at clean 82c0297 | 51 distinct assertions, 16 application-owned PNGs, two process launches plus window reopen |

The repair changes only native cancellation ownership and tests. The eval and
frontend production sources retain their earlier measured bytes. This adapter
does not change portable Engine/Host/Store, schema, Android code, curated
fixtures, expected commands, prompts, sampling or runner budgets. Android was
not requalified for this native-only adapter; prior shared-main build evidence
remains separately attributed and final integrated compatibility is still due.

Commands from repository root (use a task-owned target/TEMP and `--jobs 1` when
host memory is limited):

```powershell
cargo test --manifest-path crates/locallore-eval/Cargo.toml --locked --offline
cargo test --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --features local-model
cargo clippy --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --all-targets --all-features -- -D warnings
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline evaluation:: -- --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --all-targets --all-features -- -D warnings
```

From `apps/desktop`:

```powershell
node verify-frontend.mjs
$env:LOCALLORE_D07_TARGET_DIR = 'D:/task-output/native-target'
$env:LOCALLORE_D07_CURATED_ARTIFACT_ROOT = 'D:/task-output/curated-artifacts'
node curated-harness.mjs
```

Process-local `CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`,
`CARGO_INCREMENTAL=0` and task-owned `TEMP`/`TMP` were used. Generated output
stays local outside the repository. No system settings, protected-chat state,
devices or unrelated processes were changed.

## Native artifact review and exact boundary

After-repair private cohort:
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/curated-retirement-artifacts/curated-native-44b1f2ba-76d7-4a33-8117-8cab9913afb0`.
Summary SHA-256:
`a872f69a28d11ccbbb3fb01fb56a927b7addd985677c1500cb309c4fb86cf6bd`.
It records clean source, exact inputs and executable hash. Logs are local in
the task's `core-rust` directory (`curated-retirement-*`); original failures
were retained, including one invocation using an incorrect relative manifest
path, corrected before the valid run.

The coordinator inspected actual app-owned images for bound D05 state, accepted
receipt and raw role output, rejected/no-receipt state, Player evidence,
620-pixel wrapped output, pending, cancelled, lost acknowledgement, pre-retirement
state and process-restarted completed cache. Labels distinguish the live story
from isolated evaluated scope/revision/fingerprint. Result states, unavailable
receipt text and disabled pending controls are coherent; long hashes/raw output
wrap within bounded scroll areas. Automated gates also check every captured
viewport for outer/nested horizontal overflow. This is invisible/unfocused
WebView2 CapturePreview of the application, not a desktop screenshot or
headless/SSR substitution.

Bounded errors contain exactly one expected native Transport normalization in
the initial window's fixed lost-ack journey and zero after reopen/restart.
The visible error remains EvaluationIo. Two Chromium shutdown stderr lines
with `Chrome_WidgetWin_0` Error 1412 are retained, not hidden or called empty.

These results prove the fixed scripted journeys, same-run recovery/checkpoints,
read-only receipt/evidence filtering and unchanged live canon. They do not
prove current-source real-model quality, transcript-only versus verified-memory
comparison, generated long-session quality, peak-memory bounds, physical-phone
parity, power-loss recovery, or complete D07/D06 acceptance. The existing
historical real-model failures remain immutable. Next work is the frozen
source-bound real-model cohort, long-history/shared-memory consumer work,
timeline/correction integration and final package/parity qualification.
