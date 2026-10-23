# D09 normal application clean-path reproducibility prerequisite

Refs #31 D09.03/.05/.07 partial, with D09.01/.02 build-target/license applicability
only. Claims [6369118310](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6369118310),
[6369306097](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6369306097)
and approved packager extension
[6369724950](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6369724950).
Status: **in review; application byte reproducibility failed in both cohorts**.
Four normal developer folders/ZIPs built and verified; that does not establish
reproducibility or application execution. D09 remains unchecked.

## Source and owned changes

Isolated `impl/d09-app-repro` / `source-app-repro` starts at accepted
`c496eb87147843958653b194aed0ca934fb03923`, including the pre-spawn worker guard.
Only new `scripts/desktop-reproducible.py`, `scripts/desktop-reproducible-tests.py`,
these evidence documents, and **two lines** in `scripts/desktop-package.py` change.
No product Rust, frontend/controller, build.rs, runtime, worker, profile, model,
Cargo manifest/lock, Android, workflow or settings changed.

The wrapper freezes one exact source SHA in two independent detached worktrees,
with different ASCII/space path lengths, separate initially empty native targets,
temporary directories, copied npm dependencies and normal dist directories. It
does not copy any previous target/object/archive. The existing installed registry
source cache and tools remain shared trusted inputs. It runs the normal packager
without `dev-harness`, then independently verifies each archive. Normal frontend
TypeScript/schema/controller checks and development-hook exclusion run in both
paths. No app, worker or model is launched.

The checker records all tracked source bytes, source/lock identity, supplied
installed npm file hashes/lock fields/package versions, invoked and resolved tools,
selected Rust compiler binaries, tool versions, relevant environment/config hashes,
actual commands, logs, PE sections/imports and selected Windows notices. It checks
sources/dependencies/tools again after work. Supplied dependency hashes bind bytes;
they do not authenticate the registry. This is not a hermetic audit of all cached
Rust sources, system headers/libraries or tool installations.

Raw executable, frontend, folder inventory, **whole ZIP bytes**, ordered ZipInfo
metadata and every member hash participate, including `build-manifest.json`.
There is no byte normalization, ignored packaged field or caller-selected expected
worker hash. External evidence contains paths/timings that are intentionally
noncomparable; those files are not package members. Byte mismatch returns exit 1
and retains outputs. The tool never deletes worktrees, targets, partial outputs
or prior evidence. Reparse inputs/output ancestors, overlaps, occupied outputs,
unsupported Unicode cohort roots and ambient compiler overrides refuse.

## Actual commands and environment

Windows 11 Pro 10.0.26300 x64; Rust/Cargo 1.93.1, LLVM 21.1.8;
Node 24.22.1/npm 11.19.1; Python 3.14.9; MSVC compiler 19.34.31937,
linker 14.34.31937; existing SDK tool paths 10.0.19041.0. No installation,
download, system-codepage/environment-setting change or new dependency occurred.
Only child-process build environment was selected. Build targets/temp/artifacts
are task-owned on D:. Tools' exact hashes and compiler driver hashes are retained
in the manifests and sanitized JSON. Rustup proxies resolve to the existing
`rustup.exe`; selected compiler binaries are hashed separately.

Use an existing provisioned x64 MSVC/SDK shell and set task-local paths:

```powershell
$env:TEMP = "$task/app-repro-artifacts/temp"; $env:TMP = $env:TEMP
& $python -X utf8 scripts/desktop-reproducible-tests.py
& $python -X utf8 scripts/desktop-package-tests.py
& $python -X utf8 scripts/desktop-reproducible.py --source-commit $frozenSource `
  --node $node --npm-cli $npmCli --dependencies $installedNodeModules `
  --worker $approvedB5Worker --output "$task/app-repro-clean-02"
```

The measured host reused the existing task `d09-build-security` Node/Python/npm
tree and ordinary `node_modules` child. It reused the process-local MSVC/SDK
INCLUDE/LIB/LIBPATH/tool paths recorded by the prior worker comparison. No package
manager installation command runs; copied npm trees have **3538 ordinary files**,
inventory SHA256 `57cad8333de434d9d9c1398ed5041737746a25284b303d511eb36aad6eb03703`.
Each normal build executes the existing packager command:

```text
python -X utf8 <source>/scripts/desktop-package.py build --node <pinned node>
 --npm-cli <pinned npm-cli> --target-dir <independent empty target>
 --worker <approved b5 worker> --output <new normal developer folder>
```

