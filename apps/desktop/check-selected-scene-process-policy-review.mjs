// D07 independent FIRST SOURCE freeze. Author UNRUN. D06 exercise pattern retained; actual SELECTED launcher helper source
// in a VM with fake children/timers/FS only; no OS process, app, native IPC,
// model, build, real filesystem inventory, timer wait or desktop qualification.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { EventEmitter } from "node:events";
import { runInNewContext } from "node:vm";
import path from "node:path";

process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
assert.equal(process.argv.length, 2, "ClosedSelectedScenePolicyArguments");
const sourceUrl = new URL("./selected-evaluation-harness.mjs", import.meta.url);
const source = await readFile(sourceUrl, "utf8");
const hash = (value) => createHash("sha256").update(value).digest("hex");
const plain = (value) => JSON.parse(JSON.stringify(value));
const checks = [],
    setup = [],
    authored = [];
function between(start, end) {
    const first = source.indexOf(start),
        last = source.indexOf(end, first + start.length);
    assert(
        first >= 0 &&
            last > first &&
            source.indexOf(start, first + start.length) === -1,
        `UniqueActualSource:${start}`,
    );
    return source.slice(first, last);
}
// The admitted private helpers are top-level declarations, with top-level
// closing braces. Extract their actual text without requiring adjacent globals
// such as D06's disk/product declarations to retain a particular position.
function helper(name) {
    const start = `async function ${name}(`;
    const first = source.indexOf(start),
        last = source.indexOf("\n}", first + start.length);
    assert(
        first >= 0 &&
            last > first &&
            source.indexOf(start, first + start.length) === -1,
        `UniqueActualHelper:${name}`,
    );
    return source.slice(first, last + 2);
}
let blocks;
try {
    const finallyStarts = [...source.matchAll(/\bfinally\s*\{/g)];
    const afterFinally = /\n\}(?:\s*\n|$)/;
    assert.equal(finallyStarts.length, 1, "UniqueGlobalRestorationFinally");
    const beginning = finallyStarts[0].index + finallyStarts[0][0].length;
    const tail = source.slice(beginning),
        closing = tail.search(afterFinally);
    assert(closing >= 0, "GlobalRestorationEndRequired");
    blocks = {
        git: between(
            "// selected-git-policy-v1:start",
            "// selected-git-policy-v1:end",
        ),
        admission: between(
            "const revision = await gitRead",
            "const sourceInputs",
        ),
        run: between(
            "// selected-child-policy-v1:start",
            "// selected-child-policy-v1:end",
        ),
        footprint: helper("footprint"),
        measure: helper("measureStorage"),
        source: helper("unchangedSource"),
        products: helper("unchangedProducts"),
        restore: tail.slice(0, closing),
    };
} catch (error) {
    setup.push({
        stage: "actual-helper-extraction",
        error: String(error?.message ?? error).slice(0, 400),
        classification: "SETUP, not behavioral RED",
    });
}

const revision = "a".repeat(40);
const paths = Object.freeze({
    root: "D:\\synthetic-policy\\source",
    target: "D:\\synthetic-policy\\target",
    folder: "D:\\synthetic-policy\\packet",
    executable: "D:\\synthetic-policy\\target\\debug\\app.exe",
});
const products = Object.freeze({
    "dist/app.js": "fixed-js",
    [paths.executable]: "fixed-exe",
});
const sourceHashes = Object.freeze({ "fixed-source": "fixed-source-hash" });
const node = "D:\\synthetic-installed-tool\\node.exe";

