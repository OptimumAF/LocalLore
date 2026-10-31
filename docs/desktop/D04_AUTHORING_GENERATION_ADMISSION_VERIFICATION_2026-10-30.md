# Desktop authoring generation admission: code verification

Refs #25 D04.02, supporting D04.04 and #21. This prerequisite routes shared
authoring generation through the existing native generation slot without holding
the window's control gate. It does not enable original-story creation or author
inference. The [frozen contract](D04_AUTHORING_GENERATION_ADMISSION_CONTRACT_2026-10-30.md)
defines the scope and remaining provider gap.

## Change and authority

`host_call` computes one classification from the actual shared Host envelope after
the existing input-size check. `Prepare` and `AuthoringGenerate` acquire the same
existing single permit and run outside the control gate after lease validation.
Cancel, status, review, canonical creation and other controls retain the actual
`WindowLease::dispatch` fence. There is no new endpoint, worker or provider.

Host owns version validation, cancellation and authoring state. Engine and Store
still own validation, canonical history, transactions, receipts, observer filtering
and idempotency. This change leaves shared schemas, lease implementation, runtime
profiles, token limits, frontend and Android sources unchanged.

## Independent baseline and fixed result

The independent FIRST was frozen at `46f37ef46b43b221cdec15f2d2d18cc105d0c44f`
before a different author extracted the exact old Prepare-only behavior.
Root integrated both, applied a reviewed formatting-only change, and ran the
baseline at `a67c8e26ee21cb4484c87f6e47c2efff78656c3f`. All nine groups compiled
and executed: **5 passed, 4 failed, 0 ignored**, Cargo exit101. This is a valid
behavioral baseline; no missing helper, registration or fixture failure counted.

The four failures were author generation classification, its valid whitespace
envelope, cancellation/status blocked until explicit generation release, and
`finish_close` blocked until that release. Controlled workers were released and
joined before assertions. Prepare behavior, typed controls, stale/queued fencing,
serialization and the explicitly labeled Main source control passed.

Only after those results, the producer added `AuthoringGenerate` to the classifier.
The actual tested integration is **`1dd0880d00674f314745427b9c789dd18c180dda`**.
Producer commit `43f5a9dc` is a separate, unexecuted source lineage and is not the
test source. The same nine groups then passed; both existing lease tests passed.
The independent test file was unchanged between baseline and green.

| Check at integration1dd0880d | Actual result |
| --- | --- |
| `generation_admission_review::` | 9 passed, 0 failed/ignored; 301 filtered |
| `lease::tests::` | 2 passed, 0 failed/ignored; 308 filtered |
| Explicit three-file Rustfmt check | Exit0 |
| Desktop normal-bin Clippy, `-D warnings` | Exit0 |
| Locked/offline normal desktop build | Exit0; binary unlaunched |

All seven code children, including the initial formatter and expected failing
baseline, closed with their expected codes. No timeout, output overflow, kill,
unknown ownership or storage breach occurred. Compiler-reported normal build
time was13.98s; its wrapper measured14.714s. Neither is application performance.

## Reproduce the code checks

From a physical D: checkout, set process-local `TEMP` and `TMP` to
`D:/Dev/_Temp`. Use the existing pinned offline Cargo cache/target; this task used
one job, incremental0, and dev/test debug0. Do not repurpose an installed cache or
delete retained output to fit a budget.

From `apps/desktop`:

```powershell
cargo test --manifest-path src-tauri/Cargo.toml --bin locallore-desktop-spike --locked --offline generation_admission_review:: -- --test-threads=1
cargo test --manifest-path src-tauri/Cargo.toml --bin locallore-desktop-spike --locked --offline lease::tests:: -- --test-threads=1
rustfmt --check --edition 2021 --config skip_children=true src-tauri/src/main.rs src-tauri/src/generation_admission.rs src-tauri/src/generation_admission_review.rs
cargo clippy --manifest-path src-tauri/Cargo.toml --bin locallore-desktop-spike --locked --offline -- -D warnings
cargo build --manifest-path src-tauri/Cargo.toml --bin locallore-desktop-spike --locked --offline
```

Freshly read versions: Rust1.93.1, Cargo1.93.1, Rustfmt1.8.0-stable,
Node24.22.1, PowerShell7.6.5, Windows10.0.26300 x64. Dependencies and lockfiles
were unchanged; Tauri remains2.12.5. No dependency/model download occurred.

## Retained local evidence and boundaries

Synthetic code logs, source hashes, admission and process receipts remain local
and gitignored in the existing fork evidence group. Fixed phase admissions and
create-only START/PASS receipts prevent replay or advancement after an unresolved
child. Independent source review corrected replay, terminal-evidence persistence
and the inherited global-stop list before any code child ran.

The existing original target baseline8,259,980,576B and4GiB allowance were retained;
the final child inventory measured12,179,265,264B below12,554,947,872B. Current
ordinary build and all prior diagnostic/failure evidence were preserved. No output
was deleted or moved to a new target to evade limits. The phase's final inventory
preceded writing its own receipt: metadata1,017,577B, group53,218,642B,
joint735,539,926B; unchanged caps were1,179,648B/67,108,864B/759,169,024B.
Old code records remained549,989B physical/570,664B logical and fixtures671,744B.

Local baseline phase SHA256:
`e2e0969ef8fc1c340f6901e413c2e4d978a3d9018151547055fc3d85a3b4f210`.
Finish phase SHA256:
`ec6af6c4732cafefad367791940f89f3c62ab7fda720f7bed596de8ae194c84a`.
Built, unlaunched normal native SHA256:
`0482d821a12a92333a9974a43f301d5fe36d5ca08e7c75843c3d04f19b0e6f1f`.

These tests use the production admission helper and real window lease with fixed
controlled closures. They do not execute Tauri IPC, Host inference/cancellation,
WebView rendering, a model, an app window, Android, a device or OS isolation.
The Main check is structural source evidence, not an executed semaphore/IPC test.
Frontend/Android checks were not rerun: no interface, schema, engine or consumer
source changed. Existing Native4 execution remains bound to its separately
recorded source; all four native run grants remain spent.

## Next runnable prerequisite

Specify the existing runtime's singleton author lane and provenance under #9:
role sequencing, role-specific token/output limits, metrics and worker/profile
compatibility must agree. Preserve current play budgets. Adopt new worker bytes
only through their own reviewed qualification. Then integrate the existing shared
authoring lifecycle into desktop creation. D04, story quality and release gates
remain open; this code slice cannot satisfy them.
