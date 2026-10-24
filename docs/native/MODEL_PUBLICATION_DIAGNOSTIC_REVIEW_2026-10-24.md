# Native publication diagnostic review — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). Independent subclaim
[6381585932](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6381585932)
under root6381577583. Review starts from unmerged PR141 head `ab88cb9943611c941cde64852ae2c93ad807919b`
in a clean separate worktree. The reviewer owns only this report and performs
no builds, suites, shared-cache, device, model or SDK actions.

## Current disposition

The actual diagnostic passed one selected method and classified the fresh native
attempt as UNSUPPORTED with fixed STORAGE. Publication did not succeed: the
original 63-byte stage was preserved and destination absent. The positive
store/filesystem gate remains blocked; this result neither identifies an errno
nor retroactively classifies the prior failed import. Source, host artifacts,
actual raw execution and final local closure were independently reviewed.
This review authorizes no model transfer, fallback or storage choice.

## Preserved evidence and authority

The preceding volume packet retained two selected-method failures: selection
refusal, then fixed STORAGE during first native publication. The second stopped
index `97950aa889e180465aca65673279581e76cd9bf131d84df06fa731c1804b9c14`
contains 219 files/1,468,527 bytes and 59 known-terminal raw clients. No successful
import, proof, reopen/no-clobber or post-failure state gate was returned. That
consumed execution admission grants no retry or cleanup authority. Existing
35 packages/UIDs and both failed synthetic roots must be preserved in any new
separately reviewed cohort.

## Initial concrete review

The current Rust/JNI boundary already returns bounded codes: published, existing
destination, unsupported, other IO failure and invalid input. Pure Kotlin enum
conversion and an optional trusted observer can retain those distinctions
without changing Rust, JNI shape, fixed names, native no-replace behavior or
the setup screen's fixed failure mapping. Unknown wire values must remain a
fixed STORAGE refusal. Codes1/4 remain UNSAFE_PATH; codes2/3 remain STORAGE.

UNSUPPORTED is a category, not an exact cause: current Rust combines a missing
Bionic symbol with EINVAL/ENOSYS/EOPNOTSUPP. IO_FAILURE also includes directory
open failure and caught panic, not just a failed rename. Neither category
identifies a particular filesystem, kernel defect, permission or errno. A new
attempt in a distinct fixed synthetic child cannot establish the old failed
child's category retroactively.

