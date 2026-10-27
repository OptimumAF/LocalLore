# Recorded-turn evidence after native reopen

Refs #26 D05.03/.06/.07, supporting slice only. Base accepted772e9bd0;
final executed source clean, unchanged
`6affe0227caa3f042687ce8fa073ee238e55e17a`.

## Result and existing shared authority

A saved story's recorded narration now offers **Inspect recorded turn changes**
after reopen, even when the controller has no current raw receipt. It opens the
existing Player historical comparison and its original-source links. It does
not reconstruct a receipt, invent a base revision or persist another ledger.

Core Query2 History emits a narration row only when all receipt events are
visible, copying the complete actual event ID list. The new controller action
uses its actual final ID. Rust's completed-boundary catalog derives the preceding
state; the selected child/current head remain separate from original scope and
historical revision. No grouping of partial event pages or unfiltered
`turn_status` lookup is used.

The action requires actual current checked History/Inspection bound and row
objects, coherent Player Play context/snapshot, History view, Player privacy,
same-story original scope and nonempty safe contiguous event IDs. It revalidates
mutable DTOs through existing decoders. Query context/channel-sequence fences
remain authoritative for pending, result, final-busy and late replies. The actual
panel captures rendered context/bound/row and checks current result after await;
the accepted checked-inspection effect owns local query controls.

No Host command, engine, storage, schema, provider, canonical write, inference or
inspection grant changes. Shared crates/Cargo.lock are unchanged from772e.
Character(player-ID), Lab, missing/incoherent snapshot, original-input and stale
objects cannot use this action. Inspecting a source cannot change what a
character knows or what generation may access.

## Independently frozen headless checks

The25-case checker/contract was committed before implementation (original
e9ad97e7, Root9d4b2fa9). Root's baseline actually runs:4 pass,21 absent interfaces,
zero calibration failures. Absence is not behavioral RED. Productionef5f7cad
then passes25/0. Formatting/registration does not change its oracles; the existing
60 receipt tests stay unchanged, SHA
`b356d546dfaee2a760d2e038fbef5b3da682a24a8726eb8e24664d51205ce739`.

These compile the actual controller/panel and use real React SSR with the same
narrow server-snapshot adapter and actual JSX-handler capture as PR228. The
Gateway/History/diff DTOs are synthetic; no Core/IPC/DOM pixels, process restart
or native authorization is established by these checks. Coverage includes a
fresh controller with receipt:null, inherited/multievent narration, exact
row/bound membership, malformed/mutated data, role/snapshot denials, reentrant
context/query retirement, actual panel callbacks and inert hostile text.

Inherited narration's new action is headless coverage. The native cohort below
clicks the reopened child's narration and separately follows an inherited event
source. Same-context source-page replacement during an admitted in-flight read
is not separately qualified; existing context/query-sequence fences and Rust
scope/head/historical authority remain. Do not claim every page-retirement
interleaving or a universal privacy proof.

## Actual native execution and render review

