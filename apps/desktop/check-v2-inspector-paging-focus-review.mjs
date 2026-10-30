// Independent FIRST: accepted focus contract 91acb40e. SOURCE AUTHOR UNRUN.
// Actual future helper/controller/panel source; DOM/rAF and panel hooks are doubles.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash, webcrypto } from "node:crypto";
import { build } from "esbuild";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import path from "node:path";

assert.equal(process.argv.length, 2, "ClosedPagingFocusReviewArguments");
globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL(".", import.meta.url));
const names = ["ui/v2-inspector-paging-focus.ts", "ui/v2-play-controller.ts", "ui/V2PlayPanel.tsx", "ui/v2-view-model.ts", "ui/model.ts"];
const sha = value => createHash("sha256").update(value).digest("hex");
const source = {}, setup = [], cases = [], results = [];
let actual;
const test = (group, name, run) => cases.push({ group, name, run });
const clone = value => structuredClone(value);
const flush = async () => { for (let i = 0; i < 80; i++) await Promise.resolve(); };
function deferred() { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; }

// A closed app-owned document double, not a DOM/browser implementation. Dispatch
// executes capture listeners even when the synthetic event stops bubbling.
function dom() {
    let sequence = 0;
    const events = new Map(), frames = new Map(), cancelled = [], callbacks = [], focusCalls = [];
    const view = {
        requestAnimationFrame(callback) { const id = ++sequence; frames.set(id, callback); callbacks.push(callback); return id; },
        cancelAnimationFrame(id) { cancelled.push(id); frames.delete(id); },
    };
    const body = { kind: "body" }, external = { kind: "external" }, child = { kind: "owned-child" };
    const document = {
        body, activeElement: null, defaultView: view,
        addEventListener(type, callback, options) { assert(["focusin", "pointerdown"].includes(type), "OnlyClosedIntentEvents"); const entries = events.get(type) ?? []; entries.push({ callback, options }); events.set(type, entries); },
        removeEventListener(type, callback, options) { const entries = events.get(type) ?? []; const index = entries.findIndex(entry => entry.callback === callback && capture(entry.options) === capture(options)); if (index >= 0) entries.splice(index, 1); },
    };
    function capture(options) { return options === true || options?.capture === true; }
    const button = {
        ownerDocument: document, isConnected: true, disabled: false,
        contains(target) { return target === button || target === child; },
        focus(options) { focusCalls.push(structuredClone(options)); document.activeElement = button; },
    };
    document.activeElement = button;
    return {
        document, button, body, child, external, view, events, frames, cancelled, callbacks, focusCalls,
        emit(type, target, stopped = true) { if (type === "focusin") document.activeElement = target; for (const entry of [...(events.get(type) ?? [])]) if (!stopped || capture(entry.options)) entry.callback({ type, target, stopPropagation() {} }); },
        frame() { const pending = [...frames]; frames.clear(); for (const [, callback] of pending) callback(1); },
        late() { for (const callback of [...callbacks]) callback(2); },
        count() { return [...events.values()].reduce((sum, entries) => sum + entries.length, 0); },
    };
}
function state() {
    const value = {
        context: { session: "focus-session", scope: { story: "focus-story", branch: "main" }, revision: 7, player: "player", view: "lab", observer: { kind: "omniscient" }, persistent: true, pending: false, blocked: false, playMode: "fixture", inputKind: "action", action: "wait", fakeMode: "accepted" },
        snapshot: { owner: "opaque-snapshot" },
        inspectionPaging: { bound: true, canPrevious: true, canNext: true, retainedPrevious: 1, earlierOmitted: false, navigating: null },
        readBusy: false, queryBusy: false, pending: null, uncertain: null,
        error: null, notice: "", source: null, sourceMatched: null,
    };
    // These are deliberately opaque in helper-only tests. Valid data authority
    // and body mutation behavior belong to the existing controller FIRST.
    for (const key of ["inspection", "history", "receipt", "status"]) Object.defineProperty(value, key, { enumerable: true, get() { throw Error(`ForbiddenFocusBodyTraversal:${key}`); } });
    return value;
}
function harness() {
    const d = dom(), listeners = new Set(), calls = [];
    let current = state(), notifications = 0;
    const controller = {
        get() { return current; },
        subscribe(callback) { listeners.add(callback); return () => listeners.delete(callback); },
    };
    // Deliberately fail any accidental read/write API beyond get/subscribe.
    for (const method of ["page", "previousInspectionPage", "refresh", "readQuery", "resetInspectionPaging", "send", "cancel", "source", "dispose"]) controller[method] = () => { calls.push(method); throw Error(`ForbiddenFocusControllerCall:${method}`); };
    const h = {
        ...d, controller, listeners, calls,
        current: () => current,
        publish(patch = {}, paging = {}) {
            const descriptors = Object.getOwnPropertyDescriptors(current);
            for (const [key, value] of Object.entries(patch)) descriptors[key] = { value, enumerable: true, writable: true, configurable: true };
            descriptors.inspectionPaging = { value: { ...current.inspectionPaging, ...paging }, enumerable: true, writable: true, configurable: true };
            current = Object.defineProperties({}, descriptors); notifications++;
            for (const listener of [...listeners]) listener();
        },
        duplicate() { notifications++; for (const listener of [...listeners]) listener(); },
        replaceWithoutNotification(patch) { const descriptors = Object.getOwnPropertyDescriptors(current); for (const [key, value] of Object.entries(patch)) descriptors[key] = { value, enumerable: true }; current = Object.defineProperties({}, descriptors); },
        arm(direction = "next", button = d.button, context = current.context, snapshot = current.snapshot) { return actual.beginInspectionPagingFocus(controller, button, context, snapshot, direction); },
        pending(direction = "next") { d.button.disabled = true; d.document.activeElement = d.body; h.publish({ queryBusy: true }, { navigating: direction, canPrevious: false, canNext: false }); },
        idle(error = null) { d.button.disabled = false; h.publish({ queryBusy: false, error }, { navigating: null, canPrevious: true, canNext: true }); },
        clean() { assert.equal(listeners.size, 0, "NoControllerListenerLeak"); assert.equal(d.count(), 0, "NoDocumentListenerLeak"); assert.equal(d.frames.size, 0, "NoQueuedFrameLeak"); assert.deepEqual(calls, [], "HelperOnlyReadsPublicState"); },
        count: () => notifications,
    };
    return h;
}
function complete(h, ticket, error = null) { h.pending(); h.idle(error); ticket.settled(); h.frame(); }
function noFocus(h, ticket) { ticket.settled(); h.frame(); h.late(); assert.equal(h.focusCalls.length, 0); ticket.cancel(); h.clean(); }

