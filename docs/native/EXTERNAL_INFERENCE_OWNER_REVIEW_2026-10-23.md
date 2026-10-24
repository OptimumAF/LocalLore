# External inference owner review, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.04 partial
and M05.05 backend prerequisite. Exact base:
`cf9332718cc5ffd98c5a4ab8fa0295205d5c9a10`.

Report-only independent review was claimed in
[comment 6377708614](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6377708614),
under coordinator claim 6377698265, in a separate clean worktree. The reviewer
inspects implementation and executor evidence without invoking a build, device,
model, model copy or original save. Findings are not owner acceptance.

## Runtime compatibility research boundary

This implementation adds a generic trusted inference-owner prerequisite, not a
runtime dependency or production backend selection. Ordinary workspace creation
continues to select the scripted fixture explicitly. Configuration failure must
not silently fall back to it. No model output receives path/profile selection,
canonical write access or arbitrary tool execution.

During preceding source-only reconnaissance, current official
[release metadata](https://github.com/google-ai-edge/LiteRT-LM/releases/tag/v0.18.1)
and [Google Maven metadata](https://dl.google.com/dl/android/maven2/com/google/ai/edge/litertlm/litertlm-android/maven-metadata.xml)
still identified LiteRT-LM 0.18.1, source
`bda624851d74be34d4e1f7fac1fc4155939539c7`. The freshly reread
[publisher POM](https://dl.google.com/dl/android/maven2/com/google/ai/edge/litertlm/litertlm-android/0.18.1/litertlm-android-0.18.1.pom)
declares Gson 2.14.0, Kotlin reflection 2.4.0 and coroutines Android 1.11.0.
Existing audited SDK classes have Java classfile major 65. The Java-only
benchmark uses an installed Java 21 compiler targeting 17 and a separately
qualified newer lint analyzer; those results do not qualify the ordinary
Kotlin 2.2.21 Compose app against the SDK.

The current [Kotlin compatibility matrix](https://kotlinlang.org/docs/gradle-configure-project.html)
includes Kotlin 2.4.0 with Gradle 8.11.1 and AGP 8.10.1. The
[AGP requirements](https://developer.android.com/build/releases/agp-8-10-0-release-notes)
and [Java toolchain guidance](https://developer.android.com/build/jdks) distinguish
compiler, daemon and Android runtime roles. A separately pinned SDK/Compose
experiment remains an implementation option requiring actual compatibility,
dependency/license and lifecycle checks; this packet selects no such upgrade.

The exact existing model candidate is **Gemma 4 E2B**, not Gemma 3n. Fresh
[pinned publisher metadata](https://huggingface.co/api/models/litert-community/gemma-4-E2B-it-litert-lm/tree/a790a852d433991c0c0a41c1154cf9b3850300fa?recursive=true)
reconfirmed `gemma-4-E2B-it.litertlm`, 2,588,147,712 bytes, SHA-256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
The [prepared card](https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm/blob/a790a852d433991c0c0a41c1154cf9b3850300fa/README.md)
and [Google card](https://huggingface.co/google/gemma-4-E2B-it/blob/3e22461f65e89153144f8adb70e3b8c2cc9845a7/README.md)
declare Apache-2.0, with Google's [Gemma 4 license](https://ai.google.dev/gemma/apache_2).
Earlier Gemma-specific terms must not be conflated with this artifact.
LiteRT-LM's [source license](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/v0.18.1/LICENSE)
is Apache-2.0; the SDK's multi-component notices still need preservation and
component-specific redistribution review. Metadata verification is not a new
model load, local/device hash, transfer or performance result.

Pinned [Conversation source](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/v0.18.1/kotlin/java/com/google/ai/edge/litertlm/Conversation.kt)
explicitly leaves internal rollback after cancellation unresolved. Engine and
Conversation closure, callback drain and blocking preparation completion must
be independently tracked. Coroutine cancellation or an elapsed timeout cannot
prove native teardown. This motivates the generic owner boundary without
claiming SDK ownership qualification.

## Implementation and verification

Native `open_local` configures the existing WorkspaceRegistry lease and Host,
not a parallel save authority. Ordinary `open` still explicitly selects the
scripted provider. External polling and one-shot response submission retain
scope/branch/revision/turn, immutable prompt/schema, profile and complete budget
bindings. Tickets increase across owners in the registry; replayed, foreign,
cancelled, closed and retired tickets cannot receive replacement output.
Existing fork and deletion serialization remains attached to the same database
and lease. Rust still validates, prepares and atomically commits accepted turns.

The Kotlin owner runs native preparation and role work independently off Main.
It polls ticket liveness while opening/running work, owns role/Engine teardown,
and withholds native Ready until terminal/drain/close and preparation join are
known. Cancellation with a known terminal result can recover normally. Any
uncertainty poisons reuse and closes the same native lease, including borrowed
fork capabilities; scheduled invalidation is distinguished from a known
successful return. A still-running loader is retained after an observation
timeout rather than labelled released. Unknown workers/children retain their
parent owner. Recovery after quarantine requires a separate fresh owner/process
reading canonical SQLite state; it does not reuse the poisoned handle or
silently restart inference.

Source review found three concrete Kotlin draft issues. Late completion of
`start` ignored failed child release before closing its parent Engine; an
exceptional `start` before returning its child could likewise close an unproven
parent; and a fixed narrator cap of 220 rejected otherwise valid trusted
profiles allowing up to 350. The author now retains the parent after an
unreturned/undrained child, checks late child release before parent close, and
accepts the existing profile contract's maximum. Regression vectors cover the
uncertain-start and late-undrained-child cases. Actual checks remain required.

A native test held its control guard outside a scoped-thread callback. An
assertion failure inside that callback could wait for the blocked closer before
releasing the guard. Review requested moving the guard inside the callback so
unwind releases it before scoped joining. The corrected source retains all
original assertions. This was a test failure-path issue, not a demonstrated
production close bug. Existing `fork_retire_owner` already fenced borrowed owner
admission early; the new explicit bridge close additionally retires pending
inference before blocking Host cleanup.

The central Android draft initially borrowed a fork handle after preparation
was active, conflicting with the new borrow guard. Review requested borrowing
before starting preparation and observing the already-borrowed handle; the
production guard must stay intact.

The coordinator's first actual native integration attempts failed with
`TooLarge` before any role request because the 2,048-token test profile could
not fit the current complete prompt package and reserve. The initial failing
source and diagnostics remain retained. Positive integration uses the existing
4,096-token profile; a new negative 2,048-token case must retain the rejection,
no pending ticket and unchanged accepted history. A direct packet unit vector
still checks propagation of a 2,048-token profile. No production cap or prompt
schema is loosened by this fixture correction.

The retained first full host run returned nonzero after eight new integration
failures and an abnormal `0xc0000409` test-process exit. The later focused
diagnostic identifies `TooLarge` as the fixture failure; it does not establish
the cause of that abnormal process exit. The corrected focused run then passed
all 11 external SQLite integration tests in 2,078 ms, child zero with known
cleanup. Review read these separate terminal results and logs; the failed run
is not relabelled as successful.

The Kotlin author separately found a cancellation-order race by source review:
native ticket revocation after a proven terminal/closed role could trigger
`cancel` on the closed SDK object. The correction skips cancellation only when
the completed await explicitly reports terminal, retaining drain and close
proofs. A new regression covers that ordering. This is not attributed to an
observed failure in the preceding 17-test build.

The author then found that sharing an inference owner across two transports
could allocate a second native lease before rejecting the foreign port.
Transport identity is now reserved before allocation. Review found the inverse
ordering through the plain JVM port seam could still orphan a subsequent
production allocation. Atomic token/port admission now refuses both orderings
before dispatch/allocation. Two further regressions cover these cross-seam
cases, without introducing another runtime or gameplay interface.

## Executed host and Android checks

The coordinator's completed full host gate took 239,250 ms, child zero with
known cleanup. Independent review rehashed its 76,126-byte log and parsed 610
workspace Rust passes plus three native-linker passes, zero failures, and six
Python suites totalling 384 passes (140, 10, 14, 22, 13 and 185). The earlier
focused 11-test result overlaps this suite and is not added as unique coverage.
Eight existing ignored Rust entries remain ignored, not passing evidence.
The coordinator separately observed 186 script tests pass after the audit
changes. Its supplemental receipt transcribes the terminal tool result rather
than claiming to be a retained raw execution log; this review did not rerun it.

The first Android build completed with 199 JVM passes, including 17 owner tests,
and five JNI methods compiled. Its first APK audit correctly refused the new
verification package because it was not explicitly allowlisted. The coordinator
retained that result, added only the exact package identity and verified the
seven audit tests before the final artifact audit. No broad package exemption
or default-allow change was introduced.

After the source-derived race/binding fixes and sixth JNI method, the final
owned Android build completed in 96,078 ms, child zero with known cleanup.
Review independently parsed all 23 final JVM XML files: 203 tests, including 21
owner tests, zero failures, errors or skips. These replace the earlier overlapping
counts rather than being summed. Final lint has zero errors and one existing
`GradleDependency` warning. The new JNI methods were compiled; compilation alone
is not device execution.

Review independently rehashed both final APKs and all four packaged native
libraries against the artifact audit, with exact matches. Both actual manifest
dump texts omit `sharedUserId`; the test runner targets the exact isolated
application. The app requests only its own signature-protected receiver
permission. The audit checks SDK/package identity and native 16 KiB alignment.

| Final artifact | Bytes | SHA-256 |
|---|---:|---|
| Application APK | 23,457,912 | `6fb05b1fda50f76a96107bb71e9e38b8fbfaf74485fc15d216bf5ea613e0abf0` |
| Test APK | 2,376,140 | `6a0f5099e32f3303e9543be8ccbce6e2a7167ed70d410077e3888bf89cd6792b` |

The actual captured six-method CRLF build input is 19,808 bytes, SHA-256
`041b9c9223238a4a4af7269afefcad327b98b08739302fb14bd89ac57465f9d5`.
Its LF-normalized Git encoding has SHA-256
`4edee3a59a919d17efa4c31dbdbb3ad7db4b11afe733b5db524520cce52fe88b`.
These are encodings of the same source, not separate device executions.

## Actual bounded device evidence

The B-only cohort completed in 12,563 ms, child zero with known cleanup. Review
independently rehashed all 44 completed client stdout/length/status records with
zero mismatch. An independent parser matched all six frozen method names,
class/current start-pass pairs and final runner terminal after those pairs,
with no duplicate, skipped or unfinished method. Raw instrumentation is 4,426
bytes, SHA-256
`3ca1b0960c1eba7eaf50079aa98a47993c5bd983330d95fe295c819779dc52e1`.

The actual methods exercise external free-text commit/retry/reopen, withholding
Ready until Engine close while Main responds, unknown-close same-handle
invalidation and fresh canonical reopen, native cancellation during a synthetic
role, same-workspace story deletion during that role, and JNI admission bounds
without fallback. Drivers are synthetic; no SDK or model was invoked. Tests
use the real production transport/JNI/Host/SQLite and explicit new app-private
synthetic directories. Native slot checks precede owned temporary deletion;
the intentional unknown-worker case retains its synthetic database. The six
methods do not render the Compose UI or establish physical runtime ownership.

Before dispatch, review independently rehashed all 38 disabled-proposal input
bindings. The corrected controller points to the actual external-inference
build directory. Initial package comparison requires the preceding exact 25
entries and both new packages absent. After both audited APK installations and
the complete expected 27-entry map, it captures the exact installed test UID.
Any conditional test-only cleanup would require every method to pass, a fresh
sole exact test process/UID, matching package UID and the unchanged 27-entry map.
The actual test namespace was already absent, so **no force-stop occurred**.
This observation is not a general natural-process-exit qualification.

Independent map comparison confirms the original 25 hashes unchanged across
installed/after/final 27-entry maps. Original namespace-absence and capacity
checks passed. Final userdata available was 1,618,149,376 bytes, above the
unchanged 1,207,959,552-byte floor. There was no A query, model operation or
original-save access. Repeated pure controller runs cover the same 47 methods,
not independent sets of new tests. The initially wrong build-output path and
misparsed pre-freeze source label remain retained preparation corrections with
zero device calls, rather than fabricated device failures or passes.

## Closed evidence and remaining gates

Independent rehash found zero mismatches in the selected closed host evidence:
154 files / 109,396,654 bytes, index 29,937 bytes, SHA-256
`6ac0bd3a4a160ea63cf74a51d55b4da8754b3ef08dbd01bf267b4bf021718dc0`.
The selected closed device evidence contains 136 files / 251,634 bytes, index
23,132 bytes, SHA-256
`0b3e85e78a409c96ea48bef8e7c903b168c347fc0999e8c66199d5eb4b392305`.
Later coordinator receipts are explicitly outside the earlier selections.
These are indexed closed selections, not claims that live/temp/build trees
were sealed. Raw diagnostics, unique identities, APKs and private paths remain
local. The device specialist reports dispatch stopped and its lease released;
the reviewer issued no follow-up device command.

M05.04 remains partial/in review, with the M05.05 backend prerequisite implemented
and locally verified; no milestone checkbox or owner acceptance follows. M01.01
physical-phone work remains blocked. Existing device/cache preservation and
consumption failures remain unchanged, so new real inference is not admitted.
No model quality, SDK cleanup, ARM64 execution, sustained performance, two-emulator
or real-backend reference-phone qualification is established. The next product
step is a concrete runtime driver for this owner, with separately verified
toolchain compatibility and actual terminal/drain/close behavior, followed by
trusted provisioning and UI wiring under the unresolved device gates.
