# Source-bound scene narration: Core and Store qualification

Refs #9 M05.03 / #25 D04.04, supporting slice only. Generated prose quality
retains the owner's **needs improvement** assessment. No model ran here.

## Source and dependency

Executed source is clean, unchanged `79a50caa076cb308de26761566df45d93de2698c`.
Its stack starts at `fd27d7a6`: frozen open PR225 `4de180dd` plus accepted
desktop main `c6c21f28`. The unchanged reconciled baseline passes468 Core tests,
0 failures/4 existing ignored cases in115.683s before implementation.

At final refresh PR225 is still draft/open at `953b06fa`. Its entire delta from
4de is one Android qualification document; no code, tests or locks change.
The refreshed owned stack base is `f9af4910da96fbb1bdbc7759870ba88ddf696452`;
integration `dd07d69f` differs from executed79a only by that upstream document.
The focused PR targets this owned integration base, preserving the dependency
author's branch/resources. Dependency acceptance remains required before main
integration; this report does not accept PR225 or its Android gates.

## Implemented boundary

Two new immutable constructions use the accepted opaque preparation API:

| Construction | Prompt version | Policy |
| --- | --- | --- |
| Memory scene | `locallore-play-v2.9-scene-frame-v1` | `grounded-prose-v2.4-scene-frame-v1` |
| Literal-v1 scene | `locallore-play-v2.10-literal-director-v1-scene-frame-v1` | same |

The consumed native bound capability owns the actual full history basis,
approved turn, sanitized evidence, candidate Player location frame, selected
recipe and exact typed seed presentation. Binding and commit regenerate and
compare the source; equal scope/head/projection cannot substitute for history.
The engine-free renderer embeds only the closed six-field frame, accepted
sanitized evidence and existing typed presentation semantics. The actual shared
Play pipeline forwards that renderer's prompt/schema to the recording provider.

The optional omitted `PlayRecord.scene` stores only version1/frame SHA-256.
It is recomputed provenance, not a supplied frame or authority. Core history
dispatch reconstructs each recipe at its actual prefix. Shared Store/reopen and
archive validation use that same engine; no schema, SQL writer, ledger,
provider, dependency or second memory implementation is added.

Old2.1–2.8 mappings/defaults and bytes remain unchanged. Every old validator
family refuses `scene:Some`. New exact-key retries return the original receipt
before cancellation, profile/construction/coverage/head checks and make no
provider call. Memory retains existing corrected-Domain2 observations/raw
unsupported coverage; literal remains Domain1-only. Typed `initial_world` seeds
explicitly refuse before the first provider role. No Fact scraping manufactures
authored-world location labels.

New generated prose alone receives the contract's finite English first-person
token and listed non-Move travel checks. Ordinary event/speaker/observation and
ownership validation still runs. Exact mechanical fallback remains subject to
seed phrase exclusions; excluded fallback refuses. These checks do not establish
semantic entailment, feelings detection, scene consistency or enjoyable prose.

## Independent oracles, actual failures and fix

Core first freeze5722c9b3 contains14 cases;29f0b071 adds old-validator injection
as case15. Storage first freeze18c9d6a2 contains three functions, including a
four-combination ordinary/presented × memory/literal round trip and44 distinct
recomputed-checksum archive forgeries. Root integrates the first freezes before
production. Formatting preserves the assertions.

Production1ac7a1fe first passes all15 Core cases. First Storage execution really
runs three functions: one passes, two stop on `ClarificationRequired` before
their intended assertions. Both positive controls used unsupported `I wait.`.
The second independent freezea69cd267 changes exactly those two inputs to the
already admitted explicit one-tide form and adds a positive/negative existing
grammar calibration. It preserves all44 forgery and round-trip assertions;
neither parser nor acceptance rules are broadened. These setup failures remain
failed, not behavioral evidence of an archive defect.

Independent review then finds cancellation inside the passive post-validation
trace callback can be masked by an excluded fallback. Additive freeze20f3137a
uses the actual TraceRing measurement to cancel after rejected narration
validation. At8d5334ed, whose production equals1ac, it executes and fails for
both arms: actual `Narration`, required `Cancelled`; canonical source remains
unchanged. An earlier misplaced Cargo `--exact` argument only produced a usage
refusal; that separate record is not behavioral RED.

Fix79a polls immediately after the callback and before fallback/exclusion work.
Old paths get no new poll and no post-install poll is introduced. Independent
source review confirms that boundary and the unchanged frozen assertions.
All16 Core cases and corrected four Storage functions then pass. They cover
actual forwarded renderer bytes, real frame/self-profile comparisons, corrected
observation isolation, full-basis/presentation/tuple/provenance tampering,
cancellation, zero-call retries, old encodings, actual Store reopen and full
archive/import/reopen/reexport with unrelated destination preservation.

## Reproducible checks

