// Fixed synthetic durable native scenario. No desktop input, activation or capture.
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID, createHash } from "node:crypto";
const root = fileURLToPath(new URL(".", import.meta.url));
const base = process.env.LOCALLORE_D08_FORK_ARTIFACT_ROOT;
if (!base) throw new Error("TrustedTaskArtifactRootRequired");
const folder = path.join(base, `fork-native-${randomUUID()}`);
await mkdir(folder, { recursive: true });
const db = path.join(folder, "stories-v1.sqlite");
process.env.CARGO_PROFILE_DEV_DEBUG = "0";
process.env.CARGO_PROFILE_TEST_DEBUG = "0";
process.env.CARGO_INCREMENTAL = "0";
const target =
    process.env.LOCALLORE_D08_TARGET_DIR ??
    path.join(root, "src-tauri", "target");
const executable = path.join(target, "debug", "locallore-desktop-spike.exe");
let runNumber = 0;
async function run(command, args, env = {}) {
    const logName = `run-${++runNumber}`;
    const bounded = { stdout: Buffer.alloc(0), stderr: Buffer.alloc(0) };
    let truncated = false;
    await new Promise((resolve, reject) => {
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
        const timer = setTimeout(() => child.kill(), 240000);
        child.once("error", reject);
        child.once("exit", async (code) => {
            clearTimeout(timer);
            for (const channel of ["stdout", "stderr"])
                await writeFile(
                    path.join(folder, `${logName}-${channel}.log`),
                    bounded[channel],
                );
            await writeFile(
                path.join(folder, `${logName}-process.json`),
                JSON.stringify({ code, truncated }, null, 2),
            );
            console.log(`${logName}: exit ${code}, bounded logs retained`);
            code === 0 ? resolve() : reject(new Error(`ChildExit${code}`));
        });
    });
}
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
    target,
]);
const sourceRevision = (
    await promisify(execFile)("git", ["rev-parse", "HEAD"], { cwd: root })
).stdout.trim();
const sourceDirty =
    (
        await promisify(execFile)("git", ["status", "--porcelain"], {
            cwd: root,
        })
    ).stdout.trim().length > 0;
const reports = [];
let captures = 0;
let checks = [];
for (const stage of ["initial", "restart"]) {
    const directory = path.join(folder, stage);
    await run(executable, [], {
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_D08_FORK_HARNESS: "1",
        LOCALLORE_D02_ARTIFACT_DIR: directory,
        LOCALLORE_TEST_MEMORY: "0",
        LOCALLORE_TEST_WORKSPACE: db,
        LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
    });
    const report = JSON.parse(
        await readFile(path.join(directory, "report.json"), "utf8"),
    );
    if (!report.passed)
        throw new Error(
            `ForkJourneysFailed:${stage}:${report.failedCheck}:${report.error}`,
        );
    reports.push({ stage, report });
    checks.push(...report.checks);
    for (const file of await readdir(directory))
        if (file.endsWith(".json") && !file.endsWith(".capture.json")) {
            const snapshot = JSON.parse(
                await readFile(path.join(directory, file), "utf8"),
            );
            checks.push(...(snapshot.checks ?? []));
        }
    const stageCaptures = (await readdir(directory)).filter((f) =>
        f.endsWith(".png"),
    ).length;
    if (stageCaptures !== (stage === "initial" ? 11 : 3))
        throw new Error(`NativeCaptureCount:${stage}`);
    captures += stageCaptures;
}
const files = [
    "ui/ForkPanel.tsx",
    "ui/fork-controller.ts",
    "ui/fork-native-journeys.ts",
    "src-tauri/src/fork_commands.rs",
    "src-tauri/src/fork_harness.rs",
    "check-fork-controller.mjs",
    "fork-harness.mjs",
    "ui/TimelinePanel.tsx",
    "ui/timeline-controller.ts",
    "ui/timeline-model.ts",
    "ui/timeline-journeys.ts",
    "ui/timeline-native-journeys.ts",
    "ui/controller.ts",
    "ui/App.tsx",
    "ui/model.ts",
    "ui/main.tsx",
    "ui/style.css",
    "dist/app.js",
    "src-tauri/src/timeline_harness.rs",
    "src-tauri/src/main.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/src/lease.rs",
    "src-tauri/build.rs",
    "src-tauri/tauri.conf.json",
    "src-tauri/Cargo.toml",
    "../../Cargo.lock",
    "host-v1.schema.json",
    "ui/host.generated.ts",
    "timeline-harness.mjs",
    "check-timeline-controller.mjs",
    "verify-frontend.mjs",
    "../../crates/locallore/src/host.rs",
    "../../crates/locallore/src/engine.rs",
    "../../crates/locallore-workspace/src/lib.rs",
    "../../crates/locallore-storage/src/branch_catalog.rs",
    "../../crates/locallore-storage/src/branch_retention.rs",
    "../../crates/locallore-storage/src/lib.rs",
];
const hashes = Object.fromEntries(
    await Promise.all(
        files.map(async (f) => [
            f,
            createHash("sha256")
                .update(await readFile(path.join(root, f)))
                .digest("hex"),
        ]),
    ),
);
hashes["<native-target>/debug/locallore-desktop-spike.exe"] = createHash(
    "sha256",
)
    .update(await readFile(executable))
    .digest("hex");
checks = [...new Set(checks)];
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
            sourceRevision,
            sourceDirty,
            captures,
            checks,
            reports,
            inputSHA256: hashes,
        },
        null,
        2,
    ),
);
console.log(
    `FORK NATIVE PASS: ${checks.length} distinct assertions, ${captures} captures. Local artifacts: ${folder}`,
);
