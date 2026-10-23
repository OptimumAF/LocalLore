# MSVC notice and runtime provenance addendum — 2026-10-23

Refs #31, partial D09.03/.05/.07. Implemented, locally checked, independent
review pending. This additive packet follows immutable collector source
`c11a79ddb89cb13c6f1629ac784b230a24f7cdf6` and evidence
`c6be1620ae00b7052b7e9caf872cb01657575933`; neither record is rewritten.
The tested addendum source is `d6f663e89fc83659e8a61cadc4cce47ccfd52232`.
Claims: #31 comments 6371431413 (investigation), 6371524518 (implementation).

## Exact material and attribution

The installed MSVC 14.34.31933 `xutility` and `yvals_core.h` match the raw
official `microsoft/STL` tag `vs-2022-17.4` files byte for byte. The annotated
tag is `648b635d728ad6cce6cc6398d0869c25f3e8be15`, peeled revision
`af8adfa73b7433d4f902584bc1994c897297e492`. Their hashes and the installed
STL 143/update 202208 identity are in the public provenance resource.

The addendum preserves the pinned [STL LICENSE](https://github.com/microsoft/STL/blob/af8adfa73b7433d4f902584bc1994c897297e492/LICENSE.txt)
and complete [STL NOTICE](https://github.com/microsoft/STL/blob/af8adfa73b7433d4f902584bc1994c897297e492/NOTICE.txt).
The latter includes the additional Boost/Ulf Adams, Kempf, Unicode, LLVM,
fmt and public-domain attribution supplied by that revision. This is
conservative component notice coverage, not a claim every implementation is
linked. The installed Visual Studio third-party-notice STL section independently
contains its notice body. The object-form LLVM exception remains intact;
this inventory does not replace its conditions with a new license.

| Resource | Upstream raw bytes / SHA-256 | Packaged LF bytes / SHA-256 |
| --- | --- | --- |
| MSVC-STL-LICENSE.txt | 12,550 / `1fc6b6db121d4555d8f661937d7f6013693cd8fd67495d5e5d98c1d18fb83eda` | 12,331 / `7c68a47568bd633f7a71ee5e2038660a2cc62ce8a5405999e2b69fab3f37469c` |
| MSVC-STL-NOTICE.txt | 10,762 / `11dee60b182033b92dfcce5344093eb05e009e2c0339ce551f5667b3838c8223` | 10,534 / `e9451ef95cc6e7e41e19da99879f414b978e7e82e5b2f1af08eb8486a3b47410` |

Only CRLF-to-LF normalization is applied to notice text; wording, trailing
whitespace, attribution and original raw hashes are preserved. This is not
normalization of compared binaries or historical reproducibility evidence.
The existing narrow license-text Git whitespace rule applies. Proprietary
Visual Studio terms, toolchain libraries, headers and runtime DLLs are not copied.

## Embedded material versus prerequisites

The new first-party `MSVC-runtime-provenance.json` records the following
separately; it is metadata under the project license, not a license grant for
Microsoft code:

| Family | Actual evidence and scope |
| --- | --- |
| STL headers/templates | Retained worker dependencies contain installed STL headers; pinned source and installed header hashes match. Apache-2.0 WITH LLVM-exception and full pinned notices preserved. |
| Native CRT startup/import glue | Actual retained worker `main.cpp.obj` has `MD_DynamicRelease`, `DEFAULTLIB:msvcprt`, `MSVCRT` and `OLDNAMES`. Installed `msvcrt.lib` contains initialization, executable startup and security-cookie members; conservative startup family recorded. |
| C++/VCRuntime/OpenMP DLLs | Retained b5 worker directly imports MSVCP140.dll, VCOMP140.DLL, VCRUNTIME140.dll and VCRUNTIME140_1.dll. They are external prerequisites and none is in the retained package. |
| UCRT/Windows | Both retained app and worker import UCRT API-set DLLs. UCRT/Windows DLLs are external; no SDK library or DLL is redistributed. |

Microsoft documents [native CRT startup as statically linked even with dynamic UCRT](https://learn.microsoft.com/en-us/cpp/c-runtime-library/crt-library-features?view=msvc-170).
Consequently, `/MD` and missing packaged DLLs do not establish absence of
embedded CRT material. The installed startup source/header notice is Microsoft
all-rights-reserved; the STL exception does not relicense it. The provenance
labels that family `LicenseRef-Microsoft-Visual-Studio-Community-2022` and links
the [exact Community 2022 terms page](https://visualstudio.microsoft.com/license-terms/vs2022-ga-community/),
official document URL/hash and installed Redist.txt pointer. No broad proprietary
terms document is included in the package. The producer must review applicable
toolchain/distribution conditions; this packet does not assert their acceptance.

This read-only examination used dumpbin 14.34.31937 from the exact recorded
MSVC toolset. It inspected the historical clean02 normal app
`30be7cde451ab6d5515e27781021c54772dcf3122d4dda71d048a21bad6fc308`
(source `6e576f473a4796c329468a6abf3eeaaf4323a89b`) and unchanged approved
worker `b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`.
The app has UCRT imports but no direct MSVCP/VCRuntime DLL import. These are
historical binary observations, not current app execution or a new package.
No exact extracted startup-object/per-symbol link map is reconstructed.

## Checks actually run

Pinned Python 3.14.9, Rust 1.93.1 metadata, Windows x64; task-owned D: artifacts
and temporary directory. No package/native compilation or app/worker/model run.

```powershell
python scripts/desktop-package-tests.py
python scripts/desktop-reproducible-tests.py
python -m unittest discover -s scripts/tests -p 'test_*.py'
git diff --check
```

Results: **29 package checks**, **20 unchanged reproducibility-checker checks**
and **153 runner/helper checks**, zero failures/skips. The package suite adds
two tests: every one of the three new resources is required, changed/missing
resources fail collection, and changed/deleted outputs fail verification even
after the manifest is resealed; actual provenance distinguishes embedded
startup from external DLLs and retains false approval flags.

Actual `rust_notices(os.environ.copy())` performed locked/offline Cargo metadata
and exact material collection: unchanged **250 registry + 6 local** identities,
**466 files / 2,885,724 bytes**, unchanged five MPL source archives / 150,290
bytes. New catalog SHA-256 is
`d13bd4b6db54da101824e7a2873fa45e5fd9561ca3c50e8065d8d3d0e10eefb2`.
The source inventory contains 286 files and binds new resources. A material-only
in-memory packet using retained historical public app/worker bytes passed
trusted-catalog validation; **no new package ZIP was written**. The original
446-member ZIP remains unchanged (`3f13d9a22e64866b40c9e6e8fae05efa3867461b9fd5e5bc56088aea1f4e545b`)
and correctly reports `legacy_unreviewed`.

Exact log/resource/source hashes are in
[the sanitized evidence](D09_MSVC_NOTICE_EVIDENCE_2026-10-23.json). Reproduction
of collection uses existing `rust_notices`, `source_inventory`, `inspect_archive`
and `validate_files(..., require_license_audit=True)` entry points; the local
`msvc-notice-artifacts/collect-verify.py` driver/logs preserve the exact invocation.

## Remaining concrete items

- Independent review of this exact catalog/resource delta and prior collector.
  All `review_complete`, `distribution_approved` and legacy
  `license_audit_complete` flags remain false. Mechanical coverage is only
  catalog-required bytes present.
- The separately identified nlohmann embedded-header copyright/conditional
  attribution finding remains pending its own resource fix/review; this MSVC
  delta does not resolve it or qualify the complete component inventory.
- Final combined normal package collection must bind its actual source/toolchain
  and app/import evidence. No new package or reproducibility cohort was run here.
- Producer review of applicable toolchain/distribution terms for embedded CRT
  startup remains explicit; no per-symbol map or distribution approval invented.
- Visual C++/WebView2 prerequisite installation, offline installation, actual
  blocked-network acceptance, signed/public distribution and full D09 remain
  separate gates. No runtime DLL/installer bundling is authorized by this work.

No model/profile/worker pin, dependency, toolchain, product/runtime/core/Host,
Storage, UI, Android or repository settings changed. No models, private stories,
device actions, desktop control, release or merge occurred.
