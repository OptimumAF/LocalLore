# Scripted selected Scene4 desktop qualification

2026-10-29. Refs #29 (scoped D07.02/.04/.06/.07), parent #21. This document
records measured evidence, not the issue checklist. The application-owned scene
IPC/render/restart harness is implemented but actual application execution remains
unrun at this checkpoint. No
native rendering, new model result, quality improvement or whole D07 acceptance
is established by the adapter tests below.

## Behavior and boundaries

The adapter uses accepted shared PR268/main `4c83ed79` and its opaque selected3
plan/read APIs for source Protocol4. Desktop does not reconstruct an Engine from
a report or create another storage, provider, memory or validation implementation.
Rust retains source/index equality, actual before-state/prefixes, idempotent Start,
canonical receipts, cancellation, permission and observer enforcement. Source,
selected manifest resume and selected read bindings are separate identities.

Story Lab can prepare a separately identified scripted selected scene experiment
from a ready reader, then explicitly Start and request read consent. Literal scene
and Relevant memory scene constructions, finite privacy evidence, unavailable
recovery/timing fields and fake inference are labeled. ApprovedNative selected
scene execution remains unavailable; Rust refuses before the consent callback or
model reservation. The UI disables that choice and cannot silently turn it into
a scripted request. Existing source2/selected1 and source3/selected2 routes remain.

The frontend checks the requested source binding before publishing preparation.
It keeps a pending resume expectation separate from the retained preparation: a
failed different-source attempt preserves the genuine native mismatch and old
identity; a successful terminal response must match its pending source before
promotion. Existing client/context/operation/read fences remain. Inspection grants
do not change character knowledge or generation inputs.

## Frozen source lineage

The [desktop contract](D07_SELECTED_SCENE_DESKTOP_CONTRACT_2026-10-29.md) was
accepted988d425f, with decoder/controller immutability293145a6, parsed-input
hygiene de406270 and actual native negative-control8c5bfabd precisions before
independent FIRST. Retained-versus-pending resume precision is9ae23b34.

| Contribution | Original source | Root integration / formatting |
| --- | --- | --- |
| Native manager FIRST, eight groups |949633f1 |fa99aa98 /10aeec7d |
| Native versioned adapter |b46d9025 |f2238216 /9f20d315 |
| Frontend FIRST,16 source groups |8a4c214f |3777981a /9f20d315 |
| Frontend production, three files |24de4bac |68b0ecf0 /d0689877 |
| Actual App/reader integration and scoped old-stage assertions |Root9ae23b34 |same |
| Valid detached requests / ready reader correction |Rootb2468e00 |same |
| Independent added resume regression, explicitly post-production |bcb5b413 |8174bdb7 /b60b56fa; registration8ba50476 |

Native FIRST raw SHA256 is
`4f24ab2915929b7dd62751aba34ed597c766464e84c88ee9f0983022f988361e`;
its independently formatted source equals
`9ca857baa9b5069e75382941fb32090b18fd68524221210a7eba874ec4aeac5d`.
Frontend FIRST raw is
`8abfecef2ab5555d3069907295aea1c80f0115e065fb8a75d12e8cd07c1dec78`;
formatted source remains
`94f269d5d161f8bd2559f94f623c05f2aff3fb0141eb0ac91b48d91481ca358c`.
Resume regression raw is
`62b5c40b6c3bf8de6dbe4f33cad2d670afde78890ddd011fe0402bee4674334d`;
independently formatted source equals
`c89a948fe30a23fa4cc634d3c06d5a232f8d8bf4b6e713c40bc86625984c16be`.
Raw sources, independently derived copies and equality records remain local.

An independent native source review at9ae23b34 found no actionable issue in
binding-before-write, cold index routing, no-reservation native refusal, retained
cleanup ownership or the narrow obsolete-assertion supersession. This is source
review, not GitHub approval, human acceptance or runtime evidence.

## Commands and measured results

Run project commands from their physical D checkout. Set TEMP and TMP to
`D:/Dev/_Temp`, the existing admitted Cargo home/target to physical D, Cargo
offline, jobs1, incremental0 and dev/test debug0. Node here is the existing
24.22.1 executable. Examples below normalize only executable and checkout/cache
prefixes; local process records retain the exact full command, source, timestamps,
exit, environment, source-clean/unchanged result and log hash. No dependency or
model download occurred.

From repository root:

