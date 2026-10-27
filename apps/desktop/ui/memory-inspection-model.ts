// Read-only transport validation. Rust owns coverage, eligibility and source proof.
import { checkedPageV2 } from "./v2-view-model";
import type { EffectV2, InspectionPageV2, ScopeV2 } from "./v2-view-model";

export type MemoryInspectionContext = {
    session: string; scope: ScopeV2; expected_head: number; player: string;
    observer: string; view: "play" | "lab"; epoch: number; persistent: boolean;
    domainVersion: 1 | 2; lab: boolean;
};
export type MemorySourceRef = { scope: ScopeV2; sequence: number };
export type MemoryClosure = { kind: "open_tail" | "receipt_limit" | "event_limit" }
    | { kind: "event_budget" | "source_budget" | "packet_budget"; next_turn_end: number };
export type MemoryPacketDescriptor = {
    kind: "packet"; index: number; version: 2; method: "deterministic-event-extractive-v2";
    from_exclusive: number; through_revision: number; receipt_count: number;
    closure: MemoryClosure; entry_count: number; source_event_count: number;
};
export type MemoryAcceptedEvent = {
    version: 1; scope: ScopeV2; sequence: number; turn: string;
    rules: "fantasy_v1" | "narrative_v1"; seed: string; story_time: number;
    participants: string[]; witnesses: string[]; outcome: EffectV2;
};
export type MemoryEntryValue =
    | { class: "observed_time_span"; from: number; to: number; source_events: MemorySourceRef[] }
    | { class: "observation"; origin: "canonical_observation" | "statement" | "belief";
        source: MemorySourceRef; event: MemoryAcceptedEvent };
export type MemoryEntryRow = { kind: "entry"; packet_index: number; index: number; value: MemoryEntryValue };
export type MemoryFallback = "missing" | "budget" | "malformed" | "unsupported" | "binding" | "gap"
    | "overlap" | "open_tail_before_end" | "unprovable_closure" | "source_mismatch";
export type MemoryCoverage = {
    status: "verified" | "raw_fallback"; verified_head: number | null;
    covered_through: number | null; raw_delta_after: number; fallback: MemoryFallback | null;
};
type MemoryPageBase = {
    kind: "memory_inspection"; version: 1; session: string; scope: ScopeV2; head: number;
    observer: string; privacy: "player_visible"; binding: string; coverage: MemoryCoverage;
    total: number; next_cursor: string | null;
};
export type MemoryPacketPage = MemoryPageBase & { view: "packets"; packet_index: null; rows: MemoryPacketDescriptor[] };
export type MemoryEntryPage = MemoryPageBase & { view: "entries"; packet_index: number; rows: MemoryEntryRow[] };
export type MemorySourceReply = {
    kind: "memory_source"; version: 1; session: string; scope: ScopeV2; head: number;
    observer: string; privacy: "player_visible"; binding: string; packet_index: number;
    source: MemorySourceRef; matched: true; page: InspectionPageV2;
};
export type MemoryInspectionReply = MemoryPacketPage | MemoryEntryPage | MemorySourceReply;
export type MemoryInspectionRead =
    | { action: "packets"; binding: string | null; cursor: string | null; limit: number }
    | { action: "entries"; binding: string; cursor: string | null; limit: number; packet: MemoryPacketDescriptor }
    | { action: "source"; binding: string; packet: MemoryPacketDescriptor; source: MemorySourceRef };
