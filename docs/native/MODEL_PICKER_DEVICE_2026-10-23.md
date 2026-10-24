# Synthetic model-picker device verification

Refs #9 (M05.05; supporting M05.04). The corrected real-picker method and the
separate actual-process restart/readback method both passed on B (API 35,
x86_64, 4 KiB pages). This verifies the selected synthetic slice using an original
63-byte fixture, without model weights, an inference engine, a native workspace
or a story turn. Earlier failures and the pre-dispatch correction are preserved
below. Milestone acceptance remains incomplete and unchecked.

The packet starts from `ec16bc1` and does not reuse authorization from the earlier
provisioning cohorts.
The earlier failures and final native-publication success remain recorded in
[the provisioning report](MODEL_PROVISIONING_DEVICE_2026-10-23.md).

## Scope and admission

The slice uses a separate disposable application/test pair on the
previously selected B emulator, with a test-only document provider in its exact
named child process. It selects two instrumentation methods separately:

1. `pickerCancelFailuresBlockedReadAndVerifiedRestartPreparation` exercises the
   real document picker with tiny synthetic inputs, cancellation and provider
   failure paths, then records a verified copy and process-start proof.
2. `verifiedCopyReopensAfterActualProcessRestart` reopens and fully rehashes that
   copy in a different application process. The same-process case must fail.

The final separately admitted executions below establish these selected checks.
They do not import model weights or construct an inference engine, native
workspace or story turn. The exact final fixture source is the authority for
which scenarios each PASS establishes.

Phase 1 has no process-cleanup path. A separate phase 2 proposal was only
prepared from an actual passing phase 1 result, its closed-scenario/zero-active-
descriptor assertions, and freshly observed signed package/process ownership.
Phase 2 allowed at most one stop per exact new application/test package in
each admitted cleanup round. A new PID, UID, package-map change or unrelated
LocalLore process stops the cohort. No wildcard process action is permitted.

The complete existing 31-package APK map, including the earlier provisioning
pair, is protected. The initial phase 1 added only the new pair (31 to 33); its corrected run later
updated only that pair (33 to 33). The unchanged
userdata floor is 1,207,959,552 bytes; host storage, API 35, x86_64 and 4 KiB page
checks remain required. Installation requested userdata retention; no bytewise
private-data audit is implied. No A, original application, save, cache, real
model, network or account action was admitted in this packet.

## Preparation evidence

The initial controller proposal was disabled. Its source/artifact bindings were
prepared against the coordinator's audited build and repack records.
Before the phase 1 admission, this subclaim performed no build, device query,
installation, instrumentation, lifecycle, model or cache operation. Phase 2 was initially unadmitted.

The final bound instrumentation source is 23,552 bytes, SHA-256
`bedf09e3bd9e0cc02b77a39e1cf654074cadf8a3e8ac97054deee36bee5ce9e9`;
the provider source hash is
`1e0ddbf95f1d44e5aeaaa3a87cdb1e39dcba025df2ad5cce38a598568bf5ae7d`.
The selected application APK is 73,829,600 bytes, SHA-256
`3a053211407f386f220e2ffd0ebd4adcfafa4e7e791b130fad0731df7338e56f`;
the test APK is 1,775,837 bytes, SHA-256
`0aa9ee2f2b6e755ddd6e14b5e562114214744ac9d220ededb12f81cb160e1c7b`.
The initially disabled phase 1 proposal bound 120 source/helper/audit/build/repack, prior-map
and artifact records, SHA-256
`d40d1beb1d6c3ac7c97804d57ca5ff3b94a15fcc0207c6bbfa905cc40f6e9858`.
Those proposal flags were disabled at review; the later, separately recorded
phase 1 admission is described below.

