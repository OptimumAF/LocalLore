// Presentation decoding only. Native Host/Store own permission and canonical truth.
import type { Scope } from "./model";
export interface AuthorInput {
    version: 1; parent: Scope; expected_parent_revision: number; fork_revision: number;
    child_branch: string;
    operation: { op: "replace_fact_proposition"; fact: string; expected_proposition: string; replacement: string };
    reason: string;
}
export interface AuthorDraft { fork_revision: number; child_branch: string; fact: string; expected_proposition: string; replacement: string; reason: string }
export interface AuthorContext {
    rootIncarnation: string; selectionEpoch: number; session: string; scope: Scope; head: number;
    player: string; observer: string; view: "play" | "lab"; persistent: boolean;
    spoilerGranted: boolean; pending: boolean; brokerUncertain: boolean;
}
type TruthSource = { kind: "seed_fact"; seed_id: string; fact: string } | { kind: "author"; source: { original_scope: Scope; sequence: number } };
export interface CoreAuthorPreview {
    version: 1; input: AuthorInput; child: Scope;
    before: { fact: string; proposition: string; source: TruthSource };
    creation_revision: number; retained_knowers: number; excluded_suffix_events: number;
    excluded_suffix_records: number; original_preserved: true; downstream_replayed: false;
    new_child_requires_fresh_derivatives: true;
}
export interface AuthorPreview {
    version: 1; kind: "author_preview"; session: string; preview_token: string;
    preview_sha256: string; preview_json: string; expires_seconds: 600;
    preview: CoreAuthorPreview;
}
export interface AuthorOutcome { version: 1; scope: Scope; parent: Scope; fork_revision: number; author_revision: number; head_revision: number; created: boolean }
export interface AuthorStatus {
    version: 1; operation_id: number; running: boolean;
    phase: "starting" | "author_preparing" | "author_applying" | "author_lookup" | "completed" | "error";
    error: string | null; result: unknown;
}
const encoder = new TextEncoder();
const number = (v: unknown): v is number => typeof v === "number" && Number.isSafeInteger(v) && v >= 0;
const id = (v: unknown, max = 64): v is string => typeof v === "string" && v.length <= max && /^[A-Za-z0-9_-]+$/.test(v);
const token = (v: unknown): v is string => typeof v === "string" && /^[a-fA-F0-9]{8}-(?:[a-fA-F0-9]{4}-){3}[a-fA-F0-9]{12}$/.test(v);
function wire(): never { throw Error("Wire"); }
function text(v: unknown, max = 2048): asserts v is string {
    if (typeof v !== "string" || encoder.encode(v).length > max) wire();
    for (let i = 0; i < v.length; i++) {
        const c = v.charCodeAt(i);
        if (c >= 0xd800 && c <= 0xdbff) { const next = v.charCodeAt(++i); if (!(next >= 0xdc00 && next <= 0xdfff)) wire(); }
        else if (c >= 0xdc00 && c <= 0xdfff) wire();
    }
}
function object(v: unknown, keys: readonly string[]): asserts v is Record<string, unknown> {
    if (!v || typeof v !== "object" || Array.isArray(v) || ![Object.prototype, null].includes(Object.getPrototypeOf(v))) wire();
    const names = Reflect.ownKeys(v);
    if (names.length !== keys.length || !keys.every(k => Object.hasOwn(v, k))) wire();
    for (const name of names) { const d = Object.getOwnPropertyDescriptor(v, name)!; if (!d.enumerable || !("value" in d)) wire(); }
}
function bounded(v: unknown, max = 262144) {
    const seen = new Set<object>(); let nodes = 0;
    function visit(value: unknown, depth: number) {
        if (++nodes > 16384 || depth > 12) wire();
        if (typeof value === "string") { text(value, max); return; }
        if (value === null || typeof value === "boolean" || (typeof value === "number" && Number.isFinite(value))) return;
        if (!value || typeof value !== "object" || Array.isArray(value) || seen.has(value)) wire();
        object(value, Object.keys(value)); seen.add(value);
        for (const k of Object.keys(value)) visit((value as Record<string, unknown>)[k], depth + 1);
        seen.delete(value);
    }
    visit(v, 0); if (encoder.encode(JSON.stringify(v)).length > max) throw Error("TooLarge");
}
function freeze<T>(v: T): T { if (v && typeof v === "object") { for (const item of Object.values(v)) freeze(item); Object.freeze(v); } return v; }
function copy<T>(v: T): T { return freeze(JSON.parse(JSON.stringify(v)) as T); }
function scope(v: unknown): Scope { object(v, ["story", "branch"]); if (!id(v.story) || !id(v.branch)) wire(); return { story: v.story, branch: v.branch }; }
const sameScope = (a: Scope, b: Scope) => a.story === b.story && a.branch === b.branch;
const equal = (a: unknown, b: unknown): boolean => {
    if (a === b) return true;
    if (!a || !b || typeof a !== "object" || typeof b !== "object") return false;
    const left = a as Record<string, unknown>, right = b as Record<string, unknown>;
    return Object.keys(left).length === Object.keys(right).length && Object.keys(left).every(k => Object.hasOwn(right, k) && equal(left[k], right[k]));
};
export function checkedAuthorInput(v: unknown): AuthorInput {
    bounded(v, 65536); object(v, ["version", "parent", "expected_parent_revision", "fork_revision", "child_branch", "operation", "reason"]);
    const parent = scope(v.parent); const op = v.operation;
    object(op, ["op", "fact", "expected_proposition", "replacement"]);
    text(op.expected_proposition); text(op.replacement); text(v.reason);
    if (v.version !== 1 || !number(v.expected_parent_revision) || !number(v.fork_revision) || v.fork_revision >= Number.MAX_SAFE_INTEGER || v.fork_revision > v.expected_parent_revision || !id(v.child_branch) || v.child_branch === parent.branch || op.op !== "replace_fact_proposition" || !id(op.fact) || op.replacement === "" || op.replacement === op.expected_proposition) wire();
    return copy<AuthorInput>({version: 1, parent, expected_parent_revision: v.expected_parent_revision, fork_revision: v.fork_revision, child_branch: v.child_branch, operation: { op: "replace_fact_proposition", fact: op.fact, expected_proposition: op.expected_proposition, replacement: op.replacement }, reason: v.reason});
}
export function checkedAuthorDraft(v: unknown): AuthorDraft {
    bounded(v, 16384); object(v, ["fork_revision", "child_branch", "fact", "expected_proposition", "replacement", "reason"]);
    if (!number(v.fork_revision)) wire();
    for (const key of ["child_branch", "fact", "expected_proposition", "replacement", "reason"]) text(v[key]);
    return copy(v as unknown as AuthorDraft);
}
export function checkedAuthorContext(v: unknown): AuthorContext {
    bounded(v, 4096); object(v, ["rootIncarnation", "selectionEpoch", "session", "scope", "head", "player", "observer", "view", "persistent", "spoilerGranted", "pending", "brokerUncertain"]);
    scope(v.scope);
    if (!id(v.rootIncarnation,128) || !id(v.session,128) || !number(v.selectionEpoch) || !number(v.head) || !id(v.player) || !id(v.observer) || !["play","lab"].includes(String(v.view)) || [v.persistent,v.spoilerGranted,v.pending,v.brokerUncertain].some(x=>typeof x!=="boolean")) wire();
    return copy(v as unknown as AuthorContext);
}
export function authorAvailable(c: AuthorContext | null): boolean { return !!c && c.persistent && c.view === "lab" && c.spoilerGranted && c.observer === "omniscient" && !c.pending && !c.brokerUncertain; }
export function authorRequest(c: AuthorContext, d: AuthorDraft): AuthorInput { return checkedAuthorInput({ version: 1, parent: c.scope, expected_parent_revision: c.head, fork_revision: d.fork_revision, child_branch: d.child_branch, operation: { op: "replace_fact_proposition", fact: d.fact, expected_proposition: d.expected_proposition, replacement: d.replacement }, reason: d.reason }); }

