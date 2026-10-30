// D05.03/.07 independent FIRST, accepted f3add8f8 + mutation precision eca52680.
// SOURCE ONLY / AUTHOR UNRUN. Actual controller and real panel SSR/handlers;
// synthetic Gateway pages are transport fixtures, never Rust/privacy evidence.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID, webcrypto } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
globalThis.crypto ??= webcrypto;
assert.equal(process.argv.length, 2, "ClosedV2InspectorPagingReviewArguments");
const root = fileURLToPath(new URL(".", import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
const cohort = randomUUID(),
    hash = (value) => createHash("sha256").update(value).digest("hex");
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
            hash(await readFile(path.join(root, name))),
        ]),
    ),
);
const setup = [],
    cases = [],
    results = [],
    observations = [];
let actual;
try {
    const bundled = await build({
        stdin: {
            contents:
                'export {V2PlayController} from "./ui/v2-play-controller"; export {V2PlayPanel} from "./ui/V2PlayPanel"; export {createElement} from "react"; export {renderToStaticMarkup} from "react-dom/server"; export {created} from "paging-review-elements";',
            resolveDir: root,
            loader: "tsx",
        },
        bundle: true,
        platform: "node",
        format: "cjs",
        write: false,
        jsx: "transform",
        jsxFactory: "__pagingElement",
        jsxFragment: "__pagingFragment",
        tsconfigRaw: {
            compilerOptions: {
                jsx: "react",
                jsxFactory: "__pagingElement",
                jsxFragmentFactory: "__pagingFragment",
            },
        },
        plugins: [
            {
                name: "actual-v2-panel-elements-and-only-server-snapshot-prerequisite",
                setup(plugin) {
                    plugin.onResolve({ filter: /^react$/ }, (args) =>
                        /[\\/]V2PlayPanel\.tsx$/.test(args.importer)
                            ? {
                                  path: "real-react-server-snapshot",
                                  namespace: "paging-react-adapter",
                              }
                            : undefined,
                    );
                    plugin.onLoad(
                        { filter: /.*/, namespace: "paging-react-adapter" },
                        () => ({
                            contents:
                                'import {useSyncExternalStore as realUseSyncExternalStore} from "react"; export * from "react"; export function useSyncExternalStore(subscribe,get,serverSnapshot=get){return realUseSyncExternalStore(subscribe,get,serverSnapshot);}',
                            loader: "js",
                            resolveDir: root,
                        }),
                    );
                    plugin.onResolve(
                        { filter: /^paging-review-elements$/ },
                        () => ({
                            path: "elements",
                            namespace: "paging-elements",
                        }),
                    );
                    plugin.onLoad(
                        { filter: /.*/, namespace: "paging-elements" },
                        () => ({
                            contents:
                                'import {createElement,Fragment} from "react"; export const created=[]; export const __pagingFragment=Fragment; export function __pagingElement(type,props,...children){const element=createElement(type,props,...children);created.push(element);return element;}',
                            loader: "js",
                            resolveDir: root,
                        }),
                    );
                    plugin.onLoad(
                        { filter: /[\\/]V2PlayPanel\.tsx$/ },
                        async ({ path: filename }) => ({
                            contents:
                                'import {__pagingElement,__pagingFragment} from "paging-review-elements";\n' +
                                (await readFile(filename, "utf8")),
                            loader: "tsx",
                            resolveDir: path.dirname(filename),
                        }),
                    );
                },
            },
        ],
    });
    await mkdir(output, { recursive: true });
    const file = path.join(output, `v2-inspector-paging-${cohort}.cjs`);
    await writeFile(file, bundled.outputFiles[0].contents, { flag: "wx" });
    actual = (await import(pathToFileURL(file).href)).default;
    if (
        typeof actual.V2PlayController.prototype.previousInspectionPage !==
            "function" ||
        typeof actual.V2PlayController.prototype.resetInspectionPaging !==
            "function"
    )
        setup.push({
            stage: "new-controller-interface",
            classification: "SETUP/UNRUN, not behavioral RED",
            error: "Missing accepted Previous/reset API",
        });
    else {
        const probe = new actual.V2PlayController(
            {
                call: async () => {
                    throw Error("InterfaceProbeMustNotDispatch");
                },
            },
            async () => {},
            "paging-interface",
        );
        if (!probe.get().inspectionPaging)
            setup.push({
                stage: "new-controller-state",
                classification: "SETUP/UNRUN, not behavioral RED",
                error: "Missing accepted inspectionPaging state",
            });
        probe.dispose();
    }
} catch (error) {
    setup.push({
        stage: "actual-source-build-or-import",
        classification: "SETUP/UNRUN, not behavioral RED",
        error: String(error?.message ?? error).slice(0, 500),
    });
}

const clone = (value) => structuredClone(value),
    scope = { story: "paging-synthetic", branch: "main" };
