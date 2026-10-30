// Independent FIRST at b2728d01. SOURCE AUTHOR UNCOMPILED / UNRUN.
// Actual App/TimelinePanel/ForkPanel/V2PlayPanel/controllers and strict models.
// Inert React/hooks + JSX tree/static HTML and synthetic Gateway are disclosed
// doubles; no native IPC, Rust replay, persistence, focus, browser or pixels.
import assert from "node:assert/strict";
import { readFile, writeFile, realpath, stat } from "node:fs/promises";
import { build } from "esbuild";
import { createHash, randomUUID, webcrypto } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";

assert.equal(
    process.argv.length,
    2,
    "ClosedDomain2TimelineBrowserReviewArguments",
);
globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL(".", import.meta.url));
const MAIN = { story: "timeline-browser", branch: "main" };
const SIDE = { story: "timeline-browser", branch: "side" };
const OLD = { story: "timeline-browser", branch: "old" };
const TITLE = "Synthetic <script>NOT_CODE</script> & 雪";
const expectedReadOps = new Set([
    "workspace",
    "branches",
    "resume",
    "open",
    "close",
    "play_snapshot",
    "play_snapshot_v2",
    "inspection_query",
    "inspect",
]);
const names = [
    "App.tsx",
    "TimelinePanel.tsx",
    "ForkPanel.tsx",
    "V2PlayPanel.tsx",
    "controller.ts",
    "timeline-controller.ts",
    "timeline-model.ts",
    "fork-controller.ts",
    "v2-play-controller.ts",
    "v2-view-model.ts",
    "model.ts",
];
const setup = [],
    tests = [],
    results = [],
    source = {},
    artifacts = [];
const runId = randomUUID(),
    sha = (value) => createHash("sha256").update(value).digest("hex");
const clone = (value) => structuredClone(value);
const physicalD = (value) =>
    /^[dD]:[\\/]/.test(value.startsWith("\\\\?\\") ? value.slice(4) : value);
