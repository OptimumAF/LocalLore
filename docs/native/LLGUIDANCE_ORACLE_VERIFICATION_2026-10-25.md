# LLGuidance host-oracle verification — 2026-10-25

Refs #9 (M05.01/M05.05), #5 (M01.05 supporting). Partial implementation is
**in review**; no milestone is completed or accepted by this report.

The isolated, pinned native compiler actually ran. All eight engine schemas
compiled,113 of114 expected positives were accepted, and all85 negatives were
rejected. The remaining escaped-dialogue positive is a reproducible byte-mask
counterexample. The ordinary post-gift425-byte schema passes. This result
does not establish the cause of the prior emulator's wrapper-declared
INTERNAL13, successful real Dialogue, or restart qualification.

## Source and scope

Branch `impl/m05-llguidance-oracle`, worktree
`D:/LocalLore-receipt-capacity-20261024`, stacked on unmerged #171 at
`3f20b5744a38b33e07c1d8990705ab900360b676`. Implementation through
`10fa7206` includes engine exporter `fc892f9e`, source research `89646b92`,
checker `d44d9bf3`, and root launcher/protocol/reductions. Later changes to this
report or independent review are documentation only.

The exporter uses real guarded `play::execute` requests and the unchanged
production dependency graph. Its fake provider captures only schema bytes and
then fails; no prompt is exported. Before the ordinary Dialogue capture, an
original scripted director/narrator gift is accepted by the real engine:
revision1, receipt1, potion owned by Mira, repairs0/fallbackfalse. Capture
preserves canonical bytes/revision/receipts. Crowd positives independently
enumerate every nonempty eligible set of size<=4 for one through six listeners.

The root Cargo change only registers the new example's tests with required
`host` feature. No production source, Cargo.lock, Android dependency, profile,
schema, generation cap, SDK contract, permission or database behavior changes.
LLGuidance is deliberately outside Cargo's graph to avoid its
`serde_json/preserve_order` feature changing the schemas being measured.

Claims on #9: root6400493037, launcher-test clarification6400576546,
reduction-fixture extension6400681227; exporter6400530845,
checker6400532685, research6400555516, independent review6400628071.
Agents used distinct worktrees and sole file ownership; the coordinator
reviewed and cherry-picked focused commits. Technical review is not owner
acceptance. Live plan/work-log evidence belongs in #3/#5/#9, not retired
Markdown trackers.

## Actual compatibility and provisioning

WindowsAMD64, CPython3.9.12, Rust1.93.1
`01f6ddf75` (2026-02-11). Official LLGuidance v1.3.0 source resolves
`29e33a219f77be1cc37d8394630440f448d19945`; the pinned LiteRT-LM source names
that version. See the [primary-source research](LLGUIDANCE_ORACLE_RESEARCH_2026-10-25.md)
for API and version/license boundaries.

The official code wheel was downloaded after checking published version,
Python/ABI/platform, MIT license and absence of mandatory distribution
dependencies. Actual download:2,789,946 bytes, SHA256
`1d1cd1c8618d1a13605d3e057c978651e551c8c469b481ee4041f1d6c436002d`.
All20 extracted files total7,596,764 bytes and match the verified ZIP members;
license retained. Provisioning was create-only, outside Git, without global
installation, dependency resolution or native import. Each actual run again
verified the exact wheel and extracted file set before native loading.

Runtime `C:/Users/Avery/LocalLore-llg-oracle-runtime-20261025`, original wheel
in `C:/Users/Avery/LocalLore-llg-oracle-wheel-20261025`. The native checker
verified module/distribution provenance and version, byte vocabulary262,
EOS261 and ordinary byte mapping. Byte255 is a reserved test special marker
and never appears in valid UTF8 input. No model, tokenizer file, SDK, network
inference or device operation was performed in this packet.

## Commands and results actually observed

