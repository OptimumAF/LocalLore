# Fixed Knowledge UI build inputs

B88. Refs #14 (M10.02), supporting #13 (M09.04/M09.05/M09.06).
This is the build-attestation prerequisite for a later bounded SDK16 profile,
not an executable target runner, device result, approval or milestone acceptance.

The product is fixed at
`D:/Worktrees/LocalLore-record-query2-fixtures-v1`,
`286c0905613e9bbff2d69796155105339000eceb` (PR #358), with 2,608 raw tracked
inputs. Capture is `D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-build-v1`;
selected copies use the matching `D:/Dev/Recovery/LocalLore` child.
The prospective manifest is that capture's `knowledge-ui-build-v1.json`.

`benchmarks/knowledge_ui_build.py` exposes only `create_manifest()` and
`verify_frozen_product(artifacts)` as build interfaces. Construction/import
does not publish, observe a device, admit storage, start a process owner or infer
authority. Creation returns validated metadata; the second interface accepts
exactly `build`, `product_apk`, `test_apk`, with fixed literal paths and byte
bindings, and returns a fresh copy of the validated manifest.

The baseline identity belongs to the literal development path
`D:/Worktrees/LocalLore-original-input-compose-review-v1/benchmarks/knowledge_ui_build_baseline.json`,
not the reader's module location. Its byte count/hash are frozen in code after
the actual current build. Moving a reader cannot retarget the baseline/product.
No input selects another path, build, profile, selector, model or implementation.

The closed baseline contains `version`, `scope`, `product`, `evidence`,
`artifacts`, `native`, `bindings`, `facts`, `instrumentations`:

- Version 1 / scope `knowledge-ui-build-baseline-v1`.
- Product: fixed root/head/count, raw `source_before`, `source_after`,
  `source_archive` pins and explicit raw-byte encoding (no normalization).
- Evidence: actual request/owner/terminal/command-terminal/stdout/stderr,
  report-preservation/helper/actual-child/command-child pins. Two additional
  recorded proof pins, `jvm_execution` and `dex`, bind the separately forced
  current JVM phase and actual compiled-class/method/JUnit/native-entry analysis.
  All nested fresh-JVM evidence pins remain byte-bound; no proof is execution
  authority or a repeat of those tests by the attestor.
- Artifacts: fixed product/test APK pins; native: ordinary extracted arm64 and
  x86_64 library pins. `bindings` holds the exact recorded source/copy pairs.
- Facts record actual JVM counts, selected/compiled methods, package/audit
  review and explicit false Android/model/feature-acceptance/fresh-native flags.
- Instrumentations are the following exact ordered four triples, all in
  `org.locallore.app.ui.KnowledgeRecordFilterScreenTest`:

| Claim | Method |
| --- | --- |
| `knowledge_labels` | `exactlyFiveKnowledgeFacetsExposeLiteralLabelsSelectionAndFortyEightDpTargetsOnlyInKnowledge` |
| `knowledge_replaced` | `retainedRealFacetAndCloseActionsCannotRetargetDifferentOrEqualDistinctSuppliedViews` |
| `knowledge_remount` | `removedAndRemountedSameStateCannotReviveOldFacetOrCloseButFreshActionsStillWork` |
| `knowledge_text` | `doubledFontKeepsEveryFacetAndUnchangedOriginSourceAndCloseReachableInTheActualDialog` |

The manifest has exactly `version`, `scope`, `mode`, `product`, `artifacts`,
`current_native_bindings`, `evidence`, `facts`, `instrumentations`. Scope is
`knowledge-ui-build-v1`, mode `fixed-b88-byte-attestation-v1`. It is recorded
byte attestation, not a repeat of compilers, DEX/ELF/signature semantic tools or
Android execution. The four real UI definitions must be evidenced in the test
APK and absent from product; no synthetic/mock result substitutes for that build.

The unchanged guarded reader from `library_ui_build` supplies held-stream and
path/parent checks, 120 seconds and 512 MiB total read limits. Only ordinary,
single-link physical D: files are consumed here; its old Cargo alias exceptions
are unused. All source files and fixed Git identity are revalidated, with strict
closed keys/types and canonical comparisons that distinguish booleans/integers.
Failures produce a bounded public `BuildRefused` category, never private output.

PR #354's existing operator/source/product/APKs/proposal and SDK15 selectors
remain frozen. This interface grants no boot, recovery, ledger migration, model,
deletion or execution authority. The next integration must use current shared
storage/SDK4/SDK5 mechanisms and obtain its own applicable bounded-run approval.
