# Buffered restart: fresh profile and host build preparation

Refs #14 (M10.02), #13 (supporting M09.06), following open/unmerged #269.
Full task and runtime criteria remain unchecked. This packet prepares source
and an offline build; it does not authorize a guest or qualify a restart.
The [previous guarded run](GUARDED_RESTART_RUN_2026-10-29.md) remains refused.
Its guest, model/app state, source, build and captures remain preserved.

## Fixed profile

The SDK5 contract now names only
`D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-v1/avd-v1`.
That path was absent at preflight. No directory, ledger reservation, guest,
private ADB service or runtime action is created by this source change.
Both the immediately previous `restart-after-metadata-v1` root and the older
`author-restart-controller-v1` root are rejected by the new profile.

The production change is one constant. Two existing test constants match it;
all 28 restart-contract and seven existing fresh-profile method bodies remain
identical. JSON cannot select another root, registry or implementation.
SDK4/SDK5 wire and proof formats, 15/24 mandatory source rosters, one-shot claims,
resource floors, ownership, storage admission and deadlines are unchanged.
The [measured streaming hash implementation](RECEIPT_DIGEST_STREAM_V1.md) is
retained without further tuning or another timing capture.

Pure admission validation checks closed metadata and copies accepted input.
Synthetic matching hash strings do not prove live source freshness, storage
admission or human authorization. Those remain distinct mandatory gates.
Before any future guest work, use the current guarded preparation/SDK5 owner
and the fixed shared D: ledger under the [storage lifecycle](../runtime/android/RECEIPT_AVD_STORAGE.md).
Every earlier guest grant is spent; this prospective path has no boot grant.

## Original profile evidence

Six original methods were committed before the fix. Baseline execution records
three meaningful assertion failures and zero errors: the old constant remains,
the immediately previous spent root is accepted, and the new root is refused.
The other three methods pass. The same six assertions pass after the fix
(5,072 ms/exit1 before; 5,275 ms/exit0 after). The test source is byte-identical.

The broader profile cohort passes **41 methods**, zero failures/errors/skips/
exclusions, in 64,669 ms/exit0, with known capture/cleanup, empty stderr, stable
2,231 tracked raw source hashes and no covered forbidden IO attempts. This
cohort includes the six new and 35 existing methods; the counts are not additive.
Native/SDK/path/socket/ledger effects are refused in the pure fixtures.
Independent AST review confirms only the three constants changed in existing
code and all protected guards and method bodies remain unchanged.

## Build and storage boundaries

The next build uses a separate frozen physical D: worktree. Exact executed
source and artifact bindings belong to its actual receipts; later report
commits must not replace that source attribution. Existing frozen `f1b81363`
and `4c53db36` builds and both original dirty guard worktrees are untouched.

Existing locked Gradle/Cargo/Android caches stay on D:. Installed SDK/Java/Rust
and the existing debug signer stay in place. There is no dependency/runtime
upgrade, download or signing-key copy. The build is offline, with process-local
D: temporary/cache settings, finite owned workers and retained raw captures.
The process reader may be compiled for inspection, never executed here.

The declared incremental budget is 8–12 GiB expected, 14 GiB maximum, including
the new worktree/build outputs, cache growth, captures and recovery. Named-root
before/after metadata and contextual volume free space are observations, not
an OS quota or exclusive attribution. No cleanup or retirement makes room.
Host outputs remain at
`D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-admission-v1` with
matching D: recovery. Model weights, old guests and ignored build outputs
remain in their original locations.

Android execution, complete restart proof, real-model/physical/ARM64 performance
and full app journeys remain separate gates. The other emulator, shared ADB
service and system settings remain untouched. No merge or release occurs.
