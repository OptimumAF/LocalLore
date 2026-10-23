# D04 runtime source and publication review

Refs #25 D04.01/.02/.04 and #9 shared M05. Review claim6357883304;
coordinator publication claim6357854167. This is an independent source review
of the runtime owner, adapter and native worker, with a publication-boundary
check. It is not execution evidence, human acceptance, a security certification
or completion of D04. The reviewer authored the earlier finite action guard;
this report does not independently approve that guard.

## Source and review method

The first reviewed runtime tree was `c6044b4`, based on shared core `e3749da`,
in the coordinator's isolated `source-runtime` checkout. The reviewer only read
that checkout. Its net change has22 new files:18 under
`crates/locallore-local-runtime/**` and `native/llama-worker/**`, three carried
historical profile/runtime reports and one new publication report. All21 carried
inputs were byte-identical Git blobs to joint integration `61e8cf1`; the new
publication report is separate evidence. No root manifest/lock, canonical engine,
storage, Android/JNI, desktop native/UI, workflow or model file changed in this
boundary. The runtime has an isolated manifest/lock and an optional dependency on
the portable engine; the engine has no reverse runtime dependency.

Actually performed here: Git status/history/net-file and byte-equivalence checks,
read-only source tracing, SHA256 of the listed public source files, and diff
whitespace checks. No build, test suite, native worker, model call, app/UI/device,
network-denial experiment or protected process/resource operation was performed.
Coordinator execution results are identified separately below.

## Concrete findings and disposition

**Startup ownership gap, substantive publication blocker in c6044b4.**
`LocalRuntime::start_cancelled` starts the child before three infallible
`std::thread::spawn` calls create its pipe owners. A thread creation failure can
panic before a `LocalRuntime` exists. Its Drop cleanup therefore cannot run;
dropping `Child` does not kill/reap it, and any previously created JoinHandle is
dropped without joining. The existing blocked-pipe tests exercise fully created
owners, not this partial construction. This was reported before publication.
Required correction: install cleanup ownership immediately after child creation,
use fallible thread creation and retain/join each successfully created thread on
every later failure. Deterministic failures at each of the three creation stages
should prove exact-child exit and no remaining pipe owner. This finding is source
demonstrated; OS thread exhaustion was not induced by the reviewer.

**Native thread-launch failure, resource-recovery defect in c6044b4.**
`main.cpp` sets `busy=true` before constructing `std::thread`. If construction
throws, the outer catch publishes `invalid_request`, while no worker exists to
clear busy. Subsequent status/unload/shutdown requests receive Busy. The Rust
owner can still kill/reap on Drop, so this cannot grant canon authority, but a
resource failure is misclassified as an input error and the same owner wedges.
Reset busy on failed launch and publish a fixed runtime failure, or terminate the
worker fail-closed. Reported separately to the coordinator; no resource-exhaustion
execution was performed here.

**Two narrower contract observations in c6044b4.** The adapter allows narrator
as its first role despite ADAPTER.md describing director, optional repair, then
narrator. The authoritative shared play path starts director, so this is an
adapter contract gap rather than a canon bypass. Also, direct `LocalRuntime::call`
checks the deadline before waiting for a reply, then checks cancellation but not
elapsed deadline on successful receipt. A reply crossing the deadline during
that wait can return success. The shared `inference::generate` already rechecks
the deadline after provider completion, protecting the authoritative play path.
These observations were handed off without claiming timing reproductions.

**Correction reviewed at `5e0f8d1`.** The coordinator allocates channels and the
pipe-thread vector before process creation, then installs a LocalRuntime cleanup
owner immediately after creation. Taking pipes and every fallible Builder::spawn
now occur under that owner; each started thread enters its preallocated vector.
Failure/unwind drops the owner, closes its writer, kills/reaps the exact child
and joins the started threads. No allocation-dependent vector growth occurs
between successful thread creation and recording its JoinHandle.

The Windows-only test injects failure at each of the three spawn stages and
retains a duplicated exact-child handle. Function return plus signaled-handle
assertions verify cleanup without enumerating unrelated processes. The native
launch helper resets busy on thrown thread construction; main reports fixed
runtime_failed. Its development-only test injects std::system_error, proves no
task ran/no thread is joinable/no busy flag remains, then proves a real recovery
launch. No production fail-switch, environment override or new wire operation
was introduced.

The adapter now refuses narrator-first before starting native work, while still
allowing the subsequent valid director/narrator sequence. Direct runtime replies
recheck elapsed deadline after parsing/cancellation before publishing success.
The deadline regression delays only at a cfg(test) parsed-terminal seam, avoiding
the scheduler-dependent callback-count approach first considered. The synthetic
fixture now matches native cancellation's no-separate-ack semantics. These source
changes address all four reported paths. No remaining substantive runtime source
blocker was found in this bounded review; executing the regression checks is
attributed to the coordinator below.

