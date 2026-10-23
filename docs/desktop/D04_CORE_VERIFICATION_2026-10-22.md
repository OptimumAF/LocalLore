# Shared local-play core: experimental guarded v2.1

Refs #9 M05.01–.04 partial implementation and #25 D04.04/.05 prerequisites.
The reviewed backend-only tree preserves accepted-main v1 behavior and introduces
an explicit versioned local-play record. Desktop runtime and UI follow in separate
dependent PRs; this tree does not by itself load a model or expose desktop model
management. No M05 phone/enjoyment or complete D04 gate is accepted here.

Original bounded FreeText kind/text/scope/head/key is persisted before generation.
Supported-English single actions compile to an exact attempted command; unsupported,
negated, quoted, compound or ambiguous forms require clarification. Rust prevalidates
that attempt before inference, then compares the untrusted generated proposal again
at preview/commit/replay. No valid substitute Wait/Move/extra command is accepted.
Dialogue remains exact text, with eligible present audience IDs in its decoding
schema. Neither inspector grants nor hidden NPC sheets widen generation context.

Narration receives approved outcomes. Spoken statement contents are withheld from
that role, so its input cannot establish a statement as fact. Conservative phrase,
speaker, event-reference and name checks select a visibly labeled engine-summary
fallback on known failures. These finite checks do not prove arbitrary prose faithful.
Generated prose never supplies canonical facts, knowledge or effects.

The Store uses its existing atomic draft/idempotency/receipt/projection transaction;
there is no schema fork, second ledger or model call on replay. An already-recorded
exact retry wins before unavailable-model/new-work checks. Generation runs outside
the Host lock and database writer transaction. A channel-synchronized regression
replaces the previous wall-clock-overlap assertion with explicit provider entry and
release plus a bounded watchdog.

Failed attempts retain their terminal phase in the existing durable port, which
does not store detailed failure causes. Reloaded failures therefore return a null
cause instead of inventing Provider; a focused actual-Host restart regression
covers that distinction. Current-attempt errors still show the observed category.

Accepted v1 bytes and exact narration equality remain unchanged. Unmerged synthetic
prototype2.0 saves are deliberately unsupported by guarded policy/prompt2.1; retained
old databases/reports/source pins remain historical evidence. This is not a migration
of human stories or an authorization to accept permissive legacy fresh commits.

## Verification and environment

Joint integration source `c97c9f1` supplies the shared Rust/schema inputs, with the
focused historical-failure honesty correction above added in this review tree.
Windows11 Pro10.0.26300, i7-12700K12 cores/20 threads, about64GiB
installed RAM; Rust/Cargo1.93.1, Python3.10. Node23.10.0/npm11.2.0 are the existing
local tooling, not a supported-LTS qualification. Debug info/incremental compilation
were disabled for task-owned builds. No desktop control, ADB or unrelated app was used.

From the joint integration checkout:

```powershell
cargo test --workspace --locked --offline --target-dir <task-build>/shared-rust
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --locked --offline -- -D warnings
cargo run -p locallore --example android_fixtures --locked --offline -- --check
```

**159 Rust tests passed**. The remaining exact `scripts/check.py` host commands also
passed:191 Python tests (116+10+14+20+13+18),4 Android fixture-parity cases and3 actual
native-linker tests. Logs remain local under the original checkout's ignored target.
The12 play-v2,7 action-guard,3 durable/ephemeral local-play Host and15 ownership tests
cover wrong action/arguments/extras, missing resources, bounded repair, cancellation,
stale work, provider panic, private-context canaries, exact speech, v1/v2 replay,
tampered effects/policy, unloaded restart/retry and real SQLite writer races.
After constructing the backend-only review boundary and adding the historical-
failure correction, the complete159-test workspace suite and strict workspace
Clippy passed again from that checkout. Its accepted-main desktop UI also passed
`npm run check` (strict TypeScript,25 original fixtures/current action builders,
hostile wire/keyboard/error checks and no normal-bundle test hooks) and
`npm run format:check`. The schema received formatting only; its values did not
change. These checks do not run a model or claim a native desktop scene.

Android compatibility used installed JDK17.0.6, Gradle8.11.1, AGP8.10.1, Kotlin2.2.21,
SDK36/build-tools35.0.0/NDK29.0.14206865. A task-only Gradle init script sets each
project's buildDirectory under `<task-build>/android-build`; source/config is unchanged.
Isolated Gradle home contains copied existing caches, with no shared-cache/daemon
changes or download. The actual command was:

```powershell
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <task-build>/android-output.gradle :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain '-Pandroid.builder.sdkDownload=false'
python scripts/audit_apk.py <task-build>/android-build/_app/outputs/apk/debug/app-debug.apk
```

All78 Gradle tasks executed, both Rust JNI ABIs rebuilt, app/test APKs built,38 JVM
tests passed (9+9+7+13; zero failures/errors/skips). Lint has0 errors/1 existing
coroutines-version advisory. APK audit passed permissions, both ABIs and16KiB
ELF/ZIP alignment. No connected instrumentation or physical-phone gate is implied.
The first invocation split an unquoted PowerShell `-P` argument and failed before
building; its log is retained, and the quoted rerun passed in3m3s.

## Real-model evidence and limits

The separate fixed-worker integration used existing Qwen3-0.6B Q8_0 model
SHA256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`,
llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`, corrected worker
SHA256 `eda393e923ddfd03ea57d91741d8f7948d1a4af13deb90c7d6c90c492e63ff58`.
Profile is CPU4 threads/context4096/output350 per role/one bounded repair/120s
turn deadline. No model download, hosted inference or cloud fallback was used.

The actual native CPU-worker + Engine/Store probe passed gift, Inventory refusal,
explicit ClarificationRequired, Ability refusal, exact speech scoped to Mira and
absent from Sable, cancellation/nonmutation, restart, exact retry and no-inference
replay. A UUID story ID initially exposed display-name `Mira` versus canonical
`mira`; the schema now constrains eligible actor/item IDs without forcing a whole
command. Reproduction with that same synthetic story passed in19.109s. Both accepted
narrations used explicit safe fallback. Earlier failed runs are retained, including
wrong valid actions, grammar property-order mismatch and unfaithful generated prose.
The dependent native app has separate actual controller/IPC/WebView2 render evidence;
headless rendering and engine-only proof are not presented as native app execution.

Remaining: arbitrary-language interpretation, new entities, NPC voices, semantic
prose fidelity, enjoyment comparison, actual network-blocked qualification,
sustained-session/memory metrics, correction/branch UI and full desktop/phone gates.
No performance threshold, superiority, installer, release or whole-epic completion
is claimed. Next runnable task is the dependent fixed runtime, then the desktop
model-management/UI PR and continued D05/D06/shared-memory implementation.