const options = (patch = {}) => ({
    view: "profiles",
    atRevision: null,
    search: "",
    ...patch,
});
const context = (patch = {}) => ({
    session: "paging-session",
    scope: clone(scope),
    revision: 7,
    player: "player",
    view: "lab",
    observer: { kind: "omniscient" },
    persistent: true,
    pending: false,
    blocked: false,
    playMode: "fixture",
    inputKind: "action",
    action: "wait",
    fakeMode: "accepted",
    ...patch,
});
const snapshot = (c) => ({
    version: 2,
    domain_version: 2,
    scope: clone(c.scope),
    revision: c.revision,
    rules: "fantasy_v1",
    player: {
        observer: c.player,
        self_state: {
            name: "Synthetic Rowan",
            location: "quay",
            alive: true,
            energy: 2,
            abilities: {},
            attributes: {},
            injuries: [],
            affiliations: [],
            goals: [],
        },
    },
    inventory: {},
});
const token = (n) => `2:${n}:${hash(`synthetic-opaque-continuation-${n}`)}`;
function deferred() {
    let resolve, reject;
    const promise = new Promise((yes, no) => {
        resolve = yes;
        reject = no;
    });
    return { promise, resolve, reject };
}
async function settle() {
    for (let i = 0; i < 80; i++) await Promise.resolve();
}
const pageKeys = [
    "bound",
    "canPrevious",
    "canNext",
    "retainedPrevious",
    "earlierOmitted",
    "navigating",
].sort();
function paging(c) {
    const value = c.get().inspectionPaging;
    assert(value, "Accepted inspectionPaging state absent");
    assert.deepEqual(
        Object.keys(value).sort(),
        pageKeys,
        "PresentationOnlyClosedPagingMetadata",
    );
    assert.equal(typeof value.bound, "boolean");
    assert.equal(typeof value.canPrevious, "boolean");
    assert.equal(typeof value.canNext, "boolean");
    assert(
        Number.isInteger(value.retainedPrevious) &&
            value.retainedPrevious >= 0 &&
            value.retainedPrevious <= 32,
    );
    assert.equal(typeof value.earlierOmitted, "boolean");
    assert([null, "previous", "next"].includes(value.navigating));
    return clone(value);
}
function noFrame(c) {
    assert.deepEqual(paging(c), {
        bound: false,
        canPrevious: false,
        canNext: false,
        retainedPrevious: 0,
        earlierOmitted: false,
        navigating: null,
    });
}
function queryCalls(f) {
    return f.calls.filter((command) => command.op === "inspection_query");
}
function noWrites(f, baseline = 0) {
    assert(
        f.calls
            .slice(baseline)
            .every((command) =>
                ["inspection_query", "play_snapshot_v2"].includes(command.op),
            ),
        "NavigationDidNotWriteOrGenerate",
    );
}
function row(q, n, visit) {
    const common = { key: `row-${n}-${visit}`, origin: "canonical_field" };
    if (q.view === "profiles")
        return {
            ...common,
            kind: "field",
            actor: q.observer.kind === "character" ? q.observer.id : "player",
            field: "location",
            value: { type: "text", value: `fresh-${n}-${visit}` },
            source: { kind: "seed", value: "paging-seed" },
        };
    if (q.view === "knowledge")
        return {
            kind: "knowledge",
            key: `knowledge-${n}-${visit}`,
            id: `fact-${n}-${visit}`,
            subject:
                q.observer.kind === "omniscient"
                    ? null
                    : q.observer.kind === "character"
                      ? q.observer.id
                      : "player",
            text: `fresh-${n}-${visit}`,
            confidence: null,
            sources: [{ kind: "seed", value: "paging-seed" }],
            origin:
                q.observer.kind === "omniscient"
                    ? "canonical_truth"
                    : "known_as_observed",
        };
    if (q.view === "history" && q.observer.kind === "character")
        return {
            kind: "event",
            key: `event-${n}-${visit}`,
            event: {
                sequence: Math.min(7, q.at_revision ?? q.expected_head),
                scope: clone(q.scope),
                turn: `recorded-${n}-${visit}`,
                story_time: 107,
                participants: [q.observer.id],
                witnesses: [q.observer.id],
                consequence: { effect: "time_advanced", from: 106, to: 107 },
            },
            origin: "recorded_observation",
        };
    if (q.view === "history")
        return {
            kind: "scoped_message",
            key: `history-${n}-${visit}`,
            original_scope: clone(q.scope),
            turn: `recorded-${n}-${visit}`,
            message_kind: "narration",
            text: `history-${n}-${visit}`,
            event_ids: [Math.min(7, q.at_revision ?? q.expected_head)],
            origin: "recorded_message",
        };
    return null;
}
function reply(
    q,
    n,
    visit,
    { last = 1000, empty = false, variable = false } = {},
) {
    const unsupported = ["summaries", "retrieval_indexes"].includes(q.view);
    const first = row(q, n, visit),
        rows =
            unsupported || empty || !first
                ? []
                : [
                      first,
                      ...(variable && n % 2 ? [row(q, n, visit + 100000)] : []),
                  ];
    return {
        version: 2,
        scope: clone(q.scope),
        head: q.expected_head,
        revision: q.at_revision ?? q.expected_head,
        story_time: 107,
        observer: clone(q.observer),
        view: q.view,
        privacy:
            q.observer.kind === "player"
                ? "player_visible"
                : q.observer.kind === "character"
                  ? "private_character"
                  : "private_omniscient",
        status: unsupported ? "unsupported" : "supported",
        total: unsupported || empty || !rows.length ? 0 : 4096,
        rows,
        next_cursor: rows.length && n < last ? token(n + 1) : null,
        unsupported: unsupported ? ["Synthetic unsupported view"] : [],
    };
}
function waitReceipt(request) {
    return {
        request: clone(request),
        proposal: {
            version: 1,
            scope: clone(request.scope),
            turn: request.turn,
            expected_revision: request.expected_revision,
            commands: [{ op: "wait", ticks: 1 }],
        },
        events: [
            {
                version: 1,
                scope: clone(request.scope),
                sequence: request.expected_revision + 1,
                turn: request.turn,
                rules: "fantasy_v1",
                seed: "paging-seed",
                story_time: 108,
                participants: ["player"],
                witnesses: ["player"],
                outcome: { effect: "time_advanced", from: 107, to: 108 },
            },
        ],
        narration: "You wait one synthetic tick.",
    };
}
async function fixture({
    patch = {},
    last = 1000,
    empty = false,
    variable = false,
    rootQuery = true,
    queryOptions = options(),
} = {}) {
    let selected = context(patch),
        visit = 0,
        request = null,
        committed = null;
    const continuations = new Map([[null, 0]]);
    for (let n = 1; n <= 1001; n++) continuations.set(token(n), n);
    const f = {
        calls: [],
        queue: [],
        snapshotGate: null,
        submitGate: null,
        controller: null,
        notes: [],
    };
    const gateway = {
        call: async (command) => {
            f.calls.push(clone(command));
            if (command.op === "play_snapshot_v2") {
                const value = snapshot(selected),
                    gate = f.snapshotGate;
                f.snapshotGate = null;
                if (gate) await gate.promise;
                return value;
            }
            if (command.op === "inspection_query") {
                const q = clone(command.query);
                assert(
                    continuations.has(q.cursor),
                    "OnlyScriptedOpaqueCursorFixture",
                );
                const value = reply(q, continuations.get(q.cursor), ++visit, {
                    last,
                    empty,
                    variable,
                });
                const at = f.queue.findIndex((entry) => entry.matches(q));
                if (at >= 0) {
                    const [entry] = f.queue.splice(at, 1);
                    return entry.run(q, value);
                }
                return value;
            }
            if (command.op === "submit") {
                request = clone(command.request);
                committed = waitReceipt(request);
                if (f.submitGate) return f.submitGate.promise;
                return {
                    turn: request.turn,
                    scope: clone(request.scope),
                    expected_revision: request.expected_revision,
                    phase: "queued",
                    error: null,
                    receipt: null,
                };
            }
            if (["prepare", "commit", "turn_status"].includes(command.op))
                return {
                    turn: request.turn,
                    scope: clone(request.scope),
                    expected_revision: request.expected_revision,
                    phase: command.op === "prepare" ? "ready" : "committed",
                    error: null,
                    receipt: command.op === "prepare" ? null : clone(committed),
                };
            throw Error(`UnexpectedSyntheticOperation:${command.op}`);
        },
    };
    const c = new actual.V2PlayController(
        gateway,
        async () => {
            if (committed) {
                selected = {
                    ...selected,
                    revision: committed.events.at(-1).sequence,
                };
                c.selectedContextChanged(selected);
            }
        },
        "paging-review",
    );
    f.controller = c;
    f.current = () => clone(selected);
    f.select = (change) => {
        selected = { ...selected, ...clone(change) };
        c.selectedContextChanged(selected);
    };
    f.enqueue = (run, matches = () => true) => f.queue.push({ run, matches });
    f.hold = (matches = () => true) => {
        const gate = deferred();
        f.enqueue(async (q, value) => {
            await gate.promise;
            return value;
        }, matches);
        return gate;
    };
    f.render = () => {
        actual.created.length = 0;
        const html = actual.renderToStaticMarkup(
            actual.createElement(actual.V2PlayPanel, { controller: c }),
        );
        return { html, elements: [...actual.created] };
    };
    c.selectedContextChanged(selected);
    await c.refresh(false);
    assert(
        c.get().snapshot && c.get().history,
        "ExistingSnapshotHistoryFixtureCalibration",
    );
    assert.equal(c.get().error, null);
    if (rootQuery) {
        await c.readQuery(queryOptions);
        assert(c.get().inspection, "ExistingCheckedPageFixtureCalibration");
        assert.equal(c.get().error, null);
    }
    f.calls.length = 0;
    return f;
}
async function next(f) {
    const cursor = f.controller.get().inspection?.page.next_cursor;
    assert(cursor);
    return f.controller.page(cursor);
}
async function previous(f) {
    return f.controller.previousInspectionPage();
}
function test(name, body) {
    cases.push({ name, body });
}
function text(node) {
    if (node == null || typeof node === "boolean") return "";
    if (Array.isArray(node)) return node.map(text).join("");
    if (typeof node === "object") return text(node.props?.children);
    return String(node);
}
function descendants(node, predicate) {
    const found = [];
    const visit = (value) => {
        if (Array.isArray(value)) {
            value.forEach(visit);
            return;
        }
        if (!value || typeof value !== "object") return;
        if (predicate(value)) found.push(value);
        visit(value.props?.children);
    };
    visit(node);
    return found;
}
function panel(rendered) {
    const all = rendered.elements.filter(
        (element) =>
            element.type === "section" &&
            element.props["aria-label"] === "Read-only V2 inspector",
    );
    assert.equal(all.length, 1);
    return all[0];
}
function inspectorMarkup(rendered) {
    let start = -1,
        depth = 0;
    for (const match of rendered.html.matchAll(/<\/?section\b[^>]*>/g)) {
        if (start < 0) {
            if (!match[0].includes('aria-label="Read-only V2 inspector"'))
                continue;
            start = match.index;
        }
        depth += match[0].startsWith("</") ? -1 : 1;
        if (depth === 0)
            return rendered.html.slice(start, match.index + match[0].length);
    }
    throw Error("ActualSSRInspectorRegionMissing");
}
const markupText = (value) =>
    value
        .replace(/<[^>]*>/g, "")
        .replaceAll("&amp;", "&")
        .replaceAll("&lt;", "<")
        .replaceAll("&gt;", ">")
        .replaceAll("&#x27;", "'")
        .replaceAll("&quot;", '"');
