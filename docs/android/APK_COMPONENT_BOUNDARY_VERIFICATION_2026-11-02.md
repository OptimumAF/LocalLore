# Compiled debug APK component boundary

B100, 2026-11-02. Refs #14 (M10.03; supporting M10.02 host regressions).
Implemented and locally verified for review; full task/privacy/release gates
remain unchecked. No app manifest, permissions, dependency, model or runtime
change, device action or merge.

## Observed gap and behavior

The MAIN debug APK CLI already checked badging permissions, SDK, backup resource
linkage/rules, native packaging and services. Ordinary profiles did not check
the complete activity/provider/receiver/alias roster. Provisioning activity
validation filtered only classes under `org.locallore.app.`. Synthetic foreign
components could therefore pass; this was an artifact-admission gap, not an
observed installed-app data leak.

`audit_app_components` now uses the existing bounded, ownership-preserving AAPT
parser. It requires the exact reviewed class set across all namespaces, direct
application ownership, framework attribute URI and numeric IDs, typed exports,
and complete child/filter sets. Aliases, unknown/private extra components,
misplaced declarations, URI-grant/path-permission additions, unreviewed process/
permission/factory overrides and shared-UID declarations refuse. The compiled
root must also contain exactly the same leaf signature permission declaration
and request as badging; name/protection IDs, namespace, owner and protection2
cannot be satisfied by suffix text or child attributes.

The reviewed common debug set deliberately includes:

- The exported MainActivity MAIN/LAUNCHER, or the provisioning setup launcher
  with private MainActivity/play/fixture activities.
- The exported, no-filter `androidx.activity.ComponentActivity` debug harness.
- Private `androidx.startup.InitializationProvider`, exactly the selected
  package's `.androidx-startup` authority, and three known initializers:
  EmojiCompat, ProcessLifecycle and ProfileInstaller, each `androidx.startup`.
- Exported/enabled ProfileInstallReceiver, directBootAware=false, with its own
  `android.permission.DUMP` guard and four exact single-action filters.
- Only the volume/receipt profiles' private same-UID ReceiptProofService.

Main is not the only exported component. The provider's absent URI-grant
overrides and the receiver's actual guard/filter identity matter separately.
Permitted activity theme and soft-input attributes retain their typed encoding.

| MAIN CLI profile | Selected package suffix | Extra app declarations |
|---|---|---|
| Ordinary | none | none |
| Archive | archiveverify | none |
| LiteRT without provisioning | litertverify | none |
| Input draft | draftverify | none |
| Input process | draftprocessverify | none |
| Model provisioning | modelverify | setup/play |
| Picker | modelpickerverify | setup/play, four private fixtures |
| Volume | modelvolumeverify | setup/play, private proof service |
| Receipt | modelvolumeverify | volume plus five private fixtures |

These are nine flag profiles/eight packages on the tested main. The frozen
operator's unmerged presentation-process extension is excluded. Existing
`audit_manifest`, model/receipt helper APIs and successful CLI JSON remain
unchanged; successful JSON is exactly `status`, `permissions`, `libraries`.
Only callers entering this MAIN CLI gain the new structural gate. Standalone,
instrumentation, physical/capacity and other audit entry points retain their
separate contracts and are not silently qualified.

## Actual source and verification

Base: `027ddbaf298cd05ebdcdf65d716962e783bcad31`.
Tested code tree: `1b4cd58f56140a860c479b86930bfbcaee4041fa`.
The final PR adds this non-executable report to that exact tree. Its four code/
fixture paths are pinned here by SHA256:

| Path | SHA256 |
|---|---|
| scripts/audit_apk.py | ab77044c1a1cad3a8fb6f592439134946c07a7467aed39cf9a05c2f617d451ea |
| scripts/tests/test_apk_component_boundary.py | 22107fd775d42d631cb0b5d2a94d84fe17d5862be4616e6c0f7c16f1954183b4 |
| scripts/tests/test_apk_backup_audit.py | 61a1d3ea3d71114b5e6ef20cdb99ec19b429c1a0a5711ba33454bcd814a1dd31 |
| scripts/tests/test_apk_backup_audit_edges.py | 05106324e7b74b5702fd57febf4e833fc5ad43dcf24499e2d433567299b35f15 |

Actual Windows/Python3.14 runs used an isolated `-I -S -B` unittest loader,
the physical D: candidate path and binary capture. The final permission and
regression runs also enforced explicit discovery counts.
The final six modules were test_audit_apk, test_audit_apk_publication,
test_apk_backup_audit, test_apk_backup_audit_edges, test_audit_process_controller
and test_apk_component_boundary, all under `scripts.tests`.

