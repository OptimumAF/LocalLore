# Inventory and chat UI qualification profile

This host profile supports M10.02, M09.06 and #307/M09.04. It does not establish
Android execution or complete any milestone. It is stacked on the SDK11 host
harness (PR #328); the independently frozen inventory product is PR #330.

## Fixed authority

`owned_inventory_ui_contract.py` declares SDK12, with separate owner, session,
proof and boot-claim names. Its eleven fixed methods are the previous eight
chat methods plus the three `PlayerInventoryScreenTest` methods covering saved
inventory/known empty/unavailable, stale scope callbacks and draft retention,
and long exact identifiers/all quantities/Close at doubled font size.

The source closure contains the fifteen shared owner/socket/storage mechanism
files, eight new SDK12 files (including the build baseline JSON), and the
instrumentation evidence reader. The optional package initializer is also bound
when present. Missing or changed source refuses; a similarly named SDK11 record
cannot acquire SDK12 authority.

`inventory_ui_build.py` binds only the reviewed B59 product at final source
`ba548cbf6982c58d8a221aea2ed3606232d013d9`, whose build ran at
`b8dbbcbb1b3ea67552d7449f94286187a31166ad`. Its validation mode is explicitly
`fixed-b59-byte-attestation-v1`: immutable reviewed evidence and current source,
APK and native-stage bytes are checked again. This does not repeat the historical
XML/DEX/ELF semantic audits or make a new native/Android execution claim. See
[the build qualification](https://github.com/OptimumAF/LocalLore/blob/ba548cbf6982c58d8a221aea2ed3606232d013d9/docs/android/PLAYER_INVENTORY_APKS_2026-11-01.md) in
PR #330 for those separately attributed checks and preserved failures.

The product root is fixed to the physical D: `LocalLore-spike-review` checkout.
The build manifest has one prospective path:
`D:/Dev/Experiments/LocalLore/2026-11-01-inventory-ui-cohort-v1/inventory-ui-build-v1.json`.
The only artifact roles are `build`, `product_apk` and `test_apk`; callers cannot
choose a product root, validator, module, method roster or implementation.
Importing these modules performs no observation or target action.

## One bounded controller

The controller uses the concrete SDK12 owner/capture classes and the unchanged
shared finite process, socket, storage and proof mechanisms. It checks a fresh
API35/x86_64 guest and user0, requires both packages absent, streams each exact
APK, checks its staged hash, installs it, then records installed UID/path/hash
before and after eleven individual instrumentation commands. Raw binary output
and complete JUnit success are required, with one claim per exact method.
No model material is permitted. No gameplay or process-death command is added.

The closed command grammar is `Nboot + 35`: three properties, one user query,
two absence queries, six staging/hash/install commands, six installed checks
before, eleven instrumentation commands, and six installed checks after. One
successful boot observation therefore yields 36 complete clients. Extra boot
observations do not authorize another method attempt. Per-method 90 seconds,
controller 1200, caller 1230, owner 1700, parent 1730 and outer 1800 limits remain.
These overlapping limits do not promise all phases can consume their maxima.
An uncertain result aborts; there is no fresh guest or method retry.

## Activation and cleanup

The fixed activation helper runs from
`D:/Worktrees/locallore-inventory-ui-core-v1`. Its prospective paths are:

- Guest: `D:/Dev/Experiments/LocalLore/2026-11-01-inventory-ui-v1/avd-v1`.
- Runtime: `D:/Dev/Experiments/LocalLore/2026-11-01-inventory-ui-run-v1`.
- Controls: `D:/Dev/Experiments/LocalLore/2026-11-01-inventory-ui-harness-v1/run-controls-v1`.

The helper accepts only a hash-bound fixed input and source-bound admission.
It creates no proposal, authorization or admission. Prepared-guest validation
and the existing shared ledger remain mandatory. Caller identity is published
behind the start barrier; owner, worker and caller records must join exactly.
Only known caller termination permits a single atomic stop request. Cleanup
uncertainty is sticky. Final success requires known owner exit, complete capture,
all fifteen cleanup fields, verified guest storage closure and file-only replay
of the same controller result after cleanup.

The retirement reader recognizes the distinct SDK12 protocol for future closure
metadata validation. This registration does not authorize or perform deletion.

## Remaining execution gate

All eleven inventory-pair Android methods remain unrun until an exact authorized
operation passes fresh storage, port and ownership checks. Older pending SDK9,
SDK10 and SDK11 proposals retain their own source/APK/roster authority; none
qualifies this new pair. No phone, emulator, model copy, real inference or system
setting is required for the host packet. Host fixtures simulate boundary inputs
and cannot prove native ownership, Android behavior, real IME/TalkBack, physical
performance, ARM64 execution, story quality or release readiness.
