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
function sameCuratedRun(a: CuratedStatus, b: CuratedStatus) {
    return (
        a.run_id === b.run_id &&
        a.client_id === b.client_id &&
        a.lane === b.lane &&
        a.source_binding === b.source_binding
    );
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
    private allowed = false;
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
    private clearPresentation(extra: Partial<EvaluationState> = {}) {
        this.epoch++;
        this.evidenceEpoch++;
        this.patch({
            curatedStatus: null,
            curatedEvidence: null,
            curatedBusy: false,
            curatedError: null,
            curatedCase: null,
            curatedTurn: null,
            shown: false,
            status: null,
            report: null,
            selectedCase: null,
            selectedTurn: null,
            busy: false,
            error: null,
            ...extra,
        });
    }
    contextChanged(context: string, allowed: boolean) {
        if (this.context === context && this.allowed === allowed) return;
        this.context = context;
        this.allowed = allowed;
        this.clearPresentation({
            curatedCatalog: null,
            ...(!allowed ? { catalog: null } : {}),
        });
    }
    dispose() {
        this.allowed = false;
        this.clearPresentation({ catalog: null, curatedCatalog: null });
    }
    private canReadCurated() {
        return this.allowed && this.context.endsWith("|omniscient");
    }
    private errorCode(error: unknown) {
        const name = error instanceof Error ? error.message : String(error);
        return evaluationErrors.has(name) ? name : "EvaluationInvalidReply";
    }
    private fail(error: unknown) {
        this.patch({
            busy: false,
            error: this.errorCode(error),
        });
    }
    async show() {
        if (!this.allowed || this.state.busy || this.state.curatedBusy) return;
        const epoch = ++this.epoch;
        this.patch({ shown: true, error: null, busy: true });
        if (epoch !== this.epoch) return;
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
        this.clearPresentation();
    }
    private async action(
        command:
            | "evaluation_start"
            | "evaluation_open"
            | "evaluation_resume"
            | "evaluation_rerun",
        args: Record<string, unknown>,
        expectedRunId?: string,
    ) {
        if (!this.allowed || this.state.busy || this.state.curatedBusy) return;
        const epoch = ++this.epoch;
        this.patch({
            status: null,
            report: null,
            busy: true,
            error: null,
            selectedCase: null,
            selectedTurn: null,
        });
        if (epoch !== this.epoch) return;
        try {
            let status = decodeEvaluationStatus(
                await this.invoke(command, args),
            );
            if (epoch !== this.epoch) return;
            const first = status;
            const token = first.run_token;
            if (expectedRunId !== undefined && first.run_id !== expectedRunId)
                throw Error("EvaluationInvalidReply");
            for (;;) {
                if (epoch !== this.epoch) return;
                if (
                    status.run_token !== token ||
                    status.run_id !== first.run_id ||
                    (status.running &&
                        status.operation_id !== first.operation_id)
                )
                    throw Error("EvaluationInvalidReply");
                this.patch({ status });
                if (epoch !== this.epoch) return;
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
                        if (report.lane !== "deterministic_fake_shared_host")
                            throw Error("EvaluationInvalidReply");
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
                if (epoch !== this.epoch) return;
                if (!status.running) {
                    if (status.error) throw Error(status.error);
                    this.patch({ busy: false, error: null });
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
        return this.action("evaluation_open", { runId }, runId);
    }
    resume(batch: "one" | "all" = "all") {
        const status = this.state.status;
        return status
            ? this.action(
                  "evaluation_resume",
                  { runToken: status.run_token, batch },
                  status.run_id,
              )
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
        if (!status?.running || !status.operation_id) return;
        try {
            const reply = decodeEvaluationStatus(
                await this.invoke("evaluation_cancel", {
                    runToken: status.run_token,
                    operationId: status.operation_id,
                }),
            );
            if (
                reply.run_token !== status.run_token ||
                reply.run_id !== status.run_id ||
                (reply.running && reply.operation_id !== status.operation_id)
            )
                throw Error("EvaluationInvalidReply");
        } catch (e) {
            if (
                epoch === this.epoch &&
                this.state.status?.running &&
                this.state.status.operation_id === status.operation_id
            )
                this.patch({ error: this.errorCode(e) });
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
    private async curated(action: string, query: Record<string, unknown> = {}) {
        try {
            return await this.invoke("evaluation_curated", { action, query });
        } catch (error) {
            this.recordNativeError(this.errorCode(error));
            throw error;
        }
    }
    private curatedFailure(error: unknown) {
        this.patch({
            curatedBusy: false,
            curatedError: this.errorCode(error),
        });
    }
    private persistRecovery(client: string | null) {
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
    }
    private recovery(client: string | null) {
        this.persistRecovery(client);
        this.patch({ pendingClient: client });
    }
    async curatedShow() {
        if (!this.canReadCurated() || this.state.busy || this.state.curatedBusy)
            return;
        const epoch = this.epoch;
        try {
            const catalog = decodeCuratedCatalog(await this.curated("catalog"));
            if (epoch === this.epoch) {
                this.patch({ curatedCatalog: catalog, curatedError: null });
                if (
                    epoch === this.epoch &&
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
        action: "start" | "lookup" | "open" | "resume",
        query: Record<string, unknown>,
        expected?: CuratedStatus,
    ) {
        if (!this.canReadCurated() || this.state.busy || this.state.curatedBusy)
            return;
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
        if (epoch !== this.epoch) return;
        try {
            const client = action === "start" ? (query.clientId as string) : null;
            const priorClient = this.state.pendingClient;
            // Save the recovery identity before dispatch, but only publish it
            // to listeners once the command has actually been offered.
            if (client) this.persistRecovery(client);
            const reply = this.curated(action, query);
            if (client && this.state.pendingClient === priorClient)
                this.patch({ pendingClient: client });
            let status = decodeCuratedStatus(await reply);
            const first = status;
            if (
                ((action === "start" || action === "lookup") &&
                    first.client_id !== query.clientId) ||
                (action === "start" && first.lane !== query.lane) ||
                (action === "open" && first.run_id !== query.runId) ||
                (expected && !sameCuratedRun(first, expected))
            )
                throw Error("EvaluationInvalidReply");
            for (;;) {
                if (epoch !== this.epoch) return;
                if (
                    status.run_token !== first.run_token ||
                    !sameCuratedRun(status, first) ||
                    (status.running &&
                        status.operation_id !== first.operation_id)
                )
                    throw Error("EvaluationInvalidReply");
                this.patch({
                    curatedStatus: status,
                    curatedCase:
                        this.state.curatedCase ??
                        status.snapshot?.report.cases[0]?.id ??
                        null,
                });
                if (epoch !== this.epoch) return;
                if (!status.running) {
                    if (status.client_id === this.state.pendingClient)
                        this.recovery(null);
                    if (epoch === this.epoch)
                        this.patch({
                            curatedBusy: false,
                            curatedError: status.error,
                        });
                    return;
                }
                await new Promise((r) => setTimeout(r, 75));
                if (epoch !== this.epoch) return;
                status = decodeCuratedStatus(
                    await this.curated("status", { runToken: first.run_token }),
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
        return this.curatedAction("start", {
            clientId: crypto.randomUUID(),
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
        const status = this.state.curatedStatus;
        return status
            ? this.curatedAction(
                  "resume",
                  { runToken: status.run_token, batch, consent },
                  status,
              )
            : Promise.resolve();
    }
    async curatedCancel() {
        const status = this.state.curatedStatus,
            epoch = this.epoch;
        if (!status?.running || !status.operation_id) return;
        try {
            const reply = decodeCuratedStatus(
                await this.invoke("evaluation_cancel", {
                    runToken: status.run_token,
                    operationId: status.operation_id,
                }),
            );
            if (
                reply.run_token !== status.run_token ||
                !sameCuratedRun(reply, status) ||
                (reply.running && reply.operation_id !== status.operation_id)
            )
                throw Error("EvaluationInvalidReply");
        } catch (error) {
            if (
                epoch === this.epoch &&
                this.state.curatedStatus?.running &&
                this.state.curatedStatus.operation_id === status.operation_id
            )
                this.patch({ curatedError: this.errorCode(error) });
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
        if (
            !this.canReadCurated() ||
            !run?.snapshot ||
            !selected ||
            !turn ||
            !scope ||
            run.running
        )
            return;
        const effectiveView =
            view === "turn_diff" && turn.phase !== "committed"
                ? "profiles"
                : view;
        const epoch = this.epoch,
            sequence = ++this.evidenceEpoch;
        this.patch({ curatedEvidence: null, curatedError: null });
        if (epoch !== this.epoch || sequence !== this.evidenceEpoch) return;
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
