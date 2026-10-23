// MOCK Gateway, actual timeline decoder/controller + gameplay Controller and
// inert React semantic rendering. No app, native fixture, model or device run.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { randomUUID, createHash } from "node:crypto";
const directory =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("artifacts/checks/", import.meta.url));
await mkdir(directory, { recursive: true });
const compiled = await build({
    stdin: {
        contents:
            'export { TimelineController, timelineContext, resumeTimeline } from "./ui/timeline-controller"; export { decodeBranchCatalog } from "./ui/timeline-model"; export { TimelinePanel } from "./ui/TimelinePanel"; export { Controller } from "./ui/controller"; export { playView } from "./ui/model"; export { createElement } from "react"; export { renderToStaticMarkup } from "react-dom/server";',
        resolveDir: fileURLToPath(new URL(".", import.meta.url)),
        loader: "ts",
    },
    banner: {
        js: 'import { createRequire } from "node:module"; const require = createRequire(import.meta.url);',
    },
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
    jsx: "automatic",
});
const target = path.join(directory, `timeline-controller-${randomUUID()}.mjs`);
await writeFile(target, compiled.outputFiles[0].contents);
const {
    TimelineController,
    timelineContext,
    resumeTimeline,
    decodeBranchCatalog,
    TimelinePanel,
    Controller,
    playView,
    createElement,
    renderToStaticMarkup,
} = await import(pathToFileURL(target).href);
const checks = [];
function check(value, label) {
    assert(value, label);
    checks.push(label);
}
const scope = (branch, story = "timeline-synthetic") => ({ story, branch });
const context = (v = {}) => ({
    session: "root-session",
    scope: scope("main"),
    revision: 4,
    view: "play",
    observer: "player",
    persistent: true,
    ...v,
});
const row = (branch, parent, fork, revision, retired = false) => ({
    scope: scope(branch),
    parent_branch: parent,
    fork_revision: fork,
    revision,
    drafts: 0,
    retired,
});
const catalog = () => ({
    version: 2,
    story_id: "timeline-synthetic",
    title: "Synthetic <script>CANARY</script> 模型",
    root_branch: "main",
    branches: [
        row("child", "parent", 3, 3),
        row("main", null, null, 4),
        row("parent", "main", 2, 3, true),
        row("sibling", "main", 1, 1),
    ],
});
const gate = () => {
    let release, reject;
    const waiting = new Promise((yes, no) => {
        release = yes;
        reject = no;
    });
    return { waiting, release, reject };
};
const receipt = (original, revision, eventScope = original) => ({
    version: 1,
    request: {
        version: 1,
        scope: original,
        turn: `turn-${revision}`,
        expected_revision: revision - 1,
        intent: { kind: "actions", value: [{ op: "wait", ticks: 1 }] },
    },
    proposal: {},
    events: [
        {
            sequence: revision,
            scope: eventScope,
            turn: `turn-${revision}`,
            outcome: {},
        },
    ],
    narration: "Original accepted wait.",
});
const play = (s, revision, receipts = []) => ({
    scope: s,
    revision,
    inventory: {},
    receipts,
    player: {
        scope: s,
        revision,
        observer: "player",
        self_state: { name: "Rowan", location: "quay", energy: 2 },
        facts: {},
        beliefs: [],
        observations: [],
    },
});
async function actualChildResume() {
    const calls = [];
    const gateway = {
        async call(q) {
            calls.push(q);
            if (q.op === "resume")
                return {
                    session: "child-session",
                    scope: q.scope,
                    revision: 2,
                };
            if (q.op === "open")
                return { revision: q.scope.branch === "main" ? 1 : 2 };
            if (q.op === "play_snapshot")
                return play(
                    q.scope,
                    q.scope.branch === "main" ? 1 : 2,
                    q.scope.branch === "main"
                        ? [receipt(scope("main"), 1)]
                        : [
                              receipt(scope("main"), 1),
                              receipt(scope("child"), 2),
                          ],
                );
            if (q.op === "close") return {};
            throw Error(`Unexpected ${q.op}`);
        },
    };
    const c = new Controller(gateway);
    await c.attach({
        id: "root-session",
        scope: scope("main"),
        name: "Root",
        revision: 1,
    });
    check(c.get().play?.revision === 1, "actual-gameplay-root-control");
    await resumeTimeline(c, scope("child"));
    check(
        c.selected()?.scope.branch === "child" && c.get().play?.revision === 2,
        "actual-gameplay-child-resume",
    );
    check(
        c.get().play.receipts[0].request.scope.branch === "main" &&
            c.get().play.receipts[0].events[0].scope.branch === "main",
        "actual-gameplay-original-scopes-retained",
    );
    check(
        calls.filter((q) => q.op === "resume").length === 1 &&
            !calls.some((q) =>
                ["submit", "prepare", "commit", "grant_lab"].includes(q.op),
            ),
        "existing-resume-only-no-generation-or-grant",
    );
}
if (process.argv.includes("--child-resume-repro")) {
    await actualChildResume();
    console.log(
        "PASS: actual Controller child resume retains original inherited scopes (MOCK native gateway).",
    );
    process.exit(0);
}
const decoded = decodeBranchCatalog(catalog(), "timeline-synthetic");
check(
    decoded.branches.length === 4 && decoded.branches[2].retired,
    "retired-parent-metadata-retained",
);
check(
    Object.isFrozen(decoded) &&
        Object.isFrozen(decoded.branches) &&
        Object.isFrozen(decoded.branches[0].scope),
    "decoded-selection-data-is-immutable",
);
const rejects = (mutate, label) => {
    const data = catalog();
    mutate(data);
    assert.throws(() => decodeBranchCatalog(data, "timeline-synthetic"));
    checks.push(label);
};
for (const [label, mutate] of [
    ["version", (v) => (v.version = 1)],
    ["foreign-story", (v) => (v.story_id = "foreign")],
    ["foreign-row", (v) => (v.branches[0].scope.story = "foreign")],
    ["extra-content", (v) => (v.hidden_canon = "SECRET")],
    ["unknown-row-field", (v) => (v.branches[0].knowledge = "SECRET")],
    ["unknown-scope-field", (v) => (v.branches[0].scope.private = true)],
    ["unsafe-id", (v) => (v.branches[0].scope.branch = "../outside")],
    ["duplicate-row", (v) => v.branches.push(v.branches[0])],
    ["unsafe-revision", (v) => (v.branches[0].revision = 2 ** 53)],
    ["negative-drafts", (v) => (v.branches[0].drafts = -1)],
    ["fractional-fork", (v) => (v.branches[0].fork_revision = 1.5)],
    ["nonboolean-retired", (v) => (v.branches[0].retired = "false")],
    ["root-parent", (v) => (v.branches[1].parent_branch = "parent")],
    ["missing-root", (v) => (v.root_branch = "absent")],
    ["missing-parent", (v) => (v.branches[0].parent_branch = "absent")],
    ["cycle", (v) => (v.branches[2].parent_branch = "child")],
    [
        "future-parent-fork",
        (v) => {
            v.branches[0].fork_revision = 4;
            v.branches[0].revision = 4;
        },
    ],
    ["future-own-fork", (v) => (v.branches[0].fork_revision = 4)],
    ["title-nul", (v) => (v.title = "bad\0title")],
    ["title-cap", (v) => (v.title = "字".repeat(257))],
    [
        "row-cap",
        (v) =>
            (v.branches = Array.from({ length: 257 }, (_, i) =>
                row(`branch-${i}`, "main", 0, 0),
            )),
    ],
])
    rejects(mutate, `decoder-reject-${label}`);
