# D09 scoped license-tooling integration, 2026-10-23

Refs #31 D09.01/.03/.05/.07, partial. Coordinator-delegated integrator
`/root/desktop_runtime_profile`, reused clean `source-packaging` /
`impl/d09-license-integration`. Claim
[6373690785](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6373690785).
This integrates notice collection/verification tooling and public provenance,
not a new native package or distribution decision. `license_audit_complete`,
`review_complete` and `distribution_approved` remain **false**.

## Frozen packet and accepted-main reconciliation

Started with clean prepared packet
`8e3651525f39aeb7ba2d35b64761ec17a2e6a0d9`, including the original collector,
MSVC addendum, corrected embedded JSON attribution, and both independent reviews.
Fresh fetch confirmed current accepted main
`7b542421be8c479d22a69bbef88c7a9177302de2`. Merge `f0b04e7` applied without
conflict; existing Core/Host/Store/Android/UI work was retained, not rewritten.
Imported advisory report `78f65c5` as `dad7fb4`.

All checks below ran on
`dad7fb45d1b027c4b692d40218fe3c5e24fa6c1f`; this new report is a subsequent
documentation-only addition. The collector, catalog, resource bytes and original
tests remain identical to the prepared packet. The final PR against current main
contains only the packet's licensing/packaging scripts/tests, exact public texts,
catalog, narrow attributes and evidence documents. No dependency, root license,
toolchain/profile/worker pin, schema, application feature or workflow changes.

Historical evidence is preserved rather than updated to suggest later execution:

- [Original audit](D09_LICENSE_AUDIT_2026-10-23.md) and sanitized JSON bind the
  original collector/source and its then-existing incomplete attribution.
- [Original independent review](D09_LICENSE_INTEGRATION_REVIEW_2026-10-23.md)
  records the actual nlohmann notice omission and failed collector regression.
- [MSVC addendum](D09_MSVC_NOTICE_ADDENDUM_2026-10-23.md) separates STL notices,
  embedded CRT startup/import material and external runtime prerequisites.
- [JSON correction](D09_JSON_NOTICE_CORRECTION_2026-10-23.md) and
  [independent addenda review](D09_LICENSE_DELTA_REVIEW_2026-10-23.md) preserve the
  unchanged actual-collector RED-to-GREEN and conditional attribution limits.
- [GLib scope review](D09_GLIB_ADVISORY_SCOPE_2026-10-23.md) distinguishes the
  still-affected locked Linux/BSD path from normal Windows target selection.

The integrator authored the earlier collector/addenda; independent source/legal
disposition is not inferred from this integration. Previous independent reviews
remain separately attributed and all approval flags stay false.

## Actual collection against merged current source

The unchanged actual collector ran its locked/offline normal Windows selection:

```powershell
cargo +1.93.1 metadata --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --no-default-features --format-version 1 --filter-platform x86_64-pc-windows-msvc
```

`collect_license_materials` consumed that metadata, its actual
`metadata.workspace_root/Cargo.lock`, exact cached crate/native inputs and
existing provisioned frontend license files. The root lock is now the consumer;
the old standalone desktop-lock paths described in historical reports are not
reused as current authority. Existing metadata/lock checks accept the reviewed
root workspace and refuse identity/version/checksum/license drift.

Actual **256 selected identities =250 registry +six first-party**, exactly
matching frozen catalog
`07c8f47f8062e8bed24857e103be9f97bf8b2d2292ed0b17d0a90fe597986bf8`.
Every selected identity, license expression, lock checksum, required material and
cached embedded input passed the unchanged collector checks. Exact material
result: **467 members /2,888,215 bytes**, including five upstream MPL source
archives totaling **150,290 bytes**. No extraction, fetching or execution occurs.

The material-only scoped verifier returned
`catalog_materials_verified_review_pending`. This invokes
`validate_scope_audit(..., required=True)` using actual collected bytes and the
public profile metadata, not a synthetic catalog or an alleged current native
executable. Actual changed/deleted JSON header notices and forged approval were
all refused. The 30 policy tests additionally exercise full synthetic packet
resealing/closed names/drift/caps; no actual new package is manufactured here.

Current normal Windows selection excludes `glib`, `glib-sys`, `glib-macros`,
`gtk`, `gio`, `webkit2gtk`, `gdk` and `atk`. Fresh GitHub API read still reports
alert2 OPEN, medium, `GHSA-wrw7-89jp-8q8g`. This does not dismiss or fix the
affected `glib0.18.5` Linux/BSD dependency. Exact advisory/compatibility evidence
is in the imported scope report. No global dependency-clean or Windows-wide
vulnerability-free claim is made.

