// Closed synthetic native journey launcher. No desktop input/activation/capture.
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import {
    mkdir,
    readFile,
    writeFile,
    readdir,
    lstat,
    realpath,
} from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID, createHash } from "node:crypto";

const root = fileURLToPath(new URL(".", import.meta.url));
const base = process.env.LOCALLORE_M07_MEMORY_ARTIFACT_ROOT;
const target = process.env.LOCALLORE_M07_MEMORY_TARGET_DIR;
async function ownedDirectory(value) {
    if (!value || !path.isAbsolute(value))
        throw Error("TrustedOwnedDirectoryRequired");
    const resolved = path.resolve(value);
    if ((await realpath(resolved)).toLowerCase() !== resolved.toLowerCase())
        throw Error("UnsafeOwnedDirectory");
    for (let current = resolved; ; current = path.dirname(current)) {
        const info = await lstat(current);
        if (!info.isDirectory() || info.isSymbolicLink())
            throw Error("UnsafeOwnedDirectory");
        if (path.dirname(current) === current) break;
    }
    return resolved;
}
const artifactRoot = await ownedDirectory(base);
const targetRoot = await ownedDirectory(target);
if ((process.env.LIBSQLITE3_FLAGS ?? "").trim())
    throw Error("OrdinaryUncappedSQLiteRequired");
const folder = path.join(artifactRoot, `author-native-${randomUUID()}`);
await mkdir(folder); // A new owned leaf only; no deletion or reuse.
const db = path.join(folder, "stories-v1.sqlite");
const executable = path.join(
    targetRoot,
    "debug",
    "locallore-desktop-spike.exe",
);
console.log(`AUTHOR native local artifacts: ${folder}`);
Object.assign(process.env, {
    CARGO_BUILD_JOBS: "1",
    CARGO_PROFILE_DEV_DEBUG: "0",
    CARGO_PROFILE_TEST_DEBUG: "0",
    CARGO_INCREMENTAL: "0",
});
let runNumber = 0;
async function run(command, args, env = {}) {
    const log = `run-${++runNumber}`;
    const bounded = { stdout: Buffer.alloc(0), stderr: Buffer.alloc(0) };
    let truncated = false,
        timedOut = false;
    const result = await new Promise((resolve) => {
        const child = spawn(command, args, {
            cwd: root,
            stdio: ["ignore", "pipe", "pipe"],
            windowsHide: true,
            shell: false,
            env: { ...process.env, ...env },
        });
        for (const channel of ["stdout", "stderr"])
            child[channel].on("data", (chunk) => {
                const available = 262144 - bounded[channel].length;
                if (chunk.length > available) truncated = true;
                if (available > 0)
                    bounded[channel] = Buffer.concat([
                        bounded[channel],
                        chunk.subarray(0, available),
                    ]);
            });
        const timer = setTimeout(
            () => {
                timedOut = true;
                child.kill();
            },
            command === "cargo" ? 900000 : 240000,
        );
        child.once("error", (error) => {
            clearTimeout(timer);
            resolve({
                code: null,
                signal: null,
                error: error.code ?? "SpawnFailure",
            });
        });
        child.once("close", (code, signal) => {
            clearTimeout(timer);
            resolve({ code, signal, error: null });
        });
    });
    for (const channel of ["stdout", "stderr"])
        await writeFile(
            path.join(folder, `${log}-${channel}.log`),
            bounded[channel],
            { flag: "wx" },
        );
    await writeFile(
        path.join(folder, `${log}-process.json`),
        JSON.stringify({ ...result, truncated, timedOut }, null, 2),
        { flag: "wx" },
    );
    console.log(`${log}: exit ${result.code}; bounded logs retained`);
    if (result.code !== 0 || timedOut || truncated)
        throw Error(`AuthorHarnessChildFailure:${log}`);
}
const git = promisify(execFile);
const sourceRevision = (
    await git("git", ["rev-parse", "HEAD"], { cwd: root })
).stdout.trim();
const sourceDirty =
    (await git("git", ["status", "--porcelain"], { cwd: root })).stdout.trim()
        .length > 0;