Actual initial checker source `842bb71` stopped before output creation because
ordinary-file validation rejected normal Cargo/rustc rustup proxy symlinks. Fixed
`c170a03` records only those known sibling-rustup aliases and their resolved bytes;
source/dependency/output reparse refusal remains. That preflight failure log is
retained. No compiler-help hang was demonstrated and no running process was killed.

Final synthetic tests: **20 passed, zero failed/skipped** on code/test source
`9b623541b02a389227d1867508295012c6197ca8`; existing package tests **12 passed**.
They use synthetic PE/ZIP fixtures, not a native application. Tests detect a
single PE byte, frontend changes/extras, manifest content, ZIP timestamps/order/
archive comments, invalid PE ranges, budgets, source drift, missing/mismatched
installed packages, occupied/overlapping/Unicode/relative/reparse paths, known
rustup indirection, worker rejection before subprocess/output, no-overwrite,
internal mapping with spaces and ambient flag refusal. Formatting/diff checks pass.

## Raw application results: retained failures

| Cohort | Application source | External checker | Source files | Result |
| --- | --- | --- | ---: | --- |
| clean01 | accepted `c496eb87147843958653b194aed0ca934fb03923` | `c170a03005d17a2bf271cf78f1cbd730b65de295` | 776 | exit 1, failed_bytes_differ |
| clean02 | `6e576f473a4796c329468a6abf3eeaaf4323a89b` | same `6e576f4` | 778 | exit 1, failed_bytes_differ |

Both source trees within each pair were byte-identical and clean before/after;
supplied dependency bytes and recorded tool identities matched. All four normal
frontend builds/checks and native builds succeeded. All four closed **446-member**
packages verified, with no weights/saves/PDBs/development harness selected. All
four normal frontend files match between paths and across both cohorts.

| Cohort/path | EXE bytes | EXE SHA256 |
| --- | ---: | --- |
| clean01 first | 23624704 | `3bb0a821f621f2c4ca0b7be650bbef1a3f052b0faa5d4d6930f2e5462d2c371d` |
| clean01 second | 23581184 | `686e9800dffd738fd9fc790b773a61ca203420fbe27bf7d3286917bd0288bddd` |
| clean02 first | 23616512 | `30be7cde451ab6d5515e27781021c54772dcf3122d4dda71d048a21bad6fc308` |
| clean02 second | 23578624 | `2e863f26a88061c64ea9aba0e8574443c32863d154e197ac18eca59d0955e72d` |

| Cohort/path | ZIP bytes | ZIP SHA256 |
| --- | ---: | --- |
| clean01 first | 10686138 | `b23c9395f8f242cccdc64c5d261151db3ddacc1ad153bbc18d7eaa1a64bde9cf` |
| clean01 second | 10671588 | `ec1c1f57c1bd3f18341db52829dc14e4185bd52eb8245fe4a03181e29b7986c2` |
| clean02 first | 10686423 | `3f13d9a22e64866b40c9e6e8fae05efa3867461b9fd5e5bc56088aea1f4e545b` |
| clean02 second | 10672739 | `f9c273fa45dcea5bc3e0bbcb7c544c17518bddcd0b0651b45a7044a1052769ad` |

Every comparison first differs at PE offset 256, with differences across code/data
sections; this is not merely a wall-clock timestamp. Only executable and manifest
**payloads** differ. The manifest differs only in its executable inventory. ZIP
header offsets then differ for 444 later members; this must not be misreported as
444 changed license texts. All notice/profile/worker/README payloads match.

The clean01 executables each contain 35 absolute Rust source locations rooted in
their own checkout. The approved two-line packager change sets internally derived
`CARGO_ENCODED_RUSTFLAGS=--remap-path-prefix=<ROOT>=/locallore-source` **after**
rejecting ambient Rust overrides, preserving spaces as one argument. It applies
to all Rust compilations; the existing final-link `/Brepro` remains. The manifest
records only the stable policy, not an actual checkout path. clean02 contains
zero absolute checkout roots and 35 virtual prefixes per executable, but still
fails the raw-byte gate. Path mapping is useful and **insufficient**.

Final checker `9b62354` fixes evidence-only Windows environment key casing:
`os.environ` uppercases keys, so the earlier copied-dict lookup left the two mixed
case selector fields empty. The historical manifests still contain the actual
compiler/SDK paths, executable hashes, banners and INCLUDE/LIB/LIBPATH. They are
not rewritten. The final helper's selector regression passes; no application
cohort was rerun for this metadata-reader-only correction. No equality or complete
SDK-content qualification is inferred from missing selector fields.

