# Native publication-result diagnostic device evidence

Refs #9 (M05.05 prerequisite) and #5 (M01.05 support), root claim 6381577583,
device/report subclaim 6381589695. On 2026-10-24 the single selected diagnostic
passed, **1 PASS / 0 FAIL**, and observed **UNSUPPORTED** with the unchanged
fixed STORAGE refusal. Publication did not succeed: the exact 63-byte stage
remained present and the destination remained absent. Positive removable
publication/store qualification remains blocked. This observation does not
identify the cause of either earlier failed volume attempt.

The separate source worktree starts at unmerged PR141 head `ab88cb9`. Both earlier
failed attempts and their 148/219-file stopped selections remain unchanged.
This packet did not retry their import method or read/write the failed
`model-volume-synthetic-v1` root/cache/stage, whose post-state remains unknown.

The executed fixture was one ordinary selected method:
`ModelPublicationDiagnosticTest#classifyFreshVolumePublicationResultWithoutFallback`.
It selects the actual production Context volume, creates only a fresh fixed
`model-publication-diagnostic-v1` sibling, and forces 63 original synthetic bytes
to `model.part` with CREATE_NEW/NOFOLLOW. Exactly one actual
`NativeModelPublication.publish(root,onResult)` call records a closed result:
PUBLISHED, DESTINATION_EXISTS, UNSUPPORTED, IO_FAILURE, INVALID_INPUT or UNKNOWN.
Existing fixed exception mappings, no-replace behavior and absence of fallback
remain authoritative. There is no LocalModelStore/import/SDK/Engine call.

PUBLISHED requires no refusal, the exact tiny destination bytes and absent stage.
A classified refusal requires its fixed failure mapping, unchanged exact stage
and absent destination. DESTINATION_EXISTS contradicts this initially absent
destination and fails the fixture. UNKNOWN/INVALID_INPUT are observations only,
not compatibility claims. Nothing is removed, replaced, retried or redirected.
The actual candidate root remains absent. A distinct internal proof/marker is
forced after all checks; diagnostic PASS can mean publication was refused.
`publication_succeeded` and `positive_store_qualification=false` prevent a PASS
from being presented as a successful store import or filesystem qualification.

The original proposal was initially disabled. Root and independent reviewer
rehashed all 1,640 bindings (172,291,478 bytes), including 61 shared source copies,
11 private controller copies and the signed copied APKs, before a new exact GO.
The proposal SHA256 was
`df32b2e50ef17b4cbe53926ccce86c99bf1604e9bf7ae97a1fba95d2db583fbf`;
authorization changed only the two admission flags, with SHA256
`8e8acc2005b1948eec4c4c6db1af6e37e8d7a3ea3cf80d882a45c33092978086`.
The frozen source was `cb351a63c107758f615ad80104adee80e920abed`.

The exact selected instrumentation command shape was:

```text
am instrument -w -r -e class org.locallore.app.ModelPublicationDiagnosticTest#classifyFreshVolumePublicationResultWithoutFallback org.locallore.app.modelvolumeverify.test/androidx.test.runner.AndroidJUnitRunner
```

The original owned execution handle reached authoritative terminal status 0;
its child completed with return code 0, known client cleanup, 36,937 ms elapsed,
486 stdout bytes and zero stderr bytes. Stdout SHA256 was
`2d97c4b0014a87802e6f62cb72e9978f81d6e1d4c3a7fe8fc80d4d604c6224d9`.
All 105 bounded device clients had terminal, known-cleanup receipts. Two same-pair
APK updates preserved the other 33 APK hashes and all 35 installed UIDs. All
conditional APP/TEST stop counts were zero. Final metadata observed no owned
processes; this is an observation, not proof of natural native/SDK cleanup.

The forced diagnostic receipt recorded one native result callback, UNSUPPORTED,
`publication_succeeded=false`, `positive_store_qualification=false`, exact stage
bytes/hash, absent destination and actual Context candidate-root absence. The
category combines missing symbol, EINVAL, ENOSYS and EOPNOTSUPP; it does not expose
which condition occurred. The fixture compared bounded bytes, size, modification
time and available file-key metadata; a nullable file key is not an inode proof.

Actual Context observations were external free bytes 3,556,835,328 before and
3,556,827,136 after, with userdata 1,222,066,176 before/after. Final controller
userdata observation was 1,222,049,792 bytes, above the unchanged 1,207,959,552-byte
floor. These are boundary observations, not capacity reservations. External free
space was below the current 4,735,631,360-byte real-artifact import requirement
by **1,178,804,224 bytes**. This is a separate real-import capacity block,
independent of the UNSUPPORTED result. No real model admission or copy was attempted.

The local controller's 32 adverse-flow/parser fixtures passed with zero failures,
errors or skips. Coordinator-owned regular and volume builds each passed 299 JVM
tests across 31 suites, with zero failures/errors/skips, zero lint errors and
seven warnings. Signed APK and backup/shared-UID audits passed. The immutable
host index covered 1,480 files / 170,062,269 bytes, SHA256
`2f38c54bb15b6ddbc5b1ffa3c93f28f76a0c1b7f64f53134e7a94a11f0a61318`.

Root accepted the original consumed terminal observation. The frozen local-only
success closure subsequently revalidated all 105 raw clients, source/artifact
bindings, diagnostic proof and final gates, then sealed 320 files / 1,935,440 bytes.
The sealed index SHA256 is
`4b758f955b43ff5c70af57322a07d9ff7a722aa532f76c99f6c275ff1ef5cee5`.
Independent final review rehashed all 320 files without mismatch and checked the
105 raw clients, proof, preserved package/UID maps, final process absence and
capacity observations (review commit `6cea272867064c4638f15e00d40bf8d587f785b3`).
The single authorization is consumed; no further device action is authorized.
Prior roots and data remain preserved by the closed command scope; this is not
a whole-userdata byte audit. No clear/reset/uninstall/old-method rerun, host UI,
model weights, SDK, Engine, workspace or story action occurred. Raw identifiers,
paths and diagnostics remain local.

Full M05.05/M01.05, positive removable publication/store import, physical phone,
real model/SDK and ARM64/16KiB gates remain incomplete. A/#117/#119 holds persist.
The next runnable task is a separately reviewed narrow native unsupported-result
diagnosis or explicit compatible-publication design, without relaxing no-clobber
behavior or using this diagnostic PASS as positive store qualification.