## Authority, privacy and lifecycle audit

The adapter accepts only the existing Structured inference input and fixed
reviewed profile. Its active identity includes scope, turn, revision, prompt,
schema and budget. A changed active poll cancels and poisons the provider;
identical completed polls return a cached result. A completed director may have
one changed-prompt repair with the same turn/schema, then narrator; another turn
requires a fresh provider. The one shared runtime mutex uses try_lock, so
competing owners report Busy instead of accumulating native operations.

The native boundary receives role text/schema, not an Engine, Store, database
path, event-append capability or renderer-selected command. Only the authoritative
shared pipeline can approve output. The runtime itself cannot establish observer
eligibility: callers must supply the engine-filtered context. It does not widen
that context through an inspector grant. Director/narrator calls create fresh
chat/template, context/KV, sampler and batch owners; only immutable model weights
remain loaded. The C++ main thread joins completed work before reading/resetting
the model or starting another operation. Cancellation is atomic, and per-call
RAII objects are destroyed before terminal output is published. No cross-role
conversation/KV cache was found.

The Windows owner pins ancestor directories root-to-leaf and the final ordinary
model/worker files, rejects reparse points and denies write/delete sharing. It
hashes those retained handles before launching the fixed packaged worker name.
The exact approved model size/hash must match; the worker hash records identity
rather than checking a signed package allowlist. Trusted development overrides
are feature gated. These guarantees depend on the trusted packaged worker and
Windows handle behavior; no equivalent Unix protection or cryptographic origin
attestation is established. Worker dependencies and a compromised OS/user remain
outside these file-handle guarantees.

Transport is inherited private stdio, with no shell/socket/tool API. Bounded
channels and separate pipe owners handle a worker refusing stdin. Request/reply
frames cap at32768 bytes; visible output at16384 bytes, aggregate stderr at65536,
context at4096 tokens and output at350 tokens per role. Parent reply parsing
checks exact version/request identity, fields/types, finite metrics, status/error
consistency and forbidden reasoning markers. Native parsing independently rejects
duplicate/extra fields and unsupported operations. Oversize/malformed/dead-worker
paths fail closed; generated proposals still need authoritative Rust validation.
Constrained JSON grammar is not a replacement for that validation.

The adapter owns one background generation thread, retains external and local
Drop cancellation, joins terminal work and maps fixed failure categories.
The parent requests cancellation at the operation deadline, permits a bounded
terminal drain, then kills/reaps its exact child on uncertainty. Drop also owns
exact-child and pipe-thread cleanup. These finite checks assume ordinary OS
kill/reap and pipe behavior; they are not hard real-time guarantees or an OS
process sandbox. Packaged code must retain the reviewed no-subprocess worker;
descendants retaining inherited handles would invalidate the join assumption.

The worker suppresses native logs; stderr content is discarded, not forwarded.
Adapter metrics retain aggregate counts/timing, not prompts or generated traces.
The explicitly feature-gated scene probe intentionally writes its own fixed
synthetic scenes and outputs to ignored target files; it is not a private-save
diagnostic tool. Its report explicitly says quality_accepted=false and
network_blocked=false. No raw private story/weights/binary is added by this PR.

The CMake configuration pins the upstream commit and rejects tracked changes,
uses static reviewed libraries and disables server/app/GPU/RPC/dynamic backend,
TLS/subprocess and LLGuidance build paths. It never fetches an upstream checkout
or weights. Untracked build/source contamination is not package attestation.
The documented retained HTTP utility and lack of OS traffic blocking mean this
source inspection cannot prove offline/network-denial behavior.

## Evidence limits and next qualification

The coordinator's c6044b4 publication packet records20 passing Rust cases plus
one separately passing privilege-dependent reparse case. For correction5e0f8d1
the coordinator reports23 default cases plus that separately passing reparse
case: **24 actually executed passing Rust cases**, strict all-feature
Clippy/format checks,11 actual-native model-free protocol cases,13 actual
grammar-machine assertions and3 native thread-launch assertions. These counts
were not rerun by this reviewer. The coordinator reports a fresh pinned-source
CMake/MSVC build; the corrected worker SHA256 is
`add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87`.
Earlier carried reports have older source pins/counts/worker hashes; the new
publication packet must be updated to distinguish this later correction from
its original eda393e9 worker and21-case results. This documentation reconciliation
was explicitly handed to its owner before publication.
The preceding joint native app evidence belongs to its separate app sources,
which are absent here. Both accepted real narrations used safe engine fallback;
neither lifecycle nor mechanical scene success is prose-quality acceptance.
The earlier model/app measurements used the preceding worker binary, not the
newly rebuilt add98cf0 binary. Fresh real-model lifecycle/scene runs were underway
at this handoff; no new-binary result or actual-app rerun is asserted here.

