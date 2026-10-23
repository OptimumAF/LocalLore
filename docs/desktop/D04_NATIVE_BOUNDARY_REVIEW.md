# D04 desktop model boundary source review

Refs #25 D04.02/.03/.04/.05; reviewer claim6358000045 and coordinator claim6357973133.
This is a substantive source review of native model ownership, renderer/controller
integration and the focused publication boundary. It is not a test run, human
acceptance, release qualification or independent approval of the finite action
guard previously authored by this reviewer.

## Reviewed boundary

Initial desktop implementation was committed as `ab8469a` in the coordinator's
isolated source-desktop checkout. The reviewer only read that checkout and writes
this separate document in review/d04-native-boundary, based on runtime5e0f8d1.
The desktop changes reuse joint61e8cf1, with deliberate later changes to the
worker staging/journey hash, evidence source-input inventory and model lifecycle.
The new D05 inspection UI is not part of this review or publication.

Actually performed: read-only source/control-flow review of models.rs,
model_commands.rs, main.rs, lease.rs, the relevant exports/harness changes,
controller/model/ModelPanel/App/model journeys, staging, manifests, capability
configuration and carried evidence. Git status/net-diff/equivalence checks and
source SHA256/diff-whitespace checks are source evidence only. No compiler, test
suite, native worker/model, app/UI/browser/device, process control or protected
resource operation was performed by this reviewer.

## Findings and correction disposition

**Poisoned-owner status and unload wedge, substantive recovery defect atab8469a.**
ModelManager::status treated runtime.try_lock Poisoned like ordinary lock
contention, reporting loaded=true. The provider's worker-panic path deliberately
recovers the poisoned guard only to fail the exact runtime; that poison remains.
Unload then removed the resident runtime and set phase unloading, but its lock
error used ? before finish. The manager could stay unloading with no resident
owner, rejecting later load/import as Busy. This source path was reported before
publication; no native panic/model execution was induced by the reviewer.

Coordinator correction `62fdb7d` distinguishes Poisoned from WouldBlock in status,
recovers poisoned runtime guards only for shutdown/drain, returns Cleanup, and
routes unload outcomes through finish_unload before returning errors. Close also
uses the same draining helper. Its synthetic regression poisons a mutex without
a model, verifies failed-owner classification and drain execution, then verifies
failed/Cleanup/nonresident metadata and admission of a subsequent load. Source
inspection confirms this addresses the reported wedge without resuming inference
through a poisoned owner. Execution results remain coordinator-attributed.

**Interrupted-import staging recovery, reported resource gap atab8469a.**
copy_model removes its .import-UUID.part on returned error, but process death
bypasses that cleanup. Neither initialization nor the next import originally
reaped these files. Repeated interrupted640MB copies can consume space and make
future imports fail while no approved final artifact exists. The existing D03
preview-cache reaper covers a different directory. The coordinator was asked for
bounded recovery of only recognized ordinary staging files under the pinned model
root, preserving unrelated, reparse and actively locked entries and the approved
final model. No crash or large-file experiment was performed here.

Coordinator correction `8371caf` adds a reaper before import/load that examines
at most128 directory entries under pinned model-root handles. Only exact
.import-GUID.part names qualify. A retained DELETE-access OPEN_REPARSE_POINT
handle must identify an ordinary non-reparse file no larger than MODEL_BYTES;
deletion uses that same handle, avoiding a validated-name/reopened-name gap.
Active copies deny this DELETE-access open and remain untouched, as do unrelated
names, reparse entries and the approved final model. Per-entry failures are
preserved rather than broadening deletion. Repeated invocations may be needed
for a root with more than128 entries; this is bounded recovery, not an unbounded
directory purge. A synthetic default test covers stale, active, unrelated and
approved files. The reviewer flagged unconditional symlink creation in that
default test as a privilege dependency; `d6d1ab2` splits the reparse case into an
explicitly ignored, separately runnable qualification. No recursive deletion,
arbitrary selector or new deletion IPC was added.

