# External evidence host checks and preservation, 2026-10-26

Supporting M10.02 and M08.01/M08.05. Draft
[PR #206](https://github.com/OptimumAF/LocalLore/pull/206) is stacked on unmerged
[PR #203](https://github.com/OptimumAF/LocalLore/pull/203), base `847e4456`.
Full milestone tasks remain unchecked pending complete criteria and owner
acceptance. No merge or release occurred.

## Implemented and actually checked

Shared strict JSON decoding (`22508f15`), native helper/retained-view validation
(`b5c9fbb2`) and closed controller/producer validation (`3bcc8520`) are integrated.
The [contract](ANDROID_EXTERNAL_CONTROLLER_HOST.md) separates evidence
consistency from actual execution and Rust canonical authority.

Read-only peer review found two concrete verifier defects. `5a7d7c25` accepts
read-only producer writes after the saved acknowledgement, while still requiring
distinct bounded sequences and exact gameplay vectors. `bc4ce7ee` rejects
decreasing counters between later records from the same process. The
[protocol](ANDROID_PROCESS_RESTORATION_PROTOCOL.md) clarifies the shared
synchronized counter, newer after-super acknowledgement and unchanged process
death/gameplay requirements. Peer review confirmed both corrections; it was
not a separate test execution.

Actual Windows/Python 3.14.7 checks at source `19cc85ba`:

| Check | Result |
|---|---|
| Five focused host modules | 118 tests passed in 2.960s |
| Full `scripts/tests/test_*.py` discovery | 1,203 tests passed in 93.565s; zero failures, errors or skips |
| Full-suite owned worker | completed, exit0, 94,889ms, cleanup known, stderr0 |
| Full-suite tracked inputs | 755, identical before/after, including all five SQL migrations |
| Full-suite original stdout | 218,058 bytes; SHA-256 `23cb8f6cc39dd6ea500c9883f2b156a7d6c533e52de3dfa0bfd2b305ac5a49bd` |

The focused 118 tests are included in the 1,203 total, not additive. The full
private worker uses isolated Python imports, a stdin barrier, the existing
Windows owned-process runner, a 180-second deadline and a 262144-byte output
bound. Its selected discovery is equivalent to:

```powershell
python -B -m unittest discover -s scripts/tests -p test_*.py
```

Both meaningful failing attempts remain separate: sequence-order regression
117 tests/four case errors, then green; counter regression 118 tests/four case
failures, then green. These are synthetic host regressions, not device faults.

## Recovery copy

After the owner reported possible concurrent cleanup, source was immediately
committed/pushed through `01a8ab1e`, including an explicitly incomplete runner
checkpoint. A private ZIP contains 1,221 selected surviving files totaling
142,449,571 original bytes. All entries were reread for exact name, size and
SHA-256; an independent read-only check found no missing, extra, duplicate or
unsafe entries. Archive size: 89,912,035 bytes. Archive SHA-256:
`75d32e30d105f0b3470dd095647e90c6312f95e162683ad0c98cc2ccd6706aba`.
Its private index is 423,942 bytes, SHA-256
`cb17ca7a30af4609244a818f9e24abcf50d85825ba5915b9f1f1f50811f745bd`.

A separate 9,801,891-byte Git bundle verifies complete history through
`01a8ab1ea628924c4de1c3cc7c7e09733ffd95ca`; SHA-256
`8bc5d755f4d0088df149c073dd6fc9790f53b3603a44a70d79fe0ec5f8af7ba2`.
The ZIP selects prior sealed evidence and original author records, not guest
images, databases, models, caches, temporary roots or other-project data. No
private diagnostics were uploaded. Newer regression records are outside this
initial snapshot. Older missing records were not reconstructed and the cleanup
actor was not identified.

A second private snapshot protects 58 current-controller files/1,603,660 bytes,
including both failing regressions and the full host run. Independent review
verified every original and ZIP entry, with zero missing/mismatch/extra/unsafe
paths. Its 517,928-byte ZIP has SHA-256
`63fe28ebf30fcf55202f2f97f13f42a5b37194ce929102baa0eed8fcf4d603b0`;
both identical 18,273-byte index copies have SHA-256
`32006c8ae521fcb6856cd1aace5591c5ae598b821b47dc2b1ca7f795bd561314`.
The second Git bundle verifies complete history through `d24fa55d`; its
9,813,784 bytes have SHA-256
`ffcc15be797ea4a33ef1ddc9a39b48eca63509b2ea5c65277030f4bfe20eff0b`.
The snapshots overlap and their counts must not be added as unique evidence.

## Remaining gates

This packet's host checks make no new Android saved-task, broad Android,
phone/ARM64 or real-model qualification claim. Earlier component/JVM/APK results
remain attributed to [the prior packet](ANDROID_PROCESS_HOST_DRIVER_VERIFICATION_2026-10-26.md).
The next runnable task is to complete and review the external-controller runner,
bind a fresh build and ten-method native component gate, then execute the root
control and retained-parent two-death protocol with original readback records.
No SDK/device actions, settings changes or unrelated-emulator stops occurred
during these host checks and preservation.
