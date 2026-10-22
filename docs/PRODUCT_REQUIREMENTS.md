# Product requirements

Status: proposed v0.1, 2026-10-22. This describes the intended product, not implemented features.

## Product promise

A private, on-device storyteller that remembers meaningful consequences and respects player agency. The player writes actions or dialogue; the world responds according to its established rules, characters, and history. The app should support long-running stories without pretending that every past word fits into the model's prompt.

## Primary user journeys

**Start a story.** The user selects or writes an original premise, tone, content boundaries, and a rules profile; creates a player; reviews the initial canonical setup; and starts a scene. The app discloses storage/model needs and does not require a server account.

**Play naturally.** The user sends free text. The app distinguishes attempted action, dialogue, internal thought where supported, and explicit out-of-story UI controls. It interprets ambiguity conservatively and asks a focused in-story clarification when an irreversible action cannot be safely resolved. Suggestions are optional, do not auto-select choices, and do not limit free text.

**See lasting consequences.** Resources remain spent, items retain ownership, injuries matter, promises stay open, and relationships evolve through relevant experiences. NPCs have independent motives and knowledge; they need not agree with or admire the player.

**Return later.** A short recap is generated from accepted history and current state. It cannot invent new facts, erase unresolved obligations, or imply that real-world time advanced the plot while the app was closed.

**Inspect and correct.** The user can inspect visible character state and the supporting events behind an important fact. Play mode hides spoilers. Author mode allows explicit world edits, with an impact preview and a new branch for history-changing corrections.

**Own the data.** The user can maintain several independent stories, export an archive deliberately, import a compatible archive, and delete a story. Private content does not automatically appear in diagnostics, public issues, or cloud backups configured by the app.

## Alpha scope

English-first text chat; independent stories; one local production backend; a tested model/profile selection; manual model-file import; basic fantasy and narrative-light rules profiles; player progression; a small NPC cast; directed relationships; character knowledge; open threads; event-backed history; short/long summaries; local retrieval; branch/rewind/correction controls; export/import/deletion; accessible core screens; synthetic evaluation fixtures; documented build and contribution workflow.

Android-first is the proposed sequencing. An iOS port is a later evaluated milestone, not a guaranteed initial release. The app should avoid platform-specific domain logic that makes a future port unnecessarily expensive.

## Not in the initial scope

No cloud inference, remote vector service, user accounts, hosted multiplayer, community marketplace, arbitrary executable story plug-ins, real-time continuous NPC simulation, custom model training, image/video generation, voice stack, social feed, or mandatory graph visualization. No attempt to clone another product's proprietary prompts, story catalog, code, or branding.

A network-enabled model downloader/catalog is optional future work. The baseline app can be provisioned using a model file obtained separately and then used offline. A future downloader must never send story content and needs its own clear network/permission policy.

## Product behavior requirements

| ID | Requirement | Acceptance example |
|---|---|---|
| PR-01 | Player actions are attempts until resolved | Claiming an unlearned ability does not add it |
| PR-02 | Persistent resources have explicit changes | Spending the last potion survives restart and retry |
| PR-03 | Dialogue does not automatically establish truth | A claim of royal ancestry is stored as a claim |
| PR-04 | Relationships are directional and multi-faceted | An NPC may respect skill while distrusting motives |
| PR-05 | Knowledge is observer-specific | An unwitnessed exchange is not disclosed to a bystander |
| PR-06 | Important facts have provenance | Inspection identifies the event that granted an ability |
| PR-07 | History exceeds prompt size safely | Old promises remain retrievable after many unrelated events |
| PR-08 | Stories and branches are isolated | A sibling timeline's death does not affect this branch |
| PR-09 | Interruptions are recoverable | Cancellation leaves no partially spent resources |
| PR-10 | Corrections are explicit | Changing committed history creates a visible alternate branch |
| PR-11 | Local-only play is substantive | After installation/import, gameplay works without network |
| PR-12 | Fiction respects player agency | The model does not choose a marriage, betrayal, or major emotion for the player |
| PR-13 | Failures are explained honestly | Unsupported hardware/model errors do not trigger hidden cloud calls |
| PR-14 | User ownership is practical | Export/import preserves canonical state and deletion removes derived indexes |

## Tone, safety, and agency

Offer clear story tone/content boundaries and ordinary stop/regenerate controls. Model outputs are fictional and can be wrong; do not present NPCs as real people or design coercive engagement patterns. Do not use notifications that imply an NPC is suffering because the user has not returned. Explicit content policies, distribution requirements, and age ratings must be decided before release using the actual targeted stores, rather than promising all content is allowed because the app is local.

The app should not infer sensitive player characteristics from their fiction or use such inferences for profiling. Real-player messages and fictional player-character attributes are distinct concepts.

## UX structure

Start with a simple story library, chat screen, character/world inspector, and settings/model manager. In chat, prioritize readable prose, a stable input area, clear generation state, and optional concise outcome details. Place advanced debugging and spoiler-bearing author controls behind deliberate access.

Use list-based relationship/character views initially. A beautiful graph is not useful if the underlying memories are unreliable. Make accessibility and error recovery core user journeys rather than a late visual pass.

## Product evaluation

Measure whether players can explain consequences, distinguish an attempted action from a success, recover from a wrong interpretation, find an old promise, and understand the privacy/export boundary. Evaluate story enjoyment, pacing, distinct voices, repetition, and meaningful choices alongside database correctness. Keep findings separate from claims of outperforming another product.

## Open decisions

Actual reference phones and RAM; minimum supported OS; initial backend/model; approved latency targets; exact packaging/distribution route; privacy options for screenshots/app switcher; exported archive encryption; tone/content policy; and iOS priority. Each becomes a recorded decision with evidence rather than an unspoken assumption.
