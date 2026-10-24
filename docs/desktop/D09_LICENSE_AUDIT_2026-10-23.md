# D09 Windows developer-package notice/source audit, 2026-10-23

Refs #31 D09.03/.05/.07, partial prerequisite. **In review.** Tested source
`c11a79ddb89cb13c6f1629ac784b230a24f7cdf6`, based on accepted
`da2ff017baa4b3d08ac7f7c21c26d978cb81a89d`, in isolated
`impl/d09-package-licenses`. [Read-only claim](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6370536408),
[implementation ownership](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6370734141),
and [narrow formatting addendum](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6371145859).
The legacy `license_audit_complete` flag remains **false**, and both catalog and
report enforce `review_complete:false` / `distribution_approved:false`.
No license-policy, root LICENSE, dependency version, worker/model pin, release,
signing or repository-setting change is introduced.

## Exact scope and inputs

The existing normal Windows metadata traversal selects **256 packages: 250
registry and six first-party packages**. Fresh `--locked --offline
--no-default-features --filter-platform x86_64-pc-windows-msvc` metadata matches
the retained normal package inventory exactly. This is a conservative dependency
closure including build/proc-macro dependencies, not a per-symbol linker map.
The catalog records every selected identity, registry checksum, license expression,
required text hashes and public provenance. All available alternative texts are
retained; the three current `AND` expressions have explicit operand coverage.
The collector does not guess a legal election from a generic SPDX allowlist.

The first-party crate entries previously had no per-crate notice file, but the
root Apache-2.0 LICENSE was already shipped. The new inventory explicitly aliases
all six to that unchanged root text. Existing third-party notices are retained.
The five missing external texts are resolved from these sources:

