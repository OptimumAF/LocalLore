# Native full-comparison consumer qualification, 2026-10-26

Refs #29 (D07.03–D07.06 supporting consumer slice), #21.

This document records the frontend consumer's qualification. The accepted native
service is PR #214, merged as `61431c0e243617e287053dcf3f3b9ebc0d837eef`.
Its Rust service, actual installed-model and scripted native WebView evidence
are historical service evidence; they do not qualify this newer frontend.
The consumer contract is
[the frozen interface document](D07_NATIVE_FULL_COMPARISON_CONSUMER_CONTRACT_2026-10-26.md).
Whole D07 acceptance, human quality review and physical-phone gates remain open.

## Test boundary

The new checkers bundle actual controller/model/view source with installed,
pinned esbuild. Controller/reader tests use bounded synthetic IPC responses.
The Main checker uses actual Main, App and ComparisonRunView source with a
bounded React hook/JSX fixture and unrelated leaf stubs. Its five fixed exports
are appended only to the checker input, never production source. Importable
fixture helpers are test code; importing them does not rerun its twenty cases.
These checks are mock/headless evidence, not native IPC, WebView, OS consent or
model execution. A direct invocation is `node <checker>.mjs` from `apps/desktop`.
`LOCALLORE_CHECK_OUTPUT_DIR` selects a local ignored report directory.

## Recorded initial executions

All cohorts below recorded a clean source commit and verified the source stayed
unchanged through the command. Logs and machine-readable process/report files
are retained locally, outside the checkout; private absolute paths are omitted.

| Cohort/source | Actual result | Interpretation |
|---|---|---|
| `baseline1`, `ae4065ce35e7362f4275505ec0fd0ed40b6d820b` | Legacy 56/56; native controller 1/85; native reader 2/22; Main 0/20 | Missing feature APIs/fields. Transpilation succeeded. Main failed setup before exercising twenty mode behaviors. These are not semantic regression reproductions. |
| `first1`, `c9ade43de19fc14779b5f3cb95233e627c534a86` | Legacy 56/56; native controller 87/88; reader 22/22; Main 20/20 | One semantic failure: closing a sent native start with unknown ACK and no token left current uncertainty set after captured UUID recovery/close settled. |
| `tsc-first1`, same `c9ade43d` | TypeScript exit 1, one TS2322 | Existing scripted development journey passed the newly widened status union into a V1-only helper. |
| `tsc-second1`, `1c0fcfb13d91c04596cd048100859f3a8d3cbe3b` | `node node_modules/typescript/bin/tsc --noEmit`, exit 0 | Commit `50f154e3` explicitly narrows actual version 1 status; no V2-to-V1 conversion or cast. Source clean/unchanged. |

The 88 controller cases include the original frozen packet plus independent
one-shot cleanup observations after retired running/unknown/cleanup-flag closes
and the unknown-start-ACK/no-token case. The old 56-case checker was not rewritten
to accommodate native behavior. The reader packet has 22 declared cases and Main
has twenty; reports use different result property names, so counts above are
read from their actual case/check arrays.

Independent source review also found two frontend fences to test before fixing:
inactive native cleanup must prevent scripted admission even through retained
Start/Resume handlers, and a held Inspect callback must not reopen managed read
access after its independent reader observer/context changes. The contract adds
a presentation-only admission callback and a separate reader context/allowed/
observer fence. Neither changes Rust authority or puts observer identity into
the generation execution key.

## Environment and remaining checks

Windows NT 10.0.26300 x64, PowerShell 7.6.5, installed Node 24.22.1,
TypeScript 7.0.2, esbuild 0.28.2 and React/react-dom 19.3.1. No dependency or model
download was performed for these checks. Only one heavy build/test/model process
is allocated at a time. Separate agent checkouts perform source-only work.

Native consumer WebView rendering, actual native comparison IPC journeys,
installed-model GUI execution, final full frontend/native compatibility checks,
normal build restoration and final-head security checks are not established by
the initial results above. Their results must be added after execution. Existing
OS dialogs are not automated or counted as tested. No desktop input, activation
or desktop capture is used; any future render evidence must come from the owned
hidden/unfocused WebView and every generated image must be inspected.
