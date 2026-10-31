// Independent FIRST at64484981. SOURCE AUTHOR UNCOMPILED / UNRUN.
// Actual journey check/until/idle/click/owner/existingSession and final failure
// statements. Same-realm TS stripping; synthetic controller/DOM/frame/clock only.
// No bundles, file writes, children, native IPC or app retry.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { stripTypeScriptTypes } from "node:module";
import vm from "node:vm";
assert.equal(process.argv.length, 2, "ClosedForkSessionReviewArguments");
const hash = (s) => createHash("sha256").update(s).digest("hex");
const results = [],
    setup = [],
    sources = {};
let factory, failure, category;
try {
    const journey = await readFile(
        new URL("ui/domain2-fork-native-journeys.ts", import.meta.url),
        "utf8",
    );
    const model = await readFile(
        new URL("ui/model.ts", import.meta.url),
        "utf8",
    );
    sources.journey = hash(journey);
    sources.model = hash(model);
    const cut = (a, b) => {
        const start = journey.indexOf(a),
            end = journey.indexOf(b, start + a.length);
        assert(
            start >= 0 &&
                end > start &&
                journey.indexOf(a, start + a.length) < 0,
            "ActualUniqueClosure",
        );
        const value = journey.slice(start, end);
        sources[a.trim().split(" ")[1]] = hash(value);
        return value;
    };
    const declarations = [
        cut(
            "    const check = (value: unknown, name: string) => {",
            "    const until = async (test: () => boolean, name: string) => {",
        ),
        cut(
            "    const until = async (test: () => boolean, name: string) => {",
            "    const frames = () =>",
        ),
        cut("    const idle = async () => {", "    const panel = () =>"),
        cut(
            "    const click = (node: HTMLButtonElement, label: string) => {",
            "    const select = (label: string) => {",
        ),
        cut(
            "    const owner = (scope: Scope, head: number, domain: 1 | 2) => {",
            "    const ready = async () => {",
        ),
        cut(
            "    const existingSession = async (",
            "    const open = async (role: string, head: number, domain: 1 | 2) => {",
        ),
    ].join("\n");
    const stripped = stripTypeScriptTypes(declarations, { mode: "strip" });
    factory = vm.compileFunction(
        `let phase="setup",assertions=0;const checks=[],names=new Set(),deadline=150000;\n${stripped}\nreturn {existingSession,check,phase:()=>phase,checks};`,
        [
            "c",
            "f",
            "v2",
            "trace",
            "document",
            "structural",
            "frames",
            "timelineContext",
            "ready",
            "setTimeout",
            "performance",
        ],
    );
    const start = model.indexOf("export const categories = new Set(["),
        end = model.indexOf("export class ErrorBuffer", start);
    assert(start >= 0 && end > start, "ActualCategoryProjection");
    const projection = stripTypeScriptTypes(
        model.slice(start, end).replace(/^export /gm, ""),
        { mode: "strip" },
    );
    category = vm.compileFunction(`${projection}\nreturn category;`)();
    const tailStart = journey.lastIndexOf(
            "        const report = stateReport(false,",
        ),
        tailEnd = journey.indexOf("        await finish(report);", tailStart);
    assert(
        tailStart >= 0 && tailEnd > tailStart,
        "ActualFinalFailureStatements",
    );
    const tail = journey.slice(tailStart, tailEnd);
    sources.failureTail = hash(tail);
    failure = vm.compileFunction(
        stripTypeScriptTypes(tail, { mode: "strip" }) + "\nreturn report;",
        ["stateReport", "error", "failedPhase", "category"],
    );
} catch (error) {
    setup.push({
        classification: "UNRUN_SETUP",
        error: String(error?.message ?? error).slice(0, 300),
    });
}

