// Fixed synthetic durable native scenario. No desktop input, activation or capture.
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID, createHash } from "node:crypto";
const root = fileURLToPath(new URL(".", import.meta.url));
const folder = path.join(root, "artifacts", `model-native-${randomUUID()}`);
await mkdir(folder, { recursive: true });
const workspaceRoot = path.join(folder, "Unicode Qwen \u6a21\u578b \u00e9");
await mkdir(workspaceRoot);
const db = path.join(workspaceRoot, "stories-v1.sqlite");
await writeFile(path.join(folder, "corrupt.gguf"), "synthetic corrupt model");
process.env.CARGO_PROFILE_DEV_DEBUG = "0";
process.env.CARGO_PROFILE_TEST_DEBUG = "0";
process.env.CARGO_INCREMENTAL = "0";
if (!process.env.LOCALLORE_D04_MODEL_SOURCE)
    throw new Error("ApprovedModelSourceRequired");
const executable = path.join(
    root,
    "src-tauri",
    "target",
    "debug",
    "locallore-desktop-spike.exe",
);
async function run(command, args, env = {}) {
    await new Promise((resolve, reject) => {
        const child = spawn(command, args, {
            cwd: root,
            stdio: "inherit",
            shell: false,
            env: { ...process.env, ...env },
        });
        const timer = setTimeout(() => child.kill(), 1080000);
        child.once("error", reject);
        child.once("exit", (code) => {
            clearTimeout(timer);
            code === 0 ? resolve() : reject(new Error(`ChildExit${code}`));
        });
    });
}
await run(process.execPath, ["stage-runtime.mjs"]);
await run(process.execPath, ["build.mjs", "--harness"]);
await run("cargo", [
    "build",
    "--manifest-path",
    "src-tauri/Cargo.toml",
    "--locked",
    "--offline",
    "--features",
    "dev-harness",
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
        LOCALLORE_D04_HARNESS: "1",
        LOCALLORE_D02_ARTIFACT_DIR: directory,
        LOCALLORE_TEST_MEMORY: "0",
        LOCALLORE_TEST_WORKSPACE: db,
        LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
        LOCALLORE_D04_CASE_ROOT: folder,
        ...(process.env.LOCALLORE_D04_REUSE_MODEL_ROOT
            ? {
                  LOCALLORE_D04_MODEL_ROOT:
                      process.env.LOCALLORE_D04_REUSE_MODEL_ROOT,
              }
            : {}),
    });
    captures += (await readdir(directory)).filter((f) =>
        f.endsWith(".png"),
    ).length;
    const report = JSON.parse(
        await readFile(path.join(directory, "report.json"), "utf8"),
    );
    if (!report.passed) throw new Error(`ModelJourneysFailed:${stage}`);
    for (const file of await readdir(directory))
        if (file.endsWith(".json") && !file.endsWith("capture.json")) {
            const value = JSON.parse(
                await readFile(path.join(directory, file), "utf8"),
            );
            checks.push(...(value.checks ?? []));
        }
    reports.push({ stage, report });
}
checks = [...new Set(checks)];
const files = [
    "ui/controller.ts",
    "ui/model.ts",
    "ui/model-journeys.ts",
    "ui/ModelPanel.tsx",
    "src-tauri/src/models.rs",
    "src-tauri/src/model_commands.rs",
    "ui/App.tsx",
    "ui/main.tsx",
    "src-tauri/src/main.rs",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "host-v1.schema.json",
    "dist/app.js",
    "src-tauri/target/debug/locallore-desktop-spike.exe",
    "src-tauri/src/test_bridge.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/src/lease.rs",
    "ui/host.generated.ts",
    "model-harness.mjs",
    "stage-runtime.mjs",
    "../../crates/locallore/src/play.rs",
    "../../crates/locallore-local-runtime/src/lib.rs",
    "../../crates/locallore-local-runtime/src/adapter.rs",
    "../../native/llama-worker/profile-v1.json",
    "src-tauri/runtime/locallore-llama-worker.exe",
    "../../crates/locallore/src/host.rs",
    "../../crates/locallore-workspace/src/lib.rs",
    "../../crates/locallore-storage/src/catalog.rs",
    "../../crates/locallore-storage/src/turns.rs",
];
const inputSHA256 = Object.fromEntries(
    await Promise.all(
        files.map(async (f) => [
            f,
            createHash("sha256")
                .update(await readFile(path.join(root, f)))
                .digest("hex"),
        ]),
    ),
);
await writeFile(
    path.join(folder, "summary.json"),
    JSON.stringify(
        {
            synthetic: true,
            passed: true,
            desktopControl: false,
            actualProcessRestart: true,
            sourceRevision,
            sourceDirty,
            captures,
            checks,
            reports,
            inputSHA256,
        },
        null,
        2,
    ),
);
console.log(
    `REAL MODEL NATIVE PASS: ${checks.length} assertions; same synthetic SQLite database across real executable restart. Local artifacts: ${folder}`,
);