## Checks actually run

Installed Python3.14.9, Rust/Cargo1.93.1, Windows x64; own D-drive UUID TEMP/TMP
for pure tests and task-local `license-integration-artifacts` for logs. Metadata
is a read-only graph operation; no Cargo build/test/compiler was started while
the coordinator's heavy Store checks owned the slot.

| Command/check | Actual result |
| --- | --- |
| `python scripts/desktop-package-tests.py` | 30 PASS,0 failures/skips |
| `python scripts/desktop-reproducible-tests.py` | 20 PASS,0 failures/skips; checker unit tests, **not** two full builds |
| `python -m unittest discover -s scripts/tests -p 'test_*.py'` | 182 PASS,0 failures/skips, current runner/helper suite |
| `python scripts/desktop-license-review-tests.py` | 1 PASS, unchanged original actual-collector attribution regression |
| Actual metadata/catalog/material collection | PASS, exact counts/bytes above |
| Actual scoped material validation + three mutations | PASS; all mutations refused |
| Source inventory and ownership diff | clean inputs,322 source files; no current-main app/Core/schema delta |
| `git diff --check` | PASS |

Prior reports' 153 runner/helper counts remain historical; this run executed the
current 182 tests. No favorable gate was obtained by dropping tests or changing
their expected outcomes. Existing package entrypoint still loads the added pure
license-policy tests. The original actual-collector regression is separately
invoked unchanged, rather than erasing its retained historical failure.

## Source/evidence binding

Raw metadata includes local cache paths and remains outside Git. The local
`collect-integration.py` driver calls existing collector, scoped verifier and
source inventory APIs; the sanitized summary contains hashes/counts only.

| Input/evidence | SHA256 |
| --- | --- |
| unchanged packager | `f49ecce6c973bc3366621511e087e883bb696395503a6d4c3c323c23f7f66973` |
| exact catalog | `07c8f47f8062e8bed24857e103be9f97bf8b2d2292ed0b17d0a90fe597986bf8` |
| consumed root lock | `2d2c63f731134bdb76c3aa270afed9101fdba061b8b9a9658d679b50aa453317` |
| selected graph | `17b566ecb41d62de80a664673166065a15975fa4f701317c51c73a133b974551` |
| actual local metadata | `65bd01144513608419f8c4975ef27de4e7d26db56be164bc76e7047385828170` |
|322-file source inventory | `93a8e45d1e41040fb33f310596026336fb36121c7122cfc2e81025e3236f8cff` |
| package tests | `ed1a3b8bdc61e003507f0d2a3a189990bb7ca2e79150322b7fa1ac16b0b26cf5` |
| checker tests | `cad657117794a039f00539005d46eed5b337230b1d092ef53c74451ddeee29d4` |
| runner/helper tests | `13c88c61460a6ec25620b4c91e698c9cde1c1d6c23ea584180c3120697b1620b` |
| actual collection log | `372ee6332d567d1980bc7eba12b6bfedebd70a71c016d5eb68eb6eab6ad08882` |
| sanitized collection summary | `8943a3c3f23240bc1900fd9ec56bfa027d374a960114e19cfb13b08fa72f4a04` |
| unchanged attribution test log | `aaf634bcea1051575084c46e642de7f5db5ffc3377ed1ed8bfa2983bcb962e68` |
| fresh alert2 response | `00d81ff8708ff2741317d97f0e7d1ad27178da51a4f6b136ed53428045feaf08` |

## Remaining disposition and product gates

Technical `coverage_complete:true` means all exact trusted-catalog material bytes
are present. It is not legal approval, proof every conservative notice's code
links, a full current binary linker map, or a publisher signature. The public
MSVC provenance distinguishes STL's LLVM exception from separate proprietary
CRT startup terms; producer assessment of applicable terms remains a concrete
open item. No broad proprietary terms are newly copied and no policy is changed.

The final combined source/binary/toolchain package must be collected and verified
later, with current imports/prerequisites and unchanged raw-byte reproducibility
gates. Historical package/build failures and the old legacy-unreviewed archive
retain their own source attribution; this run neither rewrites them nor supplies
a new package. Offline installation/network-denied journeys, clean-profile and
retention behavior, signed/public distribution and full D09 matrix remain separate.

No model weights/private saves/new artifact loaders, package/native/frontend
build, application/worker/model/device/ADB/CUA/desktop/protected-resource,
dependency download, repository-setting, merge or release action occurred.
Next: focused owner review of this tooling PR, then separately authorized final
package/qualification/distribution disposition after the product features settle.