Thirty-six pure controller tests passed after final source binding, with zero
failures, errors or skips, using
`python -B -m unittest -v test_picker_controls_v1`.
They cover exact selected-method parsing; failed and malformed instrumentation;
separate application/test UIDs; exact main/provider process names; map drift;
PID/UID changes; preexisting target refusal; stopped flows; exact conditional
cleanup; and separate restart/readback sequencing. All device interfaces were
mocked. The budget regression calls the actual inherited process runner with an
already-cancelled event and verifies that no child is spawned: 180 seconds is
accepted and 210 seconds is rejected. A separate fixture verifies CLI nonzero
exit propagation.

The owned wrapper has a 180-second outer budget. Observation timeout does not
restart a cohort: any future execution must retain its original handle through
authoritative terminal and known client drain. A failure stops dependent
operations and preserves its raw evidence. No cleanup or retry follows from a
failed phase without a separate admission.

## Stopped phase 1 cohort

Root and reviewer independently verified all 120 proposal bindings without
mismatch. Root promoted only the two authorization flags for one phase 1 run,
SHA-256
`f5f927ab20aeadac2c0c742f73054595012a1b707028b1e516389ce31f13d45f`.
The original owned execution was followed through authoritative terminal without
restart. Its child result was completed with return code 2, known cleanup,
32,406 ms elapsed and zero outer stderr bytes; the outer shell terminal reported
exit 1. Root accepted the original terminal report together with independently
read hashed receipts. No second execution occurred.

The single selected first method reported paired **0 PASS / 1 FAIL** at this
combined assertion:

> Every actual picker launch must request local-only OPEN_DOCUMENT with openable wildcard type

The bound source checks both `launches.size == 6` and all recorded intent
properties at that location. The raw failure does not identify which clause
failed. The assertion follows the valid-copy, private reopen and provider-drain
checks in the source, but the failed cohort provides no independent per-scenario
PASS credit. The private PID/start proof write follows this assertion and was
not reached. No actual-process restart or second method ran. The coordinator's source diagnosis found that the pinned AndroidX OpenDocument
contract omits `CATEGORY_OPENABLE`, while the application override added only
`EXTRA_LOCAL_ONLY`. That establishes a missing category in the old launch intent;
the number of observed launches remains unobserved. The coordinator owns the
explicit-category fix and improved immediate fixture diagnostics. A corrected
cohort has not been executed.

All 22 device clients completed with return code zero and known cleanup. The
instrumentation client itself returned zero while its test failed; the parser
retained the failure and stopped dependent actions. There were no process stops,
post-PASS metadata queries or automatic retries. Successful installation stderr
counts were 150 and 160 bytes with unavailable contents; other clients had zero
stderr bytes. No cause is assigned to unavailable stderr.

Before installation, the complete 31-package map and absence of LocalLore
processes passed. The installed gate observed the exact new 33-package map with
all original 31 hashes preserved and no LocalLore process at that moment.
Userdata available was 1,464,954,880 bytes before installation and 1,389,129,728
bytes at the installed gate, both above the unchanged floor. Host/API/ABI/page
gates passed. These are boundary observations: the post-failure process/map,
provider state and storage were not queried and remain unknown. Known client
cleanup does not establish natural application/provider exit or descriptor
ownership after the test.

The raw instrumentation is 3,495 bytes, SHA-256
`db4146b89e657147cdcb329910b64688da7dba6f76ee53a1a414c20514241881`.
A failure-specific local closure, never the success helper, rehashed and copied
all 120 bound inputs before source changes and checked all 22 raw client records.
The read-only stopped selection contains 247 files / 77,939,634 bytes; its index
SHA-256 is
`8706679edaaf360df31635c1d8d8f6bb9da2be0d6bf0ae6b459f3dcc595d21e4`.
The lease was released after authoritative terminal and local closure. No further
device call was made or authorized by that closure.

## Gate after the initial failure

The original phase 1 failed; its all-PASS gate remains failed and did not
authorize phase 2.
At that point no picker/restart acceptance, inference, SDK ownership or natural
cleanup was claimed. The next step was independent review of a new disabled
recovery proposal, preserving existing data and failed evidence. Corrected tests
and exact disposable-namespace cleanup required fresh admissions; the original
authorization did not carry forward. Storage floors remained boundary
observations, not reservations against concurrent OS use.

