# ADR-0008: Versioned local play and recorded narration

Status: implementation proposal; no D04/M05 acceptance inferred.
Refs #9 (M05.01–M05.04), #25 (D04.04).

The v1 proof deliberately requires exact typed commands and engine-rendered
narration. A real backend cannot turn this into free-text play by replacing
the fake provider or deleting those comparisons. Preserve v1 fixtures, bytes
and restore semantics unchanged.

Add an explicit `free_text` intent carrying an action/dialogue input kind and
the original bounded user text. Its original scoped request/turn/revision is
persisted before generation and compared in full on retry. It is never replaced
with a synthetic Actions request after interpretation. Author corrections and
inner thoughts are separate intents and grant no director authority.

The director receives only player-eligible context, owned inventory, nearby
entity identifiers and supported operations. Output is a bounded typed proposal;
known IDs and existing mechanical rules remain authoritative. No model-created
SQL, tools, runtime paths, event effects or actor privileges are accepted. New
entities and new operation families require explicit shared contracts before
support; malformed references fail visibly instead of becoming lore.

After mechanical resolution, narration receives an immutable approved outcome
view. NPC speech may use only that speaker's eligible context. Inspector grants
never widen this context. Narration is recorded display text, never a source
of canonical facts or retrieval truth. The versioned narration contract must
bound references, speakers, bytes, repair and unsupported consequential claims;
an arbitrary nonempty string is insufficient. Semantic checks cannot prove
arbitrary prose faithful: unsupported content fails safely and measured semantic
errors remain separate from ledger correctness.

V2 receipts add a typed play record with the original interpretation, resolved
event references, narration-policy version and model/runtime/template/prompt/
schema/profile provenance. A prepared receipt stays noncanonical. Commit
revalidates scope/revision/mechanics and narration policy, then the existing
storage transaction atomically records effects, prose, provenance and the exact
original request. No schema fork or desktop ledger is needed. Replay validates
the versioned record and recorded outcomes without inference or a model seed.
Old receipts retain the strict original narration equality rule.

One complete-turn monotonic deadline and cancellation token cover director,
at most one repair, narrator and final preparation. Session changes, cancel,
stale work and unknown commit acknowledgements use existing host/storage fences.
Provider work runs outside canonical locks and write transactions. Backend
selection is trusted native construction; model output cannot choose an
executable or file. A managed warm CPU worker may retain weights, but each role
receives a fresh context and sampler. Android remains portable and gains no
Windows executable dependency.

Acceptance requires hostile proposal/narration tests, secret canaries before
model input, repair/deadline/cancel/stale races, exact durable retry/restart,
v1/v2 restore and tamper rejection, no-inference replay and actual native scene
evidence. Real local worker lifecycle measurements alone do not satisfy the
scene or enjoyment gates. This ADR does not close physical-phone qualification.
