// Fixed synthetic durable native scenario. No desktop input, activation or capture.
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID, createHash } from "node:crypto";
const root = fileURLToPath(new URL(".", import.meta.url));
const folder = path.join(
    process.env.LOCALLORE_DESKTOP_ARTIFACT_ROOT ?? path.join(root, "artifacts"),
    `durable-native-${randomUUID()}`,
);
await mkdir(folder, { recursive: true });
const db = path.join(folder, "stories-v1.sqlite");
const target =
    process.env.LOCALLORE_DESKTOP_TARGET_DIR ??
    path.join(root, "src-tauri", "target");
const executable = path.join(target, "debug", "locallore-desktop-spike.exe");
async function run(command, args, env = {}) {
    await new Promise((resolve, reject) => {
        const child = spawn(command, args, {
            cwd: root,
            stdio: "inherit",
            shell: false,
            env: { ...process.env, ...env },
        });
        const timer = setTimeout(() => child.kill(), 240000);
        child.once("error", reject);
        child.once("exit", (code) => {
            clearTimeout(timer);
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
for (const stage of ["initial", "restart", "storage-failure"]) {
    const directory = path.join(folder, stage);
    const failedDb = path.join(folder, "invalid-root", "stories-v1.sqlite");
    if (stage === "storage-failure") await mkdir(failedDb, { recursive: true });
    await run(executable, [], {
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_D02_ARTIFACT_DIR: directory,
        LOCALLORE_TEST_MEMORY: "0",
        LOCALLORE_TEST_WORKSPACE: stage === "storage-failure" ? failedDb : db,
        LOCALLORE_TEST_STORAGE_FAILURE: stage === "storage-failure" ? "1" : "0",
        LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
    });
    captures += (await readdir(directory)).filter((f) =>
        f.endsWith(".png"),
    ).length;
    const report = JSON.parse(
        await readFile(path.join(directory, "report.json"), "utf8"),
    );
    if (!report.passed) throw new Error(`DurableJourneysFailed:${stage}`);
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
    "ui/durable-journeys.ts",
    "ui/App.tsx",
    "ui/main.tsx",
    "src-tauri/src/main.rs",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "host-v1.schema.json",
    "dist/app.js",
    executable,
    "src-tauri/src/test_bridge.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/src/lease.rs",
    "ui/host.generated.ts",
    "durable-harness.mjs",
    "../../crates/locallore/src/host.rs",
    "../../crates/locallore-workspace/src/lib.rs",
    "../../crates/locallore-storage/src/catalog.rs",
    "../../crates/locallore-storage/src/turns.rs",
];
const inputSHA256 = Object.fromEntries(
    await Promise.all(
        files.map(async (f) => [
            path.isAbsolute(f)
                ? "<native-target>/debug/locallore-desktop-spike.exe"
                : f,
            createHash("sha256")
                .update(
                    await readFile(path.isAbsolute(f) ? f : path.join(root, f)),
                )
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
    `DURABLE NATIVE PASS: ${checks.length} assertions; same synthetic SQLite database across real executable restart. Local artifacts: ${folder}`,
);
