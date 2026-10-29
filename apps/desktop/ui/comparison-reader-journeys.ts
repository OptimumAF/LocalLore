// Same application controller/native IPC in a hidden WebView2; no desktop input.
import type { Controller } from "./controller";
import type { ComparisonReaderController } from "./comparison-reader-controller";
import { structural, type ErrorBuffer } from "./model";
import type { ViewV2 } from "./v2-view-model";
type FixtureProof = {
    source_gate: string;
    paired: {
        rows: number;
        source_bound_committed_rows: number;
        human_reviewed: number;
        quality_accepted: boolean;
    };
    rollout: {
        rows: number;
        source_bound_committed_rows: number;
        human_reviewed: number;
        quality_accepted: boolean;
    };
};
type DiagnosticModelObservation = {version:1;kind:"diagnostic_reader_model_observation_v1";
    reservation_sequence:number;owner_present:boolean;retained_evaluations:number};
type DiagnosticFixtureId="diagnostic-recorded"|"diagnostic-legacy"|"diagnostic-missing"|"diagnostic-unavailable"|"diagnostic-rejected"|"diagnostic-malformed";
type DiagnosticFixtureProof = {version:1;kind:"narration_diagnostic_reader_fixture_v1";protocol_version:4;synthetic:true;
    fixtures:{id:string;provenance:string;expected_status:string|null;expected_error:string|null}[];
    fixture_inventory:Record<string,string>;model_observation:DiagnosticModelObservation;
    inventory_stats:{entries:number;files:number;bytes:number};inventory_limits:{entries:number;bytes:number;file_bytes:number;depth:number}};
