# Fixed physical-phone host qualification

Supporting M01.05/M05.05; root issue #5 claim6406310135, refining6406017018.
This source is an experiment controller, not device acceptance or a selected
production backend. No physical observation, copy, import or SDK result is
implied by its mocked host tests. The coordinator owns actual discovery,
build/audit hashes, source admission, grants and execution. Never merge or
publish through this controller.

## Fixed identities and source

The only new packages are `org.locallore.app.phoneverify` and its `.test`.
Existing LocalLore package APK hashes and UIDs are preserved exactly, including
the already installed `.modelverify` pair. No replace install, uninstall,
clear, app-data cleanup, ADB lifecycle, emulator action, settings change or
fallback device is implemented. Only the new pair may receive a force-stop,
and only between known passed phase proofs. After uncertainty there are no
further guest calls, including cleanup or final queries. Host evidence output
may still record the refusal.

An existing private identity file supplies the previously selected USB serial.
`discover` looks for that exact USB row in `devices -l`; it never chooses a
different phone or TCP target. An absent selection makes zero target calls.
It reports absence rather than substituting an emulator. The current row pins
its transport ID, USB identity and product/model/device metadata. All target
calls use that transport ID, not serial fallback.

The existing loopback ADB server is observed through a fixed PowerShell query.
PID, process creation time, executable, listener ownership and pinned ADB bytes
must agree before and after target clients. No start/kill/reconnect command is
issued. External races or server disappearance refuse the run; a precheck is
not a reservation against external changes. Environment ADB-server overrides
are refused by the CLI. Private serial, transport, process and UID metadata
stay in private evidence, not public reports.

The pinned model remains2,588,147,712 bytes / SHA256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
The original precheck fixture is65 bytes / SHA256
`72e34de83e7311b37f7a17361f3d71555209ffbfe4eb9e861cc11c7903e13422`.
Its exact bytes are in `benchmarks/fixtures/physical_model_probe_v1.txt`.
The29-byte owner marker is `locallore-physical-source-v1` followed by LF,
SHA256 `6e58105a6f97416ed0727594cfaadac7326bece25e03c4305ab70fc964790b5e`.
The fixed app-relative roots are `no_backup/physical-model-source-v1` and
`no_backup/physical-model-proof-v1`; the app independently resolves its actual
Context roots and proves ownership and same filesystem. No removable volume
or emulator lease is fabricated.

`APK_HASHES` is intentionally empty until the coordinator integrates real
audited hashes into the source. Runtime construction and proposal validation
refuse while it is empty. Tiny synthetic APKs/hashes used by unit mocks do not
qualify Android artifacts. The source closure explicitly binds the host parser,
policy, proof codec, Android fixture, shared worker/proof helpers, test sources
and protocol. A grant cannot supply alternate selectors or a transport script.

## Proposal and grant

The proposal has exactly `version`, `scope`, `phase`, `identity_path`,
`identity_sha256`, `discovery_path`, `discovery_sha256`, `adb_sha256`,
`powershell_sha256`, `apk_paths`, `bindings`, `source`, `prior`, `evidence_root`.
Scope is `physical_model_probe_v1`; phase is `precheck` or `model`.
Source is exactly a path/bytes/SHA256 record for the fixed fixture or model.
Bindings associate absolute source/artifact paths with expected SHA256 values;
required source paths are source constants. Full model bytes are never loaded
as one Python object or included in bindings/output. The model source is
authenticated through the granted, held descriptor immediately before transfer.

The separate authorization has exactly `version`, `proposal_sha256`,
`allow_device_calls`, `allow_new_install`, `allow_model_copy`, `allow_sdk`,
`root_go_pending`. Version is integer1; flags have exact Boolean types.
Device calls are true and pending is false. Precheck permits new installation
and forbids weights/SDK. Model permits weights/SDK and forbids installations.
The bound evidence directory and all output files are create-only.

Model admission additionally binds the exact prior precheck raw proof, final
facts and completed result by path/SHA. The precheck result must have one
actual method, two attempted new installs, known cleanup, an exact proof hash
and completed phase boundary. A boolean completion count cannot qualify.
Private source/discovery records must never be copied into GitHub comments.

## Gates, staging and ownership

The pure physical contract fixes the observed Samsung/API36/ARM64/4KiB profile,
10–12GiB total and initial available memory at least4GiB, USB power, battery,
thermal and fresh same-filesystem capacity. A fresh sample needs
`2 * 2588147712 + 2147483648 = 7323779072` bytes, plus incoming APK bytes before
installation. Missing fields are refused, never treated as zero or success.
After source/import the host checks remaining missing bytes plus the same2GiB
reserve, without double counting external/userdata aliases. Post-SDK snapshots
can have lower available memory; initial phase admission still requires4GiB.
The app separately proves `lowMemory=false`, Context roots and receipt guards.
These observations are neither reservations nor allocation/performance promises.

Precheck has a165s aggregate/180s outer owner. Model has1170s aggregate/1200s
outer. Every actual client is clipped to remaining aggregate time. Weight
staging has a240s parent; the child remains `min(150,parent-left-5)` seconds.
The existing Job supervisor owns the worker and descendants before the stdin
barrier is released. No generic supervisor/SDK/generation deadline is changed.
Nominal phase budgets plus staging and metadata must fit; deadlines do not
guarantee worst-case completion. There is no retry on exhaustion or refusal.

