// Independent FIRST: D09 contract a23a6c46, original proposal 92021f6e.
// SOURCE AUTHOR UNRUN. Actual module/driver/preambles, same-realm DTOs; all
// filesystem/child/Git/timer observations below are disclosed in-memory doubles.
// No real child, directory, file, build product, admission or native app is made.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { EventEmitter } from "node:events";
import path from "node:path";
import * as url from "node:url";
import vm from "node:vm";
import { transform } from "esbuild";

assert.equal(process.argv.length, 2, "ClosedFrontendEvidenceReviewArguments");
const sourceRoot = url.fileURLToPath(new URL(".", import.meta.url));
const P = path.win32,
    M = 1024 * 1024,
    REV = "a".repeat(40);
const SRC = "D:\\d09-source",
    OUT = "D:\\d09-evidence",
    ADMISSION = "D:\\d09-admission.json";
const NEW_STEP = "check-frontend-evidence-policy-review.mjs";
const MODULE = "frontend-evidence-policy.mjs",
    DRIVER = "verify-frontend.mjs";
const expectedLimits = Object.freeze({
    outputBytes: 64 * M,
    cumulativeBytes: 640 * M,
    productBytes: 16 * M,
    stepReserveBytes: 4 * M,
    metadataReserveBytes: M,
    entries: 2000000,
    streamBytes: 262144,
    childMs: 240000,
    stopGraceMs: 5000,
    consoleBytes: 4 * M,
    summaryBytes: 32768,
});
const fields = [
    "version",
    "kind",
    "source_revision",
    "output_path_sha256",
    "initial_output_bytes",
    "output_limit_bytes",
    "external_evidence_bytes",
    "cumulative_limit_bytes",
];
const snapshotKeys = [
    "activeIndex",
    "currentBytes",
    "error",
    "initialBytes",
    "nextIndex",
    "productBytes",
    "status",
];
const setup = [],
    tests = [],
    results = [],
    source = {};
const sha = (value) => createHash("sha256").update(value).digest("hex");
const clone = (value) => structuredClone(value);
const test = (group, name, run) => tests.push({ group, name, run });
const flush = async () => {
    for (let n = 0; n < 100; n++) await Promise.resolve();
};
const fail = (code = "ENOENT") => Object.assign(Error(code), { code });
function key(value) {
    if (value instanceof URL)
        value = decodeURIComponent(value.pathname).replace(
            /^\/([A-Za-z]:)/,
            "$1",
        );
    return P.resolve(String(value));
}
const inside = (a, b) =>
    key(a).toLowerCase() === key(b).toLowerCase() ||
    key(a)
        .toLowerCase()
        .startsWith(key(b).toLowerCase() + "\\");
const pathDigest = (output = OUT) => sha(key(output).toLowerCase());
function record(patch = {}) {
    return {
        version: 1,
        kind: "d09_frontend_evidence_admission_v1",
        source_revision: REV,
        output_path_sha256: pathDigest(),
        initial_output_bytes: 0,
        output_limit_bytes: 8 * M,
        external_evidence_bytes: 1024,
        cumulative_limit_bytes: 640 * M,
        ...patch,
    };
}
const encode = (value) => Buffer.from(JSON.stringify(value) + "\n");
const goodOutcome = (patch = {}) => ({
    code: 0,
    closed: true,
    timedOut: false,
    truncated: false,
    error: false,
    stdoutBytes: 0,
    stderrBytes: 0,
    ...patch,
});
function checkedSnapshot(value, expected = {}) {
    assert.deepEqual(
        Object.keys(value).sort(),
        snapshotKeys,
        "ClosedSevenKeySnapshot",
    );
    for (const [k, v] of Object.entries(expected))
        assert.deepEqual(value[k], v, `Snapshot:${k}`);
    return value;
}
async function rejects(action, categories) {
    const allowed = (Array.isArray(categories) ? categories : [categories]).map(
        (c) => `FrontendEvidence${c}`,
    );
    await assert.rejects(
        typeof action === "function" ? action : () => action,
        (error) => allowed.includes(error?.message),
        `Expected:${allowed.join("|")}`,
    );
}
function parseReject(api, bytes, revision = REV, digest = pathDigest()) {
    assert.throws(
        () => api.parseFrontendEvidenceAdmission(bytes, revision, digest),
        (error) => error?.message === "FrontendEvidenceAdmission",
    );
}

// Numeric metadata may represent large files without allocating their bodies.
// Only the bounded admission and normal-bundle body are read by the real code.
function world({
    initial = 0,
    products = 0,
    limit = 8 * M,
    external = 1024,
} = {}) {
    const nodes = new Map(),
        events = [],
        writes = [],
        held = [],
        logs = [];
    let inode = 1,
        fault = null,
        hold = null;
    const add = (where, node) => {
        nodes.set(key(where).toLowerCase(), {
            dev: 1,
            ino: inode++,
            real: key(where),
            ...node,
        });
    };
    const dir = (where) => {
        where = key(where);
        const parent = P.dirname(where);
        if (parent !== where && !nodes.has(parent.toLowerCase())) dir(parent);
        add(where, { type: "dir", size: 0 });
        return where;
    };
    const file = (where, size, bytes = Buffer.alloc(0)) => {
        if (!nodes.has(P.dirname(key(where)).toLowerCase()))
            dir(P.dirname(key(where)));
        add(where, { type: "file", size, bytes: Buffer.from(bytes) });
    };
    dir(SRC);
    dir(OUT);
    dir(P.join(OUT, "_tmp"));
    if (initial) file(P.join(OUT, "retained.bin"), initial);
    if (products)
        file(P.join(SRC, "dist", "app.js"), products, "safe normal bundle");
    const admission = record({
        initial_output_bytes: initial,
        output_limit_bytes: limit,
        external_evidence_bytes: external,
    });
    file(ADMISSION, encode(admission).length, encode(admission));
    const get = (where) => {
        const value = nodes.get(key(where).toLowerCase());
        if (!value) throw fail();
        return value;
    };
    const stats = (where) => {
        const n = get(where);
        return {
            size: n.size,
            dev: n.dev,
            ino: n.ino,
            mode: n.type === "dir" ? 0o40755 : 0o100644,
            isDirectory: () => n.type === "dir",
            isFile: () => n.type === "file",
            isSymbolicLink: () => n.type === "link",
            isFIFO: () => n.type === "other",
            isSocket: () => false,
            isBlockDevice: () => false,
            isCharacterDevice: () => false,
        };
    };
    const observe = async (operation, where, action) => {
        events.push({ kind: "fs", operation, path: key(where) });
        if (fault && fault.operation === operation) {
            fault = null;
            throw fail("EACCES");
        }
        if (hold && hold.operation === operation) {
            const current = hold;
            hold = null;
            current.entered = true;
            await new Promise((resolve) => {
                current.release = resolve;
                held.push(current);
            });
        }
        return action();
    };
    const read = (where, options) => {
        const node = get(where);
        if (node.type !== "file") throw fail("EISDIR");
        const bytes = Buffer.from(node.bytes ?? []);
        const encoding =
            typeof options === "string" ? options : options?.encoding;
        return encoding ? bytes.toString(encoding) : bytes;
    };
    const fs = {
        lstat: (where) => observe("lstat", where, () => stats(where)),
        stat: (where) => observe("stat", where, () => stats(where)),
        realpath: (where) => observe("realpath", where, () => get(where).real),
        readFile: (where, options) =>
            observe("readFile", where, () => read(where, options)),
        readdir: (where, options) =>
            observe("readdir", where, () => {
                if (get(where).type !== "dir") throw fail("ENOTDIR");
                const entries = [...nodes].filter(
                    ([name]) =>
                        name !== key(where).toLowerCase() &&
                        P.dirname(name) === key(where).toLowerCase(),
                );
                return entries.map(([name, n]) =>
                    options?.withFileTypes
                        ? {
                              name: P.basename(name),
                              isFile: () => n.type === "file",
                              isDirectory: () => n.type === "dir",
                              isSymbolicLink: () => n.type === "link",
                          }
                        : P.basename(name),
                );
            }),
        open: async (where, flags) => {
            assert(["r", 0].includes(flags), "PolicyHasNoWriteAdmission");
            get(where);
            return {
                stat: async () => stats(where),
                readFile: async (options) => read(where, options),
                async read(buffer, offset = 0, length, position = 0) {
                    if (
                        !Buffer.isBuffer(buffer) &&
                        !(buffer instanceof Uint8Array)
                    ) {
                        const options = buffer ?? {};
                        buffer =
                            options.buffer ??
                            Buffer.alloc(options.length ?? 16384);
                        offset = options.offset ?? 0;
                        length = options.length ?? buffer.length - offset;
                        position = options.position ?? 0;
                    }
                    length ??= buffer.length - offset;
                    const data = read(where);
                    const bytesRead = data.copy(
                        buffer,
                        offset,
                        position,
                        position + length,
                    );
                    return { bytesRead, buffer };
                },
                async close() {},
            };
        },
    };
    for (const operation of [
        "mkdir",
        "writeFile",
        "appendFile",
        "unlink",
        "rm",
        "rename",
        "copyFile",
    ])
        fs[operation] = async (...args) => {
            writes.push({ operation, args });
            throw Error("UnexpectedPolicyFilesystemMutation");
        };
    const sync = {
        constants: { O_RDONLY: 0 },
        ...fs,
        mkdirSync(where, options) {
            events.push({ kind: "preamble-mkdir", path: key(where), options });
        },
        writeFileSync() {
            throw Error("RoutingPreambleMustNotRunBundleBody");
        },
    };
    return {
        nodes,
        events,
        writes,
        held,
        logs,
        fs,
        sync,
        dir,
        file,
        get,
        admission,
        remove: (where) => nodes.delete(key(where).toLowerCase()),
        faultNext(operation) {
            fault = { operation };
        },
        holdNext(operation) {
            hold = { operation, entered: false, release: null };
            return hold;
        },
        replaceAdmission(value) {
            const bytes = encode(value);
            file(ADMISSION, bytes.length, bytes);
        },
        bytes() {
            return JSON.stringify(
                [...nodes].map(([name, n]) => [
                    name,
                    n.type,
                    n.size,
                    n.dev,
                    n.ino,
                    n.real,
                    n.bytes?.toString("hex"),
                ]),
            );
        },
    };
}

