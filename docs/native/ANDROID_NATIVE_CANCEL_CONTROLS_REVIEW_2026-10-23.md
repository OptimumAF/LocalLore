# Native cancellation controls review, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.04 partial,
and [#8](https://github.com/OptimumAF/LocalLore/issues/8), M04.04 supporting.

## Review scope

The independent reviewer used a separate worktree at prerequisite
`c9aa4c5429c7f8bcf3924e8fdc21732fa9266e96`, with report-only ownership claimed
in [comment 6377335859](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6377335859).
The reviewer read the production Compose controller, DurableGateway,
NativeWorkspaceTransport, JNI registry, Rust Host cancellation/persistence path,
and the earlier transport ownership, storage recovery and synthetic control
fixtures. The reviewer did not build or invoke an emulator, device process,
model or original save. Execution results below belong to the coordinator and
device specialist; independent review is not owner acceptance.

## Concrete findings resolved before dispatch

The initial private device controller saved paired terminal test records but
could proceed to external test-host cleanup after a failed method. A terminal
failure does not prove that in-test native-owner checks passed. The controller
now retains parsed failures and stops that original cohort unless every frozen
method passed, before test-host observation or cleanup. This leaves any stopped
cohort intact for a separately scoped settlement rather than using process
termination as native-release evidence.

The fixture compares the permitted player snapshot and accepted receipts.
Review requested explicit checks of the existing privileged-observer refusal:
Mira, Sable and omniscient inspection must return `Forbidden`, and the player
view must identify its observer as player. These negative admission vectors do
not inspect NPC-private knowledge or establish a new broad isolation gate.

## Fixture boundaries

The six methods run the actual Compose screen, ShellViewModel and DurableGateway
against production NativeWorkspaceTransport, JNI, Rust Host and SQLite. A fresh
synthetic child of the isolated application's no-backup directory contains all
fixture storage. The Context wrapper changes only that local storage root.
No production hook, dependency, schema or alternative gameplay authority is
introduced.

The independently authored fixture was initially frozen at
`075c0498d15fdc05630079d61f528cdbff6e7615`, source SHA-256
`936e7598daca77b9be658f2efbaddaca918ba05132eacf4a8dded509a275c1ba`.
The first actual build reported a nullable parent access warning. Follow-up
`edcd93d16c8d1f730950b9322abc5e5214c76d5b` binds that parent with `checkNotNull`
before the same directory/root containment checks; it preserves all six methods
and their assertions. The revised source SHA-256 is
`bb157bb788ca5ea132dd4664a6664f59c1fca55181c2986ab3f5051e51ef8147`.
The reviewer inspected both versions and the private controller's successful-suite
admission before dispatch. Six frozen method identities are checked as paired
start/terminal records followed by the final runner terminal; a generic
instrumentation process exit code does not count as a test pass.

An earlier dialogue receipt is actually committed at revision one before the UI
submits the potion gift. Preparation and cancellation gates delay delivery of
completed real native replies. Three separate methods corrupt only delivery of
the cancellation acknowledgement: foreign key, unfinished phase and missing
committed receipt. Recovery must use the complete original cancel command,
with one original submit/prepare and no gateway commit. Late preparation and
disposal must not replace visible accepted history.

The committed case deliberately orders a real Rust commit before a real native
cancel. Its commit is counted separately from gateway commands. It demonstrates
that known ordering, including one accepted gift and no rollback claim; it is
not randomized native-race stress or cancellation during active inference.

Before temporary deletion, fixture cleanup releases gates, clears the ViewModel
store on Main, closes the gateway, waits for wrapper exchanges to reach zero,
and acquires all four real JNI owner slots simultaneously. Probe handles close
on IO even on failure. This checks the actual registry's four-owner bound after
the production transport's asynchronous teardown. Closing a Kotlin object or
externally stopping an Android process is not substituted for this assertion.

Close/reopen compares complete permitted player projection, accepted receipts,
inventory and revision through Rust's SQLite owner. It does not compare
omniscient canonical bytes or read private NPC contexts. Canonical rules and
acceptance remain in the existing Rust implementation; Kotlin assertions do
not establish another ledger. All handles must pass release checks before the
contained create-new synthetic root can be deleted.

## Execution evidence

The coordinator's first owned build completed in 69,359 ms, child zero with
known cleanup. Independent parsing of its 19 JVM XML files found 150 tests,
zero failures, errors or skips. The nullable-parent warning prompted the narrow
test-only correction described above. The coordinator rebuilt the test APK and
lint in 45,328 ms, child zero with known cleanup; the unchanged JVM suite was
not represented as newly rerun. Final lint reports zero errors and one existing
`GradleDependency` warning. The existing unrelated AtomicReference compiler
warning remains documented.

The reviewer rehashed both final APKs and all four packaged native libraries
against the final artifact audit, with exact matches. The application remains
byte-identical to prerequisite #125; this packet changes no production code.
The final source and separately rebuilt test APK are bound explicitly:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Application APK | 22,479,391 | `fc01b1ce8516b499d5ca47c518176cba1a93ba4350c2e27d1a14f7ec99950e40` |
| Test APK | 2,348,183 | `ed5b4e1a66bf4519b89c651cf451ad9d059a5b4d4bb24935a2334d38a2aab605` |

The device specialist's 43 pure controller fixtures passed. Their repeated run
after the final source binding is the same 43 methods, not 86 unique tests.
Review inspected their failure-before-cleanup case and successful-suite fence.
Two stopped local preparations remain recorded: an unsupported Python file-write
keyword and an exact final-audit phase mismatch. Both occurred before device
calls; a new version corrected each without rewriting its failure record.

The device specialist's actual B cohort completed in 48,782 ms, child zero with
known cleanup. All six unchanged methods passed, with six paired start/pass
records, no skipped or unfinished method, and a final runner terminal after
those pairs. The reviewer independently rehashed all 46 client stdout records,
lengths and statuses with zero mismatch; each client completed zero with known
cleanup. Instrumentation stdout is 4,412 bytes, SHA-256
`46b34ea40b530bd8639d6e0cb8e547e298f7ed7d8ddfa038ee831c9357b4c0d4`.

All six passing methods include their own wrapper-drain, actual four-owner-slot
and contained cleanup assertions before the external controller can advance.
The specific recovery and replay assertions passed through real production
transport/Rust/SQLite calls, rather than fabricated acceptance replies. One
conditional exact test-package stop followed the complete passing suite and
fresh process/UID/map admission. It is test-host hygiene, not evidence of
natural test-process exit or model-worker ownership. The previous #125 stopped
baseline and explicit cleanup history remain unchanged.

The reviewer independently compared before, installed, after and final package
maps: all 23 original package hashes remain equal, with only the admitted test
APK replacement. Original namespace-absence and capacity checks passed. Final
userdata available was 1,644,118,016 bytes, above the unchanged 1,207,959,552-byte
floor. No A query or two-emulator pass is claimed by this B-only cohort.

Independent rehash of the closed private device selection found zero mismatches
across 146 files / 270,802 bytes. Its 24,640-byte index has SHA-256
`c691d7f7bf2e2890d55b294ca5079d050bd4db3e804e693181320319c9fa0a93`.
Raw records, unique identities, APKs and private paths remain local. The device
specialist reports all dispatch stopped and the exclusive lease released; this
review issued no follow-up device command.

## Remaining limits

M05.04 remains partial and in review; M04.04 gains supporting native/UI recovery
evidence. No acceptance checkbox or milestone exit gate follows from this
review. A remains blocked by its previously observed storage floor, and M01.01
physical-phone verification remains blocked. No model, ARM64 execution,
sustained performance, natural process-exit or reference-phone qualification is
established. Prepared-reply delivery cancellation is not cancellation of an
active model worker. NPC-private memory contents and omniscient canonical bytes
are outside this fixture's assertions. The reviewer performed read-only
inspection of executor evidence, not an independent execution cohort.
