# Android play compatibility follow-up, 2026-10-23

Refs #5 (M01.03, bounded M01.02/M01.05) and #9 (M05.05 preparation), draft
PR #75. This follow-up tests the optional SDK bridge with the newer accepted
archive, lineage and desktop-worker changes. It preserves the earlier
[D5 results](PLAY_VERIFICATION_2026-10-23.md) as a distinct source cohort.

## Exact source under test

The initial checkout was GitHub's immutable PR test-merge commit
`b3eb20baa0f40c4550c3804381f0f49351c561c4`, with parents accepted main
`2f4efc29e989823a4cf6abf35e2a42fcfc8ee218` and PR head
`dbc2d6973feac00aa744243999fe259df5d944fb`.

During preflight, accepted main advanced to
`a2bb6639eacaa9ac416788caf2fc7a6b70bf1392` through owner-merged #74.
After the initial host run completed, the coordinator cherry-picked only that
accepted commit's net delta into the isolated verification branch. Result:
`e7beb858b271aa4636f2f5e7b34deedda1fc3f21`, a single-parent commit on b3.
Its inherited message starts with "Merge #74"; the operation created no merge
commit and did not merge a PR, alter main, rewrite history or force-push.
The source is preserved on `verify/m01-play-compat` for reproducible checks;
the implementation PR keeps its original feature branch and history.

The exact resulting tree is
`71f155de92b4fc73c9ae916f4d1c60ac330648e6`. An independent temporary index
computed the conflict-free three-way union of original base D5, accepted a2
and PR head dbc using `git read-tree -m` and `git write-tree`; the tree matches
exactly. The working index was unchanged. Installed Git 2.33 lacks the newer
`merge-tree --write-tree` option; that rejected capability probe did not run
tests or change source. The reviewer independently compared the full binary
diff b3→e7 with accepted main 2f→a2 and found them identical.

No production backend, dependency pin, gameplay rule, schema or shared API was
changed by this follow-up. Later PR commits adding only these evidence files do
not change executable source. The captured a2 tree is the verification target;
this report does not promise compatibility with future main commits.

## Checks and evidence

Initial b3 full offline host check completed successfully: **288 workspace Rust
+ 3 linker + 217 Python tests**, fmt/Clippy and four fixture comparisons. It
ran before the accepted #74 delta was added and remains separately retained.

All final e7 commands completed successfully, with private logs isolated from
the earlier D5 cohort. The initial b3 run and final e7 run are separate checks.

| Command | Actual result |
|---|---|
| `python scripts/check.py host --offline` | 288 workspace Rust + 3 linker + 217 Python; fmt, Clippy and four fixture comparisons passed |
| `cargo +1.93.1 test -p locallore-android --features play-probe --locked --offline` | 25 tests passed (suite counts 4/8/4/2/7) |
| `cargo +1.93.1 clippy --workspace --all-targets --all-features --locked --offline -- -D warnings` | Passed |
| `python benchmarks/spike/android/litert/play_build.py --java21 <existing-JDK21> --clean` | Fresh release libraries for both ABIs; SDK assembly, 53 JVM tests, lint/analyzer/dependency/APK audits passed |
| `python scripts/check.py android --offline --clean` | Fresh default JNI for both ABIs, production assembly/test APK, 38 JVM tests, lint and APK audit passed |

All JVM tests have zero failures, errors and skips. SDK lint has two existing
warnings (OldTargetApi, GradleDependency); production lint has one existing
GradleDependency warning and no errors. SDK Gradle executed 50 of 51 tasks;
production executed 78 of 79. No failing attempt or rerun occurred in this
compatibility sequence. Tests do not establish model or physical-device gates.

The frozen e7 SDK APK is 62,187,164 bytes, SHA256
`715a6c4521592256b1ee6e1bf9ec4d0f3f1974dcdde040781269163efbc534a6`.
It contains exactly four native entries: LiteRT and Rust for ARM64/x86_64.
All native ELF LOAD segments and APK ZIP alignment pass 16 KiB checks; the APK
requests no permissions. The source-built unstripped Rust hashes and AGP-stripped
packaged Rust hashes are recorded separately in the linked results. They are
different build stages, not contradictory artifact identities. The SDK APK
remained unchanged after production verification. The production app was built
only; it was not installed over the existing Compose app.

## Model and device limits

Both selected AVDs passed actual boot/API35/x86_64/4KiB preflight. Each isolated
SDK installation verified the old D5 APK and new e7 APK identities, stopped only
the owned SDK process and used replacement installation without clearing data.
Prior Compose app/test and capacity-relief app/test hashes were verified before
and after. No unrelated target or package was mutated.

One new missing-model gift probe ran on each AVD using the e7 controller/APK.
Both passed the explicitly requested failure-path assertions: one admitted
director request, model_missing, zero initialized SDK owners, unchanged canonical
revision/receipts, strict reopen equality, native owner drain, process/client
absence and exact marked-workspace removal. Both privately retained raw protocol;
the reviewer independently matched every result and projected SDK metric to
the journals. These two observations supplement, and never replace, the four
D5 observations. No SDK model initialization or active cancellation was observed.

See the sanitized [compatibility results](PLAY_COMPAT_RESULTS_2026-10-23.json)
and [independent review](PLAY_COMPAT_REVIEW_2026-10-23.md). Raw data and APKs stay
outside Git. Workspace-retained is the SDK handoff stage; workspace-removed is
the later controller cleanup stage.

The separate local model-copy permission remains pending. No model is downloaded,
copied to a device or uploaded by this follow-up. Missing-model cleanup cannot
qualify initialized SDK ownership, constrained generation or active streaming
cancellation. M01.03 remains partial; M01.01 physical-phone availability and
M01.06 production selection remain open. Task checkboxes are unchanged.
