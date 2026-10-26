# Selected2 read capability: canonical edges and observer filtering

Scope: D07.06/.04 supporting work under #29, based on accepted PR204/main
649011c3aee167778d5093e9d4952528fd908747. The new Rust read capability covers
scripted/native selected2 histories. Desktop service/controller/IPC/render
integration remains pending; this slice adds no execution or generation grant.

## Contract

literal_v3::selected_v2::desktop_read exposes opaque open_read_only, summary,
evidence and diagnostics functions using the existing Arm, EvidenceRequest,
Observer and Query2 types. The capability retains actual directory pins/lock.
Summary version2/source protocol3 includes only selection/lane, construction
descriptors and canonical edge availability, with read_only=true and
execution_available=false. Full Requests, model profiles, raw prompts/generated
text and reports are omitted from metadata.

Every summary/evidence/diagnostic call rebuilds the validated whole manifest,
both arm checkpoints/Store edges, report and raw accounting-file seal. It compares
the retained snapshot digest before returning data. Offset/coherent diagnostic
changes cannot retain a stale capability merely by preserving aggregate charges.
Native grant and actor raw/diagnostic denial precede binding/filesystem probes.

V3 StoredTurn fields map directly to the existing EvidenceTurn/render_evidence_view;
no V2 comparison row or ContextPolicy is forged. Actual Store before/after cuts,
receipt hashes, recording/capture hashes and existing Query2 remain authoritative.
Missing workflow evidence returns missing, without inventing model work or an
accepted receipt. Query2 on an available before Engine still validates the actor.
Inspection never alters character context, accepted history or generation access.

Diagnostics version2 is a manual bounded omniscient view: outcomes, expected
commands, role/timing availability, construction/status/counts, setup/accounting
and human-review status. It omits full Requests/profiles/raw prompts/generated
narration. Static expected dialogue may contain scenario text; this is not a
promise that all diagnostic strings are absent. Raw evidence remains an explicit
separate omniscient request.

Selected1 keeps its codec/API. Its accounting seal is shared by narrow visibility;
the existing missing-checkpoint Query2 transport is extracted with the same
manual row/edge fields and early access guard. No new Store/Host/compiler/memory
implementation, source importer, provider or model owner is introduced.

## Evidence

Independent frozen public packet e7271ddf was adopted431c9cec. Initial production
cb1518b3 failed compilation because two shared helpers needed qualification and
RowId intentionally has no Serialize implementation. 93df1c4d uses the existing
shared guards and explicit manual row encoding; strict all-target local-model
Clippy passed12.64s. These were compiler repairs, not a behavioral RED/GREEN case.
The old accepted API did not expose this capability.

At93df1c4dcd9ed3d9434885a90b80b154b4dcb03b, the first actual default-feature
public run passed5 groups/64.02s (+9.09s compile):

- Safe exact metadata, actual lock/drop/reacquire, and genuine old1/new2 mutual
  version refusal without rewriting source or target.
- Actual Store Query2 Player/Mira/Sable views at both edges, with unchanged
  canonical bytes, accepted basis and generation character contexts.
- Actual omniscient receipt/capture/raw-output envelopes and manual diagnostics
  matching selected records, descriptors and outcome fields.
- Native/actor denials before wrong binding and a deliberately poisoned manifest,
  with no cached private fallback.
- Coherent unselected-right checkpoint/admission-settlement drift invalidates all
  old-capability methods; a fresh capability gets a new binding. Canon is unchanged.

Fixtures are actual scripted V3 first-scene→selected Move and genuine existing
selected1 producers, not relabelled metadata. These finite tests are not a
universal privacy proof or native UI execution.

Independent genuine native packet1ce7d26c was adopted2ec28fc2/formattedde03cc44.
Atde03cc44, the ignored native history reader passes both default1/16.29s
(compile.94s) and local-model1/16.37s (compile8.67s). The actual PR204 model result
is pinned by selected.json SHA25696e0c6e860650e247fa667f5b838bd96c84f9a899bbf16f4ace29351ee971eca
and report.json SHA256c356d4f85a6b3170148c85fea36f113a4670258b64912e678a5239567ff804d8.
Both actual committed receipts match Store. Left is recovered/unknown roles0,
unavailable construction/passed=false; its orphan raw files do not become valid
capture/output evidence. Right keeps known roles2/validated_relevant/passed=true.
Query2 for all three observers at both edges matches actual Engine cuts. Actor
raw/diagnostic requests remain Forbidden. Drop/reopen preserves metadata,
diagnostics and the complete byte/directory inventory. No source path, model,
provider or new generation is used. Hash pins detect fixture drift, not authenticity.