| Captured phase | Actual outcome |
|---|---|
| Initial setup | Inline quoting failed before test-file creation; one loader error, zero declared cases |
| Behavioral baseline | 12 methods; 43 assertion failures, including subtests |
| First component gate | All original 12 methods pass |
| First regression | 89 methods, one NameError from an over-broad negative-fixture edit |
| Corrected regression | 89 methods pass after restoring that original method exactly |
| Profile matrix | 13 methods pass; one method exercises all nine CLI profiles |
| First supplemental integration | Only the prior13 methods discovered; three top-level functions did not execute, not permission RED |
| Corrected permission RED | Discovery16; 12 assertion failures in the three added permission methods |
| Final regression | Discovery93, 93 distinct passes, zero errors/failures/skips |
| Final frozen APK CLI | Exit0, unchanged successful JSON schema |

The final count is **77 existing +16 new methods**, not the sum of repeated
cohorts. The nine profile cases are within one method. Ordinary assertions can
stop a failing method before its later variants; designed variants are not all
claimed individually observed in RED. Final GREEN reaches the finite cases.
The original12 method bodies and three independent permission-oracle bodies
remain AST-identical. The original two-initializer proposal is preserved unrun;
its positive helper was corrected to the actual three before first execution.

Existing backup positives now include the real observed component subtree.
All original backup class method ASTs are restored; the bounded-attribute edge
fixture inserts attributes before children and keeps its assertions/bounds.
No negative assertion, limit or skip was weakened. The loader/discovery,
fixture-integration and real behavioral failures all remain preserved.

For ordinary repository reproduction, select the same six modules with
`python -m unittest`, and run `python scripts/audit_apk.py <debug-apk>` with
the installed Build Tools35.0.0 SDK configured. Actual retained child commands,
discovery records, raw results, post-run script source maps and artifact/tool
before/after hashes distinguish
that reproduction entry point from the isolated local launcher.

## Frozen real-artifact check

The actual final CLI audited one unchanged B88 ordinary debug APK, historical
source `286c0905613e9bbff2d69796155105339000eceb`:
28,398,622 bytes, SHA256
`0b93c6af0772ff6216a0dcbeb2f8b19b1564129f3855336ced7dcafbfca662cd`.
The old binding and current bytes were verified and a private copy retained.
The product was not rebuilt, installed or executed. The nine-profile matrix
uses synthetic AAPT/ZIP ports, not nine real APKs.

Read-only AAPT35.0.0 version/badging/manifest/resource/rules commands observed
the four merged components and three initializer entries. Current AAPT file:
4,740,896 bytes, SHA256
`cbfe5deda5f7074ce47b6f33818b456ee8046a076a11af13e29c837d3c80c564`.
Its historical SDK path is recorded; this current tool-byte pin does not
retroactively attest B88's tool bytes. Original tool/APK hashes stayed unchanged.
Native library checks inspect both ABI files; they do not execute ARM64/JNI.

## Sources, preservation and limits

Official [provider semantics](https://developer.android.com/guide/topics/manifest/provider-element)
distinguish exported access from temporary URI grants. The
[receiver permission contract](https://developer.android.com/guide/topics/manifest/receiver-element)
constrains senders; [DUMP](https://developer.android.com/reference/android/Manifest.permission#DUMP)
is not an ordinary third-party permission. Privileged holders remain outside an
ordinary-app claim. [Aliases](https://developer.android.com/guide/topics/manifest/activity-alias-element)
are separate entry points. [Framework attribute identities](https://developer.android.com/reference/android/R.attr)
and the current [AndroidX profile manifest](https://raw.githubusercontent.com/androidx/androidx/androidx-main/profileinstaller/profileinstaller/src/main/AndroidManifest.xml)
support policy review. Current upstream sources do not substitute for this
APK's compiled dump or the pinned dependency-manifest inventory.

Independent source/oracle/closed-record reviews found no remaining concrete
policy bypass after the permission fix. The coordinator preserved its clean
operator/index and used a raw-Git D: INPUT SNAPSHOT, not a managed worktree,
after the app refused worktree attachment. Reviewers used separate existing
frozen read-only worktrees; no old sources/refs were reset or repaired.

Private output/recovery basename: `2026-11-02-apk-component-boundary-v1`.
Declared bounds: source128MiB, synthetic/bytecode128MiB, controls64MiB and
recovery512MiB. Installed tools remain in their supported locations; project
cwd/captures/copies/TEMP/TMP stay physicalD. Existing backup fixtures explicitly
use D:/Dev/_Temp; shared-prefix files remain in place without retrospective
ownership attribution or deletion. Raw baseline/intermediate code, failures,
oracles, current source, frozen artifact and recovery records are retained.

This is structural MAIN debug artifact admission and finite host evidence.
It does not prove code-level IPC confidentiality, runtime-registered receivers,
OS permission enforcement/backup/keyboard/compromised-device behavior, observed
outbound traffic or offline installed play. Full Python/Rust/JVM/frontend/build/
CI and device/model suites were not rerun. Phone/ARM64/model quality/performance,
Knowledge Android0/4 and full M10.03/M10.05/release gates remain open. No SDK
management, emulator/ADB/model operation, image deletion, ledger/settings change,
private upload or merge was performed.
