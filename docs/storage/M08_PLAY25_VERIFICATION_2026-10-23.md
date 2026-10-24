# Play2.5 consumer source and verification — 2026-10-23

Refs #12 M08.03, #11 M07.01 consumer prerequisite, #29 D07.03/.04/.05
prerequisite. Status at this checkpoint: frozen source tests only, UNCOMPILED /
UNRUN; implementation and actual original2.4 capture pending. Root owns all
Core staging/Engine/Host/Store/schema/platform integration and build execution.
Agent resource_metrics_review owns exclusive existing `src/play.rs`, NEW
`tests/m08_play25.rs`, NEW `tests/m08_play24_capture.rs` (explicit allocation
extension), and this new document under `crates/locallore` / `docs/storage`.
Separate branch/worktree `impl/m08-play25` / `source-play25` from exact
`4b0734228b7c891720e5980ed3c5c0440acc23d6`. Claims #12 6377820558,
#11 6377820752, #29 6377820914; capture extension #12 6377837366.

## Pre-production freeze and original-source capture

Original capture draft b9da1cd is retained. Final separated opt-in capture
commit `33224ed71fe4d11a660dd552ef7e51379775f63b`, helper SHA256
`ab0493ef603455f20fac0a5411c5f25b2f4df8648bb4745f13401f1c08dd41fe`.
It references no future API, so Root can compile ONLY that target against
unchanged2.4 without compiling the deliberately unimplemented stage tests.
It runs actual Play with an explicitly synthetic scripted provider/profile,
validates the same result through actual original2.4 restore, and retains all
real measured timings/counts without normalization. It writes create_new only
to two fixed names under pre-existing caller-owned
`std::env::temp_dir()/locallore-play24-capture`:

- `accepted_play_v2_4.json`: actual seed/Receipt, source/synthetic metadata,
  compact Receipt and PlayRecord byte counts/SHA256.
- `accepted_play_v2_4_receipt.json`: exact compact full Receipt, no added newline.

Explicit opt-in `LOCALLORE_CAPTURE_PLAY_V24=1`; ignored by normal tests.
Proposed actual Root command, NOT an execution claim:

```text
cargo test --locked --offline -p locallore --test m08_play24_capture freeze_original_v24_before_current_version_bump --jobs 1 -- --ignored --exact --nocapture
```

Root owns adoption of the two new fixtures. Never manufacture2.4 metadata from
the2.3 fixture or treat a current2.5 generation as an original2.4 measurement.
Play production must remain2.4 until the actual capture is saved. Existing
goldens2.1/.2/.3 are untouched.

Future-API provider tests frozen before production at
`d82b1a1882ada1367701d4d836a252435fb22eec` (eight tests) plus additive
`06c08786e775d66814b24a747e8d3ac01f15b7df` (ninth grounding pair). Final
test SHA256 `108f0224713a48751fb1f7e3ad4fd1e6dedb29af0b30f1f6150e1799bcdb7085`.
No assertion in the first eight was changed. The ninth pair makes the actual
safe-evidence validator consequential: same private golden-mark truth, Wait
must fall back while actual this-turn Discover can ground the guarded phrase;
canonical items never change in either case.

## Frozen provider-path oracle families

1. Actual Domain2 discovery: Director sees retained A, narrator receives actual
   staged observed B and no optional history/other player secret/author reason;
   current2.5/narrator2.2/context2/compiler2/Relevant metadata, player-only update.
2. Both real policy arms execute compiler2 through the same actual entry;
   recent whole transcript units are visible only to Director, never narrator.
3. Wait/Dialogue do not attach old knowledge, current private truth, raw speech
   or audience to narrator. Approved outcomes remain actual.
4. All ten native closed fallback reasons are recorded separately from actual
   Domain2 compiler Raw/Unsupported; no fake Missing or cache contribution.
5. Exact committed retry uses zero roles despite changed current policy/profile,
   cancelled token and different source fallback; accepted bytes/canon persist.
6. Actual canonical current replay is exact; mismatched2.5 policy/prompt/context
   tuple, missing/unknown policy, compiler/context version tampering reject.
7. Unsupported intent0roles, wrong actual proposal1role/no narrator,
   cancellation during narrator and mandatory-budget0roles preserve canon.
8. A newly observed value mentioning an off-screen actor does not expand the
   hidden-actor allowlist; fallback stays exact mechanical summary.
9. Guarded phrase pair above distinguishes this-turn observation grounding
   from privileged world truth; safe prose never creates an inventory effect.

Scripts are synthetic test providers using the actual public Play path; no
model/quality/native/device result follows. Tests have not been compiled or
run. Core stage seven frozen oracles remain separately unchanged.

## Actual source-only checks and next work

At this checkpoint only source/issue/Git reads, standalone rustfmt/parser,
`git diff --check`, owned-path/source-hash checks ran. No Cargo/type check,
provider execution, Node/Gradle/model/assets/app/native/device/ADB/CUA/desktop,
transport/download/settings/protected-resource/PR/merge action. No heavy slot
taken. Root holds execution resources; preserve first actual compile/behavior
failure before a narrow source or explicit fixture correction.

After actual original2.4 capture, implement one current pipeline using Root's
opaque stage/evidence and consuming commit. Expose only crate-private current
validation; keep old2.1–2.4 strict history-only validation/serde omission/bytes.
Then freeze source and qualify on actual combined Core after explicit GO;
Host/Store/platform/decoder/eval policy closure remains separately Root-owned.
