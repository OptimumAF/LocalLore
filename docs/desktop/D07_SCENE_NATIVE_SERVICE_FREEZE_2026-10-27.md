# D07 native scene service: independent test freeze

Refs #29 D07.03/.05. This is a source-only proposed oracle freeze on
`97106af7`, supporting the existing native-service contract. It is not a new
roadmap or acceptance record. The new test module has not been registered,
compiled, formatted or executed. Missing proposed APIs are not behavioral RED.
Model assets and runtime availability remain unverified.

## Frozen interface

The non-Serde, crate-owned `FullComparisonProtocol::{LiteralV3, SceneV4}` selects
the native service construction only. Existing `*_native` methods retain their
Protocol3 meaning and delegate to `LiteralV3`. Typed `*_native_for` methods take
`protocol` immediately after `granted`; all other arguments retain the existing
catalog, lookup, status, open, start, resume, cancel, close and managed-pick
signatures. Close retains its existing ignored grant parameter. No new renderer
selector, command, model authority, path or execution hook is part of this freeze.

The sole test observation seam is `#[cfg(test)] ModelManager::
evaluation_sequence_for_tests() -> Result<u64, String>`. It reads the existing
evaluation reservation counter. It does not reserve, reset or add a counter.
This distinguishes no reservation from reserve-and-release, which unloaded model
status alone cannot establish. Root approved this seam; its implementation and
module registration belong to the production owner.

## Required oracles

The new `evaluation/comparison_run/scene_native_review.rs` freezes eleven tests:

1. Denied grant, stale epoch, unsupported batch and malformed client refuse
   before consent, files and any reservation.
2. A genuine actual native SceneV4 consent denial emits the closed consent
   metadata and provisional index/manifest but no turn, completed report or
   model reservation. Synthetic model/resource sentinels remain byte-identical.
3. Mixed scripted3/native3/native4 catalogs preserve original metadata bytes,
   retain old wrapper/default status values and filter only the requested lane
   and protocol. No copied native outcomes are used.
4. Bad version/protocol/lane/native flags, nested arm descriptors, budgets,
   unknown keys and duplicate clients in every index generation fail the global
   catalog before protocol filtering and without file writes.
5. The combined 32-run cap and cross-protocol client identity are checked before
   consent, reservations and new durable files.
6. Tokens cannot cross protocols through status/open/resume/cancel/close or
   managed reader selection; a failed foreign operation does not revoke the
   rightful token.
7. A held consent callback permits an idempotent retry with the same run/token/
   operation, then cancellation prevents the affirmative late callback from
   reserving a model. The callback is released before result assertions.
8. A genuine denied native4 retained prefix with a mismatched manifest binding or
   exceeded existing run budget refuses resume before new consent, reservation
   or file writes, preserving the actual failure evidence.
9. A genuine denied native4 provisional prefix can be opened by its matching
   managed read-only reader as an empty, incomplete, zero-human-review snapshot.
   This is failed-run history, not a completed native run or execution grant.
10. Separate real scripted SceneV4 Core/Host/Store output can be opened by the
   raw reader; both selected lanes refuse before consent, reservation or selected
   output. The actual report is compared, and files remain unchanged.
11. The actual default native start wrapper still emits Protocol3 consent,
    index version2, manifest version3 and the actual current native V3 binding.
    Typed status equals default status, and native4 catalog reads preserve the
    original provisional index and manifest bytes.

The fixture uses fresh UUID task TEMP directories and ordinary non-reparse
entries. Bounded inventories compare actual file bytes, including lock files.
Synthetic sentinel files are not model assets and are never passed off as such.
No native runtime is granted by these tests. Unknown cleanup retains the same
actual managers and lease rather than dropping owners or deleting evidence.

## Attribution and remaining gates

The actual scripted SceneV4 producer is used only for its own raw reader and
selected refusal. It is never relabeled as native wrapper metadata, a native
checkpoint, an approved runtime profile or a completed native report. Metadata
fixtures intentionally contain no work or canonical outcomes.

The empty managed native4 test requires only an actual consent-denied provisional
prefix. A current-source **completed native4 resume without consent/reservation/
asset work** still requires a genuine retained completed native4 cohort. This
freeze does not invent one. Actual model execution, cancellation after runtime
ownership, runtime drain, no-copy asset reuse/root precedence, native IPC,
WebView rendering, phone execution and human quality remain separate gates.
The original human assessment remains “needs improvement.”

## Coordinator execution after source review

The coordinator registers this module under `#[cfg(test)]`, integrates the typed
service implementation and records actual compile/setup failures separately from
behavioral failures. The focused command is:

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --bin locallore-desktop-spike --all-features --locked --offline --jobs 1 --target-dir <owned-target> evaluation::comparison_run::scene_native_review:: -- --nocapture --test-threads=1
```

This command is **UNRUN** for this freeze. The explicit test-thread limit applies
only to this focused service cohort, not to a claim of default-parallel native
qualification. Preserve compile logs, all original failures, fixture calibration
changes and the exact source at every actual run. Re-run existing Protocol3
native/managed-reader tests before claiming default compatibility.
