# D04 native model and free-text integration

The desktop uses one fixed, reviewed Windows CPU worker and the approved
Qwen3-0.6B Q8_0 GGUF. Model management is native-owned: the renderer can request
status, import, load, unload and cancel, but cannot provide paths, executables,
prompts, model hashes or configuration. The native file picker selects a source;
import copies only the exact approved artifact into app-local models storage.
Missing/incompatible/corrupt sources are refused. Hash, byte count, available
space, root/ancestor pinning and no-replace staged publication protect the copy.
The source is opened read-only and is never changed. No weights are distributed
with this source or downloaded during play.

One loaded model serves director and narrator sequentially with fresh isolated
role contexts. Long hash/copy/load/unload/generation work stays on native workers;
lightweight metadata reads remain responsive. Cancel reaches file hashing and
native load/decode. Native window epochs and operation tokens revoke delayed
configuration/publication/cancellation on close/reopen. Unload disables the shared
provider, cancels this Host's local work, drains the owned runtime and preserves
accepted history. Fixed enum errors and bounded progress are visible in the app.
The imported status indicates file presence; a successful load re-verifies bytes
and records actual locked-worker/profile identities.

The composer explicitly selects deterministic fake fixtures or experimental local
CPU inference. Local mode offers Action or Dialogue, retains the original free
text in the shared Request, and calls the existing scoped begin/prepare/commit/
status lifecycle. Pending work is explicitly noncanonical. Only shared approved
receipts change transcript/state. Errors, cancellation and invalid proposals
preserve canon; retries retain the original scoped key after uncertainty. A
missing/unloaded/failed real model never silently selects a fake provider.

Each saved v2 receipt displays the recorded model/profile/policy, repair count,
role/validation/total timing and whether narration used the safe engine fallback.
An engine narration fallback is distinct from switching inference providers.
Inspector mode does not grant characters hidden knowledge. Shared M05 remains
the only interpretation, validation, narration and canonical history authority.
Prose consistency is conservative and imperfect, not a semantic oracle.

## Fixed worker resource

stage-runtime.mjs requires the trusted build environment variable
LOCALLORE_D04_WORKER_SOURCE pointing to the reviewed native build artifact. It
verifies the pinned SHA256 and stages only locallore-llama-worker.exe under the
ignored src-tauri/runtime and default debug/runtime directories. It never copies
weights. Native code resolves only resource_dir/runtime/locallore-llama-worker.exe.
The default app remains buildable without this resource and reports
WorkerUnavailable on load. tauri.runtime.conf.json explicitly maps the staged
worker into runtime/ for later packaging; installer/release qualification is
separate. See the official [Tauri resource guide](https://v2.tauri.app/develop/resources/).

Normal provisioning uses an explicit model picker. The development-only
model-harness.mjs supplies an approved read-only source and fresh ignored
synthetic workspace from its trusted launcher, then exercises the real frontend
controller and native IPC. Fixed scenario hooks select only missing/corrupt/
cancel/approved cases, never arbitrary renderer file or process authority. A
trusted development root override can reuse one previously imported synthetic
model when disk space prevents duplicate copies. Production ignores these values.

## Current verification limits

The initial actual native diagnostics verified import/error/cancel/Unicode-path
and loaded provenance behavior. They deliberately retained two failures: the
shared profile validator rejected the pinned period-containing label, then the
actual director proposal failed Agency for the potion action. Shared/runtime
owners are fixing those integration defects; these runs do not qualify the real
scene or D04 exit gate. The current source has passing native lifecycle/export
regressions and frontend checks; final integrated real-scene/restart/offline/
sustained-performance/quality evidence remains pending. Physical-phone gates are
not replaced by desktop results. No release is authorized or published here.
