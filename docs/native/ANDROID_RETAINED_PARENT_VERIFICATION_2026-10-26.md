# Retained-parent implementation and interrupted verification

Date: 2026-10-26. Supporting M10.02/M08.05/M08.01, M05.05 and M09.03.
Base: open, unmerged PR #200 at `65c07ba2`. Implementation: `8049ce3d`.
This is an incomplete verification packet, not a passed lifecycle gate.

## Implemented contract

The [frozen protocol](ANDROID_RETAINED_PARENT_PROTOCOL.md) adds
`restore_retained_parent` to the scripted Compose/JNI/Rust controller.
The root cannot be individually retired. The case creates a nonroot parent P
and grandchild G, accepts an original prefix before G's fork and a distinct
tail afterwards, and saves an unsent parent draft. Native retirement should
retain P's required prefix for G while removing P from public admission.
Two actual saved-task process deaths must verify fallback, one visible notice,
draft clearing and no automatic turn. G must retain original inherited receipts
without acquiring the later parent tail. This complete case has not run.

The new worker uses typed archive preparation and a one-use commit intent,
not SQL or another gameplay authority. Four bounded, create-only sidecars compare
eligible player and receipt views before and after probe/retirement; these are
not a full-world proof. Independent raw native handles close synchronously.
New component tests fence stale parent Ready sessions while a retained child
Ready session commits exactly once. Adapter close requests remain asynchronous
and do not establish a joined drain.

Independent authors worked in separate worktrees with these owned paths:

| Author commit / integrated commit | Owned source |
|---|---|
| `facf3541` / `60aa9125` | `RetainedParentFallbackNativeTest.kt` |
| `23b9600f` / `4e501827` | `RetiredSelectionFixtureMain.java`, new `RetainedParentFixtureWorker.java`, new `RetainedParentFixtureInstrumentedTest.kt` |
| `e8b4edf2` / `8049ce3d` | `ProcessRestoreInstrumentation.java` |

The coordinator owns protocol `37e27e96`, integration and execution.
Independent source reviews found no concrete blocker; reviews alone do not
qualify runtime behavior. No production engine, schema, JNI, dependency, model
or inference-backend change is introduced.

## Executions observed before evidence loss

These terminal results were observed and reported in
[the progress comment](https://github.com/OptimumAF/LocalLore/issues/14#issuecomment-6415993753).
Their original private build-owner/source maps and raw result folders are now
missing. Historical observations are not a retained verification seal:

| Execution | Observed result | Current qualification |
|---|---|---|
| Baseline Android build | Exit0, 139,774ms; 523 inputs unchanged | Original ownership/evidence records missing |
| Integrated clean-controller build | Exit0, 23,800ms; 125 tasks, 45 executed/80 up-to-date; 523 inputs unchanged | Original ownership/evidence records missing |
| APK/signature/manifest checks | 11 commands passed | Original audit folder missing |
| Legacy and new native load/refusal instrumentation | 8 methods passed; 74 SDK clients completed cleanly | Original instrumentation/SDK records missing; no mutation proof |
| `cargo test --locked --offline -p locallore-storage --test branch_retention -- --test-threads=2` | 7 passed, 0 failed/ignored; test time10.61s, owner49,822ms | Original host result folder missing |

The integrated build reused existing 234 JVM results as up-to-date; it did not
rerun those tests. Loader methods do not prove retained-parent retirement,
process restoration or the two new native component methods. The Rust suite
concerns full Store state/receipt/history preservation; mobile sidecars concern
only eligible player and receipt views.

The next host step failed because its generated root-control driver was absent.
The root control, broad Android regression, new native component methods and
retained-parent two-death case did **not** run. Expected counts or source
assertions must not be substituted for executions.

## Preservation and ownership interruption

During inspection, generated driver scripts, owner/launcher manifests, frozen
host helpers and result directories disappeared. Earlier private evidence,
including PR #200's selected index, was also absent at its recorded path.
The owner confirmed another cleanup might be active and requested prompt
preservation and commits. The cleanup mechanism and actor were not independently
established. Missing records were not recreated or relabeled as original proof.

Integrated source was committed and pushed. A separately verified Git bundle
preserves the branch's four commits relative to `65c07ba2`; it requires that base.
Surviving files were copied into a separate private Documents evidence directory:
two driver sources, four explicitly partial live-output files, three APKs and
31 build reports. A recovery inventory describes those copies as recovered
products without original build-owner attribution. It does not replace missing
run records. No private logs, device identities, APKs, databases, caches or
model weights are committed or uploaded. Independent bounded inspection of the
helper author's worktree found no surviving current build/load/host receipts.

The new private recovery index covers 51 files / 27,478,286 bytes, SHA-256
`1ac5c5b26c441e0d508ddf580a6706158d117a215bf2abdc8d6e594a1fc30b8f`.
Its files are independently hashed; it describes recovery-time availability,
not the missing original run. No model, database or guest image is included.

The affected LocalLore execution session was interrupted after its ownership
files disappeared. Subsequent inspection found the exact previously observed
supervisor, worker, emulator launcher and guest PIDs absent. Both unrelated
emulator launchers were observed still alive. No successful owner closure
receipt, complete final capture or guest flush is claimed for this run.
The original two untracked physical-model build/cache directories remain.

Recovered APK bytes, measured after interruption:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Product | 24,555,355 | `ab1030cdbe7cc05833213f0f1064563fcf7893164961f93824927e89a9bc5fc4` |
| Instrumentation | 2,752,699 | `997f0ece760ddb5af9497b2d6d529f87292786098d9118b98660eaa2baaa507a` |
| Controller | 53,113 | `90bd8030963748ee6a98e783793e4f0588f9a131c01c05f90f4f6fe7fecb7499` |

These identify recovered files, not a lost original source map. They do not
permit adoption of a partial device fixture.

## Fresh retained checks and next execution

After preservation, this command actually ran against unchanged audit sources,
with new raw outputs retained in the private recovery directory:

```powershell
python -B -m unittest scripts.tests.test_audit_apk scripts.tests.test_audit_process_controller
```

Result: **53 passed**, 0 failures/errors, 2.408s test time (2,786ms host elapsed).
These synthetic host audit regressions do not execute Android or qualify the
new lifecycle case. `git diff --check` and private bundle verification also pass.
Read-only ADB enumeration against the existing unchanged server returned only
SDK emulator models, including TCP aliases. A non-emulator serial name does not
establish a physical phone; none was established by this observation.

Next runnable task: protect source/evidence locations from concurrent cleanup,
restore a versioned host driver from reviewed repository source, then use a new
owned cohort to rebuild/audit and rerun loader, root and native component gates
before executing the frozen retained-parent case and broad regression. Run
affected active-child and retired-leaf controls against the same final artifacts.
Preserve failures; do not adopt or retry a partially mutated fixture.

No full task is checked or accepted. Physical-phone/ARM64 and real-model
performance/quality gates remain separate and unqualified. No memory admission
threshold was changed or repeatedly sampled. No model transfer, phone benchmark,
system-setting change, merge or release occurred in this packet.
