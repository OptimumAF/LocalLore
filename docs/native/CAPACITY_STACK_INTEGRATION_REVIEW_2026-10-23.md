# Capacity stack integration review, 2026-10-23

Refs #8 M04.04, dependency order #87 then #94. Reviewer
`/root/app_storage_review`; review claims
[#87 6370706948](https://github.com/OptimumAF/LocalLore/pull/87#issuecomment-6370706948),
[#94 6370707429](https://github.com/OptimumAF/LocalLore/pull/94#issuecomment-6370707429),
[#8 6370707895](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6370707895).

## Exact boundaries and independence

Integrated #87 source is `e1a88a25b50a40552e532ac46cfa24e6649f05a0`,
merging exact `540dff07e5e09019bd04bcc4ea5ad7dc32cacb1f` with accepted
`3485aa4a8137e2408d6cbcf067296fd98b108e98`. Main review checkout is separate
`source-capacity-stack-review`, branch `review/m04-capacity-stack`.
Exact #94 `37e83419771a6a363dce571ca041b11e1b7f2a4b` was read and its
synthetic Python tests executed in a NEW own detached `source-capacity-94-review`.
No dependent branch was merged by this reviewer, and the original author's
checkout, devices and processes were untouched.

The reviewer authored neither capacity packet, the fixed helper/profiles nor
their previous independent reviews. Prior authored Store/branch/cache work is
not being self-approved here. Only NEW `test_capacity_integration_review.py`
and this report were edited. Coordinator owns every existing source/fix,
integration, host capacity example and broad platform check. There is no score,
human acceptance or full M04/D08 completion claim.

## Source findings and limits

The #87 exact schema3/format2 profiles preserve measured Ready17, Full17 and
relief32, initial17/pad14/free15. The old15-page profile is not reinterpreted.
The separate package/output/cache guards bind these development fixtures and
reject accidental ordinary/release or conflicting-mode activation. A direct
diff from accepted3485 to e1 shows no changed production Core, Store or JNI
source under their `src` directories; Rust changes are capacity examples.

The Python helper constructs a reference from actual migrations001+002+003,
checks application/schema/migration/DELETE/page-size/auto-vacuum and owned
path/marker metadata read-only before RW, then rechecks before fixed owned-table
work. Removal validates the exact table declaration, row IDs, owner and payload
before DROP. It accepts no arbitrary SQL or executable payload. These are
trusted private fixture paths, not a same-user adversarial namespace guarantee.

Host helper ownership uses its exact spawned `Child`, bounded polling and
terminal `try_wait`/reap observations. File-output polling is an observed
threshold, not a hard filesystem quota. Fixed Python children do not launch
descendants; this is not a generic arbitrary-process-tree supervisor.
An unknown owner must suppress even readiness reads and follow-on cleanup.
#94's `cleanup_allowed`/short-circuit readiness and `failed_fill` paths preserve
that distinction. A known-reaped failure may attempt only freshly admitted
owned-table cleanup, and never resumes gameplay; primary failure and cleanup
failure remain separate. Normal same-key Full/accept/cancel controls are a
different proof from injected child failures.

#94 corrects two acknowledged #87 fixture gaps: post-RO ownership drift is
exit80 rather than a known prewrite refusal71..73; and native exchange rechecks
sticky ownership after its awaited hook, immediately before counting/dispatch.
The #87 evidence does not itself qualify these injected schedules.

Android source keeps aggregate reader failure, overflow, nonterminal ownership
and malformed completion poisoning. A post-termination IOException observation
does not clear the aggregate failure or permit dependent work. Existing owners
may close/drain; new owners, helpers, native calls, reopen, probes and deletion
are fenced after poison. The nested fault test rethrows unexpected assertion
or cleanup failures rather than swallowing them as the intended child failure.
Its root-retention counters describe intentionally skipped operations, not a
post-poison filesystem/canonical-state verification.

**Source-only concurrency concern sent to coordinator:** exact #94
`SqliteReliefFixture.released()` checks ownership only before the retry loop,
then can `delay(5)` and dispatch another `NativeWorkspace.open` without a new
check. A separate helper poisoning the same process during that suspension
could evade the entry check. The existing fresh-process fault tests call probes
after poison and cover entry refusal, not this in-flight schedule. No Kotlin
execution/reproduction is claimed. This requires coordinator disposition;
the demonstrated post-hook correction does not itself establish that stronger
concurrent-probe guarantee.

## Reviewer execution: synthetic only

Windows NT10.0.26300.0, actual task-local Python3.14.9, `-B`, fresh own D-drive
TEMP/TMP. No models/workers/assets, apps, devices, ADB, CUA, process enumeration,
unrelated process control, protected resources, settings, merge or release.
Only the fixed trusted Python helper was spawned by the new CLI tests.

```text
python.exe -B -m unittest discover -s scripts/tests -p test_*capacity*probe.py
integrated87/e1: 37 PASS
exact94/37e8341 separate own checkout: 47 PASS

python.exe -B -m unittest discover -s scripts/tests -p test_capacity_integration_review.py -v
integrated87/e1: 3 PASS
exact94/37e8341 + identical new review file: 3 PASS

git diff --check
PASS
```

The new independent tests are `49bf2fb19734a7de55ffd7c6768808791cd21dfc`.
They run the actual command-line entrypoint with fixed arguments, cap/parse
stdout, require empty stderr and assert no selected path/token/seed canary in
the public report. They check owned padding removal preserves control rows,
and unknown schema/foreign padding refusals leave all database bytes unchanged.
Their database is a synthetic schema/row fixture, not a native seeded Ready17
or actual Full32 state. No native recovery, actual fault, gameplay, partition
ENOSPC or process-ownership incident is inferred from these new cases.

The original reviewer attempt has three genuine test cleanup errors, retained
in `capacity-stack-review-cli-first.log`: Python's sqlite connection context
manager commits/rolls back but does not close the connection, leaving handles
alive at Windows temporary-directory cleanup. The reviewer fixture now uses
explicit `contextlib.closing` and autocommit, then all three pass. No helper
source, production gate, safety assertion or timeout was relaxed.

| Private task-local log | SHA256 |
| --- | --- |
| initial reviewer fixture cleanup errors | `0a7d8693405d959c6ee051e0d10ff79c842068409d8343143311781f87eb4799` |
| integrated87 existing37 guards | `b8ef8a11d7033557f4ec10b40971fb234f7c73c55e8f51222ee96909e6a67d23` |
| integrated87 new3 CLI | `d0c5d996401db6ac32d91453414245d7a2413e14c9d8e948e033b90febc5bf00` |
| exact94 existing47 guards | `790c7ed70ee8a6709a12988a25493ae24807463696a23492d12e8952c50394be` |
| exact94 identical new3 CLI | `c8f9b88bcbfbb1bfdc3a610b5bf2b27629e3bc23723477acc8eee6c1144a75ad` |

## Historical evidence and remaining qualification

Read prior schema3/helper-failure contracts, independent reviews and public
verification reports. #87's22 emulator invocations and #94's18 final passes,
their preserved RED/candidate/timeout failures, JVM/build/ABI evidence and host
fault reports remain attributed to the previous authors/reviewers. This reviewer
did not operate devices or re-audit their private raw artifacts. In particular,
Android malformed/oversize/timeout inject after RO before RW; AfterFill requires
actual fill/close. The host fault cases have a separate actual-fill/readiness
proof. They must not be collapsed into one claim that every Android fault
independently observed native Full.

Root's current integrated host examples, complete checks and any Android
build/JVM/ABI audit remain separate. Unknown/unreaped OS ownership is policy
coverage, not an actual unkillable-child incident. Parent death/lease expiry,
same-user OS attacks, physical disk exhaustion/power loss, phones/ARM64 execution,
models and performance remain unqualified. The17/32 ceilings do not prove
partition ENOSPC. Full M04/D08 and owner acceptance remain open.

## Source binding

The following are actual e1 checkout SHA256 values, including its checkout
line endings:

| File | SHA256 |
| --- | --- |
| `scripts/capacity_padding_probe.py` | `46d4bee19a2b30983e0c747e0af9d9701140e067f591257b8df5c4623b9f9c02` |
| `crates/locallore-workspace/examples/capacity_relief_probe.rs` | `401ed9665892f220064a9d773ecf11b68217a27286f46d63c8e7db58e3404cfb` |
| `SqlitePaddingProcess.kt` | `0b616631e9ea9594ac8954f9fce887910be36460caf976d4d7a4b137056f0cb8` |
| `SqliteReliefFixture.kt` | `ef9d3e81e9d9151ca5c21505e8ed2a193d0a4da3d1f09a5230af7ba9a0d09762` |
| `capacity-profile.properties` | `ccd225b75018093274b28b55e9042eab70c70a43ccf2df45e37ee5098765c98f` |
| `capacity-relief-profile.properties` | `581c9b7edc0b5462667bc98c598c4f90dd796fae4bae3eb6b2f3105a54124d52` |
| new review test | `c23776fcef22386bed3326f2d7c59d8fed520002f837959404b7d359e38fedef` |

Exact94 Git blob IDs bind canonical Git bytes independently of checkout newlines:

| File | Git blob |
| --- | --- |
| Python helper | `80a32ee1be32543dd2d6f160a0eca4998d222d19` |
| Rust relief example | `dfbc7f2934a6e1b1baeb91122ef3bb74b0cf2670` |
| Kotlin process helper | `b60618f19958ddf3011d4e3ba404f304b1d676f8` |
| Kotlin fixture | `d52d4455260a9078d74f45c64460483c6347ad2e` |

## Coordinator handoff for the suspended release-loop concern

The coordinator accepted this as a concrete source-derived concern and owns
any correction in the later #94 adoption. The smallest proposed change is a
fresh `ownershipClean.get() && PaddingOwner.ownershipKnown()` check inside
`repeat(4)`, immediately before `onDispatch()` and the actual
`NativeWorkspace.open`. The existing `finally` must continue closing all
already acquired handles even after poison. Preserve the four-handle bound,
eight-second timeout, five-millisecond retry delay, counters and assertions.
This is cooperative per-dispatch admission, not a claim that independent atomic
reads and a native call form an OS transaction.

No existing local JVM/native-double route exercises this actual release loop:
it is instrumentation-only capacityRelief source, directly invokes the fixed
external NativeWorkspace API, and the ordinary JVM tests contain no
SqliteReliefFixture/PaddingOwner/NativeWorkspace coverage. A copied loop or
source-pattern assertion would not qualify it. No new dependencies, visibility
changes, device execution or source edits were made here. Coordinator may
compile the narrow change and retain explicit unexecuted concurrent-suspension
qualification; this review does not claim the proposed correction is applied.
