# Native literal Director renderer and whole-unit packing

Scope: D07.04 / M07.01 prerequisite. Accepted base PR183,
`6898a35bad4f9dbf8c6373191e7a72620c5bcb93`; implemented and tested source
`f572c1bbeba77397a3d686813e44b0e4e3b88287`. GitHub #29/#11 own status.

This pure native renderer builds literal player Director bytes from the
[accepted read-only transcript source](D07_LITERAL_TRANSCRIPT_SOURCE_QUALIFICATION_2026-10-25.md).
It has **no provider, GenerationRequest, execution, receipt, commit, Host
configuration, JSON policy grant or UI operation**. Existing defaults,
ContextPolicy and Play2.1–2.5 are unchanged. This does not complete a literal
comparison, D07.04, human quality review or the desktop epic.

## Contract

`play::render_player_literal_director_v1_cancelled` accepts an actual Engine,
Request, native transcript source, PlayProfile, DirectorPassV25 and cancellation
callback. The source must match the actual player's exact Domain1 scope/head
and accepted-history basis. A matching head alone cannot pass with a different
seed/history. The request must pass existing preflight and be FreeText.
Domain2 returns Version, wrong scope Scope, stale/divergent source Stale,
non-FreeText Agency and callback cancellation/panic Cancelled. Profile checks
remain shared; Repair with repair_limit0 returns Rule.

The private-field, non-serde `RenderedLiteralDirectorV1` exposes prompt/schema,
shared ForwardedEstimateV1, source/selected/omitted counts, selected suffix start
and native unit provenance. Prompt version is `locallore-literal-director-v1`;
schema and packing versions are1. Native provenance has original scope, turn
and final revision, also private-field/non-serde. Four additional compile-fail
doctests enforce those serialization boundaries.

The model frame has exactly kind, player_text and conversation. Conversation
entries have exact accepted narration and, when recorded, original input.
Typed input is absent, never invented. No source scope, turn, revision, observer,
basis, current state, inventory, nearby IDs, routes, event dictionaries, seed
opening, summaries or author records are inserted. Provenance stays native.
Static instructions treat conversation and the current attempt as untrusted.

The grammar derives from existing static `director_schema()` command shapes,
not the current state-resolved schema constructor. Action excludes Say; Dialogue
allows exactly one Say with exact current text. Entity ID strings use static
minLength1/maxLength64 and ASCII ID pattern; audience bounds stay1–4. No world
IDs, resolved commands, inventory quantities or state-derived enum/const choices
enter it. A current Dialogue text constant preserves input, not historical state.

## Packing and bounds

Selection is a contiguous whole suffix, newest backward, rendered chronologically.
It stops at the first older unit that cannot fit and never backfills a smaller
older unit. At most128 units are selected. If the newest unit cannot fit, return
TooLarge; an empty actual history is allowed only if the base frame fits. No
unit/input/narration truncation or synthesized opening occurs.

Every candidate uses existing `director_forwarded_budget_v25` Initial admission,
including its possible fixed repair allowance. Thus Initial and Repair select
the same suffix. Repair appends the same fixed suffix as current Play; a small
shared helper replaces the original identical inline append. The final actual
prompt/schema is checked again with the requested pass. Existing profile,
24,576-byte role-frame JSON,16,384-byte schema and32,000-byte prompt bounds
remain. Byte/4 and the existing template reserve remain estimates, not measured
tokenizer/template fit. No alternate budget calculator is introduced.

Cancellation is panic-safe before work, after exact-basis validation, per packing
candidate and before return. Existing bounded preflight/basis/serialization calls
are not interruptible internally. All inputs/history remain immutable.

## Pre-edit compatibility references

Before renderer production edits, test source256dd099 was integrated0bcdf4c3
on unchanged Core6898a35b. Root captured four actual stable projections, anchored
only the observed hashes at88dcae76, and passed the unchanged-Core baseline.
The same hashes pass after the shared suffix extraction.

These are explicitly `actual_play25_static_role_inputs` projections: actual
structured role/prompt/schema, request identity, static output/poll budgets and
full fixed profile. Each case has a real malformed-first Director, one repair,
actual accepted proposal and narrator: three actual scripted provider calls.
Real remaining deadlines and measured stage timings vary across runs and are
validated separately, not normalized into a purported whole-request/receipt
golden. Actual serialized receipts restore byte-exactly without a provider.

| Current Play case | Bytes | Stable projection SHA256 |
|---|---:|---|
| recent Action repair |22164|b3354bc3de071ba018b6d3912659c3fa525fd61fe4538ad347fd753ecbeac3f1|
| recent Dialogue repair |21800|93c269faeb3c3844b88fbe39fe7b4219ff9ef63fb4824058d2b8cc1e3db013d4|
| relevant Action repair |22162|bb24293d653b2c6f795cf54b2526f6c4de750565be2470aaac2b3294a26db6df|
| relevant Dialogue repair |21798|ff8fc717b8e25456db7ed9d43dd5cccb0086a9b5261c55ee4a54b323c84e4200|

