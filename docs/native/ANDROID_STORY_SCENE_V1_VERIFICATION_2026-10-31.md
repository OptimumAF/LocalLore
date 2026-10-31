# Android story scene selection: verification

B36, 2026-10-31. Refs #9 (M05.03), #14 (M10.02 supporting ownership).
Implemented and host/packaging verified; full milestone criteria and owner
acceptance remain open. GitHub tickets are the live tracker.

## Behavior and authority

Android's existing external-inference Bridge now explicitly configures native
MemoryStorySceneV1(StateRelevantMemoryV1). For each validated Engine seed,
initial_world absent selects the existing MemorySceneV1; present selects
MemoryAuthoredSceneV2. An authored seed starts in Domain1; actual author
correction may produce Domain2. Domain number, profile JSON, model text and
Kotlin state never choose the recipe.

The pure native resolution rule supplies trace labels from the selected seed
and executes again against the actual coherent generation snapshot. The existing
exact-seed and accepted-history-prefix checks fence those reads. Each prepare
resolves independently, allowing starter → authored → starter on one owner
without a cached choice. Concrete check_seed runs before provider construction;
there is no non-scene fallback on refusal.

The engine validates proposals before narrator input and commits the checked
turn atomically. Ready remains transient. Cancellation/stale/closed work cannot
partially append, and exact recorded retry/reopen does not invoke inference.
Typed observed labels keep PR302's distinction between observation and hidden
truth, including unseen corrections and unmapped corrected free text. Move alone
does not grant knowledge. Summaries and narrator claims never replace events.

Existing Host default and fixed constructors retain their behavior. Ordinary
WorkspaceRegistry::open uses its existing scripted fixture. The existing
open_local/JNI path reaches the same Bridge, lease, Host and SQLite owner;
no second registry/provider or Kotlin gameplay rules were added. Request keys
remain version, role, prompt, max_tokens, context_tokens, threads and schema;
32,768-byte request, profile/response/poll limits, ticket ownership and one-shot
responses remain. JNI, Kotlin lifecycle code, runtime/profile/model pins and
all three Cargo locks are unchanged from the base. No new dependency, SDK,
prompt/policy/frame version or canonical-storage schema was introduced.

The [frozen contract](ANDROID_STORY_SCENE_V1_CONTRACT.md) records interfaces,
ownership and acceptance. The concrete starter prompt/policy remain
locallore-play-v2.9-scene-frame-v1 /
grounded-prose-v2.7-scene-frame-whole-evidence-words-v1; authored remains
locallore-play-v2.11-authored-scene-frame-v2 /
grounded-prose-v2.8-authored-scene-frame-v2. Old records keep their original
interpretation; new native configuration cannot retag them.

## Source and independent fixtures

Base is open/unmerged PR302 at
e9086c24ff655457e5676974fc0c44d61831506d, itself stacked on PR300/PR297.
Final executable source is db068cc342b1a0ca5630e37695d203e0e2fb875b;
later reporting changes are documentation only. These checks do not qualify
integration with newer main. No merge or history rewrite was performed.

Root branch impl/m05-android-story-scene-v1 is at
D:/Worktrees/LocalLore-android-story-scene-v1. Root owns the two production files,
docs and execution. Separate Host and Android FIRST writers own only their new
tests/story_scene_selection.rs files in the corresponding
LocalLore-story-scene-host-tests-v1 and LocalLore-story-scene-android-tests-v1
worktrees. Frozen source commits are respectively4168ed85 and0c2f6bfb; the
Android setup correction is33c50e8d. App worktree creation refused the nested
sourceRoot; isolated physical D: Git worktrees preserved frozen predecessors.

Seven original Host methods exercise the same owner alternating story kinds,
exact rendered frame hashes and trace labels, corrected branches of both kinds,
parent conservation, durable retries with provider-constructor traps, cancelled
Ready work, stale candidates, foreign scope, noncooperative late output after
close and fixed/default compatibility. Five Android Rust methods exercise actual
Registry/open_local/Bridge/SQLite, mixed stories, Domain2 correction/rediscovery,
move-before-discovery, typed source provenance, private canaries, transient Ready,
foreign/cancelled/closed tickets, stale competitors and no-inference reopen.
Workers have bounded waits and unwind-safe close/release-before-join guards.
All inference output in these tests is synthetic.

## Actual baseline and corrections

Before production edits, baseline7a019afa stopped at compilation: Receipt
intentionally has no Deserialize, but the fixture tried serde_json::from_value.
No tests ran. The owned job closed in17,087ms with worker101 and complete
capture/cleanup. Independent setup-only correction33c50e8d reads the typed
committed receipt from the actual validated Store and adds equality with its
serialized wire reply; every original behavioral assertion remains.

On unchanged production at f145f06d, all five Android methods then ran:
one passed and four failed at the intended scene assertion, actual None versus
expected starter1/authored2. The owned job closed in2,033ms with worker101;
raw output, source/helper/admission bindings and failed databases are retained.
This is behavioral RED. After native selection/adoption, all five pass. Host
tests reference the new enum and were not presented as an executable pre-API
behavioral baseline.

Root only formatted the frozen tests. Independent comparison verified original
assertions/literals, allowing rustfmt trailing commas and exactly two witnessed
closure/match-arm brace wraps. Its first overstrict file-only comparison reader
refused these formatting edits; that failure is preserved separately from the
successful corrected reader. No product assertion was weakened.

## Closed checks at executable db068cc3

