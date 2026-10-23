# D09 native worker clean-path reproducibility

Refs #31 D09.03/.05, partial prerequisite. Claim
[6359578871](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6359578871).
Contributor: `/root/desktop_runtime_profile`, isolated `impl/d09-worker-repro` /
`source-worker-repro`, based on accepted main
`01fb9f83fd164809c2c1608655c1c432bd326458`. This packet owns only
`native/llama-worker/CMakeLists.txt`, new `test_reproducible.py` beside it, and
this document. No upstream vendor patch, build.ps1, runtime, profile, staging,
package pin, model, app, schema, Android or repository-settings change.

This qualifies the measured worker build comparison only. The existing approved
worker remains SHA256
`add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87`.
Neither that file nor its allowlist was replaced. A different candidate hash
requires coordinator review and fresh runtime/model/app qualification before
adoption. D09 completion, community support across compilers/SDKs, signed public
distribution, offline installation and release are not established here.

## Small production build change

The clean tracked upstream source still must be exactly
`620d2225cc436ab0b001e3200e590e3b286ef9ab`. Network/server/GPU/shared-library
options remain disabled. Compiler-cache use is now explicitly disabled too.
The upstream-supported `LLAMA_BUILD_NUMBER=1` and `LLAMA_BUILD_COMMIT=620d222`
inputs fix informational strings that otherwise depend on shallow/full Git
history depth; they do not replace the full commit check. Actual compiler and
target strings still come from upstream/CMake.

For MSVC Release, inherited compile options add `/Brepro` and
`/experimental:deterministic`, with C and C++ configure-time acceptance checks.
Six `/pathmap` entries map both native and forward-slash spellings of worker
source, upstream source and generated build directories to distinct fixed
`X:\locallore\worker`, `X:\locallore\llama`, `X:\locallore\build` roots.
They cover upstream translation units and generated unity includes as well as
worker code. Final executable links use `/Brepro /INCREMENTAL:NO`; Release
static archives use `/Brepro`. The existing optimization/CPU/backend/runtime
choices are retained. Debug configurations are not newly qualified.

