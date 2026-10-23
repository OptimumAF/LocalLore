# Shared M05 source review for the desktop integration

Refs #9 / #25 D04.04. Review was bounded to the coordinator's current uncommitted
shared contracts, engine, play, Host, Store and workspace source over coordinator
HEAD `4d79ae1ff74b2139b60e2e61b38cce70d88ee98d`. This report is not a final integrated
review, PR approval, independent human acceptance or D04 completion statement.
The shared writer continued implementing during review; hashes below identify
the final observed files, rather than claiming an immutable review snapshot.

## Concrete findings and observed dispositions

1. The initial director schema omitted Promise/CompletePromise, but the parsed
   Command enum and Action interpretation validator admitted them. A provider
   could bypass the advertised supported-operation set even though a correctly
   installed grammar would normally prevent it. The coordinator added a Rust
   allowlist rejection. A subsequent actual in-process engine probe against the
   updated source rejected an out-of-schema Promise before it could establish
   canon. Native grammar is useful constrained output, not authority.
2. Initial Host FreeText/Submit availability guards rejected a committed exact
   free-text retry after provider disable with Unsupported, before lookup of the
   recorded winning request/receipt. An ignored synthetic in-process Host probe
   reproduced configure → queued → ready → committed → disable → Unsupported.
   The coordinator moved availability gating after original-key lookup. Re-running
   the same probe against current files returned the original committed receipt
   with the provider disabled. This verified the memory Host case. Coordinator
   durable restart tests remain necessary for the wider storage claim.

No additional concrete mechanical blocker was identified in this bounded source
pass. That is a finite review statement, not proof of all inputs or race paths.

## Authority, replay and lifecycle observations

Original FreeText Request, kind, text, scope, turn ID and expected revision remain
in the recorded receipt. Duplicate lookup compares the full original request.
Model interpretation yields typed proposals; the existing resolver recomputes
effects/ownership/resources/knowledge and event witnesses. AcceptedEvent/Receipt
remain engine-created values rather than model-deserializable canonical objects.
The new versioned commit path requires FreeText and a validated PlayRecord;
legacy commit still rejects FreeText and still requires exact engine prose.

The optional play record serializes only when present, retaining existing v1
receipt bytes. New records carry play version2, named policy/prompt versions,
model/runtime/template profile, repair count, fallback marker, event references,
speaker and bounded stage timing metadata. Restore validates the play policy and
recomputes mechanical outcomes without an inference call. Unknown/new policies
must fail closed. Future policy changes must retain historical-version validation
instead of silently changing what old saved receipts mean.

The v2 restore contract validates mechanics, linkage, shape and its conservative
prose policy. It does not cryptographically authenticate historical prose or
model provenance: changing both stored narration copies to another policy-valid
text can pass by design. Model hashes in a record identify the configured
artifact; ordinary unsigned JSON is not an attestation that those weights
generated those words. Public claims should distinguish effect-tamper rejection
from universal metadata/text authentication.

Director input is compiled from the player's filtered CharacterContext, owned
inventory, living co-located actor identities and available routes. Narrator
input is reduced to approved outcomes and mechanical summary, not the whole
director context or omniscient inspector. The current narrator prohibits NPC
impersonation; actual scoped NPC dialogue remains separate work. Inspector grants
do not enter these inputs. Player speech can itself contain untrusted instructions;
the narrator still receives only approved outcome data and cannot read hidden
world truth merely by obeying such text.

Narrator JSON/unsupported prose falls back to exact engine narration with an
explicit fallback marker; the approved typed effect is the only canonical
consequence. The app must show that marker honestly. The conservative text checks
are not a semantic oracle. A mechanically legal but semantically mistaken action
interpretation, wrong inferred present audience, or paraphrased unsupported prose
can remain a quality/agency error. They need declared adversarial evaluation and
visible correction/recovery; do not claim mechanical correctness proves exact
intent interpretation or arbitrary prose fidelity.

Repair is limited to one malformed director response; mechanically invalid plans
fail before narrator and cannot be repaired into a different successful action.
The provider adapter now supports exactly that one completed same-schema repair,
then narrator, with immutable active-call identity. Remaining time is recomputed
across role/repair calls, and cancellation is rechecked before commit. Stage
timers and native metrics have distinct scopes; they must not be presented as
complete app latency or sustained-session results.

The Host captures a coherent clone and provider/profile for work outside the
canonical mutex. The provider factory is trusted native construction, not a wire
grant. Model disable cancels existing free-text tokens. Completion rechecks local
phase, cancellation, revision and persisted status; Store commit rebuilds from
the authoritative head inside its existing transaction. No database transaction
spans generation. Repeated/late work cannot replace an already winning durable
receipt. The adapter owns its background thread until native terminal drain/reap;
no detached generation thread is required by the integration.

## Actual verification scope and remaining checks

The reviewer created an ignored, small synthetic Rust probe under target/ using
the current core path dependency and existing cached build target. It invoked
actual in-process Engine/Host code with a scripted provider and the original
synthetic Lantern Quay fixture. The first probe compile had an incorrect
include_str relative fixture path; it was fixed locally. The probe then exposed
the retry failure, and a later rerun observed the coordinator's correction and
the out-of-schema-operation rejection. No shared source or tests were edited by
the reviewer. Source/API inspection and those two focused regressions are this
packet's actual evidence; it does not claim the coordinator's complete suite ran
here. The ignored probe includes synthetic model-free data only.

This is **engine/in-process Host execution**, not native IPC, native WebView,
headless rendering, actual local-model generation, durable cross-process replay,
Android execution, network-denial or performance qualification. Shared Host/Store
race/restart/failure tests, native application journeys and full real-model scene
evaluation remain coordinator integration checks. No desktop control, device,
model, protected process or shared experiment was operated or altered.

Final observed SHA-256 values (uncommitted shared sources):

| Source | SHA-256 |
|---|---|
| crates/locallore/src/contracts.rs | `756ed270862c2ecbeabd7fb95910a3733a909083db3690811cbe811b420c195f` |
| crates/locallore/src/engine.rs | `0a8470aad36a72f3533080809c1f299f726aa8ee68a9fb761e8c68e6549702b7` |
| crates/locallore/src/play.rs | `8633526836917f2478790769ea0054ac0fcf9ce49277162d219c6bf7f1931c11` |
| crates/locallore/src/host.rs | `baf5f1eed019d4d572e8573f78d272711950685d9f86dcf0699131c26ff49df4` |
| crates/locallore/src/inference.rs | `4de0fbc10f0ac7738cd1f11b174a57720d87da0e56a75aacb51bfa7ee6867c9a` |
| crates/locallore-storage/src/turns.rs | `704d0920553513a5b8a4cc774a9909e83f56c04bdd6dd62c84b745b680fc1134` |
| crates/locallore-workspace/src/lib.rs | `2bae7af85a9496cfa6b8e78a5079650c134443a3c06296a431fa10a002cdee7a` |
