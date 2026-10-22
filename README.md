# LocalLore

**A local-first story engine for worlds that remember.**

LocalLore is a proposed open-source phone app for interactive, chat-based stories. The player writes freely; characters respond and the world changes. Player progression, relationships, knowledge, promises, and consequences persist across long sessions without a hosted model or a cloud account.

> The model proposes. The engine validates. Accepted events establish the history. The narrator tells the story.

**Status: documentation-only bootstrap. No application, runtime integration, device benchmark, or release exists yet.** LocalLore is a working name, not a cleared trademark. The documentation is published at [OptimumAF/LocalLore](https://github.com/OptimumAF/LocalLore). Owner-reviewed pull requests protect `main`; private vulnerability reporting is enabled. See the verified setup details in project status. See [project status](docs/PROJECT_STATUS.md).

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
| [Development plan](DEVELOPMENT_PLAN.md) | Living milestones, task IDs, dependencies, acceptance criteria, and completion rules |
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

## Initial technical direction

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
