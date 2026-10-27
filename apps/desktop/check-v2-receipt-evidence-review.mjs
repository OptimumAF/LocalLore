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
            'export {V2PlayController} from "./ui/v2-play-controller"; export {V2PlayPanel} from "./ui/V2PlayPanel"; export {createElement} from "react"; export {renderToStaticMarkup} from "react-dom/server"; export {created} from "receipt-review-elements";',
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
                              namespace: "receipt-react-adapter",
                          }
                        : undefined,
                );
                plugin.onLoad(
                    { filter: /.*/, namespace: "receipt-react-adapter" },
                    () => ({
                        contents:
                            'import {useSyncExternalStore as realUseSyncExternalStore} from "react"; export * from "react"; export function useSyncExternalStore(subscribe,get,serverSnapshot=get){return realUseSyncExternalStore(subscribe,get,serverSnapshot);}',
                        loader: "js",
                        resolveDir: root,
                    }),
                );
                plugin.onResolve(
                    { filter: /^receipt-review-elements$/ },
                    () => ({ path: "elements", namespace: "receipt-review" }),
                );
                plugin.onLoad(
                    { filter: /.*/, namespace: "receipt-review" },
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
                            'import {__receiptElement,__receiptFragment} from "receipt-review-elements";\n' +
                            (await readFile(filename, "utf8")),
                        loader: "tsx",
                        resolveDir: path.dirname(filename),
                    }),
                );
            },
        },
    ],
});
const bundle = path.join(output, `v2-receipt-evidence-${cohort}.cjs`);
await writeFile(bundle, compiled.outputFiles[0].contents, { flag: "wx" });
const {
    V2PlayController,
    V2PlayPanel,
    createElement,
    renderToStaticMarkup,
    created,
} = (await import(pathToFileURL(bundle).href)).default;
const clone = (value) => structuredClone(value);
const story = "receipt-evidence-synthetic";
const selected = { story, branch: "corrected" };
const ancestor = { story, branch: "main" };
const inherited = () => ({
    kind: "scoped_event",
    value: { original_scope: clone(ancestor), sequence: 1 },
});
const seed = () => ({ kind: "seed", value: "lantern-quay-v1" });
const context = () => ({
    session: "receipt-session",
    scope: clone(selected),
    revision: 2,
    player: "player",
    view: "play",
    observer: { kind: "player" },
    persistent: true,
    pending: false,
    blocked: false,
    playMode: "fixture",
    inputKind: "action",
    action: "give",
    fakeMode: "accepted",
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
            name: "Rowan",
            location: "quay",
            alive: true,
            energy: 2,
            abilities: { steady: 1 },
            attributes: { resolve: 3 },
            injuries: [],
            affiliations: [],
            goals: [],
        },
    },
    inventory: {},
});
const page = (q, rows = []) => ({
    version: 2,
    scope: clone(q.scope),
    head: q.expected_head,
    revision: q.at_revision ?? q.expected_head,
    story_time: 101,
    observer: clone(q.observer),
    view: q.view,
    privacy:
        q.observer.kind === "player"
            ? "player_visible"
            : q.observer.kind === "character"
              ? "private_character"
              : "private_omniscient",
    status: "supported",
    total: rows.length,
    rows: clone(rows),
    next_cursor: null,
    unsupported: [],
});
const priorItem = (source = inherited()) => ({
    kind: "field",
    key: '["field","player","item/potion"]',
    actor: "player",
    field: "item/potion",
    value: {
        type: "item",
        value: { owner: "player", quantity: 1, return_to: null, healing: true },
    },
    source,
    origin: "canonical_field",
});
const removed = (source = inherited()) => ({
    kind: "change",
    key: '["field","player","item/potion"]',
    before_revision: 2,
    after_revision: 3,
    before: priorItem(source),
    after: null,
    origin: "derived_comparison",
});
const changed = () => ({
    kind: "change",
    key: '["field","player","energy"]',
    before_revision: 2,
    after_revision: 3,
    before: {
        kind: "field",
        key: '["field","player","energy"]',
        actor: "player",
        field: "energy",
        value: { type: "number", value: 2 },
        source: seed(),
        origin: "canonical_field",
    },
    after: {
        kind: "field",
        key: '["field","player","energy"]',
        actor: "player",
        field: "energy",
        value: { type: "number", value: 1 },
        source: {
            kind: "scoped_event",
            value: { original_scope: clone(selected), sequence: 3 },
        },
        origin: "canonical_field",
    },
    origin: "derived_comparison",
});
function eventRow(source) {
    return {
        kind: "event",
        key: "original-potion-source",
        event: {
            sequence: source.value.sequence,
            scope: clone(source.value.original_scope),
            turn: "original-acquisition",
            story_time: 100,
            participants: ["mira", "player"],
            witnesses: ["mira", "player"],
            consequence: {
                effect: "given",
                item: "potion",
                from: "mira",
                to: "player",
                quantity: 1,
            },
        },
        origin: "recorded_observation",
    };
}
function nativeLikeReceipt(request, multiple = false) {
    const commands = [
        { op: "give", item: "potion", to: "mira", quantity: 1 },
        ...(multiple ? [{ op: "wait", ticks: 1 }] : []),
    ];
    return {
        request: clone(request),
        proposal: {
            version: 1,
            scope: clone(request.scope),
            turn: request.turn,
            expected_revision: request.expected_revision,
            commands,
        },
        events: [
            {
                version: 1,
                scope: clone(request.scope),
                sequence: request.expected_revision + 1,
                turn: request.turn,
                rules: "fantasy_v1",
                seed: "lantern-quay-v1",
                story_time: 101,
                participants: ["mira", "player"],
                witnesses: ["mira", "player"],
                outcome: {
                    effect: "given",
                    item: "potion",
                    from: "player",
                    to: "mira",
                    quantity: 1,
                },
            },
            ...(multiple
                ? [
                      {
                          version: 1,
                          scope: clone(request.scope),
                          sequence: request.expected_revision + 2,
                          turn: request.turn,
                          rules: "fantasy_v1",
                          seed: "lantern-quay-v1",
                          story_time: 102,
                          participants: ["player"],
                          witnesses: ["player"],
                          outcome: {
                              effect: "time_advanced",
                              from: 101,
                              to: 102,
                          },
                      },
                  ]
                : []),
        ],
        narration: "You give Mira the potion.",
    };
}
function deferred() {
    let resolve;
    const promise = new Promise((done) => {
        resolve = done;
    });
    return { promise, resolve };
}
async function settle() {
    for (let n = 0; n < 40; n++) await Promise.resolve();
}
async function fixture({ multiple = false } = {}) {
    let current = context(),
        request = null,
        committed = null;
    if (multiple) current = { ...current, playMode: "local" };
    const calls = [],
        f = {
            calls,
            diffRows: [removed()],
            sourceReply: inherited(),
            queryGate: null,
        };
    if (multiple) f.diffRows = [{ ...removed(), after_revision: 4 }];
    const status = (phase) => ({
        turn: request.turn,
        scope: clone(request.scope),
        expected_revision: request.expected_revision,
        phase,
        error: null,
        receipt: phase === "committed" ? clone(committed) : null,
    });
    const gateway = {
        call: async (command) => {
            calls.push(clone(command));
            if (command.op === "play_snapshot_v2") return snapshot(current);
            if (command.op === "inspection_query") {
                const q = command.query;
                let reply = page(q);
                if (q.view === "turn_diff") reply = page(q, f.diffRows);
                if (q.view === "history" && q.search)
                    reply = page(
                        q,
                        f.sourceReply ? [eventRow(f.sourceReply)] : [],
                    );
                if (q.view === "profiles") reply = page(q, [priorItem(seed())]);
                if (f.queryGate) {
                    const held = f.queryGate;
                    f.queryGate = null;
                    await held.promise;
                }
                return reply;
            }
            if (command.op === "submit" || command.op === "free_text") {
                request = clone(command.request);
                committed = nativeLikeReceipt(request, multiple);
                return status("queued");
            }
            if (command.op === "prepare") return status("ready");
            if (command.op === "commit" || command.op === "turn_status")
                return status("committed");
            throw Error(`UnexpectedSyntheticOperation:${command.op}`);
        },
    };
    const controller = new V2PlayController(
        gateway,
        async () => {
            current = {
                ...current,
                revision: committed.events.at(-1).sequence,
            };
            controller.selectedContextChanged(current);
        },
        "receipt-evidence",
    );
    f.controller = controller;
    f.select = (patch) => {
        current = { ...current, ...clone(patch) };
        controller.selectedContextChanged(current);
    };
    f.render = () => {
        created.length = 0;
        try {
            const html = renderToStaticMarkup(
                createElement(V2PlayPanel, { controller }),
            );
            return { html, elements: [...created] };
        } catch (error) {
            error.evidence = "fixture-calibration-failure";
            throw error;
        }
    };
    try {
        controller.selectedContextChanged(current);
        await controller.refresh(false);
        if (multiple)
            controller.setDraft("Give Mira the potion and wait one tick.");
        await controller.send();
        assert.equal(
            controller.get().status.phase,
            "committed",
            "fixture must pass the actual transport decoder/controller",
        );
        assert.equal(controller.get().context.revision, multiple ? 4 : 3);
        assert.equal(controller.get().snapshot.revision, multiple ? 4 : 3);
        assert(controller.get().receipt);
    } catch (error) {
        error.evidence = "fixture-calibration-failure";
        throw error;
    }
    calls.length = 0;
    return f;
}
const queries = (f) => f.calls.filter((c) => c.op === "inspection_query");
function text(node) {
    if (node == null || typeof node === "boolean") return "";
    if (Array.isArray(node)) return node.map(text).join("");
    if (typeof node === "object") return text(node.props?.children);
    return String(node);
}
function button(rendered, label) {
    const found = rendered.elements.filter(
        (e) => e.type === "button" && text(e.props.children) === label,
    );
    if (found.length !== 1) {
        const error = Error(`Expected one actual panel button: ${label}`);
        error.evidence = "new-ui-absent";
        throw error;
    }
    return found[0].props;
}
function trace(f, candidate = f.controller.get().receipt) {
    if (typeof f.controller.traceReceipt !== "function") {
        const error = Error(
            "Missing new traceReceipt API; this is not behavioral RED",
        );
        error.evidence = "new-api-absent";
        throw error;
    }
    return f.controller.traceReceipt(candidate);
}
const noWrites = (f) =>
    assert(
        f.calls.every(
            (c) => c.op === "inspection_query" || c.op === "play_snapshot_v2",
        ),
        "evidence navigation cannot write/generate/grant/change sessions",
    );
