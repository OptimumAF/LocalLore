# Native publication-origin review — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). Independent subclaim
[6384957664](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6384957664)
under root6384948023. Review starts from unmerged PR142 head
`e05fc869a5ede27837554e3945af65db7ef877dc` in a separate clean worktree.
The reviewer owns only this report and performs no builds, suites, shared-cache,
device, model or SDK actions. Capacity options use existing evidence only.

## Current disposition

The actual fresh diagnostic passed and observed RENAME_INVALID with origin
classified, fixed STORAGE and publication false. The resolved wrapper was
called and rejected this call with EINVAL; this does not identify which layer
rejected it. The 63-byte stage remained intact, destination absent and no store
qualification was claimed. Source, host/artifact admission, raw result and final
seal were independently reviewed. Positive publication and real-copy capacity
remain blocked; there is no fallback or follow-on authority.
Earlier failed attempts and the fresh legacy-UNSUPPORTED diagnostic retain
their original limits; no new source code retroactively identifies their cause.

## Native and Kotlin boundary

The native path still validates the fixed root/stage, owns one directory
descriptor, resolves the same symbol and attempts the same no-replace rename
at most once. JNI shape, fixed names, codes0/1/3/4 and caught-panic3 behavior are
unchanged. Null lookup now returns5; failed rename immediately captures errno
and calls the same pure classifier tested on the host. It maps EEXIST to1,
EINVAL to6, ENOSYS to7, EOPNOTSUPP to8 and missing/other values to3. There is no
second syscall, retained resource, retry, replacing rename or hard-link path.

Kotlin preserves codes0–4 and legacy UNSUPPORTED2. New codes5–8 are the finite
SYMBOL_UNAVAILABLE, RENAME_INVALID, RENAME_UNAVAILABLE and RENAME_UNSUPPORTED
categories; all retain fixed STORAGE. Unknown values still fail closed, and
codes1/4 retain UNSAFE_PATH. The original one-argument publisher/default-no-op
observer remains available. Observation occurs once after native return before
fixed mapping; a throwing observer cannot imply native rollback.

The actual shared Rust module and tests were read, including absent/negative/
unrecognized/extreme errno cases. Kotlin tests extend exact mapping, unknown9+
and extreme values, redacted errors and observer ordering/count without loading
JNI. Root module cfg wiring includes the same classifier for host tests and the
Android provisioning feature; tests do not mirror a separate native mapping.

