# Independent scoped license packet review — 2026-10-23

Refs #31 D09.03/.05/.07 partial. Reviewer `/root/resource_metrics_review`,
`review/d09-license-integration`, separate `source-license-review` worktree.
Claims #31 comments 6371446204 and 6371548578. Reviewed frozen source
`c11a79ddb89cb13c6f1629ac784b230a24f7cdf6` plus documentation
`c6be1620ae00b7052b7e9caf872cb01657575933`. No existing production, catalog,
text, manifest, lock, workflow or author worktree was edited. The separate MSVC
investigation is evolving and is **not** part of this frozen review.

**One concrete attribution gap remains.** The collector's exact catalog checks
pass, but the catalog omits embedded nlohmann header author attributions. A new
actual-collector regression is retained RED at
`264f4d5413009854bdd091f2816654ac0a604342`,
`scripts/desktop-license-review-tests.py`. It is intentionally separate from the
existing CI entrypoint pending coordinator disposition. This is technical source
evidence, not a legal opinion, public distribution approval or a complete license
applicability determination. All three flags remain false:
`license_audit_complete`, `review_complete`, `distribution_approved`.

## Finding: root JSON license misses embedded author notices

The approved llama.cpp source `620d2225cc436ab0b001e3200e590e3b286ef9ab`
contains `vendor/nlohmann/json.hpp` version 3.12.0, SHA-256
`f9ce5c0a1ac99e20ef92daeb60eb571e2146988daa553ac0269755348843efd7`.
Actual retained Ninja dependency records include this header for the worker's
`main.cpp.obj`; it is not merely an unrelated vendor-directory candidate.
Read-only `ninja -t commands locallore-llama-worker` returns 137 commands;
`ninja -t deps` confirms the header without compiling or executing anything.

The header records additional authors, including:

- line 17609: Björn Hoehrmann, 2008–2009, in the UTF-8 component;
- lines 17635/17663: Florian Loitsch, 2009, in number conversion;
- line 341: Evan Nemerson, 2016–2021, in portability macros;
- line 3199: The Abseil Authors, 2018, in a utility section.

The frozen catalog has only `NOTICES/native/nlohmann-json-MIT.txt`, copied from
`licenses/LICENSE-jsonhpp`. That exact upstream root license names Niels Lohmann
alone. Its bytes/hash are correct; copying that file alone does not retain the
additional embedded attributions. The actual collector's catalog-bound JSON
component material contains neither Hoehrmann nor Loitsch. The new test executes
the **same** `rust_notices` and `collect_license_materials` with actual locked,
offline Windows Cargo metadata and fails exactly once on those missing names.
No fixture implementation, mock collector or speculative model result is used.

The Hoehrmann/Loitsch sections are outside the separate C++14 conditional
fallback. The Abseil-derived sequence implementation is inside the `#else` of
`JSON_HAS_CPP_14`; actual retained worker flags use C++17. Its nearby comment
mentions Apache-2.0, while its enclosing SPDX header says MIT. Do not conclude
that this particular fallback contributes linked code without preprocessing/link
evidence. The RED test does not assert Abseil applicability. Header inclusion also
does not establish that every template or macro contributes binary symbols.

Recommended coordinator disposition: retain conservative, exact pinned embedded
copyright excerpts with bounded source/hash/line provenance, and assess any
conditional notices explicitly. Keep the original root MIT text. Re-run the same
RED test against the frozen correction, all existing checks, combined root-lock
collection, and subsequent authorized package gates. This reviewer did not add a
replacement notice, decide legal obligations or alter the source/catalog to make
the test pass. The separate MSVC addendum cannot silently resolve this finding.

## Selected closure and material verification

Actual `cargo +1.93.1 metadata --manifest-path
apps/desktop/src-tauri/Cargo.toml --locked --offline --no-default-features
--format-version 1 --filter-platform x86_64-pc-windows-msvc` ran in this worktree.
The reviewer independently walked `resolve.root`/dependency edges and compared
selected identities, versions, source URLs, checksum entries and exact license
expressions against the catalog. Result: **256 identities, 250 registry and six
first-party**, no mismatch. Metadata selects the standalone desktop workspace at
this frozen source. The collector obtains the consumed lock through
`metadata.workspace_root`, rather than assuming a retired path. Consumed lock:
`apps/desktop/src-tauri/Cargo.lock`, SHA-256
`874d1844ec0508d2c2c6d82bdd40668c74b29e7a8726621bfd1ee9c298237563`.
The coordinator's later root-workspace alignment was not imported or requalified.

