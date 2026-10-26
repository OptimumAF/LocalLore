# External saved-task evidence verification

Supporting M10.02 and M08.01/M08.05 work, stacked on the
[versioned host driver](ANDROID_PROCESS_HOST_DRIVER.md). This document describes
host validation; the actual Android lifecycle gates require separate retained
execution records. The deterministic inference provider establishes plumbing,
not model quality or physical-phone performance.

## Separate evidence boundaries

`benchmarks/android_process_controller_evidence.py` accepts the original custom
instrumentation frame and three final product records. Its closed schemas bind
case, run, product/signature hashes, UIDs, three process identities, one saved
task, factory/restoration flags, two terminal observations, exact gameplay
vectors and scope/navigation hashes. All four cases use create-only fixture
origins. The existing root/active-child/retired-leaf check counts remain
82/123/139. The retained-parent check count is a bounded diagnostic, not a
fabricated golden count.

The final created/commands records belong to the third restored producer;
saved belongs to the second old producer. One synchronized counter assigns
distinct sequence numbers across files. Read-only commands can write after a
save; the validator checks distinct bounded sequences and exact gameplay
vectors rather than assuming commands always precede saved. Later counters
within the same process cannot decrease. The controller still requires a newer
after-super save acknowledgement, the exact STOPPED task and disappearance of
the old process before relaunch.

`benchmarks/android_retirement_evidence.py` separately requires original quiet
load/probe/retire bodies, complete helper identities and pins, zero/zero/one
commit attempts and closed resource flags. Retained-parent verification also
requires all four original canonical sidecars, each at most262144 bytes and
together at most1MiB. Their raw digests must equal the helper's preserved-view
digest. The three preserved views retain complete eligible player snapshots
and receipts, including the original root and prefix. The fixed postfork tail
must not appear in any preserved view. These checks do not reconstruct hidden
world state or replace Rust's authority.

The caller must validate both transport footers, not treat an ADB stream's exit
code as a remote helper success. The host runner also owns build/source/client
and live-emulator admission; neither pure validator grants mutation, fixture
reuse or retry authority. Original raw bytes remain private and unchanged.

## Host regression command

```powershell
python -B -m unittest scripts.tests.test_android_process_verification scripts.tests.test_android_process_client scripts.tests.test_android_instrumentation_evidence scripts.tests.test_android_process_controller_evidence scripts.tests.test_android_retirement_evidence
```

The original synthetic fixtures cover all four cases. Negative controls include
duplicate/nonfinite/malformed JSON, extra or truncated instrumentation frames,
wrong origin/scopes/certificates/identities, automatic gameplay, stale producer
records, decreasing counters, changed inherited receipts, ineligible tail
content, noncanonical bytes and invalid helper closure/commit evidence. These
host tests do not execute an Android lifecycle or native helper.

## Preservation after concurrent cleanup

Commit and push versioned harnesses promptly. Keep private execution records in
an explicitly selected evidence directory outside broad generated-build cleanup
patterns. Select files from an existing manifest; verify size and digest before
copying and again from the completed recovery archive. Preserve failures as
separate immutable attempts. Do not recursively copy guest images, databases,
models, caches or unrelated projects, and do not upload private diagnostics to
GitHub. A complete-history Git bundle is a separate recovery copy of source.

Recovery preserves surviving evidence only. Missing original execution records
remain missing; a reconstruction or later passing run cannot replace them or
retroactively expand an earlier verification claim.