All long test/native jobs used the existing process owner. A trusted worker
waited for stdin until Windows job assignment, and cleanup completed for every
recorded job. Parent `exec` sessions81895,47076,78962,42950,19736 were consumed
to terminal; quiet output did not trigger duplicate runs. The native runner's
exit1 below is an observed compatibility mismatch, not a crashed/abandoned job.

| Actual check | Result | Preserved evidence |
|---|---|---|
| Owned `cargo +1.93.1 test --frozen --offline -p locallore --features host --all-targets --target-dir C:/Users/Avery/LocalLore-llg-oracle-checks-20261025/target` |359 passed,0 failed,4 historical capture-only ignores,49 suites; includes8 new exporter tests;85.188s/exit0/known cleanup |checks root `rust-test.stdout`, `rust-test.json` |
| Owned same target `cargo +1.93.1 clippy --frozen --offline -p locallore --features host --all-targets … -- -D warnings` |exit0/known cleanup,7.688s |`clippy.stdout`, `clippy.json` |
| `cargo +1.93.1 fmt --all -- --check`; `git diff --check` |both exit0 |tool transcript |
| `python -B -m unittest scripts.tests.test_llguidance_launcher scripts.tests.test_llguidance_oracle -v`, then frozen-source owned replay |32 passed,0 failures/errors/skips; final runner0.340s, owner0.593s/exit0/known cleanup |`targeted-final.stdout`, `targeted-final.json` |
| Owned `unittest.defaultTestLoader.discover('scripts/tests')` with `TextTestRunner` |853 passed,0 failures/errors/skips;68.421s/exit0/known cleanup |`python-tests-final.stdout`, `python-tests-final.json` |
| Earlier whole Python replay before final two reduction tests |851 passed,70.047s/exit0/known cleanup; retained, superseded for final count |`python-tests.stdout`, `python-tests.json` |
| `python -I -S -B scripts/llguidance_oracle.py run --runtime C:/Users/Avery/LocalLore-llg-oracle-runtime-20261025 --output C:/Users/Avery/LocalLore-llg-oracle-final-20261025` |8 schemas compiled;199 samples;113 positive accepts/85 negative rejects/1 positive mismatch; top-level exit1 |final engine root `corpus.json`, `oracle.json`, `run.json` |
| Same launcher `reduce` with output `C:/Users/Avery/LocalLore-llg-oracle-reduction-final-20261025` |16 schemas/40 samples;14 positive accepts/24 negative rejects/2 positive mismatches; exit1 |final reduction root same3 files |

The checks root is `C:/Users/Avery/LocalLore-llg-oracle-checks-20261025`.
Full-suite expected adversarial fixture output includes refused authorization
and APK-audit errors; the unittest result is853 tests/zero failures/errors,
not an APK build or device execution. Pure Python seams construct no actual
native backend; only the two explicitly labeled native runs establish compiler
observations. No Android rebuild/emulator test was needed or claimed for this
host/example-only packet.

Final engine stages: build15.438s/exit0/stderr974B, export1.156s/exit0,
native check1.578s/exit1/stderr0. Every stage `completed`,
`cleanup_complete=true`. Corpus35,143 bytes SHA256
`1207cb0ca36f16e78c74cb50770390008ab0a6fe0fcc1de68eab5a2b7dc495f8`;
report32,539 bytes SHA256
`c5ab7010e9c907c95efabace35568dca68f873c78cab2bb2c65e6eaba9252dce`.
All five native controls pass: valid schema compile/complete EOS, illegal byte
rejection, incomplete-prefix rejection, unsupported uniqueItems compile refusal.
Provider-free engine refusals remain no listeners→ClarificationRequired,
crowd128/context512→TooLarge, each zero calls/unchanged canon.

