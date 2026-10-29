// Deterministic PROCESS-POLICY simulation only. No OS child, app, native IPC,
// model, approved asset, build, desktop capture/control or timer wait is used.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { EventEmitter } from "node:events";
import { PassThrough } from "node:stream";
import { runInNewContext } from "node:vm";
import path from "node:path";

process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
assert.equal(process.argv.length, 2, "ClosedPolicyCheckArguments");
const source = await readFile(
    new URL("./comparison-run-harness.mjs", import.meta.url),
    "utf8",
);
const between = (start, end) => {
    const first = source.indexOf(start),
        last = source.indexOf(end, first + start.length);
    assert(
        first >= 0 &&
            last > first &&
            source.indexOf(start, first + start.length) === -1,
        "UniqueSourceBlock",
    );
    return source.slice(first, last);
};
const policySource = between(
    "function createSceneChildPolicy(",
    "// END SCENE CHILD POLICY.",
);
const gitSource = between("const git = async", "const revision = await git");
const unchangedSource = between(
    "async function sourceUnchanged()",
    "async function saveExecutions()",
);
const runSource = between(
    "async function runScene(",
    "async function boundedFile(",
);
const restoreSource = between(
    "    // BEGIN SCENE RESTORATION POLICY:",
    "    // END SCENE RESTORATION POLICY.",
);
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
const createPolicy = runInNewContext(`(${policySource.trim()})`, { Buffer });
const checks = [];
// Additive SOURCE-ONLY freeze at 5145c5fa. Missing proposed pure helper blocks
// are setup gaps, not behavioral RED. Original sixteen policy cases stay below.
const boundaryChecks = [],
    boundarySetupFailures = [];
let storageHelpers = null,
    storageHelperSource = null;
