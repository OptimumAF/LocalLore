# Independent receipt setup integration review — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).

## Scope and current disposition

Independent review under root claim6387042995, subclaim6387056212, from exact
unmerged #146 head `ebb8c0913ddeffe7c824618ec2d3e5c58692b11b`. The reviewer owns
only this report and runs no builds, shared-cache changes, SDK/ADB/AVD operations,
model transfers or inference. Review findings grant no execution authority.

The explicit debug receipt route is implemented and host-tested. Its initial
Android cohort records three passes for production setup import/recheck,
cancellation before/after acceptance and disposed blocked-source drain. The
host controller then stops on its overly broad quiet-process precondition:
the original APP is absent but the known TEST helper remains. No receipt proof
reads or separate-process reopen invocation follow. This is a partial setup
qualification, not a four-pass result or a real-model/runtime qualification.
Full M05/M01 and existing owner/model/storage/device holds remain unchecked.

## Existing boundaries inspected

The baseline candidate caches a concrete `LocalModelStore`. Normal setup resolves
it lazily within its controller's IO operations. Model setup has fixed built-in
identity and immutable dependency factories; no Intent or document metadata
selects a profile. Path planning and transport construction perform no file work
on Main. `CandidateOwnerAdmission` claims before construction and deliberately
retains that claim after failure, Activity finish or uncertain callbacks.

The unchanged worker first invokes storage admission, then full model size/hash
validation, rechecks admission and only then constructs the SDK engine. Admission
also precedes initialization, conversation creation and send. The access seam
must fit these existing boundaries; it must not remove initial full hashing,
perform full 2.59 GB hashes at each later boundary or reset an uncertain owner.

The receipt transaction already distinguishes accepted state from complete but
pending bytes. Its exact bounded receipt and ownership records bind trusted
control/data roots; full reopen takes the global reservation and persistent
nonblocking OS lock. Accepted-marker creation is the logical acceptance point.
Cancellation or errors afterward can leave accepted data and require recheck;
they never establish rollback. Existing model publication and canonical story
storage remain separate contracts.

## Early interface findings

The minimal access contract is suspending `import` and `installed`, pure
`plannedFiles`, and a synchronous IO-only `admitRuntime`. A legacy adapter can
delegate its existing store behavior. An explicitly selected receipt adapter can
delegate the qualified transaction; neither adapter should silently choose the
other on failure or adopt prior model/benchmark roots.

Receipt runtime admission must establish current acceptance, rather than checking
only a cached READY Boolean or available volume. Prefer shared receipt structural
validation over a second, more permissive metadata parser. A verified-accepted
stamp can come only from successful full import/reopen validation. Clear it
before revalidation and on failure, cancellation or channel-close failure,
including errors after marker creation. A later full `installed()` can recover
accepted state. Without that stamp, metadata that merely looks valid must not
admit SDK construction.

Each runtime check should take the existing global reservation and persistent
lock without creating files or cache, revalidate zero-byte accepted marker,
exact receipt/owner/root binding and safe model/cache metadata, compare the
verified stamp, and apply current volume/capacity admission. The worker's initial
full hash still rejects corrupt model bytes before engine entry. Later metadata
checks cannot authenticate hostile concurrent OS replacement; that limitation
must remain explicit rather than being hidden by the stamp.

## Required concrete negative cases

- Pure planning/configuration/transport construction performs no filesystem
  operation or Context volume enumeration on Main.
- Missing/pending/foreign/nonzero/linked acceptance metadata, missing persistent
  lock or cache, stale stamp and capacity/media refusal stop before SDK engine
  construction and leave all existing files preserved.
- Removal or mutation after setup READY and between engine, initialization,
  conversation and send refuses at the next existing boundary, preserving
  uncertain-resource retention and the claimed candidate owner.
- Initial full hashing catches corruption despite otherwise valid acceptance
  metadata; source factories stay unopened during reopen, complete recovery and
  refusal. No alternate store or source is tried.
- Cancellation before acceptance retains pending bytes. Cancellation after
  acceptance may retain committed bytes; no stale READY result or rollback
  claim is allowed before an explicit full recheck.
- A disposed controller with a blocked source retains BUSY until the actual
  read and source close drain; a replacement Activity cannot overlap it.
- Ordinary/default and release artifacts retain their routes/exclusions, backup
  policy and permissions. Fixed new Context-derived receipt roots cannot collide
  with old candidate, benchmark, synthetic fixture or canonical workspace roots.

