// Frozen source-only oracles. Actual V2 controller and actual panel React SSR/
// captured JSX handlers, synthetic transport. No Core, native IPC, DOM, WebView,
// model, device, clipboard, desktop input or canonical-receipt authority proof.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID, webcrypto } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL(".", import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const cohort = randomUUID();
const sourceNames = [
    "ui/v2-play-controller.ts",
    "ui/V2PlayPanel.tsx",
    "ui/v2-view-model.ts",
    "ui/model.ts",
];
const sourceHashes = Object.fromEntries(
    await Promise.all(
        sourceNames.map(async (name) => [
            name,
            createHash("sha256")
                .update(await readFile(path.join(root, name)))
                .digest("hex"),
        ]),
    ),
);
// Capture props of actual JSX elements during real React SSR, following the
// accepted archive-selection review pattern. Do not substitute panel decisions.
const compiled = await build({
    stdin: {
        contents:
            'export {V2PlayController} from "./ui/v2-play-controller"; export {V2PlayPanel} from "./ui/V2PlayPanel"; export {createElement} from "react"; export {renderToStaticMarkup} from "react-dom/server"; export {created} from "recorded-turn-review-elements";',
        resolveDir: root,
        loader: "tsx",
    },
    bundle: true,
    platform: "node",
    format: "cjs",
    write: false,
    jsx: "transform",
    jsxFactory: "__receiptElement",
    jsxFragment: "__receiptFragment",
    tsconfigRaw: {
        compilerOptions: {
            jsx: "react",
            jsxFactory: "__receiptElement",
            jsxFragmentFactory: "__receiptFragment",
        },
    },
    plugins: [
        {
            name: "capture-actual-receipt-panel-elements",
            setup(plugin) {
                // V2PlayPanel is client-only: its real hook has no third argument.
                // Supply only that SSR prerequisite; all real React state/effect/
                // store hook behavior, panel decisions and JSX handlers stay real.
                plugin.onResolve({ filter: /^react$/ }, (args) =>
                    /[\\/]V2PlayPanel\.tsx$/.test(args.importer)
                        ? {
                              path: "client-store-server-snapshot",
                              namespace: "recorded-turn-react-adapter",
                          }
                        : undefined,
                );
                plugin.onLoad(
                    { filter: /.*/, namespace: "recorded-turn-react-adapter" },
                    () => ({
                        contents:
                            'import {useSyncExternalStore as realUseSyncExternalStore} from "react"; export * from "react"; export function useSyncExternalStore(subscribe,get,serverSnapshot=get){return realUseSyncExternalStore(subscribe,get,serverSnapshot);}',
                        loader: "js",
                        resolveDir: root,
                    }),
                );
                plugin.onResolve(
                    { filter: /^recorded-turn-review-elements$/ },
                    () => ({ path: "elements", namespace: "recorded-turn-review" }),
                );
                plugin.onLoad(
                    { filter: /.*/, namespace: "recorded-turn-review" },
                    () => ({
                        contents:
                            'import {createElement,Fragment} from "react"; export const created=[]; export const __receiptFragment=Fragment; export function __receiptElement(type,props,...children){const element=createElement(type,props,...children);created.push(element);return element;}',
                        loader: "js",
                        resolveDir: root,
                    }),
                );
                plugin.onLoad(
                    { filter: /[\\/]V2PlayPanel\.tsx$/ },
                    async ({ path: filename }) => ({
                        contents:
                            'import {__receiptElement,__receiptFragment} from "recorded-turn-review-elements";\n' +
                            (await readFile(filename, "utf8")),
                        loader: "tsx",
                        resolveDir: path.dirname(filename),
                    }),
                );
            },
        },
    ],
});
const bundle = path.join(output, `v2-recorded-turn-${cohort}.cjs`);
await writeFile(bundle, compiled.outputFiles[0].contents, { flag: "wx" });
const {
    V2PlayController,
    V2PlayPanel,
    createElement,
    renderToStaticMarkup,
    created,
} = (await import(pathToFileURL(bundle).href)).default;
const clone = (value) => structuredClone(value);
const story = "recorded-turn-synthetic";
const selected = { story, branch: "corrected" };
const ancestor = { story, branch: "main" };
const label = "Inspect recorded turn changes";
const context = () => ({
    session: "cold-reopened-session", scope: clone(selected), revision: 7,
    player: "player", view: "play", observer: { kind: "player" },
    persistent: true, pending: false, blocked: false, playMode: "fixture",
    inputKind: "action", action: "wait", fakeMode: "accepted",
});
const snapshot = (c) => ({
    version: 2, domain_version: 2, scope: clone(c.scope), revision: c.revision,
    rules: "fantasy_v1",
    player: { observer: c.player, self_state: {
        name: "Rowan", location: "quay", alive: true, energy: 2,
        abilities: {}, attributes: {}, injuries: [], affiliations: [], goals: [],
    } },
    inventory: {},
});
const narration = (patch = {}) => ({
    kind: "scoped_message", key: "recorded-narration",
    original_scope: clone(selected), turn: "actual-recorded-turn",
    message_kind: "narration", text: "You pause by the quay.",
    event_ids: [7], origin: "recorded_message", ...patch,
});
const page = (q, rows) => ({
    version: 2, scope: clone(q.scope), head: q.expected_head,
    revision: q.at_revision ?? q.expected_head, story_time: 107,
    observer: clone(q.observer), view: q.view,
    privacy: q.observer.kind === "player" ? "player_visible" :
        q.observer.kind === "character" ? "private_character" : "private_omniscient",
    status: "supported", total: rows.length, rows: clone(rows),
    next_cursor: null, unsupported: [],
});
function deferred() {
    let resolve;
    const promise = new Promise((done) => { resolve = done; });
    return { promise, resolve };
}
async function settle() { for (let n = 0; n < 30; n++) await Promise.resolve(); }
function text(node) {
    if (node == null || typeof node === "boolean") return "";
    if (Array.isArray(node)) return node.map(text).join("");
    if (typeof node === "object") return text(node.props?.children);
    return String(node);
}
const buttons = (rendered) => rendered.elements.filter(
    (element) => element.type === "button" && text(element.props.children) === label,
);
function actualButton(rendered) {
    const found = buttons(rendered);
    if (found.length !== 1) {
        const error = Error(`Expected exactly one actual panel button: ${label}`);
        error.evidence = "new-ui-absent";
        throw error;
    }
    return found[0].props;
}
async function fixture({ rows = [narration()], patch = {} } = {}) {
    let current = { ...context(), ...clone(patch) };
    const f = { calls: [], rows, gate: null };
    const gateway = { call: async (command) => {
        f.calls.push(clone(command));
        if (command.op === "play_snapshot_v2") return snapshot(current);
        if (command.op === "inspection_query") {
            const q = command.query;
            const reply = page(q, q.view === "history" ? f.rows : []);
            if (q.view === "turn_diff" && f.gate) {
                const gate = f.gate;
                f.gate = null;
                await gate.promise;
            }
            return reply;
        }
        throw Error(`UnexpectedSyntheticOperation:${command.op}`);
    } };
    f.controller = new V2PlayController(gateway, async () => {}, "recorded-turn-review");
    f.select = (change) => {
        current = { ...current, ...clone(change) };
        f.controller.selectedContextChanged(current);
    };
    f.bound = () => f.controller.get().history;
    f.row = () => f.bound().page.rows[0];
    f.render = () => {
        created.length = 0;
        try {
            const html = renderToStaticMarkup(createElement(V2PlayPanel, { controller: f.controller }));
            return { html, elements: [...created] };
        } catch (error) { error.evidence = "fixture-calibration-failure"; throw error; }
    };
    try {
        f.controller.selectedContextChanged(current);
        await f.controller.refresh(false);
        assert(f.controller.get().snapshot, "actual existing snapshot decoder must calibrate");
        assert(f.bound(), "actual existing History decoder must calibrate");
        assert.equal(f.bound().page.rows.length, rows.length);
        assert.equal(f.controller.get().receipt, null, "reopened fixture has no process-local receipt");
        assert.equal(f.controller.get().error, null);
    } catch (error) { error.evidence = "fixture-calibration-failure"; throw error; }
    f.calls.length = 0;
    return f;
}
function trace(f, row = f.row(), bound = f.bound()) {
    if (typeof f.controller.traceRecordedTurn !== "function") {
        const error = Error("Missing new traceRecordedTurn API; not behavioral RED");
        error.evidence = "new-api-absent";
        throw error;
    }
    return f.controller.traceRecordedTurn(row, bound);
}
const queries = (f) => f.calls.filter((command) => command.op === "inspection_query");
const noWrites = (f) => assert(f.calls.every(
    (command) => command.op === "inspection_query" || command.op === "play_snapshot_v2",
), "navigation cannot submit/commit/generate/grant/turn_status/change sessions");
function expectedQuery(f, end) {
    const calls = queries(f);
    assert.equal(calls.length, 1);
    const c = f.controller.get().context;
    assert.deepEqual(calls[0], { op: "inspection_query", session: c.session, query: {
        version: 2, scope: c.scope, expected_head: c.revision, at_revision: end,
        observer: { kind: "player" }, view: "turn_diff", cursor: null, limit: 64, search: "",
    } });
    noWrites(f);
}
async function refused(f, row, bound) {
    const result = await trace(f, row, bound);
    assert.equal(result, null);
    assert.equal(f.calls.length, 0, "ineligible recorded navigation must refuse before dispatch");
    noWrites(f);
}
const cases = [];
const test = (name, kind, run) => cases.push({ name, kind, run });

