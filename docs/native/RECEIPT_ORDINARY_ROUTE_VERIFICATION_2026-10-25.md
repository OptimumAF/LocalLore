# Ordinary setup, local gift and blocked Dialogue — 2026-10-25

Refs #9 (M05.05), #5 (M01.05), #10 (bounded M06.06 support).
[PR168](https://github.com/OptimumAF/LocalLore/pull/168) is stacked on unmerged
[PR167](https://github.com/OptimumAF/LocalLore/pull/167). Root claim6398062716;
author claims6398119552/6398122022; independent review6398092446.
All full tasks remain partial/in_review and unchecked pending their complete
acceptance criteria and owner acceptance. No merge, release or access change.

Execution source `edf2ce1ab8ab86a09057f42f7ae32349e4d3dca0` is frozen across the
actual attempt. Receipt Android compilation is
`37507f487e18e35bb41732869ae0b94b3fdc591c`; regular compilation is
`d5c2361a12a6b8b919b84720dd31f34eead13abf`. All216 tracked Android source rows
are byte-identical at execution. Later verification/review changes are documents
only. Read the [closed protocol](RECEIPT_ORDINARY_ROUTE_PROTOCOL.md).

## Actual outcome

**56 checks qualify: source preflight12, full import16, ordinary Start/gift28.**
The actual ordinary setup controller verifies the accepted local model on IO;
its READY screen and enabled Start button launch exact `LiteRtPlayActivity` and
finish setup. Its existing ShellViewModel, native transport and real local
provider commit one gift at revision1/receipt1, repairs0/fallbackfalse. The test
visibly checks accepted transcript bodies by stable message ID, potion ownership
and revision before finishing the actual activity. Native handle invalidation,
retained candidate reservation, full model postcheck, borrowable-owner guards
and a refreshed known-close worker trace pass. This removes the private activity
subclass used by the earlier Compose control from this actual entry-route proof.

| Selected phase | Result | Qualified checks | Observed time |
| --- | --- | ---: | ---: |
| SOURCE_PREFLIGHT |1PASS|12|198ms proof|
| IMPORT |1PASS|16|94338ms proof|
| ORDINARY_START |1PASS|28|80930ms proof|
| ORDINARY_DIALOGUE |1FAIL|0 of43|35.764s JUnit whole method|
| ORDINARY_REOPEN |UNRUN|0 of23|None|

The planned122 checks/five methods did **not** all pass. Four methods were
selected: three pass and one fails. None is skipped. Whole-method/proof times
include setup, model checks, Compose synchronization and teardown; they are not
generation latency, cancellation latency or phone performance measurements.

The raw failure stack reaches `ReceiptOrdinaryRouteTest.kt:452`, the `settled`
check after actual Dialogue Send. The preceding source path completes player
inspector browsing, Event#1 navigation, both hidden NPC seed-belief searches,
undiscovered beacon search, unchanged canonical snapshots, unlearned blink and
duplicate-potion refusals, and an in-memory zero-worker guard check. **No final
43-check Dialogue proof or guards sidecar was published.** Reaching that line
does not substitute for a completed phase, persist the individual flags, prove
an NPC answer, or qualify model prompt resistance. The player legitimately knows
SECRET-TIDE-731 in this seed; its positive display is required. No NPC or
omniscient inspection grant was added.

No Dialogue receipt, revision2, changed truth set, post-failure canonical state
or ordinary-route restart is claimed. The earlier separately verified gift/reopen
and cancellation controls remain dated evidence in PR164/165/167, not evidence
that this new ordinary-route REOPEN ran.

## What the failed send observation establishes

The v2 failure trace is bounded metadata, with no prompt, schema, model prose,
path or exception text. It has no saturation:

- One DIRECTOR conversation creation enters16973ms and returns18694ms.
- SEND_ADMISSION returns19082ms; SEND_ENTERED is19082ms, SEND_RETURNED is absent.
- No message, DONE, ERROR, cancel, drain or known conversation/engine close is
  observed. UNCERTAIN count2 has last19092ms; snapshot is19112ms.
- The same inner `failedStart` and outer `unknown` catch can account for two
  uncertainty notifications. They are not two independently observed SDK errors.

`OwnedEngine.start` records SEND_ENTERED before the adapter's `conversation.send`.
Inside that wrapper, `ResponseFormat.json(request.schemaJson)` and other call
arguments are evaluated before `sendMessageAsync` is invoked. The catch discards
every Throwable and replaces it with LocalInferenceUncertain. Consequently this
trace cannot distinguish argument construction failure from a synchronous SDK
invocation failure, prove async SDK entry, identify a schema incompatibility,
or establish cancellation as the cause. The35.764s failed method is below the
separate120s runner gate; no deadline expansion would explain or fix this result.

The next runnable gate is a fixed, closed observation around argument/response
format construction and actual async-call enter/return/throw. Preserve the same
failure fence/quarantine ordering,60s turn,5s cleanup, no owner reuse or close
bypass. Keep raw Throwable/class/stack/cause, schema and prompt out of diagnostics.
Test argument-construction throw with SDK-call count0, synchronous call throw,
callback error versus synchronous throw, and diagnostic failure leaving quarantine
unchanged. A new implementation/admission is needed before another SDK attempt;
there was no retry in this emulator or against this frozen proposal.

## Implementation and host checks

MainActivity exposes a weak observation of the transport its existing factory
constructed. A retained-ViewModel recreation may return null; the test refuses
null and never makes a replacement owner. Capture occurs on Main after the exact
activity is RESUMED. The returned transport is command-capable, not an enforced
read-only capability; this fixture uses only fixed resume/play_snapshot commands,
with borrowability checks before/after inspection. It never directly closes the
transport or replaces production New story/Send/commit/cancel behavior.

CandidateLocalModel exposes immutable bounded worker snapshots only in the explicit
receipt build. No setter/reset/callback/config injection is added. Missing trace
is a failure, not zero-SDK evidence. Teardown finishes the actual activity and
checks its real lifecycle/native owner. The regular profile excludes the proof
implementation and all test classes; exact APK audit boundaries enforce this.

Actual checks, in finite owned processes:

- `python -B -E -m unittest discover -s scripts/tests -p test_audit_apk.py -v`:
  **25PASS**. The first focused controller run has15PASS/1FAIL because its mocked
  empty process listing omitted the real mandatory `PID UID NAME` header. Only
  that test oracle was corrected; a helper bind/retire/reappear refusal was also
  exercised. Final focused controller **16PASS/2.459s**, known cleanup2859ms;
  exact handoff is [comment6398224294](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6398224294).
- `python -B -E -m unittest discover -s scripts/tests -v`: **774PASS/82.141s**
  after final APK pins, zero failures/errors/skips. Owned83203ms, stdout91602B,
  SHA256 `45ce25a9fd7de158ec228819956905725052de3858a57cacb6998faf871efee2`.
  The earlier pre-pin774PASS/80.429s run is retained too.
- Both Gradle profiles run assembleDebug/assembleDebugAndroidTest,
  cleanTestDebugUnitTest/testDebugUnitTest, lintDebug, auditLiteRtDependencies
  and auditLintAnalyzer. Offline/no-daemon/max-workers2, SDK auto-downloadfalse,
  Java toolchain auto-downloadfalse, Kotlin incrementalfalse, lint9.4.1,
  fixed local JBR/JDK21. Receipt includes LiteRT/setup/volume/receipt verification;
  regular includes LiteRT/setup only. **435 receipt JVM/41 suites**, including12
  new proof tests; **377 regular JVM/36 suites**. Zero failures/errors/skips.
  Lint0errors,19/9warnings. Owned builds152594/135093ms, both completed0 with
  known cleanup. No Rust/core/storage implementation changed.
- Actual `scripts/audit_apk.py` with the exact profile flags, and APP/TEST
  `apksigner verify --verbose` for both profiles: all6 completed0/known cleanup.
  Receipt markers cannot leak into regular APP; tests cannot leak into APP.
  `git diff --check` passes.

Two preliminary build-helper calls supplied `HEAD` and an abbreviated source
identifier instead of the required full SHA. Both refused at exact-source
equality before output-directory creation or a build; the full SHA was then used.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Receipt APP |75020368|`caf967a0b8ff7daa0775409bb5b7994194ffb1bff36685e55b6b5eb0dff18797`|
| Receipt TEST |2056171|`31acce94c98f7c9b59f1beca0764cac0324cb9e759f6a7bf7fdc9f060f5d0043`|
| Regular APP |74954584|`751c18fc231206bcd646b51a400a8d53a97dc8f82cb7420fb04ea44daf86a155`|
| Regular TEST |1869667|`e0d327dad0a75257b9427f914b2300f43107d1076997aa6c000ae174b792d3d6`|

## Frozen environment, consent and execution

Existing explicit human authorization permits a local copy into the fresh receipt
test package. No download, external model upload or private diagnostic upload
occurred. Exact unchanged candidate: LiteRT-LM0.18.1/revision
`bda624851d74be34d4e1f7fac1fc4155939539c7`, Gemma4-E2B publisher revision
`a790a852d433991c0c0a41c1154cf9b3850300fa`, model2588147712B/SHA256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`, worker
`271d6af5ac1f946b0cd245ac35f7ba5910a097ec49bebe1776448ff4b7885eec`.
No dependency, runtime/model version, profile/token/schema rule or supported
production backend was selected or changed by this packet.

Fresh isolated emulator35.3.12/build12990079, Android15/API35 Google APIs x86_64
image9,4096-byte pages,8192MiB/four vCPUs,12G userdata/8GiB SD. Actual guest
CPU count4 is recorded. Host20 logical CPUs; unchanged40GiB free floors on C/D
and12GiB host available memory. Guest phase admission retains its4GiB available
memory and internal/external storage floors. No old target, cache or disk was
removed. SDK/model/cache bytes are excluded from generic snapshots/inventories.

Root fully checks909 stock bindings and the initial blank SD before launch.
Independent review rehashes905 non-image contents and checks four SDK images
and the initial SD by metadata/size only, not a second image-content claim.
The frozen1554 source files total19100075B; all matched the then-current source
and snapshot at admission/execution. After the documents-only report edits,
independent review rehashed all996 non-Markdown rows/13289118B with0 mismatches.
Both105 preflight and109 candidate current/archive bindings are independently
rechecked (87264306/87270547B); neither generically binds model weights.

| Exact proposal | SHA256 |
| --- | --- |
| PREPARE |`72cc6210c4137351f37f2bf8f7147bf42839858ecb927d15e6319abb694930aa`|
| RUN |`7f9d66db641cc2d9904212f54ff5c574c3ae1db129a6438098a5e3397af3ec56`|
| Source preflight |`f66cfd6d3f83b4a5dd1e3d43a273c277341d837c359453898a2d3e962d203de7`|
| Ordinary candidate |`3b0c7a040816ab41ef09035c62eeb9baf447e912c371517c744755a7ce3fd212`|
| Running descriptor |`b2d0beb9f1d79e5d3c65af347cb83f412e2839d249e4b063b056418b3e5b6f13`|

Actual repository entry points are `receipt_avd_environment.py prepare/run`,
`receipt_real_candidate.py run` for preflight, then `receipt_ordinary_scene.py run`
with their exact proposal/authorization/evidence arguments. Each is behind an
assigned Windows Job and stdin barrier. Local create-only preparation, collection,
audit, grant, stop and sealing helpers are retained outside the repository with
the `LocalLore-receipt-ordinary-scene-*-20261025.py` prefix. No timeout or quiet
output caused a second dispatch. Fixed source selectors and private proof paths
remain in the protocol/controller; no caller-supplied script, class or phase list.

Budgets remain P30/I150/START170/DIALOGUE170/REOPEN120 seconds, transfer180,
aggregate870/outer900/entry920, emulator owner1800. The separate selected JUnit
runner Time<=120s gate remains. The nominal790s sum is not a guaranteed completion
bound; overhead clips remaining work, not an excuse to expand caps.

## Proofs, ownership closure and preservation

| Artifact | SHA256 |
| --- | --- |
| Preflight raw |`689d876b241f8bee995fd338c915d6c9c02c815d366571a39abc01a8940bd027`|
| Import raw |`bf005fc82f71b602a5a6584b3f884d618b6d4b1135182cf5aad5a5e23781dca2`|
| Start raw |`188d88670773f87783cd96bf5307ffb707a7316ccedc3e05e0b1427979bef27b`|
| Start worker raw |`1fcfe5200b3432e54c1212fdf0d004ed278e31e02cb12f4a9eca78ac14bd440b`|
| Gift receipt |`4aabf29e6d3eb12b1eb0b2bf56c27ef64c71b7494bb1e9f677103accf0171304`|
| Failed Dialogue JUnit raw |`bff70fa2b5ce00c6b1fb0f6272efbcb3498c5fbc989b45c691f44c7d606ca4d3`|
| Parsed failure-worker sidecar |`6576ed565d872afb9e1bb95b6f1fc32a1e2da6ff54cc91cbb8dbe69c117d005e`|

Preflight original driver is terminal0, child0/known cleanup/capture,41266ms.
Its44 closed clients pass. Candidate original driver is terminal1, child2,
known cleanup/capture,347172ms,466B stdout/stderr0. Import and Start pass; final
client46 is the failed Dialogue JUnit command (5365B retained stdout), completed0
at the shell boundary with known cleanup. Shell0 never substitutes for JUnit PASS.

Only after consuming the candidate terminal did root request the exact emulator
owner stop. Its original entry is terminal0, stop_requested,699594ms, worker1
under forced stop, known cleanup/output capture/preservation closure. All three
tracked host identities are absent and ports free. This establishes host process
ownership closure, not hidden SDK reclamation, guest flush or virtual-disk integrity.
Model/cache/AVD disks are retained without further generic reads or hashing.

Sealed local evidence prefix: `%USERPROFILE%/LocalLore-receipt-ordinary-scene-`
plus `{host,environment,preflight,candidate}-20261025`. No writes after sealing;
17 fixed owner/config metadata files are copied after closure, excluding disks.

| Root | Files | Bytes | Inventory SHA256 |
| --- | ---: | ---: | --- |
| host |1693|174517836|`af671aa81741551fcc5690b5810d3e99bf758a2802406b0001308d94963ddf3b`|
| environment |27|390090|`033ac2f6c7615d6e91a7a3235463b83588ba11dfaf7d0249b39952f797851371`|
| preflight |212|87384286|`5f94dd3b289a11980055a7b9b8909337fa02bcd960ef94c0b049a1cb5e81d3f3`|
| candidate |226|87414512|`72669e3ee481436d935021fb1a9b46efc1c31d40ebf157001669c4b2c9d54ba3`|

Total2158 files/349706724B. The original local model and earlier sealed attempts
remain preserved. The [independent review](RECEIPT_ORDINARY_ROUTE_REVIEW_2026-10-25.md)
records its own rehash and limits; technical review is not owner acceptance.

Physical reference phone, ARM64 execution/16KiB pages, ordinary-route Dialogue
and reopen, NPC reply/secrecy/prompt resistance, DocumentsUI/physical touch/IME,
sustained/thermal/quality/latency and broader pressure/privacy/cache gates remain
unqualified. The M05 and M06 full exit gates have not passed.
