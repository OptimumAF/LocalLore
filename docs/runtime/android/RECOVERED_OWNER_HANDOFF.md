# Current owner handoff after preparation recovery

Refs #14 (M10.02), supporting M09.04/M09.06. This extends the
[one-use recovery contract](PREPARE_RECOVERY.md); it does not execute recovery,
migrate the production ledger, authorize boot or qualify Android tests.

## Source admission

Current shared storage validation uses `prepare_recovery_contract.py`, including
for unrecovered version 1 entries. Every current owned-target profile must
therefore bind that dependency before live operations. The shared contract's
`source_bindings()` emits each profile's existing files plus this exact required
file, using current bytes. SDK14 emits 25 files instead of the historical 24.
The existing optional `__init__.py` rule remains exact.

Structural parsers accept only the exact historical set or exact current set,
with that optional initializer. They reject arbitrary extras, duplicates,
mixed parents and missing files. This preserves metadata readability, not live
authority. `revalidate_inputs()` still compares the complete admission against
the current source bindings and hashes. A historical list or changed dependency
must refuse before dispatch. No JSON field selects a different dependency set.

The source decision remains on activation, owner main/worker, runtime, live
lease, controller and client paths. It precedes the existing native, server,
socket, boot and claim mechanisms. This rule applies to all twelve current
profiles using the shared owner; it is not a special exception for SDK14.
Frozen old implementations are unchanged and remain version-1-only.

Full controller replay also revalidates current inputs and product bytes. A
new checker accepting historical metadata structurally does **not** promise
full qualification of an old directory. Use the matching preserved old
implementation for historical replay. There is no live fallback to old source.

## Fixed activation and preserved input paths

The current activation binds these literal trusted locations:

| Role | Fixed path |
| --- | --- |
| Preserved source | `D:/Worktrees/locallore-record-actions-flow-v1` |
| Helper | source root plus `benchmarks/record_controls_ui_activation.py` |
| Controls | `D:/Dev/Experiments/LocalLore/2026-11-01-recovered-owner-handoff-v1/run-controls-v1` |
| Runtime | `D:/Dev/Experiments/LocalLore/2026-11-01-current-recovered-record-controls-ui-run-v1` |
| Guest | existing charged `D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-v1/avd-v1` |

The existing flow worktree's earlier branches and native tests are preserved
before freezing the reviewed current checkpoint there. Its name is not a
permission or profile selector. The helper validates its actual file path and
the source location of imported modules; caller input cannot redirect them.
The old source at `D:/Worktrees/locallore-record-controls-ui-core-v1`, its
pending/spent controls and original SDK14 recipe are not edited or reused.

The fixed B66 APK pair, original byte-attestation baseline, nineteen selectors,
ordinary app IDs, finite deadlines and one-use claim graph are unchanged. No
model, general shell command, arbitrary profile or extra Android method is
added. Current metadata must be generated with `source_bindings()`, rather than
copying the legacy `SOURCE_NAMES` list or retagging an old admission.

The product validator anchors the baseline at its original recorded location,
`D:/Worktrees/locallore-record-controls-ui-core-v1/benchmarks/record_controls_ui_build_baseline.json`.
Moving a reader cannot change that data identity inside the immutable B66
manifest. The byte-identical copy in the current flow checkout remains a
source-roster input; the original data anchor is separately read and hash-checked.
No APK, baseline bytes/hash, recorded manifest, source fact or negative reader
check is resealed or relaxed to accommodate the new implementation location.

## Recovered preparation through owner closure

After a separately authorized recovery produces known SDK/fence cleanup, its
immutable preparation history remains linked into ledger v2. Normal current
run-proposal validation and source/resource/ownership gates still apply.
The shared owner restores the same 40 GiB reservation with the distinct RUN
digest **before** creating the boot claim or launching the guest.

Unknown recovery cleanup or changed/missing history refuses before that claim
and launch. After a run, parent closure still needs its verified worker result,
owner cleanup, handles, final sources and capture. Only then may the real
storage transition record closure. The original preparation digest, intent,
completion and outcome remain immutable; the ledger's current RUN digest and
normal closure evidence are separate. Required external history stays charged.

Host tests exercise real isolated ledger transitions and the actual owner
storage spine, while explicitly simulating build/process/SDK/worker boundaries.
They do not prove a real guest, service, model or native cleanup succeeded.

## Execution gates

A frozen source table and file-only recovery plan are review inputs, not a
fresh preparation result or admission. The real B73 guest still requires its
explicit recovery authorization and current guards. Do not fabricate a fresh
prepare/run proposal, resource observation or known cleanup while its root is
absent. Do not start the current helper with the spent SDK14 grant.

Live migration/recovery and later UI execution need exact applicable authority,
unchanged preserved inputs and fresh storage/resource/port/ownership checks.
Only the owned guest/private service may start or stop. Existing emulators,
shared ADB, settings, model data and prior records stay preserved. No retry,
alternate guest, timeout extension, cleanup or merge is authorized by this doc.

[Verification and retained failures](../../native/RECOVERED_OWNER_HANDOFF_VERIFICATION_2026-11-01.md).