Use installed Rust1.93.1/Node24.22.1, the existing pinned dependencies and the
provisioned isolated exact-lock cache. From the repository root:

```powershell
$env:CARGO_HOME = '<existing isolated locked-package cache>'
$env:CARGO_NET_OFFLINE = 'true'
$env:CARGO_BUILD_JOBS = '1'
$env:CARGO_INCREMENTAL = '0'
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:LIBSQLITE3_FLAGS = ''
$env:TEMP = '<existing owned task temporary directory>'
$env:TMP = $env:TEMP
cargo test --workspace --all-features --locked --offline --jobs 1 --target-dir $ownedTarget -- --test-threads=1
cargo clippy --workspace --all-targets --all-features --locked --offline --jobs 1 --target-dir $ownedTarget -- -D warnings
& $taskNode apps/desktop/verify-frontend.mjs
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --no-default-features --locked --offline --jobs 1 --target-dir $ownedTarget
cargo fmt --all -- --check
cargo tree -p locallore-android --target aarch64-linux-android --locked --offline
```

All commands below run on clean unchanged79a, with one heavy process at a time.

| Actual check | Result / command duration |
| --- | --- |
| Focused Core scene tests | 16 passed/0 failed/ignored;18.589s |
| Focused Storage scene tests | 4 passed/0 failed/ignored;19.606s |
| Whole workspace, serial test runner | 1,259 passed/0 failed/20 ignored,142 result summaries;1,681.330s |
| Strict whole-workspace all-target/all-feature Clippy | PASS46.056s |
| Full frontend verifier | PASS18.025s; normal bundle, strict TypeScript/current schemas and all wired suites |
| Normal native build | PASS20.312s; unlaunched |
| Rust formatting | PASS2.450s |
| Android aarch64 dependency graph | PASS0.460s;0 Tauri/Wry/WebView2/local-runtime/llama hits |

The20 ignored cases are four historical/original-source probes, eight explicit real
model/asset qualifiers, three Windows symlink-privilege cases, two child-only
entry points exercised by parent tests, a special96-page SQLite qualifier, an
expensive explicit16MiB boundary and one superseded Open contract. No ignored
case is represented as newly executed.

### Parallel native qualification remains separate

The initial default-parallel whole-workspace run exits101 in529.380s. Its native
binary reports236 passed/10 failed/9 ignored in301.18s. All ten failures are
existing selected-service inventory `fs::read` Windows33 errors, before intended
assertions. The exact failed pathname was not retained. Source review finds a
shared OnceLock source and retained exclusive Reader locks; that explains a
possible fixture conflict, not a measured failed-file identity. The first failed
case passes isolated on unchanged79a:1 passed/254 filtered,8.57s test time,
33.294s command. No process was stopped.

The serial result above matches historical qualification commands, but committed
desktop CI runs parallel. A focused private-fixture ownership fix is separately
in progress. This Core report does not claim the parallel risk is resolved or
substitute serial success for CI. Original byte inventories, locks, race checks
and budgets must be retained in that fix.

## Versions, hashes and unavailable claims

Windows NT10.0.26300 x64; rustc1.93.1 (`01f6ddf75`), cargo1.93.1 (`083ac5135`),
Node24.22.1; TypeScript7.0.2/React19.3.1/esbuild0.28.2;
Tauri2.12.5/Wry0.57/Tao0.37.1. This cohort has no WebView rendering or new
runtime user-agent measurement. Python3.14.7 reads private logs/hash records.

| Source item | SHA-256 at79a |
| --- | --- |
| Scene recipe module | `0029da5f0fefde4ba78aa194fb3a77510de1c5de763b3c625ed07c5675bc48a9` |
| Engine-free renderer | `30852991c7c33adb4278098347a9d179486d07adc52f838b20655684180fab9a` |
| Opaque preparation/binding | `58a43ce6e82ca1c2b929d9b44479adffabd5acc27913be9838448d639cca8762` |
| Core oracle file | `f12e6893a8c92244699563478830994d513965d664f0e19e98b8acde80e8a758` |
| Storage oracle file | `ba3d712f69220341916573a3b36c191410505856f76484b4836b1555f57f59ae` |
| Unchanged Cargo.lock | `4fb7c498ca0ecc62c4ea1f65c63b370ab4336eb75133d08b3a71f5664156cf93` |

Private logs retain the `d04-scene-recipe-*` names, original failures and
source/cleanliness/timing records; artifacts stay local and gitignored.
There is no new Host/JSON/UI selection, exact source-bound capture gate,
evaluation protocol, model cohort, native IPC/WebView journey or generated
render image in this Core slice. Normal builds were not launched. Android
results are Rust host compatibility and dependency exclusion, not JVM/device,
ABI or physical-phone qualification. Authored-world scene support, full
accessibility/offline/package qualification, new model samples and new human
assessment remain required. Full M05/D04/D07 checklists are unchanged.