export type MemoryInspectionState = {
    context: MemoryInspectionContext | null; allowed: boolean; busy: boolean;
    action: MemoryInspectionRead["action"] | null; packets: MemoryPacketPage | null;
    selected: MemoryPacketDescriptor | null; entries: MemoryEntryPage | null;
    source: MemorySourceReply | null; error: string | null; notice: string;
};
type Obj = Record<string, unknown>;
const encoder = new TextEncoder();
function wire(): never { throw Error("Wire"); }
function need(ok: unknown): asserts ok { if (!ok) wire(); }
function object(value: unknown): Obj {
    need(value !== null && typeof value === "object" && !Array.isArray(value));
    return value as Obj;
}
function exact(value: unknown, fields: string[]): Obj {
    const v = object(value);
    need(Object.keys(v).length === fields.length && fields.every(k => Object.hasOwn(v, k)));
    return v;
}
function integer(value: unknown, min = 0, max = Number.MAX_SAFE_INTEGER): number {
    need(typeof value === "number" && Number.isSafeInteger(value) && value >= min && value <= max);
    return value;
}
function text(value: unknown): string {
    need(typeof value === "string");
    for (let i = 0; i < value.length; i++) {
        const n = value.charCodeAt(i);
        if (n >= 0xd800 && n <= 0xdbff) {
            const next = value.charCodeAt(++i);
            need(next >= 0xdc00 && next <= 0xdfff);
        } else need(n < 0xdc00 || n > 0xdfff);
    }
    return value;
}
function id(value: unknown): string {
    const s = text(value); need(/^[A-Za-z0-9_-]{1,64}$/.test(s)); return s;
}
function hash(value: unknown): string {
    const s = text(value); need(/^[a-f0-9]{64}$/.test(s)); return s;
}
function scope(value: unknown): ScopeV2 {
    const s = exact(value, ["story", "branch"]); return { story: id(s.story), branch: id(s.branch) };
}
export const sameMemoryScope = (a: ScopeV2, b: ScopeV2) => a.story === b.story && a.branch === b.branch;
export const memorySourceIdentity = (s: MemorySourceRef) => JSON.stringify([s.scope.story, s.scope.branch, s.sequence]);
function nullable(value: unknown, validate: (v: unknown) => unknown) { if (value !== null) validate(value); }
function list(value: unknown, maximum: number, validate: (v: unknown) => unknown): unknown[] {
    need(Array.isArray(value) && value.length <= maximum); value.forEach(validate); return value;
}
function ids(value: unknown) {
    const values = list(value, 65536, id) as string[];
    need(new Set(values).size === values.length && values.every((v, i) => i === 0 || values[i - 1] < v));
}
// Copy JSON using descriptors, charging before growth; no accessor/toJSON call.
function detached(value: unknown, maximum: number): unknown {
    let bytes = 0;
    const active = new Set<object>();
    const charge = (n: number) => { bytes += n; need(bytes <= maximum); };
    const walk = (v: unknown, depth: number): unknown => {
        need(depth <= 24);
        if (typeof v === "string") { text(v); charge(encoder.encode(JSON.stringify(v)).length); return v; }
        if (typeof v === "number") { integer(v, -Number.MAX_SAFE_INTEGER); charge(String(v).length); return v; }
        if (v === null || typeof v === "boolean") { charge(v === false ? 5 : 4); return v; }
        need(typeof v === "object" && !active.has(v)); active.add(v);
        const array = Array.isArray(v), prototype = Object.getPrototypeOf(v);
        need(array ? prototype === Array.prototype : prototype === Object.prototype || prototype === null);
        const keys = Reflect.ownKeys(v); need(keys.every(k => typeof k === "string")); charge(2);
        let result: unknown;
        if (array) {
            need(keys.length === v.length + 1);
            const copy: unknown[] = [];
            for (let i = 0; i < v.length; i++) {
                const d = Object.getOwnPropertyDescriptor(v, String(i)); need(d && "value" in d && d.enumerable);
                if (i) charge(1); copy.push(walk(d.value, depth + 1));
            }
            result = copy;
        } else {
            const copy = Object.create(null) as Obj;
            for (const [i, key] of (keys as string[]).entries()) {
                const d = Object.getOwnPropertyDescriptor(v, key); need(d && "value" in d && d.enumerable);
                text(key); charge(encoder.encode(JSON.stringify(key)).length + 1 + (i ? 1 : 0));
                Object.defineProperty(copy, key, { value: walk(d.value, depth + 1), enumerable: true });
            }
            result = copy;
        }
        active.delete(v); return result;
    };
    return walk(value, 0);
}
function frozen<T>(value: T): T {
    if (value && typeof value === "object") {
        Object.values(value).forEach(frozen); Object.freeze(value);
    }
    return value;
}
export function checkedMemoryInspectionContext(value: unknown): MemoryInspectionContext {
    const c = exact(detached(value, 4096), ["session", "scope", "expected_head", "player", "observer", "view", "epoch", "persistent", "domainVersion", "lab"]);
    id(c.session); scope(c.scope); integer(c.expected_head); id(c.player); id(c.observer); integer(c.epoch);
    need((c.view === "play" || c.view === "lab") && (c.domainVersion === 1 || c.domainVersion === 2)
        && typeof c.persistent === "boolean" && typeof c.lab === "boolean");
    return frozen(c as unknown as MemoryInspectionContext);
}
export function memoryInspectionContextIdentity(c: MemoryInspectionContext | null): string {
    if (c === null) return "none";
    const v = checkedMemoryInspectionContext(c);
    return JSON.stringify([v.session,v.scope.story,v.scope.branch,v.expected_head,v.player,v.observer,v.view,v.epoch,v.persistent,v.domainVersion,v.lab]);
}
export const memoryInspectionAllowed = (c: MemoryInspectionContext | null) => !!c && c.persistent
    && c.domainVersion === 1 && c.lab && c.view === "lab" && c.observer === c.player;
