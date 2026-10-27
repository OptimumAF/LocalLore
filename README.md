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

The [original AUTHOR refusal diagnosis](docs/native/ORIGINAL_AUTHOR_DIAGNOSTIC_VERIFICATION_2026-10-27.md)
adds opt-in private response capture and one native diagnostic validator. Fresh
real-model import passes; native AUTHOR validation rejects the proposal's names.
The report preserves that failure and separates diagnostic evidence from creation.

The [original story authoring implementation](docs/native/ANDROID_ORIGINAL_STORY_AUTHORING_2026-10-27.md)
adds a bounded premise/cast generation path, editable world review and explicit
native creation. Its report distinguishes scripted plumbing, actual host/build
checks and pending real-model/device qualification. It is not an accepted release.

The [initial narration presentation](docs/native/ANDROID_STORY_PRESENTATION_2026-10-27.md)
adds native-reviewed tone and literal phrase exclusions, retained with the story
and checked before narration can commit. Its report separates host/build checks
from actual Android qualification and the remaining semantic/model gates.

The [initial player-name setup](docs/native/ANDROID_PLAYER_SETUP_2026-10-26.md)
adds an editable name and explicit native review before creating a story.
Its report records host/build checks, scripted native/player-setup execution,
and current-source creation/broad regression runs in separate fresh emulators.
Physical-model qualification and broader authoring remain in the milestone scope.

The [original starter choice](docs/native/ANDROID_STARTER_CHOICE_2026-10-26.md)
adds explicit selection of Lantern Quay fantasy rules or the original Bracken
Harbor narrative rules, with a native-owned preview before Create. Its report
records host/build and scripted emulator execution; physical-model gates remain
separate.

The [explicit starter review and named creation](docs/native/ANDROID_STORY_CREATION_VERIFICATION_2026-10-26.md)
adds a Rust-owned preview, an editable title and explicit Create/Cancel to the
persistent Android shell. The report records exact host/build/device evidence
and limits. Full premise, tone and character customization remain pending.

The [archive import follow-up](docs/native/ANDROID_ARCHIVE_IMPORT_FIX_2026-10-27.md)
uses a one-time content read and releases passive test readers. Fresh native10
and both retained-archive chooser methods pass on API35/x86_64, retaining the
original permission and canonical-history assertions. The report preserves
the original failures; physical-phone/model qualification remains separate.

The [retained-parent deletion UI qualification](docs/native/ANDROID_RETAINED_PARENT_UI_VERIFICATION_2026-10-26.md)
passes real Compose Cancel, explicit native deletion preserving a child's
original history, and stale-preview refusal after an independent parent turn.
The fixed two-method UI phase is separate from native component and lifecycle
checks. It uses scripted inference on API35/x86_64; phone/model gates remain separate.

The [current external restoration execution](docs/native/ANDROID_EXTERNAL_PROCESS_EXECUTION_2026-10-26.md)
passes the real scripted Compose/JNI/Rust root, active-child, retired-leaf and
selected-parent controls across two saved-task process deaths per case. Four original
snapshots preserve the retained child's inherited receipts and exclude the
parent's later tail. The report retains the failed setup attempt, the explicit
fork-recovery consent correction, host-validator correction and current verification.
This is API35/x86_64 evidence; phone and real-model qualification remain separate.

The [Android saved-task restoration check](docs/native/ANDROID_PROCESS_RESTORATION_VERIFICATION_2026-10-26.md)
exercises the real Compose screen and Rust storage across background process
death, including a selected second story and an unsent draft. It uses scripted
inference on an emulator; physical-phone and real-model qualification remain
separate gates.
An [active-child follow-up](docs/native/ANDROID_CHILD_PROCESS_RESTORATION_VERIFICATION_2026-10-26.md)
also exercises the real fork confirmation/resume flow and two child process
deaths, retaining the parent receipt and draft while a child turn leaves its
parent unchanged. Its host-verifier correction and remaining limits are recorded.
The [retired-child follow-up](docs/native/ANDROID_RETIRED_SELECTION_VERIFICATION_2026-10-26.md)
checks native retirement between save and restore, a visible fallback notice,
and clearing the unavailable timeline's draft. It also fixes stale editor
callbacks: rapid kind/text edits preserve both fields, and Send uses the latest
valid scoped draft. Phone and real-model qualification remain separate.
The [retained-parent implementation and preservation handoff](docs/native/ANDROID_RETAINED_PARENT_VERIFICATION_2026-10-26.md)
records interrupted verification and missing private evidence, including the
earlier retired-child index. Source is preserved; the new lifecycle case
requires a fresh owned run.
The [versioned host driver](docs/native/ANDROID_PROCESS_HOST_DRIVER.md) and its
[component verification](docs/native/ANDROID_PROCESS_HOST_DRIVER_VERIFICATION_2026-10-26.md)
retain fresh build, host and ten-method native component evidence. The current
external execution above records the separately qualified lifecycle scope.
The [external evidence validators](docs/native/ANDROID_EXTERNAL_CONTROLLER_HOST.md)
check original controller, producer and retirement records with synthetic host
regressions; their tests do not establish a new Android lifecycle result.

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

