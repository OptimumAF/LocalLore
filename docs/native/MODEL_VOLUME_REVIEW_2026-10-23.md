# Candidate volume storage review — 2026-10-23–24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). Independent subclaim
[6381051500](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6381051500)
under root6381042648. Review starts from main `1a9a314` in a clean separate
worktree. Owned paths are this report and [ADR0010](../adr/0010-candidate-volume-storage.md).
The reviewer performs no device action, shared build/cache or model/SDK call.

## Current disposition

Integrated source, final host artifacts and two admitted device attempts have
been independently reviewed. The first failed selection; after the confined
Context/capacity corrections, the second reached first native publication and
failed with fixed STORAGE. Neither selected method passed. The removable route
has no successful filesystem/import qualification, and real-model/SDK use remains
blocked. Both stopped selections are independently verified and sealed; no device
execution authority remains.

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

Build configuration requires the explicit volume flag together with setup/LiteRT, excludes the picker profile, uses a separate application suffix/build directory and leaves the default flag false. Existing AndroidComponents release-variant disablement applies transitively through LiteRT, including aggregate build requests. A requested-task-name guard is additional protection, not the sole debug-only boundary. Manifest permission/audit changes accept only the new exact package and reject added broad-storage or network permissions; merged artifact inspection remains required.

The narrow controller's `sm list-volumes public` framing matches Android15's metadata listing implementation. Its one mounted short-FAT-UUID row profile is intentionally stricter than the general opaque-UUID app policy; it may refuse other formats rather than broadening selection. Listing grants no mount, format, benchmark, adoption or model-copy authority. [Android15 sm source](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/cmds/sm/src/com/android/commands/sm/Sm.java).

Review found that the initial synthetic fixture would consume the real candidate child with incompatible tiny bytes. Before any device admission, correction `eff30fefe61695030431abb6119bc7a6e0f15972` moved actual store/publication tests to a fixed synthetic sibling beneath the same admitted Context anchor. It asserts the planned real candidate root absent initially, after injected refusal and finally, while preserving the two-byte no-clobber stage only in the synthetic child. This retains the same filesystem/store/native cases without blocking the candidate destination. Its closed receipt adds actual Context-side candidate absence and a path digest; no host-derived external path/query was added. Those source assertions still require actual selected-method PASS before device acceptance; they grant no real-model copy permission.

## Retained initial host failure

The first regular-candidate XML contains 293 tests across 30 suites with one failure and zero errors/skips. The new pre-access refusal host fixture took the default native publisher method reference, initializing Android JNI on Windows before reaching its admission guard; the actual failure type is UnsatisfiedLinkError. Its owned worker completed nonzero with known cleanup in 249,640 ms. Test-only correction `8e0bea7` injects the existing host publisher seam, preserving refusal-before-source/root assertions. Corrected regular copied XML has 293 tests/30 suites with zero failures/errors/skips and a zero-return known-cleanup worker in 66,360 ms. This is a retained host fixture failure, not evidence of removable-device or production guard failure; complete final host sealing remains separate.

## Final host and first admission evidence

Final compiled source is `53cc98c0af9d1807cbf3899086045ae05121cbd0`. The reviewer independently rehashed all 645 host-seal entries (269,546,044 bytes), index SHA-256 `06d1dc9eff4fb87a0589be5cd476c01c852f885619fca19ba64c9781f6e914bf`, with zero mismatches. Actual copied XML records regular and volume profiles at 293 tests/30 suites each, ordinary at 206/24, all with zero failures/errors/skips. Lint reports zero errors and respectively 7/7/1 warnings. Actual packaged APP backup rules retain external-domain exclusions in both cloud and device-transfer sections; signed-package, permission, helper-exclusion and SDK/native audits pass. These are host/packaging checks, not filesystem compatibility results.

Final volume APP SHA-256 is `97277fae141c46ca1057518d0a8916ffe7495bb5216fbc52ee89aae098bde51c`; TEST is `7cb157a0213653d00394393361b895e4e91dee15d35951c6f4314d98f121c9f0`. The final volume-v2 artifacts supersede the retained pre-correction TEST. Standalone script evidence records 446 passing checks and benchmark helper evidence 34 passing checks; a separate combined-shell terminal failure is retained rather than treated as successful solely because its earlier test output said OK.

Disabled proposal `13b1ea9b3584efbd94ede3f652081c3089938c60d3ae00500ed68e0778f10354` was independently rehashed: all 796 bindings/271,528,645 bytes matched, including coherent 57 shared and 11 private source copies. Its durable pure-controller result records 28 passing tests and zero failures/errors/skips. The admitted scope was two absent-package installs, one exact ordinary selected method, and captured new-pair cleanup only after PASS. It permitted no external path query, real-model copy, SDK call, prior-package lifecycle action or fallback.

The actual first owned result completed nonzero with known client cleanup in 14,406 ms. Raw selected-method output records zero PASS and one FAIL: fixed STORAGE in `AndroidModelVolume.select`, before selection returned. The retained controller result records 25 commands, one install of each new package and zero cleanup stops. No synthetic store/source/native operation or receipt was reached; framework Context enumeration may nevertheless have created app directories. Redacted STORAGE does not identify the failed check, and this result cannot establish unsupported native rename or insufficient removable capacity. Final device state was not re-queried after failure.

