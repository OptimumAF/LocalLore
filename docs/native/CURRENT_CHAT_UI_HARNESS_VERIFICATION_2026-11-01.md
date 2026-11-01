# Current-chat SDK11 host verification — 2026-11-01

Refs #14 (M10.02), supporting #13 (M09.03/M09.05/M09.06). In review; full criteria
remain unchecked. See the [fixed protocol](../runtime/android/CURRENT_CHAT_UI_SDK11_CONTRACT_2026-11-01.md).
This packet creates the new profile/owner/client/verifier, immutable B55 build
guard, controller/activation and original host fixtures. No product code,
dependency, APK, model or runtime toolchain was changed or rebuilt.

## Separate implementation and integration

Three writers used separate D: worktrees/branches with explicit file ownership:
profile in LocalLore-control-review, build guard in LocalLore-spike-review,
controller/activation in LocalLore-check-runner. Old branches/source ZIPs and
all 101 preexisting ignored files were preserved. Root integrated selected
commits centrally after closure and owns the retirement protocol addition/docs.
Frozen PR #317/#318/#319/#320/#322/#323/#325/#326 worktrees stay unchanged.

Host commands use installed Python3.14 with `-I -S -B`, physical D: working
directories and process-local TEMP/TMP/TMPDIR at `D:/Dev/_Temp`. Private runners
and finite parents retain raw streams, results and source hashes. Synthetic
SDK/owner/Windows/build seams are explicit; real SDK, socket and native-library
operations are trapped inside test execution. Parent supervision is reported
only within each capture's actual scope, not as a blanket Windows Job proof.

## Actual checks, separately attributed

There is no single fresh combined 63-test GREEN run. These are distinct observed
cohorts with unchanged relevant production bytes:

| Cohort | Actual result | Evidence and scope |
| --- | --- | --- |
| Profile | 14 PASS,0F/E/S;2.055s suite | SDK11 contract/types, byte-backed metadata, one-shot claims and shared proof replay; prohibited calls0 |
| Build guard final | 20 PASS,0F/E/S;12.255s suite | Real source/ZIP/XML/DEX/ELF/manifest validators over tiny coherent graphs; original negative assertions retained |
| Controller FIRST | 10 PASS | Actual SDK11 binary/proof/JUnit/claim replay with controlled build/native seams; part of the original23-method run |
| Activation FIRST | 12 PASS,1 assertion failure,0E/S | Combined23 run takes127.224s; failure is fixture aliasing, not demonstrated product behavior |
| Corrected activation only | 13 PASS,0F/E/S;1.219s suite | One helper deepcopy; all23 original test-method ASTs/assertions and production leaves unchanged; controller not rerun |
| SDK11 closure metadata FIRST | 6 run,2 assertion failures,0E/S;2.464s | Exact new protocol is not yet supported; four negative controls pass |
| Same closure tests after whitelist | 6 PASS,0F/E/S;2.421s | Same5160-byte oracle, SHAa0300a98…; no native/image/registry action |
| Legacy SDK8/9/10 closure checks | 11 PASS,0F/E/S;5.129s | Existing metadata checks after the one exact protocol addition |

Thus **63 distinct new methods have passing evidence across their stated
cohorts**, plus11 existing checks. Counts are not added to B55's428 JVM tests
and do not represent Android execution. Source maps and original outputs remain.

## Failures and corrections retained

The first genuine B55 guard replay refuses Cargo release cdylib nlink2 in4.356s.
Only the exact release/deps pairs have two links; generated/merged/stripped and
all generic roles remain single-link. A permissive intermediate positive-link
draft is rejected by independent review. Its16 passing synthetic tests do not
qualify that draft. The final explicit-role implementation checks exact paths,
two links, held identity/hash and final stamps. New foreign/third/missing alias
and generic-role negatives pass. Nothing was unlinked, copied or rebuilt to
evade the boundary. Original strict source/failure are retained; the original
15-test source recovered from the append-only draft matches its first recorded
SHA and is labeled as recovered.

The activation failure comes from fixture `running.owner` sharing the same
dictionary as expected actual owner. Mutating the recorded identity also changed
the expected identity, so production correctly observed equality. Commit78558dab
deep-copies that fixture value. Assertions and all23 test-method ASTs remain;
only activation13 is rerun. This does not claim a product identity bug was fixed.