// Only the bounded private Core preview shape: no arrays, execution or canonical import.
function uniquePreview(raw: string): unknown {
    text(raw,65536); let i=0;
    const space=()=>{while(/[\x20\t\r\n]/.test(raw[i]??"!")&&i<raw.length)i++;};
    function string(): string {
        if(raw[i++]!== '"')wire();const start=i-1;
        while(i<raw.length){const c=raw[i++];if(c==='"'){const value:unknown=JSON.parse(raw.slice(start,i));text(value,65536);return value;}if(c==='\\'){i++;}}
        return wire();
    }
    function value(depth:number):void {
        if(depth>12)wire();space();
        if(raw[i]==='{'){i++;space();const keys=new Set<string>();if(raw[i]==='}'){i++;return;}for(;;){space();const key=string();if(keys.has(key))wire();keys.add(key);space();if(raw[i++]!==':')wire();value(depth+1);space();const end=raw[i++];if(end==='}')return;if(end!==',')wire();}}
        if(raw[i]==='"'){string();return;}
        const literal=/^(?:true|false|null|0|[1-9][0-9]*)/.exec(raw.slice(i));if(!literal)wire();i+=literal[0].length;
    }
    try {value(0);space();if(i!==raw.length)wire();return JSON.parse(raw);} catch {return wire();}
}
export async function checkedAuthorPreview(v: unknown, input: AuthorInput, session: string): Promise<AuthorPreview> {
    bounded(v); object(v,["version","kind","session","preview_token","preview_sha256","preview_json","expires_seconds"]);
    if(v.version!==1||v.kind!=="author_preview"||v.session!==session||!token(v.preview_token)||typeof v.preview_sha256!=="string"||! /^[a-f0-9]{64}$/.test(v.preview_sha256)||v.expires_seconds!==600)wire();
    text(v.preview_json,65536);
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",encoder.encode(v.preview_json)))).map(x=>x.toString(16).padStart(2,"0")).join("");if(digest!==v.preview_sha256)wire();
    const p=uniquePreview(v.preview_json);object(p,["version","input","child","before","creation_revision","retained_knowers","excluded_suffix_events","excluded_suffix_records","original_preserved","downstream_replayed","new_child_requires_fresh_derivatives"]);
    const actual=checkedAuthorInput(p.input),child=scope(p.child);object(p.before,["fact","proposition","source"]);text(p.before.proposition);
    const source=p.before.source;if(!source||typeof source!=="object")wire();
    const tag=Object.getOwnPropertyDescriptor(source,"kind");if(!tag||!("value"in tag))wire();
    if(tag.value==="seed_fact"){object(source,["kind","seed_id","fact"]);if(!id(source.seed_id)||source.fact!==input.operation.fact)wire();}
    else if(tag.value==="author"){object(source,["kind","source"]);object(source.source,["original_scope","sequence"]);const original=scope(source.source.original_scope);if(original.story!==input.parent.story||!number(source.source.sequence)||source.source.sequence<1||source.source.sequence>input.fork_revision)wire();}
    else wire();
    if(p.version!==1||!equal(actual,input)||!sameScope(child,{story:input.parent.story,branch:input.child_branch})||p.before.fact!==input.operation.fact||p.before.proposition!==input.operation.expected_proposition||p.creation_revision!==input.fork_revision+1||!number(p.retained_knowers)||p.excluded_suffix_events!==input.expected_parent_revision-input.fork_revision||!number(p.excluded_suffix_records)||p.excluded_suffix_records>4096||p.original_preserved!==true||p.downstream_replayed!==false||p.new_child_requires_fresh_derivatives!==true)wire();
    return copy({...v,preview:p}) as unknown as AuthorPreview;
}
export function checkedAuthorOutcome(v: unknown,input:AuthorInput):AuthorOutcome {
    bounded(v,4096);object(v,["version","scope","parent","fork_revision","author_revision","head_revision","created"]);
    if(v.version!==1||!sameScope(scope(v.scope),{story:input.parent.story,branch:input.child_branch})||!sameScope(scope(v.parent),input.parent)||v.fork_revision!==input.fork_revision||v.author_revision!==input.fork_revision+1||!number(v.head_revision)||v.head_revision<input.fork_revision+1||typeof v.created!=="boolean")wire();
    return copy(v as unknown as AuthorOutcome);
}
const errors=new Set(["Closed","Scope","Stale","Busy","Unsupported","Cancelled","NotFound","TooLarge","Integrity","Database","Full","Internal","InvalidAuthorInput","AuthorConsentRequired","AuthorPreviewMismatch","UnknownAuthorPreview","AuthorPreviewLimit","ArchiveBusy","ArchiveInternal","ArchiveBudget","InvalidArchiveInput","UnknownArchiveOperation","StorageUnavailable","Transport","Wire","Rule","Version","Malformed","RetryMismatch","Io","Knowledge","ReadPreviewRequired","Unavailable"]);
export function authorError(e:unknown):string {try{const value=e instanceof Error?e.message:e;return typeof value==="string"&&errors.has(value)?value:"Wire";}catch{return "Wire";}}
export function checkedAuthorStatus(v:unknown):AuthorStatus {
    bounded(v);object(v,["version","operation_id","running","phase","error","result"]);
    if(v.version!==1||!number(v.operation_id)||v.operation_id<1||typeof v.running!=="boolean"||!["starting","author_preparing","author_applying","author_lookup","completed","error"].includes(String(v.phase)))wire();
    if(v.running){if(v.error!==null||v.result!==null||["completed","error"].includes(String(v.phase)))wire();}
    else if(v.phase==="completed"){if(v.error!==null||v.result===null)wire();}
    else if(v.phase==="error"){if(typeof v.error!=="string"||!errors.has(v.error)||v.result!==null)wire();}
    else wire();return copy(v as unknown as AuthorStatus);
}
export function checkedAuthorCompletion(v:unknown,kind:"commit"|"lookup",input:AuthorInput,session:string):AuthorOutcome|null {
    bounded(v,8192);object(v,kind==="commit"?["version","kind","session","outcome"]:["version","kind","found","outcome"]);
    if(v.version!==1||v.kind!==`author_${kind}`||(kind==="commit"&&v.session!==session))wire();
    if(kind==="lookup"){if(typeof v.found!=="boolean")wire();if(!v.found){if(v.outcome!==null)wire();return null;}}
    const result=checkedAuthorOutcome(v.outcome,input);if(kind==="lookup"&&result.created)wire();return result;
}
export function authorRaw(value:unknown):string {bounded(value,65536);return JSON.stringify(value);}
