# V2 receipt and historical evidence qualification

Refs #26 D05.03/.06/.07 and #28 D06.03/.07, supporting slices only.
Base: accepted `23e418791e8c0424064a38e319b0db717942755d` (PR227).
Executed final application source: clean, unchanged
`92c5c2ba84c1e44e07bfeebed266b4b3671893fb`.
No full milestone, prose quality, accessibility or release acceptance follows.

## Behavior and authority

The actual Domain2 Play receipt now offers **Inspect accepted turn changes**.
It uses the existing Player Query2 at that receipt's completed historical end,
with today's expected head. A readable derived comparison shows before/after
revisions, typed values, explicit absence and each side's actual source links.
Prior field provenance is explicitly not asserted to have caused a later removal.
The pinned header keeps the actual displayed query, selected head, inspected
revision and privacy visible while scrolling. Source navigation updates the
query controls to the checked result rather than leaving old control values.

`traceReceipt` accepts only the exact current receipt object, Player Play,
coherent snapshot/session/scope/head/player, and existing checked contiguous
receipt events ending at a positive completed revision no later than the head.
The panel captures context/receipt identities before dispatch and after await.
Pending, result and final-busy synchronous notifications can retire a read;
retired reads neither dispatch nor return a usable bound page. Bound source
navigation requires actual membership in typed provenance/event/message/change
slots, comparing original scope and sequence. It never searches arbitrary field
text or JSON for source-shaped values. Existing unbound source compatibility stays.

Rust still owns historical boundaries, observer filtering, grants, canonical
state and provenance. No new Host operation, schema, storage format, provider,
permission or canonical writer was introduced. Shared crates and Cargo.lock
are byte-unchanged from the accepted base. Reading evidence cannot grant a
character knowledge or change which context generation may access.

## Frozen headless evidence and retained failures

The independently authored contract/checker preceded implementation. Original
75fd execution had 7 passes/52 failures: 11 existing-API behavioral failures,
33 absent new interfaces and 8 React SSR setup failures. Missing APIs and setup
failures are not behavioral RED. A narrowly scoped real-React server-snapshot
adapter corrected client-only panel SSR setup; all original assertions remained.
Calibrated 8a613 execution had 8 passes/52 failures: 11 existing-API behavioral
failures, 41 absent interfaces and zero SSR setup failures.

At edf6883f the actual controller/panel checker passes all **60** cases.
Formatting and verifier registration at1553 preserve the oracles; subsequent
full frontend suites, including final92c5, pass them. The formatted checker SHA
is `b356d546dfaee2a760d2e038fbef5b3da682a24a8726eb8e24664d51205ce739`.
These use real controller logic, real React SSR/captured actual JSX handlers
and a synthetic Gateway. They do not establish native permission or mounted
React post-await behavior. Higher-head retained receipts, old rendered callbacks,
reentrant retirement, malformed receipts and hostile inert text are headless
coverage; no higher-head native fixture turn was added.

The first native-harness frontend check624c fails compilation because a test
local name shadows an existing author preview. Renaming that local at7223 fixes
the compile failure without changing assertions. A later supplemental DOM
condition at2b532 initially returns `boolean | undefined`; explicit Boolean
conditions at92c5 correct the test type. These compilation failures are retained
locally and are not behavioral failures or successful native runs.

## Actual mounted native journey

From `apps/desktop`, use the pinned existing Node and provisioned cache:

```powershell
$env:CARGO_HOME = '<existing isolated locked-package cache>'
$env:CARGO_NET_OFFLINE = 'true'
$env:CARGO_BUILD_JOBS = '1'
$env:CARGO_INCREMENTAL = '0'
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:LIBSQLITE3_FLAGS = ''
$env:TEMP = '<existing owned temporary directory>'
$env:TMP = $env:TEMP
$env:LOCALLORE_M07_MEMORY_ARTIFACT_ROOT = '<existing owned artifact directory>'
$env:LOCALLORE_M07_MEMORY_TARGET_DIR = '<existing owned native target>'
& $taskNode author-harness.mjs
```

The fixed launcher builds a development-only bundle/executable, creates a new
synthetic workspace, runs initial and actual process-restart phases, freezes
source/product hashes, bounds output/errors/deadlines and refuses source changes.
There is no arbitrary launcher, remote debugging service or renderer-selected
file/shell endpoint. Hidden, unfocused WebView2 captures its own rendered surface
through CapturePreview. No desktop screenshot, activation or OS input is used.

The actual mounted receipt button and source buttons activate through the app's
own DOM, exercising the same React handlers, V2 controller, native IPC, shared
engine, Store and SQLite used by the UI. The fixed author journey preserves its
original consent/preview/cancel/unknown-ack/recovery/observer/restart assertions.
New checks cover the accepted gift after a deliberately rejected duplicate,
historical potion before2/after3, prior seed profiles at0, inherited main event1
while remaining in the selected child at3, mounted local controls, read-only
canonical/snapshot/history/receipt invariance, retained receipt after cancelled
Wait and old-context refusal before native dispatch. A bridge attempt count
alone is never treated as Rust acceptance. No detached DOM callback proof is
claimed; old rendered callback oracles remain headless.