function button(rendered, label) {
    const found = rendered.elements.filter(
        (element) => element.type === "button" && text(element) === label,
    );
    if (found.length !== 1)
        throw Object.assign(Error(`Missing actual panel button: ${label}`), {
            setup: true,
        });
    assert(
        markupText(inspectorMarkup(rendered)).includes(label),
        "ActualPagerIsInsideInspector",
    );
    return found[0].props;
}
function form(rendered) {
    const found = descendants(
        panel(rendered),
        (element) => element.type === "form",
    );
    assert.equal(found.length, 1);
    return found[0].props;
}
function fields(rendered) {
    const inside = descendants(
        panel(rendered),
        (element) => element.type === "form",
    )[0];
    return {
        view: descendants(inside, (e) => e.type === "select")[0].props,
        at: descendants(
            inside,
            (e) => e.type === "input" && e.props.type === "number",
        )[0].props,
        search: descendants(
            inside,
            (e) => e.type === "input" && e.props.type !== "number",
        )[0].props,
    };
}
function statuses(rendered) {
    return [
        ...inspectorMarkup(rendered).matchAll(
            /<([a-z][\w:-]*)\b[^>]*\brole="status"[^>]*>([\s\S]*?)<\/\1>/g,
        ),
    ]
        .map((match) => markupText(match[2]))
        .join(" ");
}
function spy(c, name) {
    const original = c[name].bind(c),
        calls = [];
    c[name] = (...args) => {
        calls.push(args);
        return original(...args);
    };
    return calls;
}
function mutate(value, change) {
    const before = JSON.stringify(value);
    try {
        change(value);
    } catch {}
    return JSON.stringify(value) !== before;
}

