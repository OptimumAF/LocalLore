# Read-only inspection snapshot v1

Refs #8 (M04.06), #24 (D03.03–D03.07). This is a derived local inspection
format, not a playable archive, import API or alternate ledger.

The trusted native adapter calls `Host::inspection_snapshot(session, scope,
expected_revision, mode)`. The host verifies the session/scope and reloads the
existing shared persistence port using its coherent read transaction. An
external commit either precedes that read or follows it; a mismatched expected
head returns `Stale`. The returned validated engine clone is immutable and JSON
encoding holds no write transaction. No new SQL/schema or live database copy is
introduced. Pending turns are excluded. Capture never commits/cancels a turn.
The wire `snapshot_export` operation remains unsupported; filesystem authority
belongs exclusively to the narrow native broker, not this host API.

`ExportMode::Diagnostics` is the default: only structural scope/head/counts in
`diagnostics.json`. No seed, story prose, prompts, models or filesystem paths
are included. Player and Full are explicit **private** story exports. Player
uses the existing character-context visibility policy; incoming private
commitments require a visible source event. Full requires a trusted Story Lab
host grant and includes hidden story knowledge. Story prose itself can contain
personal data or credentials: Player is not a credential-redaction promise.
No model prompt/weight/diagnostic trace is included in any mode.

Player and Full contain exactly seven UTF-8 views: `events.jsonl`,
`transcript.jsonl`, `state.json`, `characters.json`, `relationships.json`,
`knowledge.json` and `threads.json`. Player transcript entries require every
supporting event to be visible; they omit raw requests and proposals. Full
includes accepted events and the implemented projection. Neither mode
fabricates summaries or retrieval indexes: both are explicitly `unsupported`
with a null source revision. Other view status is `observer_filtered` or
`recorded_or_derived`; Diagnostics declares those views `omitted_privacy`.

The native writer adds `manifest.json`. Its format/version, exact scope/head,
schema/rules/engine/app versions, Unix-millisecond capture time, mode/privacy,
per-file scope/source revision, byte count, media type and SHA-256 inventory
identify the captured files. Limits are 32 MiB total (including manifest) and
eight data filenames. Data names are a fixed flat allowlist. No raw database is
part of this bundle. SQLite-tool copies use the existing separate shared
`Store::backup_to` API, not `.db` copying.

`InspectionBundle::validate` checks structural bounds, mode/privacy/inventory,
view status/head metadata, UTF-8 and checksums at the native write boundary.
It does **not authenticate origin or prove observer eligibility for arbitrary
external files**: an editor can change contents and recompute checksums.
Only native-retained bundles captured by the host may be written using preview
tokens. Reopened external bundles remain explicitly untrusted, read-only and
possibly spoiler-bearing regardless of their claimed mode. No bundle is fed
to character context, canonical reducers, SQL or generation. Editing exports
has no automatic effect on a story.

The native adapter separately owns destination selection, exact preview tokens,
window/epoch/scope fencing, staging, cancellation, disk-space/fault handling,
atomic finalization and read-only opening. Those native guarantees require its
own tests; a passing host snapshot test is not a native filesystem journey.
See the desktop D03 native evidence when available. Generated synthetic export
folders stay in ignored application harness artifacts; no automatic upload.

## Dependencies and reproducible checks

The host feature adds optional exact `sha2 = 0.10.9` with default features off.
SHA-256 uses RustCrypto's implementation, not a process-specific hasher. Its
license is MIT OR Apache-2.0; the locked registry graph and locally observed
license declarations are in `INSPECTION_DEPENDENCIES.json`. This enables no
network/runtime service or model download. Primary API reference:
[sha2 0.10.9](https://docs.rs/sha2/0.10.9/sha2/).

From the repository root with cached locked dependencies:

```powershell
cargo test -p locallore-workspace --test inspection_review --locked --offline
cargo test -p locallore --features host --locked --offline
cargo clippy -p locallore-workspace --all-targets --locked --offline -- -D warnings
python scripts/check.py host --offline
```

The focused tests use only synthetic fixture variants. They cover all exported
bytes for NPC-only canaries, player-known facts, trusted Full authority, default
metadata privacy, hashes/head/source status, stale scope, tampering/budgets,
draft exclusion, immutable capture, independent writer commits and actual
capture-versus-commit races. Native render, restart, Android build and real
inference evidence remain separately labeled.
