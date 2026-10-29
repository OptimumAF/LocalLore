# Original AUTHOR external-restart proof v1

Refs #13 (M09.06) and #14 (M10.02), supporting verification only.
This adds an explicit passive post-creation process boundary after the measured
original AUTHOR case. It does not reinterpret the older internal Host reopen
as OS death or permit another AUTHOR call.

## Frozen interfaces and ownership

Root owns this specification, `benchmarks/original_author_restart_proof.py`,
reports/integration. Native specialist owns only the new
`crates/locallore-workspace/tests/original_author_process_restart.rs` real-child
host test. Android specialist owns only the new
`OriginalAuthorRestartInstrumentedTest.kt`. Adversaries own only
`scripts/tests/test_original_author_restart_proof.py`. Each uses a separate D
worktree/branch. No old proof/SDK protocol is changed.

The pure reader exports `validate_restart(raw, artifacts, author_raw,
author_artifacts, import_raw, *, expected_prompt_version="initial-world-v1.1")`.
It returns a deep copy of a valid completed proof or raises `RestartRefused`.
It performs no file, native, network, SDK, process or device access. The original
AUTHOR/import reader must validate the complete supplied baseline first. Data
consistency is not execution authentication; source/APK/target/owner/death and
JUnit records remain separately required.

## Android passive method

Select exactly
`org.locallore.app.OriginalAuthorRestartInstrumentedTest#recordsOriginalAuthorAfterExternalRestartWithoutInference`
in the isolated debug LiteRT app `org.locallore.app.litertverify`.
The fixed original import/AUTHOR namespaces and their database must already
exist. Preserve every original artifact/model. No source-model access, SDK
owner, author generation, PLAYER generation, database replacement/reset, model
copy/import, or reconstructed Seed is allowed here. Extract the original profile
from the bound AUTHOR proof and use only `NativeWorkspace.openLocal` plus
bounded passive commands. New SDK dispatch requires a separately admitted
protocol; the spent SDK4 boot/import/AUTHOR claims cannot authorize this method.

The method requires the same app UID/package and a process start strictly later
than the original AUTHOR process. Numeric PID difference alone is insufficient.
The host must independently establish the exact old process death before this
method; a test method cannot prove that death itself. All files/directories are
fixed under actual Context.noBackupFilesDir, regular/owned/non-symlink, bounded
and create-only. New output namespace: `original-author-restart-proof-v1`.
Use a fresh archive staging child within that namespace, never a model path.

Call native workspace catalog, confirm no pending inference, recover the exact
original job/review-hash/creation-id via `authoring_create`, read the canonical
PLAYER snapshot, repeat exact creation recovery, and re-read catalog. Both
recoveries must return created=false/revision0/the original story+branch, and
cannot insert or regenerate. Close actual passive workspace/archive handles and
check invalidation; unknown closure refuses. Export the whole canonical story
via NativeArchive and retain its exact bytes, equal to the original export.

Proof `proof-v1.json` has exactly:

```
version, scope, status, stage, reason, process, package, elapsed_ms,
import_proof_sha256, author_proof_sha256, records,
pending_before, pending_after, workspace_closed, archive_closed
```

Version integer1; scope `original_author_external_restart_v1`; status completed
or refused; stage one of admission/open/recover/snapshot/retry/archive/close/
completed. Completed requires completed stage, null reason, both pending fields
false and both closed fields true. Failed unknown observations are null; they
never become invented successes. Reason null or one of checks_failed/deadline/
resource_uncertain. Process exactly pid/uid/start_elapsed_ms, positive integers;
UID>=10000; package fixed. Elapsed integer0..180000. Require same UID and a
strictly newer start than baseline AUTHOR, which itself is later than import.

Records is the exact object below, each null or {bytes,sha256}; completed
requires all six nonempty bindings. Files are <=1MiB, combined <=2MiB; proof
<=32768B, JSON strict UTF-8, unique keys, finite integers/bools preserved.

- workspace-before-v1.json
- recover-v1.json
- snapshot-v1.json
- retry-v1.json
- workspace-after-v1.json
- archive-v1.json

The first five are original native envelope bytes (version1/status ok/data,
exact keys). Workspace data must equal the original workspace-created catalog
and each other, with no added/deleted story or changed scope/title/revision/drafts.
Recover/retry data exactly session/scope/revision/created; session opaque
string matching `[A-Za-z0-9_-]{1,128}`; scope equals original create, revision0 and created=false. Snapshot
data equals original snapshot-created data, including PLAYER observer, rules,
inventory and accepted receipts. Archive bytes equal original archive-v1 bytes;
no reparsing/repair changes the captured artifact. Record hashes/counts and the
exact artifact roster must match. The reader exposes no file reader callback.

## Host process-death / PLAYER case

New Rust integration tests use the actual Host+SQLite Store and original public
fixtures with an explicitly scripted provider. Child processes are spawned only
from their own test executable, bounded by parent-held Child handles/deadlines;
barrier/ready evidence precedes parent kill/wait. Commit/lost-ACK recovery and
first free-text PLAYER turn/commit/retry are separated from provider counters;
recovery invokes no inference. A second real child death/reopen must preserve
canon, receipt idempotency and story/observer isolation. All source/input/output
and failed captures remain on D when run locally, with process-local TEMP/TMP.
No child deletion/cleanup removes its database evidence. This establishes host
process-death plumbing, not Android OS death or real model generation quality.

## Gates and non-claims

Compile the Android method and run pure-reader adversaries plus actual Rust
child cases. Android execution remains UNRUN until a fresh concrete reviewed
scope is authorized. Do not boot/reset/relocate an AVD, reconnect/replace ADB,
stop another emulator, reuse closed descriptors, or call a model to make this
host packet pass. Preserve the original failed captures and protocol versions.
Physical-phone/ARM64, actual generation cancellation, broader PLAYER/UI and
quality/performance acceptance remain separate.
