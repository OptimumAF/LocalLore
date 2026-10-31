# ADR-0008: Versioned local play and recorded narration

Status: implementation proposal; no D04/M05 acceptance inferred.

The original experimental implementation used guarded policy/prompt2.1 and the
finite supported-English action compiler. Unknown or ambiguous syntax requires
clarification; arbitrary-language understanding is not claimed. It preserves
accepted v1 receipts and rejects unmerged synthetic prototype2.0 records rather
than introducing a permissive legacy commit path. See the shared-core
verification report for that explicit version disposition and actual limitations.
Refs #9 (M05.01–M05.04), #25 (D04.04).

The M07 production context integration advanced the prompt to
`locallore-play-v2.2`, retaining narration policy `grounded-prose-v2.1`. Fresh
preparation/commit requires the current prompt. Private validated history rebuild
accepts recorded `locallore-play-v2.1` under the same interpretation, mechanics,
provenance and narration checks, including when rebuilding a fork. Exact retry
returns the original receipt; neither replay nor restore calls inference. The
unmerged prototype2.0 remains rejected. This is a prompt compatibility decision,
not a SQLite schema migration or a license to accept arbitrary historical policy.

The accepted guard-bound director refinement advances fresh preparation to
`locallore-play-v2.3`. The same finite action Command that passed Engine preflight
now constrains the director and repair schema to its exact operation and
arguments. Actual provider bytes remain required, parsed, intent-checked and
Engine-validated; the expected command never substitutes for output. This does
not expand supported English or grant the model mechanical authority. Recorded
2.1/2.2 histories retain strict replay, restore, fork and exact-retry eligibility;
they are refused as fresh prepared current turns. Dialogue, narration policy,
profile budgets and storage schema are unchanged. Android SDK qualification of
this exact schema is separate from host/fake-provider and llama grammar checks.

The production director now consumes the portable bounded actor-only context
compiler, reusing the shared inspection eligibility port without accepting an
inspection grant. Only selected typed payloads enter model data; ranking and
omission diagnostics stay separate. Literal dialogue is not a factual search
query. Rules, owned inventory, current nearby entities, routes and the original
intent guard remain authoritative. Byte-derived token estimates are labeled;
the actual native tokenizer must still enforce templated input plus reserved
output against the model context limit. See M07_CONTEXT_INTEGRATION.md for
measurements and remaining memory gates.

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


## 2026-10-30: complete evidence words and immutable history

Fresh narration advances to `grounded-prose-v2.5-whole-evidence-words-v1`,
presentation to `grounded-prose-v2.6-story-presentation-whole-evidence-words-v1`,
and scene narration to `grounded-prose-v2.7-scene-frame-whole-evidence-words-v1`.
Complete words are segmented before Unicode case folding; sensitive phrases and
complete visible-name spans use consistent boundaries. This finite English-first
guard does not prove semantic entailment or authorize canonical effects.

Recognized 2.1–2.4 records retain their original policies and interpretation only
through private validated history reconstruction and exact recorded retry.
Fresh generation and commits, including staged commits, require the current
policy. Preserve the
old public scene V1 constant; use a separate current V2 constant. Never retag old
receipts, normalize their stored prose or add an arbitrary legacy commit mode.

Eval's old descriptor APIs remain immutable. Explicit current APIs serve new
writers; readers retain exact whole old/current descriptor families and reject
mixed or drifted tuples. Tauri's private Fresh/Recorded index validation preserves
historical inspectability, while Resume still compares full freshly prepared
metadata/source/protocol before consent and execution grants. Prompt, provider
schema, dependencies, receipt fields and canonical storage schema are unchanged.
See [verification and limitations](../runtime/NARRATOR_EVIDENCE_WORDS_2026-10-30.md).
Refs #9 (M05.03), #14 (M10.04), #29 (D07.04 supporting compatibility).

## 2026-10-31: explicitly selected authored scene V2

Trusted native construction may select MemoryAuthoredSceneV2 or
PlayerLiteralAuthoredSceneV2 for a validated authored seed. This adds prompt
versions2.11/2.12, grounded-prose policy2.8 and a scene-frame version2 hash in
the existing record shape. V1 recipes, defaults, frame bytes, authored-seed
refusal and historical policies retain their interpretation. Wire metadata
cannot select a history bypass or mint a staged capability.

The engine constructs a transient candidate, binds its complete history basis,
and revalidates the approved plan, observation evidence, frame, context and
presentation before atomic commit. Restore reconstructs that exact recipe;
recorded retry does not invoke inference. The new frame may add only a typed
current-location label supported by the candidate player's original seed-fact
observation. It does not grant a discovery or exempt hidden identifiers.

Only complete eligible label spans extend visible names. English first-person
tokens are segmented on original alphanumeric/Unicode Mark characters before
folding; punctuation still separates pronouns. V1 retains its original guard.
The exact unicode-general-category1.1.0 dependency supplies Unicode16.0
categories, has no runtime dependencies, and is included in all three locked
graphs and the desktop notice catalog. This finite lexical safeguard does not
prove semantic entailment or normalize every language.

See [implementation, evidence and limits](../runtime/AUTHORED_SCENE_V2_2026-10-30.md).
This is an explicit Core/Host slice; Android/default selection and real-model,
physical-device and release gates remain separate. Refs #9 (M05.03),
#14 (M10.04 supporting reliability).
