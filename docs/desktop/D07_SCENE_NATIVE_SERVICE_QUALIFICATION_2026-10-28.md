# Native scene comparison: service and harness qualification

2026-10-28 local date; the joined checks below ran on 2026-10-29 UTC.
Refs #29 D07.03/.05, supporting D07.06 and #25 D04.04.
**Partial local qualification at frozen `b70e57be`; broad checks and the full
Native4 model cohort remain PENDING.** The joined development products compile,
15 focused service cases and 4 accepted-main window-capability cases pass, and
the frontend and synthetic launcher-policy checks pass at the preceding source.
This is not milestone completion, merge approval, a new model result or human
quality acceptance.

This document's author read source, contracts, current GitHub metadata and
bounded local evidence only. Root owns compilation, execution, integration and
acceptance. The author ran no Cargo/Node/build/app/model/device operation and
did not read model assets or control/capture the desktop.

## Source, dependencies and frozen interfaces

The joined source is `b70e57be54a596b0a8d3a9d68117a3a8d54e0980` on
`impl/d07-scene-native-integration`. Its accepted-main input is
`9be0f0af316bdefc6df5f874d9044c0d215087da`, including the focused window identity
fix accepted through #245. Independent regression modules from both the scene
stack and accepted main are retained.

The [accepted-main window qualification](D07_FULL_RUN_WINDOW_IDENTITY_QUALIFICATION_2026-10-28.md)
retains its original default-concurrency timeout alongside isolated and serial
passes, without a proven causal diagnosis. That historical main result does not
substitute for the joined broad checks pending below.

At this document's GitHub readback, #232, #237, #238, #239, #241 and #243 are all
open, unmerged drafts. They provide the scene recipe, Host capture, desktop
foundation, Protocol 4 producer, Core reader and desktop reader dependencies.
Their earlier execution evidence applies to its named source, not automatically
to this joined source. Protected authoring #225 is a dependency, not part of
this allocation; no branch, checkout, resource or chat belonging to that work
was changed or used by this document's author.

The existing Rust service keeps one manager, native model owner and index
namespace. Its private non-Serde `FullComparisonProtocol::{LiteralV3, SceneV4}`
selects actual typed V3/V4 preparation, inspection and execution. Legacy native
wrappers remain Protocol 3. Native Protocol 4 uses its own exact closed index
tuple `(version 3, protocol 4, approved_native)` and actual V4 binding/report;
it is not a V3 report with new labels. Global validation, the combined 32-run
cap and cross-protocol client uniqueness precede protocol filtering. Token
controls retain lane, protocol, window identity and epoch fences. Existing
retirement/drain remains epoch-wide; independent multi-window retirement
isolation is not established.

The renderer sends the existing closed command/query shapes. It cannot select
a protocol, provider, model, worker or filesystem path. The checked development
bootstrap alone selects SceneV4. The frontend decoder/controller/View preserve
the returned protocol and acknowledged ownership through retries, catalog
recovery, cleanup and context retirement. The existing Rust engine still owns
canonical state, receipts, validation and observer restrictions; inspection
does not grant generation access or change character knowledge.

Pre-implementation contracts remain the source of intended oracles and limits:

- [Native integration contract](D07_SCENE_NATIVE_COMPARISON_CONTRACT_2026-10-27.md).
- [Independent service freeze](D07_SCENE_NATIVE_SERVICE_FREEZE_2026-10-27.md),
  initially 11 tests, with later independent capability cases retained separately.
- [Independent frontend freeze](D07_SCENE_NATIVE_FRONTEND_FREEZE_2026-10-27.md).
- [Model mutation/root guard contract](D07_SCENE_MODEL_GUARD_HARNESS_CONTRACT_2026-10-27.md).
- [Closed full-cohort harness contract](D07_SCENE_NATIVE_FULL_HARNESS_CONTRACT_2026-10-28.md).

Those documents retain their original source-only/unrun declarations. Actual
later measurements are attributed below; a contract is not execution evidence.

## Integration failures and corrections

