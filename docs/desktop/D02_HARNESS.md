# D02 application-owned development harness

These D02 compatibility journeys deliberately use ephemeral fixtures and label
their progress as memory-only. The production app now uses shared durable storage;
its distinct `npm run harness:durable` proof is documented in
[app durability](APP_DURABILITY.md). Neither backend substitutes for the other:
headless rendering is separate from actual native WebView/IPC execution.

The harness verifies the running Play/Story Lab shell without desktop control.
It invokes the same `Controller` used by React and the same `IpcGateway` used by
buttons. Native runs use actual Tauri WebView → Rust `host_call`; engine outcomes
come from the shared host. Fault injection delays/drops selected acknowledgements
around that real path. It does not replace successful engine replies with a mock
transcript or simulate gameplay in JavaScript.

From the repository root after the [development prerequisites](../../apps/desktop/README.md):

```powershell
npm --prefix apps/desktop ci --ignore-scripts --no-audit --no-fund
npm --prefix apps/desktop run check
npm --prefix apps/desktop run harness:native
npm --prefix apps/desktop run harness:headless
```

Provision headless Chromium once with
`node node_modules/playwright/cli.js install chromium` from `apps/desktop`.
This is optional for native runs. Do not run both harnesses or a normal frontend
build concurrently in the same checkout: they share `dist` and the native binary.
Each runner builds with `--locked --offline --features dev-harness`, creates a
fresh ignored `apps/desktop/artifacts/{native|headless}-UUID` leaf, and exits
nonzero on failure, timeout or missing checkpoints. Exit 0 requires the final
report and all 21 checkpoint files. Bounds are timeouts, not performance claims.

## What each backend establishes

| Backend | Actual path | Render and lifecycle evidence |
|---|---|---|
| Native | Embedded React → Tauri `host_call` → shared Rust Host → Engine | Hidden, unfocused app WebView2; app-only `CapturePreview` PNGs, including fixed narrow/wide sizing. Destroys its own WebView during pending work and recreates it against the same native host; counts must reach zero before reopen. |
| Headless | Same React/controller → fixed Playwright binding → dev-only Rust stdio Host → Engine | Own headless Chromium page only; page PNGs. Replaces its own stdio process on reopen. This is not native WebView IPC/window evidence. External asset requests are blocked and counted. |

Neither backend activates windows, injects mouse/keyboard events, attaches to a
user browser, captures desktop pixels or automates another application. Native
capture may report unsupported/failure while preserving semantic JSON; inspect
each `*.capture.json` before claiming a native render. On the tested Windows host,
all final native captures report `native-webview2`.

## Observable contract and outputs

`Controller.semantic()` returns one version-1 synthetic view containing
`uiRevision`, view, selected session/story/branch, observer, pending operation,
turn status, selected finalized receipt, visible error, player/inventory,
revision-bound inspection, transcript page, draft, state difference, layout,
bounded errors and disposal state. The driver waits for React rendering before
checkpointing, records DOM headings/control names/row counts/viewport/overflow,
then awaits capture before making the next scripted change. A PNG observes the
app render; it is not an independent canonical-state authority. Receipts and
coherent player snapshots remain authoritative Rust results.

Each checkpoint writes `{label}.json`, `{label}.png` where supported, and
`{label}.capture.json`. `report.json` is the reopened stage's final result;
earlier-stage checks/errors remain in checkpoint JSON. `summary.json` unions
distinct checks across both stages and records source commit/dirty status,
source/lock/bundle/executable SHA-256 identifiers and backend. The final
[verification packet](D02_VERIFICATION_2026-10-22.md) identifies inspected runs.
These local artifacts are ignored and contain synthetic fixtures only. Do not
point this driver at private stories or upload raw artifacts by default.

The 21 labels cover initial/accepted/rejected/pending/cancelled/retry/failed/
malformed/stale, session switch, receipt/observer/Play return, narrow/enlarged,
close/reopened/disposed, explicit copy, pagination and hostile dialogue. Named
regressions also cover lost submit/commit acknowledgements, duplicate retries,
cancel during recovery, late errors after known terminal outcomes, malformed
recovered receipts, read ordering and stale completion. The direct-engine oracle
reexecutes recorded typed requests with the shared Engine and compares complete
receipt arrays; it never calls a model.

## Narrow development boundary

Frontend `__DEV_HARNESS__` is false by default. The normal bundle eliminates
the driver/fault gateway; `npm run check` checks marker absence. Native modules,
stdio bridge and all six harness handlers compile only with Cargo feature
`dev-harness`, off by default. Native window hooks additionally require
`LOCALLORE_D02_HARNESS=1`, the current native `main-<epoch>` window lease and a launcher-owned fresh
artifact leaf. Generated permission names do not register handlers; the normal
binary registers only `host_call`. Environment variables cannot restore
compiled-out commands. The fixed initialization flag is not a production API.

There is no server/listener, remote debugging, CDP endpoint, arbitrary JavaScript,
path selector, file reader, shell executor or generic test command. The dev-only
stdio bridge accepts typed host messages, resource counts and bounded receipt
comparison; no story path or model command. Production IPC remains the bounded
host contract, with native-window checks, CSP, embedded-origin navigation and
new-window denial.

| Bound | Value |
|---|---|
| Host input/reply; sessions/turns/workers | 24,576 / 262,144 bytes; 4 / 64 per session / 4 |
| Error ring | 64 `{source,category}` enum entries; no raw exception/message/path |
| Checkpoints / semantic JSON / PNG | 40 allowlisted one-shot labels / 256 KiB / 16 MiB |
| Capture / app watchdog / runner child | 10 / 180 / 210 seconds |
| Headless per-call / close fallback | 15 / 5 seconds |
| Stdio / oracle | 1,024 frames under 32 KiB each / 64 receipts and 256 KiB |

The launcher trusts its local build environment/artifact parent; this is not an
OS sandbox. There are no private inputs in error categories or synthetic output.
Detailed [native review](D02_NATIVE_REVIEW.md) records module contracts and fixes.

After testing, restore ordinary assets and executable:

```powershell
npm --prefix apps/desktop run check
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline
```

No actual OS clipboard write, injected keyboard traversal, screen-reader audit,
installer, physical phone, real inference, durability or disconnected-network
qualification follows from these scripted journeys. Keyboard policy and labeled
native controls are checked without injecting input; copy uses an explicit sink
in the harness to avoid changing the user's clipboard.
