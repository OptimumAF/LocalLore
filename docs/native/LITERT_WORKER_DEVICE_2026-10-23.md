# LiteRT worker: emulator verification, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 prerequisite
and M05.04 fail-safe support. One authorized B-only cohort passed all three
selected methods. This is local verification for review, not a completed
playable-model gate or owner acceptance.

## Executed boundary

The frozen instrumentation class is `org.locallore.app.LiteRtWorkerInstrumentedTest`.
All three methods had paired start/terminal PASS records and the final runner
terminal, with no skipped or unfinished method:

| Method | Exercised assertion |
|---|---|
| `packagedSdkLoadsWithoutModelInitialization` | Load the actual packaged `litertlm_jni` library off Android Main, without constructing or initializing an Engine or opening a model. |
| `missingModelAdmissionFailsBeforeSdkAndPreservesCanonicalWorkspace` | Reject a missing synthetic model before injected SDK resource construction, then exercise the default paired LOCAL owner and real JNI/SQLite path: quarantine, invalidate its borrowed handle, forbid fallback and preserve the complete accepted player snapshot through a fresh paired owner. |
| `digestAndConfinementFailuresCannotAllocateSdkOrSelectFallback` | Reject a tiny synthetic file's incorrect digest and model/cache paths outside the configured synthetic models directory before injected SDK resource construction; exercise the default paired owner's digest failure and unchanged canonical state. |

The construction counter is an injected ordering check. Default paired-owner
missing/digest failures occur before SDK construction. Configured-owner metadata
checks status, provider ID and null loaded-model metadata; it does not establish
full profile-field equality. Complete permitted player-snapshot equality is not
an NPC privacy qualification.

Every file belongs to a create-new UUID child of the test application's private
no-backup directory. Context overrides both application context and no-backup
directory; canonical parent checks bound cleanup. Deliberately quarantined roots
and failed fixtures are retained. The native owner-slot and fresh SQLite snapshot
checks execute inside JUnit before any conditional external TEST-only cleanup.
No Compose screen or MainActivity was selected by these tests. SDK library
loading asserts execution off Android Main; preflight refusal is invoked from
Main and the production worker dispatches admission to IO. There is no measured
SDK initialization, callback, close or native-generation join in this packet.

## Artifact and execution identity

The isolated identities are `org.locallore.app.litertverify` and
`org.locallore.app.litertverify.test`, using the existing AndroidX runner.
The coordinator's final v4 artifact audit checked manifest identities, the exact
app-specific receiver permission, no network permission, runner target and
absence of `sharedUserId` in both manifests. All six native libraries passed
ELF and ZIP 16 KiB alignment checks, including the pinned SDK's exact binary
hashes; its complete pinned license/notice assets were checked. Both APKs passed
the actual pre-admission `apksigner` verification and their captured certificate
outputs matched. Android subsequently accepted both installations.

| Binding | Bytes | SHA256 |
|---|---:|---|
| Final APP | 73,776,528 | `945b368f66b90e1788b235dd8f7d692a804538da4a3d29d3cab4ee13dc0d437b` |
| Final TEST | 1,744,113 | `6a76dd65b3c9ae9869e6a045a4966e0aff7c230343734acca73b30340a1dee83` |
| Frozen LF test source | 12,516 | `dd5ef28b3dd5cfb7d77ed5822e0fd68ee831b969bf18b8fa3d5ca68fe46e529d` |
| Raw instrumentation, retained privately | 2,232 | `300694b66bbb2c4f5e00d72d902321b15a14e1005f2e0ddcad9262c51892c132` |

The source digest binds the actual LF build input and committed LF content.
The production worker source bound by the final audit is
`e4545d4f01b6e2b825be478bc9944162ee364b077d66a752e2020b97ab95e9bb`.
The coordinator's final package-only repack removed incremental ZIP layout gaps;
the earlier APK pair was not admitted to this device cohort.

Actually executed once through the frozen bounded controller:

```text
am instrument -w -r -e class org.locallore.app.LiteRtWorkerInstrumentedTest org.locallore.app.litertverify.test/androidx.test.runner.AndroidJUnitRunner
```

B returned API 35, x86_64 and 4096-byte pages. The owned outer cohort completed
in **13,063 ms**, exit zero with known Windows Job cleanup. All **44** recorded
clients completed with exit zero and known cleanup. Instrumentation is command
0027. No second cohort or subsequent device query ran.

Both installation stdout records matched the allowed push-install success
framing. The APP and TEST install clients recorded **174** and **196** stderr
bytes, respectively. The existing host runner retains stderr counts, not their
content; that text cannot be characterized. The outer runner recorded zero
stderr bytes. No zero-stderr claim is made for all clients.

## Preservation and external cleanup

The complete prior **27-package** map matched its closed preceding evidence and
both new package identities were absent before installation. Installed, after
and final maps each contained exactly **29** entries: the unchanged prior 27
hashes plus the two admitted final APKs. The prior map digest is
`efad41eea2dc202bec455e3ffe5650f4481c9a34a14f3e38f0f78d32ef88b4d6`;
all three resulting 29-map files have digest
`1250acc498447cb5bf997e43b0159f0cf60a0f4df9eb9aeec971faebfa8649ec`.

