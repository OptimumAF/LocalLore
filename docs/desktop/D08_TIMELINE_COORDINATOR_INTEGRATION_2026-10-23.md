# Saved timeline UI: integration and native evidence

Refs #30 D08.04 partial and #12 M08.01/.02 prerequisites. Root claims
6371663815, 6372300342 and title/draft addendum 6372497613. This slice browses
and resumes existing timelines; creating forks, replacing committed history,
regeneration and author corrections remain unavailable until their shared
application ports land. No broad D08/M08 task is completed by this PR.

The released module packet is described in
[D08_TIMELINE_BROWSE_2026-10-23.md](D08_TIMELINE_BROWSE_2026-10-23.md).
The independently reviewed integration and concrete findings are in
[D08_TIMELINE_INTEGRATION_REVIEW_2026-10-23.md](D08_TIMELINE_INTEGRATION_REVIEW_2026-10-23.md).
Root integrated accepted main `f5187b9784cc901870a05a052213777d25d212f7`
without changing its curated evaluation behavior. Final native measured source
is clean `fa22eb20a41ad04decb89e5b6843a4a1c74339ac`.

## Behavior and repaired defects

The panel uses the existing Rust catalog-v2 and Controller resume/switch paths.
It displays roots, ancestry, completed fork point, current head, saved drafts
and retained retired parents. Retired entries are not selectable. Scope,
revision, observer, session and disposal changes clear/fence presentation.
Opening metadata or inspecting a character grants no generation knowledge.
There is no second session, lineage interpreter, persistence or inference owner.

Actual Rust child snapshots preserve original ancestor request/event scopes.
The old frontend decoder incorrectly required every receipt to have the selected
child scope. The child-resume test failed Wire before the narrow decoder repair;
selected Play/player scope and revision still bind to the child, and each event
binds to its own original request. Missing/extra/unsafe/foreign original scopes
are refused. Zero/negative event sequences also produced a retained RED before
the explicit positive-sequence check. No history was relabeled.

Image review found child/sibling session titles fell back to Lantern Quay while
the actual story had another title: workspace listing contains story roots.
The actual-controller title regression failed before repair. Session titles now
use the same story ID's catalog title, with Saved story as the missing-metadata
fallback. Draft counts remain exact-scope metadata. A root-draft3/child-reply
omitted-count test caught an intermediate title fix incorrectly borrowing the
root's draft count; the unchanged test passes after separating those lookups.
Both failures remain local and documented rather than erased.

Review also found the harness could call a blank DOM/capture-unavailable result
a pass. It now requires a nonempty app, actual timeline heading, exact catalog
row count, selected branch and correct canonical story title at every checkpoint.
Each native checkpoint must report native-webview2; the launcher requires the
fixed eleven initial plus three restarted PNGs. Pending/cancelled checkpoints
require their actual visible lifecycle text and scroll to the turn controls.
No arbitrary renderer code/file/shell option or debugging service was added.

## Root execution

| Layer | Actual result |
| --- | --- |
| Frontend / decoder / actual controllers with MOCK gateway | Full verifier PASS, including 83 timeline checks, strict TypeScript, generated schema and normal-build hook exclusion |
| Native default | 54 PASS, one existing symlink-privilege ignore |
| Native dev-harness | 57 PASS, same ignore; 2 harness-contract PASS |
| Native strict all-target/all-feature Clippy | PASS |
| Formatting | Rust fmt, full frontend Prettier, git diff check PASS |
| Actual invisible/unfocused WebView2, frontend controllers and native IPC at clean fa22 | 74 distinct assertions; 14 application-owned render images; actual two-process restart |

Native unit/strict checks ran at clean daaa012, after integration with main.
Subsequent changes are frontend title/draft handling, panel prose, dev-only
snapshot assertions and docs; native Rust bytes did not change. Final normal
frontend verification follows the final native run. No Android/Core/Host/Store,
schema, prompt, model, corpus or budget change is made by this slice. No new
Android/device qualification is claimed; final integrated compatibility remains
part of the desktop assignment.

