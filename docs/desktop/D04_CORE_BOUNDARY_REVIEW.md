# Shared-core publication boundary review

Refs #9 / #25, partial shared M05/local-play work. This review covers coordinator
integration and publication boundaries. Its author wrote the finite intent guard,
so it is **not an independent review or approval of that guard**, a score, human
acceptance or a complete D04/M05 gate.

The inspected task-owned checkout was
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/source-core`, branch
impl/m05-local-play-core, initially `6a4b834`, then clean `28bfbae` after final
verification documentation. Accepted comparison base was
`51ec96331bae434fe5063b8076ac4eb0bce26f6e`. This reviewer ran read-only Git/source,
JSON-equivalence and diff checks; no build, model/app/device operation, settings
change or protected-resource action.

## Publication scope and equivalence

The net accepted-main diff contains 19 files: shared contracts/Engine/play/intent
guard/Host/Store/workspace and tests, generated portable host schema/types,
ADR0008 and bounded shared verification/review reports. At initial boundary it
was 2,722 added /52 removed lines. Later verification prose does not broaden
the production scope.

There are no net modifications to root/native/Android manifests or dependency
locks, migrations, Android app/JNI, desktop native code/capabilities, renderer
behavior/controller, package.json, workflows or model/runtime/worker source.
The final tree has no locallore-local-runtime crate or native/llama-worker files.
The existing app still uses its accepted native feature set. Joint runtime/UI
changes remain in history, but the review/PR net tree does not publish them as
present features. This is a tree-boundary observation, not a claim that joint
history or separate evidence never existed.

Compared the 18 carried inputs, excluding the new core verification report,
against joint source `c97c9f1`:

| Comparison | Observed result |
|---|---|
| 14 inputs | Byte-identical Git blobs |
| host-v1.schema.json | Text formatting differs; parsed JSON values are identical |
| ADR0008 | Seven-line explicit guarded2.1/prototype incompatibility clarification |
| host.rs | Intentional historical failed-cause honesty change from6d3f2f2 |
| play_host.rs | Corresponding 11-line actual-Host restart assertion |

Thus “all18 byte-identical” would be inaccurate. Shared implementation equivalence
has one intentional correction, with separately identified schema formatting,
version-scope documentation and its regression. Workspace/native manifests and
locks were additionally compared byte-for-byte to accepted main and matched.

## Shared integration and failure honesty

Original bounded FreeText kind/text/scope/head/key remain the persisted request.
Engine preview checks guarded action binding; typed legacy Actions retain their
exact comparison. Supported-English compilation and mechanical prevalidation
happen before inference, and untrusted generated commands are compared again.
Unsupported forms clarify; unavailable items/abilities/locations are not silently
converted into different valid actions. Dialogue remains exact text, with present
audience restrictions. This finite profile does not claim arbitrary-language
interpretation, new entities or NPC voices.

Accepted outcomes remain engine-created, and narrator input excludes the actual
contents of spoken claims. Stored prose is display evidence, never canonical
truth or a character-knowledge source. Policy/prompt2.1 explicitly refuses the
unmerged synthetic2.0 prototype; accepted v1 receipts retain omitted optional play
field, original bytes and strict narration/restore behavior. The schema/types add
only portable FreeText/PlayInputKind data; no native path, executable, SQL, model
selection or capability-grant field appears.

Trusted provider construction is an ordinary Rust factory, absent from the wire.
The final core has no runtime crate, native worker, CMake invocation or model
loader. A normal accepted app cannot acquire real inference merely from the new
request union: native provider configuration remains necessary. Store's existing
transaction revalidates prepared typed outcomes/provenance and records one winning
receipt atomically; no separate ledger or schema migration was introduced.
Already-recorded exact requests win before unavailable-provider checks. Retained
Host close/cancel/stale/durable-status fences remain the canonical authority.

The durable port records terminal phase, not detailed failure cause. Rebuilding
PhaseFailed previously invented Provider regardless of the true cause. The
intentional correction now reports null cause for a reloaded failed attempt;
cancelled/stale categories remain phase-established. Immediate worker failures
still return their observed category, including caught provider panic as Provider.
This is an explicit Host error-reporting refinement, not a change to accepted
v1 receipt bytes. A current cause is not promised to survive a subsequent durable
lookup or restart when it was never persisted.

The new regression observes immediate panic→failed/Provider, drops the actual
Host, reopens the same workspace, resumes and observes failed/null. It also checks
no worker remains and no potion effect committed. Source inspection found no
new duplicate-effect or failure-category fabrication introduced by this correction.

## Evidence, remaining risk and disposition

The core verification report distinguishes joint `c97c9f1` evidence from the final
focused checkout. It records coordinator159 Rust,191 Python, four fixture-parity
cases/three linker tests, plus38 JVM/both JNI ABIs/APK audit; final focused159/strict
Clippy and accepted-main frontend checks are separately recorded. This reviewer
did **not** rerun those checks. Older shared review reports explicitly identify
their historical sources and unrun checks; their prior “awaiting tests” language
does not override the current core verification report.

Real Qwen/native app evidence is labeled separate dependent work. Earlier wrong
action/grammar/prose failures remain acknowledged, both accepted narrations use
explicit fallback, and quality/offline/sustained/physical-phone gates remain open.
The report does not present this standalone core as a model-loading app, native
scene, installer or release. No approval or milestone completion follows from
the source review or from a mechanically passing scene with fallback narration.

One small test-stability risk was reported to the coordinator: new play_host Temp
allocation still uses PID+clock alone at this boundary, the same naming pattern
that previously collided under parallel inspection tests. It does not establish
a new observed failure here. An atomic per-process suffix would avoid that known
fixture pattern without changing assertions. No production publication blocker
was identified in this bounded integration/boundary pass.

Actual reviewer checks: clean tracked status; exact net file inventory; manifest/
lock blob equality; joint/current input comparison; JSON schema-value equality;
source/version/error-reporting inspection; `git diff --check`. Next gates remain
coordinator final PR/diff review and dependency-ordered runtime then native UI
publication, with actual execution evidence and owner acceptance kept distinct.