## Initially disabled recovery preparation

The original failure, 247-file stopped selection and its all-PASS gate remain
unchanged. A new private recovery namespace bound the old installed 33-map,
installed UID pair, sealed original inputs and recovery helpers. The proposal
was initially disabled, SHA-256
`e7a3bbbab8a78f4e3008e5cb64ffe03df7ff325bd2e904efd51a2889cb3eb964`,
with 260 bindings / 78,036,016 bytes. Eighteen original pure tests passed, zero
failures/errors/skips, using `python -B -m unittest -v test_recovery_v1`.

The proposed recovery first checks exact signed package hashes, the installed
UID pair, allowed fresh process rows, device identity and storage floors. It may
conditionally stop only the new disposable test/application packages, rechecking
map/UID/PID proof before each action and accepting only natural disappearance.
New or changed processes abort. After independently observed absence and floors,
another immediate map/UID/absence proof precedes one clear of only the new
application's synthetic data. The same 33-map, UID pair, absence and floors must
then pass again. It cannot clear the test package, stop or clear any original 31
installation, install an APK, instrument a method or continue to phase 2.

At that preparation point no recovery device operation had been authorized or
executed. A corrected first-method update/run required actual passing recovery
evidence, newly audited signed artifacts and its own admission. Those pure tests
did not establish Android clear behavior or device process ownership.

## Stopped recovery cohort

Root and reviewer independently checked all 260 recovery bindings without
mismatch. Root then promoted only the authorization flags for one recovery run,
SHA-256
`79e41481bca58b1e0b846bedd3af180198cc2e77be6ca8a47bd7e475462b4c2e`.
The original call reached synchronous authoritative terminal with no live handle:
owned child completed return code 2, known cleanup, 3,547 ms and zero outer
stderr; shell exit was 1. Root independently accepted the retained terminal
receipts. No restart was attempted.

All seven clients were read-only, completed with return code zero, known cleanup
and zero stderr. Device identity, the exact original 33-package map and the
separate installed UID pair matched. The process query then found the new test
host/provider and nine other previously installed chooser-test provider
processes. The strict foreign-process gate stopped before storage queries or
any mutation. There were **zero stops and zero clears**, no installation or
instrumentation, and no recovery success or natural process cleanup credit.

The coordinator identified the existing DocumentsUI provider enumeration as a
reason to investigate passive providers separately. Local manifest inspection
matched all nine exact process names to retained TEST APKs with the installed
hashes and declared protected document-provider entries. These observations do
not grant ownership or authority to stop those providers. The original recovery
gate remains failed; it was not resumed or weakened in place.

A failure-specific local closure rehashed and preserved all 260 bound inputs
and seven raw records before any change. The read-only stopped recovery
selection contains 297 files / 78,291,445 bytes, index SHA-256
`918d8e0f2d1d6aa876b2a6455bea5b19b5198848b70b094b09f99022fc84da5f`.
Its lease was released after terminal and closure. No device call followed
under that stopped admission.

## Initially disabled read-only settlement

A separate initially disabled proposal permitted exactly nine metadata queries: device
identity, complete 33-package hashes, full installed UID map, process snapshot
and userdata identity/free-space checks. Its SHA-256 is
`e7530be29afe91293081661e09ca39f092d74fdce3b11e56ccdb0708b793235e`,
with 61 bindings / 21,264,194 bytes. It hash-links both stopped selections and
binds the necessary raw records, exact nine retained TEST APKs and local
manifest audit. Sixteen original pure tests passed, zero failures/errors/skips,
using `python -B -m unittest -v test_settlement_v1`, including actual budget and
CLI regressions.

Only the exact nine passive provider names are recognized against their signed
package hashes and full fresh installed UID map. Passive PID appearance or
disappearance is observation only. An original application's main process or
any other colon process aborts; current owned rows remain restricted to the new
pair's three exact process names and separate installed UIDs. This proposal
cannot stop, clear, install, instrument, read model files or continue to a
recovery or test. At review both flags were disabled. The separately admitted settlement result
follows; no recovery or test was implied by the preparation.