// Closed builtin substitutions, not a production injection seam. CommonJS runs
// in this test's realm; strict transport prototypes are never patched/injected.
let moduleCode, driverParts, scaledModuleCode, scaledEntryProof;
function loadCjs(code, doubles) {
    const module = { exports: {} };
    const require = (name) => {
        if (!Object.hasOwn(doubles.imports, name))
            throw Error(`UNRUN_SETUP:UndisclosedImport:${name}`);
        return doubles.imports[name];
    };
    const invoke = vm.compileFunction(
        code,
        [
            "require",
            "module",
            "exports",
            "process",
            "console",
            "setTimeout",
            "clearTimeout",
            "Date",
        ],
        { filename: "actual-d09-source-review.cjs" },
    );
    invoke(
        require,
        module,
        module.exports,
        doubles.process,
        doubles.console,
        doubles.setTimeout,
        doubles.clearTimeout,
        doubles.Date ?? Date,
    );
    return module.exports;
}
function importsFor(w, extra = {}) {
    const urlDouble = {
        ...url,
        fileURLToPath: (v) => key(v),
        pathToFileURL: (v) =>
            new URL(`file:///${key(v).replaceAll("\\", "/")}`),
    };
    const closed = (value, label) =>
        new Proxy(value, {
            get(target, name) {
                if (Reflect.has(target, name)) return Reflect.get(target, name);
                if (name === "__esModule" || typeof name === "symbol")
                    return undefined;
                throw Error(
                    `UNRUN_SETUP:Undisclosed${label}API:${String(name)}`,
                );
            },
        });
    const promises = closed(w.fs, "FsPromise");
    return {
        "node:fs/promises": promises,
        "node:fs": closed({ ...w.sync, promises }, "Fs"),
        "node:path": P,
        "node:url": urlDouble,
        "node:crypto": {
            createHash,
            randomUUID: () => "11111111-2222-4333-8444-555555555555",
        },
        "node:assert/strict": assert,
        ...extra,
    };
}
function moduleFor(w, code = moduleCode) {
    return loadCjs(code, {
        imports: importsFor(w),
        process: { platform: "win32", env: {} },
        console,
        setTimeout,
        clearTimeout,
    });
}
async function opened(w = world(), code = moduleCode) {
    const api = moduleFor(w, code);
    const policy = await api.openFrontendEvidencePolicy({
        sourceRoot: SRC,
        outputDir: OUT,
        admissionFile: ADMISSION,
        sourceRevision: REV,
    });
    assert.deepEqual(Object.keys(policy).sort(), [
        "beforeStep",
        "completeStep",
        "finish",
        "snapshot",
    ]);
    return { w, api, policy };
}
async function completed(policy, index = 0) {
    await policy.beforeStep(index);
    return policy.completeStep(index, goodOutcome());
}

