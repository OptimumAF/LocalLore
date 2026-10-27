// Independent admission oracles: actual App/View, synthetic controller state.
// Importing the fixture builds the fixed component bundles, not its prior suite.
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
    using,
    appFixture,
    lab,
    nodes,
    ids,
    tick,
} from "./check-main-comparison-run-native.mjs";

const tests = [];
const test = (name, run) => tests.push({ name, run });
const text = (value) =>
    Array.isArray(value)
        ? value.map(text).join("")
        : value && typeof value === "object"
          ? text(value.props?.children)
          : value == null || typeof value === "boolean"
            ? ""
            : String(value);
function button(tree, label) {
    const found = nodes(tree).filter(
        (node) => node.type === "button" && text(node).trim() === label,
    );
    assert.equal(found.length, 1, `one actual View button: ${label}`);
    return found[0];
}
async function click(node) {
    await Promise.resolve(node.props.onClick());
    await tick();
}
const blockers = ["required", "running", "uncertain"];
function block(a, kind) {
    const old = a.native.get();
    // Synthetic last-reported global cleanup state, not an inferred worker fact.
    a.native.replace(
        kind === "uncertain"
            ? { cleanupUncertain: true, cleanupError: "EvaluationIo" }
            : {
                  cleanup: {
                      ...old.cleanup,
                      cleanup_required: kind === "required",
                      running: kind === "running",
                  },
              },
    );
}
const startLabel = "Start scripted comparison";
const resumeLabel = "Resume next chunk explicitly";

for (const kind of blockers) {
    test(`inactive native cleanup ${kind} disables and fences scripted Start and Resume`, () =>
        using(async (f) => {
            await lab(f);
            const a = appFixture(f),
                initial = a.scripted.get(),
                nativeContext = a.native.get().context;
            a.scripted.replace({ clientId: null, status: null });
            block(a, kind);
            const start = button(a.viewTree(), startLabel);
            // Invoke even a disabled handler: handler admission must be independent.
            await click(start);
            a.scripted.replace({
                clientId: initial.clientId,
                status: initial.status,
            });
            const resume = button(a.viewTree(), resumeLabel);
            await click(resume);
            assert.equal(start.props.disabled, true);
            assert.equal(resume.props.disabled, true);
            assert.deepEqual(
                a.scripted.calls,
                [],
                "neither generation callback dispatched",
            );
            assert.deepEqual(a.native.calls, [], "no implicit cleanup action");
            assert.equal(
                a.native.get().context,
                nativeContext,
                "admission cannot rekey native ownership",
            );
            assert.equal(a.lane().props.value, "scripted_baseline");
        }));
}

for (const action of ["start", "resume"]) {
    test(`retained scripted ${action} handler rechecks newly blocked inactive native state without rerender`, () =>
        using(async (f) => {
            await lab(f);
            const a = appFixture(f);
            if (action === "start")
                a.scripted.replace({ clientId: null, status: null });
            const held = button(
                a.viewTree(),
                action === "start" ? startLabel : resumeLabel,
            );
            assert.equal(
                held.props.disabled,
                false,
                "handler was eligible when captured",
            );
            block(a, action === "start" ? "running" : "uncertain");
            // Deliberately do not render: this is the stale callback boundary.
            await click(held);
            assert.deepEqual(a.scripted.calls, []);
            assert.deepEqual(a.native.calls, []);
            assert.equal(
                a.scripted.get().allowed,
                true,
                "not implemented by withdrawing Story Lab",
            );
        }));
}

for (const kind of blockers) {
    test(`inactive native cleanup ${kind} leaves actual metadata, inspection and cleanup recovery controls usable`, () =>
        using(async (f) => {
            await lab(f);
            const a = appFixture(f);
            block(a, kind);
            for (const label of [
                "Look up exact client",
                "Check status",
                "Refresh saved metadata",
                "Inspect report · asks permission",
            ]) {
                const control = button(a.viewTree(), label);
                assert.equal(control.props.disabled, false, label);
                await click(control);
            }
            assert.deepEqual(a.scripted.calls, [
                "lookup",
                "status",
                "loadCatalog",
            ]);
            assert.deepEqual(a.reader.calls, [
                { action: "close" },
                { action: "pick", runId: ids.scripted },
            ]);
            const close = button(a.viewTree(), "Close captured access");
            assert.equal(close.props.disabled, false);
            await click(close);
            assert.deepEqual(a.scripted.calls, [
                "lookup",
                "status",
                "loadCatalog",
                "close",
            ]);

            f.controller.returnToPlay();
            const cleanup = nodes(a.render()).find(
                (node) =>
                    node.type === "section" &&
                    node.props.id === "comparison-native-cleanup",
            );
            assert(cleanup, "actual native recovery remains outside Story Lab");
            for (const label of ["Refresh cleanup state", "Retry cleanup"]) {
                const control = button(cleanup, label);
                assert.equal(control.props.disabled, false);
                await click(control);
            }
            assert.deepEqual(
                a.native.calls,
                ["cleanup_status", "retry_cleanup"],
                "only explicit recovery actions",
            );
            assert(
                !a.scripted.calls.some((action) =>
                    ["start", "resume"].includes(action),
                ),
            );
        }));
}

test("clear combined admission leaves the actual scripted Start and Resume callbacks usable", () =>
    using(async (f) => {
        await lab(f);
        const a = appFixture(f),
            initial = a.scripted.get();
        a.scripted.replace({ clientId: null, status: null });
        const start = button(a.viewTree(), startLabel);
        assert.equal(start.props.disabled, false);
        await click(start);
        a.scripted.replace({
            clientId: initial.clientId,
            status: initial.status,
        });
        const resume = button(a.viewTree(), resumeLabel);
        assert.equal(resume.props.disabled, false);
        await click(resume);
        assert.deepEqual(a.scripted.calls, ["start", "resume"]);
        assert.deepEqual(a.native.calls, []);
    }));

const checks = [];
for (const { name, run } of tests) {
    try {
        await run();
        checks.push({ name, passed: true });
    } catch (error) {
        checks.push({
            name,
            passed: false,
            error: String(error?.message ?? error).slice(0, 512),
        });
    }
}
const report = {
    version: 1,
    synthetic: true,
    evidence:
        "actual App and ComparisonRunView callbacks with fixture controller doubles and React hook values",
    checks,
    passed: checks.filter((row) => row.passed).length,
    failed: checks.filter((row) => !row.passed).length,
    nativeIpc: false,
    modelExecution: false,
    rendering: "none",
    desktopInput: false,
    limitations: [
        "no actual controller transport or native cleanup proof",
        "no DOM, pixels, layout or accessibility qualification",
        "no permission, model generation or resource qualification",
    ],
};
const desktop = path.dirname(fileURLToPath(import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(desktop, "artifacts/checks");
await mkdir(output, { recursive: true });
const json = JSON.stringify(report, null, 2);
assert(Buffer.byteLength(json) <= 64 * 1024);
await writeFile(
    path.join(output, `native-comparison-admission-${randomUUID()}.json`),
    json,
    { flag: "wx" },
);
console.log(json);
if (report.failed) process.exitCode = 1;
