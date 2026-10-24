# M08 legacy Host consumer frozen oracles — 2026-10-23

This is a source-only regression handoff for partial #12 M08.03/M08.06 and
supporting #8 M04.01/M04.04/M04.06. It does not establish acceptance of those
tasks, a working Domain2 desktop UI, or a native application run.

## Freeze and ownership

- Base: `b85122a1057e136b934f275c68001d806eaa262a`, including accepted main
  `cf93327` and the coordinator's schema5 Store work.
- Isolated branch: `review/m08-legacy-host-consumers`; worktree:
  `source-legacy-host-consumer-review`.
- Frozen test commit: `78e369340c18e2ba9a9224ddc7f64856cbea440d`.
- Test source:
  `crates/locallore-workspace/tests/m08_legacy_host_consumers.rs`.
- Test source SHA256 at freeze:
  `487425f06cdd53b5e3c8d1ea69c9c11f664398e25799250d73f8f2f72985f427`.
- Claims before writes: [#12 claim](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6377683088),
  [#8 claim](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6377683299).
- Reviewer owns only the new test and this new document. The coordinator owns
  production Rust Host admission, actual RED/fix/GREEN execution, integration,
  and the final acceptance record. No production files, dependencies, existing
  assertions, archives, capacity profiles, or historical evidence were edited.

## Actual interfaces and synthetic fixture

The fixture creates a new schema5 SQLite database through
`Store::open_application`, creates an ordinary parent story and a separate
ordinary control story, and uses `prepare_author_correction` followed by
`apply_author_correction` to create an authored child. Public Store replay must
confirm exactly one `CanonicalRecord::AuthorV1`, Domain2, and head revision1.
The parent and separate-story control must still be Domain1.

Each consumer case opens an actual `locallore_workspace::open` Host over that
database with Story Lab privilege enabled. It sends the same protocol1
`Host::call` commands used by platform adapters. There is no fake persistence
port, provider, model, SQL injection, alternate engine, or platform UI.
The only files created by execution are a bounded, synthetic temporary database
and its normal SQLite files inside a uniquely created test directory. The
guard removes only that directory after Store/Host owners drop.

## Frozen cases

| Test | Required outcome |
| --- | --- |
| `actual_schema5_workspace_keeps_protocol1_with_store_authored_domain2_present` | Actual Host workspace metadata succeeds with `version:1`, workspace `schema_version:1`, `database_schema_version:5`, persistence true, and two root stories. No durable canon changes. |
| `legacy_play_snapshot_refuses_domain2_without_poisoning_unrelated_domain1_host_work` | Legacy Domain2 Play snapshot is closed with exactly `Version` or `Unsupported`, either at Resume or at the subsequent snapshot call. The same Host still reads workspace metadata, resumes the unrelated Domain1 story, and produces its ordinary snapshot. No durable canon changes. |
| `legacy_omniscient_inspect_refuses_domain2_without_incomplete_success_or_canon_change` | Legacy omniscient Inspect has the same closed refusal alternatives and subsequent Host usability requirements. Incomplete mechanical-state/legacy-receipts success is rejected. Story Lab permission is enabled, so `Forbidden` cannot accidentally satisfy the oracle. |

Each consumer owns a separate fresh fixture and Host. The historical caught
PlaySnapshot panic must not mask the independent Inspect incomplete-success
defect. Follow-up responses are captured before refusal assertions so a caught
panic, `Internal` response, or poisoned owner remains visible in the failure
diagnostic. A rejected Resume with any other category also fails.

Both interim implementation choices are intentionally allowed:

1. Refuse Domain2 at legacy Host Resume with a closed `Version`/`Unsupported`
   response.
2. Resume successfully at the actual child scope/head, then refuse the specific
   legacy snapshot/inspection consumer with the same typed response.

Neither route is a Domain2 Play implementation, fallback success, or permission
to discard authored history. The newer Play2.5/V2 snapshot route remains a
separate capability. These tests do not exercise generation or claim Query2
actor isolation; those retain their owning Core oracles.

The before/after comparison uses a separate public read-only Store after Host
drop. For the parent, authored child, and unrelated control, it compares seed,
domain, revision, complete canonical projection bytes, complete mixed canonical
records, and legacy receipt view, plus both stories' branch catalogs and current
database version. It is a canonical-content invariant, not a byte-for-byte
SQLite file comparison or an oracle for every derived cache/table.

## Verification status and next execution

Reviewer checks actually run:

```text
rustfmt --edition 2021 crates/locallore-workspace/tests/m08_legacy_host_consumers.rs
git diff --check
```

Both commands completed successfully. Git/source inspection and a source hash
were also collected. No Cargo, Node, Gradle, SQLite CLI, model, device, native
application, browser, desktop capture, or UI automation was run by this reviewer.
The new test source is **UNCOMPILED / UNRUN** at handoff; no RED or GREEN result
is inferred from reading the pre-fix source.

Coordinator's next bounded command, under its exclusive execution slot:

```text
cargo test --locked -p locallore-workspace --test m08_legacy_host_consumers -- --nocapture
```

Run the unchanged frozen tests against the base production sources first and
retain each actual result. Then implement only the closed legacy Domain2 route,
run the same tests unchanged, and run appropriate existing Host/Workspace/Store
and platform compatibility checks. Record toolchain/environment versions and
actual result artifacts with the coordinator's evidence. Broader Store13,
review3, and real-Full results reported by the coordinator are not reviewer-run
results and are not substituted for this Host regression run.

No model/device/desktop/Android-native execution or functional Domain2 UI claim
is established by this packet. Claims are released to the coordinator after the
source/doc handoff; task checkboxes remain unchanged.
