import {
    checkedReaderEvidence,
    checkedReaderObserver,
    checkedReaderRequest,
    checkedReaderRow,
    checkedReaderSource,
    checkedReaderStatus,
    checkedReaderSummary,
    readerErrors,
    readerRowKey,
    sameReaderObserver,
    sameReaderSource,
} from "./comparison-reader-model";
import type {
    EvidenceRequest,
    ObserverV2,
    ReaderError,
    ReaderEvidence,
    ReaderSource,
    ReaderStatus,
    ReaderSummary,
    RowId,
} from "./comparison-reader-model";

export type ComparisonReaderInvoke = (
    name: string,
    args: Record<string, unknown>,
) => Promise<unknown>;
export type ComparisonReaderState = {
    context: string;
    allowed: boolean;
    observer: ObserverV2;
    clientId: string | null;
    status: ReaderStatus | null;
    source: ReaderSource | null;
    summary: ReaderSummary | null;
    selected: RowId | null;
    evidence: ReaderEvidence | null;
    busy: boolean;
    uncertain: boolean;
    error: ReaderError | null;
};
type Ticket = {
    context: number;
    request: number;
    client: string;
    lifecycle: number | null;
};
const POLL_MS = 300;
const MAX_STATUS_POLLS = 200;

function frozen<T>(value: T): T {
    if (
        value !== null &&
        typeof value === "object" &&
        !Object.isFrozen(value)
    ) {
        Object.values(value).forEach(frozen);
        Object.freeze(value);
    }
    return value;
}
function category(error: unknown): ReaderError {
    const message =
        error instanceof Error
            ? error.message
            : typeof error === "string"
              ? error
              : "";
    if (message === "ComparisonReaderWire") return message;
    return readerErrors.find((v) => v === message) ?? "EvaluationIo";
}
function uncertain(error: ReaderError): boolean {
    // An unacknowledged read is not an uncertain canonical write. Only its
    // in-memory client identity is retained for explicit status/close recovery.
    return (
        error === "EvaluationIo" ||
        error === "EvaluationInternal" ||
        error === "ComparisonReaderWire"
    );
}

export class ComparisonReaderController {
    private state: ComparisonReaderState = frozen<ComparisonReaderState>({
        context: "",
        allowed: false,
        observer: { kind: "omniscient" },
        clientId: null,
        status: null,
        source: null,
        summary: null,
        selected: null,
        evidence: null,
        busy: false,
        uncertain: false,
        error: null,
    });
    private listeners = new Set<() => void>();
    private contextEpoch = 0;
    private requestEpoch = 0;
    private lifecycleEpoch = 0;
    private lifecycleActive = false;
    private disposed = false;
    private closing = false;
    private retired = new Map<string, string | null>();
    private releasing = new Map<string, Promise<void>>();
    private nativeClients = new Set<string>();
    private reportingError = false;

    constructor(
        private invoke: ComparisonReaderInvoke,
        private onNativeError?: (error: ReaderError) => void,
    ) {}

