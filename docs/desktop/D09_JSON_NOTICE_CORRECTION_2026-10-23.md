# Pinned JSON header attribution correction — 2026-10-23

Refs #31, partial D09.03/.05/.07, claim 6371627124. In review, not full D09
or distribution approval. Source fix `c74c54ca078d1b2113caeb22d76bb364f5a96ef1`
is separate from the immutable original collector `c11a79d`/`c6be162` and
MSVC addendum `d6f663e`/`40ce967`. Their recorded results are not rewritten.

## Observed failure and focused change

Independent review supplied actual-collector regression
`264f4d5413009854bdd091f2816654ac0a604342`, with report
`04dcf25cb9b8434013001a1781d32c727c3c65f2`. The retained approved worker's
actual Ninja dependency record includes `vendor/nlohmann/json.hpp`. Its
pinned source has additional author notices that the original root MIT notice
alone did not preserve. This is a concrete inventory gap, not a model-quality
or worker-behavior issue.

The same unchanged reviewer test (SHA-256
`4dd2429163c31b6a6a0250651be08925b9a10256958d93c6919169e368bdaeef`)
was executed against the actual collector here: **1 test failed before the fix**
(missing Hoehrmann/Loitsch names), **1 passed after the fix**. The test bytes
were read directly from the reviewer commit and executed unchanged with this
checkout's package module. The reviewer owns the original regression/report;
this author does not present the fix as independent approval.

The new `nlohmann-json-header-notices.txt` resource preserves exact notice
excerpts from [the pinned llama.cpp header](https://github.com/ggml-org/llama.cpp/blob/620d2225cc436ab0b001e3200e590e3b286ef9ab/vendor/nlohmann/json.hpp).
Source SHA-256 is
`f9ce5c0a1ac99e20ef92daeb60eb571e2146988daa553ac0269755348843efd7`.
The resource is **2,491 bytes**, SHA-256
`c81b7f95cf00d14e71d32c3586e690cc012e6f3bb9eee9dc914d6a2154bda24e`.
All five distinct SPDX copyright holders in the exact header are retained:
Niels Lohmann, Evan Nemerson, The Abseil Authors, Björn Hoehrmann and Florian
Loitsch. Original line ranges and source hash are catalog-bound; labels explain
their source and applicability. Notice excerpts retain original wording with
LF line endings. Existing required MIT and Apache-2.0 text members are referenced.

| Source lines, one-based | Notice/applicability |
| --- | --- |
| 6–7; 340–347 | Root Niels Lohmann MIT and Hedley/Evan Nemerson MIT declarations. |
| 3198–3200; 3233–3234 | Original Abseil author declaration and Apache-2.0 source reference. The utility implementation is under `#else` of `JSON_HAS_CPP_14` at 3219/3227. |
| 17609–17611 | Hoehrmann UTF-8 serializer attribution, outside the Abseil conditional. |
| 17635–17637; 17655–17663 | Loitsch conversion attribution/MIT declaration, outside that conditional. |
| 19869 | Additional original Hoehrmann copyright declaration. |

The worker uses C++17. Conservative inclusion of Abseil's notice does **not**
assert that its pre-C++14 fallback compiled or contributed binary symbols.
Header consumption and source attribution are not a per-template link map.

## Actual checks and evidence

Windows x64, pinned Python 3.14.9 and Rust 1.93.1 metadata; task-owned D: temp
and artifacts. No dependency, toolchain, runtime, worker/model/profile pin,
product/frontend/Host/Storage/Android changes.

```powershell
python scripts/desktop-package-tests.py
# Execute unchanged reviewer regression from commit 264f4d5 against this package module.
# Local exact driver: msvc-notice-artifacts/run-review.py
git diff --check
```

**30 package-policy tests pass**, zero failures/skips. The additional own test
checks the actual catalog/resource identities, all five names, license-member
references and honest conditional applicability. The unchanged independent
reviewer test separately passes **1/1** against the actual cached collector.
The MSVC source had already passed 20 unchanged checker and 153 runner/helper
tests; neither runner's implementation changed in this correction.

Actual locked/offline `rust_notices(os.environ.copy())` collection at the fixed
source: unchanged **250 registry + 6 local** identities, **467 materials /
2,888,215 bytes**, unchanged five MPL source archives / 150,290 bytes. New
catalog SHA-256:
`07c8f47f8062e8bed24857e103be9f97bf8b2d2292ed0b17d0a90fe597986bf8`.
Source inventory: 287 files. Changing or deleting the **actual collected** JSON
header notice and then resealing the file manifest is rejected in both cases by
the trusted-catalog packet verifier. Material-only in-memory validation passes;
it uses retained historical public app/worker bytes and is not a compiled package.
No new ZIP is written. The original 446-member ZIP remains unchanged,
`3f13d9a22e64866b40c9e6e8fae05efa3867461b9fd5e5bc56088aea1f4e545b`,
and remains `legacy_unreviewed`.

[Sanitized evidence](D09_JSON_NOTICE_EVIDENCE_2026-10-23.json) binds source,
catalog, resources and local log hashes. Exact drivers/reports are in the local
`nlohmann-notice-artifacts` and `msvc-notice-artifacts` directories. An initial
test-wrapper setup attempt discovered zero tests; that log is retained and is
not counted as a pass. The corrected wrapper's before/after runs each execute
exactly one unchanged test.

## Remaining gates

Independent review of this resource correction and the complete exact catalog
remains pending. Legacy `license_audit_complete`, `review_complete` and
`distribution_approved` remain false. Mechanical catalog-byte coverage is not
legal/release signoff. Final combined package collection/source binding, the
separate MSVC runtime/terms review, prerequisite/offline-installation checks and
full D09 acceptance remain separate. No new package/native build,
app/worker/model/device execution, desktop control, release or merge occurred.
