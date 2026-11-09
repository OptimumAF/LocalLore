# SDK15 library/recovery host verification — 2026-11-02

Refs #14 (M10.02), supporting #13 (M09.02/M09.03/M09.06).
Supporting implementation is in review; full task criteria remain unchecked.
This adds the [fixed four-method profile](LIBRARY_UI_V1.md), with no Android
app, Rust engine, dependency, shared storage mechanism or resource-policy change.

## Source and actual checks

Physical source: `D:/Worktrees/locallore-record-actions-tests-v1`, branch
`impl/m10-library-ui-v1`. Final executable/test source is
`49abb334af21e06619ecbfb5e60ff2e547b1269d`; later publication edits are documentation
only. The PR stacks on open/unmerged recovery PR #347 at `c1835a51`, while its
separately frozen product dependency is open/unmerged PR #351 at `7ab4918f`.
No PR was merged by this work.

Windows, installed CPython 3.14.7 (64-bit), process-local `TEMP`/`TMP`/`TMPDIR`
all `D:/Dev/_Temp`. The installed Python executable remains in its supported C:
location; project source, temporary data and captures are on physical D:.
Each central cohort ran behind a stdin barrier after assignment to its owned
Windows job, with a 300-second ceiling and bounded raw capture. All reported
successful jobs exited zero with known cleanup, complete capture and unchanged
monitored benchmark/test/baseline bytes.

Private control root, abbreviated OUT below:
`D:/Dev/Experiments/LocalLore/2026-11-02-library-ui-harness-v1`.

| Actual command from the source directory | Result |
| --- | --- |
| `python -I -S -B OUT/run-checks-v1.py regressions regressions-v1` | 173 existing tests pass, 83.038 s; source `e32a45f1`, before adapter integration |
| `python -I -S -B OUT/run-checks-v2.py current current-v2` | 46 new tests pass, 154.337 s; final executable source `49abb334` |
| `python -I -S -B OUT/attest-build-v2.py` | Genuine fixed B80 byte replay, exclusive manifest publication and readback pass; 3,845 ms host job / 3,656 ms worker |
| AST parsing with Python 3.9 grammar | All 13 new Python modules/test files pass; syntax compatibility only |
| `git diff --check c1835a51` | Pass |

OUT denotes the full literal path above, not a shell environment variable.
Bounded drivers explicitly insert the physical checkout in isolated Python mode.
The public profile document also gives direct unittest commands.

The 46 new cases are build 12, profile 8, controller 8, activation 9 and recovered
storage 9. Earlier separate cohorts passed 45 before the added permission case;
they are not added to the final count. The legacy 173 were not rerun after the
SDK15-only permission correction; all their existing shared source/test files
remain unchanged. No Rust, Gradle, JVM, APK auditor or Android method was newly
executed by B81.

Final integrated raw stderr is 10,621 bytes,
SHA256 `ad452f74fb40f76e394b25a82b5b2e4a7a19341a2f5c723098f691e4f3c6d8da`.
Its ordinary unittest result is 46/0 failures/0 errors/0 skips. The tests use
real tiny binary/raw/JUnit/source/claim files and real isolated recovery journal,
RUN rebinding and closure transitions. Native, process/socket, SDK and build
ports are explicitly simulated where identified in the fixtures. Host test
success does not qualify those simulated ports on a real guest.

## Preserved failure and exact correction

The first unmocked build replay really failed `BuildRefused: audit`, despite
the initial synthetic tests passing. The reader and synthetic positive graph
incorrectly expected an empty product permission list. Original B80 raw output
and `audit_apk.py` instead require exactly the existing AndroidX signature
permission `org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`.

The correction requires that exact singleton and leaves test permission
`android.permission.REORDER_TASKS` unchanged. Four coherently rebound synthetic
graphs with missing, extra contacts, extra network or network-only permissions
reach and fail the audit guard. No permission, APK, raw audit, fixed baseline,
source pin, deadline, byte budget or native alias rule was broadened/resealed.