Pending qualification includes blocked-network execution, sustained
latency/memory, allocator/OOM behavior, packaged worker/model
provisioning, installer/distribution reproducibility, semantic quality and physical
phone gates. No D04/M05 checkbox, approval score, merge or release follows from
this source review.

## Final source identities

At5e0f8d1 the implementation differs intentionally from the carried joint inputs
in six existing files: adapter.rs, lib.rs, protocol_fixture.rs, CMakeLists.txt,
build.ps1 and main.cpp. worker_launch.h and worker_launch_test.cpp are new.
The other15 of the original21 carried inputs remain byte-identical Git blobs
to61e8cf1. The publication report is an additional document, not a carried
implementation equivalence claim. Thus the final boundary has24 additions over
coree3749da before this separate review document:20 runtime/worker files and
four profile/publication reports. Root/engine/storage/app/mobile files remain
outside its net diff. Read-only git diff --check passed.

SHA256 below identifies the actual reviewed Windows checkout file bytes at
5e0f8d1 (including checkout line endings), not a reproducible binary build or
package signature. The source commit identifies the canonical Git blobs.

```text
6331fe92a7cd86bfaa166a39241accddc1396cd0d7704e6a0e1c02f95fd6c42f  crates/locallore-local-runtime/ADAPTER.md
3c581238977f788a9ab0d90dcf3ad1ff469a46e4e147bab7d794a5e922b5fa31  crates/locallore-local-runtime/Cargo.lock
e39122e22dc004b0904fdd5f2bdbb40207403f62fbd816eec7f1ab5023961014  crates/locallore-local-runtime/Cargo.toml
6abd1f097ab6cede4b3a4a8dfadc6a7b394074f1f1d8b926013d7eb9019da065  crates/locallore-local-runtime/src/adapter.rs
ea74a166946924c83801284d555b4f9e379725ff074de9c6c5b5691941f68802  crates/locallore-local-runtime/src/bin/play_scene_probe.rs
d6383142f4964562907d5f185d07e89da866081706c75f5492517fd85266e071  crates/locallore-local-runtime/src/bin/protocol_fixture.rs
fbfde457d8accd1bc10920bbc2a173ced835f073676481bf3b265ccc5442c1d5  crates/locallore-local-runtime/src/bin/runtime_probe.rs
eb017282cea79973c31922136dc36ca7c88b771c512b80efe0ed898379550ff6  crates/locallore-local-runtime/src/lib.rs
174ce98efa37ce7c6d370ec50f1c252d86737ce3648c208b7c9d7e819b3b186c  native/llama-worker/CMakeLists.txt
751673fdeffffbdd4aabb043dcd1b8622bc2c0fb195d0d1b7418a2c5a5eff5e3  native/llama-worker/NOTICE
1b8d078581ec7d2fcf3117577fb48d815d4dc23cc844e356d1db81e469aab988  native/llama-worker/SCHEMA_ORDERING.md
0a0832172e0986c807426a478d19fb951710555ccecbe2cd1528ca9f8c5c397e  native/llama-worker/build.ps1
55456ba808e2334125a74f5f6437bb562735cf1dbb7b6de2f5a297ae2b6250d2  native/llama-worker/generate.inc
1f3f0adf19616afa230568558de6310c5dec6093d337a8462bec0f11478e3797  native/llama-worker/main.cpp
77ca04648f1d1a232b2f950d71d5e489494145e314a56a0d9a9fdb1cb1eb9d80  native/llama-worker/profile-v1.json
1c20912fc7625bf689338ba4c84a9136351f61f93c4b5613c44e8304cb52e0bc  native/llama-worker/schema_order.h
b4fa50e9842c3c7ead73ff5ecd7c20096b5a744c3de396bcca0fa63a510f8c00  native/llama-worker/schema_order_test.cpp
c9c386e338b4e031735fc641482bab7800b6abe4aa7900c77402bf9c18cc025a  native/llama-worker/test_protocol.py
94be00d403aa8c92e06faabf3adef3ab3f951ec78494ed92173960a3d960933a  native/llama-worker/worker_launch.h
fe54d6a366d12342e82e7af9a3487c01125b873759d5cf48839433753a12a98f  native/llama-worker/worker_launch_test.cpp
61c99a8e8ff9cb6dc09204021067f9ed481163402c957d7e380c08499749a3ac  docs/desktop/D04_PROFILE_INVESTIGATION_2026-10-22.md
b2e153cfdeb9302b2bea5c88b1ae98038557a17e2b95025e550b6128a54128b5  docs/desktop/D04_RUNTIME_IDENTITIES_2026-10-22.md
3b8d67a5745591582c7edff2a2ac3a1e2c4e16df56583e62431482ad31ebb760  docs/desktop/D04_RUNTIME_VERIFICATION_2026-10-22.md
```
