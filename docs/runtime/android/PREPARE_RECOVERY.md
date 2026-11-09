# One-use preparation recovery

Refs #14 (M10.02). This host operation does not boot an emulator, authorize a
spent UI cohort, remove guest files or cancel a reservation. Gameplay, canonical
events, Android permissions and model dependencies are unchanged.

## Eligibility and authority

`benchmarks.receipt_avd_prepare_recovery.plan(root, failure, output)` makes a
file-only snapshot against the shared production ledger. Tests supply isolated
D: registries; production must use `D:/Dev/_Migration/LocalLore-AVD-Storage`.
Planning never initializes that registry, creates a lock, parent or guest,
generates a fresh SDK proposal, observes processes or invokes Android tools.
It checks that its entry snapshot remains unchanged after reading evidence.

Eligibility is intentionally narrow: the same root is absent, its entry is
`preparing` with the full 40 GiB and no closure/retirement, and a preserved
operator observation records Windows error 3 at the exclusive `root.mkdir()`,
before any SDK worker. The original proposal and operator file are hash-bound.
Only the two reviewed historical environment source hashes whose order is
reserve, exclusive mkdir, then SDK are allowlisted. The original profile is
8 GiB RAM/four cores with the unchanged 12 GiB host-available-memory floor.

An absent root alone proves neither process closure nor absence of a previously
started SDK. An operator observation is not retained native process evidence.
The recovery authorization must explicitly accept that evidence type and bind
the exact plan. A failed/uncertain SDK, different failure stage/source, changed
evidence, prior recovery or nonordinary path refuses. There is no force option.

If the immediate experiment parent is missing, planning records `create_one`.
It does not bypass ordinary planning's existing-parent check or fabricate a
fresh preparation proposal. Actual parent creation and fresh input generation
are deferred to explicitly authorized, exclusively owned recovery execution.
Only one missing parent is permitted; its parent must already exist on D:.

The authorization JSON has exactly these fields:

```json
{
  "version": 1,
  "action": "recover_failed_root_mkdir_once",
  "plan_sha256": "<actual plan SHA-256>",
  "allow_sdk_prepare": true,
  "accept_operator_observation": true
}
```

This is local operator authority metadata, not cryptographic authentication.
It grants one preparation within the reviewed scope, never a guest boot.

## Journal, admission and ownership

`execute(plan_path, authorization_path, output)` rechecks current source,
evidence, exact entry, parent mode and unchanged resource floors. Under the
existing shared admission lock it forces a deterministic create-only recovery
intent **before** parent/root creation. Ledger version 2 adds a required
`recovery` field to every entry: null for unrelated entries, or exact bindings
for `intent`, `completion` and `outcome`. Migration preserves all previous
entry fields and the same root/count/reservation. It releases no capacity.

The intent retains the old entry/proposal/error, current sources, authorization
and new owner identity. There is no rollback or intent deletion. A crash before
ledger publication leaves a spent orphan that current validation refuses;
an incomplete linked intent remains charged. A deleted/changed required record
or malformed pointer refuses subsequent lifecycle operations. Root removal
does not erase the registry intent or permit another attempt.

Windows directory handles hold the existing path chain without deletion
sharing. New directories are created atomically with an already-held native
handle, relative to the held parent. A winning legacy mkdir causes recovery
to refuse; a winning recovery claim prevents the legacy mkdir during guarded
preparation. Child files may still be created. Existing roots are never adopted.
The fence remains held across SDK preparation and its returned cleanup.

Only after the claim does the current environment build and authorize a fresh
proposal. An immutable completion binds that proposal, its normal preparation
authorization and the guest's intent marker. The ledger rebinds the same entry
to the new digest. The existing bounded preparation worker, resource/source
checks, result recording and prepared transition are shared with ordinary
preparation; ordinary `reserve_prepare` is never called again.

After SDK return and fence closure, an immutable outcome records both cleanup
results. Unknown cleanup or any failure stays spent/charged. Retaining for boot
or recording closure requires the successful outcome and verified preparation
result. A proposed state change is validated before writing the ledger, so an
incomplete claim cannot persist an invalid `prepared` transition. Later normal
RUN digests do not rewrite the historical preparation digest or evidence.

All exact required recovery records and pinned source files are counted,
deduplicated, in closed and retired charges and closure measurements. No SDK or
source directory is recursively added. Active preparation retains 40 GiB.

## Compatibility and limits

Version 1 ledgers remain readable and unchanged until explicit recovery.
Frozen version 1 helpers reject version 2. A successful recovery cannot simply
resume PR #338's historical activation recipe: later current-source owner/
admission review and matching execution authority remain required.

Execution must use a dedicated frozen reviewed source checkout. History
revalidates its seven bound source files and the legacy source on each ledger
load, including after retirement. Those physical paths, plans, authorizations
and evidence must remain preserved. Editing or removing them deliberately
blocks lifecycle operations. A snapshot made from an actively edited checkout
is inspection evidence, not a reusable execution grant.

The implementation uses installed Windows APIs through Python `ctypes`, with
no new package, SDK, native library download, privilege or settings change.
The atomic creation API is documented
[NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile)
with `FILE_CREATE`, directory access and a held relative parent. Existing
directory handles use documented
[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
sharing rules. NTFS, identity, reparse and path checks fail closed; no weaker
creation fallback is used. Host checks do not establish Android compatibility.

This fence does not survive process death. When SDK cleanup is unknown, handles
are closed and the root, reservation and history must be preserved; no further
recovery, boot or cleanup is permitted without separate resolution. The journal
does not prove global process absence, resist an administrator rewriting both
ledger and evidence, guarantee power-loss durability of directory metadata, or
recover arbitrary interrupted SDK preparations.

The B73 failed attempt remains failed. Its original records, recovery copies,
frozen source, old proposal and spent SDK14 grant are not rewritten. The
[verification report](../../native/PREPARE_RECOVERY_VERIFICATION_2026-11-01.md)
separates host tests, actual read-only inspection and unexecuted live recovery.
