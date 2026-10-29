# Compiled APK backup policy audit

M10.03 / issue #14, 2026-10-29. Implemented for review; full privacy/release
gates remain unchecked. No app, manifest, rules XML, dependency or APK changes.
The [buffered restart packet](BUFFERED_RESTART_ADMISSION_2026-10-29.md),
frozen source and pending guest approval remain untouched.

## Gap and contract

The previous main APK audit checked package/SDK/permissions and native
libraries, but ignored backup flags and the referenced extraction rules.
The source already declares exclusions; this was an artifact-audit gap,
not an observed backup or data leak.

The main CLI now requires one manifest/application, matching package, and
application-scoped Android names/framework IDs for `allowBackup=false`,
`fullBackupContent=false` and one `dataExtractionRules` reference. False must
be an unquoted boolean. Names and non-null IDs are unique per node; a critical
ID cannot hide under another name. Unreviewed `backupAgent` and
`defaultToDeviceProtectedStorage` overrides refuse by name or ID.

The reference must resolve in the same package/type to exactly one default
XML file, `res/xml/data_extraction_rules.xml`. Aliases, qualifier overrides,
duplicate identities, inconsistent entry ranges and other paths refuse.
Both unique cloud-backup/device-transfer sections must exclude the full `.`
root of `root`, `file`, `database`, `sharedpref`, `external`. Four optional
`device_*` domains may only add unique full-root exclusions; they cannot
replace mandatory domains. Includes, unknown sections/attributes, nested
exclusions, duplicates and narrowed paths refuse.

The structural parser retains ownership and identity: 4 MiB/tool text,
65,536 lines, 4,096 nodes, depth32, 16,384 attributes. Sets avoid quadratic
duplicate scans. Uniform LF/CRLF and unrelated Unicode resources work;
mixed framing/control bytes refuse. Untrusted paths never select a host file.
Successful CLI JSON remains exactly `status`, `permissions`, `libraries`.
The permissions-only `audit_manifest` API and existing ZIP/JNI checks stay
unchanged; separate physical/capacity callers are not claimed to gain this
main-CLI resource-linkage contract.

## Official semantics and limits

[Android's backup guide](https://developer.android.com/identity/data/autobackup)
documents separate cloud/D2D rules, device-protected domains and OEM behavior:
`allowBackup=false` alone does not disable every manufacturer's D2D transfer.
API36.1 cross-platform transfer is a distinct mode; this checker neither
qualifies it nor infers its behavior from absent rules. Unknown sections
require a reviewed policy change.

[AttributeSet](https://developer.android.com/reference/android/util/AttributeSet#getAttributeNameResource(int))
exposes compiled IDs separately from names.
[R.attr](https://developer.android.com/reference/android/R.attr) and
[AOSP public IDs](https://android.googlesource.com/platform/frameworks/base/+/f0720bc5a165c835d291b36b368dd46e895e3871/core/res/res/values/public.xml)
identify the controls/override IDs. No explicit device-protected/direct-boot
use was found in 282 inspected app files; this is not transitive/native/OEM
proof. The policy covers the declared five domains, not all-storage backup
prevention. Device backup/transfer, traffic, installed offline play, file
access, exports/logs and CI qualification remain required for M10.03.

## Original adversarial verification

Eight original main-level methods first record 93 unsafe-case assertion
subtest failures, zero errors (3,141 ms/exit1); their positive controls pass.
The unchanged eight then pass with all40 existing APK/publication methods
(48-method cohort,4,352 ms/exit0). Existing method bodies and non-main original
audit functions remain unchanged.

Review found crafted-ID ambiguity in that first fix. Four separate original
edge methods record eleven assertion failures: six hidden override-ID cases,
three duplicated critical IDs under other names, two duplicate namespaces
(3,343 ms/exit1, zero errors). The identity fix passes all52 methods
(15,972 ms/exit0); its exact intermediate source is retained. The final
bounded-set implementation passes the same4 edge methods (3,494 ms/exit0),
including resource-index and exact metadata-limit controls. These are two
distinct RED/GREEN cohorts; neither replaces or weakens the other.

Final executed source: `bfd6092c20c360c6f7ba55ea90dfe25073a07221`.
Auditor SHA256: `b273f08bb45c47f9ca07ef6df42fe25ac31dafd3d034419f1e1ee72dd34af757`.
Full discovery passes **2,281 unique tests**, zero failures/errors/skips/
exclusions, **260,602 ms/owned exit0**, known capture/cleanup, empty stderr
and all **2,234 raw tracked hashes stable**. Cooperative Python auditing
records0 forbidden attempts and8 exact stdlib null opens; not an OS sandbox.
Elapsed figures are job records, not runtime/inference performance claims.

Exact command from the physical D integration worktree with process-local
`TEMP`, `TMP`, `TMPDIR=D:/Dev/_Temp`:

```powershell
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-apk-backup-audit-v1/check-host-v1.py all full-host-v1
```

Runner SHA256 `ba9f5350facf9dfa60a36cf6dc81e5e9eb5e94eee43f194e87cd5f9d832a6ca2`;
full result `ad42ee07ea613d44d6231a095c05f98323b962c3cd10b3330ebf64a2ca2988b3`.
Later report text does not replace the executed source.

## Actual existing-APK audit

The unchanged78,423,520B APK built at frozen `778f6f78` has SHA256
`c8adf07e9ae6802f98108ea8f9d0f061200119203273c95dd6f7e98069bfcd09`.
Installed AAPT2:4,740,896B,
`cbfe5deda5f7074ce47b6f33818b456ee8046a076a11af13e29c837d3c80c564`.
Three read-only format captures confirm false flags and resource
`0x7f0b0000` pointing to the default XML with both five-domain sections.

The first private helper refuses a tuple/list serialization mismatch before
any AAPT call (3,291 ms/exit1). A distinct corrected helper executes the
original three calls once (9,152 ms/exit0). A snippet-reader locale error is
corrected with explicit UTF-8 without recapture. Failed controls remain
preserved; neither is an APK/runtime failure.

The separate new whole-CLI implementation check runs:

```powershell
python -I -S -B scripts/audit_apk.py D:/Dev/Experiments/LocalLore/2026-10-29-buffered-restart-admission-v1/android/sdk-build-v1/apks/product.apk --litert-verification
```

Its owner exits0 in **9,608 ms**, known capture/cleanup and empty worker
streams. Actual1,101B output has the three-key schema, `status=passed`, six
library records. Auditor/driver/tool/APK,2,234 audit-source and2,232 frozen
source bindings stay unchanged. Independent closed readback verifies command/
profile, started worker/request, bindings/maps and output without repeating
CLI/parser/tests/AAPT. Whole result:
`8946a3023c69a535f28afa14f87b6eb30ae6f147a48eb92513adace790301bb5`;
independent receipt:
`7ab31b52148af53759d39e416a38f337181c633b2d288b7b1add9938cef1d13d`.

Original/failed/corrected controls and raw outputs remain under
`D:/Dev/Experiments/LocalLore/2026-10-29-apk-backup-audit-v1` with D recovery.
Expected storage<0.25GiB, maximum0.5GiB including source/captures/recovery;
existing APKs are read in place. No APK copy/rebuild, model/key/guest image,
device/ADB/socket/ledger action, permission/settings change, other-emulator
stop, cleanup, merge or release occurs.

Physical/OEM backup behavior remains untested. Invalid UTF-8 tool output
already aborts before success; direct `main()` return-code normalization for
that existing non-bypass error remains a separate follow-up.