Final reduction check0.407s/exit1/stderr0/known cleanup. Corpus7,534 bytes SHA256
`5385c27ddb9eeb5525dcbf2faa06e05df9fa9ce83d82c43c61691713da757e97`;
report8,532 bytes SHA256
`757625b444d7c928deb916450fb585aabca49ca7544ed765d94f4d7d580d01ef`.
The frozen launcher source SHA256 is
`9f464e6f2c18bdfeaae77ccdcb34f3e7c4222d571ccae0a5e5812c14c9c95c57`;
checker `528feae94cadc7637dca030b8ada3970f5f56b71aa034af3d32ab1c1ff888bc4`;
exporter `beeecb9776251dec2f1f97250b833f5ede10a5cf1dd9e8091943954afaf7bfd8`.
Each final run records these and Cargo.lock/example-manifest/reduction hashes.

## Counterexample and limits

The original `escaped-dialogue` literal (quoted Mira, one backslash, snow
character, newline and tideglass question) remains a positive. Decoding the original candidate
and captured schema const produces exactly equal text. Native byte-mask
rejection occurs at offset65/103, the backslash introducing the closing quote
escape, before the Unicode/newline bytes. A minimal string-only const carrying
the same text also rejects at the corresponding offset13/48. Therefore the
surrounding engine schema is unnecessary to reproduce this admitted byte-path
failure. No production schema was rewritten to make it pass.

Plain text, a quote alone, one/two quotes, one/two backslashes, newline alone,
Unicode alone, the quote-pair prefix, and all five shorter quote-pair tail
interactions (backslash, Unicode, newline, double slash, slash+newline) pass.
The longer combined literal still fails. This does not yet identify whether
the native string compiler, lexical/matcher path or another byte-backend
interaction is responsible. Upstream source explicitly supports quote/string
escapes; this is distinct from its documented fixed property order and outer
whitespace restrictions.

Earlier first native engine run and11-case reduction are preserved in
`LocalLore-llg-oracle-host-20261025` and
`LocalLore-llg-oracle-reduction-20261025`. They are not overwritten; first
engine corpus/report hashes equal the final run. Initial provisioning checks
found the wheel license begins with indentation and Windows ZipInfo normalizes
backslashes: guards/tests were corrected before any native run. Independent
review also found minimal checker reports could qualify and argument errors
could echo caller data; strict report/corpus binding and closed argument
errors were implemented and regression-tested before the final replay.

A selected-file index (not a claim about build/cache trees) retains22 explicit
evidence files/211,298 bytes, excluding its own4,374 bytes:
`C:/Users/Avery/LocalLore-llg-oracle-evidence-index-20261025.json`, SHA256
`f0fe2f97d3172c2436b5a0d2416f8851034e48a29c6754a41ff55cb281da55dc`.
Build targets and exact verified code runtime/wheel are preserved separately.
No old sealed receipt evidence, model/cache/VM disks or private story data was
read, rehashed, moved, deleted or uploaded by this packet.

See the [independent source/result review](LLGUIDANCE_ORACLE_REVIEW_2026-10-25.md)
for its separate claims, evidence replay and corrected findings.

## Handoff and task status

M05.01/M05.05/M01.05: this host-oracle slice is implemented/tested/in review;
full criteria stay unchecked. Physical M01.01 remains blocked on an accessible
authorized reference phone. ARM64/16KiB execution, real Dialogue/restart,
NPC secrecy/quality, sustained/thermal/latency and broader device/privacy
qualification remain open. #171's56/122-check receipt outcome is historical
and unchanged; this packet adds no real-model or emulator success.

Next runnable task: minimize the longer escaped-literal interaction further
and independently compare the pinned native compiler/matcher paths before
choosing a narrow compatibility fix. Keep the original positive and
deterministic oracle. Separately, the ordinary425-byte schema's successful
byte acceptance does not qualify the real Gemma tokenizer or diagnose its
SDK/JNI INTERNAL13; another SDK attempt needs an evidence-backed hypothesis
and the existing admission/ownership gates. No merge, release, access change,
model download/upload, cloud fallback or mechanical-authority change.