Synthetic Compose tests may inject a trusted fixed source/checkpoint through an
internal fixture seam to exercise inherited UI/controller/receipt wiring. They
must state when they do not exercise DocumentsUI, provider grants or actual
Activity-result delivery. A separate ordinary instrumentation reopen can prove
process recovery now that no picker is outstanding; compare PID/start identity
pairs and full accepted bytes, not PID alone or a recreated Activity.

## Frozen interface review

The actual shared interface and contract at
`3540bffdb96fee67aa22d128f84520bb7645144a` preserve the existing publication
delegate, explicit receipt/volume/setup/LiteRT build gate, fixed new roots and
legacy removable-root refusal. The contract requires stamp publication after
all closes while retaining the global reservation, noncreating current
acceptance checks, cache directory identity without child-write timestamps, and
the unchanged full-hash worker path. No remaining concrete contract blocker was
found. Actual source must implement those conditions; a contract is not evidence
that the new runtime path does so.

## Concrete source findings and isolated evidence

The actual core/adapter/test handoff at
`08fc9cf58a75da508244ba2db0c5cd23c93b3a02` implements shared structural checks,
stamp capture under the held OS lock and publication after action/lock closes,
while the global reservation is still held. Its outer failure path clears
prompt cancellation when returning from IO. Runtime admission is noncreating and
bounded; cache child writes are opaque and initial full model hashing remains.
No concrete remaining core source blocker was found.

The reviewer independently checked all 21 isolated compile/test input bindings,
69,690,729 bytes. Retained compilation completed zero with known cleanup in
10,079 ms. Actual JUnit records 36 passes in 5.308 seconds, including 12 new
access methods and the existing transaction/process tests. Its original owned
test child completed zero with known cleanup in 5,625 ms; 92-byte output
SHA-256 `9b5e47da95c0c025de80a66852089b6a2eb361ede35ac08f3bc76eac8807f7ea`.
This uses installed JDK21/Kotlin2.4.0 with JVM target17; it is not an Android,
Gradle, Java17-runtime or SDK execution result. No reviewer tests ran.

Review identified a typed-error regression in the draft Android guard: an
already-redacted `NO_SPACE` was remapped to `STORAGE`. The coordinator accepted
preserving that fixed exception while retaining sticky refusal. Integrated
`773b0af7b92f8b5837ea27c6aee0bf72a4da86f5` contains that correction and five
focused guard tests covering absent/present/dangling legacy roots, typed capacity
failure, sticky refusal, cancellation and redaction. Their central execution
remains separate evidence.

The Android fixture draft also opened the persistent lock inode to check that
it was empty while the import held that lock. A second same-process channel can
disturb native locks on some systems, precisely what the global reservation
avoids. The author replaced that read with NOFOLLOW regular/size metadata only.
This concern is specified in [FileLock platform dependencies](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/FileLock.html).
The fixture also gained explicit local API guards before newer process APIs.

Emergency gate/source timeouts could previously look like successful explicit
drain. The corrected tests require flags set only when their release waits
return successfully; a timeout cannot earn the cancellation/drain checks.
Source-only fixture handoff `9fe9ec0a30c95be795878d0c494b17b94ebd1e88`
contains these fixes. No compile, lint or Android pass is inferred from that
handoff. Its four fixed nonexported activities and separate reopen invocation
retain explicit direct-callback/no-DocumentsUI limits.

The first setup-controller draft requested a 360-second outer operation from
the existing process helper, which accepts at most 180 seconds. That path would
refuse before spawning the worker. The coordinator corrected the new controller
and protocol to a 180-second outer/165-second aggregate limit in
`84735f3e56fce8a9d427aee92f0821797e2c2df5`, preserving the shared helper limit.
Each client is capped by remaining time. The outer-entry regression below
exercises the real helper validator; a mocked dispatcher alone would not
establish that this CLI works.

Independent controller tests initially asserted that the production APK map
must stay empty. That would fail after the coordinator pins the actual audited
pair. Review identified all three such assertions; `6cf7383` changes them to
preserve the original map and patch an empty map only for the explicit unfrozen
negative case. Positive synthetic hashes remain confined to test patches.

