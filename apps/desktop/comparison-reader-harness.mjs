// Fixed app-owned WebView2 journeys. No desktop capture, input, dialogs or model.
import assert from "node:assert/strict";
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, readdir, lstat } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = fileURLToPath(new URL(".", import.meta.url));
const base = process.env.LOCALLORE_D07_COMPARISON_READER_ARTIFACT_ROOT;
if (!base || !path.isAbsolute(base))
    throw Error("TrustedTaskArtifactRootRequired");
const folder = path.join(base, `comparison-reader-native-${randomUUID()}`);
await mkdir(folder, { recursive: false });
const target =
    process.env.LOCALLORE_D07_COMPARISON_READER_TARGET_DIR ??
    path.join(root, "src-tauri", "target");
const executable = path.join(target, "debug", "locallore-desktop-spike.exe");
const revision = (
    await promisify(execFile)("git", ["rev-parse", "HEAD"], { cwd: root })
).stdout.trim();
assert.equal(
    (
        await promisify(execFile)("git", ["status", "--porcelain"], {
            cwd: root,
        })
    ).stdout.trim(),
    "",
    "CleanSourceRequired",
);
const executions = [];
async function run(label, command, args, env = {}, limit = 240000) {
    const started = new Date().toISOString();
    let stdout = "",
        stderr = "",
        overflow = false,
        timedOut = false;
    const maximum = 1024 * 1024;
    const result = await new Promise((resolve, reject) => {
        const child = spawn(command, args, {
            cwd: root,
            shell: false,
            windowsHide: true,
            stdio: ["ignore", "pipe", "pipe"],
            env: {
                ...process.env,
                CARGO_BUILD_JOBS: "1",
                CARGO_INCREMENTAL: "0",
                CARGO_PROFILE_DEV_DEBUG: "0",
                CARGO_PROFILE_TEST_DEBUG: "0",
                ...env,
            },
        });
        const append = (current, chunk) => {
            const value = current + chunk.toString("utf8");
            if (Buffer.byteLength(value) > maximum) {
                overflow = true;
                return value.slice(0, maximum);
            }
            return value;
        };
        child.stdout.on("data", (chunk) => {
            stdout = append(stdout, chunk);
        });
        child.stderr.on("data", (chunk) => {
            stderr = append(stderr, chunk);
        });
        const timer = setTimeout(() => {
            timedOut = true;
            child.kill();
        }, limit);
        child.once("error", (error) => {
            clearTimeout(timer);
            reject(error);
        });
        child.once("exit", (exit, signal) => {
            clearTimeout(timer);
            resolve({ exit, signal, pid: child.pid });
        });
    });
    await writeFile(path.join(folder, `${label}.stdout.log`), stdout, {
        flag: "wx",
    });
    await writeFile(path.join(folder, `${label}.stderr.log`), stderr, {
        flag: "wx",
    });
    const entry = {
        label,
        command,
        args,
        started,
        ended: new Date().toISOString(),
        ...result,
        timedOut,
        overflow,
        stdoutBytes: Buffer.byteLength(stdout),
        stderrBytes: Buffer.byteLength(stderr),
    };
    executions.push(entry);
    await writeFile(
        path.join(folder, "executions.json"),
        JSON.stringify(executions, null, 2),
    );
    assert(!timedOut, `${label}:owned-process-timeout`);
    assert(!overflow, `${label}:bounded-output-overflow`);
    assert.equal(result.exit, 0, `${label}:exit`);
}
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
async function inventory(directory) {
    const files = {};
    let bytes = 0;
    async function visit(current, depth) {
        assert(depth <= 8, "FixtureDepth");
        for (const name of (await readdir(current)).sort()) {
            const full = path.join(current, name),
                stat = await lstat(full);
            assert(!stat.isSymbolicLink(), "FixtureLink");
            if (stat.isDirectory()) await visit(full, depth + 1);
            else {
                assert(
                    stat.isFile() && stat.size <= 8 * 1024 * 1024,
                    "FixtureFileBudget",
                );
                bytes += stat.size;
                assert(bytes <= 64 * 1024 * 1024, "FixtureTotalBudget");
                assert(Object.keys(files).length < 2048, "FixtureCountBudget");
                files[
                    path.relative(directory, full).replaceAll(path.sep, "/")
                ] = digest(await readFile(full));
            }
        }
    }
    await visit(directory, 0);
    return files;
}
await run("frontend-build", process.execPath, ["build.mjs", "--harness"]);
await run(
    "native-build",
    "cargo",
    [
        "build",
        "--manifest-path",
        "src-tauri/Cargo.toml",
        "--locked",
        "--offline",
        "--features",
        "dev-harness",
        "--jobs",
        "1",
        "--target-dir",
        target,
    ],
    {},
    900000,
);
const reports = [];
let expectedFixtures = null;
for (const stage of ["initial", "restart"]) {
    const directory = path.join(folder, stage);
    await run(`app-${stage}`, executable, [], {
        LOCALLORE_D02_HARNESS: "1",
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
        LOCALLORE_D07_COMPARISON_READER_HARNESS: "1",
        LOCALLORE_D02_ARTIFACT_DIR: directory,
        LOCALLORE_TEST_MEMORY: "0",
        LOCALLORE_TEST_WORKSPACE: path.join(folder, "stories-v1.sqlite"),
        LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
    });
    const report = JSON.parse(
        await readFile(path.join(directory, "report.json"), "utf8"),
    );
    reports.push({ stage, report });
    assert.equal(
        report.passed,
        true,
        `Journeys:${stage}:${report.failedCheck}`,
    );
    const opened = JSON.parse(
        await readFile(
            path.join(
                directory,
                stage === "restart"
                    ? "comparison-restarted.json"
                    : "comparison-open.json",
            ),
            "utf8",
        ),
    );
    assert(
        opened.fixtureInventory &&
            Object.keys(opened.fixtureInventory).length > 0,
        "ActualProducerInventoryRequired",
    );
    const actual = await inventory(path.join(folder, "comparison-fixtures"));
    assert.deepEqual(
        actual,
        opened.fixtureInventory,
        `CompleteFixtureBytesUnchanged:${stage}`,
    );
    if (expectedFixtures)
        assert.deepEqual(
            actual,
            expectedFixtures,
            "RestartPreservesEveryOriginalFixtureByte",
        );
    expectedFixtures = actual;
    const captures = (await readdir(directory)).filter((name) =>
        name.endsWith(".png"),
    );
    assert.equal(captures.length, 15, `ActualWebViewImages:${stage}`);
    for (const name of captures) {
        const capture = JSON.parse(
            await readFile(
                path.join(directory, name.replace(/\.png$/, ".capture.json")),
                "utf8",
            ),
        );
        assert.equal(
            capture.rendering,
            "native-webview2",
            `ActualNativeRendering:${name}`,
        );
        const snapshot = JSON.parse(
            await readFile(
                path.join(directory, name.replace(/\.png$/, ".json")),
                "utf8",
            ),
        );
        assert.equal(snapshot.semanticVersion, 2, `SemanticVersion:${name}`);
        const state = snapshot.comparison;
        const selected = state.source?.rows.find(
            (row) =>
                row.row.turn === state.selected?.turn &&
                row.row.arm === state.selected?.arm,
        );
        assert.deepEqual(
            snapshot.selectedStory,
            selected?.source.scope ?? null,
            `ExperimentScope:${name}`,
        );
        assert.equal(
            snapshot.gameplayContext.revision,
            snapshot.uiRevision,
            `GameplayRevision:${name}`,
        );
        assert.equal(
            snapshot.visibleError,
            state.error,
            `VisibleError:${name}`,
        );
        assert.equal(
            snapshot.selectedReport,
            state.status?.run_token ?? null,
            `ReportToken:${name}`,
        );
        const evidence = state.evidence;
        const revision = evidence
            ? evidence.body.kind === "query"
                ? evidence.body.page.revision
                : evidence.edge === "before"
                  ? evidence.before_head
                  : evidence.edge === "after"
                    ? evidence.after_head
                    : null
            : (selected?.source.after_head ?? null);
        assert.equal(snapshot.revision, revision, `InspectionRevision:${name}`);
        assert.deepEqual(
            snapshot.displayedReceipt,
            evidence?.body.kind === "receipt" ? evidence.body.receipt : null,
            `DisplayedReceipt:${name}`,
        );
        if (evidence) {
            assert.deepEqual(
                snapshot.observer,
                evidence.observer,
                `DisplayedObserver:${name}`,
            );
            assert.deepEqual(
                snapshot.selectedStory,
                evidence.scope,
                `DisplayedScope:${name}`,
            );
            if (evidence.body.kind === "query") {
                assert.equal(
                    evidence.edge,
                    state.querySelection.edge,
                    `QueryEdge:${name}`,
                );
                assert.equal(
                    evidence.body.page.view,
                    state.querySelection.view,
                    `QueryView:${name}`,
                );
                const selectedValues = snapshot.dom.controls
                    .filter((control) => control.tag === "SELECT")
                    .map((control) => control.value);
                assert(
                    selectedValues.includes(state.querySelection.edge) &&
                        selectedValues.includes(state.querySelection.view),
                    `ActualControlSelection:${name}`,
                );
            }
        }
        if (state.status?.running)
            assert.equal(
                snapshot.pendingOperation?.id,
                state.status.operation_id,
                `ActualPendingOperation:${name}`,
            );
        else if (state.uncertain) {
            assert.equal(
                snapshot.pendingOperation?.id,
                null,
                `UnknownPendingIdentity:${name}`,
            );
            assert.equal(
                snapshot.pendingOperation?.phase,
                "acknowledgement_unknown",
                `UnknownPendingPhase:${name}`,
            );
        } else if (state.busy)
            assert.equal(
                snapshot.pendingOperation?.id,
                null,
                `UnobservedPendingIdentity:${name}`,
            );
        else
            assert.equal(
                snapshot.pendingOperation,
                null,
                `NoInventedPendingOperation:${name}`,
            );
    }
}
assert.equal(
    (
        await promisify(execFile)("git", ["rev-parse", "HEAD"], { cwd: root })
    ).stdout.trim(),
    revision,
    "SourceChanged",
);
assert.equal(
    (
        await promisify(execFile)("git", ["status", "--porcelain"], {
            cwd: root,
        })
    ).stdout.trim(),
    "",
    "SourceBecameDirty",
);
const files = [
    "ui/comparison-reader-model.ts",
    "ui/comparison-reader-controller.ts",
    "ui/ComparisonReaderPanel.tsx",
    "ui/comparison-reader-journeys.ts",
    "ui/main.tsx",
    "ui/App.tsx",
    "ui/style.css",
    "src-tauri/src/comparison_commands.rs",
    "src-tauri/src/comparison_reader_harness.rs",
    "src-tauri/src/evaluation.rs",
    "src-tauri/src/evaluation/comparison.rs",
    "src-tauri/src/main.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/tauri.conf.json",
    "dist/app.js",
    "comparison-reader-harness.mjs",
    "check-comparison-reader.mjs",
];
const hashes = Object.fromEntries(
    await Promise.all(
        files.map(async (file) => [
            file,
            digest(await readFile(path.join(root, file))),
        ]),
    ),
);
const summary = {
    version: 1,
    passed: true,
    sourceRevision: revision,
    sourceClean: true,
    synthetic: true,
    nativeIpc: true,
    rendering: "actual-hidden-unfocused-webview2",
    desktopInput: false,
    nativeDialogsAutomated: false,
    modelExecution: false,
    executions,
    reports,
    fixtureFiles: Object.keys(expectedFixtures).length,
    fixtureInventory: expectedFixtures,
    executableSha256: digest(await readFile(executable)),
    hashes,
    limitations: [
        "Synthetic scripted inference only",
        "Fixed native picker doubles; OS dialogs not automated",
        "Selected-case rerun and comparison execution unavailable",
        "Native handle/ack recovery is in memory",
        "Access-time expiry does not guarantee wall-clock release",
        "Whole-report snapshot is last validated at open; selected evidence is refreshed",
        "Native images require separate visual inspection",
    ],
};
await writeFile(
    path.join(folder, "qualification.json"),
    JSON.stringify(summary, null, 2),
    { flag: "wx" },
);
console.log(
    JSON.stringify({
        passed: true,
        artifactDirectory: folder,
        sourceRevision: revision,
        stages: reports.length,
        nativeIpc: true,
        modelExecution: false,
    }),
);
