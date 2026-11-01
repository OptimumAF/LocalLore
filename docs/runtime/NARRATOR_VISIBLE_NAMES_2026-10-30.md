# Complete visible character names in narration

Refs #9 **M05.03**, supporting #14 **M10.04**. Implemented and locally
verified, **in review** in [PR #297](https://github.com/OptimumAF/LocalLore/pull/297).
Full task criteria, real-model quality and owner acceptance remain open.

## Problem and behavior

The engine allowed whole observer-visible character labels, but the conservative
prose check compared each capitalized word with that set. After an accepted Give
to actor ID `mira`, faithful prose using the display name `Sera Vale` therefore
fell back to mechanical narration. A hidden actor named `Vale` also incorrectly
made an occurrence inside that complete visible name look like a disclosure.

The validator now recognizes complete visible-label spans. Capitalized tokens
and overlapping hidden **display-name occurrences** are exempt only inside one
such span. Individual fragments do not become generally allowed vocabulary.
Hidden actor IDs keep priority, and the existing exact shared-label behavior
remains. Alphanumeric, underscore, hyphen and apostrophe continuations cannot
make an invented extended name into an approved span. Bounded ASCII and curly
possessives work. Original word/sentence positions are retained; folded Unicode
offsets never slice the original text.

The model still proposes prose; the engine validates and commits. Name matching
does not grant character knowledge or change world truth, canonical events,
receipt provenance, prompts, schemas, dependencies or cancellation boundaries.
Quotation, mechanical-effect, transferred-item and other existing guards remain.

## Executed verification

Windows host, Rust/Cargo **1.93.1**, locked/offline dependencies. All commands ran
from the physical D: source checkout with process-local TEMP/TMP/TMPDIR on D:,
the existing D: Cargo cache, a task-owned D: target, two build jobs and debug
information disabled. The finite owner allowed at most 1800 seconds and 262144
capture bytes per command; every listed owner completed with known cleanup and
capture and unchanged before/after source bindings. Owner times below are host
check intervals, not model or gameplay latency.

| Phase | Actual result | Owner interval |
|---|---|---:|
| Original eight regressions on unchanged production, `3375adfe` | 3 pass, **5 assertion failures**, command 101 | 17481 ms |
| Same eight, initial candidate `9b8e994f` production-file hash | 8 pass, command 0 | 4607 ms |
| Initial complete-core invocation without `host` | **Compilation failed**, E0432 in an existing host-only test; no test result | 8143 ms |
| Complete host-enabled core at `79e7cde0` | **553 pass**, 0 failures, 4 existing ignored; 66 aggregate binary summaries | 71426 ms |
| Storage/workspace/Android Rust host compatibility at `79e7cde0` | **517 pass**, 0 failures, 7 existing ignored; 81 aggregate binary summaries | 227645 ms |
| Initial strict Clippy at `79e7cde0` | **Failed** on the new test helper's cloned one-element slice | 15008 ms |
| Final ten named regressions at `1a1d3886` | **10 pass**, 0 failures/ignored/filtered | 3140 ms |
| Final workspace formatting at `1a1d3886` | Pass | 4561 ms |
| Final strict Clippy at `1a1d3886` | Pass, warnings denied | 6018 ms |

The full core command was:

```text
cargo +1.93.1 test -p locallore --features host --locked --offline --quiet
```

Compatibility used `cargo +1.93.1 test -p locallore-storage -p
locallore-workspace -p locallore-android --locked --offline --quiet`.
Final focused execution used `cargo +1.93.1 test -p locallore --test
narrator_visible_names --locked --offline -- --nocapture`. Formatting used
`cargo +1.93.1 fmt --all -- --check`; Clippy selected the same four crates,
`--features locallore/host --all-targets --locked --offline -- -D warnings`.

The 1070 broad passes are not a rerun at the final head: its only code delta
from the broad source is the test helper's `std::slice::from_ref(&receipt)`
idiom. Production SHA256 remains
`249bfab0d0824bd0c90724c672a1fca7c39d848e19bb374dfd8c742e8d4c2311`.
Final test SHA256 is
`d3cbf51d0919ccae201a548909f4e5b89523c74c0b4e99628f1a30117790c1ff`.
The report itself was added afterward; it changes no executable source.

The independent tests use real Engine/Play with recording synthetic inference.
They cover complete names, possessives, Unicode case expansion, same-name and
hidden component overlap, malformed boundaries, component occurrences elsewhere,
hidden IDs and cancellation. Resolved paths also check inventory, exact prose
or safe fallback, real restore/replay, idempotent retry and mismatched retry.
The original eight method/assertion blocks remain unchanged. Two additional
cases followed source review of apostrophe boundaries, not a measured old-model
failure or a sample-specific keyword change.

Independent static review found no remaining concrete blocker. A separate
closed-file audit checked all ten phase records, owners, raw counters, historical
source/helper bindings, final ten unique names and 2302 current source hashes.
It passed in 779 ms body / 868 ms outer, without tests, native calls, model
execution or device access. Receipt SHA256:
`1c91e02310af821aaa0f1f123bd9ac20f4f6c9cd47ba26388018e94b79075449`.
Quiet broad logs establish aggregate counts, not individual IDs for all 1070.
The first checker failed on CRLF/custom-panic parsing; that failure is retained.
Its corrected partial draft stayed unrun; the final audit ran once. Original
test, compile and lint failures are preserved separately, without relabeling.

## Storage overrun and remaining limits

**The declared 4 GiB packet budget failed.** A closeout observation measured
4523445697 logical bytes in the packet and 32286290 / 32283175 bytes in the two
source checkouts: **4588015162 bytes**, exceeding 4294967296 by **293047866**.
This is retained logical size, not a peak, physical allocation or global-cache
measurement. All build work stopped; targets, failures and originals remain.
The old cap was not retroactively raised. A separate metadata-only closeout
allowance is expected 4–8 MiB / maximum 16 MiB; no binary backup or full source
bundle is added. Committed source is pushed, and selected private controls have
recovery copies. This operational failure does not invalidate a recorded test
result or turn the storage criterion into a pass.

These finite lexical checks are not semantic entailment, complete Unicode name
normalization or universal privacy proof. A visible name containing a distinct
hidden actor ID can still be refused. No new NPC dialogue support is implied.
No model was run, and no historical fallback rate or enjoyment improvement was
measured. Android packaging, emulator/phone execution, ARM64, inference,
accessibility and release qualification are separate. This packet does not
repeat Python suites or qualify all workspace features such as desktop UI.

The existing emulator-image deletion proposal remains pending owner approval;
another boot also needs applicable approval and storage admission. No guest,
image, shared ledger, other emulator or system setting was changed, and no PR
was merged. Those lifecycle/device gates remain required.