    get(): Readonly<ComparisonReaderState> {
        return this.state;
    }
    subscribe(listener: () => void): () => void {
        if (!this.disposed) this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    }
    private patch(update: Partial<ComparisonReaderState>): void {
        this.state = frozen({ ...this.state, ...update });
        for (const listener of [...this.listeners]) {
            if (this.disposed) break;
            // A faulty presentation subscriber must not prevent other listeners
            // or the caller's ownership check/cleanup from running.
            try {
                listener();
            } catch {
                this.emitError("EvaluationInternal");
            }
        }
    }
    private emitError(error: ReaderError): void {
        if (this.reportingError) return;
        this.reportingError = true;
        try {
            this.onNativeError?.(error);
        } catch {
            /* callback is not authority */
        } finally {
            this.reportingError = false;
        }
    }
    private live(ticket: Ticket): boolean {
        return (
            this.ownsClient(ticket) &&
            this.state.allowed &&
            (ticket.lifecycle === null
                ? this.requestEpoch === ticket.request
                : this.lifecycleEpoch === ticket.lifecycle)
        );
    }
    private ownsClient(ticket: Ticket): boolean {
        return (
            !this.disposed &&
            this.contextEpoch === ticket.context &&
            this.state.clientId === ticket.client
        );
    }
    private ticket(client: string, lifecycle = false): Ticket {
        if (lifecycle) this.lifecycleActive = true;
        return {
            context: this.contextEpoch,
            request: ++this.requestEpoch,
            client,
            lifecycle: lifecycle ? ++this.lifecycleEpoch : null,
        };
    }
    private call(
        action: string,
        query: Record<string, unknown>,
    ): Promise<unknown> {
        return this.invoke("evaluation_comparison", { action, query });
    }
    private clearPrivate(): Partial<ComparisonReaderState> {
        return { summary: null, evidence: null, selected: null };
    }
    private rememberRetired(client: string | null, token: string | null): void {
        if (!client || (!this.nativeClients.has(client) && token === null))
            return;
        // New admission is refused until these old owners are released, so at
        // most one previous active client plus its late token is retained.
        this.nativeClients.add(client);
        this.retired.set(client, token ?? this.retired.get(client) ?? null);
    }
    private release(client: string): Promise<void> {
        const running = this.releasing.get(client);
        if (running) return running;
        if (!this.retired.has(client)) return Promise.resolve();
        const token = this.retired.get(client)!;
        const work = (async () => {
            try {
                const status = checkedReaderStatus(
                    await this.call("close", {
                        clientId: client,
                        runToken: token,
                    }),
                    client,
                );
                if (
                    status.phase === "closed" &&
                    this.retired.get(client) === token
                ) {
                    this.retired.delete(client);
                    this.nativeClients.delete(client);
                }
            } catch (error) {
                if (
                    category(error) === "UnknownEvaluationRun" &&
                    this.retired.get(client) === token
                ) {
                    this.retired.delete(client);
                    this.nativeClients.delete(client);
                }
            }
        })().finally(() => {
            this.releasing.delete(client);
            // A late original picker acknowledgement may reveal the token while
            // the exact null-token close was in flight. Release that token too.
            if (this.retired.has(client) && this.retired.get(client) !== token)
                void this.release(client);
        });
        this.releasing.set(client, work);
        return work;
    }
    private retire(client: string | null, token: string | null): void {
        this.rememberRetired(client, token);
        if (client) void this.release(client);
    }
    private async flushRetired(): Promise<void> {
        for (const client of [...this.retired.keys()])
            await this.release(client);
        if (this.retired.size) throw new Error("EvaluationBusy");
    }
    private failed(error: unknown, ticket: Ticket, recovery = false): void {
        if (!this.live(ticket)) return;
        const safe = category(error);
        if (ticket.lifecycle !== null) this.lifecycleActive = false;
        this.emitError(safe);
        if (!this.live(ticket)) return;
        const ended =
            recovery &&
            (safe === "UnknownEvaluationRun" ||
                (this.state.status === null && !uncertain(safe)));
        if (ended)
            this.rememberRetired(
                ticket.client,
                this.state.status?.run_token ?? null,
            );
        this.patch({
            error: safe,
            busy: false,
            uncertain: recovery && uncertain(safe),
            ...(ended
                ? {
                      clientId: null,
                      status: null,
                      source: null,
                      ...this.clearPrivate(),
                  }
                : {}),
        });
        if (ended) void this.release(ticket.client);
    }
    private invalid(error: ReaderError): void {
        if (this.disposed) return;
        this.patch({ error });
    }

    contextChanged(context: string, allowed: boolean): void {
        if (this.disposed) return;
        const valid =
            typeof context === "string" && typeof allowed === "boolean";
        const next = valid ? context : "",
            eligible = valid && allowed;
        if (next === this.state.context && eligible === this.state.allowed)
            return;
        const client = this.state.clientId,
            token = this.state.status?.run_token ?? null;
        // Install private epochs and context BEFORE any synchronous listener.
        this.contextEpoch++;
        this.requestEpoch++;
        this.lifecycleEpoch++;
        this.lifecycleActive = false;
        this.closing = false;
        this.rememberRetired(client, token);
        this.patch({
            context: next,
            allowed: eligible,
            clientId: null,
            status: null,
            source: null,
            ...this.clearPrivate(),
            busy: false,
            uncertain: false,
            error: null,
        });
        if (client) void this.release(client);
    }
    setObserver(value: ObserverV2): void {
        if (this.disposed) return;
        let observer: ObserverV2;
        try {
            observer = checkedReaderObserver(value);
        } catch {
            this.invalid("ComparisonReaderWire");
            return;
        }
        if (sameReaderObserver(observer, this.state.observer)) return;
        this.requestEpoch++;
        // The capability/metadata survive, but raw/private presentation never
        // crosses a local actor lens. An explicit new query is required.
        this.patch({
            observer,
            summary: null,
            evidence: null,
            busy: this.lifecycleActive && this.state.busy,
            error: null,
        });
    }
    clearEvidence(): void {
        if (this.disposed || this.state.busy) return;
        this.requestEpoch++;
        this.patch({ evidence: null, error: null });
    }
    select(value: RowId | null): void {
        if (this.disposed) return;
        let selected: RowId | null;
        try {
            selected = value === null ? null : checkedReaderRow(value);
        } catch {
            this.invalid("ComparisonReaderWire");
            return;
        }
        if (
            selected &&
            !this.state.source?.rows.some(
                (v) => readerRowKey(v.row) === readerRowKey(selected!),
            )
        ) {
            this.invalid("InvalidEvaluationInput");
            return;
        }
        if (
            selected === null
                ? this.state.selected === null
                : this.state.selected !== null &&
                  readerRowKey(selected) === readerRowKey(this.state.selected)
        )
            return;
        this.requestEpoch++;
        this.patch({
            selected,
            evidence: null,
            busy: this.lifecycleActive && this.state.busy,
            error: null,
        });
    }

