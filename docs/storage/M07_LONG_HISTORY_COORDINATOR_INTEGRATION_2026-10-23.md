# Long-history baseline coordinator integration

Refs #11 M07.06 and #29 D07.01/.04, partial. Root integration claim6372789316,
branch impl/m07-long-history-integration, accepted base
`b2c03d4151dc6d257f2dbddbb64b13950ddbf41e`.

Imported the unchanged two-file author packet through
`a22dfff463c0b8febc93ec0b99fc35e804025c9c` and independent review
`d7a56186603f4281597adb421cfc88166886b016`. Root read the complete test,
reports and actual called API boundaries. The final test's Git blob is
`4d9308aa57f1c39b8d02c2c7a920ed8add61783d`; SHA-256 remains
`8e8ba98f0f4f4b11fbcf271efecaab5963ee648a9e9c87de5029c1fdb30bc8af`.
No original case, budget, assertion, accepted command or production file changed.

Root verified with `git diff --exit-code` that production crates/locallore and
crates/locallore-storage are byte-identical between the measured accepted
`a13b80b8f7e37c1fb2aad714f5ba931f7bf37941` base and current accepted main.
Intervening desktop adapters do not change this portable test's implementation.
The integration is therefore the exact tested source and dependency basis;
root did not rerun or reattribute the author's/reviewer's experiments.

The author ran default/all-feature selected test plus strict Clippy/fmt.
The independent reviewer reran the unchanged test in both feature modes:
**1 Rust integration / 26 fixed checks PASS each**, zero failures/ignores,
53.74/49.18 seconds, and independently queried actual SQLite rows:
**2,072 original-scoped events / 262 committed receipts**. Primary root history
is 1,032 events in129 receipts; extra negative histories ensure same-revision
and observer isolation. All finite source/hash/query/count/error/timing limits
and the original allocator failure are preserved in the linked reports:

- [Author baseline](M07_LONG_HISTORY_BASELINE_2026-10-23.md)
- [Independent execution and review](M07_LONG_HISTORY_INTEGRATION_REVIEW_2026-10-23.md)

Root Git/ownership/diff checks passed. No native renderer, model, Android/device,
download, settings or protected-chat action was involved. This PR adds a real
model-free regression baseline, not durable maintenance jobs, a production
memory consumer, narrative quality, measured tokenizer fit or a performance
claim. Broad M07/D07 gates remain open. The next runnable implementation is
schema4 durable jobs and same-snapshot coverage, followed by the prompt2.4
consumer and same-scenario raw/verified comparison.