The six first-party entries alias the unchanged root Apache-2.0 LICENSE. Exact
legacy license-expression spelling is preserved, including slash forms; no
generic SPDX heuristic silently elects terms. Current combined operands are
explicitly represented and checked: brotli 9.0.0 BSD-3-Clause AND MIT; dpi 0.1.2
Apache-2.0 AND MIT; unicode-ident 1.0.27 (MIT OR Apache-2.0) AND Unicode-3.0.
The last retains both alternative texts as well as Unicode. Unknown expressions,
identities, versions/checksums and removed required operands fail collection.

Actual collection returns **463 material files / 2,854,428 bytes**, including
the generated audit report. The report binds 462 other material members and the
selected graph/catalog/runtime profile/worker identities. `coverage_complete`
means those exact catalog-required bytes exist; the finding above demonstrates
why this is narrower than complete component attribution or approval.

All 16 source-controlled resource texts match their exact Git blobs and contain
canonical LF bytes. Upstream trailing whitespace/blank EOF is intentionally
preserved; the narrow approved `.gitattributes` exception affects only those
third-party texts. Ordinary source whitespace checks remain active. The source
inventory has 283 entries and binds the catalog, resources and attributes.

Five original cached MPL `.crate` archives match their exact consumed lock
checksums. Independently read tar metadata (no extraction) shows ordinary files
and directories only, expected package-root prefixes, no traversal or link
entries. Compressed total is **150,290 bytes**:

| Archive | Bytes | Members | Expanded file bytes |
| --- | ---: | ---: | ---: |
| cssparser 0.37.0 | 56,860 | 24 | 253,007 |
| cssparser-macros 0.7.1 | 8,197 | 6 | 24,274 |
| dtoa-short 0.3.5 | 8,287 | 6 | 24,754 |
| option-ext 0.2.0 | 7,345 | 8 | 22,611 |
| selectors 0.38.0 | 69,601 | 22 | 333,611 |

Independent normal-kind traversal excluding proc-macro targets identifies four
as runtime-kind eligible; cssparser-macros is proc-macro. This is not a final
per-symbol linker map. Including all five is conservative. Only their exact
`SOURCES/MPL/<name>-<version>.crate` outputs receive the binary exception:
five count, 131,072 bytes each, 262,144 aggregate. MPL text/source index identifies
format, versions, hashes and source availability without app extraction or fetch.

## Component boundaries checked

Installed Rust 1.93.1 standard-library copyright HTML plus the five selected
license texts match the catalog resources byte-for-byte (LF normalization was
unnecessary for these installed inputs). The 425,661-byte copyright HTML is
conservative across targets and includes dependency notices; it is not evidence
that every listed component links on Windows, nor an authorization to redistribute
the compiler/toolchain. Runtime prerequisite distribution remains separate.

Pinned native nlohmann root MIT, cpp-httplib license and 2026 header, and
llamafile sgemm notice excerpts match actual source620d2225 files and recorded
source hashes. The JSON embedded attribution gap is stated separately above.
SQLite amalgamation and WebView2 static loader bytes are checked against the
catalog's bounded cached native inputs. SQLite's public-domain provenance is
separate from the Rust wrapper MIT notice. Microsoft WebView2 SDK 1.0.3800.47
loader terms are separately included; wrapper MIT alone does not cover that
component. Cached published VCS metadata independently confirms distinct
WebView2 wrapper/macro source revisions. Original small official text retrieval
is author-supplied historical evidence; this reviewer made no new network fetch.

React/React DOM 19.3.1 and scheduler 0.28.0 identities, MIT texts and the frontend
lock match collection. The build function compares newly generated esbuild legal
comments against the trusted catalog before publication; collection alone does
not compile or regenerate the frontend. The model profile is hash-bound metadata,
not weights or a redistribution grant. No weights were read or bundled.

## Closed verification and actual checks