The retained pre-pin controller suite records 19 passes in 7.376 seconds; its
owned child completed zero with known cleanup in 7,641 ms and unchanged input
hashes. Output SHA-256
`2690163bee9bff8c6fa9e682084b1bf7cd31cf3052b8feb8a52cb2c9dd9fda8e`.
The tests exercise the actual precancelled process-helper validator without
spawning a process, including accepted 180-second and refused 360-second limits,
plus two-stage full mocked flow, actual raw retention, owner/cleanup loss,
capacity, proof/runner and stale-restart refusals. This historical pass does not
cover the later map-pinning/test adjustment; the final 559-test gate below does.

## Environment input review

The initial disabled environment proposal selected installed JDK21 instead of
the previously exercised JBR17 preparation runtime. Review identified that
unnecessary toolchain delta before any SDK execution. Its 925 bindings,
5,282,231,951 bytes, and token/old-registry metadata independently match, but
the coordinator retained it unused and chose a separately frozen proposal with
the proven JBR17 runtime. No target directory, guest or test result was created
by reviewing that unused proposal.

The separately disabled prepare v2 proposal SHA-256 is
`67267c43c7d6b0fffb93f4f37101df4bf4e835071e80f03999cdd3c659b7688f`.
Its 909 installed/helper bindings, 5,046,134,929 bytes, equal the previously
exercised JBR17 preparation set and independently rehash without mismatch. The
existing token and eight default-registry metadata bindings also match. Only
fresh target paths differ; target and authorization were absent at review.
Requested 12 GiB userdata/8 GiB SD/2 GiB RAM/two CPUs and corrected launch
arguments are unchanged. No remaining concrete source/input blocker was found
for preparation; build, actual preparation, retained launch, guest capacity and
setup qualification are separate gates.

The coordinator confirmed the original preparation completed zero with known
cleanup in 4,125 ms, successful closure and an accepted prepared record. The
separately disabled run proposal SHA-256 is
`347108ad67a41916e818035517ed1b0edc7a3076194a7ba387810f8365042ce9`.
Shared fields and all 909 bindings exactly equal the reviewed prepare proposal;
prepared and successful-result linkage match. Independent stream hashing of
three immutable files, initial 8 GiB SD and token/old-registry records has zero
mismatches. Actual normalized config retains 12 GiB userdata/8 GiB SD/2 GiB
RAM/two CPUs and only fresh owned data/cache/SD paths. Userdata is absent and
boot explicitly unverified; reviewed run namespace was unused and authorization
absent. No remaining concrete source/input blocker was found for the bounded
owned run; readiness and guest results remain separate gates.

## Central receipt build and checks

The coordinator reports the actual receipt build completed zero with known
cleanup in 361,812 ms. The reviewer checked its retained output digest and actual
XML: 340 JVM tests across 35 suites, zero failures/errors/skips, including 12 new
access and five guard tests. Lint records zero errors and 19 advisories, including
16 usable-space observations; no warning is suppressed or treated as measured
capacity. Actual copied APP/TEST sizes and SHA-256 match the frozen pair. A pure
read-only ZIP/native/receipt-fixture audit of the actual APP passes six native
library checks without invoking an SDK executable.

The 62 runtime and 67 analyzer artifact rows exactly match the earlier retained
graphs; analyzer32.4.1 reports actual work. No dependency/model/runtime selection
changes follow from this adapter. The current controller pins the audited pair;
the post-pin central script gate records 559 passes, zero failures/errors/skips,
47.438 seconds. Original owned child completed zero with known cleanup in
48,281 ms; the reviewer checked actual summary and output SHA-256
`599c7aeb8b49bd5335293b44daf19756b375e8536aa7b44dd812534ec72ededf`.

Regular and ordinary builds also completed zero with known cleanup, respectively
335,047 and 363,250 ms. Independent actual XML counts are 340/35 and 206/24,
zero failures/errors/skips; retained lint reports zero errors with nine and one
advisories. Actual APP DEX excludes receipt setup fixtures in both profiles;
packaged audit records pass six and four native-library checks respectively.
The six actual invalid-profile invocations each return one with their expected
refusal: false receipt flag, absent volume, absent SDK profile, picker conflict,
release request and wrong project cache. Aggregate output digest matches the
known-clean owned result. These host gates precede the partial Android result
below. Existing A/#117/#119,
real-model/cache/runtime, physical-phone/ARM64/16 KiB, power-loss and
privacy/quality gates remain.

## Frozen guest-input review

All 1,418 final source snapshot files, 16,705,626 bytes, independently match
source commit `4b6c2db48c342b13b2c6b9e6cc8e599eab003dc2`, index SHA-256
`9a1cefc913f9419b9a1bf05c7c9c3e7d9c9e6a37588cf5228f70e8f9df2149d2`.
App source since the compiled integration differs only in README documentation.
The final controller carries the actual audited APK hashes and the corrected
180/165-second budgets.

