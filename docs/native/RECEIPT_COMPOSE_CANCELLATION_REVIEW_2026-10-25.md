# Compose cancellation and visible recovery: independent review

Status: **in_review**, M05.05 / M01.05 bounded support. Root claim
`6397202908`; independent claim `6397211578`. The corrected selected control
passes; full milestone acceptance and merge are not implied.

The reviewer owns only this file on `review/m05-compose-cancel`, based on
`56d2f654b6185da4bcb661712b5a994a2a967810`. Source and copied evidence were inspected
without reviewer SDK/ADB/AVD/build/test execution, model-byte reads, disk-image
reads or mutation of old targets and sealed evidence.

## Source findings and boundaries

The new receipt-only, nonexported `ReceiptComposeCancellationActivity` overrides
only the production transport factory. It retains `MainActivity`, its real
`ShellViewModel`, production Compose controls and callbacks. The test obtains the
existing ViewModel rather than replacing its factory. The old gateway API control
and proof namespace remain intact.

The source review verified these important distinctions:

- Manual Activity launch follows off-Main full model verification and admission.
  Launching before that would consume the process reservation without a prepared
  store. No full model hash or directory construction is inserted on Main.
- The empty library initially reports an unavailable text provider. The LOCAL
  check for cancellation was moved after the actual New-story click settles;
  recovery and reopen check it after the saved story is initialized.
- The production header's unconditional fake-inference label was corrected to a
  closed `TextProvider` label. LOCAL says **configured**, not successful inference.
  Exact APK audit sets include the new private activity and proof classes while
  retaining the sole launcher, permissions, services and profile exclusions.
- UI Cancel cancels the ViewModel's waiting Job. This fixture therefore does not
  borrow the API test's original-Deferred result assertion. It requires the actual
  cancellation-refresh notice, settled state and displayed accepted history while
  the Activity remains RESUMED, then worker/owner and canonical checks.
  `onCleared` clearing busy flags cannot earn cancellation success.
- `MainActivity.onStop` also cancels. The Cancel control is scrolled into view
  before sampling, and the resumed/preparing state, actual semantic click and
  final SDK cancel observations are required. A missed window fails without retry.
- Same-trace history, known public drain/close, a post-model borrow guard and a
  refreshed post-close trace are required. Historical trace observations do not
  establish an exact native-active instant, hidden JNI reclamation or immunity to
  unseen later callbacks.
- Recovery uses real UI Send and the production automatic commit. Its full
  accepted-model recheck occurs **after** that commit, unlike the older API
  fixture's test-controlled precommit hash. No test interception delays commit or
  forces the production transport onto IO. Generated transcript comparisons fail
  with fixed messages rather than including narration in diagnostics.

The new host controller has its own strict UI phase/check grammar and fixed
namespace, selectors and stream module. It reuses old actual preflight/import
lineage without rewriting bound files, fabricating old API checks or mutating
global controller constants. Scope normalization is local to validation.
Exclusive evidence creation, raw-first retention, unknown-cleanup refusal,
process/helper retirement, source authorization and aggregate clipping remain.

UI_CANCEL26 / UI_RECOVER24 / UI_REOPEN17 complement preflight12/import16:
95 checks in the actual corrected full control. Phase caps remain 170/170/120s,
with the existing conservative 120s selected-runner gate. Transfer/import and
870s aggregate / 900s outer / 920s entry, 1800s owner and SDK 60s/5s limits are
unchanged. Nominal phase sums do not guarantee completion after all overhead.

## Independently replayed host and admission evidence

Initial execution source is `89a335df2480bc6041c652c46b8085bb23a2bd1b`; receipt/regular
compilation source is `c50f72546d502d6c5dd579ff751fbce1c6ba4a11`.
All **1,546 source rows / 18,949,246 bytes** match current source and snapshot;
all **213** compiled Android rows match. Receipt results contain **423 JVM tests
/ 40 suites**, regular **377 / 36**, with zero failures/errors/skips. Lint has
zero errors and 19/9 warnings respectively. Six APK audit/signature receipts
and their retained output hashes agree with successful known cleanup.

Initial packet's final host discovery passed **758 tests / 80.408s**, known cleanup 82,265ms;
89,623 output bytes, SHA-256
`9340781ea67f1a76afbddda64ad5d801c24cdaea33fa6e89b3025582c5010189`.
The central JVM and host runs include the new codec and controller cases
respectively; host results alone do not qualify actual UI/SDK behavior.

