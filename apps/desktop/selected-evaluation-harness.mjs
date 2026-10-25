// Fixed app-owned WebView2 journeys. No desktop capture, input, dialogs or model.
import assert from "node:assert/strict";
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, readdir, lstat } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = fileURLToPath(new URL(".", import.meta.url));
const base = process.env.LOCALLORE_D07_SELECTED_ARTIFACT_ROOT;
if (!base || !path.isAbsolute(base))
    throw Error("TrustedTaskArtifactRootRequired");
const folder = path.join(base, `comparison-reader-native-${randomUUID()}`);
await mkdir(folder, { recursive: false });
const target =
    process.env.LOCALLORE_D07_SELECTED_TARGET_DIR ??
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
// Frozen mandatory captures. Each must be an actual app-owned WebView image.
const labels = [
    "selected-prepared",
    "selected-completed",
    "selected-summary",
    "selected-left-after",
    "selected-right-after",
    "selected-receipt",
    "selected-capture",
    "selected-outputs",
    "selected-narrow",
    "selected-mira",
    "selected-sable",
    "selected-guard",
    "selected-unknown",
    "selected-recovered",
    "selected-consent-pending",
    "selected-consent-actor",
    "selected-consent-cancelled",
    "selected-consent-denied",
    "selected-context-retired",
    "selected-finished",
];
const reports = [];
let expectedFixtures = null;
for (const stage of ["initial", "restart"]) {
    const directory = path.join(folder, stage);
    await run(`app-${stage}`, executable, [], {
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_D07_COMPARISON_READER_HARNESS: "1",
        LOCALLORE_D07_SELECTED_HARNESS: "1",
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
        LOCALLORE_TEST_MEMORY: "0",
        LOCALLORE_D02_ARTIFACT_DIR: directory,
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
    assert(
        Array.isArray(report.checks) &&
            report.checks.length >= (stage === "restart" ? 158 : 152),
        `FrozenCheckCount:${stage}`,
    );
    const expectedLabels =
        stage === "restart" ? [...labels, "selected-restarted"] : labels;
    const captures = (await readdir(directory))
        .filter((name) => name.endsWith(".png"))
        .map((name) => name.slice(0, -4));
    assert.deepEqual(
        captures.sort(),
        [...expectedLabels].sort(),
        `ActualWebViewImages:${stage}`,
    );
    for (const label of expectedLabels) {
        const capture = JSON.parse(
            await readFile(
                path.join(directory, `${label}.capture.json`),
                "utf8",
            ),
        );
        assert.equal(
            capture.rendering,
            "native-webview2",
            `ActualNativeRendering:${label}`,
        );
        const snapshot = JSON.parse(
            await readFile(path.join(directory, `${label}.json`), "utf8"),
        );
        assert.equal(snapshot.semanticVersion, 2, `SemanticVersion:${label}`);
        assert(snapshot.selectedEvaluation, `SelectedSnapshot:${label}`);
        assert(
            Object.hasOwn(snapshot, "selectedStory") &&
                Object.hasOwn(snapshot, "observer") &&
                Object.hasOwn(snapshot, "revision") &&
                Object.hasOwn(snapshot, "pendingOperation") &&
                Object.hasOwn(snapshot, "displayedReceipt") &&
                Object.hasOwn(snapshot, "visibleError"),
            `CoherentSnapshotFields:${label}`,
        );
    }
    const actual = await inventory(path.join(folder, "comparison-fixtures"));
    const finalSnapshot = JSON.parse(
        await readFile(path.join(directory, "selected-finished.json"), "utf8"),
    );
    assert.deepEqual(
        actual,
        finalSnapshot.fixtureInventory,
        `CompleteSourceFixtureBytesUnchanged:${stage}`,
    );
    if (expectedFixtures)
        assert.deepEqual(
            actual,
            expectedFixtures,
            "RestartPreservesEverySourceFixtureByte",
        );
    expectedFixtures = actual;
}
assert.equal(await gitStatus(), "", "TerminalCleanSourceRequired");
async function gitStatus() {
    return (
        await promisify(execFile)("git", ["status", "--porcelain"], {
            cwd: root,
        })
    ).stdout.trim();
}
const qualification = {
    version: 1,
    passed: true,
    sourceRevision: revision,
    synthetic: true,
    nativeIpc: true,
    rendering: "actual-hidden-unfocused-webview2",
    desktopInput: false,
    nativeDialogsAutomated: false,
    modelExecution: false,
    executions,
    reports,
    fixtureInventory: expectedFixtures,
    executableSha256: digest(await readFile(executable)),
    limitations: [
        "Scripted fake inference only",
        "Fixed native consent and picker doubles; no OS dialogs automated",
        "Installed-model Rust tests are a separate cohort",
        "Images require separate visual inspection",
        "No human quality, whole-app memory, phone parity or release qualification",
    ],
};
await writeFile(
    path.join(folder, "qualification.json"),
    JSON.stringify(qualification, null, 2),
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