// Retain source identity even when a build or an actual native journey fails.
// These are fixed application/shared inputs, never renderer-selected paths.
const startInputSHA256 = Object.fromEntries(
    await Promise.all(
        [
            "author-harness.mjs",
            "ui/main.tsx",
            "ui/author-native-journeys.ts",
            "ui/author-controller.ts",
            "ui/timeline-controller.ts",
            "ui/AuthorPanel.tsx",
            "ui/broker-retention.ts",
            "ui/v2-play-controller.ts",
            "src-tauri/src/main.rs",
            "src-tauri/src/author_ipc.rs",
            "src-tauri/src/author_commands.rs",
            "../../crates/locallore/src/inference.rs",
            "../../Cargo.lock",
        ].map(async (file) => [
            file,
            createHash("sha256")
                .update(await readFile(path.join(root, file)))
                .digest("hex"),
        ]),
    ),
);
await writeFile(
    path.join(folder, "source-manifest.json"),
    JSON.stringify(
        {
            version: 1,
            synthetic: true,
            qualification: "pending",
            sourceRevision,
            sourceDirty,
            node: process.version,
            backend: "native",
            desktopControl: false,
            inputSHA256: startInputSHA256,
        },
        null,
        2,
    ),
    { flag: "wx" },
);
await run(process.execPath, ["build.mjs", "--harness"]);
await run("cargo", [
    "build",
    "--manifest-path",
    "src-tauri/Cargo.toml",
    "--locked",
    "--offline",
    "--features",
    "dev-harness",
    "--target-dir",
    targetRoot,
]);
const labels = {
    initial: [
        "consent",
        "preview",
        "rejected",
        "pending",
        "cancelled",
        "saved",
        "history",
        "observer",
        "receipt",
        "turn-cancelled",
        "stale-context",
        "late-cancel",
        "unknown",
        "recovered",
        "narrow",
    ].map((s) => `author-native-${s}`),
    restart: ["author-native-restarted", "author-native-reopened"],
};
const reports = [],
    checks = new Set(),
    artifacts = {};
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
for (const stage of ["initial", "restart"]) {
    const directory = path.join(folder, stage);
    await run(executable, [], {
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_M08_AUTHOR_HARNESS: "1",
        LOCALLORE_M07_MEMORY_HARNESS: "0",
        LOCALLORE_D03_HARNESS: "0",
        LOCALLORE_D04_HARNESS: "0",
        LOCALLORE_D05_HARNESS: "0",
        LOCALLORE_D06_HARNESS: "0",
        LOCALLORE_D06_CAPTURE_HARNESS: "0",
        LOCALLORE_M07_LEGACY_HARNESS: "0",
        LOCALLORE_D07_HARNESS: "0",
        LOCALLORE_D07_CURATED_HARNESS: "0",
        LOCALLORE_D08_HARNESS: "0",
        LOCALLORE_D08_TIMELINE_HARNESS: "0",
        LOCALLORE_D08_FORK_HARNESS: "0",
        LOCALLORE_TEST_STORAGE_FAILURE: "0",
        LOCALLORE_D02_ARTIFACT_DIR: directory,
        LOCALLORE_TEST_MEMORY: "0",
        LOCALLORE_TEST_WORKSPACE: db,
        LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
    });
    const filenames = await readdir(directory);
    const reportBytes = await readFile(path.join(directory, "report.json"));
    const report = JSON.parse(reportBytes.toString("utf8"));
    if (
        report.synthetic !== true ||
        report.passed !== true ||
        report.stage !== stage ||
        report.realModelGeneration !== false ||
        !Array.isArray(report.checks)
    )
        throw Error(
            `AuthorJourneysFailed:${stage}:${report.failedCheck ?? "Report"}`,
        );
    for (const check of report.checks) {
        if (typeof check !== "string") throw Error("InvalidCheck");
        checks.add(check);
    }
    const actual = filenames
        .filter((f) => f.endsWith(".png"))
        .map((f) => f.slice(0, -4))
        .sort();
    if (JSON.stringify(actual) !== JSON.stringify([...labels[stage]].sort()))
        throw Error(`AuthorCaptureLabels:${stage}`);
    const permitted = new Set([
        "report.json",
        ...labels[stage].flatMap((label) => [
            `${label}.png`,
            `${label}.json`,
            `${label}.capture.json`,
        ]),
    ]);
    if (filenames.some((name) => !permitted.has(name)))
        throw Error(`UnexpectedAuthorArtifact:${stage}`);
    for (const label of labels[stage]) {
        for (const suffix of [".json", ".capture.json", ".png"]) {
            const name = label + suffix,
                bytes = await readFile(path.join(directory, name));
            if (bytes.length > (suffix === ".png" ? 16777216 : 262144))
                throw Error(`AuthorArtifactBudget:${stage}:${name}`);
            artifacts[`${stage}/${name}`] = {
                bytes: bytes.length,
                sha256: hash(bytes),
            };
            if (suffix === ".capture.json") {
                const capture = JSON.parse(bytes.toString("utf8"));
                if (
                    capture.label !== label ||
                    capture.rendering !== "native-webview2" ||
                    capture.synthetic !== true
                )
                    throw Error(`AuthorNotNativeRendering:${label}`);
            } else if (suffix === ".json") {
                const snapshot = JSON.parse(bytes.toString("utf8"));
                if (
                    snapshot.synthetic !== true ||
                    !Number.isSafeInteger(snapshot.uiRevision) ||
                    !snapshot.author ||
                    !snapshot.v2 ||
                    !snapshot.dom?.structure
                )
                    throw Error(`AuthorSemanticSnapshot:${label}`);
            } else if (
                !bytes
                    .subarray(0, 8)
                    .equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))
            )
                throw Error(`AuthorImageHeader:${label}`);
        }
    }
    artifacts[`${stage}/report.json`] = {
        bytes: reportBytes.length,
        sha256: hash(reportBytes),
    };
    reports.push({ stage, report });
}
const inputs = [
    "author-harness.mjs",
    "ui/author-native-journeys.ts",
    "ui/author-model.ts",
    "ui/author-controller.ts",
    "ui/timeline-controller.ts",
    "ui/AuthorPanel.tsx",
    "ui/author-broker-binding.ts",
    "ui/broker-retention.ts",
    "ui/BrokerRetentionPanel.tsx",
    "ui/v2-view-model.ts",
    "ui/v2-play-controller.ts",
    "ui/V2PlayPanel.tsx",
    "ui/controller.ts",
    "ui/model.ts",
    "ui/journeys.ts",
    "ui/main.tsx",
    "ui/App.tsx",
    "ui/style.css",
    "dist/app.js",
    "src-tauri/src/main.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/src/author_harness.rs",
    "src-tauri/src/author_commands.rs",
    "src-tauri/src/author_ipc.rs",
    "src-tauri/src/archive.rs",
    "src-tauri/src/lease.rs",
    "src-tauri/build.rs",
    "src-tauri/tauri.conf.json",
    "src-tauri/Cargo.toml",
    "../../Cargo.lock",
    "../../fixtures/lantern_quay.json",
    "../../crates/locallore/src/host.rs",
    "../../crates/locallore/src/host/author_port.rs",
    "../../crates/locallore/src/engine.rs",
    "../../crates/locallore/src/inference.rs",
    "../../crates/locallore/src/author_correction.rs",
    "../../crates/locallore/src/inspection_query.rs",
    "../../crates/locallore/src/inspection_query_v2.rs",
    "../../crates/locallore-workspace/src/lib.rs",
    "../../crates/locallore-workspace/src/author_port.rs",
    "../../crates/locallore-storage/src/author_correction.rs",
];
const inputSHA256 = Object.fromEntries(
    await Promise.all(
        inputs.map(async (file) => [
            file,
            hash(await readFile(path.join(root, file))),
        ]),
    ),
);
inputSHA256["<native-target>/debug/locallore-desktop-spike.exe"] = hash(
    await readFile(executable),
);
await writeFile(
    path.join(folder, "summary.json"),
    JSON.stringify(
        {
            synthetic: true,
            passed: true,
            backend: "native",
            desktopControl: false,
            actualProcessRestart: true,
            realModelGeneration: false,
            authorRestartRecovery: false,
            sourceRevision,
            sourceDirty,
            node: process.version,
            captures: 17,
            checks: [...checks],
            reports,
            inputSHA256,
            artifacts,
        },
        null,
        2,
    ),
    { flag: "wx" },
);
console.log(
    `AUTHOR NATIVE PASS: ${checks.size} distinct assertions,17 app-owned captures; local artifacts: ${folder}`,
);
