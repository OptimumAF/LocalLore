# Real original-author model probe — 2026-10-27

Refs [PR #236](https://github.com/OptimumAF/LocalLore/pull/236), #13 (M09.02/M09.06), #5 (M01.03), and #14 (M10.02/M10.03 support). The [experiment protocol](REAL_ORIGINAL_AUTHOR_MODEL_PROTOCOL_V1.md) defines the intended factory/JNI/model roundtrip and its separate admission gates.

## Result

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

Admit a fresh owned guest with the unchanged full resource and lease margins. Execute the binary transfer control and independently verify it before any model copy, then run the two individually selected methods under the existing protocol. A phone run instead requires fresh authorized identity/resource admission; the earlier empty host-only census established no phone profile. Preserve any refusal without editing its generated outcome or weakening admission. M09.02/M09.06 and M10.02/M10.03 supporting implementation is in review; actual real-model verification and full task acceptance remain pending.