function sandbox(options = {}) {
    const events = [],
        tasks = [],
        timers = new Map(),
        spawns = [],
        writes = [],
        metadata = [],
        messages = [];
    const files = new Map([
        [paths.root, [{ name: "source.txt", size: 0 }]],
        [paths.target, [{ name: "target.bin", size: 0 }]],
        [paths.folder, []],
    ]);
    const control = {
        ioError: false,
        sourceMismatch: false,
        productMismatch: false,
        gitCount: 0,
        nextProgram: null,
        nextGit: null,
        gitFaultAt: 0,
        gitFault: null,
    };
    let now = 0,
        timerId = 0,
        nextPid = 700;
    class Stream extends EventEmitter {
        destroyed = false;
        destroy() {
            this.destroyed = true;
        }
    }
    class Child extends EventEmitter {
        stdout = new Stream();
        stderr = new Stream();
        kills = 0;
        unrefs = 0;
        constructor(spec) {
            super();
            this.spec = spec;
            this.pid = spec.noPid ? undefined : ++nextPid;
        }
        kill() {
            this.kills++;
            events.push({ kind: "kill", pid: this.pid });
            if (this.spec.kill === "throw")
                throw Object.assign(Error("synthetic kill refusal"), {
                    code: "SYNTHETIC_KILL",
                });
            return this.spec.kill !== "false";
        }
        unref() {
            this.unrefs++;
        }
        close(code = 0, signal = null) {
            this.emit("close", code, signal);
        }
    }
    function spawn(command, args, spawnOptions) {
        const git = command === "git";
        if (git) control.gitCount++;
        const spec = (git && control.gitFaultAt === control.gitCount
            ? control.gitFault
            : null) ??
            (git ? control.nextGit : control.nextProgram) ?? {
                mode: "success",
            };
        if (git) control.nextGit = null;
        else control.nextProgram = null;
        const record = {
            command,
            args: [...args],
            options: spawnOptions,
            spec,
            child: null,
        };
        spawns.push(record);
        if (spec.mode === "throw")
            throw Object.assign(Error("synthetic spawn refusal"), {
                code: "SYNTHETIC_SPAWN",
            });
        const child = new Child(spec);
        record.child = child;
        if (spec.mode !== "manual")
            tasks.push(() => {
                if (spec.mode === "error")
                    child.emit(
                        "error",
                        Object.assign(Error("synthetic child error"), {
                            code: "SYNTHETIC_CHILD",
                        }),
                    );
                else if (spec.mode === "pipe") {
                    child[spec.channel ?? "stdout"].emit(
                        "error",
                        Object.assign(Error("synthetic pipe refusal"), {
                            code: "SYNTHETIC_PIPE",
                        }),
                    );
                    child.close();
                } else if (spec.mode === "overflow") {
                    child[spec.channel ?? "stdout"].emit(
                        "data",
                        Buffer.alloc(262145, 120),
                    );
                    child.close();
                } else {
                    if (spec.stdout !== undefined)
                        child.stdout.emit("data", Buffer.from(spec.stdout));
                    else if (git && args[0] === "rev-parse")
                        child.stdout.emit("data", Buffer.from(`${revision}\n`));
                    child.close(spec.code ?? 0, spec.signal ?? null);
                }
            });
        return child;
    }
    async function readdir(directory) {
        if (control.ioError)
            throw Object.assign(Error("synthetic inventory failure"), {
                code: "SYNTHETIC_IO",
            });
        if (!files.has(directory))
            throw Object.assign(Error("synthetic missing directory"), {
                code: "ENOENT",
            });
        return files.get(directory).map((file) => ({ name: file.name }));
    }
    async function lstat(file) {
        for (const [directory, entries] of files) {
            const entry = entries.find(
                (value) => path.win32.join(directory, value.name) === file,
            );
            if (entry)
                return {
                    size: entry.size,
                    isSymbolicLink: () => !!entry.alias,
                    isDirectory: () => !!entry.directory,
                    isFile: () => !entry.directory && !entry.special,
                };
        }
        throw Error("SyntheticMetadataMissing");
    }
    const context = {
        Buffer,
        Date,
        Math,
        Number,
        String,
        Object,
        Set,
        Promise,
        Error,
        path: path.win32,
        root: paths.root,
        target: paths.target,
        folder: paths.folder,
        executable: paths.executable,
        scene: true,
        literal: false,
        revision,
        sourceHashes,
        sourceInputs: ["fixed-source"],
        initialStorage: {
            target: { bytes: options.initialTargetBytes ?? 0 },
            source: { bytes: options.initialSourceBytes ?? 0 },
        },
        limits: {
            targetGrowth: 2 * 1024 ** 3,
            sourceGrowth: 128 * 1024 ** 2,
            artifacts: 256 * 1024 ** 2,
            entries: options.entryCap ?? 2_000_000,
        },
        process: {
            execPath: node,
            argv: [
                node,
                "D:\\synthetic-policy\\source\\selected-evaluation-harness.mjs",
                "--scene",
            ],
            env: {
                PATH: "synthetic-installed-tools",
                TEMP: "bad-parent-temp",
                TMP: "bad-parent-temp",
                CARGO_HOME: "D:/synthetic-cache",
                LOCALLORE_D04_MODEL_ROOT: "never-read-model",
                locallore_d04_model_root: "never-read-alias",
                LoCaLlOrE_D04_MoDeL_RoOt: "never-read-mixed-alias",
                locallore_d07_selected_harness: "remove-legacy-alias",
                LoCaLlOrE_D07_ScEnE_CoMpArIsOn_ReAdEr: "remove-scene-alias",
                LoCaLlOrE_Unknown: "remove",
                LOCALLORE_: "remove",
                X_LOCALLORE_MARKER: "keep",
            },
        },
        console: {
            error: (value) => messages.push(String(value)),
            log: (value) => messages.push(String(value)),
        },
        spawn,
        readdir,
        lstat,
        digest: hash,
        setTimeout: (callback, ms) => {
            const id = ++timerId;
            timers.set(id, { at: now + ms, callback, ms });
            return id;
        },
        clearTimeout: (id) => timers.delete(id),
        writeFile: async (file, bytes, writeOptions) => {
            assert.equal(writeOptions.flag, "wx");
            writes.push({ file, bytes: Buffer.from(bytes) });
        },
        write: async (name, value) => {
            metadata.push({ name, value: plain(value) });
        },
        hashes: async (names) =>
            names.includes("dist/app.js")
                ? control.productMismatch
                    ? { changed: true }
                    : products
                : control.sourceMismatch
                  ? { changed: true }
                  : sourceHashes,
        sourceStub: async () => {},
        buildArgs: (normal) => [
            "build",
            normal ? "normal-fixed" : "harness-fixed",
        ],
        expectedProducts: products,
    };
    const api = runInNewContext(
        `(() => { "use strict";
        let ownedDrainUnknown = false; const unknownChildren = [], gitChildren = [];
        let storageBreached = false, lastStorage = null, runNumber = 0;
        const processes = [], artifacts = {}, reports = [];
        ${blocks.git}
        ${blocks.footprint}
        ${blocks.measure}
        ${options.actualSource ? blocks.source : "const unchangedSource = sourceStub;"}
        let productHashes = expectedProducts;
        ${blocks.products}
        ${blocks.run}
        let originalError = null, restoration = null, workspace = null;
        return { gitRead, run, measureStorage, footprint, latchUnknown, unchangedSource, unchangedProducts,
            admit: async () => { ${blocks.admission} return revision; },
            restore: async () => { ${blocks.restore} return restoration; },
            observe: () => ({ ownedDrainUnknown, unknownChildren, gitChildren, storageBreached, lastStorage, processes, restoration }) };
    })()`,
        context,
        { timeout: 1000 },
    );
    const track = (promise) => {
        const result = {
            settled: false,
            ok: false,
            error: null,
            value: undefined,
        };
        Promise.resolve(promise).then(
            (value) =>
                Object.assign(result, { settled: true, ok: true, value }),
            (error) => Object.assign(result, { settled: true, error }),
        );
        return result;
    };
    async function flush() {
        for (let count = 0; count < 80; count++) {
            await Promise.resolve();
            const next = tasks.shift();
            if (next) next();
        }
    }
    async function advance(ms) {
        const until = now + ms;
        for (let count = 0; count < 16; count++) {
            const due = [...timers.entries()]
                .filter(([, value]) => value.at <= until)
                .sort((a, b) => a[1].at - b[1].at)[0];
            if (!due) {
                now = until;
                await flush();
                return;
            }
            timers.delete(due[0]);
            now = due[1].at;
            due[1].callback();
            await flush();
        }
        throw Error("SyntheticTimerIterationBound");
    }
    function start(
        kind,
        spec = { mode: "manual" },
        command = paths.executable,
        additions = {},
    ) {
        if (kind === "git") control.nextGit = spec;
        else control.nextProgram = spec;
        return track(
            kind === "git"
                ? api.gitRead(["rev-parse", "HEAD"])
                : api.run(command, [], additions),
        );
    }
    function program() {
        return spawns.filter((record) => record.command !== "git").at(-1)
            ?.child;
    }
    function last() {
        return spawns.at(-1)?.child;
    }
    async function finish(outcome) {
        for (let turn = 0; turn < 8 && !outcome.settled; turn++) await flush();
        assert.equal(outcome.settled, true, "BoundedFakeOutcomeSettled");
        return outcome;
    }
    async function blocked(kind = "child") {
        const count = spawns.length,
            outcome = track(
                kind === "git"
                    ? api.gitRead(["status", "--porcelain"])
                    : api.run(node, ["build.mjs"]),
            );
        await finish(outcome);
        assert.equal(outcome.ok, false);
        assert.equal(spawns.length, count, "NoSubsequentSpawnAfterLatch");
    }
    return {
        api,
        control,
        files,
        spawns,
        writes,
        metadata,
        messages,
        timers,
        events,
        track,
        flush,
        advance,
        start,
        program,
        last,
        finish,
        blocked,
    };
}
// Post-production scheduler calibration only: the original frozen source and
// 02df4593 result (152 PASS / 3 FAIL at restore Git6/7/8 timeout) remain evidence.
// Reach the intended manual child without advancing any virtual timer. Merely
// increasing the global microtick count would not establish this fault boundary.
async function awaitIntendedGitTimeout(h, outcome, position) {
    for (
        let flushes = 0;
        flushes < 8 && h.control.gitCount < position && !outcome.settled;
        flushes++
    )
        await h.flush();
    const lastGit = h.spawns.filter((entry) => entry.command === "git").at(-1),
        timers = [...h.timers.values()],
        child = lastGit?.child,
        observed = h.api.observe();
    try {
        assert.equal(h.control.gitCount, position, "IntendedGitPosition");
        assert.equal(outcome.settled, false, "IntendedGitStillPending");
        assert.equal(
            lastGit?.spec,
            h.control.gitFault,
            "IntendedGitFaultIdentity",
        );
        assert.equal(lastGit?.spec?.mode, "manual", "IntendedGitManualChild");
        assert(child?.pid != null, "IntendedGitHasPid");
        assert.equal(child.kills, 0, "IntendedGitNotPreviouslyKilled");
        assert.equal(
            observed.ownedDrainUnknown,
            false,
            "NoPrecedingUnknownDrain",
        );
        assert.equal(timers.length, 1, "OnlyIntendedGitTimerPending");
        assert.equal(timers[0].ms, 15000, "IntendedGitTimerIs15Seconds");
    } catch {
        throw Object.assign(Error("IntendedGitTimeoutBoundaryUnreached"), {
            code: "SYNTHETIC_GIT_FAULT_BOUNDARY_UNREACHED",
            readiness: {
                position,
                gitCount: h.control.gitCount,
                settled: outcome.settled,
                manualFault:
                    lastGit?.spec === h.control.gitFault &&
                    lastGit?.spec?.mode === "manual",
                pidPresent: child?.pid != null,
                kills: child?.kills ?? null,
                ownedDrainUnknown: observed.ownedDrainUnknown,
                timers: timers
                    .slice(0, 4)
                    .map((timer) => ({ ms: timer.ms, at: timer.at })),
            },
        });
    }
}
async function check(name, body) {
    authored.push(name);
    if (setup.length) return;
    try {
        await body();
        checks.push({ name, passed: true });
    } catch (error) {
        if (error?.code === "SYNTHETIC_GIT_FAULT_BOUNDARY_UNREACHED") {
            setup.push({
                stage: "intended-manual-git-timeout-readiness",
                name,
                error: String(error.message).slice(0, 400),
                readiness: error.readiness,
                classification:
                    "SETUP_UNRUN fault boundary not reached; no behavioral timeout result",
            });
            return;
        }
        checks.push({
            name,
            passed: false,
            error: String(error?.message ?? error).slice(0, 500),
        });
    }
}
if (blocks)
    try {
        sandbox();
    } catch (error) {
        setup.push({
            stage: "actual-helper-vm-construction",
            error: String(error?.message ?? error).slice(0, 400),
            classification: "SETUP, not behavioral RED",
        });
    }