MSVC19.34 also incorporates its original translation-unit argument into lambda
symbol identities, beyond `__FILE__` remapping. A generated CMake script compiles
only the worker's three fixed translation units (`main.cpp`,
`schema_order_test.cpp`, `worker_launch_test.cpp`) by basename from their source
directory. All inherited flags/includes remain in the invocation; only the
approved source argument and known `/Fo`/`/Fd` output forms are rebased. Outputs
must remain in the configured binary directory. The launcher verifies supplied
compiler bytes (including Ninja's 8.3 spelling), then executes only the literal
configured compiler after rechecking its hash. It rejects ambiguous/unknown
source/output forms and response files. It is build-time-only, not product IPC
or a general server. Vendor targets use their normal compiler rules.

Resolved compiler argv/cwd/source/exit records and the generated launcher hash
are retained. An immediate second build must be a Ninja no-op. Touching only
the copied `worker_launch.h` timestamp must rebuild `main.cpp.obj` and
`worker_launch_test.cpp.obj` with identical final worker bytes, proving the
launcher preserves this actual `/showIncludes` dependency path. Eight negative
launcher cases fail before overwriting those successful invocation records.

These MSVC options are measured with the exact toolset below, including the
experimental prerequisite. A successful flag acceptance check alone does not
prove source remapping or reproducibility: the separate probe executes C/C++
`__FILE__` expressions and an absolute forward-slash generated-header include,
then the actual worker comparison checks generated metadata, every compile
command, physical-path absence and exact PE bytes. No post-link timestamp,
header, path, section or binary normalization is permitted.

Primary source interfaces inspected: pinned upstream
[build-info.cmake](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/cmake/build-info.cmake),
[CMakeLists.txt](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/CMakeLists.txt),
and [build-info.cpp.in](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/common/build-info.cpp.in).
Microsoft documents [PDBALTPATH](https://learn.microsoft.com/en-us/cpp/build/reference/pdbaltpath-use-alternate-pdb-path)
for an alternate embedded PDB location; this packet does not introduce PDB/debug
information or that option into the existing Release profile.

## Reproduction command and trusted inputs

Use the already provisioned Windows x64 MSVC development environment. No tools,
source or weights are downloaded by this test. Supply an existing clean pinned
upstream checkout, installed CMake with its sibling Ninja, and a **new** output
directory outside both source inputs. Outputs contain local paths and stay
outside Git. The script refuses existing output directories and common ambient
compiler/link flag overrides; it is not a hermetic compiler/SDK sandbox.

Exact measured command, with the task-root alias expanded locally:

```powershell
$taskRoot = 'D:\CodexLocalLore\01a165d9-ff25-7500-a550-1099087d4e37'
$taskVs = 'C:\Program Files\Microsoft Visual Studio\2022\Community'
Import-Module "$taskVs\Common7\Tools\Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $taskVs -SkipAutomaticLocation -Arch amd64 -HostArch amd64
& "$taskRoot\d09-build-security\python-3.14.9\python.exe" `
  native/llama-worker/test_reproducible.py `
  --upstream "C:\Users\Avery\Documents\ChatGPT\The Hero's Journey\LocalLore-llama-spike\target\runtime-spike\llama.cpp" `
  --cmake 'C:\Users\Avery\AppData\Local\Android\Sdk\cmake\3.22.1\bin\cmake.exe' `
  --output "$taskRoot\worker-repro-clean-09"
```

The working directory is `source-worker-repro`; the final source revision is
recorded with the results below.
No object, archive, CMake cache or build directory was copied into either build.
The script makes two local source clones using `git clone --no-hardlinks
--no-checkout`, checks out the exact pin in each, rejects modified/incomplete
tracked sources, hashes the complete tracked source inventory and copies the
small fixed worker input inventory. The original checkout's tracked status is
checked and remains untouched. No Git worktree metadata is written there.

Independent source/build paths under the output root are `first` and
`b`, each containing its own `llama source`, `worker source`, `clean build`
and TEMP directory. Both build sequentially with Ninja Release, four jobs, and
explicit compile-command export. Native grammar, launch and hostile protocol
tests execute separately against each new output without loading a model.

Measured environment: Windows 11 Pro 10.0.26300 x64; Visual Studio developer shell
17.4.3; MSVC tools directory 14.34.31933, actual compiler 19.34.31937.0 / linker
14.34.31937.0; Windows SDK 10.0.19041.0; CMake
`3.22.1-g37088a8-dirty` from the existing Android SDK installation; Ninja 1.10.2;
official portable Python 3.14.9, PowerShell 7.6.5, preferred locale encoding
CP1252 (Python filesystem encoding UTF-8). OS version/build26300 is the actual
Win32_OperatingSystem/CIM value. The CMake version string describes that existing
tool build, not a modification made here. Local manifests record executable
SHA256s for compiler/linker/librarian/dumpbin/SDK rc+mt/Git/CMake/Ninja/Python,
SDK/include/library environment, `/Bv` compiler component versions, exact build
commands/flags, source inventories, generated build info and PE headers/imports.
Installed SDK/header/library contents and system runtime remain trusted host
inputs; this is not an independently provisioned second toolchain or license audit.

## Observed failures retained

- `worker-repro-probes-01`: `/pathmap` without its MSVC prerequisite emits D9007
  and is ignored. The actual `__FILE__` oracle rejects the result. The final
  driver also rejects D9007/unknown/ignored-option diagnostics explicitly.
- `worker-repro-probes-02`: adding `/experimental:deterministic` accepts the
  options, but forward-slash-only map prefixes do not match direct native-path
  source inputs. The actual mapping oracle rejects the result.
- `worker-repro-probes-03/04`: native-separator and then three-root C/C++/header
  probes pass from ASCII and space/Unicode locations. This was probe evidence,
  not a worker comparison.
- `worker-repro-clean-01`: the first clean worker compiles and passes native
  grammar13/launch3/protocol11. The excessively long second source-root name
  exceeds Git's Windows path limit in unused upstream UI files. Git reports
  errors despite exit0; the complete tracked-file inventory rejects the partial
  checkout. The final driver also checks tracked status. No global Git config,
  registry or OS long-path setting was changed; a shorter Unicode test root
  preserves independent-path coverage.
- `worker-repro-clean-02`: native worker tests pass, but the PE scan finds
  forward-slash physical upstream paths in llama.cpp unity-included source
  assertions. Native-only remapping was insufficient; both spellings are now
  mapped. This failure is retained, not relabeled reproducible.
- `worker-repro-clean-03`: the new absolute Unicode header probe initially lacks
  UTF-8 source decoding and fails C1083. The probe now uses `/utf-8`, matching
  the existing upstream unity-source compile mode. Production upstream code
  already supplies that option; no vendor patch was needed.
- `worker-repro-clean-04`: the exact compile-command guard rejects five map
  entries instead of six. The explicit Windows upstream path arrived with
  native separators, so CMake deduplicated its two identical entries. The final
  CMake change normalizes each input before constructing both spellings; the
  guard is retained rather than weakened.
- `worker-repro-clean-05`: the first final-policy PE passes all native checks,
  all135 compile-command checks and physical-path absence. Even the shortened
  `second Δ` root leaves one unused upstream UI file over Git's path limit;
  the tracked-status guard rejects the incomplete second checkout. The final
  next second root is simply `Δ`, shorter than `first`, preserving different
  lengths without changing any system setting.
- `worker-repro-clean-06`: both full source inventories are complete, but
  CMake3.22.1 invoking Ninja1.10.2 fails compiler ABI configuration because
  Ninja receives `?` for the Greek `Δ` build directory on this CP1252 host. This
  is a generator-stack limit despite passing direct-MSVC Greek probes. The
  coordinator explicitly approved measuring the existing tools with `é` next,
  and retaining full Greek-path builds as unsupported rather than changing
  system code pages/tools/settings or silently claiming general Unicode support.
  A separate own `worker-path-config-é` configure probe passes.
- `worker-repro-clean-07`: the full `é` source/build path configures, but CMake
  writes its generated unity includes using bytes incompatible with upstream's
  `/utf-8` source mode. MSVC rejects them with C4828/C1083. No second worker was
  produced. The coordinator's explicit fallback permits two independent
  ASCII/space clean builds plus direct-MSVC Greek probes, while retaining both
  full Unicode generator failures as unqualified. No unity-mode/vendor patch,
  new tools, system code-page change or silent Unicode support claim was used.
- `worker-repro-clean-08`: both complete workers pass13/3/11 native checks,
  source manifests match, all135 command/six-map checks pass and physical paths
  are absent. Actual PE comparison nevertheless fails: first SHA256
  `a5156224de91026d350ae430b456be4f1a688e154af9619390ea2b2681202bf5`,
  second `2178bac7915deb7409c6155716057d716a92847ea016ea5bb153d4ec10d85ccd`.
  Both are6,014,464 bytes;2,074 bytes differ. Object inspection isolates changed
  lambda symbol identities in worker `main.cpp` and `worker_launch_test.cpp`;
  upstream objects and the schema-test object match. Direct controlled lambda
  probes in `worker-lambda-probe-01/02/03` show that absolute input spelling
  remains significant despite map variants; compiling by relative basename
  from each source directory produces identical objects, including with
  absolute object/PDB outputs. No undocumented compiler flag was adopted.
  The coordinator then explicitly approved the fixed three-source launcher.
- `worker-launcher-control-01`: the first launcher control build rejects Ninja's
  trailing-directory `/Fd` form rather than silently dropping it. The narrowly
  recognized form now requires an existing directory inside the binary root;
  the repeated control target builds and its three launch assertions pass.
  Full clean comparison09 below uses that final implementation.

## Final result and limits

Final source: `4258b365a61ccba70cbcfb9ebe2cf356e7bcd055`.
`worker-repro-clean-09/comparison.json` reports
`passed_same_tools_two_clean_paths`, `actual_pe_bytes_equal=true`,
`models_loaded=false`, `staged=false`; command exit0. This compares actual raw
PE bytes, not normalized hashes. The manifest's `worker_source_dirty=true`
records this untracked report draft only; all nine compiled/test input files
were committed and their exact SHA256s checked before/after both builds.

| Measured check | `first` | `b` |
| --- | --- | --- |
| Tracked upstream input files | 3,795 ordinary files | 3,795 ordinary files |
| Source inventory SHA256 | `ca50b8d681d075f5a8cf5f54a1cb6b9e39648d8cdde1b1ca1120ad6286c367c4` | identical |
| Actual compiler commands | 135, each `/Brepro`, `/experimental:deterministic`, six maps | same |
| C/C++/absolute-header mapping oracles | ASCII and Greek/space direct probes pass | shared preflight probes |
| Ninja no-op and owned-header rebuild | pass; rebuilt worker bytes unchanged | pass; rebuilt worker bytes unchanged |
| Fixed launcher rejection cases | 8 rejected as expected | 8 rejected as expected |
| Actual native grammar assertions | 13 pass, including op-first Give | 13 pass |
| Actual native launch assertions | 3 pass | 3 pass |
| Actual native hostile protocol cases | 11 pass, no model | 11 pass, no model |
| Physical worker/upstream/build root absence in PE | pass for native/forward UTF-8/UTF-16 spellings | pass |
| Worker bytes | 6,014,464 | 6,014,464 |
| Worker SHA256 | `b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434` | identical |

Eight rejected cases: wrong compiler, unapproved source, escaped object, escaped
PDB, duplicate source, duplicate object, relative response file, unknown `/Fe`
output. Both copied worker directories retain exactly the nine original source
files with unchanged bytes; neither compiler writes into its source directory.

Candidate paths (local only):

```text
D:\CodexLocalLore\01a165d9-ff25-7500-a550-1099087d4e37\worker-repro-clean-09\first\clean build\locallore-llama-worker.exe
D:\CodexLocalLore\01a165d9-ff25-7500-a550-1099087d4e37\worker-repro-clean-09\b\clean build\locallore-llama-worker.exe
```

Evidence SHA256s, under `worker-repro-clean-09`:

| File | SHA256 |
| --- | --- |
| `comparison.json` | `15b059051c467363b1564988782db77c97b442e3f1fcd25227493f0186b019c4` |
| `first/manifest.json` | `42bb203d181f3fd71542237e3eadedd78d4f7613ce27f261d4db37decd02a4a8` |
| `b/manifest.json` | `2bd2b3cf34bca5c97cd1bd39e234fa2ff5fa88815eea8f5f8988e66d05c56e1b` |
| First generated launcher | `2dd243f11a71d5b5d544e46f2a805498be7a1f66e9eeb0b0e60ba7b759a38e36` |
| Second generated launcher | `7b722318a1fc7bdc1f16dd763bda31d8e7e19aa580185b137f5045fc8149c889` |
| Input `CMakeLists.txt` | `ad1fb1edd1c54e1c9c279850e704d06a4e5dfe097234daa3539d8347d527e7ba` |
| Input `test_reproducible.py` | `098e973f0254df03700f7c5341ccfc62f0490addebaec4aaa1ad1ce223ae609d` |

Generated launcher hashes differ because the scripts deliberately embed their
actual configured paths. Both invoke the same compiler bytes and preserve the
same inherited flags, with relative fixed source names and confined absolute
outputs; all three resolved invocations and their hashes are in each manifest.
Build info in both is number1, commit620d222. PE imports in both are KERNEL32,
ADVAPI32, MSVCP140, VCOMP140, VCRUNTIME140, VCRUNTIME140_1 and UCRT runtime,
math, heap, convert, stdio, locale, environment, string, time, utility DLLs.
These existing system/runtime dependencies are not bundled or newly qualified
as an offline redistributable by this comparison.

Selected exact tool identities (remaining SDK/tool hashes are in comparison):

| Tool | SHA256 |
| --- | --- |
| `cl.exe` | `36d32d60b9d26a3b5c7dcf763d4628d5cec2505059db1364c826776cbb37763d` |
| `link.exe` | `38f375b084e796c6be3ae724641136897770fbc4858e578724f7956c41c48fce` |
| `lib.exe` | `54e8c0b868ad2509e9bd4b7845c67380a4e074af76c286ecd049a3679ccfa3b9` |
| CMake | `41d609bae2a65a9a8e2060bb222d6e031d33c0546054d354137eb490933cb8ac` |
| Ninja | `d5d6705439aac3162ff6cfb1509246cdbbecaf9d10d7c846713af2c07d8d7ee8` |
| Python | `e67f33a86fc64a07798a136af126f38a8e0d3c0a25787c635fb1678c2b66b12a` |

The original qualified worker was rehashed after comparison and remains
`add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87`;
the original upstream tracked status remains clean. No candidate adoption was
performed. Local artifacts remain outside Git; no worker, model, PDB, raw save
or private story is published by this packet. Existing resource/package pins
remain unchanged.

The native model-free checks test the actual pinned grammar converter and worker
process protocol/lifecycle launch helper. They do not exercise Rust/native IPC,
WebView rendering, model loading, real free-text generation, cancellation during
inference, offline traffic observation or a final developer package. All changed
worker identities must pass those separate owning gates before adoption. Different
compiler/SDK/library contents, architectures, CPU options and operating systems
remain unqualified. Full D09 stays unchecked.

Next runnable task: independent review of these three changed paths and retained
manifests, then coordinator-owned fixed-package hash adoption plus actual runtime/
model/app requalification. No general Unicode-build acceptance follows from the
successful direct compiler probes or the two ASCII/space builds.
