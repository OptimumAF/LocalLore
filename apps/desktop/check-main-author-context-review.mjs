// Frozen actual-Main subscription/admission oracles. Synthetic transport, no DOM/native execution.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { readFile } from "node:fs/promises";
import { createHash, webcrypto } from "node:crypto";
import { fileURLToPath } from "node:url";

const desktop = fileURLToPath(new URL("./", import.meta.url));
const source = await readFile(new URL("./ui/main.tsx", import.meta.url), "utf8");
const mainSha256 = createHash("sha256").update(source).digest("hex");
const compiled = await build({
    stdin: {
        contents: `${source}\nexport { controller, v2, author, brokerRetention, dispose };`,
        resolveDir: fileURLToPath(new URL("./ui/", import.meta.url)),
        sourcefile: "main-context-review.tsx",
        loader: "tsx",
    },
    absWorkingDir: desktop,
    bundle: true, platform: "node", format: "esm", write: false,
    jsx: "automatic", define: { __DEV_HARNESS__: "false" },
    plugins: [{
        name: "render-only-stubs",
        setup(plugin) {
            plugin.onResolve({ filter: /^(\.\/App|react-dom\/client|react\/jsx-runtime)$/ },
                ({ path }) => ({ path, namespace: "review-render" }));
            plugin.onLoad({ filter: /.*/, namespace: "review-render" }, ({ path }) => ({
                contents: path === "./App" ? "export function App() { return null; }"
                    : path === "react-dom/client" ? "export function createRoot(){return {render(){},unmount(){}}}"
                    : "export const jsx=()=>null; export const jsxs=jsx; export const Fragment=Symbol('fragment');",
                loader: "js",
            }));
        },
    }],
});
const code = compiled.outputFiles[0].text;
const clone = (value) => structuredClone(value);
const scope = { story: "quay", branch: "child" };
const session = "session-1";
const revision = 3;
const writes = new Set(["prepare", "submit", "free_text", "commit"]);
const metadata = { version: 1, root_incarnation: "synthetic-root", window_epoch: 1, story_lab_granted: true };
const thin = (domain) => ({
    version: 2, domain_version: domain, scope: clone(scope), revision, rules: "fantasy_v1",
    player: { observer: "player", self_state: {
        name: "Rowan", location: "quay", alive: true, energy: 2,
        abilities: { steady: 1 }, attributes: { resolve: 3 }, injuries: [], affiliations: [], goals: [],
    } }, inventory: {},
});
const legacy = () => ({ scope: clone(scope), revision, rules: "fantasy_v1", inventory: {}, receipts: [],
    player: { scope: clone(scope), revision, observer: "player", self_state: {
        name: "Rowan", energy: 2, location: "quay",
    }, observations: [], facts: {}, beliefs: [] } });
const page = (q) => ({
    version: 2, scope: clone(q.scope), head: q.expected_head,
    revision: q.at_revision ?? q.expected_head, story_time: 100,
    observer: clone(q.observer), view: q.view,
    privacy: q.observer.kind === "player" ? "player_visible" : q.observer.kind === "character" ? "private_character" : "private_omniscient",
    status: ["summaries", "retrieval_indexes"].includes(q.view) ? "unsupported" : "supported",
    total: 0, rows: [], next_cursor: null, unsupported: [],
});
const operation = (extra = {}) => ({
    version: 1, operation_id: 11, running: true, phase: "capturing", error: null, result: null, ...extra,
});
const archiveIdentity = () => ({ surface: "archive", action: "archive_export_preview", session,
    story: scope.story, branch: scope.branch, head: revision });