## Bounded compiler diagnostics and next workspace proposal

Sixteen tiny fixed Rust fixture builds used the same installed compiler, no external
dependencies and `--locked --offline`; **none of their executables ran**. Each case
uses two different source paths and independent empty targets, with/without the
same source-remap flag and final `/Brepro`:

| Fixture | Default bytes equal | Remapped bytes equal |
| --- | --- | --- |
| Standalone app, sibling path dependency returning `file!()` | false | true |
| Same layout, also retaining `TypeId::of::<LeafType>()` | false | false |
| TypeId dependency nested beneath app workspace | true | true |
| Common parent workspace with app member and excluded sibling dependency retaining its own workspace | true | true |

The remapped first fixture matches SHA256
`f652329fc56befd38213851eaeeabdb65704d4cdc47e6a38b73da1ec06f7ec33`.
The parent-workspace fixture matches
`61663d2746f0a2fba7dca992f645b76824b9fdb2b054acbc662a2fccd9333117`
in all four builds. TypeId in the outside-workspace fixture still differs despite
zero absolute source strings. Cargo's different cache fingerprints alone are not
proof that output must differ: the first remapped fixture demonstrates that limit.

Reproduction fixture source has package names `repro-fixture`/`repro-leaf`, version
0.1.0, edition 2021, app dependency `repro-leaf={path="../leaf"}` and app `[workspace]`.
The leaf source is:

```rust
#[inline(never)] pub fn value() -> u64 { 42 }
pub fn origin() -> &'static str { file!() }
pub struct Identified;
pub fn id() -> std::any::TypeId { std::any::TypeId::of::<Identified>() }
```

The app prints value/origin/id; omit id/type declarations for the first fixture.
Move the leaf to `app/leaf` and use `path="leaf"` for the third. For the fourth,
remove app `[workspace]`, retain leaf `[workspace]`, and put this manifest above
both with the lockfile there:

```toml
[workspace]
members = ["app"]
exclude = ["leaf"]
resolver = "2"
```

For exact fixture generation, the measured Python `Path.write_text` inputs were
the following strings (UTF-8; native text newlines):

```python
app_manifest = '[package]\nname="repro-fixture"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nrepro-leaf={path="../leaf"}\n[workspace]\n'
leaf_manifest = '[package]\nname="repro-leaf"\nversion="0.1.0"\nedition="2021"\n'
main = 'fn main(){println!("{} {} {:?}",repro_leaf::value(),repro_leaf::origin(),repro_leaf::id());}\n'
leaf = '#[inline(never)] pub fn value()->u64{42}\npub fn origin()-> &\'static str{file!()}\npub struct Identified; pub fn id()->std::any::TypeId{std::any::TypeId::of::<Identified>()}\n'
lock = 'version = 4\n[[package]]\nname = "repro-fixture"\nversion = "0.1.0"\ndependencies = ["repro-leaf"]\n[[package]]\nname = "repro-leaf"\nversion = "0.1.0"\n'
```

First fixture main uses `println!("{} {}",repro_leaf::value(),repro_leaf::origin())`
and the leaf string ends after `origin`. Third uses `path="leaf"` and that nested
location. Fourth removes the app's final `[workspace]\n`, appends `[workspace]\n`
to the leaf manifest, puts the virtual parent manifest above them, and writes the
same lock at that parent. Use `first source` and `second much longer source` as
the two new parent directory names, with separate `target control`/`target remap`
directories. Clear ambient `RUSTFLAGS`/`CARGO_ENCODED_RUSTFLAGS` for control.

Each fixed compile command is `cargo +1.93.1 rustc --manifest-path <app/Cargo.toml>
--locked --offline --target-dir <new target> -vv -- -C link-arg=/Brepro`; remapped
mode sets the single encoded flag before invoking Cargo. Complete generated source,
locked fixtures, argv, actual compiler commands and raw outputs remain local in
`app-repro-artifacts/pathdep-probe-01` through `-04`, with result hashes in the
sanitized JSON. This matrix diagnoses an upstream workspace-path contribution;
it is not application success or permission to rewrite compiler metadata.

