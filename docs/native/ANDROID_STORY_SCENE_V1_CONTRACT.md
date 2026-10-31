# Android story scene selection V1

B36; Refs #9 (M05.03), #14 (M10.02 supporting ownership tests).
Base PR302 at e9086c24ff655457e5676974fc0c44d61831506d, unmerged.

## Trusted selection

Add only native `HostPlayConstructionV1::MemoryStorySceneV1(PlayContextPolicy)`.
It has no Serialize/Deserialize/wire constructor. Resolve from a validated
Engine seed: absent initial_world selects existing MemorySceneV1(policy);
present initial_world selects existing MemoryAuthoredSceneV2(policy). Those
concrete recipes keep their exact guards, prompts, policy IDs, frame hashes,
coverage rules, presentation and replay validation. No new scene format or
policy is introduced. Never fall back to a non-scene recipe on refusal.

The actual coherent generation snapshot determines the concrete recipe before
creating the provider. Seed metadata, not domain_version, distinguishes authored
from starter: an authored seed is initially Domain1 and may later become
Domain2 through an accepted author correction. Memory recipes support their
existing corrected-history paths. Trace labels resolve against the bound engine
and identify the actual concrete recipe rather than a new fictitious prompt.

The selected option belongs to native configuration, not a session, model,
profile JSON, Host command, Kotlin enum, narrator reply or receipt capability.
Each prepare resolves independently; two stories in one Host cannot cache a
choice for each other. Existing Host constructors/defaults and explicit fixed
recipes retain their behavior, including V1 authored refusal/V2 starter refusal.

## Android adoption

The existing external Bridge::configure explicitly uses the new native selector
with StateRelevantMemoryV1. The existing WorkspaceRegistry::open_local and JNI
NativeWorkspace.openLocal route reach that same Bridge. No extra registry,
provider, model owner, worker, wire operation, JNI signature or Kotlin gameplay
authority is added. Ordinary open(path) keeps the deterministic fake fixture;
explicit external construction never silently falls back to it.

Keep profile identity and role/token/context/deadline/response/request bounds,
ticket monotonicity, one-shot responses, cancellation, poison/close/disposal and
storage ownership unchanged. Generation remains outside canonical locks and
SQLite transactions. Ready is transient; only exact commit mutates accepted
state. Same request retry/reopen returns saved outcomes without inference.

Typed observed labels obey PR302's boundary: only the original seed fact in the
player's observations admits a typed current label; move does not grant it.
Unseen corrections preserve memory; observed corrected prose without a mapping
omits the typed label. Added frame excludes descriptions/private origin/NPCs;
actual accepted discoveries retain their legitimate narrator evidence.

## Independent fixtures and acceptance

Root owns host.rs, Android external_inference.rs integration and docs/ADR.
Independent Host-test writer owns ONLY new Workspace tests/story_scene_selection.rs.
Independent Android-test writer owns ONLY new Android tests/story_scene_selection.rs.
Both use separate frozen-base D: worktrees; separate reviewer is read-only.
No agent runs builds/tests without Root's bounded execution admission.

FIRST tests are source-authored before production changes. Android tests call
the existing open_local API and can demonstrate a real baseline non-scene
failure; Host tests using the new enum may initially fail compilation, which is
setup rather than behavioral RED. Preserve first assertions and every failure.

Exercise working mixed starter/authored selection on the same actual owner,
Domain2 correction, exact prompt/policy/frame provenance, hidden canaries,
cancel/stale/foreign/closed tickets, unchanged canonical state before commit,
one exact append, durable reopen/retry without provider work, and fixed-recipe
compatibility. Use deterministic synthetic provider output only. Existing JVM
owner tests remain regression checks; build/log attribution must distinguish
actual execution from cached tasks. Build both JNI ABIs and ordinary APKs;
run existing product audit, Core/Host/Android Rust checks, Clippy and formatting.

No dependency/model/runtime/SDK change, phone/ADB/emulator/app/model execution,
new boot/copy grant, shared settings/service change, cleanup, merge or release.
No current-source device, ARM64 execution, model quality/performance or full
milestone acceptance follows from host/fake/build checks.
