// Independent FIRST at288e4381. SOURCE AUTHOR UNCOMPILED / UNRUN.
// Actual dev trace and Controller public resume/dispose, synthetic native DTOs.
// Fixed same-realm TS loading only: no bundler, files written, children or app.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash, webcrypto } from "node:crypto";
import { stripTypeScriptTypes } from "node:module";
import vm from "node:vm";
assert.equal(process.argv.length, 2, "ClosedForkCloseReviewArguments");
const sha = (v) => createHash("sha256").update(v).digest("hex");
const sourceHashes = {}, setup = [], results = [];
let Trace, Controller, ErrorBuffer;
// Builtin transform also lowers actual Controller constructor parameter properties.
const strip = (text) => stripTypeScriptTypes(text, { mode: "transform" })
    .replace(/^import[\s\S]*?from\s+["'][^"']+["'];\s*/gm, "")
    .replace(/^export\s*\{[^}]*\};?\s*/gm, "")
    .replace(/^export\s+/gm, "");
async function actualModule(file, exports, dependencies = {}) {
    const source = await readFile(new URL(`ui/${file}`, import.meta.url), "utf8");
    sourceHashes[file] = sha(source);
    const parameters = { crypto: webcrypto, ...dependencies };
    return vm.compileFunction(strip(source) + `\nreturn {${exports.join(",")}};`, Object.keys(parameters))(...Object.values(parameters));
}
try {
    const model = await actualModule("model.ts", ["category", "difference", "ErrorBuffer", "PAGE_SIZE", "playView", "request", "sameScope", "structural"]);
    ErrorBuffer = model.ErrorBuffer;
    const trace = await actualModule("trace-model.ts", ["initialTrace", "checkedTrace", "attemptKey"]);
    const query = await actualModule("query-model.ts", ["initialQuery", "checkedPage"]);
    const v2 = await actualModule("v2-view-model.ts", ["checkedJsonV2:detached", "checkedPlaySnapshotV2"]);
    const diagnostic = await actualModule("narration-diagnostic-model.ts", ["checkedNarrationValidationDataV1"]);
    ({ Controller } = await actualModule("controller.ts", ["Controller"], { ...model, ...trace, ...query, ...v2, ...diagnostic }));
    const fork = await readFile(new URL("ui/fork-controller.ts", import.meta.url), "utf8");
    sourceHashes["fork-controller.ts"] = sha(fork);
    const errorStart = fork.indexOf("const errors = new Set(["), errorEnd = fork.indexOf("function errorName(", errorStart);
    assert(errorStart >= 0 && errorEnd > errorStart, "ActualForkErrorProjection");
    const isForkError = vm.compileFunction(strip(fork.slice(errorStart, errorEnd)) + "\nreturn isForkError;")();
    const journey = await readFile(new URL("ui/domain2-fork-native-journeys.ts", import.meta.url), "utf8");
    sourceHashes["domain2-fork-native-journeys.ts"] = sha(journey);
    const start = journey.indexOf("const FORK_CALLS = new Set(["), end = journey.indexOf("export async function domain2ForkNativeJourneys(", start);
    assert(start >= 0 && end > start && journey.indexOf("export class Domain2ForkTrace", start) < end, "ActualTraceExtraction");
    const actual = journey.slice(start, end); sourceHashes.traceClosure = sha(actual);
    Trace = vm.compileFunction(strip(actual) + "\nreturn Domain2ForkTrace;", ["crypto", "category", "isForkError"])(webcrypto, model.category, isForkError);
} catch (error) { setup.push({ classification: "UNRUN_SETUP", error: String(error?.message ?? error).slice(0, 300) }); }