| Source | Actual event and limit |
| --- | --- |
| `3a22aeb940886c1e378727db1e6d750366dd2c23` | Launcher correction puts Git, build and app children behind the same permanent unknown-drain barrier before initial Git. |
| `41b18db8f1af096ae415e5171082e0db4bafc184` | A nonterminating PowerShell exception left stale replacement content in a variable and the local merge script wrote it to two Rust files. No build, app or model run used this intermediate source. |
| `94438ca5c0336e2579d68b20e18cdfa45a509872` | Restored `evaluation.rs` and `evaluation/comparison_run.rs` from frozen `3a22aeb9`, adding only accepted-main test registration; the lease file matches accepted main. The retained source-repair record names both files and the failure. |
| `9633793292473e233cecac9339925d3f03a3a70a` | Formatting of joined source and registration of the policy checker. Full frontend and pinned Node policy/syntax checks pass here. First joined Rust compilation fails with E0574. |
| `b70e57be54a596b0a8d3a9d68117a3a8d54e0980` | Only the legacy metadata fixture changes: decode the same exact V1/V2 closed metadata through existing `Index::decode` because joined `Index` is an enum. Production source, protocol choices, assertions, deadlines and file-byte oracles do not change. Joined compilation and both focused cohorts pass here. |

The retained repair record is `d07-scene-main-merge-source-repair1.json`.
Independent source review found the enum-fixture mismatch and found no blocker
in the repaired production logic. Review is a source finding, not execution or
owner acceptance. Root changed later shell handling to stop on errors and check
exit codes; no failed artifact was rewritten into success.

Earlier service measurements are also retained. At `71c6ce6f`, compilation
passed, then the original 11 cases produced 9 passes and 2 failures: the token
boundary and a Windows file-lock error while inventorying an active source.
Fixture calibration at `3c1f1146` still produced 9/2. Quiescent inventories and
a fresh consumed reader per lane at `eda395d1` produced 10/1; the token-boundary
failure remained. The later production capability fix plus four independent
regressions produced 15/0 at `35630d3e`. The interrupted first attempt at that
source has no terminal result and remains `interrupted_unverified`; its separate
58.0032193 s resumed command is the actual completed 15-pass measurement.
The joined-source 15-pass result below is a new measurement, not inherited from
that earlier result.

## Joined source checks actually completed

Times below are complete process durations, including compilation where relevant.
Each record in this table starts clean and reports unchanged source and no dirty
files at exit. All commands use physical D: source/cache/target and process-local
`TEMP`/`TMP=D:/Dev/_Temp`. Cargo jobs 1 limits compilation jobs; only an explicit
`--test-threads=1` limits libtest execution to one thread.

| Local evidence prefix | Source | Actual result | Seconds |
| --- | --- | --- | ---: |
| `d07-scene-native-full-clean-transition1` | `96337932` | Exit 0; six owned project packages only, 376 files / 474.4 MiB removed before the main-to-scene cache transition | 1.9273971 |
| `d07-scene-native-full-first-compile1` | `96337932` | Exit 101; E0574 in legacy `window_identity_review.rs`: struct syntax for the joined enum; tests did not run | 38.5650540 |
| `d07-scene-native-full-second-compile1` | `b70e57be` | Exit 0; development all-targets test compilation only | 13.2072800 |
| `d07-scene-native-full-service-fence-after-index1` | `b70e57be` | Exit 0; 15 service cases passed, 0 failed; test time 23.20 s | 24.1332590 |
| `d07-scene-native-full-main-lease-after-index1` | `b70e57be` | Exit 0; 4 accepted-main capability cases passed, 0 failed; test time 0.39 s | 0.9730599 |
| `d07-scene-native-full-frontend-first1` | `96337932` | Exit 0; full frontend verifier, strict types, regression checkers, policy checker and normal-bundle exclusion | 14.8698463 |
| `d07-scene-native-full-process-policy1` | `96337932` | Exit 0; 16 simulated child/timer policy cases, no OS children inside checker | 0.1155494 |
| `d07-scene-native-full-process-check-syntax1` | `96337932` | Exit 0; policy checker syntax only | 0.0940730 |
| `d07-scene-native-full-launcher-syntax1` | `96337932` | Exit 0; launcher syntax only | 0.1114425 |