function clock() {
    let now = 0,
        id = 0;
    const timers = new Map();
    return {
        get now() {
            return now;
        },
        set(callback, delay = 0) {
            const token = {
                id: ++id,
                unref() {
                    return this;
                },
            };
            timers.set(token, { callback, at: now + Number(delay) });
            return token;
        },
        clear(token) {
            timers.delete(token);
        },
        next() {
            const selected = [...timers].sort((a, b) => a[1].at - b[1].at)[0];
            if (!selected) return false;
            timers.delete(selected[0]);
            now = selected[1].at;
            selected[1].callback();
            return true;
        },
        get pending() {
            return timers.size;
        },
    };
}
async function driver({
    args = ["--bounded"],
    script = () => ({}),
    w = world({ products: 16 }),
    env = {},
} = {}) {
    const timer = clock(),
        calls = [],
        logs = [],
        policies = [];
    let nodes = 0,
        git = 0,
        completedRun = false,
        error = null;
    const fakeProcess = {
        argv: [process.execPath, "verify-frontend.mjs", ...args],
        execPath: process.execPath,
        platform: "win32",
        env: {
            LOCALLORE_CHECK_OUTPUT_DIR: OUT,
            LOCALLORE_CHECK_BUDGET_FILE: ADMISSION,
            ...env,
        },
        exitCode: 0,
        stdout: {
            write: (text) => {
                logs.push(String(text));
                return true;
            },
        },
        stderr: {
            write: (text) => {
                logs.push(String(text));
                return true;
            },
        },
        exit(code) {
            this.exitCode = code;
            throw Error(`ReviewProcessExit:${code}`);
        },
    };
    const spawn = (command, argv, options) => {
        const isGit =
            P.basename(String(command))
                .toLowerCase()
                .replace(/\.exe$/, "") === "git";
        const index = isGit ? git++ : nodes++;
        const specification =
            script({ isGit, index, command, args: argv, options, w }) ?? {};
        const entry = {
            command,
            args: clone(argv),
            options,
            isGit,
            index,
            kills: 0,
            closed: false,
            exit: false,
        };
        calls.push(entry);
        w.events.push({
            kind: isGit ? "git" : "child",
            index,
            args: clone(argv),
        });
        if (specification.spawnThrows) throw Error("SyntheticSpawnFailure");
        const child = new EventEmitter();
        child.stdout = new EventEmitter();
        child.stderr = new EventEmitter();
        child.pid = calls.length + 100;
        const close = () => {
            if (entry.closed) return;
            entry.closed = true;
            specification.beforeClose?.(w);
            child.emit(
                "close",
                Object.hasOwn(specification, "code") ? specification.code : 0,
                specification.signal ?? null,
            );
        };
        child.kill = () => {
            entry.kills++;
            if (specification.killThrows) throw Error("SyntheticKillFailure");
            if (specification.closeOnKill)
                timer.set(close, specification.closeDelay ?? 1);
            return !specification.killFalse;
        };
        queueMicrotask(() => {
            try {
                let stdout = specification.stdout;
                if (isGit && stdout === undefined)
                    stdout = argv.includes("rev-parse") ? `${REV}\n` : "";
                if (stdout !== undefined)
                    child.stdout.emit("data", Buffer.from(stdout));
                if (specification.stderr !== undefined)
                    child.stderr.emit(
                        "data",
                        Buffer.from(specification.stderr),
                    );
                if (specification.streamError)
                    child[specification.streamError].emit(
                        "error",
                        Error("SyntheticPipeError"),
                    );
                if (specification.error)
                    child.emit("error", Error("SyntheticChildError"));
                if (specification.exitOnly) {
                    entry.exit = true;
                    child.emit("exit", 0, null);
                } else if (!specification.noClose) close();
            } catch (value) {
                entry.uncaughtEvent = String(value);
            }
        });
        return child;
    };
    const actual = moduleFor(w);
    const observed = {
        ...actual,
        async openFrontendEvidencePolicy(options) {
            const policy = await actual.openFrontendEvidencePolicy(options);
            policies.push(policy);
            return policy;
        },
    };
    const log = (...values) =>
        logs.push(
            values
                .map((v) => (typeof v === "string" ? v : JSON.stringify(v)))
                .join(" ") + "\n",
        );
    const fakeConsole = { log, error: log, warn: log, info: log };
    const FrozenDate = class extends Date {
        static now() {
            return timer.now;
        }
    };
    const api = loadCjs(driverParts, {
        imports: importsFor(w, {
            "node:child_process": { spawn },
            "./frontend-evidence-policy.mjs": observed,
            "node:process": fakeProcess,
        }),
        process: fakeProcess,
        console: fakeConsole,
        setTimeout: timer.set,
        clearTimeout: timer.clear,
        Date: FrozenDate,
    });
    const pending = Promise.resolve()
        .then(() => api.__reviewDriver())
        .then(
            () => {
                completedRun = true;
            },
            (value) => {
                error = value;
                completedRun = true;
            },
        );
    for (let n = 0; n < 1200 && !completedRun; n++) {
        await flush();
        if (!completedRun) timer.next();
    }
    assert(
        completedRun,
        "ActualDriverMustSettleWithinDisclosedFakeTimerBudget",
    );
    await pending;
    assert(
        !calls.some((entry) => entry.uncaughtEvent),
        "ActualChildAndPipeEventsMustNotThrowUnhandled",
    );
    return {
        w,
        calls,
        logs,
        policies,
        fakeProcess,
        error,
        timer,
        nodeCalls: calls.filter((c) => !c.isGit),
        gitCalls: calls.filter((c) => c.isGit),
        text: logs.join(""),
        bundleReads: w.events.filter(
            (e) =>
                e.kind === "fs" &&
                e.operation === "readFile" &&
                key(e.path) === key(P.join(SRC, "dist", "app.js")),
        ),
    };
}
function globalSuccess(r) {
    // The actual driver's terminal message is an unquoted line. A JSON child
    // receipt may legitimately retain the same words inside stdout/stderr.
    const terminal =
        "PASS: strict TypeScript, current request/schema checks, and no development journey/control hooks in normal frontend.";
    return r.logs.some((text) => {
        if (text.split(/\r?\n/).some((line) => line === terminal)) return true;
        let value;
        try {
            value = JSON.parse(text);
        } catch {
            return false;
        }
        if (value?.kind !== "d09_frontend_evidence_run_v1") return false;
        assert.equal(
            typeof value.passed,
            "boolean",
            "OverallReceiptPassedMustBeBoolean",
        );
        assert(
            Number.isSafeInteger(value.completedSteps) &&
                value.completedSteps >= 0 &&
                value.completedSteps <= 77,
            "OverallReceiptCompletedStepsMustBeBoundedSafeInteger",
        );
        return value.passed;
    });
}
function noDriverSuccess(r) {
    assert(
        r.error || r.fakeProcess.exitCode !== 0,
        "ActualDriverFailureMustNotExitSuccessful",
    );
    assert(!globalSuccess(r), "NoGlobalTerminalPassAfterFailure");
    assert.equal(r.bundleReads.length, 0, "NoNormalBundleReadAfterFailure");
}
function failureStops(r, expectedChildren = 1) {
    noDriverSuccess(r);
    assert.equal(r.nodeCalls.length, expectedChildren);
    assert.equal(
        r.gitCalls.length,
        2,
        "OnlyInitialReadOnlyGitBeforeFailedStep",
    );
    assert(
        r.calls.every((c) => c.kills <= 1),
        "AtMostOneStopAttemptPerOwnedChild",
    );
    assert.equal(r.timer.pending, 0, "AllOwnedDeadlineAndDrainTimersRetired");
}
function loggedObjects(logs) {
    const found = [];
    const visit = (value, depth = 0) => {
        if (!value || typeof value !== "object" || depth > 16) return;
        found.push(value);
        for (const item of Object.values(value)) visit(item, depth + 1);
    };
    for (const text of logs) {
        try {
            visit(JSON.parse(text));
        } catch {
            /* Non-JSON legacy message. */
        }
    }
    return found;
}

// Actual-source top-level-await adaptation only. Imports stay imports and every
// original body statement executes; no scheduler/decoder/policy is copied here.
async function compile(text, filename, wrapped = false, tail = "") {
    const importPattern = /^import\s[\s\S]*?;\s*(?:\r?\n|$)/gm;
    const imports = [...text.matchAll(importPattern)]
        .map((m) => m[0])
        .join("\n");
    let body = text
        .replace(importPattern, "")
        .replaceAll(
            "import.meta.url",
            JSON.stringify(`file:///D:/d09-source/${filename}`),
        );
    const contents = wrapped
        ? `${imports}\nexport async function __reviewDriver(){\n${body}\n${tail}\n}`
        : text;
    return (
        await transform(contents, {
            loader: "js",
            format: "cjs",
            platform: "node",
            target: "node24",
            sourcefile: filename,
        })
    ).code;
}

// CASES follow. All quantities below are synthetic metadata, not disk charges.
test("record", "actual-immutable-closed-limits", () => {
    const api = moduleFor(world());
    assert.deepEqual(api.FRONTEND_EVIDENCE_LIMITS, expectedLimits);
    assert(Object.isFrozen(api.FRONTEND_EVIDENCE_LIMITS));
});
test("record", "canonical-eight-key-bytes-and-detached-result", () => {
    const api = moduleFor(world()),
        raw = encode(record());
    const value = api.parseFrontendEvidenceAdmission(raw, REV, pathDigest());
    assert.deepEqual(Object.keys(value), fields);
    assert.equal(JSON.stringify(value), JSON.stringify(record()));
    raw.fill(0);
    try {
        value.initial_output_bytes = 17;
    } catch {
        /* Frozen is also detached. */
    }
    assert.equal(
        JSON.stringify(
            api.parseFrontendEvidenceAdmission(
                encode(record()),
                REV,
                pathDigest(),
            ),
        ),
        JSON.stringify(record()),
    );
});
for (const [name, mutate] of [
    ["duplicate", (s) => s.replace('"version":1', '"version":1,"version":1')],
    ["escaped-key", (s) => s.replace('"version"', '"\\u0076ersion"')],
    ["unknown-key", (s) => s.replace("{", '{"unknown":0,')],
    ["missing-key", (s) => s.replace('"version":1,', "")],
    [
        "key-order",
        () =>
            JSON.stringify(
                Object.fromEntries(Object.entries(record()).reverse()),
            ) + "\n",
    ],
    ["no-LF", (s) => s.trimEnd()],
    ["second-LF", (s) => s + "\n"],
    ["space", (s) => " " + s],
    ["BOM", (s) => "\ufeff" + s],
    ["trailing-json", (s) => s + "{}"],
    ["alternate-number", (s) => s.replace('"version":1', '"version":1.0')],
    [
        "negative-zero",
        (s) =>
            s.replace('"initial_output_bytes":0', '"initial_output_bytes":-0'),
    ],
])
    test("record", name, () =>
        parseReject(
            moduleFor(world()),
            Buffer.from(mutate(encode(record()).toString("utf8"))),
        ),
    );
for (const [name, patch] of [
    ["version", { version: 2 }],
    ["kind", { kind: "other" }],
    ["revision-uppercase", { source_revision: "A".repeat(40) }],
    ["revision-length", { source_revision: "a".repeat(39) }],
    ["path-uppercase", { output_path_sha256: "A".repeat(64) }],
    ["path-length", { output_path_sha256: "a".repeat(63) }],
    ["negative", { initial_output_bytes: -1 }],
    ["unsafe", { external_evidence_bytes: Number.MAX_SAFE_INTEGER + 1 }],
    ["fraction", { initial_output_bytes: 0.5 }],
    ["numeric-string", { external_evidence_bytes: "1024" }],
    ["null", { initial_output_bytes: null }],
    ["output-limit", { output_limit_bytes: 64 * M + 1 }],
    ["reserve-too-small", { output_limit_bytes: 5 * M - 1 }],
    ["aggregate-limit", { cumulative_limit_bytes: 640 * M + 1 }],
])
    test("record", name, () =>
        parseReject(moduleFor(world()), encode(record(patch))),
    );