const SCOPE = { story: "synthetic-fork", branch: "authored" };
const SESSION = { id: "native-session-73", scope: SCOPE, revision: 3 };
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
async function flush() {
    for (let n = 0; n < 12; n++) await Promise.resolve();
}
function fixture({
    selected = null,
    play = null,
    starting = false,
    matching = true,
} = {}) {
    let current = selected,
        now = 0,
        clickCount = 0,
        readyCount = 0,
        timerCount = 0;
    const state = { sessions: [SESSION], starting, play: null, playV2: play };
    const queue = [],
        trace = { rows: [{ settled: true }] };
    const controller = { get: () => state, selected: () => current };
    const context = () =>
        current
            ? {
                  session: current.id,
                  scope: current.scope,
                  revision:
                      (state.play ?? state.playV2)?.revision ??
                      current.revision,
                  persistent: true,
              }
            : null;
    const fork = {
        get: () => ({ boundaryBusy: false, busy: false }),
        matchesContext: (c) =>
            matching &&
            c.session === SESSION.id &&
            equal(c.scope, SCOPE) &&
            c.revision === 3,
    };
    const button = {
        isConnected: true,
        disabled: false,
        querySelector: () => ({ textContent: "authored · revision 3" }),
        click() {
            clickCount++;
            current = SESSION;
            state.play = null;
            state.playV2 = null;
        },
    };
    const document = {
        querySelectorAll: (selector) => {
            assert.equal(selector, ".session-list button");
            return [button];
        },
    };
    const api = factory(
        controller,
        fork,
        { get: () => ({ readBusy: false, queryBusy: false }) },
        trace,
        document,
        JSON.stringify,
        async () => {},
        context,
        async () => {
            readyCount++;
        },
        (callback, delay) => {
            assert.equal(delay, 10);
            timerCount++;
            queue.push(callback);
            return timerCount;
        },
        { now: () => now },
    );
    let settled = false,
        error = null;
    const promise = api.existingSession(SCOPE, 3, 2).then(
        () => {
            settled = true;
        },
        (e) => {
            settled = true;
            error = e;
        },
    );
    return {
        api,
        promise,
        state,
        queue,
        stats: () => ({ settled, error, clickCount, readyCount, timerCount }),
        coherent() {
            current = SESSION;
            state.starting = false;
            state.play = null;
            state.playV2 = { scope: SCOPE, revision: 3, domain_version: 2 };
            matching = true;
        },
        async tick() {
            const callback = queue.shift();
            if (callback) {
                now += 10;
                callback();
            }
            await flush();
        },
        async complete() {
            for (let n = 0; n < 1600 && !settled; n++) await this.tick();
            assert(settled, "BoundedSyntheticCompletion");
            await promise;
        },
    };
}
const cases = [
    [
        "actual-click-switch-does-not-treat-selected-play-null-as-ready",
        async () => {
            const f = fixture({
                selected: {
                    id: "old-session",
                    scope: { story: "synthetic-fork", branch: "main" },
                    revision: 2,
                },
            });
            await flush();
            assert.equal(f.stats().clickCount, 1);
            assert.equal(f.stats().settled, false);
            f.coherent();
            await f.complete();
            assert.equal(f.stats().error, null);
            assert.equal(f.stats().readyCount, 1);
            assert(
                f.api.checks.includes("selected-scope-head-owned") &&
                    f.api.checks.includes("actual-domain-route") &&
                    f.api.checks.includes("fork-context-exact-current"),
            );
        },
    ],
    [
        "already-selected-loading-waits-without-duplicate-click",
        async () => {
            const f = fixture({ selected: SESSION });
            await flush();
            assert.equal(f.stats().clickCount, 0);
            assert.equal(f.stats().settled, false);
            f.coherent();
            await f.complete();
            assert.equal(f.stats().error, null);
            assert.equal(f.stats().clickCount, 0);
        },
    ],
    [
        "wrong-owner-head-domain-starting-or-context-remains-pending",
        async () => {
            for (const fault of [
                "scope",
                "head",
                "domain",
                "session",
                "starting",
                "context",
            ]) {
                const play = {
                    scope:
                        fault === "scope"
                            ? { ...SCOPE, branch: "foreign" }
                            : SCOPE,
                    revision: fault === "head" ? 2 : 3,
                    domain_version: fault === "domain" ? 1 : 2,
                };
                const f = fixture({
                    selected:
                        fault === "session"
                            ? { ...SESSION, id: "foreign-session" }
                            : SESSION,
                    play,
                    starting: fault === "starting",
                    matching: fault !== "context",
                });
                await flush();
                assert.equal(f.stats().settled, false, fault);
                f.coherent();
                await f.complete();
                assert.equal(f.stats().error, null, fault);
                assert(f.stats().clickCount <= 1, "NoDuplicateSwitchOrResume");
            }
        },
    ],
    [
        "correct-ready-fastpath-keeps-owner-checks-and-no-click",
        async () => {
            const f = fixture({
                selected: SESSION,
                play: { scope: SCOPE, revision: 3, domain_version: 2 },
            });
            await f.complete();
            assert.equal(f.stats().error, null);
            assert.equal(f.stats().clickCount, 0);
            assert.equal(f.stats().timerCount, 0);
            assert.equal(f.stats().readyCount, 1);
            for (const name of [
                "selected-scope-head-owned",
                "actual-domain-route",
                "fork-context-exact-current",
            ])
                assert(f.api.checks.includes(name));
        },
    ],
    [
        "never-coherent-readiness-is-bounded-without-native-work",
        async () => {
            const f = fixture({ selected: SESSION });
            await f.complete();
            assert.match(
                f.stats().error?.message ?? "",
                /^D08Domain2ForkDeadline:/,
            );
            assert(f.stats().timerCount > 0 && f.stats().timerCount <= 1500);
            assert.equal(f.stats().clickCount, 0);
            assert.equal(f.stats().readyCount, 0);
        },
    ],
    [
        "actual-failed-check-retains-finite-assertion-and-phase-not-native-transport",
        async () => {
            const f = fixture({
                selected: SESSION,
                play: { scope: SCOPE, revision: 3, domain_version: 2 },
            });
            await f.complete();
            let error;
            try {
                f.api.check(false, "selected-scope-head-owned");
            } catch (e) {
                error = e;
            }
            assert.equal(error?.message, "HarnessAssertion");
            const stateReport = (passed, code) => ({
                synthetic: true,
                passed,
                error: code,
            });
            const value = failure(stateReport, error, f.api.phase(), category);
            assert.deepEqual(value, {
                synthetic: true,
                passed: false,
                error: "HarnessAssertion",
                failure: {
                    phase: "selected-scope-head-owned",
                    error: "HarnessAssertion",
                },
            });
            const transport = failure(
                stateReport,
                Error("Transport"),
                "fixed-transport-phase",
                category,
            );
            assert.equal(transport.error, "Transport");
            assert.equal(transport.failure.error, "Transport");
            assert.equal(JSON.stringify(value).includes("stack"), false);
        },
    ],
];
for (const [name, run] of cases) {
    if (!factory || !failure || !category) {
        results.push({ name, status: "UNRUN_SETUP" });
        continue;
    }
    try {
        await run();
        results.push({ name, status: "PASS" });
    } catch (error) {
        results.push({
            name,
            status: "FAIL",
            error: String(error?.message ?? error).slice(0, 300),
        });
    }
}
const report = {
    kind: "d08_domain2_fork_session_independent_first_v1",
    authored: cases.length,
    executed: results.filter((r) => r.status !== "UNRUN_SETUP").length,
    passed: results.filter((r) => r.status === "PASS").length,
    failed: results.filter((r) => r.status === "FAIL").length,
    setup,
    results,
    sources,
    limits: [
        "Source author UNRUN; no app retry, resource admission, pixels or native qualification",
        "Actual journey closures; synthetic async controllers, DOM click, frames and bounded virtual10ms timers",
        "No Controller/Rust changes, extra resume, canonical mutation, generation, file writes, children or bundles",
        "Virtual deadline is algorithm coverage, not an observed150s native timeout",
    ],
};
const output = JSON.stringify(report);
assert(Buffer.byteLength(output) + 1 <= 8192, "BoundedEightKiBReport");
console.log(output);
process.exitCode = setup.length ? 2 : report.failed ? 1 : 0;
