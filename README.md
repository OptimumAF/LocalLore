# LocalLore

**A local-first story engine for worlds that remember.**

LocalLore is a proposed open-source phone app for interactive, chat-based stories. The player writes freely; characters respond and the world changes. Player progression, relationships, knowledge, promises, and consequences persist across long sessions without a hosted model or a cloud account.

> The model proposes. The engine validates. Accepted events establish the history. The narrator tells the story.

**Development status:** see the [roadmap and status ticket #3](https://github.com/OptimumAF/LocalLore/issues/3) and its linked milestone tickets for accepted work, active implementation, evidence, and blockers. LocalLore is a working name, not a cleared trademark. The project is published at [OptimumAF/LocalLore](https://github.com/OptimumAF/LocalLore). Owner-reviewed pull requests protect `main`; private vulnerability reporting is enabled. Dated setup evidence is preserved in [archive #2](https://github.com/OptimumAF/LocalLore/issues/2).

## What we are building

- A progressive player record: abilities, inventory, attributes, injuries, affiliations, goals, and their supporting events.
- Short- and long-term story memory: recent scenes, durable events, evidence-linked summaries, and unresolved threads.
- A character network: persistent NPC identities, directed relationships, interactions, beliefs, and knowledge boundaries.
- A consequential chat interface: interpret player messages as intentions, not unrestricted permission to rewrite the world.
- Multiple independent stories and alternate timelines, with no accidental cross-story memory.
- Fully on-device inference and storage during play, explicit export, and no silent cloud fallback.

These are planned capabilities, not claims about implemented software. Free-form prose cannot be promised perfectly consistent; the project will enforce defined mechanical invariants and evaluate narrative consistency separately.

## Start here

| Document | Purpose |
|---|---|
| [Roadmap and project status](https://github.com/OptimumAF/LocalLore/issues/3) | Authoritative milestone tickets, task IDs, dependencies, acceptance criteria, status, and evidence |
| [Ticket workflow](docs/ISSUE_WORKFLOW.md) | Claim work, post verification/handoffs, revise tasks, and record owner acceptance |
| [Agent prompt](AGENT_PROMPT.md) | Paste into an implementation agent when implementation is authorized |
| [Agent rules](AGENTS.md) | Repository-wide instructions, authority boundaries, and evidence standards |
| [Product requirements](docs/PRODUCT_REQUIREMENTS.md) | User experience, scope, and non-goals |
| [Architecture](docs/ARCHITECTURE.md) | Component boundaries, turn lifecycle, and proposed stack |
| [Data model](docs/DATA_MODEL.md) | Canonical history, projections, epistemic state, and branch semantics |
| [Memory and retrieval](docs/MEMORY_AND_RETRIEVAL.md) | Context compilation, summaries, provenance, and bounded retrieval |
| [Model evaluation](docs/MODEL_EVALUATION.md) | Real-device experiments and model/runtime selection gates |
| [Evaluation and testing](docs/EVALUATION_AND_TESTING.md) | Consistency, crash, privacy, quality, and regression tests |
| [Privacy and threat model](docs/PRIVACY_AND_THREAT_MODEL.md) | Local-only contract, untrusted inputs, backups, and exports |
| [Governance](GOVERNANCE.md) | Community participation with founder-controlled upstream decisions |
| [Contributing](CONTRIBUTING.md) | Contributor workflow and review expectations |
| [Repository setup](docs/REPOSITORY_SETUP.md) | Publication and GitHub controls; not evidence that settings are enabled |
| [References](docs/REFERENCES.md) | Primary sources and verification notes |

## Run the host contract proof

The first implementation provides strict typed proposals, engine validation,
in-memory accepted history, observer-filtered contexts, branch fixtures and a
deterministic fake provider. With Python 3.9+ and Rust 1.93.1 installed:

```powershell
python scripts/check.py host
cargo run --locked -p locallore
```

The original Lantern Quay demo gives the player's sole potion to Mira, verifies
replay equality, and checks that the absent Sable did not observe the gift.
The host command does not implement disk saves or real inference. Read
[development instructions](docs/DEVELOPMENT.md), [contract v1](docs/DOMAIN_CONTRACT_V1.md),
and [host verification evidence](docs/IMPLEMENTATION_EVIDENCE.md). Official-source
[runtime preparation](docs/runtime/FEASIBILITY_2026-10-22.md) selects no backend;
physical-device measurements remain blocked.

A separate [development runtime spike](docs/runtime/spike/README.md) exercises
verified local model files through actual LiteRT-LM and llama.cpp on Windows
CPU. It adds no Android inference backend. Host compatibility, strict synthetic
proposal acceptance and process cleanup do not establish phone support or prose
quality; those gates remain pending.

The [isolated Android runtime experiment](docs/runtime/android/README.md) runs
both candidates and the existing Rust oracle on authorized emulators. It adds
no production inference dependency; physical-device and reliability gates remain
open, with failures retained in the dated results.

Separate [Android model-storage receipt checks](docs/native/MODEL_RECEIPT_ANDROID_VERIFICATION_2026-10-24.md)
exercise a tiny synthetic file without model inference. Three emulator methods
passed; process-death qualification remains blocked after a service correction
by update staging headroom. The experiment does not change the active setup route.

An opt-in [current Rust play probe](docs/runtime/android/PLAY_PROTOCOL.md) connects
the isolated SDK to guarded free-text preparation and durable commit. Its
[verification](docs/runtime/android/PLAY_VERIFICATION_2026-10-23.md) establishes
host/build and missing-model cleanup checks; real generation remains pending.

## Run the Android engine demo

The minimal Compose app calls the actual Rust engine through bounded JNI. It
supports pending, cancel, failure, retry and reset with fake inference and no account.
The app saves accepted turns in its private SQLite workspace and offers a saved-story
library and resume. From the repository root, with Python 3.9+,
Java 17 and Android
SDK 36, NDK 29.0.14206865 and both Rust Android targets installed:

```powershell
python scripts/check.py android
```

The **Write a turn** composer now sends Action/Dialogue input through Rust's
guarded play-v2 flow using an explicitly scripted fixture, with no language model.
**Potion example** fills a draft; **Send** proposes the gift for engine validation.
Dialogue records the player's literal statement without establishing world truth.
Cancellation, exact-key recovery and saved-story reopen were exercised on both
test emulators. This is input plumbing, not the real-backend/reference-phone demo.
See [verification and limitations](docs/native/ANDROID_INPUT_VERIFICATION_2026-10-23.md).

See [Android build and sample instructions](apps/android/README.md) and
[dated native/emulator verification](docs/native/VERIFICATION_2026-10-22.md).
The [durable-app FFI follow-up](docs/native/APP_DEVICE_VERIFICATION_2026-10-22.md)
records current production-transport cancellation, disposal and process-restart checks.
The [shared check runner/CI instructions](docs/ci/CHECKS.md) document offline
mode, prerequisites and separate authorized emulator commands. Build/static
checks do not establish hosted execution or device qualification.

**Timelines** selects existing validated branches, including their inherited
accepted transcript and independent progress. Gameplay and lineage checks remain
in Rust. See the [catalog contract](docs/native/TIMELINE_CATALOG_CONTRACT.md).
Use **Delete timeline** on a nonroot timeline to retire it while preserving
required original ancestry for retained children. See the
[retention contract](docs/native/PARENT_RETENTION_CONTRACT.md).

**Local diagnostics** previews a bounded memory-only log of timing/error enums;
explicit export writes exactly the reviewed JSON through the system picker.
Exports are plaintext and their selected provider may sync them. See
[diagnostic verification and limits](docs/diagnostics/VERIFICATION_2026-10-22.md).

**Story archive** adds explicit full-private export/import previews through the
system document picker. The shared Rust Store validates and replays every import
before committing; existing IDs conflict and accepted history remains authoritative.
See [Android archive checks and limits](docs/native/ANDROID_ARCHIVE_VERIFICATION_2026-10-23.md).
This partial adapter is under review; it does not establish cross-device or model support.

**Delete story** previews every timeline and removes the story atomically through
the shared Store, with explicit confirmation and native session invalidation.
An empty library stays empty until **New story**. This whole-story slice is under
review; forensic erasure is not provided. Individual timeline retirement uses
the separate preview described above. See
[deletion verification and limits](docs/native/STORY_DELETION_VERIFICATION_2026-10-23.md).

## Initial technical direction

The [shared SQLite owner](docs/storage/README.md) provides scoped seed storage,
atomic root-branch turns and validated save/resume with exact durable retries.
Run `cargo run -p locallore-storage --example durable_smoke --locked --offline -- --directory target/my-fresh-durability-proof`
for a synthetic potion-spend/reopen/retry/backup proof; the directory must be new.
Both Compose and desktop now use this owner through the shared
[native workspace adapter](docs/storage/APP_INTEGRATION.md). Each application
keeps its own local database; this does not sync saves between devices. No model is needed;
Android cross-build evidence is separate from actual device execution/support.

The [desktop Play/Story Lab shell](apps/desktop/README.md) adds a native Windows
window over the same Rust engine, with typed fixture actions, finalized receipts,
fake inference, durable sessions and explicit spoiler-bearing inspection.
[D02 verification](docs/desktop/D02_VERIFICATION_2026-10-22.md) records native IPC,
app-only rendering and compatibility checks. [ADR-0006](docs/adr/0006-desktop-host.md)
records the Tauri choice.
See [desktop epic #21](https://github.com/OptimumAF/LocalLore/issues/21) for the
staged playable-app plan; this shell does not implement real models or inspection exports.

The proposed first target is Android, with a Kotlin/Jetpack Compose interface, a portable Rust story engine, and SQLite persistence. One locally loaded model initially performs director, narrator, and archivist roles sequentially. A narrow inference interface allows backend replacement without committing to multiple production integrations.

These are starting decisions subject to feasibility work and recorded architecture decisions. No specific phone, RAM capacity, model speed, minimum operating-system version, or production inference backend is confirmed. Android-first is an execution proposal, not a permanent exclusion of iOS.

## Community and control

Community members are welcome to propose features, submit patches, review designs, write stories they have rights to share, and contribute reproducible device benchmarks. **Avery Fernandez (`@OptimumAF`) is the sole initial owner and final decision-maker for the official project.** No contribution count, vote, automated agent, or reviewer score grants merge, administrative, or release authority.

That authority concerns the official repository and releases. It does not revoke the rights granted by the open-source license to users or independent forks.

## License and provenance

First-party project material is licensed under [Apache License 2.0](LICENSE), unless a file says otherwise. Copyright 2026 LocalLore contributors. Third-party models, runtimes, assets, and imported stories retain their own licenses; model weights are not included. See [licensing policy](docs/LICENSING.md).

This is an independent project. Do not copy proprietary app code, prompts, branding, datasets, or paid story content. Similarity in product category is not permission to reuse another product's materials.

## First implementation objective

Prove a small local scene in which a player can give their last potion to a character, the item remains spent after restarting, the character remembers the act, and an unwitnessed NPC does not acquire that knowledge. Do not build a large interface around an unmeasured model first.