| Initial admitted artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Receipt app | 75,169,295 | `de6bcd7ecde0ca7093a76002ce94d29c69df00e80ed6b1e12408fd34ddd2cb54` |
| Receipt test | 2,946,849 | `1bafa52a0a70ce6952a1093b952e92874ff98c26d357784fe190964db2326778` |
| Regular app | 74,954,584 | `b63980af1d851ed4b1b3d915a0e32d821ba8c8baf6fa40665a43f3ceddfb332f` |

Independent preparation/run review content-hashed 905 tool/source bindings and
checked four public SDK images by metadata only. The reviewer checked initial SD
metadata only; the coordinator retained full stock/initial-disk checks. Fresh
userdata absence, exact generated configuration, three immutable files,
registry/token preservation and free ports passed. No token contents were output.
The admitted profile retains guest 8GiB/four CPUs, userdata12GiB/SD8GiB,
C/D40GiB reserves and 12GiB minimum available host RAM.

The first preflight grant attempt (`40135`, terminal1) refused `host_capacity`
before authorization, driver creation or guest dispatch. Its failing resource
values were not captured; later passing values do not diagnose the cause. The
same unchanged unconsumed proposal then received its separate grant. First
actual preflight (`71580`, terminal0) passed: 44 known-clean clients, one exact
JUnit pass and 12 true checks, 206ms proof observation, SDK false. Raw proof SHA
is `3e9799ef653ba7f2b85109be26972b5d6e5a1bc81c317e1ee5c7fbabfed74d82`.

All 101 preflight bindings/archive copies (88,220,215 bytes) and 105 candidate
bindings/archive copies (88,226,456 bytes) match. Candidate authorization binds
the standing direct human local-copy/SDK consent and fixed destination/model
identity. The weight file is excluded from generic bindings and archives;
reviewer inspection was metadata only. The new candidate input passed its own
strict validator and live identity/deadline checks before root admission.

## Initial actual UI attempt: retained partial result

The first candidate stopped at UI_RECOVER. Independently replayed positive
evidence is preflight12/import16/UI_CANCEL26, totaling **54 checks**. IMPORT
passed in 94,346ms; raw proof SHA
`f572b50a91aa102fa71ce671074a4135cafca14f65b6cf6a483a5abf50838855`.
UI_CANCEL passed its exact selected method in 75,713ms, raw proof SHA
`6d3332ad862be8e5c026962b265e87cde6b0c072dd538959f5eece13061c9daa`.
Its same-history trace records actual cancel entry/return once, ERROR1/DONE0,
drain and conversation/engine known close once, no UNCERTAIN observation, and
revision0/no receipt. Actual UI state checks were earned before Activity close.