The previously anchored six whole PolicyCompilation byte references also pass.
Neither finite set claims universal byte equivalence or deterministic inference.

## Exact execution results

Windows NT10.0.26300 x64 / PowerShell7.6.5 / Rust1.93.1 (`01f6ddf75`) /
Cargo1.93.1 (`083ac5135`) / LLVM21.1.8. Cached dependencies only, locked/offline,
jobs1, debug0/incremental0 and owned TEMP/target. All checks ran serially with
clean source, recorded terminal unchanged state and exited0 except the two
explicit capture/compile observations below.

| Check | Result / command time |
|---|---|
| Legacy capture0bcdf4c3 | deliberate sentinel failure after all four hashes;3.818s; not behavioral RED |
| Anchored old-Core baseline88dcae76 |1PASS/0FAIL,0.07s test/2.357s command |
| Frozen renderer API before implementation18fa89df | missing-import compiler failure,0.715s; not behavioral RED |
| New renderer f572c1bb |8PASS/0FAIL,0.23s test/8.342s command |
| Four current-Play projections after factoring |1PASS,0.05s test/1.464s command |
| Six original whole-policy references |1PASS,0.03s test/1.211s command |
| Related host-feature policy/Play regressions |30PASS;12.488s command |
| No-serde doctests (source4 + renderer4) |8PASS,0.61s test/1.406s command |
| Core strict all-target/all-feature Clippy |PASS;14.035s command |
| Workspace Rust format |PASS;2.099s command |
| Android Rust host |20PASS,1.70s test/15.696s command |
| Desktop strict all-target/all-feature Clippy |PASS;16.19s Cargo/16.457s command |
| Normal desktop build |PASS;36.61s Cargo/36.760s command; executable not launched |

Eight focused renderer groups exercise exact Unicode/quoted/backslash/newline
text, typed absent input and empty history; fork repeated IDs with native-only
provenance/future+sibling exclusion; schema equality across different actual
worlds; exact shared Initial/Repair relation and budget getter equality;
shared-budget suffix cut with a smaller older unit that would fit but must not
backfill;129 actual source units with128 selected despite129 fitting, newest/base
refusal; divergent seed/history/scope/head/Domain2/type/profile refusal; cancellation,
panic and request/profile/source/projection/history-basis immutability. Test-only
candidate prompt variations are diagnostic calculations, never actual forwarded
model requests. The fixed cancellation panic-hook message is expected in a pass.

Independent bounded source review found no concrete failure in basis/privacy,
static grammar, contiguous suffix/caps, shared budget/repair or cancellation.
It performed no execution and does not constitute human quality review.

## Reproduce and remaining work

Use owned absolute target/TEMP paths and the same environment described above.
From repository root, serialize these commands with other heavy work:

```powershell
cargo test --locked --offline -p locallore --jobs 1 --target-dir <target> --test literal_director_render --test literal_director_legacy_bytes --test literal_transcript_legacy_bytes -- --nocapture --test-threads=1
cargo test --locked --offline -p locallore --features host --jobs 1 --target-dir <target> --test m08_context_policy --test m08_context_policy_review --test m08_play25 --test d07_host_policy -- --test-threads=1
cargo test --locked --offline -p locallore --jobs 1 --target-dir <target> --doc -- --test-threads=1
cargo clippy --locked --offline -p locallore --all-targets --all-features --jobs 1 --target-dir <target> -- -D warnings
cargo test --locked --offline --manifest-path crates/locallore-android/Cargo.toml --jobs 1 --target-dir <target> --lib -- --test-threads=1
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --all-features --jobs 1 --target-dir <target> -- -D warnings
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1 --target-dir <target>
cargo fmt --all -- --check
```

Synthetic raw logs/process records remain local and ignored under
`d07-literal-render-*`. No private stories/prompts, personal paths, weights or raw
diagnostics are published. No browser/native UI/app/IPC/model execution, render
image, OS dialog, device/ABI/JVM/Gradle/emulator/phone, performance/RAM, installer
or narrative-quality result is claimed for this slice. Native compilation is
not native rendering. No new dependency or settings/release change. The existing
moderate GLib advisory remains open and unmodified, not zero vulnerabilities.

Next runnable prerequisite is an explicit versioned executable construction and
receipt/replay path through the same action guard, staging and Engine commit.
Current unversioned ContextPolicy cannot silently gain new semantics. Then bind
Host/evaluation/capture/decoder/UI consumers without relabeling old reports.
No NPC literal generation or Domain2 maintenance is enabled. Ordinary Play still
uses mandatory state. The observed unrelated-library narration quality failure
and the human quality gate remain unresolved.
