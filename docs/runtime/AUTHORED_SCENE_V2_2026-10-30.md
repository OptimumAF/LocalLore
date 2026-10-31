# Authored scene V2: implementation and verification

B35, started2026-10-30; final host checks2026-10-31. Refs #9 (M05.03),
#14 (M10.04 supporting reliability). Implemented and locally verified; owner
acceptance, Android adoption and device/model qualification remain separate.
GitHub Issues remain the live tracker; no milestone checkbox is closed here.

## Result and contract

The explicit native MemoryAuthoredSceneV2 and PlayerLiteralAuthoredSceneV2
selectors let Core and the durable Host narrate authored stories through the
existing deterministic fake-provider pipeline. The engine validates and commits
accepted outcomes; narrator prose cannot establish canonical facts. Defaults,
Android wire/Kotlin selection and old scene V1 authored-world refusal remain.
Starter seeds refuse V2; a consumer serving both must deliberately select the
appropriate native recipe rather than globally replace its default.

The [frozen interface](AUTHORED_SCENE_V2_CONTRACT.md) defines opaque staged/bound
capabilities and a read-only version2 frame. The frame contains scope, revisions,
player, actual candidate location and an optional typed location label with fact
and observation provenance. Only the exact original materialized seed fact in
that player's observations permits the label. Move alone does not reveal it.
An unseen correction preserves remembered knowledge; observing corrected free
text with no typed mapping removes the label. Ancestor provenance retains its
original scope. No proposition parsing supplies a name.

The added frame excludes descriptions, other locations, raw author origin,
private NPC data, beliefs and hidden corrections. Existing narrator evidence
still includes exact propositions of discoveries accepted in this turn. Such
an observation is legitimate evidence, not permission to parse a typed label or
read unrelated origin data. The observation/world-truth distinction remains.

Binding and commit regenerate the full accepted-history basis and candidate
frame. Cancellation and stale-history refusal leave canonical state unchanged.
Durable restore validates exact recipe/prompt/policy/context/presentation/hash
joins; recorded retry returns the prior receipt without inference or an append.
No canonical event, provider role/schema or storage field was added. The existing
scene record shape uses version2 and its exact serialized frame hash.

Prompts are `locallore-play-v2.11-authored-scene-frame-v2` and
`locallore-play-v2.12-literal-director-v1-authored-scene-frame-v2`;
policy is `grounded-prose-v2.8-authored-scene-frame-v2`. Baseline policies through
2.7 and V1 interpretation remain intact. Intermediate unmerged B35 experiments
are not a new historical compatibility family or permission to retag receipts.

Only complete eligible label spans extend visible-name authority. Hidden-ID,
effect, knowledge and complete evidence-word checks remain. The V2 English
first-person guard segments original alphanumeric and Unicode Mark characters
before case folding, preserving names such as composed İpek and decomposed
I-plus-mark. Punctuation and contractions still expose actual pronouns. V1 keeps
its original guard. This is a finite lexical check, not semantic entailment,
general Unicode normalization or creative-quality proof.

## Source, ownership and dependency

Base is open/unmerged PR #300 at
`efaab06499a8e4a4a9324c0b464400ae0d529090`, itself stacked on PR #297.
Final executable source is `0a50c294c9faaa2087e38edee5612b7f61d8e401`.
Subsequent reporting changes are documentation only. Newer main was separately
`eab64f7625de48b8d18e139226223fb4c6f11791`; these checks do not qualify its
integration. No merge or history rewrite was performed.

Root integrated shared APIs, restore dispatch, Host selectors and consumer
lock/license changes in `D:/Worktrees/LocalLore-authored-scene-v2`. Independent
implementation work owned only the two new modules in the `-core-v2` worktree;
independent fixture work owned only the two new test files in `-tests-v2`.
Their final source commits are respectively `1a90d5f7` and `8044b736`.
Read-only source/dependency/storage/evidence review was separate from both.
No agent ran unadmitted project builds or edited another writer's files.