An unexecuted private source formatter's stale-index SyntaxError and Root's
integration audit setup have retained corrections. On Windows the Popen audit event carries a framed
command string; Root's first guard wrongly treated it as an argv list and
refused before dispatch. The corrected private runner checks the original argv
and the exact Windows framing. No production boundary or old result was relaxed.

## Resource failures remain failures

| Observed point | Result |
| --- | --- |
| Build fixture meter | 24,951,495B exceeds original16MiB by8,174,279B: FAILED |
| Combined controller/activation postflight | 74,128,970B exceeds amended64MiB by7,020,106B: FAILED |
| Corrected activation13 only | Aggregate74,391,277B below explicitly amended80MiB |
| After Root metadata/legacy checks | Aggregate75,700,883B below80MiB83,886,080B |

Both failed caps and all original graphs remain. The first underestimates
duplicated complete build graphs. The second underestimates binary controller
proof graphs; the midrun observation was belowcap but later growth was not
enforced. No cleanup or cap reset repairs either outcome.

Root records each budget change on #14 before further runs. Remaining execution
is limited to activation-only and small metadata checks; no repeat of the large
controller/build cohorts. Controls remain below64MiB, selected recovery below
128MiB. These are host-fixture limits; shared emulator ledger limits never change.

## Genuine B55 replay and source/API integration

The final guard validates actual B55 evidence in10.253s in the writer checkout:
six fixed read-only Git queries,2540 executed inputs/2541 final source files,
428 unique JVM cases/50 XML,8 selectors, native joins/DEX/audits and current
Cargo aliases. No SDK, socket or native-library execution occurs.

Root then runs the integrated genuine creator in10.337s and the actual
`verify_frozen_product` in10.346s, with14 fixed read-only Git queries total,
23 actual source bindings, matching owner/client classes and eight contract
rows. The immutable fixed manifest is published create-only; no admission is
manufactured. Published manifest415,680B has SHA-256
`c21cc05f6a687605ad7d3f8e1e66d90ff9e96c504844f7e53a6268e4b8ab1c6b`.

Independent readback finds exactly three semantic path-role changes from the
writer's private validated data: launcher paths for instrumentation evidence,
audit_apk and audit_physical_model_apk relocate Spike-review→Control-review.
Their byte/hash pins and every other JSON value match. This is not described
as formatting-only identity. Product remains8d66 with executedfcf92; historical
supervisor/inner-raw/tool-byte limitations remain explicit.

Prospective guest, runtime and run-controls directories remain absent before
and after integration. Source bytes stay stable. Actual caller/proof/cleanup
and a real closed ledger entry still require an authorized run; no host fixture
or manifest grants that authority.

## Review, preservation and next step

Independent source review covers the profile, fixed graph, exact Cargo exception,
controller/activation, post-cleanup same-binding replay and Root's whitelist/test.
No concrete final source blocker is found. Reviewers preserve separate reported
cohort attribution and do not promote it into a fresh full-suite or device pass.
Integration evidence/manifest/source bindings are independently read back without
new product validation, tests or runtime calls.

Controls/old archives remain at
`D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-harness-v1` (64MiB).
All synthetic graphs remain at
`D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-host-fixtures-v1` (amended80MiB).
Selected source/evidence recovery is at
`D:/Dev/Recovery/LocalLore/2026-11-01-current-chat-harness-v1` (128MiB), with final
seals in ticket handoff. Existing ignored data and failed captures stay intact.

No actual guest, ledger mutation/lock/plan/reservation, authorization/input,
preparation/boot/retirement, SDK/ADB/phone/device/port/process census, model,
system-setting, unrelated-emulator/shared-service, approval request or merge
operation occurred. Storage code is byte-identical; only one new retirement
closure-protocol literal is added to existing code. Original SDK10 helpers,
proofs, proposal and frozen APKs are untouched.

All eight Android methods remain unrun. Next runnable host step: prepare and
review a fresh exact capacity/evidence proposal for SDK11 through the existing
shared guard. Its eventual device execution needs applicable exact approval;
the older pending SDK10 six-method operation is a separate alternative.