First native cohort7223 passes157 distinct assertions and produces20 images.
Its old summary/terminal hardcodes17; the verified fixed-label inventory contains
18 initial and2 restart PNGs. That report remains unchanged. Individual image
review found the seed-source inspected revision scrolled away. The final source
adds the pinned context and actual-source control synchronization, and derives
the capture count from the fixed label allocation.

Final actual cohort92c5:

- Private artifact leaf `author-native-5a93fd13-0558-4d20-a71b-463f16b33786`.
- **157 distinct assertions**,171 initial/19 restart cumulative labels,
  **20 captures**. All20 final images and all20 earlier images individually viewed.
- Initial native process5.860s; restart0.907s. Build18.319s; complete launcher27.462s.
  All commands exit0, no timeout, overflow or truncated output.
- Initial errors exactly intentional `Inventory`, `Cancelled`, `Cancelled`;
  restart errors empty. No blanket transport/error allowance was added.
- Potion comparison and per-side prior source are legible. Seed screenshot
  visibly says selectedhead3/inspected0. Original event scope/sequence remains
  distinct from selected child/head. Non-target form sections extend outside
  the viewport; this is not whole-form or accessibility qualification.
- Reopen preserves child head3 and recorded history, but the actual thin
  snapshot does not reconstruct a controller receipt. The harness checks that
  no receipt link is fabricated and records it unavailable. Historical receipt
  browsing after cold reopen remains a separate missing UI capability.

Hashes of the final private products/evidence:

| Item | SHA-256 |
| --- | --- |
| Development GUI executable | `ba5bfca08092bf5a945468091fe115628d8f98fc648f28a6777e4cbdc24a15c7` |
| Development frontend | `94b06671bd354e446efeec5434894cadc86b360cb4cab72be648a71ab92ae957` |
| Fixed launcher | `4de23e72b5162954445a0f52e68795a4520b612b51ab7cf680c8b1d685be1dfb` |
| Native summary | `3be2a199a44afaaf06343d7fadcb6516a38f35908a969e821f9f4597371eca6b` |
| Root render review with individual image hashes | `9ff81f5722f645f5be323c6ccca35f6e45421d125704af3a61f032f0a92d39a2` |

## Other exact checks and limits

At clean unchanged92c5, with locked/offline/jobs1 and the same target:

| Command | Actual result |
| --- | --- |
| `node verify-frontend.mjs` | PASS16.964s; strict TypeScript, all wired suites,60 frozen cases and normal bundle hook exclusions |
| `node node_modules/prettier/bin/prettier.cjs --check "ui/*.{ts,tsx,html,css}" "*.{json,mjs}"` | PASS |
| `cargo test --manifest-path src-tauri/Cargo.toml --test harness_contract --features dev-harness --locked --offline --jobs 1 --target-dir $ownedTarget` | 2 passed,0 failed/ignored;25.293s command |
| `cargo clippy --manifest-path src-tauri/Cargo.toml --all-targets --all-features --locked --offline --jobs 1 --target-dir $ownedTarget -- -D warnings` | PASS13.342s |
| `node build.mjs` | PASS0.332s; normal frontend restored |
| `cargo build --manifest-path src-tauri/Cargo.toml --no-default-features --locked --offline --jobs 1 --target-dir $ownedTarget` | PASS16.533s; normal executable restored, unlaunched |
| `cargo fmt --all -- --check` | PASS3.910s |
| From repository root: `cargo tree -p locallore-android --target aarch64-linux-android --locked --offline` | PASS0.361s;0 Tauri/Wry/WebView2/local-runtime/llama hits |

Initial Android graph attempts genuinely refuse missing cached cesu8, combine
and windows-sys archives. Under the owner's exact-locked-package restoration
approval, only pinned archives were restored to the existing isolated cache.
An independent checksum audit matches all156 restored archives to unchanged
Cargo.lock (`4fb7c498ca0ecc62c4ea1f65c63b370ab4336eb75133d08b3a71f5664156cf93`).
No dependency upgrade, model download or lock change occurred. The final graph
is offline; restoration itself is not described as offline.

Normal frontend SHA `77bbc6c0c75ddfa0243027d71a89c09ccac6a58c75771a7d53771dc10904084b`;
normal executable SHA `d4bbb0029bcdd7767de7753bd69ab8a1de321e6c654b93687b6b8a44cb84f75e`.
They were built, not launched. Existing full shared/native/Android-host suites
in the PR226 qualification retain their own source attribution; they were not
rerun or relabeled as new results here. This slice changes no shared Rust path.

Environment: Windows NT10.0.26300 x64; rustc/Cargo1.93.1; Node24.22.1;
TypeScript7.0.2; React19.3.1; esbuild0.28.2; Tauri2.12.5/Wry0.57/Tao0.37.1.
Actual WebView user-agent advertises Windows10/x64 and Edge/Chrome155.0.0.0;
that is a user-agent observation, not an exact installed runtime build number.
Python3.14.7 performs the private archive checksum audit only.

No model ran. No physical/emulated Android, JNI/ABI build, JVM/Gradle, clipboard,
OS keyboard input, screen reader, enlarged-text matrix, full D05/D06/Domain2
memory, offline whole-app or package/distribution qualification is claimed.
Generated raw synthetic artifacts remain local and gitignored.
