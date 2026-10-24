import { category, categories, request as typedRequest, sameScope, structural } from "./model";
import type { Action, FakeMode, Gateway, Request, Scope } from "./model";
import { checkedPageV2, checkedPlaySnapshotV2 } from "./v2-view-model";
import type { InspectionPageV2, InspectionQueryV2, ObserverV2, PlaySnapshotV2, SourceV2, ViewV2 } from "./v2-view-model";

export interface V2PlayContext {
    session: string; scope: Scope; revision: number; player: string;
    view: "play" | "lab"; observer: ObserverV2; persistent: boolean;
    /** OTHER Root work only: own pending/uncertain is exposed separately below. */
    pending: boolean; blocked: boolean; playMode: "fixture" | "local";
    inputKind: "action" | "dialogue"; action: Action; fakeMode: FakeMode;
}
export interface V2Receipt {
    request: Request; proposal: Record<string, unknown>;
    events: { version: number; scope: Scope; sequence: number; turn: string;
        rules: string; seed: string; story_time: number; participants: string[];
        witnesses: string[]; outcome: Record<string, unknown> }[];
    narration: string; play?: Record<string, unknown>;
}
export interface V2TurnStatus {
    turn: string; scope: Scope; expected_revision: number;
    phase: "queued" | "running" | "ready" | "committed" | "cancelled" | "failed" | "stale";
    error: string | null; receipt: V2Receipt | null;
}
export interface V2BoundPage { query: InspectionQueryV2; page: InspectionPageV2 }
export interface V2RetainedTurn { session: string; request: Request; mode: FakeMode; cancelRequested: boolean }
export interface V2PlayState {
    context: V2PlayContext | null; snapshot: PlaySnapshotV2 | null;
    history: V2BoundPage | null; inspection: V2BoundPage | null;
    draft: string; pending: (V2RetainedTurn & { stage: string }) | null;
    uncertain: V2RetainedTurn | null; status: V2TurnStatus | null;
    receipt: V2Receipt | null; error: string | null; notice: string;
    readBusy: boolean; queryBusy: boolean; source: SourceV2 | null;
    sourceMatched: boolean | null;
}
interface Operation extends V2RetainedTurn {
    player: string;
    key: string; retired: boolean; started: boolean; submitted: boolean;
    terminal: boolean; unknown: boolean; committed: V2TurnStatus | null;
    terminalStatus: V2TurnStatus | null;
    refreshed: boolean;
    promise: Promise<void>;
}
const utf8 = (value: string) => new TextEncoder().encode(value).length;
const wire = (): never => { throw Error("Wire"); };
function record(value: unknown): Record<string, unknown> {
    if (!value || typeof value !== "object" || Array.isArray(value)) wire();
    return value as Record<string, unknown>;
}
function exact(value: unknown, keys: string[]) {
    const object = record(value);
    if (Object.keys(object).sort().join("\0") !== [...keys].sort().join("\0")) wire();
    return object;
}
function text(value: unknown): string { if (typeof value !== "string") wire(); return value; }
function integer(value: unknown): number { if (!Number.isSafeInteger(value) || (value as number) < 0) wire(); return value as number; }
function id(value: unknown): string { const result = text(value); if (!/^[A-Za-z0-9_-]{1,64}$/.test(result)) wire(); return result; }
function scoped(value: unknown): Scope { const r = exact(value, ["story", "branch"]); return {story:id(r.story), branch:id(r.branch)}; }
function detached(value: unknown, cap: number): unknown {
    try { const encoded = JSON.stringify(value); if (typeof encoded !== "string" || utf8(encoded) > cap) wire(); return JSON.parse(encoded); }
    catch { return wire(); }
}
function ids(value: unknown): string[] {
    if (!Array.isArray(value)) wire();
    const result = value.map(id);
    if (new Set(result).size !== result.length) wire();
    return result;
}
// Transport shape/binding only. Rust remains the only accepted-outcome validator.
function receipt(value: unknown, request: Request): V2Receipt {
    const r = record(detached(value, 65_536));
    exact(r, ["request", "proposal", "events", "narration", ...(Object.hasOwn(r, "play") ? ["play"] : [])]);
    if (structural(r.request) !== structural(request)) wire();
    const proposal = exact(r.proposal, ["version", "scope", "turn", "expected_revision", "commands"]);
    if (proposal.version !== 1 || !sameScope(scoped(proposal.scope), request.scope) || proposal.turn !== request.turn || proposal.expected_revision !== request.expected_revision || !Array.isArray(proposal.commands) || proposal.commands.length < 1 || proposal.commands.length > 8) wire();
    if (!Array.isArray(r.events) || r.events.length < 1 || r.events.length > 8) wire();
    r.events.forEach((value, index) => {
        const event = exact(value, ["version", "scope", "sequence", "turn", "rules", "seed", "story_time", "participants", "witnesses", "outcome"]);
        if (event.version !== 1 || !sameScope(scoped(event.scope), request.scope) || event.turn !== request.turn || integer(event.sequence) !== request.expected_revision + index + 1 || !["fantasy_v1", "narrative_v1"].includes(text(event.rules))) wire();
        id(event.seed); integer(event.story_time); ids(event.participants); ids(event.witnesses);
        text(record(event.outcome).effect);
    });
    text(r.narration);
    if (Object.hasOwn(r, "play")) {
        const play = record(r.play);
        exact(play, ["version", "policy", "prompt_version", "profile", "repairs", "fallback", "narration", "stages", ...(Object.hasOwn(play, "context") ? ["context"] : []), ...(Object.hasOwn(play, "context_policy") ? ["context_policy"] : [])]);
        if (integer(play.version) > 65535 || typeof play.fallback !== "boolean") wire();
        text(play.policy); text(play.prompt_version); integer(play.repairs);
        const profile = exact(play.profile, ["id", "model_sha256", "runtime_revision", "template_sha256", "worker_sha256", "profile_manifest_sha256", "context_tokens", "director_tokens", "narrator_tokens", "deadline_ms", "repair_limit"]);
        for (const key of ["id", "model_sha256", "runtime_revision", "template_sha256", "worker_sha256", "profile_manifest_sha256"]) text(profile[key]);
        for (const key of ["context_tokens", "director_tokens", "narrator_tokens", "deadline_ms", "repair_limit"]) integer(profile[key]);
        const narration = exact(play.narration, ["text", "event_ids", "speaker"]);
        if (text(narration.text) !== r.narration || !Array.isArray(narration.event_ids)) wire();
        narration.event_ids.forEach(integer); text(narration.speaker);
        if (!Array.isArray(play.stages)) wire();
        play.stages.forEach(v => { const stage = exact(v, ["stage", "elapsed_ms"]); text(stage.stage); integer(stage.elapsed_ms); });
        // Optional historical/current count provenance is preserved as bounded
        // data; it cannot grant coverage, knowledge or canonical validity.
        if (Object.hasOwn(play, "context")) record(play.context);
        if (Object.hasOwn(play, "context_policy")) text(play.context_policy);
    }
    return r as unknown as V2Receipt;
}
function status(value: unknown, request: Request): V2TurnStatus {
    const r = exact(detached(value, 262_144), ["turn", "scope", "expected_revision", "phase", "error", "receipt"]);
    if (r.turn !== request.turn || !sameScope(scoped(r.scope), request.scope) || r.expected_revision !== request.expected_revision || !["queued", "running", "ready", "committed", "cancelled", "failed", "stale"].includes(text(r.phase)) || (r.error !== null && !categories.has(text(r.error)))) wire();
    if (r.phase === "committed") r.receipt = receipt(r.receipt, request);
    else if (r.receipt !== null) wire();
    return r as unknown as V2TurnStatus;
}
function context(value: V2PlayContext): V2PlayContext {
    const c = detached(value, 16_384) as V2PlayContext;
    scoped(c.scope); id(c.session); id(c.player); integer(c.revision);
    if (!["play", "lab"].includes(c.view) || !["fixture", "local"].includes(c.playMode) || !["action", "dialogue"].includes(c.inputKind) || !["give", "ability", "wait", "dialogue"].includes(c.action) || !["accepted", "delayed", "malformed", "rejected", "failed", "cancelled"].includes(c.fakeMode) || [c.persistent, c.pending, c.blocked].some(v => typeof v !== "boolean")) wire();
    if (c.observer.kind === "character") id(c.observer.id);
    else if (!["player", "omniscient"].includes(c.observer.kind)) wire();
    return c;
}
const lens = (c: V2PlayContext): ObserverV2 => c.view === "play" ? {kind:"player"} : c.observer;

