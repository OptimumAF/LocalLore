# D09 local build/package evidence, 2026-10-22

Refs #31 D09.01/.03/.04/.05/.07. Status: **in_review, partial**; all milestone
acceptance boxes stay unchecked. Reviewer/implementer: app_storage_review,
`impl/d09-build-security`, isolated LocalLore-d03-review checkout. Exact claims
preceded edits on #31 comment6358414659 / #7 comment6358414908. The historical
8d427f7/f9d3d39/8e41deb preparation was inspected, not treated as current evidence.

## Exact boundary and method

Initial baseline: accepted `8f3842e10a3258cc801e9d842e13a465bac1f260`.
Final build input: accepted **`18c5c2f7050001f8b23fe2ca74d188ba1c637228`**.
The fast-forward incorporated accepted D05 UI and native formatting correction.
No Rust/Host/play/runtime/native/UI/schema/lock/Android source was changed by this
packet. Only the new desktop workflow, desktop-package scripts and D09 docs are
submitted. Source inputs were clean/committed before and after each package build;
the then-uncommitted packager is separately identified by its exact byte hash below.

Actual build host: Windows 11 Pro, 10.0.26300 x64; rustc1.93.1
`01f6ddf7588f42ae2d7eb0a2f21d44e8e96674cf`, LLVM21.1.8; Node24.22.1,
npm11.19.1, Python3.14.9. Node/Python official portable archive checksums are in
[the build instructions](D09_BUILD_AND_PACKAGE.md). No system tool installation,
global environment setting, signing, repository setting or hosted Actions run was
performed. All new target/cache/package/temp outputs are in the task-owned
D:/CodexLocalLore/.../d09-build-security directory. A finished dependency cache
was copied read-only into this own target; this is not a clean-from-zero build.

Fresh `npm ci --ignore-scripts --no-audit --no-fund` under the pinned Node/npm
completed (32 packages), using a task-local npm cache. Its first dependency
relocation had a differently named node_modules target, breaking sibling lookup.
That failed check was retained in local logs and repaired by copying the same
locked dependencies to the ordinary D: node_modules ancestor. No package/lock
mutation or check suppression was used. Final build manifest has empty NODE_OPTIONS.

## Checks actually executed

All Cargo commands below used +1.93.1, `--locked --offline`, own D: target,
DEV/TEST_DEBUG=0 and INCREMENTAL=0. Native/default/dev commands were rerun on final
18c5c2f. Runtime23-case execution was at8f3842e; Git diff confirms the entire
standalone runtime/native worker/desktop Cargo lock is unchanged through18c5c2f.

| Command / boundary | Actual result |
|---|---|
| Pinned npm `run check` | PASS normal frontend build, TypeScript, 25 original wire fixtures/current builders/hostile wire, delayed export cancellation, model recovery/status races, two D05 inspector context/provenance controller suites, and normal-bundle development-hook scan |
| Pinned npm `run format:check`; generated host TS Git diff | PASS; generated tracked type file unchanged |
| Runtime ordinary `build --features development-worker,engine-adapter --bin protocol-fixture` | PASS before runtime tests |
| Runtime `test --all-targets --features development-worker,engine-adapter` | **23 passed, 1 ignored**; synthetic ordinary fixture, zero-case fixture/probe test targets; no model |
| Runtime `clippy --all-targets --features development-worker,engine-adapter -- -D warnings`; fmt | PASS |
| Native default `test` | **17 passed, 1 ignored** |
| Native `test --features dev-harness` | **19 passed, 1 ignored**, plus **2** integration-wrapper passes (the two harness policy cases are repeated, not two new behaviors) |
| Native default/dev `clippy --all-targets ... -- -D warnings`; fmt | PASS final18c5c2f. Historical8f fmt failed on inherited one-line FILE_DISPOSITION_INFO formatting, fixed upstream by7611297 before this final run |
| `python scripts/desktop-package-tests.py` (Python3.14.9) | **12 passed**; wrong worker before side effects, tampered/missing inventory, resealed extras/weights/save/symbol/traversal, duplicate/symlink/unsupported-compression archive, metadata/notice budgets, policy flags, changed profile/native magic, no-overwrite sentinel, build override refusal and standalone-runtime CI regression |
| `node scripts/desktop-package-workflow-check.mjs` | PASS actual YAML parse and source policy: pinned actions/tools, read-only token, hosted Windows, runtime fixture/test/Clippy order, no privileged/untrusted run interpolation, final normal link |
| Packager `build` and independent `verify` | PASS normal frontend + normal native build, closed folder/ZIP inventory, worker pin, every payload size/hash |
| `git diff --check` | PASS before handoff |