test("record", "fatal-UTF8-and4096-total-byte-cap", () => {
    const api = moduleFor(world());
    parseReject(api, Buffer.from([0xff]));
    parseReject(api, Buffer.alloc(4097, 32));
});
test("record", "actual-source-and-output-digest-fences", () => {
    const api = moduleFor(world());
    parseReject(api, encode(record()), "b".repeat(40));
    parseReject(api, encode(record()), REV, "b".repeat(64));
});

test(
    "path",
    "nonempty-output-and-live-products-measured-without-mutation",
    async () => {
        const w = world({ initial: 8192, products: 23 }),
            before = w.bytes(),
            { policy } = await opened(w);
        checkedSnapshot(policy.snapshot(), {
            status: "ready",
            nextIndex: 0,
            activeIndex: null,
            initialBytes: 8192,
            currentBytes: 8192,
            productBytes: 23,
            error: null,
        });
        assert.equal(w.bytes(), before);
        assert.deepEqual(w.writes, []);
    },
);
for (const [name, mutate, options = {}] of [
    ["output-missing", (w) => w.remove(OUT)],
    ["output-file", (w) => (w.get(OUT).type = "file")],
    ["output-link", (w) => (w.get(OUT).type = "link")],
    ["output-alias", (w) => (w.get(OUT).real = "D:\\alias")],
    [
        "output-non-D",
        (w) => {
            w.dir("C:\\evidence");
            w.dir("C:\\evidence\\_tmp");
        },
        { outputDir: "C:\\evidence" },
    ],
    [
        "output-inside-source",
        (w) => {
            w.dir(P.join(SRC, "evidence", "_tmp"));
        },
        { outputDir: P.join(SRC, "evidence") },
    ],
    [
        "source-inside-output",
        (w) => {
            w.dir(P.join(OUT, "source"));
        },
        { sourceRoot: P.join(OUT, "source") },
    ],
    [
        "admission-inside-output",
        (w) => {
            w.file(P.join(OUT, "record.json"), 2, "{}");
        },
        { admissionFile: P.join(OUT, "record.json") },
    ],
    [
        "admission-inside-source",
        () => {},
        { admissionFile: P.join(SRC, "record.json") },
    ],
    ["tmp-missing", (w) => w.remove(P.join(OUT, "_tmp"))],
    ["tmp-file", (w) => (w.get(P.join(OUT, "_tmp")).type = "file")],
    ["ancestor-link", (w) => (w.get("D:\\").type = "link")],
])
    test("path", name, async () => {
        const w = world();
        mutate(w);
        if (options.outputDir)
            w.replaceAdmission(
                record({ output_path_sha256: pathDigest(options.outputDir) }),
            );
        const api = moduleFor(w),
            before = w.bytes();
        await rejects(
            () =>
                api.openFrontendEvidencePolicy({
                    sourceRoot: SRC,
                    outputDir: OUT,
                    admissionFile: ADMISSION,
                    sourceRevision: REV,
                    ...options,
                }),
            ["Path", "Admission"],
        );
        assert.equal(w.bytes(), before);
        assert.deepEqual(w.writes, []);
    });
test("path", "initial-inventory-must-match-declared-baseline", async () => {
    const w = world({ initial: 7 });
    w.replaceAdmission(record({ initial_output_bytes: 6 }));
    await rejects(() => opened(w), "Admission");
});
test("path", "admission-bounded-file-type-and-byte-length", async () => {
    for (const variant of ["missing", "link", "directory", "oversize"]) {
        const w = world();
        if (variant === "missing") w.remove(ADMISSION);
        else if (variant === "oversize") w.get(ADMISSION).size = 4097;
        else w.get(ADMISSION).type = variant === "link" ? "link" : "dir";
        await rejects(() => opened(w), ["Path", "Admission"]);
    }
});
for (const [name, mutate] of [
    [
        "dist-parent-link",
        (w) => {
            w.get(P.join(SRC, "dist")).type = "link";
        },
    ],
    [
        "dist-parent-alias",
        (w) => {
            w.get(P.join(SRC, "dist")).real = "D:\\foreign-dist";
        },
    ],
    [
        "generated-leaf-link",
        (w) => {
            w.file(P.join(SRC, "ui", "host.generated.ts"), 1);
            w.get(P.join(SRC, "ui", "host.generated.ts")).type = "link";
        },
    ],
])
    test("path", name, async () => {
        const w = world({ products: 1 });
        mutate(w);
        await rejects(() => opened(w), ["Path", "Inventory"]);
        assert.deepEqual(w.writes, []);
    });
for (const [name, mutate] of [
    ["output-identity-change", (w) => w.get(OUT).ino++],
    ["source-identity-change", (w) => w.get(SRC).dev++],
    [
        "tmp-alias-change",
        (w) => (w.get(P.join(OUT, "_tmp")).real = "D:\\alias"),
    ],
    [
        "new-symlink",
        (w) => {
            w.file(P.join(OUT, "link"), 1);
            w.get(P.join(OUT, "link")).type = "link";
        },
    ],
    [
        "unsupported-entry",
        (w) => {
            w.file(P.join(OUT, "pipe"), 1);
            w.get(P.join(OUT, "pipe")).type = "other";
        },
    ],
    [
        "unsafe-size",
        (w) => w.file(P.join(OUT, "unsafe"), Number.MAX_SAFE_INTEGER + 1),
    ],
])
    test("path", name, async () => {
        const { w, policy } = await opened();
        mutate(w);
        await rejects(() => policy.beforeStep(0), ["Path", "Inventory"]);
        checkedSnapshot(policy.snapshot(), {
            status: "failed",
            currentBytes: null,
            productBytes: null,
        });
        await rejects(() => policy.finish(), ["Path", "Inventory"]);
    });

test("budget", "fixed-dist-and-host-type-products-both-count", async () => {
    const w = world({ products: 5 });
    w.file(P.join(SRC, "ui", "host.generated.ts"), 7);
    const { policy } = await opened(w);
    assert.equal(policy.snapshot().productBytes, 12);
});
test("budget", "missing-fixed-products-count-zero", async () => {
    const { policy } = await opened();
    assert.equal(policy.snapshot().productBytes, 0);
});
test("budget", "initial-product-cap-refuses", async () => {
    await rejects(
        () => opened(world({ products: 16 * M + 1 })),
        "ProductBudget",
    );
});
test("budget", "live-products-are-charged-to-joint-headroom", async () => {
    await rejects(
        () => opened(world({ products: 16 * M, external: 640 * M - 5 * M })),
        ["AggregateBudget", "Reserve"],
    );
});
test("budget", "reserve-before-first-child-output-and-joint", async () => {
    const w = world({ limit: 5 * M, external: 0 }),
        { policy } = await opened(w);
    w.file(P.join(OUT, "outside-step.bin"), 1);
    await rejects(() => policy.beforeStep(0), "Reserve");
    assert.equal(policy.snapshot().activeIndex, null);
});
test("budget", "each-step-baseline-not-original-run-baseline", async () => {
    const w = world({ limit: 64 * M }),
        { policy } = await opened(w);
    await policy.beforeStep(0);
    w.file(P.join(OUT, "first"), 3 * M);
    await policy.completeStep(0, goodOutcome());
    await policy.beforeStep(1);
    w.file(P.join(OUT, "second"), 3 * M);
    await policy.completeStep(1, goodOutcome());
    checkedSnapshot(await policy.finish(), {
        status: "finished",
        nextIndex: 2,
        currentBytes: 6 * M,
    });
});
test("budget", "exact-step-reserve-positive-growth-accepted", async () => {
    const w = world({ limit: 64 * M }),
        { policy } = await opened(w);
    await policy.beforeStep(0);
    w.file(P.join(OUT, "equal"), 3 * M);
    w.file(P.join(SRC, "dist", "product"), M);
    checkedSnapshot(await policy.completeStep(0, goodOutcome()), {
        status: "ready",
        nextIndex: 1,
    });
});
test(
    "budget",
    "positive-output-plus-product-growth-cannot-exceed-reserve",
    async () => {
        const w = world({ limit: 64 * M }),
            { policy } = await opened(w);
        await policy.beforeStep(0);
        w.file(P.join(OUT, "evidence"), 3 * M);
        w.file(P.join(SRC, "dist", "product"), M + 1);
        await rejects(
            () => policy.completeStep(0, goodOutcome()),
            "StepBudget",
        );
        w.remove(P.join(OUT, "evidence"));
        w.remove(P.join(SRC, "dist", "product"));
        await rejects(() => policy.beforeStep(1), "StepBudget");
    },
);
test("budget", "product-shrink-is-not-evidence-growth-subsidy", async () => {
    const w = world({ limit: 64 * M, products: 8 * M }),
        { policy } = await opened(w);
    await policy.beforeStep(0);
    w.get(P.join(SRC, "dist", "app.js")).size = 0;
    w.file(P.join(OUT, "growth"), 4 * M + 1);
    await rejects(() => policy.completeStep(0, goodOutcome()), "StepBudget");
});
for (const [name, options, mutate, category] of [
    [
        "output",
        { limit: 8 * M },
        (w) => w.file(P.join(OUT, "full"), 8 * M + 1),
        ["OutputBudget", "StepBudget"],
    ],
    [
        "output-metadata-reserve",
        { limit: 8 * M },
        (w) => w.file(P.join(OUT, "full"), 8 * M - M + 1),
        ["OutputBudget", "StepBudget"],
    ],
    [
        "products",
        { limit: 64 * M },
        (w) => w.file(P.join(SRC, "dist", "full"), 16 * M + 1),
        ["ProductBudget", "StepBudget"],
    ],
    [
        "aggregate",
        { limit: 64 * M, external: 640 * M - 6 * M },
        (w) => {
            w.file(P.join(OUT, "a"), 3 * M);
            w.file(P.join(SRC, "dist", "b"), 3 * M);
        },
        ["AggregateBudget", "StepBudget"],
    ],
])
    test("budget", `post-child-${name}`, async () => {
        const w = world(options),
            { policy } = await opened(w);
        await policy.beforeStep(0);
        mutate(w);
        await rejects(() => policy.completeStep(0, goodOutcome()), category);
        assert.equal(policy.snapshot().status, "failed");
        assert.equal(policy.snapshot().activeIndex, 0);
        const first = policy.snapshot().error;
        await rejects(() => policy.beforeStep(1), first);
        await rejects(() => policy.finish(), first);
        assert.equal(policy.snapshot().nextIndex, 0);
    });

