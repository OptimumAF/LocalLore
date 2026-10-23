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
    private listeners = new Set<() => void>();
    constructor(private invoke: EvaluationInvoke) {}
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
}