const inert = [
    ["null-button", h => ({ button: null })], ["undefined-button", h => ({ button: undefined })],
    ["unfocused", h => { h.document.activeElement = h.external; return {}; }],
    ["detached", h => { h.button.isConnected = false; return {}; }],
    ["disabled", h => { h.button.disabled = true; return {}; }],
    ["no-document", h => { h.button.ownerDocument = null; return {}; }],
    ["no-window", h => { h.document.defaultView = null; return {}; }],
    ["null-context", h => ({ context: null })], ["wrong-context-reference", h => ({ context: { ...h.current().context } })],
    ["null-snapshot", h => ({ snapshot: null })], ["wrong-snapshot-reference", h => ({ snapshot: {} })],
    ["unbound", h => { h.publish({}, { bound: false }); return {}; }],
    ["read-busy", h => { h.publish({ readBusy: true }); return {}; }],
    ["query-busy", h => { h.publish({ queryBusy: true }); return {}; }],
    ["already-navigating", h => { h.publish({}, { navigating: "next" }); return {}; }],
    ["pending-turn", h => { h.publish({ pending: {} }); return {}; }],
    ["uncertain-turn", h => { h.publish({ uncertain: {} }); return {}; }],
    ["context-pending", h => { h.current().context.pending = true; return {}; }],
    ["context-blocked", h => { h.current().context.blocked = true; return {}; }],
];
for (const [name, change] of inert) test("eligibility", name, () => {
    const h = harness(), options = change(h), s = h.current();
    const t = actual.beginInspectionPagingFocus(h.controller, Object.hasOwn(options, "button") ? options.button : h.button, Object.hasOwn(options, "context") ? options.context : s.context, Object.hasOwn(options, "snapshot") ? options.snapshot : s.snapshot, "next");
    assert.equal(typeof t.settled, "function"); assert.equal(typeof t.cancel, "function");
    h.pending(); h.idle(); t.settled(); t.settled(); t.cancel(); t.cancel(); h.frame(); assert.equal(h.focusCalls.length, 0); h.clean();
});
for (const direction of ["previous", "next"]) test("completion", `${direction}-automatic-body-blur`, () => {
    const h = harness(), t = h.arm(direction); h.pending(direction); h.idle(); t.settled();
    assert.equal(h.frames.size, 1); t.settled(); assert.equal(h.frames.size, 1); h.frame();
    assert.deepEqual(h.focusCalls, [{ preventScroll: true }]); t.settled(); t.cancel(); h.late(); assert.equal(h.focusCalls.length, 1); h.clean();
});
test("completion", "error-then-independent-enabled-retry", () => { const h = harness(); complete(h, h.arm(), "Transport"); assert.equal(h.focusCalls.length, 1); complete(h, h.arm()); assert.equal(h.focusCalls.length, 2); h.clean(); });
test("completion", "settled-without-navigation-is-noop", () => { const h = harness(), t = h.arm(); h.document.activeElement = h.body; noFocus(h, t); });
test("completion", "settled-while-pending-does-not-schedule", () => { const h = harness(), t = h.arm(); h.pending(); t.settled(); assert.equal(h.frames.size, 0); t.cancel(); h.clean(); });
test("completion", "already-focused-needs-no-focus-call", () => { const h = harness(), t = h.arm(); h.pending(); h.idle(); h.document.activeElement = h.button; t.settled(); h.frame(); assert.equal(h.focusCalls.length, 0); h.clean(); });
test("completion", "disabled-terminal-boundary-no-peer-focus", () => { const h = harness(), t = h.arm(); h.pending(); h.idle(); h.button.disabled = true; noFocus(h, t); });
test("intent", "capture-listeners-ignore-stopped-bubbling", () => { const h = harness(), t = h.arm(); for (const type of ["focusin", "pointerdown"]) { assert.equal((h.events.get(type) ?? []).length, 1); const option = h.events.get(type)[0].options; assert(option === true || option?.capture === true); } h.emit("pointerdown", h.external, true); h.pending(); h.idle(); noFocus(h, t); });
for (const type of ["focusin", "pointerdown"]) test("intent", `${type}-owned-descendant-keeps-ticket`, () => { const h = harness(), t = h.arm(); h.emit(type, h.child); complete(h, t); assert.equal(h.focusCalls.length, 1); h.clean(); });
for (const type of ["focusin", "pointerdown"]) for (const phase of ["pending", "queued"]) test("intent", `${type}-external-${phase}-wins`, () => { const h = harness(), t = h.arm(); h.pending(); if (phase === "queued") { h.idle(); t.settled(); } h.emit(type, h.external); if (phase === "pending") h.idle(); noFocus(h, t); });
test("intent", "body-automatic-focusin-keeps-ticket", () => { const h = harness(), t = h.arm(); h.pending(); h.emit("focusin", h.body); h.idle(); t.settled(); h.frame(); assert.equal(h.focusCalls.length, 1); h.clean(); });
test("intent", "body-pointer-intent-retires-ticket", () => { const h = harness(), t = h.arm(); h.pending(); h.emit("pointerdown", h.body); h.idle(); noFocus(h, t); });
test("intent", "unnotified-active-element-change-wins-at-frame", () => { const h = harness(), t = h.arm(); h.pending(); h.idle(); t.settled(); h.document.activeElement = h.external; h.frame(); assert.equal(h.focusCalls.length, 0); h.clean(); });
const retirement = [
    ["same-value-context-replacement", h => h.publish({ context: { ...h.current().context } })],
    ["same-head-snapshot-replacement", h => h.publish({ snapshot: {} })],
    ["session-switch", h => h.publish({ context: { ...h.current().context, session: "other" } })],
    ["head-switch", h => h.publish({ context: { ...h.current().context, revision: 8 } })],
    ["observer-lens-switch", h => h.publish({ context: { ...h.current().context, observer: { kind: "character", id: "mira" } } })],
    ["reset-or-form-change", h => h.publish({}, { bound: false, navigating: null })],
    ["fresh-read-or-source", h => h.publish({ queryBusy: true }, { navigating: null })],
    ["refresh", h => h.publish({ readBusy: true }, { bound: false })],
    ["pending-gameplay", h => h.publish({ pending: {} })],
    ["uncertain-gameplay", h => h.publish({ uncertain: {} })],
    ["blocked-context", h => { h.current().context.blocked = true; h.publish(); }],
    ["pending-context", h => { h.current().context.pending = true; h.publish(); }],
    ["opposite-navigation", h => h.publish({ queryBusy: true }, { navigating: "previous" })],
];
for (const [name, retire] of retirement) for (const phase of ["pending", "queued"]) test("retirement", `${name}-${phase}`, () => { const h = harness(), t = h.arm(); h.pending(); if (phase === "queued") { h.idle(); t.settled(); } retire(h); if (phase === "pending") h.idle(); noFocus(h, t); });
for (const phase of ["armed", "pending", "idle", "queued"]) test("cleanup", `cancel-${phase}-and-late-callback`, () => { const h = harness(), t = h.arm(); if (phase !== "armed") h.pending(); if (["idle", "queued"].includes(phase)) h.idle(); if (phase === "queued") t.settled(); t.cancel(); t.cancel(); t.settled(); h.frame(); h.late(); assert.equal(h.focusCalls.length, 0); h.clean(); });
for (const phase of ["settlement", "frame", "event"]) test("cleanup", `silent-dispose-${phase}-recheck`, () => { const h = harness(), t = h.arm(); h.pending(); h.idle(); if (phase !== "settlement") t.settled(); h.replaceWithoutNotification({ context: null }); if (phase === "event") h.emit("focusin", h.body); noFocus(h, t); });
test("cleanup", "disconnect-before-frame", () => { const h = harness(), t = h.arm(); h.pending(); h.idle(); t.settled(); h.button.isConnected = false; noFocus(h, t); });
test("cleanup", "new-navigation-after-first-idle-retires", () => { const h = harness(), t = h.arm(); h.pending(); h.idle(); h.pending(); h.idle(); noFocus(h, t); });
test("cleanup", "duplicate-public-state-identity-retires", () => { const h = harness(), t = h.arm(); h.pending(); h.duplicate(); h.idle(); noFocus(h, t); });
test("cleanup", "notification-65-retires-bounded-reservation", () => { const h = harness(), t = h.arm(); h.pending(); for (let i = 0; i < 64; i++) h.publish({ notice: `notification-${i}` }); h.idle(); noFocus(h, t); });
test("cleanup", "ordinary-get-rechecks-do-not-spend-notification-budget", () => { const h = harness(), t = h.arm(); for (let i = 0; i < 100; i++) h.controller.get(); h.pending(); h.idle(); t.settled(); h.frame(); assert.equal(h.focusCalls.length, 1); h.clean(); });