The guest proposal was separately reviewed while disabled; its SHA-256 is
`8f5504473d9ae244f5967027d2dec1185479f8d4a7119c64463349635a624614`.
All 46 input bindings, 86,046,985 bytes, independently match, including the
actual APP/TEST pair and receipt build/audit evidence. The reviewer opened the
read-only live environment lease and checked its descriptor, exact tool/path
linkage and finite deadline; boot was explicitly unverified at that admission
review. The evidence parent then contained only proposal/admission metadata,
with cohort/start/result names unused and authorization absent. No SDK executable, ADB or guest
command was invoked by the reviewer. No remaining concrete controller/input
blocker was found, subject to ordinary-build exclusion and build-quiet gates.
Those host gates subsequently passed before the separately authorized guest
attempt recorded below.

## First retained guest attempt

The coordinator confirmed the original guest execution consumed a nonzero tool
terminal (one); the owned worker result is separately completed two, known-clean
in 65,734 ms, outer stderr zero. Its 345-byte stdout SHA-256 is
`579d700003ef2b99b9de7d158235675dce653a6eac14a0e69717ef2c4ce7e5cf`.
The retained controller result is stopped after its initial instrumentation.
Independent replay of all 36 client records
matches their stdout sizes/hashes and completed-zero cleanup metadata. The
strict original transcript parses exactly three passes and zero failures for
import/recheck, cancellation on both sides of acceptance, and disposed blocked
source drain. Empty-to-two-package inventory and pinned installed identities
passed; installed userdata availability was 11,273,560,064 bytes.

The stop is a concrete controller quiet-gate refusal. Its post-instrumentation
process list contains the known TEST main process and no APP target process;
the frozen `facts()` requires both sets empty. That observation does not make
the three test passes failures and does not establish separate-process reopen.
No proof-read commands or restart instrumentation were dispatched. A separate
continuation was considered but not implemented, tested or admitted before the
remaining owner deadline. The coordinator requested the exact admitted stop.
The necessary future restart
precondition is actual APP-process absence plus current pinned identities; any
allowance for the known TEST helper must be exact, source-bound and independently
admitted rather than retroactively relaxing this stopped run.

## Closed evidence and remaining gate

The coordinator confirmed the original environment owner consumed tool terminal
zero after the stop request. The retained owner result is `stop_requested`,
cleanup complete and closure verified, 920,000 ms, with worker return one from
the owned drain. The separately recorded process/port closure says all three
original process identities are absent and the reserved ports are free. This
is owned process cleanup, not a graceful guest flush. Virtual-disk rows record
sizes only; no final disk integrity or unchanged-content claim follows.

The reviewer independently rehashed every entry in these final immutable
inventories with zero mismatches:

| Inventory | Files | Bytes | Index SHA-256 |
| --- | ---: | ---: | --- |
| Host | 1,570 | 197,304,811 | `64c1267450678c0fdd161ee318fa005c1b714939f1022917b2a03d644b9b7cb9` |
| Environment | 23 | 561,229 | `55fb2c86480db40f4612c526deac066ff85ec826438410a44e59fe9501529115` |
| Stopped guest | 129 | 86,124,753 | `a8a7faad8d2e82cb73baa73def32a7f483b4e31c21c9d14fc1453ab363ac050c` |

The guest inventory archives all 46 originally admitted inputs; later public
documentation edits do not alter those source/APK bindings. No additional guest
operations, tests or continuation were run during closure.

Completed within this slice: explicit debug receipt access/runtime admission,
typed capacity refusal, default-profile exclusion, host checks and the three
initial synthetic setup methods. Blocked/incomplete within M05.05: the remaining
separate-process reopen invocation, host parsing of all eight proof records and
final four-method qualification. M01.05 gains no real-model/runtime result.

The next runnable task is a focused controller correction with original APP
absence and exact known TEST-helper classification kept distinct, meaningful
refusal tests, and another fresh isolated target under a separately reviewed
admission. Do not repeat initial actions on this saved target or reinterpret
its stopped result. Successful tiny import is not permission or evidence for
real weights, SDK construction, cache growth, physical media or a default route.
Existing A/#117/#119 and reference-phone, ARM64/16 KiB, capacity, privacy,
power-loss and model-quality gates remain unchanged.