The controller captured the newly assigned TEST UID from exact unambiguous
installed-package metadata only after successful installations and complete
29-map verification. Its conditional stop path requires all three PASS records,
then a fresh sole TEST process, matching fresh package UID and captured installed
UID, and the exact 29-map. No earlier cohort's assigned UID was reused.

After all three PASS records, no LocalLore process appeared in the bounded
namespace snapshot. Therefore **zero force-stop commands** ran. The conditional
fresh stop-admission path was covered purely on the host and was not exercised
on-device. This observation does not establish natural SDK process exit or
model ownership cleanup.

All original storage/process gates passed. Final userdata availability was
**1,542,373,376 bytes**, above the unchanged **1,207,959,552-byte** floor. There
was no A query, relaunch, reset, clear, uninstall, APP stop, real model
initialization/generation/copy, existing model-cache access or original-save
access. Only fresh synthetic fixture files were used by model-admission checks.

## Controller preparation and retained evidence

The corrected LF source frozen in commit `9674998e8560a8f6b4cdd823d6be114b10d9c275`
is 12,516 bytes, SHA256
`dd5ef28b3dd5cfb7d77ed5822e0fd68ee831b969bf18b8fa3d5ca68fe46e529d`.
Original commit `b9031a02d25ad2c282e6424e0629b149ebc0499f` and its source
digest `2c0d43bf52428f6466b56adc598c37f37356bd4383b4f4bc852698bb8ccf6f9e`
remain preserved. The coordinator's first actual JVM run found that coroutine
stack recovery copies the fixed uncertainty exception. Before device execution,
only the test helper was corrected to accept a finite acyclic chain of at most
eight exact fixed uncertainty copies ending in null, rejecting unrelated/private
causes. Test identities and canonical/ownership assertions are unchanged.
Independent source review found no concrete blocking fixture issue; no build or
device result is inferred from that review. The coordinator subsequently built
the final source and ran its host checks before artifact admission.

The disabled B-only controller passed 47 distinct pure host fixtures. They cover
paired instrumentation starts/terminals, failures and unfinished tests fencing
all post-instrumentation calls, dynamic assigned TEST UID capture and fresh
ownership validation, foreign namespace/UID/map rejection and unchanged storage
floors. The final run's 47 distinct cases passed in 0.045 seconds. Repeated
executions of these fixtures are not additional unique tests.

The complete prior 27-package map was verified read-only against the preceding
sealed external-owner index. The prior map's SHA256 is
`efad41eea2dc202bec455e3ffe5650f4481c9a34a14f3e38f0f78d32ef88b4d6`.
Both new identities must be absent before installation; the resulting map must
contain exactly those prior 27 hashes plus the new admitted APP and TEST hashes.
The final controller SHA256 is
`531ecd9f3fb7388867eda23b896a81382ed97df485e04ee9bec9c0086a86265a`.
Disabled proposal `1b33024abd1b375543e260f6577f179e69f62ae39384c310df26d47b8a4e5c56`
became exact root authorization
`108127d0f7a3cdb07ca0720c44354eef2b68e2fae268be01776112e8a634275d`
by changing only its two promotion flags. Coordinator and independent reviewer
rehashed all **50** bindings before that single dispatch. The earlier disabled
source-selection module is preserved separately.

An additional local-only sealing assertion initially assumed all client stderr
counts were zero and stopped on the successful install counts described above.
Its script and failure receipt remain preserved. A corrected local-only audit
retained those counts explicitly while preserving all actual dispatch gates,
stdout/status checks, package-map equality and test-result assertions. No device
query or retry followed that local audit correction.

The closed private selection contains **134 files / 226,678 bytes**. Its index
is 22,677 bytes, SHA256
`ae7c26282f95cf52725f3ca0ca6ffe4ff38d34c29043b580771239872e7ed71e`.
All selected files and the index are read-only. Local rehashing matched all 50
bound inputs, all 44 command stdout/status records and all selected file hashes.
The independent reviewer separately matched the 134 selected files, read-only
attributes, all 44 command records, paired PASS records, maps and authorization
promotion with zero mismatches; it made no device calls.
Raw diagnostics, complete maps, assigned UID, local paths and APKs remain local.
The cohort's original handle reached authoritative terminal and its lease was
released after sealing; no further device actions are authorized by this report.

## Remaining gates

Library loading can qualify only packaged ABI linkage. These tests do not
initialize a model, generate text, exercise actual SDK callbacks or prove native
generation cancellation/drain/close. The pinned public SDK's initialization and
cleanup behavior requires separate real-model qualification; missing-model
preflight is not that evidence. Real weights, model caches and original saves
are outside this packet. Physical-phone, ARM64 execution, A, real inference,
model quality and sustained resource ownership remain unqualified. The next
runnable task is explicit trusted model/profile selection and separately
authorized real-model initialization, callback cancellation and cleanup
qualification through the paired owner. MainActivity wiring and a playable
local-model experience remain incomplete.
