# External process-restoration execution, 2026-10-26

Supporting M10.02 and M08.01/M08.05. Source starts at draft/unmerged
[PR #206](https://github.com/OptimumAF/LocalLore/pull/206), `50989ca2`.
The current packet uses the versioned [component driver](ANDROID_PROCESS_HOST_DRIVER.md)
and [external runner](ANDROID_EXTERNAL_CONTROLLER_HOST.md). Full milestone
tasks remain unchecked; no owner acceptance, merge or release is implied.

## Fresh build and native gate

The offline input-process build actually reran 234 JVM tests in 27 XML suites,
with zero failures/errors/skips, both lint checks and eleven artifact audits.
Its owned worker completed exit0 in 36,702ms, with known cleanup/capture and
no stderr. All756 tracked inputs, including all five SQL files, were identical
before/after. Source-map SHA-256:
`0d16493ccf5b9715561d6e3d6c4e26ec8e18f1d874cd60900c1cabb77580dd89`.

| Fresh artifact | Bytes | SHA-256 |
|---|---:|---|
| Product | 24,555,355 | `ab1030cdbe7cc05833213f0f1064563fcf7893164961f93824927e89a9bc5fc4` |
| Test | 2,752,699 | `997f0ece760ddb5af9497b2d6d529f87292786098d9118b98660eaa2baaa507a` |
| Controller | 53,113 | `90bd8030963748ee6a98e783793e4f0588f9a131c01c05f90f4f6fe7fecb7499` |

These APK bytes equal the earlier packet's artifacts, but the new build,
executed JVM XML, source maps and command records were actually captured anew.
The existing server was observed without starting or replacing it. A fresh
owned API35 Google APIs/x86_64 guest uses the unchanged 2GiB/two-CPU profile
and 4GiB host-memory floor.

The ten native component methods passed: four retired-selection loader/refusal
methods, four retained-parent loader/refusal methods and two actual Rust-native
retained-parent methods. All84 captured clients were clean; the owned worker
completed exit0 in 307,486ms with known cleanup/capture, no stderr and the same
756 source rows. Additional boot-health captures explain the client-count
difference from the earlier 81-client packet; no client-count gold is invented.
Independent read-only review revalidated original rosters, raw-to-client copies,
artifact/source bindings and terminal owners. This ten-method gate explicitly
does not establish external process-death or visible UI recovery behavior.

## Preservation

The completed build/component/server gate has a private recovery copy:
258 files/27,903,386 original bytes. Independent review verified every original
and ZIP entry, with no missing, changed, duplicate, extra or unsafe entries.
ZIP: 17,823,810 bytes, SHA-256
`25412f5ef829fd7b3d46e7d6e8a516e4ade801123280de06592747f56e7712bc`.
Both identical 76,685-byte index copies have SHA-256
`8c268cc74ccc78a2b4e5d38980954f56f233b47c730c945907fdc5f055ed446d`.
No live-case files, guest images/databases, models, caches or unrelated-project
data were selected. Raw diagnostics remain private.

The first environment-planning invocation incorrectly used isolated Python
mode, which this preexisting CLI does not support. It failed during imports,
before entering the environment API or creating a proposal/guest. The
documented `-B` invocation succeeded. This is a retained tool-output observation,
not reconstructed original pipe bytes or a device-case failure; no source,
budget or admission rule was changed.

## Pending execution gates

At this checkpoint the root external case is running; no external result is
credited yet. The retained-parent guest is prepared separately and remains
unlaunched. Active-child/retired-leaf controls and broad Android regression also
remain pending for this source. Phone/ARM64 and real-model qualification are
separate gates; no result follows from fake-provider or emulator checks.
