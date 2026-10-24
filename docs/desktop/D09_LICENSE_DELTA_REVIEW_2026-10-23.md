# Independent notice addenda review — 2026-10-23

Refs #31 D09.03/.05/.07 partial. Reviewer `/root/resource_metrics_review`,
isolated `review/d09-license-delta` / `source-license-delta-review`; claim
6371646550. Sole new review artifact is this report. No existing source, catalog,
resource, original regression, lock, runtime or author worktree was edited.

Frozen MSVC source: `d6f663e89fc83659e8a61cadc4cce47ccfd52232`, documentation
`40ce967054dae200a976bbd648e2961488d55426`. Frozen JSON correction:
`c74c54ca078d1b2113caeb22d76bb364f5a96ef1`, final documentation/evidence
`f43a4141dcb6e2c140bd61adb92df111a69a3c39`. The reviewer imported those exact
commits and original regression `264f4d5413009854bdd091f2816654ac0a604342`
unchanged into this separate tree. The prior collector review `04dcf25` and its
c11/c6 source bindings, RED evidence and historical artifacts remain immutable.

The JSON correction addresses the demonstrated embedded-attribution omission:
the **same unchanged actual-collector test fails on MSVC-only source and passes
after c74c54c**. No additional technical blocker was demonstrated in these frozen
addenda. This does not provide legal warranty, producer acceptance, complete
per-symbol attribution or public distribution approval. All legacy audit,
`review_complete` and `distribution_approved` flags remain false for coordinator
disposition. Full D09 and package qualification remain open.

## MSVC/STL/CRT evidence

Independently compared all ten installed input fingerprints in the provenance
resource: exact MSVC14.34.31933 STL/CRT headers, startup/import libraries and
SDK10.0.19041.0 UCRT inputs. Installed `xutility` and `yvals_core.h` match the
retained raw pinned-tag source files byte-for-byte. The published tag label
`vs-2022-17.4` / peeled revision `af8adfa73b7433d4f902584bc1994c897297e492`
is bound in catalog/provenance. Upstream network retrieval/tag resolution is
historical author evidence; this reviewer made no fresh download or independent
remote-signature verification.

The complete pinned STL LICENSE and NOTICE match the retained raw source after
only CRLF-to-LF conversion. Original wording, whitespace and object-form LLVM
exception remain. Raw LICENSE is 12,550 bytes, SHA
`1fc6b6db121d4555d8f661937d7f6013693cd8fd67495d5e5d98c1d18fb83eda`;
packaged LF is 12,331 bytes, SHA
`7c68a47568bd633f7a71ee5e2038660a2cc62ce8a5405999e2b69fab3f37469c`.
Raw NOTICE is 10,762 bytes, SHA
`11dee60b182033b92dfcce5344093eb05e009e2c0339ce551f5667b3838c8223`;
LF is 10,534 bytes, SHA
`e9451ef95cc6e7e41e19da99879f414b978e7e82e5b2f1af08eb8486a3b47410`.
The complete NOTICE retains the supplied additional author/component notices
conservatively, without claiming every implementation is linked.

The first-party runtime provenance correctly separates STL Apache-2.0 WITH
LLVM-exception material from the Microsoft all-rights-reserved CRT startup/import
family. The custom `LicenseRef-Microsoft-Visual-Studio-Community-2022` identifies
the separate terms reference; STL's exception does not relicense the CRT family.
Producer assessment of applicable proprietary toolchain/distribution terms is
explicitly unresolved. The document URL/hash and installed Redist.txt pointer
match retained/installed evidence; no broad proprietary terms document is copied
into the package. Fingerprints and linked terms do not themselves grant rights.

This reviewer executed **bounded read-only** installed dumpbin14.34.31937
`/dependents` on the retained historical app and approved b5 worker, and
`/directives` on the retained worker main object. Binary hashes/import lists match
the provenance exactly. The object shows MD_DynamicRelease and defaults for
msvcprt, MSVCRT and OLDNAMES. The worker imports MSVCP140, VCOMP140, VCRUNTIME140,
VCRUNTIME140_1 and UCRT API sets. The historical app has UCRT imports but no direct
MSVCP/VCRuntime DLL import. This is binary inspection, not execution or a new
build. Dynamic imports and `/MD` do not prove embedded CRT startup absent.

The unchanged retained 446-member package contains no DLL, library, header or
terms DOCX member. External Visual C++/UCRT/WebView2 prerequisites are not
redistributed there. That observation does not authorize their future bundling
or prove offline installation. The resource makes no whole-toolchain
redistribution claim. Exact extracted startup-object/per-symbol maps and current
combined-build evidence remain unavailable. Public addendum/provenance/evidence
scan contains no host drive/home paths. No toolchain/dependency/runtime pin changed.

## JSON attribution correction and unchanged regression

Independently read the exact selected `vendor/nlohmann/json.hpp` at approved
llama.cpp620d2225; source SHA
`f9ce5c0a1ac99e20ef92daeb60eb571e2146988daa553ac0269755348843efd7`.
The new 2,491-byte resource is SHA
`c81b7f95cf00d14e71d32c3586e690cc012e6f3bb9eee9dc914d6a2154bda24e`,
matches its exact Git blob and LF catalog binding. All eight recorded inclusive
line ranges match the actual pinned source excerpts. Independently extracting
the header's distinct SPDX copyright lines gives **five**, and every exact line
is present: Niels Lohmann, Evan Nemerson, The Abseil Authors, Björn Hoehrmann,
Florian Loitsch. The original root MIT text remains required and unchanged;
referenced MIT and Apache-2.0 text members actually exist in collected materials.

