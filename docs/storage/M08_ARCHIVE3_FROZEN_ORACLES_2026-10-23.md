# Archive3 frozen Store oracles — 2026-10-23

**Source-only; all 13 tests UNCOMPILED / UNRUN.** This packet freezes independent
oracles before Archive3 implementation, not acceptance evidence for #12
M08.04/M08.06 or #30 D08. The coordinator approved the exact contract in
[#12 comment6378000457](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378000457).
The contract is [M08_ARCHIVE3_IMPLEMENTATION_CONTRACT_2026-10-23.md](M08_ARCHIVE3_IMPLEMENTATION_CONTRACT_2026-10-23.md).

## Freeze, ownership and actual interfaces

- Base: `ff58727`, coordinator's import of the approved contract.
- Branch/worktree: `test/m08-archive3-frozen` / `source-archive3-oracles`.
- Test freeze: `b85b917d51430a1059273b5ad8034ea39716c00a`.
- Only new test paths and SHA256:

| File | SHA256 |
| --- | --- |
| `crates/locallore-storage/tests/m08_archive3.rs` | `5d9e3dbea14ae732b2f82162993fd24681aaa4a21244a80817afff85405fe880` |
| `crates/locallore-storage/tests/m08_archive3_hostile.rs` | `643b16a93c406c37f88407e3a1f7f0cd9dfdb0b7c3f02b8fcb3d95c3be6fea67` |

Claims before edits: [#12](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378010030)
and [#30](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6378010252).
Reviewer owns only these two new tests and this new document. Existing
production, tests/assertions, fixtures/assets, migrations, dependencies, platform
code and runtime resources are unchanged. Root owns implementation and all
actual execution/qualification.

The actual APIs are `Store::export_archive`, `validate_archive` and
`Store::import_archive` (there is no invented `export_playable` convenience
API). Histories use actual public Store author prepare/apply, fork, typed
begin/commit, branch deletion and reopen. Actual Core supplies canonical records,
projection, opaque accepted-history bases and actor V2 contexts. There is no
fake persistence port, forged native Receipt, provider, copied resolver,
alternate parser/validator or test SQL writer. Each test owns a unique bounded
synthetic temp directory and drops Store owners before removing it.

The approved count contract is explicit: preview/outcome `committed_turns`
counts **committed canonical records**, including author rows for version3.
Tests require preview3 to omit retirement when empty; Payload3 must contain an
empty array. Nonempty retirement is preserved in both. Product “Accepted
records” labels and closed platform decoders remain a separate prerequisite.

## Seven actual-history tests

| Frozen test | Oracle |
| --- | --- |
| `full_mixed_roundtrip_preserves_sources_a_b_a_native_bases_and_original_turn_recovery` | Actual legacy prefix, private sibling, author B, two discoveries in one turn, author A and rediscovery A. Late parent continuation remains separate. Export/validate/import/reopen/re-export preserve complete records, seed, projection, native bases and player/Mira/Sable contexts at all active heads. Three discovery views retain B/B/A and distinct event identities. Author reason and sibling data remain full-private archive content, excluded from the unrelated actor context. Preview/outcome count7 records across4 branches; ordinary exact-key status/begin/commit recovery returns original receipts without duplication; imported author lookup is a known existing result. Actual typed continuation appends once. |
| `equal_projection_and_head_cannot_erase_different_private_author_sources` | Two actual same-scope/head mechanical-and-knowledge projections have different B/C author records and native bases. Payload hashes differ; each import preserves its actual complete source. This prevents treating projection hash alone as full source identity. |
| `actual_retirement_preserves_author_prefix_prebirth_rewind_and_collected_identity` | Actual author parent born at4 is rewound to1; retirement keeps the birth floor4 and discards its later author row. A different retained author at5 remains required by a live descendant. A deleted leaf becomes a tombstone. Import/reopen preserve active bases/contexts, hide retired targets, preserve all reserved identities, omit discarded private values, and re-export exact current bytes. |
| `cancellation_panic_and_progressive_import_polls_leave_foreign_canon_unchanged` | True/panicking validator callback closes as Cancelled. A successful disposable import measures its actual callback count; independent fresh targets cancel at initial, early, middle and final precommit polls and also panic in the middle. Every failure leaves the unrelated story's full records/projection/native basis unchanged and no imported story. This is callback cancellation/atomicity, not OS process death or Full. |
| `winning_import_reopen_and_identical_or_divergent_identity_retry_never_overwrite` | After a successful import and owner reopen, identical and source-continued archives of the same story ID are Conflict. Imported and unrelated original bases remain unchanged, with exactly2 saved stories. This proves Store identity policy; it does not simulate a native lost acknowledgement. |
| `immutable_archive1_and2_assets_keep_original_bytes_and_domain1_export_selection` | Pin3 existing asset hashes, validate/import their unchanged1/2 bytes, and require current Domain1 export to select1/2 with local_receipts. Exactly the truthful source-schema field and dependent payload digest are normalized for comparison against the historical input; all other receipt, lineage, reference and projection integrity fields must match. Old source metadata/assets are never rewritten. |
| `maximal_escaped_author_fields_roundtrip_full_wrapper_and_private_reason` | Actual valid escaped 2048-character replacement/reason produces a full record above24,576 bytes but within65,536. The full author wrapper and actual recovery identity survive import. No widening of ordinary request limits is implied. |

## Six hostile groups / 52 serialized counterexamples

Every mixed source archive first comes from the actual public Store export.
Hostile edits recompute canonical payload, seed and complete local-record hashes.
They retain the original replayed-projection digest; there is no synthetic
projection authority or duplicate Core implementation. Validation must reject
before granting an import capability. If a capability is incorrectly granted,
the test attempts actual import into its disposable target and fails explicitly.
All refusal cases also check a real foreign destination story remains unchanged.

| Frozen group | Counterexamples |
| --- | --- |
| `recomputed_hashes_do_not_admit_changed_author_or_discovery_source_wrappers` |16: unknown wrapper version/kind, extra author field, wrong prior value, future before-source, author witnesses, missing/empty observation bindings, seed truth substitution, sibling/future truth refs, conflated discovery event, wrong actor/story, inconsistent accepted proposal, duplicate original turn. Require Integrity. |
| `recomputed_hashes_do_not_admit_broken_lineage_caps_or_retirement` |12: cycle, missing parent, fork/head splitting a multi-event discovery, root parent, retired root/unneeded leaf, unsorted/duplicate/invalid tombstones, branch order and rescoped author. Require Integrity. |
| `exact_archive3_tuple_and_required_field_sets_are_closed` |12: domain/source-schema/transcript mismatch, future4, downgrade to1/2, partial privacy, missing/null required retirement, unknown payload and ambiguous local_receipts/local_records. Require closed Unsupported/Malformed. |
| `archive3_domain2_claim_requires_real_author_history_and_exact_projection_digest` |2: ordinary actual legacy data relabeled as3/domain2 without a Domain2 source, and wrong replayed projection checksum on genuine mixed history. Require closed Unsupported/Integrity as applicable. |
| `invalid_bytes_duplicate_keys_and_untrusted_payload_hashes_never_grant_import` |5: truncation, invalid UTF-8, duplicate version key, appended document, and bad payload checksum. Require Malformed/Integrity. |
| `enforced_archive3_caps_cover_complete_private_wrappers_counts_and_envelope` |5: full author wrapper above65,536 bytes,4097 canonical records including authors,33 physical branches,257 retirement identities, and input above32MiB. Require TooLarge before expensive semantic replay. |

Checksum editing demonstrates that structural/semantic validation is necessary;
it cannot establish authenticity of the original author. A coherent replacement
of an author reason is not inherently invalid. The extra-author-field vector
therefore tests a closed receipt shape, not a fictional signature guarantee.

## Historical bytes pinned without replacement

| Existing immutable input | SHA256 |
| --- | --- |
| `apps/android/app/src/androidTest/assets/platform-roundtrip-v1/windows-origin.json` | `ac77f1144db9de68c0d01241949f85f21660da6526b241cb9e947277b3c27fbb` |
| `apps/android/app/src/androidTest/assets/platform-roundtrip-v1/windows-continued.json` | `31f7bdb6904d8759186f0586b80c79b0346d9e9d03f04c015c409a1f1670ec6a` |
| `apps/android/app/src/androidTest/assets/parent-retention-v1.json` | `5cc8eea595258669c1ebb04a15c0a8d642e43be0e534a35cd776920883d62dc7` |

These are repository source hashes actually read during this source pass,
not newly executed desktop/Android transfer results. Current export reports
physical DB5 truthfully; the historical assets retain their original metadata.

## Execution and limits

Actually executed by this reviewer:

```text
rustfmt --edition 2021 crates/locallore-storage/tests/m08_archive3.rs crates/locallore-storage/tests/m08_archive3_hostile.rs
git diff --check
```

Both succeeded. Git/source/API inspection and file SHA256 collection also ran.
No Cargo, typecheck, Node, Gradle, SQLite, provider, native application, JNI,
WebView, emulator/device, model or desktop-control execution ran. At the frozen
base mixed export is explicitly Unsupported; actual RED must still be measured,
and a fixture setup failure must not be reported as per-vector semantic RED.

Coordinator next imports the unchanged frozen tests and retains first actual
results under its exclusive slot:

```text
cargo test --locked -p locallore-storage --test m08_archive3 --test m08_archive3_hostile -- --nocapture
```

Implementation follows that freeze. Re-run the unchanged oracles, then existing
archive1/2, branch retention, author, normalized Store, cancellation and broader
compatibility suites. Preserve each actual fixture/typecheck/behavior failure
with its precise attribution before narrow correction.

Deliberate remaining gates: no actual SQL Busy/SQLITE_FULL pressure hook or
claim; no near16MiB response-plus-index boundary construction, per-model cap or
full32-depth sweep; no Play2.5 provider/metadata reference round trip in this
packet (typed Domain2 records are real, generated Play is separately owned);
no native lost-ack/cross-surface gate, process death, frontend rendering,
desktop↔Android execution or physical phone qualification. Cancellation tests
compare public full canon and story absence, not all derived/raw SQL tables or
bitwise SQLite files. Existing suites and separately allocated schema5 real
pressure/platform gates remain required. Do not reuse schema4 capacity evidence
as schema5 calibration.

Root owns production normalization/import/closure, actual RED/GREEN, honest
platform decoding/labels, and integration. Claims are released after this source
handoff; no milestone checklist is marked accepted by this packet.
