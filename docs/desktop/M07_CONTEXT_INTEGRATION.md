# Bounded context in production local play

Refs #11 (M07.01/.02/.06, partial), #25 and #28. The earlier
M07_CONTEXT_2026-10-22.md describes the original isolated prototype. This report
describes its production integration, based on accepted main
`32173cbd27487096be784f5b88a84d466fc72022` after integration commit `929de87`.
Functional commits are `d35c884` and compatibility correction `a46c1f4`.
Independent source review is recorded in M07_CONTEXT_INTEGRATION_REVIEW.md.

## Behavior and authority

The same `play::execute_traced` used by the shared Host now calls the portable
context compiler before director generation. A crate-private actor-only port
reuses the existing Profiles/Knowledge/Relationships/Promises eligibility rules.
No renderer-supplied inspector grant, omniscient selector, model-created truth,
new database, summary authority or inference backend is introduced. The compiler
and eligibility module compile without the native Host feature. SHA-256 becomes
a regular portable dependency at its existing locked version 0.10.9.

The compiler pins current rules/self state, known truth, current beliefs, open
commitments, directed relationships, recent eligible events and their visible
supporting evidence. Remaining eligible records use deterministic exact-ID and
literal lexical selection. Explicit references resolve only against eligible
identities. Historical root snapshots must be completed-turn boundaries; actual
fork context remains explicitly unsupported. The actor identity and source
revision stay attached to each selected typed record.

Model input contains selected typed payloads, kinds and source revisions. Rank,
omission and selection diagnostics are not model instructions. Dialogue uses an
empty factual retrieval query while retaining the original literal speech in
its exact-utterance proposal schema. The established inventory, living nearby
entities, route data, finite supported-English action guard and Engine validation
remain in the director path. Inspection privileges cannot alter this selection.

Whole-package accounting caps output at 24,576 bytes, 128 selected records and
the configured estimated token budget; optional records, candidate bytes/counts
and diagnostic entries also have explicit caps. Estimates are ceiling UTF-8
bytes/4, not measured tokenizer counts. A mandatory packet that does not fit
fails before the provider is called. Final serialized director input also has
the existing 24,576-byte cap. The native worker's actual fully templated input
tokens plus output allowance must fit its 4096-token context before decoding.
Compiler selection is now an actual Retrieval trace span with eligible-only
counts and explicitly estimated tokens. Summary maintenance remains not run.

Prompt provenance advances to `locallore-play-v2.2`. The exact accepted v2.1
fixture restores, replays, forks and retries without a model, preserving receipts,
projection and original outcome text. Fresh legacy prepared commits still reject,
and unmerged2.0 records still reject. Recorded compatibility is private to the
validated history rebuild path; no storage or receipt format change is needed.

## Reproduction and evidence attribution

Windows 11 Pro x64 10.0.26300, Intel i7-12700K, approximately 64GiB RAM;
Rust/Cargo1.93.1. Locked/offline commands use task-owned D: targets, debug
information disabled and incremental compilation disabled. Frontend checks use
bundled Node24.19.0 and existing locked dependencies. Android uses JDK17.0.6,
Gradle8.11.1, AGP8.10.1, Kotlin2.2.21, SDK36 and NDK29.0.14206865.

```powershell
cargo test --workspace --locked --offline --target-dir <task>/m07-context
cargo clippy --workspace --all-targets --locked --offline --target-dir <task>/m07-context -- -D warnings
cargo fmt --all -- --check
node apps/desktop/verify-frontend.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <task>/desktop-publication-target
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <task>/desktop-publication-target -- -D warnings
```

The synthetic production-provider regression creates more than 1000 accepted
events. It proves the old open promise survives selection, old distractors and
hidden-NPC canaries are absent from actual provider input, diagnostics are absent
from model data and candidate generation leaves the original Engine unchanged.
Additional cases prove budget failure invokes the provider zero times and exact
accepted v2.1 compatibility. Collector/production on/off golden tests still run.

An actual existing CPU worker/model scene on the changed prompt passed in
**32,252ms**: gift committed in11,497ms, secret dialogue committed in10,503ms,
rejected inventory/clarification/ability paths in4/4/5ms and cancellation in58ms.
Restart, exact retry and replay required no additional inference; observer secrecy
passed. This was native worker plus shared Rust Engine/SQLite, **not desktop IPC
or WebView rendering**. Local report: `target/context-scene.json`.

