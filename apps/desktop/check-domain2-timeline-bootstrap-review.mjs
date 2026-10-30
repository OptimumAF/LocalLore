// Independent bootstrap FIRST at d21bc019. SOURCE AUTHOR UNCOMPILED / UNRUN.
// Executes the actual journey prefix and actual Controller/strict thin decoder.
// Gateway, oracle, idle and owner observer are disclosed synthetic composition
// controls. No Main mount, native IPC, Rust canon, DOM, timers, RAF or pixels.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash, webcrypto } from "node:crypto";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import vm from "node:vm";

assert.equal(process.argv.length, 2, "ClosedBootstrapReviewArguments");
globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL(".", import.meta.url));
const PARENT = { story: "d05-inspector-native", branch: "main" };
const CHILD = { story: "d05-inspector-native", branch: "paging" };
const OTHER = { story: "d05-inspector-other", branch: "main" };
const clone = (value) => structuredClone(value);
const sha = (value) => createHash("sha256").update(value).digest("hex");
const equalScope = (left, right) =>
    left?.story === right.story && left?.branch === right.branch;
const allowed = new Set([
    "workspace",
    "resume",
    "open",
    "play_snapshot_v2",
    "play_snapshot",
    "close",
]);
const groups = [],
    results = [],
    setup = [],
    sources = {};
