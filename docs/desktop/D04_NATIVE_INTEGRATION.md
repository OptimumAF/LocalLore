# D04 native model and free-text integration

The desktop uses one fixed, reviewed Windows CPU worker and the approved
Qwen3-0.6B Q8_0 GGUF. Model management is native-owned: the renderer can request
status, import, load, unload and cancel, but cannot provide paths, executables,
prompts, model hashes or configuration. The native file picker selects a source;
import copies only the exact approved artifact into app-local models storage.
Missing/incompatible/corrupt sources are refused. Hash, byte count, available
space, root/ancestor pinning and no-replace staged publication protect the copy.
The source is opened read-only and is never changed. The packaged application and
native worker remain a trusted installation boundary; a compromised package or
operating system can replace code or read local data. Hash/provenance checks do
not promise protection from that compromise. No weights are distributed
with this source or downloaded during play.

One loaded model serves director and narrator sequentially with fresh isolated
role contexts. Long hash/copy/load/unload/generation work stays on native workers;
lightweight metadata reads remain responsive. Cancel reaches file hashing and
native load/decode. Native window epochs and operation tokens revoke delayed
configuration/publication/cancellation on close/reopen. Cancellation also carries
the first observed native operation ID, so delayed same-window cancellation cannot
cancel a newer job. Unload disables the shared
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

The final actual native journey passes 31 distinct assertions and ten app-only
captures, including a real process restart, exact receipt recovery, potion
inventory, private dialogue, invalid ability, clarification, cancel, isolation
and explicit unload/reload. Both committed turns used the labelled safe engine
narration fallback. This verifies the app plumbing; prose quality, network-blocked
operation and sustained performance remain unqualified. See
[the verification record](D04_NATIVE_VERIFICATION_2026-10-22.md).

Earlier diagnostic failures are retained separately: the shared profile validator
rejected a valid period-containing label; old worker schema ordering restricted
Give decoding; a display-name recipient failed the canonical-ID guard. Shared
fixes preserve engine authority and the final run uses canonical eligible-ID
grammar. No whole-command constant schema or fake-provider substitution is used.
Physical-phone gates are not replaced by desktop results. No release is published.

## Reproduce the bounded native journey

From apps/desktop, provide trusted launcher-only environment variables and run
node model-harness.mjs. LOCALLORE_D04_WORKER_SOURCE must name the reviewed worker;
LOCALLORE_D04_MODEL_SOURCE must name the approved read-only GGUF. The launcher
hashes and stages only the fixed worker and uses a fresh synthetic database.
LOCALLORE_D04_ARTIFACT_ROOT and LOCALLORE_D04_TARGET_DIR can select task-owned
output directories on a drive with adequate free space. With no reuse override,
the journey checks missing/corrupt/cancelled imports and creates its own verified
model copy. LOCALLORE_D04_REUSE_MODEL_ROOT can reuse a previous harness-owned
models root without making a second 640 MB copy; that mode explicitly records
the skipped import cases. Production ignores all harness overrides. Do not point
the harness at production app data. Restore npm run check and rebuild native
without dev-harness afterwards.
