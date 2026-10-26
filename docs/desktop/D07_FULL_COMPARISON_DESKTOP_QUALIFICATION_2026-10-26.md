# Full comparison desktop scripted slice: qualification

Supporting **D07.06/.02/.04**, under [Root claim6422925411](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6422925411).
This record supports [PR211](https://github.com/OptimumAF/LocalLore/pull/211)
with completed, source-bound checks, including both actual hidden WebView cohorts
and final native/compatibility/build verification. It awards no full D07 acceptance,
human quality approval, native-model desktop qualification or release readiness.

The [frozen contract](D07_FULL_COMPARISON_DESKTOP_CONTRACT_2026-10-26.md)
started at `f77c36e2`, following accepted `1bb152f9`/PR209. Draft integration
first-cohort source is `7f7d870c295463b6788315ccadb7127a0d935ad6`; layout correction
is `381abe50374708e38a169798045343799d01eb47`. Earlier checks below retain
their actual source attribution. Root executed the checks. This document's
author read terminal records/logs only and performed no application execution.

## Implemented boundary

Ordinary desktop controls run fixed **ScriptedBaseline fake inference** through
the existing Rust `EvaluationManager` parent Job/worker and shared protocol3
`literal_v3::run_comparison/inspect_comparison`. Paired runs use the existing
scripted reference APIs; rollout runs use each arm's actual history. Literal and
Relevant constructions remain the compiled shared descriptors, not renderer
choices. No new engine, Store, memory semantics, provider or model owner is added.

Each native-owned UUID directory contains bounded `desktop.json` index metadata,
shared authoritative output under `work/`, and paired-only `reference-source/`.
The index's kind/protocol/full shared binding must match an existing manifest.
Canonical receipts, source checks, replay and evidence remain shared Rust duties.
Status, lookup, open and an exact repeated start never implicitly resume work.
Resume is explicit, with1..4 new scenes; a completed resume performs no new work.

The closed `evaluation_comparison_run` transport captures the actual native
WindowLease and Host Story Lab permission. Cleanup close does not require the
grant. Execution completion is **not** permission to read private evidence:
managed inspection obtains independent native spoiler-read consent and reuses
the existing reader's actual Query2 observer filtering and raw-evidence guards.

## Preserved failures and corrections

| Attempt | Actual source / retained log | Result and disposition |
|---|---|---|
| First service compile | `7e4556d6`; `d07-full-comparison-service-first1.log` | Exit101, E0308 in the token guard; no tests executed. This is a compile failure, not behavioral RED. Its process record says terminal source unchanged=false; no immutable-cohort claim is made. |
| Original seven service tests | `7e0423d8`; `d07-full-comparison-service-first2.log` | **6 passed /1 failed**,456.79s test time. Paired resume3 hit the test's180s scheduling wait while operation2 was running with null error. Failure retained. |
| Scheduling fixture correction | Authored `68889826`, integrated `001e8faf` | Only the helper wait180→600s and its comment changed. Remaining18 scenario turns/both arms incur repeated SQLite prefix/cold validation. Behavioral assertions and product/runtime/consent/cancel/resource/quality limits were unchanged. This correction is not a latency qualification. |
| Per-run budget regression | `6986a65d`; `d07-full-comparison-budget-red1.log` | **0 passed /1 failed**,27.77s. A partial real rollout plus three owned12MiB padding files exceeded the existing32MiB leaf cap; resume changed the inventory before reporting budget failure. This is actual behavioral RED. |
| Budget fix | `4a00f5b8`; `d07-full-comparison-budget-green1.log` | **1 passed /0 failed**,9.19s. Prework budget refusal preserves canonical DB/checkpoint/invocation/ledger bytes. Synthetic padding is not a disk-full experiment. |
| First frontend checker | `6986a65d`; `d07-full-comparison-fe-first1.log` | **54/54 passed**, but its mock parsed query strings and masked the native object's required wire shape. Not native wire-conformance evidence. |
| Strengthened frontend boundary | `6fad061b`; `d07-full-comparison-fe-wire-red1.log` | **47/56 passed,9 failed**. Checker now requires a nonnull/nonarray object and includes a positive actual-controller dispatch case. Original54 assertions retained. |
| Object-forwarding fix | `8bb22d96`, checked at `4a00f5b8`; `d07-full-comparison-fe-wire-green1.log` | **56/56 passed**. Controller sends the object; native parsing was not relaxed to accept strings. |
| First strict native lint | `6ba283a8`; `d07-full-comparison-native-clippy1.log` | Exit101: two needless-borrow warnings in test-only review fixtures. Removed only those borrows at `7e628ded`; assertions and application behavior unchanged. Rerun passed. |

The frontend cases use synthetic transport, actual controller code and React
static HTML. They are not native IPC, WebView rendering or model evidence.
No failed attempt above is silently replaced by its later success.

## Completed integration checks

| Check | Source | Exact observed result |
|---|---|---|
| Native Rust full-comparison service + managed reader | `f4270d8bc5c31720e97ad0f9605ef4d18b1fc16c` | **11 passed,0 failed,0 ignored**,465.39s test time;17.39s compile. Process exit0, clean source and terminal source unchanged=true. |
| Closed native command parser | `7f7d870c295463b6788315ccadb7127a0d935ad6` | **8 passed,0 failed,0 ignored**,0.01s test time;30.62s compile. Process exit0, clean/unchanged source. |
| Wired full frontend verifier | `7f7d870c295463b6788315ccadb7127a0d935ad6` | Exit0; strict TypeScript, request/schema checks, existing controller/headless suites and normal-frontend development-hook exclusions passed. Process clean/unchanged. No aggregate assertion count inferred. |
| Earlier full frontend verifier | `c3b31e4af9f3403de18aa9595a393406c05d7c6e` | Exit0; retained separately, not additive evidence. |
| Frontend after layout correction | `381abe50374708e38a169798045343799d01eb47` | Full verifier exit0,18.79s command wall time, reported by Root. This does not qualify the corrected native rendering. |

The eleven native service cases comprise the original seven, one budget guard
and three post-implementation managed-reader cases. They cover paired1→resume3,
rollout4, actual report3/48 rows, reference immutability, completed-resume file
equality, exact-client retry/conflicts/lookup, cold reopen/new epoch, wrong native
index/shared manifest/checkpoint refusal, global worker exclusion, cancellation,
stale operation, retirement and spawn failure. Managed-reader tests additionally
cover independent consent, late-close suppression, actual Store-cut History
queries for Player/Mira/Sable, early raw denial and retained read-lock exclusion
until explicit close. These finite tests are not a universal concurrency proof.

Eight parser cases cover closed keys/actions, lowercase UUIDs, safe operations,
integer1..4 batches,4096-byte encoded Value cap and refusal of renderer-selected
provider/policy/path/consent. Parsing an already decoded Value does not prove
duplicate-key rejection in arbitrary raw transport bytes.

## First actual native WebView cohort and visible correction

[Root's first-cohort evidence](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6424791401)
is bound to clean/unchanged `7f7d870c`. The retained local cohort basename is
`full-comparison-native-534bbe22-8e27-4acb-b378-b4f8abb667ef`.
This ran the real app-owned controllers and native IPC in hidden, unfocused
Windows WebView2 processes, using scripted fake inference and fixed native
fixture controls. It did not capture or control the desktop.

| Stage | Actual assertions | App-owned PNGs | Native outcome | Frontend error buffer |
|---|---:|---:|---|---|
| Initial process |182|14|Exit0; stderr0bytes; no timeout/output overflow|Exactly1 intentional lost-start-ACK `Transport`|
| Fresh-process restart |63|4|Exit0; stderr0bytes; no timeout/output overflow|0|

These are245 stage assertion entries and18 captures, not a claim of245 distinct
assertions or18 distinct capture labels. Root individually viewed all18 PNGs.
Actual journeys passed paired1→resume3, completed read-only resume, rollout4,
independent managed consent/denial, Store Query2 observer isolation/early raw
denial, unknown-ACK lookup/cancel, context retirement/drain/close and cold reopen.
The intentional transport fault is retained; this is not a zero-frontend-error claim.

Independent Node/native comparison-file inventories matched: **1,068 files,
15,055,053 bytes**, with initial/restart maps unchanged and digest
`360d6f68210e0b23898363904f1ceb762d01ace5b7f63058c6acc8bc46d37fa8`.
This digest covers owned shared comparison files, not every process/artifact byte.
Initial app stage ran18:46:36.191Z–18:56:30.241Z on2026-10-26 (**594.050s**);
restart18:56:31.644Z–18:57:41.982Z (**70.338s**). These journey wall times include
scripted work and inspection; they are not whole-turn/model latency qualification.

Visual review found the Saved run placeholder clipped in a produced render
despite correct empty semantic selection. This draft attributes neither a
particular capture/catalog state nor an intrinsic cause to that observation.
`381abe50` adds responsive Saved label/select sizing and a computed-font
placeholder-fit assertion. It also strengthens launcher acceptance to minimum
stage counts100/40 and exact required inventory-proof names: two initial and
one restart. Functional success of the original cohort does not certify this
correction's pixels. The corrected cohort is active and **PENDING** here.

## Corrected actual native cohort

Clean, unchanged source `381abe50374708e38a169798045343799d01eb47` completed the
same fixed launcher in local cohort
`full-comparison-native-9df5381e-848d-4b2e-9ce5-4b0e5b2d1b13`:

| Stage | Assertions | Captures | App wall time | Native stderr | Frontend buffer |
|---|---:|---:|---:|---:|---|
| Initial |198|14|537.829s|0 bytes|One deliberate lost-start-ACK Transport|
| Fresh-process restart |69|4|66.963s|0 bytes|Empty|

Both app processes exited0, with no watchdog timeout or output overflow. Builds
also exited0. App wall times include the full synthetic journey and repeated
cold SQLite validation; these are not whole-turn performance measurements.
The native app used fixed native consent doubles and actual WebView2
CapturePreview. No OS dialogs or desktop controls were automated; no model ran.

All18 corrected PNGs were individually inspected: Root12 and independent
frontend reviewer6 (reader, Mira, Sable, receipt, narrow and denied). No further
visible layout defect was found in their captured areas. The empty and populated
saved-run placeholder fits in the corrected captures. The620px reader wraps
long output hashes, with no page or panel horizontal overflow. Captures scroll
to particular application sections, so they do not show the entire app at once.
Bounded JSON evidence is scrollable: Mira's private content below the visible
viewport is established by the actual semantic/native assertion, not by those
pixels alone. Live selected scope/head and inspected scope/head remain separate.

Both independent Node and native inventories matched, and all1068 comparison
files /15054826 bytes remained identical across restart. Their digest is
`dd7ed11cee3ae08f8fd7a3031d4b1cf78d28590a2e1961b2558e72edd314b0bb`.
The exact two initial and one restart read-only proofs were required by the
launcher, along with stage minima100/40; observed counts are198/69. This covers
completed resume, inspection and cold-open/read/close without regenerating data.

Executable SHA256:
`f7a7fd5c2793bbf847e99d82e9e7bd3607a24dac8b6cd0f34a35d3e00d871973`.
Launcher SHA256:
`480cf82be1c2e2363ded8edf591ce6c97e85fed32b8fa8fdd735d939cc964bba`.
The captured user agent reports Chrome/Edge155.0.0.0, device pixel ratio1,
1280px normal and620px narrow viewports; this is not an independently queried
WebView runtime patch version. No clean-SDK universal guarantee, leak, model
quality, human enjoyment, physical-device or release claim follows.

## Reproduction

From repository root, using the coordinator's existing isolated native target:

```powershell
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir <NATIVE_TARGET> --bin locallore-desktop-spike evaluation::comparison_run::review_tests:: -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --target-dir <NATIVE_TARGET> --bin locallore-desktop-spike comparison_run_commands:: -- --nocapture --test-threads=1
```

From `apps/desktop`:

```powershell
<NODE> check-comparison-run.mjs
<NODE> verify-frontend.mjs
```

For the closed app-owned launcher, from a clean checkout at the intended source:

```powershell
$env:LOCALLORE_D07_FULL_COMPARISON_ARTIFACT_ROOT = '<EXISTING_ABSOLUTE_TASK_ARTIFACT_ROOT>'
$env:LOCALLORE_D07_FULL_COMPARISON_TARGET_DIR = '<EXISTING_ABSOLUTE_EXTERNAL_NATIVE_TARGET>'
$env:TEMP = '<EXISTING_ABSOLUTE_OWNED_TEMP>'
$env:TMP = $env:TEMP
& '<NODE>' '.\apps\desktop\comparison-run-harness.mjs'
```

The launcher accepts **no CLI parameters**, requires Windows and ordinary
existing absolute artifact/target directories, and refuses a build target
inside the repository. It builds the frontend and native dev-harness with
locked/offline, one-job settings, then owns only the hidden initial/restart
processes and bounded output. Its fixed app watchdog is900,000ms and outer
launcher watchdog960,000ms. Limits are bounds, not a cleanup/timing guarantee.
Do not reuse protected or unrelated task directories for these placeholders.

`<NATIVE_TARGET>` is task-owned. `<NODE>` in the retained frontend process record
is the bundled Node24.22.1 executable. Root observed this turn's environment:
Rust/cargo1.93.1, Node24.22.1, PowerShell7.6.5, WindowsNT10.0.26300. This author
did not independently execute version queries or measure hardware/runtime builds.
Native Rust test process records include exact arguments and timestamps; test
durations above are not total command wall times or user-facing latency metrics.

## Final local qualification and source closure

All final commands below ran on clean, unchanged
`7e628deda0f69a182d7c8b97f56de0f8e5e487f9`, tree
`acc73237dfce1c8e45333b3dae7b59909167160c`, with locked/offline dependencies,
one Cargo build job and serial Rust tests. Source-bound process records retain
the exact arguments, timestamps, exit status and clean/unchanged proof.

| Final check | Result |
|---|---|
| Unfiltered native all-features suite |209 passed,0 failed,5 ignored;1322.01s test time,33.73s compile. Both standalone harness-contract tests also passed. |
| Strict native all-features/all-targets Clippy |Pass, warnings denied;6.73s. |
| Full frontend verifier |Pass;22.325s command wall time. Strict TypeScript, current controller/schema suites, normal frontend build and test-hook exclusion including the new full-comparison markers. No aggregate assertion count inferred. |
| Whole frontend Prettier / Rust workspace format |Both pass. |
| Android Rust host library |20 passed,0 failed,0 ignored;1.80s test time. |
| Android normal/build/dev dependency graph |Pass; no local-runtime, llama, LiteRT, Tauri, WebView or Wry matches. This is graph/host evidence, not an Android build/device run. |
| Normal native desktop build after normal frontend restoration |Pass;24.04s compile,24.209s command wall time. The restored normal executable was not launched. |

The five ignored tests are four explicit approved-asset native-model experiments
and one Windows symlink-privilege test. They were not run or counted as passes.
Earlier separate shared native-model qualification is not reclassified as this
scripted desktop cohort. No JVM/Gradle/SDK/ABI/APK/emulator/physical-phone cohort
or new model/asset download was performed.

Normal unlaunched executable SHA256:
`5926787a8a59120531d3c8bd4c8a18f30ded173fe724ad6ecbd5da833e4ee43f`.
Restored normal frontend SHA256:
`8c063930b9e9ac223168df51686fc8fe4270bfcd43c7869db5ebd223546a2c08`.
These are artifact identities, not reproducible-build or normal-render execution
claims. Existing pinned dependencies include React/react-dom19.3.1,
TypeScript7.0.2, esbuild0.28.2, Prettier3.9.10 and Tauri2.12.5.

The local seal `d07-full-comparison-qualified-evidence-seal1.json` binds all eight
final process records,48 retained local evidence files, both native cohort
qualification/report hashes and normal artifact hashes. Its SHA256 is
`f75a8541435f92e40efa8ea6559a49f3b07a7506415693854757fff2321db01a`.
Visual manifests identify every image and reviewer: first-cohort manifest SHA256
`4d555db718f9b5a1a33c1c3dbfdcb1385d54e770759958f4441a958a1978581a`;
corrected manifest SHA256
`3f90348b3effd9b8303dcc955c4be9c64ebdd6ab899121623936aaef34ee4eda`.
All artifacts remain local and ignored. Byte-identical review copies add no
independent rendering evidence.

Since actual UI source381abe50, the checked candidate changes only this evidence
document, the desktop README, the normal hook-exclusion scanner and two redundant
test borrows. Production Rust/frontend action and render code are unchanged.
Subsequent finalization must remain documentation-only and is verified by diff;
it is not a claim that every command ran at the final documentation commit.
Merge acceptance and fresh exact-final-head GitGuardian success are tracked in
PR211 and ticket29. The owner's review override does not substitute for these
checks, change repository settings or fabricate an approval.

| Gate | Current disposition |
|---|---|
| Actual hidden/unfocused app-owned WebView journey, initial and fresh-process restart | Corrected cohort passed198/69 at381abe50; exact source binding above. |
| Actual UI paired/resume/rollout, unknown ACK/recovery, independent reader/privacy and cold reopen | Both cohorts passed as attributed above. Rust/mock evidence remains separately classified. |
| Application-owned PNG/semantic captures and all-image visual inspection | All36 images across both cohorts inspected; first defect retained and corrected rerender verified within captured areas. |
| Bounded frontend/native errors, process exits/timeouts/truncation | Each cohort: intentional1/0 frontend errors, native stderr0/0, both exit0/no timeout/overflow. |
| Final native suite, strict lint/format and normal build |Passed as attributed above; normal executable compile only, not normal native rendering. |
| Final frontend/format and normal frontend/native restoration |Passed, with artifact hashes and normal hook exclusion above. |
| Shared compatibility, Android Rust-host/dependency checks, unavailable checks |20 host tests and graph passed; excluded model/privilege/device checks explicitly listed above. |
| Final source closure, artifact manifest/counts/hashes and PR status |Local gate passed at7e628ded; subsequent docs-only diff and final-head security/merge remain PR workflow facts. |

The fixed launcher uses the existing development harness and native-only
synthetic fixture surface. Both completed runs are attributed above. The user forbids desktop control:
evidence must remain application-owned
CapturePreview/semantic output, with no desktop screenshots, input injection,
window activation or unrelated application automation.

## Retained local evidence

Logs/process records are private, gitignored under `<TASK_ARTIFACTS>`; no raw
story, model path or machine-specific absolute directory is published here.
The following hashes identify the earlier terminal logs retained for this record.
The final seal above also binds the completed application and final-check records.

| Log basename | SHA256 |
|---|---|
| `d07-full-comparison-service-first2.log` | `252957ac904cfaf29f7ab32bb039d941c9392cda38fdc6857cd4b636213be6be` |
| `d07-full-comparison-budget-red1.log` | `8d4986056e10a917debfd4e57ac1c40d6608f61129ae151a7a958dde2bd36523` |
| `d07-full-comparison-budget-green1.log` | `674e2f07a4c56d21d9dfbd57bafde24d75ad6dd3a001b00d787d02ed79d16c21` |
| `d07-full-comparison-service-corrected1.log` | `ecc1acc051470b11df9246fa22c1ac89fe462a94de85acb00221000ee3bb5c5b` |
| `d07-full-comparison-fe-first1.log` | `fbb61499605bca8ac4d07608003dd183c59df4e628baac5bf6aa57bc3c0b1688` |
| `d07-full-comparison-fe-wire-red1.log` | `7920b7f3be8f32c97c4e09b49910e9cc63ffc081cb048e6ce750548f3c6fe20d` |
| `d07-full-comparison-fe-wire-green1.log` | `f8b46b4e62c085f5ee988750248173a738215ba65d175c6b4686acd740bcebe2` |
| `d07-full-comparison-frontend-wired1.log` | `14fd3c0159dce9f75f6ca210a4c8e2fdc9721cdedc2ece2a269175d102edd0b9` |
| `d07-full-comparison-wire-native1.log` | `88a0c97dc64679e3691971df8af1030cf12b4b870acc35a4a5d0d4dc6fd43b13` |

Ordinary desktop **native-model execution remains unavailable** in this scripted
slice, although shared native producers have separately qualified prerequisites.
Scripted reports preserve real outcomes and do not establish prose quality,
human enjoyment, fair model superiority, offline/whole-RAM/performance behavior
or phone parity. No downloaded assets, provider selection escape, canonical
rewrite, competing persistence or automatic inference on inspection is authorized.
The next runnable implementation is the separately scoped ordinary-desktop native
full-comparison adapter on the accepted shared runner and existing model owner,
after this focused PR is eligible. Whole D07, human quality and other desktop
epic gates remain unchecked until their own actual acceptance criteria are met.
