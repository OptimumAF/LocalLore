# Fixed diagnostic UI build attestation v1

`benchmarks.diagnostic_ui_build` joins the preserved B103 source, build, JVM and packaging records to the current original/copy files and APK pair. It is a file-only prerequisite for a later diagnostic UI run. It creates no guest, reservation, target admission, receipt, run grant or Android result. Refs #14 (M10.03 DIAGNOSTIC_UI_BUILD_ATTESTATION; supporting M10.02).

The fixed product is PR #380 at `dafff3bce95cdcb7125095f9fee483e8373d45a8`, whose unmerged parent is PR #377. This utility stacks on #380. The input is a recorded **raw Git snapshot**, without a `.git` directory. It does not claim a clean managed worktree. Its byte-pinned baseline is deliberately specific to the preserved local B103 locations; another operator's build must receive its own reviewed baseline rather than a caller-selected override.

## Interface

Importing the module performs no project reads or process dispatch. `create_manifest()` accepts no arguments, validates the fixed inputs, and returns detached deterministic JSON-compatible data. It does not publish a file. `verify_frozen_product(artifacts)` accepts exactly three binding roles: `build`, `product_apk`, `test_apk`. Each binding has exactly `path`, integer `bytes`, and lowercase SHA256. The APKs must be the fixed baseline pair and the build file must occupy the fixed B104 manifest path. Verification recomputes the metadata and requires strict typed equality to the saved manifest.

From a physical D: source directory with the preserved B103 artifacts available:

```powershell
$env:TEMP = 'D:\Dev\_Temp'
$env:TMP = 'D:\Dev\_Temp'
python -I -S -B -c "import sys; sys.path.insert(0, '.'); from benchmarks.diagnostic_ui_build import main; raise SystemExit(main(['create']))"
```

`create` prints JSON only. Save it with exclusive creation at the fixed path named in the baseline, then use the same command with `verify`. No alternate source, APK, verifier, selector, registry or target argument exists. APIs raise a fixed `BuildRefused` category without echoing private file contents or paths; the CLI returns a fixed refusal message and nonzero status.

## Validated joins

- Both primary preservation manifests must contain identical bytes. Every one of the 2,725 original/copy pairs is read and hash-checked at the exact recorded mirror location. Every selected input, APK and JVM report must belong to that roster.
- All 2,581 source files match raw SHA256 and Git blob IDs. A pure Git tree implementation preserves recorded `100644`/`100755` modes and Git directory ordering. It does not infer executable bits from Windows filesystem modes or normalize newlines. The 2,580 before/after build rows agree exactly with the corresponding current files and reconstruct the tested tree. Only the declared later verification document is absent from the tested subset.
- The saved owner result must indicate the original successful full phase, known closure, unchanged source/tools and actual JVM task execution. The request must name the fixed offline full-build command. Exact critical task names must have fresh unsuffixed headers and the saved summary must say 81 actionable/81 executed. Gradle's repeated compile-test header around a warning is an explicit recorded exception; it is not counted as a second build. Stale JVM XML alone is insufficient.
- The 49 JVM XML suites contain 427 unique cases with no failure/error/skip elements or declared counts, including the eight source-declared shell-consent methods. These are **recorded B103 JVM executions**, not a new compiler/JVM run. Lint must contain no Error/Fatal finding. Saved packaging audit status, APK hashes, command roles, packages, certificate digest format and permission sets must agree. Installed audit tools are neither reopened nor launched; this is recorded audit evidence, not fresh tool-binary provenance.
- The six source-declared diagnostic methods must be actual test-APK definitions, absent from the product APK, with public concrete class ownership and public instance, nonnative, nonabstract, void/noarg, runtime-JUnit methods. Each selected method requires a positive nonboolean instruction-unit count.

## Read and parser boundaries

The reader reuses the accepted archive build reader's physical D:, ancestor/reparse, regular single-link and held-file checks. Limits are 128 MiB/file, 2 MiB/JSON, 256 MiB verified resident bytes, 512 MiB cumulative reads and 120 seconds/session. JSON rejects duplicate keys, invalid UTF8, nonfinite values including floating overflow, and mutable input buffers. XML rejects DTD/entity declarations. Files are cached only after their complete bytes match the pin; DEX is decoded from those exact bytes in memory. All tracked files are rehashed before return, with file/ancestor identity checks. This is bounded filesystem validation, not a transaction against a hostile administrator or arbitrary concurrent writers.

`Dex.definitions(*, with_code=False)` and `dex_classes(path, *, with_code=False)` retain the default four-field method tuples. Exact boolean opt-in appends an instruction-unit count. Nonzero code offsets must be aligned and the complete declared instruction array must fit. The [official AOSP DEX format](https://source.android.com/docs/core/runtime/dex-format#code-item) defines the 16-byte `code_item` header, 16-bit instruction units, and four-byte alignment. The extension keeps the prior accepted DEX versions; it does not add experimental version 041. It does not verify the entire instruction stream, control flow, map/checksum/try structures, ART loading or JUnit execution. Missing/empty code remains a decoder fact of zero; the attestor rejects it for selected methods.

## Qualification limits

The returned facts explicitly deny Android runtime execution, model material, feature acceptance, run authority, repeated native compilation, remote recheck and current tool-binary revalidation. A nonempty method body proves neither that an assertion exists nor that the method passed. Source/DEX/report consistency is an additional prerequisite, not the Android/SAF/offline/privacy gate. It must not be passed to an older run owner as a substitute profile or grant.

Tests combine independent in-memory full-count record graphs, independent tiny actual DEX/ZIP bytes, real D: file mutation/link/budget tests, and existing APK/archive/record regressions. No model, emulator, ledger change, new dependency or SDK installation is required. Genuine replay and exact verification evidence are recorded separately in [the packet report](DIAGNOSTIC_UI_BUILD_VERIFICATION_2026-11-02.md).