test("existing actual decoder and client panel calibrate cold-reopened narration without receipt", "calibration", async () => {
    const f = await fixture();
    assert.equal(f.row().message_kind, "narration");
    const rendered = f.render();
    assert(rendered.html.includes("You pause by the quay."));
    assert(rendered.html.includes("actual-recorded-turn"));
    assert.equal(f.calls.length, 0);
    f.controller.dispose();
});
test("existing History decoder accepts ascending gapped IDs but new action must independently require contiguous receipt IDs", "calibration", async () => {
    const f = await fixture({ rows: [narration({ event_ids: [5, 7] })] });
    assert.deepEqual(f.row().event_ids, [5, 7]);
    assert.equal(f.calls.length, 0);
    f.controller.dispose();
});
test("current actual narration opens historical diff with no retained raw receipt", "new-api", async () => {
    const f = await fixture();
    const result = await trace(f);
    assert(result && result === f.controller.get().inspection);
    assert.equal(f.controller.get().receipt, null);
    expectedQuery(f, 7);
    f.controller.dispose();
});
test("inherited original narration keeps selected child and uses old completed end with current head", "new-api", async () => {
    const f = await fixture({ rows: [narration({ original_scope: ancestor, event_ids: [1, 2] })], patch: { revision: 9 } });
    const original = clone(f.row().original_scope);
    const result = await trace(f);
    assert(result);
    expectedQuery(f, 2);
    assert.deepEqual(original, ancestor);
    assert.deepEqual(f.controller.get().context.scope, selected);
    f.controller.dispose();
});
test("multi-event narration uses actual last recorded ID rather than inferred base plus one", "new-api", async () => {
    const f = await fixture({ rows: [narration({ event_ids: [5, 6, 7] })] });
    assert(await trace(f));
    expectedQuery(f, 7);
    f.controller.dispose();
});
test("actual current Inspection History page narration is also eligible", "new-api", async () => {
    const f = await fixture();
    const bound = await f.controller.readQuery({ view: "history", atRevision: 7, search: "" });
    assert(bound && bound === f.controller.get().inspection);
    f.calls.length = 0;
    assert(await trace(f, bound.page.rows[0], bound));
    expectedQuery(f, 7);
    f.controller.dispose();
});
test("cloned row and cloned bound cannot manufacture displayed membership", "new-api", async () => {
    const f = await fixture();
    await refused(f, clone(f.row()), f.bound());
    await refused(f, f.row(), clone(f.bound()));
    f.controller.dispose();
});
test("replaced actual bound refuses old row even if all transport values are identical", "new-api", async () => {
    const f = await fixture(), old = f.bound(), row = f.row();
    await f.controller.refresh(false);
    assert.notEqual(f.bound(), old);
    f.calls.length = 0;
    await refused(f, row, old);
    f.controller.dispose();
});
test("original-input rows never authorize completed-turn navigation", "new-api", async () => {
    const f = await fixture({ rows: [narration({ message_kind: "original_input" })] });
    await refused(f, f.row(), f.bound());
    f.controller.dispose();
});
test("mutated actual row cannot substitute another story", "new-api", async () => {
    const f = await fixture();
    f.row().original_scope = { story: "another-story", branch: "main" };
    await refused(f, f.row(), f.bound());
    f.controller.dispose();
});
test("Player Play eligibility never follows a Character alias or Lab lens", "new-api", async () => {
    for (const patch of [
        { observer: { kind: "character", id: "player" } },
        { view: "lab", observer: { kind: "player" } },
        { view: "lab", observer: { kind: "omniscient" } },
    ]) {
        const f = await fixture({ patch });
        await refused(f, f.row(), f.bound());
        f.controller.dispose();
    }
});
test("missing or incoherent snapshot cannot supply authority for a current row", "new-api", async () => {
    for (const mutation of ["missing", "head", "player", "scope"]) {
        const f = await fixture();
        const state = f.controller.get();
        if (mutation === "missing") state.snapshot = null;
        if (mutation === "head") state.snapshot.revision = 6;
        if (mutation === "player") state.snapshot.player.observer = "mira";
        if (mutation === "scope") state.snapshot.scope = { story, branch: "other" };
        await refused(f, f.row(), f.bound());
        f.controller.dispose();
    }
});
test("actual decoded row mutations with empty zero fractional unsafe future duplicate or gapped IDs refuse before dispatch", "new-api", async () => {
    for (const ids of [[], [0], [1.5], [Number.MAX_SAFE_INTEGER + 1], [8], [6, 6], [5, 7]]) {
        const f = await fixture();
        f.row().event_ids = ids;
        await refused(f, f.row(), f.bound());
        f.controller.dispose();
    }
});
test("actual current bound must retain History view Player privacy and coherent selected head", "new-api", async () => {
    for (const mutation of ["view", "privacy", "head", "inspected-end"]) {
        const f = await fixture(), bound = f.bound();
        if (mutation === "view") { bound.query.view = "profiles"; bound.page.view = "profiles"; }
        if (mutation === "privacy") bound.page.privacy = "private_character";
        if (mutation === "head") bound.page.head = 6;
        if (mutation === "inspected-end") bound.page.revision = 6;
        await refused(f, f.row(), bound);
        f.controller.dispose();
    }
});
test("pending notification retirement prevents dispatch of old recorded-turn read", "new-api", async () => {
    const f = await fixture();
    let acted = false;
    f.controller.subscribe(() => {
        if (!acted && f.controller.get().queryBusy) { acted = true; f.select({ revision: 8 }); }
    });
    assert.equal(await trace(f), null);
    assert(acted);
    assert.equal(f.calls.length, 0);
    f.controller.dispose();
});
test("result notification retirement cannot return a retired bound page", "new-api", async () => {
    const f = await fixture();
    let acted = false;
    f.controller.subscribe(() => {
        if (!acted && f.controller.get().inspection) { acted = true; f.select({ revision: 8 }); }
    });
    assert.equal(await trace(f), null);
    assert(acted);
    assert.equal(f.controller.get().inspection, null);
    noWrites(f);
    f.controller.dispose();
});
test("final busy notification retirement cannot return the otherwise completed bound page", "new-api", async () => {
    const f = await fixture();
    let acted = false;
    f.controller.subscribe(() => {
        const state = f.controller.get();
        if (!acted && state.inspection && !state.queryBusy) { acted = true; f.select({ revision: 8 }); }
    });
    assert.equal(await trace(f), null);
    assert(acted);
    assert.equal(f.controller.get().inspection, null);
    noWrites(f);
    f.controller.dispose();
});
test("held reply across head session lens or dispose retirement never publishes or returns old evidence", "new-api", async () => {
    for (const mutation of ["head", "session", "lens", "dispose"]) {
        const f = await fixture(), gate = deferred();
        f.gate = gate;
        const pending = trace(f);
        await settle();
        assert.equal(queries(f).length, 1, "read must really be held after dispatch");
        if (mutation === "head") f.select({ revision: 8 });
        if (mutation === "session") f.select({ session: "other-session" });
        if (mutation === "lens") f.select({ view: "lab", observer: { kind: "character", id: "mira" } });
        if (mutation === "dispose") f.controller.dispose();
        gate.resolve();
        assert.equal(await pending, null);
        assert.equal(f.controller.get().inspection, null);
        noWrites(f);
        f.controller.dispose();
    }
});
test("disposed current row cannot dispatch", "new-api", async () => {
    const f = await fixture(), row = f.row(), bound = f.bound();
    f.controller.dispose();
    await refused(f, row, bound);
});
test("newer same-context query supersedes a held recorded-turn read without replacing its result", "new-api", async () => {
    const f = await fixture(), gate = deferred();
    f.gate = gate;
    const pending = trace(f);
    await settle();
    assert.equal(queries(f).length, 1);
    const newer = await f.controller.readQuery({ view: "profiles", atRevision: null, search: "" });
    assert(newer && newer === f.controller.get().inspection);
    gate.resolve();
    assert.equal(await pending, null);
    assert.equal(f.controller.get().inspection, newer);
    noWrites(f);
    f.controller.dispose();
});
test("actual panel recorded-turn button invokes actual action without receipt write or grant", "new-ui", async () => {
    const f = await fixture();
    const actual = actualButton(f.render());
    assert(!actual.disabled);
    await actual.onClick();
    await settle();
    assert(f.controller.get().inspection);
    assert.equal(f.controller.get().receipt, null);
    expectedQuery(f, 7);
    f.controller.dispose();
});
test("actual old panel callback cannot navigate a replacement context", "new-ui", async () => {
    const f = await fixture(), actual = actualButton(f.render());
    f.select({ revision: 8 });
    await actual.onClick();
    await settle();
    assert.equal(f.calls.length, 0);
    assert.equal(f.controller.get().inspection, null);
    f.controller.dispose();
});
test("actual panel never enables recorded-turn action for input rows Character identity or Lab", "new-ui", async () => {
    for (const options of [
        { rows: [narration({ message_kind: "original_input" })] },
        { patch: { observer: { kind: "character", id: "player" } } },
        { patch: { view: "lab", observer: { kind: "player" } } },
    ]) {
        const f = await fixture(options);
        assert(buttons(f.render()).every((element) => element.props.disabled), "ineligible action must be absent or disabled");
        assert.equal(f.calls.length, 0);
        f.controller.dispose();
    }
});
test("actual held panel action cannot restore evidence after replacement session", "new-ui", async () => {
    const f = await fixture(), actual = actualButton(f.render()), gate = deferred();
    f.gate = gate;
    const pending = actual.onClick();
    await settle();
    assert.equal(queries(f).length, 1);
    f.select({ session: "replacement-session" });
    gate.resolve();
    await pending;
    await settle();
    assert.equal(f.controller.get().inspection, null);
    noWrites(f);
    f.controller.dispose();
});
test("actual existing narration markup keeps hostile synthetic text inert", "calibration", async () => {
    const hostile = '<script>recorded_only()</script> <img src="remote.invalid" onerror="never()">';
    const f = await fixture({ rows: [narration({ text: hostile })] });
    const rendered = f.render();
    assert(rendered.html.includes("&lt;script&gt;"));
    assert(!rendered.html.includes("<script>recorded_only()"));
    assert(!rendered.html.includes('<img src="remote.invalid"'));
    assert.equal(f.calls.length, 0);
    f.controller.dispose();
});

