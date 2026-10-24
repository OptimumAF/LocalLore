# Candidate volume storage review — 2026-10-23

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). Independent subclaim
[6381051500](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6381051500)
under root6381042648. Review starts from main `1a9a314` in a clean separate
worktree. Owned paths are this report and [ADR0010](../adr/0010-candidate-volume-storage.md).
The reviewer performs no device action, shared build/cache or model/SDK call.

## Current disposition

Official API/privacy research and the proposed ADR are drafted. Integrated
source/tests and actual artifacts/results are not yet reviewed. The API route
is feasible as a deliberately restricted debug experiment, but there is no
filesystem/device/runtime qualification or owner approval from this review.

## Early concrete findings

API30 is justified by StorageVolume.directory, not by a need for new storage
permission. UUID/state/primary/removable/emulated metadata and file-to-volume
mapping predate that requirement. The UUID is an opaque string; using the
API31 converted UUID or Java UUID parsing would unnecessarily refuse portable
media. Null UUID/directory, ambiguous eligible volumes, wrong flags, mounted-read-
only state, changed path/device or unsafe paths require explicit refusal.

Context external-files enumeration may create framework app directories and
cannot be described as read-only. A returned app-specific path is authority to
use that directory, not authority to adopt a public benchmark path or manually
create an unavailable app tree. No policy may silently select array element one,
the largest volume or an alternate volume after a pinned one fails.

Repeated volume guards must include native publication and cleanup as well as
initial selection and SDK construction. A guard only around the top-level store
method can leave later reads/writes/deletion on an identity that changed during
an operation. Recheck after full hashing before READY/runtime admission. These
checks reduce accidental redirection but cannot provide atomic physical-media
identity or eliminate OS remount races. Unknown ownership must retain files
rather than clean up on a replacement mount.

Scoped storage and backup exclusions do not imply physical-media encryption or
internal-storage confidentiality. If the configured runtime cache is external,
its possible story-derived content remains a privacy gate; cache provenance
cannot be inferred from its name. The default route, canonical saves and release
privacy promises must remain unchanged, with a clear debug-only disclosure.

Actual repository manifest sets allowBackup/fullBackupContent false and links
data-extraction rules that exclude the external domain for cloud backup and
device transfer. No legacy backup_rules XML exists; the legacy manifest flag is
used instead. These source controls require merged-artifact inspection and
platform testing rather than a blanket backup claim.

## Initial integrated source review

Pure policy commit `291018724e3916fb452760a91920eed6efb16f74` defines a bounded opaque observation pin with exact Context-anchor shape, one eligible volume, userdata/device separation, inclusive external/userdata floors and overflow-safe missing-artifact-plus-reserve arithmetic. Its original refusal cases cover duplicate/malformed eligible observations, flag changes, missing/unsafe paths, identity changes and redacted diagnostics. The policy deliberately performs no IO or SDK work; Android observations must establish its supplied facts. No substantive pure-policy blocker was found on source review; tests have not been run by this reviewer.

The coordinator Android adapter derives anchors from Context, maps storage metadata, checks canonical non-symlink directory chains, pins filesystem device plus mount/anchor inode observations and makes an observed refusal sticky in process. Candidate storage branches on the trusted build flag; the default continues using its internal anchor. Store guard hooks cover root creation/checks, model validation, publication and cleanup; post-hash checks precede successful return. A race during an already opened stream remains outside the atomic guarantees of these path-based checks.

A concrete SDK integration gap was returned: the initial draft guarded Engine construction but not later `initialize`, per-role conversation creation or send. A pin could fail between roles and still enter SDK/cache work. The review requested guards before these subsequent SDK entries and fake-resource refusal tests, without pretending unknown resources were released. Worker source provenance hashes also need updating when these hooks change, even though SDK/model versions remain fixed. Coordinator correction `eab95a46e7ef3bcbbf1cb8c07830336665ccd057` now rechecks before initialize, conversation and send. Its fake-resource cases refuse at each point and assert no forbidden SDK entry or closing of an unknown parent. Store refusal after source entry preserves its stage and prevents publication/cleanup on a replacement. The normalized worker source hash is updated in both the constant and manifest. The source findings are resolved; actual checks remain separate.

The separate Android synthetic test source `bd574d4c1e7d12effa27633b8efc071e82f48ab4` uses the real adapter/store/native publication and fixed original 63 bytes in a new package. It checks an injected admission refusal before root/source access, full reopen/hash, wrong expected identity without source open, sentinel preservation and direct no-replace refusal with an existing destination while retaining a two-byte stage. It creates no SDK, story workspace or normal-launcher session. The disabled host controller admits only a new absent APP/TEST pair, one ordinary selected method and post-PASS captured-process cleanup, preserving all prior 33 package hashes/UIDs. This is source review; no Android execution or removable filesystem support is inferred.

The setup screen conditionally discloses that this debug profile places model/runtime cache in removable app-specific storage, the cache may contain sensitive data, removal makes the model unavailable and story saves remain internal. The default wording/route remain separate. This is an appropriate scope disclosure; no physical-media encryption, SDK-cache content or release privacy qualification is inferred.

## Evidence pending

Frozen pure-policy interfaces, Android observation/guard integration, store/worker
call sites, negative tests, opt-in packaging/audit exclusions and actual retained
host or synthetic filesystem evidence remain to be inspected. Native no-replace
support on the selected removable filesystem is unknown and must fail closed.
Real models/SDK, reference phone, ARM64/16 KiB/power-loss and #117/#119/A holds
remain separate. No merge, release or device/owner permission is granted here.
