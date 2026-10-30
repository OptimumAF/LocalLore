// FIRST 7c8f3417 UNRUN. Pure factory returns NON-async unknown=>Promise<unknown>.
// Retain before reentry; JSON-detach summary; VM port doubles.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { stripTypeScriptTypes } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";

assert.equal(process.argv.length, 2, "ClosedArguments");
const root = fileURLToPath(new URL(".", import.meta.url));
const MODE = "domain2_fork_v1",
    CAP = 262144;
const LABELS = [
    "catalog",
    "rejected",
    "pending",
    "preauthor",
    "authored",
    "recovered",
    "enlarged",
].map((x) => `d08-fork-${x}`);
const FAILURE = "d08-fork-failure";
const ERR = "D08ForkReportInvalid",
    SUM = "D08ForkCheckpointSummary",
    BIG = "D08ForkFinalReportBudget",
    IPC = "D08ForkFinishRejected";
const HELPER = "ui/domain2-fork-native-finalization.ts";
const JOURNEY = "ui/domain2-fork-native-journeys.ts";
const START = "// d08-fork-finalizer-owner-v1:start",
    END = "// d08-fork-finalizer-owner-v1:end";
const sha = (value) => createHash("sha256").update(value).digest("hex");
const copy = (value) => structuredClone(value);
const bytes = (value, pretty = false) =>
    Buffer.byteLength(
        JSON.stringify(value, null, pretty ? 2 : undefined),
        "utf8",
    );
const tests = [],
    results = [],
    setup = [],
    sources = {};
let create, ownerSource, journeySource;
const test = (need, name, run) => tests.push({ need, name, run });
const refs = (n = 7, count = 1) =>
    LABELS.slice(0, n).map((label) => ({
        label,
        json: `${label}.json`,
        count,
    }));
const summary = (rows) => ({
    retainedInCheckpoints: true,
    total: rows.reduce((n, r) => n + r.count, 0),
    checkpoints: rows,
});
const report = (passed = true, n = 7, count = 1) => ({
    synthetic: true,
    mode: MODE,
    passed,
    captures: LABELS.slice(0, n),
    scrollObservations: summary(refs(n, count)),
    checks: ["synthetic-source-check"],
    baseline: { hash: "a".repeat(64) },
    finalOracle: { hash: "b".repeat(64) },
    fonts: [{ target: "synthetic", px: 15 }],
    calls: [],
});
const fallback = (failureCategory) => ({
    synthetic: true,
    mode: MODE,
    passed: false,
    originalPassed: false,
    detailReportUnavailable: true,
    failureCategory,
    noFinalStateProof: true,
});
function port(behavior = async () => "finished") {
    const calls = [];
    return {
        calls,
        finish(value) {
            calls.push(value);
            return behavior(calls.length, value);
        },
    };
}
function bounded(p) {
    assert(p.calls.length >= 1 && p.calls.length <= 2);
    for (const value of p.calls)
        assert(bytes(value) <= CAP && bytes(value, true) <= CAP);
}
async function invalid(value, category = ERR) {
    const p = port(),
        finish = create(p.finish);
    await finish(value);
    assert.equal(p.calls.length, 1);
    assert.deepEqual(p.calls[0], fallback(category));
    bounded(p);
}
function held() {
    let resolve, reject;
    const promise = new Promise((a, b) => {
        resolve = a;
        reject = b;
    });
    return { promise, resolve, reject };
}
async function flush() {
    for (let i = 0; i < 12; i++) await Promise.resolve();
}
function actualOwner(p) {
    const stripped = stripTypeScriptTypes(`${ownerSource}\nreturn finish;`, {
        mode: "strip",
    });
    return vm.compileFunction(stripped, [
        "createDomain2ForkFinalizer",
        "invoke",
    ])(create, (name, args) => {
        assert.equal(name, "harness_finish");
        assert.deepEqual(Object.keys(args), ["report"]);
        return p.finish(args.report);
    });
}