for (const kind of ["git", "child"]) {
    await check(`${kind}:success-awaits-owned-close`, async () => {
        const h = sandbox(),
            outcome = h.start(kind);
        await h.flush();
        const child = h.last();
        assert(child);
        assert.equal(outcome.settled, false);
        child.stdout.emit(
            "data",
            Buffer.from(
                kind === "git" ? `${revision}\n` : "synthetic bounded output",
            ),
        );
        child.close();
        await h.finish(outcome);
        assert.equal(outcome.ok, true);
        assert.equal(h.api.observe().ownedDrainUnknown, false);
        assert.equal(child.kills, 0);
        const record =
            kind === "git"
                ? h.api.observe().gitChildren[0]
                : h.api.observe().processes[0];
        assert.equal(record.closed, true);
        assert.equal(record.code, 0);
        assert.equal(record.pid, child.pid);
        assert.equal(h.timers.size, 0);
        assert.equal(h.spawns[0].options.shell, false);
        assert.equal(h.spawns[0].options.windowsHide, true);
        assert.equal(h.spawns[0].options.cwd, paths.root);
        assert.equal(h.spawns[0].options.env.TEMP, "D:/Dev/_Temp");
        assert.equal(h.spawns[0].options.env.TMP, "D:/Dev/_Temp");
    });
    await check(
        `${kind}:nonzero-known-close-is-not-unknown-ownership`,
        async () => {
            const h = sandbox(),
                outcome = h.start(kind);
            await h.flush();
            h.last().close(1);
            await h.finish(outcome);
            assert.equal(outcome.ok, false);
            assert.equal(h.api.observe().ownedDrainUnknown, false);
            const record =
                kind === "git"
                    ? h.api.observe().gitChildren[0]
                    : h.api.observe().processes[0];
            assert.equal(record.closed, true);
            assert.equal(record.code, 1);
        },
    );
    for (const mode of ["throw", "no-pid-error", "pid-error"])
        await check(`${kind}:${mode}`, async () => {
            const h = sandbox(),
                outcome = h.start(
                    kind,
                    mode === "throw"
                        ? { mode: "throw" }
                        : { mode: "error", noPid: mode === "no-pid-error" },
                );
            await h.flush();
            if (h.last()) h.last().close();
            await h.finish(outcome);
            assert.equal(outcome.ok, false);
            const observation = h.api.observe();
            assert.equal(observation.ownedDrainUnknown, mode === "pid-error");
            const record =
                kind === "git"
                    ? observation.gitChildren[0]
                    : observation.processes[0];
            assert.equal(record.closed, false);
            assert.equal(
                record.pid,
                mode === "pid-error" ? h.last().pid : null,
            );
            assert.equal(
                record.error,
                mode === "throw" ? "SYNTHETIC_SPAWN" : "SYNTHETIC_CHILD",
            );
            if (mode === "pid-error") {
                assert(observation.unknownChildren.length > 0);
                await h.blocked();
                await h.blocked("git");
            }
        });
    for (const channel of ["stdout", "stderr"])
        await check(
            `${kind}:${channel}-error-recorded-without-uncaught-event`,
            async () => {
                const h = sandbox(),
                    outcome = h.start(kind);
                await h.flush();
                const child = h.last();
                let uncaught = null;
                try {
                    child[channel].emit(
                        "error",
                        Object.assign(Error("synthetic pipe failure"), {
                            code: "SYNTHETIC_PIPE",
                        }),
                    );
                } catch (error) {
                    uncaught = error;
                }
                await h.flush();
                child.close();
                await h.flush();
                // Assert outside the callback. An EventEmitter throw must not silently
                // become a fake success or disappear into the child's Promise handling.
                assert.equal(
                    uncaught,
                    null,
                    "OwnedPipeErrorMustNotEscapeLauncher",
                );
                assert.equal(h.api.observe().ownedDrainUnknown, true);
                await h.finish(outcome);
                assert.equal(outcome.ok, false);
                await h.blocked();
                await h.blocked("git");
                const restored = h.track(h.api.restore());
                await h.finish(restored);
                assert.equal(h.api.observe().restoration.skipped, true);
            },
        );
    for (const kill of ["true", "false", "throw"])
        await check(
            `${kind}:timeout-grace-late-close-kill-${kill}`,
            async () => {
                const h = sandbox(),
                    outcome = h.start(kind, { mode: "manual", kill });
                await h.flush();
                const child = h.last();
                await h.advance(kind === "git" ? 15000 : 960000);
                assert.equal(child.kills, 1);
                assert.equal(outcome.settled, false);
                assert.equal(h.api.observe().ownedDrainUnknown, true);
                await h.advance(4999);
                assert.equal(outcome.settled, false);
                await h.advance(1);
                await h.finish(outcome);
                assert.equal(outcome.ok, false);
                assert.equal(child.unrefs, 1);
                assert(child.stdout.destroyed && child.stderr.destroyed);
                const record =
                    kind === "git"
                        ? h.api.observe().gitChildren[0]
                        : h.api.observe().processes[0];
                assert.equal(record.closed, false);
                assert.equal(record.pid, child.pid);
                assert.equal(record.killAttempted, true);
                assert.equal(
                    record.killReturned,
                    kill === "throw" ? null : kill !== "false",
                );
                assert.equal(
                    record.killError,
                    kill === "throw" ? "SYNTHETIC_KILL" : null,
                );
                child.close();
                await h.flush();
                assert.equal(child.kills, 1);
                assert.equal(record.closed, false);
                await h.blocked();
                await h.blocked("git");
                const count = h.spawns.length,
                    restored = h.track(h.api.restore());
                await h.finish(restored);
                assert.equal(h.spawns.length, count);
                assert.equal(h.api.observe().restoration.skipped, true);
            },
        );
    await check(
        `${kind}:timeout-known-direct-close-still-preserves-unknown-latch`,
        async () => {
            const h = sandbox(),
                outcome = h.start(kind);
            await h.flush();
            const child = h.last();
            await h.advance(kind === "git" ? 15000 : 960000);
            child.close(null, "SIGTERM");
            await h.finish(outcome);
            assert.equal(outcome.ok, false);
            assert.equal(child.kills, 1);
            assert.equal(h.api.observe().ownedDrainUnknown, true);
            await h.blocked("git");
        },
    );
    for (const channel of ["stdout", "stderr"])
        await check(
            `${kind}:${channel}-overflow-bounded-permanently-blocks`,
            async () => {
                const h = sandbox(),
                    outcome = h.start(kind);
                await h.flush();
                const child = h.last();
                child[channel].emit("data", Buffer.alloc(262144, 120));
                assert.equal(
                    h.api.observe().ownedDrainUnknown,
                    false,
                    "ExactCapNotOverflow",
                );
                child[channel].emit("data", Buffer.alloc(8, 121));
                child[channel].emit("data", Buffer.alloc(8, 122));
                child.close();
                await h.finish(outcome);
                assert.equal(outcome.ok, false);
                assert.equal(
                    h.api.observe().unknownChildren.length,
                    1,
                    "OneOverflowLatchPerChild",
                );
                if (kind === "git")
                    assert.equal(
                        h.api.observe().gitChildren[0][`${channel}Bytes`],
                        262144,
                    );
                else
                    assert.equal(
                        h.writes.find((entry) =>
                            entry.file.endsWith(`${channel}.log`),
                        ).bytes.length,
                        262144,
                    );
                await h.blocked();
                await h.blocked("git");
            },
        );
}