test(
    "lifecycle",
    "exact-detached-seven-key-snapshots-and-index-progress",
    async () => {
        const { w, policy } = await opened(),
            before = w.bytes();
        const initial = checkedSnapshot(policy.snapshot(), {
            status: "ready",
            nextIndex: 0,
            activeIndex: null,
        });
        try {
            initial.status = "finished";
            initial.nextIndex = 90;
        } catch {
            /* Frozen is acceptable. */
        }
        checkedSnapshot(policy.snapshot(), { status: "ready", nextIndex: 0 });
        checkedSnapshot(await policy.beforeStep(0), {
            status: "running",
            nextIndex: 0,
            activeIndex: 0,
        });
        checkedSnapshot(await policy.completeStep(0, goodOutcome()), {
            status: "ready",
            nextIndex: 1,
            activeIndex: null,
        });
        checkedSnapshot(await policy.finish(), {
            status: "finished",
            nextIndex: 1,
            error: null,
        });
        assert.equal(w.bytes(), before);
        assert.deepEqual(w.writes, []);
    },
);
for (const [name, action] of [
    ["skip-index", (p) => p.beforeStep(1)],
    ["negative-index", (p) => p.beforeStep(-1)],
    ["fractional-index", (p) => p.beforeStep(0.5)],
    ["complete-before-admission", (p) => p.completeStep(0, goodOutcome())],
    ["empty-finish", (p) => p.finish()],
])
    test("lifecycle", name, async () => {
        const { policy } = await opened();
        await rejects(() => action(policy), "Sequence");
        assert.equal(policy.snapshot().status, "failed");
    });
test("lifecycle", "one-active-index-no-skip-reuse-or-finish", async () => {
    for (const action of [
        (p) => p.beforeStep(1),
        (p) => p.completeStep(1, goodOutcome()),
        (p) => p.finish(),
    ]) {
        const { policy } = await opened();
        await policy.beforeStep(0);
        await rejects(() => action(policy), "Sequence");
        checkedSnapshot(policy.snapshot(), {
            status: "failed",
            activeIndex: 0,
        });
    }
});
for (const [name, outcome, category] of [
    ["nonzero", goodOutcome({ code: 1 }), "Outcome"],
    ["signal", goodOutcome({ code: null }), "Outcome"],
    ["timeout", goodOutcome({ timedOut: true }), "Outcome"],
    ["truncated", goodOutcome({ truncated: true }), "Outcome"],
    ["error", goodOutcome({ error: true }), "Outcome"],
    ["unknown-child", goodOutcome({ closed: false }), "UnknownChild"],
    ["stdout-overflow", goodOutcome({ stdoutBytes: 262145 }), "Outcome"],
    ["stderr-overflow", goodOutcome({ stderrBytes: 262145 }), "Outcome"],
    ["extra-key", { ...goodOutcome(), extra: 0 }, "Outcome"],
    ["string-code", goodOutcome({ code: "0" }), "Outcome"],
    ["flag-type", goodOutcome({ timedOut: 0 }), "Outcome"],
    [
        "unsafe-count",
        goodOutcome({ stdoutBytes: Number.MAX_SAFE_INTEGER + 1 }),
        "Outcome",
    ],
])
    test("lifecycle", name, async () => {
        const { policy } = await opened();
        await policy.beforeStep(0);
        await rejects(() => policy.completeStep(0, outcome), category);
        const snapshot = clone(policy.snapshot());
        checkedSnapshot(snapshot, {
            status: "failed",
            activeIndex: 0,
            nextIndex: 0,
            error: category,
            ...(category === "UnknownChild"
                ? { currentBytes: null, productBytes: null }
                : {}),
        });
        await rejects(() => policy.beforeStep(0), category);
        await rejects(() => policy.completeStep(0, goodOutcome()), category);
        await rejects(() => policy.finish(), category);
        assert.deepEqual(policy.snapshot(), snapshot);
    });
test(
    "lifecycle",
    "finished-instance-is-retired-without-snapshot-mutation",
    async () => {
        const { policy } = await opened();
        await completed(policy);
        await policy.finish();
        const before = clone(policy.snapshot());
        await rejects(() => policy.beforeStep(1), "Sequence");
        await rejects(() => policy.completeStep(1, goodOutcome()), "Sequence");
        await rejects(() => policy.finish(), "Sequence");
        assert.deepEqual(policy.snapshot(), before);
    },
);
test(
    "lifecycle",
    "unavailable-inventory-nulls-both-counts-and-sticks",
    async () => {
        const { w, policy } = await opened();
        await policy.beforeStep(0);
        w.faultNext("readdir");
        await rejects(() => policy.completeStep(0, goodOutcome()), "Inventory");
        checkedSnapshot(policy.snapshot(), {
            status: "failed",
            currentBytes: null,
            productBytes: null,
            error: "Inventory",
        });
        await rejects(() => policy.finish(), "Inventory");
    },
);
for (const method of ["beforeStep", "completeStep", "finish"])
    test("lifecycle", `synchronous-inflight-guard-${method}`, async () => {
        const { w, policy } = await opened();
        if (method === "completeStep") await policy.beforeStep(0);
        if (method === "finish") await completed(policy);
        const gate = w.holdNext("readdir");
        const pending =
            method === "beforeStep"
                ? policy.beforeStep(0)
                : method === "completeStep"
                  ? policy.completeStep(0, goodOutcome())
                  : policy.finish();
        // Attach immediately so intentional later rejection is not unhandled.
        const first = Promise.resolve(pending).then(
            () => null,
            (error) => error,
        );
        for (let n = 0; n < 50 && !gate.entered; n++) await flush();
        assert(gate.entered, "ActualInventoryMustReachDisclosedHold");
        await rejects(() => policy.beforeStep(0), "Sequence");
        gate.release();
        assert.equal((await first)?.message, "FrontendEvidenceSequence");
        checkedSnapshot(policy.snapshot(), {
            status: "failed",
            error: "Sequence",
        });
    });