The stream worker revalidates the grant and exact parent process creation,
one-shot parent/facts hashes, current server/transport/fingerprint and pinned
source metadata. It hashes through a held unbuffered descriptor in at most1MiB
blocks, bounds the read to expected length, rewinds, and passes that same FD
directly to fixed binary `exec-in` stdin. Pre/post path and FD identity agree.
No shell transport fallback is allowed. Client zero and full host cursor are
never destination/import authority: the six-field summary explicitly says
remote exit is unknown and destination unverified. The actual IMPORT proof
must independently read and hash the whole staged source, perform the receipt
transaction, close sources and full-recheck the accepted model before SDK.

All raw client output is forced before parsing; metadata records size/SHA,
return state, stderr count and cleanup. A thrown client, nonzero return,
unknown cleanup/capture, identity drift, parse failure or evidence write failure
poisons the run permanently. No `CLEAN=True` reset or `pidof || true` is used.
Process absence uses bounded strict PS rows and exact package UIDs. Only a known
passed phase permits stopping the new pair and checking that neither remains.
The original app data/model/saves and failed source/receipt roots are retained.

## Six fixed phases

Each row is one exact FQN in `org.locallore.app`; wildcard, all-tests and
caller-selected method execution are absent.

| Phase | Class | Method | App budget ms |
|---|---|---|---:|
| PRECHECK | PhysicalModelPreflightTest | verifiesPrivatePhoneSourceBeforeCopy |30000|
| IMPORT | PhysicalModelImportTest | importsFixedPhoneCandidate |150000|
| CANCEL | PhysicalModelCancellationTest | cancelsAndJoinsWithoutCommit |170000|
| GIFT | PhysicalModelGiftTest | commitsGuardedPhoneGift |170000|
| DIALOGUE | PhysicalModelDialogueTest | recordsLiteralPhoneDialogue |170000|
| REOPEN | PhysicalModelReopenTest | reopensPhoneReceiptsWithoutInference |120000|

Precheck stages only the original fixture. A new model grant then runs IMPORT,
CANCEL at revision0/zero receipts, GIFT at revision1/one receipt, DIALOGUE at
revision2/two receipts and REOPEN with those same two receipts/source unopened/
SDK false. All later phases have distinct PID/start process instances and
exact prior proof/process hashes. Story identity is a hash, never a raw story ID.
Gift and Dialogue require zero repairs/fallback. Literal statements remain
statements, not world truth. The Rust engine remains canonical authority.

Closed proof/check sets are defined by `PhysicalModelProof.kt` and mirrored
exactly by the host:13/17/18/15/16/13 checks. Each phase adds its proof JSON and
empty ready marker; the positive whitelist grows only by those files and fixed
trace sidecars. CANCEL uses `cancel-sample-worker-v2.json` and
`cancel-worker-v2.json`; GIFT uses `gift-worker-v2.json`; DIALOGUE uses
`guards-worker-v2.json` and `dialogue-worker-v2.json`; REOPEN uses
`reopen-worker-v2.json`. All sidecar bytes are SHA-bound in the proof, including
`guards_trace_sha256` and `sample_trace_sha256`. The retained return/close
metadata predicates come from the existing cancellation controller; they are
not native lifecycle authority. Actual original response join/no commit and
known ownership are mandatory app checks, not inferred from cancel ACK alone.
Reopen and invalid-action guards require exact zero worker records, not an
absent record interpreted as zero.

Failure status channels remain independent passive observations. They persist
before the unchanged strict runner gate and cannot qualify a failed method or
authorize the next phase. JUnit exit zero alone is insufficient. The new family
does not rewrite emulator selectors, APK identity or proof grammar.

## Host verification and remaining gates

Run the sole targeted unit module through an owned bounded Python child:
`python -I -S -B` with `unittest` loading
`scripts.tests.test_physical_model_probe`. Both client and supervisor seams,
OS process identity and all hardware operations are mocked by default. Tests
use original tiny files and model-size metadata, never actual weights. Retain
failed test attempts and fix the actual issue before reporting a pass.

The author's final targeted run passed26 methods in0.689s, owned1075ms,
child0/known Job cleanup/zero stderr;5439B retained stdout SHA256
`fc9b73fd4e68be975cdd9423e4348de3802da36dd94c533cf9617ddd9f9816d9`.
Source hashes matched before/after. The first21-case run had one test-oracle
error (it inspected the supervisor callback argument instead of its seconds
argument); original output is retained. The corrected24-case run passed; the
25/26-case runs added parent/source closure, legacy-UID aliases and refusal of
relative APK/evidence paths that might become a command-option surface.
These are mocked host tests, not Android or physical model results.

Root still must build/audit the new physical profile, pin exact APK bytes,
check actual current phone presence and resources, review/admit the proposal,
run the precheck and separately admit weights/SDK. No phone result, native
resource reclamation, thermal/memory high-water mark, prose quality, DocumentsUI,
16KiB-device or production-backend acceptance follows from these host tests.
