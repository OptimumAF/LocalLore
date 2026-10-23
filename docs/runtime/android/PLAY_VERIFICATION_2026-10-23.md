# Current Rust play / Android SDK verification, 2026-10-23

Refs #5 (M01.03, bounded M01.02/M01.05), #9 (M05.05 preparation).
Base accepted main d5a76d2308a6863e49b3d088041d0eccadf8bb38 includes owner-merged
#70. No dependency on open Compose input PR #69. No production backend, gameplay
rule or store schema change. No real-model result is claimed.
See [protocol](PLAY_PROTOCOL.md), [profile](PLAY_PROFILE_V1.json),
[all attempts](PLAY_RESULTS_2026-10-23.json), [review](PLAY_REVIEW_2026-10-23.md).

## Actual checks

Opt-in JNI feeds original Rust director/narrator requests to SDK and returns
untrusted text. Rust owns validation/commit/original-key retry/strict reopen.
Java owns scheduling/SDK lifetime/reporting. Actual schema/model acceptance is
pending. Private logs: target/checks/android-play.

| Command | Result |
|---|---|
| `python scripts/check.py host --offline` | Final PASS:267 workspace Rust +3 linker +217 Python; fmt/Clippy/four fixture comparisons |
| `cargo +1.93.1 test -p locallore-android --features play-probe --locked --offline` | PASS:25 tests, seven new probe integration tests |
| `cargo +1.93.1 clippy --workspace --all-targets --all-features --locked --offline -- -D warnings` | PASS |
| `python benchmarks/spike/android/litert/play_build.py --java21 <existing-JDK21> --clean` | PASS:fresh ARM64/x86_64 native, SDK build/53 JVM/lint/analyzer/dependency/APK audits |
| `python scripts/check.py android --offline --clean` | PASS:production both-ABI build,38 JVM,lint0errors/1existing advisory,APK audit |
| `python benchmarks/spike/android/litert/build.py --java21 <existing-JDK21> --clean` | PASS:default SDK53 JVM/all audits, original two SDK libraries only |

Final default SDK command used cached dependencies but omitted --offline;
Android/Java tool downloads were disabled. Opt-in helper/host/production used
offline mode. Dependency pins did not change. Current official runtime/schema/
Maven/model/license sources are linked in the independent review.

Opt-in APK SHA256:62791103926363f3558389325db49c01b8b0addceacb3a4d6eb24e157c168f82.
Four native entries (SDK+Rust,two ABIs) pass zero-permission,16KiB ZIP/ELF audits.
Initial build predates helper's preserved-copy step; coordinator copied successful
APK and checked hash before ordinary builds. Helper now preserves automatically.
Export inspection:five experimental JNI methods in each optional ABI,zero in
both production ABIs. Cross-compilation/alignment is not ARM64 execution.

## All emulator attempts

Two authorized Android15/API35 x86_64/4KiB AVDs. Isolated SDK/cache absent before
install; exact new APK and prior package hashes checked. Existing Compose/test
and capacity-relief/test packages/data preserved. Both AVDs already running at
later relaunch authorization, so no additional restart needed.

Four actual missing-model JNI checks passed explicitly requested failure-path
assertions:two initial,two after private raw capture. Each admits one director,
fails model_missing,opens zero SDK Engines/Conversations,leaves revision/receipts
unchanged,reopens equal canon,drains native owner,confirms process/client cleanup,
removes only marked probe workspace. Initial two lack original raw protocol;
stdout contains aggregates. Latter two retain private raw and were independently
matched to journal results/metrics. Four cleanup observations,zero generations,
zero active SDK cancellation observations.

Local publisher model verified:2,588,147,712 bytes,
SHA256181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c.
No weights downloaded,device-copied or uploaded in this packet. Permission for
local copies into isolated caches remains pending; AVD relaunch is separate.

Corrections/failures retained:

- Source review found contradictory success reports/role-owner counts,weak named
  errors,incomplete native metadata binding,pending JNI exception allocation,
  unsafe parent close after child failure,ambient SQLite flags. Fixed before
  first execution; no executed red claimed. Initial controller/reviewer22passed.
- Weak cancellation regression passed due unrelated owner-count mismatch. Stronger
  consistent-count regression reproduced one failure:cancelled/Inventory/completed
  generation accepted. Parser now requires Cancelled errors,observed output and
  cancelled final generation. Final24passed, included in217Python.
- SDK test replaced Thread.isAlive immediately after executor termination with
  native-finished event/joined future/termination contract. Final53 JVM passed;
  no device failure inferred.

## Remaining gates

M01.03 partial/in review; no checkbox acceptance. Unchanged-schema/model acceptance,
gift,dialogue,invalid ability,second spend,streaming cancellation,fresh recovery
unrun. Next:on approved local provisioning,all cases on both AVDs with preserved
APK,retaining every attempt/rejection without relaxing schema/budgets/Rust checks.
M01.01 blocked on authorized available physical phone. M01.06 selection,ARM64/
16KiB OS execution,sustained memory/thermal/performance,arbitrary language/Unicode,
enjoyment unqualified. One model per turn is not a multi-turn warm session.
No merge,release or settings change.

After these checks, accepted main advanced to 2f4efc2 through #71/#72/#73.
The counts and APK above remain evidence for d5a76d2 plus this packet, not
that newer combined tree. Rebase/current-main compatibility verification is an
additional pending PR gate; the newer archive/lineage code was not rewritten
or substituted into the already measured artifact.

That compatibility gate was subsequently verified against the exact captured
a2bb663 + PR executable tree in the separate
[compatibility follow-up](PLAY_COMPAT_VERIFICATION_2026-10-23.md). Its new APK,
counts and two device observations remain separate from this original cohort.
Model-backed gates described above are still pending.
