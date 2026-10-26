# External process-restoration execution, 2026-10-26

Supporting M10.02 and M08.01/M08.05. Source starts at draft/unmerged
[PR #206](https://github.com/OptimumAF/LocalLore/pull/206), `50989ca2`.
The current packet uses the versioned [component driver](ANDROID_PROCESS_HOST_DRIVER.md)
and [external runner](ANDROID_EXTERNAL_CONTROLLER_HOST.md). Full milestone
tasks remain unchecked; no owner acceptance, merge or release is implied.
Revised mapped source is `85ff9a69`: its current native10 gate, root82,
active-child123, retired-leaf139 and corrected retained-parent two-death cases
have now passed. The earlier
failed retained cohort remains separately attributed and preserved below.

## Fresh build and native gate

The offline input-process build actually reran 234 JVM tests in 27 XML suites,
with zero failures/errors/skips, both lint checks and eleven artifact audits.
Its owned worker completed exit0 in 36,702ms, with known cleanup/capture and
no stderr. All756 tracked inputs, including all five SQL files, were identical
before/after. Source-map SHA-256:
`0d16493ccf5b9715561d6e3d6c4e26ec8e18f1d874cd60900c1cabb77580dd89`.

| Fresh artifact | Bytes | SHA-256 |
|---|---:|---|
| Product | 24,555,355 | `ab1030cdbe7cc05833213f0f1064563fcf7893164961f93824927e89a9bc5fc4` |
| Test | 2,752,699 | `997f0ece760ddb5af9497b2d6d529f87292786098d9118b98660eaa2baaa507a` |
| Controller | 53,113 | `90bd8030963748ee6a98e783793e4f0588f9a131c01c05f90f4f6fe7fecb7499` |

These APK bytes equal the earlier packet's artifacts, but the new build,
executed JVM XML, source maps and command records were actually captured anew.
The existing server was observed without starting or replacing it. A fresh
owned API35 Google APIs/x86_64 guest uses the unchanged 2GiB/two-CPU profile
and 4GiB host-memory floor.

The ten native component methods passed: four retired-selection loader/refusal
methods, four retained-parent loader/refusal methods and two actual Rust-native
retained-parent methods. All84 captured clients were clean; the owned worker
completed exit0 in 307,486ms with known cleanup/capture, no stderr and the same
756 source rows. Additional boot-health captures explain the client-count
difference from the earlier 81-client packet; no client-count gold is invented.
Independent read-only review revalidated original rosters, raw-to-client copies,
artifact/source bindings and terminal owners. This ten-method gate explicitly
does not establish external process-death or visible UI recovery behavior.

## Preservation

The completed build/component/server gate has a private recovery copy:
258 files/27,903,386 original bytes. Independent review verified every original
and ZIP entry, with no missing, changed, duplicate, extra or unsafe entries.
ZIP: 17,823,810 bytes, SHA-256
`25412f5ef829fd7b3d46e7d6e8a516e4ade801123280de06592747f56e7712bc`.
Both identical 76,685-byte index copies have SHA-256
`8c268cc74ccc78a2b4e5d38980954f56f233b47c730c945907fdc5f055ed446d`.
No live-case files, guest images/databases, models, caches or unrelated-project
data were selected. Raw diagnostics remain private.

The first environment-planning invocation incorrectly used isolated Python
mode, which this preexisting CLI does not support. It failed during imports,
before entering the environment API or creating a proposal/guest. The
documented `-B` invocation succeeded. This is a retained tool-output observation,
not reconstructed original pipe bytes or a device-case failure; no source,
budget or admission rule was changed.

## Root saved-task control

The actual `restore_non_default` case passed **82 controller checks and two
same-task process deaths**, with three distinct product process identities and
factory1 in each restored process. It selected B, restored the original unsent
draft/kind after the first death, and committed only on explicit Send. The
first old terminal gameplay vector is all zero; the second is
free_text1/submit0/prepare1/commit1/cancel0/other0. The second restoration kept
the accepted outcome without automatic gameplay or story creation.

The runner continued only the exact completed component installation; its
controller fixture was newly created. All69 captured clients were clean.
The host worker completed exit0 in 318,902ms, with known cleanup/capture and
stderr0. Independent readback verified the original controller frame,
fixture/claim, saved and command records, scope/hint/factory links, all client
copies, and the final PID/UID/product with both old PIDs absent. All756 source
rows remained identical. Original controller frame: 1,650 bytes, SHA-256
`2c2846f78d787ecc8edeb5ed4253faef0dff1527c8fb1ef70fc1b2ac17602758`.

The root guest then closed through its proposal-bound stop record only after
the clients were terminal. Its outer invocation exited0; owner status
stop_requested, elapsed843,537ms, cleanup/capture/closure all true, worker1 at
the requested stop. The emulator had 1,077 stderr bytes; these private emulator
logs are distinct from the test workers' stderr0. No guest flush, graceful app
shutdown, power-loss or forensic-erasure claim follows from job closure.

## Retained setup failure and explicit recovery correction

The first actual retained-parent case at `50989ca2` failed at
`FORK_SETUP/SCOPE`, 69 checks and zero deaths. All126 captured clients were
clean, but the controller correctly finished failed. Its owned host worker
completed exit2 in 540,274ms with known cleanup/capture and stderr0. Four of the
fourteen fixed diagnostic leaves existed: created, commands, load helper and
load transport. Ten contain the exact27-byte missing marker: saved, fixture,
probe/retire bodies and transports, and all four preserved sidecars. Load
committed zero; the retirement/death path was not reached. No success proof or
external artifact was produced, and this cohort was never retried or adopted.

After those clients were terminal, a guarded read-only UI dump used20 clean
clients. Its original7,957 bytes and standard dump footer independently confirm
lookup-only recovery, one current selection and a different requested parent.
The first confirmed fork's original recovery identity remained, as required by
the [existing explicit-recovery contract](M08_ANDROID_FORK_APP_2026-10-23.md).
The test journey had omitted separately consented Forget before requesting a
second child. The failed guest then closed by its bound stop: owner903,795ms,
worker1, cleanup/capture/closure true, guest flush false; emulator stderr1,081
bytes remains distinct from the test worker's stderr0.

`5537afbb` adds a retained-case-only UI step after the first confirmed fork and
explicit resume. It verifies the exact prior root/child identity and lookup-only
state, selects the separate Forget consent, requires recovery controls gone,
closes the panel and verifies P1/accepted ROOT and gameplay/create counters
unchanged. The original second-fork scope check, native nine-row oracle,
gameplay vectors, caps and deadlines remain. Production recovery behavior is
unchanged. [Protocol correction](ANDROID_RETAINED_PARENT_PROTOCOL.md).

`87be4110` integrates the independent fixed broad89-method/18-class regression
phase, keeping the original component10 gate separate. `85ff9a69` adds one
real-ShellViewModel JVM journey: known-outcome resume retains the original
hint; second open cannot reroll or confirm it; false consent/failed clear keep
it; successful explicit Forget permits only a later explicitly confirmed fork
from the current child. Exactly two register/run pairs occur, with no automatic
turn/create/second resume. Fake saved-snapshot/draft metadata assertions are
not Compose-editor or native-world proofs.

## Revised-source host/build qualification

At `85ff9a69`, all **1,242 Python tests passed in 114.306s**, zero
failures/errors/skips. The owned worker completed exit0 in116,159ms, cleanup
known and stderr0. Original stdout225,756 bytes has SHA-256
`666408644965852506928aadf16cf1f963b4e622e07df76bb6b7adee0926d938`.
These supersede the earlier full-host count for revised-source attribution;
overlapping tests/runs must not be added as unique coverage.

The fresh revised build actually reran **235 JVM tests/27 XML suites**, including
the exact new sequential-fork method once in `BranchForkShellTest`14, with zero
failures/errors/skips. Both lints and eleven audits passed. Owner188,201ms,
worker0, cleanup/capture known, stderr0. All756 inputs, including five SQL
migrations, match before/after; source-map SHA-256:
`9cf2b017f32b6e3eb70caee7b85b908a73ba6ff770833fe3b55f11fb040b89b2`.
Independent review verified the original XML method, APK/audit bindings and
terminal records. Product/test artifacts retain the earlier table's exact
bytes/hashes; the revised controller is54,201 bytes, SHA-256
`805187cb0f28a48bfd304fdd507f5b8c8ef8bddd2fffa901ef6a9e69eae5cd96`.

The original failure/UI/closed-lease records have an independently verified
private341-file recovery copy:578,130 original bytes; ZIP234,550 bytes,
SHA-256 `3cb9c245183a077c51d990b88b434e7048d1bc0ca84b7edbe321200b12940fda`.
Both100,651-byte indexes match SHA-256
`efe6bd7c6cfcdf317fd606c8db05c7a2b90448c9f7d798da05b4b1e4399f7d27`.
The manifest retains source-at-execution50989ca2 and passedfalse. Complete-history
bundle through85ff9a69:9,840,403 bytes, SHA-256
`346ddd8d16d3e35bd90026706f0acdadcf0c44ae57a8796f4c76adb9578a0394`.
No images, databases, weights or caches were selected, and no original failure
was overwritten by its correction.

## Corrected-source runtime qualification

The revised native component gate passed all10 methods,81 clean captured
clients, owner299,578ms/worker0/known cleanup+capture/stderr0. The revised root
control passed82 checks/two deaths,69 clean clients, owner342,229ms with the
same terminal guarantees. Its closed owned guest records stop_requested,
881,397ms/worker1, cleanup/capture/closure true, guest flush false, emulator
stderr1,079 bytes. These current-source records replace no earlier raw run.

The corrected `restore_retained_parent` case passed **two genuine saved-task
deaths**, three product instances/one task/factory1,202 diagnostic checks and
126 clean clients. The count202 is the observed diagnostic, not a frozen gold.
Its host owner completed exit0 in645,228ms with known cleanup/capture/stderr0.
The fixture was newly created on a separate fresh installation; no partial
fixture or prior run was adopted. All756 source rows still match9cf2b017... .

The first terminal gameplay vectors are exactly free_text3/submit0/prepare3/
commit3/cancel0/other4: three explicit Sends and two register/run fork pairs.
Both second-old vectors are zero. The real UI verifies fallback to A0 with the
exact one-shot unavailable notice and blank Action editor, explicit reread
consuming the notice, then a second death without notice/draft/hint resurrection
or automatic gameplay. Root1/G2 remain selectable; retired P stays unavailable.

All three original native helper bodies/transports validate: load619B,
probe1,049B, retire1,056B, exact singleLF/closed native owners/0,0,1 commit
attempts and both original zero exit footers. Probe leaves state unchanged.
Retirement changes P from public3/physical3 to public-unavailable/physical2,
keeping A0/root1/G2 active. The source-bound helper executed its exact nine-row
preview assertions; its raw proof exposes states, not an independent raw
nine-row preview transcript.

The four original Java-compatible canonical sidecars are byte-identical:
12,174 bytes each,48,696 total; SHA-256
`1ceca2dfdc641ce7c5a6a0f362e82c0e05c5d488eedc3dfc6e3204f71343a73e`.
Their complete six-key eligible player/receipt views retain A0/root1/G2,
receipt counts0/1/2, original ROOT(root,expected revision0) and PREFIX(P,expected
revision1) scopes/text, with no exact TAIL anywhere in the nested views.
This is eligible player/receipt preservation, not hidden-world equality.
Independent controller/producer/client audit and a separate native/helper/
sidecar comparison found no mismatch. Controller raw SHA-256:
`4a70bb6ddb53d46f14261d69e5ee12a08859e290378284a98f9b61767bfb0cad`.

The successful retained guest then closed via its proposal-bound stop:
1,061,245ms/worker1, cleanup/capture/closure true, guest flush false, emulator
stderr1,081 bytes. Native helper closes are synchronous; these results do not
turn the app's asynchronous adapter close requests into joined drains.

A private corrected-runtime snapshot contains479 selected terminal files/
1,405,956 original bytes, including both current cases and closed-lease metadata.
Its verified498,838-byte ZIP SHA-256 is
`d180aa1911abe881121139dda0c848cce657bdac47981a9d9be4377f42dc9430`.
Independent review verified all479 originals and ZIP entries without mismatch;
both138,886-byte indexes match SHA-256
`ec706a02f58cf0e011eb187c6a0b30877af3aae39ca7c8dd923b6e7e79947618`.
The complete-history bundle through0f69fa0f is9,847,687 bytes, SHA-256
`88e4a9d84fe241bd4d91250fe3e7621cc216d231f0b43af47225c9ce1fb15b15`.
Current build/component/host/server prerequisites have a separate259-file/
28,326,608-byte recovery copy; ZIP17,929,611 bytes, SHA-256
`f0c90976c8040f7d724cf09c029d312b8f90f95ee43d578accf0ca3e7aac4178`.
Independent review verified all259 originals and copies; both74,985-byte indexes
match SHA-256
`c4d397ed48c4672cb9f3efcc2e10743fa9f675e587849daacfeda3990a80b5db`.
No active-cohort files, images, databases, models or caches were selected.

The current-source active-child control also passed123 checks/two deaths,
96 clean clients and independent original-record readback. Host owner458,469ms,
worker0, cleanup/capture known, stderr0. Its create-only fixture retains the
historical A0/B0 roots and B1/child1 setup; explicit child Send reaches child2
without changing B1. Both old terminal saved/command vectors are exact: first
free_text1/submit0/prepare1/commit1/cancel0/other2, then the same single explicit
Send with other0. Final child restoration does no automatic gameplay/create.
All756 inputs remain9cf2b017... . The owned guest closed after clients were
terminal: stop_requested1,058,118ms/worker1, cleanup/capture/closure true,
guest flush false, emulator stderr1,079 bytes.

The terminal active-child case and closed-guest metadata now have a separate
private recovery copy:233 files/657,204 original bytes. Independent readback
verified every original and all233 ZIP entries, with no extra, duplicate,
unsafe or mismatched entries. ZIP240,284 bytes, SHA-256
`d6ecfcb4ef80723389bf008f61bfe85fda337957485e09d2c9230ec670299b11`.
Both67,487-byte indexes match SHA-256
`dbf162594e7df0a39bf10a1e0dfb2316150ade400153fe912e5416356d44d2b5`.
No live leaf/regression cohort, guest image, database, model or cache was selected.

## Retired-leaf control and remaining gates

The current-source retired-leaf case passed139 checks/two deaths,114 clean
clients, owner601,344ms/worker0 with known cleanup/capture and stderr0.
Its exact original helpers and merged zero-exit footers validate: load611B,
probe741B, retire748B; commit attempts0/0/1, native owners closed. The retired
target becomes inactive/public-unavailable while A0 and parent1 remain.
Both old saved/command vectors match: setup free_text1/prepare1/commit1/other2,
then all zero after fallback. Real UI recovery clears the invalid draft,
shows the one-shot unavailable notice and does no automatic gameplay/create.
Independent original controller/producer/fixture/client/postflight readback
passes; all756 inputs still match9cf2b017... . Original controller3,816B SHA-256:
`a22021c8deff3d733aa350e5f9bfbc096a607577d389a822dce3a8e7d33a5681`.

The owned leaf guest then closed through its bound stop:709,243ms/worker1,
cleanup/capture/closure true, guest flush false, emulator stderr1,077B.
Its independent recovery seal verifies275 originals/ZIP entries,676,986B,
without mismatch or unsafe entries. ZIP256,390B SHA-256
`11bc49fe2d181cf8f6d5a3b484f1e87a70136c340e64a0edd3450ab278c13eb9`;
both78,464B indexes match SHA-256
`e51e427b509f167c8996df13dce33e04daa348acb840deb43211de0355189c17`.
No live regression cohort, images, databases, models or caches were selected.

The first separate89-method broad run completed all18 classes and its worker
exit0 in714,974ms, known cleanup/capture/stderr0,174 clean clients and unchanged
756-input map. Its aggregate is nevertheless **failed/validation_refused**.
Direct original-record diagnosis identifies `regression_client_copy`: the host
validator's `instrument-` prefix also classified the legitimate repeated
`instrument-user` checks as class-result copies. Each actual `instrument-0`
through `instrument-17` original copy matches its class raw output, but the
aggregate refusal is retained and must not be promoted to passed.
The used guest closed via bound stop:772,194ms/worker1, cleanup/capture/closure
true, flush false, emulator stderr1,083B. A correction must preserve all client
integrity checks, distinguish the exact ordinary user-check label, and add a
realistic interleaved-client regression. Fresh host/build qualification and a
fresh guest run are planned after that fix; no used fixture is adopted.
The original refused case/closed guest has a separately verified399-file/
761,956B recovery copy, explicitly retaining passedfalse/validation_refusedtrue.
ZIP286,705B SHA-256
`4b9f2799bf0a51fbd619a30f0a850e964988afba67c4739e2c1870209e9c9cbf`;
both115,608B indexes match SHA-256
`d4a66b020039a4b927c8b4e7da7c65cf97e02ea1b725a72c571fcce2613e5278`.

`31c0f700` integrates only the host validator's exact `instrument-user`
exception and realistic interleaved-client regressions. Ordinary user-check
rows still require strict shape, clean exit, original bytes and hashes;
unknown/duplicate/extra numeric class labels still refuse. The new positive
test actually failed on the original validator, then all34 targeted host tests
passed after correction. App/controller/native sources are unchanged. New
mapped qualification is separate from the85ff9a69 Android executions above;
an equal APK hash would establish artifact equality, not equal source maps.
Fresh full-host/build checks are running before a new create-only89-method run.

## Host correction qualification

At mapped code31c0f700, all1,245 Python tests passed in126.401s, zero
failures/errors/skips. Host owner128,018ms/completed0/cleanuptrue/stderr0;
stdout226,427B SHA-256
`c8614b3192c9b2de7c916404732852c9f10cc64d42920f22fa07255223e8f673`.
The fresh build passed235 executed JVM tests/27 XML suites, both lints and
eleven audits, owner57,461ms/worker0/known cleanup+capture/stderr0.
All756 tracked inputs/five SQL files match before/after, new source-map SHA-256
`be527ea35b56a5c8e16d273a5b1abeaa9e7bd93e4d6e2b55deb9a7cd94826340`.
Independent original build/XML/audit validation also streamed all three APKs
byte-for-byte against build-v2: product/test/controller are identical to the
85ff9a69 artifacts. The native10 and four external cases above retain their
85ff9a69 execution attribution; they are not relabeled as new-map runs.
The new89-method suite is running in a separate fresh guest against build-v3.

Independent host/build recovery verification covers85 original files/ZIP
entries,28,088,511B, with no mismatch/extra/duplicate/unsafe entry. ZIP17,807,874B
SHA-256 `78b9dbec1fdceca06c8f0ed9a099e2f3f0da4c984fda7d8b756f8bab3381ea86`;
both24,877B indexes match SHA-256
`d878b6a9cf96de77459c7fd21d25ecf8d6dd38b3b3c55b874afa4374985c29ec`.
Only terminal build-v3/full-host-v3/server-v1 files were selected; no live
cohort, image, database, model or cache was selected. A verified complete-history
Git bundle through05ebbe31 is9,851,812B, SHA-256
`18a094b1910396047eb9c502608629bd32672d2428dc70224685a89ecd9bd151`.
Earlier50989ca2 results remain historical source-attributed records; the current
source has separate fresh runtime qualification above. Phone/ARM64 and real-model qualification are
separate gates; no result follows from fake-provider or emulator checks.