Commands ran physically on D:, using installed Rust1.93.1/JDK21 and existing
D: dependency caches. Cargo checks use locked/offline resolution, two build jobs,
debug/incremental disabled and one new bounded target. No dependency fetch,
device call or model execution was needed. Durations below are owned-job elapsed
time including supervision/cleanup, not benchmarks. Each job binds2,319 source
hashes, exact source head, fixed command, helper, global and per-job admissions,
actual child identity, exit, complete streams and positive owned closure.

| Check | Command | Result |
| --- | --- | --- |
| Android owner FIRST | `cargo +1.93.1 test --locked --offline -p locallore-android --test story_scene_selection -- --test-threads=1` |5 pass;10,065ms |
| Host FIRST | `cargo +1.93.1 test --locked --offline -p locallore-workspace --features locallore/host --test story_scene_selection -- --test-threads=1` |7 pass;3,348ms |
| Core | `cargo +1.93.1 test --locked --offline -p locallore --features host --all-targets` |590 pass/5 intentional ignores;71 summaries;59,918ms |
| Storage/Host/Android Rust | `cargo +1.93.1 test --locked --offline -p locallore-storage -p locallore-workspace -p locallore-android --features locallore/host --all-targets` |535 pass/7 intentional ignores;85 summaries;213,868ms |
| Strict Clippy | `cargo +1.93.1 clippy --locked --offline -p locallore -p locallore-storage -p locallore-workspace -p locallore-android --features locallore/host --all-targets -- -D warnings` |pass;15,067ms |
| Formatting | `cargo +1.93.1 fmt --all -- --check` |pass;2,337ms |
| Eval consumers | `cargo +1.93.1 check --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --all-targets` |compile only;7,741ms |
| Runtime consumers | `cargo +1.93.1 check --locked --offline --manifest-path crates/locallore-local-runtime/Cargo.toml --features engine-adapter --all-targets` |compile only;5,671ms |
| Default Android | `python -I -S -B scripts/check.py android --offline` |pass;240,510ms |

The new7+5 methods are included in535, not additional passes. Existing ignores
remain. No full Eval benchmark or model-dependent tests were executed.

Android ran324 JVM cases across38 XML suites, zero failures/errors/skips;
the actual testDebugUnitTest task executed, not UP-TO-DATE or FROM-CACHE.
Both Rust JNI ABIs and product/test APKs built. Fresh lint has zero errors and
one existing dependency-version warning; an existing instrumentation compiler
warning about AtomicReference<Boolean?> is separate from lint. The normal
product audit passed four libraries,16,384-byte ELF LOAD alignment and its
custom signature receiver permission. This is the default profile, not complete
paired-profile qualification or Android runtime execution. Existing JVM owner
tests verify lifecycle plumbing; they do not prove the new JNI path on a device.

Sealed product APK:27,907,292 bytes, SHA256
93780a0abaa7d970f28794e29591f690dc955492fc5ff711717c1f0915539239.
Test APK:2,188,835 bytes, SHA256
40be63e5cb67f2dfdbc8a7cdc9509774962d9ef827ab3f5deee5542cb9ecd33f.
All41 artifacts (38 JVM XMLs, lint XML and2 APKs) have verified copy/hash rosters.

## Review, retention and remaining gates

Independent source review at db068cc3 found no concrete blocker, conserving
fixed/default recipes, exact-seed/prefix fences and provider/ticket/bounds code.
Receipt review-source-v1/source-review-v2.json SHA256
6e5f6734f39209b4defb30eaa3fb6f43efb12a4e0812c6cb16521285566ac877.
Closed-evidence/document review and selected recovery readback follow before
PR publication. Model review is evidence, not owner acceptance.

Private controls/raw successes and failures are under
D:/Dev/Experiments/LocalLore/2026-10-31-android-story-scene-v1; selected compact
recovery is under D:/Dev/Recovery/LocalLore/2026-10-31-android-story-scene-v1.
Exact selection/hash/readback is posted with the PR. Preserve original controls,
failed captures/databases, source worktrees, ignored files and build targets.
Recovery includes small controls, changed source and sealed APK/XMLs; it excludes
targets, dependency caches, weights, keys, guest images and full-repository bundles.

Declared forecast is3–6GiB retained; unchanged packet cap8GiB/stop7GiB includes
all three new worktrees, evidence, recovery and future owned TEMP
D:/Dev/_Temp/LocalLore-B36-host-v1 (512MiB cap/384MiB stop). Launchers set
TEMP/TMP to D:/Dev/_Temp. Previous B35 roots remain separately retained; the
combined B35/B36 forecast is8–11GiB, not a reset or deletion of old bytes.
The last check closed at3,583,832,408 logical bytes including45,177,045 owned
TEMP bytes, before compact recovery. Compat counted four expected disappearing
generated files and zero unexpected meter errors; all other final checks also
have no unexpected meter errors. Source/permission/unknown accounting errors
remain fail-closed. Shared global caches/Git metadata are not fully attributed;
observed named-path size is not aggregate peak use or a system quota.

Prior bounded emulator grants remain spent; no emulator/phone/ADB/model/app action, AVD ledger
change, unrelated-emulator stop, system setting, cleanup, release or merge occurred.
M01.01/M01.02/M10.05 device gates remain blocked/unverified. New-source emulator,
physical-phone/ARM64 execution, real inference, story quality, joined SDK drain,
causal Android OS-death restart, privacy and release acceptance are not established.
Next runnable independent implementation is M09.04's remaining Query1 inspector
sections for corrected Domain2 histories; current native scene adoption still
requires separately authorized device/model qualification and owner review.