await check(
    "child:case-insensitive-LOCALLORE-scrub-and-effective-fixed-additions",
    async () => {
        const h = sandbox(),
            additions = Object.freeze({
                LOCALLORE_D02_HARNESS: "1",
                LOCALLORE_TEST_MEMORY: "0",
            });
        const outcome = h.start(
            "child",
            { mode: "manual" },
            paths.executable,
            additions,
        );
        await h.flush();
        const environment = h.spawns[0].options.env;
        assert.deepEqual(
            Object.keys(environment)
                .filter((key) => /^LOCALLORE_/i.test(key))
                .sort(),
            ["LOCALLORE_D02_HARNESS", "LOCALLORE_TEST_MEMORY"],
        );
        assert.equal(environment.LOCALLORE_TEST_MEMORY, "0");
        assert.equal(environment.X_LOCALLORE_MARKER, "keep");
        assert.equal(environment.PATH, "synthetic-installed-tools");
        assert.equal(environment.CARGO_HOME, "D:/synthetic-cache");
        assert.equal(environment.TEMP, "D:/Dev/_Temp");
        assert.equal(environment.TMP, "D:/Dev/_Temp");
        h.last().close();
        await h.finish(outcome);
        assert.equal(outcome.ok, true);
    },
);
await check(
    "child:closed-native-arguments-and-product-mismatch-precede-spawn",
    async () => {
        const h = sandbox();
        const args = h.track(h.api.run(paths.executable, ["unexpected"]));
        await h.finish(args);
        assert.equal(args.ok, false);
        h.control.productMismatch = true;
        const product = h.track(h.api.run(paths.executable, []));
        await h.finish(product);
        assert.equal(product.ok, false);
        assert.equal(h.spawns.length, 0);
    },
);
await check(
    "child:Cargo-fixed-timeout-is-fifteen-minutes-with-one-kill",
    async () => {
        const h = sandbox(),
            outcome = h.start("child", { mode: "manual" }, "cargo");
        await h.flush();
        assert.equal([...h.timers.values()].length, 1);
        assert.equal([...h.timers.values()][0].ms, 900000);
        await h.advance(899999);
        assert.equal(h.last().kills, 0);
        assert.equal(outcome.settled, false);
        await h.advance(1);
        assert.equal(h.last().kills, 1);
        await h.advance(5000);
        await h.finish(outcome);
        assert.equal(outcome.ok, false);
        await h.blocked();
        await h.blocked("git");
    },
);

