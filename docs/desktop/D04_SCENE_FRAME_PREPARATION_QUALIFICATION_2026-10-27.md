# Scene-frame preparation qualification

Refs #9 M05.03 and #25 D04.04, supporting preparation only. Generated prose
is unchanged. No new narrator recipe, quality acceptance or full task is claimed.
Base: accepted `6f6608bffb48b3b921ef30d3d9f85a3c208e10b0`.

## Implemented boundary

`Engine::stage_scene_play_v1` wraps the actual opaque V25 stage, retaining its
complete accepted-history basis and approved receipt/evidence. On a transient
clone it applies the actual canonical append and reads only the seed player's
self-location through `character_context_v2`, the same source policy used by
Player profiles. The clone is discarded; no candidate, cache or alternate state
is retained. The selected source's seed, history basis, records and canonical
projection stay unchanged.

The private, non-Clone/non-serializable native stage exposes its ordinary
approved receipt for native use, its existing sanitized narrator evidence, and
a closed serializable frame. The frame's six private fields are version, scope,
before revision, after revision, player ID and actual candidate location ID.
It has getters, no wire deserialization/public constructor, and contains no
location catalog, NPC position, world fact, observation, author reason or
Director context. There is no actor, observer or inspection-grant input.

Only a new Engine module and its declaration are production changes. Existing
Play execution, record schema, prompt/default/version IDs, commit/restore,
Host/storage/provider, literal/memory construction and frontend behavior are
unchanged. In particular this adds no commit API stub and sends no frame to a
model. The larger scene recipe in the source-only contract remains a proposal;
it still needs presentation/initial-world dependency reconciliation, opaque
commit/restore/capture closure and separate actual model/native qualification.

## Independent oracles and source review

The six-case test source was frozen before implementation (local integration
75c126fe, original bc0436cd). Its independent candidate uses the actual existing
Play2.5 pipeline and deterministic provider: exact typed Director output and
malformed narrator JSON force the existing mechanical fallback. The recorded
candidate's actual Player Query2 profile and self-context must agree. The new
frame and its complete serialization must match that value; the original
opaque stage's approved events and narrator evidence must remain identical.
These are engine-only synthetic-provider tests, not real-model execution.

At clean unchanged15a787056fd90fad9b8da0b8825eae5078142090 all6 pass.
Cases cover Say/Give/Use, accepted Move destination, invalid route, cancellation,
source preservation, and a corrected Domain2 child retaining observed A after
world correction B until an actual new Discovery observes B. Mira retains A;
the frame excludes both fact propositions and all private fixture fields.

Independent source review found no new privacy/source-authority defect, but
identified that the frozen cancellation threshold fires inside old staging.
Root added one calibrated late-cancellation test beyond all measured old-stage
callback polls, without changing the six frozen oracles or production. At
clean61a1962408b8b0ac3073ec529923cd6e3777b963 all7 focused cases pass.
This is phase/canonical preservation evidence, not a hard latency bound:
`character_context_v2` internally performs a noncancellable full-context walk;
the wrapper polls before and after it. No heap or cancellation-latency
qualification is claimed.

## Exact verification

Commands run from repository root with the existing isolated provisioned cache,
owned TEMP/TMP and target directory. All use Rust/Cargo1.93.1, locked/offline,
jobs1, incremental0, dev/test debug0 and ordinary uncapped SQLite flags.

| Source and command | Actual result |
| --- | --- |
| 15a: `cargo test -p locallore --test narrator_scene_frame_v1 --locked --offline --jobs 1 --target-dir $ownedTarget` | 6 passed/0 failed/ignored;20.682s command |
| 15a: `cargo test -p locallore --all-features --locked --offline --jobs 1 --target-dir $ownedTarget` | 424 passed/0 failed/4 historical opt-in ignored;58 summaries;114.688s |
| 61a: `cargo test -p locallore --all-features --test narrator_scene_frame_v1 --locked --offline --jobs 1 --target-dir $ownedTarget` | 7 passed/0 failed/ignored;1.300s |
| 61a: `cargo test -p locallore-storage -p locallore-workspace -p locallore-android --all-features --locked --offline --jobs 1 --target-dir $ownedTarget` | 483 passed/0 failed/7 explicitly ignored;74 summaries;426.477s |
| 61a: `node apps/desktop/verify-frontend.mjs` | PASS18.000s; strict TypeScript, all wired checks,60 receipt oracles and normal bundle exclusions |
| 61a: `cargo clippy --workspace --all-targets --all-features --locked --offline --jobs 1 --target-dir $ownedTarget -- -D warnings` | PASS49.586s; includes native compile checks |
| 61a: `cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --no-default-features --bin locallore-desktop-spike --locked --offline --jobs 1 --target-dir $ownedTarget` | PASS37.359s; normal native executable built, unlaunched |
| 61a: `cargo fmt --all -- --check` | PASS2.770s |
| 61a: `cargo tree -p locallore-android --target aarch64-linux-android --locked --offline` | PASS0.387s;0 Tauri/Wry/WebView2/local-runtime/llama hits |

Production is byte-identical at15a/61a;61a adds only the late test. Counts above
remain separately attributed and are not added into a fictitious single run.
The four Core ignores are historical capture/baseline-only cases. The seven
compatibility ignores are an explicitly capped SQLite qualifier, child-only
process helpers, an expensive16MiB archive qualifier, two real Windows symlink
cases and a superseded passive-open test. None is counted as a pass. No new
device/ABI/JNI/JVM/Gradle/emulator cohort, model/inference worker or UI journey ran.

Hashes at61a:

| Item | SHA-256 |
| --- | --- |
| New production module | `bd851b416efdb2421d667ce840b2eaa99a8017117801c735935739e09c2f9683` |
| Focused test source including late case | `9166e6cca4f7b1954c969cc3b41c4f3dec3c7c5ba448d233ab6301c1e54937ac` |
| Normal frontend | `77bbc6c0c75ddfa0243027d71a89c09ccac6a58c75771a7d53771dc10904084b` |
| Normal native executable, unlaunched | `17cb29648f2bdf414e21880f32d528b5282826b3cc50085e0af09f78d601e5f1` |

Windows NT10.0.26300 x64; Node24.22.1; TypeScript7.0.2; React19.3.1;
Tauri2.12.5/Wry0.57/Tao0.37.1. Python3.14.7 reads private timing records only.
No dependency, lock, model asset, repository/system setting or release change.

The owner's original eight-sample **needs improvement** assessment and all
historical reports remain unchanged. There are no new prose samples to assess.
The next narrator task is the new recipe's complete source-bound prompt,
presentation, record, commit/restore and actual forwarded-byte capture closure;
only then can a bounded approved-model cohort and new human assessment qualify
a narrative improvement. Whole-app offline and other desktop gates remain open.
