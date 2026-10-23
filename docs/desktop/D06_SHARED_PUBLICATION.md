# Shared passive trace publication

Refs #28 (D06.01/.06/.07, partial). This report supplements the collector,
production-hook and Host reports; it does not accept the desktop debugger gate.

The publication branch starts at accepted main
`18c5c2f7050001f8b23fe2ca74d188ba1c637228`. Its implementation is the unchanged
collector, production hooks and Host handoffs, integrated as `181443e`, `fac128b`
and `b3169e2`. The coordinator reviewed the combined source and tests, including
the opaque per-session trace owner, authorization before reads, durable-head
checks, bounded reply, best-effort locks, actual prepare/publication/commit
boundaries and saved-receipt comparison after an uncertain acknowledgement.
The implementation author and coordinator are different agents; this source
review is not a human approval or an independently executed native UI journey.

The collector has no I/O or canonical-state capability. Hooks cannot submit an
operation or widen a generation observer. Clear/disable invalidates retained
handles. A reopened session cannot read the previous session's window metadata.
Exact retries do not synthesize missing generation stages. When neither a commit
acknowledgement nor its saved-status lookup proves an outcome, the trace labels
the commit unknown and leaves the attempt running. A competing receipt cannot
be presented as this worker's accepted candidate. Truncation, contention, poison
and dropped hooks cannot become a gameplay rejection. No concrete unresolved
source blocker was found in this integration review.

## Checks actually run on the integrated branch

Windows x86_64, Rust/Cargo 1.93.1. Rust commands used locked offline dependencies,
development/test debug information disabled, incremental compilation disabled,
and the task-owned D: targets. Frontend checks used bundled Node 24.19.0 and the
existing locked dependency installation, not an installation or model download.

```powershell
cargo test --workspace --locked --offline --target-dir <task>/d06-trace
cargo clippy --workspace --all-targets --locked --offline --target-dir <task>/d06-trace -- -D warnings
cargo fmt --all -- --check
node apps/desktop/verify-frontend.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <task>/desktop-publication-target
```

- Complete Rust workspace: **217 passed, zero failed or ignored**. This includes
  all nine final Host/SQLite trace cases, the production on/off golden runs,
  collector limits and the Rust Android/JNI adapter tests.
- Strict workspace/all-target Clippy and Rust formatting: passed.
- Frontend: normal build, strict TypeScript, current Rust-schema request checks,
  export/model/terminal-refresh/inspection regressions and exclusion of
  development hooks from the normal bundle: passed. Generated schema equality is
  also tested in the actual Rust workspace; the frontend regeneration left the
  generated TypeScript unchanged.
- Native Windows Rust tests: **17 passed, zero failed, one explicitly ignored**
  Windows symlink-privilege case. This integration did not rerun that privileged
  case; previous dated evidence remains separate.

Local logs are `target/publication-workspace.log`, `publication-clippy.log`,
`publication-frontend.log` and `publication-native.log`. Targets and logs remain
gitignored. These native unit tests do not execute WebView rendering or frontend
IPC. No model, physical Android device, APK journey or desktop screenshot was
executed for this slice. Full capture, selected-context artifacts, summary
maintenance, debugger pause and the native debugger UI remain unavailable here.
The next runnable integration is the separately claimed desktop metadata view,
followed by the shared context compiler and its eligible selection evidence.
