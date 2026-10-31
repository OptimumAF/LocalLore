# Exact-image retirement executor

`benchmarks/receipt_avd_retirement.py` implements the host boundary identified
by the [archive UI storage preflight](ARCHIVE_UI_STORAGE_PREFLIGHT_2026-10-30.md).
It removes only the reviewed image objects of one tracked closed guest, under
the shared receipt admission lock. It does not prepare or boot a guest, run
ADB, remove directories, change settings, or infer permission from a report.
M10.02 / supporting M09.06 remain subject to complete criteria and owner acceptance.

## Approval and inputs

Actual image retirement needs explicit owner approval for its exact scope.
Records-only recovery cannot restore discarded disk/RAM state. Preserve every
non-disposable guest file, the external owner proofs and their transitive raw
captures before proposing destruction. Keep private credentials, diagnostics,
device identifiers and model material out of the public repository.

The current [storage contract](RECEIPT_AVD_STORAGE.md) still owns admission,
plan and tombstone formats and charging. `plan_retirement` hashes image bytes
and pins the plan while holding the shared lock; it changes the ledger even
though it does not delete images. A private read-only preview is not that
pinned plan. Do not invoke planning or execution on the production registry
outside the applicable authorized operation.

For proposal preparation, `preview_retirement` and the fixed-registry
`benchmarks/receipt_avd_retirement_preview.py` CLI instead produce an unlocked
read-only snapshot. They recheck the ledger, complete file roster, preserved
records/evidence and closure bindings around strict image hashing. They do not
initialize or lock the registry, pin a plan, reserve capacity, delete images,
or start a process. An observed admission lock or changed input refuses.
The CLI writes only its explicit fresh output file, whose existing normal D:
parent must be outside the registry and every tracked guest root:

```powershell
python -I -S -B benchmarks/receipt_avd_retirement_preview.py --root D:\tracked\closed-guest --evidence-manifest D:\preserved\guest-manifest.json --output D:\proposal\preview-v1.json
```

These are placeholder paths. The exact outer snapshot envelope cannot execute
as a retirement plan. The snapshot is neither concurrent exclusion, permission,
an admission reservation nor a future ownership guarantee. A later approved
operation must freshly check and pin the exact plan under the unchanged shared
guard. Existing pinned plans are left unchanged. Partial report publication is
retained on failure; the CLI never overwrites or creates parent directories.
Keep reports private: they contain local paths and file fingerprints. Credential
evidence may be hashed by existing strict checks; this does not authorize copying
or publishing keys. See the [frozen contract](RETIREMENT_PREVIEW_CONTRACT_2026-10-31.md)
and [executed verification](RETIREMENT_PREVIEW_VERIFICATION_2026-10-31.md).

The executor requires an already pinned unchanged plan and its exact file
digest. It does not generate, adopt or replace a plan. Production `execute`
and the CLI select only the fixed shared registry. `_execute` is an internal
seam for isolated tiny test registries, not an authorization boundary for
untrusted Python callers.

From a physical D: checkout, after the concrete operation is reviewed and
authorized, set process-local TEMP/TMP/TMPDIR to `D:\Dev\_Temp` and use:

```powershell
python -I -S -B benchmarks/receipt_avd_retirement.py --plan D:\approved\plan-v1.json --plan-sha256 <reviewed-digest> --output D:\approved\execution-v1 --execute-reviewed-plan
```

The paths and digest above are placeholders. `--execute-reviewed-plan` is a
trusted operator assertion; it cannot authenticate the owner or create the
missing human approval. An absent or non-boolean API flag refuses before file
or native operations. Output must be a fresh directory outside the guest and
registry. There is no CLI registry, backend, executable or command override.

## Checks and resource ownership

The executor keeps the original admission lock across source/plan/evidence
checks, native ownership, deletion, known handle closure and finalization.
It rechecks the exact image roster, preserved records, evidence copies and
four accepted closure-bound proofs. Historical cleanup flags and coherent
admission/root/proposal bindings are required. This is the existing trusted
local-producer boundary, not full recursive owner/client proof authentication.

The Windows backend requires physical D: regular singly linked files and an
explicit NTFS result. All planned image handles are acquired before hashing
or marking any object. Bounded reads verify their exact bytes through those
handles; native IDs and timestamps are compared with the same API. Sharing
denies content writers and other deleters. Compatible readers may remain, so
this is not exclusive-reader ownership, a mapping inventory or an immediate
unlink guarantee. Reparse points, hardlinks, changed identity, sharing errors
and unknown cleanup refuse. Other or unknown filesystems are unsupported.

Fresh process checks require an original PID to be absent, reused, or proven
terminated by matching creation time and a signaled process handle. Live or
unknown required state refuses. The executable path remains historical
provenance; a terminated process need not support a new image-name query.
Exit code 259 alone is not a liveness oracle. These checks never terminate a
process. See Microsoft's [process termination](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process)
and [wait-state contract](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).

Each intent record is flushed before its exact held object is marked. Native
deletion uses [SetFileInformationByHandle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfileinformationbyhandle),
with the [one-byte disposition field](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_disposition_info).
No acquisition uses delete-on-close. Every owned handle gets a close attempt,
including after expiry or failure. An uncertain close remains unknown and is
never retried with a possibly reused handle. Finalization requires known image
cleanup, exact image absence and unchanged evidence. Retained files, evidence
copies, manifest, direct proofs and tombstone remain charged.

## Failure records and limits

Create-only request, before, per-image intent/mark and final records retain
progress. `outcome: completed` requires normal qualified finalization and
lock release. `retirement_recorded` is true after a returned durable finalizer,
false before finalization starts, or null if finalization started but did not
return. An unlock or final-result publication error after a qualified commit
cannot honestly be called rollback; inspect the canonical ledger/tombstone.

File dispositions may take effect when handles close during failure cleanup.
Nine deletions are not atomic. A partial image or unknown native cleanup
failure cannot qualify retirement or release its reservation. Hard termination
can leave an admission lock; there is no automatic repair, retry or rollback.
Keep all failed evidence and request a separately reviewed recovery operation.

The 900-second clock is cooperative. Synchronous filesystem/native calls can
block between checks; use the existing finite process-tree owner for an actual
run and verify its cleanup/capture separately. No power-loss, hostile-OS,
arbitrary-filesystem or whole-device privacy guarantee is made. There are no
new runtime, model, SDK or library dependencies; Kernel32 is an installed OS
component. Host tiny-fixture checks do not qualify real images, an emulator,
Android UI, physical phones, model quality or release readiness.