try {
    storageHelperSource = between(
        "// BEGIN SCENE STORAGE/ENVIRONMENT HELPERS.",
        "// END SCENE STORAGE/ENVIRONMENT HELPERS.",
    );
    storageHelpers = runInNewContext(
        `(() => { "use strict";
        ${storageHelperSource}
        return { sceneStorageDisjoint, sceneReviewEnvironment };
    })()`,
        { path: path.win32 },
    );
    for (const key of ["sceneStorageDisjoint", "sceneReviewEnvironment"])
        assert.equal(
            typeof storageHelpers[key],
            "function",
            `ProposedPureHelper:${key}`,
        );
} catch (error) {
    boundarySetupFailures.push({
        stage: "pure-helper-source",
        error: String(error?.message ?? error).slice(0, 500),
    });
}
// First freeze at 38d1c908 for the existing retained-packet ancestry helper.
// No new API and no filesystem probe: exact function source plus path strings.
const ancestryObservations = [];
const syntheticReviewRoot = "D:/synthetic-boundary/retained-packet";
let ancestrySource = null, outsideReviewCheck = null;
try {
    ancestrySource = between("function outsideReviewPacket(", "async function absent(");
    outsideReviewCheck = runInNewContext(`(${ancestrySource.trim()})`, {
        assert, path: path.win32, reviewPacketRoot: syntheticReviewRoot,
    });
    assert.equal(typeof outsideReviewCheck, "function");
} catch (error) {
    boundarySetupFailures.push({ stage: "existing-packet-ancestry-source", error: String(error?.message ?? error).slice(0, 500) });
}
const flush = async () => {
    for (let count = 0; count < 20; count++) await Promise.resolve();
};
class FakeChild extends EventEmitter {
    constructor(pid = 41) {
        super();
        this.pid = pid;
        this.stdout = new PassThrough();
        this.stderr = new PassThrough();
        this.killCalls = 0;
        this.unrefCalls = 0;
        this.killResult = true;
        this.onKill = null;
    }
    kill() {
        this.killCalls++;
        if (this.onKill) this.onKill();
        return this.killResult;
    }
    unref() {
        this.unrefCalls++;
    }
    close(exit = 0, signal = null) {
        this.emit("close", exit, signal);
    }
}
function fixture({ noPid = false, throws = false, automatic = false } = {}) {
    let elapsed = 0,
        nextId = 0;
    const timers = new Map(),
        children = [],
        launches = [];
    const setTimer = (callback, ms) => {
        const id = ++nextId;
        timers.set(id, { due: elapsed + ms, callback });
        return id;
    };
    const clearTimer = (id) => timers.delete(id);
    const tick = (ms) => {
        const until = elapsed + ms;
        for (;;) {
            const next = [...timers.entries()]
                .filter(([, timer]) => timer.due <= until)
                .sort((a, b) => a[1].due - b[1].due)[0];
            if (!next) break;
            elapsed = next[1].due;
            timers.delete(next[0]);
            next[1].callback();
        }
        elapsed = until;
    };
    const policy = createPolicy({
        sha256,
        setTimer,
        clearTimer,
        now: () => `simulated-${elapsed}`,
        spawnChild: (command, args, options) => {
            launches.push({ command, args, options });
            if (throws)
                throw Object.assign(Error("fixed missing executable"), {
                    code: "ENOENT",
                });
            const child = new FakeChild(
                noPid ? undefined : 41 + children.length,
            );
            if (noPid) child.pid = undefined;
            children.push(child);
            if (automatic)
                queueMicrotask(() => {
                    if (
                        command === "git" &&
                        args.join(" ") === "rev-parse HEAD"
                    )
                        child.stdout.write("revision\n");
                    child.close();
                });
            return child;
        },
    });
    return { policy, children, launches, tick, timers };
}
function integration(f, sceneMode = true, inheritedEnvironment = {}) {
    const writes = [],
        snapshots = [],
        legacy = [],
        executions = [];
    const context = {
        assert,
        Buffer,
        path,
        process: { env: { ...inheritedEnvironment } },
        sceneReviewEnvironment: storageHelpers?.sceneReviewEnvironment,
        sceneMode,
        scenePolicy: f.policy,
        root: "D:/synthetic-policy/desktop",
        folder: "D:/synthetic-policy/packet",
        executable: "fixed-app.exe",
        revision: "revision",
        sceneSourceHashes: null,
        sceneHarnessProducts: null,
        writeFile: async (...args) => {
            writes.push(args);
        },
        saveSceneProcessEvidence: async () => {
            snapshots.push(
                JSON.parse(
                    JSON.stringify({
                        unknown: f.policy.unknownDrain,
                        records: f.policy.records,
                        unknownChildren: f.policy.unknownChildren,
                    }),
                ),
            );
        },
        sceneProducts: async () => ({}),
        saveExecutions: async () => {},
        executions,
        execFile: "legacy-sentinel",
        promisify:
            (fn) =>
            async (...args) => {
                assert.equal(fn, "legacy-sentinel");
                legacy.push(args);
                return { stdout: " legacy output \n" };
            },
    };
    const controls = runInNewContext(
        `(() => { let sceneRestoration = null, failure = null;
        ${gitSource}\n${unchangedSource}\n${runSource}
        return { git, sourceUnchanged, runScene, restore: async () => {
            const run = runScene;
            ${restoreSource}
            return { sceneRestoration, failure };
        } };
    })()`,
        context,
    );
    return { ...controls, writes, snapshots, legacy, executions };
}
async function blocked(policy, f) {
    const count = f.launches.length;
    for (const label of [
        "git-after",
        "app-after",
        "normal-frontend-restoration",
        "normal-native-restoration",
    ])
        await assert.rejects(
            policy.run(label, "fixed", [], {}, 1),
            /SceneOwnedDrainUnknown/,
        );
    assert.equal(f.launches.length, count, "ZeroLaterLaunches");
}
async function test(name, action) {
    await action();
    checks.push(name);
}

