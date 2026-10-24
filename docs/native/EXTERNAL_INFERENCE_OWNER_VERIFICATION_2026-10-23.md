# External workspace inference owner verification — 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 prerequisite
and M05.04 supporting; [#5](https://github.com/OptimumAF/LocalLore/issues/5),
M01.02 supporting. Implemented partial work remains in review; milestone tasks
are unchecked pending full criteria and owner acceptance.

## Implementation and source boundary

The optional app owner pumps external director/narrator requests through the
**production workspace lease**, with its existing Rust Host, SQLite, session,
fork and deletion authority. It returns Ready only after known worker terminal,
drain, role close, engine close and joined native preparation. Unknown resource
ownership permanently quarantines the owner and invalidates its same native
handle, including borrowed handles. Strict profiles/tickets and bounded UTF-8
prevent worker replies from selecting another scope, request or provider.

MainActivity still constructs the explicit scripted provider. No inference SDK,
model, dependency pin, network capability or gameplay rule was added. The
synthetic JNI fixture's `configured_native_owner` / `real_model=true` status
means configured external ownership; `loaded` is null. It is not model-load
or runtime-performance evidence. See the [contract](EXTERNAL_INFERENCE_OWNER_CONTRACT.md).

Base: owner-merged `main` at `cf9332718cc5ffd98c5a4ab8fa0295205d5c9a10`.
Independent native and Kotlin authors used separate worktrees and exact path
claims; an independent reviewer inspected source and retained evidence. The
coordinator integrated shared module/build/test boundaries and ran actual builds.

## Host checks

`python scripts/check.py host --offline` passed under Rust 1.93.1 on Windows,
with two Cargo jobs and an isolated host target directory. The bounded process
owner completed in 239,250 ms, child exit 0, known cleanup. This is harness
wall time, not inference latency.

- 610 workspace Rust tests plus 3 linker tests passed; zero failed. Eight
  existing ignored entries are one-time capture/measurement helpers, explicit
  capacity/IPC qualifications, two Windows symlink-privilege cases and one
  superseded compatibility scenario. Ignored tests are not passing evidence.
- Warnings-denied Clippy, formatting and four fixture comparisons passed.
- Six Python suites passed: 140 + 10 + 14 + 22 + 13 + 185 = 384 tests.
- After adding the exact APK package allowlist regression, all 186 script tests
  passed again (including seven APK-audit tests). Other host sources were unchanged.
- Focused corrected external-workspace tests: 11 passed, zero failed, zero
  ignored, serial execution; bounded owner completed in 2,078 ms.

Full-host stdout: 76,126 bytes, SHA256
`9cd313a96164163b135754b8677222eddd2dddead97c815f346e93bfff43558f`.

## Retained failures and corrections

The first host attempt compiled and passed native units, then eight new
integration methods failed and the process aborted before its aggregate.
The abort's cause is not established. Original source, binary and output were
retained. Failure-safe fixture cleanup now preserves failed synthetic directories
without a second unwind panic. A focused diagnostic proved `failed/TooLarge`
before provider delivery: a 2,048-token positive fixture could not fit the
current guarded prompt and its reserved output budget.

Successful fixtures now use the existing 4,096 context profile. A separate
2,048 negative integration case requires TooLarge, no pending request, unchanged
accepted canon and zero allocated ticket (the next successful ticket is 1).
The pure request test still verifies non-hardcoded 2,048 propagation. Production
budgets, context compiler and canonical assertions were not relaxed.

Review also corrected late allocation ownership, cancellation after a proven
closed role, and atomic transport reservation before native allocation. The
corresponding final Kotlin regressions actually passed below. An initial APK
audit refused the unlisted external verification identity; the explicit package
was added with rejection/permission regression coverage. No audit guard was
removed. Initial artifacts and results remain retained separately.

## Android build and artifact checks

From `apps/android`, Java 17 and existing offline dependencies:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreExternalInferenceVerification=true --project-cache-dir .gradle-external-inference -Pkotlin.incremental=false --offline --no-daemon --console=plain --max-workers=2 -Pandroid.builder.sdkDownload=false
```

Initial build completed in 340,641 ms with fresh Rust release builds for both
x86_64 and arm64-v8a, 199 JVM passes (17 new owner tests), and five compiled JNI
methods. The corrected final build completed in 96,078 ms, child exit 0 and
known cleanup; **203 JVM tests passed**, including **21 owner tests**, across
23 XML suites, zero failures/errors/skips. All six final JNI methods compiled.
Lint has zero errors and one existing `GradleDependency` advisory. The existing
framework interruption fixture also emits an AtomicReference/Boolean warning.
Final build stdout: 5,855 bytes, SHA256
`684fc0d9c7261edc5e4829b0c0f9265b2df439526461e250091c7fb47effc4fa`.

The final APP is 23,457,912 bytes, SHA256
`6fb05b1fda50f76a96107bb71e9e38b8fbfaf74485fc15d216bf5ea613e0abf0`.
The final TEST is 2,376,140 bytes, SHA256
`6a0f5099e32f3303e9543be8ccbce6e2a7167ed70d410077e3888bf89cd6792b`.
The final six-method test source is SHA256
`041b9c9223238a4a4af7269afefcad327b98b08739302fb14bd89ac57465f9d5`.

Actual aapt/ZIP/ELF audit confirms the exact isolated APP package and its sole
app-owned signature receiver permission; no Internet capability. The TEST has
the exact AndroidJUnitRunner/target and only its expected test permission.
Neither manifest declares sharedUserId. The exact four native libraries are
uncompressed and 16 KiB ZIP/ELF aligned on both ABIs. TEST has no native library.
Release, combined timeline, combined capacity and wrong-cache profile probes
all refused with their expected fixed configuration errors and known cleanup.

## Evidence retention

The closed host/build selection contains 154 files, 109,396,654 bytes. Its index
SHA256 is `6ac0bd3a4a160ea63cf74a51d55b4da8754b3ef08dbd01bf267b4bf021718dc0`;
root and the independent reviewer rehashed every entry without mismatch.
It retains initial/final source, failures, process results, XML and APK audits;
raw local evidence and binaries are not uploaded. The later 186-script rerun
was observed through its original terminal tool handle; its supplemental receipt
is explicitly a transcription, not an independently retained execution log.
The primary full-host 384-test Python log remains retained independently.

## Device qualification and remaining gates

The separately admitted B-only synthetic cohort passed all six paired tests
with the actual production transport/gateway/JNI/Host/SQLite. The 12,563 ms
outer process and all 44 client commands completed with known cleanup. The
TEST process was already absent; no force-stop occurred. Complete initial
25-package and installed/after/final 27-package maps preserved all prior 25 APK
hashes. Final userdata available was 1,618,149,376 bytes, above the unchanged
1,207,959,552-byte admission floor. No A query or model action occurred.
See the [device report](EXTERNAL_INFERENCE_OWNER_DEVICE_2026-10-23.md) and
[independent review](EXTERNAL_INFERENCE_OWNER_REVIEW_2026-10-23.md).

The six cases exercise original free-text commit/reopen equality, Ready held
until engine close with a Main heartbeat, unknown-close quarantine of borrowed
handles, native cancellation discarding late output, story deletion cancelling
the same ticket, and JNI malformed/oversize admission plus explicit provider
selection. They use direct transport/gateway calls, not Compose/Activity UI.
Host compilation and synthetic JVM/JNI results do not establish SDK
resource ownership, actual model quality, physical-phone performance or ARM64
execution. No physical phone was available; M01.01 remains blocked. Existing
A artifact mismatch and #117 consumption / #119 preservation failures remain
unchanged. Earlier local-copy permission was already exercised; this packet
makes no new model copy, inference or repair claim.

The next product task is a concrete runtime adapter implementing this narrow
worker contract, with independently resolved SDK/toolchain compatibility and
actual terminal/drain/close evidence, followed by trusted model provisioning
and UI wiring. Real inference must respect the unresolved device/cache gates.