// Minimal valid Query2 transport fixtures used with the ACTUAL controller. These
// values do not claim native cursor/visibility/canonical authority.
const token = n => `2:${n}:${sha(`focus-opaque-${n}`)}`;
async function realFixture() {
    const context = state().context, calls = [], queued = [];
    const snapshot = { version: 2, domain_version: 2, scope: clone(context.scope), revision: 7, rules: "fantasy_v1", player: { observer: "player", self_state: { name: "Synthetic Rowan", location: "quay", alive: true, energy: 2, abilities: {}, attributes: {}, injuries: [], affiliations: [], goals: [] } }, inventory: {} };
    const gateway = { async call(command) {
        calls.push(clone(command));
        if (command.op === "play_snapshot_v2") return clone(snapshot);
        assert.equal(command.op, "inspection_query", "FocusJourneysOnlyNativeReads");
        const q = command.query, index = q.cursor === null ? 0 : q.cursor === token(1) ? 1 : 2;
        const gate = queued.shift(); if (gate) await gate.promise;
        const row = q.view === "history" ? { kind: "scoped_message", key: `focus-history-${index}`, original_scope: clone(q.scope), turn: `focus-turn-${index}`, message_kind: "narration", text: `Synthetic history ${index}`, event_ids: [1], origin: "recorded_message" } : { kind: "field", key: `focus-${index}`, actor: "player", field: "location", value: { type: "text", value: `page-${index}` }, source: { kind: "seed", value: "focus-seed" }, origin: "canonical_field" };
        return { version: 2, scope: clone(q.scope), head: 7, revision: q.at_revision ?? 7, story_time: 100, observer: clone(q.observer), view: q.view, privacy: "private_omniscient", status: "supported", total: 3, rows: [row], next_cursor: index < 2 ? token(index + 1) : null, unsupported: [] };
    } };
    const controller = new actual.V2PlayController(gateway, async () => {}, "focus-first");
    controller.selectedContextChanged(context); await controller.refresh(false); await controller.readQuery({ view: "profiles", atRevision: null, search: "" });
    assert(controller.get().inspectionPaging.bound, "RealControllerFixtureMustBeBound"); assert(controller.get().history, "RealControllerInitialHistoryMustDecode");
    return { controller, calls, queued, dom: dom(), initialQueries: calls.filter(call => call.op === "inspection_query").length };
}
for (const order of ["before-helper", "after-helper"]) test("actual-controller", `same-direction-reentrant-new-navigation-${order}`, async () => {
    const f = await realFixture(), c = f.controller, d = f.dom, oldGate = deferred(), newGate = deferred();
    f.queued.push(oldGate, newGate); let started = false, sawPending = false, newer;
    const reenter = () => { const s = c.get(); if (s.queryBusy && s.inspectionPaging.navigating === "next") sawPending = true; if (sawPending && !started && !s.queryBusy && s.inspectionPaging.navigating === null && s.inspectionPaging.canNext) { started = true; newer = c.page(s.inspection.page.next_cursor); } };
    let remove; if (order === "before-helper") remove = c.subscribe(reenter);
    const s = c.get(), t = actual.beginInspectionPagingFocus(c, d.button, s.context, s.snapshot, "next");
    if (order === "after-helper") remove = c.subscribe(reenter);
    const old = c.page(s.inspection.page.next_cursor); d.button.disabled = true; d.document.activeElement = d.body;
    oldGate.resolve(); await old; await flush(); assert(started, "ActualFinalIdleSubscriberMustReenter");
    t.settled(); newGate.resolve(); await newer; d.button.disabled = false; t.settled(); d.frame(); d.late();
    assert.equal(d.focusCalls.length, 0, "OldPromiseMustNotRestoreForSameDirectionNewRead");
    assert.equal(f.calls.filter(call => call.op === "inspection_query").length, f.initialQueries + 2); t.cancel(); remove(); c.dispose(); assert.equal(d.count(), 0); assert.equal(d.frames.size, 0);
});
test("actual-controller", "ordinary-navigation-restores-without-extra-query", async () => { const f = await realFixture(), c = f.controller, d = f.dom, s = c.get(), gate = deferred(); f.queued.push(gate); const t = actual.beginInspectionPagingFocus(c, d.button, s.context, s.snapshot, "next"); const pending = c.page(s.inspection.page.next_cursor); d.document.activeElement = d.body; d.button.disabled = true; gate.resolve(); await pending; d.button.disabled = false; t.settled(); d.frame(); assert.equal(d.focusCalls.length, 1); assert.equal(f.calls.filter(call => call.op === "inspection_query").length, f.initialQueries + 1); t.cancel(); c.dispose(); assert.equal(d.count(), 0); });
test("actual-controller", "dispose-without-notification-blocks-frame", async () => { const f = await realFixture(), c = f.controller, d = f.dom, s = c.get(), t = actual.beginInspectionPagingFocus(c, d.button, s.context, s.snapshot, "next"); await c.page(s.inspection.page.next_cursor); d.document.activeElement = d.body; t.settled(); c.dispose(); d.frame(); d.late(); assert.equal(d.focusCalls.length, 0); t.cancel(); assert.equal(d.count(), 0); });