    async pick(): Promise<void> {
        if (
            this.disposed ||
            !this.state.allowed ||
            this.state.busy ||
            this.state.clientId !== null
        )
            return;
        const client = crypto.randomUUID(),
            ticket = this.ticket(client, true);
        this.closing = false;
        this.patch({
            clientId: client,
            status: null,
            source: null,
            ...this.clearPrivate(),
            busy: true,
            uncertain: false,
            error: null,
        });
        if (!this.live(ticket)) return;
        try {
            await this.flushRetired();
            if (!this.live(ticket)) return;
            this.nativeClients.add(client);
            const raw = await this.call("pick", { clientId: client });
            const status = checkedReaderStatus(raw, client);
            if (!this.live(ticket)) {
                if (!this.ownsClient(ticket))
                    this.retire(client, status.run_token);
                return;
            }
            await this.follow(ticket, status);
        } catch (error) {
            this.failed(error, ticket, true);
        }
    }
    async recover(): Promise<void> {
        const client = this.state.clientId;
        if (this.disposed || !this.state.allowed || !client || this.state.busy)
            return;
        const ticket = this.ticket(client, true);
        this.patch({ busy: true, error: null });
        if (!this.live(ticket)) return;
        try {
            const status = checkedReaderStatus(
                await this.call("status", { clientId: client }),
                client,
            );
            if (!this.live(ticket)) {
                if (!this.ownsClient(ticket))
                    this.retire(client, status.run_token);
                return;
            }
            if (this.closing && status.phase === "ready") {
                const closed = checkedReaderStatus(
                    await this.call("close", {
                        clientId: client,
                        runToken: status.run_token,
                    }),
                    client,
                );
                if (!this.live(ticket)) return;
                await this.follow(ticket, closed);
            } else await this.follow(ticket, status);
        } catch (error) {
            this.failed(error, ticket, true);
        }
    }
    private async follow(ticket: Ticket, first: ReaderStatus): Promise<void> {
        let status = first;
        for (let polls = 0; ; polls++) {
            if (!this.live(ticket)) return;
            const retained = this.state.status;
            if (
                retained?.run_token &&
                status.run_token &&
                (status.run_token !== retained.run_token ||
                    status.binding !== retained.binding)
            )
                throw new Error("ComparisonReaderWire");
            if (
                retained?.running &&
                ["choosing", "opening"].includes(retained.phase) &&
                ["choosing", "opening", "ready"].includes(status.phase) &&
                retained.operation_id !== status.operation_id
            )
                throw new Error("ComparisonReaderWire");
            this.patch({ status, uncertain: false, error: status.error });
            if (!this.live(ticket)) return;
            if (status.phase === "ready") {
                if (this.closing) throw new Error("ComparisonReaderWire");
                const token = status.run_token!,
                    binding = status.binding!;
                const source = checkedReaderSource(
                    await this.call("source", { runToken: token }),
                    token,
                    binding,
                );
                if (!this.live(ticket)) return;
                this.lifecycleActive = false;
                this.patch({ source, busy: false });
                return;
            }
            if (["cancelled", "failed", "closed"].includes(status.phase)) {
                const closed = status.phase === "closed";
                if (closed) {
                    this.closing = false;
                    this.nativeClients.delete(ticket.client);
                }
                this.lifecycleActive = false;
                this.patch({
                    busy: false,
                    source: null,
                    ...this.clearPrivate(),
                    clientId: closed ? null : ticket.client,
                });
                return;
            }
            if (polls >= MAX_STATUS_POLLS) {
                // Known pending stays known; the next action is explicit SAME
                // client status recovery, never a second picker or a new key.
                this.lifecycleActive = false;
                this.patch({ busy: false });
                return;
            }
            await new Promise<void>((resolve) => setTimeout(resolve, POLL_MS));
            if (!this.live(ticket)) return;
            status = checkedReaderStatus(
                await this.call("status", { clientId: ticket.client }),
                ticket.client,
            );
            if (!this.live(ticket)) {
                if (!this.ownsClient(ticket))
                    this.retire(ticket.client, status.run_token);
                return;
            }
        }
    }
    private beginRead(): {
        ticket: Ticket;
        token: string;
        source: ReaderSource;
    } | null {
        const { allowed, busy, clientId, status, source } = this.state;
        if (
            this.disposed ||
            !allowed ||
            busy ||
            !clientId ||
            status?.phase !== "ready" ||
            !status.run_token ||
            !source ||
            this.closing
        )
            return null;
        const ticket = this.ticket(clientId),
            token = status.run_token;
        this.patch({ busy: true, error: null });
        return this.live(ticket) ? { ticket, token, source } : null;
    }
    async loadSummary(): Promise<void> {
        if (this.disposed || !this.state.allowed) return;
        if (this.state.observer.kind !== "omniscient") {
            this.invalid("Forbidden");
            return;
        }
        const read = this.beginRead();
        if (!read) return;
        const { ticket, token, source } = read;
        try {
            const summary = checkedReaderSummary(
                await this.call("summary", { runToken: token }),
                token,
                source.binding,
            );
            if (!this.live(ticket)) return;
            if (!sameReaderSource(summary, source))
                throw new Error("ComparisonReaderWire");
            this.patch({ summary, busy: false });
        } catch (error) {
            this.failed(error, ticket);
        }
    }
    async inspect(value: EvidenceRequest): Promise<void> {
        if (this.disposed || !this.state.allowed) return;
        let request: EvidenceRequest;
        try {
            request = checkedReaderRequest(value);
        } catch {
            this.invalid("ComparisonReaderWire");
            return;
        }
        // Refuse raw actor requests before row/binding/source lookup or dispatch.
        if (
            request.kind !== "query" &&
            request.observer.kind !== "omniscient"
        ) {
            this.invalid("Forbidden");
            return;
        }
        if (!sameReaderObserver(request.observer, this.state.observer)) {
            this.invalid("Forbidden");
            return;
        }
        const selected = this.state.selected;
        if (!selected) {
            this.invalid("InvalidEvaluationInput");
            return;
        }
        const read = this.beginRead();
        if (!read) return;
        const { ticket, token, source } = read;
        try {
            const raw = await this.call("evidence", {
                runToken: token,
                binding: source.binding,
                turnId: selected.turn,
                arm: selected.arm,
                request,
            });
            const evidence = checkedReaderEvidence(
                raw,
                token,
                source,
                selected,
                request,
            );
            if (!this.live(ticket)) return;
            this.patch({ evidence, busy: false });
        } catch (error) {
            this.failed(error, ticket);
        }
    }
    async close(): Promise<void> {
        if (this.disposed) return;
        const client = this.state.clientId;
        if (!client) return;
        const token = this.state.status?.run_token ?? null,
            ticket = this.ticket(client, true);
        this.closing = true;
        this.patch({
            source: null,
            ...this.clearPrivate(),
            busy: true,
            error: null,
        });
        if (!this.live(ticket)) return;
        try {
            const status = checkedReaderStatus(
                await this.call("close", { clientId: client, runToken: token }),
                client,
            );
            if (!this.live(ticket)) return;
            if (status.phase !== "closing" && status.phase !== "closed")
                throw new Error("ComparisonReaderWire");
            await this.follow(ticket, status);
        } catch (error) {
            this.failed(error, ticket, true);
        }
    }
    dispose(): void {
        if (this.disposed) return;
        const client = this.state.clientId,
            token = this.state.status?.run_token ?? null;
        this.disposed = true;
        this.contextEpoch++;
        this.requestEpoch++;
        this.lifecycleEpoch++;
        this.lifecycleActive = false;
        this.listeners.clear();
        this.state = frozen({
            ...this.state,
            allowed: false,
            clientId: null,
            status: null,
            source: null,
            ...this.clearPrivate(),
            busy: false,
            uncertain: false,
            error: null,
        });
        this.retire(client, token);
    }
}