for (const failure of ["io", "entries", "size", "alias"])
    await check(
        `storage:${failure}-inventory-failure-latches-before-restoration`,
        async () => {
            const h = sandbox({
                entryCap: failure === "entries" ? 2 : 2_000_000,
            });
            if (failure === "io") h.control.ioError = true;
            if (failure === "entries")
                h.files.set(paths.target, [
                    { name: "one", size: 0 },
                    { name: "two", size: 0 },
                    { name: "three", size: 0 },
                ]);
            if (failure === "size")
                h.files.set(paths.target, [
                    { name: "unsafe", size: Number.MAX_SAFE_INTEGER + 1 },
                ]);
            if (failure === "alias")
                h.files.set(paths.target, [
                    { name: "aliased", size: 0, alias: true },
                ]);
            const measuring = h.track(h.api.measureStorage());
            await h.finish(measuring);
            assert.equal(measuring.ok, false);
            const failureLatched = h.api.observe().storageBreached;
            // Remove the synthetic fault: a single later good observation cannot reopen
            // work after an earlier failed measurement. Never delete real evidence.
            h.control.ioError = false;
            h.files.set(paths.target, [{ name: "target.bin", size: 0 }]);
            const restored = h.track(h.api.restore());
            await h.finish(restored);
            assert.equal(
                failureLatched,
                true,
                `FailedObservationMustLatch:restoration=${JSON.stringify(h.api.observe().restoration)};spawns=${h.spawns.length}`,
            );
            assert.equal(h.api.observe().restoration.skipped, true);
            assert.equal(h.spawns.length, 0);
            await h.blocked();
        },
    );
for (const area of ["target", "source", "packet"])
    await check(`storage:${area}-byte-budget-latch`, async () => {
        const h = sandbox(),
            directory =
                area === "target"
                    ? paths.target
                    : area === "source"
                      ? paths.root
                      : paths.folder;
        const cap =
            area === "target"
                ? 2 * 1024 ** 3
                : area === "source"
                  ? 128 * 1024 ** 2
                  : 255 * 1024 ** 2;
        h.files.set(directory, [{ name: "oversized.bin", size: cap + 1 }]);
        const measuring = h.track(h.api.measureStorage());
        await h.finish(measuring);
        assert.equal(measuring.ok, false);
        assert.equal(h.api.observe().storageBreached, true);
        h.files.set(directory, []);
        const restored = h.track(h.api.restore());
        await h.finish(restored);
        assert.equal(h.api.observe().restoration.skipped, true);
        assert.equal(h.spawns.length, 0);
        await h.blocked();
    });

for (const stage of ["early", "mid", "source-postclose", "restoration"])
    await check(`actual-source-git:${stage}-unknown-barrier`, async () => {
        const h = sandbox({ actualSource: true });
        if (stage === "restoration") {
            h.control.gitFaultAt = 1;
            h.control.gitFault = { mode: "manual" };
            const restoring = h.track(h.api.restore());
            await h.flush();
            assert.equal(h.spawns[0].command, "git");
            await h.advance(15000);
            await h.advance(5000);
            await h.finish(restoring);
            assert.equal(h.api.observe().restoration.passed, false);
        } else {
            h.control.gitFaultAt =
                stage === "early" ? 1 : stage === "mid" ? 2 : 3;
            h.control.gitFault = { mode: "manual" };
            const running = h.start("child", { mode: "success" });
            await h.flush();
            assert.equal(h.spawns.at(-1).command, "git");
            if (stage === "mid") {
                h.last().stdout.emit("data", Buffer.alloc(262145, 120));
                h.last().close();
            } else {
                await h.advance(15000);
                await h.advance(5000);
            }
            await h.finish(running);
            assert.equal(running.ok, false);
            assert.equal(
                h.spawns.filter((entry) => entry.command === paths.executable)
                    .length,
                stage === "source-postclose" ? 1 : 0,
            );
            const count = h.spawns.length,
                restoring = h.track(h.api.restore());
            await h.finish(restoring);
            assert.equal(h.spawns.length, count);
            assert.equal(h.api.observe().restoration.skipped, true);
        }
        assert.equal(h.api.observe().ownedDrainUnknown, true);
        await h.blocked("git");
        await h.blocked();
    });