const equalScope = (a, b) => a?.story === b?.story && a?.branch === b?.branch;
const test = (group, name, run) => tests.push({ group, name, run });
let actual, output;
const tick = async () => {
    for (let n = 0; n < 100; n++) await Promise.resolve();
};
async function waitFor(predicate, label) {
    for (let n = 0; n < 50; n++) {
        if (predicate()) return;
        await tick();
    }
    assert(predicate(), label);
}
function deferred() {
    let resolve, reject;
    const promise = new Promise((a, b) => {
        resolve = a;
        reject = b;
    });
    return { promise, resolve, reject };
}
function thin(
    scope = MAIN,
    revision = 7,
    domain = 2,
    player = "native-player-7",
) {
    return {
        version: 2,
        domain_version: domain,
        scope: clone(scope),
        revision,
        rules: "fantasy_v1",
        player: {
            observer: player,
            self_state: {
                name: "Synthetic Rowan",
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
    };
}
function legacy(scope = MAIN, revision = 7) {
    return {
        scope: clone(scope),
        revision,
        rules: "fantasy_v1",
        player: {
            scope: clone(scope),
            revision,
            observer: "player",
            self_state: {
                name: "Synthetic Rowan",
                location: "quay",
                energy: 2,
            },
            facts: {},
            beliefs: [],
            observations: [],
        },
        inventory: {},
        receipts: [],
    };
}
function catalog(story = MAIN.story) {
    const row = (branch, parent, fork, revision, drafts, retired) => ({
        scope: { story, branch },
        parent_branch: parent,
        fork_revision: fork,
        revision,
        drafts,
        retired,
    });
    return {
        version: 2,
        story_id: story,
        title: TITLE,
        root_branch: "main",
        branches: [
            row("old", "main", 2, 5, 1, true),
            row("main", null, null, 7, 0, false),
            row("side", "old", 1, 3, 2, false),
        ],
    };
}
const context = (patch = {}) => ({
    session: "session-main",
    scope: clone(MAIN),
    revision: 7,
    view: "play",
    observer: "player",
    persistent: true,
    ...patch,
});
function contextInput(
    patch = {},
    selected = { id: "session-main", scope: clone(MAIN), revision: 7 },
) {
    const state = {
        disposed: false,
        play: null,
        playV2: thin(),
        view: "play",
        observer: "player",
        workspace: { persistent: true },
        ...patch,
    };
    return { get: () => state, selected: () => selected };
}

class Gateway {
    playSnapshotV2 = true;
    calls = [];
    domain = 2;
    failWorkspace = false;
    failSide = false;
    branchResponse = null;
    async call(command) {
        this.calls.push(clone(command));
        assert(
            expectedReadOps.has(command.op),
            `NoGenerationAuthorForkOrGrant:${command.op}`,
        );
        const head = command.scope?.branch === "side" ? 3 : 7;
        if (command.op === "workspace") {
            if (this.failWorkspace) {
                this.failWorkspace = false;
                throw Error("Transport");
            }
            return {
                persistent: true,
                location: "synthetic-transport-only",
                schema_version: 1,
                database_schema_version: 5,
                stories: [
                    {
                        scope: clone(MAIN),
                        title: TITLE,
                        revision: 7,
                        drafts: 0,
                    },
                ],
            };
        }
        if (command.op === "branches")
            return this.branchResponse
                ? await this.branchResponse(command)
                : catalog(command.story);
        if (command.op === "resume") {
            if (this.failSide && equalScope(command.scope, SIDE))
                throw Error("Transport");
            return {
                session: `session-${command.scope.branch}`,
                scope: clone(command.scope),
                revision: head,
                drafts: command.scope.branch === "side" ? 2 : 0,
            };
        }
        if (command.op === "open") return { revision: head };
        if (command.op === "close") return {};
        if (command.op === "play_snapshot_v2")
            return thin(
                command.scope,
                command.expected_revision,
                this.domain,
                this.domain === 2 ? "native-player-7" : "player",
            );
        if (command.op === "play_snapshot") {
            assert.equal(this.domain, 1, "Domain2CannotFallBackToLegacyPlay");
            return legacy(command.scope, command.expected_revision);
        }
        if (command.op === "inspection_query") {
            const q = command.query;
            return {
                version: 2,
                scope: clone(q.scope),
                head: q.expected_head,
                revision: q.at_revision ?? q.expected_head,
                story_time: 100,
                observer: clone(q.observer),
                view: q.view,
                privacy:
                    q.observer.kind === "player"
                        ? "player_visible"
                        : q.observer.kind === "character"
                          ? "private_character"
                          : "private_omniscient",
                status: "supported",
                total: 0,
                rows: [],
                next_cursor: null,
                unsupported: [],
            };
        }
        if (command.op === "inspect") return { synthetic: true };
        throw Error(`UnexpectedRead:${command.op}`);
    }
}
async function fixture(domain = 2) {
    const gateway = new Gateway();
    gateway.domain = domain;
    const c = new actual.Controller(gateway);
    const timeline = new actual.TimelineController(gateway, (scope) =>
        actual.resumeTimeline(c, scope),
    );
    const v2 = new actual.V2PlayController(
        gateway,
        async () => {},
        "timeline-browser-first",
    );
    const fork = new actual.ForkController(
        async () => {
            throw Error("NoForkNativeDispatch");
        },
        async () => {},
        () => {
            throw Error("NoForkRecoveryWrite");
        },
    );
    const sync = () => {
        const selected = c.selected(),
            s = c.get(),
            ctx = actual.timelineContext(c);
        timeline.contextChanged(ctx);
        fork.contextChanged(ctx);
        v2.selectedContextChanged(
            selected && s.playV2
                ? {
                      session: selected.id,
                      scope: clone(selected.scope),
                      revision: s.playV2.revision,
                      player: s.playV2.player.observer,
                      view: s.view,
                      observer:
                          s.observer === "player"
                              ? { kind: "player" }
                              : s.observer === "omniscient"
                                ? { kind: "omniscient" }
                                : { kind: "character", id: s.observer },
                      persistent: s.workspace?.persistent === true,
                      pending: !!s.pending,
                      blocked: false,
                      playMode: s.playMode,
                      inputKind: s.inputKind,
                      action: s.action,
                      fakeMode: s.fakeMode,
                  }
                : null,
        );
    };
    const unsubscribe = c.subscribe(sync);
    await c.library();
    await c.resume(MAIN);
    sync();
    assert(
        equalScope(c.selected()?.scope, MAIN),
        "ActualControllerFixtureSelectedMain",
    );
    if (domain === 2) {
        assert(c.get().playV2 && !c.get().play);
        await v2.refresh(false);
        assert(v2.get().snapshot);
    } else assert(c.get().play && !c.get().playV2);
    return {
        c,
        timeline,
        v2,
        fork,
        gateway,
        sync,
        async close() {
            unsubscribe();
            timeline.dispose();
            v2.dispose();
            fork.dispose();
            await c.dispose();
        },
    };
}
function browser(patch = {}, gateway = new Gateway()) {
    const selected = [],
        timeline = new actual.TimelineController(gateway, async (scope) => {
            selected.push(clone(scope));
        });
    const ctx = context(patch);
    timeline.contextChanged(ctx);
    return { timeline, gateway, selected, ctx };
}
function noWrites(gateway) {
    assert(gateway.calls.every((command) => expectedReadOps.has(command.op)));
}
function browserOnly(gateway, after = 0) {
    assert(
        gateway.calls
            .slice(after)
            .every((command) => command.op === "branches"),
        "BrowsingUsesOnlyExistingBranchesRead",
    );
}

// This adapter evaluates ACTUAL JSX function decisions/handlers with inert hooks.
// It is not React reconciliation, a mounted DOM, focus, native rendering or CSS.
const hookModule = `
export const __d08Fragment = Symbol("D08Fragment");
export const __d08Element = (type, props, ...children) => ({type,props:{...(props??{}),children}});
export const useSyncExternalStore = (_subscribe,get,_server) => get();
export const useState = (initial) => [typeof initial==="function"?initial():initial,()=>{}];
export const useRef = (initial) => ({current:initial});
export const useEffect = () => {};
export const useCallback = (callback) => callback;
`;
function expand(node, components, budget = { count: 0 }) {
    assert(++budget.count <= 12000, "BoundedActualAppTree");
    if (node === null || node === undefined || typeof node === "boolean")
        return null;
    if (Array.isArray(node))
        return node.map((item) => expand(item, components, budget));
    if (typeof node === "string" || typeof node === "number") return node;
    if (typeof node.type === "function") {
        components.push(node.type);
        return expand(node.type(node.props), components, budget);
    }
    if (typeof node.type === "symbol")
        return expand(node.props.children, components, budget);
    assert.equal(typeof node.type, "string");
    return {
        type: node.type,
        props: {
            ...node.props,
            children: expand(node.props.children, components, budget),
        },
    };
}
function escape(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}
function html(node) {
    if (node === null || node === undefined || typeof node === "boolean")
        return "";
    if (Array.isArray(node)) return node.map(html).join("");
    if (typeof node !== "object") return escape(node);
    const attrs = Object.entries(node.props)
        .filter(
            ([name, value]) =>
                ![
                    "children",
                    "key",
                    "ref",
                    "style",
                    "dangerouslySetInnerHTML",
                ].includes(name) &&
                !/^on[A-Z]/.test(name) &&
                typeof value !== "function" &&
                value !== null &&
                value !== undefined &&
                value !== false,
        )
        .map(
            ([name, value]) =>
                ` ${name === "className" ? "class" : name}="${escape(value === true ? "" : value)}"`,
        )
        .join("");
    const body =
        node.props.dangerouslySetInnerHTML?.__html ?? html(node.props.children);
    return `<${node.type}${attrs}>${body}</${node.type}>`;
}
function text(node) {
    if (node === null || node === undefined || typeof node === "boolean")
        return "";
    if (Array.isArray(node)) return node.map(text).join(" ");
    if (typeof node !== "object") return String(node);
    return text(node.props.children);
}
function nodes(node, predicate) {
    if (!node || typeof node !== "object") return [];
    if (Array.isArray(node))
        return node.flatMap((item) => nodes(item, predicate));
    return [
        ...(predicate(node) ? [node] : []),
        ...nodes(node.props.children, predicate),
    ];
}
function rendered(component, props) {
    const components = [],
        tree = expand({ type: component, props }, components),
        markup = html(tree);
    assert(
        Buffer.byteLength(markup) <= 256 * 1024,
        "BoundedSyntheticStaticHTML",
    );
    return {
        components,
        tree,
        html: markup,
        text: text(tree).replace(/\s+/g, " ").trim(),
    };
}
const panel = (timeline, ctx) =>
    rendered(actual.TimelinePanel, { timeline, context: ctx });
const app = (f) =>
    rendered(actual.App, {
        controller: f.c,
        timeline: f.timeline,
        fork: f.fork,
        v2: f.v2,
    });
function button(r, label) {
    const found = nodes(
        r.tree,
        (node) =>
            node.type === "button" &&
            text(node).replace(/\s+/g, " ").trim() === label,
    );
    assert.equal(found.length, 1, `UniqueActualButton:${label}`);
    return found[0].props;
}
async function save(label, r) {
    assert(artifacts.length < 4, "FixedFourStaticHTMLArtifacts");
    const name = `domain2-timeline-${runId}-${label}.html`;
    await writeFile(path.join(output, name), r.html, { flag: "wx" });
    artifacts.push({
        name,
        sha256: sha(r.html),
        bytes: Buffer.byteLength(r.html),
        rendering: "inert-JSX-static-HTML",
    });
}

for (const view of ["play", "lab"])
    test(
        "routing",
        `actual-App-V2-${view}-real-browser-and-hidden-Fork`,
        async () => {
            const f = await fixture();
            try {
                if (view === "lab") {
                    f.c.requestLab();
                    f.c.acknowledgeLab(true);
                    await f.v2.refresh(false);
                }
                await f.timeline.show();
                const before = f.gateway.calls.length,
                    r = app(f);
                await save(`app-${view}`, r);
                assert(
                    r.components.includes(actual.TimelinePanel),
                    "ActualAppMustEvaluateRealTimelinePanel",
                );
                assert(
                    r.components.includes(actual.V2PlayPanel),
                    "ActualAppRetainsRealV2PlayPanel",
                );
                assert(
                    !r.components.includes(actual.ForkPanel),
                    "Domain2ForkAdapterRemainsExcluded",
                );
                assert(!r.text.includes("Create alternate timeline"));
                assert(r.text.includes("Saved timelines"));
                assert(
                    !/timeline navigation and derived-memory maintenance remain unavailable/i.test(
                        r.text,
                    ),
                    "NoContradictoryDomain2NavigationNotice",
                );
                assert(
                    !r.text.includes("Author corrections remain unavailable"),
                    "BrowserIsNotAuthorityForGlobalAuthorCapabilityRefusal",
                );
                assert.equal(
                    f.gateway.calls.length,
                    before,
                    "RenderingDoesNotDispatch",
                );
                noWrites(f.gateway);
            } finally {
                await f.close();
            }
        },
    );
test("routing", "actual-App-legacy-keeps-real-browser-and-Fork", async () => {
    const f = await fixture(1);
    try {
        await f.timeline.show();
        const r = app(f);
        await save("app-legacy", r);
        assert(r.components.includes(actual.TimelinePanel));
        assert(r.components.includes(actual.ForkPanel));
        assert(!r.components.includes(actual.V2PlayPanel));
        assert(r.text.includes("Create alternate timeline"));
        noWrites(f.gateway);
    } finally {
        await f.close();
    }
});

test(
    "context",
    "V2-matching-head-preserves-session-workspace-and-three-lenses",
    () => {
        for (const [view, observer] of [
            ["play", "player"],
            ["lab", "mira"],
            ["lab", "omniscient"],
        ]) {
            const input = contextInput({ view, observer }),
                before = clone(input.get()),
                value = actual.timelineContext(input);
            assert.deepEqual(value, context({ view, observer }));
            assert.deepEqual(input.get(), before);
            assert.equal(input.get().playV2.player.observer, "native-player-7");
        }
    },
);
test("context", "V2-foreign-story-or-branch-refuses-owner-binding", () => {
    for (const scope of [{ story: "foreign", branch: "main" }, SIDE])
        assert.equal(
            actual.timelineContext(contextInput({ playV2: thin(scope) })),
            null,
        );
});
test("context", "V2-head-mismatch-refuses-selected-revision-fallback", () => {
    assert.equal(
        actual.timelineContext(contextInput({ playV2: thin(MAIN, 8) })),
        null,
    );
    assert.equal(
        actual.timelineContext(contextInput({ playV2: thin(MAIN, 6) })),
        null,
    );
});
test(
    "context",
    "public-dual-slots-use-coherent-V2-head-before-stale-legacy",
    () => {
        // Public Pick seam conformance. Actual Controller publishes exclusive slots;
        // no private state is injected and no dual-slot runtime defect is claimed.
        for (const stale of [
            legacy(MAIN, 5),
            legacy({ story: "foreign", branch: "main" }, 5),
        ]) {
            assert.deepEqual(
                actual.timelineContext(contextInput({ play: stale })),
                context(),
            );
        }
    },
);
test("context", "disposed-or-no-selected-owner-is-null", () => {
    assert.equal(
        actual.timelineContext(contextInput({ disposed: true })),
        null,
    );
    assert.equal(actual.timelineContext(contextInput({}, null)), null);
});
test("context", "legacy-play-and-selected-fallback-are-unchanged", () => {
    assert.equal(
        actual.timelineContext(
            contextInput({ playV2: null, play: legacy(MAIN, 5) }),
        ).revision,
        5,
    );
    assert.deepEqual(
        actual.timelineContext(
            contextInput({ playV2: null, play: null, workspace: null }),
        ),
        context({ persistent: false }),
    );
});

test(
    "panel",
    "real-catalog-metadata-ancestry-current-retired-and-escaping",
    async () => {
        const b = browser();
        await b.timeline.show();
        const r = panel(b.timeline, b.ctx);
        await save("catalog", r);
        assert(r.text.includes("old") && r.text.includes("main → old → side"));
        assert(
            r.text.includes("at accepted revision 1") &&
                r.text.includes("Catalogued head: 3") &&
                r.text.includes("saved uncommitted requests: 2"),
        );
        assert(button(r, "Selected timeline main").disabled);
        assert(button(r, "Retired timeline old").disabled);
        assert.equal(button(r, "Resume timeline side").disabled, false);
        assert(
            r.html.includes("&lt;script&gt;NOT_CODE&lt;/script&gt; &amp; 雪"),
        );
        assert(!r.html.includes("<script>"));
        assert(!r.text.includes("Author corrections remain unavailable"));
        browserOnly(b.gateway);
        b.timeline.dispose();
    },
);

test(
    "integration",
    "actual-panel-selection-uses-Timeline-resumeTimeline-Controller-exact-child",
    async () => {
        const f = await fixture();
        try {
            await f.timeline.show();
            const r = panel(f.timeline, actual.timelineContext(f.c)),
                before = f.gateway.calls.length;
            button(r, "Resume timeline side").onClick();
            await waitFor(
                () => equalScope(f.c.get().playV2?.scope, SIDE),
                "ExactChildSnapshotAfterActualPanelHandler",
            );
            assert.deepEqual(f.c.selected()?.scope, SIDE);
            assert.equal(f.c.selected()?.revision, 3);
            assert.equal(f.c.get().play, null);
            assert.deepEqual(
                f.gateway.calls
                    .slice(before)
                    .filter((q) => q.op === "resume")
                    .map((q) => q.scope),
                [SIDE],
            );
            assert.equal(f.c.get().playV2.player.observer, "native-player-7");
            noWrites(f.gateway);
        } finally {
            await f.close();
        }
    },
);
test(
    "integration",
    "existing-child-session-switch-does-not-create-second-resume",
    async () => {
        const f = await fixture();
        try {
            await actual.resumeTimeline(f.c, SIDE);
            await actual.resumeTimeline(f.c, MAIN);
            await f.timeline.show();
            const before = f.gateway.calls.filter(
                (q) => q.op === "resume",
            ).length;
            await f.timeline.select("side");
            assert.deepEqual(f.c.selected()?.scope, SIDE);
            assert.equal(
                f.gateway.calls.filter((q) => q.op === "resume").length,
                before,
            );
            assert.equal(f.c.get().playV2?.revision, 3);
            noWrites(f.gateway);
        } finally {
            await f.close();
        }
    },
);
test(
    "integration",
    "successful-target-wins-over-unrelated-prior-visible-error",
    async () => {
        const f = await fixture();
        try {
            f.gateway.failWorkspace = true;
            await f.c.start();
            assert.equal(f.c.get().visibleError, "Transport");
            await f.timeline.show();
            await f.timeline.select("side");
            assert.deepEqual(f.c.selected()?.scope, SIDE);
            assert.equal(f.c.get().playV2?.revision, 3);
            assert.equal(f.c.get().visibleError, null);
            noWrites(f.gateway);
        } finally {
            await f.close();
        }
    },
);
test(
    "integration",
    "failed-target-cannot-borrow-an-unrelated-old-error-as-success",
    async () => {
        const f = await fixture();
        try {
            f.gateway.failWorkspace = true;
            await f.c.start();
            assert.equal(f.c.get().visibleError, "Transport");
            f.gateway.failSide = true;
            await f.timeline.show();
            await f.timeline.select("side");
            assert.deepEqual(f.c.selected()?.scope, MAIN);
            assert.equal(f.timeline.get().status, "error");
            assert.equal(f.timeline.get().error, "NotReady");
            assert(!f.timeline.get().notice.includes("Selection completed"));
            noWrites(f.gateway);
        } finally {
            await f.close();
        }
    },
);
test(
    "integration",
    "browsing-only-branches-preserves-thin-play-and-observer",
    async () => {
        const f = await fixture();
        try {
            const before = f.gateway.calls.length,
                snapshot = clone(f.c.get().playV2),
                observer = f.c.get().observer;
            await f.timeline.show();
            await f.timeline.refresh();
            f.timeline.hide();
            await f.timeline.show();
            app(f);
            browserOnly(f.gateway, before);
            assert.deepEqual(f.c.get().playV2, snapshot);
            assert.equal(f.c.get().observer, observer);
            noWrites(f.gateway);
        } finally {
            await f.close();
        }
    },
);

test(
    "selection",
    "current-retired-unknown-busy-and-invalid-context-never-resume",
    async () => {
        const b = browser();
        await b.timeline.show();
        await b.timeline.select("main");
        await b.timeline.select("old");
        assert.equal(b.timeline.get().error, "Closed");
        await b.timeline.select("absent");
        assert.equal(b.timeline.get().error, "NotFound");
        assert.deepEqual(b.selected, []);
        const gate = deferred();
        b.gateway.branchResponse = async () => gate.promise;
        const refresh = b.timeline.refresh();
        assert.equal(b.timeline.get().busy, true);
        await b.timeline.select("side");
        assert.deepEqual(b.selected, []);
        b.timeline.contextChanged(null);
        gate.resolve(catalog());
        await refresh;
        await b.timeline.select("side");
        assert.deepEqual(b.selected, []);
        b.timeline.dispose();
        browserOnly(b.gateway);
    },
);
test(
    "errors",
    "typed-catalog-error-and-explicit-real-panel-retry",
    async () => {
        const b = browser();
        b.gateway.branchResponse = async () => {
            throw Error("Transport");
        };
        await b.timeline.show();
        assert.equal(b.timeline.get().error, "Transport");
        const r = panel(b.timeline, b.ctx);
        assert(r.text.includes("Timeline request: Transport"));
        assert.equal(b.timeline.get().catalog, null);
        b.gateway.branchResponse = null;
        const before = b.gateway.calls.length;
        button(r, "Refresh timeline catalog").onClick();
        await waitFor(
            () => b.timeline.get().status === "ready",
            "ActualRetryCompletes",
        );
        assert.equal(b.gateway.calls.length, before + 1);
        assert.equal(b.timeline.get().error, null);
        assert.deepEqual(b.selected, []);
        b.timeline.dispose();
    },
);
test(
    "errors",
    "malformed-foreign-and-unsupported-catalogs-never-select",
    async () => {
        for (const variant of ["version", "foreign", "extra", "unsupported"]) {
            const b = browser();
            b.gateway.branchResponse = async () => {
                if (variant === "unsupported") throw Error("Unsupported");
                const value = catalog();
                if (variant === "version") value.version = 1;
                if (variant === "foreign") value.story_id = "foreign";
                if (variant === "extra") value.hidden = "no extra metadata";
                return value;
            };
            await b.timeline.show();
            assert.equal(b.timeline.get().catalog, null);
            assert.equal(
                b.timeline.get().status,
                variant === "unsupported" ? "unsupported" : "error",
            );
            await b.timeline.select("side");
            assert.deepEqual(b.selected, []);
            b.timeline.dispose();
        }
    },
);

const changes = [
    ["story", { scope: { story: "other-story", branch: "main" } }],
    ["session", { session: "another-session" }],
    ["head", { revision: 8 }],
    ["view", { view: "lab" }],
    ["observer", { observer: "mira" }],
];
for (const [name, patch] of changes)
    test(
        "retirement",
        `late-catalog-after-${name}-change-is-retired`,
        async () => {
            const b = browser(),
                gate = deferred();
            b.gateway.branchResponse = async () => gate.promise;
            const pending = b.timeline.show();
            assert.equal(b.gateway.calls.length, 1);
            const next = context(patch);
            b.timeline.contextChanged(next);
            gate.resolve(catalog());
            await pending;
            assert.equal(b.timeline.get().catalog, null);
            assert.equal(b.timeline.get().shown, false);
            assert.equal(b.timeline.get().status, "idle");
            assert(b.timeline.matchesContext(next));
            assert.deepEqual(b.selected, []);
            b.timeline.dispose();
        },
    );
for (const [name, patch] of changes)
    test(
        "callbacks",
        `all-four-old-render-handlers-fence-${name}-change`,
        async () => {
            for (const action of ["show", "hide", "refresh", "resume"]) {
                const b = browser(),
                    calls = [];
                const exposed = {
                    get: b.timeline.get,
                    subscribe: b.timeline.subscribe,
                    matchesContext: (ctx) => b.timeline.matchesContext(ctx),
                    show: () => {
                        calls.push("show");
                        return b.timeline.show();
                    },
                    hide: () => {
                        calls.push("hide");
                        return b.timeline.hide();
                    },
                    refresh: () => {
                        calls.push("refresh");
                        return b.timeline.refresh();
                    },
                    select: (id) => {
                        calls.push("resume");
                        return b.timeline.select(id);
                    },
                };
                const oldShow = button(
                    panel(exposed, b.ctx),
                    "Saved timelines",
                ).onClick;
                await b.timeline.show();
                const r = panel(exposed, b.ctx);
                const handler =
                    action === "show"
                        ? oldShow
                        : button(
                              r,
                              action === "hide"
                                  ? "Close saved timelines"
                                  : action === "refresh"
                                    ? "Refresh timeline catalog"
                                    : "Resume timeline side",
                          ).onClick;
                const next = context(patch);
                b.timeline.contextChanged(next);
                b.gateway.branchResponse = async (command) => {
                    const value = catalog(command.story);
                    value.branches.find(
                        (row) => row.scope.branch === "main",
                    ).revision = next.revision;
                    return value;
                };
                await b.timeline.show();
                const before = clone(b.timeline.get()),
                    count = b.gateway.calls.length;
                handler();
                await tick();
                assert.deepEqual(
                    calls,
                    [],
                    `Old${action}MustCheckCapturedContextBeforeCallingController`,
                );
                assert.deepEqual(b.timeline.get(), before);
                assert.equal(b.gateway.calls.length, count);
                assert.deepEqual(b.selected, []);
                b.timeline.dispose();
            }
        },
    );
test(
    "retirement",
    "late-resume-error-cannot-relabel-a-new-context",
    async () => {
        const gateway = new Gateway(),
            gate = deferred(),
            selected = [];
        const t = new actual.TimelineController(gateway, async (scope) => {
            selected.push(clone(scope));
            await gate.promise;
        });
        t.contextChanged(context());
        await t.show();
        const pending = t.select("side");
        assert.equal(t.get().status, "resuming");
        const next = context({ session: "new-owner" });
        t.contextChanged(next);
        gate.reject(Error("Transport"));
        await pending;
        assert.deepEqual(selected, [SIDE]);
        assert.equal(t.get().status, "idle");
        assert.equal(t.get().error, null);
        assert.equal(t.get().catalog, null);
        t.dispose();
    },
);
test(
    "retirement",
    "disposal-retires-held-catalog-and-its-presentation",
    async () => {
        const b = browser(),
            gate = deferred();
        b.gateway.branchResponse = async () => gate.promise;
        const pending = b.timeline.show();
        b.timeline.dispose();
        gate.resolve(catalog());
        await pending;
        assert.equal(b.timeline.get().shown, false);
        assert.equal(b.timeline.get().catalog, null);
        assert.equal(b.timeline.get().busy, false);
        assert.equal(b.timeline.matchesContext(b.ctx), false);
        assert.deepEqual(b.selected, []);
    },
);
test(
    "availability",
    "empty-catalog-and-in-memory-unavailable-are-honest",
    async () => {
        const b = browser();
        b.gateway.branchResponse = async () => ({ ...catalog(), branches: [] });
        await b.timeline.show();
        assert.equal(b.timeline.get().status, "empty");
        assert(
            panel(b.timeline, b.ctx).text.includes(
                "No timelines were returned",
            ),
        );
        b.timeline.contextChanged(context({ persistent: false }));
        const before = b.gateway.calls.length;
        await b.timeline.show();
        assert.equal(b.timeline.get().status, "unsupported");
        assert.equal(b.gateway.calls.length, before);
        await b.timeline.select("side");
        assert.deepEqual(b.selected, []);
        b.timeline.dispose();
    },
);

assert.equal(tests.length, 31, "FrozenThirtyOneCaseBrowserFirstRoster");
try {
    const explicit = process.env.LOCALLORE_CHECK_OUTPUT_DIR;
    if (!explicit || !path.isAbsolute(explicit))
        throw Error("UNRUN_SETUP:ExplicitExistingDOutputRequired");
    const candidate = await realpath(explicit);
    if (!physicalD(candidate) || !(await stat(candidate)).isDirectory())
        throw Error("UNRUN_SETUP:PhysicalDOutputRequired");
    output = candidate;
    for (const name of ["TEMP", "TMP"]) {
        const temporary = process.env[name]
            ? await realpath(process.env[name])
            : null;
        if (
            !temporary ||
            !physicalD(temporary) ||
            !(await stat(temporary)).isDirectory()
        )
            throw Error("UNRUN_SETUP:PhysicalDTemporaryDirectoryRequired");
    }
    for (const name of names)
        source[name] = await readFile(path.join(root, "ui", name), "utf8");
    const bundled = await build({
        stdin: {
            contents:
                'export {App} from "./ui/App";export {TimelinePanel} from "./ui/TimelinePanel";export {ForkPanel} from "./ui/ForkPanel";export {V2PlayPanel} from "./ui/V2PlayPanel";export {Controller} from "./ui/controller";export {TimelineController,timelineContext,resumeTimeline} from "./ui/timeline-controller";export {V2PlayController} from "./ui/v2-play-controller";export {ForkController} from "./ui/fork-controller";',
            resolveDir: root,
            loader: "tsx",
        },
        bundle: true,
        platform: "node",
        format: "cjs",
        write: false,
        jsx: "transform",
        jsxFactory: "__d08Element",
        jsxFragment: "__d08Fragment",
        tsconfigRaw: {
            compilerOptions: {
                jsx: "react",
                jsxFactory: "__d08Element",
                jsxFragmentFactory: "__d08Fragment",
            },
        },
        plugins: [
            {
                name: "disclosed-inert-React-actual-App-tree",
                setup(plugin) {
                    plugin.onResolve({ filter: /^(react|d08-hooks)$/ }, () => ({
                        path: "d08-hooks",
                        namespace: "d08-hooks",
                    }));
                    plugin.onLoad(
                        { filter: /.*/, namespace: "d08-hooks" },
                        () => ({ contents: hookModule, loader: "js" }),
                    );
                    plugin.onLoad(
                        { filter: /\.tsx$/ },
                        async ({ path: filename }) => ({
                            contents:
                                'import {__d08Element,__d08Fragment} from "d08-hooks";\n' +
                                (await readFile(filename, "utf8")),
                            loader: "tsx",
                            resolveDir: path.dirname(filename),
                        }),
                    );
                },
            },
        ],
    });
    actual = vm.runInThisContext(
        `(function(){const module={exports:{}};const exports=module.exports;\n${bundled.outputFiles[0].text}\nreturn module.exports;})()`,
        { timeout: 1000, filename: "actual-domain2-timeline-App-first.cjs" },
    );
    for (const name of [
        "App",
        "TimelinePanel",
        "ForkPanel",
        "V2PlayPanel",
        "Controller",
        "TimelineController",
        "timelineContext",
        "resumeTimeline",
        "V2PlayController",
        "ForkController",
    ])
        if (typeof actual[name] !== "function")
            throw Error(`UNRUN_SETUP:MissingActualExport:${name}`);
} catch (error) {
    setup.push({
        classification: "UNRUN_SETUP",
        error: String(error).slice(0, 2048),
    });
}
if (!setup.length)
    for (const entry of tests) {
        try {
            await entry.run();
            results.push({
                group: entry.group,
                name: entry.name,
                passed: true,
            });
        } catch (error) {
            results.push({
                group: entry.group,
                name: entry.name,
                passed: false,
                error: String(error).slice(0, 1024),
            });
        }
    }
for (const [name, value] of Object.entries(source))
    if (sha(await readFile(path.join(root, "ui", name), "utf8")) !== sha(value))
        setup.push({
            classification: "UNRUN_SETUP",
            error: `SourceChangedDuringReview:${name}`,
        });
const report = {
    kind: "d08_domain2_timeline_browser_independent_first_v1",
    authored: tests.length,
    setup,
    executed: results.length,
    passed: results.filter((r) => r.passed).length,
    failed: results.filter((r) => !r.passed).length,
    results,
    artifacts,
    source: Object.fromEntries(
        Object.entries(source).map(([name, value]) => [name, sha(value)]),
    ),
    evidence: {
        routing: "actual App and real Timeline/Fork/V2 components evaluated",
        rendering: "inert React/hooks actual JSX tree/static HTML",
        transport:
            "synthetic Gateway through actual controllers and resumeTimeline",
        nativeIpc: false,
        webView: false,
        pixels: false,
        canonicalRust: false,
        durableSave: false,
        generation: false,
        device: false,
        desktopControl: false,
    },
    limitations: [
        "Source author ran no Node/toolchain/formatter/test/fixture; current-product failures are hypotheses until Root execution",
        "Inert hooks do not mount subscriptions/effects/local state, DOM/focus/CSS/keyboard or screen-reader behavior",
        "Public timelineContext input controls test owner binding without mutating private real-controller state; integrated fixtures use public Controller APIs",
        "Synthetic persistent metadata and snapshot DTOs are not real Store saves, accepted receipts or canonical validation",
        "No verifier registration/77-roster change; standalone execution requires separate prospective Root storage admission",
        "At most4 synthetic static HTML files<=256KiB each and this report<=64KiB, no saved bundle/new run directory; previous failed evidence is preserved",
    ],
};
const encoded = JSON.stringify(report);
assert(
    Buffer.byteLength(encoded) + 1 <= 64 * 1024,
    "Bounded64KiBBrowserReviewReport",
);
if (output)
    await writeFile(
        path.join(output, `domain2-timeline-${runId}-report.json`),
        encoded + "\n",
        { flag: "wx" },
    );
console.log(encoded);
process.exitCode = setup.length
    ? 2
    : !results.length || results.some((r) => !r.passed)
      ? 1
      : 0;