test("first-next-previous-null-forward-refetch-exact-query-and-new-body", async () => {
    const f = await fixture(),
        c = f.controller,
        original = c.get().inspection;
    assert.deepEqual(paging(c), {
        bound: true,
        canPrevious: false,
        canNext: true,
        retainedPrevious: 0,
        earlierOmitted: false,
        navigating: null,
    });
    await next(f);
    assert.equal(paging(c).retainedPrevious, 1);
    assert.equal(c.get().inspection.query.cursor, token(1));
    const back = await previous(f);
    assert.equal(back.query.cursor, null);
    assert.notDeepEqual(
        back.page.rows,
        original.page.rows,
        "PreviousMustRefetchNotRestoreCachedRows",
    );
    assert.equal(paging(c).retainedPrevious, 0);
    await next(f);
    assert.equal(c.get().inspection.query.cursor, token(1));
    assert.equal(queryCalls(f).length, 3);
    for (const call of queryCalls(f)) {
        const { cursor, ...identity } = call.query;
        const { cursor: ignored, ...expected } = original.query;
        assert.deepEqual(identity, expected);
        assert.equal(call.session, f.current().session);
    }
    noWrites(f);
    c.dispose();
});
test("rolling32-retains-most-recent-cursors-not-page-count-limit", async () => {
    const f = await fixture({ variable: true }),
        c = f.controller;
    for (let n = 1; n <= 35; n++) {
        await next(f);
        assert.equal(paging(c).retainedPrevious, Math.min(n, 32));
        assert.equal(paging(c).canNext, true);
        assert.equal(paging(c).earlierOmitted, n > 32);
    }
    for (let n = 0; n < 32; n++) await previous(f);
    assert.equal(c.get().inspection.query.cursor, token(3));
    assert.equal(paging(c).retainedPrevious, 0);
    assert.equal(paging(c).canPrevious, false);
    assert.equal(paging(c).earlierOmitted, true);
    const calls = f.calls.length;
    assert.equal(await previous(f), null);
    assert.equal(f.calls.length, calls);
    await c.readQuery(options());
    assert.equal(c.get().inspection.query.cursor, null);
    assert.equal(paging(c).earlierOmitted, false);
    assert.equal(paging(c).retainedPrevious, 0);
    await next(f);
    await previous(f);
    assert.equal(paging(c).earlierOmitted, false);
    noWrites(f);
    c.dispose();
});
test("final-page-and-no-predecessor-are-local-noops", async () => {
    const f = await fixture({ last: 2 }),
        c = f.controller;
    assert.equal(await previous(f), null);
    assert.equal(f.calls.length, 0);
    assert.equal(c.get().error, null);
    await next(f);
    await next(f);
    assert.equal(paging(c).canNext, false);
    assert.equal(paging(c).retainedPrevious, 2);
    const page = c.get().inspection;
    await c.page("foreign-cursor");
    assert.equal(queryCalls(f).length, 2);
    assert.strictEqual(c.get().inspection, page);
    assert.equal(paging(c).retainedPrevious, 2);
    await previous(f);
    assert.equal(c.get().inspection.query.cursor, token(1));
    noWrites(f);
    c.dispose();
});
for (const view of ["summaries", "retrieval_indexes"])
    test(`unsupported-${view}-no-fabricated-pagination`, async () => {
        const f = await fixture({ queryOptions: options({ view }) }),
            c = f.controller;
        assert.equal(c.get().inspection.page.status, "unsupported");
        assert.equal(paging(c).canPrevious, false);
        assert.equal(paging(c).canNext, false);
        assert.equal(await previous(f), null);
        assert.equal(f.calls.length, 0);
        noWrites(f);
        c.dispose();
    });
test("empty-supported-page-has-no-previous-or-next", async () => {
    const f = await fixture({ empty: true }),
        c = f.controller;
    assert.equal(paging(c).canPrevious, false);
    assert.equal(paging(c).canNext, false);
    assert.equal(await previous(f), null);
    assert.equal(f.calls.length, 0);
    c.dispose();
});
for (const [label, fail] of [
    [
        "native-stale",
        () => {
            throw Error("Stale");
        },
    ],
    ["malformed-page", (q, p) => ({ ...p, rows: [{ kind: "foreign" }] })],
    ["wrong-head", (q, p) => ({ ...p, head: p.head + 1 })],
    [
        "wrong-observer",
        (q, p) => ({
            ...p,
            observer: { kind: "player" },
            privacy: "player_visible",
        }),
    ],
    [
        "oversized-next",
        (q, p) => ({
            ...p,
            next_cursor: "2:" + "1".repeat(129) + ":" + "a".repeat(64),
        }),
    ],
])
    test(`failed-previous-${label}-preserves-body-stack-and-retries-same-cursor`, async () => {
        const f = await fixture(),
            c = f.controller;
        await next(f);
        const bound = c.get().inspection;
        f.enqueue(fail);
        assert.equal(await previous(f), null);
        assert.strictEqual(c.get().inspection, bound);
        assert.equal(paging(c).retainedPrevious, 1);
        assert.equal(paging(c).canPrevious, true);
        assert(c.get().error);
        await previous(f);
        assert.equal(c.get().inspection.query.cursor, null);
        assert.equal(paging(c).retainedPrevious, 0);
        assert.equal(
            queryCalls(f).at(-1).query.cursor,
            queryCalls(f).at(-2).query.cursor,
        );
        noWrites(f);
        c.dispose();
    });
test("navigation-inflight-is-installed-before-reentrant-pending-notification", async () => {
    const f = await fixture(),
        c = f.controller,
        gate = f.hold();
    let once = false;
    const repeats = [];
    c.subscribe(() => {
        if (c.get().queryBusy && !once) {
            once = true;
            repeats.push(previous(f), next(f));
        }
    });
    const pending = next(f);
    await settle();
    assert.equal(queryCalls(f).length, 1);
    assert.equal(paging(c).navigating, "next");
    assert.equal(await previous(f), null);
    gate.resolve();
    await pending;
    await Promise.all(repeats);
    assert.equal(queryCalls(f).length, 1);
    assert.equal(paging(c).retainedPrevious, 1);
    noWrites(f);
    c.dispose();
});
test("history-forward-is-independent-during-inspector-navigation", async () => {
    const f = await fixture(),
        c = f.controller,
        gate = f.hold((q) => q.view === "profiles"),
        before = c.get().history;
    const pending = next(f);
    await settle();
    await c.page(before.page.next_cursor, "history");
    assert.notStrictEqual(c.get().history, before);
    assert.equal(c.get().queryBusy, true);
    assert.equal(paging(c).navigating, "next");
    gate.resolve();
    await pending;
    assert.equal(paging(c).retainedPrevious, 1);
    assert.equal(c.get().inspection.query.cursor, token(1));
    noWrites(f);
    c.dispose();
});
for (const change of [
    { session: "other-session" },
    { scope: { ...scope, story: "other-story" } },
    { scope: { ...scope, branch: "other-branch" } },
    { revision: 8 },
    { player: "other-player" },
    { observer: { kind: "player" } },
    { observer: { kind: "character", id: "mira" } },
    { view: "play" },
])
    test(`context-change-retires-cursors-${JSON.stringify(change)}`, async () => {
        const f = await fixture(),
            c = f.controller;
        await next(f);
        f.select(change);
        noFrame(c);
        assert.equal(c.get().inspection, null);
        const before = f.calls.length;
        assert.equal(await previous(f), null);
        assert.equal(f.calls.length, before);
        await c.refresh(false);
        await c.readQuery(options());
        assert.equal(paging(c).retainedPrevious, 0);
        f.select(
            f.current().view === "play"
                ? { view: "lab" }
                : {
                      observer: { kind: "omniscient" },
                      session: "paging-session",
                      scope: clone(scope),
                      revision: 7,
                      player: "player",
                  },
        );
        noFrame(c);
        c.dispose();
    });