// ONE accepted TEST-ONLY scaled constant, with unchanged actual algorithm and
// one-literal prefix/suffix proof. Every other case uses the unmodified module.
test(
    "inventory",
    "scaled12-combined-ordinary-unique-entry-algorithm",
    async () => {
        const w = world(),
            { policy, api } = await opened(w, scaledModuleCode);
        assert.equal(api.FRONTEND_EVIDENCE_LIMITS.entries, 12);
        await policy.beforeStep(0);
        for (let index = 0; index < 6; index++) {
            w.file(P.join(OUT, `evidence-${index}`), 0);
            w.file(P.join(SRC, "dist", `product-${index}`), 0);
        }
        const outputEntries = [...w.nodes.keys()].filter((name) =>
            inside(name, OUT),
        ).length;
        const productEntries = [...w.nodes.keys()].filter((name) =>
            inside(name, P.join(SRC, "dist")),
        ).length;
        assert(
            outputEntries < 12 &&
                productEntries < 12 &&
                outputEntries + productEntries > 12,
        );
        await rejects(() => policy.completeStep(0, goodOutcome()), "Inventory");
        checkedSnapshot(policy.snapshot(), {
            status: "failed",
            activeIndex: 0,
            nextIndex: 0,
            error: "Inventory",
        });
        await rejects(() => policy.beforeStep(1), "Inventory");
        await rejects(() => policy.finish(), "Inventory");
    },
);
test(
    "inventory",
    "unsafe-combined-size-sum-refuses-without-writes",
    async () => {
        const w = world();
        w.file(P.join(OUT, "a"), Number.MAX_SAFE_INTEGER);
        w.file(P.join(OUT, "b"), Number.MAX_SAFE_INTEGER);
        await rejects(() => opened(w), ["Inventory", "OutputBudget"]);
        assert.deepEqual(w.writes, []);
    },
);
test(
    "inventory",
    "finish-rechecks-identity-and-current-metadata-reserve",
    async () => {
        const { w, policy } = await opened();
        await completed(policy);
        w.get(OUT).ino++;
        await rejects(() => policy.finish(), ["Path", "Inventory"]);
        checkedSnapshot(policy.snapshot(), {
            status: "failed",
            currentBytes: null,
            productBytes: null,
        });
    },
);
test(
    "inventory",
    "snapshot-is-read-free-and-detached-after-retirement",
    async () => {
        const { w, policy } = await opened();
        await completed(policy);
        await policy.finish();
        const count = w.events.length,
            first = policy.snapshot(),
            second = policy.snapshot();
        assert.notEqual(first, second);
        assert.deepEqual(first, second);
        assert.equal(w.events.length, count);
    },
);

function roster(r) {
    assert.equal(
        r.nodeCalls.length,
        77,
        "Exactly77FixedChecksIncludingIndependentPolicyReview",
    );
    const actual = r.nodeCalls.map((c) => c.args),
        existing = actual.filter((args) => args[0] !== NEW_STEP);
    assert.equal(actual.filter((args) => args[0] === NEW_STEP).length, 1);
    assert.equal(existing.length, 76);
    assert.equal(
        sha(JSON.stringify(existing)),
        "d021b7a801f051bac71799528cb000c5b8a6636cfa6f81cc2d615877e79a0ec0",
        "Frozen76CheckOrderAndArguments",
    );
    for (const call of r.nodeCalls) {
        assert.equal(call.command, process.execPath);
        assert.equal(call.options.shell, false);
    }
}
test(
    "driver",
    "legacy-zero-arguments-preserve-roster-and-normal-exclusions",
    async () => {
        const r = await driver({ args: [] });
        assert.equal(r.error, null);
        roster(r);
        assert.equal(r.policies.length, 0, "LegacyNeverCreatesEvidencePolicy");
        assert(r.bundleReads.length >= 1);
        assert(r.text.includes("PASS:"));
    },
);
test(
    "driver",
    "bounded77-sequential-policy-steps-and-explicit-child-environment",
    async () => {
        const r = await driver();
        assert.equal(r.error, null);
        assert.equal(r.fakeProcess.exitCode, 0);
        roster(r);
        assert.equal(r.policies.length, 1);
        checkedSnapshot(r.policies[0].snapshot(), {
            status: "finished",
            nextIndex: 77,
            activeIndex: null,
        });
        for (const call of r.nodeCalls) {
            assert.equal(call.options.windowsHide, true);
            assert.equal(call.options.env.LOCALLORE_CHECK_OUTPUT_DIR, OUT);
            assert.equal(key(call.options.env.TEMP), key(P.join(OUT, "_tmp")));
            assert.equal(call.options.env.TMP, call.options.env.TEMP);
            assert.equal(key(call.options.cwd), key(SRC));
            assert.notEqual(call.options.stdio, "inherit");
        }
        assert.equal(r.gitCalls.length, 4);
        assert(
            r.gitCalls.every(
                (c) =>
                    JSON.stringify(c.args) ===
                        JSON.stringify(["rev-parse", "HEAD"]) ||
                    JSON.stringify(c.args) ===
                        JSON.stringify(["status", "--porcelain"]),
            ),
        );
        assert(r.bundleReads.length >= 1);
        assert(r.text.includes("PASS:"));
        assert.equal(r.timer.pending, 0);
    },
);
for (const args of [[], ["--bounded"]])
    test(
        "driver",
        `actual-normal-hook-refusal-${args.length ? "bounded" : "legacy"}`,
        async () => {
            const w = world({ products: 32 });
            w.get(P.join(SRC, "dist", "app.js")).bytes =
                Buffer.from("harness_checkpoint");
            const r = await driver({ args, w });
            roster(r);
            assert(r.bundleReads.length >= 1);
            assert(r.error || r.fakeProcess.exitCode !== 0);
            assert(!r.text.includes("PASS:"));
        },
    );
for (const args of [
    ["--other"],
    ["--bounded", "--bounded"],
    ["--bounded", "chosen.mjs"],
    ["--bounded", ""],
])
    test("driver", `closed-arguments-${JSON.stringify(args)}`, async () => {
        const r = await driver({ args });
        noDriverSuccess(r);
        assert.equal(r.calls.length, 0);
    });
test(
    "driver",
    "alternate-esbuild-executable-refused-before-child",
    async () => {
        const r = await driver({
            env: { ESBUILD_BINARY_PATH: "D:\\foreign-esbuild.exe" },
        });
        noDriverSuccess(r);
        assert.equal(r.nodeCalls.length, 0);
    },
);
test("driver", "empty-esbuild-override-does-not-invent-refusal", async () => {
    const r = await driver({ env: { ESBUILD_BINARY_PATH: "" } });
    assert.equal(r.error, null);
    roster(r);
});
for (const missing of [
    "LOCALLORE_CHECK_OUTPUT_DIR",
    "LOCALLORE_CHECK_BUDGET_FILE",
])
    test("driver", `explicit-required-${missing}`, async () => {
        const r = await driver({ env: { [missing]: undefined } });
        noDriverSuccess(r);
        assert.equal(r.nodeCalls.length, 0);
    });
for (const [name, fault] of [
    [
        "dirty",
        ({ index }) => (index === 1 ? { stdout: " M changed.mjs\n" } : {}),
    ],
    [
        "malformed-head",
        ({ index }) => (index === 0 ? { stdout: "main\n" } : {}),
    ],
    ["nonzero", ({ index }) => (index === 0 ? { code: 1 } : {})],
    ["spawn-throws", ({ index }) => (index === 0 ? { spawnThrows: true } : {})],
    [
        "unknown-close",
        ({ index }) => (index === 0 ? { noClose: true, killFalse: true } : {}),
    ],
    [
        "64KiB-original-byte-overflow",
        ({ index }) => (index === 0 ? { stdout: "x".repeat(65537) } : {}),
    ],
])
    test("driver", `initial-git-${name}`, async () => {
        const r = await driver({
            script: (entry) => (entry.isGit ? fault(entry) : {}),
        });
        noDriverSuccess(r);
        assert.equal(r.nodeCalls.length, 0);
        assert(r.gitCalls.length <= 2);
        assert(r.calls.every((c) => c.kills <= 1));
        if (name === "unknown-close") {
            assert.equal(r.gitCalls.length, 1);
            assert.equal(r.gitCalls[0].closed, false);
            assert.equal(r.gitCalls[0].kills, 1);
            assert.equal(r.timer.now, 20000);
        }
    });
for (const phase of [2, 3])
    test("driver", `final-git-source-fence-${phase}`, async () => {
        const r = await driver({
            script: ({ isGit, index }) =>
                isGit && index === phase
                    ? {
                          stdout:
                              phase === 2
                                  ? "b".repeat(40) + "\n"
                                  : " M changed.mjs\n",
                      }
                    : {},
        });
        roster(r);
        noDriverSuccess(r);
        assert(r.gitCalls.length >= 3 && r.gitCalls.length <= 4);
    });
