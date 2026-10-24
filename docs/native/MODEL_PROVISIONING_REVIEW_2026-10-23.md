# Model provisioning independent review

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 prerequisite
and M05.04 supporting. Review claim 6378454938 under coordinator 6378445316.
This report records source inspection separately from executed evidence. It is
not owner acceptance, runtime selection, redistribution clearance or device
qualification.

The source and evidence sections follow the investigation in order. The early
hard-link design is superseded by the final native-publication correction;
the final host and Android sections describe the implemented result.

## Scope and primary sources

The reviewer owns this report only in a separate branch/worktree based on
`cb251e7145f0a7038a0a1bd7976035bb95d957d2`. No reviewer build, test suite,
device operation, model-content/cache read, model copy or inference ran.

Official Android sources were read on 2026-10-23:

- [Storage Access Framework](https://developer.android.com/training/data-storage/shared/documents-files):
  selected documents can come from local or cloud providers. A selected URI is
  access to a document, not a trusted filesystem path or artifact identity.
- [EXTRA_LOCAL_ONLY](https://developer.android.com/reference/android/content/Intent#EXTRA_LOCAL_ONLY):
  requests locally available selections; a provider remains a separate component.
  The app's missing INTERNET permission does not police another provider's
  network behavior.
- [ContentResolver](https://developer.android.com/reference/android/content/ContentResolver#openAssetFileDescriptor(android.net.Uri,%20java.lang.String,%20android.os.CancellationSignal))
  and [AssetFileDescriptor](https://developer.android.com/reference/android/content/res/AssetFileDescriptor#createInputStream()):
  opening can return null or fail; descriptors are caller-owned and can represent
  streams/subsections. A cancellation request is not proof that a blocking
  provider read, open or close returned.
- [App-specific storage](https://developer.android.com/training/data-storage/app-specific)
  and [noBackupFilesDir](https://developer.android.com/reference/android/content/Context#getNoBackupFilesDir()):
  private persistent storage needs no broad permission. Recompute its current
  root rather than persist an absolute device path. No-backup storage is
  excluded from automatic remote backup; it does not protect against a
  compromised OS or deliberate export.
- [Activity tasks](https://developer.android.com/guide/components/activities/tasks-and-back-stack):
  launch modes affect Activity reuse, not proof of native teardown or process
  termination. A process-level owner admission guard must remain authoritative.

Fresh bounded HTTPS reads of publisher metadata, without weights, confirmed
the retained artifact at revision
`a790a852d433991c0c0a41c1154cf9b3850300fa`:

| Field | Publisher metadata |
|---|---|
| Repository | `litert-community/gemma-4-E2B-it-litert-lm` |
| Artifact | `gemma-4-E2B-it.litertlm` |
| Exact bytes | `2588147712` |
| LFS SHA256 | `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c` |
| Pinned card license metadata | `apache-2.0` |

The [exact tree API](https://huggingface.co/api/models/litert-community/gemma-4-E2B-it-litert-lm/tree/a790a852d433991c0c0a41c1154cf9b3850300fa?recursive=true&expand=false)
returned 3,576 bytes, SHA256
`050ed847fdfbfa0411a35976f671eb3a2dab8ebab58959b816890ccb3d64e554`.
The [pinned model card](https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/raw/a790a852d433991c0c0a41c1154cf9b3850300fa/README.md)
returned 17,262 bytes, SHA256
`b044a20b524e854497d5074e3afee2e7b186eb482b9f0c1f499692d5421ecdc7`.
That tree has no standalone LICENSE file. The card identifies
[Google's base model](https://huggingface.co/google/gemma-4-E2B-it), whose current
card also reports Apache-2.0. These are provenance/license metadata checks,
not a complete redistribution audit. Existing SDK mixed-notice and component
clearance limitations remain in the [worker review](LITERT_WORKER_REVIEW_2026-10-23.md).
No runtime/model dependency or supported device tier was selected by this review.
The [official SDK release](https://github.com/google-ai-edge/LiteRT-LM/releases/tag/v0.18.1)
was freshly checked and still identifies 0.18.1 at `bda6248`. The candidate
retains the prior pinned SDK/toolchain graph; this packet adds no dependency.

## Source review

The store, setup controller/Activity/manifest and central candidate factory
were inspected as drafts in the authors' separate worktrees. Concrete findings
were returned before freeze:

1. The original built-in identity contained uppercase `E2B`, while the store
   identity type accepts lowercase IDs. That object could not initialize.
   The application identity is now lowercase; the publisher's case-sensitive
   repository/artifact names remain exact. The central profile test constructs
   the actual built-in identity.
2. A competing FileChannel could open, encounter a JVM-overlapping lock and
   close while the first import remained active. The official
   [FileLock contract](https://developer.android.com/reference/java/nio/channels/FileLock)
   documents platform-dependent process-lock release when another channel on
   the same inode closes. A process-wide admission flag now precedes opening
   any store channel; the persistent file lock supplements this local guard.
   This is source reasoning, not a multiprocess or Android filesystem test.
3. An independent Activity launch could otherwise create a new SDK owner while
   a prior owner retained uncertain resources. The candidate now admits one
   transport attachment for the process lifetime, with no reset on finish,
   constructor failure or apparent close. Configuration recreation reuses the
   existing ViewModel. `singleTask` is supplementary; it does not prove cleanup.
4. Construction exceptions originally bypassed the fixed unavailable surface.
   Candidate construction now maps ordinary exceptions to a fixed category,
   preserves the admission reservation and requests close for an owner already
   constructed before transport failure. Setup resolves the private store lazily
   inside IO operations. No provider path/message reaches displayed failures.
5. Play's synchronous ViewModel factory originally fetched `noBackupFilesDir`
   again on Main. Even that Android getter can perform filesystem work. The
   candidate now caches one store first established on IO; Play consumes its
   planned paths or fails with the fixed unavailable surface. It does not query
   or create private directories on Main. The normal setup check/import API is
   unchanged.

The inspected import path copies an explicitly selected stream into a fixed
private staging file, reads at most expected bytes plus one, checks the complete
SHA256, closes the source, forces the staging file and publishes using an atomic
no-clobber hard link. Existing valid bytes are reused; existing corrupt bytes
are preserved with a failure. An appearing destination cannot be replaced.
Unsupported hard links fail closed. Only the fixed owned staging name is
recovered while admission and the persistent lock are held. Unknown files and
cache contents are preserved; no recursive deletion occurs. Root/model/cache/
staging/lock path checks reject symlinks where inspected.

The free-space check includes a fixed reserve without addition overflow. It is
a preflight observation, not a reservation against another process consuming
space. Mid-write failures remain ordinary failure paths. The store does not
promise directory-fsync durability after sudden power loss or authenticate
hostile OS replacement after checking a path. No parser safety follows solely
from matching a published hash.

Cancellation invalidates UI readiness immediately, but the setup operation and
store slot remain reserved until actual open/read/close/cleanup return. The
picker adapter uses `openInputStream`; it has no API cancellation signal and
can remain in Stopping with a noncooperative provider. No second import or
runtime fallback follows that state. Publication may already have won before
cancellation; later full revalidation discovers a complete artifact rather
than promising rollback. Restart rehashes bytes instead of trusting a receipt.

The setup controller tests supplied for central execution include pre-dispatch
cancellation, noncooperative completion, disposal, stale picker delivery,
foreground revalidation, fixed errors, duplicate start and process-held
admission. The Activity requests local/openable documents without retaining a
URI grant. Provider metadata never selects an expected hash, private path,
profile or runtime. The source manifest removes the scripted MainActivity
launcher and makes Main/Play nonexported in the isolated candidate. Actual
merged-manifest verification is a separate execution obligation.

The candidate pairs its static artifact/profile provenance with the existing
real worker and the same NativeWorkspaceTransport. Kotlin adds file/admission
state only; Rust still constructs model context, validates proposals and commits
accepted history. The ordinary app keeps its explicitly scripted construction.
No model hot replacement is offered during or after a claimed candidate session.
Finishing an Activity is not a process restart; the held-session message
requires closing the app completely and does not promise Close kills it.

## Execution evidence inspected

The coordinator reported the original script process reached authoritative
terminal exit 0. The reviewer independently inspected its retained result and
matching raw output: 192 script tests passed in 18.921 seconds; outer owned
execution took 19,703 ms with known cleanup. The 478-byte stdout SHA256 is
`00a686345da758ada127be90842150b65a8e3269cd1ca95678b59d7ff70883e3`.
This includes the model-specific audit additions. Their source checks the actual
aapt launcher/activity boundary, with hostile stale launcher/export/alias cases;
it is not just permission/package matching.

The four instrumentation methods were inspected for meaningful assertions:
missing built-in model disables Start on the real Compose setup surface; a tiny
original byte fixture exercises Android hard-link publication/reopen; a symlink
cannot redirect staging or destroy an outside fixture; and cancellation of a
blocked read retains import admission until actual return. Each creates only
fresh isolated synthetic file namespaces. These methods do not initialize a
model or establish real inference. The missing-model method also invokes the
same candidate transport factory on Main, reads actual Rust/JNI/SQLite
`configured_native_owner` metadata with `loaded=null`, borrows the same handle,
closes the transport, waits for actual `InvalidHandle`, and rejects a second
process attachment. That path creates only the new candidate's empty workspace;
it never prepares a turn. Their device execution remains pending.

After the IO-store correction, the coordinator confirmed authoritative terminal
exit 0/known cleanup for the first complete production/unit-source run. The reviewer
independently parsed the retained 27 XML suites: 273 tests, zero failures,
errors or skips, including 23 store, 16 setup controller and three candidate
admission/profile tests. The host symlink fixture actually ran. That run's raw
9,298-byte stdout SHA256 is
`8d69cdbe3218db2306e3a326b21763bab930b1689ee1ac3aa2087ed693efbb69`;
owned elapsed time was 109,500 ms. Main, AndroidTest and UnitTest lint analysis
tasks ran; retained lint has zero errors and four unsuppressed warnings
(two UsableSpace, one GradleDependency, one OldTargetApi). UsableSpace is an
advisory about potentially reclaimable cache, not evidence that the conservative
free-space reserve failed or permission to clear existing experiment caches.

The ordinary build's coordinator-confirmed terminal run passed 203 tests in
23 suites with zero failures/errors/skips, compiled the shared MainActivity
change and ran lint under the existing ordinary graph. Its owned elapsed time
was 125,891 ms; raw stdout SHA256 is
`881934b3f1bd5e3543ee9fa0e49403a0d3f096756aa1042fc3e682bb5c2ccc74`.
The final AndroidTest-only source deepening compiled and packaged separately;
those source edits do not change production or JVM test bytes. Its retained
owned result is exit 0/known cleanup in 63,812 ms. The source is 7,759 bytes,
SHA256 `efb46762fbc72083eca9e2bb36c4ed82356102808f5649e26f4a3a5e01c53e6f`.

The disabled B-only controller source was independently inspected. It preserves
the complete prior 29-package map and adds only the new modelverify APP/TEST
pair, leaves A and existing storage floors untouched, requires four exact paired
PASS records plus final runner terminal before any conditional TEST-only cleanup,
and verifies installed hashes/UID ownership before that cleanup. The proposed
44-client already-absent and 47-client exact-stop paths disclose that an external
test process stop cannot prove natural exit or native model ownership. Source
freeze, signatures, final APK audit and independent rehashes precede promotion.
The 47 host-only controller fixture results were read; the reviewer did not run
them or dispatch a device.

The final disabled proposal SHA256 is
`ca5fec3f39a12c51f2152978678c7baa2ff5b22103c90d071cbdfa601f11a2ad`.
The reviewer independently rehashed all 60 bindings with zero mismatches before
promotion, including current sources, audit files, controller helpers, prior
sealed package map and both actual selected APKs. Flags were still disabled/
pending at that review. This is source/artifact review, not authorization.

The first device cohort's selected APKs were independently rehashed:

| Artifact | Bytes | SHA256 |
|---|---:|---|
| APP | 73,809,384 | `7c9c6f38e99d2e4b8cdea787ec8ef3277db00fd6b3b966cdab910613210ca8f5` |
| TEST | 1,754,737 | `7859b3e06dcb34694095915e2d54b45055b04d9f204e304e8d13d193ec95af74` |

Captured actual aapt output shows Setup as the sole MAIN/LAUNCHER, Main/Play
nonexported, and Setup/Play `singleTask`. The merged debug app also retains the
existing AndroidX test ComponentActivity; the audit's owned-activity rule does
not claim that no third-party debug Activity exists. Captured apksigner output
verifies both APKs with the same debug signer. The app retains exactly six
native libraries across both ABIs; TEST has none. Full SDK LICENSE/NOTICE
assets independently match the pinned hashes and sizes, 16,086/2,198,164 bytes.
Complete included notices remain distinct from redistribution clearance.

The first actual aapt audit stopped because the oracle accepted hexadecimal
`0x2` but aapt emitted decimal `2` for singleTask. The revised finite numeric
check admits those equivalent forms and rejects another mode; actual launcher/
export requirements remain unchanged. The earlier helper/audit observations
are preserved. A package-only repack removed incremental ZIP overhead. The
reviewer compared both pairs: all 156 APP and 121 TEST unique entry names and
decompressed bytes are identical before/after repack. No production/source or
test-assertion change follows from that layout/signature change.

## First Android run: retained failure

The original admitted device process reached terminal exit 2 with known cleanup
in 20,187 ms. The controller stopped after its 27th client, the instrumentation
command. No post-instrumentation device action ran. The reviewer read the actual
13,900-byte output, SHA256
`27fbec0a0aac246155251d1981814d892b496478e1a582211c106f05d26371ff`:
four paired results, two PASS and two FAIL, with runner terminal present.
Publication/reopen and blocked-read cancellation both failed at `prepareRoot`
before the intended copy/read path, with `UNSAFE_PATH`. This is a failed device
cohort, not successful import or cancellation qualification.

The source compares an absolute root with its canonical form. A framework
private-storage alias is a plausible cause, but that raw output contains no
path and does not prove which alias differed. Source investigation is required.
The recommended narrow correction resolves the trusted framework no-backup
anchor on IO before appending a fixed child; it preserves arbitrary-root and
owned-path symlink rejection rather than weakening the store's checks.

Two passing methods do not erase these failures. The missing-model UI waited
for Choose enabled, which can also occur in Unchecked/Failed; it did not prove
the genuine Missing state. The reviewer requested an exact missing-state
assertion. The symlink method could reject the same bad ancestor before reaching
its selected staging link, so its pass is not isolated evidence of the intended
symlink check until the positive path works under the same trusted anchor.
The direct factory/native configured-status, borrowed close/InvalidHandle and
second-attachment assertions did run and pass; no model was initialized.

All first-run source, APKs, controller bindings and failure output must remain
retained. A corrected run needs new source/artifact verification and a fresh
explicit admission; an observation timeout, failed test or fixture repair does
not authorize resuming the stopped controller. The coordinator owns actual
suites, device admission and the PR. No reviewer device call occurred.

The reviewer independently rehashed the stopped selection: 156 files,
781,775 bytes, zero mismatches; index SHA256
`a3b14b198b40138b0bfacc7d3cc4be3843402fa3212b1fc7c279938c92f51a7d`.
All 27 client records are completed exit 0/known cleanup and match their retained
stdout size/hash. Before/installed maps contain 29/31 exact expected packages
and preserve every prior hash. The two successful install clients record
174/196 stderr bytes; their content is unavailable under the existing count-only
capture, so no cause or zero-stderr claim follows. There is no after/final map,
post-run process-settlement observation or external force-stop in this stopped
selection. Original bindings were copied before source corrections.

The original host selection was also independently rehashed: 396 files,
227,922,176 bytes, zero mismatches; index SHA256
`2c60d825cdc17536e2effdd488619375e73c47b53e4449df680b14c149d42035`.
This is a closed hash selection, without a claim that its Windows namespace
is read-only. The source correction changes only trusted Context anchor
canonicalization and stronger Android assertions. The generic store and its
untrusted-root/symlink refusal remain unchanged. Corrected execution and any
new device admission are separate evidence, still pending here.

## Corrected host verification

The corrected production/store-anchor and strengthened Android oracles were
rebuilt with authoritative terminal exit 0/known cleanup in 106,641 ms. Raw
8,839-byte stdout SHA256 is
`cd721538bd479b2b6712b23c17e0b5b87d9534ced064ae95dace26c5c6855e4f`.
The reviewer independently parsed retained XML: 27 suites, 273 tests, zero
failures/errors/skips. Lint remains zero errors/four warnings; the generic
store and first worker's ownership rules are unchanged.

The corrected host selection binds 99 files/76,109,960 bytes, independently
rehashed with zero mismatches; index SHA256
`797481e45e2b674d877d59baae8889178660239815891bbf475b0db61d28ea55`.
It is a closed hash selection. Selected corrected APKs independently match:

| Artifact | Bytes | SHA256 |
|---|---:|---|
| APP | 73,809,384 | `24f59ee6c9d8fbb0932435989af888891c5f13df77c505f87a5fbc87da2c1fce` |
| TEST | 1,755,057 | `44b1e3889f4cc764f2076edf666acad50e2ce6a4fc6fc3edb88698135ae58eb4` |

The corrected instrumented source is SHA256
`1e2b93f17f044a0f656a988ce88976e069961ee95b1a3f88d8301d16e2347713`.
The symlink method now positively admits its ordinary root before injecting the
staging symlink, and Missing is distinguished from a failed file check. Final
APK audits retain the same manifest, signatures, native and full-notice
requirements. Android execution of this corrected pair remains separate.

## Separate read-only settlement preparation

A separate nine-query metadata-only proposal was inspected with all 73 bindings
rehashing correctly. Its first wrapper stopped before any child/device dispatch:
it requested 210 seconds while the copied process runner accepts at most 180.
The initial 18 pure fixtures and this review missed that integration limit.
That is not an Android query failure or an observation of post-run device state.
The original proposal/wrapper and prelaunch failure are retained.

The revised disabled proposal is SHA256
`b801ec15bd46cdade7b92d8549b8e4371e29792834a6521afecf615566e7b6b4`;
all 73 bindings were independently rehashed with zero mismatches before root
admission. It still selects exactly nine fixed read-only identity, package,
process and storage metadata queries with unchanged floors and expected 31-map.
It contains no lifecycle, installation, instrumentation, model/cache/save query
or A operation. Observed processes confer no cleanup authorization.

The reviewer inspected the new 21-fixture result and the actual integration
regressions: the wrapper's shared 180-second/request/output budget is passed
through the copied real process validator with pre-cancellation and a patched
Popen that must never run; the invalid original 210-second request is refused.
The actual wrapper main guard is compiled from its AST and must propagate a
nonzero return via SystemExit. This closes the fake-dispatch-only coverage gap;
it does not authorize a device dispatch. No reviewer suite or device call ran.

The subsequently root-admitted read-only settlement completed in 2,891 ms,
exit 0/known cleanup. The reviewer independently rehashed its 43 selected files,
157,822 bytes, with zero mismatches; index SHA256
`b6452b2ac6eb0f7d920c01504e46b3070bee3fcc9b38fe02ff06ab1a38103335`.
All nine raw client outputs match their records and are completed exit 0/known
cleanup with zero stderr. The process listing contains only the exact TEST
process among LocalLore names, with UID matching fresh package metadata; APP
and foreign LocalLore processes are absent at that observation. The complete
31-map matches the failed pair plus all prior 29 hashes. Userdata available is
1,465,380,864 bytes, above the unchanged floor. No lifecycle action ran. These
observations do not establish natural TEST exit, runtime ownership or permission
to clean up; any mutation remains a separate admission.

Root separately admitted cleanup of only the disposable TEST host after a new
disabled proposal was reviewed and all 23 bindings matched. It required the
same captured process/UID twice, fresh installed UID and exact 31-map before
one exact TEST force-stop. APP/foreign/drift cases abort; no application stop,
install, model, cache, save or A operation is included. The original failed
cohort's all-PASS requirement was not resumed or changed.

Actual cleanup completed exit 0/known cleanup in 5,437 ms. The reviewer rehashed
52 files/130,315 bytes with zero mismatches; index SHA256
`a89a855c1594b1eca832c2f15007f4c45526fe13663f2783257d71a9518cc9ba`.
All 15 client outputs match their records, completed exit 0/known cleanup/zero
stderr. Raw before/immediate process records match the captured sole TEST,
client 11 is the sole exact TEST stop, the subsequent listing contains no
LocalLore process, and both 31-maps match exactly. Post-cleanup userdata is
1,465,262,080 bytes. This is disposable test-host cleanup, not evidence about
natural process exit or real native-model resource ownership.

## Second Android stop and platform publication correction

The first corrected pair was admitted separately for an explicit update of its
own two verification packages. Its controller stopped at instrumentation again:
authoritative exit 2/known cleanup in 16,312 ms, 27 clients, two passing and two
failing methods. The genuine Missing-state/native factory method and the
positive-root-then-child-symlink method passed. Tiny-copy/reopen and blocked-read
cancellation/retry failed with the fixed STORAGE exception from the store's
guard. The latter method includes a valid retry after cancellation drains, so
this output alone does not locate failure before or after the blocked read.
No provider path or underlying exception is exposed. The exact failing
operation/cause remains unobserved; a particular SELinux denial is not claimed.

Raw instrumentation stdout is 8,691 bytes, SHA256
`a78d85cb259d788b5042479425178e602f3ccf0b80d656ed036959f688c6ec82`.
The reviewer independently rehashed the stopped 151-file/805,879-byte selection,
zero mismatches; index SHA256
`cff94f985b606a0617cb5b900cc92740db82a4e1707acb3d065c397a4762732a`.
All 27 client records match their retained stdout and known exit/cleanup. The
before and installed 31-maps preserve the prior 29 packages while replacing
only the selected APP/TEST pair. There are no post-instrumentation observations
inside that failed cohort. Its acceptance gate remains failed.

Independent primary-source review identifies a definite incompatibility in the
old publication design regardless of the sanitized exception: Android 15's
[application neverallows](https://android.googlesource.com/platform/system/sepolicy/+/refs/tags/android-15.0.0_r1/private/app_neverallows.te)
prohibit untrusted applications from creating hard links to any file type.
This applies to app-private destinations as well. Source SHA256 is
`71c7b3c6c0a5af0282c5213f194b7d358f360a8b66f32ec5a00f0d90c270b515`.
The host hard-link tests therefore could not qualify Android publication.
Changing to Os.link, weakening policy or rooting a device would not repair the
application contract.

The coordinator's replacement is a narrow fixed-name JNI publisher using
`renameat2(..., RENAME_NOREPLACE)` with one canonical directory descriptor,
`O_DIRECTORY | O_NOFOLLOW`, and fixed `model.part`/`model.litertlm` children.
It refuses any existing destination, including a symlink, and has no replacing
rename or raw-syscall fallback. The wrapper returns only a small fixed status;
bounded UTF-8 directory bytes carry no provider URI, metadata or model content.
Successful rename consumes the stage, so the store immediately clears its
stage-ownership flag before further checks. A cancellation or later cache
failure preserves a published complete artifact. Forced file contents and
atomic publication do not promise directory durability after power loss.

The [Bionic API declaration](https://android.googlesource.com/platform/bionic/+/refs/tags/android-15.0.0_r1/libc/include/stdio.h)
introduces the public wrapper at API 30. Runtime lookup through public libdl
avoids an unconditional symbol requirement when loading on minSdk 26; missing
symbol or unsupported kernel/filesystem fails closed. This does not establish
support on API 26–29 or all filesystems. No Cargo dependency or SDK upgrade is
added. The JNI module is enabled only by the candidate `model-provisioning`
feature, and the build input fingerprint includes the selected flag and source.
The ordinary profile leaves this capability disabled.

Review caught a concrete ABI error before final source freeze: Android arm64's
directory/no-follow flags differ from x86_64. Corrected source uses arm64
`0x4000`/`0x8000` and x86_64 `0x10000`/`0x20000`, as declared in the primary
[arm64 UAPI header](https://android.googlesource.com/platform/bionic/+/refs/tags/android-15.0.0_r1/libc/kernel/uapi/asm-arm64/asm/fcntl.h)
and generic x86 header. The initial common-flag suggestion was incorrect.
Compiling both ABIs does not demonstrate execution of either one. The reviewer
has inspected the corrected source, injection/cleanup ownership and feature
integration; replacement build and Android execution remain separate evidence.

## Settlement of the second stopped TEST host

The new read-only settlement completed exit 0/known cleanup in 2,985 ms. The
reviewer independently rehashed 35 files/106,929 bytes, zero mismatches; index
SHA256 `9241369740d4829ef2175f60a23f89595bc91890cda2b7f635478010496e3bd2`.
All nine raw records match their hashes/sizes and are exit 0/known cleanup with
zero stderr. The sole LocalLore process observed was the captured TEST host,
matching fresh installed package UID. The complete 31-map matches the selected
24f59ee6…/44b1e388… pair plus the unchanged 29, with 1,465,212,928 bytes
available userdata. This contains no lifecycle action or ownership qualification.

Root separately admitted the same narrow disposable TEST cleanup. The reviewer
inspected the actual controller and closed evidence, not a device. Fresh nine
metadata queries and an immediate process recheck matched that exact PID/UID,
installed UID and full 31-map. Client 11 stopped only the exact TEST package;
subsequent process output contains no LocalLore process, and the package map
remains identical. All 15 clients are exit 0/known cleanup/zero stderr, with
matching raw hashes. Authoritative outer completion is exit 0/known cleanup in
7,468 ms. The 51-file/130,004-byte closed selection independently rehashes with
zero mismatches; index SHA256
`957435d934b517901b6512f02a4842e80ad099f8da7055966990dbe8309f63fa`.
Userdata available before/after is 1,465,200,640 bytes. This neither resumes the
failed all-PASS cohort nor qualifies native-model ownership or natural exit.

## Final native-publication host selection

After the ABI correction, the selected candidate build completed exit 0/known
cleanup in 40,969 ms; APK repack/audit completed exit 0/known cleanup in
12,735 ms. The earlier pre-ABI-fix build is retained separately and superseded.
The reviewer independently rehashed all 194 selected files/90,898,633 bytes,
zero mismatches; closed index SHA256
`71dd514dcf172ec354712518f8f35857b24fd248265a0b72534c6c3008d031e7`.
This hash selection excludes live build/cache/temp paths and does not claim a
read-only Windows namespace. Retained XML independently parses as 27 suites,
275 tests, zero failures/errors/skips. Lint retains zero errors and four
unsuppressed warnings. These host tests inject a host publisher; they do not
execute Android's JNI publication operation.

| Final candidate artifact | Bytes | SHA256 |
|---|---:|---|
| APP | 73,829,560 | `228ec0aa4a742707df3a73c4fe14509a7047d3cd3bc7e20f02b5b352dd527415` |
| TEST | 1,755,365 | `6ea5c33f3023280ca304b30f844228760e02279e576902a3ba8d824c37569477` |

Both packaged Rust libraries independently match the retained symbol-inspection
inputs byte for byte. Each exposes the new fixed-name publication JNI entry
and imports dlsym, with no required renameat2 dynamic symbol. The reviewed
frozen native source matches current source exactly, SHA256
`dc8b447d92862a017c7c3a54157b533b640f79c27000b7ccae6d6268f9c31fbc`.
The final APP has 156 unique ZIP entries, exact full SDK LICENSE/NOTICE bytes,
no Internet permission or shared UID, and the same actual Setup-only launcher,
nonexported Main/Play and numeric singleTask manifest requirements. Both APK
signature records verify with the same debug certificate. This demonstrates
selected packaging and source/build provenance, not successful Android import
or ARM64 execution. The four-method Android fixture now includes native
regular-file and symlink destination no-clobber assertions as well as tiny
copy/reopen and cancellation/retry; execution remains a separate gate.

## Final synthetic Android execution and ordinary exclusion

The final disabled native-publication proposal was independently reviewed and
all 68 bindings rehashed before root admission: SHA256
`9df172337efbddf5fecbc48a1d86264ced6e2cb48aed052429a9dd8c1b412aee`.
It updates only the existing APP/TEST pair, preserves the other 29 packages,
and retains the four exact paired-PASS gate before any post-instrumentation
action. The retained 50 pure-controller fixtures pass; the reviewer inspected
their results and actual-budget/CLI regressions, without running them.

The actual B execution completed exit 0/known cleanup in 22,828 ms. Independent
inspection of 2,998-byte instrumentation stdout, SHA256
`c37c9c37efcaa155bcd6bd140cef6c0f6bf5f902831df9d0bdfc1330d869deda`,
shows the four exact methods each start and complete PASS, zero failures.
This exercises actual Android tiny verified publication, rehash/reopen/reuse,
regular-file and symlink no-clobber, positive-root child-symlink rejection,
blocked-read cancellation retaining the slot until actual return, clean retry,
and the Missing UI plus actual configured native factory/borrow/close boundary.
The selected source constructs no SDK Engine and prepares no story or turn.

All 47 client stdout hashes/sizes independently match their records, each
completed exit 0/known cleanup. The two install clients retain 174/196 stderr
bytes by count only; their unavailable content is not inferred. Instrumentation
is client 27; the sole external lifecycle action is client 31's exact disposable
TEST stop, after four PASS and fresh package/process/UID proof. The before map
matches all 31 prior packages; installed/after/final maps equal the final
228ec0aa…/6ea5c33f… pair plus the identical protected 29. Final available
userdata is 1,465,159,680 bytes, above the unchanged floor. No APP stop, model
read/copy, A call, screenshot or original-save operation is included.

The closed success selection independently rehashes with zero mismatches:
139 files/270,719 bytes, 23,588-byte index SHA256
`eb664c86a4a9b11a01113512395648aa2e93a007f356b7664c6098cc926ded23`.
An initial local closure helper incorrectly expected the owned pair to be
absent, although the admitted controller already required a 31-to-31 update.
It stopped before sealing and is retained with that failure. Review of the v2
helper diff confirms only the local prior-pair assertion changed to require
presence and the explicit update flag. No device call, raw result, controller
or acceptance gate changed. The failed earlier instrumentation cohorts remain
failed historical evidence. TEST cleanup does not prove natural process exit
or physical SDK/model resource ownership.

The final ordinary profile was freshly built for both Rust ABIs, separately
from the candidate. Its original record is exit 0/known cleanup in 177,485 ms.
The reviewer independently rehashed 38 files/36,811,287 bytes, zero mismatches;
closed index SHA256
`89a15340bd1fc3212161dd185fbb7645ab8213916cda1b99ba0b08a25b34d539`.
Retained XML independently totals 23 suites/203 tests with zero failures,
errors or skips. Lint has zero errors and one GradleDependency warning.
Ordinary APK is 23,214,204 bytes, SHA256
`29c56f9d6b37d030d352ecf78ac983cd515774801b27a1a49ae356095e27c111`.
Its signature verifies; its manifest excludes Setup/Play and Internet
permission; its four native libraries exclude the LiteRT SDK. Both packaged
Rust libraries match the symbol-inspected bytes and exclude the candidate
publication JNI export. The retained artifact audit confirms 16-KiB ELF load
alignment. No ordinary installation or device execution was performed here.

## Review disposition and remaining gates

No unresolved source blocker was found within this candidate provisioning
packet after the fixes above. The independent reviewer executed no build,
test suite, Android call or inference and read no model content. Execution
claims in this report come from inspected, hashed coordinator/executor evidence;
primary-source/API conclusions and read-only evidence rehashing are independent.
This handoff is a source/evidence review, not merge approval or milestone
acceptance. Root owns integration, ticket acceptance and the focused PR.

Actual qualification is limited to synthetic Android API 35/x86_64/4-KiB B
tests and the host/packaging checks stated above. Full SAF picker/provider
roundtrips, real model import/initialization/generation, a physical phone,
ARM64 execution, API 26–29 import availability, other filesystem behavior,
directory durability after sudden power loss, and model redistribution
clearance remain unestablished. Existing runtime/device/model gates remain
unchanged; no checkbox should imply those broader results.