let actual, prefix;
const test = (name, run) => groups.push({ name, run });
const ticks = async () => {
    for (let index = 0; index < 40; index++) await Promise.resolve();
};
function deferred() {
    let resolve;
    const promise = new Promise((done) => {
        resolve = done;
    });
    return { promise, resolve };
}
function workspace() {
    return {
        persistent: true,
        location: "synthetic-bootstrap-transport-only",
        schema_version: 1,
        database_schema_version: 5,
        stories: [
            {
                scope: clone(PARENT),
                title: "Fixed synthetic parent",
                revision: 0,
                drafts: 0,
            },
            {
                scope: clone(OTHER),
                title: "Fixed synthetic other",
                revision: 1,
                drafts: 0,
            },
        ],
    };
}
function thin(scope, revision, domain) {
    return {
        version: 2,
        domain_version: domain,
        scope: clone(scope),
        revision,
        rules: "fantasy_v1",
        player: {
            observer: "player",
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
function legacy(scope, revision) {
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
class Gateway {
    playSnapshotV2 = true;
    calls = [];
    events = [];
    starts = 0;
    workspaceValue = workspace();
    workspaceGate = null;
    workspaceError = null;
    startInspectorPagingTrace() {
        this.starts++;
        this.events.push("trace-start");
    }
    async call(command) {
        assert(
            allowed.has(command.op),
            `NoGenerationOrExtraRead:${command.op}`,
        );
        this.calls.push(clone(command));
        this.events.push(`call:${command.op}`);
        if (command.op === "workspace") {
            if (this.workspaceGate) await this.workspaceGate.promise;
            if (this.workspaceError) throw Error(this.workspaceError);
            this.events.push("workspace-resolved");
            return clone(this.workspaceValue);
        }
        assert(
            equalScope(command.scope, CHILD) ||
                equalScope(command.scope, OTHER),
            "NoRootOrRecentFallbackDispatch",
        );
        const child = equalScope(command.scope, CHILD),
            revision = child ? 44 : 1;
        if (command.op === "resume")
            return {
                session: child
                    ? "synthetic-child-session"
                    : "synthetic-other-session",
                scope: clone(command.scope),
                revision,
                drafts: 0,
            };
        if (command.op === "open") return { revision };
        if (command.op === "play_snapshot_v2") {
            assert.equal(command.expected_revision, revision);
            return thin(command.scope, revision, child ? 2 : 1);
        }
        if (command.op === "play_snapshot") {
            assert(!child, "ChildMustNeverUseLegacySnapshotFallback");
            assert.equal(command.expected_revision, 1);
            return legacy(command.scope, 1);
        }
        if (command.op === "close") return {};
        throw Error(`UnexpectedBootstrapRead:${command.op}`);
    }
}
function fixture() {
    const gateway = new Gateway(),
        c = new actual.Controller(gateway);
    let oracleCalls = 0,
        ownerCalls = 0,
        idleCalls = 0;
    const check = (condition, label) => assert(condition, label);
    const dependencies = {
        c,
        gateway,
        check,
        // Immediate composition check: deliberately no actual Main/native wait.
        until: async (predicate, label) => check(predicate(), label),
        oracle: async (label) => {
            assert.equal(label, "before-browser-navigation");
            assert(c.get().workspace, "LibraryMustPrecedeMockOracle");
            gateway.events.push("symbolic-oracle");
            oracleCalls++;
            return { synthetic: true, kind: "bootstrap-symbolic-oracle" };
        },
        idle: async () => {
            idleCalls++;
            assert.equal(c.get().pending, null);
            assert.equal(c.get().starting, false);
        },
        assertOwner: (scope, revision, domain) => {
            ownerCalls++;
            assert.deepEqual(scope, CHILD);
            assert.equal(revision, 44);
            assert.equal(domain, 2);
            const state = c.get(),
                selected = c.selected();
            assert(selected);
            assert.deepEqual(selected.scope, CHILD);
            assert.equal(selected.revision, 44);
            assert.equal(state.play, null);
            assert.equal(state.visibleError, null);
            assert(state.playV2);
            assert.equal(state.playV2.domain_version, 2);
            // Real strict model validates the actual Controller publication.
            assert.deepEqual(
                actual.checkedPlaySnapshotV2(state.playV2, CHILD, 44),
                state.playV2,
            );
            gateway.events.push("checked-controller-owner");
        },
        CHILD,
        PARENT,
        OTHER,
        structural: actual.structural,
    };
    return {
        c,
        gateway,
        run: () =>
            prefix(
                ...Object.keys(dependencies).map((name) => dependencies[name]),
            ),
        counts: () => ({ oracleCalls, ownerCalls, idleCalls }),
        close: () => c.dispose(),
    };
}
function assertSuccess(f, from = 0) {
    assert.deepEqual(
        f.gateway.calls.slice(from).map((command) => command.op),
        ["workspace", "resume", "open", "play_snapshot_v2"],
    );
    assert.deepEqual(f.gateway.calls[from + 1].scope, CHILD);
    assert.equal(f.gateway.starts, 1);
    assert.deepEqual(f.counts(), {
        oracleCalls: 1,
        ownerCalls: 1,
        idleCalls: 1,
    });
    const events = f.gateway.events;
    assert(
        events.lastIndexOf("workspace-resolved") <
            events.lastIndexOf("symbolic-oracle"),
    );
    assert(
        events.lastIndexOf("symbolic-oracle") <
            events.lastIndexOf("call:resume"),
    );
    assert(
        events.lastIndexOf("call:play_snapshot_v2") <
            events.lastIndexOf("checked-controller-owner"),
    );
}
test("empty-Main-state-loads-exact-two-roots-before-explicit-child-resume", async () => {
    const f = fixture();
    try {
        assert.equal(f.c.get().workspace, null);
        assert.equal(f.c.selected(), null);
        await f.run();
        assertSuccess(f);
        assert.deepEqual(
            f.c.get().workspace.stories.map((story) => story.scope),
            [PARENT, OTHER],
        );
    } finally {
        await f.close();
    }
});
test("preexisting-other-selection-cannot-substitute-first-or-recent-scope", async () => {
    const f = fixture();
    try {
        await f.c.library();
        await f.c.resume(OTHER);
        assert.deepEqual(f.c.selected().scope, OTHER);
        assert(f.c.get().play);
        assert.equal(f.c.get().playV2, null);
        const from = f.gateway.calls.length;
        await f.run();
        assertSuccess(f, from);
        assert.deepEqual(f.c.selected().scope, CHILD);
        assert.equal(f.c.get().sessions.length, 2);
    } finally {
        await f.close();
    }
});
test("unavailable-corrupt-or-wrong-two-root-roster-never-resumes-or-runs-oracle", async () => {
    const bad = [
        [
            "unavailable",
            {
                persistent: false,
                location: null,
                schema_version: null,
                stories: [],
            },
        ],
        [
            "missing-other",
            { ...workspace(), stories: workspace().stories.slice(0, 1) },
        ],
        [
            "wrong-other-head",
            {
                ...workspace(),
                stories: workspace().stories.map((story, i) => ({
                    ...story,
                    revision: i ? 2 : 0,
                })),
            },
        ],
        [
            "child-pretends-root",
            {
                ...workspace(),
                stories: [
                    { ...workspace().stories[0], scope: clone(CHILD) },
                    workspace().stories[1],
                ],
            },
        ],
        [
            "extra-root",
            {
                ...workspace(),
                stories: [
                    ...workspace().stories,
                    {
                        ...workspace().stories[0],
                        scope: { story: "unexpected", branch: "main" },
                    },
                ],
            },
        ],
        ["malformed-stories", { ...workspace(), stories: null }],
        ["transport-unavailable", null],
    ];
    for (const [label, value] of bad) {
        const f = fixture();
        f.gateway.workspaceValue = value;
        if (label === "transport-unavailable")
            f.gateway.workspaceError = "Transport";
        try {
            await assert.rejects(f.run(), undefined, label);
            assert.deepEqual(
                f.gateway.calls.map((command) => command.op),
                ["workspace"],
                label,
            );
            assert.equal(f.gateway.starts, 1, label);
            assert.deepEqual(
                f.counts(),
                { oracleCalls: 0, ownerCalls: 0, idleCalls: 0 },
                label,
            );
            assert.equal(f.c.selected(), null, label);
        } finally {
            await f.close();
        }
    }
});
test("pending-library-is-awaited-before-oracle-selection-and-snapshot", async () => {
    const f = fixture(),
        gate = deferred();
    f.gateway.workspaceGate = gate;
    let settled = false;
    const observed = f
        .run()
        .then(
            (value) => ({ value }),
            (error) => ({ error }),
        )
        .then((value) => {
            settled = true;
            return value;
        });
    try {
        await ticks();
        assert.equal(settled, false, "PrefixMustAwaitActualLibraryPromise");
        assert.deepEqual(
            f.gateway.calls.map((command) => command.op),
            ["workspace"],
        );
        assert.equal(f.c.selected(), null);
        assert.equal(f.c.get().workspace, null);
        assert.deepEqual(f.counts(), {
            oracleCalls: 0,
            ownerCalls: 0,
            idleCalls: 0,
        });
        gate.resolve();
        const outcome = await observed;
        if (outcome.error) throw outcome.error;
        assertSuccess(f);
    } finally {
        gate.resolve();
        await observed;
        await f.close();
    }
});

try {
    for (const filename of [
        "ui/controller.ts",
        "ui/model.ts",
        "ui/v2-view-model.ts",
        "ui/domain2-timeline-browser-native-journeys.ts",
    ])
        sources[filename] = sha(
            await readFile(new URL(filename, import.meta.url), "utf8"),
        );
    const journey = await readFile(
        new URL(
            "ui/domain2-timeline-browser-native-journeys.ts",
            import.meta.url,
        ),
        "utf8",
    );
    const start = "\n    try {\n",
        end = "        assertOwner(CHILD, 44, 2);";
    assert.equal(
        journey.split(start).length,
        2,
        "UNRUN_SETUP:UniqueTopLevelJourneyTry",
    );
    const startIndex = journey.indexOf(start) + start.length;
    const endIndex = journey.indexOf(end, startIndex);
    assert(endIndex > startIndex, "UNRUN_SETUP:FirstChildOwnerBoundaryMissing");
    const body = journey.slice(startIndex, endIndex + end.length);
    assert(body.length < 8192, "UNRUN_SETUP:BoundedActualBootstrapPrefix");
    assert(
        !/\bdocument\b|\brequestAnimationFrame\b|\bsetTimeout\b|\bclick\s*\(/.test(
            body,
        ),
        "UNRUN_SETUP:PrefixMustEndBeforeDOM",
    );
    sources.actualBootstrapPrefix = sha(body);
    const bundled = await build({
        stdin: {
            contents:
                'export {Controller} from "./ui/controller";export {checkedPlaySnapshotV2} from "./ui/v2-view-model";export {structural} from "./ui/model";',
            resolveDir: root,
            loader: "ts",
        },
        bundle: true,
        platform: "node",
        format: "cjs",
        write: false,
        logLevel: "silent",
    });
    actual = vm.runInThisContext(
        `(function(){const module={exports:{}};const exports=module.exports;\n${bundled.outputFiles[0].text}\nreturn module.exports;})()`,
        { timeout: 1000, filename: "actual-bootstrap-controller-memory.cjs" },
    );
    assert.equal(typeof actual.Controller, "function");
    assert.equal(typeof actual.checkedPlaySnapshotV2, "function");
    assert.equal(typeof actual.structural, "function");
    const names = [
        "c",
        "gateway",
        "check",
        "until",
        "oracle",
        "idle",
        "assertOwner",
        "CHILD",
        "PARENT",
        "OTHER",
        "structural",
    ];
    prefix = vm.runInThisContext(
        `(async function(${names.join(",")}){let baseline=null;\n${body}\nreturn baseline;})`,
        { timeout: 1000, filename: "actual-bootstrap-prefix-memory.js" },
    );
} catch (error) {
    setup.push({
        classification: "UNRUN_SETUP",
        error: String(error).slice(0, 2048),
    });
}
if (!setup.length)
    for (const group of groups) {
        try {
            await group.run();
            results.push({ name: group.name, status: "PASS" });
        } catch (error) {
            results.push({
                name: group.name,
                status: "FAIL",
                error: String(error).slice(0, 2048),
            });
        }
    }
const report = {
    kind: "domain2_timeline_bootstrap_prefix_review_v1",
    sourceOnlyAuthorFreeze: true,
    authoredGroups: groups.length,
    invalidRosterVariants: 7,
    executed: results.length,
    passed: results.filter((result) => result.status === "PASS").length,
    failed: results.filter((result) => result.status === "FAIL").length,
    setup,
    sources,
    results,
    evidence: {
        actualController: true,
        actualStrictModel: true,
        actualJourneyPrefix: true,
        syntheticGateway: true,
        symbolicOracle: true,
        stubbedIdleAndOwnerObserver: true,
        nativeIpc: false,
        rustCanonicalValidation: false,
        mainMount: false,
        dom: false,
        timers: false,
        rendering: false,
    },
};
const output = JSON.stringify(report) + "\n";
assert(
    Buffer.byteLength(output, "utf8") <= 65536,
    "BootstrapReviewOutputBudget",
);
process.stdout.write(output);
if (setup.length || report.failed) process.exitCode = 1;
