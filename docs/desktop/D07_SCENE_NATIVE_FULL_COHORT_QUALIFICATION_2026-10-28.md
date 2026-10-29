# Native4 full comparison: measured cohort and remaining gates

2026-10-28 local date; execution occurred on 2026-10-29 UTC.
Refs #29 D07.03/.04/.05/.06 and #25 D04.04.
**One actual native/model cohort completed at frozen `7bd21c7b`: 48 rows,
36 commits, 12 failed phases and 41/48 scenario passes. Of the 36 commits,
30 used mechanical narration fallback and 6 did not.** Application lifecycle
checks passed, but seven scenario failures and three visible UI defects remain
evidence. This is neither prose-quality acceptance nor completion of D07 or
the desktop epic. No output or row was regenerated for this qualification.

The document author read the immutable packet, actual Core report, bounded
process logs and external image-review manifests only. Root performed the
native execution. The author ran no build, Node/Cargo/app, model/asset, phone or
desktop operation and changed only this document. Raw prompts, generated prose,
receipt text, private paths and the new human packet stay local.

## Frozen source and actual execution

The packet is `full-comparison-native-135af5f2-30af-4300-982b-60227e0555cc`.
Its source is `7bd21c7b0a62ae78c47d66b9030ae715b68f96b5`, initially clean and
reported unchanged at termination. That source differs from tested `b70e57be`
only in two qualification documents. The preceding source checks and their
retained failures are in the [service qualification](D07_SCENE_NATIVE_SERVICE_QUALIFICATION_2026-10-28.md).
The [full harness contract](D07_SCENE_NATIVE_FULL_HARNESS_CONTRACT_2026-10-28.md)
contains the predeclared run limits and eight review slots.

The actual launcher command, from the task-owned physical D: checkout, was:

```text
<task-owned D: Node 24.22.1> apps/desktop/comparison-run-harness.mjs --native-scene-v1
```

The four explicit existing owned D: inputs were the artifact base, Cargo target,
approved publication reuse root and approved worker source. Exact private paths
remain in the local process/preflight records. `TEMP` and `TMP` were
`D:/Dev/_Temp`. This command records an already spent cohort, not an instruction
to regenerate failed rows or improve the sample selection.

| Measurement | Actual result |
| --- | --- |
| Whole launcher invocation | Exit 0; 2026-10-29 05:29:34.3726384Z to 05:43:16.9656571Z; 822.5930187 s |
| Initial app stage | 411 checks, 22 application-owned PNGs; stage passed |
| Cold restart stage | 98 checks, 4 application-owned PNGs; stage passed |
| Native execution/rendering | Actual native IPC, actual installed model, hidden/unfocused WebView2; no desktop input or OS dialog automation |
| Run shape | One paired run, batch 1 then explicit resume 3; 24 scheduled attempts per arm / 48 rows |
| Source/product evidence | Source hashes, harness product hashes, seven fixed execution stages and bounded child-process records retained |
| Termination/restoration | No unknown owned drain or unknown children; normal frontend/native restoration passed, restored products unlaunched |

Fixed consent/read doubles and lost-start acknowledgement are explicitly
labeled test controls. The frontend uses its actual controller/actions and
native IPC; Rust remains authoritative for service state, canonical validation,
receipts, idempotency, revisions, cancellation and observer access. There is no
frontend story reducer or fake provider standing in for the generated rows.

The seven execution stages are worker-only staging, harness frontend build,
native build, initial app, restart app and the two normal-product restorations.
All close with exit 0. There are 44 recorded Scene4 child-policy entries,
including source inspection. This successful known-close execution does not
qualify real timeout/kill/descendant handling: process-tree containment remains
false, and no Windows Job or universal cleanup proof is claimed.

## Approved assets and environment

The read-only preflight at `c9c99bc60d2f0feec07c57c2ed1127d6444585eb`,
2026-10-29T05:27:45.5476545Z, verified existing owned ordinary paths and bytes.
It did not launch a runtime, stage a worker, copy weights or access the original
human packet. The later launcher stages the approved worker only. The actual
qualification records `weightsCopied=false` and `importedByHarness=false`.