The [2026-10-25 admission reassessment](docs/native/EMULATOR_COMMIT_REASSESSMENT_VERIFICATION_2026-10-25.md)
corrects an unsupported 18 GiB host commit cutoff to an explicit 10 GiB project
budget for the unchanged 8 GiB emulator. Actual startup and 12 preflight checks
pass without stopping other emulators or changing system settings. Two original
1 GiB transfer controls pass; an alternate shell path fails its binary prerequisite
and is refused. A connected Samsung ARM64/4 KiB phone also passes nine actual
Rust JNI/SQLite tests with fake inference. These establish no new phone model
performance or playable-scene qualification.

The subsequent [Windows binary staging and scene run](docs/native/WINDOWS_BINARY_TRANSFER_VERIFICATION_2026-10-25.md)
reproduces the text-mode truncation mechanism and refuses the unsafe Windows
shell route. A fresh isolated receipt test build passes **122 app checks**:
full local model import, actual SDK Gift and literal Dialogue validated/committed
by Rust, inspector/invalid-action guards, and a new-process reopen of both
receipts without inference. This qualifies the current codec for that original
emulator fixture; phone model performance and production backend selection
remain pending. Historical failures are preserved.

The separate [physical-model harness](docs/native/PHYSICAL_MODEL_HARNESS_VERIFICATION_2026-10-25.md)
now builds the six guarded phone phases, with 488 JVM tests and a signed APK
pair audit passing. The selected USB phone was absent at the initial refresh;
these host/build checks establish no phone import or inference result.

Separate [Android model-storage receipt checks](docs/native/RECEIPT_FRESH_TARGET_VERIFICATION_2026-10-24.md)
passed four methods on a fresh isolated emulator, including cancellation and
owned process-death recovery, using a tiny synthetic file. Existing-target
staging headroom remains held. An explicit debug-only
[receipt-backed setup route](docs/native/RECEIPT_SETUP_FAILURE_TRACE_VERIFICATION_2026-10-24.md)
passes three initial synthetic setup methods and a separate-process reopen on a
fresh emulator, with all44 proof checks and owned cleanup verified. Earlier
START-only and READY-timeout attempts remain documented; their causes are unknown.
The positive run emitted no failure status. A separate
[controlled failing test](docs/native/RECEIPT_SETUP_FAILURE_TRANSPORT_VERIFICATION_2026-10-24.md)
delivered the bounded record and preserved its original error; it does not
diagnose the earlier timeout.
The earlier [real-candidate probe](docs/native/RECEIPT_REAL_CANDIDATE_VERIFICATION_2026-10-24.md)
is compiled and host-tested; its fresh8 GiB emulator preflight verified tiny
local staging and capacity. The owner has now authorized the new test-app
destination. The [authorized execution](docs/native/RECEIPT_REAL_EXECUTION_VERIFICATION_2026-10-24.md)
records the earlier successful full-model receipt import after a tested bounded I/O
correction. Its PLAY attempt stopped at the inference-ownership fence before
an accepted gift or restart. The
[earlier partial result](docs/native/MODEL_RECEIPT_ANDROID_VERIFICATION_2026-10-24.md)
is preserved. [Closed worker-stage observations](docs/native/LITERT_WORKER_TRACE_CONTRACT.md)
expose no prompts or private errors. A separately admitted
[C-root follow-up](docs/native/RECEIPT_C_ROOT_EXECUTION_VERIFICATION_2026-10-25.md)
passes full import and records a first SDK terminal/close observation before a
second conversation attempt lacks a return. The subsequent
[role-aware timed run](docs/native/LITERT_WORKER_TIMING_VERIFICATION_2026-10-25.md)
passes import and observes42.175s from director send to DONE; narration starts
59.580s after trace creation near the60s turn deadline and PLAY fails its ownership fence. This does
not establish a long second-creation hang. A separately admitted
[fresh four-core run](docs/native/RECEIPT_FOUR_CORE_VERIFICATION_2026-10-25.md)
now passes 56 protocol checks: full local model import, one actual SDK gift
validated/committed by Rust, and a new-process reopen of the unchanged receipt
without inference. This is a synthetic emulator proof; phone, sustained-use,
DocumentsUI and performance qualification remain open. Earlier failures are retained.
The subsequent [real cancellation/recovery control](docs/native/RECEIPT_REAL_CANCELLATION_VERIFICATION_2026-10-25.md)
passes 82 checks across five emulator methods. It verifies the Main-thread
gateway API's actual SDK cancellation with unchanged canon, then a new-process
gift and no-inference reopen. Cancellation latency and broader phone
qualification remain open.
The [real Compose control](docs/native/RECEIPT_COMPOSE_CANCELLATION_VERIFICATION_2026-10-25.md)
passes 95 checks across five fresh-emulator methods: actual New story/Send/Cancel,
unchanged cancelled canon, a real recovery gift and another-process visible
reopen of the same receipt without inference. Stable accepted-message IDs keep
transcript checks distinct from retained draft text. The initial visibility
failure is preserved; its discarded cause remains unproven. Whole-test timings
do not measure cancellation latency or qualify physical-phone performance.
The [ordinary setup route](docs/native/RECEIPT_ORDINARY_ROUTE_VERIFICATION_2026-10-25.md)
now passes the actual setup READY/Start transition into `LiteRtPlayActivity` and
one real, Rust-committed gift on a fresh emulator: 56 qualified checks including
preflight/import. Its later inspector/dialogue method fails inside the director
send wrapper; no Dialogue receipt or ordinary-route reopen is qualified. The
retained trace does not identify the discarded exception or prove SDK async-call
entry. The next gate is a bounded observation separating argument construction
from SDK invocation, while preserving quarantine and the existing deadlines.
The [portable Dialogue follow-up](docs/native/LITERT_SEND_BOUNDARY_VERIFICATION_2026-10-25.md)
replaces a known unsupported schema keyword with bounded choices covering every
permitted audience set. Its fresh ordinary Start/gift passes again. Dialogue now
returns from the public SDK call and receives 21 message callbacks before an
asynchronous error; no accepted Dialogue or ordinary-route reopen is qualified.
The new privacy-safe send record works on the actual failure path. The async
error's cause remains unknown; all owned processes stopped and evidence is sealed.
The [closed callback follow-up](docs/native/LITERT_CALLBACK_VERIFICATION_2026-10-25.md)
again passes import and the ordinary Start/gift. Its actual failure record shows
one SDK JNI-category error after 21 accepted chunks/61 UTF-8 bytes; configured
request sizes are recorded without text. These are not token counts or an error
diagnosis. Dialogue and ordinary-route reopen remain unqualified; all owned
processes stopped and evidence is sealed. Safe native-status retention is the
next investigation, with the existing privacy and ownership fences preserved.
The [wrapper-declared status follow-up](docs/native/LITERT_STATUS_VERIFICATION_2026-10-25.md)
tests a receipt-only bounded prefix bridge: the wrapper declares code13/INTERNAL on
the actual Dialogue failure, after 15 validated chunks/58 UTF-8 bytes. It retains
no private error payload and grants no resource or gameplay authority. Import
and the real ordinary gift pass again; Dialogue and ordinary restart remain
unqualified. A host grammar oracle is the next experiment; the cause is unproven.

