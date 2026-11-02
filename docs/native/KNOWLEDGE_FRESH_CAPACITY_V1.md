# Fresh SDK16 guest and read-only capacity preview

Refs #14 (M10.02), supporting #13 (M09.06). This host prerequisite does not
qualify Android execution or grant an emulator/storage operation.

The approved SDK15 operation used the November 1 guest that SDK16 originally
named. SDK16 now names exactly
`D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-v1/avd-v1`.
It cannot adopt the used SDK15 guest. SDK14/SDK15 contracts, frozen results and
original failed preparation evidence remain unchanged. The new parent and guest
are not created by importing or validating this profile.

Four Knowledge selectors, the frozen B88 product/APKs, protocol/client/session
versions, source closure, activation paths and all time limits remain unchanged.
Existing source pins must be rebuilt and reviewed after this source change;
old SDK16 admissions cannot be relabeled. There is no caller-selected guest path.

`benchmarks.receipt_avd_storage.preview_prepare(root, registry=DEFAULT_REGISTRY)`
provides file-only capacity facts from the existing shared ledger. It requires
an existing ordinary D: parent and an absent candidate, rejects overlap with the
registry or any tracked root (including retired/preparing roots), and refuses
missing, corrupt, locked or detected changing inputs. It does not initialize a
registry, acquire/create a lock, write a ledger, create a root, reserve storage,
retire images, recover preparation, invoke SDK/ADB or inspect native processes.

The preview uses the same ledger validator and charges as actual preparation.
Every entry contributes, including retired evidence/history. Closed entries keep
at least their earlier recorded charge. Ledger, closure, recovery and retirement
evidence are rechecked; current charges must agree on both passes. The final
ledger binding and path/lock preconditions are checked again.

The result reports the exact ledger binding, active root count, current charged
bytes and projected bytes with one 40 GiB reservation. Root and byte limit flags
are separate. `would_fit` describes only this observed two-root/64 GiB accounting
calculation. `admission_granted` is always false, even when both flags are false.
There is no preview authorization file or path to reserve/execute from this result.

This is an advisory observation, not a locked/linearizable snapshot, a filesystem
quota, or protection against hostile concurrent mutation. No disk-free, memory,
port, owner, runtime, model or human-approval gate is checked. Actual preparation
must still obtain exact applicable authority and perform fresh locked admission
through the existing guarded SDK4/SDK5 paths. An observation can become stale.

The SDK15 run grant is spent. The new SDK16 parent is absent at the start of this
packet, and two roots remain unretired. A representative candidate beneath an
existing inspection-output directory may report shared capacity; it is not the
fixed SDK16 target and cannot establish that target's parent/readiness. Any exact
retirement and boot require a separately reviewed proposal and authorization.
No deletion, guest adoption, reset, alternate ledger or policy relaxation follows
from the preview.