```powershell
cargo test --locked --offline -p locallore-desktop-spike --bin locallore-desktop-spike --features dev-harness evaluation::selected::tests::scene_v4_review_tests -- --test-threads=1
cargo test --locked --offline -p locallore-desktop-spike --bin locallore-desktop-spike --features dev-harness evaluation::comparison::scene_read_review::v4_selected_scripted_prepares_while_native_refuses_before_consent_or_model_reservation -- --exact --test-threads=1
cargo test --locked --offline -p locallore-desktop-spike --bin locallore-desktop-spike --features dev-harness evaluation::comparison_run::scene_native_review::separate_actual_scripted_scene_source_prepares_scripted_but_native_refuses_before_consent -- --exact --test-threads=1
cargo test --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --features local-model --test scene_comparison_reader_v4 actual_scene_report_snapshot_is_bound_read_only_and_lossless -- --exact --test-threads=1
cargo clippy --locked --offline -p locallore-desktop-spike --all-targets --features dev-harness -- -D warnings
cargo check --locked --offline -p locallore-android
cargo fmt --all -- --check
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml -- --check
node apps/desktop/build.mjs
cargo build --locked --offline -p locallore-desktop-spike --bin locallore-desktop-spike --no-default-features
```

From `apps/desktop`:

```powershell
node node_modules/typescript/bin/tsc --noEmit
node check-selected-scene-v4-review.mjs
node verify-frontend.mjs
node check-selected-scene-resume-identity-review.mjs
```

LOCALLORE_SELECTED_SCENE4_NATIVE_TEST_ROOT points to the admitted existing fixture
parent; LOCALLORE_CHECK_OUTPUT_DIR points to the admitted frontend output parent.
Both are local-only output controls, not app command or renderer capabilities.

| Check | Exact source | Result | Test / whole command seconds |
| --- | --- | --- | --- |
| New native manager FIRST |9ae23b34 |8pass/0fail/0ignored;302filtered |280.34 /300.8999176 |
| Old reader scripted/native stage supersession |e3c5cf51 |1pass;309filtered |21.29 /33.8477896 |
| Old actual source scripted/native supersession |e3c5cf51 |1pass;309filtered |15.16 /15.682932 |
| Shared source summary/note/grant check |53df4d3f |1pass;3filtered |9.70 /18.6719372 |
| Corrected types |b2468e00 |pass |command0.3177603 |
| Unchanged frontend FIRST |b2468e00 |setup ready;490/490pass;27 static HTML artifacts |command1.3014077 |
| Complete frontend driver |b2468e00 |pass, including old contracts and normal hook exclusion |command18.4658283 |
| Added independent resume identity regression |8ba50476 |setup ready;29/29pass |command2.3390769 |
| Desktop Clippy, all targets/dev-harness |53df4d3f |pass |command11.8946043 |
| Android Rust Windows-host compatibility |53df4d3f |pass |command0.3245512 |
| Workspace format |53df4d3f |pass |command1.9217887 |
| Separate Eval format |53df4d3f |pass |command0.5594356 |
| Normal frontend build |53df4d3f |pass |command0.2992036 |
| Normal no-default-feature desktop build |53df4d3f |pass, executable unlaunched |command15.0234647 |

The native manager FIRST uses actual shared paired/rollout noninitial selected
inputs, receipt/prefix equality and repeated Start; held in-memory model ownership;
native consent deny/error/cancel/close/epoch retirement; capability/source/window
boundaries; cold capability reopen and completed resume; actor Query2 versus raw
reads; six corrupt actual cold indices; and corrupted actual Prepared metadata
before target creation. Consent/ACK decisions are disclosed test doubles. Cold
epoch reopen is not executable restart. No model is loaded.

Frontend tests use actual decoders/controller/panel/App selection with synthetic
transport, React SSR, actual captured JSX handlers and separately disclosed hook
doubles. They do not execute a DOM browser, native IPC, WebView, images or engine.
The29-case regression was added after production source freeze; it is not
retroactively counted as pre-implementation FIRST. The full frontend driver
above precedes that registration; the added check was executed separately.

Clippy compiles the stopped offline qualifier as one target but never executes
it. Android compatibility is Rust Windows-host compilation only: no Gradle, SDK,
ABI, emulator, device, physical-phone or Android runtime qualification.

## Preserved failures and corrections

Original frontend d0689877 types passed0.3230577s, but unchanged FIRST failed
three of490 checks after1.4380027s, setup ready. Actor query and omniscient receipt
controller reads rejected valid null-prototype DTOs returned by established
reader helpers on their second validation pass. The new selected copy boundary
now permits null-prototype non-array data objects while retaining descriptor,
getter/toJSON, symbol, cycle, nonfinite and inherited-object rejection. The third
failure exposed App offering retained source during opening; ready/nonrunning
gating fixes it. No frozen assertion was changed. The originally queued full
frontend command was unrun after failure.