Original `genuine-build-replay-v1` remains failed, with complete host cleanup
and capture. Its 1,524-byte stderr has SHA256
`1f66c661f3beb05629917fa98df54d9352d167ae8ff68c73c697f1f34656c880`.
The first driver did not separately publish a pre-dispatch request; its source,
prior static source pins, raw traceback and terminal are retained without
inventing that missing record. The additive v2 driver records its request/source
pins before dispatch. An agent's intermediate driver draft also refused its
own path assertion before creating a child/test capture; the corrected v3
driver passed 12 focused tests. These helper drafts and original captures remain.

## Genuine frozen product gate

The final unmocked call sequence is `create_manifest()`, exclusive publication
at the fixed path, then `verify_frozen_product()` and equality with the original
value. No mock verdict is used. The baseline remains 29,083 bytes,
SHA256 `c39f35c45c1c43a1ae4ffa9e5b955b1b4f3300eec8fcdf6660a34e77107fa3f5`.
The validated manifest is 30,730 bytes,
SHA256 `496f6358a860c2f5ff8809610d0d2f83e93dd867fbfdfe5e6c4c551871058ad3`.
It binds 87 fixed evidence references and the exact four selectors/APK pair.

The real byte graph retains B80's six phase chains, four source archives,
550 JVM cases/67 XML suites, APK audit and native provenance records and recovery
copies. Those are recorded B80 results, not repeated B81 semantic execution.
Its original FIRST and failed whole Android compile remain failed; partial
JVM/product/older-test-APK results cannot qualify the final pair. B80's native
tasks were up to date; the historical compilation is attributed separately.
The 120-second/512-MiB reader limits and exact Cargo alias identities remain.

## Review and preservation

Independent source/file-evidence review found no concrete blocker, while
retaining the initial unmocked refusal and the exact permission correction.
This is a model-assisted review, not owner acceptance or Android qualification.

Additive copies under
`D:/Dev/Recovery/LocalLore/2026-11-02-library-ui-harness-v1` verify 79 source/copy
pairs: 14 executable/test/baseline files and 65 private control/raw/helper records,
1,040,980 bytes. `preservation-v1.json` is 44,097 bytes, SHA256
`5e9807f130e122d63f17481a7e1f87897f3cf0ce89a8adb507deda1f4821ee8a`;
its canonical recovery copy matches. The original failed replay is included.
Synthetic fixture trees remain in their original bounded D: location and are
not represented as full recovery copies. Existing B77/B80 frozen evidence and
recovery are retained separately and never overwritten. Publication documents
are preserved additively after final commit, outside this earlier code receipt.
No weights, saves, raw private diagnostics or recovery contents are uploaded.

## Remaining gates

SDK15 Android execution is **0/4 methods, unrun**. The older B77 nineteen-method
run remains **0/19**, blocked by its actual pre-intent host commit-capacity
refusal and spent one-attempt grant. This packet performs no recovery, real
ledger migration, SDK/ADB operation, emulator boot/stop, phone/model operation,
retirement, settings change, private upload or merge.

The production v1 ledger remains 41,230 bytes, SHA256
`4917ec696f7c9f9de5917838aafbd9c2d11184e17c8cbecd71f4eb66ae6a58c5`.
The original 40 GiB reservation is still charged and its guest/parent remain
absent. Original failed evidence, old model guest, other emulator and shared
ADB are outside this work's lifecycle actions. No new physical-device,
performance, model-quality, accessibility or process-death result is claimed.

Next runnable task: freeze the reviewed SDK15 source and prepare a new
source-bound guarded recovery/run proposal for the existing reservation and
this exact current APK pair/four selectors. The old Flow5907 plan and spent
SDK14 grants cannot be substituted. Actual migration/boot requires fresh exact
authority and successful current resource/storage/ownership checks. No task
checkbox or milestone is accepted by this host report.