test("helper", "success-detached-proofs", async () => {
    const input = report(),
        before = copy(input),
        p = port(),
        value = { accepted: true };
    p.finish = (x) => {
        p.calls.push(x);
        return Promise.resolve(value);
    };
    assert.equal(await create(p.finish)(input), value);
    assert.equal(p.calls.length, 1);
    assert.deepEqual(p.calls[0], before);
    input.baseline.hash = "changed";
    input.scrollObservations.checkpoints[0].count = 2;
    assert.deepEqual(p.calls[0], before);
    bounded(p);
});
test("helper", "invalid-headers", async () => {
    for (const input of [
        null,
        undefined,
        [],
        1,
        "x",
        {},
        { ...report(), synthetic: false },
        { ...report(), mode: "domain2_timeline_browser_v1" },
        { ...report(), passed: "true" },
    ])
        await invalid(input);
    for (const key of [
        "synthetic",
        "mode",
        "passed",
        "captures",
        "scrollObservations",
    ]) {
        const input = report();
        delete input[key];
        await invalid(
            input,
            ["captures", "scrollObservations"].includes(key) ? SUM : ERR,
        );
    }
});
test("helper", "seven-ordered-success-labels", async () => {
    for (let n = 0; n < 7; n++) await invalid(report(true, n), SUM);
    for (const captures of [
        [...LABELS].reverse(),
        [...LABELS, FAILURE],
        [...LABELS, LABELS[0]],
        [...LABELS.slice(0, 6), "other"],
    ])
        await invalid({ ...report(), captures }, SUM);
});
test("helper", "invalid-captures", async () => {
    const sparse = [...LABELS];
    delete sparse[1];
    for (const captures of [
        null,
        {},
        sparse,
        [LABELS[1]],
        [LABELS[0], LABELS[0]],
        ["../d08-fork-catalog"],
        [FAILURE, LABELS[0]],
    ])
        await invalid({ ...report(false), captures }, SUM);
});
test("helper", "failed-prefix-zero-through-seven", async () => {
    for (let n = 0; n <= 7; n++) {
        const input = report(false, n, 24),
            p = port();
        await create(p.finish)(input);
        assert.equal(p.calls.length, 1);
        assert.deepEqual(p.calls[0], input);
        bounded(p);
    }
});
test("helper", "terminal-failure-not-scroll", async () => {
    for (let n = 0; n <= 7; n++) {
        const input = report(false, n, 24);
        input.captures.push(FAILURE);
        const p = port();
        await create(p.finish)(input);
        assert.deepEqual(p.calls, [input]);
        assert.equal(p.calls[0].scrollObservations.total, n * 24);
        bounded(p);
    }
});
test("helper", "invalid-failure-image", async () => {
    for (const captures of [
        [FAILURE, FAILURE],
        [LABELS[0], FAILURE, LABELS[1]],
        [...LABELS, FAILURE, FAILURE],
    ])
        await invalid({ ...report(false), captures }, SUM);
    const input = report(false, 1);
    input.captures.push(FAILURE);
    input.scrollObservations.checkpoints.push({
        label: FAILURE,
        json: `${FAILURE}.json`,
        count: 0,
    });
    await invalid(input, SUM);
});
test("helper", "closed-summary", async () => {
    for (const value of [
        null,
        [],
        {},
        { ...summary(refs()), extra: 1 },
        { ...summary(refs()), retainedInCheckpoints: false },
        { ...summary(refs()), total: 8 },
        { ...summary(refs()), total: "7" },
        { ...summary(refs()), checkpoints: null },
        [{ label: LABELS[0], rectangle: [1, 2, 3, 4] }],
    ])
        await invalid({ ...report(), scrollObservations: value }, SUM);
});
test("helper", "invalid-summary-rows", async () => {
    const sparse = refs();
    delete sparse[1];
    for (const rows of [
        sparse,
        refs().reverse(),
        refs(6),
        [...refs(), refs()[0]],
        [{ ...refs()[0], json: "arbitrary.json" }],
        [{ ...refs()[0], extra: 1 }],
    ])
        await invalid({ ...report(), scrollObservations: summary(rows) }, SUM);
});
test("helper", "count-bounds", async () => {
    for (const count of [1, 24]) {
        const input = report(true, 7, count),
            p = port();
        await create(p.finish)(input);
        assert.deepEqual(p.calls, [input]);
        bounded(p);
    }
    for (const count of [
        0,
        -1,
        25,
        0.5,
        NaN,
        Infinity,
        "1",
        null,
        Number.MAX_SAFE_INTEGER + 1,
    ])
        for (const passed of [true, false])
            await invalid(report(passed, 7, count), SUM);
});
test("helper", "pretty-limit", async () => {
    const input = { ...report(), padding: "" };
    input.padding = "x".repeat(CAP - bytes(input, true));
    assert.equal(bytes(input, true), CAP);
    const p = port();
    await create(p.finish)(input);
    assert.equal(p.calls.length, 1);
    assert.equal(p.calls[0].passed, true);
    bounded(p);
});
test("helper", "pretty-overflow", async () => {
    const input = { ...report(), padding: "" };
    input.padding = "x".repeat(CAP - bytes(input, true) + 1);
    assert(bytes(input) < CAP && bytes(input, true) > CAP);
    await invalid(input, BIG);
});
test("helper", "utf8-nonascii-exact-and-overflow", async () => {
    const input = { ...report(), padding: "" },
        remaining = CAP - bytes(input, true);
    input.padding =
        "界".repeat(Math.floor(remaining / 3)) + "x".repeat(remaining % 3);
    assert.equal(bytes(input, true), CAP);
    const p = port();
    await create(p.finish)(input);
    assert.equal(p.calls[0].passed, true);
    bounded(p);
    input.padding += "界";
    await invalid(input, BIG);
});
test("helper", "circular-and-bigint", async () => {
    const input = report();
    input.circular = input;
    for (const value of [input, { ...report(), privateCause: 1n }])
        await invalid(value);
});
test("helper", "encoding-throw", async () => {
    await invalid({
        ...report(),
        detail: {
            toJSON() {
                throw Error("PRIVATE-CAUSE-421");
            },
        },
    });
});
test("helper", "detailed-rejection", async () => {
    const p = port(async (n) => {
        if (n === 1) throw Error("PRIVATE-NATIVE-421");
        return "fallback";
    });
    assert.equal(await create(p.finish)(report()), "fallback");
    assert.equal(p.calls.length, 2);
    assert.deepEqual(p.calls[1], fallback(IPC));
    bounded(p);
});
test("helper", "both-reject", async () => {
    const second = Error("fallback-rejected"),
        p = port(async (n) => {
            throw n === 1 ? Error("detail") : second;
        });
    const finish = create(p.finish),
        first = finish(report());
    await assert.rejects(first, (e) => e === second);
    assert.equal(finish(report(false)), first);
    await assert.rejects(finish(report(false)), (e) => e === second);
    assert.equal(p.calls.length, 2);
    bounded(p);
});
test("helper", "invalid-fallback-rejects", async () => {
    const error = Error("fallback-rejected"),
        p = port(async () => {
            throw error;
        });
    const finish = create(p.finish),
        first = finish(null);
    await assert.rejects(first, (e) => e === error);
    assert.equal(finish(report()), first);
    assert.deepEqual(p.calls, [fallback(ERR)]);
    bounded(p);
});
test("helper", "concurrent-same-promise", async () => {
    const gate = held(),
        p = port(() => gate.promise),
        finish = create(p.finish);
    assert.notEqual(finish.constructor.name, "AsyncFunction");
    const first = finish(report());
    assert(first instanceof Promise);
    assert.equal(finish(report(false)), first);
    await flush();
    assert.equal(p.calls.length, 1);
    gate.resolve("done");
    await first;
    assert.equal(finish(null), first);
    assert.equal(p.calls.length, 1);
});
test("helper", "failed-first-no-upgrade", async () => {
    const p = port(),
        finish = create(p.finish),
        first = finish(report(false, 0));
    assert.equal(finish(report()), first);
    await first;
    assert.equal(finish(report()), first);
    assert.equal(p.calls.length, 1);
    assert.equal(p.calls[0].passed, false);
});
test("helper", "invalid-first-no-upgrade", async () => {
    const p = port(),
        finish = create(p.finish),
        first = finish(null);
    assert.equal(finish(report()), first);
    await first;
    assert.equal(finish(report()), first);
    assert.deepEqual(p.calls, [fallback(ERR)]);
});
test("helper", "synchronous-reentry", async () => {
    let finish, reentered;
    const p = port(() => {
        reentered = finish(report(false));
        return Promise.resolve("done");
    });
    finish = create(p.finish);
    const first = finish(report());
    await first;
    assert.equal(reentered, first);
    assert.equal(p.calls.length, 1);
});
test("helper", "sync-throw", async () => {
    const p = port((n) => {
        if (n === 1) throw Error("PRIVATE-SYNC-421");
        return Promise.resolve("done");
    });
    await create(p.finish)(report());
    assert.deepEqual(p.calls[1], fallback(IPC));
    bounded(p);
});
test("helper", "fallback-reentry", async () => {
    let finish, reentered;
    const p = port((n) => {
        reentered = finish(report());
        return n === 1
            ? Promise.reject(Error("detail"))
            : Promise.resolve("done");
    });
    finish = create(p.finish);
    const first = finish(report(false, 0));
    await first;
    assert.equal(reentered, first);
    assert.equal(p.calls.length, 2);
    assert.equal(p.calls[1].passed, false);
    bounded(p);
});
test("journey", "actual-owner-route", async () => {
    const p = port(),
        finish = actualOwner(p),
        input = report(),
        first = finish(input);
    assert.equal(finish(report(false)), first);
    await first;
    assert.deepEqual(p.calls, [input]);
    bounded(p);
});
test("journey", "actual-owner-max2", async () => {
    const error = Error("fixed-rejection"),
        p = port(async () => {
            throw error;
        }),
        finish = actualOwner(p);
    const first = finish(report());
    await assert.rejects(first, (e) => e === error);
    assert.equal(finish(report(false, 0)), first);
    await assert.rejects(finish(report(false, 0)));
    assert.equal(p.calls.length, 2);
    bounded(p);
});
test("journey", "single-owner-both-paths", () => {
    const clean = stripTypeScriptTypes(journeySource, { mode: "strip" });
    assert.equal(
        (clean.match(/createDomain2ForkFinalizer\s*\(/g) ?? []).length,
        1,
    );
    assert(
        journeySource.indexOf(START) < journeySource.indexOf("await "),
        "OwnerFirst",
    );
    const after = journeySource.slice(journeySource.indexOf(END) + END.length);
    assert(/try\s*\{/.test(after) && /catch\s*\(/.test(after));
    assert.equal(
        (after.match(/await\s+finish\s*\(/g) ?? []).length,
        2,
        "BothPaths",
    );
    const catchAt = after.lastIndexOf("catch");
    assert(
        /await\s+finish\s*\(/.test(after.slice(0, catchAt)) &&
            /await\s+finish\s*\(/.test(after.slice(catchAt)),
    );
    assert(!/invoke\s*\(\s*["']harness_finish["']/.test(after), "OnePort");
});
test("journey", "actual-owner-invalid", async () => {
    const p = port(),
        finish = actualOwner(p);
    await finish({ privateCause: "do-not-echo" });
    assert.deepEqual(p.calls, [fallback(ERR)]);
    bounded(p);
});
test("both", "source-stable", async () => {
    for (const [name, source] of Object.entries(sources))
        assert.equal(
            sha(await readFile(path.join(root, name), "utf8")),
            sha(source),
        );
});

assert.equal(tests.length, 29, "Frozen29ForkFinalizationGroups");
try {
    sources[HELPER] = await readFile(path.join(root, HELPER), "utf8");
    if (/^\s*import\s/m.test(sources[HELPER])) throw Error("Standalone");
    const stripped = stripTypeScriptTypes(sources[HELPER], { mode: "strip" });
    const declaration = "export function createDomain2ForkFinalizer";
    if (!stripped.includes(declaration)) throw Error("FactoryExport");
    const code = stripped.replace(
        declaration,
        "function createDomain2ForkFinalizer",
    );
    create = vm.compileFunction(
        `${code}\nreturn createDomain2ForkFinalizer;`,
        [],
    )();
    assert.equal(typeof create, "function");
} catch (error) {
    create = null;
    setup.push({
        stage: "helper",
        status: "UNRUN_SETUP",
        reason: String(error.code ?? error.message).slice(0, 160),
    });
}
try {
    journeySource = sources[JOURNEY] = await readFile(
        path.join(root, JOURNEY),
        "utf8",
    );
    const a = journeySource.indexOf(START),
        b = journeySource.indexOf(END);
    if (
        a < 0 ||
        b <= a ||
        journeySource.indexOf(START, a + START.length) >= 0 ||
        journeySource.indexOf(END, b + END.length) >= 0
    )
        throw Error("OwnerMarkers");
    ownerSource = journeySource.slice(a + START.length, b);
    if (!/const\s+finish\s*=/.test(ownerSource)) throw Error("FinishOwner");
} catch (error) {
    ownerSource = null;
    setup.push({
        stage: "journey",
        status: "UNRUN_SETUP",
        reason: String(error.code ?? error.message).slice(0, 160),
    });
}
for (const item of tests) {
    if (!create || (item.need !== "helper" && !ownerSource)) {
        results.push({ name: item.name, status: "UNRUN_SETUP" });
        continue;
    }
    try {
        await item.run();
        results.push({ name: item.name, status: "PASS" });
    } catch (error) {
        results.push({
            name: item.name,
            status: "FAIL",
            error: String(error.message).slice(0, 64),
        });
    }
}
const output = {
    kind: "d08_domain2_fork_finalization_independent_first_v1",
    authored: tests.length,
    executed: results.filter((x) => x.status !== "UNRUN_SETUP").length,
    passed: results.filter((x) => x.status === "PASS").length,
    failed: results.filter((x) => x.status === "FAIL").length,
    unrun: results.filter((x) => x.status === "UNRUN_SETUP").length,
    setup,
    results,
    source: Object.fromEntries(
        Object.entries(sources).map(([name, value]) => [name, sha(value)]),
    ),
    evidence: {
        actual: "helper/owner",
        doubles: "finish/invoke",
        native: false,
        pixels: false,
        writes: false,
        bundles: false,
        children: false,
    },
};
const encoded = JSON.stringify(output);
assert(
    Buffer.byteLength(encoded, "utf8") + 1 <= 8192,
    "ForkFinalizationStdout8KiB",
);
console.log(encoded);
process.exitCode =
    setup.length || output.unrun
        ? 2
        : output.failed || !output.executed
          ? 1
          : 0;
