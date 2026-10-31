# Author packet A: proposed bounded code checks

Refs #25 D04.02, supporting D04.04 and shared #9. **Owner metadata decision
pending; no check admission or code child has run.** This is the execution plan
for the [frozen default-disabled Author contract](D04_AUTHOR_LANE_CONTRACT_2026-10-30.md).
It grants no application, model or worker-adoption execution.

## Prepared source

Independent FIRST `dc9ade7b` contains16 groups in two new files. Before any
baseline, its author corrected a private type path (`d8595d0`) and the timeout
fixture (`5197d89`). An unacknowledged blocked worker correctly reaches Cleanup;
the timeout test instead uses the existing completed-reply delay and retains its
Timeout/cache/retry/cleanup assertions. Original unrun sources remain in history.

Different-author extraction `0dc87b7a`, integrated at `d81fefe2`, registers the
tests and named private seams. It preserves old Play behavior and refuses every
Author frame, including synthetic Author dispatch until the behavioral phase.
Independent source review found no baseline blocker. **Uncompiled and unrun.**
Only after an actual compiled baseline and Root's raw-log review may the producer
implement the synthetic Author behavior. Production constructors remain disabled.

## Fixed phases and gates

1. Format exactly the five allocated Rust files. Root reviews and commits the
   formatting diff; those two FIRST hashes then remain fixed.
2. Build the existing `protocol-fixture` binary offline, without a model.
3. Run exactly16 Author test groups against the old behavior. Require executed
   cases, exit101 and behavioral failures; missing setup cannot count as RED.
4. After Root's baseline review and the separate behavior commit, run the same16.
5. Run the existing runtime unit suite, explicit formatting check, strict
   all-target/all-feature Clippy and normal desktop build.
6. After eligible merge, verify exact main/source identity and compile the normal
   desktop binary again, preserving its previous product. Leave it unlaunched.

The local, gitignored coordinator has a closed command list, one-use phase
admissions/START/PASS receipts, source/tool/product hashes, frozen FIRST, prepared
fixture identity and bounded lossless logs. Unknown closure, overflow, identity
change, unresolved phase or hard storage failure stops advancement. A forecast
miss is retained and requires review before additional commands. Root review is
separate from GitHub approval and execution authority.

## Storage decision

The previous whole-packet forecast was96KiB. The fixture baseline and initial
source candidates already consume42,585B. At that checkpoint logical metadata
was1,109,058B, leaving70,590B below the existing1,179,648B limit. The baseline
alone requires69,632B of conservative log/receipt reserve; the remaining958B
cannot hold the stage/admission and earlier phases. No command was attempted to
discover this refusal. Final source-review corrections add further bytes.

Propose **metadata1152 to1280KiB**, an additional128KiB, and revise the expected
whole-packet records to144KiB. Keep all other hard limits:

| Retained scope | Unchanged limit |
| --- | --- |
| Original target baseline8,259,980,576B plus4GiB | 12,554,947,872B total |
| Same evidence group | 64MiB |
| Joint evidence | 724MiB |
| Old code records, physical and decoded | 576KiB |
| New synthetic fixtures, including existing fork fixtures | 8MiB |

Current target is12,221,409,520B; expected cumulative additional code-build/copy
growth is128MiB. Reuse the existing exact normal-build preservation copy.
New retained fixtures are expected below1MiB plus the existing671,744B fork
fixtures. Pin the27 existing protocol/runtime fixture roots (27 files,0B) and
charge every newly retained root. All earlier evidence, failures and products
remain preserved. No deletion, target reset, new target or lowered log bound may
substitute for the decision.

The frozen contract states that existing ceilings "are not reset here." The
larger metadata value may be used only after an actual owner reply, recorded in
a separately hashed decision with the exact scope and unchanged other caps.
Without that decision the active1152KiB limit remains. Preparing a gated source
branch or a draft PR supplies no approval.

These are Rust/helper, synthetic process and compilation checks. They do not
qualify packaged C++ worker behavior, author inference, native IPC/rendering,
original-story UI, Android/device parity, OS/network isolation, story quality or
release. All four earlier native app grants remain spent.
