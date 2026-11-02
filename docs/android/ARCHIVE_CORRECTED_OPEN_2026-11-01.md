# Opening imported corrected timelines

B70, 2026-11-01. Refs #13 (M09.06; supporting M09.04), #14 (M10.02).
Supporting implementation is in review; full task criteria remain unchecked
pending owner acceptance and broader qualification. Based on open, unmerged
PR #339 at `0e9755248d9eec80d98567546d50b085e2095535`.

## Corrected behavior and authority

ArchiveDialog's preview and import-complete views incorrectly said corrected
timelines could not open on Android. The current native player presentation
already supports Domain1 and Domain2. Replace that warning with the actual
route: explicit **Open imported story** starts a fresh session on the original
root; choose other playable timelines, including corrected ones, in the library.
Do not imply that opening automatically selects a corrected child or applies
its changes to the root. Retained deleted ancestry remains unplayable.

The V3 preview still discloses private correction details, prior world facts
and discovery evidence. Full-private contents, plaintext/provider sync, checksum
non-authentication, ID conflicts, uncertain cancellation and no-old-pending-work
boundaries remain visible. No import automatically opens a story. Exact current
preview/import references, refreshed native root selection, stale/cancelled/
closed capabilities, session and observer fences remain unchanged.

This changes two UI text sites only. No feature toggle, gameplay rule, canonical
event, storage schema, JNI ABI, protocol, dependency, SDK, runtime or model choice
is introduced. Native code owns accepted history and visibility; Kotlin consumes
the existing validated player presentation rather than rebuilding world truth.

## Source and independent work

Root reuses clean source-only `D:/Worktrees/locallore-record-actions-ui-v1` on
`fix/m09-archive-corrected-open-v1`, owning ArchiveDialog, the new JVM/UI cases,
integration, central execution and docs. The independently advanced older tests
worktree is left untouched. Agent N reuses separate
`D:/Worktrees/locallore-record-actions-flow-v1` on
`test/m09-archive-corrected-open-native-v1`, owning only the new native test file.
Its original commits are `c9502c6c` and `1891a6f9`; Root's formatter-only commit
precedes all executed tests. A separate reviewer uses frozen #339's worktree,
owns no product/test code, and inspects actual routes and nonowned oracles.
No authorship overlap or model-score acceptance is claimed. Claims are released
at handoff; Root retains coordination.

Two independent route inspections refine the initial imprecise test plan:
ArchiveRegistry returns the original root, while author correction creates a
separate child. The tests therefore assert root opening and explicit corrected
child selection separately. Review also catches an initially already-known
synthetic fact before execution: clearing its seed `known_by` allows the planned
real discovery event, preserving strict assertions and original commit history.
No runtime failure or behavioral FIRST claim follows. The initial rustfmt
differences and a host-runner authoring delimiter error are retained; the latter
writes no runner and starts no build. No product boundary or timeout is weakened.

## Verification actually executed

Both phases run clean code `0e7b8331bad20aa5fed6b476e79d9bf0b812f34d`.
All 2,579 raw source files match before/after; one immutable source ZIP is shared.
Existing Rust1.93.1, JDK21, installed Android tools and locked dependencies are
reused offline. TEMP/TMP/TMPDIR and project outputs stay on D:. Existing D:
Cargo/Gradle caches stay in place. Each phase has a 900-second Windows Job owner,
actual child identity/start barrier, complete raw capture and verified cleanup.

| Actual command | Result |
| --- | --- |
| `cargo +1.93.1 test --locked --offline --package locallore-android --test archive_corrected_open --test archive --test archive_review --test branch_catalog -- --nocapture` | **13 pass**, including two new; zero failed/ignored/measured/filtered. Owner22,694ms. |
| `python -I -S -B scripts/check.py android --offline` | Exit0, owner209,330ms. **494 unique JVM methods / 60 XML**, including two new, zero failures/errors/skips. Lint zero errors, one existing warning and one hint. Both public APK audits pass. |
| `git diff --check` | Pass before publication. |

All81 Android tasks execute, including fresh native compilation outputs for
both packaged ABIs. No exclusion, clean, install or device task is used. This
does not establish ARM64/JNI/Android execution. Final source differs from tested
code only in README and this report; no rebuild follows documentation changes.