export class V2PlayController {
    private state: V2PlayState = {context:null,snapshot:null,history:null,inspection:null,draft:"",pending:null,uncertain:null,status:null,receipt:null,error:null,notice:"",readBusy:false,queryBusy:false,source:null,sourceMatched:null};
    private listeners = new Set<() => void>();
    private key = "none";
    private readSequence = 0;
    private querySequence = 0;
    private historySequence = 0;
    private turn = 0;
    private active: Operation | null = null;
    private retained: Operation | null = null;
    private disposed = false;
    constructor(private gateway: Gateway, private refreshRoot: () => Promise<void>, private prefix = `v2-${crypto.randomUUID()}`) {
        if (!/^[A-Za-z0-9_-]{1,48}$/.test(prefix)) throw Error("Wire");
    }
    get = () => this.state;
    subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
    private patch(patch: Partial<V2PlayState>) { if (this.disposed) return; this.state = {...this.state,...patch}; for (const listener of this.listeners) listener(); }
    private current(key: string) { return !this.disposed && this.key === key; }
    private presenting(op: Operation) { return !op.retired && this.current(op.key); }
    private retainedValue(op: Operation): V2RetainedTurn { return {session:op.session,request:structuredClone(op.request),mode:op.mode,cancelRequested:op.cancelRequested}; }
    private unresolved(op: Operation) {
        if (op.terminal || op.committed) return;
        op.unknown = true;
        this.patch({uncertain:this.retainedValue(op),notice:"Original turn unresolved. Read status or explicitly resume this exact request; another turn is blocked."});
    }
    selectedContextChanged(value: V2PlayContext | null) {
        if (this.disposed) return;
        let next: V2PlayContext | null;
        try { next = value ? context(value) : null; }
        catch { next = null; }
        const key = structural(next);
        if (key === this.key) return;
        const previous = this.state.context;
        const sameIdentity = !!next && !!previous && next.session === previous.session && sameScope(next.scope, previous.scope) && next.player === previous.player;
        const ownCommitted = this.retained?.committed;
        const candidateReceipt = this.state.receipt ?? (this.retained && next
            && this.retained.session === next.session && sameScope(this.retained.request.scope,next.scope)
            && this.retained.player === next.player ? ownCommitted?.receipt ?? null : null);
        const receiptHead = candidateReceipt?.events.at(-1)?.sequence ?? 0;
        const keepReceipt = sameIdentity && next?.view === "play" && previous?.view === "play"
            && next.revision >= receiptHead && structural(next.observer) === structural(previous.observer);
        this.key = key; this.readSequence++; this.querySequence++; this.historySequence++;
        if (this.retained && !this.retained.terminal) { this.retained.retired = true; this.retained.unknown = true; }
        this.patch({context:next,snapshot:null,history:null,inspection:null,readBusy:false,queryBusy:false,source:null,sourceMatched:null,
            draft:sameIdentity ? this.state.draft : "", receipt:keepReceipt ? candidateReceipt : null,
            status:keepReceipt && candidateReceipt ? ownCommitted ?? this.state.status : null,
            error:value && !next ? "Wire" : null,
            uncertain:this.retained && !this.retained.terminal ? this.retainedValue(this.retained) : null,
            notice:this.retained && !this.retained.terminal ? "Original turn retained across context change. Its outcome is unresolved." : ""});
    }
    setDraft(draft: string) { if (utf8(draft) > 2048) { this.patch({error:"TooLarge"}); return; } this.patch({draft}); }
    async refresh(reconcile = true) {
        const original = this.state.context;
        if (!original || this.disposed) return;
        if (reconcile) {
            const requestedKey = this.key;
            this.patch({readBusy:true});
            try { await this.refreshRoot(); }
            catch(error) { if (this.current(requestedKey)) this.patch({readBusy:false,error:category(error)}); return; }
            const selected = this.state.context;
            if (!selected || selected.session !== original.session || !sameScope(selected.scope,original.scope) || selected.player !== original.player) return;
        }
        const c = this.state.context, key = this.key, sequence = ++this.readSequence;
        if (!c || this.disposed) return;
        this.patch({readBusy:true,error:null});
        try {
            const value = await this.gateway.call({op:"play_snapshot_v2",session:c.session,scope:c.scope,expected_revision:c.revision});
            const snapshot = checkedPlaySnapshotV2(value,c.scope,c.revision);
            if (snapshot.player.observer !== c.player) wire();
            if (!this.current(key) || sequence !== this.readSequence) return;
            this.patch({snapshot});
            if (!this.current(key) || sequence !== this.readSequence) return;
            await this.query({view:"history",atRevision:null,search:""},"history");
        } catch(error) { if (this.current(key) && sequence === this.readSequence) this.patch({error:category(error)}); }
        finally { if (this.current(key) && sequence === this.readSequence) this.patch({readBusy:false}); }
    }
    private async query(options: {view:ViewV2;atRevision:number|null;search:string}, channel:"history"|"inspection", cursor:string|null = null): Promise<V2BoundPage|null> {
        const c = this.state.context, key = this.key;
        if (!c || this.disposed || !this.state.snapshot) return null;
        if (utf8(options.search) > 256 || /[\u0000-\u001f\u007f-\u009f]/.test(options.search)
            || (options.atRevision !== null && (!Number.isSafeInteger(options.atRevision) || options.atRevision < 0 || options.atRevision > c.revision))) {
            this.patch({error:"InvalidRequest"}); return null;
        }
        const sequence = channel === "history" ? ++this.historySequence : ++this.querySequence;
        const query: InspectionQueryV2 = {version:2,scope:{...c.scope},expected_head:c.revision,at_revision:options.atRevision,observer:structuredClone(lens(c)),view:options.view,cursor,limit:64,search:options.search};
        if (channel === "inspection") this.patch({queryBusy:true,error:null,source:null,sourceMatched:null});
        try {
            const value = await this.gateway.call({op:"inspection_query",session:c.session,query});
            const page = checkedPageV2(value,query,c.player);
            if (!this.current(key) || sequence !== (channel === "history" ? this.historySequence : this.querySequence)) return null;
            const result = {query,page};
            this.patch(channel === "history" ? {history:result} : {inspection:result});
            return result;
        } catch(error) { if (this.current(key) && sequence === (channel === "history" ? this.historySequence : this.querySequence)) this.patch({error:category(error)}); return null; }
        finally { if (channel === "inspection" && this.current(key) && sequence === this.querySequence) this.patch({queryBusy:false}); }
    }
    readQuery(options: {view:ViewV2;atRevision:number|null;search:string}) { return this.query(options,"inspection"); }
    page(cursor: string, channel:"history"|"inspection" = "inspection") {
        const bound = channel === "history" ? this.state.history : this.state.inspection;
        if (!bound || cursor !== bound.page.next_cursor) { this.patch({error:"InvalidCursor"}); return Promise.resolve(null); }
        return this.query({view:bound.query.view,atRevision:bound.query.at_revision,search:bound.query.search},channel,cursor);
    }
    async source(source: SourceV2, from?: V2BoundPage) {
        const c = this.state.context, key = this.key;
        if (!c || source.kind === "withheld") return;
        if (from && from !== this.state.history && from !== this.state.inspection) { this.patch({error:"Scope"}); return; }
        if (source.kind === "scoped_event" && (source.value.original_scope.story !== c.scope.story || !Number.isSafeInteger(source.value.sequence) || source.value.sequence < 1 || source.value.sequence > c.revision)) { this.patch({error:"Scope"}); return; }
        const atRevision = from ? from.query.at_revision : this.state.inspection?.query.at_revision ?? null;
        const result = await this.query(source.kind === "seed" ? {view:"profiles",atRevision:0,search:""} : {view:"history",atRevision,search:`"sequence":${source.value.sequence},`},"inspection");
        if (!result || !this.current(key) || this.state.inspection !== result) return;
        const matched = source.kind === "scoped_event" && result.page.rows.some(row => row.kind === "event" && row.event.sequence === source.value.sequence && sameScope(row.event.scope,source.value.original_scope));
        this.patch({source:structuredClone(source),sourceMatched:matched,
            notice:source.kind === "seed" ? "Seed-era profiles; no additional source identity is inferred." : matched ? "Matched actual original-scope event within the selected timeline and observer." : "Original-scope event is not present in this permitted page; no substitute source is asserted."});
    }
    private control(op: Operation, command:"prepare"|"commit"|"cancel"|"turn_status") {
        return this.gateway.call({op:command,session:op.session,scope:{...op.request.scope},turn:op.request.turn}).then(value => status(value,op.request));
    }
    private accept(op: Operation, value: V2TurnStatus) {
        if (op.committed) return op.committed;
        if (op.terminalStatus && value.phase !== "committed") return op.terminalStatus;
        if (value.phase === "committed") op.committed = value;
        op.terminal = ["committed","cancelled","failed","stale"].includes(value.phase);
        if (op.terminal) { op.unknown = false; op.terminalStatus = value; }
        if (this.retained === op && op.terminal) this.patch({uncertain:null});
        if (this.presenting(op)) {
            const committed = value.phase === "committed";
            this.patch({status:value,receipt:committed ? value.receipt : this.state.receipt,
                error:committed || value.phase === "cancelled" ? null : value.error ?? (value.phase === "failed" || value.phase === "stale" ? value.phase : null),
                notice:committed ? (this.state.context?.persistent ? "Committed and saved by Rust." : "Committed by Rust; progress is in memory.") : value.phase === "cancelled" ? "Rust reports this original turn cancelled." : value.error ?? value.phase,
                pending:op.terminal ? null : this.state.pending});
            if (committed && ["dialogue","free_text"].includes(op.request.intent.kind)) {
                const intent = op.request.intent as {kind:string;value:{text:string}};
                if (this.state.draft === intent.value.text) this.patch({draft:""});
            }
        }
        return value;
    }
    private async drive(op: Operation, admission: boolean) {
        try {
            let result: V2TurnStatus;
            if (!this.presenting(op) || (op.cancelRequested && !op.started)) {
                if (op.started) this.unresolved(op);
                else { op.terminal = true; op.unknown = false; this.patch({uncertain:null,notice:"This local request was not submitted. No canonical cancellation is claimed."}); }
                return;
            }
            if (admission) {
                op.started = true;
                const value = await this.gateway.call(op.request.intent.kind === "free_text" ? {op:"free_text",session:op.session,request:structuredClone(op.request)} : {op:"submit",session:op.session,request:structuredClone(op.request),mode:op.mode});
                result = status(value,op.request); op.submitted = true;
            } else {
                try { result = await this.control(op,"turn_status"); op.submitted = true; }
                catch(error) {
                    if (category(error) !== "UnknownTurn" || !this.presenting(op)) throw error;
                    op.started = true;
                    const value = await this.gateway.call(op.request.intent.kind === "free_text" ? {op:"free_text",session:op.session,request:structuredClone(op.request)} : {op:"submit",session:op.session,request:structuredClone(op.request),mode:op.mode});
                    result = status(value,op.request); op.submitted = true;
                }
            }
            result = this.accept(op,result);
            if (op.terminal) { await this.afterTerminal(op); return; }
            if (op.cancelRequested) { result = this.accept(op,await this.control(op,"cancel")); if (op.terminal) await this.afterTerminal(op); else this.unresolved(op); return; }
            if (!this.presenting(op)) { this.unresolved(op); return; }
            if (result.phase === "queued") {
                this.patch({pending:{...this.retainedValue(op),stage:"preparing"}});
                if (!this.presenting(op)) { this.unresolved(op); return; }
                result = this.accept(op,await this.control(op,"prepare"));
            }
            if (op.terminal) { await this.afterTerminal(op); return; }
            if (op.cancelRequested) { this.accept(op,await this.control(op,"cancel")); if (op.terminal) await this.afterTerminal(op); else this.unresolved(op); return; }
            if (!this.presenting(op)) { this.unresolved(op); return; }
            if (result.phase === "ready") {
                this.patch({pending:{...this.retainedValue(op),stage:"committing"}});
                if (!this.presenting(op) || op.cancelRequested) { this.unresolved(op); return; }
                result = this.accept(op,await this.control(op,"commit"));
            }
            if (op.terminal) await this.afterTerminal(op); else this.unresolved(op);
        } catch(error) {
            if (!op.committed) { this.unresolved(op); if (this.presenting(op)) this.patch({error:category(error)}); }
        }
    }
    private async afterTerminal(op: Operation) {
        if (!op.committed || op.refreshed || !this.presenting(op)) return;
        op.refreshed = true;
        await this.refresh();
    }
    private start(op: Operation, admission: boolean) {
        // Install the promise and reservation before a subscriber can reenter.
        this.active = op; this.retained = op;
        op.promise = Promise.resolve().then(() => this.drive(op,admission)).finally(() => {
            if (this.active === op) { this.active = null; this.patch({pending:null}); }
        });
        this.patch({pending:{...this.retainedValue(op),stage:admission ? "submitting" : "recovering"},uncertain:op.unknown ? this.retainedValue(op) : null,error:null});
        return op.promise;
    }
    send(): Promise<void> {
        if (this.active) return this.active.promise;
        const c = this.state.context;
        if (this.retained && !this.retained.terminal) { this.patch({error:"Busy",notice:"Resolve the original exact turn before admitting another."}); return Promise.resolve(); }
        if (!c || !this.state.snapshot) { this.patch({error:"SessionRequired"}); return Promise.resolve(); }
        if (c.view !== "play" || c.pending || c.blocked || this.disposed) { this.patch({error:"Busy"}); return Promise.resolve(); }
        if ((c.playMode === "local" || c.action === "dialogue") && !this.state.draft.trim()) { this.patch({error:"DraftRequired"}); return Promise.resolve(); }
        const turn = `${this.prefix}-${++this.turn}`;
        const request: Request = c.playMode === "local" ? {version:1,scope:{...c.scope},turn,expected_revision:c.revision,intent:{kind:"free_text",value:{kind:c.inputKind,text:this.state.draft}}} : typedRequest({...c.scope},turn,c.revision,c.action,this.state.draft);
        const op: Operation = {session:c.session,player:c.player,request,mode:c.fakeMode,cancelRequested:false,key:this.key,retired:false,started:false,submitted:false,terminal:false,unknown:false,committed:null,terminalStatus:null,refreshed:false,promise:Promise.resolve()};
        return this.start(op,true);
    }
    retryExact(): Promise<void> {
        if (this.active) return this.active.promise;
        const op = this.retained, c = this.state.context;
        if (!op || !c || c.session !== op.session || !sameScope(c.scope,op.request.scope) || c.player !== op.player || c.view !== "play" || c.pending || c.blocked) { this.patch({error:"Scope"}); return Promise.resolve(); }
        if (op.terminal) return this.status();
        // Explicit user recovery binds the original request to a fresh view
        // epoch. Its request/body/mode/revision/key are never regenerated.
        op.key = this.key; op.retired = false;
        return this.start(op,false);
    }
    async status() {
        const op = this.retained, key = this.key;
        if (!op || this.disposed) return;
        try { const result = await this.control(op,"turn_status"); op.submitted = true; this.accept(op,result); if (op.terminal) await this.afterTerminal(op); else this.unresolved(op); }
        catch(error) { if (!op.committed) { this.unresolved(op); if (this.current(key)) this.patch({error:category(error)}); } }
    }
    async cancel() {
        const op = this.retained;
        if (!op || this.disposed || op.terminal) return;
        op.cancelRequested = true;
        this.patch({pending:this.state.pending ? {...this.state.pending,stage:"cancelling",cancelRequested:true} : null,
            uncertain:op.unknown ? this.retainedValue(op) : this.state.uncertain,
            notice:!op.submitted ? "Cancel intent retained locally. Admission acknowledgement is unresolved; no native cancellation is claimed. Read original status." : "Cancellation requested for the original native turn."});
        if (!op.submitted) return; // Lost acknowledgement is never claimed cancelled.
        try { this.accept(op,await this.control(op,"cancel")); if (op.terminal) await this.afterTerminal(op); else this.unresolved(op); }
        catch(error) { if (!op.committed) { this.unresolved(op); if (this.presenting(op)) this.patch({error:category(error)}); } }
    }
    dispose() { if (this.retained && !this.retained.terminal) { this.retained.retired = true; this.retained.unknown = true; } this.disposed = true; this.listeners.clear(); }
}