await check(
    "actual-admission:unknown-initial-Git-prevents-any-packet-or-application-work",
    async () => {
        assert(
            source.indexOf("const revision = await gitRead") <
                source.indexOf("await mkdir(folder,"),
            "GitAdmissionPrecedesCreateNewPacket",
        );
        const h = sandbox();
        h.control.nextGit = { mode: "manual" };
        const admitting = h.track(h.api.admit());
        await h.flush();
        assert.equal(h.spawns.length, 1);
        await h.advance(15000);
        await h.advance(5000);
        await h.finish(admitting);
        assert.equal(admitting.ok, false);
        assert.equal(h.writes.length, 0);
        assert.equal(h.metadata.length, 0);
        assert(h.spawns.every((entry) => entry.command === "git"));
        await h.blocked();
        await h.blocked("git");
    },
);
await check(
    "actual-source:known-Git-failure-admission-can-only-restore-after-fresh-checks",
    async () => {
        const h = sandbox({ actualSource: true });
        h.control.gitFaultAt = 1;
        h.control.gitFault = { mode: "success", code: 1 };
        const running = h.start("child", { mode: "success" });
        await h.finish(running);
        assert.equal(running.ok, false);
        assert.equal(h.api.observe().ownedDrainUnknown, false);
        assert(!h.spawns.some((entry) => entry.command === paths.executable));
        const restoring = h.track(h.api.restore());
        await h.finish(restoring);
        assert.equal(h.api.observe().restoration.passed, true);
        const programIndices = h.spawns.flatMap((entry, index) =>
            entry.command !== "git" ? [index] : [],
        );
        assert.equal(programIndices.length, 2);
        assert.deepEqual(
            programIndices.map((index) => h.spawns[index].command),
            [node, "cargo"],
        );
        assert.deepEqual(plain(h.spawns[programIndices[0]].args), [
            "build.mjs",
        ]);
        assert.deepEqual(plain(h.spawns[programIndices[1]].args), [
            "build",
            "normal-fixed",
        ]);
        for (const index of programIndices)
            assert(
                h.spawns
                    .slice(0, index)
                    .filter((entry) => entry.command === "git").length >= 2,
            );
        assert(
            !h.spawns.some((entry) => entry.command === paths.executable),
            "RestorationNeverLaunchesNormalApp",
        );
    },
);
await check(
    "actual-source:hash-mismatch-refuses-native-and-cannot-restore-unverified-source",
    async () => {
        const h = sandbox({ actualSource: true });
        h.control.sourceMismatch = true;
        const running = h.start("child", { mode: "success" });
        await h.finish(running);
        assert.equal(running.ok, false);
        const restoring = h.track(h.api.restore());
        await h.finish(restoring);
        assert.equal(h.api.observe().restoration.passed, false);
        assert(h.spawns.every((entry) => entry.command === "git"));
    },
);

// D07 additions exercise the selected source, not a copied D06 implementation.
// No host child/files/timers are used by these policy simulations.
function gitFault(fault) {
    return fault === "known-nonzero"
        ? { mode: "success", code: 1 }
        : fault === "spawn-throw"
          ? { mode: "throw" }
          : fault === "no-pid"
            ? { mode: "error", noPid: true }
            : fault === "pid-error"
              ? { mode: "error" }
              : fault.endsWith("-pipe")
                ? { mode: "pipe", channel: fault.split("-")[0] }
                : fault.endsWith("-overflow")
                  ? { mode: "overflow", channel: fault.split("-")[0] }
                  : { mode: "manual" };
}
for (const kind of ["git", "child"])
    await check(
        `${kind}:exit-alone-never-proves-owned-pipe-closure`,
        async () => {
            const h = sandbox(),
                outcome = h.start(kind);
            await h.flush();
            const child = h.last();
            child.emit("exit", 0, null);
            await h.flush();
            assert.equal(outcome.settled, false);
            assert.equal(h.api.observe().ownedDrainUnknown, false);
            child.close();
            await h.finish(outcome);
            assert.equal(outcome.ok, true);
        },
    );
await check(
    "child:fixed-frontend-deadline-is240s-distinct-from960s-app",
    async () => {
        const h = sandbox(),
            outcome = h.start("child", { mode: "manual" }, node);
        await h.flush();
        assert.equal([...h.timers.values()][0].ms, 240000);
        await h.advance(239999);
        assert.equal(h.last().kills, 0);
        await h.advance(1);
        assert.equal(h.last().kills, 1);
        await h.advance(5000);
        await h.finish(outcome);
        assert.equal(outcome.ok, false);
        await h.blocked();
        await h.blocked("git");
    },
);
await check("child:fixed-scene-app-deadline-is960s-without-reset", async () => {
    const h = sandbox(),
        outcome = h.start("child");
    await h.flush();
    assert.equal([...h.timers.values()][0].ms, 960000);
    await h.advance(959999);
    assert.equal(h.last().kills, 0);
    await h.advance(1);
    assert.equal(h.last().kills, 1);
    await h.advance(5000);
    await h.finish(outcome);
    assert.equal(outcome.ok, false);
    await h.blocked();
    await h.blocked("git");
});
await check(
    "git:128-record-cap-is-finite-without-inventing-an-unknown-child",
    async () => {
        const h = sandbox();
        for (let i = 0; i < 128; i++) {
            const outcome = h.start("git", { mode: "success" });
            await h.finish(outcome);
            assert.equal(outcome.ok, true);
        }
        const before = h.spawns.length,
            last = h.start("git", { mode: "success" });
        await h.finish(last);
        assert.equal(last.ok, false);
        assert.equal(h.spawns.length, before);
        assert.equal(h.api.observe().gitChildren.length, 128);
        assert.equal(h.api.observe().ownedDrainUnknown, false);
    },
);
await check(
    "unknown:actual-latch-is-sticky-bounded-and-blocks-native-Git-and-restore",
    async () => {
        const h = sandbox();
        for (let i = 0; i < 75; i++)
            h.api.latchUnknown("synthetic-explicit-unknown", { pid: i + 1 });
        const before = h.spawns.length;
        assert.equal(h.api.observe().ownedDrainUnknown, true);
        assert.equal(h.api.observe().unknownChildren.length, 64);
        assert(
            h.api
                .observe()
                .unknownChildren.every((r) => r.processTreeContained === false),
        );
        await h.blocked();
        await h.blocked("git");
        const restoring = h.track(h.api.restore());
        await h.finish(restoring);
        assert.equal(h.spawns.length, before);
        assert.equal(h.api.observe().restoration.skipped, true);
    },
);
await check(
    "child:fixed-scene-additions-replace-every-case-alias-without-retaining-model-root",
    async () => {
        const h = sandbox(),
            additions = Object.freeze({
                LOCALLORE_D02_HARNESS: "1",
                LOCALLORE_D07_SELECTED_HARNESS: "1",
                LOCALLORE_D07_SCENE_COMPARISON_READER: "1",
                LOCALLORE_D07_LITERAL_COMPARISON_READER: "0",
                LOCALLORE_D07_NARRATION_DIAGNOSTIC_READER: "0",
            });
        const outcome = h.start(
            "child",
            { mode: "manual" },
            paths.executable,
            additions,
        );
        await h.flush();
        const env = h.spawns[0].options.env;
        assert.deepEqual(
            Object.keys(env)
                .filter((key) => /^LOCALLORE_/i.test(key))
                .sort(),
            Object.keys(additions).sort(),
        );
        assert(
            Object.keys(env).every(
                (key) => !/^LOCALLORE_D04_MODEL_ROOT$/i.test(key),
            ),
        );
        assert.equal(env.CARGO_HOME, "D:/synthetic-cache");
        assert.equal(env.TEMP, "D:/Dev/_Temp");
        assert.equal(env.TMP, "D:/Dev/_Temp");
        h.last().close();
        await h.finish(outcome);
        assert.equal(outcome.ok, true);
    },
);
await check(
    "git:case-insensitive-harness-and-model-root-aliases-never-reach-Git",
    async () => {
        const h = sandbox(),
            outcome = h.start("git");
        await h.flush();
        const env = h.spawns[0].options.env;
        assert(!Object.keys(env).some((key) => /^LOCALLORE_/i.test(key)));
        assert.equal(env.PATH, "synthetic-installed-tools");
        assert.equal(env.CARGO_HOME, "D:/synthetic-cache");
        h.last().stdout.emit("data", Buffer.from(`${revision}\n`));
        h.last().close();
        await h.finish(outcome);
        assert.equal(outcome.ok, true);
    },
);
for (const unsafe of [
    -1,
    0.5,
    Number.NaN,
    Infinity,
    Number.MAX_SAFE_INTEGER + 1,
])
    await check(
        `storage:unsafe-file-size-${String(unsafe)}-never-grants-work`,
        async () => {
            const h = sandbox();
            h.files.set(paths.target, [{ name: "unsafe-size", size: unsafe }]);
            const measuring = h.track(h.api.measureStorage());
            await h.finish(measuring);
            assert.equal(measuring.ok, false);
            assert.equal(h.api.observe().storageBreached, true);
            assert.equal(h.api.observe().lastStorage.unavailable, true);
            h.files.set(paths.target, []);
            await h.blocked();
            await h.blocked("git");
            const restoring = h.track(h.api.restore());
            await h.finish(restoring);
            assert.equal(h.api.observe().restoration.skipped, true);
            assert.equal(h.spawns.length, 0);
        },
    );