// Only this panel import uses hook doubles. Captured JSX is the actual product
// function, not a replacement UI. No mounted React/browser/focus is claimed.
function panelHarness() {
    const h = harness(), s = h.current(), calls = [], gates = [];
    const page = { next_cursor: token(1), rows: [], scope: s.context.scope, head: 7, revision: 7, privacy: "private_omniscient", total: 3, status: "supported", unsupported: [] };
    const published = { ...Object.fromEntries(Object.entries(Object.getOwnPropertyDescriptors(s)).filter(([, d]) => Object.hasOwn(d, "value")).map(([k, d]) => [k, d.value])), inspection: { query: { view: "profiles", at_revision: null, search: "" }, page }, history: null, receipt: null, status: null, draft: "" };
    h.replaceWithoutNotification(published);
    const c = h.controller;
    c.refresh = async () => {};
    for (const [method, direction] of [["page", "next"], ["previousInspectionPage", "previous"]]) c[method] = async (...args) => { calls.push({ method, args, armed: h.listeners.size > 0 }); h.pending(direction); const gate = deferred(); gates.push(gate); await gate.promise; h.idle(); return null; };
    actual.hooks.reset();
    const render = () => { actual.hooks.begin(); actual.V2PlayPanel({ controller: c }); return actual.hooks.elements; };
    const elements = render(); actual.hooks.effects();
    const find = text => { const matches = elements.filter(e => e.type === "button" && e.props.children === text); assert.equal(matches.length, 1, `ActualPanelControl:${text}`); return matches[0]; };
    return { h, c, calls, gates, render, previous: find("Previous inspection page"), next: find("Next inspection page") };
}
for (const direction of ["previous", "next"]) test("actual-panel", `${direction}-arms-before-one-existing-dispatch`, async () => { const f = panelHarness(), e = f[direction]; assert.equal(e.props.disabled, false); e.props.onClick({ currentTarget: f.h.button }); assert.equal(f.calls.length, 1); assert(f.calls[0].armed, "HelperArmedBeforeDispatch"); assert.equal(f.calls[0].method, direction === "next" ? "page" : "previousInspectionPage"); assert.deepEqual(f.calls[0].args, direction === "next" ? [token(1)] : []); f.gates[0].resolve(); await flush(); f.h.frame(); assert.equal(f.h.focusCalls.length, 1); actual.hooks.cleanup(); f.h.clean(); });
test("actual-panel", "ssr-no-event-still-dispatches-eligible-action", async () => { const f = panelHarness(); f.next.props.onClick(); assert.equal(f.calls.length, 1); f.gates[0].resolve(); await flush(); actual.hooks.cleanup(); f.h.clean(); });
test("actual-panel", "unmount-cancels-pending-owned-ticket", async () => { const f = panelHarness(); f.next.props.onClick({ currentTarget: f.h.button }); assert.equal(f.calls.length, 1); actual.hooks.cleanup(); f.gates[0].resolve(); await flush(); f.h.frame(); f.h.late(); assert.equal(f.h.focusCalls.length, 0); f.h.clean(); });
test("actual-panel", "stale-rendered-owner-handler-does-not-dispatch", () => { const f = panelHarness(); f.h.publish({ context: { ...f.h.current().context, session: "other" } }); f.next.props.onClick({ currentTarget: f.h.button }); assert.equal(f.calls.length, 0); actual.hooks.cleanup(); f.h.clean(); });
test("actual-panel", "new-eligible-handler-cancels-prior-queued-ticket", async () => { const f = panelHarness(); f.next.props.onClick({ currentTarget: f.h.button }); f.gates[0].resolve(); await flush(); assert.equal(f.h.frames.size, 1); f.h.document.activeElement = f.h.button; f.next.props.onClick({ currentTarget: f.h.button }); assert.equal(f.calls.length, 2); assert.equal(f.h.frames.size, 0); assert(f.h.cancelled.length >= 1); assert.equal(f.h.listeners.size, 1); f.gates[1].resolve(); await flush(); f.h.frame(); assert.equal(f.h.focusCalls.length, 1); actual.hooks.cleanup(); f.h.clean(); });