async function diff(f) {
    const result = await f.controller.readQuery({
        view: "turn_diff",
        atRevision: 3,
        search: "",
    });
    try {
        assert(
            result &&
                result === f.controller.get().inspection &&
                result.page.rows.length,
            "existing DTO path must decode before assertions",
        );
    } catch (error) {
        error.evidence = "fixture-calibration-failure";
        throw error;
    }
    return result;
}
const cases = [],
    test = (name, kind, run) => cases.push({ name, kind, run });

test(
    "existing client-only panel renders current actual decoded receipt before new-button checks",
    "existing-ui",
    async () => {
        const f = await fixture(),
            current = f.controller.get().receipt,
            rendered = f.render();
        assert.match(rendered.html, /aria-label="Actual native receipt"/);
        assert.match(rendered.html, /Actual Rust receipt/);
        assert(rendered.html.includes(current.request.turn));
        assert(rendered.html.includes(current.narration));
        assert.equal(
            f.calls.length,
            0,
            "SSR calibration must not dispatch work or run client effects",
        );
        f.controller.dispose();
    },
);
test(
    "existing actual query decodes historical removed-field rows before new API exists",
    "existing-api",
    async () => {
        const f = await fixture(),
            bound = await diff(f);
        assert.equal(bound.page.rows[0].kind, "change");
        assert.equal(bound.page.rows[0].after, null);
        assert.deepEqual(bound.page.rows[0].before.source, inherited());
        noWrites(f);
        f.controller.dispose();
    },
);
for (const mutation of ["head", "session", "lens", "dispose", "nested-query"]) {
    test(
        `existing query pending notification ${mutation} cannot dispatch old read`,
        "existing-api",
        async () => {
            const f = await fixture();
            let acted = false;
            f.controller.subscribe(() => {
                if (!f.controller.get().queryBusy || acted) return;
                acted = true;
                if (mutation === "head") f.select({ revision: 4 });
                if (mutation === "session")
                    f.select({
                        session: "another-session",
                        scope: { story: "another-story", branch: "main" },
                    });
                if (mutation === "lens")
                    f.select({
                        view: "lab",
                        observer: { kind: "character", id: "mira" },
                    });
                if (mutation === "dispose") f.controller.dispose();
                if (mutation === "nested-query")
                    void f.controller.readQuery({
                        view: "knowledge",
                        atRevision: null,
                        search: "",
                    });
            });
            const result = await f.controller.readQuery({
                view: "turn_diff",
                atRevision: 3,
                search: "",
            });
            await settle();
            assert(acted);
            assert.equal(result, null);
            assert.equal(
                queries(f).filter((c) => c.query.view === "turn_diff").length,
                0,
            );
            if (mutation === "nested-query")
                assert.equal(
                    queries(f).length,
                    1,
                    "only newer read may dispatch",
                );
            else assert.equal(queries(f).length, 0);
            noWrites(f);
            f.controller.dispose();
        },
    );
}
for (const mutation of ["context", "newer-query", "dispose"]) {
    test(
        `existing query result notification ${mutation} cannot return retired bound page`,
        "existing-api",
        async () => {
            const f = await fixture();
            let acted = false;
            f.controller.subscribe(() => {
                if (
                    acted ||
                    f.controller.get().inspection?.query.view !== "turn_diff"
                )
                    return;
                acted = true;
                if (mutation === "context") f.select({ revision: 4 });
                if (mutation === "newer-query")
                    void f.controller.readQuery({
                        view: "knowledge",
                        atRevision: null,
                        search: "",
                    });
                if (mutation === "dispose") f.controller.dispose();
            });
            const result = await f.controller.readQuery({
                view: "turn_diff",
                atRevision: 3,
                search: "",
            });
            await settle();
            assert(acted);
            assert.equal(result, null);
            noWrites(f);
            f.controller.dispose();
        },
    );
}
for (const wrong of [
    { kind: "seed", value: "invented-seed" },
    {
        kind: "scoped_event",
        value: { original_scope: clone(ancestor), sequence: 2 },
    },
    {
        kind: "scoped_event",
        value: { original_scope: clone(selected), sequence: 1 },
    },
    {
        kind: "scoped_event",
        value: {
            original_scope: { story: "other-story", branch: "main" },
            sequence: 1,
        },
    },
]) {
    test(
        `bound source membership rejects invented ${JSON.stringify(wrong)}`,
        "existing-api",
        async () => {
            const f = await fixture(),
                bound = await diff(f);
            f.calls.length = 0;
            await f.controller.source(wrong, bound);
            assert.equal(f.calls.length, 0);
            assert.equal(f.controller.get().sourceMatched, null);
            f.controller.dispose();
        },
    );
}
test(
    "exact inherited member of removed before-value follows original scope without changing selected child",
    "existing-api",
    async () => {
        const f = await fixture(),
            bound = await diff(f),
            prior = bound.page.rows[0].before.source;
        f.calls.length = 0;
        await f.controller.source(prior, bound);
        assert.equal(queries(f).length, 1);
        assert.deepEqual(queries(f)[0].query.scope, selected);
        assert.deepEqual(queries(f)[0].query.observer, { kind: "player" });
        assert.equal(queries(f)[0].query.at_revision, 3);
        assert.equal(f.controller.get().sourceMatched, true);
        assert.deepEqual(
            f.controller.get().source.value.original_scope,
            ancestor,
        );
        assert.deepEqual(f.controller.get().context.scope, selected);
        assert.doesNotMatch(
            f.controller.get().notice,
            /caused|cause of|removed by/i,
        );
        noWrites(f);
        f.controller.dispose();
    },
);
test(
    "seed member navigates seed-era profiles and never asserts exact event/cause",
    "existing-api",
    async () => {
        const f = await fixture();
        f.diffRows = [removed(seed())];
        const bound = await diff(f);
        f.calls.length = 0;
        await f.controller.source(bound.page.rows[0].before.source, bound);
        assert.equal(queries(f).length, 1);
        assert.equal(queries(f)[0].query.view, "profiles");
        assert.equal(queries(f)[0].query.at_revision, 0);
        assert.equal(f.controller.get().sourceMatched, false);
        assert.match(f.controller.get().notice, /seed-era/i);
        assert.doesNotMatch(
            f.controller.get().notice,
            /caused|cause of|removed by/i,
        );
        noWrites(f);
        f.controller.dispose();
    },
);
test(
    "withheld member and obsolete bound object cannot dispatch",
    "existing-api",
    async () => {
        const f = await fixture();
        f.diffRows = [removed({ kind: "withheld" })];
        const bound = await diff(f);
        f.calls.length = 0;
        await f.controller.source({ kind: "withheld" }, bound);
        assert.equal(f.calls.length, 0);
        f.diffRows = [removed()];
        await diff(f);
        f.calls.length = 0;
        await f.controller.source(inherited(), bound);
        assert.equal(f.calls.length, 0);
        f.controller.dispose();
    },
);
test(
    "same sequence in wrong original branch and unavailable source never establish match",
    "existing-api",
    async () => {
        for (const answer of [
            null,
            {
                kind: "scoped_event",
                value: { original_scope: clone(selected), sequence: 1 },
            },
        ]) {
            const f = await fixture(),
                bound = await diff(f);
            f.sourceReply = answer;
            f.calls.length = 0;
            await f.controller.source(bound.page.rows[0].before.source, bound);
            assert.equal(f.controller.get().sourceMatched, false);
            assert.match(
                f.controller.get().notice,
                /no substitute|not present/i,
            );
            noWrites(f);
            f.controller.dispose();
        }
    },
);
test(
    "nested after-value source membership is accepted without requiring before-source equality",
    "existing-api",
    async () => {
        const f = await fixture();
        f.diffRows = [changed()];
        const bound = await diff(f),
            after = bound.page.rows[0].after.source;
        f.sourceReply = clone(after);
        f.calls.length = 0;
        await f.controller.source(after, bound);
        assert.equal(queries(f).length, 1);
        assert.equal(f.controller.get().sourceMatched, true);
        noWrites(f);
        f.controller.dispose();
    },
);

