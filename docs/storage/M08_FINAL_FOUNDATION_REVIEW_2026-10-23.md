# Final first-foundation source review — 2026-10-23

No new concrete safety defect was established in this bounded source review.
This is not public approval, an owner acceptance decision, or a runtime PASS.
Root retains responsibility for the current heavy checks, final evidence and
focused PR. #12 M08.03/M08.06 and #8 M04.04/M04.06 remain subject to their
actual acceptance gates.

Exact reviewed integration: `95db6af97107ba52918885759441a9a4eca953b6`;
diff baseline: accepted main `cf93327`. Own clean existing worktree
`source-integrated-store-review` was switched to a new isolated
`review/m08-final-foundation` branch at that exact integration. Only this new
document was written. Claims before edits:
[#12](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378413622),
[#8](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6378413775).
No existing production, test, fixture, schema, evidence or other branch was
modified by this reviewer.

## Diff observations

| Boundary | Final source observation |
| --- | --- |
| Desktop schema5 admission | `export_commands::storage_metadata` admits bounded known database versions1–5 while separately requiring workspace protocol1. Existing future5 assertion explicitly becomes future6, with prior1–4 and missing-field assertions retained. The five frozen actual Store/Host/native-helper tests are registered as a test-only child module; there is no copied validator or production test endpoint. This helper-level evidence must not be presented as WebView/native IPC execution. |
| Android schema5 admission | Both live `DurableGateway` checks move exact physical4→5; envelope/workspace protocol stays1. `workspace()` validates before library attachment; a later refresh revalidates before publishing its SavedSnapshot. Existing recovery keys/cancellation/commit logic is unchanged. `TimelineProtocolTest` now treats4 and6 as incompatible live owners and preserves no-gameplay-before-refusal assertions. The five new actual-JSONObject/Gateway cases are **instrumentation source with synthetic transport**, not local JVM or actual JNI/SQLite evidence. |
| Honest Domain2 legacy closure | Host omniscient Inspect checks Story Lab permission and then refuses non-Domain1 with Version, rather than returning a receipts-only partial view. PlaySnapshot propagates `character_context` errors rather than unwrapping and poisoning its owner. Independent frozen Host tests require exact Version/Unsupported, unchanged full canon and a usable unrelated Domain1 session on the same Host. No fallback converts that refusal into a successful Domain2 app view. |
| Other old consumers | Query1/compiler1 refuse Domain2 before legacy construction. Archive1/2 export refuses any actual mixed branch; the only format change is truthful source-schema5 metadata admission for supported Domain1 history. Derived-memory/job/proof construction refuses Domain2; coherent context snapshot returns the actual engine with explicit raw Unsupported fallback. Current compiler2 uses actor-safe raw events on unsupported old packet paths. No new persistence, memory engine or scheduler appears in this diff. |
| Current Play2.5 guard | Fresh current Play dispatch uses stage-bound evidence and current grounded-prose2.2 validation. The additional ownership helper examines actual `Effect::Given` from the player and matches a bounded clause containing that item's identifier plus first/second-person possession/with-me forms. It is called only when current staged evidence is present. It rejects prose into the existing mechanical fallback; it does not change inventory, accepted event or branch knowledge. |
| Historical narration / dialogue | Legacy Play2.1–2.4 validation passes no current evidence and does not invoke the new ownership helper. Actual literal player dialogue remains its original Said payload and is not passed as narrator speech. New frozen tests retain the full originally observed contradictory prose, generalized potion/vial forms, recipient-ownership positive, literal-dialogue case and original historical replay/hash checks. No model output or old fixture was replaced to manufacture the correction. |
| Native harness changes | Migration current-target checks/labels move4→5 while backup1, original canonical/receipt hashes, one backup, no extra effects, observers and restart/read-only invariants remain. The development helper now reconstructs exact historical001 DDL instead of merely relabeling current5. Model harness additionally asserts exact current prompt2.5/policy2.2/context2/compiler2/relevant policy metadata and hashes the new source files. These are source observations; running/rendering the harness remains Root-owned. |
| Foundation scope | The diff includes new immutable synthetic pre-bump Play2.4 capture files, not edits to prior2.1–2.3 captures. Android archive assets are unchanged. Unimplemented Archive3 test files are absent from this foundation diff; the separate future Archive3 stack remains separate. Native author capabilities and complete V2 app read/author flows are not exposed by this first foundation. |

This review builds on the earlier bounded Store source review at
`e4d24c4389a75441e7b9f7a6854300fafe29f745`, documented in
[M08_INTEGRATED_STORE_REVIEW_2026-10-23.md](M08_INTEGRATED_STORE_REVIEW_2026-10-23.md).
Between that base and the final reviewed head, production Store sources are
unchanged. The additional production change is the current-only ownership
narration guard; other code changes are its frozen tests and model harness
provenance checks. The previous owner/full-source/native capability, exact
recovery, normalized private binding and single-transaction analysis therefore
continues to describe those unchanged Store files. This does not substitute a
source review for rerunning current integration checks.

## Exact source and fixture identities

SHA256 collected directly from this reviewed checkout:

| File | SHA256 |
| --- | --- |
| `apps/android/app/src/main/java/org/locallore/app/DurableGateway.kt` | `10db91184ef5cd24a2fb3f6a0a5a8ed1b77d7928149dc6806259574443ca1c70` |
| `apps/desktop/src-tauri/src/export_commands.rs` | `3040c22539128f558cbfe1be2e6063310100d24cb862c3a55d78f0cc3586b1f3` |
| `crates/locallore/src/host.rs` | `69975804076f834f4f15395d3f2edc0d6f0c1a6c2f8c1ef6c39c19f1d3d42192` |
| `crates/locallore/src/play.rs` | `ef69516a24bc7666ee1e87c4a28980eaed95057ebd2383bef3be86633d1c0cd6` |
| Existing `accepted_play_v2_1.json` | `3aefb5a8c1a9ad0f27b15d424dfcecf5f7fb58a639572758a6128fb75ace36d4` |
| Existing `accepted_play_v2_2.json` | `f3645af4047e02b827010134cb57b1d974c86538b68ebf8e43801ea8bcde8f3d` |
| Existing `accepted_play_v2_3.json` | `57fb218ef2f9a50842f77c2c87cd7e694ca53ea064c6205cfef18abd9e51035c` |
| New pre-bump `accepted_play_v2_4.json` | `f08801ab9ce13e0bb47434896dafa1e8e671fa4f4a239731cbd2ee0f42730e2d` |
| New pre-bump `accepted_play_v2_4_receipt.json` | `38dcf7329addf4ed98fd984cdb9eac95f8d078be03bf4633dd7082d23ac4bc3f` |

These file hashes match the frozen historical narration regression's literals.
Hash comparison is a source check, not an independently executed replay test.
The old fixture/Android asset diff was inspected: only the two new2.4 files are
added; no existing accepted capture/Android archive asset is modified.

## Checks and remaining limits

Reviewer actually performed Git/source/API/frozen-test inspection, source hash
collection and `git diff --check` over the integration diff and new document.
No Cargo/Clippy/typecheck, Node, Gradle, SQLite execution, model/provider call,
native app/IPC/WebView, capture/render, emulator/device, desktop-control or
protected-resource action ran. Root's active processes were not inspected,
interrupted, or used. No heavy execution slot was taken.

The narration guard is intentionally conservative finite phrase matching. This
review does not claim general semantic consistency, all paraphrase coverage,
universal factual entailment, model quality or zero false positives. Original
mechanical state remains authoritative. Bounded syntactic fallback policy and
actual subsequent model/native evidence must remain separately reported.

The coordinator verification document at the reviewed head still labels some
platform/native migration qualification as pending. This reviewer does not
infer completion from builds, source changes or earlier cohorts. Root must
finish its current checks and reconcile that evidence with exact commands,
versions, preserved first failures, app-owned render inspection and unavailable
checks before the focused PR's final gate. Existing synthetic protocol tests
must not become claimed emulator/physical-phone or JNI execution.

Complete Domain2 app playback/inspection and author UI remain unavailable until
the separately designed V2 consumer route closes its decoders and privileges.
Archive3 and physical-phone/release gates remain separate. This source-only
packet adds no approval, merge, release or repository-setting authority.