test("play-lens-remains-player-and-no-inspection-can-grant-another-lens", async () => {
    const f = await fixture({
        patch: { view: "play", observer: { kind: "omniscient" } },
    });
    await next(f);
    assert(
        queryCalls(f).every((call) => call.query.observer.kind === "player"),
    );
    noWrites(f);
    f.controller.dispose();
});
const mutations = [
    [
        "context-session",
        (s) => {
            s.context.session = "foreign";
        },
    ],
    [
        "context-scope",
        (s) => {
            s.context.scope.branch = "foreign";
        },
    ],
    [
        "context-player",
        (s) => {
            s.context.player = "mira";
        },
    ],
    [
        "snapshot-player",
        (s) => {
            s.snapshot.player.observer = "mira";
        },
    ],
    [
        "snapshot-same-head-object",
        (s) => {
            s.snapshot = clone(s.snapshot);
        },
    ],
    [
        "bound-page-same-value-object",
        (s) => {
            s.inspection = clone(s.inspection);
        },
    ],
    [
        "query-search",
        (s) => {
            s.inspection.query.search = "foreign";
        },
    ],
    [
        "query-limit",
        (s) => {
            s.inspection.query.limit = 1;
        },
    ],
    [
        "query-cursor",
        (s) => {
            s.inspection.query.cursor = token(2);
        },
    ],
    [
        "query-view",
        (s) => {
            s.inspection.query.view = "history";
        },
    ],
    [
        "query-and-page-historical",
        (s) => {
            s.inspection.query.at_revision = 0;
            s.inspection.page.revision = 0;
        },
    ],
    [
        "query-and-page-head",
        (s) => {
            s.inspection.query.expected_head = 8;
            s.inspection.page.head = 8;
            s.inspection.page.revision = 8;
        },
    ],
    [
        "query-and-page-scope",
        (s) => {
            s.inspection.query.scope.branch = "foreign";
            s.inspection.page.scope.branch = "foreign";
        },
    ],
    [
        "query-observer",
        (s) => {
            s.inspection.query.observer = { kind: "player" };
        },
    ],
    [
        "page-next-valid-shape",
        (s) => {
            s.inspection.page.next_cursor = token(99);
        },
    ],
    [
        "page-next-over128",
        (s) => {
            s.inspection.page.next_cursor = "x".repeat(129);
        },
    ],
    [
        "page-negative-total",
        (s) => {
            s.inspection.page.total = -1;
        },
    ],
    [
        "page-invalid-row",
        (s) => {
            s.inspection.page.rows[0].kind = "foreign";
        },
    ],
];
for (const [name, change] of mutations)
    test(`public-mutation-${name}-cannot-borrow-navigation`, async () => {
        const f = await fixture(),
            c = f.controller;
        await next(f);
        const before = f.calls.length,
            originalQuery = clone(c.get().inspection.query),
            oldSnapshot = c.get().snapshot,
            oldBound = c.get().inspection;
        const applied =
            mutate(c.get(), change) ||
            c.get().snapshot !== oldSnapshot ||
            c.get().inspection !== oldBound;
        observations.push({
            case: name,
            controlApplied: applied,
            ifPrevented:
                "original tuple must remain authoritative; mutation itself is not required",
        });
        if (applied) {
            assert.equal(await previous(f), null);
            assert.equal(f.calls.length, before);
            noFrame(c);
        } else {
            await previous(f);
            const actualQuery = queryCalls(f).at(-1).query;
            assert.deepEqual(
                { ...actualQuery, cursor: originalQuery.cursor },
                originalQuery,
            );
        }
        noWrites(f);
        c.dispose();
    });
test("public-paging-hints-never-mint-a-predecessor", async () => {
    const f = await fixture(),
        c = f.controller;
    mutate(c.get().inspectionPaging, (p) => {
        p.canPrevious = true;
        p.retainedPrevious = 32;
        p.earlierOmitted = true;
    });
    assert.equal(await previous(f), null);
    assert.equal(f.calls.length, 0);
    await c.readQuery(options());
    assert.equal(paging(c).retainedPrevious, 0);
    noWrites(f);
    c.dispose();
});
for (const bad of [
    options({ atRevision: -1 }),
    options({ atRevision: 8 }),
    options({ search: "x".repeat(257) }),
    options({ search: "é".repeat(129) }),
    options({ search: "bad\nsearch" }),
])
    test(`invalid-fresh-query-retires-before-error-${JSON.stringify(bad)}`, async () => {
        const f = await fixture(),
            c = f.controller;
        await next(f);
        const bound = c.get().inspection,
            before = f.calls.length;
        let observed = false;
        c.subscribe(() => {
            if (c.get().error === "InvalidRequest") {
                observed = true;
                noFrame(c);
            }
        });
        assert.equal(await c.readQuery(bad), null);
        assert(observed);
        assert.strictEqual(c.get().inspection, bound);
        assert.equal(f.calls.length, before);
        noFrame(c);
        c.dispose();
    });
test("fresh-identical-read-clears-stack-before-pending-and-failure-keeps-own-body", async () => {
    const f = await fixture(),
        c = f.controller;
    await next(f);
    const displayed = c.get().inspection;
    let observed = false;
    f.enqueue(() => {
        throw Error("Stale");
    });
    c.subscribe(() => {
        if (c.get().queryBusy && !observed) {
            observed = true;
            noFrame(c);
        }
    });
    await c.readQuery(options());
    assert(observed);
    assert.strictEqual(c.get().inspection, displayed);
    assert.equal(c.get().error, "Stale");
    noFrame(c);
    const calls = f.calls.length;
    assert.equal(await previous(f), null);
    assert.equal(f.calls.length, calls);
    await c.readQuery(options());
    assert.equal(paging(c).retainedPrevious, 0);
    c.dispose();
});
for (const action of ["dispose", "replace-context"])
    test(`refresh-start-subscriber-${action}-prevents-old-snapshot-dispatch`, async () => {
        const f = await fixture(),
            c = f.controller;
        await next(f);
        const before = f.calls.length;
        let fired = false;
        c.subscribe(() => {
            if (c.get().readBusy && !fired) {
                fired = true;
                noFrame(c);
                if (action === "dispose") c.dispose();
                else f.select({ session: "replacement" });
            }
        });
        await c.refresh(false);
        assert(fired);
        assert.equal(f.calls.length, before);
        noFrame(c);
        c.dispose();
    });