Run from `apps/desktop`, using the pinned existing Node and provisioned cache:

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
$env:LOCALLORE_M07_MEMORY_ARTIFACT_ROOT = '<existing owned artifact directory>'
$env:LOCALLORE_M07_MEMORY_TARGET_DIR = '<existing owned native target>'
& $taskNode author-harness.mjs
```

The fixed launcher enforces unchanged source and product hashes, new synthetic
workspace ownership, fixed commands, bounded logs/deadlines and exact capture
inventories. Its app is hidden/unfocused. WebView2 CapturePreview captures only
the app's own render surface; no desktop screenshot, window activation or OS
input is used. Actual mounted DOM button activation invokes the same React,
controller, native IPC, shared engine and SQLite paths as the UI.

At6affe the actual initial/restart journey passes **183 distinct assertions**,
171 initial/57 restart cumulative check labels and **23 app-owned PNGs**
(18 initial/5 restart). Every image was individually viewed by Root. All original
20 capture meanings remain. Three added restart images show the actual persisted
Gift narration opening diff3, a readable potion before2/after3 comparison and its
prior seed source at0, followed by the exact inherited main event1 while staying
in selected child/head3. The pinned header and local controls agree with actual
checked pages. No horizontal overflow or illegible target was found; non-target
form content extends outside the viewport. No full accessibility claim follows.

Each cold read preserves the actual native oracle, root/thin Player snapshots,
History and null raw receipt. The original receipt-link-unavailable metadata
remains distinct from the newly available recorded-turn route. After switching
to Lab, the old Player row's direct controller action refuses with no bridge
attempt; detached DOM callback behavior is not claimed as native evidence.

Initial native process4.172s; restart1.206s; development build39.670s. Every
command exits0, without timeout/truncation. Initial errors are exactly the
unchanged deliberate Inventory/Cancelled/Cancelled; restart errors are empty.
Fixture inference is synthetic and labeled; no model or inference worker runs.
The private artifact leaf is
`author-native-a0ceb6ac-5f20-477e-8c00-c22c722f270e`.

| Final native item | SHA-256 |
| --- | --- |
| Development executable | `32be55205e32a6b1400e9e1b6287105aa1efd4cc171d16e2aaecfab9f4c7686e` |
| Development frontend | `3727370ea74f1894a01d713ec19f1ab6e330ec293b163b38b53ded3f894759fa` |
| Fixed launcher | `e17388c2929441f21b5b597110fb8a333eccfa9ba5c49e231f07b86d3ff431b2` |
| Native summary | `cb1cf0d49128c5b680b09dafe9a5582a67cb15aa618d8923aeb4710d37eda047` |
| Individual image review | `a63c6dc362cc76f4a1a4b8412a2888e16c1cbeb81779e40f427c8770b64f41d1` |

## Other checks at clean6affe

All Cargo commands use the same owned target, locked/offline/jobs1, with
ordinary uncapped SQLite. No source changed during execution.

| Command | Actual result |
| --- | --- |
| `node verify-frontend.mjs` | PASS17.349s; strict TypeScript, all wired suites,25 new+60 unchanged oracles and normal bundle hook scan |
| `cargo test --manifest-path src-tauri/Cargo.toml --test harness_contract --features dev-harness --locked --offline --jobs 1 --target-dir $ownedTarget` | 2 passed/0 failed/ignored;23.253s command |
| `cargo clippy --manifest-path src-tauri/Cargo.toml --all-targets --all-features --locked --offline --jobs 1 --target-dir $ownedTarget -- -D warnings` | PASS18.535s |
| `node build.mjs` | PASS0.341s; normal frontend restored |
| `cargo build --manifest-path src-tauri/Cargo.toml --no-default-features --locked --offline --jobs 1 --target-dir $ownedTarget` | PASS13.684s; normal native restored, unlaunched |
| `node node_modules/prettier/bin/prettier.cjs --check "ui/*.{ts,tsx,html,css}" "*.{json,mjs}"` | PASS3.339s |
| `cargo fmt --all -- --check` | PASS3.919s |
| From repository root: `cargo tree -p locallore-android --target aarch64-linux-android --locked --offline` | PASS0.293s;0 desktop/runtime dependency hits |

Normal frontend SHA `96410b8093913b4d8d516d1254bd661f88e7d0a7c99cf44830d06d42f88ee921`;
normal native SHA `a406bf6e6dcfbb66d6e793c9d5443a7cb79e465965591a0744ba931810802963`.
They were built, not launched. PR229's shared424 and host-compatibility483 test
results retain their own source attribution; no new Core suite is invented here.

Windows NT10.0.26300 x64; Rust/Cargo1.93.1; Node24.22.1; TypeScript7.0.2;
React19.3.1; esbuild0.28.2; Tauri2.12.5/Wry0.57/Tao0.37.1. Actual WebView
user-agent reports Windows10/x64, Edge/Chrome155.0.0.0; no exact runtime build
number is inferred. Python3.14.7 reads private timing/hash records only.

Raw full receipt/proposal reconstruction after reopen remains unavailable;
recorded historical state changes/source inspection is now available. No new
model, phone/emulator/ABI/JVM cohort, real keyboard/screen reader, enlarged-text
matrix, full D05/D06, whole-app offline, package or release qualification follows.
Raw synthetic artifacts remain local/gitignored. Narrative quality retains the
owner's original needs-improvement assessment.
