# Physical APK backup resource linkage

M10.03 / issue #14, 2026-10-29. Implemented for review, stacked on the
[main APK backup guard](APK_BACKUP_AUDIT_2026-10-29.md). Full privacy and
physical-device gates remain unchecked. No app, rules XML, dependency, model,
permission or APK changes.

## Gap and resulting behavior

The paired phone checker previously counted one dataExtractionRules string,
then always inspected res/xml/data_extraction_rules.xml. A manifest could
select another resource while an unused benign XML file satisfied the audit.
Its backup string matching also discarded namespace/framework identity and
rules hierarchy. These are demonstrated audit gaps, not observed data leaks.

audit_manifests now requires compiled app_resources as its sixth positional
argument; there is no compatibility default that skips linkage. audit_pair
dumps the full table, calls the shared audit_backup_resource before fetching
XML, and passes the same table into the manifest audit. The resolved path
must satisfy the shared own-package/default-file contract. Both shared strict
backup helpers run; the physical profile's existing exact five-domain count
also remains required. Optional device-protected-domain expansion is not
introduced into this profile.

Wrong references, aliases/configurations, malformed tables, quoted flags,
namespace/ID overrides and permissive/misplaced XML refuse before signing or
success JSON. DEX definitions, six physical methods, explicit fixture opt-in,
permissions, SDK/launcher/provider checks, paired signing and before/after APK
identity remain required. The public CLI arguments and nine-key success
schema are unchanged. Separate capacity callers are not upgraded by this work.

## Bounded capture

Installed SDK35 resources help exposes only --no-values, -v and -h.
The single help call returns exit1 with313B stderr/0stdout, owned216ms and
known cleanup/capture. No XML/type/config filter is available; --no-values
would remove file/configuration linkage. Full tables can exceed262144B.

The existing run_process signature, default131072B, ceiling262144B and all
lifecycle behavior remain unchanged. A separate run_resource_table(command)
entry fixes empty request,15-second execution deadline and4MiB combined
stdout/stderr cap. It reuses the same process/job/pipe/overflow/cleanup body.
The private ceiling selector accepts only the two fixed caps; there is no
environment/JSON selector or fallback. Physical tool dispatch uses this entry
only for the exact four-argument dump/resources shape. Other calls retain
their old budget. Cleanup waits can add to execution time;15seconds is not a
total-wall guarantee.

Independent AST reconstruction verifies the shared lifecycle body against its
pre-change source. All25 original physical test methods retain their
assertions after canonical synthetic IDs/hierarchy and resource-sequence
metadata adjustments. The main checker/shared backup parsers are unchanged.

[Android's official backup guide](https://developer.android.com/identity/data/autobackup)
distinguishes cloud/device-transfer rules and OEM behavior. Compiled-policy
acceptance is not proof of physical backup/restore or every storage domain,
OS version, manufacturer or cross-platform transfer mode.

## Verification actually executed

Executed source: 847a38318264b6bd402498c1d5ca421f9fe24e71.
The report commit changes only README and this new document.

Six original caller methods are committed before the fix. Their baseline
records19 assertion failures, zero errors/skips (4308ms/ownedexit1);
the same byte-identical file then passes. Canonical default and explicit
fixture controls pass in both versions; no missing-API error substitutes for
an unsafe-acceptance assertion. Baseline result:
792e394bdd469609da1f24b4750e29f7fd76d2cccda6a3f171c7e3f4c2dbd10a.

Five additional actual local-subprocess tests verify complete307200B stdout
plus24680B stderr, exact combined4MiB EOF, combined-pipe overflow refusal,
fixed15-second timeout/cleanup and unchanged old-API/no-extra-knob refusal.
These are post-implementation owner tests, not an invented RED cohort.
Focus passes52 methods in29799ms/ownedexit0. Original25 physical and16
runtime-spike methods remain in this cohort. Focus result:
83190556c79d44f91366cdee9b39281a725be336a33b05de01e1ba52507083ae.

The first private focus runner executes31 physical methods without assertion
failures but records one benchmark import error. That failed capture remains.
Distinct v2 adds the benchmark import path and includes its original suite
alongside full script discovery, asserting unique IDs without exclusions.

From physical D:/Worktrees/LocalLore-storage-integration-v1 with process-local
TEMP/TMP/TMPDIR=D:/Dev/_Temp:

```powershell
python -I -S -B D:/Dev/Experiments/LocalLore/2026-10-29-physical-backup-linkage-v1/check-host-v2.py all full-host-v1
```

Full discovery passes **2308 unique tests** (2292 script +16 original benchmark
methods), zero failures/errors/skips/exclusions, **424024ms/ownedexit0**, known
cleanup/capture and empty owner stderr. All2237 raw tracked hashes remain
stable. Cooperative Python auditing records0 forbidden attempts and8 exact
stdlib null opens; it is not an OS sandbox. Elapsed figures are job records,
not Android/model performance. Full result:
49beda2205323fd3a44ac5b155d4af7eefcf1114366ed7ce63ffdefc8e3654a6.
Runner SHA256:
0cd776ce3cb2057289cf9d374f34d9f1a591bd5a04b8e2b3383ac437f6b882e4.

## Actual SDK resource capture and remaining gates

The actual new physical.tool resource path runs once against the existing
litertverify product APK, SHA256
c8adf07e9ae6802f98108ea8f9d0f061200119203273c95dd6f7e98069bfcd09.
It returns the complete364246B table, SHA256
bfe4e89d96f660a8cff10f85b731b9a76ff347e9a1d85e518d9f67814cd3c3ca,
identical to the prior capture. The shared parser accepts it against the
hash-pinned saved manifest with explicit package org.locallore.app.litertverify.
This is not a phone-package audit.

Outer owner10123ms/exit0, cleanup/capture known, outer streams empty;
all2237 source and tool/APK/manifest/runtime/driver bindings stay unchanged.
Inner completed/return0/cleanup are enforced by tool source, not a separately
retained inner ProcessResult; no inner raw-stderr claim is made.
Result76ffc77ff33202b5d759b8f9763750855305da22ca6319320d7535d8e97eff40.
Independent file-only reader:
299504c0bbedd7e743a775300dde0d680bc5cfb6ac74e1837ec696b511a3a94c.

Unrun capture-driver v1 is preserved; v2 corrects API-call counting before
execution. The first evidence reader actually exits1 because it expects the
wrong historical field name (tool_api_calls instead of tool_calls). Its
submitted text/combined trace are preserved without claiming raw-stdin byte
attestation. A distinct AST-corrected reader exits0 with all original checks,
without SDK/parser/test replay. Neither control is a product failure.

The compatible phone APK pair is not found in36 exact paths/six named migration
inventories. This bounded observation proves neither global artifact absence
nor phone absence. Actual paired-APK audit remains **blocked on compatible
artifacts**; no phone APK is rebuilt or copied in this packet.

Closed small captures and recovery live under D:/Dev/Experiments/LocalLore/
2026-10-29-physical-backup-linkage-v1 and the matching D:/Dev/Recovery/LocalLore
packet. Expected<0.25GiB/max0.5GiB including source/captures/recovery; existing
APKs/tools are read in place. No model/key/guest/device/ADB/socket/ledger
action, other-emulator stop, shared-service/settings change, cleanup, merge or
release occurs.

Next runnable host task: inventory and budget a current offline phone-profile
build, then run the full paired audit against its verified artifacts.
M10.02/M09.06 buffered-guest import/AUTHOR/passive restart still requires the
existing unanswered approval and fresh guarded admission. Full M10.03
offline-traffic, backup/restore, OS/device and privacy qualification remains
separate.