const SCOPE = { story: "synthetic-close", branch: "main" };
const envelope = (op, session = "native-session-73", scope = SCOPE) => ({ input: JSON.stringify({ version: 1, command: { op, session, scope } }) });
function port(trace = new Trace()) {
    const native = [];
    return { trace, native,
        host(op, work = async () => ({ synthetic: true }), session, scope) {
            return trace.dispatch("host_call", envelope(op, session, scope), async () => { native.push({ op, session, scope }); return work(); });
        },
        nativeCall(command, work = async () => ({ synthetic: true })) {
            return trace.dispatch(command, {}, async () => { native.push({ command }); return work(); });
        },
    };
}
async function reads(p, count = 64) { for (let n = 0; n < count; n++) await p.host("workspace"); }
const rejected = (work) => assert.rejects(work, /D08ForkTraceBudget/);
const digest = /^[a-f0-9]{64}$/;
function settled(trace) {
    trace.rows.forEach((row, index) => {
        assert.equal(row.sequence, index + 1); assert.equal(row.nativeSettled, true); assert.equal(row.settled, true);
        if (row.error === null) assert.match(row.replySha256, digest);
    });
}
const cases = [
    ["ordinary-host-read64-and65-refusal-preserved", async () => {
        const p = port(); await reads(p); await rejected(p.host("workspace"));
        assert.equal(p.trace.hostReads, 64); assert.equal(p.native.length, 64); assert.equal(p.trace.rows.length, 64); settled(p.trace);
    }],
    ["four-close-attempts-have-separate-budget-after64-reads", async () => {
        const p = port(); await reads(p);
        for (let n = 0; n < 4; n++) await p.host("close", undefined, `native-session-${n}`);
        await rejected(p.host("close")); await rejected(p.host("workspace"));
        assert.equal(p.trace.hostReads, 64); assert.equal(p.native.filter((v) => v.op === "close").length, 4);
        assert.equal(p.trace.rows.length, 68); settled(p.trace);
    }],
    ["close-first-does-not-spend-or-expand-ordinary-read-budget", async () => {
        const p = port(); for (let n = 0; n < 4; n++) await p.host("close");
        await reads(p); await rejected(p.host("workspace")); await rejected(p.host("close"));
        assert.equal(p.trace.hostReads, 64); assert.equal(p.trace.rows.length, 68); assert.equal(p.native.length, 68);
    }],
    ["row256-cap-also-refuses-an-unspent-close-allowance", async () => {
        const p = port(); await reads(p);
        for (let n = 0; n < 128; n++) await p.nativeCall("fork_boundaries");
        for (let n = 0; n < 64; n++) await p.nativeCall("model_status");
        assert.equal(p.trace.rows.length, 256); assert.equal(p.native.length, 256);
        await rejected(p.host("close")); await rejected(p.nativeCall("model_status"));
        assert.equal(p.trace.rows.length, 256); assert.equal(p.native.length, 256); settled(p.trace);
    }],
    ["fork128-cap-preserved-and-close-does-not-increase-it", async () => {
        const p = port(); for (let n = 0; n < 128; n++) await p.nativeCall("fork_boundaries");
        await rejected(p.nativeCall("fork_boundaries")); await p.host("close"); await rejected(p.nativeCall("fork_boundaries"));
        assert.equal(p.trace.forkCalls, 128); assert.equal(p.trace.rows.length, 129); settled(p.trace);
    }],
    ["lifecycle-allowance-does-not-admit-host-canonical-writes", async () => {
        const p = port();
        for (const op of ["create", "submit", "prepare", "commit", "free_text", "author_fork", "Close", "close_other"])
            await assert.rejects(p.host(op), /D08ForkForbiddenHostWrite/);
        assert.equal(p.native.length, 0); assert.equal(p.trace.rows.length, 0); assert.equal(p.trace.hostReads, 0);
    }],
    ["close-pending-settlement-digest-error-and-no-failed-attempt-refund", async () => {
        const p = port(); await reads(p); let release;
        const held = new Promise((resolve) => { release = resolve; });
        const pending = p.host("close", () => held); await Promise.resolve();
        const row = p.trace.rows.at(-1); assert.equal(row.command, "close"); assert.equal(row.nativeSettled, false); assert.equal(row.settled, false);
        release({ closed: true }); await pending; assert.match(row.replySha256, digest);
        await assert.rejects(p.host("close", async () => { throw Error("Forbidden"); }), /Forbidden/);
        const failed = p.trace.rows.at(-1); assert.equal(failed.error, "Forbidden"); assert.equal(failed.replySha256, null);
        await p.host("close"); await p.host("close"); await rejected(p.host("close"));
        assert.equal(p.native.filter((v) => v.op === "close").length, 4); assert.equal(p.trace.hostReads, 64); settled(p.trace);
    }],
    ["actual-controller-four-public-resumes-dispose-native-close-once-without-errors", async () => {
        const trace = new Trace(), calls = [], active = new Map(), failures = [];
        let sequence = 0;
        const gateway = { playSnapshotV2: true, call(command) {
            return trace.dispatch("host_call", { input: JSON.stringify({ version: 1, command }) }, async () => {
                calls.push(structuredClone(command));
                if (command.op === "resume") {
                    const session = `native-real-close-${++sequence}`; active.set(session, command.scope);
                    return { session, scope: command.scope, revision: 3, drafts: 0 };
                }
                if (command.op === "open") { assert.deepEqual(active.get(command.session), command.scope); return { revision: 3 }; }
                if (command.op === "play_snapshot_v2") {
                    assert.deepEqual(active.get(command.session), command.scope); assert.equal(command.expected_revision, 3);
                    return { version: 2, domain_version: 2, scope: command.scope, revision: 3, rules: "fantasy_v1", player: { observer: "player", self_state: { name: "Synthetic Rowan", location: "quay", alive: true, energy: 2, abilities: { steady: 1 }, attributes: { resolve: 3 }, injuries: [], affiliations: [], goals: [] } }, inventory: {} };
                }
                if (command.op === "workspace") return { synthetic: true };
                if (command.op === "close") { assert.deepEqual(active.get(command.session), command.scope); active.delete(command.session); return { closed: true }; }
                throw Error("UnexpectedSyntheticCommand:" + command.op);
            }).catch((error) => { failures.push({ op: command.op, error: error.message }); throw error; });
        } };
        const errors = new ErrorBuffer(), c = new Controller(gateway, errors, "synthetic-fixed-prefix");
        for (let n = 0; n < 4; n++) await c.resume({ story: SCOPE.story, branch: `saved-${n}` });
        assert.equal(c.get().sessions.length, 4); assert.equal(active.size, 4); assert.equal(c.get().visibleError, null);
        const admitted = c.get().sessions.map((s) => ({ id: s.id, scope: structuredClone(s.scope) }));
        while (trace.hostReads < 64) await gateway.call({ op: "workspace" });
        assert.equal(trace.hostReads, 64); const before = calls.length;
        await c.dispose(); await c.dispose();
        const closes = calls.slice(before); assert.equal(closes.length, 4); assert(closes.every((r) => r.op === "close"));
        assert.deepEqual(closes.map((r) => ({ id: r.session, scope: r.scope })), admitted);
        assert.equal(active.size, 0); assert.deepEqual(failures, []); assert.deepEqual(errors.snapshot(), []);
        assert.equal(c.get().disposed, true); assert.equal(c.get().sessions.length, 0); assert.equal(trace.hostReads, 64); settled(trace);
    }],
];
for (const [name, run] of cases) {
    if (!Trace || !Controller || !ErrorBuffer) { results.push({ name, status: "UNRUN_SETUP" }); continue; }
    try { await run(); results.push({ name, status: "PASS" }); }
    catch (error) { results.push({ name, status: "FAIL", error: String(error?.message ?? error).slice(0, 350) }); }
}
const report = { kind: "d08_domain2_fork_close_independent_first_v1", authored: cases.length,
    executed: results.filter((r) => r.status !== "UNRUN_SETUP").length, passed: results.filter((r) => r.status === "PASS").length,
    failed: results.filter((r) => r.status === "FAIL").length, setup, results, sourceHashes,
    limits: ["Source author UNRUN; no app grant/retry, physical fixture, native IPC, Rust/session statistics or renderer qualification", "Actual trace and Controller public resume/dispose with fixed synthetic transport; active Map proves only double-side lifecycle", "64 ordinary reads, four attempted closes, 128 fork calls and 256 total rows remain independent hard limits", "Only builtin same-realm TS stripping/VM and crypto; no esbuild/service, bundle, files written or children"] };
const output = JSON.stringify(report); assert(Buffer.byteLength(output) + 1 <= 8192, "BoundedEightKiBReport"); console.log(output);
process.exitCode = setup.length ? 2 : report.failed ? 1 : 0;