The stopped seal has SHA-256 `db81c6182740c25e4da0dd1bbcab577b079a661cb26ed3d800b8d94b00926d4f`: all 148 files/1,373,941 bytes independently rehashed with zero mismatches. The local stopped selection and consumed-execution release record no retry or follow-on authority. Client cleanup is not a claim that Android processes or model resources were naturally released.

## Selection compatibility finding

The adapter initially applies its all-ancestors non-symlink/canonical-equality predicate to the trusted internal Context anchor before discovering removable anchors. Official Android15 Zygote source explicitly creates the framework `/data/user/0` alias inside app-data isolation. Treating every such system alias as an untrusted model-child escape can reject legitimate Context storage. This is a concrete compatibility concern; the redacted first result does not prove it was the observed failing check. A correction must distinguish canonicalizing a framework-provided anchor from allowing symlink model children, preserve exact Context authority and device pins, and qualify its actual result separately. [Android15 app-data isolation source](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/core/jni/com_android_internal_os_Zygote.cpp).

## Capacity continuity finding

Cross-checking coordinator discovery against actual store call sites confirms that the first formula, `max(2 GiB, missing bytes + 256 MiB)`, can admit a known-doomed copy: preflight allows model bytes plus the smaller reserve, while later zero-missing-byte guards still require 2 GiB free. With a continuous post-copy floor, preflight must instead require missing bytes plus the larger retained floor/reserve, using overflow-safe addition. Correction `bfb4cb2` implements that minimum and raises the fixed candidate's external preflight lower bound to 4,735,631,360 bytes while leaving the 2 GiB runtime floor and existing reserve intact. Its eleven policy tests cover zero/tiny/fixed-model exact boundaries and one-byte-less refusals, a three-GiB pre-dispatch refusal and overflow boundaries. Metadata/cache growth and concurrent consumption remain separate uncertainties. The first device failure did not reach this arithmetic and cannot be attributed to it.

## Corrected source and second admission

Source `f3cb9a1fdc8894cb89b0ba57f651cc219c17e7b7` includes the internal Context normalization, finite last-entered diagnostic and corrected preflight. The second host seal, SHA-256 `7e1e09ebccbd43da2e837cf47c27da9b1c7dea70073d3f721e91f8ef4173faa8`, independently rehashes all 594 files/312,653,936 bytes with zero mismatches. Actual final regular-v3 and volume-v3 XML each records 294 tests/30 suites, zero failures/errors/skips; each lint report has zero errors and seven advisories. Actual owned results record zero exit/known cleanup in 147,453 ms and 144,531 ms. Signed final volume APP is `7cae58f2c27c3d8949c724c27eca12555e4b725a033958524fd3052fdabbeba6`; TEST is `48a5a8fd741ec9c11eab86175f57ada727a14416b13d45544ba4f29640b93823`. Packaged cloud/device external exclusions remain present.

The second proposal, reviewed while disabled, `dfad1532552bed80bcb4070b01b998d8116324485fafa63c601f8859142e47c0` independently rehashes all 746 bindings/314,614,965 bytes, with 57 shared and 11 private live/copy/record sources coherent. Its durable pure-controller result is 30 PASS, zero failures/errors/skips. It captures current installed-35 identities and process rows afresh, rechecks captured subsets before conditional exact new-pair stops, requires own-process absence before updating only those two APKs, then selects one ordinary method. Proof and final captured-process cleanup depend on actual PASS. No clear, external-path inference, previous-33 lifecycle action or SDK operation is admitted. The first stopped attempt remains preserved.

The actual second owned result completed nonzero with known client cleanup in 31,922 ms. Its controller result records 59 commands, one update of each new APK, and zero stops both before and after instrumentation. Actual selected raw output records zero PASS/one FAIL in `NativeModelPublication.publish` during first import. That execution advanced beyond selection and its STABILITY assertion, but did not return from import. JNI maps both its unsupported category and other IO failure to fixed STORAGE, so this result does not identify a native category, errno, filesystem limitation or exact cause. No proof, reopen/reuse, sentinel, no-clobber or final gate ran to completion. Post-failure synthetic files/processes/capacity remain unobserved; no rollback or successful external candidate-root absence receipt is inferred. The refused route remains closed without replace/hard-link/alternate-volume fallback.

Second stopped index SHA-256 is `97950aa889e180465aca65673279581e76cd9bf131d84df06fa731c1804b9c14`: all 219 files/1,468,527 bytes independently rehash with zero mismatches. All 59 raw-client receipt sizes/hashes and known terminal states match. The local stopped selection and consumed-execution release preserve the absence of success, post-state or natural-resource-drain claims and provide no follow-on authority.

Native no-replace support on the selected removable filesystem remains unknown.
Real models/SDK, reference phone, ARM64/16 KiB/power-loss and #117/#119/A holds
remain separate. No merge, release or device/owner permission is granted here.

The next runnable task is a separately claimed, narrow classification of the
existing native publication result into unsupported versus other IO refusal,
with closed sanitized evidence. It must preserve current files and refused
state, introduce no publication fallback, and precede any real-model copy or
new storage choice. This packet supplies host implementation evidence while
leaving the positive native/device gate and full M05.05/M01 work incomplete.
