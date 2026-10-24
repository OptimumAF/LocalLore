# Local model setup candidate

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 provisioning
prerequisite and M05.04 supporting. This debug candidate builds on the
[concrete LiteRT worker](LITERT_WORKER_CONTRACT.md). It selects no production
backend or supported phone and does not satisfy the real-inference exit gate.

## Explicit construction

The additional `localLoreModelSetupVerification=true` flag requires
`localLoreLiteRtVerification=true`. It creates `org.locallore.app.modelverify`,
separate from the ordinary app, previous SDK candidate and benchmark packages.
Only this profile replaces the launcher with the model setup Activity. Its
MainActivity and play Activity are not exported. The ordinary app and the
LiteRT-only qualification profile retain their existing scripted launcher.

The setup screen requests an existing local document through the system picker
with `EXTRA_LOCAL_ONLY`. No download, network permission, account, broad storage
permission or persistent URI grant is added. A selected provider remains a
separate application and controls its documents. The local-only request is not
proof about a malicious provider. Input URI, filename and metadata never choose
expected hashes, SDKs, budgets, native paths or a fallback.

The built-in candidate is the exact `gemma-4-E2B-it.litertlm` artifact at
`litert-community/gemma-4-E2B-it-litert-lm` revision
`a790a852d433991c0c0a41c1154cf9b3850300fa`, 2,588,147,712 bytes, SHA256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
This is Gemma 4 E2B, not another Gemma family. Source metadata and licensing are
reviewed separately; no weights are bundled. The fixed configuration manifest
is exact UTF-8 text in `CandidateLocalModel`, hashed for provenance. Template
identity denotes the whole verified model container; worker identity denotes
the LF-normalized `LiteRtRoleWorker.kt` source. The build refuses a changed
worker until that identity is reviewed. It is not an APK-signature identity.

## Copy, cancellation and restart

The model store owns only `local-model-v1` under `noBackupFilesDir`, separate
from stories and previous experiments. It verifies exact size and full SHA256
using a 64 KiB buffer on IO. The source read is capped at expected bytes plus
one; zero-progress streams fail. Admission requires the expected bytes plus
256 MiB available. This floor is an import reserve, not a measured runtime
cache, RAM or device-support budget. Actual writes can still fail as other
processes consume space.

Setup resolves and caches this private store on IO. Play's ViewModel factory
consumes only that prepared path plan; it does not query/create directories on
Main. The trusted framework storage anchor is canonicalized before fixed child
paths are planned; arbitrary supplied store roots remain subject to the strict
canonical-path check. Entering play without completed setup fails closed.

A process reservation precedes opening the persistent file-lock inode.
Cooperating processes then use a nonblocking OS lock. No contender closes a
second channel under an existing process lock. The reservation spans source
open/read/close, file flush, publication and cleanup. Cancelling a coroutine
does not prove a provider stopped. The UI remains stopping until the operation
actually returns; no overlapping import or play may start from that controller.
Disposal/backgrounding invalidates stale completions. A noncooperative provider
can keep the slot busy indefinitely; no thread is declared released by timeout.

Only the fixed regular `model.part` staging path is recovered under the lock.
Unknown files and existing model/cache contents are preserved. Symlinks and
unsafe paths fail closed. After complete hash/size verification and file force,
a narrow Rust JNI operation publishes `model.litertlm` using the public bionic
`renameat2` wrapper with `RENAME_NOREPLACE`. One directory descriptor anchors
both fixed filenames. The operation consumes the stage and atomically refuses
any existing destination, including a dangling symlink. Android forbids app
hard links; the original host-tested hard-link design was replaced after this
platform discovery. There is no replacing-move or hard-link fallback.

This helper is compiled only with the `model-provisioning` Cargo feature,
enabled by the existing debug model-setup profile. No dependency is added.
Because the public bionic wrapper begins at API 30, system `libdl` resolves it
at runtime; an unavailable symbol or unsupported filesystem fails closed.
This avoids a new API-30 dynamic-symbol requirement when loading the existing
minSdk-26 library. API 26 execution remains unmeasured and model import there
is unavailable if the wrapper is absent. The helper accepts a bounded UTF-8
private root and uses only `model.part` and `model.litertlm`; it cannot receive
filenames from picker metadata or model output.
Cancellation after publication can leave a complete valid model. Later checks
discover it; cancellation does not promise rollback. Restart checks rehash the
whole artifact before enabling play. The worker independently rehashes it on IO
before SDK construction. There is no claim about directory durability after
sudden power loss or defense against a compromised OS replacing private files.

Existing corrupt model files are retained and refused. This packet adds no
model-removal/replacement flow; repeated file selection cannot repair them.
No prior benchmark cache or model copy is inspected, repaired or consumed.

## Gameplay and runtime ownership

Start opens the existing story shell through the same `NativeWorkspaceTransport`
with `LiteRtWorkerConfig.createOwner()`. Fork operations borrow that exact owner;
the established archive/deletion adapters remain unchanged. Rust constructs
scoped requests, validates proposals and commits accepted outcomes through the
existing SQLite owner. Kotlin adds no gameplay rules. No model response or
summary becomes canonical state, and failed construction cannot select a
scripted provider.

The candidate reserves one runtime attachment per process before construction.
The reservation survives construction failure, Activity finish, apparent close
and late callbacks. Retained ViewModels handle configuration recreation without
reattaching. Another attachment shows a fixed unavailable screen; finishing an
Activity is not a complete process restart. This conservative candidate limit
prevents a new SDK owner from overlapping an uncertain predecessor. It is not
active-model cleanup qualification. Setup and play use `singleTask` as an
additional UI constraint; the process reservation is authoritative.

Only fully verified file state enables Start. The native owner remains configured,
not loaded, until an actual turn asks for inference. Missing/corrupt files,
initialization failures, uncertain cancellation and unknown commit acknowledgments
follow the existing fail-closed owner/recovery boundary. Accepted events remain
saved. The pinned SDK's exposed callback/close limitations still apply.

See the accompanying verification and independent review for actual tests and
limits. Physical phone, ARM64 execution, model quality, real initialization,
active cancellation, sustained memory/thermal behavior and redistribution
clearance remain separate gates. Prior A/#117/#119 holds remain unchanged.