await check(
    "storage:unsafe-sum-overflow-remains-an-unavailable-measurement",
    async () => {
        const h = sandbox();
        h.files.set(paths.target, [
            { name: "first", size: Number.MAX_SAFE_INTEGER },
            { name: "second", size: 1 },
        ]);
        const measuring = h.track(h.api.measureStorage());
        await h.finish(measuring);
        assert.equal(measuring.ok, false);
        assert.equal(h.api.observe().lastStorage.unavailable, true);
        await h.blocked("git");
        await h.blocked();
    },
);
for (const area of ["target", "source", "packet"])
    await check(
        `storage:${area}-checks-total-of-individually-bounded-files`,
        async () => {
            const h = sandbox(),
                directory =
                    area === "target"
                        ? paths.target
                        : area === "source"
                          ? paths.root
                          : paths.folder;
            const cap =
                area === "target"
                    ? 2 * 1024 ** 3
                    : area === "source"
                      ? 128 * 1024 ** 2
                      : 255 * 1024 ** 2;
            h.files.set(directory, [
                { name: "part-one", size: Math.floor(cap / 2) },
                { name: "part-two", size: Math.ceil(cap / 2) },
                { name: "one-too-many", size: 1 },
            ]);
            const measuring = h.track(h.api.measureStorage());
            await h.finish(measuring);
            assert.equal(measuring.ok, false);
            assert.equal(h.api.observe().storageBreached, true);
            h.files.set(directory, []);
            await h.blocked("git");
            await h.blocked();
            const restoring = h.track(h.api.restore());
            await h.finish(restoring);
            assert.equal(h.api.observe().restoration.skipped, true);
        },
    );
await check(
    "storage:known-baseline-deltas-and-exact-caps-remain-admissible",
    async () => {
        const initialTargetBytes = 1024 ** 3,
            initialSourceBytes = 64 * 1024 ** 2;
        const h = sandbox({ initialTargetBytes, initialSourceBytes });
        h.files.set(paths.target, [
            {
                name: "existing-plus-growth",
                size: initialTargetBytes + 2 * 1024 ** 3,
            },
        ]);
        h.files.set(paths.root, [
            {
                name: "existing-plus-source",
                size: initialSourceBytes + 128 * 1024 ** 2,
            },
        ]);
        h.files.set(paths.folder, [
            { name: "packet-reserving-final-metadata", size: 255 * 1024 ** 2 },
        ]);
        const measuring = h.track(h.api.measureStorage());
        await h.finish(measuring);
        assert.equal(measuring.ok, true);
        assert.equal(h.api.observe().storageBreached, false);
        assert.equal(h.api.observe().lastStorage.targetGrowth, 2 * 1024 ** 3);
        assert.equal(h.api.observe().lastStorage.sourceGrowth, 128 * 1024 ** 2);
    },
);
await check(
    "storage:last-good-observation-is-retained-and-never-replaced-by-a-later-good-permission",
    async () => {
        const h = sandbox();
        h.files.set(paths.target, [{ name: "known", size: 25 }]);
        const known = h.track(h.api.measureStorage());
        await h.finish(known);
        assert.equal(known.ok, true);
        const lastKnown = plain(h.api.observe().lastStorage);
        h.control.ioError = true;
        const failed = h.track(h.api.measureStorage());
        await h.finish(failed);
        assert.equal(failed.ok, false);
        assert.equal(h.api.observe().lastStorage.unavailable, true);
        assert.deepEqual(
            plain(h.api.observe().lastStorage.lastKnown),
            lastKnown,
        );
        h.control.ioError = false;
        const retry = h.track(h.api.measureStorage());
        await h.finish(retry);
        assert.equal(retry.ok, false);
        await h.blocked();
        await h.blocked("git");
        const restoring = h.track(h.api.restore());
        await h.finish(restoring);
        const retention = h.metadata.find(
            (v) => v.name === "retention-measurement.json",
        ).value;
        assert.equal(retention.final, null);
        assert.equal(
            retention.finalObservation,
            "unavailable-storage-inventory",
        );
        assert.deepEqual(retention.lastKnown, lastKnown);
        assert.equal(retention.cleanupAttempted, false);
    },
);
for (const which of ["revision", "dirty-status"])
    await check(
        `actual-admission:${which}-known-refusal-never-starts-program-or-creates-packet`,
        async () => {
            const h = sandbox();
            h.control.gitFaultAt = which === "revision" ? 1 : 2;
            h.control.gitFault = {
                mode: "success",
                stdout:
                    which === "revision"
                        ? "not-a-commit\n"
                        : " M tracked-input\n",
            };
            const admitting = h.track(h.api.admit());
            await h.finish(admitting);
            assert.equal(admitting.ok, false);
            assert.equal(h.api.observe().ownedDrainUnknown, false);
            assert(h.spawns.every((v) => v.command === "git"));
            assert.equal(h.writes.length, 0);
            assert.equal(h.metadata.length, 0);
        },
    );
