# Frozen record cancellation UI build attestation

M10.02 `RECORD_CANCELLATION_UI_BUILD_HANDOFF`, supporting M09.04/M09.06.

This component verifies the existing PR #386/B110 record cancellation artifacts
before a separate owner/profile integration can consume them. It returns data;
it does not grant run authority, register a profile, reserve storage, prepare or
boot a guest, start ADB, run Android tests, or copy a model.

## Fixed inputs and interface

The tooling parent is PR #384, commit
`b1ba494248bb0d9f55661081ddb27175d1eb3cc9`. The independently frozen product is
PR #386, commit `7e29fb724ed781e953f321385f66a5f8982ad0f1`, depending on
PR #385. Rebuilding the tooling branch does not replace the frozen product artifacts.

`benchmarks.record_cancellation_ui_build` exposes:

- `create_manifest()`: return a detached, deterministic manifest without writing it.
- `verify_frozen_product(artifacts)`: verify exactly `build`, `product_apk`, and
  `test_apk`, each with exactly `path`, `bytes`, and `sha256`.
- `python -m benchmarks.record_cancellation_ui_build create|verify`: print JSON
  from the repository root. Exit 0 means success, 1 a safe refusal, 2 invalid
  arguments. There are no root, path, selector, or profile overrides.

The 741,682-byte baseline has SHA256
`8cce430fa23ffa1562e2f0397e6cbebd763183a6c2de79fec2bac27416048cce`.
It pins 2,589 product source files and their raw Git blobs/modes, phase requests,
owners, launches, workers, before/after maps, logs, JUnit, APKs/copies, lint,
alignment audits, and compiled roster. Raw source bytes are not newline-normalized.
The focused/full/package XML cohorts contain respectively 3/425/0 cases across
1/50/0 suites; packaging does not earn credit for old XML.

The fixed class is `org.locallore.app.StoryRecordCancellationScreenTest`.
Selectors `record_cancel_1` through `record_cancel_5` map in order to:

1. `cancelledCurrentPageShowsSafeRetryAndReusesTheExactFrozenCursor`
2. `cancelledScopedDetailRendersSafeProblemAndRetriesTheSamePlayerLens`
3. `obsoletePageCancellationCannotReplaceSectionSelectionOrClosedAndReopenedRecords`
4. `oldDetailCancellationAfterBackCannotFinishTheReplacementDetail`
5. `disposedOwnerAndRemountedScreenCannotBorrowOldReadsOrRetainedCallbacks`

The current bounded DEX parser verifies actual method code items. The old
compiled proof's parser hash is checked against its frozen product source, not
mistakenly equated to the newer tooling parser. `current_native_bindings` joins
recorded alignment audit facts to the fixed whole APK; it is not fresh ELF or
native execution evidence.

## Boundaries and failure behavior

The shared guarded physical-D reader checks file/ancestor identities, single
links, sizes, hashes and a final reread. Limits are 128 MiB per file, 2 MiB per
JSON, 512 MiB guarded reads, 256 MiB retained raw bytes and a cooperative
120-second reader deadline. These are logical reader bounds, not RSS limits or
hard preemption of OS I/O. Strict JSON rejects duplicate keys and nonfinite
numbers. Git/source, phase, package and compiled proof joins must all agree.

Malformed roles and `None` refuse before reader construction/baseline loading.
Foreign caller-provided artifact paths refuse before any artifact read attempt. Ordinary exceptions
cross public boundaries as fixed, whitelisted refusal categories; private error
text is not returned. `KeyboardInterrupt` and `SystemExit` still propagate.

The manifest's recorded JVM count is not a new JVM run. Android, native, model,
run-authority and feature-acceptance facts remain false. A manifest is neither
user consent nor ledger admission. Existing SDK16/SDK17 profiles are unchanged;
this component does not enable a new profile. A separate fixed owner adapter,
capacity admission, reviewed proposal and fresh exact device approval remain
necessary before execution.

See [verification](RECORD_CANCELLATION_UI_BUILD_VERIFICATION_2026-11-03.md).