Original failure log SHA256:
`69b399a8949c899713cdd83e7aee81ebde48988d449cb1dd0767f79e143122e2`.
Complete original JSON/CJS/27HTML/log/process freeze SHA256:
`3d9081f1df196901a012c33b1b748aeaa5311667361b55d211267c8ef1063dd0`.
All originals remain local and unchanged.

A separate command incorrectly requested excluded `locallore-eval` from the
root workspace using `-p` plus features. Cargo refused at setup in0.1169604s,
exit101; no test executed and later queued checks remained unrun. The corrected
explicit manifest command above passes. The original refusal log is retained.

Accepted PR268's earlier failures, shared fixture freezes, real Native4 cohort
and human packets remain unchanged. Both human assessments remain
needs_improvement, without invented scores or case-specific feedback.

## Local evidence, storage and environment

Local packet basename: `selected4-desktop-20261029-v1`, under the task-owned
physical-D author-integration-artifacts parent. Logs, exact process records,
source hashes, source-only FIRST originals/derived copies, complete original
failure freeze, normal product hashes and17-command adapter-check summary remain
local/gitignored. The initial manager fixture packet uses an existing parent
supplied through its narrow test-only output variable. Nine further compatibility
roots in D:/Dev/_Temp total7,982,856 bytes and remain retained with an exact roster.

The cumulative shared+desktop evidence ceiling is512MiB; original target baseline
8,259,980,576 bytes and2GiB growth ceiling are not reset for this gate. Initial
admission measured target8,303,337,865 bytes and D free326,966,153,216 bytes. Later
harness admission must remeasure all retained packet/provenance/compatibility
roots, target/source growth and remaining cumulative allowance. No cleanup,
model copies, new cache root, guest or virtual disk is admitted.

Measured tools: Rust1.93.1, Cargo1.93.1, rustfmt1.8.0-stable, Node24.22.1,
PowerShell7.6.5, Windows10.0.26300.0 X64, React19.3.1, TypeScript7.0.2,
Tauri2.12.5 pinned. Loaded WebView runtime is unmeasured in this gate so far.
Complete normal four-file frontend bundle and unlaunched executable hashes are
retained separately. Normal app.js is
`71a5446b6ac5a0c6417fe93d6c04c32ec0fb4127517f50b3407099c65f35e1d5`;
normal executable is
`dda295ed425a215eaef3c57356ccb0ec234b9bc630465396b53a2d2915f16cfe`.

## Next qualification boundary

The separately reviewed [fixed scene harness contract](D07_SELECTED_SCENE_NATIVE_HARNESS_CONTRACT_2026-10-29.md)
accepts exact closed --scene mode, existing native IPC, hidden/unfocused owned
WebView, create-once/frozen sources, refusal of missing retained fixtures,30
success captures and genuine150% scale checks. Every generated image needs
individual inspection. No desktop control/capture/input, arbitrary execution
service, additional inference hook or SDK/OS probe is permitted.

Native harness FIRST edfad063 was importeddd9bc39a and registered/formatted
221cd4ab. Its raw SHA256 is
`7435b96be39957bbec4d9a620c0e983d6ce6e3653cc0de50158832bf68af105b`;
independently formatted source equals
`eb1da161d377bf4cefd7c5751080328c181fad420c7cb7c8552150b111fe2f2f`.
Eight groups are uncompiled/unrun until the accepted actual native helpers exist.
Their runtime forecast includes22 complete retained source-set equivalents plus
four small partial/guard packets; measure an actual template before full admission.
Missing helper/marker prerequisites are setup gaps, never zero-test passes or
observed behavioral RED. Process-policy FIRST is still source-only in preparation.

Actual native IPC/render/restart, improved story quality, native selected Scene4
inference, between-arm native interruption, Android runtime parity, stopped OS
security gates, packaging/release and whole D07 remain unqualified here.

## Subsequent harness integration checks before app execution

Native fixture FIRST edfad063 is integrateddd9bc39a/221cd4ab; actual producer/
launcher source e68e8790 is integrated17bc72b6/02df4593. Journey/labels af20a774
are integratedc65e2617 and writer8c605e5f is integratedf8dbf42b, formattedbe5d0370.
The source-only writer FIRST4128b6f1 precedes that implementation; seven groups
exercise the actual private writer, including pre-open refusal/no-refund I/O
failure, without large allocations or environment mutation.