Approved existing Qwen3-0.6B Q8 model SHA-256
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`,
llama.cpp revision `620d2225cc436ab0b001e3200e590e3b286ef9ab`, worker SHA-256
`add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87`.
CPU4threads, context4096, batch512, GPU0, seed42, temperature0.7, top-p0.8,
top-k20, min-p0, presence1.5, maximum350 output tokens per role,120s turn budget.
No model download or hosted inference was used.

Both accepted turns used safe canonical narration fallback (**2/2**, zero
director repairs). Raw narration introduced unsupported details and was rejected;
`quality_accepted` is false. The report retains only last-role measured token
metrics:149/55 and154/48 input/output tokens for the narrator. Director tokenizer
metrics and actual long-history model usefulness/fit are not established by this
scene. `network_blocked` is false; an offline build is not a network-isolation test.

Review found a recorded v2.1 fork regression, corrected in `a46c1f4` with38
focused follow-up passes. Integration then exposed a pre-existing clock-tick
collision between parallel atomic-storage test directories. `3cecb9f` adds an
atomic sequence only inside the test fixture, preserving assertions and
parallelism. The original failing workspace log is retained separately from its
subsequent full rerun. No test expectation was relaxed.

Final integrated results: complete Rust workspace **230 passed, zero failed or
ignored**; strict workspace/all-target Clippy and formatting passed. Current
frontend/controller/schema checks passed. Native Windows default tests17 passed
with1 explicit symlink-privilege case ignored; dev-harness19 passed/1 ignored plus2
harness-contract tests passed. Strict dev-harness/all-target Clippy and the
normal native build passed. These are native unit/build checks, not WebView IPC
or render evidence for the changed context prompt.

Standalone runtime checks first exposed a pre-existing cancellation-test timing
assumption: a30ms sleep could cancel before the role thread began, legitimately
leaving the owner loaded. `2c0c293` changes only the development synthetic fixture
and test to wait for its actual generation-frame marker before cancelling.
The original blocked-stdin fixture mode is preserved separately. Final standalone
runtime tests **23 passed/1 ignored**, strict all-target Clippy and formatting
passed; the explicit Windows reparse case then **1 passed**. Thus all24 runtime
tests were actually exercised. Original failure and corrected logs remain local.

Android compatibility ran the actual offline Gradle tasks below with the
task-private Gradle home/output init script, SDK downloads disabled:

```powershell
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <task>/android-output.gradle :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain -Pandroid.builder.sdkDownload=false
python scripts/audit_apk.py <task>/android-build/_app/outputs/apk/debug/app-debug.apk
```

**78 tasks executed**, both Rust JNI ABIs rebuilt, app/instrumentation APKs built,
**38 JVM tests passed**, zero failures/errors/skips. Lint has zero errors and one
existing newer-coroutines-version advisory. APK capability and16KiB ELF/ZIP
alignment audit passed for both ABIs. The first audit invocation omitted the
SDK environment and failed before inspection; the corrected invocation with the
existing `ANDROID_HOME` passed. No APK was installed and no emulator, ADB or phone
was controlled. APK build success does not close a physical-device gate.

Logs are gitignored under `target/publication-*`; the successful complete
workspace rerun is `publication-workspace-fixed.log`, and final standalone
runtime output is `publication-runtime-final.log`. The real-scene JSON SHA-256 is
`23d5fc15e44a04937e20d6ae1948a86d41bd90be5a4148268c855a2a08e0cdfb`.

## Limits and next work

This slice does not complete M07 or D04/D06. SQLite FTS, maintained scene/entity
summaries, invalidation/resumable maintenance, full identity aliases, optional
semantic retrieval and durable branch context remain separate shared work.
Some compiler paths clone/collect before enforcing candidate caps and currently
have no compiler cancellation callback; maximum-scale responsiveness remains
unqualified. A bounded borrowed observer-event port is the next prerequisite
for the separately claimed derived-memory slice. No physical Android execution,
enjoyment acceptance, native context debugger or full prompt capture is claimed.
