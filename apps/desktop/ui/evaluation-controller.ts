import {
    decodeCuratedCatalog,
    decodeCuratedStatus,
    decodeCuratedEvidence,
} from "./evaluation-model";
import type {
    CuratedCatalog,
    CuratedStatus,
    CuratedEvidence,
} from "./evaluation-model";
import type { InspectionQuery } from "./query-model";
import {
    decodeEvaluationCatalog,
    decodeEvaluationReport,
    decodeEvaluationStatus,
    evaluationErrors,
} from "./evaluation-model";
import type {
    EvaluationCatalog,
    EvaluationReport,
    EvaluationStatus,
} from "./evaluation-model";
export type EvaluationInvoke = (
    name: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
export interface EvaluationState {
    curatedCatalog: CuratedCatalog | null;
    curatedStatus: CuratedStatus | null;
    curatedEvidence: CuratedEvidence | null;
    curatedBusy: boolean;
    curatedError: string | null;
    curatedCase: string | null;
    curatedTurn: string | null;
    pendingClient: string | null;
    shown: boolean;
    catalog: EvaluationCatalog | null;
    status: EvaluationStatus | null;
    report: EvaluationReport | null;
    selectedCase: string | null;
    selectedTurn: string | null;
    busy: boolean;
    error: string | null;
}
export class EvaluationController {
    private state: EvaluationState = {
        curatedCatalog: null,
        curatedStatus: null,
        curatedEvidence: null,
        curatedBusy: false,
        curatedError: null,
        curatedCase: null,
        curatedTurn: null,
        pendingClient: null,
        shown: false,
        catalog: null,
        status: null,
        report: null,
        selectedCase: null,
        selectedTurn: null,
        busy: false,
        error: null,
    };
    private epoch = 0;
    private context = "";
    private evidenceEpoch = 0;
    private listeners = new Set<() => void>();
    constructor(
        private invoke: EvaluationInvoke,
        private recordNativeError: (category: string) => void = () => {},
    ) {}
    get = () => this.state;
    presentationVersion = () => this.epoch;
    matchesContext(context: string) {
        return this.context === context;
    }
    subscribe = (f: () => void) => {
        this.listeners.add(f);
        return () => {
            this.listeners.delete(f);
        };
    };
    private patch(v: Partial<EvaluationState>) {
        this.state = { ...this.state, ...v };
        for (const f of this.listeners) f();
    }
    contextChanged(context: string, allowed: boolean) {
        if (this.context === context) return;
        this.context = context;
        this.evidenceEpoch++;
        this.patch({
            curatedCatalog: null,
            curatedStatus: null,
            curatedEvidence: null,
            curatedBusy: false,
            curatedError: null,
            curatedCase: null,
            curatedTurn: null,
        });
        this.epoch++;
        this.patch({
            shown: false,
            status: null,
            report: null,
            selectedCase: null,
            selectedTurn: null,
            busy: false,
            error: null,
        });
        if (!allowed) this.patch({ catalog: null });
    }
    dispose() {
        this.epoch++;
        this.evidenceEpoch++;
        this.patch({
            curatedCatalog: null,
            curatedStatus: null,
            curatedEvidence: null,
            curatedBusy: false,
        });
        this.patch({ shown: false, status: null, report: null, busy: false });
    }
    private fail(error: unknown) {
        const name = error instanceof Error ? error.message : String(error);
        this.patch({
            busy: false,
            error: evaluationErrors.has(name) ? name : "EvaluationInvalidReply",
        });
    }
    async show() {
        const epoch = ++this.epoch;
        this.patch({ shown: true, error: null, busy: true });
        try {
            const catalog = decodeEvaluationCatalog(
                await this.invoke("evaluation_catalog"),
            );
            if (epoch === this.epoch) this.patch({ catalog, busy: false });
        } catch (e) {
            if (epoch === this.epoch) this.fail(e);
        }
    }
    hide() {
        this.epoch++;
        this.evidenceEpoch++;
        this.patch({
            curatedStatus: null,
            curatedEvidence: null,
            curatedBusy: false,
            curatedError: null,
            curatedCase: null,
            curatedTurn: null,
        });
        this.patch({
            shown: false,
            status: null,
            report: null,
            busy: false,
            selectedCase: null,
            selectedTurn: null,
        });
    }
    async action(
        command:
            | "evaluation_start"
            | "evaluation_open"
            | "evaluation_resume"
            | "evaluation_rerun",
        args: Record<string, unknown>,
    ) {
        const epoch = ++this.epoch;
        this.patch({
            status: null,
            report: null,
            busy: true,
            error: null,
            selectedCase: null,
            selectedTurn: null,
        });
        try {
            let status = decodeEvaluationStatus(
                await this.invoke(command, args),
            );
            if (epoch !== this.epoch) return;
            const token = status.run_token;
            for (;;) {
                if (epoch !== this.epoch) return;
                if (status.run_token !== token)
                    throw Error("EvaluationInvalidReply");
                this.patch({ status });
                if (status.completed_cases > 0 || !status.running) {
                    try {
                        const value = (await this.invoke("evaluation_read", {
                            runToken: token,
                            caseId: null,
                        })) as {
                            version: number;
                            run_token: string;
                            run_id: string;
                            case_id: null;
                            report: unknown;
                        };
                        if (epoch !== this.epoch) return;
                        if (
                            value.version !== 1 ||
                            value.run_token !== token ||
                            value.run_id !== status.run_id ||
                            value.case_id !== null
                        )
                            throw Error("EvaluationInvalidReply");
                        const report = decodeEvaluationReport(value.report);
                        this.patch({
                            report,
                            selectedCase:
                                this.state.selectedCase ??
                                report.cases[0]?.id ??
                                null,
                        });
                    } catch (e) {
                        if (
                            (e instanceof Error ? e.message : String(e)) ===
                                "EvaluationNotReady" &&
                            status.running
                        ) {
                        } else throw e;
                    }
                }
                if (!status.running) {
                    if (status.error) throw Error(status.error);
                    this.patch({ busy: false });
                    return;
                }
                await new Promise((r) => setTimeout(r, 75));
                if (epoch !== this.epoch) return;
                status = decodeEvaluationStatus(
                    await this.invoke("evaluation_status", { runToken: token }),
                );
            }
        } catch (e) {
            if (epoch === this.epoch) this.fail(e);
        }
    }
    start(caseId: string | null = null, batch: "one" | "all" = "all") {
        return this.action("evaluation_start", { caseId, batch });
    }
    open(runId: string) {
        return this.action("evaluation_open", { runId });
    }
    resume(batch: "one" | "all" = "all") {
        const token = this.state.status?.run_token;
        return token
            ? this.action("evaluation_resume", { runToken: token, batch })
            : Promise.resolve();
    }
    rerun() {
        const token = this.state.status?.run_token,
            id = this.state.selectedCase;
        return token && id
            ? this.action("evaluation_rerun", { runToken: token, caseId: id })
            : Promise.resolve();
    }
    async cancel() {
        const status = this.state.status,
            epoch = this.epoch;
        if (!status?.operation_id) return;
        try {
            await this.invoke("evaluation_cancel", {
                runToken: status.run_token,
                operationId: status.operation_id,
            });
        } catch (e) {
            if (epoch === this.epoch) this.fail(e);
        }
    }
    selectCase(id: string) {
        if (this.state.report?.cases.some((c) => c.id === id))
            this.patch({ selectedCase: id, selectedTurn: null });
    }
    selectTurn(id: string) {
        if (
            this.selected()?.turns.some((t) => t.id === id) ||
            id.startsWith("seed:")
        )
            this.patch({ selectedTurn: id });
    }
    selected() {
        return this.state.report?.cases.find(
            (c) => c.id === this.state.selectedCase,
        );
    }
    private curated(action: string, query: Record<string, unknown> = {}) {
        return this.invoke("evaluation_curated", { action, query }).catch(
            (error) => {
                const code =
                    error instanceof Error ? error.message : String(error);
                this.recordNativeError(
                    evaluationErrors.has(code)
                        ? code
                        : "EvaluationInvalidReply",
                );
                throw error;
            },
        );
    }
    private curatedFailure(error: unknown) {
        const name = error instanceof Error ? error.message : String(error);
        this.patch({
            curatedBusy: false,
            curatedError: evaluationErrors.has(name)
                ? name
                : "EvaluationInvalidReply",
        });
    }
    private recovery(client: string | null) {
        try {
            if (typeof localStorage !== "undefined") {
                if (client)
                    localStorage.setItem(
                        "locallore.curated.pending.v1",
                        client,
                    );
                else localStorage.removeItem("locallore.curated.pending.v1");
            }
        } catch {
            /* Native library/lookup remain available when browser storage is denied. */
        }
        this.patch({ pendingClient: client });
    }
    async curatedShow() {
        const epoch = this.epoch;
        try {
            const catalog = decodeCuratedCatalog(await this.curated("catalog"));
            if (epoch === this.epoch) {
                this.patch({ curatedCatalog: catalog, curatedError: null });
                if (
                    !this.state.pendingClient &&
                    typeof localStorage !== "undefined"
                ) {
                    try {
                        const id = localStorage.getItem(
                            "locallore.curated.pending.v1",
                        );
                        if (id && /^[a-f0-9-]{36}$/.test(id))
                            this.patch({ pendingClient: id });
                    } catch {}
                }
            }
        } catch (error) {
            if (epoch === this.epoch) this.curatedFailure(error);
        }
    }
    private async curatedAction(
        action: string,
        query: Record<string, unknown>,
    ) {
        if (this.state.busy || this.state.curatedBusy) return;
        const epoch = ++this.epoch;
        this.evidenceEpoch++;
        this.patch({
            curatedBusy: true,
            curatedError: null,
            curatedEvidence: null,
            curatedCase: null,
            curatedTurn: null,
            curatedStatus: null,
        });
        try {
            let status = decodeCuratedStatus(await this.curated(action, query));
            const token = status.run_token,
                runId = status.run_id,
                clientId = status.client_id,
                bound = status.source_binding,
                lane = status.lane;
            for (;;) {
                if (epoch !== this.epoch) return;
                if (
                    status.run_token !== token ||
                    status.run_id !== runId ||
                    status.client_id !== clientId ||
                    status.source_binding !== bound ||
                    status.lane !== lane
                )
                    throw Error("EvaluationInvalidReply");
                this.patch({
                    curatedStatus: status,
                    curatedCase:
                        this.state.curatedCase ??
                        status.snapshot?.report.cases[0]?.id ??
                        null,
                });
                if (!status.running) {
                    this.patch({ curatedBusy: false });
                    if (status.client_id === this.state.pendingClient)
                        this.recovery(null);
                    if (status.error) throw Error(status.error);
                    return;
                }
                await new Promise((r) => setTimeout(r, 75));
                if (epoch !== this.epoch) return;
                status = decodeCuratedStatus(
                    await this.curated("status", { runToken: token }),
                );
            }
        } catch (error) {
            if (epoch === this.epoch) this.curatedFailure(error);
        }
    }
    curatedStart(
        lane: "scripted" | "native",
        caseId: string | null = null,
        batch: "one" | "all" = "all",
        consent = false,
    ) {
        if (this.state.busy || this.state.curatedBusy) return Promise.resolve();
        const clientId = crypto.randomUUID();
        this.recovery(clientId);
        return this.curatedAction("start", {
            clientId,
            lane,
            caseId,
            batch,
            consent,
        });
    }
    curatedRecover() {
        const clientId = this.state.pendingClient;
        return clientId
            ? this.curatedAction("lookup", { clientId })
            : Promise.resolve();
    }
    curatedOpen(runId: string) {
        return this.curatedAction("open", { runId });
    }
    curatedResume(consent = false, batch: "one" | "all" = "all") {
        const runToken = this.state.curatedStatus?.run_token;
        return runToken
            ? this.curatedAction("resume", { runToken, batch, consent })
            : Promise.resolve();
    }
    async curatedCancel() {
        const status = this.state.curatedStatus,
            epoch = this.epoch;
        if (!status?.operation_id) return;
        try {
            await this.invoke("evaluation_cancel", {
                runToken: status.run_token,
                operationId: status.operation_id,
            });
        } catch (error) {
            if (epoch === this.epoch) this.curatedFailure(error);
        }
    }
    curatedSelectCase(id: string) {
        if (
            this.state.curatedStatus?.snapshot?.report.cases.some(
                (c) => c.id === id,
            )
        ) {
            this.evidenceEpoch++;
            this.patch({
                curatedCase: id,
                curatedTurn: null,
                curatedEvidence: null,
            });
        }
    }
    curatedSelectTurn(id: string) {
        if (this.curatedSelected()?.turns.some((t) => t.id === id)) {
            this.evidenceEpoch++;
            this.patch({ curatedTurn: id, curatedEvidence: null });
        }
    }
    curatedSelected() {
        return this.state.curatedStatus?.snapshot?.report.cases.find(
            (c) => c.id === this.state.curatedCase,
        );
    }
    async curatedInspect(
        observer: InspectionQuery["observer"] = { kind: "omniscient" },
        view: InspectionQuery["view"] = "turn_diff",
    ) {
        const run = this.state.curatedStatus,
            selected = this.curatedSelected(),
            turn = selected?.turns.find((t) => t.id === this.state.curatedTurn);
        const scope = this.state.curatedCatalog?.cases
            .find((c) => c.id === selected?.id)
            ?.sources.find((s) => s.turn === turn?.id)?.scope;
        if (!run?.snapshot || !selected || !turn || !scope || run.running)
            return;
        const effectiveView =
            view === "turn_diff" && turn.phase !== "committed"
                ? "profiles"
                : view;
        const epoch = this.epoch,
            sequence = ++this.evidenceEpoch;
        this.patch({ curatedEvidence: null, curatedError: null });
        try {
            const evidence = decodeCuratedEvidence(
                await this.curated("evidence", {
                    runToken: run.run_token,
                    binding: run.snapshot.binding_sha256,
                    caseId: selected.id,
                    turnId: turn.id,
                    observer,
                    view: effectiveView,
                }),
                run,
                selected.id,
                turn,
                scope,
                observer,
                effectiveView,
            );
            if (epoch === this.epoch && sequence === this.evidenceEpoch)
                this.patch({ curatedEvidence: evidence });
        } catch (error) {
            if (epoch === this.epoch && sequence === this.evidenceEpoch)
                this.curatedFailure(error);
        }
    }
}