The two new native cases use actual accepted discovery/statement/belief,
author correction, playable fork and retired ancestry. Real ArchiveRegistry
exports/preflights/imports V3, then fresh WorkspaceRegistry/Host selects the
original Domain1 root and an active Domain2 child. Assertions pin legacy
snapshot rejection on the child, player V2 transcript and inherited original
scope, observed-old proposition versus private corrected truth/reason, distinct
belief/claim origins, exact discovery provenance and neutral correction marker.
Retired metadata stays present but cannot resume. Strict reopen gives the same
player view; canonical records/projections match across source/target/control.
The other case attacks cancelled, closed and reused import capabilities,
stale heads/scopes and closed workspace handles. No inference provider, JNI,
SQL injection, hand-set domain flag or raw SQLite-file gameplay parity claim.

The two new JVM cases run real ArchiveController/ShellViewModel/DurableGateway
against cloned genuine native presentation frames, with synthetic archive I/O
and catalog availability. They verify no auto-open, exact consent objects,
root-first then actual current-timeline selection, Domain2 player frames,
private canary exclusion, disposal and rejection of an imported child claiming
to be the root. This is transport/orchestration evidence, not an actual import.

Two new state-only Compose cases check V3 private/retired disclosures, separate
import and root-open clicks, busy disablement and return-to-library behavior.
Concrete runtime-JUnit methods (182/352 code units) are present only in the test
APK. **UNRUN on Android**: no rendered/touch/keyboard/accessibility/native-device
or cancellation-timing claim follows from compilation/DEX inspection.

## Artifacts and preservation

| APK | Bytes | SHA-256 |
| --- | ---: | --- |
| org.locallore.app | 28,071,776 | `3fd4fb2596b4c9ead38ec245d1d51e143655bbd6112505a38093ffd4f7120405` |
| org.locallore.app.test | 2,391,858 | `6372eb5a4730d768a171411259a0f3efecb0b0dc8cf8d881dbce2b4a24f43f39` |

Recorded common signer:
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Four packaged native libraries pass16KiB ELF/ZIP audits; only REORDER_TASKS is
requested by the test package. Both ABI release/deps aliases have exactly two
links; generated/merged bytes match release, and stripped bytes match the APK.

Captures are under `D:/Dev/Experiments/LocalLore/2026-11-01-archive-corrected-open-v1`;
selected recovery uses the matching `D:/Dev/Recovery/LocalLore` path.
Closed evidence108,121B SHA256
`43f02177b3d86e07f8d76d45824eccf15ef58c34d2d90164317750abae5108a9`.
Shared source ZIP11,394,987B SHA256
`8079d247568dc0bbb0e15893cd9e39b5f72ccfc5e5c9e4aebc3dbd3ccde0dbb7`.
All60 JUnit XML plus lint XML are copied before any future rerun. Four APK/native
copies total53,282,530B. Eight retained synthetic fixture files total472,902B;
their manifest3,777B SHA256
`b1bbab4948e2ef3d2cbf9307fbca6cd995baedef31ad89ead866df72fdcf87c3`.
Originals remain, including the two marked D: TEMP fixture roots.

Independent route/source readers report no unresolved finding; their receipts
retain the corrected fixture setup issue. Closed evidence is independently read
without a test/build or semantic audit rerun: `b70-closed-reader-v1.json`,
11,561B SHA256 `34c5391f526a8042578068a4f445e9ca3e5a577bb9a8d25b3638e50b39f0fe13`,
2.453 seconds, no findings or authorship overlap. It joins both phases' actual
commands/owner identities/raw capture, every source/ZIP entry, reports, APK/native
chains, recorded audits, compiled UI definitions and synthetic fixture copies.
Final source reconstruction uses
the single tested ZIP plus exactly two documentation overlays, not a redundant
full ZIP. Selected recovery is not a backup of ordinary generated scratch.
Both new phases sample generated output every two seconds and at terminal below
3GiB (final1,133,700,287B); controls stay below64MiB and selected recovery below
256MiB. Sampling is not a filesystem quota and excludes global cache/TEMP peaks.
Earlier packets' failed/frozen captures and XML-retention limitations are not
repaired or promoted by these new results.

## Open gates and next task

M09.06 supporting clarification and M10.02 host checks are in review. Full task
criteria remain unchecked. Frozen pending SDK14 #338 and its B66 #337 APKs,
SDK13 proposal and prior #339 outputs stay untouched. This new pair/UI cohort
does not inherit any prior run grant. No emulator/ADB/phone discovery, ledger,
model transfer/inference, settings change, unrelated stop, private upload,
merge or release occurs. Current Android UI, physical/model/ARM64 execution,
accessibility, causal OS-death and full milestone acceptance remain separate.

Next host-runnable task: investigate archive consent-control delivery across
equal-valued replacement previews/imports through the production collection
path, and reproduce any retained-action failure before changing its fences.
Device qualification still requires matching authorization and fresh admission.
