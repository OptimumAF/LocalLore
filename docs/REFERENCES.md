# Primary references and research notes

Checked while preparing these documents on 2026-10-22. This is a source index, not a claim that every referenced capability was tested in this project. Pin exact dependency/model revisions during implementation and recheck changing APIs/licenses.

| ID | Primary source | Relevance and limit |
|---|---|---|
| S01 | [SQLite transactions](https://sqlite.org/transactional.html) | Atomic transaction semantics; app-level staging/idempotency still require correct design and testing |
| S02 | [SQLite FTS5](https://sqlite.org/fts5.html) and [foreign keys](https://sqlite.org/foreignkeys.html) | Local full-text search and constraints; verify build options and per-connection enforcement |
| S03 | [llama.cpp Android documentation](https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md) | Native Android integration path; not a benchmark for this app |
| S04 | [llama.cpp grammars](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md) | Constrained generation and schema conversion limitations; structural validity is not semantic correctness |
| S05 | [LiteRT-LM overview](https://developers.google.com/edge/litert-lm/overview) | Official local inference/runtime direction; actual backend/device support needs verification |
| S06 | [Gemma model overview](https://ai.google.dev/gemma/docs/core) and [official E4B model card](https://huggingface.co/google/gemma-4-E4B-it) | Small mobile/edge candidates; no project-specific speed or quality claim |
| S07 | [Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B) | Candidate identity and published model details; conversion/runtime compatibility is a separate test |
| S08 | [Qwen3.5-4B license](https://huggingface.co/Qwen/Qwen3.5-4B/blob/main/LICENSE) | Artifact-specific terms; verify the exact downloaded revision/conversion |
| S09 | [Android Auto Backup](https://developer.android.com/identity/data/autobackup) | App databases/files may be backed up; configure and test exclusions and transfer behavior |
| S10 | [Generative Agents, Park et al., 2023](https://arxiv.org/abs/2304.03442) | Memory/reflection/retrieval/planning precedent; not a mobile implementation or consistency guarantee |
| S11 | [GitHub code owners](https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) | Review ownership and enforcement prerequisites |
| S12 | [GitHub rulesets](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) and [rules REST API](https://docs.github.com/en/rest/repos/rules) | Active controls and bypass semantics; documentation files do not apply them |
| S13 | [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.txt) | Full license terms; local LICENSE contains the standard text |
| S14 | [GitHub CLI repository creation](https://cli.github.com/manual/gh_repo_create) | Owner-run creation of a new public repo; no creation was performed in this documentation session |
| S15 | [GitHub branches API](https://docs.github.com/en/rest/branches/branches) | Branch reads/renaming for setup; exact available permissions must be verified |
| S16 | [GitHub CLI API](https://cli.github.com/manual/gh_api) and [repositories REST API](https://docs.github.com/en/rest/repos/repos) | Owner-run publisher transport, creation, and private reporting; not executed live here |
| S17 | [GitHub Actions permissions API](https://docs.github.com/en/rest/actions/permissions) | Documentation-stage Actions control; requires actual permission and read-back |

| S18 | [GitHub reporting abuse or spam](https://docs.github.com/en/communities/maintaining-your-safety-on-github/reporting-abuse-or-spam) | Bootstrap reporting route in ADR-0002; no report was submitted |

## Interpretation rules

External sources establish available APIs, model identities, and research patterns. Architecture, milestone ordering, token budgets, latency targets, privacy requirements, and evaluation gates in this repository are project proposals. Do not present them as conclusions proven by the sources.

Do not reuse old device assumptions, unverified benchmark numbers, third-party marketing claims, or generated citations. Add a source, exact revision/date, and reproducible measurement when a factual choice depends on changing software or hardware.