Official [rustc path mapping](https://doc.rust-lang.org/rustc/command-line-arguments.html#--remap-path-prefix-remap-source-paths-in-output)
and [Cargo encoded flags](https://doc.rust-lang.org/cargo/reference/environment-variables.html)
support the tested stable flag. In the actual pinned Cargo source,
[compilation metadata](https://github.com/rust-lang/cargo/blob/083ac5135f967fd9dc906ab057a2315861c7a80d/src/cargo/core/compiler/build_runner/compilation_files.rs#L645)
includes package source identity relative to the primary workspace.
[SourceId hashing](https://github.com/rust-lang/cargo/blob/083ac5135f967fd9dc906ab057a2315861c7a80d/src/cargo/core/source_id.rs#L515)
strips only a matching workspace prefix, otherwise retaining the absolute URL.
[Rust 1.93.1 metadata parsing](https://github.com/rust-lang/rust/blob/1.93.1/compiler/rustc_session/src/options.rs#L972)
appends metadata strings; an extra flag cannot simply replace Cargo's value.

The desktop primary workspace is currently `apps/desktop/src-tauri`, with five
local dependencies above it in `crates/`. Smallest proposed coordinator-owned
follow-up, **not implemented here**:

1. Add desktop as a root workspace member. Keep the four current portable packages
   as explicit default-members. Remove the desktop exclusion; explicitly exclude
   `crates/locallore-local-runtime` and `crates/locallore-eval` so their existing
   standalone manifests/locks remain authoritative for their own commands.
2. Remove only the empty desktop `[workspace]`. The desktop build then uses the
   repository workspace root, above every local dependency. The fourth fixture
   demonstrates why even excluded standalone dependencies get relative identities
   in that primary build. Runtime/eval manifests need no change for this app gate.
3. Resolve the root lock offline from the existing root/desktop lock union and
   compare every selected name/version/source/checksum; no new versions/downloads.
   Retire the desktop lock as a no-longer-consulted authority. Reconcile current
   accepted D07 optional dependency edges before freezing the integration source.
4. Portable `scripts/check.py` explicitly uses `--workspace`: add desktop exclusion
   to its test/Clippy package selection, preserving Linux/Android's existing scope.
   Default-members alone do not constrain `--workspace`. Update selection tests
   and affected workspace/build docs; preserve explicit runtime/eval/desktop checks.
5. Verify metadata workspace root/member/default-member/feature/target selection,
   root host suites, native default/dev/runtime/eval tests, frontend, Android
   compatibility and lock policy. Then rerun this exact two-clean-path normal
   package checker on that newly frozen source. No success is promised in advance.

The coordinator owns this engineering follow-up after claims are reconciled.
No hand-written crate hash, metadata override, wrapper, generated manifest overlay,
global drive alias, nightly flag, toolchain upgrade or byte patch is used here.

## Target/license limits and evidence retention

Fresh read-only Dependabot lookup reports open alert 1, locked glib 0.18.5,
[GHSA-wrw7-89jp-8q8g](https://github.com/advisories/GHSA-wrw7-89jp-8q8g).
Both actual Windows selected graphs have 256 packages and no glib. That establishes
target applicability only; it is not remediation or dismissal, and Linux remains
unqualified. No dependency/alert/repository-setting change occurred.

Both packages keep `license_audit_complete=false`. Missing collected upstream text
remains for alloc-stdlib 0.3.0, selectors 0.38.0 and webview2-com 0.39.1/
macros 0.8.1/sys 0.39.1. Native/embedded/MPL obligations remain a distribution gate.
Native imports were statically inspected, not exercised. Installed WebView2,
Windows/UCRT and the worker's documented Visual C++/OpenMP runtime prerequisites
remain explicit; no DLL bootstrapper or installer qualification is added.

Worker bytes remain approved b5 SHA256
`b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`;
only that executable and public profile metadata were read/copied. **No model
weights were read, copied or loaded.** Prior worker two-path reproducibility and
model/native-WebView qualifications retain their original source attribution.
Neither was repeated by this packet.

Raw comparison/manifests/build logs/folders/ZIPs and failed preflight/probe evidence
remain task-local outside Git. Sanitized hashes/counts/outcomes are adjacent to
this document. Full Unicode clean builds, app launch, native IPC/WebView render,
offline observation/installation, DLL absence behavior, retention/update/uninstall,
Android/device and quality checks were **not run** here. No CUA, desktop input,
activation or screenshot, model call, protected resource change, Actions run,
release, merge or repository setting change occurred.

The next runnable task is the coordinator's minimal workspace/lock/portable-check
integration, followed by the unchanged raw-byte gate. This is a concrete engineering
dependency, not an external blocker or a waived D09 requirement.