| Check | Source | Actual result / whole command seconds |
| --- | --- | --- |
| Original process policy FIRST |02df4593 |152pass/3fail;155simulated cases;0.245323 |
| Context FIRST before product framing |02df4593 |0pass/25fail;26SSR HTML;0.3026773 |
| Framing types |7ece5405 |pass;0.3292751 |
| Unchanged context FIRST after product fix |7ece5405 |25pass/0fail;0.2906844 |
| Unchanged adapter FIRST after product fix |7ece5405 |490pass/0fail;1.3034198 |
| Calibrated policy FIRST |be5d0370 |155pass/0fail;0.2440883 |
| Native complete source-set calibration |88642b82 |1pass;185.98s test/201.8540142s command |
| Original native fixture eight groups |88642b82 |7pass/1fail;459.00s test/459.6881518s command |
| Actual writer seven groups |88642b82 |7pass;0.01s test/0.7322052s command |
| Corrected native path group only |5b3a2ef4 |1pass;0.01s test/19.1832561s command |
| Qualification baseline FIRST |5b3a2ef4 |61pass/0fail;0.208923 |
| Existing policy after baseline amendment |5b3a2ef4 |155pass/0fail;0.2809795 |

The policy's three original failures were synthetic timeout scheduling: a queued
successful predecessor Git child had not closed when the fake clock advanced.
Independent author correction cf92aef0 preserves all155cases and every original
post-fault assertion, adding a bounded wait/assertion for the intended manual Git
child and its timer before time advances. Unreachable readiness is setup/unrun.
The actual production policy helper hashes stay identical across that correction.

The native path failure was a portable fixture-construction defect, verified
against installed Rust1.93.1 source: canonical Windows verbatim paths make
PathBuf::push normalize parent components, and join calls push. The negative
therefore supplied a valid path. Independent correction98909267 builds the exact
lexical input via OsString then PathBuf::from, asserting ParentDir survives before
the unchanged refusal/byte checks. Production guards and other seven groups did
not change. Evidence is original7/1 plus corrected1/0, not one current all-eight
green command. The accidentally valid source set remains retained628files/
7,517,514 bytes, exact full failure-freeze SHA256
`6571ec1cddc8f7952d3d69fef3bce5490d74e15611b24fcf9c2b01458ce51522`.
Original policy/context failure-log freeze is
`31a3edf4673c02f1253e7d98a27e72915db2fb2e8c993cb3d98d9fe89c7c8c2a`.

The context checks use actual View/React SSR with a disclosed immutable
state/subscription double; no actual controller, pixels or native permission is
proven by those25cases. Existing490/29 controller checks remain separate. Native
fixture/writer checks execute actual Rust helpers/files with synthetic inputs;
they do not launch a WebView, IPC app, model or OS isolation probe.

Whole-qualification admission source9af0ddfd is integratede0dae2e9/6b3c418a;
independent FIRST dcac928c is integrated174c7775, registered5b3a2ef4. It requires
a create-new coordinator record with exact source/target binding and the original
target baseline plus measured external evidence. Its61cases exercise actual
decoder/startup/storage/process policy through disclosed VM doubles. Scene
snapshot semanticVersion3 is checked separately from legacy2. Final paired/right
and rollout/left fixtures retain the same original courier-05/index4 inputs;
restart checks exact role IDs and all saved/reopened IDs without generation.

Calibration measured one complete source set627files/7,517,007 bytes. The full
fixture forecast was revised BEFORE execution from128MiB to224MiB, preserving
all copies/failed bytes and the same512MiB total. Frontend forecast was likewise
revised from64MiB to96MiB before another justified full driver run. Neither
per-source64MiB, writer64MiB/process, original target2GiB growth nor the512MiB
cumulative cap was lifted. Retained total after native checks is440,735,510
bytes, with96,135,402 bytes remaining before later logs/metadata.

Full current frontend execution is deliberately scheduled AFTER actual native
layout/debugging and BEFORE the PR review/merge gate, avoiding another soon-stale
complete bundle set. Before app admission, the earlier full driver plus fresh
affected types/490/29/25/155/61, current normal build/exclusion assertions and
Rust native/lint/host checks must pass. No check or acceptance criterion is
waived. GitHub Actions is currently disabled (read-only verification); no setting
was changed or remote CI runtime claimed. The application cohort remains unrun
and needs its own exact measured admission record and individual image review.