test(
    "new receipt action queries actual historical turn diff through Player without a Lab grant",
    "new-api",
    async () => {
        const f = await fixture(),
            current = f.controller.get().receipt;
        const result = await trace(f, current);
        assert(result && result === f.controller.get().inspection);
        assert.deepEqual(
            queries(f).map((c) => c.query),
            [
                {
                    version: 2,
                    scope: selected,
                    expected_head: 3,
                    at_revision: 3,
                    observer: { kind: "player" },
                    view: "turn_diff",
                    cursor: null,
                    limit: 64,
                    search: "",
                },
            ],
        );
        assert.equal(f.controller.get().receipt, current);
        assert.equal(f.controller.get().context.view, "play");
        noWrites(f);
        f.controller.dispose();
    },
);
test(
    "retained prior receipt uses old completed boundary and new current head",
    "new-api",
    async () => {
        const f = await fixture(),
            current = f.controller.get().receipt;
        f.select({ revision: 5 });
        await f.controller.refresh(false);
        assert.equal(f.controller.get().receipt, current);
        f.calls.length = 0;
        const result = await trace(f, current);
        assert(result);
        assert.equal(queries(f)[0].query.at_revision, 3);
        assert.equal(queries(f)[0].query.expected_head, 5);
        assert.equal(result.page.revision, 3);
        assert.equal(result.page.head, 5);
        noWrites(f);
        f.controller.dispose();
    },
);
test(
    "positive multi-event receipt uses final completed event rather than base plus one",
    "new-api",
    async () => {
        const f = await fixture({ multiple: true }),
            current = f.controller.get().receipt;
        // The free_text response above is a synthetic transport DTO, not model execution.
        assert.equal(current.events.length, 2);
        assert.deepEqual(
            current.events.map((event) => event.sequence),
            [3, 4],
        );
        const result = await trace(f, current);
        assert(result);
        assert.equal(queries(f)[0].query.at_revision, 4);
        assert.equal(queries(f)[0].query.expected_head, 4);
        noWrites(f);
        f.controller.dispose();
    },
);
for (const mode of [
    "cloned-receipt",
    "replaced-receipt",
    "no-snapshot",
    "lab-player",
    "lab-character",
    "lab-omniscient",
    "play-character",
    "wrong-snapshot-scope",
    "wrong-snapshot-head",
    "wrong-snapshot-player",
    "disposed",
]) {
    test(
        `new receipt action refuses ${mode} before dispatch`,
        "new-api",
        async () => {
            const f = await fixture();
            let candidate = f.controller.get().receipt;
            if (mode === "cloned-receipt") candidate = clone(candidate);
            if (mode === "replaced-receipt") {
                await f.controller.send();
            }
            if (mode === "no-snapshot") f.select({ revision: 4 });
            // Deliberate public-state mutation retains the exact receipt, so these
            // validate lens eligibility independently of contextChanged clearing it.
            if (mode === "lab-player")
                Object.assign(f.controller.get().context, {
                    view: "lab",
                    observer: { kind: "player" },
                });
            if (mode === "lab-character")
                Object.assign(f.controller.get().context, {
                    view: "lab",
                    observer: { kind: "character", id: "mira" },
                });
            if (mode === "lab-omniscient")
                Object.assign(f.controller.get().context, {
                    view: "lab",
                    observer: { kind: "omniscient" },
                });
            if (mode === "play-character") {
                f.controller.get().context.observer = {
                    kind: "character",
                    id: "player",
                };
            }
            if (mode === "wrong-snapshot-scope")
                f.controller.get().snapshot.scope.branch = "wrong";
            if (mode === "wrong-snapshot-head")
                f.controller.get().snapshot.revision = 2;
            if (mode === "wrong-snapshot-player")
                f.controller.get().snapshot.player.observer = "mira";
            if (mode === "disposed") f.controller.dispose();
            f.calls.length = 0;
            assert.equal(await trace(f, candidate), null);
            assert.equal(f.calls.length, 0);
            f.controller.dispose();
        },
    );
}
const malformed = [
    [
        "empty events",
        (r) => {
            r.events = [];
        },
    ],
    [
        "zero end",
        (r) => {
            r.events[0].sequence = 0;
        },
    ],
    [
        "fractional end",
        (r) => {
            r.events[0].sequence = 2.5;
        },
    ],
    [
        "unsafe end",
        (r) => {
            r.events[0].sequence = Number.MAX_SAFE_INTEGER + 1;
        },
    ],
    [
        "future end",
        (r) => {
            r.events[0].sequence = 4;
        },
    ],
    [
        "unsafe base",
        (r) => {
            r.request.expected_revision = Number.MAX_SAFE_INTEGER + 1;
        },
    ],
    [
        "fractional base",
        (r) => {
            r.request.expected_revision = 1.5;
        },
    ],
    [
        "wrong request scope",
        (r) => {
            r.request.scope.branch = "sibling";
        },
    ],
    [
        "wrong proposal scope",
        (r) => {
            r.proposal.scope.branch = "sibling";
        },
    ],
    [
        "wrong event scope",
        (r) => {
            r.events[0].scope.branch = "sibling";
        },
    ],
    [
        "wrong event turn",
        (r) => {
            r.events[0].turn = "other-turn";
        },
    ],
    [
        "duplicate sequence",
        (r) => {
            r.events.push(clone(r.events[0]));
        },
    ],
    [
        "gap sequence",
        (r) => {
            const event = clone(r.events[0]);
            event.sequence = 5;
            r.events.push(event);
        },
    ],
];
for (const [name, change] of malformed) {
    test(
        `new receipt action rejects current-object mutation: ${name}`,
        "new-api",
        async () => {
            const f = await fixture(),
                current = f.controller.get().receipt;
            change(current);
            assert.equal(await trace(f, current), null);
            assert.equal(f.calls.length, 0);
            f.controller.dispose();
        },
    );
}
for (const mode of ["head", "session", "lens", "dispose"]) {
    test(
        `new receipt held reply retired by ${mode} cannot publish`,
        "new-api",
        async () => {
            const f = await fixture(),
                held = deferred();
            f.queryGate = held;
            const pending = trace(f);
            await settle();
            assert.equal(queries(f).length, 1);
            if (mode === "head") f.select({ revision: 4 });
            if (mode === "session")
                f.select({
                    session: "other-session",
                    scope: { story: "other-story", branch: "main" },
                });
            if (mode === "lens")
                f.select({
                    view: "lab",
                    observer: { kind: "character", id: "mira" },
                });
            if (mode === "dispose") f.controller.dispose();
            held.resolve();
            assert.equal(await pending, null);
            assert.equal(f.controller.get().inspection, null);
            noWrites(f);
            f.controller.dispose();
        },
    );
}