Official Android15 Bionic headers define LP64 RTLD_DEFAULT as null and describe
null dlsym lookup as unavailable. The existing renameat2 declaration is API30
with the same signature/NOREPLACE flag. These support the compatibility boundary,
not actual symbol lookup or filesystem execution. [Bionic dynamic lookup](https://raw.githubusercontent.com/aosp-mirror/platform_bionic/android-15.0.0_r1/libc/include/dlfcn.h),
[Bionic publication declaration](https://raw.githubusercontent.com/aosp-mirror/platform_bionic/android-15.0.0_r1/libc/include/stdio.h).

These categories describe observed operation origins, not particular defects.
SYMBOL_UNAVAILABLE does not prove that the OS lacks the wrapper; RENAME_INVALID
does not alone identify a bad flag/path; syscall-origin categories do not
identify which kernel, broker or filesystem layer rejected the operation.
No raw errno, path, provider text or underlying exception enters the observer/UI.

## Synthetic fixture source

The actual new fixture uses a distinct fixed origin sibling and internal proof
root. It stages/forces the original 63 bytes with CREATE_NEW/NOFOLLOW, calls the
real publisher once, checks one callback and exact result-dependent stage/
destination bytes, guards candidate absence and preserves files in both branches.
It never reads an earlier failed or diagnostic child and calls no store/SDK/
engine. An existing-destination contradiction fails rather than qualifying.
Nullable fileKey equality is not a mandatory non-null inode identity proof.

Its closed proof separates diagnostic PASS, publication_succeeded,
origin_classified and positive_store_qualification=false. Origin is classified
only for the four new codes. Legacy UNSUPPORTED, UNKNOWN or other diagnostic
refusal cannot establish the requested origin distinction. A passing diagnostic
may still be a preserved refusal rather than positive publication support.

## Capacity options from existing evidence

The preceding actual external observation is 3,556,827,136 bytes versus fixed
real-copy preflight 4,735,631,360: a separate 1,178,804,224-byte shortfall.
Final userdata was 1,222,049,792 bytes. These are dated endpoint observations,
not reservations or attribution of consumed space. The advertised 8GiB backing
and known benchmark files provide no ownership/reclaimability inference.

| Option | Evidence and remaining gate |
|---|---|
| Preserve the current route and refuse real copy | Correct under known capacity; native support remains independently gated. Fresh admission must reobserve rather than reuse the dated sample. |
| Plan a larger separately backed app-owned volume or test environment | Needs a separate owner-scoped preparation, preservation plan, Context discovery/device/host mapping, unchanged reserves, new pin/native qualification and fresh admission. Adding a second eligible volume alone fails the exact-one policy; preserve existing data and satisfy that policy rather than silently selecting the larger one. This review performs no AVD/media mutation. |
| Use more internal capacity | The default internal route remains unchanged; the observed userdata cannot cover even the fixed artifact plus existing import reserve. Any separate capacity preparation must preserve canonical saves and earlier evidence. |
| Reuse a benchmark file, delete earlier data, lower floors or silently switch model | None is authorized or justified by aggregate free-space measurements. Benchmark ownership, new model identity/runtime/quality and release policy remain separate gates. |

The repository's offline storage explanation compares supplied host groups and
budgets without collecting new measurements or identifying responsible writers.
It can support a separately claimed planning task, not fresh device permission
or cleanup. Host partition aliases must not double-count shared backing. Runtime
cache growth remains uncalibrated and potentially sensitive; model SHA does not
attest cache integrity. No capacity option overrides #117/#119/A, physical-phone,
ARM64/16 KiB, real-model/SDK or full milestone gates.

## Host and admission evidence

The actual Rust owned result records zero exit/known cleanup in 75,984 ms.
Its worker runs pinned fmt-check, strict locked/offline clippy for all Android
package targets with model-provisioning and warnings denied, then package tests
sequentially. Retained stdout records 90 passes, zero failures/ignored, including
all three new classifier tests. The separate script log records 446 passes in
20.668 seconds. These files were read independently; the reviewer ran no check.

Final compiled source is `69342d8ccc87fad61045ec516caca52bf74961d5`. Host seal
SHA-256 `81835dcbcfe140154f56c11432a4749ba6294d740ccd7fc187a469dd5c7dca5d`
independently rehashes all 1,488 files/170,117,736 bytes with zero mismatches.
Actual regular and volume XML each records 299 tests/31 suites, zero failures,
errors or skips; actual lint XML each has zero errors/seven advisories. Owned
results record zero exit/known cleanup in 353,454 and 318,703 ms. Actual volume
APP SHA-256 is `318f84bd85400bc58ee67b6c843427f0cf927baa36a846739831e8273a218c4e`,
TEST `185aac71e0a4d00ba9367425fc982a9cc942ea57a4fe65e0c55c8003aa5230b9`.
Signed/artifact/class audits pass; only volume TEST contains the fixture.
Packaged cloud/device external exclusions remain present. These checks establish
no Android publication or physical-device result.

Exact proposal `bc7d7413915e40bad4de1df92c58d6e3c6362915dcf0a04dc134454a1e7fd131`
was reviewed disabled. All 1,663 bindings/172,484,785 bytes independently rehash
without mismatch, including 64 shared and 13 private coherent live/copy/record
sources. The durable controller result is 37 PASS, zero failures/errors/skips,
in 10.261 seconds; log hash matches. Phase/request/selected method, fresh35
hash/UID/captured-process gates, two-pair updates and PASS-dependent proof/final
cleanup remain closed. No old-root read, storage remedy or model/SDK capability
is admitted. Review found no source/evidence blocker for that bounded proposal;
root alone owns execution admission and subsequently admitted that exact cohort.

## Actual origin result and closure

Actual owned execution completed zero with known client cleanup in 43,891 ms.
The exact selected raw stream records one PASS/zero FAIL and OK(1 test).
Its actual proof records RENAME_INVALID, origin_classified=true, one callback,
fixed STORAGE, publication_succeeded=false and positive_store_qualification=false.
The source-bound stage/destination checks retain the original 63 bytes/full hash,
absent destination and candidate slot. This establishes the requested fresh
lookup-versus-rename distinction without changing the old attempts' category.

All 105 raw clients have known zero terminal status and matching stdout
length/hash. Only the current pair was updated once each; all pre/post stop
counts are zero. Final metadata matches all 35 expected APK hashes/all prior
UIDs, preserving the other 33 hashes, with no owned/passive processes. Public
volume metadata is unchanged. Internal candidate absence is a distinct host
check; external absence is the actual Context-side assertion, without host path
inference. These endpoint checks do not qualify SDK drainage or audit all data.

The source proof observes external free 3,556,827,136 bytes before and
3,556,818,944 after, userdata 1,299,030,016 at both source observations. Final
userdata is 1,299,017,728 bytes. The external real-copy shortfall is now
1,178,812,416 bytes against the unchanged 4,735,631,360-byte lower bound.
Free-space changes do not attribute ownership or authorize deleting data.

Owned start/authorization/180-second deadline and outer stdout length/hash are
coherent. The coordinator accepted the consumed original terminal; frozen
local-only closure completed zero. Final index SHA-256
`7a87494483a08197d9fd59c889d835080be8e6ada88b4e6d995051826ad923d5`
independently rehashes all 327 files/1,957,888 bytes with zero mismatches. Its
closed selection retains publication/store qualification false and no natural
resource-drain credit. No further device execution authority remains.

## Source-consistent inference and next work

After the actual result, official Android15 MediaProvider source was inspected:
its FUSE rename handler returns EINVAL for nonzero flags. That is consistent
with the observed rejection of NOREPLACE=1, but this cohort did not trace the
device's dispatch path or authenticate its daemon implementation. It is a
planning hypothesis, not a proven cause or permission to remove the flag.
[Android15 MediaProvider FUSE rename source](https://raw.githubusercontent.com/aosp-mirror/platform_packages_providers_mediaprovider/android-15.0.0_r1/jni/FuseDaemon.cpp).

The next useful work is a separately claimed host-side publication/capacity
design comparison, preserving existing files, exact-one selection and reserves.
Any new publication protocol or larger independent environment needs its own
reviewed contract/admission; no live fallback, storage mutation, model copy or
weakened floor follows from this diagnostic. Positive removable publication/
import, #117/#119/A, reference phone and full M05.05/M01.05 remain incomplete.
