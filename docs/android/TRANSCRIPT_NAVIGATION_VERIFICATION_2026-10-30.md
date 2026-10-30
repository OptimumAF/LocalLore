# Scoped transcript navigation

Date: 2026-10-30. M09.03 scrolling slice and supporting M09.05/M10.02/M10.03
checks are locally verified and in review. Full milestone criteria and owner
acceptance remain open. Base: open/unmerged [PR #291](https://github.com/OptimumAF/LocalLore/pull/291),
`ff345b63cdb7d8cd22add2cd7c46fdbdf8746e25`.

## Implemented behavior

The chat now follows a strict appended history only when the reader had reached
the previous transcript end. Otherwise it retains the reading position and
offers **Latest** below the list. Latest is also available while browsing existing
history. It targets the newest message, rather than the controls below it.

Presentation scope is saved story plus branch, with a separate demo scope and an
inert unresolved scope. Frozen visible-history snapshots include message ID,
text and role. Initial load, scope changes, replacement, reordering, truncation
and unchanged history do not trigger automatic scrolling. A previous-history
read witness authorizes follow; only a current-history read witness acknowledges
unread replies. Scheduling a scroll does not establish that a reply was read.

Measured geometry requires reaching the tail's bottom or moving past its row.
The visible head of a long reply is insufficient. An active empty history uses
the existing state row as its anchor for a later first reply. The three-row
prefix and four required footer rows, plus optional composer/inspector rows,
are explicitly coupled to LocalLoreScreen and covered by the compiled journeys.

The Compose adapter consumes the old witness before acknowledging a fresh
layout, checks row counts and message keys, and guards requests against exact
scope/history changes. A drag invalidates pending navigation. Navigation uses
instant scrollToItem without decorative animation. Scope-keyed
rememberLazyListState preserves Compose's saveable list state; witnesses,
unread state and pending requests are ephemeral. Existing draft/callback guards,
message keys, engine, native boundary and canonical history are unchanged.

No dependency, permission, model, schema, gameplay rule or preference is added.
Implementation follows the official [list-state and scrolling guidance](https://developer.android.com/develop/ui/compose/lists).
The screen tests use the public [isDisplayed API](https://developer.android.com/reference/kotlin/androidx/compose/ui/test/package-summary#isDisplayed(androidx.compose.ui.test.SemanticsNodeInteraction)),
available since Compose 1.6.0, within the existing pinned Compose dependencies.

## Checks actually performed

Executed source: `7dd9ea3bcbb3efa162d2639f6807208b3da238c0`, 2,312 tracked raw
inputs. Subsequent changes document behavior and results only.

```powershell
python scripts/check.py android --offline
```

The unchanged public checker runs the verified Gradle wrapper for both APKs,
all JVM tests and lint, then the product and instrumentation-pair audits. No
test filter, exclusion, forced rerun, task substitution or download was used.

| Check | Actual result |
| --- | --- |
| JVM suite | 345 unique cases / 41 XML; 0 failures, errors or skips |
| New policy tests | Eight methods pass; previous 337 cases unchanged |
| Lint | 0 Error/Fatal; one existing GradleDependency warning; one AutoboxingStateCreation hint |
| Native builds | Fresh offline x86_64 and arm64-v8a builds |
| APKs and public audits | Both assembled; product and pair audits pass |
| New Compose journeys | Four compiled/packaged definitions in test APK only; not executed |
| Source checks | git diff --check passes; raw source/tool/signing guards stable |

The public call returns 0 in **237,362 ms**. Its single 900-second process-tree
owner closes in **239,482 ms**, worker0, complete cleanup/capture,
stdout10,795 bytes and stderr0. The fresh build directory was absent initially;
native/JVM/lint/assembly task lines execute without cached/up-to-date suffixes.
No corrective build was required. The warning concerns existing coroutines1.10.2
versus1.11.0; the new hint suggests an unboxed ephemeral gesture counter.

Existing process-local D: caches/temp and reviewed signing override were reused;
the original credential was read in place, no key copied/generated or global
setting changed. Both fixed D: default-key paths stayed absent. Toolchain and
dependency versions remain those recorded in the preceding theme verification.

Product APK: **27,756,136 bytes**, SHA256
`02cdb416fdfe9dd56d71f343b79519291fe488f2ea6d766f299b34bac7ef88e3`.
Test APK: **2,220,063 bytes**, SHA256
`22a35b4b4c4548fa44d7069c65896b5e2c795279f6d8d15cf78f15060e917d2c`.
Normal packages are org.locallore.app and org.locallore.app.test; actual audits
verify matching certificate
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.

Independent closed-file review passes in3,219ms. It joins actual commands,
reports, APK/DEX definitions, preserved copies and before/after raw source maps.
All372 native inputs are unchanged from B22; both release/generated/merged
chains join, and stripped JNI/APK bytes match B22 for both ABIs. This does not
claim ARM64 execution. Review receipt SHA256:
`9643e0ba34ad90b5969a335dfa3732491016013f7853ff9a136ed5aa86ffe5a2`.

## Original fixtures and preservation

Eight original JVM methods cover initial/null/scope changes, exact old read
witnesses, unread acknowledgement, strict prefix versus rewritten/reordered
histories, mutable caller lists, stale Latest requests/read witnesses, and
long-row/footer/invalid/overflow geometry. Four real-screen methods cover history
reading plus Latest and draft conservation, a partially read long reply,
composer-past-tail follow, and a retained stale-branch callback with reused IDs.

Original test commitf849df74 remains preserved. Before execution, three test-line
corrections at511b3f4d align initial-history Latest availability, establish a known
viewport before stale-callback invocation and wait for display rather than
composition. These are source-review corrections, not an executed RED/GREEN
claim. Independent review also prompted preserving saveable scroll state and
the active empty-history anchor before the first build.

Private packet: `D:\Dev\Experiments\LocalLore\2026-10-30-transcript-follow-v1`.
Before docs, all2,312 raw files/32,084,846 bytes were preserved and read back in
the10,281,571-byte source ZIP, SHA256
`00749125072c104ae43b501295fc4b4ef35692d57e4fa855cf3844e1946f8cb6`.
Additionally51 selected APK/report/native copies total93,062,618 bytes.
Preserved-build manifest SHA256:
`323bbf51e14319bed906c800944d45b0f4d68401901293707cb5cb4dca7283b4`.

Final ticket handoff records selected recovery/copy/ZIP/three-branch bundle and
independent readback seals at the matching `D:\Dev\Recovery\LocalLore` root.
The original8GiB packet budget includes three worktrees, build outputs,
cache/temp allowances and selected recovery. The pre-build conservative bound
was6,538,685,634 bytes; this is not an exclusive peak or OS quota claim. Original
generated builds, caches, historical worktrees, guest state and failures remain
in place. Selected recovery is not every ignored byte.

## Limits and next runnable task

The owner chose to continue without the phone. No phone, emulator, ADB/service,
model, traffic, system-setting, merge or release action occurred. Real scrolling,
gesture races, IME, screen readers, large fonts, recreation and complete current
Android journeys remain unrun. Pure policy tests and APK packaging do not
qualify these behaviors, physical-device performance or model/story quality.

Next runnable host check: the archive-profile public gate on this updated source
in a separate bounded packet. Executing the four screen journeys requires
separately authorized target admission. Full tasks remain unchecked pending
their broader criteria and owner acceptance.