**Unload cancellation wording.** The original UI offered Cancel during unloading,
but native unload must disable the provider, cancel/drain its work and shut it
down; its cancellation token did not abort that cleanup. This was reported as a
UI/contract issue rather than a canon defect. Cleanup should remain irreversible
once underway and the UI should clearly identify that drain, not promise abort.
Correction8371caf removes unloading from cancel-ready phases, returns native
finishing_cleanup for a delayed cancel, and labels the UI as waiting for local
work to stop. The progress label now says model operation rather than import.

All of the reported source paths are addressed throughd6d1ab2. No remaining
substantive native source blocker was found in this bounded pass. The regression
sources are present; exact final native execution is still pending at handoff
and will be recorded separately by the coordinator. Original source or old
screenshots are not evidence that the new regression cases passed.

## Authority, lifecycle and path audit

The renderer's production model API can request status/import/load/unload and
cancel one safe-integer operation ID. It supplies no file path, executable name,
raw model prompt, model hash or configuration. Only the native Windows picker
selects a source. Native setup chooses the app-local models root and fixed
resource_dir/runtime/locallore-llama-worker.exe. Trusted harness environment
overrides and fixed missing/corrupt/cancel/approved scenarios are compiled behind
dev-harness; production handlers do not expose them.

Import pins source ancestors and opens an ordinary non-reparse source without
write/delete sharing, checks exact approved size, pins the destination root,
checks space, uses create_new staging and hashes copied bytes. The final fixed
name is published from the retained DELETE-capable handle without replacement,
after sync and a cancellation/window check. No source write or renderer-selected
destination is present. Presence alone marks imported; load independently
re-verifies the complete artifact through the runtime's pinned handles. The
fixed worker hash is recorded as provenance, not a package signature. Compromised
installation/OS access, backups and arbitrary model choice are not solved by this
boundary and the docs say so.

Long picker/copy/hash/load/generation/shutdown operations run on native blocking
workers. Metadata locks are brief; status uses nonblocking runtime inspection so
an active generation does not stall it. The model-manager metadata lock is not
held across Host configuration or storage I/O. Provider construction/configuration
is trusted native code. It installs the existing shared RuntimeProvider factory;
it does not add an interpreter, event ledger, memory truth or direct Store writes.
Unload disables future local work and signals existing FreeText cancellation
before draining the runtime. Accepted receipts/history remain authoritative.

Window commands capture the native main-epoch label. Dispatch uses the lease gate
for begin/cancel/configuration/publication; delayed closed-window calls reject.
Destroyed invalidates the epoch and export tokens and retires model metadata
synchronously before scheduling Host/model cleanup. Retirement changes the job
ID and cancellation token, preventing old progress/finish callbacks from publishing
new-window state. New model admission waits through the unloading phase. The
controller captures the first observed operation ID after its baseline; a delayed
cancel retains that ID instead of adopting a later status ID. This is supported
by finite source regressions, not a proof against arbitrary OS/picker failures.

Prepare has bounded native admission while cancel/status remain dispatchable.
It calls the same scoped Host begin/prepare/commit/status API; original FreeText
kind/text/key/head is retained. Recovery resubmits the exact request only after
UnknownTurn, never the stale fake-mode selector. Epoch/session checks fence late
controller results. Committed transcript entries come from validated receipts,
not streamed drafts or model-manager status. Unload/failure keeps local play
selected and reports ModelUnavailable; it cannot silently switch to fake mode.

## Renderer, capabilities and visible behavior

Model/error/provenance text renders through React text/pre elements, without raw
HTML insertion or remote images. The CSP is local, navigation admits only this
app origin, new windows are denied, and capabilities grant fixed app commands to
main-* rather than generic filesystem/shell/process access. Harness permission
names appear in configuration/build metadata, but production invoke handlers and
modules are absent under cfg; a permission for a missing handler does not create
it. Frontend harness imports are behind the compile-time __DEV_HARNESS__ constant;
the normal build defines it false and existing checks scan for known hook markers.
This source check is not a freshly built release-artifact audit.

The UI distinguishes fake fixtures from experimental local CPU play and explicitly
labels finite English single-action support, exact Dialogue, unavailable models,
noncanonical pending work and safe engine narration fallback. Receipt displays
show version/policy/profile/stages rather than presenting prose as a new state
authority. Story Lab remains the deliberately private inspector; runtime calls
receive engine-filtered role context and no extra grant from inspection state.
Unknown/ambiguous/compound actions ask for clarification, and failed/unloaded
real play does not select a fake provider. No arbitrary-language, finished prose
quality, GPU or phone claim follows.

