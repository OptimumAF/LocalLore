# Approved worker identity before execution — 2026-10-23

Refs #25 D04.02 and #31 D09.01; supports the #29 D07.03 local evaluation lane.
This is a fixed packaged-worker identity guard, not a model-quality or signed
release qualification.

## Change and boundary

Previously `ModelManager::load` hashed/pinned the selected packaged worker but
only recorded its actual digest in the Play profile after starting it. It did
not compare that digest to the application's approved identity before process
creation. The desktop now supplies the compiled reviewed worker digest
`b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`
to `LocalRuntime::spawn_packaged_expected_cancelled`.

The trusted Rust API requires exactly 64 lowercase hex characters. It verifies
the existing approved model and hashes the worker on the same held file guard
that is retained through process lifetime. A mismatch returns WorkerUnavailable
before `start_cancelled` can create a process; cancellation remains Cancelled.
Existing model/worker ancestor pins remain held. Neither a renderer path nor an
editable profile selects the expected identity. The recorded profile still
uses the actual verified runtime digest. Legacy runtime constructors preserve
their existing behavior; this patch changes the desktop caller explicitly.

This guard relies on the installed application and its compiled expectation.
It does not establish publisher authenticity, signing, OS isolation, protection
against a compromised same-user process, full application reproducibility or
blocked-network operation. There is no new model, provider, protocol, dependency
or Android inference backend.

## Review and synthetic checks

Runtime source is `41f8b70`; the desktop adoption is `7021839`. The independent
runtime-lane author read the held-handle comparison and pre-spawn order without
editing them. A separate reviewer read `7021839` and checked the compiled hash
against the existing fixed staging script; no concrete blocker was found. These
were source reviews, not independently executed model or packaging checks.

New runtime tests exercise the actual held-worker helper with a small synthetic
file: exact digest, mismatch, cancellation and denied write/rename while the
Windows guard remains held. The public constructor refuses invalid/uppercase
digest syntax before reading assets and honors early cancellation. Existing
lifecycle, deadline, process reaping, malformed reply, observer/Play and optional
resource tests remain active.

Final clean production `cc93a11db06bc4226f712c7edbee28d99f71316c` includes
accepted main `586e46a0bbcbc0eda9a264762f2b077e40c9944c` (#88/#89/#90).
Windows Rust/Cargo1.93.1, Node24.22.1/npm11.19.1, debug=0/incremental=0,
locked/offline dependencies and task-owned D targets/TEMP/TMP were used:

```powershell
cargo +1.93.1 test --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker,engine-adapter --all-targets --locked --offline --target-dir <native-target>
cargo +1.93.1 clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --features scene-probe --all-targets --locked --offline --target-dir <native-target> -- -D warnings
node apps/desktop/verify-frontend.mjs
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <native-target>
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <native-target> -- -D warnings
```

Runtime: **40 passed, one existing privileged-reparse qualification ignore**;
strict scene-probe Clippy passed. Normal frontend verification passed. Native
desktop **44 module + 2 harness contract tests passed**, one existing ignore;
strict native Clippy and both runtime/native formatting passed.
Logs remain local under `worker-adoption-native/worker-identity-*`.

## Actual native approved-model cohort

```powershell
$env:LOCALLORE_D04_TARGET_DIR='<native-target>'
$env:LOCALLORE_D04_ARTIFACT_ROOT='<private-artifacts>'
$env:LOCALLORE_D04_WORKER_SOURCE='<approved-b5-worker>'
$env:LOCALLORE_D04_MODEL_SOURCE='<already-approved-qwen-gguf>'
$env:LOCALLORE_D04_REUSE_MODEL_ROOT='<existing-approved-app-models-directory>'
node apps/desktop/model-harness.mjs
# Restore normal assets and verify development hooks are absent afterward.
node apps/desktop/verify-frontend.mjs
```

On source `cc93a11`, the actual invisible/unfocused native WebView2 harness
passed **52 assertions and 10 application-owned render captures**, across a
real executable restart using the same synthetic SQLite database. It exercised
explicit approved-model loading through the new guard, pending output, a real
free-text potion transfer, dialogue, rejected unlearned ability, cancellation,
saved restart, observer knowledge and original receipt/retry behavior. These
were the actual UI controller and native IPC paths; no desktop control/input,
system screenshot or unrelated application automation was used. Native picker
post-selection uses the existing fixed development harness, not dialog UI
automation.

The coordinator inspected the pending, accepted receipt and rejected-ability
images. They were populated and readable, with matching story/revision,
noncanonical pending work, displayed fallback provenance and visible Ability
error. The render checks found no RenderError or unhandled frontend error.
Bounded native Cancelled diagnostics were retained. WebView shutdown emitted
the existing class-unregister error1412 after passing checks; it remains in the
local log and is not hidden as a frontend error.

Model: Qwen3-0.6B-Q8_0, 639446688 bytes, SHA-256
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`;
llama.cpp revision `620d2225cc436ab0b001e3200e590e3b286ef9ab`;
approved worker digest above; profile `qwen3-0.6b-q8-cpu-v1`, context4096,
director/narrator350 tokens, 120s turn deadline, one repair, prompt2.2 and
grounded-prose2.1. No new weights were copied/downloaded; the harness staged the
existing approved worker only. Both accepted turns used visibly labeled engine
fallback narration (2/2); no narrative-quality success is implied.

Local directory: `worker-identity-artifacts/model-native-a5927032-b6fe-4ba3-bf75-87438b85cb5f`.
Summary SHA-256:
`9c324a42f348b6db0d3d80e7b409070099f3970f778e88efdf91f0bb05c2e275`.
It records a clean source binding, source/binary hashes, captures, assertions and
both stage reports. Exact WebView runtime selection was not recorded. No
physical device, Android execution, private raw-capture UI, network-blocked or
package/install/release gate was exercised. Next: qualify reproducible normal
application builds separately and retain the larger D07 cohort's honest
wrong-action/fallback failures.