Official Android15 Bionic headers declare the existing `renameat2` signature
with API30 introduction and define NOREPLACE as refusal when the destination
exists; the symbol map exports it in LIBC_R. That supports the existing dynamic
resolution/minSDK boundary, without proving a particular runtime lookup or
filesystem result. No dependency or native wrapper change is needed for the
closed Kotlin observation. [Bionic header](https://raw.githubusercontent.com/aosp-mirror/platform_bionic/android-15.0.0_r1/libc/include/stdio.h),
[Bionic symbol map](https://raw.githubusercontent.com/aosp-mirror/platform_bionic/android-15.0.0_r1/libc/libc.map.txt).

The observer sees an outcome after native execution. It must not supply a path,
retry, replacing operation or alternate destination. Default behavior remains a
no-op. A throwing observer cannot imply rollback of an already published file;
the implementation/tests must make observer ordering and exception behavior
explicit while keeping the production mapping unchanged.

The actual synthetic fixture was independently read before source freeze. It
creates only a distinct fixed sibling and new internal proof root, forces the
original 63-byte stage with CREATE_NEW/NOFOLLOW, calls the native publisher once
and records its enum. It checks full fixed bytes and stage/destination effects
for success or refusal, rejects an existing-destination contradiction, preserves
files in either branch and guards candidate-root absence. It calls no store,
SDK or engine and reads no earlier failed synthetic child. Nullable fileKey
equality in its bounded read helper is not a mandatory inode-identity proof;
the byte/hash/size/mtime checks remain finite evidence.

The disabled controller source preserves installed35 identities, updates only
the current pair after fresh metadata/captured-subset checks and process
absence, and selects exactly the diagnostic method. Ordinary PASS precedes
forced-marker/proof reads and final captured-process cleanup. Its closed proof
keeps native category, publication success and positive store qualification
separate; a classified refusal can pass the diagnostic with publication false.
There is no host external path query or old-root capability. A stale aggregate
path-digest label was removed before freeze because this proof has no digest.

## Source, host and admission verification

Actual source commits `1d536a4f96863019f2f48c15968033416d9bf35b` and `74a530a`
were read independently. Enum conversion preserves codes0–4 and fail-closed
unknown handling. The one-argument publisher overload remains available for
existing typed method references; the two-argument overload observes the actual
native result. The native declaration and Rust publication/lib files have no
diff from the base. Five original pure test methods cover every category,
extreme unknown codes, default success, fixed redacted failure mapping and
observer cardinality/order without referencing or initializing the JNI object.
No substantive source blocker was found. Observer exceptions propagate; trusted
diagnostic callbacks must not treat an exception as native rollback.

Final compiled source is `cb351a63c107758f615ad80104adee80e920abed`. The host seal
SHA-256 `2f38c54bb15b6ddbc5b1ffa3c93f28f76a0c1b7f64f53134e7a94a11f0a61318`
independently rehashes all 1,480 files/170,062,269 bytes with zero mismatches.
Actual regular/volume copied XML each records 299 tests/31 suites and zero
failures/errors/skips. Each actual lint XML has zero errors/seven advisories.
Owned build results record zero exits/known cleanup in 321,984 ms and 296,593 ms;
the standalone script log records 446 passing checks in 19.063 seconds.

Actual volume APP is `c5d37c91c5b4125d997b0a3cbf7a0038af29a78d63fca2f1ba98794176963e7f`,
TEST `1d12f85fe8e71a2381d80407a201392c8d7452e5ee495e8e5ddec7ee015ed6a0`.
Signed-package and packaged backup audits pass; actual class inventory contains
the diagnostic fixture only in the volume TEST. No build or suite was run by
this reviewer, and no Android filesystem result follows from these checks.

Exact proposal `df32b2e50ef17b4cbe53926ccce86c99bf1604e9bf7ae97a1fba95d2db583fbf`
was reviewed while disabled. All 1,640 bindings/172,291,478 bytes independently
rehash with zero mismatches, including 61 shared and 11 private coherent
live/copy/record sources. The durable pure-controller result records 32 PASS,
zero failures/errors/skips, in 7.478 seconds; its log hash matches. Final flags
at review were device calls false/root GO pending true. No source/evidence
blocker was found for the bounded diagnostic; this opinion granted no execution
authority. Root subsequently admitted the exact cohort separately.

## Actual diagnostic and remaining gate

Actual owned execution completed zero with known client cleanup in 36,937 ms.
The exact selected raw method stream records one PASS/zero FAIL and OK(1 test).
Its forced internal proof records UNSUPPORTED, fixed STORAGE, one observer
callback and publication_succeeded=false. Source-bound checks verify the
original 63-byte stage hash, absent destination and candidate root, and
positive_store_qualification=false. No store import/reopen/no-clobber or SDK was
called by this diagnostic, and neither old failed synthetic root was read.

All 105 raw-client receipts have known zero terminal status and matching stdout
sizes/hashes. The current pair was updated once each; all before/after cleanup
stop counts are zero. Final metadata independently matches all 35 expected APK
hashes and all 35 prior UIDs, preserving the other 33 package hashes. Owned and
passive process rows are absent; public-volume metadata is unchanged. Final
userdata observation is 1,222,049,792 bytes. Internal candidate absence remains
a distinct host check; external candidate absence comes from the actual
Context-side proof, without host path inference.

The source proof observes external space 3,556,835,328 bytes before and
3,556,827,136 after, with userdata 1,222,066,176 at both source observations.
Those are finite synthetic observations, not a reservation. External space also
falls below the unchanged 4,735,631,360-byte real-candidate preflight by
1,178,804,224 bytes, independent of the unsupported native result. No cause or
ownership of consumed space, capacity exception, cleanup permission or model-copy
route is established.

At closure, all 1,640 admitted source/artifact bindings matched, and owned
start/authorization/deadline plus outer stdout length/hash are coherent. The
coordinator accepted the original executor terminal and the frozen local-only
sealer completed zero. Final device index SHA-256
`4b758f955b43ff5c70af57322a07d9ff7a722aa532f76c99f6c275ff1ef5cee5`
independently rehashes all 320 files/1,935,440 bytes with zero mismatches. The
closed selection explicitly retains UNSUPPORTED, publication false and no
positive store or natural-resource-drain qualification. No further device
execution authority remains.

The next runnable packet is a separately claimed closed native-origin diagnostic
distinguishing missing-symbol refusal from syscall rejection before choosing a
publication/storage remedy. Independent capacity planning must preserve existing
files and reserves. Neither task permits deleting data, weakening the floor,
adopting a benchmark copy or transferring a real model. The positive removable
publication/import gate and full M05.05/M01.05 remain incomplete, with
A/#117/#119/reference-phone holds unchanged.

No dependency/runtime choice changes are planned. Real models/SDK, private
stories, reference phone, ARM64/16 KiB, power-loss, A/#117/#119 and full milestone
gates remain separate.