export async function comparisonReaderJourneys({
    controller: c,
    comparison: r,
    errors,
    invoke,
    dispose,
    config,
}: {
    controller: Controller;
    comparison: ComparisonReaderController;
    errors: ErrorBuffer;
    invoke: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
    dispose: () => Promise<void>;
    config: { stage: string };
}) {
    const checks: string[] = [];
    const startedAt = performance.now();
    const timing: { check: string; elapsedMs: number }[] = [];
    let failedCheck = "comparison-start";
    let failureCategory: string | null = null;
    let fixtureInventory: Record<string, string> | null = null;
    let protocolVersion: 2 | 3 | 4 = 2;
    let fixtureProof: FixtureProof | null = null;
    let diagnosticMode=false;
    let diagnosticProof:Omit<DiagnosticFixtureProof,"fixture_inventory">|null=null;
    let diagnosticObservation:DiagnosticModelObservation|null=null;
    const expectedDiagnosticErrors:{action:string;code:string;broker_delta:ReturnType<ErrorBuffer["snapshot"]>}[]=[];
    const diagnosticCaptures:Record<string,{source:string;provenance:string}>={};
    const check = (value: unknown, label: string) => {
        failedCheck = label;
        if (!value) throw Error(label);
        checks.push(label);
        timing.push({
            check: label,
            elapsedMs: Math.round(performance.now() - startedAt),
        });
    };
    const until = async (fn: () => boolean) => {
        for (let n = 0; n < 3000; n++) {
            if (fn()) return;
            await new Promise((resolve) => setTimeout(resolve, 10));
        }
        throw Error("ComparisonJourneyTimeout");
    };
    const scenario = async (name: string) => {
        failedCheck = `native-fixture-${name}`;
        return invoke("harness_comparison_reader_case", { scenario: name });
    };
    const button = (label: string) => {
        const matches = [
            ...document.querySelectorAll<HTMLButtonElement>(
                "#comparison-reader button",
            ),
        ].filter((node) => node.textContent?.trim() === label);
        check(
            matches.length === 1 && !matches[0].disabled,
            `actual-mounted-button-${label}`,
        );
        return matches[0];
    };
    const open = async () => {
        if (protocolVersion !== 4) return r.pick();
        button("Choose comparison report folder").click();
        await until(() => !r.get().busy && !r.get().status?.running);
        check(
            r.get().status?.phase === "ready" && !!r.get().source,
            "mounted-picker-actual-native-ready",
        );
    };
    const summary = async () => {
        if (protocolVersion !== 4) return r.loadSummary();
        if (!r.get().summary) {
            button("Show private report").click();
            await until(() => !r.get().busy);
        }
        check(
            r.get().summary?.report.version === 4,
            "mounted-private-summary-keeps-protocol4",
        );
    };
    const selectRow = async (row: { turn: string; arm: string }) => {
        if (protocolVersion !== 4) {
            r.select(row as Parameters<typeof r.select>[0]);
            return;
        }
        const value = `Inspect ${row.arm} ${row.turn}`;
        const matches = [
            ...document.querySelectorAll<HTMLButtonElement>(
                "#comparison-reader button",
            ),
        ].filter((node) => node.getAttribute("aria-label") === value);
        check(
            matches.length === 1 && !matches[0].disabled,
            "actual-mounted-source-row-control",
        );
        matches[0].click();
        await until(
            () =>
                r.get().selected?.turn === row.turn &&
                r.get().selected?.arm === row.arm,
        );
    };
    const inspect = async (
        kind: "query" | "receipt" | "capture" | "outputs",
        edge: "before" | "after" = "after",
        view: ViewV2 = "knowledge",
    ) => {
        failedCheck = `comparison-inspect-${kind}-${edge}`;
        if (protocolVersion === 4) {
            if (kind === "query") {
                const selects = [
                    ...document.querySelectorAll<HTMLSelectElement>(
                        ".comparison-selected .comparison-controls select",
                    ),
                ];
                check(
                    selects.length === 2,
                    "actual-mounted-query-edge-and-view-controls",
                );
                for (const [control, value] of [
                    [selects[0], edge],
                    [selects[1], view],
                ] as const) {
                    control.value = value;
                    control.dispatchEvent(
                        new Event("change", { bubbles: true }),
                    );
                }
                await until(
                    () =>
                        r.get().querySelection.edge === edge &&
                        r.get().querySelection.view === view,
                );
            }
            const previous = r.get().evidence;
            const label =
                kind === "query"
                    ? "Inspect filtered state"
                    : kind === "receipt"
                      ? "Inspect accepted receipt"
                      : kind === "capture"
                        ? "Inspect actual context capture"
                        : "Inspect recorded role outputs";
            button(label).click();
            await until(
                () =>
                    !r.get().busy &&
                    r.get().evidence !== previous &&
                    r.get().evidence !== null,
            );
            return;
        }
        if (kind === "query")
            await r.inspect({
                kind,
                edge,
                observer: r.get().observer,
                view,
            });
        else await r.inspect({ kind, observer: r.get().observer });
    };
    const capture = async (
        label: string,
        selector = "#comparison-reader",
        includeSummary = false,
    ) => {
        failedCheck = `${label}-capture`;
        let target = document.querySelector<HTMLElement>(selector);
        let requireSelectedContext = false;
        let hashRange: Range | null = null;
        let diagnosticGeometry:unknown=null;
        const diagnosticGeometryFailures:string[]=[];
        const geometryCheck=(value:unknown,name:string)=>{if(!value)diagnosticGeometryFailures.push(name);};
        if (diagnosticMode) {
            target=document.querySelector<HTMLElement>(".comparison-narration-diagnostic, .comparison-evidence, .comparison-selection-context")
                ?? document.querySelector<HTMLElement>("#comparison-reader .comparison-controls");
        } else if (protocolVersion === 4) {
            if (
                [
                    "comparison-receipt",
                    "comparison-capture",
                    "comparison-outputs",
                    "comparison-mira",
                    "comparison-sable",
                    "comparison-guard",
                ].includes(label)
            ) {
                target = document.querySelector<HTMLElement>(
                    ".comparison-evidence pre, .comparison-evidence",
                );
                // Prefer the actual bounded content, not only its outer heading.
                target = target?.querySelector<HTMLElement>("pre") ?? target;
                requireSelectedContext = true;
                if (target?.tagName === "PRE") {
                    const needle =
                        label === "comparison-receipt" ||
                        label === "comparison-mira"
                            ? "The pennant I carry has an amber stitch."
                            : label === "comparison-capture"
                              ? "generation_request"
                              : label === "comparison-outputs"
                                ? '"director"'
                                : '"rows"';
                    const walker = document.createTreeWalker(
                        target,
                        NodeFilter.SHOW_TEXT,
                    );
                    let node: Node | null;
                    let located = false;
                    while ((node = walker.nextNode())) {
                        const at = node.textContent?.indexOf(needle) ?? -1;
                        if (at < 0) continue;
                        const range = document.createRange();
                        range.setStart(node, at);
                        range.setEnd(node, at + needle.length);
                        target.scrollTop +=
                            range.getBoundingClientRect().top -
                            target.getBoundingClientRect().top -
                            48;
                        located = true;
                        break;
                    }
                    check(located, `${label}-actual-target-content-present`);
                }
            } else if (label === "comparison-narrow") {
                const terms = [
                    ...document.querySelectorAll<HTMLElement>(
                        ".comparison-selected dt",
                    ),
                ];
                const first = terms.find(
                    (node) =>
                        node.textContent?.trim() === "Construction evidence",
                );
                const last = terms.find(
                    (node) => node.textContent?.trim() === "Scene frame hash",
                )?.nextElementSibling;
                check(
                    first && last,
                    "actual-protocol4-status-hash-fields-mounted",
                );
                hashRange = document.createRange();
                hashRange.setStartBefore(first!);
                hashRange.setEndAfter(last!);
                target = first!;
                requireSelectedContext = true;
            } else if (includeSummary) {
                target = document.querySelector<HTMLElement>(
                    "#comparison-reader .comparison-table",
                );
                check(
                    !!target?.querySelector("thead"),
                    `${label}-actual-report-table-mounted`,
                );
                check(
                    structural(
                        [...target!.querySelectorAll("thead th")].map((node) =>
                            node.textContent?.trim(),
                        ),
                    ) ===
                        structural([
                            "Turn",
                            "Arm",
                            "Revision",
                            "Result",
                            "Roles",
                            "Inspect",
                        ]),
                    `${label}-actual-report-table-headers`,
                );
            }
        }
        check(target, `${label}-actual-capture-target-present`);
        target!.scrollIntoView({
            block: diagnosticMode ? "start" : protocolVersion === 4 ? "center" : "start",
        });
        if (hashRange) {
            const bounds = hashRange.getBoundingClientRect();
            window.scrollBy(
                0,
                (bounds.top + bounds.bottom) / 2 - innerHeight / 2,
            );
        }
        await new Promise((resolve) => setTimeout(resolve, 150));
        const state = r.get(),
            panel = document.querySelector<HTMLElement>("#comparison-reader");
        const selected = state.source?.rows.find(
            (row) =>
                row.row.turn === state.selected?.turn &&
                row.row.arm === state.selected?.arm,
        );
        const overflow = document.documentElement.scrollWidth > innerWidth + 2;
        const nested = !!panel && panel.scrollWidth > panel.clientWidth + 2;
        if (diagnosticMode) {
            const diagnosticArtifact=document.querySelector<HTMLElement>(".comparison-narration-diagnostic");
            const artifact=diagnosticArtifact??document.querySelector<HTMLElement>(".comparison-evidence");
            const rect=(node:Element)=>{const b=node.getBoundingClientRect();return {top:b.top,bottom:b.bottom,left:b.left,right:b.right,width:b.width,height:b.height};};
            const header=document.querySelector<HTMLElement>(".comparison-selection-context");
            const fixed=!!header&&["sticky","fixed"].includes(getComputedStyle(header).position);
            const nodes=artifact?[artifact.querySelector<HTMLElement>("h4"),...artifact.querySelectorAll<HTMLElement>("p")
                ].filter((node):node is HTMLElement=>!!node&&(/^(Source story|Case phase|Selected case phase|Case error|Quality|Prose quality)/i.test(node.textContent?.trim()??"")||node.tagName==="H4")):[target!];
            geometryCheck(nodes.length>0,`${label}-positive-context-nodes`);
            diagnosticGeometry={target:rect(target!),header:header?rect(header):null,headerPosition:header?getComputedStyle(header).position:null,
                context:nodes.map(node=>({text:node.textContent?.slice(0,1024),...rect(node)}))};
            for(const node of nodes) {
                const b=rect(node),h=header?rect(header):null;
                geometryCheck(b.width>0&&b.height>0&&b.top>=-2&&b.bottom<=innerHeight+2,`${label}-artifact-context-visible`);
                geometryCheck(!fixed||!h||b.bottom<=h.top||b.top>=h.bottom,`${label}-context-not-covered-by-sticky-header`);
                const hit=document.elementFromPoint(Math.min(innerWidth-2,Math.max(2,(b.left+b.right)/2)),Math.min(innerHeight-2,Math.max(2,(b.top+b.bottom)/2)));
                geometryCheck(!!hit&&node.contains(hit),`${label}-actual-context-hit-test`);
            }
            if(artifact&&selected) {
                const body=artifact.innerText.split("Inspect bound diagnostic metadata")[0];
                geometryCheck(body.includes(selected.source.scope.story)&&body.includes(selected.source.scope.branch)&&
                    new RegExp(`before(?: head| revision)?\\s*:?\\s*${selected.source.before_head}\\b`,"i").test(body)&&
                    new RegExp(`after(?: head| revision)?\\s*:?\\s*${selected.source.after_head}\\b`,"i").test(body),`${label}-artifact-local-source-before-after`);
                if(diagnosticArtifact)geometryCheck(/case error/i.test(body)&&/quality/i.test(body),`${label}-artifact-case-error-and-quality-labels`);
            }
        } else if (protocolVersion === 4) {
            const rectangle =
                hashRange?.getBoundingClientRect() ??
                target!.getBoundingClientRect();
            if (requireSelectedContext) {
                const header = document.querySelector<HTMLElement>(
                    ".comparison-selection-context",
                );
                check(
                    !!header &&
                        !!selected &&
                        header.textContent?.includes(
                            selected.source.scope.story,
                        ) &&
                        header.textContent?.includes(
                            selected.source.scope.branch,
                        ) &&
                        header.textContent?.includes(
                            `before ${selected.source.before_head}`,
                        ) &&
                        header.textContent?.includes(
                            `after ${selected.source.after_head}`,
                        ),
                    `${label}-actual-selected-scope-header`,
                );
                const context = header!.getBoundingClientRect();
                check(
                    context.top >= -2 &&
                        context.bottom < innerHeight &&
                        rectangle.top >= context.bottom - 2 &&
                        rectangle.bottom <= innerHeight + 2,
                    `${label}-actual-content-visible-below-context-header`,
                );
            } else if (includeSummary) {
                const header = document.querySelector<HTMLElement>(
                    ".comparison-report-context",
                );
                check(
                    !selected &&
                        !!header &&
                        header.textContent?.includes("Protocol 4"),
                    `${label}-actual-unselected-report-context`,
                );
                const context = header!.getBoundingClientRect();
                check(
                    context.top >= -2 &&
                        rectangle.top >= context.bottom - 2 &&
                        rectangle.bottom <= innerHeight + 2,
                    `${label}-actual-report-table-within-viewport`,
                );
            }
        }
        const evidence = state.evidence;
        const inspectedRevision = evidence
            ? evidence.body.kind === "query"
                ? evidence.body.page.revision
                : evidence.edge === "before"
                  ? evidence.before_head
                  : evidence.edge === "after"
                    ? evidence.after_head
                    : null
            : (selected?.source.after_head ?? null);
        const pendingOperation = state.status?.running
            ? {
                  id: state.status.operation_id,
                  phase: state.status.phase,
                  client: state.clientId,
              }
            : state.uncertain
              ? {
                    id: null,
                    phase: "acknowledgement_unknown",
                    client: state.clientId,
                }
              : state.busy
                ? { id: null, phase: "awaiting_reply", client: state.clientId }
                : null;
        const summaryProjection =
            includeSummary && state.summary
                ? {
                      kind: "summary_projection",
                      binding: state.summary.binding,
                      report: {
                          version: state.summary.report.version,
                          kind: state.summary.report.kind,
                          lane: state.summary.report.lane,
                          source_matches: state.summary.report.source_matches,
                          completed: state.summary.report.completed,
                          completed_scenes:
                              state.summary.report.completed_scenes,
                          profile: state.summary.report.profile,
                          unavailable: state.summary.report.unavailable,
                          limitations: state.summary.report.limitations,
                          human_reviewed: state.summary.report.human_reviewed,
                          human_rubric: state.summary.report.human_rubric,
                          quality_accepted:
                              state.summary.report.quality_accepted,
                          ...(state.summary.report.version === 4
                              ? {
                                    source_bound_committed_rows:
                                        state.summary.report
                                            .source_bound_committed_rows,
                                }
                              : {}),
                          turns: state.summary.report.turns.map((row) => ({
                              turn: row.turn,
                              arm: row.arm,
                              phase: row.phase,
                              error: row.error,
                              expected: row.expected,
                              passed: row.passed,
                              failures: row.failures,
                              roles: row.roles,
                              roles_known: row.roles_known,
                              input_semantic_sha256: row.input_semantic_sha256,
                              output_semantic_sha256:
                                  row.output_semantic_sha256,
                              ...("construction" in row
                                  ? {
                                        construction: row.construction,
                                        construction_evidence_status:
                                            row.construction_evidence_status,
                                        ...("literal_source_units" in row
                                            ? {
                                                  literal_source_units:
                                                      row.literal_source_units,
                                                  literal_selected_start:
                                                      row.literal_selected_start,
                                                  literal_selected_units:
                                                      row.literal_selected_units,
                                              }
                                            : {
                                                  construction_evidence_reason:
                                                      row.construction_evidence_reason,
                                                  narrator_prompt_sha256:
                                                      row.narrator_prompt_sha256,
                                                  narrator_schema_sha256:
                                                      row.narrator_schema_sha256,
                                                  scene_frame_sha256:
                                                      row.scene_frame_sha256,
                                                  privacy_evidence_status:
                                                      row.privacy_evidence_status,
                                                  actual_receipt_sha256:
                                                      row.actual_receipt_sha256,
                                              }),
                                    }
                                  : { policy: row.policy }),
                          })),
                      },
                  }
                : null;
        try {
            await invoke("harness_checkpoint", {
                label,
                snapshot: {
                    synthetic: true,
                    semanticVersion: 2,
                    uiRevision: (c.get().play ?? c.get().playV2)?.revision ?? 0,
                    checks: [...checks],
                    errors: errors.snapshot(),
                    fixtureInventory: includeSummary ? fixtureInventory : null,
                    fixtureProof: includeSummary ? fixtureProof : null,
                    ...(diagnosticMode?{diagnosticFixtureProof:includeSummary?diagnosticProof:null,
                        diagnosticProvenance:diagnosticCaptures[label]??null,modelObservation:diagnosticObservation,
                        diagnostic:state.diagnostic,diagnosticGeometry,diagnosticGeometryFailures,expectedDiagnosticErrors,
                        selectedCase:{before:selected?.source.before_head??null,after:selected?.source.after_head??null,
                            base:state.diagnostic&&"observation"in state.diagnostic.diagnostic?state.diagnostic.diagnostic.observation.host_query.command.base_revision:null,
                            attempt:state.diagnostic&&"observation"in state.diagnostic.diagnostic?state.diagnostic.diagnostic.observation.host_query.command.attempt:null,
                            phase:state.summary?.report.turns.find(t=>t.turn===state.selected?.turn&&t.arm===state.selected?.arm)?.phase??null,
                            error:state.summary?.report.turns.find(t=>t.turn===state.selected?.turn&&t.arm===state.selected?.arm)?.error??null,
                            fallback:state.summary?.report.turns.find(t=>t.turn===state.selected?.turn&&t.arm===state.selected?.arm)?.fallback??null,
                            receipt_available:selected?.receipt_available??null}}:{}),
                    selectedStory: selected?.source.scope ?? null,
                    selectedReport: state.status?.run_token ?? null,
                    observer: state.observer,
                    revision: inspectedRevision,
                    pendingOperation,
                    gameplayContext: {
                        scope: c.selected()?.scope ?? null,
                        revision:
                            (c.get().play ?? c.get().playV2)?.revision ?? null,
                        observer: c.get().observer,
                    },
                    displayedReceipt:
                        state.evidence?.body.kind === "receipt"
                            ? state.evidence.body.receipt
                            : null,
                    visibleError: state.error,
                    comparison: {
                        status: state.status,
                        source: state.source,
                        selected: state.selected,
                        querySelection: state.querySelection,
                        summaryProjection,
                        evidence: state.evidence,
                        uncertain: state.uncertain,
                        busy: state.busy,
                        error: state.error,
                        ...(diagnosticMode?{diagnostic:state.diagnostic}:{}),
                    },
                    dom: {
                        text: panel?.innerText.slice(0, 24576),
                        controls: [
                            ...(panel?.querySelectorAll(
                                "button,select,summary",
                            ) ?? []),
                        ].map((node) => ({
                            tag: node.tagName,
                            text: node.textContent?.slice(0, 256),
                            disabled:
                                (node as HTMLButtonElement).disabled ?? false,
                            value:
                                node instanceof HTMLSelectElement
                                    ? node.value
                                    : null,
                        })),
                        width: innerWidth,
                        userAgent: navigator.userAgent,
                        devicePixelRatio,
                        horizontalOverflow: overflow,
                        nestedOverflow: nested,
                        captureTarget:
                            protocolVersion === 4
                                ? {
                                      text: target?.textContent?.slice(0, 2048),
                                      scrollTop: target?.scrollTop ?? null,
                                      context:
                                          document
                                              .querySelector(
                                                  ".comparison-selection-context",
                                              )
                                              ?.textContent?.slice(0, 2048) ??
                                          null,
                                  }
                                : null,
                    },
                },
            });
        } catch (error) {
            const categories = new Set([
                "ArtifactTooLarge",
                "ArtifactInvalid",
                "CheckpointInvalid",
                "CheckpointLimit",
                "CheckpointDuplicate",
                "RevisionRequired",
                "SyntheticFixtureRequired",
                "Forbidden",
                "Closed",
                "CaptureUnavailable",
                "CaptureFailed",
                "CaptureTimeout",
            ]);
            failureCategory =
                typeof error === "string" && categories.has(error)
                    ? error
                    : "CheckpointFailed";
            throw error;
        }
        check(!overflow, `${label}-no-page-overflow`);
        check(!nested, `${label}-no-panel-overflow`);
        for(const geometryFailure of diagnosticGeometryFailures)check(false,geometryFailure);
    };
    const diagnosticJourneys=async(prepared:DiagnosticFixtureProof,canonicalBefore:string)=>{
        diagnosticMode=true;protocolVersion=4;
        const {fixture_inventory,...proof}=prepared;diagnosticProof=proof;fixtureInventory=fixture_inventory;
        diagnosticObservation=prepared.model_observation;
        check(prepared.version===1&&prepared.synthetic===true&&prepared.protocol_version===4&&prepared.fixtures.length===6,"closed-six-diagnostic-fixtures");
        const ids=["diagnostic-recorded","diagnostic-legacy","diagnostic-missing","diagnostic-unavailable","diagnostic-rejected","diagnostic-malformed"] as const;
        check(structural(prepared.fixtures.map(f=>f.id))===structural(ids),"fixed-diagnostic-fixture-roster");
        const observe=async()=>{
            diagnosticObservation=await scenario("diagnostic-observation") as DiagnosticModelObservation;
            check(diagnosticObservation.version===1&&diagnosticObservation.kind==="diagnostic_reader_model_observation_v1"&&
                diagnosticObservation.reservation_sequence===0&&!diagnosticObservation.owner_present&&diagnosticObservation.retained_evaluations===0,"existing-model-manager-stays-unreserved");
        };
        await observe();
        let current:DiagnosticFixtureId="diagnostic-recorded";
        const choose={"diagnostic-recorded":"choose-diagnostic-recorded","diagnostic-legacy":"choose-diagnostic-legacy",
            "diagnostic-missing":"choose-diagnostic-missing","diagnostic-unavailable":"choose-diagnostic-unavailable",
            "diagnostic-rejected":"choose-diagnostic-rejected","diagnostic-malformed":"choose-diagnostic-malformed"} as const;
        const select=(arm:"left"|"right")=>selectRow({turn:"courier-01",arm});
        const openFixture=async(id:DiagnosticFixtureId,arm:"left"|"right"="left")=>{
            await r.close();current=id;await scenario(choose[id]);await open();await summary();await select(arm);
            check(r.get().source?.rows.length===12&&r.get().summary?.report.version===4,"actual-diagnostic-source-through-existing-reader");
        };
        const readDiagnostic=async(status:string)=>{
            button("Inspect narration diagnostic").click();
            check(r.get().busy&&r.get().diagnostic===null,"actual-diagnostic-action-synchronous-busy-clear");
            await until(()=>!r.get().busy);
            check(r.get().error===null&&r.get().diagnostic?.diagnostic.status===status,`actual-native-diagnostic-${status}`);
        };
        const image=async(label:string,include=false,provenance?:string)=>{
            diagnosticCaptures[label]={source:current,provenance:provenance??prepared.fixtures.find(f=>f.id===current)!.provenance};
            await capture(label,"#comparison-reader",include);
        };
        await openFixture("diagnostic-recorded");await readDiagnostic("recorded");
        await image(config.stage==="restart"?"comparison-restarted":"comparison-open",true);
        if(config.stage!=="restart") {
            await inspect("receipt");check(r.get().evidence?.body.kind==="receipt","actual-diagnostic-source-accepted-receipt");
            await image("comparison-receipt");
            await openFixture("diagnostic-unavailable");await readDiagnostic("host_unavailable");await image("comparison-capture");
            await openFixture("diagnostic-rejected");await readDiagnostic("host_rejected");await image("comparison-outputs");
            await openFixture("diagnostic-recorded","right");await readDiagnostic("recorded");
            await invoke("harness_viewport",{preset:"capture-narrow"});await image("comparison-narrow");await invoke("harness_viewport",{preset:"wide"});
            const lateObserver=r.inspectNarrationDiagnosticV1();
            check(r.get().busy&&r.get().diagnostic===null,"real-diagnostic-pending-observer-switch");
            r.setObserver({kind:"character",id:"mira"});await lateObserver;
            check(r.get().diagnostic===null&&r.get().summary===null&&r.get().evidence===null,"real-late-diagnostic-cannot-refill-mira");
            await image("comparison-mira",false,"frontend_actor_lens_cleared_after_real_ipc");
            r.setObserver({kind:"character",id:"sable"});
            const status=r.get().status!;const errorBefore=errors.snapshot();let denial="";
            try {await invoke("evaluation_comparison",{action:"narration_diagnostic_v1",query:{runToken:status.run_token,
                binding:"0".repeat(64),turnId:"not-a-retained-row",arm:"left",observer:{kind:"character",id:"sable"}}});}
            catch(error){denial=String(error);}
            const denialDelta=errors.snapshot().slice(errorBefore.length);
            expectedDiagnosticErrors.push({action:"direct_actor_diagnostic_denial",code:denial,broker_delta:denialDelta});
            check(denial==="Forbidden","actual-native-actor-denial-before-binding-row-probes");
            check(denialDelta.length===0,"direct-native-denial-does-not-invent-a-controller-error-callback");
            await image("comparison-sable",false,"actual_native_actor_denial_with_frontend_clearing");
            r.setObserver({kind:"omniscient"});await summary();await readDiagnostic("recorded");
            const lateRow=r.inspectNarrationDiagnosticV1();r.select({turn:"courier-01",arm:"left"});await lateRow;
            check(r.get().diagnostic===null&&r.get().selected?.arm==="left","real-late-diagnostic-cannot-refill-other-row");
            await readDiagnostic("recorded");await image("comparison-recovered",false,"explicit_fresh_omniscient_read");
            await openFixture("diagnostic-missing");await readDiagnostic("no_observation");await image("comparison-guard");
            await openFixture("diagnostic-legacy");await readDiagnostic("no_declaration");await image("comparison-rollout");
            await r.close();current="diagnostic-recorded";await scenario("choose-diagnostic-recorded");await scenario("hold-picker");
            const opening=r.pick();await until(()=>r.get().status?.running===true);
            await image("comparison-pending",false,"held_picker_pending_not_diagnostic_io");
            const closing=r.close();await scenario("release-picker");await closing;await opening;
            check(r.get().source===null&&r.get().diagnostic===null,"real-late-picker-never-restores-closed-capability");
            await image("comparison-closed",false,"closed_native_reader_capability");
            await openFixture("diagnostic-malformed");const malformedBefore=errors.snapshot();
            await r.inspectNarrationDiagnosticV1();
            const malformedDelta=errors.snapshot().slice(malformedBefore.length);
            expectedDiagnosticErrors.push({action:"malformed_companion_refusal",code:r.get().error??"missing",broker_delta:malformedDelta});
            check(r.get().error==="EvaluationIntegrity"&&r.get().diagnostic===null,"actual-malformed-companion-is-integrity-refusal");
            check(malformedDelta.length===1&&malformedDelta[0].source==="native"&&malformedDelta[0].category==="Transport","actual-malformed-native-error-delta-retained");
            await image("comparison-unknown");
            await openFixture("diagnostic-recorded");await readDiagnostic("recorded");
            const lateContext=r.inspectNarrationDiagnosticV1();c.returnToPlay();
            await until(()=>!r.get().allowed);await lateContext;
            check(r.get().source===null&&r.get().diagnostic===null,"actual-context-retirement-fences-real-late-completion");
            c.requestLab();c.acknowledgeLab(true);await until(()=>r.get().allowed);
            await image("comparison-switched",false,"local_lab_context_clear_not_host_privilege_revocation");
        }
        await r.close();await observe();await c.refresh();
        check(structural(c.get().play??c.get().playV2)===canonicalBefore,"diagnostic-inspection-preserves-live-gameplay-canon");
        check(structural(errors.snapshot())===structural(expectedDiagnosticErrors.flatMap(e=>e.broker_delta)),"only-bounded-expected-native-error-deltas");
        await image("comparison-finished",false,"all_caps_closed_before_exit");
        await dispose();
        await invoke("harness_finish",{report:{synthetic:true,passed:true,stage:config.stage,protocolVersion:4,diagnosticReader:true,
            checks,errors:errors.snapshot(),expectedDiagnosticErrors,diagnosticCaptures,fixtureProof:diagnosticProof,
            modelObservation:diagnosticObservation,diagnosticPendingImage:"unavailable_no_io_hold_seam",
            pendingImage:"held_picker_only",realModelGeneration:false,nativeIpc:true,desktopInput:false,
            rendering:"native-webview2",nativeDialogsAutomated:false,timing}});
    };
    try {
        await c.start();
        const before = structural(c.get().play ?? c.get().playV2);
        c.requestLab();
        c.acknowledgeLab(true);
        await until(() => r.get().allowed);
        const rawPrepared=await scenario("prepare");
        if((rawPrepared as {kind?:string})?.kind==="narration_diagnostic_reader_fixture_v1") {
            await diagnosticJourneys(rawPrepared as DiagnosticFixtureProof,before);return;
        }
        const prepared = rawPrepared as {
            protocol_version: 2 | 3 | 4;
            paired_rows: number;
            rollout_rows: number;
            fixture_inventory: Record<string, string>;
            models_executed: boolean;
            scene_proof: FixtureProof | null;
        };
        protocolVersion = prepared.protocol_version;
        fixtureProof = prepared.scene_proof;
        fixtureInventory = prepared.fixture_inventory;
        check(
            [2, 3, 4].includes(prepared.protocol_version),
            "closed-comparison-protocol",
        );
        check(
            prepared.models_executed === false,
            "native-fixture-is-scripted-not-model-execution",
        );
        check(
            prepared.paired_rows === 24 && prepared.rollout_rows === 12,
            "actual-scripted-paired-and-rollout-fixtures",
        );
        if (protocolVersion === 4) {
            await scenario("cancel-picker");
            await r.pick();
            check(
                r.get().status?.phase === "cancelled" &&
                    r.get().source === null &&
                    r.get().summary === null,
                "actual-cancelled-picker-never-opens-a-report",
            );
            await r.close();
        }
        await scenario("choose-paired");
        failedCheck = "native-comparison-pick";
        await open();
        await summary();
        check(
            r.get().status?.phase === "ready" &&
                r.get().source?.rows.length === 24 &&
                r.get().source?.protocol_version ===
                    prepared.protocol_version &&
                r.get().summary?.report.version === prepared.protocol_version,
            "actual-comparison-reader-native-open",
        );
        check(
            r.get().summary?.report.version === prepared.protocol_version,
            "actual-versioned-report-decoded-through-controller",
        );
        check(
            r.get().summary?.report.source_matches === true,
            "fresh-compiled-source-match",
        );
        await capture(
            config.stage === "restart"
                ? "comparison-restarted"
                : "comparison-open",
            "#comparison-reader",
            true,
        );
        const first = r
            .get()
            .source!.rows.find((row) => row.receipt_available)!;
        check(first, "real-accepted-turn-source-present");
        if (prepared.protocol_version === 4) {
            const report = r.get().summary!.report;
            check(report.version === 4, "actual-protocol4-report-discriminant");
            if (report.version !== 4) throw Error("SceneReportRequired");
            check(
                fixtureProof?.source_gate ===
                    "fresh_domain1_committed_narrator_input_only" &&
                    fixtureProof.paired.rows === 24 &&
                    fixtureProof.rollout.rows === 12 &&
                    report.source_bound_committed_rows ===
                        fixtureProof.paired.source_bound_committed_rows,
                "actual-native-producer-and-Core-reader-source-count-preserved",
            );
            check(
                report.human_reviewed === 0 &&
                    report.human_rubric === "not_reviewed" &&
                    report.quality_accepted === false,
                "actual-protocol4-human-and-quality-not-invented",
            );
            check(
                report.turns.every(
                    (row) =>
                        row.construction.scene_capture_gate_version === 1 &&
                        row.construction.scene_frame_version === 1,
                ),
                "actual-protocol4-scene-descriptors-preserved",
            );
            const text =
                document.querySelector<HTMLElement>("#comparison-reader")
                    ?.innerText ?? "";
            check(
                text.includes("Literal scene") &&
                    text.includes("Relevant memory scene") &&
                    text.includes("committed narrator inputs checked") &&
                    text.includes("needs improvement") &&
                    text.includes("Protocol 4 selected-case rerun unavailable"),
                "actual-protocol4-visible-scope-and-limits",
            );
        }
        if (prepared.protocol_version === 3) {
            const text =
                document.querySelector<HTMLElement>("#comparison-reader")
                    ?.innerText ?? "";
            check(
                text.includes("Literal player conversation") &&
                    text.includes("Relevant memory"),
                "actual-native-construction-labels",
            );
            check(
                text.includes("Read-only Protocol 3 report") &&
                    text.includes(
                        "Selected experiments use their separate controls",
                    ),
                "actual-native-protocol3-explains-separate-selected-controls",
            );
            const before = r.get().status!;
            // Source3 now maps to selected2. Its separate selected journeys own
            // preparation/execution; this read-only journey must not consume it.
            await r.loadSummary();
            check(
                r.get().status?.run_token === before.run_token &&
                    r.get().summary?.report.version === 3,
                "read-only-refresh-preserves-native-protocol3-reader",
            );
        }
        await selectRow(first.row);
        await inspect("receipt");
        check(
            r.get().evidence?.body.kind === "receipt",
            "actual-rust-accepted-receipt",
        );
        if (protocolVersion === 4) {
            const turn = r
                .get()
                .summary!.report.turns.find(
                    (row) =>
                        row.turn === first.row.turn &&
                        row.arm === first.row.arm,
                )!;
            check(
                "narrator_prompt_sha256" in turn &&
                    turn.construction_evidence_status ===
                        "validated_committed_scene_narrator_v1" &&
                    /^[a-f0-9]{64}$/.test(turn.narrator_prompt_sha256 ?? "") &&
                    /^[a-f0-9]{64}$/.test(turn.narrator_schema_sha256 ?? "") &&
                    /^[a-f0-9]{64}$/.test(turn.scene_frame_sha256 ?? "") &&
                    /^[a-f0-9]{64}$/.test(turn.actual_receipt_sha256 ?? ""),
                "actual-source-bound-protocol4-status-and-hashes",
            );
            const selectedButton = [
                ...document.querySelectorAll<HTMLButtonElement>(
                    '[aria-label="Prepare selected experiment"] button',
                ),
            ].find(
                (node) => node.textContent?.trim() === "Prepare selected case",
            );
            check(
                !!selectedButton?.disabled,
                "protocol4-mounted-selected-admission-remains-disabled",
            );
        }
        await capture("comparison-receipt", ".comparison-selected");
        await inspect("capture");
        check(
            r.get().evidence?.body.kind === "capture",
            "actual-recorded-context-not-reconstruction",
        );
        await capture("comparison-capture", ".comparison-evidence");
        await inspect("outputs");
        check(
            r.get().evidence?.body.kind === "outputs",
            "actual-recorded-role-outputs",
        );
        await capture("comparison-outputs", ".comparison-evidence");
        await invoke("harness_viewport", { preset: "capture-narrow" });
        await capture("comparison-narrow", ".comparison-evidence");
        await invoke("harness_viewport", { preset: "wide" });
        r.setObserver({ kind: "character", id: "mira" });
        check(
            r.get().summary === null && r.get().evidence === null,
            "mira-transition-clears-all-raw-presentation",
        );
        await inspect("query", "after", "history");
        check(
            JSON.stringify(r.get().evidence).includes(
                "The pennant I carry has an amber stitch.",
            ) && !JSON.stringify(r.get().evidence).includes("SECRET-TIDE-731"),
            "mira-observed-dialogue-without-player-private-secret",
        );
        await capture("comparison-mira", ".comparison-selected");
        r.setObserver({ kind: "character", id: "sable" });
        await inspect("query", "after", "history");
        check(
            !JSON.stringify(r.get().evidence).includes(
                "The pennant I carry has an amber stitch.",
            ) && !JSON.stringify(r.get().evidence).includes("SECRET-TIDE-731"),
            "sable-withholds-unseen-dialogue-and-player-secret",
        );
        await capture("comparison-sable", ".comparison-selected");
        const status = r.get().status!,
            binding = r.get().source!.binding;
        let denial = "";
        try {
            await invoke("evaluation_comparison", {
                action: "evidence",
                query: {
                    runToken: status.run_token,
                    binding,
                    turnId: first.row.turn,
                    arm: first.row.arm,
                    request: {
                        kind: "capture",
                        observer: { kind: "character", id: "sable" },
                    },
                },
            });
        } catch (error) {
            denial = String(error);
        }
        check(denial === "Forbidden", "actual-native-raw-actor-denial");
        if (protocolVersion === 4) {
            let early = "";
            try {
                await invoke("evaluation_comparison", {
                    action: "evidence",
                    query: {
                        runToken: status.run_token,
                        binding: "0".repeat(64),
                        turnId: "not-an-actual-row",
                        arm: "left",
                        request: {
                            kind: "outputs",
                            observer: { kind: "character", id: "sable" },
                        },
                    },
                });
            } catch (error) {
                early = String(error);
            }
            check(
                early === "Forbidden",
                "actual-native-actor-raw-denial-precedes-binding-and-row-probes",
            );
            const originalEvidence = structural(r.get().evidence);
            let mismatch = "";
            try {
                await invoke("evaluation_comparison", {
                    action: "evidence",
                    query: {
                        runToken: status.run_token,
                        binding: "0".repeat(64),
                        turnId: first.row.turn,
                        arm: first.row.arm,
                        request: {
                            kind: "receipt",
                            observer: { kind: "omniscient" },
                        },
                    },
                });
            } catch (error) {
                mismatch = String(error);
            }
            check(
                mismatch === "EvaluationIntegrity" &&
                    structural(r.get().evidence) === originalEvidence,
                "actual-native-stale-binding-refused-without-changing-current-evidence",
            );
        }
        r.setObserver({ kind: "player" });
        await inspect("query", "before");
        check(
            JSON.stringify(r.get().evidence).includes("SECRET-TIDE-731"),
            "player-before-state-preserves-own-original-seed-knowledge",
        );
        r.setObserver({ kind: "omniscient" });
        await r.loadSummary();
        const guard = r
            .get()
            .source!.rows.find((row) => !row.receipt_available)!;
        check(guard, "real-guard-only-turn-present");
        await selectRow(guard.row);
        await inspect("receipt");
        check(
            r.get().evidence?.body.kind === "missing",
            "guard-does-not-invent-receipt",
        );
        if (
            prepared.protocol_version === 3 ||
            prepared.protocol_version === 4
        ) {
            const text =
                document.querySelector<HTMLElement>(".comparison-selected")
                    ?.innerText ?? "";
            check(
                text.includes("Not applicable") &&
                    !text.includes("Privacy pass"),
                "native-guard-has-no-generation-privacy-proof",
            );
        }
        await capture("comparison-guard", ".comparison-selected");
        await r.close();
        check(r.get().source === null, "explicit-close-clears-private-source");
        await scenario("hold-picker");
        const opening = r.pick();
        await until(() => r.get().status?.running === true);
        await capture("comparison-pending");
        const closing = r.close();
        await until(
            () =>
                r.get().status?.phase === "closing" || r.get().source === null,
        );
        await scenario("release-picker");
        await closing;
        await opening;
        check(
            r.get().source === null && r.get().summary === null,
            "late-picker-success-not-published-after-close",
        );
        await capture("comparison-closed");
        check(
            errors.snapshot().length === 0,
            "no-unexpected-errors-before-deliberate-lost-ack",
        );
        await scenario("lose-pick-ack");
        await r.pick();
        check(
            r.get().uncertain && !!r.get().clientId,
            "lost-open-ack-keeps-exact-client-for-recovery",
        );
        await capture("comparison-unknown");
        const client = r.get().clientId;
        await r.recover();
        check(
            r.get().status?.phase === "ready" && r.get().clientId === client,
            "same-client-recovers-existing-native-source",
        );
        await capture("comparison-recovered");
        await r.close();
        await scenario("choose-rollout");
        await open();
        await summary();
        check(
            r.get().source?.rows.length === 12 &&
                r.get().summary?.report.kind === "continuous_rollout",
            "separate-actual-rollout-source",
        );
        await capture("comparison-rollout", "#comparison-reader", true);
        if (protocolVersion === 4) {
            const session = c.selected()!;
            await c.closeSession();
            await until(() => r.get().source === null);
            check(
                r.get().summary === null && r.get().evidence === null,
                "actual-gameplay-session-close-retires-all-private-reader-data",
            );
            await c.resume(session.scope);
            check(
                c.selected()?.id !== session.id &&
                    structural(c.selected()?.scope) ===
                        structural(session.scope),
                "actual-new-Host-session-same-canonical-story",
            );
            await until(() => r.get().allowed);
            await scenario("choose-rollout");
            await open();
            await summary();
            check(
                r.get().source?.protocol_version === 4,
                "new-session-can-open-same-read-only-scene-report",
            );
        }
        c.returnToPlay();
        await until(() => r.get().source === null);
        check(
            r.get().summary === null && r.get().evidence === null,
            "surrounding-play-context-retires-all-private-data",
        );
        c.requestLab();
        c.acknowledgeLab(true);
        await until(() => r.get().allowed);
        await capture("comparison-switched");
        await c.refresh();
        check(
            structural(c.get().play ?? c.get().playV2) === before,
            "all-comparison-actions-preserve-live-gameplay-canon",
        );
        const recorded = errors.snapshot();
        check(
            recorded.length === 1 &&
                recorded[0].source === "native" &&
                recorded[0].category === "Transport",
            "only-deliberately-lost-open-ack-error-recorded",
        );
        await capture("comparison-finished");
        await dispose();
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                stage: config.stage,
                protocolVersion,
                checks,
                errors: errors.snapshot(),
                realModelGeneration: false,
                nativeIpc: true,
                desktopInput: false,
                rendering: "native-webview2",
                nativeDialogsAutomated: false,
                timing,
            },
        });
    } catch (error) {
        const originalFailedCheck = failedCheck;
        // Cleanup can retire the capability and replace the visible error.
        // Preserve the bounded original state before doing any cleanup work.
        const original = r.get();
        const originalFailure = {
            elapsedMs: Math.round(performance.now() - startedAt),
            error:
                error instanceof Error
                    ? error.message.slice(0, 256)
                    : String(error).slice(0, 256),
            comparisonError: original.error,
            phase: original.status?.phase ?? null,
            running: original.status?.running ?? null,
            busy: original.busy,
            uncertain: original.uncertain,
            sourceVersion: original.source?.protocol_version ?? null,
        };
        try {
            await invoke("harness_comparison_reader_case", {
                scenario: "release-picker",
            });
            await dispose();
        } catch {
            /* Preserve the original failure; never label cleanup as success. */
        }
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                stage: config.stage,
                protocolVersion,
                failedCheck: originalFailedCheck,
                failureCategory,
                checks,
                timing,
                originalFailure,
                errors: errors.snapshot(),
                comparisonError: r.get().error,
                phase: r.get().status?.phase,
                realModelGeneration: false,
            },
        });
    }
}