for (const position of [1, 2])
    for (const fault of [
        "known-nonzero",
        "spawn-throw",
        "no-pid",
        "pid-error",
        "stdout-pipe",
        "stderr-pipe",
        "stdout-overflow",
        "stderr-overflow",
        "timeout",
    ])
        await check(
            `actual-admission:Git${position}-${fault}-cannot-create-packet-or-launch-work`,
            async () => {
                const h = sandbox();
                h.control.gitFaultAt = position;
                h.control.gitFault = gitFault(fault);
                const unknown = ![
                        "known-nonzero",
                        "spawn-throw",
                        "no-pid",
                    ].includes(fault),
                    admitting = h.track(h.api.admit());
                await h.flush();
                if (fault === "timeout") {
                    await h.advance(15000);
                    await h.advance(5000);
                }
                await h.finish(admitting);
                assert.equal(admitting.ok, false);
                assert.equal(h.api.observe().ownedDrainUnknown, unknown);
                assert.equal(h.control.gitCount, position);
                assert(h.spawns.every((v) => v.command === "git"));
                assert.equal(h.writes.length, 0);
                assert.equal(h.metadata.length, 0);
                if (unknown) {
                    await h.blocked();
                    await h.blocked("git");
                    const count = h.spawns.length,
                        restoring = h.track(h.api.restore());
                    await h.finish(restoring);
                    assert.equal(h.spawns.length, count);
                    assert.equal(h.api.observe().restoration.skipped, true);
                }
            },
        );
for (const position of [1, 2, 3, 4, 5, 6, 7, 8])
    for (const fault of [
        "known-nonzero",
        "spawn-throw",
        "no-pid",
        "pid-error",
        "stdout-pipe",
        "stderr-pipe",
        "stdout-overflow",
        "stderr-overflow",
        "timeout",
    ])
        await check(
            `actual-restore:Git${position}-${fault}-prevents-unverified-followup`,
            async () => {
                const h = sandbox({ actualSource: true });
                h.control.gitFaultAt = position;
                const unknown = ![
                    "known-nonzero",
                    "spawn-throw",
                    "no-pid",
                ].includes(fault);
                h.control.gitFault = gitFault(fault);
                const restoring = h.track(h.api.restore());
                await h.flush();
                if (fault === "timeout") {
                    await awaitIntendedGitTimeout(h, restoring, position);
                    await h.advance(15000);
                    await h.advance(5000);
                }
                await h.finish(restoring);
                assert.equal(h.api.observe().restoration.passed, false);
                assert.equal(h.api.observe().ownedDrainUnknown, unknown);
                assert.equal(h.control.gitCount, position);
                const programs = h.spawns.filter((v) => v.command !== "git");
                assert.deepEqual(
                    programs.map((v) => v.command),
                    position <= 2
                        ? []
                        : position <= 6
                          ? [node]
                          : [node, "cargo"],
                );
                assert(
                    !h.spawns.some((v) => v.command === paths.executable),
                    "normal restoration never starts an app",
                );
                if (unknown) {
                    const count = h.spawns.length;
                    await h.blocked();
                    await h.blocked("git");
                    const again = h.track(h.api.restore());
                    await h.finish(again);
                    assert.equal(h.spawns.length, count);
                    assert.equal(h.api.observe().restoration.skipped, true);
                }
            },
        );
await check(
    "actual-source:known-closed-program-failure-restores-only-normal-builds-after-fresh-source-checks",
    async () => {
        const h = sandbox({ actualSource: true }),
            running = h.start("child", { mode: "success", code: 1 });
        await h.finish(running);
        assert.equal(running.ok, false);
        assert.equal(h.api.observe().ownedDrainUnknown, false);
        const count = h.spawns.length,
            restoring = h.track(h.api.restore());
        await h.finish(restoring);
        assert.equal(h.api.observe().restoration.passed, true);
        const later = h.spawns.slice(count);
        assert.deepEqual(
            later.filter((v) => v.command !== "git").map((v) => v.command),
            [node, "cargo"],
        );
        assert(
            later
                .filter((v) => v.command !== "git")
                .every(
                    (v) =>
                        !Object.keys(v.options.env).some((key) =>
                            /^LOCALLORE_/i.test(key),
                        ),
                ),
        );
        assert(
            later
                .filter((v) => v.command !== "git")
                .every((v) => v.command !== paths.executable),
        );
        assert(later.filter((v) => v.command === "git").length >= 8);
    },
);

assert.equal(
    hash(await readFile(sourceUrl, "utf8")),
    hash(source),
    "ActualLauncherSourceUnchanged",
);
const report = {
    version: 1,
    kind: "d07_selected_scene_process_policy_first_v1",
    contractSource:
        "e3c5cf51 helper/marker interface and read 53df4d3f fixture-reference/mixed-mode precision",
    sourceSHA256: hash(source),
    extractedSHA256: blocks
        ? Object.fromEntries(
              Object.entries(blocks).map(([name, text]) => [name, hash(text)]),
          )
        : null,
    setup,
    authored: authored.length,
    passed: checks.filter((entry) => entry.passed).length,
    failed: checks.filter((entry) => !entry.passed).length,
    checks,
    simulation:
        "actual trusted launcher helper source; synthetic children, pipe events, timers, FS/source/product observations",
    osChildExecution: false,
    nativeIpc: false,
    rendering: false,
    modelExecution: false,
    limits: [
        "No real child, timeout wall-clock, storage footprint, file alias or Windows process-tree measurement",
        "Entry overflow uses a smaller VM-only cap control; no actual two-million-entry traversal",
        "Known close is direct-child evidence only; no descendant containment claim",
        "Process-policy checks do not qualify journey oracles, WebView images, SDK/model absence or native UI",
        "Root separately measures/admit cumulative512MiB qualification evidence; these fake helper tests cover current packet/target/source accounting and never manufacture an external cohort measurement",
        "The bounded fixture reference/8192-entry native fixture/mixed-mode guards from53df4d3f are separate native FIRST/application evidence, not established by these process helper simulations",
    ],
};
console.log(JSON.stringify(report));
if (setup.length || report.failed) process.exitCode = 1;
