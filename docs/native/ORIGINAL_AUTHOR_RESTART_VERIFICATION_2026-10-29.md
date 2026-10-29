# Original AUTHOR / PLAYER restart verification — 2026-10-29

Refs #13 (M09.06) and #14 (M10.02). Supporting implementation is in_review in
draft #256, stacked on open/unmerged #254 at7600b42a. Full milestone acceptance
and checkboxes remain unchanged. This packet executes real **Windows host
process deaths with scripted inference**; the new Android method is compiled
but **UNRUN**. The earlier real-model/internal-reopen result remains separately
attributed to [#254](OWNED_TARGET_VERIFICATION_2026-10-29.md).

## What changed

The new Rust integration test commits two original public-fixture worlds and a
separate branch canary through the actual Host/SQLite Store. Its parent waits
for a forced, atomically published ready record, kills/waits its held AUTHOR
child before consuming the commit reply, and recovers exact creation consent in
a new process without generation. Wrong review hashes, foreign creation keys
and cross-story/branch requests refuse without canonical mutation.

A supported free-text PLAYER request runs the actual director/validation/
narrator/prepare/commit flow with a clearly scripted provider. After another
held-child kill/wait, a third process returns the same accepted receipt for
exact retries without even constructing a provider. Main revision advances0→1,
with one receipt; the other story and sealed sibling branch remain unchanged.
NPC-only facts, false beliefs, other-story data and the sibling canary stay out
of PLAYER/director/narrator context. The test opens Story Lab mode for explicit
fixture setup/inspection; it does not establish an ordinary Android UI journey.

`original_author_restart_proof.py` is a pure bounded reader. It first validates
the complete original import/AUTHOR baseline, then binds six passive native
records, the exact canonical archive bytes, PLAYER snapshot, catalog, process
start/UID, pending observations and checked closure. It cannot authenticate
execution, process death or a target from metadata alone. Legacy readers and
SDK4 permissions/claims remain unchanged. See the
[frozen new protocol](ORIGINAL_AUTHOR_RESTART_PROTOCOL_V1.md).

`OriginalAuthorRestartInstrumentedTest` adds one explicitly selected passive
method. It uses the prior bound profile only with NativeWorkspace.openLocal;
there is no SDK owner, model/source-model read, generation or reconstructed
Seed. It checks two created=false native recoveries, canonical snapshot/catalog/
archive conservation, observed pending state and actual handle invalidation.
Platform JSON receives bounded strict grammar/duplicate-key checks. The fixed
output namespace is create-only and app-owned; descendant files remain regular,
non-symlink and on the admitted device. Compilation is not runtime evidence.

## Actual checks and source attribution

| Check | Executed source and actual result |
| --- | --- |
| Original proof adversaries | 21 tests,617ms, child0, stable10 selected source pins and known capture/cleanup. Synthetic byte fixtures call the actual old and new readers, without verdict mocks or model/device access. Included in the Root104 below, not counted twice. |
| Root focused host suite |5b45f5df3a960508b30a1dfbb810a7a53740298a;43948ms parent0;19 Rust tests and104 Python tests,0 failures/errors/skips, formatting and focused Clippy-Dwarnings pass;2065 tracked inputs stable. |
| Real process case within Rust19 | One composite scenario plus its normally no-op child test entrypoint. Three self-spawned child phases, two actual held Child.kill/wait deaths, followed by terminal successful recovery;27 state/capture files retained. Root scenario1.22s. |
| First Android build |5b45f5df;122329ms parent0;588 JVM tests/58XML classes pass; both APKs assembled/audited;2065 tracked inputs stable. New method compiled, unexecuted. |
| Corrected Android build |9433789f8bc4f7480e29022f4c7a6f99bf0bdce7;74149ms parent0;588 JVM tests/58XML classes pass; both APKs assembled/audited;2065 tracked inputs stable. New method still unexecuted. |
| Lint |0 errors/10 retained warnings in each Android build. Analyzer records analysis_did_work=false: cached analysis, not fresh analysis of the new test. Kotlin/Gradle warnings remain. |
| Independent closed review | No new test/runtime calls. Verifies both distinct build cohorts, exact code Git bytes, captured source maps,588 JVM methods, APK class/method strings, prior actual AUTHOR sidecars through the original reader, all27 new host-case files/deaths/counters/canonical scope assertions. |

Root host source and final Android source differ only in the new test's trusted
Context anchor resolution/comment. Rust/Python code bytes remain unchanged;
those tests were not rerun merely to relabel them at a later revision. Later
report/README commits are documentation only. No runtime/model/SDK/dependency
version or production engine/FFI behavior changed. Tools remain Rust1.93.1,
installed Java21, pinned Android/NDK packages and LiteRT-LM0.18.1; no download.

Final product APK remains78289152B/SHA256
`0ad6f03adf0179438570c7d4a7933f2ef7b1fd929ce7361c2627749168439fa9`.
Final test APK2272447B/SHA256
`215731ef23e46f1dd1d97f9fb846672eaa954467332069f8723520f3101a0221`;
first compiled test APK has the same length/SHA4321cb6f…728daa11 and remains
preserved. Both contain the new method strings; strings alone do not prove a
method executed.

Host result SHA256
`900328207b17c0437f9b81171628122ff985de6f0bb1f3b6c2d363b55ac1b447`;
Android v1/v2 result hashes
`2fef01214a95d606e48021790b6368e588f9e08643d2554d7e91487ef29ea483` /
`b6ee0e8915a2be11e4565bc64066661a067405e1148e33cb0d21a0adece7f013`.
Independent closed-review19438B/SHA256
`4d386c9fd9338d7eea3fdcb2b4479ec76dadd107e07f11e6b77396988b9717cb`.

## Original failures and corrections

Two actual initial Rust cohorts fail at PLAYER preparation after the first
successful committed-world death/recovery. The first did not retain its bounded
prepare reply; the second adds diagnostics while preserving the ready assertion
and captures ClarificationRequired with0 provider polls. The fixture phrase
`I wait for the next station clock tick.` lies outside the existing documented
numeric/one-tick intent grammar. No engine guard is relaxed. The final positive
case uses `I wait for one tick.` and adds an explicit negative for the original
phrase: canonical state unchanged,0 generation requests,1 constructed provider.
This is a corrected positive fixture with a retained negative, **not identical
whole-test RED/GREEN or a fixed production inference defect**. Recovery in the
third process separately has0 provider factories/requests. The provider factory
and generation request counts must not be conflated.

The initial spec's integer-session wording was corrected to the actual bounded
opaque Host string before dependent implementation. An original adversary
fixture boolean was corrected before its first run. Root caught an incorrect
one-key catalog assertion before the first Android build; the actual native
catalog has five keys. Independent review subsequently found the conditional
platform alias refusal: the new class used absoluteFile then rejected canonical
path changes, while the proven prior class resolved Context.noBackupFilesDir.
The corrected version resolves only that trusted top anchor; strict descendant
checks remain. Neither source finding is represented as an observed device
failure. Both earlier drafts/build products remain preserved.

The independent review's first two helpers refuse setup-only assumptions before
writing a final report: a Markdown CRLF-vs-Git-LF documentary byte check, and
conflating the negative input's1 factory/0 polls with the final recovery's0/0.
Final review records these separately. Code/captures/archive byte checks remain
exact; no captured artifact is normalized or repaired.

## Reproducible commands, preservation and limits

All local project commands ran from physical D worktrees with process-local
TEMP/TMP/TMPDIR on D. Cargo is locked/offline; Cargo/Gradle/Android caches and
all test outputs are D-local; installed tools and the existing signer remain
in their supported locations. No global setting or credential copy is needed.
Root's private source-bound runner records exact argv/environment/binary barrier,
finite Windows job, stdout/stderr, source-before/after and actual terminal state.

```powershell
cargo +1.93.1 fmt --all -- --check
cargo +1.93.1 clippy -p locallore-workspace --test original_author_process_restart --locked --offline -- -D warnings
cargo +1.93.1 test -p locallore-workspace --test original_author_process_restart --test original_story_authoring --test play_host --test generation_play_consumer --locked --offline -- --test-threads=1 --nocapture
```

The Python runner loads test_original_author_restart_proof,
test_original_author_model_proof, test_original_author_prompt_provenance,
test_original_author_diagnostic, test_original_author_stream_admission and
test_original_story_verification from scripts.tests. Android helpers use the
same offline Gradle prefix/tasks as the prior owned-target build, separate
create-only sdk-build-v1/v2 outputs, an existing signer read in place, D caches
and no provisioning. No connected/installed-device task is invoked.

Root packet: `D:/Dev/Experiments/LocalLore/2026-10-29-author-player-restart-v1`.
Separate agent pure-test and native execution roots retain their original names
`2026-10-29-original-author-restart-v1` and
`2026-10-29-original-author-process-restart-v1`. The original failed states
`locallore-original-author-process-restart-50984-1793275195934971200` and
`…-8636-1793275281996566000`, plus passing `…-45508-1793275473661873800`, remain
under D:/Dev/_Temp. Root's later27-file successful case is inside its packet.
Source commits, raw failures, databases/WAL, unacknowledged replies and counters
are retained. Normal generated target caches remain on D; their recompilation
is not an assertion that superseded compiled binaries were independently sealed.
Final recovery/hash receipt is posted to tickets separately; no raw diagnostics,
model weights, keys or guest state are uploaded.

Nested test readiness has a15s deadline and polls capture-file size against64KiB;
it is not a hard truncating sink or independently bounded kernel wait. The actual
successful Child.kill/wait calls terminate; Root's separate360s owned job/capture
ceiling bounds the whole host check. No general sandbox claim follows.

M09.06/M10.02 remain partial/in_review. Actual Android post-creation process
death, broader PLAYER/UI, physical-phone/ARM64, sustained performance and real
mid-generation cancellation are still unqualified. The earlier real-model pass
is not rerun or substituted for these gates. No emulator/model/device call,
other-emulator stop, settings/access change, release or merge occurs here.

Next runnable task: implement the separately admitted third passive-method
controller/claim and same-boot death/receipt collection. A future live cohort
needs concrete fresh authorization and must capture AUTHOR then app-process
death within one admitted Android boot; elapsed starts cannot compare across a
VM/OS reboot. The retained stopped guest's old proof and spent boot/import/AUTHOR
claims cannot authorize that run. Leave all old captures and acceptance criteria
unchanged.