| Identity | Recorded value |
| --- | --- |
| Model | Qwen3-0.6B-Q8_0, 639446688 bytes; SHA256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` |
| Worker | 6014464 bytes; SHA256 `b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434` |
| Runtime revision | `620d2225cc436ab0b001e3200e590e3b286ef9ab` |
| Profile | `qwen3-0.6b-q8-cpu-v1`, CPU4, context 4096, Director/Narrator budgets 350 each, repair limit 1, role deadline 120000 ms |
| Profile/template hashes | `01ad542001b04a96f4a8ed6c841be1866eb025350836e0c5d0a4969fdb361d38` / `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361` |

These configuration limits are not measured latency or a phone simulator. The
nearby environment record at exact `b70e57be`, 2026-10-29T05:23:45.0472237Z,
reports Intel Core Ultra 7 270K Plus, 24 cores / 24 logical processors,
68144017408 physical-memory bytes, Windows NT 10.0.26300.0, PowerShell 7.6.5,
Rust/Cargo 1.93.1 and Node 24.22.1. No older i7 hardware or prior Protocol 3
latency is used as a controlled same-hardware comparison. The packet identifies
actual WebView2 rendering, but this document has no new WebView2 version capture.

## Outcomes, fallback and scenario failures

The completed Core report is version 4, `source_matches=true`, with arms
`literal_scene_v1` and `relevant_memory_scene_v1`. It records 24 same-input pairs;
the literal and memory information channels still differ. The following are
different denominators, not interchangeable success scores:

| Actual report metric | Literal / left | Memory / right | Total |
| --- | ---: | ---: | ---: |
| Rows | 24 | 24 | 48 |
| Committed phases | 15 | 21 | 36 |
| Failed phases | 9 | 3 | 12 |
| Scenario assertions passed | 17 | 24 | 41 |
| Scenario assertions failed | 7 | 0 | 7 |
| Committed with mechanical fallback | 14 | 16 | 30 |
| Committed without fallback | 1 | 5 | 6 |

Six failed phases are expected guards, three in each arm: `Inventory`, `Ability`
and `ClarificationRequired`. They pass their scenario assertion and have
construction/privacy evidence `not_applicable_guard`. The other six failed
phases are unexpected left-arm refusals. One further left row commits but
fails its exact expected-command assertion:

| Row(s), left arm | Recorded outcome | Report failure classification |
| --- | --- | --- |
| `courier-01`, `06`, `08`, `14` | Failed; `UnknownReference`; no accepted receipt | `scenario_outcome`, missing construction receipt/capture and unavailable privacy evidence |
| `courier-16`, `19` | Failed; `Agency`; no accepted receipt | `player_agency`, missing construction receipt/capture and unavailable privacy evidence |
| `courier-20` | Committed with mechanical fallback, but wrong dialogue audience | `scenario_outcome` only |

For `courier-20`, the synthetic player input is dialogue announcing return of
carried items, not an item-transfer action. The expected typed command is
`Say` to `mira`. The captured proposal preserves the payload text but selects
audience `player`; its accepted event is `said`, with only `player` as
participant/witness, at revision 17 to 18. No transfer effect is present.
The actual Core receipt binding/replay and source checks succeed; the exact
expected-command comparison fails. This is a measured intent/scenario mismatch,
not a reported canonical receipt/replay invariant failure. The document author
did not independently query the SQLite receipt. No cause or general safety
conclusion is inferred from this one row.

All 30 fallback rows' actual bounded traces record `narration_validation`
as `rejected`, error `narration`, before mechanical fallback is accepted. The
summaries do not provide a finer rejection reason. They do not justify a claim
about which unsupported phrase, schema rule or model behavior caused each
rejection. Committed rows report zero repairs; the configured repair allowance
is not a measured repair attempt. Raw untrusted Narrator output remains
separate from the actual accepted mechanical narration.

The 36 source-bound rows validate **committed Narrator input**, regenerated
against actual Store prefix/receipt and the selected construction. They are
not 36 accepted generated-prose outcomes. Only 6 commits have `fallback=false`,
and those still have no human quality approval. The 36 finite privacy checks,
6 guard-not-applicable rows and 6 unavailable rows preserve their separate
statuses. Unavailable privacy evidence is not a pass; this is not universal
semantic privacy, Director/compiler execution or raw-output origin proof.

## Actual timing and sampled resources

The report records 78 known role calls: 42 Director and 36 Narrator, with no
unknown-role rows. It records 2 physical setups, 16574 ms combined setup time,
and load observations of 198.691 and 233.8885 ms. Those are actual reported
load/setup fields, not a controlled cold-versus-warm experiment. The per-arm
charged clocks are 161362 ms left and 372490 ms right; they have a different
scope from the 822.5930187 s launcher duration, which includes builds,
inspection/captures, restart and restoration.

The following are computed from the immutable report's **committed rows only**.
Percentiles use nearest rank, index `ceil(p*n)-1`; values are milliseconds.
The left population includes its one scenario-mismatching commit and 14
fallbacks; the right includes 16 fallbacks. Failed/guard rows are excluded, so
these are conditional distributions, not whole-suite or quality comparisons.

| Report field | Left n / p50 / p95 / max | Right n / p50 / p95 / max |
| --- | --- | --- |
| `elapsed_ms` | 15 / 3704 / 5495 / 5495 | 21 / 13522 / 17017 / 17254 |
| `first_final_response_ms` | 15 / 3581 / 5227 / 5227 | 21 / 13440 / 16799 / 17046 |
| `commit_elapsed_ms` | 15 / 111 / 400 / 400 | 21 / 106 / 300 / 325 |

All 78 role resource records report sampled status, 250 ms interval, zero failed
samples and no sample-limit flag. Across those records, sampled peak worker
private committed memory is 947109888 bytes, sampled peak working set is
1221795840 bytes and process-lifetime peak working set is 1237385216 bytes.
These worker observations are neither a whole-app peak nor continuous
instantaneous memory coverage, phone performance or a leak/stress result.
No performance superiority or enjoyment conclusion follows from the two arms'
different outcomes and fallback populations.

## Transport recovery, completed resume and cold inspection

Initial `errors` contains exactly two native `Transport` entries. Their paired
evidence identifies one deliberate lost-start acknowledgement and one observed
uncertainty at explicit-three-scene-resume poll 0. The latter is **recovered**,
not a second deliberate fault. The report records one timeout recovery, keeps
the same client/run, reaches the terminal native status and reports no service
error for that resume. A presentation poll deadline is not a native execution
budget. Restart records zero errors and zero timeout recoveries.

The native journeys also exercise held-consent cancellation before reservation,
consent denial, lost-acknowledgement recovery, exact-owner retirement and late
publication fencing through the real controllers/service. Those controls do
not fabricate a completed report. The finite observer/inspection journeys
remain read-only and cannot change character knowledge or generation access.

The completed actual private run contains 2072 inventoried files. Completed
resume and inspection preserve the entire inventory digest; cold open/read/
close preserves the same digest:

```text
f22cd3ec7c40c8870684b025fe1bcd909a4664e34f92f552779f2068bce429e5
```

| Observation | Before and after |
| --- | --- |
| Same-process completed resume | Reservation sequence 2, consent calls 6, owner absent, retained evaluations 0 |
| Fresh-process cold open/read/completed resume | Reservation sequence 0, consent calls 0, owner absent, retained evaluations 0 |

Together with unchanged report bytes and the Rust branch before reservation,
these support the bounded no-new-work/no-new-consent result. Counter equality
does not independently count SDK loads. The separate actual report's two
physical setup/load observations must not be inferred from the sequence value.

## Render review and frozen human slots

All 26 application-owned PNGs were individually inspected in the external
review records below: initial first six v2, remaining sixteen v1 and Root's
restart four. This author verified all 26 unique PNG hashes against those
manifests; the author did not perform a new visual review. The first-six v1
manifest has zero image entries after a PowerShell construction failure and is
explicitly excluded. Existing failed manifests and the original packet remain
unchanged. These are actual WebView2 app renders, not desktop screenshots or
headless HTML presented as native execution.

Three P2 findings persist in the captured source:

| Finding | Visible defect / evidence limit |
| --- | --- |
| R1 | Worker-running wording appears while the actual native phase is awaiting confirmation. The adjacent confirmation text is correct; inference activity is overstated. |
| R2 | After metadata becomes null on context retirement, fallback guidance suggests model import despite the Scene4 reuse-only/import-disabled contract. |
| R3 | The failed `courier-01/left` viewport shows report/raw-output content while its failed status, `UnknownReference` and missing receipt sit outside the viewport. Semantic evidence keeps all three facts; no receipt is invented. |

Long lower panels and some headings extend outside evidence-target viewports;
unseen content and universal accessibility are not qualified. Selected story,
observer and revision are carried by paired semantic snapshots where outside
the panel viewport. Later copy/framing changes are outside frozen `7bd21c7b`.
Their source/headless tests do not establish post-fix native rendering or repair
these original images; no model rows are regenerated for a UI correction.

The eight fixed slots remain the predeclared selection:

| Slot | Actual outcome | Accepted receipt / narration |
| --- | --- | --- |
| `courier-01/left` | Failed Director `UnknownReference` | No Narrator output or accepted receipt |
| `courier-01/right` | Committed | Receipt; generated narration accepted without fallback |
| `courier-05/left`, `05/right` | Both committed | Receipts; mechanical fallback, raw Narrator text remains untrusted |
| `courier-12/left`, `12/right` | Both committed | Receipts; generated narration accepted without fallback |
| `courier-22/left`, `22/right` | Both committed | Receipts; mechanical fallback, raw Narrator text remains untrusted |

Thus the slots contain 7 commits, of which 4 use fallback and 3 do not, plus
1 failed slot. No nicer sample replaces the failure. All report human counts
remain zero, `human_rubric=not_reviewed`, `quality_accepted=false`. Root owns
the separate new human packet/review. The original eight-sample human assessment
remains **needs improvement**; the new run is not a human approval or a claim
of improved consistency, agency, repetition or readability.

## Acceptance boundary and next task

At readback, PR #247 is open, draft and unmerged on its explicit review stack.
Lower dependencies #232/#237/#238/#239/#241/#243 are also open unmerged drafts;
their dependency gate remains. Protected #225 and its resources were not
interacted with by this author. No merge, release, settings change, milestone
checkbox or epic acceptance follows from this cohort.

The next runnable work is to review the preserved typed scenario failures and
fallback bottleneck, finish the visible-state/capture follow-up with its own
evidence, and prepare the fixed human packet. Post-fix native UI qualification,
human assessment, whole-app resource/offline/security/packaging checks,
Android/physical-phone parity and full D07 acceptance remain separate gates.
There is no new model cohort or weakened validator in this documentation task.

## Retained local evidence anchors

The following are local artifact basenames/relative names and SHA256 anchors.
Exact private absolute paths and raw model/player content are intentionally
absent. `Core report` means the actual completed run's `work/report.json`.

| Record | SHA256 |
| --- | --- |
| `d07-scene-native-full-owned-cohort-first1-process.json` | `676a88e0bfbf358a14f55ad15d89031dc6ab18610d2c36852c9ed9ec67091a15` |
| Packet `qualification.json` | `d01dcc97c8e4595c4ddffc0354f8bbaf6219580e106049d1dbe839201bc926df` |
| `initial/report.json` | `0bafcfab6c1f7e22daa8e223375d397f262c0f5e64cc2eec1554c57135179b76` |
| `restart/report.json` | `094d20a2a977143e4335b580d8ab6c85c2eac2a0ff6054e35461b2e77fc54e61` |
| Core report | `9a274f33d8d43529d091e060db08e581f3246f4ba2dee43e75d4ff778301f23b` |
| `executions.json` | `5dd0c1d5672f15ffcc78d468e100b0b808eaed90fd071be754d508c8da35fcc9` |
| `scene-processes.json` | `346f3b56c3605a8d6b1f3b03c1c8b1125baf1c0ef398d9ccbd1c6636b84e9e92` |
| `source-manifest.json` | `41fa2984c4f98edc656eeac9e211adffc2f54b562c7fe6f5606a62079db50475` |
| `product-manifest.json` | `21b19e7622d7fd141964a391181fb679fdca3e59de08f1d0e72ae08e53b54751` |
| `normal-restoration.json` | `eb515c2db026431ec65fec052a10dc644788c12808076df127abdb726c028676` |
| `d07-scene-native-full-approved-assets-preflight1.json` | `ae203655aef44a743227cf0442b6f77d5f02a3b05a8371d81ee56ae4713075a9` |
| `d07-scene-native-full-environment1.json` | `6c20fee5bfa4c7603196567ff9b6f34fc479b5af534c0805b3cc5d9aaea98b7a` |
| `d07-scene-native-initial-first-six-independent-render-review2.json` | `8bcc1aa31555732ae333488d57dc3216a37690242f03d16269e06a996ecab495` |
| `d07-scene-native-initial-remaining-sixteen-render-review1.json` | `8bd6ced4876abee098fe0c84e1a5be80772795fa86bbac83f8e2ddd302b9275d` |
| `d07-scene-native-restart-four-root-render-review1.json` | `740ae982d56682e0aaa3f75151b86aaec3b9d97f63e1c75571ecb8a86caae973` |