await test("early-policy-and-D-packet-before-first-Git", async () => {
    assert(
        source.indexOf("const scenePolicy =") <
            source.indexOf("const revision = await git"),
    );
    assert(
        source.indexOf("scenePacketFolder = path.join") <
            source.indexOf("const revision = await git"),
    );
    assert(
        !/\bgit\s*\(|sourceUnchanged\s*\(/.test(policySource),
        "NonrecursivePrimitive",
    );
    assert(
        gitSource.includes("scenePolicy.run") &&
            runSource.includes("scenePolicy.run"),
    );
    assert(
        source.includes("if (!sceneMode || !scenePolicy.unknownDrain)"),
        "TerminalGitInspectionBarrier",
    );
});
await test("known-close-retains-bounded-output-and-allows-next-child", async () => {
    const f = fixture(),
        work = f.policy.run("git", "git", [], {}, 15000);
    f.children[0].stdout.write("known\n");
    f.children[0].close();
    const result = await work;
    assert.equal(result.stdout.toString(), "known\n");
    assert.equal(result.record.closed, true);
    assert.equal(result.record.stdoutSha256, sha256(Buffer.from("known\n")));
    assert.equal(f.policy.unknownDrain, false);
    assert.equal(f.timers.size, 0);
    const next = f.policy.run("next", "fixed", [], {}, 15000);
    f.children[1].close(7);
    assert.equal((await next).record.exit, 7);
    assert.equal(f.policy.unknownDrain, false);
});
await test("spawn-error-without-PID-is-recorded-without-invented-owner", async () => {
    const f = fixture({ noPid: true }),
        work = f.policy.run("git", "git", [], {}, 15000);
    f.children[0].emit(
        "error",
        Object.assign(Error("missing"), { code: "ENOENT" }),
    );
    const { record } = await work;
    assert.equal(record.pid, null);
    assert.equal(record.spawnError, "ENOENT");
    assert.equal(record.closed, false);
    assert.equal(f.children[0].killCalls, 0);
    assert.equal(f.policy.unknownDrain, false);
    assert.equal(f.timers.size, 0);
});
await test("synchronous-spawn-failure-has-no-owned-PID", async () => {
    const f = fixture({ throws: true }),
        { record } = await f.policy.run("git", "git", [], {}, 15000);
    assert.equal(record.spawnError, "ENOENT");
    assert.equal(record.pid, null);
    assert.equal(f.policy.records.length, 1);
    assert.equal(f.policy.unknownDrain, false);
});
await test("Git-timeout-close-after-kill-never-resets-unknown", async () => {
    const f = fixture(),
        i = integration(f),
        work = i.git("status", "--porcelain");
    f.children[0].onKill = () => f.children[0].close(0);
    f.tick(15000);
    await assert.rejects(work, /SceneOwnedDrainUnknown/);
    assert.equal(f.children[0].killCalls, 1);
    assert.equal(f.policy.records[0].closed, true);
    assert.equal(f.policy.unknownChildren[0].pid, 41);
    assert.equal(f.policy.unknownChildren[0].reason, "DirectChildTimeout");
    assert.equal(i.snapshots[0].unknown, true);
    assert.equal(i.snapshots[0].records[0].timedOut, true);
    await blocked(f.policy, f);
});
await test("no-close-waits-exact-five-second-simulated-grace-then-detaches", async () => {
    const f = fixture(),
        work = f.policy.run("git", "git", [], {}, 15000);
    let settled = false;
    work.then(() => {
        settled = true;
    });
    f.tick(15000);
    await flush();
    assert.equal(settled, false);
    f.tick(4999);
    await flush();
    assert.equal(settled, false);
    f.tick(1);
    const { record } = await work;
    assert.equal(record.closed, false);
    assert.equal(record.spawnError, "OwnedDrainUnknown");
    assert.equal(f.children[0].killCalls, 1);
    assert.equal(f.children[0].unrefCalls, 1);
    assert.equal(f.children[0].stdout.destroyed, true);
    assert.equal(f.children[0].stderr.destroyed, true);
    await blocked(f.policy, f);
});
await test("error-with-PID-is-permanent-and-preserves-error-after-close", async () => {
    const f = fixture(),
        work = f.policy.run("git", "git", [], {}, 15000);
    f.children[0].onKill = () => f.children[0].close(1);
    f.children[0].emit(
        "error",
        Object.assign(Error("owned failure"), { code: "EIO" }),
    );
    const { record } = await work;
    assert.equal(record.spawnError, "EIO");
    assert.equal(record.closed, true);
    assert.equal(f.children[0].killCalls, 1);
    assert.equal(f.policy.unknownChildren[0].reason, "ErrorWithPid");
    await blocked(f.policy, f);
});
await test("repeated-error-and-timeout-events-use-only-one-kill-and-grace", async () => {
    const f = fixture(),
        work = f.policy.run("git", "git", [], {}, 15000);
    f.children[0].emit("error", Object.assign(Error("first"), { code: "EIO" }));
    f.children[0].emit(
        "error",
        Object.assign(Error("second"), { code: "EACCES" }),
    );
    f.tick(5000);
    const { record } = await work;
    assert.equal(record.spawnError, "EIO");
    assert.equal(f.children[0].killCalls, 1);
    assert.equal(f.policy.unknownChildren.length, 1);
    assert.equal(f.timers.size, 0);
    f.children[0].emit("error", Error("late ignored error"));
    await blocked(f.policy, f);
});
for (const channel of ["stdout", "stderr"])
    await test(`${channel}-overflow-is-bounded-and-blocks-later-children`, async () => {
        const f = fixture(),
            work = f.policy.run("git", "git", [], {}, 15000);
        f.children[0].onKill = () => f.children[0].close(1);
        f.children[0][channel].write(Buffer.alloc(1024 * 1024 + 1, 120));
        const result = await work;
        assert.equal(result[channel].length, 1024 * 1024);
        assert.equal(result.record.overflow, true);
        assert.equal(
            result.record[
                channel === "stdout"
                    ? "observedStdoutBytes"
                    : "observedStderrBytes"
            ],
            1024 * 1024 + 1,
        );
        assert.equal(f.children[0].killCalls, 1);
        await blocked(f.policy, f);
    });
await test("kill-false-and-kill-throw-remain-unknown-after-late-close", async () => {
    for (const throws of [false, true]) {
        const f = fixture(),
            work = f.policy.run("git", "git", [], {}, 15000);
        f.children[0].killResult = false;
        if (throws)
            f.children[0].onKill = () => {
                throw Object.assign(Error("denied"), { code: "EACCES" });
            };
        f.tick(15000);
        f.children[0].close(0);
        const { record } = await work;
        assert.equal(record.killReturned, throws ? null : false);
        assert.equal(record.killError, throws ? "EACCES" : null);
        assert.equal(f.children[0].killCalls, 1);
        await blocked(f.policy, f);
    }
});
await test("sourceUnchanged-Git-error-blocks-app-and-exact-finally-restoration", async () => {
    const f = fixture(),
        i = integration(f),
        work = i.runScene("app-initial", "fixed-app.exe", []);
    f.children[0].onKill = () => f.children[0].close(1);
    f.children[0].emit(
        "error",
        Object.assign(Error("source Git unknown"), { code: "EIO" }),
    );
    await assert.rejects(work, /SceneOwnedDrainUnknown/);
    const restored = await i.restore();
    assert.equal(restored.sceneRestoration.skipped, true);
    assert.equal(restored.sceneRestoration.launched, false);
    assert.equal(restored.sceneRestoration.reason, "SceneOwnedDrainUnknown");
    assert.equal(f.launches.length, 1);
    assert.equal(f.launches[0].command, "git");
    await assert.rejects(i.git("rev-parse", "HEAD"), /SceneOwnedDrainUnknown/);
    assert.equal(f.launches.length, 1);
    assert.equal(i.snapshots[0].unknownChildren[0].pid, 41);
});
await test("second-source-Git-timeout-blocks-app-after-successful-HEAD", async () => {
    const f = fixture(),
        i = integration(f),
        work = i.runScene("app-initial", "fixed-app.exe", []);
    f.children[0].stdout.write("revision\n");
    f.children[0].close();
    await flush();
    assert.equal(f.launches.length, 2);
    assert.equal(f.launches[1].args.join(" "), "status --porcelain");
    f.children[1].onKill = () => f.children[1].close(0);
    f.tick(15000);
    await assert.rejects(work, /SceneOwnedDrainUnknown/);
    assert.equal((await i.restore()).sceneRestoration.skipped, true);
    assert.equal(f.launches.length, 2);
});
await test("Git-failure-during-restoration-blocks-second-restore-and-later-Git", async () => {
    const f = fixture(),
        i = integration(f),
        restoring = i.restore();
    f.children[0].onKill = () => f.children[0].close(0);
    f.tick(15000);
    const result = await restoring;
    assert.equal(result.sceneRestoration.passed, false);
    assert.equal(result.sceneRestoration.ownedDrainUnknown, true);
    assert.equal(result.sceneRestoration.launched, false);
    assert.match(result.failure.message, /SceneOwnedDrainUnknown/);
    assert.equal(f.launches.length, 1);
    await blocked(f.policy, f);
});
await test("successful-source-guards-and-build-child-do-not-recurse", async () => {
    const f = fixture({ automatic: true }),
        i = integration(f);
    await i.runScene("small-simulated-build", "fixed-build", []);
    assert.equal(f.launches.length, 5);
    assert.equal(
        f.launches.filter((entry) => entry.command === "git").length,
        4,
    );
    assert.equal(f.policy.unknownDrain, false);
    assert.equal(i.executions.length, 1);
    assert(f.launches.every((entry) => entry.options.shell === false));
    assert(
        f.launches.every(
            (entry) =>
                entry.options.env.TEMP === "D:/Dev/_Temp" &&
                entry.options.env.TMP === "D:/Dev/_Temp",
        ),
    );
});
await test("legacy-Git-retains-original-execFile-path-and-options", async () => {
    const f = fixture(),
        i = integration(f, false);
    assert.equal(await i.git("rev-parse", "HEAD"), "legacy output");
    assert.equal(f.launches.length, 0);
    assert.equal(i.legacy.length, 1);
    assert.equal(i.legacy[0][0], "git");
    assert.equal(i.legacy[0][2].timeout, 15000);
    assert.equal(i.legacy[0][2].maxBuffer, 1024 * 1024);
    assert.equal(i.legacy[0][2].shell, false);
});
async function boundaryTest(name, action) {
    if (!storageHelpers || boundarySetupFailures.length) return;
    try {
        await action();
        boundaryChecks.push({ name, passed: true });
    } catch (error) {
        boundaryChecks.push({
            name,
            passed: false,
            error: String(error?.message ?? error).slice(0, 500),
        });
    }
}
const plain = (value) => JSON.parse(JSON.stringify(value));
await boundaryTest(
    "storage-disjointness-is-bidirectional-normalized-and-does-not-need-existing-output",
    () => {
        const cases = [
            [
                "D:/synthetic-boundary/publication",
                "D:/synthetic-boundary/publication",
                false,
            ],
            [
                "D:/synthetic-boundary/publication",
                "d:\\SYNTHETIC-BOUNDARY\\PUBLICATION",
                false,
            ],
            [
                "D:/synthetic-boundary/publication",
                "D:/synthetic-boundary/publication/future-packet",
                false,
            ],
            [
                "D:/synthetic-boundary/output",
                "D:/synthetic-boundary/output/publication",
                false,
            ],
            [
                "D:/synthetic-boundary/publication",
                "d:\\SYNTHETIC-BOUNDARY\\PUBLICATION\\future-packet\\review",
                false,
            ],
            [
                "D:/synthetic-boundary/publication",
                "D:/synthetic-boundary/publication/prospective/nonexistent/webview-profile",
                false,
            ],
            [
                "D:/synthetic-boundary/publication",
                "D:/synthetic-boundary/output",
                true,
            ],
            [
                "D:/synthetic-boundary/publication",
                "D:/synthetic-boundary/publication-output",
                true,
            ],
            [
                "D:/synthetic-boundary/publication",
                "D:/synthetic-boundary/publication/../output",
                true,
            ],
        ];
        for (const [left, right, expected] of cases) {
            assert.equal(
                storageHelpers.sceneStorageDisjoint(left, right),
                expected,
                `forward:${left}:${right}`,
            );
            assert.equal(
                storageHelpers.sceneStorageDisjoint(right, left),
                expected,
                `reverse:${right}:${left}`,
            );
        }
    },
);
await boundaryTest(
    "review-environment-copies-without-any-case-insensitive-LOCALLORE-prefix",
    () => {
        const input = Object.freeze({
            PATH: "synthetic-tools",
            TEMP: "D:/Dev/_Temp",
            TMP: "D:/Dev/_Temp",
            LOCALLORE_D02_HARNESS: "1",
            locallore_m07_memory_harness: "1",
            LoCaLlOrE_M07_LeGaCy_HaRnEsS: "1",
            locallore_test_storage_failure: "1",
            LOCALLORE_D04_MODEL_ROOT: "synthetic-metadata-only",
            LoCaLlOrE_UnKnOwN: "keep-out",
            X_LOCALLORE_MARKER: "unrelated-keep",
        });
        const before = plain(input),
            result = storageHelpers.sceneReviewEnvironment(input);
        assert.notEqual(
            result,
            input,
            "caller environment is never mutated or returned directly",
        );
        assert.deepEqual(plain(input), before);
        assert(!Object.keys(result).some((key) => /^locallore_/i.test(key)));
        assert.deepEqual(plain(result), {
            PATH: "synthetic-tools",
            TEMP: "D:/Dev/_Temp",
            TMP: "D:/Dev/_Temp",
            X_LOCALLORE_MARKER: "unrelated-keep",
        });
    },
);
await boundaryTest(
    "actual-scene-runner-sanitizes-aliases-before-explicit-review-flags-with-only-fake-children",
    async () => {
        const inherited = Object.freeze({
            PATH: "synthetic-tools",
            locallore_m07_memory_harness: "1",
            LoCaLlOrE_M07_LeGaCy_HaRnEsS: "1",
            locallore_test_storage_failure: "1",
        });
        const f = fixture({ automatic: true }),
            i = integration(f, true, inherited);
        await i.runScene("synthetic-review-build", "fixed-review-build", [], {
            LOCALLORE_D02_HARNESS: "1",
            LOCALLORE_TEST_MEMORY: "1",
            LOCALLORE_TEST_RESTART: "review",
        });
        const child = f.launches.find(
            (entry) => entry.command === "fixed-review-build",
        );
        assert(child);
        const environment = plain(child.options.env);
        assert.equal(environment.PATH, "synthetic-tools");
        assert.deepEqual(
            Object.keys(environment)
                .filter((key) => /^locallore_/i.test(key))
                .sort(),
            [
                "LOCALLORE_D02_HARNESS",
                "LOCALLORE_TEST_MEMORY",
                "LOCALLORE_TEST_RESTART",
            ].sort(),
        );
        assert.equal(environment.LOCALLORE_TEST_RESTART, "review");
        assert.deepEqual(plain(inherited), {
            PATH: "synthetic-tools",
            locallore_m07_memory_harness: "1",
            LoCaLlOrE_M07_LeGaCy_HaRnEsS: "1",
            locallore_test_storage_failure: "1",
        });
        assert(
            /sceneReviewEnvironment\s*\(\s*process\.env\s*\)/.test(runSource),
            "actual runner calls the frozen pure sanitizer",
        );
    },
);
await boundaryTest(
    "storage-preflight-is-called-before-first-packet-mkdir-and-first-Git",
    () => {
        assert(
            /async\s+function\s+validateScenePacketStorage\s*\(\s*folder\s*\)/.test(
                source,
            ),
        );
        const validation = source.search(
            /await\s+validateScenePacketStorage\s*\(\s*scenePacketFolder\s*\)/,
        );
        const creation = source.search(
            /await\s+mkdir\s*\(\s*scenePacketFolder\b/,
        );
        const firstGit = source.search(
            /const\s+revision\s*=\s*await\s+git\s*\(/,
        );
        assert(
            validation >= 0 && creation > validation && firstGit > creation,
            "prospective output/publication refusal must precede even packet/log creation and startup Git",
        );
    },
);
await boundaryTest(
    "frozen-storage-environment-block-is-pure-no-filesystem-or-process-action",
    () => {
        assert.doesNotMatch(
            storageHelperSource,
            /\b(?:writeFile|mkdir|readFile|lstat|realpath|spawn|execFile|runScene|git)\s*\(|process\.env/,
            "two pure helpers operate only on supplied paths/environment; async preflight remains outside their block",
        );
    },
);
function ancestryCases(disjoint, cases) {
    for (const { label, destination, allowed } of cases) {
        let refused = false, error = null;
        try { outsideReviewCheck(destination, disjoint); }
        catch (caught) { refused = true; error = caught; }
        ancestryObservations.push({ label, disjoint, allowed, refused,
            passed: refused === !allowed && (!error || error.code === "ERR_ASSERTION"),
            ...(error ? { error: String(error.message ?? error).slice(0, 300) } : {}) });
    }
}
await boundaryTest("existing-retained-packet-guard-allows-artifact-parent-without-weakening-disjoint-mode", () => {
const parentArtifactBase = path.win32.dirname(syntheticReviewRoot);
const fartherArtifactAncestor = path.win32.dirname(parentArtifactBase);
const siblingPacket = path.win32.join(parentArtifactBase, "different-fresh-packet");
ancestryCases(false, [
    { label: "immediate-parent-relative-dotdot", destination: parentArtifactBase, allowed: true },
    { label: "farther-ancestor", destination: fartherArtifactAncestor, allowed: true },
    { label: "sibling", destination: siblingPacket, allowed: true },
    { label: "case-alias-parent", destination: parentArtifactBase.toUpperCase(), allowed: true },
    { label: "equal", destination: syntheticReviewRoot, allowed: false },
    { label: "case-alias-equal", destination: syntheticReviewRoot.toUpperCase(), allowed: false },
    { label: "descendant", destination: path.win32.join(syntheticReviewRoot, "review"), allowed: false },
    { label: "case-alias-descendant", destination: path.win32.join(syntheticReviewRoot.toUpperCase(), "REVIEW"), allowed: false },
]);
ancestryCases(true, [
    { label: "immediate-parent", destination: parentArtifactBase, allowed: false },
    { label: "farther-ancestor", destination: fartherArtifactAncestor, allowed: false },
    { label: "equal", destination: syntheticReviewRoot, allowed: false },
    { label: "descendant", destination: path.win32.join(syntheticReviewRoot, "review"), allowed: false },
    { label: "case-alias-parent", destination: parentArtifactBase.toUpperCase(), allowed: false },
    { label: "sibling", destination: siblingPacket, allowed: true },
    { label: "case-alias-sibling", destination: siblingPacket.toUpperCase(), allowed: true },
]);
assert.equal(ancestryObservations.length, 15);
assert(ancestryObservations.every((entry) => entry.passed), "all existing guard ancestry modes preserve their distinct contracts");
});
const boundaryPassed =
    boundarySetupFailures.length === 0 &&
    boundaryChecks.length === 6 &&
    boundaryChecks.every((entry) => entry.passed);
console.log(
    JSON.stringify(
        {
            passed: boundaryPassed,
            kind: "synthetic-scene-child-process-policy",
            checks: checks.length,
            names: checks,
            boundary_setup_failure: boundarySetupFailures.length > 0,
            boundary_setup_failures: boundarySetupFailures,
            boundary_checks: boundaryChecks,
            boundary_helper_source_sha256:
                storageHelperSource === null
                    ? null
                    : sha256(storageHelperSource),
            retained_ancestry_observations: ancestryObservations,
            retained_ancestry_source_sha256: ancestrySource === null ? null : sha256(ancestrySource),
            node: process.version,
            platform: process.platform,
            actualChildLaunches: 0,
            nativeIpc: false,
            modelExecution: false,
            rendering: "unqualified-no-images",
            limitations: [
                "Simulated child/timer events only",
                "Storage/env additions use pure Windows path strings and copied metadata, not approved assets or real child/application actions",
                "No Windows kill/descendant/Job or real timeout-drain qualification",
                "No app, native IPC, model, asset, build, render, Android or human-quality qualification",
            ],
        },
        null,
        2,
    ),
);
if (!boundaryPassed) process.exitCode = 1;