The [format and tokenizer follow-up](docs/native/SDK_FORMAT_TOKENIZER_VERIFICATION_2026-10-25.md)
records the actual prepared REGEX argument on a fresh Dialogue failure. Import
and the real Rust-committed gift pass again; Dialogue and ordinary restart remain
unqualified. The selected SentencePiece vocabulary has no raw ASCII-space pieces.
Native controls retain every original sample and expose representation/callback
limits; they do not establish the SDK failure's cause. All owned emulator
processes are stopped, and earlier failures remain preserved.

The [JSON spelling controls](docs/native/JSON_SPELLING_VERIFICATION_2026-10-25.md)
preserve decoded speech while allowing bounded equivalent space/Unicode escapes.
Rust, JVM and native controls pass their stated scopes; both fresh attempts
stop during model copy before SDK execution. A bounded host trace identifies a
client timeout with a partial host read on the second attempt. Import, corrected
Dialogue and restart remain unqualified.

The [original synthetic transfer probe](docs/native/RECEIPT_TRANSFER_PROBE_VERIFICATION_2026-10-25.md)
adds fixed local copy controls and a Windows commit-capacity guard. Its host
checks pass; the first emulator exits before preflight for insufficient commit
headroom. No transport speedup or new inference result is qualified.

An opt-in [current Rust play probe](docs/runtime/android/PLAY_PROTOCOL.md) connects
the isolated SDK to guarded free-text preparation and durable commit. Its
[verification](docs/runtime/android/PLAY_VERIFICATION_2026-10-23.md) establishes
host/build and missing-model cleanup checks; that separate probe's real-generation
qualification remains pending.

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

The [finite-schema SDK correction](docs/native/LLGUIDANCE_LITERAL_VERIFICATION_2026-10-25.md)
uses exact public regex constraints for supported finite schemas. Actual Kotlin
output passed215 native byte-mask cases, and both Android variants passed host
tests and package audits. This addresses a reproduced escaped-literal compiler
tail omission; it does not establish the cause of earlier SDK errors or qualify
the full real-model scene. The [fresh Android follow-up](docs/native/LLGUIDANCE_LITERAL_VERIFICATION_2026-10-25.md#second-fresh-attempt-import-and-real-gift-pass-dialogue-still-fails)
passes full receipt import and one ordinary Rust-committed SDK gift. Dialogue
still reports INTERNAL13, so its restart check remains unrun. The actual SDK
format selection and model-tokenizer failure need further investigation.

The [isolated LLGuidance development oracle](docs/native/LLGUIDANCE_ORACLE_PROTOCOL.md)
exports actual engine Dialogue schemas and checks their exact bytes with a
pinned host compiler. It uses original synthetic fixtures and no model or SDK;
its result does not qualify real inference or a phone.

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