for (const [name, specification] of [
    ["nonzero", { code: 7 }],
    ["signal", { code: null, signal: "SIGTERM" }],
    ["spawn-throws", { spawnThrows: true }],
    ["stdout-error", { streamError: "stdout" }],
    ["stderr-error", { streamError: "stderr" }],
    ["child-error", { error: true }],
    [
        "timeout-known-close",
        { noClose: true, closeOnKill: true, closeDelay: 1000 },
    ],
    ["timeout-unknown-killfalse", { noClose: true, killFalse: true }],
    ["timeout-unknown-killthrows", { noClose: true, killThrows: true }],
    ["exit-is-not-close", { exitOnly: true, killFalse: true }],
    ["stdout-overflow", { stdout: "x".repeat(262145) }],
    ["stderr-overflow", { stderr: "x".repeat(262145) }],
    [
        "overflow-unknown-close",
        { stdout: "x".repeat(262145), noClose: true, killFalse: true },
    ],
])
    test("driver", `first-node-${name}`, async () => {
        const r = await driver({
            script: ({ isGit, index }) =>
                !isGit && index === 0 ? specification : {},
        });
        failureStops(r);
        const first = r.nodeCalls[0];
        if (name.startsWith("timeout") || name === "exit-is-not-close") {
            assert.equal(first.kills, 1);
            assert(r.timer.now >= 240000 && r.timer.now <= 245000);
        }
        if (name.includes("unknown") || name === "exit-is-not-close") {
            assert.equal(first.closed, false);
            assert.equal(r.policies[0].snapshot().error, "UnknownChild");
            checkedSnapshot(r.policies[0].snapshot(), {
                currentBytes: null,
                productBytes: null,
            });
        }
        assert(
            Buffer.byteLength(r.text) <= expectedLimits.consoleBytes,
            "AllSerializedOutputRemainsBounded",
        );
    });
for (const [name, mutate, options = {}] of [
    ["inventory-unavailable", (w) => w.faultNext("readdir")],
    [
        "growth-stepbudget",
        (w) => w.file(P.join(OUT, "too-large"), 4 * M + 1),
        { limit: 64 * M },
    ],
    [
        "next-reserve-no-second-child",
        (w) => w.file(P.join(OUT, "one-byte"), 1),
        { limit: 5 * M },
    ],
    [
        "product-cap",
        (w) => w.file(P.join(SRC, "dist", "oversize"), 16 * M + 1),
        { limit: 64 * M },
    ],
])
    test("driver", `storage-failure-${name}`, async () => {
        const r = await driver({
            w: world({ products: 16, ...options }),
            script: ({ isGit, index }) =>
                !isGit && index === 0 ? { beforeClose: mutate } : {},
        });
        failureStops(r);
        assert.equal(r.policies[0].snapshot().status, "failed");
    });
test(
    "driver",
    "prior-child-PASS-prefix-survives-later-inventory-failure-without-global-success",
    async () => {
        const earlier =
            "PASS: strict TypeScript, current request/schema checks, and no development journey/control hooks in normal frontend.";
        const r = await driver({
            script: ({ isGit, index }) =>
                isGit
                    ? {}
                    : index === 0
                      ? { stdout: earlier + "\n" }
                      : index === 1
                        ? { beforeClose: (w) => w.faultNext("readdir") }
                        : {},
        });
        failureStops(r, 2);
        assert(
            r.text.includes(earlier),
            "EarlierActualChildPrefixMustRemainRetained",
        );
        const policy = r.policies[0],
            failed = clone(policy.snapshot()),
            observed = r.w.events.length;
        checkedSnapshot(failed, {
            status: "failed",
            nextIndex: 1,
            activeIndex: 1,
            error: "Inventory",
            currentBytes: null,
            productBytes: null,
        });
        await rejects(() => policy.beforeStep(2), "Inventory");
        await rejects(() => policy.finish(), "Inventory");
        assert.deepEqual(policy.snapshot(), failed);
        assert.equal(r.w.events.length, observed, "RetiredPolicyAddsNoIO");
    },
);
test(
    "driver",
    "multibyte-both-original-stream-counts-kept-separate",
    async () => {
        const r = await driver({
            script: ({ isGit, index }) =>
                !isGit && index === 0
                    ? { stdout: "雪".repeat(7), stderr: "é".repeat(11) }
                    : {},
        });
        assert.equal(r.error, null);
        roster(r);
        const objects = loggedObjects(r.logs);
        assert(
            objects.some(
                (value) => value.stdoutBytes === 21 && value.stderrBytes === 22,
            ),
            "ActualPrintedOriginalByteCountsNotJSCharacterLengths",
        );
    },
);
test(
    "driver",
    "JSON-expansion-and-total-console-reserve-stop-with-original-counts",
    async () => {
        const r = await driver({
            script: ({ isGit }) =>
                isGit
                    ? {}
                    : {
                          stdout: "\u0001".repeat(262144),
                          stderr: "\u0002".repeat(262144),
                      },
        });
        noDriverSuccess(r);
        assert.equal(r.nodeCalls.length, 2);
        assert.equal(r.gitCalls.length, 2);
        assert(
            Buffer.byteLength(r.text) <= expectedLimits.consoleBytes,
            "EncodedStdoutStderrMetadataAndNewlinesShare4MiB",
        );
        assert(
            r.text.includes("ConsoleBudget"),
            "ExplicitRunnerConsoleBudgetReason",
        );
        const objects = r.logs.flatMap((text) => {
            try {
                return [JSON.parse(text)];
            } catch {
                return [];
            }
        });
        const compact = objects.filter((value) =>
            JSON.stringify(value).includes("ConsoleBudget"),
        );
        assert(compact.length > 0, "BoundedFailureMetadataOrSummaryPresent");
        const prefixIndex = r.logs.findIndex(
            (text) => Buffer.byteLength(text) > M && text.includes("\\u0001"),
        );
        assert(
            prefixIndex >= 0,
            "FirstSerializedDualStreamReceiptFitsAndIsPreserved",
        );
        assert(
            Buffer.byteLength(r.logs.slice(prefixIndex + 1).join("")) <=
                expectedLimits.summaryBytes,
            "CompactFailureAndSummaryJointlyFitReserved32768",
        );
        assert(
            compact.some((value) => JSON.stringify(value).includes("262144")),
            "OriginalStreamCountsRetainedWhenTextOmitted",
        );
        assert(
            loggedObjects(r.logs.slice(prefixIndex + 1)).some(
                (value) =>
                    value.stdoutBytes === 262144 &&
                    value.stderrBytes === 262144 &&
                    value.closed === true &&
                    value.code === 0,
            ),
            "ConsoleFailurePreservesActualKnownCloseCodeAndBothOriginalRawCounts",
        );
    },
);

