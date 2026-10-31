# Read-only retirement preview contract

B39. Refs #14 M10.02, #13 M09.06 capacity prerequisite.
Code base reviewed/unmerged PR296 f8d4a769d2501c46be65c78bc54952c9e53f1a27.
Consumer PR305 inspector inputs stay frozen separately; no merge.

## Boundary

Existing plan_retirement writes/pins under the admission lock. It is not a
read-only preview and must not run on production before applicable authority.
Add preview_retirement(root,evidence_manifest_path,registry=DEFAULT_REGISTRY).
Import/call does not initialize, lock, write or reserve a registry, pin a plan,
delete/move guest data, start/stop a process/service/SDK/ADB/guest or copy images.
Reuse strict existing ledger/closed/proof/evidence/known-image validation.
Observed admission.lock at start/end refuses registry_locked; changed ledger
binding refuses preview_ledger_changed; changed root roster refuses
preview_guest_tree_changed. Existing validation reasons propagate. Preserved
records/evidence/closure bindings are rechecked after image hashing.

This is an unlocked read-only snapshot, not exclusion, a hostile-writer boundary,
owner permission, a future capacity guarantee or an executable/pinned plan.
After separate approval, existing planning/execution must recheck exact inputs
and freshly pin under the unchanged shared guard. No budget/registry alternative.

Exact outer keys: version,scope,ledger_binding,plan,remove_bytes,preserve_bytes,
snapshot_only,pins_plan,deletes_images,registry_written. Version1; scope
receipt-avd-retirement-preview-v1; ledger_binding is an ordinary byte/hash pin.
plan is the existing canonical _plan shape; byte counts sum its remove/preserve.
snapshot_only=true, pins_plan=false, deletes_images=false, registry_written=false
describe this call, not whether an old pinned plan exists. Call does not change
an existing plan. The outer envelope refuses the executor's exact plan schema.
Returned mutable data never changes files. No historical process/tool reattestation.

## CLI

NEW benchmarks/receipt_avd_retirement_preview.py main(argv=None), imported storage
alias. Only --root,--evidence-manifest,--output; production uses fixed
storage.DEFAULT_REGISTRY. No registry/execute/backend/script overrides.
API tests may use an isolated existing D registry. Require an existing normal
D output parent and a fresh create-only output outside registry and ALL tracked
guest roots; no overwriting or implicit parents. All checks precede output.
Success main returns0/stdout exact new result-file binding. Boundary failure
returns1/no success binding/private-path output; argparse unknown-switch exit2.
The CLI writes only that explicit report; partial publication is retained on
failure, no cleanup. Python3.9 syntax, stdlib/existing dependencies only.

## Actual proposal preparation

Candidate CLOSED B32 model-free UI guest only:
D:/Dev/Experiments/LocalLore/2026-10-30-archive-ui-v1/avd-v1.
Preserve every nonimage guest record and whole external runtime capture tree,
including all four bound external proofs/transitive captures; all images and
other guests remain. Source/executor and fresh original-process closure receive
independent read-only review using Windows process read/wait/close only.
Hash only the exact allowed image roster after source tests and preservation.
Production ledger/guest records must remain unchanged. No plan pinning/lock or
retirement during preview. Present an exact verified private proposal before
asking for deletion or new-boot authority. All earlier grants are spent.

Expected new source/records/recovery128–384MiB; cap1GiB, stop768MiB across two
source worktrees/new Experiments+Recovery/ownedTEMP256MiB stop192MiB. Existing
guest image bytes are read only and separately charged by the shared ledger.
No image/model copy. All captures/failures/source/metadata originals retained.
No actual Android/model/phone/ARM64 or release gate follows from host checks.