The fixed native fixture creates a **new pinned synthetic database** through
Store/Engine typed operations before Host opens it. Root has four accepted
turns, parent forks at2, child at4, sibling at1. The parent later advances then
retires while preserving the child's required prefix. Child excludes future
parent and sibling canaries, retains original inherited receipts, cancels a
pending fake preparation at4, retries once to commit its own event at5, and
resumes at5 after process restart. A delayed child snapshot cannot overwrite
the selected sibling. Sable cannot inspect unwitnessed inherited dialogue;
inspection leaves canonical Play unchanged. Root remains at4. All owned Host
sessions/workers are released. The development fixture cannot overwrite or
reseed an existing database. Seeding uses typed commands; continuation uses the
explicitly labeled fake provider. No actual model executes.

Root inspected representative final app-owned PNGs for child receipt/title,
pending/cancel/retry controls, narrow catalog and restarted child; earlier
images exposed the title defect. Final controls/status/receipt text are
coherent, wide/narrow text wraps and automated overflow/DOM/render gates pass.
Semantic snapshots include selected scope/observer/revision, pending operation,
displayed receipt, visible error, catalog and bounded DOM text. Lifecycle images
intentionally show the turn controls; their full metadata stays in paired JSON.
These are actual WebView2 CapturePreview images, not desktop screenshots or
headless/SSR/native-engine substitutions.

Final local directory:
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/timeline-integration-artifacts/timeline-native-235d92c0-9d22-4c06-8da9-fe7deb4fea02`.
Summary SHA-256:
`4049c27e056b1a1aeaefb3d631704db5e4854515cde784003a03b131037bd4c1`.
It records clean source, exact inputs and executable hash. Artifacts stay local,
outside Git. Initial bounded errors are exactly two expected native Cancelled
entries from the deliberately cancelled preparation; restart has zero. No
frontend/unhandled errors. Two Chromium shutdown Error1412 stderr lines remain.

## Reproduce and limits

Windows11 Pro10.0.26300; Rust/Cargo1.93.1; Node24.22.1; MSVC14.34.31933;
Windows SDK10.0.19041.0; existing pinned frontend dependencies. Exact selected
WebView2 runtime loader version was not captured. Use task-owned TEMP/TMP,
debug info0, incremental off, and one Cargo build job under memory pressure.

From repository root:

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --jobs 1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --jobs 1
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --all-targets --all-features --jobs 1 -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
```

From apps/desktop with Node on PATH:

```powershell
node verify-frontend.mjs
node node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}'
$env:LOCALLORE_D08_TARGET_DIR = 'D:/task-output/native-target'
$env:LOCALLORE_D08_TIMELINE_ARTIFACT_ROOT = 'D:/task-output/timeline-artifacts'
node timeline-harness.mjs
node verify-frontend.mjs
```

Retained setup failures: wrong private AcceptedEvent field accessor corrected
to scope(); OS1455 compiler allocation failure followed by identical-source
jobs1 execution; test cleanup DirectoryNotEmpty from SQLite WAL/SHM corrected
to only four literal test-owned names; wrapper viewport arguments corrected
to existing fixed presets. The first36/14 cohort had sourceDirty:true solely
from an untracked generated permission for the then-unmerged curated command.
Accepted-main integration tracks that identical permission. Historical artifacts
are not rewritten or reattributed to the final clean cohort. Later60/14 and72/14
cohorts remain separately source-bound; final74/14 adds visible lifecycle guards.

No model, device/emulator/ADB, network-blocking experiment, desktop input or
capture, protected-chat action, OS/repository setting, release or download was
used. Next runnable shared work is the application-owned fork/replace port,
durable verified-memory jobs/consumer and typed author-correction semantics,
then their desktop UI and cross-host qualification.
