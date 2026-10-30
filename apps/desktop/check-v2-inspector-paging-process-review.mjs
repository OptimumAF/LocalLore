// Independent D05 launcher FIRST. SOURCE ONLY / UNCOMPILED / UNRUN at freeze.
// Executes ACTUAL future launcher helper/startup/finally text in a disclosed VM.
// Children, clocks, files, hashes and process are synthetic dependency doubles.
// The inventory body is ALSO actual launcher source; readdir/lstat are doubled.
// No OS child, actual timer wait, disk inventory, IPC, browser, pixels or model.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { EventEmitter } from "node:events";
import { runInNewContext } from "node:vm";
import path from "node:path";

const sourceUrl = new URL("./v2-inspector-paging-harness.mjs", import.meta.url);
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const plain = (value) => JSON.parse(JSON.stringify(value));
const cases = [],
    setup = [];
const register = (group, name, body) => cases.push({ group, name, body });
let source = "",
    blocks = null;
try {
    source = await readFile(sourceUrl, "utf8");
} catch (error) {
    setup.push({
        stage: "actual-launcher-source",
        error: String(error?.code ?? "SourceUnavailable"),
        classification: "SETUP_UNRUN; no behavioral result",
    });
}
function between(start, end) {
    const first = source.indexOf(start),
        last = source.indexOf(end, first + start.length);
    assert(
        first >= 0 &&
            last > first &&
            source.indexOf(start, first + start.length) < 0,
        `UniqueActualSeam:${start}`,
    );
    return source.slice(first + start.length, last);
}
if (!setup.length)
    try {
        const finallySites = [...source.matchAll(/\bfinally\s*\{/g)];
        assert.equal(finallySites.length, 1, "OneActualGlobalFinally");
        assert.equal(
            [...source.matchAll(/^try\s*\{/gm)].length,
            1,
            "OneActualTopLevelDriverTry",
        );
        assert.equal(
            [...source.matchAll(/^\}\s*catch\s*\(/gm)].length,
            1,
            "OneActualTopLevelDriverCatch",
        );
        assert.equal(
            [...source.matchAll(/^\}\s*finally\s*\{/gm)].length,
            1,
            "RestorationIsActualTopLevelFinally",
        );
        const tail = source.slice(
                finallySites[0].index + finallySites[0][0].length,
            ),
            end = tail.search(/\n\}(?:\s*\n|$)/);
        assert(end >= 0, "ActualGlobalFinallyEnd");
        blocks = {
            git: between(
                "// d05-paging-git-policy-v1:start",
                "// d05-paging-git-policy-v1:end",
            ),
            process: between(
                "// d05-paging-process-policy-v1:start",
                "// d05-paging-process-policy-v1:end",
            ),
            budget: between(
                "// d05-paging-budget-policy-v1:start",
                "// d05-paging-budget-policy-v1:end",
            ),
            gitAdmission: between(
                "// d05-paging-git-admission-v1:start",
                "// d05-paging-git-admission-v1:end",
            ),
            footprint: between(
                "// d05-paging-footprint-v1:start",
                "// d05-paging-footprint-v1:end",
            ),
            restore: tail.slice(0, end),
        };
        for (const [name, text] of [
            ["latchUnknown", blocks.git],
            ["gitRead", blocks.git],
            ["footprint", blocks.footprint],
            ["measureStorage", blocks.process],
            ["unchangedSource", blocks.process],
            ["unchangedProducts", blocks.process],
            ["run", blocks.process],
            ["checkedPagingBudget", blocks.budget],
        ])
            assert.match(
                text,
                new RegExp(`\\bfunction\\s+${name}\\s*\\(`),
                `ActualHelper:${name}`,
            );
        const packetMkdir = source.indexOf("await mkdir(folder");
        assert(
            packetMkdir > source.indexOf("// d05-paging-budget-policy-v1:end"),
            "ActualPacketMkdirAfterBudgetAdmission",
        );
    } catch (error) {
        setup.push({
            stage: "actual-launcher-extraction",
            error: String(error?.message ?? error).slice(0, 500),
            classification: "SETUP_UNRUN; no behavioral result",
        });
    }

const revision = "a".repeat(40),
    MiB = 1024 ** 2;
const paths = Object.freeze({
    root: "D:\\synthetic-d05\\source",
    base: "D:\\synthetic-d05\\evidence",
    target: "D:\\synthetic-d05\\target",
    folder: "D:\\synthetic-d05\\evidence\\packet",
    executable: "D:\\synthetic-d05\\target\\debug\\locallore-desktop-spike.exe",
});
const node = "D:\\synthetic-installed\\node.exe";
const limits = Object.freeze({
    targetGrowth: 2 * 1024 ** 3,
    sourceGrowth: 128 * MiB,
    artifacts: 64 * MiB,
    entries: 2_000_000,
    cumulativeEvidence: 640 * MiB,
    expectedEvidence: 64 * MiB,
    pagingEvidence: 128 * MiB,
});
const sourceHashes = { "source-fixed": "source-hash" },
    products = {
        "dist/app.js": "normal-fixed",
        [paths.executable]: "exe-fixed",
    };
function record(patch = {}) {
    return {
        version: 1,
        kind: "d05_v2_inspector_paging_budget_v1",
        source_revision: revision,
        target_path_sha256: hash(
            Buffer.from(path.win32.resolve(paths.target).toLowerCase(), "utf8"),
        ),
        original_target_bytes: 1000,
        external_evidence_bytes: 480 * MiB,
        d05_external_evidence_bytes: 0,
        cumulative_limit_bytes: 640 * MiB,
        ...patch,
    };
}
const recordBytes = (patch = {}) =>
    Buffer.from(JSON.stringify(record(patch)), "utf8");
const setupBoundary = (details) =>
    Object.assign(Error("IntendedFakeFaultBoundaryUnreached"), {
        code: "D05_FAKE_FAULT_SETUP_UNREACHED",
        details,
    });

function sandbox(options = {}) {
    const tasks = [],
        timers = new Map(),
        spawns = [],
        events = [],
        writes = [],
        metadata = [],
        messages = [],
        observations = [],
        reads = [],
        mkdirs = [];
    const control = {
        nextGit: null,
        nextProgram: null,
        gitFaultAt: 0,
        gitFault: null,
        gitCount: 0,
        sourceMismatch: false,
        productMismatch: false,
        inventoryError: false,
        recordError: false,
        recordBytes: recordBytes(),
        fileTrees: new Map(),
        footprints: {
            [paths.root]: { entries: 1, bytes: 100 },
            [paths.target]: { entries: 1, bytes: 1000 },
            [paths.base]: { entries: 1, bytes: 8 * MiB },
            [paths.folder]: { entries: 0, bytes: 0 },
        },
    };
    let now = 0,
        timerId = 0,
        pid = 700;
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
            this.pid = spec.noPid ? undefined : ++pid;
        }
        kill() {
            this.kills++;
            events.push({ kind: "kill", pid: this.pid });
            if (this.spec.kill === "throw")
                throw Object.assign(Error("SyntheticKill"), {
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
    function spawn(command, args, childOptions) {
        const git = command === "git";
        if (git) control.gitCount++;
        const spec = (git && control.gitCount === control.gitFaultAt
            ? control.gitFault
            : null) ??
            (git ? control.nextGit : control.nextProgram) ?? {
                mode: "success",
            };
        if (git) control.nextGit = null;
        else control.nextProgram = null;
        const item = {
            command,
            args: [...args],
            options: childOptions,
            spec,
            child: null,
        };
        spawns.push(item);
        if (spec.mode === "throw")
            throw Object.assign(Error("SyntheticSpawn"), {
                code: "SYNTHETIC_SPAWN",
            });
        const child = new Child(spec);
        item.child = child;
        if (spec.mode !== "manual")
            tasks.push(() => {
                if (spec.mode === "error")
                    child.emit(
                        "error",
                        Object.assign(Error("SyntheticChild"), {
                            code: "SYNTHETIC_CHILD",
                        }),
                    );
                else if (spec.mode === "pipe") {
                    child[spec.channel ?? "stdout"].emit(
                        "error",
                        Error("SyntheticPipe"),
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
    // Fake entries/metadata only. Traversal, exclusions, reparse/file checks,
    // byte sums and entry limits are exercised in blocks.footprint, not copied.
    function entries(directory) {
        if (control.fileTrees.has(directory))
            return control.fileTrees.get(directory);
        const value = control.footprints[directory];
        assert(value, "ClosedFakeInventoryDirectory");
        return value.entries === 0 && value.bytes === 0
            ? []
            : [{ name: "fixture.bin", size: value.bytes }];
    }
    async function readdir(directory) {
        observations.push(directory);
        if (control.inventoryError)
            throw Error("SyntheticInventoryUnavailable");
        return entries(directory).map((v) => ({ name: v.name }));
    }
    async function lstat(file) {
        if (control.inventoryError)
            throw Error("SyntheticInventoryUnavailable");
        if (
            Object.hasOwn(control.footprints, file) ||
            control.fileTrees.has(file)
        )
            return {
                size: 0,
                isSymbolicLink: () => false,
                isDirectory: () => true,
                isFile: () => false,
            };
        const parent = path.win32.dirname(file),
            name = path.win32.basename(file);
        const entry = entries(parent).find((v) => v.name === name);
        assert(entry, "ClosedFakeInventoryMetadata");
        return {
            size: entry.size ?? 0,
            isSymbolicLink: () => !!entry.alias,
            isDirectory: () => !!entry.directory,
            isFile: () => !entry.directory && !entry.special,
        };
    }
    const initialStorage = {
        target: { bytes: 1000 },
        source: { bytes: 100 },
        evidence: { bytes: 488 * MiB },
        pagingEvidence: { bytes: 8 * MiB },
    };
    const context = {
        Buffer,
        TextDecoder,
        Date,
        Promise,
        path: path.win32,
        root: paths.root,
        base: paths.base,
        target: paths.target,
        folder: paths.folder,
        executable: paths.executable,
        revision,
        sourcePaths: ["source-fixed"],
        sourceHashes,
        productHashes: options.noProductSnapshot ? null : products,
        initialStorage,
        limits: { ...limits, entries: options.entryCap ?? limits.entries },
        process: {
            execPath: node,
            argv: [
                node,
                "D:\\synthetic-d05\\source\\v2-inspector-paging-harness.mjs",
            ],
            env: {
                PATH: "synthetic-installed",
                TEMP: "wrong-parent",
                TMP: "wrong-parent",
                CARGO_HOME: "D:/synthetic-cache",
                LOCALLORE_D04_MODEL_ROOT: "never-read",
                locallore_d04_model_root: "never-read-lower",
                LoCaLlOrE_D04_MoDeL_RoOt: "never-read-mixed",
                LOCALLORE_D05_HARNESS: "remove-legacy",
                locallore_test_restart: "remove-restart",
                LoCaLlOrE_Unknown: "remove",
                LOCALLORE_: "remove",
                X_LOCALLORE_MARKER: "keep",
            },
        },
        spawn,
        digest: hash,
        readdir,
        lstat,
        hashes: async (names) =>
            names.includes("dist/app.js")
                ? control.productMismatch
                    ? { changed: true }
                    : products
                : control.sourceMismatch
                  ? { changed: true }
                  : sourceHashes,
        boundedBytes: async (file, maximum) => {
            reads.push({ file, maximum });
            if (control.recordError)
                throw Object.assign(Error("SyntheticMissingRecord"), {
                    code: "ENOENT",
                });
            return Buffer.from(control.recordBytes);
        },
        readFile: async () => Buffer.from("synthetic-unused-file"),
        statfs: async () => ({ bavail: 100n * 1024n ** 3n, bsize: 1n }),
        write: async (name, value) => {
            metadata.push({ name, value: plain(value) });
        },
        writeFile: async (file, bytes, flags) => {
            assert.equal(flags.flag, "wx");
            writes.push({ file, bytes: Buffer.from(bytes) });
        },
        mkdir: async (directory, flags) => {
            mkdirs.push({ directory, flags });
        },
        buildArgs: (normal) => [
            "build",
            normal ? "normal-fixed" : "harness-fixed",
        ],
        setTimeout: (callback, ms) => {
            const id = ++timerId;
            timers.set(id, { callback, ms, at: now + ms });
            return id;
        },
        clearTimeout: (id) => timers.delete(id),
        console: {
            error: (value) => messages.push(String(value)),
            log: (value) => messages.push(String(value)),
        },
    };
    const api = runInNewContext(
        `(() => { "use strict";
      let ownedDrainUnknown=false,storageBreached=false,lastStorage=null,runNumber=0;
      const unknownChildren=[],gitChildren=[],processes=[];
      let originalError=null,restoration=null,workspace=null;
      ${blocks.git}
      ${blocks.footprint}
      ${blocks.process}
      return {gitRead,run,footprint,measureStorage,unchangedSource,unchangedProducts,latchUnknown,
        admitGit:async()=>{${blocks.gitAdmission} return revision;},
        admit:async()=>{${blocks.budget} await mkdir(folder,{recursive:false}); return {initialStorage,checkedPagingBudget};},
        restore:async()=>{${blocks.restore} return restoration;},
        observe:()=>({ownedDrainUnknown,storageBreached,lastStorage,runNumber,unknownChildren,gitChildren,processes,restoration})};
    })()`,
        context,
        { timeout: 1000 },
    );
    const track = (promise) => {
        const outcome = {
            settled: false,
            ok: false,
            value: undefined,
            error: null,
        };
        Promise.resolve(promise).then(
            (value) =>
                Object.assign(outcome, { settled: true, ok: true, value }),
            (error) => Object.assign(outcome, { settled: true, error }),
        );
        return outcome;
    };
    async function flush() {
        for (let n = 0; n < 80; n++) {
            await Promise.resolve();
            const task = tasks.shift();
            if (task) task();
        }
    }
    async function finish(outcome) {
        for (let n = 0; n < 8 && !outcome.settled; n++) await flush();
        assert(outcome.settled, "BoundedFakeOutcomeSettled");
        return outcome;
    }
    async function advance(ms) {
        const until = now + ms;
        for (let n = 0; n < 16; n++) {
            const due = [...timers.entries()]
                .filter(([, v]) => v.at <= until)
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
        throw Error("FakeTimerIterationBudget");
    }
    function start(
        kind,
        spec,
        command = paths.executable,
        args = [],
        additions = {},
    ) {
        if (kind === "git") control.nextGit = spec;
        else control.nextProgram = spec;
        return track(
            kind === "git"
                ? api.gitRead(["rev-parse", "HEAD"])
                : api.run(command, args, additions),
        );
    }
    const last = (kind) =>
        spawns
            .filter((item) =>
                kind === "git"
                    ? item.command === "git"
                    : item.command !== "git",
            )
            .at(-1);
    async function ready(outcome, kind, ms, position = null) {
        for (let n = 0; n < 8; n++) {
            const item = last(kind);
            if (
                item?.spec?.mode === "manual" &&
                (position === null || control.gitCount === position)
            )
                break;
            if (outcome.settled) break;
            await flush();
        }
        const item = last(kind),
            pending = [...timers.values()];
        try {
            assert(!outcome.settled);
            assert(item?.child?.pid != null);
            assert.equal(item.spec.mode, "manual");
            if (position !== null) {
                assert.equal(control.gitCount, position);
                assert.equal(item.spec, control.gitFault);
            }
            assert.equal(item.child.kills, 0);
            assert.equal(api.observe().ownedDrainUnknown, false);
            assert.equal(pending.length, 1);
            assert.equal(pending[0].ms, ms);
        } catch {
            throw setupBoundary({
                kind,
                ms,
                position,
                gitCount: control.gitCount,
                settled: outcome.settled,
                timers: pending.slice(0, 4).map(({ ms, at }) => ({ ms, at })),
            });
        }
        return item.child;
    }
    async function barrier() {
        const count = spawns.length;
        for (const promise of [
            () => api.gitRead(["status", "--porcelain"]),
            () => api.run(paths.executable, []),
            () => api.run(node, ["build.mjs"]),
        ]) {
            const out = track(promise());
            await finish(out);
            assert.equal(out.ok, false);
            assert.equal(spawns.length, count, "NoLaterGitOrProgramAfterLatch");
        }
        const restore = track(api.restore());
        await finish(restore);
        assert.equal(spawns.length, count, "NoRestorationSpawnAfterLatch");
        assert.equal(api.observe().restoration?.skipped, true);
    }
    return {
        api,
        control,
        initialStorage,
        spawns,
        writes,
        metadata,
        messages,
        observations,
        reads,
        mkdirs,
        timers,
        events,
        track,
        start,
        flush,
        finish,
        advance,
        ready,
        last,
        barrier,
    };
}
const faultSpec = (fault) =>
    fault === "known-nonzero"
        ? { mode: "success", code: 1 }
        : fault === "spawn-throw"
          ? { mode: "throw" }
          : fault === "no-pid"
            ? { mode: "error", noPid: true }
            : fault === "pid-error"
              ? { mode: "error" }
              : fault.endsWith("pipe")
                ? { mode: "pipe", channel: fault.split("-")[0] }
                : fault.endsWith("overflow")
                  ? { mode: "overflow", channel: fault.split("-")[0] }
                  : { mode: "manual" };
const faults = [
    "known-nonzero",
    "spawn-throw",
    "no-pid",
    "pid-error",
    "stdout-pipe",
    "stderr-pipe",
    "stdout-overflow",
    "stderr-overflow",
    "timeout",
];
const isUnknown = (fault) =>
    !["known-nonzero", "spawn-throw", "no-pid"].includes(fault);

for (const kind of ["git", "child"]) {
    register("closure", `${kind}:success-requires-owned-close`, async () => {
        const h = sandbox(),
            out = h.start(kind, { mode: "manual" });
        await h.ready(out, kind, kind === "git" ? 15000 : 180000);
        assert.equal(out.settled, false);
        h.last(kind).child.close();
        await h.finish(out);
        assert.equal(out.ok, true);
        assert.equal(h.api.observe().ownedDrainUnknown, false);
        assert.equal(h.timers.size, 0);
    });
    register(
        "closure",
        `${kind}:exit-does-not-substitute-for-pipe-close`,
        async () => {
            const h = sandbox(),
                out = h.start(kind, { mode: "manual" });
            const child = await h.ready(
                out,
                kind,
                kind === "git" ? 15000 : 180000,
            );
            child.emit("exit", 0, null);
            await h.flush();
            assert.equal(out.settled, false);
            child.close();
            await h.finish(out);
            assert.equal(out.ok, true);
        },
    );
    for (const fault of faults.filter((v) => v !== "timeout"))
        register("child-faults", `${kind}:${fault}`, async () => {
            const h = sandbox(),
                out = h.start(kind, faultSpec(fault));
            await h.finish(out);
            assert.equal(out.ok, false);
            assert.equal(h.api.observe().ownedDrainUnknown, isUnknown(fault));
            const recorded =
                kind === "git"
                    ? h.api.observe().gitChildren
                    : h.api.observe().processes;
            assert.equal(recorded.length, kind === "git" ? 1 : 1);
            if (fault.endsWith("overflow")) {
                assert.equal(recorded[0].truncated, true);
                for (const channel of ["stdout", "stderr"])
                    assert((recorded[0][`${channel}Bytes`] ?? 0) <= 262144);
                for (const written of h.writes.filter((v) =>
                    /(?:stdout|stderr)\.log$/.test(v.file),
                ))
                    assert(written.bytes.length <= 262144);
            }
            if (isUnknown(fault)) {
                h.last(kind).child?.close();
                await h.flush();
                assert.equal(h.api.observe().ownedDrainUnknown, true);
                await h.barrier();
            }
        });
}
for (const [kind, command, deadline] of [
    ["git", "git", 15000],
    ["child", node, 240000],
    ["child", "cargo", 900000],
    ["child", paths.executable, 180000],
]) {
    for (const kill of ["true", "false", "throw"])
        register(
            "deadlines",
            `${command}:timeout-one-kill-${kill}-five-second-grace-late-close`,
            async () => {
                const h = sandbox(),
                    out = h.start(kind, { mode: "manual", kill }, command);
                const child = await h.ready(out, kind, deadline);
                await h.advance(deadline - 1);
                assert.equal(child.kills, 0);
                assert.equal(out.settled, false);
                await h.advance(1);
                assert.equal(child.kills, 1);
                assert.equal(h.api.observe().ownedDrainUnknown, true);
                assert.equal(out.settled, false);
                await h.advance(4999);
                assert.equal(out.settled, false);
                await h.advance(1);
                await h.finish(out);
                assert.equal(out.ok, false);
                assert.equal(child.kills, 1);
                assert(child.unrefs >= 1);
                child.close();
                await h.flush();
                assert.equal(h.api.observe().ownedDrainUnknown, true);
                await h.barrier();
            },
        );
    register(
        "deadlines",
        `${command}:known-direct-close-after-timeout-never-clears-latch`,
        async () => {
            const h = sandbox(),
                out = h.start(kind, { mode: "manual" }, command);
            const child = await h.ready(out, kind, deadline);
            await h.advance(deadline);
            child.close();
            await h.finish(out);
            assert.equal(out.ok, false);
            assert.equal(h.api.observe().ownedDrainUnknown, true);
            await h.barrier();
        },
    );
}
for (const kind of ["git", "child"])
    register(
        "environment",
        `${kind}:case-folded-model-harness-aliases-scrubbed-fixed-D-temporaries`,
        async () => {
            const h = sandbox();
            const additions =
                kind === "child"
                    ? {
                          LOCALLORE_D02_HARNESS: "1",
                          LOCALLORE_D02_ARTIFACT_DIR: paths.folder,
                          LOCALLORE_TEST_WORKSPACE: path.win32.join(
                              paths.folder,
                              "stories-v1.sqlite",
                          ),
                          LOCALLORE_D05_INSPECTOR_PAGING_HARNESS: "1",
                      }
                    : {};
            const out = h.start(
                kind,
                { mode: "success" },
                kind === "git" ? "git" : paths.executable,
                [],
                additions,
            );
            await h.finish(out);
            assert.equal(out.ok, true);
            const item = h.last(kind),
                env = item.options.env;
            assert.equal(item.options.shell, false);
            assert.equal(item.options.windowsHide, true);
            assert.equal(env.TEMP, "D:/Dev/_Temp");
            assert.equal(env.TMP, "D:/Dev/_Temp");
            assert.equal(env.X_LOCALLORE_MARKER, "keep");
            assert.equal(item.options.cwd, paths.root);
            assert.deepEqual(plain(item.options.stdio), [
                "ignore",
                "pipe",
                "pipe",
            ]);
            assert.deepEqual(
                Object.keys(env)
                    .filter((v) => /^LOCALLORE_/i.test(v))
                    .sort(),
                Object.keys(additions).sort(),
            );
            for (const [key, value] of Object.entries(additions))
                assert.equal(env[key], value);
        },
    );
for (const mode of [
    "source-before",
    "product-before",
    "source-after",
    "product-after",
    "native-arguments",
])
    register("identity", `actual-source-products:${mode}`, async () => {
        const h = sandbox();
        if (mode === "source-before") h.control.sourceMismatch = true;
        if (mode === "product-before") h.control.productMismatch = true;
        const out = h.start(
            "child",
            { mode: "manual" },
            paths.executable,
            mode === "native-arguments" ? ["--arbitrary"] : [],
        );
        if (mode.endsWith("after")) {
            const child = await h.ready(out, "child", 180000);
            h.control[
                mode === "source-after" ? "sourceMismatch" : "productMismatch"
            ] = true;
            child.close();
        }
        await h.finish(out);
        assert.equal(out.ok, false);
        assert.equal(h.api.observe().ownedDrainUnknown, false);
        assert.equal(
            h.spawns.filter((v) => v.command === paths.executable).length,
            mode.endsWith("after") ? 1 : 0,
        );
    });

for (const position of [1, 2])
    for (const fault of faults)
        register(
            "git-admission",
            `actual-initial-Git${position}:${fault}`,
            async () => {
                const h = sandbox();
                h.control.gitFaultAt = position;
                h.control.gitFault = faultSpec(fault);
                const out = h.track(h.api.admitGit());
                if (fault === "timeout") {
                    await h.ready(out, "git", 15000, position);
                    await h.advance(15000);
                    await h.advance(5000);
                }
                await h.finish(out);
                assert.equal(out.ok, false);
                assert.equal(h.control.gitCount, position);
                assert.equal(
                    h.api.observe().ownedDrainUnknown,
                    isUnknown(fault),
                );
                assert(h.spawns.every((v) => v.command === "git"));
                assert.equal(h.mkdirs.length, 0);
                assert.equal(h.writes.length, 0);
                assert.equal(h.metadata.length, 0);
                if (isUnknown(fault)) await h.barrier();
            },
        );
for (const which of ["revision", "dirty"])
    register(
        "git-admission",
        `actual-initial-Git:${which}-known-refusal`,
        async () => {
            const h = sandbox();
            h.control.gitFaultAt = which === "revision" ? 1 : 2;
            h.control.gitFault = {
                mode: "success",
                stdout:
                    which === "revision"
                        ? "not-a-commit\n"
                        : " M source-fixed\n",
            };
            const out = h.track(h.api.admitGit());
            await h.finish(out);
            assert.equal(out.ok, false);
            assert.equal(h.api.observe().ownedDrainUnknown, false);
            assert(h.spawns.every((v) => v.command === "git"));
            assert.equal(h.mkdirs.length, 0);
        },
    );
for (const position of [1, 2, 3, 4, 5, 6, 7, 8])
    for (const fault of faults)
        register(
            "global-finally",
            `actual-restore-Git${position}:${fault}`,
            async () => {
                const h = sandbox();
                h.control.gitFaultAt = position;
                h.control.gitFault = faultSpec(fault);
                const out = h.track(h.api.restore());
                if (fault === "timeout") {
                    await h.ready(out, "git", 15000, position);
                    await h.advance(15000);
                    await h.advance(5000);
                }
                await h.finish(out);
                assert.equal(h.api.observe().restoration?.passed, false);
                assert.equal(h.control.gitCount, position);
                assert.equal(
                    h.api.observe().ownedDrainUnknown,
                    isUnknown(fault),
                );
                assert.deepEqual(
                    h.spawns
                        .filter((v) => v.command !== "git")
                        .map((v) => v.command),
                    position <= 2
                        ? []
                        : position <= 6
                          ? [node]
                          : [node, "cargo"],
                );
                assert(!h.spawns.some((v) => v.command === paths.executable));
                if (isUnknown(fault)) await h.barrier();
            },
        );
register(
    "global-finally",
    "known-closed-program-failure-restores-only-normal-products",
    async () => {
        const h = sandbox(),
            failed = h.start("child", { mode: "success", code: 1 });
        await h.finish(failed);
        assert.equal(failed.ok, false);
        assert.equal(h.api.observe().ownedDrainUnknown, false);
        const before = h.spawns.length,
            out = h.track(h.api.restore());
        await h.finish(out);
        assert.equal(h.api.observe().restoration?.passed, true);
        const later = h.spawns.slice(before);
        assert.deepEqual(
            later.filter((v) => v.command !== "git").map((v) => v.command),
            [node, "cargo"],
        );
        assert(later.every((v) => v.command !== paths.executable));
        assert(later.filter((v) => v.command === "git").length >= 8);
        for (const item of later)
            assert.equal(
                Object.keys(item.options.env).some((key) =>
                    /^LOCALLORE_/i.test(key),
                ),
                false,
            );
    },
);
// Independent pre-fix extension after the original 243-case result. These run
// the extracted ACTUAL finally, preserving every original case and policy body.
register(
    "global-finally",
    "captured-product-mismatch-refuses-before-any-normal-restoration-child",
    async () => {
        const h = sandbox();
        h.control.productMismatch = true;
        const before = h.spawns.length,
            out = h.track(h.api.restore());
        await h.finish(out);
        const observed = h.api.observe();
        assert.equal(observed.restoration?.passed, false);
        assert.equal(observed.restoration?.launched, false);
        assert.equal(observed.ownedDrainUnknown, false);
        assert.equal(observed.storageBreached, false);
        assert.deepEqual(
            h.spawns.slice(before).filter((item) => item.command !== "git"),
            [],
            "Changed captured products must not be overwritten by Node/Cargo/native",
        );
        assert.equal(observed.processes.length, 0);
        const evidence = h.metadata.find((item) => item.name === "normal-restoration.json");
        assert.equal(evidence?.value.passed, false);
    },
);
register(
    "global-finally",
    "known-closed-initial-build-failure-without-product-snapshot-still-restores",
    async () => {
        const h = sandbox({ noProductSnapshot: true }),
            failed = h.start("child", { mode: "success", code: 1 }, node);
        await h.finish(failed);
        assert.equal(failed.ok, false);
        assert.equal(h.api.observe().ownedDrainUnknown, false);
        const before = h.spawns.length,
            out = h.track(h.api.restore());
        await h.finish(out);
        assert.equal(h.api.observe().restoration?.passed, true);
        assert.equal(h.api.observe().restoration?.launched, false);
        const later = h.spawns.slice(before);
        assert.deepEqual(
            later.filter((item) => item.command !== "git").map((item) => item.command),
            [node, "cargo"],
        );
        assert(later.every((item) => item.command !== paths.executable));
        assert(later.filter((item) => item.command === "git").length >= 8);
    },
);
register(
    "finite-records",
    "Git-record-cap128-refuses-before-spawn-with-known-closure",
    async () => {
        const h = sandbox();
        for (let i = 0; i < 128; i++) {
            const out = h.start("git", { mode: "success" });
            await h.finish(out);
            assert.equal(out.ok, true);
        }
        const count = h.spawns.length,
            refused = h.start("git", { mode: "success" });
        await h.finish(refused);
        assert.equal(refused.ok, false);
        assert.equal(h.spawns.length, count);
        assert.equal(h.api.observe().gitChildren.length, 128);
        assert.equal(h.api.observe().ownedDrainUnknown, false);
    },
);
register(
    "finite-records",
    "unknown-observation-cap64-never-unlatches",
    async () => {
        const h = sandbox();
        for (let i = 0; i < 80; i++)
            h.api.latchUnknown("SyntheticUnknown", { sequence: i, pid: 123 });
        assert.equal(h.api.observe().ownedDrainUnknown, true);
        assert(
            h.api.observe().unknownChildren.length > 0 &&
                h.api.observe().unknownChildren.length <= 64,
        );
        await h.barrier();
    },
);

async function refusedStorage(h) {
    const out = h.track(h.api.measureStorage());
    await h.finish(out);
    assert.equal(out.ok, false);
    assert.equal(h.api.observe().storageBreached, true);
    await h.barrier();
}
for (const [name, directory, bytes] of [
    ["target", paths.target, 1000 + limits.targetGrowth + 1],
    ["source", paths.root, 100 + limits.sourceGrowth + 1],
    ["packet", paths.folder, limits.artifacts - MiB + 1],
])
    register("storage", `${name}:bounded-growth-refusal-sticky`, async () => {
        const h = sandbox();
        h.control.footprints[directory].bytes = bytes;
        await refusedStorage(h);
    });
for (const directory of [paths.root, paths.target, paths.folder])
    for (const value of [-1, 0.5, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1])
        register(
            "storage",
            `${directory}:invalid-footprint-byte-${String(value)}`,
            async () => {
                const h = sandbox();
                h.control.footprints[directory].bytes = value;
                await refusedStorage(h);
            },
        );
for (const entry of [
    { name: "alias", alias: true },
    { name: "special", special: true },
])
    register(
        "inventory",
        `actual-inventory-rejects-${entry.name}`,
        async () => {
            const h = sandbox();
            h.control.fileTrees.set(paths.folder, [entry]);
            await refusedStorage(h);
        },
    );
register(
    "inventory",
    "actual-entry-cap-small-VM-control-not-million-file-execution",
    async () => {
        const h = sandbox({ entryCap: 3 });
        h.control.fileTrees.set(
            paths.folder,
            [0, 1, 2, 3].map((v) => ({ name: `entry-${v}`, size: 0 })),
        );
        await refusedStorage(h);
    },
);
register(
    "inventory",
    "actual-byte-sum-overflow-refuses-individually-safe-files",
    async () => {
        const h = sandbox();
        h.control.fileTrees.set(paths.folder, [
            { name: "first", size: Number.MAX_SAFE_INTEGER },
            { name: "second", size: 1 },
        ]);
        await refusedStorage(h);
    },
);
register(
    "inventory",
    "actual-inventory-sums-ordinary-files-and-source-exclusions",
    async () => {
        const h = sandbox();
        h.control.fileTrees.set(paths.root, [
            { name: ".git", directory: true },
            { name: "node_modules", directory: true },
            { name: "artifacts", directory: true },
            { name: "target", directory: true },
            { name: "a.txt", size: 11 },
            { name: "b.txt", size: 17 },
        ]);
        const out = h.track(h.api.footprint(paths.root, true));
        await h.finish(out);
        assert.equal(out.ok, true);
        assert.equal(out.value.bytes, 28);
        assert.equal(out.value.entries, 2);
    },
);
for (const which of ["joint", "paging", "unsafe-sum"])
    register(
        "storage",
        `${which}:evidence-baseline-plus-packet-no-reset`,
        async () => {
            const h = sandbox();
            h.control.footprints[paths.folder].bytes = 100;
            if (which === "joint")
                h.initialStorage.evidence.bytes =
                    limits.cumulativeEvidence - MiB - 99;
            if (which === "paging")
                h.initialStorage.pagingEvidence.bytes =
                    limits.pagingEvidence - MiB - 99;
            if (which === "unsafe-sum")
                h.initialStorage.evidence.bytes = Number.MAX_SAFE_INTEGER;
            await refusedStorage(h);
        },
    );
register(
    "storage",
    "exact-bounds-both-evidence-baselines-and-original-target",
    async () => {
        const h = sandbox();
        h.control.footprints[paths.folder].bytes = 100;
        h.initialStorage.evidence.bytes = limits.cumulativeEvidence - MiB - 100;
        h.initialStorage.pagingEvidence.bytes =
            limits.pagingEvidence - MiB - 100;
        h.control.footprints[paths.target].bytes = 1000 + limits.targetGrowth;
        h.control.footprints[paths.root].bytes = 100 + limits.sourceGrowth;
        const out = h.track(h.api.measureStorage());
        await h.finish(out);
        assert.equal(out.ok, true);
        const measured = h.api.observe().lastStorage;
        assert.equal(measured.targetGrowth, limits.targetGrowth);
        assert.equal(
            measured.cumulativeEvidence,
            limits.cumulativeEvidence - MiB,
        );
        assert.equal(measured.pagingEvidence, limits.pagingEvidence - MiB);
    },
);
register(
    "storage",
    "inventory-unavailable-retains-last-known-and-never-grants-retry",
    async () => {
        const h = sandbox(),
            first = h.track(h.api.measureStorage());
        await h.finish(first);
        assert.equal(first.ok, true);
        const known = plain(h.api.observe().lastStorage);
        h.control.inventoryError = true;
        const failed = h.track(h.api.measureStorage());
        await h.finish(failed);
        assert.equal(failed.ok, false);
        assert.equal(h.api.observe().lastStorage?.unavailable, true);
        assert.deepEqual(plain(h.api.observe().lastStorage.lastKnown), known);
        h.control.inventoryError = false;
        await refusedStorage(h);
    },
);
register(
    "storage",
    "actual-run-inventory-failure-prevents-program-and-all-further-work",
    async () => {
        const h = sandbox();
        h.control.inventoryError = true;
        const out = h.start("child", { mode: "manual" });
        await h.finish(out);
        assert.equal(out.ok, false);
        assert.equal(h.api.observe().storageBreached, true);
        assert.equal(h.spawns.filter((v) => v.command !== "git").length, 0);
        h.control.inventoryError = false;
        await h.barrier();
    },
);

async function rejectedAdmission(h) {
    const out = h.track(h.api.admit());
    await h.finish(out);
    assert.equal(out.ok, false);
    assert.equal(h.mkdirs.length, 0, "NoPacketBeforeFailedBudgetAdmission");
    assert.equal(h.spawns.length, 0);
    assert.equal(h.writes.length, 0);
    return out;
}
register(
    "budget-startup",
    "actual-startup-valid-eight-key-record-projects-only-three-fields",
    async () => {
        const h = sandbox(),
            out = h.track(h.api.admit());
        await h.finish(out);
        assert.equal(out.ok, true);
        assert.equal(h.mkdirs.length, 1);
        assert.equal(h.spawns.length, 0);
        assert.equal(h.reads.length, 1);
        assert.equal(
            h.reads[0].file,
            path.win32.join(
                paths.base,
                `d05-v2-inspector-paging-budget-v1-${revision}.json`,
            ),
        );
        assert.equal(h.reads[0].maximum, 4096);
        const projected = out.value.checkedPagingBudget(
            recordBytes(),
            revision,
            paths.target,
            1000,
        );
        assert.deepEqual(plain(projected), {
            originalTargetBytes: 1000,
            externalEvidenceBytes: 480 * MiB,
            d05ExternalEvidenceBytes: 0,
        });
        assert.equal(out.value.initialStorage.target.bytes, 1000);
        assert.equal(out.value.initialStorage.evidence.bytes, 488 * MiB);
        assert.equal(out.value.initialStorage.pagingEvidence.bytes, 8 * MiB);
    },
);
for (const key of Object.keys(record()))
    register("budget-decoder", `missing:${key}`, async () => {
        const h = sandbox(),
            value = record();
        delete value[key];
        h.control.recordBytes = Buffer.from(JSON.stringify(value));
        await rejectedAdmission(h);
    });
for (const key of Object.keys(record()))
    register("budget-decoder", `duplicate-identical:${key}`, async () => {
        const h = sandbox(),
            text = JSON.stringify(record());
        h.control.recordBytes = Buffer.from(
            text.slice(0, -1) +
                `,${JSON.stringify(key)}:${JSON.stringify(record()[key])}}`,
        );
        await rejectedAdmission(h);
    });
register(
    "budget-decoder",
    "duplicate-escaped-version-refuses-before-projection",
    async () => {
        const h = sandbox(),
            text = JSON.stringify(record());
        h.control.recordBytes = Buffer.from(
            text.slice(0, -1) + ',"\\u0076ersion":1}',
        );
        await rejectedAdmission(h);
    },
);
register("budget-decoder", "unknown-key-refuses", async () => {
    const h = sandbox();
    h.control.recordBytes = recordBytes({ arbitrary: 1 });
    await rejectedAdmission(h);
});
for (const [name, text] of [
    ["empty", ""],
    ["null", "null"],
    ["array", "[]"],
    ["nested", '{"version":{}}'],
    ["trailing-comma", JSON.stringify(record()).slice(0, -1) + ",}"],
    ["trailing-junk", JSON.stringify(record()) + "x"],
    ["two-records", JSON.stringify(record()) + JSON.stringify(record())],
    ["truncated", JSON.stringify(record()).slice(0, -3)],
    [
        "non-json-number",
        JSON.stringify(record()).replace('"version":1', '"version":NaN'),
    ],
    ["utf8-bom", "\ufeff" + JSON.stringify(record())],
])
    register("budget-decoder", `malformed:${name}`, async () => {
        const h = sandbox();
        h.control.recordBytes = Buffer.from(text);
        await rejectedAdmission(h);
    });
register("budget-decoder", "fatal-invalid-utf8", async () => {
    const h = sandbox();
    h.control.recordBytes = Buffer.from([0xc3, 0x28]);
    await rejectedAdmission(h);
});
register("budget-decoder", "raw-byte-ceiling-4096", async () => {
    const h = sandbox();
    h.control.recordBytes = Buffer.concat([
        recordBytes(),
        Buffer.alloc(4097, 32),
    ]);
    await rejectedAdmission(h);
});
register(
    "budget-decoder",
    "valid-JSON-exactly4096-raw-bytes-remains-admissible",
    async () => {
        const h = sandbox(),
            bytes = recordBytes();
        h.control.recordBytes = Buffer.concat([
            bytes,
            Buffer.alloc(4096 - bytes.length, 32),
        ]);
        const out = h.track(h.api.admit());
        await h.finish(out);
        assert.equal(out.ok, true);
    },
);
register(
    "budget-startup",
    "missing-record-does-not-create-repair-or-launch",
    async () => {
        const h = sandbox();
        h.control.recordError = true;
        await rejectedAdmission(h);
    },
);
for (const [key, value] of [
    ["version", 2],
    ["kind", "selected_scene_budget_v1"],
    ["source_revision", "b".repeat(40)],
    ["source_revision", revision.toUpperCase()],
    ["source_revision", "a".repeat(39)],
    ["target_path_sha256", "0".repeat(64)],
    ["target_path_sha256", record().target_path_sha256.toUpperCase()],
    ["cumulative_limit_bytes", 512 * MiB],
    ["external_evidence_bytes", 512 * MiB + 1],
    ["original_target_bytes", 1001],
])
    register(
        "budget-decoder",
        `binding-or-constant:${key}:${String(value)}`,
        async () => {
            const h = sandbox();
            h.control.recordBytes = recordBytes({ [key]: value });
            await rejectedAdmission(h);
        },
    );
for (const key of [
    "original_target_bytes",
    "external_evidence_bytes",
    "d05_external_evidence_bytes",
    "cumulative_limit_bytes",
])
    for (const value of [-1, 0.5, Number.MAX_SAFE_INTEGER + 1, "0", null])
        register(
            "budget-decoder",
            `unsafe-count:${key}:${String(value)}`,
            async () => {
                const h = sandbox();
                h.control.recordBytes = recordBytes({ [key]: value });
                await rejectedAdmission(h);
            },
        );
// With prior selected4 <=512MiB, the two admission headroom failures can be
// coupled: joint640MiB minus paging128MiB is exactly that preserved512MiB cap.
// Test paging-only refusal and the coupled refusal without claiming impossible
// independent joint-only startup inputs. measureStorage tests each sum directly.
for (const which of [
    "paging-only",
    "coupled-joint-and-paging",
    "sum-overflow",
    "original-target-growth",
])
    register("budget-startup", `headroom:${which}`, async () => {
        const h = sandbox();
        if (which === "paging-only") {
            h.control.recordBytes = recordBytes({ external_evidence_bytes: 0 });
            h.control.footprints[paths.base].bytes = 64 * MiB + 1;
        }
        if (which === "coupled-joint-and-paging") {
            h.control.recordBytes = recordBytes({
                external_evidence_bytes: 512 * MiB,
            });
            h.control.footprints[paths.base].bytes = 64 * MiB + 1;
        }
        if (which === "sum-overflow")
            h.control.recordBytes = recordBytes({
                d05_external_evidence_bytes: Number.MAX_SAFE_INTEGER,
            });
        if (which === "original-target-growth")
            h.control.footprints[paths.target].bytes =
                1000 + limits.targetGrowth + 1;
        await rejectedAdmission(h);
    });
register(
    "budget-startup",
    "exact-dual-headroom-and-original-target-not-current-baseline",
    async () => {
        const h = sandbox();
        h.control.recordBytes = recordBytes({
            external_evidence_bytes: 512 * MiB,
        });
        h.control.footprints[paths.base].bytes = 64 * MiB;
        h.control.footprints[paths.target].bytes = 1000 + limits.targetGrowth;
        const out = h.track(h.api.admit());
        await h.finish(out);
        assert.equal(out.ok, true);
        assert.equal(out.value.initialStorage.target.bytes, 1000);
        assert.equal(out.value.initialStorage.evidence.bytes, 576 * MiB);
        assert.equal(out.value.initialStorage.pagingEvidence.bytes, 64 * MiB);
    },
);
register(
    "budget-startup",
    "D05-external-counted-with-base-exactly-once",
    async () => {
        const h = sandbox();
        h.control.recordBytes = recordBytes({
            d05_external_evidence_bytes: 8 * MiB,
        });
        const out = h.track(h.api.admit());
        await h.finish(out);
        assert.equal(out.ok, true);
        assert.equal(out.value.initialStorage.evidence.bytes, 496 * MiB);
        assert.equal(out.value.initialStorage.pagingEvidence.bytes, 16 * MiB);
    },
);
for (const which of [
    "relative-target",
    "foreign-target",
    "invalid-revision",
    "negative-current",
    "unsafe-current",
    "nonbuffer",
])
    register(
        "budget-decoder",
        `actual-decoder-parameter:${which}`,
        async () => {
            const h = sandbox(),
                out = h.track(h.api.admit());
            await h.finish(out);
            assert.equal(out.ok, true);
            const decoder = out.value.checkedPagingBudget;
            const target =
                which === "relative-target"
                    ? "relative-target"
                    : which === "foreign-target"
                      ? "D:\\synthetic-d05\\other-target"
                      : paths.target;
            assert.throws(() =>
                decoder(
                    which === "nonbuffer"
                        ? JSON.stringify(record())
                        : recordBytes(),
                    which === "invalid-revision" ? "not-a-revision" : revision,
                    target,
                    which === "negative-current"
                        ? -1
                        : which === "unsafe-current"
                          ? Number.MAX_SAFE_INTEGER + 1
                          : 1000,
                ),
            );
        },
    );
register(
    "budget-decoder",
    "target-hash-binds-case-folded-resolved-path-without-changing-record",
    async () => {
        const h = sandbox(),
            out = h.track(h.api.admit());
        await h.finish(out);
        assert.equal(out.ok, true);
        const projected = out.value.checkedPagingBudget(
            recordBytes(),
            revision,
            paths.target.toUpperCase(),
            1000,
        );
        assert.deepEqual(plain(projected), {
            originalTargetBytes: 1000,
            externalEvidenceBytes: 480 * MiB,
            d05ExternalEvidenceBytes: 0,
        });
    },
);

const results = [];
if (blocks && !setup.length)
    try {
        sandbox();
    } catch (error) {
        setup.push({
            stage: "actual-helper-vm-registration",
            error: String(error?.message ?? error).slice(0, 500),
            classification: "SETUP_UNRUN; no behavioral result",
        });
    }
for (const item of cases) {
    if (setup.length) continue;
    try {
        await item.body();
        results.push({ group: item.group, name: item.name, passed: true });
    } catch (error) {
        if (error?.code === "D05_FAKE_FAULT_SETUP_UNREACHED")
            setup.push({
                stage: "intended-fake-fault-readiness",
                name: item.name,
                details: error.details,
                classification:
                    "SETUP_UNRUN; intended child/timer boundary not reached, no timeout result",
            });
        else
            results.push({
                group: item.group,
                name: item.name,
                passed: false,
                error: String(error?.message ?? error).slice(0, 600),
            });
    }
}
if (source)
    assert.equal(
        hash(await readFile(sourceUrl, "utf8")),
        hash(source),
        "ActualLauncherSourceUnchanged",
    );
const groups = Object.fromEntries(
    [...new Set(cases.map((v) => v.group))].map((group) => [
        group,
        cases.filter((v) => v.group === group).length,
    ]),
);
const report = {
    version: 1,
    kind: "d05_v2_inspector_paging_process_first_v1",
    contract:
        "a76c500a; exact private shapes893e5824; actual Git/inventory seams1bd234fc (all accepted before FIRST freeze)",
    sourceSHA256: source ? hash(source) : null,
    extractedSHA256: blocks
        ? Object.fromEntries(
              Object.entries(blocks).map(([key, value]) => [key, hash(value)]),
          )
        : null,
    setup,
    authored: cases.length,
    executed: results.length,
    passed: results.filter((v) => v.passed).length,
    failed: results.filter((v) => !v.passed).length,
    groups,
    checks: results,
    evidence:
        "Actual future D05 launcher helper/inventory/startup/global-finally text. Disclosed VM children/timers/files/hash/process dependency doubles. No copied policy implementation.",
    limits: [
        "Source author freeze is uncompiled/unrun. Root separately registers/executes.",
        "VM source trust/extraction is not a general script service or hostile-code sandbox.",
        "Actual inventory body sees fake entries/lstat; the entry-overflow case reduces only the VM limit to3. No real two-million-file traversal, physical D/ancestor path or OS reparse qualification.",
        "No actual wall-clock timeout, child or descendant containment, disk capacity, model/SDK/OS measurement, native IPC, browser/DOM/focus/render or runtime acceptance.",
        "The budget record is a coordinator declaration; this does not independently inventory external retained roots.",
        "Missing future file/helper/marker or unreachable intended fault boundary produces nonpassing SETUP_UNRUN, never fake RED or zero-case PASS.",
    ],
};
console.log(JSON.stringify(report));
if (setup.length || report.failed || report.executed !== report.authored)
    process.exitCode = 1;