Source review found no additional concrete production defect. It clarified the
static expected-dialogue wording above. This is not human quality/approval evidence.

Final compatibility atde03cc44aec4970d967042ef725f8e24349b3e6a, all terminal,
clean and unchanged. Production is identical to93df1c4d; subsequent code commits
only add/format the standalone public native-history oracle.

| Check | Actual result |
|---|---|
| Existing selected1 read-capability unit groups | 9 passed;83.97s |
| Genuine existing native-selected1 capability history | 1 passed;26.93s; full retained inventory unchanged |
| Eval strict all-target protocol-owner-tests Clippy | PASS;14.50s compiler-reported |
| Eval rustfmt | PASS;2.895s command wall |
| Full frontend/type/controller/headless/normal-hook exclusion | PASS;14.007s command wall |
| Native strict all-feature/all-target Clippy | PASS;15.91s compiler-reported |
| Normal native build | PASS;27.32s compiler-reported; not launched |
| Android Rust host | 20 passed;2.15s |
| Android dependency graph | PASS; no Eval/runtime/Tauri dependency |

These durations are test/build execution times, not app/model latency. No new
scripted/native execution logic changed in this slice; the changed shared old1
missing-evidence/accounting paths are covered by the9 compatibility groups and
genuine native selected1 history. Public selected2 read tests ran at93df1c4d,
not relabelled as native IPC or a later-source model run.

## Reproduce

Use pinned Rust and already available dependencies; qualify an external owned
Cargo target with --target-dir as recorded locally. One Cargo job, debug
information0, incremental disabled, locked/offline resolution. No ignored
historical test or model runs by default.

```powershell
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --test literal_selected_desktop_read -- --nocapture --test-threads=1
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --features local-model --lib local_lane::comparison::selected::desktop_read -- --nocapture --test-threads=1
cargo clippy --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --features protocol-owner-tests --all-targets -- -D warnings
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml --all -- --check
cargo clippy --locked --offline --jobs 1 --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --all-targets -- -D warnings
cargo build --locked --offline --jobs 1 --manifest-path apps/desktop/src-tauri/Cargo.toml
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-android/Cargo.toml --lib -- --nocapture --test-threads=1
cargo tree --locked --offline --manifest-path crates/locallore-android/Cargo.toml --edges normal,build,dev --prefix none
# From apps/desktop using the existing pinned Node/dependencies:
node verify-frontend.mjs
```

The genuine native-selected2 artifact above must be selected explicitly by
LOCALLORE_LITERAL_SELECTED_NATIVE_HISTORY. Run the ignored history once per
feature mode, preserving its supplied hash pins and all retained files:

```powershell
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --test literal_selected_desktop_native_history -- --ignored --nocapture --test-threads=1
cargo test --locked --offline --jobs 1 --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test literal_selected_desktop_native_history -- --ignored --nocapture --test-threads=1
```

The older actual native-selected1 history uses LOCALLORE_SELECTED_NATIVE_HISTORY
and the existing comparison_selected_desktop_native_historical_review ignored
test with --features local-model. Without each genuine owned fixture, its opt-in
qualification is unavailable; do not regenerate/relabel scripted data to pass.
No model asset is needed for these reads. Exact local logs/process arguments
remain outside Git; public commands omit machine-specific paths.

Environment: Windows NT10.0.26300 x64, PowerShell7.6.5, Rust1.93.1
(01f6ddf75), Cargo1.93.1 (083ac5135), LLVM21.1.8, existing Node24.22.1.

No new app render/semantic snapshot, native IPC, model execution, Android JVM/ABI,
emulator or phone check ran in this slice. Frontend headless/controller checks and
normal unlaunched builds must remain distinct from native execution. Raw synthetic
artifacts stay local/ignored; no desktop control, screenshots, downloads, settings
changes, release or protected-resource activity. The whole D07/desktop goal remains
open. Next: the existing desktop selected manager/strict frontend/controller and
application-owned IPC/render harness using this typed capability.
