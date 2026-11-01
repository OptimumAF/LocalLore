# Archive UI harness: implementation and host/build verification

Date: 2026-10-30. Packet B25. M10.02 and supporting
M09.03/M09.05/M09.06/M10.03 are implemented/in review for this bounded harness
slice. Full tasks remain unchecked. Stacked on open/unmerged
[PR #293](https://github.com/OptimumAF/LocalLore/pull/293),
`1beb172d76da325fd8e0313db88f21a71a14a2fb`.

The [operational contract](../runtime/android/ARCHIVE_UI_HARNESS.md) describes
the fixed ten-method model-free profile, source/build admission and controller.
New code is Python host tooling; Android/native application code and dependencies
are unchanged. Shared model-profile defaults remain intact. Root coordinated
separate profile, controller and adversarial-test worktrees; independent closed
artifact review checked the actual results after producers finished.

## Executed source and actual checks

Both final checks used clean source
`62ba698d064143d8602aa917c96b459c1a37594e` / 2,328 tracked raw inputs.
The immutable executed Android checkout is
`D:\Worktrees\LocalLore-ui-runner-build-v1`. The later reporting commit adds
documentation only in the implementation checkout; it is not substituted for
the executed source in the strict build manifest.

| Actual procedure | Result |
| --- | --- |
| Complete stdlib unittest discovery across the six existing Python roots, separate isolated child per root, no filters | 2,567 unique (suite, ID) cases; 0 failures/errors/skips/load errors/expected failures/unexpected successes |
| All five new test modules within that run | 41 cases exactly once: contract 10, client 8, owner 3, build 12, controller 8 |
| `python scripts/check.py android --archive-verification --offline` | Exit 0; 345 unique JVM cases / 41 XML; zero failures/errors/skips |
| Fresh native/Kotlin/JVM/lint/APK tasks and public product/pair audits | Both ABIs built; both audits pass; lint 0 Error/Fatal, one existing warning and one hint |
| Real `archive_ui_build.py --public-run … --output …` against closed actual build | Exit 0; genuine manifest created, all ten source/annotated DEX targets verified |
| Direct `verify_current` replay against that manifest and actual APK bindings | Pass in 2,995 ms; no target admission created or native/service/device operation |

The six Python suites contain 140 / 10 / 14 / 34 / 13 / 2,356 cases for
benchmarks, LiteRT, llama, Android LiteRT, Android llama and scripts/tests.
The single 900-second owner closes in 404,413 ms, worker exit 0, complete
cleanup/capture, stdout 2,152 and stderr 4,360 bytes. This is the complete Python
discovery portion of host validation; Cargo tests, fmt, Clippy and native linker
host tests were not executed by this Python-only packet. It is not a complete
`check.py host` claim.

The actual public Android call takes 265,979 ms; its finite owner closes in
268,207 ms, worker exit 0, complete cleanup/capture, stdout 10,900 and stderr zero.
All source/tool/signing guards remain equal. Process-local temporary/cache
outputs stay D:. Existing installed tools and signing credential are used in
place, with no credential copied or global setting changed. Critical tasks
execute with bare headings, including a repeated compiler-warning heading.
Lint retains GradleDependency (coroutines 1.10.2 versus 1.11.0) and
AutoboxingStateCreation; neither changes the zero-error result.

## Failed evidence and corrections retained

| Closed attempt | Actual result and disposition |
| --- | --- |
| `focused-v1`, source `897bee4c` | 218 methods; 21 assertions across six methods/subtests fail, zero errors/skips. All 186 legacy cases pass. Genuine DEX adapter, package paths, task freshness, XML coherence and typed counters corrected without weakening tests. |
| `focused-fixed-v1`, source `f4092855` | 226 methods; eight controller cases fail at common admission before instrumentation. Other 32 new and 186 legacy cases pass. Those eight intended controller scenarios were not exercised. |
| Direct controller admission diagnosis | Source-binding refusal traced to a synthetic fixture's marker C-source pin. Two fixture lines bind the actual public refuser source; guards/assertions remain unchanged. Corrected direct admission passes. |
| `controller-cohort-v1`, source `54c7a726` | All eight controller cases pass, including the full simulated ten-method graph, malformed JUnit, caller/evidence mismatch, order, source drift and unknown cleanup. |
| `freshness-red-v1`, source `6d9dc51a` | New real-log regression fails: repeated bare Gradle headings are incorrectly refused. Other 11 build cases pass. Actual preceding successful logs establish the warning-group duplication. |
| `freshness-fixed-v1`, source `62ba698d` | All 12 build cases pass. All matching headings must be bare and at least one present; missing/up-to-date/cached states still refuse. Full final Python and Android checks then pass on this exact source. |

Every failed source snapshot, source ZIP, test identity/result, diagnostic,
unrun preparation wrapper and terminal capture remains in the packet. The
`6d9dc51a` ZIP was reconstructed from the sealed `54c7a726` source ZIP plus the
one changed test file, with every current raw input and ZIP member checked;
this is explicitly a verified delta reconstruction, not an invented direct copy.

## Artifacts and independent verification

| APK | Bytes | SHA-256 |
| --- | ---: | --- |
| org.locallore.app.archiveverify | 27,756,156 | `b152ddea01363fc622a286dab3d59386739a997c5cb77a14d97851ec166ab192` |
| org.locallore.app.archiveverify.test | 2,220,071 | `0b58ff22bc0d51585fc695e20d2ce303a7e8d38fb621ee61464ba14cc3a5db70` |

The actual pair audit verifies matching certificate
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`;
test permission is solely android.permission.REORDER_TASKS. Both APKs are
byte-identical to B24's archive pair; no application code change is inferred.

Independent file-only artifact/host review passes in 4,337 ms. It independently
joins source maps, actual commands, all 345 XML cases, both audits, signing/tool
proofs, 372 unchanged native inputs, both native artifact chains, and all ten
public annotated JUnit definitions in four test-only DEX classes. It also
checks the complete 2,567 composite Python identities, all 41 new cases once,
and prior failures separately. It does not call the build-admission verdict,
rerun tests/audits or inspect key material. Review receipt SHA-256:
`ae01f34be38ed1ded10f4527b90dad1f1905fc9c7717da1a783f4f2ee2782154`.

The genuine build manifest is 15,424 bytes, SHA-256
`823195e3770228b12c4f967c2b749efcc92aa0973385d7970369414a0ff3430e`.
The final executed source ZIP is 10,327,620 bytes, SHA-256
`89acfb45b1141c7f0eb227869200b149af5e1f116e26daaa7d51f856a44aaae4`;
all 2,328 raw inputs total 32,218,946 bytes. Fifty-one selected build copies
total 93,062,635 bytes. Preserved-build manifest SHA-256:
`b3888b8e5a8b5d309ae41674d654507ecfc6cce151b6a47d63308b4417a10e29`.

## Retention, blocked gates and next task

Originals stay under
`D:\Dev\Experiments\LocalLore\2026-10-30-archive-ui-harness-v1`, with all five
source worktrees and generated Android outputs retained. The selected recovery
and five-branch source bundle use the matching `D:\Dev\Recovery\LocalLore`
root; final ticket handoff records their seals and independent readback. The
original 10 GiB packet cap covers source trees, build outputs, selected recovery
and process-local cache/temp allowances. Selected recovery does not preserve
every ignored byte; original outputs and earlier recovery remain in place.

All ten Android UI methods are **unrun** by this packet. A simulated controller
pass, fresh APK build, DEX roster or file-only manifest replay does not prove
touch/scroll/IME/accessibility behavior, provider-running cancellation, Android
restart, traffic privacy, ARM64 execution, phone performance or real-model
quality. Full M09/M10 acceptance remains open.

The owner chose to continue without the phone. No live ADB roster/service,
guest/model operation, ledger mutation, other-emulator stop, system setting,
merge or release occurred. The last read-only shared ledger observation has
two closed unretired roots occupying the two-root limit; it is not fresh
process/disk proof. A new guest also needs the shared 64 GiB/40 GiB admission
rules and fresh authorization. No guest is created by this implementation.

Next target task is a separately reviewed storage/capacity disposition and
one freshly authorized guarded ten-method run against the frozen qualified
source. Preserve existing guests and recovery. Until admission is available,
review this implementation and its source-bound host/build evidence; do not
relax the guard or infer missing target results.