const depth = { ...catalog(), branches: [row("main", null, null, 100)] };
for (let i = 1; i < 32; i++)
    depth.branches.push(
        row(`nested-${i}`, i === 1 ? "main" : `nested-${i - 1}`, 0, 100),
    );
check(
    decodeBranchCatalog(depth, "timeline-synthetic").branches.length === 32,
    "shared-depth32-accepted",
);
depth.branches.push(row("nested-32", "nested-31", 0, 100));
assert.throws(() => decodeBranchCatalog(depth, "timeline-synthetic"));
checks.push("depth33-rejected");
const unicode = catalog();
unicode.title = "😀".repeat(256);
check(
    decodeBranchCatalog(unicode, "timeline-synthetic").title === unicode.title,
    "shared-title256-unicode-codepoints-accepted",
);
const prebirth = catalog();
prebirth.branches[2] = row("parent", "main", 4, 4, true);
prebirth.branches[0] = row("child", "parent", 1, 1);
check(
    decodeBranchCatalog(prebirth, "timeline-synthetic").branches[0]
        .fork_revision === 1,
    "nested-prebirth-fork-not-rejected",
);
let calls = [],
    selections = [];
const gateway = {
    async call(q) {
        calls.push(q);
        return catalog();
    },
};
const t = new TimelineController(gateway, async (s) => {
    selections.push(s);
});
t.contextChanged(context());
await t.show();
check(
    t.get().status === "ready" &&
        calls[0].op === "branches" &&
        calls[0].story === "timeline-synthetic",
    "real-command-shape-catalog-only",
);
await t.select("parent");
await t.select("absent");
await t.select("main");
check(selections.length === 0, "retired-absent-current-no-selection");
await t.select("child");
check(
    selections.length === 1 && selections[0].branch === "child",
    "active-child-delegated-exact-scope",
);
let markup = renderToStaticMarkup(
    createElement(TimelinePanel, { timeline: t, context: context() }),
);
check(
    markup.includes("&lt;script&gt;CANARY&lt;/script&gt;") &&
        !markup.includes("<script>"),
    "inert-title-escaped",
);
check(
    markup.includes("at accepted revision 3") &&
        markup.includes("retained ancestry only") &&
        markup.includes('aria-label="Saved timeline metadata"'),
    "semantic-original-fork-and-retired-labels",
);
check(
    /disabled=""[^>]*>Retired timeline parent/.test(markup),
    "retired-resume-control-disabled",
);
check(
    !markup.includes(">Fork timeline<") &&
        markup.includes("are unavailable in this view"),
    "no-unimplemented-author-controls",
);
for (const [label, changed] of [
    ["story", { scope: scope("main", "other-story") }],
    ["branch", { scope: scope("sibling") }],
    ["session", { session: "reopened" }],
    ["head", { revision: 5 }],
    ["view", { view: "lab" }],
    ["observer", { observer: "mira" }],
    ["persistence", { persistent: false }],
]) {
    const held = gate();
    const x = new TimelineController({ call: () => held.waiting }, async () => {
        throw Error("No selection expected");
    });
    x.contextChanged(context());
    const pending = x.show();
    x.contextChanged(context(changed));
    held.release(catalog());
    await pending;
    check(
        x.get().catalog === null &&
            !x.get().shown &&
            !x.get().busy &&
            x.get().error === null,
        `late-catalog-fenced-${label}`,
    );
}
{
    const held = gate(),
        x = new TimelineController(
            { call: () => held.waiting },
            async () => {},
        );
    x.contextChanged(context());
    const pending = x.show();
    x.contextChanged(context({ session: "B" }));
    x.contextChanged(context());
    held.reject(Error("PRIVATE_LATE_ERROR"));
    await pending;
    check(
        x.get().catalog === null && x.get().error === null,
        "A-B-A-does-not-revive-old-reply",
    );
}
{
    const a = gate(),
        b = gate();
    let n = 0;
    const x = new TimelineController(
        { call: () => (++n === 1 ? a.waiting : b.waiting) },
        async () => {},
    );
    x.contextChanged(context());
    const first = x.show(),
        second = x.refresh();
    const latest = catalog();
    latest.title = "Newest";
    b.release(latest);
    await second;
    a.release({ version: 999 });
    await first;
    check(
        x.get().catalog.title === "Newest" && x.get().error === null,
        "newest-read-wins-old-malformed-reply-ignored",
    );
}
for (const action of ["hide", "dispose"]) {
    const held = gate(),
        x = new TimelineController(
            { call: () => held.waiting },
            async () => {},
        );
    x.contextChanged(context());
    const pending = x.show();
    x[action]();
    held.release(catalog());
    await pending;
    check(
        !x.get().shown && x.get().catalog === null && !x.get().busy,
        `late-read-after-${action}-ignored`,
    );
}
{
    let n = 0;
    const x = new TimelineController(
        {
            call: async () => {
                n++;
                throw Error("MustNotCall");
            },
        },
        async () => {},
    );
    await x.show();
    check(
        x.get().status === "unavailable" && n === 0,
        "no-story-honest-unavailable",
    );
    x.contextChanged(context({ persistent: false }));
    await x.show();
    check(
        x.get().status === "unsupported" && n === 0,
        "memory-session-no-storage-fallback",
    );
}
for (const error of [
    "Unsupported",
    "Busy",
    "Integrity",
    "PRIVATE_DATABASE_PATH",
]) {
    const x = new TimelineController(
        {
            call: async () => {
                throw Error(error);
            },
        },
        async () => {},
    );
    x.contextChanged(context());
    await x.show();
    check(
        x.get().catalog === null &&
            !x.get().busy &&
            x.get().error != "PRIVATE_DATABASE_PATH",
        `bounded-error-${error}`,
    );
    if (error === "Unsupported")
        check(
            x.get().status === "unsupported",
            "native-unsupported-no-synthetic-catalog",
        );
}
{
    const x = new TimelineController(
        { call: async () => ({ ...catalog(), branches: [] }) },
        async () => {},
    );
    x.contextChanged(context());
    await x.show();
    check(
        x.get().status === "empty" && x.get().catalog.branches.length === 0,
        "empty-catalog-honest",
    );
}
{
    const held = gate();
    const x = new TimelineController(gateway, () => held.waiting);
    x.contextChanged(context());
    await x.show();
    const select = x.select("child");
    check(x.get().busy, "selection-busy");
    x.contextChanged(context({ session: "new-native-session" }));
    await x.show();
    held.reject(Error("PRIVATE_OLD_SELECTION"));
    await select;
    check(
        x.get().status === "ready" &&
            x.get().error === null &&
            !x.get().notice.includes("Selection completed"),
        "old-selection-cannot-label-new-session",
    );
}
{
    const x = new TimelineController(gateway, async () => {
        throw Error("SessionLimit");
    });
    x.contextChanged(context());
    await x.show();
    await x.select("child");
    check(
        x.get().error === "SessionLimit" && !x.get().busy,
        "resume-limit-honest-error",
    );
    const html = renderToStaticMarkup(
        createElement(TimelinePanel, {
            timeline: x,
            context: context({ observer: "mira" }),
        }),
    );
    check(html === "", "panel-refuses-mismatched-context-before-render");
}
for (const [label, mutate] of [
    ["cross-story", (r) => (r.request.scope = scope("main", "foreign"))],
    [
        "event-request-scope-disagreement",
        (r) => (r.events[0].scope = scope("sibling")),
    ],
    ["future-event", (r) => (r.events[0].sequence = 3)],
]) {
    const r = receipt(scope("main"), 1);
    mutate(r);
    assert.throws(() =>
        playView(play(scope("child"), 2, [r]), scope("child"), 2),
    );
    checks.push(`gameplay-reject-${label}`);
}
await actualChildResume();
const snapshot = play(scope("child"), 2, [
    receipt(scope("main"), 1),
    receipt(scope("child"), 2),
]);
await resumeTimeline(
    {
        get: () => ({ visibleError: "OldUnrelatedError", play: snapshot }),
        selected: () => ({ scope: scope("child"), revision: 2 }),
        resume: async () => {},
    },
    scope("child"),
);
checks.push("successful-target-snapshot-not-mislabeled-by-old-error");
const report = {
    lane: "MOCK gateway + actual controllers/decoder + inert React",
    passed: true,
    checks,
    bundle_sha256: createHash("sha256")
        .update(compiled.outputFiles[0].contents)
        .digest("hex"),
    native_app: false,
};
await writeFile(
    path.join(directory, "timeline-controller-report.json"),
    JSON.stringify(report, null, 2),
);
console.log(
    `PASS: ${checks.length} timeline controller/decoder/semantic checks (MOCK, no native application).`,
);