| Package | Source / resulting material |
|---|---|
| alloc-stdlib 0.3.0 | [Exact upstream revision LICENSE](https://raw.githubusercontent.com/dropbox/rust-alloc-no-stdlib/0a81fd6928ea3b33c8cd484aa4575d50ffb98012/LICENSE), BSD-3-Clause |
| selectors 0.38.0 | Published source-file MPL headers and [Mozilla's MPL-2.0](https://www.mozilla.org/en-US/MPL/2.0/); full matching text copied from cached cssparser 0.37.0 LICENSE |
| webview2-com 0.39.1 / webview2-com-sys 0.39.1 | [Repository MIT license at edc2caf](https://raw.githubusercontent.com/wravery/webview2-rs/edc2caf886175ccaebe86078c9cfe1ae2a187328/LICENSE) |
| webview2-com-macros 0.8.1 | [Repository MIT license at its distinct dffa41a revision](https://raw.githubusercontent.com/wravery/webview2-rs/dffa41a8a46d3f5565eefbff2de57d38d399f158/LICENSE); same verified text |

The actual published crate revision metadata is recorded, rather than assuming
all three WebView2 crates share one source revision. Official pinned root
LICENSE guesses for selectors returned 404; no missing upstream text was
invented. Its actual source headers and the canonical MPL establish the text.

## Source availability and native components

Mozilla's [MPL section 3.2 and FAQ Q8](https://www.mozilla.org/en-US/MPL/2.0/FAQ/)
explain source availability and recipient information when distributing covered
executable code. The conservative package includes the **exact five already-cached
upstream .crate source archives**, checksum-verified against the consumed lock:

| Archive | Bytes |
|---|---:|
| cssparser 0.37.0 | 56,860 |
| cssparser-macros 0.7.1 | 8,197 |
| dtoa-short 0.3.5 | 8,287 |
| option-ext 0.2.0 | 7,345 |
| selectors 0.38.0 | 69,601 |
| Total | **150,290** |

They occupy only the exact allowlisted `SOURCES/MPL/<name>-<version>.crate` names.
The README and `NOTICES/MPL-sources.json` identify their format, license and exact
versions/hashes. These are original gzip-compressed tar source archives. The
packager neither extracts nor executes them and never fetches anything. Source
archive bytes are absent from Git; they are copied from the already-provisioned
Cargo cache only during package collection. Fixed limits are five archives,
131,072 bytes each and 262,144 bytes total. Original archives have no symlink or
hardlink entries; that was inspected without extraction. Four dependencies are
runtime-eligible by Cargo dependency-kind traversal; cssparser-macros is a
build/proc-macro dependency. Including all five is conservative and does not
assert all five are linked into the final executable.

Read-only `ninja -t commands locallore-llama-worker` and `-t deps` on the retained
qualified build establish the worker target/header closure. No compiler or
worker was run. The closure contains 137 build/link commands. In addition to the
existing ggml MIT notice, the public catalog preserves:

- [nlohmann/json 3.12.0 MIT text](https://raw.githubusercontent.com/ggml-org/llama.cpp/620d2225cc436ab0b001e3200e590e3b286ef9ab/licenses/LICENSE-jsonhpp).
- [cpp-httplib 0.61.0 MIT text](https://raw.githubusercontent.com/ggml-org/llama.cpp/620d2225cc436ab0b001e3200e590e3b286ef9ab/vendor/cpp-httplib/LICENSE), plus its distinct 2026 source-header copyright.
- [llamafile sgemm's Mozilla 2024 MIT header](https://raw.githubusercontent.com/ggml-org/llama.cpp/620d2225cc436ab0b001e3200e590e3b286ef9ab/ggml/src/ggml-cpu/llamafile/sgemm.cpp).

All use approved llama.cpp revision `620d2225...`; the worker stays
`b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`.
The repository also contains base64/Unlicense, sheredom and hash libraries, but
vendor presence alone is insufficient: they are outside this worker's inspected
closure or disabled by `LLAMA_SUBPROCESS=OFF`. They are not claimed embedded.

The Rust WebView2 wrapper MIT license does not cover the separate Microsoft
loader automatically. [The exact pinned updater](https://raw.githubusercontent.com/wravery/webview2-rs/edc2caf886175ccaebe86078c9cfe1ae2a187328/crates/update-bindings/src/main.rs)
selects SDK **1.0.3800.47**; the cached DLL version agrees. The official
[NuGet license for that SDK](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.3800.47/License)
is Microsoft BSD-3-Clause-style text and is included separately. The web tool
could not fetch that page; a bounded standard-library HTTPS request returned
200, and its original license `<pre>` text was extracted with HTML entities
decoded. The source-controlled text uses LF with unchanged wording. The static
x64 loader library is 10,500,472 bytes, SHA
`89c6b872783b8f6c3cedbff618adb42082d455c615453ae10cfc753f1e8f25d8`.
[Microsoft's distribution documentation](https://learn.microsoft.com/microsoft-edge/webview2/concepts/distribution)
distinguishes the loader from the externally installed WebView2 Runtime. The
package still ships no Runtime or VC prerequisite installer/DLL collection.

Rust's [pinned copyright guidance](https://raw.githubusercontent.com/rust-lang/rust/1.93.1/COPYRIGHT)
identifies `COPYRIGHT-library.html` as the standard-library subset of its binary
release notices. That installed 425,661-byte document and relevant canonical
license texts are included. It conservatively spans targets; it is not proof
that every component listed there links on Windows. No compiler/toolchain
executable is packaged. The libsqlite3-sys 0.38.2 wrapper MIT notice was already
included; bundled SQLite 3.53.2 has separate source/hash and
[public-domain provenance](https://www.sqlite.org/copyright.html).

The installed MSVC 14.34.31933 `xutility` header declares Apache-2.0 with
LLVM-exception. [Microsoft STL's official license](https://raw.githubusercontent.com/microsoft/STL/main/LICENSE.txt)
contains an object-embedding exception. Generic Apache/LLVM texts are already
included, but this packet does not establish complete per-header MSVC attribution
or redistribution rights for a whole toolchain. That applicability assessment
remains part of independent review; no toolchain source or binary is copied.

React/React DOM 19.3.1 and scheduler 0.28.0 existing MIT texts and original esbuild
legal comments remain. Their exact package versions, lock hash, text hashes and
actual generated legal-comment bytes must match the catalog; new generated
comments cannot be silently replaced with an older notice file.
The unchanged runtime profile hash is also bound to the scope report. The Qwen
profile is metadata only: [its pinned upstream model license](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/blob/23749fefcc72300e3a2ad315e1317431b06b590a/LICENSE)
is recorded separately, and no weights are read, copied or redistributed here.

## Collector and verification behavior

`collect_license_materials(meta)` returns `(files, inventory, scope_report)`;
`rust_notices(env)` obtains actual offline metadata then uses that same collector.
The consumed lock comes from `meta.workspace_root`, supporting the current
standalone desktop and the proposed root-workspace alignment. Only the exact
selected graph can reach material reads; unselected manifest paths are ignored.
Unknown identities, versions, checksums, license expressions, missing AND
operands, changed texts/resources/cache inputs or frontend lock fail before
publication. Native loader/amalgamation inputs are checked too.

The new catalog is trusted source-controlled policy input, not supplied by an
archive. Package verification compares the exact report and required files to
that catalog, including registry inventory, runtime-profile identity and source
archive hashes. Recomputing an archive's own manifest cannot authorize changed
texts, hidden extra notices, foreign sources or approval claims. Generated
inventory/report names are reserved. There are at most 1,024 material members
and 16 MiB aggregate declared material bytes, with existing notice/archive and
whole-package limits retained. There is no general source archive exception.

`coverage_complete:true` means that all catalog-required material bytes are
present. It does **not** mean independent/legal review or distribution approval;
those fields remain false, and the remaining gaps are carried in every report.
Historical packets with no scoped report remain inspectable only as
`legacy_unreviewed`. Removing a report cannot turn an old or stripped packet into
an audited one; new build publication explicitly requires the scoped report.
The new inventory's notice paths refer to package members, not cache paths.

The source inventory binds `licenses/desktop` and `.gitattributes`. Sixteen public
text assets are canonical LF and were checked equal to their staged Git blobs,
preventing a clean checkout's line conversion from invalidating their hashes.
Upstream trailing whitespace/blank EOF is intentionally preserved. Only
`licenses/desktop/texts/*` has the approved whitespace attribute disabling those
two cosmetic checks; ordinary source-code whitespace checking is unchanged.

## Measured checks and reproduction

Source-bound Python 3.14.9, Node 24.22.1, Rust/Cargo 1.93.1 on Windows 11 26300.
Existing tools/cache only; no provisioning, installs or downloads except the
small official public license-text requests. Own D: temp/artifacts, no model
assets or protected checkouts changed.

| Command | Actual result |
|---|---|
| `python scripts/desktop-package-tests.py` | **27 PASS**, 0 fail/skip: original 12 plus 15 new license regressions |
| `python scripts/desktop-reproducible-tests.py` | **20 PASS**, 0 fail/skip; original byte/refusal tests preserved |
| `python -m unittest discover -s scripts/tests -p 'test_*.py'` | **153 PASS**, 0 fail/skip |
| `node scripts/desktop-package-workflow-check.mjs` | PASS static workflow/pin policy; no hosted workflow execution |
| Actual `rust_notices` / source inventory | PASS exact 256 identities; **463 material files / 2,854,428 bytes**; source inventory 283 files binds catalog/texts/attributes |
| In-memory materials-only packet validation | PASS catalog-bound files/report with retained public test app/worker bytes; **not a new build/package** |
| Historical 446-member normal package inspection | PASS format/inventory; explicitly `legacy_unreviewed`; original ZIP SHA unchanged |
| `git diff --check`, resource Git-blob/checkout equality | PASS with narrow approved third-party formatting rule |

The existing package CI entrypoint loads the new suite, without workflow edits.
Regressions cover selection-before-read, version/source/checksum/expression drift,
AND text removal, changed root/resource/native/frontend material, source archive
hash/count/budgets/names, forged/resealed reports/inventory/profile/approval,
extra notices, source-binary namespace, aggregate caps, reserved names and legacy
downgrade labeling. All are synthetic; the actual public catalog/text hashes and
actual cached-source collection are checked separately.

Reproduce collection from a provisioned clean checkout without building/launching:

```powershell
python -c "import importlib.util, os, json; s=importlib.util.spec_from_file_location('p','scripts/desktop-package.py'); p=importlib.util.module_from_spec(s); s.loader.exec_module(p); files, inventory, audit=p.rust_notices(os.environ.copy()); print(json.dumps(audit,indent=2)); print(len(files))"
```

This invokes only pinned Cargo metadata and bounded file reads. It needs the
existing locked registry cache and normal frontend dependency files. It uses no
network, downloads, source extraction, compilation, native app, worker or model.
The [sanitized evidence](D09_LICENSE_AUDIT_EVIDENCE_2026-10-23.json) records exact
source/catalog hashes, original archive hashes, counts and raw-log hashes. Full
metadata, loader/license retrieval evidence, source-archive inspection, read-only
Ninja closure and logs remain in local `package-license-artifacts/`.

## Remaining gate and handoff

No new normal frontend/native developer package, raw two-path reproducibility
cohort, native WebView image, app journey, model/device run, offline observation,
installer, prerequisite redistribution, signing or release occurred. Historical
clean01/02 byte failures remain unchanged. The inspected legacy ZIP remains
`3f13d9a22e64866b40c9e6e8fae05efa3867461b9fd5e5bc56088aea1f4e545b`.
Its successful format verification does not repair its missing scoped notices.
No dependency/advisory change is made; Windows graph exclusion is not remediation
of the existing GLib advisory on other selections.

Next: coordinator independently reviews catalog provenance/coverage, integrates
with the pending workspace/retention changes, repeats actual collection against
the combined consumed root lock, then authorizes a fresh ordinary package and
unchanged raw-byte gate. Do not change the legacy audit flag, claim licensing
compliance, approve public distribution or mark D09 complete from this packet.
