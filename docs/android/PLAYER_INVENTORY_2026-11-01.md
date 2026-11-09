# Android player inventory — 2026-11-01

Refs #13 (M09.03/M09.04, supporting M09.02/M09.06). In review; full criteria
remain unchecked. Stacked on the frozen current-chat product PR #326, retaining
#325/#323/#322/#320. No dependency, Rust production code, protocol, database or
gameplay-rule change. The pending SDK11 operation and its APKs remain frozen.

## Problem and behavior

The native `play_presentation_v2` operation already returns every current item
owned by the actual seed player, for both domain versions. Android checked all
item fields but retained only `inventory.has("potion")`. Every saved world then
showed a hardcoded healing-potion row, discarding unrelated items and quantities.
This loss is established by source inspection; no artificial missing-API RED or
pre-fix rendered Android failure is claimed.

The decoder now preserves a detached, ID-sorted, unmodifiable list of
`PlayerInventoryItem(id, quantity)`. Existing strict item-field, identifier,
native-observer ownership, unsigned-16, scope, head, actor and history checks
remain. Legacy `hasPotion` key-presence semantics are unchanged.

`SavedSnapshot` and `ShellState` append nullable inventory fields. Null means
unavailable; an empty list means a validated empty inventory. The gateway
forwards the list only with the existing coherent snapshot and final attachment,
revision and catalog checks. Every saved-state publication replaces the field,
including null, and defensively copies the list. No title, narration, notice,
fact, initial-world JSON, rule-profile or literal player ID supplies inventory.

Saved stories show a compact summary and a read-only scrollable dialog with
every exact item ID and quantity. Items have no display-name field in this
contract; no names, healing effects or loan recipients are inferred. Possession
is not permission to give or consume an item. There are no gameplay callbacks
or extra native queries in the dialog. The in-memory demo retains its exact
original healing-potion row.

The summary stays inside the existing single lazy `state` item; outer item keys
and transcript prefix counts are unchanged. Dialog state lives outside the lazy
list so scrolling does not dispose it. Logical story/branch selection changes
close it and fence retained open/dismiss callbacks. Same-scope head/title or
inventory refreshes update accepted rows. Generation and an unavailable text
provider do not block coherent read-only inspection. Recovery, another workflow
or an unavailable projection closes/disables it; known-empty remains openable.
Drafts, input kinds, accepted messages and existing action scope rules remain.

## Original tests and independent review

Independent writers used separate physical D: worktrees with exact ownership.
Root preserved old branches/source ZIPs and all 87 preexisting ignored files,
then integrated four writer commits centrally. Two source/oracle findings were
corrected before Android testing:

- Lazy row absence can mean offscreen, rather than absent from inventory. The
  migrated helper first checks exact accepted-state potion membership/quantity,
  then the healthy UI summary count and every expected row. The long-list case
  explicitly demonstrates the original offscreen false absence. During recovery,
  source inventory plus disabled summary is distinct evidence; it does not claim
  individual rows are rendered while inspection is disabled.
- Initial eligibility omitted nonnull inventory. The corrected common condition
  closes/fences a list-to-null transition; restoring data does not reopen it.

Exactly 17 presentation assertion lines change across eight existing Android
test files; Root independently checks that every other original line is
unchanged. Existing cancellation, restart, contention, revision, history and
canonical assertions and method identities remain. Existing native test source
has a byte-identical 22,140-byte/eight-test prefix; three tests are appended.

The new 853-byte original synthetic golden is the complete native Host reply,
SHA-256 `b52f5b64a2398f4009f6a139ac7220d590aac2280c58dceb79b3643fb34dd505`.
A real Engine with an opaque player, two owned stacks and a foreign-item canary
undergoes a real accepted author correction to Domain2. Actual Host output must
equal the whole golden twice, with canonical bytes, history basis and zero
persistence writes conserved. Other tests exercise full-stack transfer in both
domains, native zero-stack refusal and loan-consumption refusal. No domain tag
is fabricated. Existing corpus cases with empty inventory are not substituted
for this positive opaque-player fixture.

Five new JVM wire tests decode that verified golden and explicit structural
mutants. They cover all rows/quantities, deterministic ordering, detached and
unmodifiable output, empty versus malformed inventory, wrong owner, unknown
fields, invalid quantities and scope/head mismatch. Six new real ViewModel
tests use a clearly synthetic gateway for accepted-state publication, null/empty
replacement, same-head story/branch switches, failed recovery, cancellation,
late results and disposal. Wire detachment is executable evidence; direct
mutation of a caller-owned saved-snapshot list after VM publication is covered
by source review of the defensive copy, not a separate executed VM oracle.

