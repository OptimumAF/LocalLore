# Model picker independent review

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 synthetic
picker/provider/restart prerequisite and M05.04 supporting. Review subclaim
6379029108 under coordinator claim 6379021921. Base `ec16bc1`;
[PR #132](https://github.com/OptimumAF/LocalLore/pull/132) was open/unmerged
when this packet was claimed.
This report records independent source/evidence inspection, not owner acceptance.

The reviewer owns this file only in a separate worktree. No reviewer build,
suite, device, model-content/cache operation or inference ran. Source and host
evidence are inspected below; device results are recorded only when supplied.

## Initial lifecycle findings

The existing Setup Activity registers its OpenDocument callback unconditionally;
the retained ViewModel fences duplicate results, background/disposal completions
and overlapping operations until actual provider return. The selected stream is
opened through ContentResolver on IO, not during the callback on Main. Provider
metadata cannot change the fixed identity or select native paths/runtime profiles.
Cancellation cannot promise that provider open/read/close returned.

A retained Activity recreation and a fresh controller have different behavior.
The existing ViewModel retains PICKING through ordinary recreation. A fresh
controller has no outstanding-picker state and rejects a restored result. The
host test `restoredControllerIgnoresOldPickerDelivery` deliberately encodes that
fail-closed behavior. It prevents an unassociated result from opening a stream,
but does not preserve an explicitly selected file across process death. Tests
and user-facing claims must distinguish these cases. Either restore only the
pending transaction marker or retain the conservative discard policy with clear
retry guidance; never restore READY, a stream, a provider-selected identity or a
runtime attachment from saved state. This is a workflow decision, not evidence
of partial canonical mutation.

Coordinator amendment 6379057534 preserves the existing conservative discard
policy; this packet does not add automatic resume or SavedState persistence.
Fresh-process file revalidation must be tested independently of a pending picker.

The official [Activity Result guide](https://developer.android.com/training/basics/intents/result)
requires unconditional registration and independently saving additional state
needed to handle a result after process recreation. Its registration contract
does not persist application ViewModel state. The [UI state guide](https://developer.android.com/topic/libraries/architecture/saving-states)
distinguishes retained ViewModels from process-restorable saved state.

The current [AndroidX ActivityResultRegistry source](https://raw.githubusercontent.com/androidx/androidx/androidx-main/activity/activity/src/main/java/androidx/activity/result/ActivityResultRegistry.kt)
registers lifecycle callbacks at ON_START, removes them at ON_STOP, stores pending
results, and saves launched keys/pending results in a Bundle. This upstream source
explains why a callback can be delivered around the Activity's foreground hook;
it is not proof of execution under the project's pinned dependency version.

## Fixture boundary recommendation

Use a fixed tiny identity and private root in a non-exported subclass compiled
only into an explicit isolated debug fixture profile/package. Override one narrow
setup-dependencies factory while inheriting production OpenDocument creation,
ContentResolver opening, controller, rendering and store/publication. Do not add
an Intent extra, URI parameter, model response, system property or external
profile selector that changes the production identity. Verify the actual merged
manifest and DEX exclusions for ordinary and modelverify artifacts.

The [Android build-variant guide](https://developer.android.com/build/build-variants)
supports source-set separation. The [Compose testing guide](https://developer.android.com/develop/ui/compose/testing/common-patterns)
requires host Activities to be declared in the app manifest. A real picker test
must launch the real contract/system DocumentsUI and explicitly select a document;
an injected registry or manually delivered URI alone cannot establish SAF wiring.
The [SAF overview](https://developer.android.com/guide/topics/providers/document-provider)
distinguishes the system picker, provider and client roles. A fixed local test
DocumentsProvider can exercise that path without exposing model weights or
private files. Provider controls must authenticate exact test/target callers and
accept only finite fixture actions, never arbitrary paths or content.

The frozen amendment chooses `.modelpickerverify` only with all three explicit
verification flags, conditional `modelPicker` target sources and conditional
`modelPickerAndroidTest` sources. A single internal immutable
`LocalModelSetupDependencies` factory supplies identity/check/install/admission/
openPlay; the default remains fixed CandidateLocalModel. The fixture fixes a tiny
identity/root and refuses play. This interface can exercise successful real
picker/import wiring without making a fixture artifact a runtime/model result.

Public API-26 [StorageManager.openProxyFileDescriptor](https://developer.android.com/reference/android/os/storage/StorageManager#openProxyFileDescriptor(int,%20android.os.ProxyFileDescriptorCallback,%20android.os.Handler))
dispatches file operations to the supplied callback Handler. Its
[ProxyFileDescriptorCallback](https://developer.android.com/reference/android/os/ProxyFileDescriptorCallback)
reports `onRelease` after file close. A fixed proxy fixture with a bounded blocked
read and independently reachable release control can observe actual descriptor
drain; a cancellation request alone cannot replace that observation. Provider
process identity and permitted cleanup need explicit controller admission.

The installed official API-34 SDK `Instrumentation.java` was inspected (source
reasoning, not API-34 execution). Its no-argument ActivityMonitor invokes
`onStartActivity(Intent)`; returning null observes without intercepting the
launch. The filter constructor does not invoke that callback. This permits
finite assertions about the actual OpenDocument action/type/openable/local-only
request while still using the real DocumentsUI. Do not retain selected URI data
or substitute an ActivityResult in that monitor.

## Implementation and audit review

The draft central seam/build/manifests and three fixture-author files were read.
The inherited Activity path keeps the original local-only OpenDocument contract
and ContentResolver stream opening. The fixture supplies an immutable original
63-byte payload identity and a fixed child of the canonical private anchor;
its root getter refuses Main-thread access and another installation. Its play
callback refuses inference rather than providing a fake runtime fallback.

The TEST-only provider authenticates exact package-resolved target/test UIDs for
control, accepts finite configure/stats/release operations, uses random bounded
transaction tokens and rejects stale controls. Document IDs select only four
fixed kinds; none become file paths. Real DocumentsProvider grant enforcement
remains in the framework dispatch. The callback Handler is separate from Binder
control, so releasing a blocked read does not require its blocked Handler.

An initial draft checked active ownership before allocating a proxy descriptor
but reserved only after allocation. That left a gap for another open/configure.
The author corrected it before handoff: reservation now occurs under the same
gate before allocation, failure releases that reservation and successful open
retains it until actual `onRelease`. The reviewer reread the changed hunk.
This is a source correction; a concurrency execution result is not inferred.

The first draft test meaningfully checks real picker dismissal across retained
recreation, preselection denial and postselection temporary grants, exact fixed
failure text, wrong bytes, open failure, blocking descriptor retention after
Cancel, actual BUSY from the shared store, subsequent release/drain, no stale
READY, full valid publication/reopen and no persisted grants. A passive monitor
checks each real launch request. A second method requires a different private
PID/start proof before revalidating the same private file without picker reopen.
The controller must additionally observe old-process exit between methods.

The author subsequently added a second blocked-provider transaction spanning
actual Activity recreation/background cancellation, disposal and a fresh
controller. It checks retained STOPPING, the new controller's BUSY failure
without another provider open, and actual descriptor release plus stage removal
and successful store reacquisition. Neither disposed nor fresh controller may
become READY from the old work; valid selection follows separately. A stale
first-transaction release is refused. This closes the earlier source-coverage
gap; execution had not yet run at that source review. That draft expected six actual picker
launches and exact descriptor counters for both transactions.

Pending-picker recreation now uses the stopped Activity's `recreate()` on Main
and observes its CREATED replacement through the lifecycle monitor. It keeps
DocumentsUI foreground, retains the original ViewModel and avoids
ActivityScenario's resumed-state precondition while the picker is open. Actual
replacement tracking and result delivery still need device evidence.

The new fixture test manifest replaces the normal TEST manifest only for this
isolated profile. Compilation of other tests does not establish execution of
their former provider flows.

The first APK exclusion draft searched only the fixture Activity name. The
reviewer requested rejecting a leaked `ModelPickerFixture` helper/identity even
without that Activity. The revised source detects both helper-family presence
and the required Activity, with a helper-only hostile regression. It also
rejects a test provider in APP DEX and inspects the exact owned TEST provider
authorities, process, platform permission/grants and control boundary. These are
finite source checks; actual artifact inspection and test execution were still
separate requirements at that draft review. The artifact helper must invoke the TEST-manifest audit
on actual TEST aapt output, not infer it from the APP CLI audit.

## Provisional execution evidence review

The retained fixture build result records completed exit 0/known cleanup in
295,172 ms, with 12,470-byte stdout SHA256
`0b025ccf6d2c572316c80eb726a680ed8bb325d49bdcb73b24adbae93edc7470`.
The reviewer independently parsed the current 27 XML suites: 275 tests, zero
failures/errors/skips. Lint XML contains zero errors/four warnings: two
UsableSpace, one GradleDependency and one OldTargetApi. The retained script
result is completed exit 0/known cleanup, 18,094 ms; actual raw output records
194 passing tests in 17.488 seconds. No reviewer suite ran. These observations
precede a closed hash selection and cannot substitute for its final bindings.

The artifact helper was inspected and does invoke the TEST provider audit on
actual aapt output. It additionally verifies exact runner/target, the TEST's
REORDER_TASKS-only permission, no TEST native libraries, APP permission/native/
launcher audits and actual signature output. Source/artifact rehash admission
remains separate from these helper assertions.

The device agent's disabled provisional controller and 36 pure fixture
definitions were inspected without executing them. Phase 1 preserves the prior
31 packages, adds only the new pair, selects only the first exact method and
has no process-stop path. Phase 2 requires its successful predecessor's actual
zero-descriptor/scenario-close assertions, then compares fresh full maps,
installed UIDs and process rows before each exact TEST/APP stop. Only captured
rows or their natural-disappearance subsets are accepted; new PIDs or another
LocalLore process abort. No wildcard, original APP stop, storage reset or model
operation is admitted. Old-process absence precedes the separate readback
method; a failed readback cannot reach final cleanup.

The wrapper's 180-second budget is checked through the actual inherited helper
with pre-cancel set before spawn. The source guards propagate nonzero CLI exit;
the pure fixture definitions cover the old invalid 210-second budget, no-spawn
validation, changed PID/UID/map, sticky uncertain cleanup, wrong method, failure
despite runner success and absence of late cleanup. These tests were not rerun
by the reviewer. Source-final was false at this initial inspection. A final disabled
proposal must bind the prior sealed package map and final sources/APKs/audits
before any coordinator admission. Storage floors are boundary observations,
not filesystem space reservations.

## Frozen phase-1 admission review

The final disabled proposal SHA256 is
`d40d1beb1d6c3ac7c97804d57ca5ff3b94a15fcc0207c6bbfa905cc40f6e9858`.
The reviewer independently rehashed all 120 bindings, 77,018,645 bytes, with zero
mismatches. Source-final was true; device flags were disabled/pending at this
pre-GO review. The prior 31-package map matches the sealed provisioning result. The
bindings include fixed source snapshots, actual final source, artifact copies,
captured aapt/signature output, actual helper definitions and final pure results.
The retained pure log has 36 passing tests in 0.052 seconds, preparation-only
exit 0 in 263 ms, with no device calls. A hash match is not device execution or
coordinator authorization.

| Selected artifact | Bytes | SHA256 |
|---|---:|---|
| APP | 73,829,600 | `3a053211407f386f220e2ffd0ebd4adcfafa4e7e791b130fad0731df7338e56f` |
| TEST | 1,775,837 | `0aa9ee2f2b6e755ddd6e14b5e562114214744ac9d220ededb12f81cb160e1c7b` |

Actual TEST manifest output confirms the exact two owned provider authorities
and private provider process, MANAGE_DOCUMENTS protection/URI grants on document
access and the separate authenticated control. Existing AndroidX test Activities
remain; the audit does not claim there are no third-party debug components.
Captured signatures verify the same signer for both selected APKs. APP retains
the setup-only launcher, private Main/Play/fixture Activities, no INTERNET and
six native libraries with the checked 16 KiB alignments; TEST has no native
libraries. Full pinned SDK notice assets remain checked independently of
redistribution clearance.

The archived host closure was subsequently inspected independently: ordinary
23 suites/203 tests and fixture 27 suites/275 tests, all zero failures/errors/
skips. Ordinary lint has zero errors/one warning. Direct ordinary APK reading
confirms 23,214,204 bytes, SHA256
`29c56f9d6b37d030d352ecf78ac983cd515774801b27a1a49ae356095e27c111`,
five DEX files with no fixture helper/Activity or DocumentsProvider marker, and
only the existing four native libraries across two ABIs. This ordinary result
does not execute an ARM64 device or a real inference engine.

No source/artifact objection was returned for the coordinator considering one
phase-1 admission. Phase 2 cannot be inferred from that review; it requires an
actual passing predecessor, fresh bindings and a separate coordinator decision.

## First device cohort: retained failure

The original owned process reached completed exit 2/known cleanup in 32,406 ms.
The controller stopped at client 22, the first selected instrumentation method.
All 22 clients record completed exit 0/known cleanup. The actual 3,495-byte runner
output, SHA256
`db4146b89e657147cdcb329910b64688da7dba6f76ee53a1a414c20514241881`,
contains zero PASS/one FAIL at source line 194: the combined six-launch-count
and all-request-flags assertion. The raw output does not distinguish the failing
clause or record any individual count/flag values.

The test reached its earlier picker, wrong/open-failure, blocked cancellation,
recreation/disposal, valid publication and revalidation assertions. That is
bounded evidence for those assertions, not an overall passing cohort. The
private restart proof comes after the failing assertion and was not written;
the second method did not run. No post-instrumentation process/map/storage
query or cleanup ran. The last installed gate preserves all original 31 hashes
in the 33-package map and reports 1,389,129,728 available bytes. Post-failure
device state was unobserved until the separate settlement below. Two install stderr byte counts were retained
without contents; no zero-stderr claim is made for those clients.

The reviewer independently rehashed the stopped selection: 247 files,
77,939,634 bytes, zero mismatches. Its 44,667-byte index SHA256 is
`8706679edaaf360df31635c1d8d8f6bb9da2be0d6bf0ae6b459f3dcc595d21e4`.
All 120 original inputs were captured before source correction. A new fixture
or production correction needs new host/artifact checks and device admission;
this failed all-PASS gate is not resumed.

The fixture author then inspected the pinned contract implementation and found
that OpenDocument does not add CATEGORY_OPENABLE. Independent reading of the
official [AndroidX contract source](https://raw.githubusercontent.com/androidx/androidx/androidx-main/activity/activity/src/main/java/androidx/activity/result/contract/ActivityResultContracts.kt)
confirms OpenDocument sets action/MIME types/wildcard type, while GetContent
explicitly adds that category. The production override added only LOCAL_ONLY.
The review had inferred openability from superclass behavior incorrectly.
Source evidence establishes that omission; it does not recover the first run's
unrecorded monitor values. Explicitly adding CATEGORY_OPENABLE is appropriate
for this raw InputStream importer, which cannot consume virtual documents.
The proposed fix retains the strict test and splits bounded diagnostics for
count/type/openable/local-only, rather than weakening the request requirement.

The repaired test was reread before handoff: it retains at most 16 finite request
records, separately counts actual launches, and immediately checks exactly one
observation plus wildcard type, local-only, openable and the exact wildcard MIME
array after each actual picker launch. It still requires six total launches.
Diagnostic messages contain only capped counts, ordinal and booleans. The root
adds CATEGORY_OPENABLE explicitly in the production contract. Neither change
intercepts a result or chooses a model from external input.

## Separate disposable-namespace recovery review

The coordinator chose a separately admitted exact reset of the new synthetic
APP after preserving failed evidence. A new fixed fixture child was an
alternative, not a requirement to preserve reproducible generated 63-byte
output. The original 31 installations and real story/model/runtime namespaces
remain outside this recovery.

The disabled recovery-only proposal SHA256 is
`e7a3bbbab8a78f4e3008e5cb64ffe03df7ff325bd2e904efd51a2889cb3eb964`.
The reviewer independently rehashed 260 bindings, 78,036,016 bytes, with zero
mismatches; flags were disabled/pending at inspection. The selected immutable
failed cohort, old inputs, installed 33-package map and separate installed UID
pair are included. Source and 18 pure fixture definitions/results were reviewed;
no reviewer execution followed.

The controller admits only metadata, conditional exact new TEST/APP stops and
one APP-only clear. It captures fresh matching map/UID/process rows, rechecks
the captured subset before each stop, accepts natural disappearance and aborts
on new/foreign rows. It proves absence and floors, repeats the complete
map/UID/absence observation immediately before the sole clear, then checks the
full state again. Install, instrumentation, TEST clear, original-namespace
lifecycle operations, wildcard selection and path deletion are absent from the
allowlist. The actual 180-second budget and CLI nonzero propagation remain
covered by pure definitions. Review found no source/artifact objection to the
coordinator considering this recovery-only admission. Corrected execution must
be separately admitted against prior 33 packages and actual recovery evidence;
the original prior-31/absent-pair controller cannot be resumed.

The admitted recovery then stopped before mutation: seven completed exit-0/
known clients in 3,547 ms, owned child exit 2/known cleanup, zero stops and zero
clears. Identity, installed 33 hashes and the separate UID pair matched. The
first process observation contained nine older registered TEST chooser-provider
processes, so the strict parser rejected it before storage observations or any
cleanup. This failed recovery does not authorize stopping those processes.

The reviewer investigated archived artifacts without device access. All nine
retained TEST APKs exactly match their installed hashes, and actual local aapt
manifest inspection confirms ChooserArchiveProvider, each exact TEST chooser
authority, `:chooser_test_provider`, MANAGE_DOCUMENTS and document-provider
discovery. The nine known installation suffixes are archivecapacity,
archiveverify, storydelete, timelineverify, parentverify, externalverify,
litertverify, modelverify and cancelack. No blanket process-name prefix is
justified by that finite set.

The current provider source resolves its TEST identity/private base and starts
a callback Handler in onCreate; queryRoots supplies metadata without invoking
an engine/model. Official [AOSP ProvidersCache source](https://android.googlesource.com/platform/packages/apps/DocumentsUI/+/cc8e4ba53cdfb832b48f26d521a916aed40166e0/src/com/android/documentsui/roots/ProvidersCache.java)
acquires registered providers and queries their root URI. DocumentsUI discovery
is therefore a supported explanation, not an observed causal trace. That source
does not certify the exact system image or prove that an unknown process is
safe. A separately admitted read-only full-package UID/process/map/floor
settlement can establish narrow passive classification: exact nine full names,
matching immutable APK hashes and fresh installed UIDs, with no old lifecycle
operation or file read and all other LocalLore names still refused.

## Corrected host selection

The coordinator completed corrected regular and fixture builds after the
explicit openable category and per-request assertion changes. The final host
v2 selection was independently rehashed: 591 files, 329,530,742 bytes, zero
mismatches; index SHA256
`c6b7e68b56a52ffaf92d6b2b98a02b2e166a732f9f0625a24cf115a20abf89f1`.
The first index remains retained because a fixture-audit helper invocation
omitted its phase argument and exited before creating its output. The corrected
argument produced the selected actual audit; no build result is inferred from
that failed helper invocation or an unnecessary build rerun.

The final corrected regular and fixture XML archives were independently parsed
under `final-host-selection-v1`: each has 27 suites/275 tests, zero failures,
errors or skips. They are included in the verified v2 selection. Corrected
fixture owned execution is exit 0/known cleanup in 118,766 ms; its actual selected
APP is 73,829,600 bytes, SHA256
`31d3131612f75972096ef78d843995bbf5d3f1feb811c9b07ffd4563f8a9ae89`;
TEST is 1,777,609 bytes, SHA256
`7aa2495ca37675ac2bf0e72c43f68051b01cc3b0566314d33211c957dd624fe5`.

## Separate read-only provider settlement

The disabled proposal SHA256
`e7530be29afe91293081661e09ca39f092d74fdce3b11e56ccdb0708b793235e`
and all 61 bindings/21,264,194 bytes were independently rehashed, zero mismatches.
It admits exactly nine ordered metadata queries, the exact 33-package/UID set,
the finite nine passive provider names with APK/fresh UID correspondence, the
three owned names with their separate UIDs, and rejects all other LocalLore
names. It has no lifecycle, mutation, installation, instrumentation, model or
follow-on path. The reviewer returned no source/artifact blocker while flags
were still disabled/pending; coordinator admission is separate.

The admitted settlement completed exit 0/known cleanup in 2,984 ms. The reviewer
independently inspected all nine client records and matching raw hashes: each
completed exit 0/known cleanup, all client stderr counts zero. Actual facts
contain 33 package hashes, 33 installed UIDs, two owned rows and nine passive
provider rows, with 1,389,101,056 available bytes. This is a metadata observation;
it neither proves provider natural teardown nor authorizes a stop/reset or a
corrected instrumentation run.

The read-only settlement selection was independently rehashed: 63 files,
211,678 bytes, zero mismatches; index SHA256
`826df61adaa74ac43f5aa3296a82e1f769ccddeeef47b7296e564178f094eb5d`.
The stopped earlier recovery selection was independently rehashed too: 297
files/78,291,445 bytes, index SHA256
`918d8e0f2d1d6aa876b2a6455bea5b19b5198848b70b094b09f99022fc84da5f`.

## Revised recovery

The full-UID/passive-aware recovery v2 proposal was reviewed and all 105
bindings/21,391,280 bytes independently matched. Before dispatch the device
agent found its clear-success oracle accepted raw LF only, whereas retained
metadata uses CRLF. The coordinator revoked the unused GO; no v2 lease, start,
result or dispatch directory existed. This is a prevented likely oracle error,
not a failed device recovery or proof of any returned clear value.

The fresh v3 proposal SHA256
`91c090061f76e7ad2a44543983123b583afcc97cd2731653e3db284910be7a07`
and 109 bindings/21,451,599 bytes were independently rehashed, zero mismatches.
Its sole controller change imports the existing strict normalizer and accepts
exact semantic `Success\n` for consistent LF/CRLF. Mixed/lone CR, controls,
Failure, extra/oversized output remain rejected; 23 pure tests pass in the
retained log. The same exact new namespace stop/clear and passive nonownership
guards remain. Review returned no source/artifact blocker for this separate GO.

Actual v3 recovery completed exit 0/known cleanup in 18,204 ms. The reviewer
independently checked all 41 client records and raw hashes: terminal exit 0/
known cleanup, stderr counts zero. There was one exact new TEST stop, no APP
stop and one exact new APP clear. Final metadata preserves all 33 APK hashes/
UIDs, shows zero owned and six passive rows, and 1,389,264,896 available bytes.
The passive decrease is an observation only. This externally controlled reset
does not qualify natural provider/model teardown or admit the next execution.

The recovery-v3 closed selection was independently rehashed: 119 files/301,734
bytes, zero mismatches; index SHA256
`356c9fcc3b42a91deed27a70b23e3576d4583e9d4a4bd5255dca61e6fd237b30`.

## Corrected first method

The separately disabled corrected proposal SHA256
`d2bc907da08db0f5b28e295996fed6c2fa040cafefc8a5ea737157cc6639695c`
and 218 bindings/77,355,874 bytes independently match, zero mismatches. It
requires actual observed recovery/reset evidence, preserves all 33 installed
UIDs, permits only the two owned APK updates, preserves the other 31 hashes,
requires owned-process absence before installation/test and selects only the
corrected first method. Exact nine passive identities remain observation only;
unknown names still abort. No lifecycle or readback command is admitted. The
reviewer read the retained 30-passing-test pure log and returned no source/
artifact blocker while flags remained disabled/pending.

The admitted corrected method completed exit 0/known cleanup in 29,219 ms.
All 30 client records/raw hashes were independently checked: completed exit 0/
known cleanup and zero stops. The actual 833-byte instrumentation output SHA256
is `a24c44b6fb8278916500ba21d561f04c94570dfe241f87e51ca24147336091b7`;
it contains exactly one PASS/zero FAIL in 17.614 seconds. It verifies every
actual request independently and all six total requests, real grant boundaries,
wrong-byte/provider failures, both blocked-read cancellation/lifecycle cases,
descriptor drain, stale-state refusal, valid native publication/full reopen,
recreated/new Activity revalidation and the private process-proof write. No
runtime owner, real model or canonical gameplay workspace was constructed.

The after gate has the exact 33 hashes/UIDs, two owned and three passive rows,
with 1,387,884,544 available bytes. Install stderr totals 331 bytes with contents
unretained; no blanket zero-stderr claim follows. The method's actual PASS
establishes its source assertions, not untested semantic/model/phone gates.
The closed corrected first-method selection was independently rehashed: 133
files/918,459 bytes, zero mismatches; index SHA256
`956362a1df54866e53d942c5f3bec110e7fb3983e77eabe984b95a3dcffc1817`.

## Actual process restart/readback

The separate disabled readback proposal SHA256
`4eafb363d2766a0f273c5a824407d2d98a76de7e4990bf1af1b1ca229cb10718`
and 303 bindings/77,583,352 bytes independently matched, zero mismatches.
Review verified actual first-PASS/zero-descriptor/closed-scenario/private-proof
prerequisites; full fresh package/UID checks and captured-owned-row subsets
before each exact TEST/APP stop; observed owned-process absence before selecting
only the second method; no installation/clear/reset; final cleanup only after
its exact PASS. Passive identities remain observation only. The retained pure
log records 24 passing tests. Review returned no source/artifact blocker while
flags were disabled/pending.

Admitted readback completed exit 0/known cleanup in 39,047 ms. The reviewer
independently checked all 72 client records/raw hashes: completed exit 0/known
cleanup and zero client stderr counts. The 800-byte instrumentation output
SHA256 is `62f27d928a95b3e5607da05adcd58e58bcc590c3a9008c90c7514dd2fe177ba3`;
it contains exactly one PASS/zero FAIL in 3.259 seconds. The selected test
requires a different actual PID/start pair and verifies the full same private
63-byte artifact, size/hash/cache/staging state, READY and no picker/persisted
grant. The controller separately observed old-owned-process absence first.

There were two exact new TEST stops across the restart/final cleanup rounds,
no APP stop and no clear/reset during readback. Final metadata retains all 33
APK hashes/UIDs, zero owned and two passive rows, with 1,388,707,840 available
bytes. External stops do not prove natural or active-model cleanup. No prior
namespace lifecycle operation, real-model read/copy, Engine initialization, native
workspace/turn or inference followed from these synthetic methods.

After the original owned handle was confirmed terminal, the reviewer
independently rehashed the final readback selection: 184 files/508,273 bytes,
zero mismatches; index SHA256
`77e755f068bc73e2db17b3ae95e77c28ae4a4b0fbdc301088439eb10aafeee48`.
The lease was released and no further device call was planned for this packet.

## Disposition and remaining scope

The scoped M05.05 picker/provider/restart implementation and M05.04 supporting
failure handling have meaningful passing synthetic evidence after the retained
failures/corrections: two separately selected methods, two PASS/zero FAIL in
the corrected cohort. Execution covers one admitted Android 15/API 35 x86_64
emulator with 4 KiB pages. Source/artifact/evidence review has no remaining concrete
blocker for this packet. This is an independent engineering review, not owner
acceptance or permission to merge/check milestone tasks.

The next runnable packet is M05.05 pending-picker/import process-death synthetic
recovery. The present restart test starts after a verified publication and does
not establish recovery from process death during picker/open/read/publication.
Full M05.05 real-backend scene and reference-phone gates remain pending;
M01.01 physical-phone availability remains blocked per [#5](https://github.com/OptimumAF/LocalLore/issues/5).

A/#117/#119 and physical-phone/model gates remain held. Synthetic tests do not
qualify real model initialization, active inference cancellation, phone memory,
thermal performance, narrative quality, ARM64 execution or redistribution.
