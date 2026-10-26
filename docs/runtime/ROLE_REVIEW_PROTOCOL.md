# Private role review packets v1

Supporting M01.03/M05.06 and D07.04/.06. This tool records declarations about
existing synthetic comparison evidence. It does not generate turns, grade a
model automatically, authenticate a reviewer, alter canonical state, or accept
model quality. Full milestone criteria still require actual human review and
the other device, quality and comparison gates.

## Use the existing source of evidence

The `locallore-eval` comparison runner already stores actual engine/Host/Store
outcomes, role recordings, captures, failures and provenance. This separate
binary reuses `comparison::desktop_api::open_read_only`, `summary` and `evidence`.
It holds the existing comparison read capability and lock while constructing
the packet. It does not deserialize a user-supplied report as authority or
rebuild prompts, context, gameplay rules or accepted events.

Raw Capture and Outputs require the existing Omniscient/Author inspection
boundary. Both commands require the explicit
`--allow-synthetic-author-evidence` flag before inspecting any path. That flag
permits private evidence inspection only; it grants no generation, correction,
commit, model loading or system operation. No renderer command or application
permission is added.

The facade checks the snapshot, checkpoint, recording and original raw byte
hashes. The review packet additionally binds its snapshot and report digest,
turn/arm, complete source row, exact evidence envelopes and each ordered raw
attempt's role, byte count and SHA256. Repaired Director attempts retain separate
zero-based ordinals. The packet never treats diagnostic text as canonical truth.

## Commands

Build from the repository root with the existing pinned Rust toolchain and
cached dependencies. No model or dependency download is part of these commands.

```text
cargo build --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --bin quality-review
quality-review template RUN_DIR NEW_PRIVATE_JSON --max-turns 4 --allow-synthetic-author-evidence
quality-review summarize RUN_DIR REVIEWED_PRIVATE_JSON --allow-synthetic-author-evidence
```

Use the built executable from your selected Cargo target directory. The
optional local-model feature applies the existing native evaluation graph;
neither review command invokes a provider, with or without that feature.

`template` exports the first N existing report rows in their existing order;
N is 1–8, default 4, clipped to the available rows. Every report row remains in
the packet and denominator. Unselected rows have no exported capture/output or
assessment; they are not silently removed or credited. Empty runs are refused.

The destination must be a new file outside the comparison root, with an
existing ordinary parent. Existing files are never replaced. Parent traversal,
symbolic links and Windows reparse ancestors are refused. Windows device/UNC
prefixes, alternate streams and reserved DOS device names are refused. File
reads/writes are bounded to 4 MiB. Failed or interrupted exports remain retained
and cannot be reused as successful packets. These guards do not authenticate
host evidence against an adversary who controls the machine or all source data.

Successful template stdout contains only aggregate counts, a snapshot binding
and file size/hash. The private JSON contains prompt/schema captures, original
role outputs and retained narration. Keep it outside public Git, issue uploads
and hosted evaluation services. It is Author evidence, not a player export.
No file path, raw prose, reviewer token or rationale is emitted by the summary.

## Review fields

The exact top-level fields are `version`, `scope`, `rubric`, `source`,
`reviewer`, `quality_accepted`, `entries` and `limitations`. Version is integer 1;
scope is `locallore_role_review`; rubric is `role-quality-v1`.

`source` contains the snapshot binding, report SHA256, original lane and
source-match status, total/selected turn counts and `first_n_report_rows`
sampling label. Each entry retains its turn, arm, selection flag, original
source row, selected capture/output envelopes and ordered assessments.

Only these declarations may change:

- `reviewer`: initially null; an anonymous 1–48 character ASCII token using
  letters, digits, underscore, hyphen or period. It is self-reported metadata,
  not verified human identity. A changed judgment or supplied rationale requires
  a non-null token.
- Each assessment's `judgments`: values are `satisfactory`, `concern` or
  `not_assessed`, initially all `not_assessed`.
- Each assessment's `rationale`: initially null; at most 1,024 UTF-8 bytes on
  one line, without control characters. It remains private.

| Role | Independent judgment dimensions |
| --- | --- |
| Director | `intent_fidelity`, `scope_attribution` |
| Narrator | `outcome_fidelity`, `player_agency`, `voice`, `readability`, `repetition_pacing`, `enjoyment` |

These subjective labels do not replace engine validation or source/observer
checks. A reader should judge intent against the retained original request and
Narrator grounding against approved outcomes, rather than asking prose to
resolve mechanics again. An agent-generated test rating is not a human result.

Partial reviews are valid. A rationale without any judgment requires a reviewer
but does not count as a reviewed attempt. Missing output creates no fabricated
assessment. All original failures, fallback/unknown states and unavailable rows
stay visible. The final fallback narration remains labelled as fallback; it
does not become a successfully generated Narrator sample. Scripted/fake and
native lanes keep their original separate labels.

## Validation and summary

`summarize` rebuilds the selected packet from the current retained source and
compares every immutable field. Changing source bindings, rows, hashes, prose,
attempt order, selection metadata or provenance is refused. JSON duplicate
keys are rejected recursively, including escaped duplicate names. Unknown
fields, incorrect types, Boolean counters, invalid judgments and oversized or
control-bearing declarations are refused. No model call repairs invalid review
data. Neither command writes comparison reports, checkpoints, recordings or
story databases.

The new summary uses scope `locallore_role_review_summary`. It reports full and
selected turn coverage, missing/unselected evidence, original outcomes and
per-role counts of declared judgments. It does not average unrelated dimensions
or publish a composite score. `quality_accepted` remains false for pending,
partial and fully declared reviews. Original protocol2 reports keep their
historical `human_reviewed=0`/`not_reviewed` fields; this sidecar does not rewrite
them or claim an owner decision.

The retained outputs came from integrated turns. They are not independent
Director-only or Narrator-only experiments: Director failure can prevent a
Narrator output. The report keeps that limitation and its denominator. Host
Qwen/llama.cpp evidence does not qualify Android Gemma/LiteRT, a physical phone,
model ranking or enjoyment. A hash proves a binding to retained bytes, not who
reviewed them or whether their subjective judgment is correct.

## Verification

The contract's original adversarial tests and the separate Store-backed CLI
tests are part of:

```text
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --all-features --all-targets -- --test-threads=1
```

Default tests use scripted providers and synthetic data. They cover the reader
boundary, real comparison files, unchanged source inventories, pending/partial
reviews, strict tamper/duplicate/type/role-order checks, create-only output,
inspection refusal and corrupt recording refusal. Platform-specific tests
must be reported for the platform actually executed. Test declarations do not
constitute a quality review.