Actual source lines3219/3227 place the Abseil utility fallback under the `#else`
of `JSON_HAS_CPP_14`. The source and retained build flags establish the stated
C++17 profile, while the new resource/catalog explicitly avoid asserting that
fallback compiled or contributed symbols. Hoehrmann/Loitsch attribution sections
are outside that conditional. Conservative inclusion does not become an invented
per-template binary linkage claim. The exact excerpts preserve original source
attribution and include first-party range/applicability labels.

Original regression SHA remains
`4dd2429163c31b6a6a0250651be08925b9a10256958d93c6919169e368bdaeef`.
It executes the same actual locked/offline `rust_notices` collector. MSVC-only
review tree retained **1 failure / 1 test**, missing Hoehrmann/Loitsch; after
importing c74c54c, **1 passed / 1 test** with identical bytes and assertion. The
original source/report was not edited, its historical failure not relabeled,
and the test was not silently removed. Author's separately disclosed zero-test
wrapper setup attempt is historical author evidence, not reviewer execution.

Using actual collected material and retained app/worker bytes **in memory only**,
required-scope packet validation passes. Independently changed/deleted the new
attribution, changed it plus forged the audit, added an uncataloged notice, and
removed the audit. After recomputing each file manifest, all **five mutations
were refused** by the same verifier. No ZIP was written and no binary executed.

## Checks actually executed

Windows x64 10.0.26300.0, pinned Python3.14.9, Node24.22.1, Rust/Cargo1.93.1;
existing locked dependencies, own UUID D: TEMP/TMP and local artifacts. No new
downloads, compiler/package builds, app/worker/model/device/CUA/protected-resource
actions, settings, merges or releases. Current original approval flags stay false.
Delegation slots were occupied; reviewer work ran sequentially in its own tree.

| Command/check | MSVC-only freeze | With exact JSON correction |
| --- | --- | --- |
| `python scripts/desktop-package-tests.py` | 29 PASS | 30 PASS |
| `python scripts/desktop-reproducible-tests.py` | 20 PASS | 20 PASS |
| `python -m unittest discover -s scripts/tests -p 'test_*.py'` | 153 PASS | 153 PASS |
| `python scripts/desktop-license-review-tests.py` | **1 FAIL**, retained | **1 PASS**, identical source |
| Actual locked/offline collection | 466 files / 2,885,724 bytes | 467 files / 2,888,215 bytes |
| Required-scope in-memory material validation | PASS | PASS; five resealed mutations refused |
| `node scripts/desktop-package-workflow-check.mjs` | Unchanged source | PASS static policy |
| `git diff --check` | PASS | PASS |

Each selected closure remains **250 registry + six local** identities. Five MPL
archives /150,290 bytes and their lock/checksum/source bounds remain unchanged.
Source inventory grows 286→287. Final catalog SHA is
`07c8f47f8062e8bed24857e103be9f97bf8b2d2292ed0b17d0a90fe597986bf8`.
This frozen tree consumes its metadata-selected standalone desktop lock, not the
coordinator's later combined root lock. No combined-lock claim is inferred.

Reproduction uses the commands above with provisioned pinned executables and
dependencies; set own TEMP/TMP and `PYTHONIOENCODING=utf-8`. Actual collection
uses existing `rust_notices(os.environ.copy())`; read-only inspection uses the
installed exact dumpbin against retained files. Frozen collector APIs did not
change. Logs/drivers remain outside Git in sibling `license-delta-review/`, with
separate `msvc` and `json` subfolders; earlier evidence was not overwritten.

| Reviewer evidence | SHA-256 |
| --- | --- |
| MSVC actual collection JSON | e68f2ffe88f37faf1a366d4be081a649f1c9ee38c4ada14946c6342dbb930e36 |
| MSVC installed/binary inspection JSON | 62bfd4baf9ba6d5953d9c73f62a1bea16a57bf2cfa3669e1140b9627d1953d4f |
| MSVC-only RED log | f500c4af8a65208634bcae2078a0c11d1bc5be9c39845874b4123910edee9b4d |
| Corrected actual collection JSON | 325820347a75ffa392ca1836d05745033668a12b4eb842cff19a1d08f3b75785 |
| Exact JSON source/tamper inspection JSON | be4bd62e17b930272c05cf9e69c93aead00d0b9b1c82febafbeba4320f06d8ea |
| Unchanged regression GREEN log | 268c1ebd699a9c58bed908d46723febd6a3f29299800909e8dca9578ed76f941 |

Historical ZIP remains SHA
`3f13d9a22e64866b40c9e6e8fae05efa3867461b9fd5e5bc56088aea1f4e545b`,
446 members, unchanged and `legacy_unreviewed`. Technical scoped material
completeness is not warranty or legal/public-distribution approval. Remaining
work belongs to coordinator: applicable producer terms disposition, combined
root-workspace/current app/toolchain/import binding, fresh authorized normal
package/raw-byte gates, prerequisite/offline qualification and full D09 acceptance.
No current app execution, model quality, GUI/device or signed release is qualified.
