# Real original-author model probe — 2026-10-27

Refs [PR #236](https://github.com/OptimumAF/LocalLore/pull/236), #13 (M09.02/M09.06), #5 (M01.03), and #14 (M10.02/M10.03 support). The [experiment protocol](REAL_ORIGINAL_AUTHOR_MODEL_PROTOCOL_V1.md) defines the intended factory/JNI/model roundtrip and its separate admission gates.

## Corrected APK: import passes; original proposal is rejected

The exact corrected APKs now ran in a fresh owned 8 GiB/four-core API35/x86_64 guest. Runtime checkpoint `a63c95e9` has 2,008 tracked inputs and the same 884 compiled inputs as build checkpoint `11f8be70`; only the two existing protocol/report documents changed. The product/test APK hashes remain `4db224d6fc79dbe8e3ef02ab30d0339dc7e1f7f7391a3e41388cd669f4ec1e1e` / `f58fcdd3adc06da4b1e91fdf549cfd6b21f7b0d22c98c1ad160307ee60e235bd`. No rebuild, dependency change or model download is substituted for this admission.

| Check | Actual result |
| --- | --- |
| Binary control | All 65 destination bytes and SHA256 match. Its child closes after 46,777 ms with worker0 and known cleanup/capture. |
| Existing local model copy | Full held-source identity/hash and full 2,588,147,712-byte destination identity/hash match. The binary client completes in 85,472 ms; its child closes in 135,872 ms with worker0, known capture/cleanup and no stderr, within the unchanged 180-second owner. Direct `exec-in` still has no independent remote-exit-status claim. |
| Production import | One selected JUnit method passes in 24.461 seconds. The retained proof records 24,393 ms, one open, one close, all model bytes read off Main and the exact accepted-model hash. The strict host import validator passes. |
| Real AUTHOR | One selected JUnit method fails in 41.376 seconds at `generate/checks_failed`. The exact returned native envelope is `status:rejected`, `error:InvalidProposal`. Review, explicit creation, archive and reopen do not run. |
| Retained SDK traces | One real default-factory AUTHOR request, context4096/output-budget1024, one JSON_OBJECT send, 353 output chunks/765 output bytes and one DONE; no SDK error callback. Conversation and engine close are recorded known, with no UNCERTAIN count. These are trace observations, not a hardware callback-drain qualification. |
| Runtime owner | `child_exited`, 625,298 ms, worker1, known cleanup and complete capture, 1,414 stderr bytes retained. The overall result remains failed; source/compiled maps are unchanged and the parent manifest is complete. |

The captured `InvalidProposal` comes from native semantic validation after response deserialization. The precise violated rule is unknown: this harness retains the rejection envelope and trace counts but not the original rejected response or a granular validation code. Only four pre-review records and four traces accompany the refused proof. The post-generation workspace observation is also absent because the harness stops at the rejection. No generated output was replaced, repaired or retried to obtain a pass. Import and real SDK completion are established; the complete factory/JNI/create/reopen roundtrip is not.

The unchanged read-only transfer admission is now reviewable in `benchmarks/original_author_stream_admission.py`, with 14 original synthetic adversaries in `scripts/tests/test_original_author_stream_admission.py`. The public module is byte-identical to the private module used by this runtime (5,711 bytes, SHA256 `64899c1552e1472f7aaba476eb1b52523a095cc483e3f4e3608d07a2455f6faf`). Both private and public executions pass the same 14 methods, zero failures/errors/skips; these are two executions of the same cases. The public promotion owner closes in 5,746 ms with worker0, known capture/cleanup and 2,010 unchanged inputs. No SDK executes in those tests. The single read-only batch retains both UIDs, installed APK hashes, safe distinct paths, profile/user, exact framing, bounded decimal parsing and the original storage/memory floors. Parent, child, direct-stream, JUnit and guest budgets remain unchanged.

Source review found and fixed an undefined transfer UID argument before runtime execution; its earlier drafts remain unexecuted. The original malformed-CR test draft and pre-decimal-bound sources also remain unexecuted, not fabricated failing test runs. Two closure drafts were superseded during source review; the executed closure keeps successful partial phase evidence distinct from a failed overall owner result.

The exact guest closes through its proposal-bound stop: 696,269 ms, worker1, known cleanup/capture/closure and no flush claim. Seven fixed metadata files copy to C: with zero mismatches. The final existing-server observation passes with zero device calls and no unrelated-process census. No other emulator is stopped, no system setting changes, and no model or private diagnostic is uploaded. The initial bounded availability capture has zero rows; no physical-phone profile is established by it.

The next runnable task is bounded native refusal diagnostics and original-response preservation for the synthetic AUTHOR experiment, followed by a fresh admitted run without weakening semantic validation. Keep the failed proposal as historical evidence; a new diagnostic run cannot retroactively qualify it. Full M09.02/M09.06, phone/ARM64, cancellation, narrative quality, performance and milestone acceptance remain open.

## Earlier import failure and publication fix

A fresh 8 GiB/four-core API35/x86_64 guest moved past the original CRLF refusal. The binary control delivered all 65 bytes with the expected hash. The model's direct binary client completed in 85,672 ms with known capture and the verified full local source identity. Its separate supervisor expired at 180,042 ms before postflight completed. The initial owner closed after 471,075 ms with worker exit1 and known cleanup/capture. That attempt remains failed: its final manually recorded model-stream client lacks the following observer, and its historical manifest remains null.

A separately reviewed continuation first rechecked the same owned guest, exact transport, APKs and UIDs, fixed source roster and absent accepted/proof/workspace namespaces. New read-only checks verified both the 65-byte control and the entire 2,588,147,712-byte model destination against their expected hashes. Storage had 8,565,837,824 bytes free; available memory was 6,700,707,840 bytes. Both unchanged margins passed. No model resend, reinstall, clear or generation retry occurred.

The first production import actually ran **one JUnit method and failed one assertion in 12.354 seconds**. Its retained proof records one open, one close, all model bytes read off Main, `accepted:null`, and `import/checks_failed`. The continuation owner closed after 180,678 ms with worker exit1 and known cleanup/capture. All 93 continuation client/raw pairs are complete and bracketed. AUTHOR, inference, explicit creation and reopening did not run. The caught inner import exception type was not observed.

The continuation also retains an orchestration error: an extra launcher diagnostic requiring 1,000 seconds of headroom refused, but the launcher erroneously dispatched anyway. The unchanged worker independently passed its required 950-second gate before creating its SDK capture. The failed extra diagnostic is recorded as a discrepancy, never as a successful admission; no runtime/resource limit was lowered.

Independent inspection found a necessary packaging defect: both exact original APK libraries omit `Java_org_locallore_app_NativeModelPublication_publishNoReplace`, while retaining their other JNI exports. Native feature selection enabled `model-provisioning` only for the setup profile, whereas the LiteRT-only experiment calls that production import path. This proves a missing prerequisite consistent with the failure; the generic failed import proof does not identify its inner exception.

The fix at executable checkpoint `11f8be70` enables that existing native feature for LiteRT candidate builds as well as setup builds. Its boolean remains a declared native-task input. A read-only configured-task probe reproduces the old selection failure, then passes after the fix; setup stays enabled and the ordinary profile stays disabled. The APK auditor now requires the defined public JNI function in both candidate ABIs. It checks bounded dynamic-symbol/string/section tables and executable file-backed mappings; an embedded name, undefined/local/weak/hidden/object symbol, malformed bounds or one missing ABI refuses. Ordinary auditing retains its existing contract.

Actual fix checks are separate from device inference:

| Check | Actual result |
| --- | --- |
| Configured task input | Old `041e3b7f`: LiteRT true/setup false, actual publication false/expected true, Gradle exit1. Fixed `80431b06`: true/true selection, Gradle exit0. Setup control remains true; ordinary control at `11f8be70` remains false. All four bounded owners close with stable per-run sources. |
| Auditor adversaries | Original negative test gives two ABI subtest failures against the old auditor. Corrected auditor passes 65 focused tests, including nine new tests and existing APK/physical audit modules, zero failures/errors/skips. These are synthetic ELF/ZIP tests. |
| Actual old APK | The new `audit_zip(..., litert=True)` rejects the retained original product for its missing publication export. No native library is loaded. |
| Corrected build | Both debug APKs assemble offline; product/dependency/analyzer audits pass. The owner closes in 56,941 ms with worker0, known cleanup/capture, zero stderr and all 2,008 tracked inputs unchanged. The native build task executes; cached Cargo products are not described as wholly fresh compilation. The corresponding compiled-input map has 884 entries. |
| Focused JVM tests | 31 actually execute again: 27 model-store and four author-worker tests, zero failures/errors/skips. |
| Lint | Zero errors and ten retained warnings. Main, Android-test, unit analysis and report are all UP-TO-DATE; analyzer32.4.1 records `analysis_did_work:false`. This is reused analysis/report evidence. |

The corrected product APK is 78,235,120 bytes, SHA256 `4db224d6fc79dbe8e3ef02ab30d0339dc7e1f7f7391a3e41388cd669f4ec1e1e`. The test APK remains 2,247,119 bytes, SHA256 `f58fcdd3adc06da4b1e91fdf549cfd6b21f7b0d22c98c1ad160307ee60e235bd`. Both corrected product libraries pass the dynamic-export audit: x86_64 is 9,319,560 bytes/SHA256 `14f48a3a61b7a91c16eda7a01820b1cd380c56ec4bb600507d75159ee7e16ef6`; arm64-v8a is 8,342,304 bytes/SHA256 `0e6e3747905b5fd138f03b94eca4b0159ad7cd811e0aae974e6470cc69d2643d`. These are packaging results, not ARM64 or model execution.

The configured check can be reproduced from `apps/android` with the same offline/toolchain flags used below, adding `--init-script ../../scripts/probe_litert_publication.gradle` and selecting only `:app:inspectLocalLoreModelPublication`. The LiteRT profile uses its reserved `.gradle-litert-worker` cache; the ordinary control omits that property and uses `.gradle`. The focused auditor command from the repository root is `python -B -m unittest scripts.tests.test_audit_apk_publication scripts.tests.test_audit_apk scripts.tests.test_audit_physical_model_apk` (the retained helper records the exact selected modules).

The failed fresh guest subsequently closes through its exact proposal-bound stop: owner `stop_requested`, 1,280,797 ms, worker1, known cleanup/capture/closure and no flush claim. Seven bounded metadata files copy to the host with zero mismatches. One final unchanged-existing-server observation passes with zero device calls and no unrelated-process census. The latest host-only availability capture has zero rows; it establishes no physical phone profile.

Failure preservation is independently replayed: 629 admitted originals, 633 copies, 634 ZIP members and 636 files/6,701,508 bytes, zero missing/mismatched. ZIP SHA256 `8ae7ed179e069a466495761489ace74176a6e9c79b146faada6966edf389f62f`; index `bbcf8bc52056f62dd11b9a2da6f927cc244b916d46c4c7388faf585d71932937`; independent verification `e4d1827835ec22c3aba7302aa4ca476efacdbfa9e7b016614c0680072c076ce3`. All 262 captured SDK2/raw pairs retain their scope: the initial set's missing final bracket is preserved, while the continuation's 93 pairs are complete. Both source cohorts retain their original 2,006/882 maps. This cohort excludes weight/image payloads and references only three small prior sealed controls. Fix-build/source recovery is recorded separately in the ticket handoff.

At that earlier checkpoint the corrected APK had not run import or AUTHOR inference. The later experiment above batches the unchanged read-only admission facts, preserves the limits and verifies both destinations before import. It establishes successful import and SDK completion, while retaining its original rejected proposal as a failed roundtrip.

## First attempt: CRLF parser refusal

The runtime attempt failed during host-side parsing of a resource sample, after the two verification APKs were installed. No model was transferred, imported, loaded, or invoked. Neither individually selected instrumentation method ran. This attempt does not qualify real AUTHOR inference, creation, reopening, a physical phone, or model quality.

A corrected continuation helper was prepared and reviewed, but remained unexecuted when the original guest lease no longer had the required admission margin. Its 950-second remaining-lease requirement was retained. The next runnable experiment requires a fresh admitted owned guest; the failed attempt remains failed.

The exact owned guest subsequently closed through its proposal-bound stop helper. The stop helper and original guest tool both completed with exit0. The guest owner recorded stop_requested after 981,416 ms, worker exit1, known cleanup, complete output capture and verified closure; no guest-flush proof is claimed. Its 11,229-byte stdout and 1,096-byte stderr were preserved. Seven fixed metadata files were copied to host evidence with zero mismatches.

The final postflight completed with exit0 and confirmed the unchanged existing server through one listener observation, with zero device calls. It made no fresh unrelated-process census: protected inventory was null and unrelated observations were zero. This does not establish that unrelated emulators or a physical phone were absent. Private recovery is sealed and independently replayed below.

## Implemented experiment and focused checks

The two-method Android probe uses the existing production model store and real default local SDK factory. Its intended sequence is import, one native AUTHOR generation, unchanged explicit review/create, native archive inspection, then passive inference-free reopening and exact creation retry. The pure host validator binds the captured proof artifacts, exact original response and provenance, unchanged library before creation, canonical snapshot conservation, and four independent AUTHOR trace snapshots. It leaves native domain validation and replay with the engine. Legacy DIRECTOR/NARRATOR trace readers retain their existing contracts.

The focused checks completed as follows:

| Check | Observed result and attribution |
| --- | --- |
| Pure Python proof validator | 24 tests passed, zero failures/errors/skips. The bounded owner completed in 8,279 ms with known cleanup and output capture, no stderr, and 2,003 source inputs unchanged. The validator/test bytes match the integrated sources. These are synthetic proof adversaries, not SDK execution. |
| Focused Android JVM checks | 31 tests passed: 27 in LocalModelStoreTest and 4 in OriginalAuthorWorkerTest; zero failures/errors/skips. The unit-test task was cleaned before execution. |
| Android build | Offline debug application and test APK assembly, dependency/analyzer audits and APK audit passed against source checkpoint 06472490. The bounded build owner completed in 109,469 ms with known cleanup/capture, no stderr and 2,005 tracked source inputs unchanged. The runtime bracket also retained the same 882 compiled inputs. |
| Lint | lintDebug completed with a retained report containing zero errors and ten warnings: OldTargetApi, GradleDependency, ObsoleteSdkInt and seven UsableSpace findings. lintReportDebug was UP-TO-DATE; this was a reused report. Android-test lint analysis executed. Cached Rust and other UP-TO-DATE tasks are not fresh recompilation evidence. |
| Corrected resource parser | All 13 pure cases passed in a bounded 115 ms host run, with zero stderr and unchanged helper bytes. Cases include the actual CRLF sample, equivalent LF input, bare CR, duplicate/negative memory data, low memory/space, malformed rows, non-ASCII input and oversized input. This invoked no SDK. |

The following are runnable equivalents of the focused checks. The retained runs additionally used bounded owners and original output/source bindings. Run the Python command from the repository root:

~~~powershell
python -B -m unittest scripts.tests.test_original_author_model_proof
~~~

Run the Android command from apps/android with the admitted local JDK, SDK and offline dependencies available. It preserves the exact selected tests, flags and tasks from the build helper:

~~~powershell
.\gradlew.bat --offline --no-daemon --no-build-cache --max-workers=2 --console=plain --project-cache-dir .gradle-litert-worker -PlocalLoreLiteRtVerification=true -Pandroid.experimental.lint.version=9.4.1 -Porg.gradle.java.installations.auto-download=false -Pandroid.builder.sdkDownload=false -Pkotlin.incremental=false :app:cleanTestDebugUnitTest :app:testDebugUnitTest --tests org.locallore.app.OriginalAuthorWorkerTest --tests org.locallore.app.LocalModelStoreTest :app:lintDebug :app:auditLiteRtDependencies :app:auditLintAnalyzer :app:cleanPackageDebug :app:cleanPackageDebugAndroidTest :app:assembleDebug :app:assembleDebugAndroidTest
~~~

This packet does not claim a fresh full repository matrix. Neither command runs a target instrumentation method or model inference.

The product APK is 78,241,840 bytes, SHA256 `e9f7e4c2d8ffe0ea978e2ea8fa75f62520218bc9b5cb2358994dc49e7eaa2c87`; the test APK is 2,247,119 bytes, SHA256 `f58fcdd3adc06da4b1e91fdf549cfd6b21f7b0d22c98c1ad160307ee60e235bd`. Product-policy auditing applies to the product APK. The test APK was separately byte-bound and its two method names checked, without substituting that check for a product-policy audit. Both product native ABIs retain the exact 8,117-byte corrected schema; packaging does not prove ARM64 execution.

## Retained failed attempt

The reviewed second private runner was executed once. Its outer owner finished after 164,896 ms with worker exit1, known cleanup and complete output capture. Its 1,390-byte stderr was retained; it was not treated as a passing run.

All 75 SDK client records and their original raw bodies were independently replayed: 50 existing-server observations and 25 target clients, all completed with exit0, known cleanup and zero stderr. Raw sizes/hashes, observer brackets and the pinned server identity matched. These clean clients do not convert the failed parent phase into success.

The captured sequence established the initially absent package pair, exactly two successful installs, package UID observations and installed APK hashes matching the admitted application/test APKs. It then stopped at the first resource sample. There were no source-directory creation, binary streaming, instrumentation or app force-stop calls. Import and author proof validation remained false; the JUnit result list was empty. All 2,005 current source-file hashes and the 882 compiled-input bindings matched the retained request and before/after maps.

The sample reported 6,481,469,440 bytes of available memory and 11,154,305,024 bytes of free storage. Both exceeded the unchanged experiment floors: 4 GiB memory, and two complete model copies plus a 2 GiB storage reserve. The failure was explained by the frozen parser and captured bytes: its anchored MemAvailable expression did not accept the carriage return preceding each line feed. The original sample contained 48 CRLF pairs and no bare carriage returns. Replacing CRLF with LF produces exactly one valid memory value. The inner exception was caught by the runner; this diagnosis follows from its source and retained sample rather than an exposed inner traceback.

The third helper normalizes CRLF only, rejects bare CR and malformed/duplicate rows, and preserves both capacity floors. Its narrowly bound continuation admission requires the exact failed attempt, known worker closure, all 75 client/raw bindings, the original two installs, the same source/APK/guest bindings and fresh package identity checks. It does not reinstall, clear application data or adopt another package. The original first helper and this corrected third helper remained source-only. Neither is a runtime result.

## Model and authority limits

An existing local 2,588,147,712-byte Gemma container was fully hash-verified against the protocol identity. No model download, target model copy, import or inference occurred in this attempt. The existing LiteRT-LM 0.18.1, artifact, runtime, worker, template and profile pins were retained.

The engine still owns accepted initial-world validation and creation. The model may propose a typed world; explicit review authorizes creation. Persisted original response/proposal/input and reviewed values remain distinct provenance. A fabricated self-consistent proof cannot authenticate a model run: exact source/APK/target admission, JUnit records and known host/SDK ownership are additional gates.

M09.02 real-model authoring and the related device/runtime gates remain unqualified. This packet establishes focused harness checks and a diagnosed host parser failure. It establishes neither physical ARM64 execution nor sustained performance, narrative quality, cancellation latency, joined hidden callback drain, supported hardware or release readiness.

## Preservation

The owner requested immediate preservation after reporting possible concurrent cleanup. All newly collected evidence and helpers are retained on the host system drive; only seven fixed, bounded, already closed guest metadata files were copied from the guest drive. No model, save, emulator image, cache, tool binary or private diagnostic was uploaded. The cleanup process and any earlier missing file's cause remain unestablished.

The create-only recovery contains 245 admitted originals, 249 indexed copies, 250 ZIP members and 252 files totaling 153,991,677 bytes. An independent verifier actually exits0 in 2,301 ms (1,989 ms internal replay), streams every original/copy/ZIP binding and checks exact rosters, with zero missing or mismatched entries. Failed V2 remains failed; V1/V3 remain unexecuted source. An unfilled postflight-pins template is explicitly labeled as a template and retained alongside the actual filled pins. Three unchanged first-version preservation helpers are retained as pinned source controls; the second version adds only that template path and those controls. Preservation is separate from feature acceptance.

| Recovery control | Bytes | SHA256 |
| --- | ---: | --- |
| Index | 167,949 | `27814399fe3012d55a5fd93f070eaa178008884d170cfb7826fdd7f7d2be872c` |
| ZIP | 56,601,521 | `59c352515ec99e8b29a65322b1d5ebd29f57f3c627bd70a9d6f2796c09b928e5` |
| Result | 1,104 | `3878982bd988ee8606e6bb8198840ddab3847fc11c7e1a7db0cf451b6e3fac02` |
| Independent verification | 901 | `6ac81db54bcb5989b5cc5db87b8041fd6559d1022aa8e3e3289745d8487d106d` |

The included source bundle preserves checkpoint `42e231782769678ae695590efca44e2ed25fef71`, all 1,251 named refs and 1,566 bundle heads, including all 312 distinct current worktree commit values. It is 12,881,234 bytes, SHA256 `24f854aeb6756497b97b83f8415c8c8eb1e89a857c4230696d27e3aea43b5a6a`. Git verification and named-ref/worktree-commit checks pass. Two initial source-bundle invocations refused unsupported helper arguments before spawning Git or creating files; the derived closed-attempt summary retains that attribution. This report's later recovery-note edits are committed and pushed separately from that source checkpoint. Earlier sealed recovery sets remain untouched.

## Next runnable task

Add bounded diagnostic evidence for the native semantic rejection, preserve the exact original synthetic response, then admit a fresh owned guest for a new run with the same resource and lease margins. A phone run requires fresh authorized identity/resource admission; the empty captured census established no phone profile. Preserve the original refusal without editing its outcome or weakening validation. M09.02/M09.06 and M10.02/M10.03 supporting implementation is in review; full real-model roundtrip and task acceptance remain pending.