const hookModule = `
export const hooks={slots:[],index:0,elements:[],pending:[],cleanups:[],reset(){this.slots=[];this.cleanups=[];this.pending=[];this.begin()},begin(){this.index=0;this.elements=[]},effects(){for(const effect of this.pending.splice(0)){const cleanup=effect();if(typeof cleanup==='function')this.cleanups.push(cleanup)}},cleanup(){for(const cleanup of this.cleanups.splice(0).reverse())cleanup()}};
export function useState(value){const i=hooks.index++;if(!(i in hooks.slots))hooks.slots[i]=typeof value==='function'?value():value;return[hooks.slots[i],value=>{hooks.slots[i]=typeof value==='function'?value(hooks.slots[i]):value}]}
export function useRef(value){const i=hooks.index++;return hooks.slots[i]??(hooks.slots[i]={current:value})}
export function useEffect(effect,deps){const i=hooks.index++,old=hooks.slots[i];if(!old||!deps||deps.some((v,n)=>v!==old[n])){hooks.slots[i]=deps;hooks.pending.push(effect)}}
export function useSyncExternalStore(subscribe,get){return get()}
export function __focusElement(type,props,...children){const e={type,props:{...props,children:children.length===1?children[0]:children}};hooks.elements.push(e);return e}
export const __focusFragment='fragment';
`;
try {
    for (const name of names) source[name] = await readFile(path.join(root, name), "utf8");
    const bundled = await build({ stdin: { contents: 'export {beginInspectionPagingFocus} from "./ui/v2-inspector-paging-focus";export {V2PlayController} from "./ui/v2-play-controller";export {V2PlayPanel} from "./ui/V2PlayPanel";export {hooks} from "focus-hooks";', resolveDir: root, loader: "tsx" }, bundle: true, platform: "node", format: "cjs", write: false, jsx: "transform", jsxFactory: "__focusElement", jsxFragment: "__focusFragment", tsconfigRaw: { compilerOptions: { jsx: "react", jsxFactory: "__focusElement", jsxFragmentFactory: "__focusFragment" } }, plugins: [{ name: "disclosed-actual-panel-hook-double", setup(plugin) {
        plugin.onResolve({ filter: /^(react|focus-hooks)$/ }, () => ({ path: "focus-hooks", namespace: "focus-double" }));
        plugin.onLoad({ filter: /.*/, namespace: "focus-double" }, () => ({ contents: hookModule, loader: "js" }));
        plugin.onLoad({ filter: /[\\/]V2PlayPanel\.tsx$/ }, async ({ path: filename }) => ({ contents: 'import {__focusElement,__focusFragment} from "focus-hooks";\n' + await readFile(filename, "utf8"), loader: "tsx", resolveDir: path.dirname(filename) }));
    } }] });
    const module = { exports: {} };
    vm.runInNewContext(bundled.outputFiles[0].text, { module, exports: module.exports, crypto: webcrypto, TextEncoder, TextDecoder, structuredClone, console }, { timeout: 1000, filename: "actual-focus-controller-panel.cjs" });
    actual = module.exports;
    if (typeof actual.beginInspectionPagingFocus !== "function" || typeof actual.V2PlayPanel !== "function" || typeof actual.V2PlayController !== "function") throw Error("MissingAcceptedFocusExport");
} catch (error) { setup.push({ classification: "UNRUN_SETUP", error: String(error).slice(0, 2048) }); }
if (!setup.length) for (const entry of cases) { try { await entry.run(); results.push({ group: entry.group, name: entry.name, passed: true }); } catch (error) { results.push({ group: entry.group, name: entry.name, passed: false, error: String(error).slice(0, 4096) }); } }
const hashes = Object.fromEntries(Object.entries(source).map(([name, text]) => [name, sha(text)]));
for (const [name, text] of Object.entries(source)) if (sha(await readFile(path.join(root, name), "utf8")) !== sha(text)) setup.push({ classification: "UNRUN_SETUP", error: `SourceChangedDuringReview:${name}` });
const groups = {};
for (const entry of cases) groups[entry.group] = (groups[entry.group] ?? 0) + 1;
const report = { kind: "d05_v2_inspector_pager_focus_independent_first_v1", source: hashes, authored: cases.length, groups, setup, executed: results.length, passed: results.filter(r => r.passed).length, failed: results.filter(r => !r.passed).length, results, evidence: { helper: "actual bundled production source with DOM/rAF/public-state doubles", controller: "actual V2PlayController with synthetic Query2 transport", panel: "actual V2PlayPanel JSX handlers/effect cleanup; hook and element doubles", nativeIpc: false, browser: false, pixels: false, keyboardOrScreenReader: false, desktopControl: false }, limitations: ["Source author executed no runtime; missing helper/export/bundle prerequisite is UNRUN_SETUP, never behavioral RED or zero-case PASS", "Doubles test logical focus calls and bounded listener/frame cleanup, not actual WebView disabled blur or layout", "Actual-controller disposal sends no notification; settlement/frame/document-event rechecks and panel unmount cleanup are tested, not invented immediate disposal events", "Opaque-body getter fixtures reject traversal but cannot prove absence of all unused private retention; independent source review remains required", "Enabled native pager focus assertion and every existing 92/245/38 check remain unchanged; actual native reproduction and all-image review require separate admission", "No elapsed-time, provider, Rust visibility/cursor authority, OS/process isolation or whole-D05 acceptance is inferred"] };
console.log(JSON.stringify(report));
process.exitCode = setup.length ? 2 : report.failed || !report.executed ? 1 : 0;