function sourceRef(value: unknown, c: MemoryInspectionContext, packet: MemoryPacketDescriptor): MemorySourceRef {
    const s = exact(value, ["scope", "sequence"]), original = scope(s.scope);
    need(original.story === c.scope.story);
    integer(s.sequence, packet.from_exclusive + 1, packet.through_revision);
    return s as unknown as MemorySourceRef;
}
function descriptor(value: unknown, c: MemoryInspectionContext): MemoryPacketDescriptor {
    const p = exact(value, ["kind","index","version","method","from_exclusive","through_revision","receipt_count","closure","entry_count","source_event_count"]);
    need(p.kind === "packet" && p.version === 2 && p.method === "deterministic-event-extractive-v2");
    integer(p.index,0,31); const from = integer(p.from_exclusive,0,c.expected_head);
    const through = integer(p.through_revision,from + 1,c.expected_head);
    integer(p.receipt_count,1,128); integer(p.entry_count,0,256); integer(p.source_event_count,0,256);
    const closure = object(p.closure);
    if (typeof closure.kind === "string" && ["open_tail","receipt_limit","event_limit"].includes(closure.kind)) exact(closure,["kind"]);
    else {
        exact(closure,["kind","next_turn_end"]);
        need(typeof closure.kind === "string" && ["event_budget","source_budget","packet_budget"].includes(closure.kind));
        integer(closure.next_turn_end,through + 1,c.expected_head);
    }
    return p as unknown as MemoryPacketDescriptor;
}
function evidence(value: unknown, revision: number) {
    const e = exact(value,["kind","value"]);
    if (e.kind === "seed") id(e.value);
    else { need(e.kind === "event"); integer(e.value,1,revision); }
}
function effect(value: unknown, revision: number) {
    const e = object(value), shape = (fields: string[]) => exact(e,["effect",...fields]);
    switch(e.effect) {
        case "given": shape(["item","from","to","quantity"]); id(e.item);id(e.from);id(e.to);integer(e.quantity,1,65535); break;
        case "consumed": shape(["item","actor","healed"]);id(e.item);id(e.actor);nullable(e.healed,text);break;
        case "ability_used": shape(["actor","ability","cost"]);id(e.actor);text(e.ability);integer(e.cost,0,100);break;
        case "learned": shape(["actor","ability","rank"]);id(e.actor);text(e.ability);integer(e.rank,1,65535);break;
        case "moved": shape(["actor","from","to"]);id(e.actor);text(e.from);text(e.to);break;
        case "said": shape(["speaker","text","audience","source"]);id(e.speaker);text(e.text);need(encoder.encode(e.text as string).length<=2048);ids(e.audience);need(integer(e.source,1,revision)===revision);break;
        case "believed": shape(["believer","proposition","source_claim","source","confidence"]);id(e.believer);text(e.proposition);need(encoder.encode(e.proposition as string).length<=2048);nullable(e.source_claim,v=>integer(v,1,revision));evidence(e.source,revision);need(typeof e.confidence === "string" && ["uncertain","suspected","believed"].includes(e.confidence));break;
        case "discovered": shape(["actor","fact"]);id(e.actor);id(e.fact);break;
        case "promised": {
            shape(["id","commitment"]);id(e.id);
            const p=exact(e.commitment,["from","to","terms","deadline","source","return_item","completed_by"]);
            id(p.from);id(p.to);text(p.terms);need(encoder.encode(p.terms as string).length<=2048);
            integer(p.deadline);evidence(p.source,revision);nullable(p.return_item,id);nullable(p.completed_by,v=>integer(v,1,revision));break;
        }
        case "promise_completed": shape(["id","return_event"]);id(e.id);integer(e.return_event,1,revision);break;
        case "time_advanced": shape(["from","to"]);integer(e.from);integer(e.to,Number(e.from));break;
        default: wire();
    }
}
function entry(value: unknown, c: MemoryInspectionContext, packet: MemoryPacketDescriptor) {
    const r = exact(value,["kind","packet_index","index","value"]);
    need(r.kind === "entry" && r.packet_index === packet.index); integer(r.index,0,255);
    const v = object(r.value);
    if (v.class === "observed_time_span") {
        exact(v,["class","from","to","source_events"]);integer(v.from);integer(v.to,Number(v.from));
        const refs = list(v.source_events,256,s=>sourceRef(s,c,packet)) as MemorySourceRef[];
        need(refs.length>0 && refs.every((s,i)=>i===0 || refs[i-1].sequence<s.sequence));
    } else {
        exact(v,["class","origin","source","event"]);need(v.class === "observation");
        const ref = sourceRef(v.source,c,packet);
        const e = exact(v.event,["version","scope","sequence","turn","rules","seed","story_time","participants","witnesses","outcome"]);
        need(e.version === 1 && sameMemoryScope(scope(e.scope),ref.scope) && e.sequence===ref.sequence);
        id(e.turn);id(e.seed);integer(e.story_time);ids(e.participants);ids(e.witnesses);
        need(e.rules==="fantasy_v1" || e.rules==="narrative_v1");effect(e.outcome,ref.sequence);
        const outcome = object(e.outcome);
        need(v.origin === (outcome.effect === "said" ? "statement" : outcome.effect === "believed" ? "belief" : "canonical_observation"));
    }
}
function cursor(value: unknown, total: number): number {
    const v = text(value), match = /^mp1:([1-9][0-9]*):[a-f0-9]{64}$/.exec(v);
    need(v.length<=128 && match); return integer(Number(match[1]),1,total-1);
}
function coverage(value: unknown, head: number): MemoryCoverage {
    const c = exact(value,["status","verified_head","covered_through","raw_delta_after","fallback"]);
    if (c.status === "verified") {
        need(c.verified_head===head && c.fallback===null);
        integer(c.covered_through,0,head);need(c.raw_delta_after===c.covered_through);
    } else {
        need(c.status === "raw_fallback" && c.verified_head===null && c.covered_through===null && c.raw_delta_after===0);
        need(typeof c.fallback === "string" && ["missing","budget","malformed","unsupported","binding","gap","overlap","open_tail_before_end","unprovable_closure","source_mismatch"].includes(c.fallback));
    }
    return c as unknown as MemoryCoverage;
}
export function checkedMemoryInspection(value: unknown, context: MemoryInspectionContext, requested: MemoryInspectionRead): MemoryInspectionReply {
    const c = checkedMemoryInspectionContext(context);need(memoryInspectionAllowed(c));
    const r = object(detached(requested,4096));
    let packet: MemoryPacketDescriptor | null = null;
    if (r.action === "packets") exact(r,["action","binding","cursor","limit"]);
    else if (r.action === "entries") { exact(r,["action","binding","cursor","limit","packet"]);packet=descriptor(r.packet,c); }
    else { exact(r,["action","binding","packet","source"]);need(r.action==="source");packet=descriptor(r.packet,c);sourceRef(r.source,c,packet); }
    nullable(r.binding,hash);if(r.action!=="packets")hash(r.binding);
    if(r.action!=="source") { integer(r.limit,1,64);nullable(r.cursor,text);need(r.cursor===null || r.binding!==null); }
    const p = exact(detached(value,65536),r.action==="source"
        ? ["kind","version","session","scope","head","observer","privacy","binding","packet_index","source","matched","page"]
        : ["kind","version","session","scope","head","observer","privacy","binding","coverage","view","packet_index","total","rows","next_cursor"]);
    need(p.version===1 && p.session===c.session && sameMemoryScope(scope(p.scope),c.scope)
        && p.head===c.expected_head && p.observer===c.player && p.privacy==="player_visible");
    hash(p.binding);need(r.binding===null || p.binding===r.binding);
    if(r.action==="source") {
        need(p.kind==="memory_source" && p.packet_index===packet!.index && p.matched===true);
        const actual=sourceRef(p.source,c,packet!), expected=sourceRef(r.source,c,packet!);
        need(memorySourceIdentity(actual)===memorySourceIdentity(expected));
        const page=checkedPageV2(p.page,{version:2,scope:c.scope,expected_head:c.expected_head,
            at_revision:packet!.through_revision,observer:{kind:"player"},view:"history",cursor:null,
            limit:64,search:`"sequence":${expected.sequence},`},c.player);
        need(page.rows.some(row=>row.kind==="event" && row.event.sequence===expected.sequence && sameMemoryScope(row.event.scope,expected.scope)));
        return frozen({...p,page} as unknown as MemorySourceReply);
    }
    need(p.kind==="memory_inspection" && p.view===r.action);
    const cov=coverage(p.coverage,c.expected_head), total=integer(p.total,0,r.action==="packets"?32:256);
    need(Array.isArray(p.rows) && p.rows.length<=Number(r.limit) && p.rows.length<=total);
    const offset=r.cursor===null?0:cursor(r.cursor,total), rows=p.rows as unknown[];
    need(offset+rows.length<=total);
    if(p.next_cursor!==null)need(rows.length>0 && cursor(p.next_cursor,total)===offset+rows.length);
    else need(offset+rows.length===total);
    if(r.action==="packets") {
        need(p.packet_index===null);
        if(cov.status==="raw_fallback")need(total===0 && rows.length===0 && p.next_cursor===null);
        else {
            need(total>0);
            const descriptors=rows.map(v=>descriptor(v,c));
            descriptors.forEach((d,i)=>{
                need(d.index===offset+i && d.through_revision<=cov.covered_through!);
                if(i>0)need(d.from_exclusive===descriptors[i-1].through_revision);
                else if(offset===0)need(d.from_exclusive===0);
            });
        }
    } else {
        need(cov.status==="verified" && p.packet_index===packet!.index && total===packet!.entry_count
            && packet!.through_revision<=cov.covered_through!);
        const seen=new Set<string>();
        rows.forEach((v,i)=>{
            entry(v,c,packet!);const e=v as MemoryEntryRow;need(e.index===offset+i);
            const refs=e.value.class==="observation"?[e.value.source]:e.value.source_events;
            for(const ref of refs){const key=memorySourceIdentity(ref);need(!seen.has(key));seen.add(key);}
        });
        need(seen.size<=packet!.source_event_count);
        if(offset===0 && p.next_cursor===null)need(seen.size===packet!.source_event_count);
    }
    return frozen(p as unknown as MemoryPacketPage | MemoryEntryPage);
}
export function checkedMemorySourceRef(value: unknown, c: MemoryInspectionContext, packet: MemoryPacketDescriptor): MemorySourceRef {
    return frozen(sourceRef(detached(value,4096),c,packet));
}
export function memoryInspectionError(error: unknown): string {
    const value=error instanceof Error?error.message:String(error);
    return ["Version","Forbidden","Closed","Scope","Stale","Unsupported","InvalidInput","InvalidCursor",
        "Binding","TooLarge","Cancelled","Integrity","Unavailable","Busy","Database","Full","Internal","Wire"].includes(value)
        ? value : "Transport";
}