UI_RECOVER's selected method failed at the fixed `Accepted transcript is not
visible` assertion after 52.435s. Completed client47 was returncode0/known-clean;
strict runner validation correctly refused a method pass. Its retained 9,452-byte
transcript SHA is
`61d102d69907deaf5c09b81a72b319ca5f174841f5cd7bff0e5f62bfc2aaafb7`.
The passive failure trace records returned DIRECTOR/NARRATOR, paired DONE2,
drain/known conversation close2, engine close1 and no error/cancel/uncertainty.
That is not a positive recovery proof. In the frozen source, accepted notice,
visible revision/potion and two-message state checks precede the failed lookup;
independent native gift, post-SDK model recheck and recovery proof occur after
it and were not reached. No REOPEN was dispatched or qualified.

A concrete selector flaw was then found: accepted heads deliberately retain the
composer input, but transcript lookup used unscoped `onNodeWithText`. The player
message can therefore collide with its retained editable input. Official
[Compose matcher documentation](https://developer.android.com/reference/kotlin/androidx/compose/ui/test/package-summary)
confirms text matching includes editable/input text. The catch discarded the
underlying lookup error, so this counterexample does **not** prove the actual
failure's cause. A passing corrected run must not retrospectively diagnose it.

Original candidate `60146` was consumed at tool terminal1, chunk `0b273e`;
owned worker2 had known cleanup/capture, 360,640ms, 471 stdout bytes and no stderr.
It retained 47 clients and three selected-method attempts, then stopped without
later work. Exact stop followed. Original owner `29812` was consumed at terminal0,
chunk `cb384d`; retained stop_requested closure is 758,687ms, worker1 requested
drain, cleanup/capture/closure true and guest-flush false. Post-stop host checks
record all three tracked identities absent and ports free.

The four initial `sealed-inventory-v1.json` files were independently rehashed:
**2,139 files / 352,365,338 bytes**, zero mismatches. They exclude model/VM disks.
Private evidence is under `C:/Users/Avery/`, using initial prefix
`LocalLore-receipt-compose-cancellation-` and corrected prefix
`LocalLore-receipt-compose-identity-`, then `host`, `environment`, `preflight` or
`candidate` and suffix `-20261025`.

| Initial namespace | Inventory SHA-256 |
| --- | --- |
| Host | `940027f3590208562325bc50e32957136f39d805e3a7059e9a94a0a45d13941e` |
| Environment | `97a11b2fe3b48cba0b7ec2c5227fa9a20526204bab448d0ad53698ab4beb18d4` |
| Preflight | `b790fb1674bb42c5e1c76ae92b5048c3073da2c3f443eb411fcb52c2bc74d31a` |
| Candidate | `3f38619851da464d3d349c6b6c9bd963ce958d044702b6c839f2fb4589312bbf` |

## Separate corrected qualification

Production commit `6b0f444351748360dc4dddb827124a223ecd3df1` adds row/body
semantics tags derived from existing accepted message IDs. It changes neither
contents nor lazy keys. Corrected instrumentation scrolls to the exact body tag,
requires exactly one body, compares its actual Text semantics to the accepted
message, and retains the same `isDisplayed()` check. It neither clears the draft
nor selects a first/last text match or weakens visibility. Diagnostics use fixed
LOOKUP/MISSING/DUPLICATE/SCROLL/TEXT/VISIBILITY categories without narration or
framework causes. Source review found no remaining selector or authority blocker.

The corrected receipt build at `8db49a32f3701c99951185df61e93389f26a77de`
passed 423 JVM tests/40 suites; regular passed 377/36, zero failures/errors/skips
and lint zero errors/19 and nine warnings. Six artifact audit/signature records
passed with known cleanup. Corrected APP/TEST DEX also contains the new body tags
and all fixed diagnostic categories. No SDK-worker, dependency or budget changed.

Corrected execution source `b1e4437d3e6aaa2a97ec9c579fe83e1d5f88cd43` matches all
1,546 current/snapshot rows, 18,951,108 bytes, and all 213 compiled Android rows.
Its full host run passed 758 tests/77.453s, known cleanup 78,750ms; 89,623 bytes,
SHA `a41cd488ba3a79dcfbd7067d81480313615eebd07d97a9d98fba721f2fb080ab`.

| Corrected artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Receipt app | 75,003,984 | `501d3ddf86430f6c0ddd19f0e88a94e189656fa5c243d3a0657458e4dd4520df` |
| Receipt test | 2,025,483 | `7075dc1104f95e0e58e64d9e01c9bfa7007e4b4ffc4d942cd52246ccf99cbfd6` |
| Regular app | 74,954,584 | `7a457be8af1fa7562c68ad00504a228f7e0eee925ec48e30ef7b537e32acd281` |

Fresh `LocalLore-receipt-compose-identity-*` namespaces were separately admitted
with the same 905 content/four SDK-image metadata review limit and unchanged
profile, floors and budgets. Preflight2 passed 44 clients/one exact method/12 true
checks, 197ms, SDK false; raw proof SHA
`7aff7d2edd86c8042a3a8aca713bbc1cf0ad376534dd685239cca2bce7b61934`.
Candidate2 proposal
`0442cba7544b8c97a75dfe88d559ee58c61976f06585b9d013fe4cc9ebc223ad`
binds 105 matching current/archive files, 87,141,432 bytes, the actual fresh
preflight chain and standing consent. Its live identities and remaining lifetime
passed before root admission; no weight bytes were read by the reviewer.

### Corrected actual result

Strict independent replay verified 44 preflight clients and 77 candidate clients,
their retained stdout hashes/status/cleanup, five exact selected JUnit passes and
all **95 checks**. Progressive manifests, trace hashes/history, process links,
package/UID maps and receipt continuity agree. APP was absent at each post-phase
sample; the permitted TEST helper stayed identical. This is sampled identity
evidence, not continuous liveness or immunity to unobserved PID reuse.

| Corrected phase | Checks | Whole-method observation, ms |
| --- | ---: | ---: |
| Source preflight | 12 | 197 |
| Import | 16 | 96,632 |
| UI Cancel | 26 | 76,535 |
| UI recovery/gift | 24 | 66,054 |
| UI reopen | 17 | 18,283 |

Import verified and imported each full 2,588,147,712-byte stream exactly once.
UI Cancel earned the production New story/Send/Cancel and settled visible-state
checks, with canonical revision0/no receipt/player potion preserved. Its trace
has actual public cancel entry/return, known drain/conversation/engine close and
no UNCERTAIN observation, with the same returned DIRECTOR history.
UI recovery in a fresh process shows the accepted player/narrator bodies through
their exact message identities, commits one guarded gift, and passes independent
canonical/profile/model checks: revision1/one receipt, repairs0/fallbackfalse.
Another process visibly reopens the same receipt without reopening the staged
source or invoking SDK work. Its closed `no_worker_events` check passed.

The proof hashes independently agree:

| Corrected raw proof | SHA-256 |
| --- | --- |
| Import | `dea205e4208b5899ed62d9de47ae44f1c173ed593707e7a5b22630041da87d7e` |
| UI Cancel | `ed91a0c7e93d44925fbbf4325242e87f4d8fd9b9b508825d2597bac14d243a15` |
| UI recovery | `177992002498213959598cbb31a11898d62f277a8d9efec208bd8e352db04c12` |
| UI reopen | `70c5938d0315d113a445d8edc450f50b371dd729e234e3ad0818038b82db2fbb` |

Recovery/reopen receipt SHA is
`869cca72512c85edd49dda53c27ce6d813b5fa4c38fa96eddf45e1c02a849145`.
No failure worker record was emitted in this passing control. Whole-method
observations include admission, model reads, UI operations and teardown; they
are not cancellation latency, isolated generation or a causal speedup measure.

Original candidate `99962` was consumed at terminal0, chunk `340332`; owned
completion was0/known cleanup/capture, 409,640ms, stdout422/stderr0 bytes. Exact
stop followed that terminal. Original owner `89350` was consumed at terminal0,
chunk `46c0ae`; retained stop_requested result is 860,718ms, cleanup/capture/
closure true, worker1 requested drain, stdout15,845/stderr1,086 bytes. Post-stop
host queries record the three tracked identities absent and ports free. No guest
flush or power-loss durability is claimed.

Every entry of corrected H/E/P/C `sealed-inventory-v1.json` was independently
rehashed: **2,207 files / 349,178,336 bytes**, zero mismatches, no model/VM images.
Together with the initial sealed attempt, 4,346 listed files / 701,543,674 bytes
were checked. Initial namespaces remain unchanged and separate.

| Corrected namespace | Inventory SHA-256 |
| --- | --- |
| Host | `e54ed0869742e8210dd0f575c317a16b756c1a67077c85fca94a2d985a9429bc` |
| Environment | `bebf39eefdfae3233323243e0e718be6f0be8fc6010f044baeeb3e1044a6d9ea` |
| Preflight | `88942af8dc10cb401449ff7d77b422347d16a237093b2ff35f778e52bdae5135` |
| Candidate | `d18141be11aff320d348513ae9cb8ec78d458cd652b7b15b7fc0c4b6d32318a6` |

### Disposition and limits

No remaining concrete blocker was found for this selected, separately admitted
Compose semantic-control path. The corrected pass does not diagnose the earlier
discarded visibility failure or erase its partial result. It is not a physical
touch/IME, DocumentsUI or phone qualification. Fresh-process reopen is not an
emulator power cycle. Hidden native reclamation, future callbacks, ARM64/16KiB
runtime, backgrounding, pressure/thermal/sustained performance, privacy/cache
growth and broader scene/quality criteria remain open. The runtime/model,
dependencies, ownership quarantine and all budgets/floors remain unchanged.
Full milestone checkboxes stay pending complete criteria and owner acceptance;
this report authorizes no merge or further device/model operation.