For exact command reproduction, the recorded source root is
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/source-resource-metrics-review`.
Below, `<target>` means exactly
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/d07-comparison-reader-native-target`,
and `<node>` means exactly
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/d09-build-security/node-v24.22.1-win-x64/node.exe`.
`CARGO_HOME` is the existing sibling
`d07-consumer-cargo-home-20261026-restore1`. Run from the recorded source root,
with the owned D: environment, rather than recreating a cache or using a C: path.

```text
cargo clean --manifest-path Cargo.toml --offline -p locallore -p locallore-storage -p locallore-workspace -p locallore-android -p locallore-eval -p locallore-desktop-spike --target-dir <target>
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --all-targets --no-run --jobs 1 --target-dir <target>
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --bin locallore-desktop-spike --jobs 1 --target-dir <target> evaluation::comparison_run::scene_native_review:: -- --nocapture --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --bin locallore-desktop-spike --jobs 1 --target-dir <target> evaluation::comparison_run::window_identity_review:: -- --nocapture --test-threads=1
<node> apps/desktop/verify-frontend.mjs
<node> apps/desktop/comparison-run-process-policy-check.mjs
<node> --check apps/desktop/comparison-run-process-policy-check.mjs
<node> --check apps/desktop/comparison-run-harness.mjs
```

The service cohort exercises actual Rust entry points, consent-denied native
provisional metadata, exact mixed-version catalog closure, cross-protocol caps
and clients, stolen-token refusal, held-consent cancellation before reservation,
resume refusal, empty denied-prefix inspection and a separately generated
scripted scene source. Its existing ModelManager reservation sequence reads the
actual counter, distinguishing no reservation from reserve-and-release.
It does not start an approved runtime. Scripted Host/Store output remains
scripted and does not substitute for a completed native report.

## Frontend baseline and guard execution are separate evidence

The independent frontend checker uses the actual decoders, controller and React
static View with synthetic DTOs and mocked transport. At `78b47321` it measured
41 passes / 28 failures among 69 checks, with zero calibration failures. Two
additional lost-acknowledgement owner cases measured 69/2 among 71 checks at
`a116f649`. At `71c6ce6f`, the same expanded checker passed 71/71 in 1.1220222 s.
The original failures and exact source hashes remain in the records. The old
native/scripted controls were not renamed as Protocol 4 successes. Static HTML
checks labels and disabled states; it is neither pixel/layout review nor mounted
native WebView execution. The later full frontend verifier at `96337932` is
reported separately above; `b70e57be` only changes the Rust test fixture.

The model-root matrix is Rust test-process evidence. An initial run at `1ef9e318`
failed with source changing during execution and is not valid frozen-source
qualification. After registration at clean `2780733a`, the unchanged matrix
still failed on actual Windows case-alias acceptance. Production path handling
was corrected before the clean `acedfc23` pass: one parent test launches the
14 fixed isolated child cases and passes in 22.7774041 s command time / 0.44 s
parent-test time. Short-path alias availability was explicitly unavailable;
the ordinary nested control ran, but an 8.3-alias refusal is not qualified.

The distinct app guard cohort does exercise native IPC with tiny synthetic
staging sentinels, without approved assets or inference:

| Evidence | Source | Actual result | Seconds |
| --- | --- | --- | ---: |
| `d07-scene-model-guard-native-cohort-first1`, packet `scene-model-guards-f48c7dd6-3df8-4f94-9a1f-c4444166fee0` | `b4b2cbad` | Exit 1; fixed command refused by app-window ACL before guard checks; original failure retained | 58.1067588 |
| `d07-scene-model-guard-native-cohort-second1`, packet `scene-model-guards-280c53ea-6482-49cb-a0b8-d9bc6db74213` | `0606ecd2` | Exit 0; app IPC guard cohort passed; no model execution or images | 34.9218798 |

The first report says `harness_scene_model_guards not allowed`, identifying the
missing `allow-harness-scene-model-guards` capability. Commit `0606ecd2` adds
only that already registered closed development command to the app test window.
The second actual report records `model_import` and `model_load` as `Forbidden`
before manager side effects, byte-identical complete publication/control
inventories across the refusals, and the application manager still unloaded
with no job. The separate counterfactual manager reaps only its own control
sentinel before picker cancellation, makes one picker call, and leaves the
publication untouched. There is no approved model file or runtime owner.
No unexpected frontend/native errors are recorded. Normal frontend/native
restoration passes, with restored products unlaunched.

The guard packet explicitly records `nativeIpc: true`, `modelExecution: false`
and `rendering: unqualified-no-images`. This is a bounded command-entry mutation
guard result at `0606ecd2`; it does not qualify the later full comparison cohort,
native rendering, actual asset reuse/load, OS descendant cleanup or model quality.
Its report SHA256 is
`d22deb47a605f92d1d0f7c0773e54969587486827d3c068cd170b03b4cbcc738`;
the wrapper `qualification.json` SHA256 is
`b457b646fcd054769c8bf60a6a6100ea7283bb3ac3ea0d040f17c322401ed31f`.

The earlier exact guard/matrix/frontend commands run from the same physical
source's `apps/desktop` directory, so their manifest is `src-tauri/Cargo.toml`:

```text
<node> check-scene-native-transport-review.mjs
cargo test --manifest-path src-tauri/Cargo.toml --locked --offline --features dev-harness --bin locallore-desktop-spike --jobs 1 --target-dir <target> scene_model_guard_harness::tests::root_protocol_matrix_uses_isolated_fixed_children_without_parent_environment_mutation -- --nocapture --test-threads=1
<node> scene-model-guard-harness.mjs
```

## Full Native4 model harness: implemented source, execution pending

The closed `--native-scene-v1` launcher/journey path is integrated with the same
frontend controllers, native IPC and Rust service. No arguments still selects
scripted Protocol 3; `--native` still selects native Protocol 3. It accepts only
explicit owned existing D: roots, reuses an approved publication in place,
skips ordinary import/load, and stages only the separately approved worker via
the established script. Read-only execution observations expose the existing
reservation sequence, fixed consent count and owner state only under the
checked development Scene4 gate. No general execution/debug server was added.

The predeclared full cohort remains one paired run, batch 1 then explicit
resume 3: 24 scheduled attempts per arm / 48 report rows. Completed resume and
cold restart require the same actual native report, unchanged files and no new
consent/reservation/owner, rather than native-looking scripted metadata. The
eight review slots remain `courier-01`, `courier-05`, `courier-12`, `courier-22`,
both arms; failed or unavailable slots cannot be replaced. Fixed captures are
22 initial and 4 restart images, all requiring later individual inspection.
These are planned requirements, not counts measured by this document.

The launcher uses a bounded, nonrecursive direct-child primitive before initial
Git. Error/timeout/overflow with a PID makes drain unknown permanently, attempts
one kill and waits five seconds; late close cannot clear the barrier. Later
Git/build/app/restoration spawns are blocked after unknown drain. The pinned
Node 24 checker verifies 16 simulated child/timer cases, including startup and
restoration Git failures, overflow, repeated errors and zero later launches.
It launches no OS children. Syntax and simulations do not qualify actual
Windows timeout, kill, descendant containment or Job cleanup.

## Environment, pending gates and next runnable work

Pinned Node 24.22.1 is explicit in the recorded commands. The nearby
`d07-main-window-versions-20261029.json` observation at
`2026-10-29T04:58:46.4425223Z` records Rust 1.93.1, Cargo 1.93.1,
PowerShell 7.6.5 and Windows NT 10.0.26300.0, but its source is `2401fcd3`.
It is environment context, not an exact-`b70e57be` version capture. No current
WebView, model, worker or Android runtime version is measured by this source
author. D: cache/temp settings in the process records are retained; no global
SDK/cache/installed-tool settings were changed by this documentation work.

At this handoff the joined broad serial Rust suite, strict development/normal
Clippy, Rust formatting, normal native build and Android Rust host compatibility
checks are **PENDING**. Root owns the active serialized check job; this document
does not infer terminal results from a partial log or historical main passes.
Final exact-head source review, focused PR, security scan and owner acceptance
are also **PENDING**. The next runnable task is to complete and inspect those
exact-source checks before any separately approved full model cohort.

No new Native4 inference, completed-native no-load resume/cold restart,
application-owned render images/layout inspection, physical phone, Android ABI,
offline/security/packaging qualification or prose improvement is established.
The original eight-sample human assessment remains **needs improvement**.
All D07 checklist acceptance stays with the issue and owner; no checkbox,
milestone, release or merge is performed by this document.

## Local evidence anchors

Records and logs remain local/gitignored in the sibling
`author-integration-artifacts` directory. The following hashes identify the
actual retained process records; the corresponding `.log` files preserve
individual failures and results. Historical rows keep their original source,
including the one source-changing matrix attempt.

| Record prefix | Source | Exit | Seconds | `-process.json` SHA256 |
| --- | --- | ---: | ---: | --- |
| `d07-scene-native-service-first-compile1` | `71c6ce6f4fed61da0848897d2402c0783fefa8ea` | 0 | 42.2745619 | `afb6538ea3f3416b67b6e1c388f744bc6b35a16d7a483da312700d11adfaebf7` |
| `d07-scene-native-service-first-tests1` | `71c6ce6f4fed61da0848897d2402c0783fefa8ea` | 101 | 22.4147253 | `1345c69ddd04093403380b9d1ea6c8045b6ae2bcc282cd7f4d9433cd4a50034e` |
| `d07-scene-native-service-calibrated-tests1` | `3c1f11468421985e935705ecb5a811da26d400a9` | 101 | 39.8879061 | `cac7033107b7c6ad43b8861856e91db2490705e8af44ebd531f95f1b74decfaf` |
| `d07-scene-native-service-quiescent-tests1` | `eda395d1d766f026367bd0ad5bc70ef199e64af4` | 101 | 45.4276795 | `27fc368386ba828fa865aa5302be63c523b7502bf793663ffb83f31096e52a72` |
| `d07-scene-native-service-lease-resumed1` | `35630d3e682b97ba0fa3988616c36b087c2cb179` | 0 | 58.0032193 | `9d8e38f0338ac56466e9492303c7dd1eae633e251559eec78e7c49add38dccd2` |
| `d07-scene-native-frontend-baseline1` | `78b4732132e73d8a87c56a99932246f6e1993c12` | 1 | 7.9814581 | `ecd48f7263e3b47729c9e1cee2e0a069539736e9e8f3ec138d93c84efd18d64b` |
| `d07-scene-native-frontend-null-owner-baseline1` | `a116f649a34dce5e178d83e48b05a2a02cbd9e01` | 1 | 1.1292281 | `8a1228d8e3ed5df143fa81907ca1f668ea0115f1c6ce95c186f69c925d018553` |
| `d07-scene-native-frontend-first-green1` | `71c6ce6f4fed61da0848897d2402c0783fefa8ea` | 0 | 1.1220222 | `5737c33d988f3b23f4bf9f67091c7e36bad81a2b589cb023eac544bdc8204709` |
| `d07-scene-native-frontend-first-full1` | `eda395d1d766f026367bd0ad5bc70ef199e64af4` | 0 | 19.2753802 | `b66279e5cbdb9003db15fd9a8a61ab7b157eba1bd0d1a9e31c192209150e63b7` |
| `d07-scene-model-guard-matrix-baseline1` | `1ef9e3182cf534deb6d5537a82341f49c6044496` | 101 | 22.7980405 | `f8caebe8d920f32acd5411d5ee547f040adb972d4f4ccb77fe15ecb3571db5c9` |
| `d07-scene-model-guard-matrix-registered-baseline1` | `2780733a60ca72a528c25304fb243413ae8b869b` | 101 | 21.6854326 | `b6f1621100b884baca594890a887b5d9e196da819408b4904b12fbd6583c3cf8` |
| `d07-scene-model-guard-matrix-first-green1` | `acedfc232dbb0c9b058d460d501cfff00497cf03` | 0 | 22.7774041 | `26a785e72c93a2986c179cc631ff6c748518676d5c538f9bfa2f5c0b61158071` |
| `d07-scene-model-guard-native-cohort-first1` | `b4b2cbad08b1403213c6c3a1465f80b4e131b8f0` | 1 | 58.1067588 | `985560734ad51c1e3403a402cb5a50b47f17a32d2bfdf2a1c639da002b1187b7` |
| `d07-scene-model-guard-native-cohort-second1` | `0606ecd2e35c1658e4da2f0f8261dea222aeda96` | 0 | 34.9218798 | `1e91b07a8d54da85df9829712e1f81ccf4b8d434a9542646ab772955a3b4a320` |
| `d07-scene-native-full-clean-transition1` | `9633793292473e233cecac9339925d3f03a3a70a` | 0 | 1.9273971 | `4f42b523959e2456bf4abdb9179dfbd8b3b29318142726f83fe33fb5b080a94e` |
| `d07-scene-native-full-first-compile1` | `9633793292473e233cecac9339925d3f03a3a70a` | 101 | 38.5650540 | `d0f8d04271718160072ff394d88913aa297717514baea20c8936cb831d2132e8` |
| `d07-scene-native-full-second-compile1` | `b70e57be54a596b0a8d3a9d68117a3a8d54e0980` | 0 | 13.2072800 | `4c179078870c4214867fbf720665bfcf33f75e907563ad630e3e53674c55cb71` |
| `d07-scene-native-full-service-fence-after-index1` | `b70e57be54a596b0a8d3a9d68117a3a8d54e0980` | 0 | 24.1332590 | `d3b53e8b07c7f7c89cc839030bc59a20caff17ecace2f977346c5b288644286e` |
| `d07-scene-native-full-main-lease-after-index1` | `b70e57be54a596b0a8d3a9d68117a3a8d54e0980` | 0 | 0.9730599 | `53d58ed78449361b0f8486d1eca2538c25774cab9ba352526d04ec788564e4e9` |
| `d07-scene-native-full-frontend-first1` | `9633793292473e233cecac9339925d3f03a3a70a` | 0 | 14.8698463 | `ceaf2f475d92ee6e0219f11251c0164db7109309f7ebc1c9160527b30205378c` |
| `d07-scene-native-full-process-policy1` | `9633793292473e233cecac9339925d3f03a3a70a` | 0 | 0.1155494 | `7ebf8b5c15a831e19a5ada2bcbc2c9a24d6018419c66231736c40926846add02` |
| `d07-scene-native-full-process-check-syntax1` | `9633793292473e233cecac9339925d3f03a3a70a` | 0 | 0.0940730 | `485528f92f017072f1352d383e6df1a81d4b4a84fc0dff95b54b038d0791eb71` |
| `d07-scene-native-full-launcher-syntax1` | `9633793292473e233cecac9339925d3f03a3a70a` | 0 | 0.1114425 | `0d16b65187f41c2341613590fdc811bc8237887561e4018b86c26679266b1844` |

Additional bounded records:

- `d07-scene-main-merge-source-repair1.json` SHA256: `34cb5ce2b6170d141be34049a426dfd7af4687a7956d02c991a05b604137a965`.
- `d07-scene-native-service-lease-first-green1-interruption-observation.json` SHA256: `bd6f83cf6546d88e16f834b7520430493127c5938dad5b18eb97922dca223634`.
- `d07-main-window-versions-20261029.json` SHA256: `3b81ca4f4a392e4f3631056f4e9ace0ac7b462a050d80b597ea7c5fd6eb17056`.