Trusted source catalog controls expected materials. Re-sealing an archive's own
manifest cannot authorize changed report, text, registry inventory, source archive,
runtime profile, approval field or extra notice. Reserved generated names, closed
paths/origins, bounded individual/aggregate text and source budgets are checked.
The collector validates the selected graph before reading notice sources.
Unselected metadata paths are not used. Exact package/report hashes provide
integrity relative to this trusted source; they are not publisher authentication,
a binary supply-chain signature or proof of all upstream license applicability.

Historical no-scope packets remain viewable as `legacy_unreviewed`; removing the
new report cannot gain an audited status. New build publication requires the
scoped report. Independently inspected the historical **446-member** ZIP, SHA
`3f13d9a22e64866b40c9e6e8fae05efa3867461b9fd5e5bc56088aea1f4e545b`,
before/after identical and still `legacy_unreviewed`. Constructing an in-memory
materials-only packet using its retained app/worker bytes passes required-scope
validation; this did not write a new package, alter that ZIP, build or run code.

Executed Windows x64 10.0.26300.0, Python **3.14.9**, Node **24.22.1**, Rust/Cargo
**1.93.1**, existing locked cache only, own UUID D: TEMP/TMP. The ignored frontend
dependency junction points to the already provisioned dependency directory.
No download/install, compile, package build, app/worker/model/device execution,
CUA, screenshot, protected resource, setting, merge or release action occurred.
All delegation slots were occupied; this reviewer worked sequentially, separately
from the author and coordinator. Previous review/implementation ownership is
unrelated to the new license collector.

| Command/check | Reviewer result |
| --- | --- |
| `python scripts/desktop-package-tests.py` | **27 PASS**, no skips; original 12 + 15 author license tests |
| `python scripts/desktop-reproducible-tests.py` | **20 PASS**, no skips |
| `python -m unittest discover -s scripts/tests -p 'test_*.py'` | **153 PASS**, no skips |
| `node scripts/desktop-package-workflow-check.mjs` | PASS static policy, not hosted execution |
| Actual locked/offline metadata/collector | PASS mechanical catalog identity/material checks; attribution finding remains |
| Independent archives/resources/component/legacy inspection | PASS exact byte checks stated above |
| `python scripts/desktop-license-review-tests.py` | **1 FAIL / 1 test**, retained embedded-attribution regression |
| `git diff --check` | PASS |

Use the pinned executables rather than an ambient older Python (ambient Python
here is 3.9.12 and was not used for collection/tests). Reproduce the RED command
with provisioned dependencies, own TEMP/TMP and `PYTHONIOENCODING=utf-8` for the
exact author spelling in logs. Reproduce collection with the author document's
`rust_notices(os.environ.copy())` command. No test failure was waived, normalized
into PASS or removed from the gate. The new test remains separate RED evidence.

Local private evidence lives outside Git in sibling `license-review/`. Sanitized
SHA-256 bindings:

| Input/evidence | SHA-256 |
| --- | --- |
| Frozen packager | f49ecce6c973bc3366621511e087e883bb696395503a6d4c3c323c23f7f66973 |
| Frozen catalog | ce2399f4ef8991b78296929af386de636c5c906537b5aacc9404ad7465c329d8 |
| Actual collection review JSON | d86ce3fe5c12367d0d43d17fc99d2b0f626d10c4014b76322efc60508fb72937 |
| Actual component review JSON | 9766b75b40eabce3a7190e0d198197068777b5a4f31654639416d4e5c5acea51 |
| New regression source | 4dd2429163c31b6a6a0250651be08925b9a10256958d93c6919169e368bdaeef |
| Actual RED UTF-8 log | ea1a05bd8b374e0c41da4e5197ec46de39f05bb8dd49817f6797ef0f0a762042 |
| Read-only worker commands | 90869ce6aa9e3052e866e0b1a50804c4c105e168146ec873bfb037ed26b3f66b |
| Read-only native header dependencies | 2db745acaae0b01cf62cde38a6961dffb3dfa6d2947931b1a9683d7608f79c74 |

Next runnable work: coordinator resolves the native embedded attribution finding,
reviews the separate MSVC addendum, repeats the same regression and collector
against the combined root-workspace lock, then separately authorizes a fresh
normal package/raw reproducibility gate. No new raw package comparison, offline
installation/runtime, GUI, model, Android/physical-device, signed release, legal
or public-distribution gate is qualified by this review. Full D09 stays open.