## Completed read-only settlement

Root and reviewer rehashed all 61 bindings without mismatch, then root admitted
one nine-query run, authorization SHA-256
`daf63c76422d864bec73be4bfb91dc9829097897b3cf6b9b0db4a67f46d7578d`.
The original synchronous call completed return code zero with known cleanup,
2,984 ms and zero stderr. All nine clients completed with return code zero,
known cleanup and zero stderr. The complete 33-package map and full installed
UID map matched, with two owned rows and all nine exact passive providers. No
owned application main process or unrecognized LocalLore process was observed.
Userdata available was 1,389,101,056 bytes; identity and host floors passed.
No lifecycle, installation, instrumentation or model action occurred.

The local closure rehashed all 61 bindings and nine raw records. Its read-only
selection contains 63 files / 211,678 bytes, index SHA-256
`826df61adaa74ac43f5aa3296a82e1f769ccddeeef47b7296e564178f094eb5d`.
The lease was released after authoritative terminal and local closure. Passive
identity classification grants no ownership or stop authority over those prior
providers.

## Revised recovery and pre-dispatch correction

The revised recovery retained the same mutation scope but classified only the
nine exact passive providers separately against signed package hashes and the
full installed UID map. Unknown original main or other colon names still abort.
Owned rows are freshly captured and rechecked as subsets before each action;
new owned PID/UID rows abort after capture. Passive PID appearance/disappearance
is observation only. Own namespace absence excludes only those exact passives.

The first revised proposal was independently reviewed (105 bindings, 21 pure
tests), but **never dispatched**. Before creating a lease or start receipt,
local inspection found retained shell responses use consistent CRLF while the
clear response oracle required raw LF. Root explicitly revoked the unused GO;
its supersession receipt SHA-256 is
`1a9c201f6a389dbfa31c338042ef37315d0dac2422d7338326abf304b5768d66`.
No recovery device action occurred under that revoked admission.

A new immutable recovery version applied the existing strict newline parser,
then required exactly `Success\n`. It accepts LF or consistent CRLF and rejects
mixed/lone CR, control bytes, failure, extra or oversized output. The mutation
scope did not change. Twenty-three pure tests passed, zero failures/errors/skips.
Root and reviewer independently rehashed its 109 bindings without mismatch;
proposal SHA-256
`91c090061f76e7ad2a44543983123b583afcc97cd2731653e3db284910be7a07`.
Root separately admitted that version, authorization SHA-256
`2628998fd5058c9b83a54ce259afd06be5e070139f14deaaae812f8148a89fba`.

The original owned run completed return code zero, known cleanup, 18,204 ms and
zero outer stderr. All 41 clients completed with return code zero, known cleanup
and zero stderr. Fresh signed map/full UID/process proof admitted one stop of
only the new test package; the new application process was already absent and
was not stopped. Own namespace absence and storage checks then passed. After
another immediate map/UID/absence proof, the controller cleared only the new
application's disposable synthetic data once. The exact clear-success response
and final gates passed. No original 31 package lifecycle command occurred, and
there was no test-package clear, uninstall, installation or instrumentation.

Final observations retained all 33 APK hashes and installed UIDs, no owned
process row and six recognized passive provider rows. Userdata available was
1,389,264,896 bytes; host and identity floors passed. The controller did not stop
any passive provider; their disappearance does not establish natural cleanup.
An Android clear-success response is not a bytewise audit of unrelated data;
the next first-method fixture must still prove its synthetic root is absent.

The local closure rehashed all 109 bindings and 41 raw records. Its read-only
selection contains 119 files / 301,734 bytes, index SHA-256
`356c9fcc3b42a91deed27a70b23e3576d4583e9d4a4bd5255dca61e6fd237b30`.
The lease was released after authoritative terminal and closure. No inference,
SDK ownership, descriptor cleanup under a real model, or corrected test result
is implied by this limited reset.

