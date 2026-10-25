# Fresh real-candidate receipt experiment

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). This is an opt-in debug
probe of the existing fixed Gemma/LiteRT worker through production receipt
access, setup, Rust transport and guarded free-text gateway. It selects no
production backend, phone profile or new dependency. The older caches and
A/#117/#119 holds remain untouched.

Use the existing receipt build and separately admitted fresh environment with
`plan-prepare --real-model-candidate`:8 GiB RAM,12 GiB userdata,8 GiB removable
SD,2 virtual CPUs and12 GiB host available-memory floor. The old2 GiB/4 GiB
synthetic profile stays unchanged. Observe actual7–8 GiB guest total and at
least4 GiB available before each phase; this is admission, not a fit benchmark.

The separately explicit `--real-model-candidate --four-core-candidate` profile
uses4 guest vCPUs with the same RAM/disks/floors/deadlines. It requires at least8
reported logical host CPUs, rechecked before owned SDK launch. It is a resource
experiment matching the existing four inference threads, not an accepted device
tier or a latency fix. See [closed profile](RECEIPT_FOUR_CORE_PROFILE.md).
After boot, before install or model copy, the four-core controller makes one
bounded `cat /sys/devices/system/cpu/online` observation, requiring exactly
`0-3` plus a line ending. It retains the ordinary owned client record and a
closed three-integer `guest-cpu-profile-v1.json`; mismatch, unknown cleanup,
owner loss or failed retention stops before copy/inference. The existing two-core
profiles issue no additional guest command. No such probe runs after SDK uncertainty.

## Separate preflight and candidate authority

Runner summaries are checked against the existing fixed app-phase budget:
SOURCE_PREFLIGHT30000ms, IMPORT150000ms, PLAY170000ms and REOPEN120000ms.
The trusted selector supplies that phase's constant to the shared framing
parser; there is no caller-selected deadline or CLI override. The shared
synthetic parser retains its120000ms default. A134.086-second passing IMPORT
runner exposed the old inherited120-second cap; the original stopped attempt
remains documented in [finite SDK verification](LLGUIDANCE_LITERAL_VERIFICATION_2026-10-25.md).
Corrected parsing does not retroactively fetch or qualify its unread proof.
App-phase,180-second client, aggregate and live-lease limits remain distinct
and unchanged. Passing runner framing never substitutes for the app proof,
exact source/artifact links, ownership or known cleanup.

`benchmarks/receipt_real_candidate.py` requires a closed disabled proposal and
exact separate grant. The preflight grants device calls only, explicitly false
for weight copy and SDK calls. It admits two fresh installs, a fixed private
source directory/owner, one original61-byte probe stream and one exact source
preflight test. The probe is `benchmarks/fixtures/receipt_real_source_probe_v1.txt`,
SHA-256 `a4ab41067238a10078cec646fcf00a952c1c58511661d5d8dc4632b37ea017af`.
Context-derived source is `no_backup/receipt-real-source-v1`, with exact
`source.owner` bytes `locallore-real-source-v1\n`, then `probe.txt` and later
`model.litertlm`. No Intent or CLI selects these names or a provider.

A candidate grant is separate: it binds the successful preflight result,
known-clean outer result, exact installed facts, raw source proof, same live
environment descriptor and new destination-specific human consent. The older
consent for two runtime-benchmark installations does not authorize this new
receipt-package destination. Complete build, fresh target, measured capacity
and tiny staging evidence before requesting that final copy approval.

The fixed model is2,588,147,712 bytes,SHA-256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
Candidate scope requires both local-weight-copy and SDK flags true; preflight
requires both false. Model bytes are never part of a generic `read_bytes`
binding/archive, public log or Git artifact. Proposal validation checks source
shape/path/size; the authorized transfer hashes the held source FD before use.

## Local staging boundary

A barrier worker is assigned to the existing Windows Job before it can open
the transfer child. It validates the frozen grant/live lease, exact live
controller process/start, bound fresh installed/capacity facts and deadline,
then exclusively claims its one transfer. Replay/direct worker invocation
without that live parent record refuses. The child inherits the job and reads
only the held, fully hashed source FD into a fixed local-server
`adb exec-in run-as` command, with output discarded. Source identity/size/mtime
are rechecked afterward. No giant byte array, download or shell-temp duplicate.
An unknown cleanup/persistence result stops dispatch and preserves staging.

ADB raw `exec-in` returns client status, not remote shell exit status. Therefore
client0 is **transfer-only**, with remote exit unknown and destination unverified.
The app-domain test must independently reject missing/partial/foreign/symlinked
source and verify exact bytes/hash before receipt import. Fixed source creation
and no-clobber writes never overwrite, rename, adopt or clean old files.

Internal space before copying must retain the unchanged userdata floor plus
one full source copy; the external receipt route independently requires
model bytes plus its unchanged2 GiB floor,4,735,631,360 bytes pre-import.
Source and accepted receipt copies remain retained. Cache peak growth and
external-cache privacy are still unqualified; no reserve is silently reduced.

## Four fixed phases and proofs

Each receipt-only test has an exact class-selection assumption guard. Only the
declared FQN runs; default discovery and suffix/comma selections skip. No skip
can satisfy this controller. One ordinary instrumentation per phase:

