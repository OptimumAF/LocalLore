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
function integration(f, sceneMode = true) {
    const writes = [],
        snapshots = [],
        legacy = [],
        executions = [];
    const context = {
        assert,
        Buffer,
        path,
        process: { env: {} },
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
console.log(
    JSON.stringify(
        {
            passed: true,
            kind: "synthetic-scene-child-process-policy",
            checks: checks.length,
            names: checks,
            node: process.version,
            platform: process.platform,
            actualChildLaunches: 0,
            nativeIpc: false,
            modelExecution: false,
            rendering: "unqualified-no-images",
            limitations: [
                "Simulated child/timer events only",
                "No Windows kill/descendant/Job or real timeout-drain qualification",
                "No app, native IPC, model, asset, build, render, Android or human-quality qualification",
            ],
        },
        null,
        2,
    ),
);