The runtime staging script verifies a pinned actual worker hash, copies only that
binary into ignored fixed resource locations and never copies/downloads weights.
The source app can build without that optional resource and fail load visibly.
bundle.active=false and the separate resource config are not an installed package
or installer qualification. WebView2 and model/worker provisioning are explicit
prerequisites. Source/network-feature inspection is not an OS network-denial run.

## Evidence distinctions and pending gates

The carried public JSON records a clean old joint source7c66260,31 distinct
assertions,10 app-owned captures and two real executable processes across restart.
It identifies workereda393e9. Its double-spend measurement explicitly records
failed/Inventory at45ms; the test's unchanged-revision assertion alone would not
prove that category. The same JSON records ClarificationRequired/Ability refusals
and both accepted real turns' fallback metadata. The reviewer read these public
synthetic records, not private saves or model artifacts.

Current staging/journeys pin the later add98cf0 worker and include worker_launch.h
in the evidence source inventory. These source changes cannot reassign the old
31/10 measurements to the new binary or prove a new app run. The coordinator owns
fresh execution, capture inspection and publication evidence reconciliation.
Harness model-reuse mode explicitly skips full import cases; an earlier separate
import diagnostic is not a passing whole-scene run. A synthetic harness assertion
or favorable source review is not human acceptance of story quality.

Still pending at this source handoff: corrected recovery regression execution and
the new-worker app run. The coordinator is running those checks and owns their
separate evidence report. Other open qualification includes genuine network-blocked
play, sustained memory/latency/OOM behavior, native-picker/installer/package
qualification, enjoyable prose/NPC voices and physical-phone gates. Neither this
report nor the partial publication closes D04/M05 or the desktop epic.

## Final source identities

The final code reviewed here isd6d1ab2. Its app/native-evidence net scope is33
files overruntime5e0f8d1. Of those original33 carried joint61e8cf1 inputs,27
remain byte-identical Git blobs; six intentionally differ: models.rs,
ui/controller.ts, ui/ModelPanel.tsx, stage-runtime.mjs, model-harness.mjs and
ui/model-journeys.ts. The first three include reviewed lifecycle/cancel fixes;
the latter three update worker/evidence-input pins. Do not call all33
byte-identical or silently apply old app evidence to the changed implementation.

The branch also carries the preceding runtime publication/review documents;
those are dependency evidence, not desktop implementation changes. No shared
engine/storage/schema, Android, D05 UI, model weight or binary was edited in
this native slice. Read-only git diff --check passed. The following SHA256s
identify the actual reviewed Windows checkout bytes atd6d1ab2, including checkout
line endings; the commit identifies canonical Git blobs. They are source
identities, not signatures or reproducible binary-build claims.

