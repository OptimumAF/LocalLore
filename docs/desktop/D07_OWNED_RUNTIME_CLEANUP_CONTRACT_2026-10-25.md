# Owned runtime cleanup contract — 2026-10-25

Refs #29 D07.06, supporting #25 D04.02/.03 and D09.06.
**FROZEN by Root for independent tests; UNIMPLEMENTED / new tests UNRUN.**
Root adopted proposal `78671188` after an accepted-main baseline: fixed fixture
build exit0; runtime library40 passed/1 existing Windows symlink-privilege ignore.
Those existing passes are not acceptance of the new failure paths.
This prerequisite does not implement native selected execution or qualify a model.
Sole owned new document: this file, `docs/d07-owned-runtime-cleanup-contract`
in reused `source-d07-selected-case-execution`, accepted main base
`7838a7ca6b4e85c59e4139fdebcf1fbec018e998`.
Root integration: `impl/d07-runtime-cleanup-integration` / SourceNative.
Claims: [#29 6396641444](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6396641444),
[#25 6396641582](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6396641582),
under Root claims 6396608770/6396608919.

## Purpose and current source boundary

Keep one existing LocalRuntime and one existing ModelManager, retaining ownership
until cleanup is observed. No new Core authority, Store/schema, provider/backend,
manager, process registry, IPC command/keyset, UI or model/worker asset identity.
The future selected-reservation interface remains under review, not implemented.

Current runtime `load` can return the original error after discarding `fail`'s
cleanup result; Drop ignores kill/wait/join results. `shutdown` calls the protocol
entry, which refuses Status::Failed before cleanup. ModelManager's reservation
Drop clears its ticket; unload/retire take runtime out of the slot, and close
can report unloaded after ignoring failure. These APIs do not provide all-error
cleanup proof. This is a source finding, not a reproduced leak or a universal
OS failure claim. Existing successful worker fixtures are finite evidence.

## Additive owned startup API

```rust
pub enum OwnedStartFailure {
    BeforeChild(Error),
    AfterChild { cause: Error, owner: LocalRuntime },
}
pub fn spawn_packaged_owned_expected_cancelled(
    resource_dir: &Path, model: &Path, expected_sha256: &str,
    cancel: impl Fn() -> bool,
) -> Result<Self, OwnedStartFailure>;
pub fn terminate_and_reap(&mut self) -> Result<(), Error>;
```

The methods are inherent LocalRuntime methods; the enum/owner are not Clone or
Serialize/Deserialize. Implement redacted Debug for OwnedStartFailure: show only
fixed Error/variant, never runtime internals, handles, model paths or raw output.

Use ONE private owned startup implementation and common existing verification/
pipe helpers. Every failure before child creation is BeforeChild. Every failure
after child creation returns AfterChild with the exact retained child, acquired
pipes/thread handles and pinned files, including partial pipe-thread startup.
Do not lose that owner into implicit Drop before constructing the error.
Expected-worker syntax/model/worker verification and cancellation order remain
the same; create the cleanup owner immediately after process creation.

Existing packaged/development constructors delegate this same body. Their legacy
Result<LocalRuntime, Error> mapping retains original cause and existing best-effort
Drop cleanup semantics; do not claim that this old API gains cleanup proof.
The new packaged method uses the same fixed worker basename, reviewed expected
hash and trusted native resource/model arguments. No raw executable, shell,
arbitrary command or renderer path is introduced. The single fixed development
fixture below exists solely to test ownership without approved model assets.

## Direct cleanup proof and retention

`terminate_and_reap` works in every runtime state, including Failed, without
calling the normal protocol operation gate. Mark inference unavailable/Failed,
close the command writer, and act only on this retained Child handle.

1. Observe terminal state, or request termination and positively wait/reap that
   exact child. A kill request alone is not proof. An already exited/reaped child
   is valid; a failed kill can be resolved only by actual terminal observation.
2. Join/drain pipe threads only after the child is known terminal. On error,
   retain every unresolved handle/pipe/thread in the owner for another call.
   Do not drain a vector then silently detach its unjoined remainder. A joined
   panicked thread is terminal; retain remaining unresolved handles and report
   Cleanup rather than treating panic as successful operation completion.
3. Ok means child positively terminal/reaped and owned pipe threads drained.
   Repeating successful cleanup is idempotent. Never resume inference afterward.
   Err means cleanup is not confirmed; retry remains possible with the same owner.

No OS-wide wall-time guarantee is made for kill/wait/join or blocking I/O.
Existing operation/drain deadlines are cooperative control bounds, not proof
of cleanup. Do not clamp elapsed time, refund unknown work, add a budget or
release exclusion merely because a timeout elapsed. Drop remains a final
best-effort fallback, not evidence that lets a caller declare cleanup confirmed.

Keep initial startup/load/generation cause separate from cleanup uncertainty.
For an owned runtime, explicitly clean up after any failure; never infer success
from load's original error or Status::Failed. If cleanup is uncertain, the fixed
external error/status is Cleanup, with original fixed cause retained internally
for bounded diagnosis. No new wire keys or private paths/output in diagnostics.

## Same ModelManager slot and lifecycle

Proposed exact private native adapter method:

```rust
pub(crate) fn retain_uncertain(
    &mut self, runtime: SharedRuntime,
) -> Result<(), SharedRuntime>; // EvaluationReservation method
```

Under the existing ModelManager mutex, require the reservation's matching ticket.
Store the actual owner in existing Inner.runtime **before** reservation Drop
releases that ticket. Same ticket plus same Arc is idempotent. Never overwrite
a different owner. Err returns the input ownership; caller must retain both
reservation and returned Arc, not convert it into a String/drop it on failure.
The normal matching-ticket transfer is deterministic; no second quarantine list.

Quarantine is resident/Failed, loaded=false, error Cleanup. Status/finish must not
turn it into loaded/unloaded or replace the cleanup uncertainty with a success
label. This latch must remain truthful even if the runtime mutex is busy/poisoned.
Existing runtimeSome exclusion blocks load and another evaluation reservation;
the same manager is app-managed across windows. No new owner registry is needed.

Ordinary model load also uses owned startup and direct cleanup, not just future
evaluation. BeforeChild can release normally. AfterChild/load failure keeps the
owner through cleanup; on uncertainty install/retain its same Arc in this slot.
Prepublication load/retirement races must retain exclusion: runtimeNone while a
startup still owns a child is not permission to publish unloaded/start another.

Disable only this owner's configured Host supplier and drain its provider/work
references before releasing ownership. If Arc unwrap is unavailable, retain the
actual SharedRuntime; do not assume close_all proves exclusive ownership. A
poisoned mutex may be recovered only to clean/retain, never resume inference.

Unload/retire/close retain the same Arc while cleanup occurs outside the manager
metadata lock, using direct terminate/reap even for Failed. Clear the slot only
after confirmed cleanup and matching Arc pointer plus current job/epoch fences.
Err preserves it and blocks replacement; a stale cleanup cannot clear a newer
owner. Retirement is not a successful cleanup acknowledgement. Existing unload
is the explicit retry path, not an automatic inference restart or hidden worker.

Track the existing loading job until its owner cleanup/publication completes.
`begin("loading")`, retirement and `finish(original_job, result)` must share
that identity: closing a window while startup is pending keeps replacement
blocked; only the matching old loading completion can acknowledge its cleanup.
It cannot clear another job/owner. A cleanup-uncertain latch keeps status truthful
even while the runtime mutex is held or poisoned. Private field names may vary;
no new serialized lifecycle or second owner registry is introduced.

## Frozen tests before implementation

Root registers separately claimed NEW modules:
`crates/locallore-local-runtime/src/owned_cleanup_tests.rs` and
`apps/desktop/src-tauri/src/models/owned_cleanup_tests.rs`.
Freeze substantive assertions first; retain first compile/actual failures before
fixes. No production factory hook, generic fault callback, server or IPC test API.

Runtime cases: BeforeChild invalid artifact/hash creates no child; each existing
partial-pipe fault yields AfterChild with retained owner; cleanup in Failed
positively reaps the exact duplicated child handle and drains acquired threads;
retry/idempotence. A fixed private cfg(test) cleanup-failure seam, if needed,
must retain unresolved ownership and be default-off with no app/dev wire access.
Test original cause versus Cleanup independently, including load failure and
pipe panic. Known development-worker timing assertions are not universal bounds.

The common private constructor is `start_owned_cancelled(executable: &Path,
model: &Path, file: File, cancel: &impl Fn() -> bool)
-> Result<LocalRuntime, OwnedStartFailure>`; existing raw-path construction stays
private/test-scoped as before. New tests may use it with the already fixed worker.
A private `cfg(test)` thread-local `FAIL_CLEANUP_ONCE: Cell<bool>`, default false,
can refuse once before termination and auto-reset, preserving actual ownership.
Use the same narrowly scoped fault in the model manager's cleanup wrapper;
neither is a production/development IPC hook or a general supplied callback.

Model cases: use a REAL LocalRuntime from the existing fixed protocol fixture;
uncertain handoff before ticket Drop blocks load/reserve; matching same-Arc
transfer is idempotent and another owner/ticket is not overwritten; returned Err
still owns its Arc. Failed unload/retire/close retains resident/loadedfalse/Cleanup,
then explicit successful cleanup clears only that owner and permits reservation.
Cover pending load/window retirement, poisoned/held provider ownership and stale
job/epoch completion; prove no double release or false unloaded report.

Root may claim ONLY a desktop Cargo.toml dev-dependencies entry for the SAME
existing local-runtime path with engine-adapter + development-worker features.
No new package/version/third-party/lock upgrade/download. Test-only feature
unification enables the existing public development-worker fixture API; verify
normal build feature/artifact restoration separately. Build existing fixed
protocol-fixture binary into SourceNative's owned target before these tests.
The existing public development constructor still verifies real model bytes, so
feature unification alone cannot create a synthetic owner in cross-crate tests.
Add exactly one zero-argument, development-worker-feature-only inherent helper:
`LocalRuntime::development_protocol_fixture()
-> Result<(LocalRuntime, PathBuf), OwnedStartFailure>`. It locates only the fixed
protocol-fixture executable relative to the current test executable, creates its
own unique synthetic temporary directory and fixed `valid` mode file, then uses
the same owned private startup. No caller executable/path/mode/arguments or
arbitrary execution API. Return its owned directory for cleanup after the owner;
retain local artifacts on failure. The normal build excludes this helper.
Missing prerequisite fails honestly; privilege-only checks use explicit existing
ignore reasons, never silently claim execution. No models or assets are needed.

Root alone runs serial runtime/native/frontend compatibility and restores normal
artifacts. This document records no baseline/RED/GREEN result. No Cargo/Node/
formatter/runtime/process/model/assets/app/device/CUA/desktop/protected actions
were executed by this author. Root owns freeze, source/test claims, integration
and acceptance; selected native execution and model-quality gates remain open.
