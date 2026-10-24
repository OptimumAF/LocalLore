# Schema3 Android capacity verification, 2026-10-23

Refs [#8](https://github.com/OptimumAF/LocalLore/issues/8), M04.04.
Implemented and locally verified, pending owner acceptance. This packet stacks
on unmerged parent-retention PR #85, base `a1b1cc9`; qualified code `37bb3ff`.
See [host calibration](SCHEMA3_CAPACITY_HOST_2026-10-23.md),
[structured results](SCHEMA3_CAPACITY_RESULTS_2026-10-23.json) and
[independent review](SCHEMA3_CAPACITY_REVIEW_2026-10-23.md).

## Fixed fixtures

Schema3 increases the original seeded Ready fixture to17 pages; the accepted
potion gift needs18. The old15-page and immediately lower16-page builds fail at
creation. The new full profile therefore uses the measured17-page compile-time
SQLite ceiling, prefix0, format2 and database schema3. The relief profile keeps
its32-page ceiling:14 fixed3500-byte padding rows fill it; insert15 returns
SQLite Full and removing the owned table frees15 pages. These values are fixed
and audited, with no runtime ceiling adjustment or injected Full reply.

| Profile | Application ID | Build directory / exclusive project cache |
|---|---|---|
| Full17 | `org.locallore.app.capacityv3` | `build-capacity-v3` / `.gradle-capacity-v3` |
| Relief32 | `org.locallore.app.capacityreliefv3` | `build-capacity-relief-v3` / `.gradle-capacity-relief-v3` |

Both are visibly labeled debug/testOnly installations with separate test APKs.
Historical schema1/15-page and relief32 evidence and artifacts remain preserved.
The old project caches are explicitly refused to prevent stale-output deletion.
Ordinary storage remains uncapped; no production Rust, Store, JNI, migration,
gameplay authority, dependency, runtime or model version changed.

The one-shot relief child admits only exact schema3/migration records, the known
schema fingerprint, a fixed synthetic root and owned marker. It checks these
read-only before writable admission, rechecks after opening, and repeats marker,
path and file-identity guards around fixed writes and close. Only known writes
advance the expected file stamp. Failures from writable-open onward poison
ownership; unknown child/pipe/protocol/close state fences further native calls.
It drops only its exact owned padding table and validates restoration before
native reopen. The temporary table intentionally violates normal schema
admission; an existing live native owner is needed for the Full recovery proof.
The child's connection-local max-page PRAGMA is distinct from the audited
compile-time Rust SQLite ceiling. No SQL or path command reaches gameplay APIs.

## Checks executed

Windows; Rust1.93.1, Java17.0.6, Gradle8.11.1, AGP8.10.1, Kotlin2.2.21,
NDK29.0.14206865, BuildTools35.0.0, compile/targetSDK36. Two authorized,
already running API35/x86_64 emulators, aliases A/B, each with4096-byte OS pages.

| Check | Actual result |
|---|---|
| `python scripts/check.py host --offline` | 380 Rust workspace +3 linker passes;364 Python tests; four fixture bindings; fmt/strict Clippy pass |
| Final targeted manifest-audit tests | 5 full +6 relief methods pass, including wrong schema/count/legacy identity, mixed/duplicate metadata and malformed numeric suffixes |
| `python scripts/android_capacity_probe.py build --offline` | PASS;146 JVM tests, lint0errors/1existing dependency advisory, both native ABIs and16KiB ELF/ZIP alignment audit |
| `python scripts/android_capacity_relief_probe.py build --offline` | Same checks PASS;146 JVM tests; exact schema3/format2/count metadata and32-page native binary audited |
| Invalid Gradle configurations | 11 terminal expected refusals: missing/mismatched/historical caches, mixed fixtures/verification and release tasks |
| Ordered full lifecycle suite | 5/5 per emulator, before/after empty-Compose controls in verified order |
| Relief native/gateway/Compose cohort | 3/3 per emulator |
| Default full discovery | Original3/3 per emulator; these repeat the three proofs above |
| Preservation/cleanup | 16 prior local APKs and15 prior installed package APK identities per emulator unchanged; bounded clients terminal; owned app/test processes absent |

Total22 emulator test executions, with zero failures, skips or unfinished
methods. Two existing Rust qualifiers remain explicitly ignored and uncounted.
ARM64 libraries were cross-built/audited; they were not executed.

Full tests assert actual native Full twice/repeatedly, unchanged canonical view,
the same36-byte original key, no replacement submit/prepare, cancellation without
spend, safe draft/retry behavior after reopen and disposed UI callback fencing.
Relief tests assert original Ready-key acceptance exactly once after drop,
stable receipt and exact retry/reopen, cancellation remaining terminal/unspent,
and the collected Compose flow. Wrong-owner and forged schema-marker children
refuse before writes and are reaped before later native calls. Accepted snapshot
comparisons retain schema/provider/all timeline metadata; only the separately
asserted uncommitted draft count is normalized.

## Reproduction and artifact binding

Build from this branch with the two commands above, Java17/installed SDK/NDK and
cached pinned dependencies. Unset ambient `LIBSQLITE3_FLAGS`; the native build
owns it. Install only each reviewed v3 app/test pair on authorized targets with
`adb -s <target> install -t <apk>`. Do not clear or replace existing packages.

Run `am instrument -w -r` using `androidx.test.runner.AndroidJUnitRunner`:

* Full ordered selector: `org.locallore.app.CapacityLifecycleCohort$OrderedSuite`
  in `org.locallore.app.capacityv3.test`. Quote the selector in the **remote**
  shell so `$OrderedSuite` is literal. The repository's
  `benchmarks/android_runtime_spike.py` `Device.shell` quotes remote arguments.
* Relief selectors: `org.locallore.app.SqliteReliefNativeTest` and
  `org.locallore.app.SqliteReliefInstrumentedTest` in
  `org.locallore.app.capacityreliefv3.test`.
* Full default discovery: omit the class selector; expect exactly3 cases.

Use the existing strict `scripts/android_instrumentation_result.py` parser;
match every expected class/method/start/terminal/count, final runner result and
ordered controls. ADB exit0 or `OK` alone is insufficient. Clients used a180s
outer budget, with bounded pipes/child cleanup; no budget was relaxed. The result
JSON binds both APK pairs, ABI audits, individual case outcomes and75 private
all-attempt artifact hashes. Source hashes describe tested workspace bytes
(including its line endings), not a portable checkout normalization. Raw paths,
device IDs, diagnostics, databases and model weights are not published.

## Retained nonpassing attempts and limits

The first two builds failed old opt-in UI calls passing a nullable selected story
to a disposal probe. `46764a3` requires the already initialized selection; the
disposal assertions remain intact. The second builds passed. Source review also
caused the repeated Android ownership checks and stricter integer audit parsing.

Initial A/B install helpers failed a host logging-field lookup after installing
each app, before writing their ownership ledgers. Completed/clean client journals
and recorded absent-before/exact-hash-after inventories permitted adoption of
those exact app identities. Only the missing test APKs were then installed; no
reinstall, clear or uninstall occurred. A first configuration driver discarded
stderr and cannot qualify the refusal reason; all11 were recaptured with both
streams and checked for their expected terminal guard. These setup failures are
retained, not counted as gameplay failures or silently replaced by passes.

Host storage approached1GB during builds. Only this checkout's two inactive
legacy capacity build directories were moved to task-owned secondary storage,
with junctions at their original paths; all16 prior APK hashes were reverified.
New native/build/temp outputs used secondary storage. No model cache/AVD/save
was removed. The preexisting ordinary APK was audited and preserved; this packet
does not claim an ordinary Android rebuild or instrumentation run.

These are synthetic SQLite page-limit tests, not partition ENOSPC, power-loss,
filesystem corruption, phone performance, real-model quality, thermal behavior
or same-UID race immunity qualification. No physical phone was available and
the independent model integrity/storage hold remains. The uncertainty fence was
source-reviewed; this packet adds no live unknown-child or ownership-drift fault
injection. The broader M04.04/exit gate stays unchecked pending those wider
criteria and owner acceptance. Next runnable M04.04 work is bounded helper-failure
and ownership-uncertainty fault injection against these qualified v3 fixtures.