```text
c2dc2325d7872a816a3a9921ee9ed7a7560e21e8a8823a26c76dc79b05b93b9f  apps/desktop/.gitignore
011e0aa78c5c9b338d25bb375a05cfcff0a27d9a398280b4cd6e754ff3c10d24  apps/desktop/README.md
0015cb11af99c455de984660dcf13b89e8f94721aa97e9835ec98d1e2ebb5fdf  apps/desktop/check-model-controller.mjs
9fff34b93cbfcc8294988d2bd752296709bc077c30a518ef1b3f9adbf6ee1d9c  apps/desktop/model-harness.mjs
b71f155d6d16743858c24e9e3056648029504fed74f69c28843741b9fb14579f  apps/desktop/src-tauri/Cargo.lock
a12e0340ae9f331acc059f6f91d53e704f2dfff33968b63c874c9fd53b6a4cd9  apps/desktop/src-tauri/Cargo.toml
7fe7b073fe778541b96f6c056c1738c0831fd6da52196a613fb813c01e294f0f  apps/desktop/src-tauri/build.rs
c262ac4395c3baaca6a56c2215d18fb2bb4f8f6740a6a565dc6cd5857a5a66fa  apps/desktop/src-tauri/permissions/autogenerated/harness_model_case.toml
e15da158a4c4f9573a7e6528705fe9d175ee00223b65b467912c04a65aa41521  apps/desktop/src-tauri/permissions/autogenerated/model_cancel.toml
2eda5b0f408dbb87a658e980b17d5ef4b9cdfec8a0f0810af8541c1372bfb0f2  apps/desktop/src-tauri/permissions/autogenerated/model_import.toml
6af7f26457066f9dc7b5594f90713a4783fed44b5a287bd1a57a9d74c1d59551  apps/desktop/src-tauri/permissions/autogenerated/model_load.toml
1437c6697d07bf4b2b1ea8ab5df3d824f385fc98629b7d3eeee6704ddf2e1c4b  apps/desktop/src-tauri/permissions/autogenerated/model_status.toml
8ca39d6cb26e48644c411ce50eea8fbb7d964312cb988f9bb982c07a967df492  apps/desktop/src-tauri/permissions/autogenerated/model_unload.toml
745ed087aded36386270120af0988a4320e53f3cfbd103462ef377d6b8ce0888  apps/desktop/src-tauri/src/exports.rs
a80c801c28531640a07e6d8386b1684218ecf7aeb577fa2a4d8546e040c5bfbf  apps/desktop/src-tauri/src/harness.rs
c967f8be9b48feb9448a89fbd11734a8c185fbdf2ca22e8eb9040b50047286dd  apps/desktop/src-tauri/src/main.rs
5da9ddb1ba7b883733febee9a49c1acbb2a6eb5cab92f3341cead0c1a0debc01  apps/desktop/src-tauri/src/model_commands.rs
443487757f4498542fed6f02a71b61dc974b5ce9dcf06aaf49a4b137f5e7c423  apps/desktop/src-tauri/src/models.rs
2588642221ebfad86a40ef45cadb4a668ceaf554c2cd1637f725b3a6c9e64ed7  apps/desktop/src-tauri/tauri.conf.json
65bf393eb04a145e3fd8ff193f17a830379627270c9c76e654edac7773ee93d2  apps/desktop/src-tauri/tauri.runtime.conf.json
d423a47f82f720e947f105f56a6b5c5520f23699a1757528f6db52aa33c38391  apps/desktop/stage-runtime.mjs
5377045d5abf4d0d7c0198c23798ddb061c8f3f50dd615302f332d76a327b335  apps/desktop/ui/App.tsx
596afe11088569e82eb8892c8676d02f6a445fa49d2bb3cc65d402e44eebeb70  apps/desktop/ui/ModelPanel.tsx
b1dba3b2b6dc3d80c78c9cbeef2419724d5c4f6d5aed279502350fee0d6f2468  apps/desktop/ui/controller.ts
fb2905738ef828413cf23f95c21975d874e760f038a62844b87fb716098b0c3b  apps/desktop/ui/journeys.ts
61c8b5afdfafde204752d31a16eef9d79e3e2bdd8e45f03ad632b1b714fb28a7  apps/desktop/ui/main.tsx
aa454734fba02191eaad83c8e856f76d482ae092c5a9794f55e228fd3b4f87c2  apps/desktop/ui/model-journeys.ts
0e97394ea2bce7d226642dacacf4b445edc77c21c8147eae8352b89af2bf675f  apps/desktop/ui/model.ts
33250060c2546db56902f2de269e1f7380bc557fba869405ff89a40fbaf5a24d  apps/desktop/ui/style.css
90f82d2de5882fa20b2778af09432b7ccd7a019cf177ec421c8ae6f6fdd33986  apps/desktop/verify-frontend.mjs
9fe5aeef6fb21eaeb9aa38177bd81fa6468876b5f4489720d8f7249c36d825f9  docs/desktop/D04_NATIVE_EVIDENCE_2026-10-22.json
69cf25a6ca19d4d1842f8eac7ba6ff8444b32247ff8e0b92942b8bafe80b65ca  docs/desktop/D04_NATIVE_INTEGRATION.md
33786378837ea0495a900e840a9c9b148410cec2e313dad850d9e12fc188bb0d  docs/desktop/D04_NATIVE_VERIFICATION_2026-10-22.md
```
