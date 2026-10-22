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

## Run the Android engine demo

The minimal Compose app calls the actual Rust engine through bounded JNI. It
supports pending, cancel, failure, retry and reset with fake inference and no account.
Durable saves remain future work. From the repository root, with Python 3.9+,
Java 17 and Android
SDK 36, NDK 29.0.14206865 and both Rust Android targets installed:

```powershell
python scripts/check.py android
```

See [Android build and sample instructions](apps/android/README.md) and
[dated native/emulator verification](docs/native/VERIFICATION_2026-10-22.md).
The [shared check runner/CI instructions](docs/ci/CHECKS.md) document offline
mode, prerequisites and separate authorized emulator commands. Build/static
checks do not establish hosted execution or device qualification.

## Initial technical direction

The [desktop D01 spike](apps/desktop/README.md) adds a native Windows window over
the same Rust engine, with fake inference, in-memory turns and explicit Story Lab
inspection. [ADR-0006](docs/adr/0006-desktop-host.md) proposes Tauri for owner review.
See [desktop epic #21](https://github.com/OptimumAF/LocalLore/issues/21) for the
staged playable-app plan; the spike does not implement real models or saves.

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