const memoryIdentity = (action) => ({ ...archiveIdentity(), surface: "memory", action });
function deferred() {
    let resolve, reject;
    const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
    return { promise, resolve, reject };
}
async function tick() { for (let n = 0; n < 24; n++) await Promise.resolve(); }
let incarnation = 0;
async function fixture({ domain = 2, nativeContext = metadata, authorReply } = {}) {
    const calls = [], holds = [];
    const saved = new Map();
    globalThis.crypto ??= webcrypto;
    globalThis.localStorage = { getItem: (key) => saved.get(key) ?? null,
        setItem: (key, value) => saved.set(key, String(value)), removeItem: (key) => saved.delete(key) };
    globalThis.document = { getElementById: () => ({}) };
    globalThis.window = { addEventListener() {}, removeEventListener() {}, __TAURI__: { core: {
        invoke: async (command, args = {}) => {
            if (calls.length >= 256) throw Error("ReviewCallLimit");
            calls.push({ command, args: clone(args) });
            if (command === "author_context") return clone(nativeContext);
            if (command === "author_prepare_start") {
                if (!authorReply) throw Error("ReviewUnexpectedAuthorStart");
                return await authorReply(JSON.parse(args.request));
            }
            if (command === "author_preview_discard") return true;
            if (command === "archive_cancel") return operation({ running: false, phase: "error", error: "Cancelled" });
            if (command !== "host_call") throw Error(`ReviewUnexpectedNative:${command}`);
            assert.equal(typeof args.input, "string");
            assert.ok(args.input.length <= 262144);
            const envelope = JSON.parse(args.input);
            assert.equal(envelope.version, 1);
            const c = envelope.command;
            let data;
            switch (c.op) {
                case "workspace": data = { persistent: true, location: "synthetic", schema_version: 1,
                    database_schema_version: 5, stories: [{ scope: clone(scope), title: "Synthetic", revision, drafts: 0 }] }; break;
                case "resume": data = { session, scope: clone(c.scope), revision, drafts: 0 }; break;
                case "open": data = { revision }; break;
                case "play_snapshot_v2": data = thin(domain); break;
                case "play_snapshot": data = legacy(); break;
                case "inspection_query": data = page(c.query); break;
                case "inspect": data = { synthetic: true }; break;
                case "close": data = null; break;
                case "turn_status": case "cancel": data = { turn: c.turn, scope: clone(c.scope),
                    expected_revision: revision, phase: c.op === "cancel" ? "cancelled" : "queued", error: null, receipt: null }; break;
                default:
                    if (writes.has(c.op)) return { version: 1, status: "error", error: "Busy" };
                    throw Error(`ReviewUnexpectedHost:${c.op}`);
            }
            return { version: 1, status: "ok", data };
        },
    } } };
    const m = await import(`data:text/javascript;base64,${Buffer.from(`${code}\n// incarnation:${++incarnation}`).toString("base64")}`);
    await tick();
    assert.equal(m.controller.selected()?.id, session, "actual startup must resume selected synthetic session");
    assert.equal(m.controller.get().visibleError, null, "startup fixture must be accepted by actual controller");
    assert.ok(domain === 2 ? m.controller.get().playV2 : m.controller.get().play);
    const hostCalls = () => calls.filter((c) => c.command === "host_call").map((c) => JSON.parse(c.args.input).command);
    return { ...m, calls, hostCalls,
        async holdKnown() {
            const d = deferred();
            const work = m.brokerRetention.start(archiveIdentity(), () => d.promise);
            holds.push(() => { d.resolve(operation()); return work; });
            assert.equal(m.brokerRetention.get().inFlight, true);
            assert.equal(m.brokerRetention.get().unknown, false);
        },
        async unknown() {
            await m.brokerRetention.start(archiveIdentity(), () => Promise.reject(Error("Transport"))).catch(() => {});
            assert.equal(m.brokerRetention.get().unknown, true);
        },
        async heldAcknowledgedRecovery() {
            await m.brokerRetention.start(memoryIdentity("admit"), () => Promise.reject(Error("Transport"))).catch(() => {});
            assert.equal(m.brokerRetention.acknowledgeUnresolved(true), true);
            const d = deferred();
            const work = m.brokerRetention.recoverMemory(memoryIdentity("status"), () => d.promise).catch(() => {});
            holds.push(() => { d.reject(Error("Transport")); return work; });
            assert.equal(m.brokerRetention.get().acknowledgedUnresolved, true);
            assert.equal(m.brokerRetention.get().inFlight, true);
        },
        async close() {
            for (const release of holds) await release();
            await m.dispose();
        },
    };
}
const tests = [];
const test = (name, run) => tests.push({ name, run });
async function using(options, run) {
    const f = await fixture(options);
    try { await run(f); } finally { await f.close(); }
}
async function labToPlay(f) {
    f.controller.setView("lab"); f.controller.setView("play");
    await f.v2.refresh(false); await tick();
}
const draft = { fork_revision: revision, child_branch: "new-child", fact: "relic-location",
    expected_proposition: "A", replacement: "B", reason: "SYNTHETIC_REASON" };
test("native true grant enables actual coherent Story Lab author context", () => using({}, async (f) => {
    f.controller.setView("lab"); await tick();
    assert.equal(f.author.get().available, true);
    assert.equal(f.controller.selected().scope.branch, "child");
}));
for (const [label, nativeContext] of [["denied", { ...metadata, story_lab_granted: false }],
    ["malformed", { ...metadata, window_epoch: 0 }]]) {
    test(`native ${label} context cannot enable author dispatch`, () => using({ nativeContext }, async (f) => {
        f.controller.setView("lab"); await tick();
        assert.equal(f.author.get().available, false);
        f.author.setDraft(draft); f.author.setAuthorConsent(true); await f.author.prepare();
        assert.equal(f.calls.filter((c) => c.command === "author_prepare_start").length, 0);
    }));
}
test("known running shared work survives Lab→Play synchronous author notifications", () => using({}, async (f) => {
    await f.holdKnown(); await labToPlay(f);
    assert.equal(f.v2.get().context.blocked, true);
    const before = f.hostCalls().filter((c) => writes.has(c.op)).length;
    await f.v2.send();
    assert.equal(f.hostCalls().filter((c) => writes.has(c.op)).length, before);
}));
test("explicit unresolved acknowledgement releases idle Play after context notifications", () => using({}, async (f) => {
    await f.unknown(); assert.equal(f.brokerRetention.acknowledgeUnresolved(true), true);
    await labToPlay(f);
    assert.equal(f.v2.get().context.blocked, false);
}));
test("inFlight passive recovery blocks even with previous explicit acknowledgement", () => using({}, async (f) => {
    await f.heldAcknowledgedRecovery(); await labToPlay(f);
    assert.equal(f.v2.get().context.blocked, true);
}));
test("malformed terminal remains sticky unknown across author and lens changes", () => using({}, async (f) => {
    await f.brokerRetention.start(archiveIdentity(), async () => operation({ running: false, phase: "completed", result: {} }));
    assert.equal(f.brokerRetention.get().unknown, true);
    f.controller.setView("lab"); f.author.setDraft(draft); f.author.setAuthorConsent(true);
    await labToPlay(f);
    assert.equal(f.brokerRetention.get().unknown, true);
    assert.equal(f.brokerRetention.get().consumed, false);
    assert.equal(f.v2.get().context.blocked, true);
}));
const request = () => ({ version: 1, scope: clone(scope), turn: "synthetic-turn", expected_revision: revision,
    intent: { kind: "actions", value: [{ op: "wait", ticks: 1 }] } });
function command(op) {
    if (op === "submit") return { op, session, mode: "accepted", request: request() };
    if (op === "free_text") return { op, session, request: { ...request(), intent: { kind: "free_text", value: { kind: "action", text: "Wait." } } } };
    return { op, session, scope: clone(scope), turn: "synthetic-turn" };
}
for (const state of ["known", "unknown", "acknowledged-inFlight", "author-busy"]) {
    test(`Domain1 actual Gateway blocks all four gameplay writes during ${state}`, async () => {
        const reply = deferred();
        await using({ domain: 1, authorReply: () => reply.promise }, async (f) => {
            let preparing;
            try {
                if (state === "known") await f.holdKnown();
                else if (state === "unknown") await f.unknown();
                else if (state === "acknowledged-inFlight") await f.heldAcknowledgedRecovery();
                else {
                    f.controller.setView("lab"); f.author.setDraft(draft); f.author.setAuthorConsent(true);
                    preparing = f.author.prepare(); await tick();
                    assert.equal(f.author.get().busy, true);
                }
                const before = f.hostCalls().filter((c) => writes.has(c.op)).length;
                for (const op of writes) await assert.rejects(f.controller.gateway.call(command(op)));
                assert.equal(f.hostCalls().filter((c) => writes.has(c.op)).length, before,
                    "guard must reject BEFORE native transport, not merely receive native Busy");
            } finally {
                reply.reject(Error("Transport"));
                if (preparing) await preparing;
            }
        });
    });
}
test("acknowledged unknown allows explicit next Domain1 dispatch without claiming cancellation", () => using({ domain: 1 }, async (f) => {
    await f.unknown(); assert.equal(f.brokerRetention.acknowledgeUnresolved(true), true);
    const before = f.hostCalls().filter((c) => writes.has(c.op)).length;
    // Synthetic native returns Busy: the oracle is transport admission, not a fabricated accepted turn.
    await assert.rejects(f.controller.gateway.call(command("submit")), /Busy/);
    assert.equal(f.hostCalls().filter((c) => writes.has(c.op)).length, before + 1);
    assert.equal(f.brokerRetention.get().unknown, true);
}));
test("known shared work permits readonly, exact status/cancel and session context switching", () => using({ domain: 1 }, async (f) => {
    await f.holdKnown();
    await f.controller.gateway.call({ op: "open", session, scope: clone(scope) });
    await f.controller.gateway.call(command("turn_status"));
    await f.controller.gateway.call(command("cancel"));
    await f.controller.gateway.call({ op: "close", session, scope: clone(scope) });
    f.controller.setView("lab"); f.controller.setView("play");
    assert.equal(f.controller.get().view, "play");
    assert.equal(f.brokerRetention.get().inFlight, true);
    for (const op of ["open", "turn_status", "cancel", "close"])
        assert.ok(f.hostCalls().some((c) => c.op === op));
}));
test("own author admission stays live and terminal consumption waits for actual controller", async () => {
    const reply = deferred();
    await using({ authorReply: () => reply.promise }, async (f) => {
        f.controller.setView("lab"); f.author.setDraft(draft); f.author.setAuthorConsent(true);
        const observations = [];
        const release = f.brokerRetention.subscribe(() => observations.push({
            busy: f.author.get().busy, consumed: f.brokerRetention.get()?.consumed,
            inFlight: f.brokerRetention.get()?.inFlight,
        }));
        const preparing = f.author.prepare();
        try {
            await tick();
            assert.equal(f.author.get().busy, true);
            assert.equal(f.author.get().uncertain, false);
            assert.equal(f.brokerRetention.get().consumed, false);
            const start = f.calls.find((c) => c.command === "author_prepare_start");
            assert.ok(start, "actual Main author dispatch must occur");
            const input = JSON.parse(start.args.request).input;
            const raw = JSON.stringify({ version: 1, input, child: { story: scope.story, branch: input.child_branch },
                before: { fact: input.operation.fact, proposition: input.operation.expected_proposition,
                    source: { kind: "seed_fact", seed_id: "lantern-quay-v1", fact: input.operation.fact } },
                creation_revision: revision + 1, retained_knowers: 2, excluded_suffix_events: 0,
                excluded_suffix_records: 0, original_preserved: true, downstream_replayed: false,
                new_child_requires_fresh_derivatives: true });
            reply.resolve(operation({ running: false, phase: "completed", result: {
                version: 1, kind: "author_preview", session,
                preview_token: "12345678-1234-1234-1234-123456789abc",
                preview_sha256: createHash("sha256").update(raw).digest("hex"), preview_json: raw, expires_seconds: 600,
            } }));
            await preparing; await tick();
            assert.equal(f.author.get().status, "preview");
            assert.equal(f.author.get().uncertain, false);
            assert.ok(f.author.get().preview);
            assert.equal(f.brokerRetention.get().unknown, false);
            assert.equal(f.brokerRetention.get().consumed, true);
            assert.ok(observations.every((o) => !o.consumed || (!o.busy && !o.inFlight)), "no premature own result consumption");
            assert.equal(f.calls.filter((c) => ["archive_cancel", "author_preview_discard"].includes(c.command)).length, 0);
        } finally {
            reply.reject(Error("Transport")); await preparing; release();
        }
    });
});
let passed = 0;
const results = [];
for (const { name, run } of tests) {
    try { await run(); passed++; results.push({ name, status: "PASS" }); }
    catch (error) { results.push({ name, status: "FAIL", error: String(error).slice(0, 1200) }); }
}
console.log(JSON.stringify({ kind: "synthetic-actual-Main-subscriptions", mainSha256,
    passed, failed: tests.length - passed, results }, null, 2));
if (passed !== tests.length) process.exitCode = 1;