| Phase | Class / method | Absolute test observation cap |
|---|---|---:|
| SOURCE_PREFLIGHT | ReceiptRealSourcePreflightTest.verifiesTrustedSourceBeforeModelCopy |30s|
| IMPORT | ReceiptRealImportTest.importsFixedRealCandidateThroughProductionSetup |150s|
| PLAY | ReceiptRealPlayTest.commitsOneGuardedRealSdkGift |170s|
| REOPEN | ReceiptRealReopenTest.reopensReceiptAndGiftAfterProcessRestart |120s|

The source preflight validates trusted roots/UIDs, owner/probe/whitelist, absent
real candidate and real model, actual memory and copy/import capacity. It reads
no model and opens no Activity or SDK. IMPORT independently full-hashes the
staged source, then opens the actual production setup screen/controller and
uses the fixed source callback. Verification and import each open/close once
and consume exactly the model byte count. This does not qualify DocumentsUI.
Its real-file observation cap does not modify the synthetic ten-second wait.

PLAY fully reopens the actual receipt in that fresh process, establishing that
instance's runtime stamp before production transport attachment. One fixed
free-text gift passes through the real default SDK and Rust validation. Only
Prepared establishes the existing public terminal/drain/returned-close contract;
there are no invented SDK/JNI teardown counters. Fully verify the accepted
model again after the SDK and BEFORE commit. A mismatch stops without commit;
uncertain SDK ownership stops without forcing a read. Preserve state, do not
retry or substitute a provider. Successful commit must record one authoritative
Given(player,potion,mira,1), revision1 and one exact local-profile receipt.
Record actual repairs/fallback; this is not prose-quality acceptance.

REOPEN fully verifies the receipt and canonical gift in a separate ordinary
process with changed PID/start linked to PLAY. It never resolves the staged
source, submits free text or initializes an SDK. Receipt hashing uses sorted-key
canonical JSON. Native InvalidHandle after closing the borrowed same handle
establishes native lease invalidation, not hidden SDK resource reclamation.

Create-only regular/NOFOLLOW proofs live under `no_backup/receipt-real-proof-v1`:
`source-preflight`, `import`, `play`, `reopen`, each `-v1.json` plus an empty
`-ready-v1.txt`. JSON is capped4096 bytes. Exact closed checks count12/16/15/13,
**56 total**. Common model identity is expected in preflight, not a verified
model claim. Model-source counters are zero outside IMPORT; probe reads are
separate. PID/start is independently observed per phase, not assumed constant.
Prior-proof hashes link each phase and canonical receipt hashes link reopen.

The ordinary setup parser keeps its original allowed classes. This new
controller shares its strict framing only behind the four fixed selectors.
Raw output precedes parsing; any failed/skipped/unknown runner stops before
further generation. Saved facts distinguish mandatory APP absence from at most
the pinned distinct-UID TEST helper. If the no-UI preflight and continued-before
observations have no helper, permit one first binding only after exact IMPORT
PASS and its linked proof; this is the first UI phase. An absent row there
closes that opportunity. A preexisting row cannot be replaced. Natural helper disappearance revokes it;
new/reappearing helpers refuse. This grants no file/runtime authority or claim
of continuous helper liveness/unobserved PID reuse detection.

The preflight aggregate remains165s/outer180s. The separate candidate aggregate
is870s/outer900s through the already tested durable-output supervisor; each
client remains at most180s. Production context4096, director350/narrator220,
one repair, turn60s and cleanup5s remain unchanged. File guards are unmeasured
observation bounds and can fail safely; they do not promise model feasibility.
The explicit8 GiB profile now defaults to a bounded1,800s emulator owner;
the default2 GiB profile retains1,200s. Full input verification, boot, preflight
and admissions consumed296.4s in an actual authorized attempt, leaving too
little of the old envelope for the unchanged900s candidate plus20s margin.
This scheduling correction changes no inference/phase budget or entry gate.
It applies only through a new source admission and fresh target; an existing
owner's deadline cannot be extended. See the authorized execution report.
The exact owned emulator stop/terminal/cleanup/capture/preservation closure is
required separately. Retain all targets/attempts, without guest-flush or
power-loss integrity claims. Full physical-phone, ARM64/16 KiB, sustained,
quality, cache/privacy, DocumentsUI and milestone acceptance remain open.

## Passive worker failure observations

The exact PLAY fixture may attach the final, in-memory
[closed worker trace](LITERT_WORKER_TRACE_V2_CONTRACT.md) to the same production
candidate owner. It does not replace resources, supply generated output or alter
any limit. If `respondText` throws or its existing Prepared assertion fails,
before the existing catch/finally cleanup it
attempts one bounded `locallore_receipt_worker_v2` status1337 record per process.
Successful calls emit none. Snapshot or delivery failure cannot replace the
identical original throwable. No extra SDK, model-file or transport call is made
to obtain the snapshot; no path, prompt, response or exception text is serialized.

The controller demultiplexes this worker channel only for PLAY. Other phases
retain the separate setup-failure channel and forbid worker records. A worker
record is retained before the unchanged strict runner gate; it cannot explain
away a failed, skipped or malformed runner, replace a proof, qualify resource
reclamation or permit REOPEN. Returned/settled/known counts are historical
observations at the specified Kotlin points, not independent JNI completion,
caller-delivery or current-ownership evidence. Missing counters never authorize
retry; the existing owner quarantine remains authoritative.

V2 adds closed DIRECTOR/NARRATOR creation ordinals and bounded monotonic offsets,
including pending/returned/closed-category failure observations. It retains the
original counters and4096-byte wire cap; v1 remains strictly readable. Timing is
relative to the trace's own creation, not wall-clock or native substep time.
Neither version can qualify a failed runner or permit a later phase.