Native valid seeds reject zero quantities and final consumption removes an
entry. Kotlin retains its old structural 0..65535 boundary; its zero test is
explicitly a wire mutant, not a claim that native gameplay creates zero stacks.

## Actual verification

All commands ran from physical D: directories with process-local TEMP/TMP/TMPDIR
at `D:/Dev/_Temp`. Existing D: Cargo/Gradle caches and installed tools were used;
no dependency or SDK download, global setting or cache relocation occurred.

| Check | Actual evidence |
| --- | --- |
| Native host | `cargo +1.93.1 test -p locallore --features host --test m09_player_presentation_v2 --offline --locked`: 11 PASS (8 existing +3 new), 0 failures/ignored/filtered; 0.18s suite, 11.477s worker, 11.580s owner |
| Native ownership | Actual child joined, return0, cleanup/capture known, 58 source pins unchanged, budget monitor closed with no faults; no inference/Android execution |
| Android host FIRST | Failed before compilation/tests in6.908s: this reused checkout had no SDK path; unchanged source and original log/result retained |
| Corrected Android host | One full integrated gate PASS in51.675s; 42 actionable tasks/42 executed, no cache result substituted |
| JVM | 439 unique methods /52 XML suites, 0 failures/errors/skips, including all11 new cases |
| Compile/lint | Production and AndroidTest compilation pass; lint0 errors, one existing GradleDependency warning and one existing AutoboxingStateCreation hint; inherited AtomicReference/Boolean compiler warning remains |
| Compiled UI | Actual class/javap contains all3 public zero-argument Compose journey methods; this is class evidence, not DEX/APK or runtime proof |
| Source/conservation | All2,547 tested raw source files unchanged during both attempts; original87 ignored files unchanged; source/diff checks pass |

The corrected gate supplies the existing SDK through process-local ANDROID_HOME
and ANDROID_SDK_ROOT, disables SDK download, and changes no code or assertion:

```text
gradlew.bat --offline --no-daemon --console=plain --rerun-tasks -Dorg.gradle.java.installations.auto-download=false -Pandroid.builder.sdkDownload=false :app:testDebugUnitTest :app:compileDebugAndroidTestKotlin :app:lintDebug -x :app:buildRustAndroid
```

Tested integrated source is `3450f314b0810947904544aee7fbdfecb518d7a2`.
Its source ZIP has2,547 files/11,389,196B, SHA-256
`ef78916d2e6a808243583da2285385c213eee3ba3b2da7f2736d06553024d9d4`.
Final documentation follows that tested code. JDK21.0.4, Cargo/Rust1.93.1,
cached Gradle8.11.1 and the existing AGP/Kotlin/Compose pins remain. The Android
build wrapper does not claim a complete supervised descendant/deadline proof;
the native cohort's finite-owner evidence is reported separately.

## Preservation and unrun gates

Private controls/source and failed captures remain at
`D:/Dev/Experiments/LocalLore/2026-11-01-player-inventory-v1` (64MiB budget).
Selected recovery is at the corresponding `D:/Dev/Recovery/LocalLore` root
(128MiB budget); final seals are in the ticket handoff. Generated Rust output
is retained under `2026-11-01-player-inventory-generated-v1`; new Android output
stays in the integration worktree. Measured combined generated bytes477,061,271
are below4GiB. Full offline metadata produced2.3MB, exceeding an initial2MiB
estimate but staying within the actual64MiB controls cap; it is retained.

All three new Compose journeys remain UNRUN. Their inert screen snapshots cover
known/empty/unavailable/demo views, scope/retained callback and workflow fences,
draft conservation, twice-sized text, long IDs/all rows and reachable Close.
Compilation and semantics assertions do not establish rendered/touch/TalkBack,
real keyboard, actual JNI/ARM64, native Android gameplay, real inference, phone,
performance, privacy, process death or full-journey acceptance.

No new APK, JNI cross-build or device result is claimed. All frozen SDK10/SDK11
sources, proposals, build manifests and APKs remain unchanged. No actual guest,
retirement, ledger lock/plan/reservation/admission/auth/input/prepare/boot,
ADB/phone/port/process census, model, settings, unrelated-emulator/shared-service
or merge operation occurred. The exact SDK11 approval question remains pending;
it does not cover this new product source. Next runnable host task: build/audit
the new inventory app/test pair before separately source-bound device testing.