## Initially disabled corrected first-method execution

The corrected source adds the explicit openable category and immediate bounded
per-request intent assertions. Final test source is 25,291 bytes, SHA-256
`3a849ed1d86a971c30662f226366d6c976489f39c4cec72f28b46f10dc705067`;
the application activity source hash is
`d2824bc252cc4347469eafd678b571054787bb91baae1a12607906cdc960cd94`.
The audited application APK is 73,829,600 bytes, SHA-256
`31d3131612f75972096ef78d843995bbf5d3f1feb811c9b07ffd4563f8a9ae89`;
the test APK is 1,777,609 bytes, SHA-256
`7aa2495ca37675ac2bf0e72c43f68051b01cc3b0566314d33211c957dd624fe5`.

A separate initially disabled proposal bound the actual reset receipt/closed selection,
final source/artifacts and host evidence. Proposal SHA-256
`d2bc907da08db0f5b28e295996fed6c2fa040cafefc8a5ea737157cc6639695c`,
218 bindings / 77,355,874 bytes. Thirty pure tests passed, zero
failures/errors/skips, using `python -B -m unittest -v test_execution_v1`.
The controller requires own absence before installation and before the selected
first method, updates only its exact pair from 33 to 33 while preserving all
other 31 hashes and all installed UIDs, then captures after-PASS metadata. It
has no stop/clear path and cannot select phase 2. At proposal review both flags
were disabled. The separately admitted first-method result follows; original
failures remain unqualified.

## Corrected first-method result

Root and reviewer independently rehashed all 218 bindings without mismatch.
Root admitted one exact pair update and first method, authorization SHA-256
`e6359896c71cb071df8717d7cb95f92a978405ece1b83183752d71a474930556`.
The original owned handle reached authoritative terminal return code zero with
known cleanup, 29,219 ms and zero outer stderr. All 30 clients completed with
return code zero and known cleanup. Installation stderr counts were 160 and 171
bytes with unavailable contents; all other clients had zero stderr.

The separately selected first method reported **1 PASS / 0 FAIL**. Against real
DocumentsUI and the production picker/resolver/store wiring, this establishes
its assertions for picker Back without stream open, retained recreation behind
the picker, same-length wrong bytes, provider-open failure with safe UI text,
blocked-read cancellation with continued reservation, non-overlap, actual proxy
release/drain, background/recreation/disposal stale-result fencing, eventual
valid tiny native publication, full private reopen/reuse and no persisted URI
grant. Each of the six actual requests was observed with the required local-only,
openable and wildcard-type properties. The method then wrote its private process
proof only after those checks. Its teardown completed all owned scenarios and
asserted zero active descriptors. No inference engine or native workspace was
constructed.

Own namespace absence passed both before installation and before the method.
Before and after maps contained 33 packages: only the exact pair changed to the
corrected hashes, all other 31 hashes and all 33 installed UIDs remained
identical. After-PASS observation found two owned rows and three recognized
passive provider rows, with userdata available 1,387,884,544 bytes. Host/identity
floors passed. There were **zero stops and zero clears** in this cohort. Passive
process disappearance has no natural-cleanup or SDK-ownership credit.

Raw instrumentation: 833 bytes, SHA-256
`a24c44b6fb8278916500ba21d561f04c94570dfe241f87e51ca24147336091b7`.
The local closure rehashed all 218 bindings and 30 raw records. Read-only
selection: 133 files / 918,459 bytes, index SHA-256
`956362a1df54866e53d942c5f3bec110e7fb3983e77eabe984b95a3dcffc1817`.
The lease was released after terminal and closure. This proves the selected
synthetic picker/preparation method; actual-process restart/readback still
requires a separate run.

## Initially disabled restart/readback proposal

The initially disabled separate proposal bound the actual first-method PASS, closed selection,
captured owned process rows, full installed UID map, updated 33-package map and
same audited final source/APKs. SHA-256
`4eafb363d2766a0f273c5a824407d2d98a76de7e4990bf1af1b1ca229cb10718`,
303 bindings / 77,583,352 bytes. Twenty-four original pure tests passed, zero
failures/errors/skips, using `python -B -m unittest -v test_readback_v1`.