test("same-head-refresh-snapshot-loss-and-malformed-context-do-not-recover-old-chain", async () => {
    const f = await fixture(),
        c = f.controller;
    await next(f);
    const old = c.get().snapshot;
    await c.refresh(false);
    assert.notStrictEqual(c.get().snapshot, old);
    noFrame(c);
    await c.readQuery(options());
    assert.equal(paging(c).retainedPrevious, 0);
    await next(f);
    if (
        mutate(c.get(), (s) => {
            s.snapshot = null;
        })
    ) {
        const before = f.calls.length;
        assert.equal(await previous(f), null);
        assert.equal(f.calls.length, before);
        noFrame(c);
    }
    c.selectedContextChanged({ ...f.current(), session: "" });
    assert.equal(c.get().context, null);
    noFrame(c);
    assert.equal(c.get().inspection, null);
    c.dispose();
});
test("reset-during-held-reply-retires-presentation-without-native-cancel", async () => {
    const f = await fixture(),
        c = f.controller,
        gate = f.hold();
    const pending = next(f);
    await settle();
    c.resetInspectionPaging();
    noFrame(c);
    gate.resolve();
    assert.equal(await pending, null);
    noFrame(c);
    assert.equal(c.get().source, null);
    assert.equal(c.get().sourceMatched, null);
    noWrites(f);
    c.dispose();
});
for (const phase of ["pending", "error", "result", "final"])
    for (const action of ["reset", "new-query", "context", "dispose"])
        test(`subscriber-${phase}-${action}-cannot-republish-retired-ledger`, async () => {
            const f = await fixture(),
                c = f.controller;
            await next(f);
            const before = c.get().inspection;
            let fired = false,
                newRead = null;
            if (phase === "error")
                f.enqueue(() => {
                    throw Error("Stale");
                });
            const newer = deferred();
            c.subscribe(() => {
                const state = c.get(),
                    p = state.inspectionPaging;
                const at =
                    phase === "pending"
                        ? state.queryBusy &&
                          p?.navigating === "previous" &&
                          state.inspection === before
                        : phase === "error"
                          ? state.error === "Stale"
                          : phase === "result"
                            ? state.queryBusy && state.inspection !== before
                            : !state.queryBusy && state.inspection !== before;
                if (!at || fired) return;
                fired = true;
                if (action === "reset") c.resetInspectionPaging();
                else if (action === "context")
                    f.select({ session: "replacement" });
                else if (action === "dispose") c.dispose();
                else {
                    f.enqueue(async (q, value) => {
                        await newer.promise;
                        return value;
                    });
                    newRead = c.readQuery(options({ search: "new-owner" }));
                }
            });
            const pending = previous(f);
            await settle();
            assert(fired, "ActualSubscriberBoundaryReached");
            if (action === "new-query") {
                assert(newRead);
                assert.equal(queryCalls(f).at(-1).query.search, "new-owner");
                assert.equal(c.get().queryBusy, true);
                newer.resolve();
                await newRead;
                assert.equal(c.get().inspection.query.search, "new-owner");
                assert.equal(paging(c).retainedPrevious, 0);
            } else {
                await pending;
                noFrame(c);
            }
            assert.equal(await pending, null);
            noWrites(f);
            c.dispose();
        });