const results = [];
for (const { name, kind, run } of cases) {
    try { await run(); results.push({ name, kind, passed: true }); }
    catch (error) { results.push({
        name, kind, passed: false,
        classification: error.evidence ?? (kind === "calibration" ? "fixture-calibration-failure" : "new-interface-assertion-failure"),
        error: String(error?.message ?? error).slice(0, 600),
    }); }
}
const report = {
    version: 1, synthetic: true,
    execution: "actual V2PlayController and actual client-only V2PlayPanel with narrow server-snapshot adapter, real React SSR/captured JSX handlers; synthetic Gateway only",
    nativeIpc: false, rustCoreExecution: false, modelExecution: false,
    rendering: "React SSR; no browser pixels or mounted client local-state proof",
    reactAdapter: { scope: "V2PlayPanel react import only", realReactHook: true, otherHooksReplaced: false },
    desktopInput: false, sourceHashes, checks: results,
    passed: results.filter((result) => result.passed).length,
    failed: results.filter((result) => !result.passed).length,
    missingInterface: results.filter((result) => /absent$/.test(result.classification ?? "")).length,
    limitations: [
        "New API/UI absence and setup errors are not behavioral RED; synthetic transports do not prove Core outcomes/privacy",
        "No actual cold process restart/Main subscription/IPC/Store/native WebView/clipboard/accessibility or model execution",
        "Mutation cases deliberately alter already decoded JS fixtures; no assertion that native Core produced malformed DTOs",
        "SSR handler capture does not qualify mounted React post-await local control updates",
    ],
};
await writeFile(path.join(output, `v2-recorded-turn-${cohort}.json`), JSON.stringify(report, null, 2), { flag: "wx" });
console.log(JSON.stringify(report));
if (report.failed) process.exitCode = 1;