const routes = [
    [
        "check-contract.mjs",
        "folder",
        "file",
        "mkdirSync(",
        "4be4a0b79102c76daeacc34b66c11a0d6cdc613238a7fad646958e07d523fc01",
        "model-",
    ],
    [
        "check-export-controller.mjs",
        "folder",
        "file",
        "mkdirSync(",
        "8eeca61789d4ce9cf9a9484b56b582c471c603ae080dbfc9c31fc23a1f5988a2",
        "export-controller-",
    ],
    [
        "check-model-controller.mjs",
        "dir",
        "file",
        "mkdirSync(",
        "d986ae64379e0c955d48dcadb417c2fe5e97e1a0592f45fd53830e10a13e8ac2",
        "model-controller-",
    ],
    [
        "check-inspection-controller.mjs",
        "dir",
        "output",
        "await mkdir(",
        "520a4217ea4338949d4f18292e4a129cdfb5f2ab0a1abce7f6613acad2e7814a",
        "inspection-controller-",
    ],
];
for (const [name, folder, file, start, suffixHash, prefix] of routes) {
    test("routing", `${name}-original-UUID-bundle-and-assertion-suffix`, () => {
        const text = source[name].replaceAll("\r\n", "\n"),
            index = text.indexOf(start);
        assert(index >= 0);
        assert.equal(
            sha(text.slice(index)),
            suffixHash,
            "OriginalSuffixMustRemainByteIdenticalApartFromLineEndings",
        );
    });
    for (const explicit of [false, true])
        test(
            "routing",
            `${name}-${explicit ? "explicit-root" : "original-fallback"}`,
            async () => {
                const text = source[name],
                    marker = /const\s+\w+\s*=\s*await\s+build\s*\(/.exec(text);
                assert(marker, "ActualRoutingPrefixMustReachOriginalBuild");
                const w = world(),
                    preamble = text.slice(0, marker.index);
                const recordingFs = {
                    ...w.fs,
                    async mkdir(where, options) {
                        w.events.push({
                            kind: "preamble-mkdir",
                            path: key(where),
                            options,
                        });
                    },
                };
                const code = await compile(
                    preamble,
                    name,
                    true,
                    `return {folder:${folder},file:${file}};`,
                );
                const api = loadCjs(code, {
                    imports: {
                        ...importsFor(w, {
                            esbuild: {
                                build() {
                                    throw Error("PreamblePassedItsBoundary");
                                },
                            },
                            "ajv/dist/2020.js": class {},
                        }),
                        "node:fs/promises": recordingFs,
                    },
                    process: {
                        env: explicit
                            ? {
                                  LOCALLORE_CHECK_OUTPUT_DIR:
                                      "D:\\explicit evidence",
                              }
                            : {},
                    },
                    console,
                    setTimeout,
                    clearTimeout,
                });
                const value = await api.__reviewDriver(),
                    expected = explicit
                        ? "D:\\explicit evidence"
                        : P.join(SRC, "artifacts", "checks");
                assert.equal(key(value.folder), key(expected));
                assert.equal(
                    key(value.file),
                    key(
                        P.join(
                            expected,
                            `${prefix}11111111-2222-4333-8444-555555555555.mjs`,
                        ),
                    ),
                );
                assert.deepEqual(
                    w.events
                        .filter((e) => e.kind === "preamble-mkdir")
                        .map((e) => e.path),
                    [key(expected)],
                );
            },
        );
}
test("source", "build-script-unchanged", () => {
    assert.equal(
        sha(source["build.mjs"]),
        "cc44e2f79a9b3eb59af6cf4fc2f87f2b3e6aad62b75b64f4fee7a3b0be420492",
    );
});
test("source", "original-normal-bundle-exclusion-assertions-preserved", () => {
    const text = source[DRIVER].replaceAll("\r\n", "\n");
    const loop = /for\s*\(\s*const\s+marker\s+of\s*(\[[\s\S]*?\])\s*\)/.exec(
        text,
    );
    assert(loop, "OriginalNormalExclusionLoopPresent");
    const markers = [...loop[1].matchAll(/"([^"\\]*)"/g)].map(
        (entry) => entry[1],
    );
    assert.equal(markers.length, 67);
    assert.equal(
        sha(JSON.stringify(markers)),
        "51cf216ac58ddd12d869950d63cb173814221fab796b637b7a8619388e6e59b5",
    );
    assert(
        /^\s*\{?\s*assert\(\s*!normal\.includes\(marker\),\s*`Test hook leaked into normal bundle: \$\{marker\}`\s*,?\s*\)/.test(
            text.slice(loop.index + loop[0].length),
        ),
        "ActualOriginalNormalBundleExclusionPredicateAndMessage",
    );
});

const frozenGroups = {
    record: 30,
    path: 24,
    budget: 13,
    lifecycle: 24,
    inventory: 4,
    driver: 40,
    routing: 12,
    source: 2,
};
const authoredGroups = {};
for (const entry of tests)
    authoredGroups[entry.group] = (authoredGroups[entry.group] ?? 0) + 1;
assert.deepEqual(authoredGroups, frozenGroups, "Frozen149CaseSourceRoster");

// Setup must succeed before ANY behavior runs. The absent prospective producer
// is not behavior RED, a skipped PASS, or permission to supply a copied policy.
try {
    for (const name of [
        MODULE,
        DRIVER,
        "build.mjs",
        ...routes.map((r) => r[0]),
    ])
        source[name] = await readFile(path.join(sourceRoot, name), "utf8");
    moduleCode = await compile(source[MODULE], MODULE);
    const entryLiterals = [
        ...moduleCode.matchAll(
            /(?:\bentries|"entries"|'entries'):\s*(2000000|2_000_000|2e6|2E6)\b/g,
        ),
    ];
    if (entryLiterals.length !== 1)
        throw Error("UNRUN_SETUP:OneProvenCompiledEntryLiteralRequired");
    const literal = entryLiterals[0],
        index = literal.index + literal[0].lastIndexOf(literal[1]);
    const prefix = moduleCode.slice(0, index),
        suffix = moduleCode.slice(index + literal[1].length);
    scaledModuleCode = prefix + "12" + suffix;
    assert.equal(scaledModuleCode.slice(0, index), prefix);
    assert.equal(scaledModuleCode.slice(index + 2), suffix);
    scaledEntryProof = {
        classification: "TEST_ONLY_SCALED_ACTUAL_ALGORITHM",
        matches: 1,
        from: literal[1],
        to: "12",
        index,
        originalSha256: sha(moduleCode),
        derivedSha256: sha(scaledModuleCode),
        unchangedPrefixSha256: sha(prefix),
        unchangedSuffixSha256: sha(suffix),
    };
    const api = moduleFor(world());
    assert.equal(
        typeof api.parseFrontendEvidenceAdmission,
        "function",
        "MissingAcceptedAdmissionParser",
    );
    assert.equal(
        typeof api.openFrontendEvidencePolicy,
        "function",
        "MissingAcceptedPolicyConstructor",
    );
    assert(
        source[DRIVER].includes("--bounded"),
        "MissingActualBoundedDriverBranch",
    );
    assert(
        source[DRIVER].includes(NEW_STEP),
        "MissingOnceRegisteredIndependentPolicyReview",
    );
    driverParts = await compile(source[DRIVER], DRIVER, true);
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
            if (String(error).includes("UNRUN_SETUP:")) {
                setup.push({
                    classification: "UNRUN_SETUP",
                    at: entry.name,
                    error: String(error).slice(0, 2048),
                });
                break;
            }
            results.push({
                group: entry.group,
                name: entry.name,
                passed: false,
                error: String(error).slice(0, 2048),
            });
        }
    }
for (const [name, text] of Object.entries(source)) {
    if (sha(await readFile(path.join(sourceRoot, name), "utf8")) !== sha(text))
        setup.push({
            classification: "UNRUN_SETUP",
            error: `SourceChangedDuringReview:${name}`,
        });
}
const groups = {};
for (const entry of tests) groups[entry.group] = (groups[entry.group] ?? 0) + 1;
console.log(
    JSON.stringify({
        kind: "d09_frontend_evidence_policy_independent_first_v1",
        authored: tests.length,
        groups,
        setup,
        executed: results.length,
        passed: results.filter((r) => r.passed).length,
        failed: results.filter((r) => !r.passed).length,
        results,
        source: Object.fromEntries(
            Object.entries(source).map(([name, text]) => [name, sha(text)]),
        ),
        evidence: {
            module: "actual source with in-memory fs identity/entry/byte observations",
            scaledEntryProof,
            driver: "actual full source with fixed child/Git/timer doubles",
            routing: "actual four preambles plus frozen original suffixes",
            realFilesystemInventory: false,
            realChild: false,
            native: false,
            browser: false,
            model: false,
            desktopControl: false,
        },
        limitations: [
            "Source author ran no Node/toolchain/runtime; missing producer/import/registration is UNRUN_SETUP",
            "Synthetic directory identities/entry counts are Node-observable controls, not universal Windows reparse or process-tree containment",
            "Unmodified immutable entries=2000000 is asserted; ONE compiled literal→12 combined-entry algorithm case has proven unchanged prefix/suffix and separate hashes, not actual two-million-file runtime qualification",
            "Post-child output/product/aggregate budget controls overlap StepBudget where reservation makes isolation impossible; corresponding finite budget failures only",
            "Numeric growth is synthetic metadata and creates no physical files; routing mkdir is doubled; real installed esbuild build-tool execution is not a native application",
            "Same-realm CommonJS/TLA wrapper executes actual source body; no copied scheduling/decoder, arbitrary child selection, app hook or server",
            "Original failed32MiB D05 gate is preserved; this policy check cannot repair it, authorize full-driver repetition or establish new runtime/storage acceptance",
        ],
    }),
);
process.exitCode = setup.length
    ? 2
    : !results.length || results.some((r) => !r.passed)
      ? 1
      : 0;