const traceLabel = "Inspect accepted turn changes";
test(
    "actual panel current receipt button invokes the actual action without writes or Lab",
    "new-ui",
    async () => {
        const f = await fixture(),
            rendered = f.render(),
            action = button(rendered, traceLabel);
        assert.equal(Boolean(action.disabled), false);
        await action.onClick();
        await settle();
        assert.equal(queries(f).length, 1);
        assert.equal(queries(f)[0].query.view, "turn_diff");
        assert.equal(f.controller.get().context.view, "play");
        noWrites(f);
        f.controller.dispose();
    },
);
for (const mode of [
    "head-with-same-receipt",
    "session",
    "lens",
    "replaced-receipt",
    "dispose",
]) {
    test(
        `actual retained panel callback refuses ${mode} before dispatch`,
        "new-ui",
        async () => {
            const f = await fixture(),
                receipt = f.controller.get().receipt,
                action = button(f.render(), traceLabel);
            if (mode === "head-with-same-receipt") {
                f.select({ revision: 5 });
                await f.controller.refresh(false);
                assert.equal(f.controller.get().receipt, receipt);
            }
            if (mode === "session")
                f.select({
                    session: "other-session",
                    scope: { story: "other-story", branch: "main" },
                });
            if (mode === "lens")
                f.select({ view: "lab", observer: { kind: "omniscient" } });
            if (mode === "replaced-receipt") await f.controller.send();
            if (mode === "dispose") f.controller.dispose();
            f.calls.length = 0;
            await action.onClick();
            await settle();
            assert.equal(f.calls.length, 0);
            f.controller.dispose();
        },
    );
}
test(
    "newly rendered higher-head button can inspect retained historical receipt",
    "new-ui",
    async () => {
        const f = await fixture();
        f.select({ revision: 5 });
        await f.controller.refresh(false);
        f.calls.length = 0;
        const action = button(f.render(), traceLabel);
        assert.equal(Boolean(action.disabled), false);
        await action.onClick();
        await settle();
        assert.equal(queries(f).length, 1);
        assert.equal(queries(f)[0].query.at_revision, 3);
        assert.equal(queries(f)[0].query.expected_head, 5);
        noWrites(f);
        f.controller.dispose();
    },
);
test(
    "actual panel held action cannot restore retired inspection after a head change",
    "new-ui",
    async () => {
        const f = await fixture(),
            action = button(f.render(), traceLabel),
            held = deferred();
        f.queryGate = held;
        const pending = action.onClick();
        await settle();
        assert.equal(queries(f).length, 1);
        f.select({ revision: 5 });
        held.resolve();
        await pending;
        await settle();
        assert.equal(f.controller.get().inspection, null);
        assert.equal(queries(f).length, 1);
        // SSR cannot observe mounted local useState updates; native rendering must
        // separately verify that obsolete controls are not restored after await.
        noWrites(f);
        f.controller.dispose();
    },
);
test(
    "actual change table exposes before and after revisions, absence and prior-source qualification",
    "new-ui",
    async () => {
        const f = await fixture();
        await trace(f);
        const rendered = f.render();
        const tables = rendered.elements.filter((e) => e.type === "table");
        assert(
            tables.some(
                (e) => /before/i.test(text(e)) && /after/i.test(text(e)),
            ),
            "changes must have a readable semantic table, not only JSON",
        );
        assert.match(rendered.html, /Before[^<]*(?:r|revision)[^<]*2/i);
        assert.match(rendered.html, /After[^<]*(?:r|revision)[^<]*3/i);
        assert.match(rendered.html, /Absent/i);
        assert.match(
            rendered.html,
            /prior[^<]*(?:evidence|provenance)|(?:evidence|provenance)[^<]*prior/i,
        );
        assert.doesNotMatch(
            rendered.html,
            /caused the removal|removed by (?:event|source)/i,
        );
        const action = button(rendered, `${story} / main · event 1`);
        f.calls.length = 0;
        await action.onClick();
        await settle();
        assert.equal(f.controller.get().sourceMatched, true);
        assert.deepEqual(f.controller.get().context.scope, selected);
        noWrites(f);
        f.controller.dispose();
    },
);
test(
    "actual change table keeps literal hostile text inert and source controls scoped",
    "new-ui",
    async () => {
        const f = await fixture(),
            literal =
                '<img src="https://invalid.example/a" onerror="globalThis.receiptEvidence=1"> 雪 ' +
                "long ".repeat(80);
        // Presentation-only checked DTO row, not a claim this field changed in Rust.
        f.diffRows = [
            {
                kind: "change",
                key: '["field","player","name"]',
                before_revision: 2,
                after_revision: 3,
                before: {
                    kind: "field",
                    key: '["field","player","name"]',
                    actor: "player",
                    field: "name",
                    value: { type: "text", value: literal },
                    source: seed(),
                    origin: "canonical_field",
                },
                after: null,
                origin: "derived_comparison",
            },
        ];
        await trace(f);
        const rendered = f.render();
        assert.match(rendered.html, /&lt;img/);
        assert.match(rendered.html, /雪/);
        assert.doesNotMatch(rendered.html, /<img\b|<script\b|<iframe\b/i);
        assert(rendered.elements.some((e) => e.type === "table"));
        noWrites(f);
        f.controller.dispose();
    },
);