test("final-busy-subscriber-can-start-new-navigation-without-old-finally-clearing-it", async () => {
    const f = await fixture(),
        c = f.controller;
    let started = false,
        back = null;
    const gate = deferred();
    c.subscribe(() => {
        if (
            !started &&
            !c.get().queryBusy &&
            c.get().inspection?.query.cursor === token(1)
        ) {
            started = true;
            f.enqueue(async (q, value) => {
                await gate.promise;
                return value;
            });
            back = previous(f);
        }
    });
    const forward = next(f);
    await settle();
    assert(started);
    assert.equal(c.get().queryBusy, true);
    assert.equal(paging(c).navigating, "previous");
    assert.equal(await forward, null);
    gate.resolve();
    await back;
    assert.equal(c.get().inspection.query.cursor, null);
    assert.equal(paging(c).retainedPrevious, 0);
    noWrites(f);
    c.dispose();
});
test("reset-inspector-does-not-retire-an-independent-history-reply", async () => {
    const f = await fixture(),
        c = f.controller,
        gate = f.hold((q) => q.view === "history");
    const old = c.get().history;
    const history = c.page(old.page.next_cursor, "history");
    await settle();
    c.resetInspectionPaging();
    gate.resolve();
    await history;
    assert.notStrictEqual(c.get().history, old);
    noFrame(c);
    noWrites(f);
    c.dispose();
});
test("trace-recorded-and-seed-source-reads-start-fresh-cursor-chains", async () => {
    const f = await fixture({
            patch: { view: "play", observer: { kind: "player" } },
        }),
        c = f.controller;
    await next(f);
    const history = c.get().history,
        narration = history.page.rows[0];
    await c.traceRecordedTurn(narration, history);
    assert.equal(c.get().inspection.query.view, "turn_diff");
    assert.equal(paging(c).retainedPrevious, 0);
    await c.readQuery(options());
    await next(f);
    await c.source({ kind: "seed", value: "paging-seed" });
    assert.equal(c.get().inspection.query.at_revision, 0);
    assert.equal(paging(c).retainedPrevious, 0);
    assert(c.get().source);
    c.resetInspectionPaging();
    assert.equal(c.get().source, null);
    assert.equal(c.get().sourceMatched, null);
    await c.readQuery(options());
    await next(f);
    await c.source({
        kind: "scoped_event",
        value: { original_scope: clone(scope), sequence: 1 },
    });
    assert.equal(c.get().inspection.query.cursor, null);
    assert.equal(c.get().inspection.query.view, "history");
    assert.equal(paging(c).retainedPrevious, 0);
    noWrites(f);
    c.dispose();
});
test("held-source-completion-cannot-republish-link-after-reset-and-new-query", async () => {
    const f = await fixture(),
        c = f.controller;
    await next(f);
    const gate = f.hold(),
        source = c.source({ kind: "seed", value: "paging-seed" });
    await settle();
    c.resetInspectionPaging();
    await c.readQuery(options({ search: "replacement" }));
    const bound = c.get().inspection;
    gate.resolve();
    await source;
    assert.strictEqual(c.get().inspection, bound);
    assert.equal(c.get().source, null);
    assert.equal(c.get().sourceMatched, null);
    assert.equal(paging(c).retainedPrevious, 0);
    noWrites(f);
    c.dispose();
});
test("accepted-receipt-trace-is-a-fresh-query-and-never-borrows-old-stack", async () => {
    const f = await fixture({
            patch: { view: "play", observer: { kind: "player" } },
        }),
        c = f.controller;
    await c.send();
    assert(c.get().receipt, "PublicSyntheticReceiptSetup");
    await c.readQuery(options());
    await next(f);
    const before = f.calls.length;
    await c.traceReceipt(c.get().receipt);
    assert.equal(c.get().inspection.query.view, "turn_diff");
    assert.equal(paging(c).retainedPrevious, 0);
    noWrites(f, before);
    c.dispose();
});
test("pending-and-uncertain-gameplay-operations-remain-unchanged-by-read-navigation", async () => {
    const f = await fixture({
            patch: { view: "play", observer: { kind: "player" } },
        }),
        c = f.controller,
        held = deferred();
    f.submitGate = held;
    const sending = c.send();
    await settle();
    assert(c.get().pending);
    const original = clone(c.get().pending.request),
        start = f.calls.length;
    await next(f);
    await previous(f);
    assert.deepEqual(c.get().pending.request, original);
    noWrites(f, start);
    held.reject(Error("Transport"));
    await sending;
    assert(c.get().uncertain);
    const notice = c.get().notice,
        before = f.calls.length;
    await next(f);
    assert.deepEqual(c.get().uncertain.request, original);
    assert.equal(c.get().notice, notice);
    noWrites(f, before);
    c.dispose();
});
test("panel-mounted-buttons-have-exact-names-type-and-safe-initial-disable", async () => {
    const f = await fixture({ rootQuery: false }),
        r = f.render();
    for (const name of ["Previous inspection page", "Next inspection page"]) {
        const b = button(r, name);
        assert.equal(b.type, "button");
        assert.equal(b.disabled, true);
    }
    assert(r.html.includes("Read-only V2 inspector"));
    f.controller.dispose();
});
test("panel-actual-previous-and-next-handlers-dispatch-once-and-no-write", async () => {
    const f = await fixture({ queryOptions: options({ view: "knowledge" }) }),
        c = f.controller;
    let r = f.render();
    assert.equal(button(r, "Previous inspection page").disabled, true);
    assert.equal(button(r, "Next inspection page").disabled, false);
    button(r, "Next inspection page").onClick();
    await settle();
    r = f.render();
    assert.equal(button(r, "Previous inspection page").disabled, false);
    button(r, "Previous inspection page").onClick();
    await settle();
    assert.equal(c.get().inspection.query.cursor, null);
    assert.equal(queryCalls(f).length, 2);
    noWrites(f);
    c.dispose();
});
for (const name of ["Previous inspection page", "Next inspection page"])
    for (const replacement of [
        "context",
        "same-head-snapshot",
        "same-value-page",
    ])
        test(`panel-captured-${name}-${replacement}-is-not-owner`, async () => {
            const f = await fixture({
                    queryOptions: options({ view: "knowledge" }),
                }),
                c = f.controller;
            await next(f);
            const old = button(f.render(), name),
                method = spy(
                    c,
                    name.startsWith("Previous")
                        ? "previousInspectionPage"
                        : "page",
                );
            if (replacement === "context") {
                f.select({ session: "replacement" });
                await c.refresh(false);
                await c.readQuery(options({ view: "knowledge" }));
            } else if (replacement === "same-head-snapshot") {
                await c.refresh(false);
                await c.readQuery(options({ view: "knowledge" }));
            } else if (
                !mutate(c.get(), (s) => {
                    s.inspection = clone(s.inspection);
                })
            ) {
                c.resetInspectionPaging();
            }
            const before = f.calls.length;
            old.onClick();
            await settle();
            assert.equal(
                method.length,
                0,
                "PanelChecksOwnerBeforeControllerMethod",
            );
            assert.equal(f.calls.length, before);
            c.dispose();
        });
for (const name of ["view", "at", "search"])
    test(`panel-form-${name}-invalidates-current-ledger-synchronously`, async () => {
        const f = await fixture({
                queryOptions: options({ view: "knowledge" }),
            }),
            c = f.controller;
        await next(f);
        const bound = c.get().inspection,
            reset = spy(c, "resetInspectionPaging"),
            handler = fields(f.render())[name];
        handler.onChange({
            target: {
                value:
                    name === "view"
                        ? "history"
                        : name === "at"
                          ? "4"
                          : "new search",
            },
        });
        assert.equal(reset.length, 1);
        noFrame(c);
        assert.strictEqual(c.get().inspection, bound);
        assert.equal(c.get().source, null);
        assert.equal(c.get().sourceMatched, null);
        noWrites(f);
        c.dispose();
    });
for (const field of ["view", "at", "search"])
    test(`panel-form-${field}-old-owner-does-not-reset-new-owner`, async () => {
        const f = await fixture({
                queryOptions: options({ view: "knowledge" }),
            }),
            c = f.controller,
            old = fields(f.render())[field],
            reset = spy(c, "resetInspectionPaging");
        f.select({ session: "replacement" });
        await c.refresh(false);
        await c.readQuery(options({ view: "knowledge" }));
        const expected = paging(c),
            before = f.calls.length;
        old.onChange({ target: { value: field === "view" ? "history" : "3" } });
        assert.equal(reset.length, 0);
        assert.deepEqual(paging(c), expected);
        assert.equal(f.calls.length, before);
        c.dispose();
    });