Neither privileged symlink test was explicitly run here. No ignored case is
counted as passed. Root host/Android, C++ grammar/worker/protocol/real-model gates
and prior actual-app journeys were **not** rerun in this packet. No application,
WebView, llama worker/model, desktop/browser/device automation or network-denied
play was launched by these build checks. The runtime test fixture processes are
synthetic test executables, not the inference worker.

## Measured repeatability and artifacts

The first two full package invocations used ordinary `cargo build` at the same
18c5c2f/source path/cache/tools. Input inventories and packager hashes matched;
the executable and resulting manifest/ZIP did not. The executable size stayed
19,131,392 bytes, with SHA256 `693c2c52ad85f92c79e242d1f79c627bb9f91cee70f89341dceea23853cf7f1a`
versus `6d81ffcec51cffc0d8afd8e6734fe8e0efe5dc7fabfd43056fd9fda3b7d13725`.
`dumpbin /headers` reported link times23:10:33 and23:12:19 (2026-10-22).
ZIP SHA256s were `67153eb938abac3d906f7d227c8cb27d2043896817a23849d3d3634f3f47de7f`
and `09717e823ad739fc74610282fb89cb338765d7bf8799191f1b5d751e52111332`.
This demonstrated failure motivated a bounded **packager-only final link** change.

The final packager uses `cargo rustc ... --bin locallore-desktop-spike
--no-default-features -- -C link-arg=/Brepro`. Both subsequent full frontend/native
invocations rebuilt/relinked the final crate and produced **byte-identical**
executable, manifest and ZIP in the same source/target/tool/cache environment.
`dumpbin` reports a REPRO debug directory and timestamp field125B380F. `/Brepro`
is an MSVC-specific option tested with linker14.34 here; this measurement is not a
portable/stable-toolchain guarantee or a substitute for separate-path clean builds.

| Final measured artifact (both invocations) | Bytes | SHA256 |
|---|---:|---|
| `LocalLore Desktop.exe` | 19,131,392 | `27454d3ed939f321f74a791683b2b99f681831849263dbde0435c88374bcb8df` |
| `runtime/locallore-llama-worker.exe` | 6,030,336 | `add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87` |
| Complete 446-member developer ZIP | 9,437,270 | `de51590b4325938b10b1dfdb8a1c575dc5bb60f05df1b1a08cd255a6fb7ada16` |
| Packager source bytes used in both builds | — | `0cf9a45981bf996f4d506e986ae82f08cfdbfac16f206b611d0834bce092ffe6` |

Artifacts remain outside Git under task-local `package outputs/LocalLore Δ developer
18c5c2f brepro[ repeat]`. The manifest in each folder records the full selected
relative source-input inventory and per-member checksums, profile metadata, normal
feature/build flags, tools and incomplete license/installer gates. No binary is
uploaded or attached to this commit. No claim is made that a different source or
target path/compiler/SDK/environment/clean dependency build will match these bits.
The unchanged worker is one prebuilt pinned input; no worker rebuild comparison
was performed. Its non-repro link timestamp/community staging problem remains open.

Static PE inspection found x64/14.34 in both executables. Worker imports include
MSVCP140, VCOMP140, VCRUNTIME140/140_1 and Windows UCRT/system DLLs. Normal executable
imports are Windows/UCRT; no separate WebView2Loader DLL is listed. DLLs/model
weights were not copied into the package. Source review confirms the executable
directory/runtime/fixed worker resource layout; writing/verifying that folder in
a Unicode/space path passed. **Resource/model load or clean-profile app launch
from the folder did not run.**

## Scope/status and next runnable work

D09.01 source threat model is updated; real observed privacy/offline work remains.
D09.03 build commands, checksums and same-environment repeat measurement are
prepared; clean separate-path/compiler/native-worker reproducibility remains.
D09.04 workflow is prepared and locally parsed, not run on GitHub/enabled/made a
required check. D09.05 unsigned folder assembly/static inspection is measured;
license audit, model/native resource loading, missing dependency UX, clean-profile
launch and update/uninstall story retention remain. D09.07 evidence is prepared
for review, not public readiness/owner acceptance. D09.02/.06 are unrun in this
slice. All #31 tasks remain unchecked.

Next: independent review of these scripts/workflow, controlled clean builds from
separate paths including the C++ worker and license inventory, then explicitly
authorized final-package clean-profile/offline/privacy acceptance with installed
prerequisites. Keep signing/installer/public release and repository settings
separate owner decisions. Existing protected-chat resources and other writers'
checkouts/processes were not used or modified.
