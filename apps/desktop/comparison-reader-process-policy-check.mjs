// Independent FIRST: trusted-source policy simulation only. No launcher import,
// OS child, app, IPC, model, asset, filesystem probe, timer wait or desktop use.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { EventEmitter } from "node:events";
import { runInNewContext } from "node:vm";
import path from "node:path";

process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
assert.equal(process.argv.length, 2, "ClosedReaderPolicyArguments");
const source = await readFile(
    new URL("./comparison-reader-harness.mjs", import.meta.url),
    "utf8",
);
const sha256 = (text) => createHash("sha256").update(text).digest("hex");
const plain = (value) => JSON.parse(JSON.stringify(value));
const checks = [],
    setupFailures = [];
function between(start, end) {
    const first = source.indexOf(start),
        last = source.indexOf(end, first + start.length);
    assert(
        first >= 0 &&
            last > first &&
            source.indexOf(start, first + start.length) === -1,
        `UniqueReaderSourceBlock:${start}`,
    );
    return source.slice(first, last);
}
let helpers = null,
    helperSource = null,
    runSource = null,
    launchSource = null;
try {
    helperSource = between(
        "// reader-policy-v1:start",
        "// reader-policy-v1:end",
    );
    helpers = runInNewContext(
        `(() => { "use strict"; ${helperSource}
        return { readerDiagnosticMode, readerChildEnvironment }; })()`,
        { assert },
    );
    for (const name of ["readerDiagnosticMode", "readerChildEnvironment"])
        assert.equal(
            typeof helpers[name],
            "function",
            `ReaderPureHelper:${name}`,
        );
} catch (error) {
    helpers = null;
    setupFailures.push({
        stage: "reader-pure-helpers",
        error: String(error?.message ?? error).slice(0, 500),
    });
}
try {
    runSource = between("async function run(", "async function inventory(");
    // Existing fixed initial/restart call site, stopped BEFORE artifact reads.
    // No additional production helper or marker is requested by this freeze.
    launchSource = between(
        'for (const stage of ["initial", "restart"]) {',
        "const report = await artifactJson(",
    );
} catch (error) {
    setupFailures.push({
        stage: "existing-reader-run-and-call-site",
        error: String(error?.message ?? error).slice(0, 500),
    });
}
async function check(name, body) {
    try {
        await body();
        checks.push({ name, passed: true });
    } catch (error) {
        checks.push({
            name,
            passed: false,
            error: String(error?.message ?? error).slice(0, 500),
        });
    }
}
const selector = "LOCALLORE_D07_NARRATION_DIAGNOSTIC_READER";
const scene = "LOCALLORE_D07_SCENE_COMPARISON_READER";
const literal = "LOCALLORE_D07_LITERAL_COMPARISON_READER";
const withValues = (diagnostic, sceneValue, literalValue) => {
    const result = {};
    for (const [key, value] of [
        [selector, diagnostic],
        [scene, sceneValue],
        [literal, literalValue],
    ])
        if (value !== undefined) result[key] = value;
    return result;
};
if (helpers) {
    // Group 1: all 27 finite absent/0/1 combinations. Disabled new mode does
    // not replace the launcher's existing legacy exclusive-mode check.
    for (const diagnostic of [undefined, "0", "1"])
        for (const sceneValue of [undefined, "0", "1"])
            for (const literalValue of [undefined, "0", "1"])
                await check(
                    `mode:${diagnostic ?? "absent"}/${sceneValue ?? "absent"}/${literalValue ?? "absent"}`,
                    () => {
                        const input = Object.freeze(
                            withValues(diagnostic, sceneValue, literalValue),
                        );
                        const before = plain(input);
                        if (
                            diagnostic === "1" &&
                            (sceneValue !== "1" || literalValue === "1")
                        )
                            assert.throws(() =>
                                helpers.readerDiagnosticMode(input),
                            );
                        else
                            assert.equal(
                                helpers.readerDiagnosticMode(input),
                                diagnostic === "1",
                            );
                        assert.deepEqual(plain(input), before);
                    },
                );
    // Group 2: malformed new selector values cannot silently select legacy.
    for (const value of ["", "2", "true", "01", " 1", "1 ", true, 1, null])
        await check(`selector-malformed:${JSON.stringify(value)}`, () => {
            const input = Object.freeze(withValues(value, "1", "0"));
            assert.throws(() => helpers.readerDiagnosticMode(input));
        });
    // Group 3: enabled-mode prerequisite values are closed 0/1 strings.
    for (const key of [scene, literal])
        for (const value of ["", "2", "true", " 0", true, 0])
            await check(
                `prerequisite-malformed:${key}:${JSON.stringify(value)}`,
                () => {
                    const input = {
                        ...withValues("1", "1", "0"),
                        [key]: value,
                    };
                    assert.throws(() =>
                        helpers.readerDiagnosticMode(Object.freeze(input)),
                    );
                },
            );
    // Group 4: single mixed-case selectors are unambiguous; duplicate aliases
    // refuse even with equal values rather than depend on Windows key order.
    for (const key of [selector, scene, literal]) {
        await check(`single-case-alias:${key}`, () => {
            const input = withValues("1", "1", "0"),
                value = input[key];
            delete input[key];
            input[key.toLowerCase()] = value;
            assert.equal(
                helpers.readerDiagnosticMode(Object.freeze(input)),
                true,
            );
        });
        for (const duplicate of ["same", "conflicting"])
            await check(`ambiguous-case-alias:${key}:${duplicate}`, () => {
                const input = withValues("1", "1", "0");
                input[key.toLowerCase()] =
                    duplicate === "same"
                        ? input[key]
                        : input[key] === "1"
                          ? "0"
                          : "1";
                assert.throws(() =>
                    helpers.readerDiagnosticMode(Object.freeze(input)),
                );
            });
    }
    // Group 5: complete namespace stripping includes model-root aliases, not
    // only HARNESS/TEST names. Unrelated installed-tool settings are preserved.
    await check(
        "environment:copy-strip-entire-case-insensitive-namespace",
        () => {
            const input = Object.freeze({
                PATH: "synthetic-installed-tools",
                TEMP: "D:/Dev/_Temp",
                TMP: "D:/Dev/_Temp",
                CARGO_HOME: "synthetic-existing-cache",
                X_LOCALLORE_MARKER: "keep",
                LOCALLORE_D02_HARNESS: "1",
                locallore_m07_memory_harness: "1",
                LoCaLlOrE_D04_MoDeL_RoOt: "synthetic-never-open-this",
                LOCALLORE_D04_MODEL_ROOT: "synthetic-never-open-that",
                locallore_test_workspace: "synthetic-parent-workspace",
                LoCaLlOrE_UnKnOwN: "remove",
                LOCALLORE_: "remove",
            });
            const before = plain(input),
                output = helpers.readerChildEnvironment(input);
            assert.notEqual(output, input);
            assert.deepEqual(plain(input), before);
            assert(
                !Object.keys(output).some((key) => /^LOCALLORE_/i.test(key)),
            );
            assert.deepEqual(plain(output), {
                PATH: input.PATH,
                TEMP: input.TEMP,
                TMP: input.TMP,
                CARGO_HOME: input.CARGO_HOME,
                X_LOCALLORE_MARKER: "keep",
            });
            output.PATH = "changed-copy";
            assert.equal(input.PATH, "synthetic-installed-tools");
        },
    );
    // Group 6: caller need not pre-enable D02/reader; those are fixed child
    // flags. The mode decision depends only on its accepted selectors.
    await check("mode:no-parent-D02-or-reader-prerequisite", () => {
        const input = Object.freeze(withValues("1", "1", "0"));
        assert.equal(helpers.readerDiagnosticMode(input), true);
        assert.equal(input.LOCALLORE_D02_HARNESS, undefined);
        assert.equal(input.LOCALLORE_D07_COMPARISON_READER_HARNESS, undefined);
    });
    // Group 7: marked policy and selector call precede packet creation/build.
    await check(
        "source:policy-and-mode-check-before-first-packet-write-or-build",
        () => {
            const markerEnd = source.indexOf("// reader-policy-v1:end");
            const call = /readerDiagnosticMode\s*\(\s*process\.env\s*\)/g;
            const matches = [...source.matchAll(call)].map(
                (match) => match.index,
            );
            assert.equal(matches.length, 1, "SingleActualSelectorCall");
            const firstMkdir = source.indexOf("await mkdir(folder,");
            const firstRun = source.indexOf("await run(");
            assert(
                markerEnd < matches[0] &&
                    matches[0] < firstMkdir &&
                    matches[0] < firstRun,
            );
            assert(
                markerEnd < source.indexOf("const literalMode"),
                "PolicyBeforeTopLevelModes",
            );
        },
    );
}
// Group 8: execute ONLY extracted trusted existing run/call-site source with
// fake spawn/writes/timers. No child process or filesystem output can occur.
if (helpers && runSource && launchSource)
    await check(
        "fake-child:actual-initial-restart-fixed-overlay-and-sanitizer",
        async () => {
            const input = Object.freeze({
                PATH: "synthetic-tools",
                TEMP: "D:/Dev/_Temp",
                TMP: "D:/Dev/_Temp",
                locallore_d04_model_root: "synthetic-DO-NOT-PROBE",
                LoCaLlOrE_D04_HaRnEsS: "1",
                LOCALLORE_M07_MEMORY_HARNESS: "1",
                LoCaLlOrE_D07_Selected_Harness: "1",
                locallore_test_workspace: "synthetic-foreign-workspace",
                LOCALLORE_UNKNOWN: "remove",
            });
            const before = plain(input),
                launches = [],
                writes = [],
                timers = new Map();
            let nextTimer = 0;
            const context = {
                assert,
                Buffer,
                path: path.win32,
                process: { env: input },
                readerDiagnosticMode: helpers.readerDiagnosticMode,
                readerChildEnvironment: helpers.readerChildEnvironment,
                literalMode: false,
                sceneMode: true,
                diagnosticMode: true,
                root: "D:/synthetic-reader-policy/source",
                folder: "D:/synthetic-reader-policy/packet",
                executable: "synthetic-reader.exe",
                revision: "synthetic-source",
                unchangedSource: async () => {},
                unchangedProducts: async () => {},
                writeFile: async (...args) => {
                    writes.push(args);
                },
                setTimeout: (callback, milliseconds) => {
                    const id = ++nextTimer;
                    timers.set(id, { callback, milliseconds });
                    return id;
                },
                clearTimeout: (id) => {
                    timers.delete(id);
                },
                spawn: (command, args, options) => {
                    launches.push({
                        command,
                        args: plain(args),
                        options: plain(options),
                    });
                    const child = new EventEmitter();
                    child.pid = 700 + launches.length;
                    child.stdout = new EventEmitter();
                    child.stderr = new EventEmitter();
                    child.kill = () => {
                        throw Error("NoSyntheticKillExpected");
                    };
                    queueMicrotask(() => child.emit("close", 0, null));
                    return child;
                },
            };
            const launch = runInNewContext(
                `(async () => {
        const executions = [], unknownOwnedChildren = []; let ownedDrainUnknown = false;
        ${runSource}
        ${launchSource}
        }
        return { executions, ownedDrainUnknown };
    })`,
                context,
            );
            const result = await launch();
            assert.equal(launches.length, 2);
            assert.equal(result.executions.length, 2);
            assert.equal(result.ownedDrainUnknown, false);
            assert.equal(timers.size, 0);
            assert.equal(
                writes.length,
                6,
                "OnlyFakeStdoutStderrAndExecutionRecords",
            );
            for (const [index, child] of launches.entries()) {
                assert.equal(child.command, "synthetic-reader.exe");
                assert.deepEqual(child.args, []);
                assert.equal(child.options.shell, false);
                assert.equal(child.options.windowsHide, true);
                const env = child.options.env;
                assert.equal(env.PATH, input.PATH);
                assert.equal(env.TEMP, "D:/Dev/_Temp");
                assert.equal(env.TMP, "D:/Dev/_Temp");
                const expected = {
                    LOCALLORE_D02_HARNESS: "1",
                    LOCALLORE_D07_COMPARISON_READER_HARNESS: "1",
                    LOCALLORE_D07_SCENE_COMPARISON_READER: "1",
                    [selector]: "1",
                    LOCALLORE_D03_HARNESS: "0",
                    LOCALLORE_D04_HARNESS: "0",
                    LOCALLORE_D05_HARNESS: "0",
                    LOCALLORE_D06_HARNESS: "0",
                    LOCALLORE_D06_CAPTURE_HARNESS: "0",
                    LOCALLORE_D07_HARNESS: "0",
                    LOCALLORE_D07_CURATED_HARNESS: "0",
                    LOCALLORE_D08_HARNESS: "0",
                    LOCALLORE_D08_TIMELINE_HARNESS: "0",
                    LOCALLORE_D08_FORK_HARNESS: "0",
                    LOCALLORE_M07_LEGACY_HARNESS: "0",
                    LOCALLORE_M07_MEMORY_HARNESS: "0",
                    LOCALLORE_M08_AUTHOR_HARNESS: "0",
                    LOCALLORE_TEST_STORAGE_FAILURE: "0",
                    LOCALLORE_D07_LITERAL_COMPARISON_READER: "0",
                    LOCALLORE_TEST_MEMORY: "0",
                    LOCALLORE_D02_ARTIFACT_DIR: `D:\\synthetic-reader-policy\\packet\\${index === 0 ? "initial" : "restart"}`,
                    LOCALLORE_TEST_WORKSPACE:
                        "D:\\synthetic-reader-policy\\packet\\stories-v1.sqlite",
                    LOCALLORE_TEST_RESTART: index === 0 ? "0" : "1",
                };
                const actual = Object.fromEntries(
                    Object.entries(env).filter(([key]) =>
                        /^LOCALLORE_/i.test(key),
                    ),
                );
                assert.deepEqual(
                    actual,
                    expected,
                    "ExactClosedChildNamespaceNoModelRootOrInheritedAliases",
                );
            }
            assert.deepEqual(plain(input), before);
        },
    );
const failed = checks.filter((entry) => !entry.passed);
console.log(
    JSON.stringify(
        {
            version: 1,
            kind: "comparison_reader_process_policy_review_v1",
            source_sha256: sha256(source),
            helper_sha256: helperSource === null ? null : sha256(helperSource),
            setup: setupFailures,
            passed: checks.length - failed.length,
            failed: failed.length,
            checks,
            native_execution: false,
            native_ipc: false,
            model_execution: false,
            filesystem_probe: false,
            desktop_capture_or_control: false,
        },
        null,
        2,
    ),
);
if (setupFailures.length || failed.length) process.exitCode = 1;