const results = [];
for (const { name, kind, run } of cases) {
    try {
        await run();
        results.push({ name, kind, passed: true });
    } catch (error) {
        results.push({
            name,
            kind,
            passed: false,
            classification:
                error.evidence ??
                (kind === "existing-ui"
                    ? "fixture-calibration-failure"
                    : kind === "existing-api"
                      ? "behavioral-assertion-failure"
                      : "new-interface-assertion-failure"),
            error: String(error?.message ?? error).slice(0, 600),
        });
    }
}
const report = {
    version: 1,
    synthetic: true,
    execution:
        "actual V2PlayController, actual client-only V2PlayPanel with test server-snapshot adapter, real React SSR and captured real JSX handlers; synthetic Gateway only",
    reactAdapter: {
        scope: "only V2PlayPanel react import",
        change: "supply existing get as missing useSyncExternalStore server snapshot",
        realReactHook: true,
        otherHooksReplaced: false,
    },
    nativeIpc: false,
    rustCoreExecution: false,
    modelExecution: false,
    rendering: "React SSR with test-only server snapshot; no browser pixels",
    desktopInput: false,
    sourceHashes,
    checks: results,
    passed: results.filter((r) => r.passed).length,
    failed: results.filter((r) => !r.passed).length,
    missingInterface: results.filter((r) =>
        /absent$/.test(r.classification ?? ""),
    ).length,
    limitations: [
        "No Main subscriptions/native grant/Core canonical outcomes/Store/actual IPC/WebView/DOM/clipboard or accessibility proof",
        "New traceReceipt API/panel absence is not behavioral RED; existing-api failures require actual execution and calibrated fixture decoding",
        "SSR handler capture does not qualify mounted React local-state rerender after await",
        "Synthetic changed-row DTOs are renderer/transport fixtures, not accepted engine receipts",
    ],
};
await writeFile(
    path.join(output, `v2-receipt-evidence-${cohort}.json`),
    JSON.stringify(report, null, 2),
    { flag: "wx" },
);
console.log(JSON.stringify(report));
if (report.failed) process.exitCode = 1;