test("panel-submit-stale-render-does-not-query-a-new-session", async () => {
    const f = await fixture({ queryOptions: options({ view: "knowledge" }) }),
        c = f.controller,
        submit = form(f.render()),
        read = spy(c, "readQuery");
    f.select({ session: "replacement" });
    await c.refresh(false);
    const before = f.calls.length;
    let prevented = false;
    submit.onSubmit({
        preventDefault() {
            prevented = true;
        },
    });
    await settle();
    assert(prevented);
    assert.equal(read.length, 0);
    assert.equal(f.calls.length, before);
    c.dispose();
});
test("panel-current-submit-uses-real-rendered-drafts-and-starts-fresh", async () => {
    const f = await fixture({ queryOptions: options({ view: "knowledge" }) }),
        c = f.controller;
    await next(f);
    const r = f.render(),
        draft = fields(r),
        before = f.calls.length;
    form(r).onSubmit({ preventDefault() {} });
    await settle();
    const call = f.calls
        .slice(before)
        .find((call) => call.op === "inspection_query");
    assert(call);
    assert.equal(call.query.view, draft.view.value);
    assert.equal(call.query.search, draft.search.value);
    assert.equal(
        call.query.at_revision,
        draft.at.value === "" ? null : Number(draft.at.value),
    );
    assert.equal(call.query.cursor, null);
    assert.equal(paging(c).retainedPrevious, 0);
    noWrites(f);
    c.dispose();
});
test("panel-pending-direction-status-and-disabled-handler-guards", async () => {
    const f = await fixture({ queryOptions: options({ view: "knowledge" }) }),
        c = f.controller,
        gate = f.hold();
    const pending = next(f);
    await settle();
    const r = f.render();
    assert(
        /next/i.test(statuses(r)) &&
            /(reading|pending|loading)/i.test(statuses(r)),
    );
    const prev = spy(c, "previousInspectionPage"),
        forward = spy(c, "page"),
        before = f.calls.length;
    for (const label of ["Previous inspection page", "Next inspection page"]) {
        const b = button(r, label);
        assert.equal(b.disabled, true);
        b.onClick();
    }
    await settle();
    assert.equal(prev.length, 0);
    assert.equal(forward.length, 0);
    assert.equal(f.calls.length, before);
    gate.resolve();
    await pending;
    c.dispose();
});
test("panel-overflow-boundary-reset-failure-labels-keep-actual-context-and-hide-cursors", async () => {
    const f = await fixture({
            queryOptions: options({ view: "knowledge", atRevision: 5 }),
        }),
        c = f.controller;
    for (let n = 0; n < 35; n++) await next(f);
    for (let n = 0; n < 32; n++) await previous(f);
    let r = f.render(),
        status = statuses(r);
    assert(
        /earlier/i.test(status) && /(outside|retained|window)/i.test(status),
    );
    assert(/Read permitted view/i.test(status));
    assert.equal(button(r, "Previous inspection page").disabled, true);
    assert(!r.html.includes(token(3)));
    assert(!/\bpage\s+\d+\s+(?:of|\/)/i.test(r.html));
    c.resetInspectionPaging();
    r = f.render();
    assert(/successful.*read|read.*successful/i.test(statuses(r)));
    assert.equal(button(r, "Next inspection page").disabled, true);
    await c.readQuery(options({ view: "knowledge", atRevision: 5 }));
    await next(f);
    const bound = c.get().inspection;
    f.enqueue(() => {
        throw Error("Stale");
    });
    await previous(f);
    r = f.render();
    assert.strictEqual(c.get().inspection, bound);
    assert(
        r.html.includes("Stale") &&
            r.html.includes("selected head") &&
            r.html.includes("r7") &&
            r.html.includes("r5") &&
            r.html.includes("private omniscient"),
    );
    c.dispose();
});
test("panel-onchange-reset-subscriber-cannot-admit-through-a-replaced-owner", async () => {
    const f = await fixture({ queryOptions: options({ view: "knowledge" }) }),
        c = f.controller;
    await next(f);
    const handler = fields(f.render()).search;
    let fired = false;
    c.subscribe(() => {
        if (!fired && !c.get().inspectionPaging.bound) {
            fired = true;
            f.select({ session: "replacement" });
        }
    });
    const before = f.calls.length;
    handler.onChange({ target: { value: "stale-draft" } });
    assert(fired);
    assert.equal(c.get().context.session, "replacement");
    assert.equal(f.calls.length, before);
    noFrame(c);
    c.dispose();
});

assert.equal(cases.length, 92, "FrozenFinitePagingCaseRoster");
for (const { name, body } of cases) {
    if (setup.length) {
        results.push({ name, classification: "UNRUN_SETUP", passed: false });
        continue;
    }
    try {
        await body();
        results.push({ name, passed: true });
    } catch (error) {
        if (error?.setup)
            setup.push({
                stage: "new-panel-interface",
                classification: "SETUP/UNRUN, not behavioral RED",
                error: String(error.message).slice(0, 400),
            });
        results.push({
            name,
            passed: false,
            classification: error?.setup
                ? "SETUP/UNRUN"
                : "actual-source-assertion",
            error: String(error?.message ?? error).slice(0, 600),
        });
    }
}
for (const [name, expected] of Object.entries(sourceHashes))
    assert.equal(
        hash(await readFile(path.join(root, name))),
        expected,
        "ActualReviewedSourceUnchanged",
    );
const report = {
    version: 1,
    kind: "d05_v2_inspector_paging_first_v1",
    contractSource: "f3add8f8 plus eca52680 mutation precision",
    synthetic: true,
    sourceHashes,
    setup,
    authored: cases.length,
    passed: results.filter((r) => r.passed).length,
    failed: results.filter(
        (r) => r.classification === "actual-source-assertion",
    ).length,
    unrun: results.filter((r) =>
        String(r.classification ?? "").includes("SETUP"),
    ).length,
    checks: results,
    observations,
    execution:
        "actual V2PlayController and actual V2PlayPanel React SSR/captured JSX handlers; synthetic Gateway",
    nativeIpc: false,
    rustCoreExecution: false,
    modelExecution: false,
    rendering: "real React SSR only; no mounted browser DOM, pixels or focus",
    reactAdapter: {
        scope: "V2PlayPanel react import only",
        realReactHook: true,
        otherHooksReplaced: false,
    },
    desktopInput: false,
    limitations: [
        "Missing methods/UI or compilation are SETUP/UNRUN, not behavioral RED or zero-test PASS",
        "Synthetic cursors satisfy transport shape only; no native cursor authentication or Rust visibility/canonical outcome proof",
        "Previous refetch/new-body and rolling-window public behavior are tested; absence of unused private old-body retention additionally requires source review",
        "Mutation controls target binding/navigation scalars, actual player, object identity and failed bounded transport, not authentication of still-valid row text/total",
        "128-byte cursor refusal overlaps the fixed cursor grammar/safe-number bound; no constructible valid128-byte boundary is claimed",
        "Real SSR/captured handlers cannot observe mounted client useState/effects, post-reset local form values, focus, WebView layout or native IPC",
        "Synthetic accepted/pending submit controls are separately counted setup operations; read navigation itself must emit only inspection_query/play_snapshot_v2",
        "All actual generated bundle/report bytes remain retained in coordinator-admitted output; this source author ran no toolchain or runtime",
    ],
};
await mkdir(output, { recursive: true });
await writeFile(
    path.join(output, `v2-inspector-paging-${cohort}.json`),
    JSON.stringify(report, null, 2),
    { flag: "wx" },
);
console.log(JSON.stringify(report));
if (setup.length || report.failed) process.exitCode = 1;