Before each exact new test/application package stop, fresh full map/UID/subset
proof must match the captured first-method ownership. Only natural owned
process disappearance is accepted; new owned PID/UID rows abort. Recognized
passive providers remain observation only. Own namespace absence is required
before separately selecting `verifiedCopyReopensAfterActualProcessRestart`.
That method must read the preserved private process proof, reject the original
process identity, and rehash all 63 bytes without a picker launch. Only
its PASS admits a fresh, captured final scoped cleanup and final
map/full-UID/own-absence/storage gates. No clear, reset, installation, model or
original 31 lifecycle action is permitted. At proposal review both flags were
disabled; the separately admitted result follows.

## Actual-process restart/readback result

Root and reviewer independently rehashed all 303 bindings without mismatch.
Root admitted one readback cohort, authorization SHA-256
`be17203cf3d11da809413e61eebc7571db9322797d0fbb1189f1250d806a24bf`.
The original handle reached authoritative terminal return code zero with known
cleanup, 39,047 ms and zero outer stderr. All 72 clients completed with return
code zero, known cleanup and zero stderr. Observation yields were followed by
polling the same original handle; no execution was restarted.

Fresh full map/UID/captured-subset proof admitted one stop of only the new test
package. The application process was already absent and was not stopped. Own
namespace absence passed before the separately selected second method, which
reported **1 PASS / 0 FAIL**. It read the private first-phase process proof,
rejected the original PID/start identity, showed READY without launching a
picker or retaining URI grants, and reopened/fully rehashed the original 63-byte
private fixture (SHA-256
`648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0`).
The external absence gate and new-process proof together establish actual
process restart, rather than Activity recreation alone.

Only after that PASS did fresh captured ownership/map/full-UID proof admit one
final stop of the new test package. Total: two exact new-test stops in separate
rounds, zero application stops, zero clears, zero installations and zero original
31 lifecycle actions. The 63-byte copy and its process receipt were preserved.
Final observations retained the exact updated 33-package hashes and all 33
installed UIDs, no owned process row, and two recognized passive provider rows.
Userdata available was 1,388,707,840 bytes, above the unchanged floor; host and
identity gates passed. Passive disappearance and the explicit test-package stops
provide no natural process-exit or SDK/model ownership qualification.

Raw instrumentation: 800 bytes, SHA-256
`62f27d928a95b3e5607da05adcd58e58bcc590c3a9008c90c7514dd2fe177ba3`.
The local closure rehashed all 303 bindings and 72 raw records. Read-only final
readback selection: 184 files / 508,273 bytes, index SHA-256
`77e755f068bc73e2db17b3ae95e77c28ae4a4b0fbdc301088439eb10aafeee48`.
The lease was released after authoritative terminal and local closure. No further
device action was performed or authorized.

## Status and next runnable task

The scoped M05.05 synthetic SAF picker/cancel/recreation/disposal/verified-restart
slice is locally verified and ready for integration review, with M05.04 supporting
boundary evidence. The original 0-PASS/1-FAIL picker cohort, stopped seven-query
recovery and revoked unused admission retain their original failed/unexecuted
status. Their gates were not relaxed or resumed in place. The fixed two methods
ran separately under new, independently reviewed source-bound admissions.

The next runnable task is a separately admitted **pending-picker/import process
death synthetic recovery** fixture and its host-first tests. Corrected first
method/readback proof does not establish process death during an unfinished
picker or blocked import. Real model import/cache behavior, SDK/model inference
ownership/cancellation, A, ARM64 execution and physical-phone qualification remain
pending their separate evidence and authorizations. M05.04/M05.05 milestone
checkboxes remain unchanged until all acceptance criteria and owner acceptance
are satisfied. No merge, release, access change, model upload or story-data
operation occurred in this packet.