The exact `unicode-general-category =1.1.0` utility provides Mn/Mc/Me categories
from Unicode16.0, is no_std, Apache-2.0, edition2018, has no runtime dependencies
and declares no MSRV. Before selection, current official tagged
[manifest](https://github.com/yeslogic/unicode-general-category/blob/1.1.0/Cargo.toml),
[source](https://github.com/yeslogic/unicode-general-category/blob/1.1.0/src/lib.rs),
[build script](https://github.com/yeslogic/unicode-general-category/blob/1.1.0/build.rs)
and [license](https://github.com/yeslogic/unicode-general-category/blob/1.1.0/LICENSE)
were inspected. The build generates bundled tables under Cargo OUT_DIR, without
network/model/device behavior. Newer Unicode characters may conservatively
fall back. Rust1.93.1 host and both Android JNI targets compile this version.
The evaluated XID-continuation alternative was not selected: identifier
continuation includes punctuation outside the required category contract.

[Dependency provenance](AUTHORED_SCENE_V2_DEPENDENCIES.json) records the crate
checksum and notice. One new package and the Core dependency edge were added
to each of the three lockfiles; every old package record was conserved
(414/43/41 before). No runtime source, model pin/profile, backend or role changed.
The actual desktop-selected graph has257 packages (251 registry,6 local).
Its catalog preserves the previous256 rows and all unrelated fields, with
review_complete/distribution_approved still false. Actual public notice
collection reads468 material files/2,899,873 bytes including the new notice.
No executable/model was run or copied by that file-only collection.

## Closed verification

All final rows below use executable source0a50c294. Commands ran physically on
D: with Rust1.93.1, locked/offline dependency resolution, two build jobs,
debug/incremental disabled, installed tools unchanged and D: caches/targets.
Each retained worker record binds source hashes, helper, actual child identity,
return code, complete output capture and owned-process cleanup. Listed durations
are owned-job elapsed time including supervision/cleanup, not benchmarks or
device performance. Public project
commands shown below omit only the installed executable's absolute location.

| Check | Exact command | Result |
| --- | --- | --- |
| Core | `cargo +1.93.1 test --locked --offline -p locallore --features host --all-targets` |590 passed,5 intentional ignores;71 summaries;58,358ms |
| Storage/Host/Android Rust | `cargo +1.93.1 test --locked --offline -p locallore-storage -p locallore-workspace -p locallore-android --features locallore/host --all-targets` |523 passed,7 intentional ignores;83 summaries;175,513ms |
| Strict Clippy | `cargo +1.93.1 clippy --locked --offline -p locallore -p locallore-storage -p locallore-workspace -p locallore-android --features locallore/host --all-targets -- -D warnings` |pass;15,318ms |
| Formatting | `cargo +1.93.1 fmt --all -- --check` |pass;2,539ms |
| Eval consumers | `cargo +1.93.1 check --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --all-targets` |compile only;9,915ms |
| Runtime adapter consumers | `cargo +1.93.1 check --locked --offline --manifest-path crates/locallore-local-runtime/Cargo.toml --features engine-adapter --all-targets` |compile only;6,277ms |
| License tests | `python -I -S -B scripts/desktop-license-tests.py` |18 passed;1,230ms |
| Public license collector | private file-only caller of public `scripts/desktop-package.py` collector |257 packages/468 files;2,846ms |
| Default Android check | `python -I -S -B scripts/check.py android --offline` |both JNI targets/APKs and product audit passed;118,317ms |

The new15 Core and4 Workspace methods are included in the totals, not additional
passes. Original adversarial cases cover typed/no-label paths, actual Domain2
correction/rediscovery, full-label and Unicode boundaries, hidden-ID collision,
sibling/ancestor/head/history isolation, metadata tampering, actual canonical
restore, final-install cancellation, stale competing Host commits, exact retry
and no-inference durable reopen with the opposite selector/provider trap.

Android uses the normal default product profile, not an isolated paired-profile
qualification. At earlier source`acf55a42`, the fresh first build ran324 JVM
cases across38 XML suites with zero failures/errors/skips, plus fresh lint
(zero errors,one warning). Kotlin/Java/instrumentation/Gradle sources are
unchanged through0a50c294. At final source, both ARM64/x86_64 JNI libraries
rebuilt; JVM and lint report tasks were UP-TO-DATE. Do not count324 fresh JVM
executions at the final head. The product audit checks four libraries,
16,384-byte ELF LOAD alignment and only its custom signature receiver permission.
No Android app or native library was executed on a device for B35.

Sealed final APKs: product37,309,928 bytes,
SHA256`e0f322375a865c797ffcf19aa0b4e5cb396abf5560ae06024ae530694407708e`;
test2,188,835 bytes,
SHA256`40be63e5cb67f2dfdbc8a7cdc9509774962d9ef827ab3f5deee5542cb9ecd33f`.
Both earlier and final41-file sets (38 JVM XMLs, lint XML,2 APKs) are retained
with hash rosters. APK size is not a runtime-memory or dependency-size benchmark.

## Preserved failures and corrected assumptions

The unchanged old V1 baseline passed16 cases. The first B35 Core run had6
passes/4 failures: three fixture setup errors and one real composed-İ name
failure from lowercasing before tokenization. Workspace initially had3 passes
and one fixture error. Fixes used actual supported staging/typed actions without
relaxing assertions. A coordinator conflict-resolution mistake briefly committed
markers at406a70ad; its actual compile failure remains retained. Exact
independent fixtures were restored at e969c824;10 Core methods then passed.

Independent later fixtures expanded Core to15. An intermediate broad-non-ASCII
token fix really failed the fullwidth-comma `me` case at2c7c4a62 (14 passes,
one failure). The other two candidates in that loop were not reached during
that failing execution. Final original alphanumeric-plus-Mark segmentation
passes all three punctuation negatives, composed/decomposed names and actual
English pronouns/contractions. The earlier failed captures remain immutable.

Initial0.5–1.5GiB, then0.8–2.7GiB forecasts were too low. PDB/executable output
made the original4GiB admission's3.5GiB stop trigger in compat-v1. It closed
after19,066ms with worker1, zero test stdout and no completed command result.
It is an incomplete attempt, not a passing test suite. Its measured closure
was3,862,396,251 bytes, below the original hard cap. No old cap or capture changed.

A separately recorded cumulative host closure admission uses8GiB hard cap,
7GiB stop across the same roots, every prior byte still charged, plus an owned
future TEMP allowance. Compat-v2 functionally passed523/7, but the operator
observed a watcher FileNotFoundError on a disappearing SQLite fixture in PTY
session36760. This is retained in `operator-observations-v1.json`; no separately
sealed parent stderr exists, and the owned worker stderr does not prove that
exception. Compat-v2 does not establish continuous monitoring. The corrected
meter counts expected disappearing files
only under named generated/temp roots; source/permission/unexpected errors stop
the job. Three synthetic meter guards passed. Compat-v3 repeated the actual
suite successfully with two expected disappearances and no unexpected errors;
all later closure checks also have no unexpected meter errors. No test boundary
or original failure was removed to make a result pass.

## Retention and limits

Private controls/captures are under
`D:/Dev/Experiments/LocalLore/2026-10-30-authored-scene-v2`.
Selected compact recovery is under
`D:/Dev/Recovery/LocalLore/2026-10-30-authored-scene-v2`; its exact hash/roster and
verification are posted with the implementation PR. Selection preserves small
controls, raw successes/failures, reviews, changed source and sealed APK/XML
artifacts. It excludes build targets, dependency caches, weights, signing keys,
guest images and the rest of the repository. Originals/targets remain; no cleanup.

The cumulative8GiB admission includes all three B35 worktrees, the evidence and
recovery roots, and `D:/Dev/_Temp/LocalLore-B35-closure-v1`. This future owned
TEMP has a512MiB cap/384MiB stop; outer launchers retain D:/Dev/_Temp. Earlier
shared TEMP/global cache changes are not fully attributable. Logical path-size
observations are not aggregate peak use, an OS quota or complete cache accounting.
The last check closure measured4,839,251,053 bytes including80,480,680 bytes of
owned TEMP, before compact recovery. Final selection/observed size are recorded
separately. Existing generated output, including the D-to-D read-only dependency
junction used for notices, stays charged by the same accounting method.

Source/dependency review found no additional blocker at0a50c294; it verified
V1 preservation, the category boundary and exact lock/catalog deltas. Independent
closed-evidence/document review is recorded beside the retained controls;
recovery review follows preservation and must close before PR publication.
Review is evidence, not owner acceptance or distribution approval.

No guest, AVD ledger, shared ADB service, other emulator, phone, model cache or
system setting was changed in B35. M01.01/M01.02 and M10.05 physical-device gates
remain blocked/unverified. No real-model inference, creative quality, ARM64
execution, causal Android process-death restart, privacy or release acceptance
is established here. Next runnable work is a deliberate mixed starter/authored
native consumer selector with Core/JVM ownership tests; another device run
requires its own applicable authorization.
