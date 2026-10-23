// Fixed synthetic durable native scenario. No desktop input, activation or capture.
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID, createHash } from "node:crypto";
const root = fileURLToPath(new URL(".", import.meta.url));
const base = process.env.LOCALLORE_D07_ARTIFACT_ROOT;
if (!base) throw new Error("TrustedTaskArtifactRootRequired");
const folder = path.join(base, `evaluation-native-${randomUUID()}`);
await mkdir(folder, { recursive: true });
const db = path.join(folder, "stories-v1.sqlite");
process.env.CARGO_PROFILE_DEV_DEBUG = "0";
process.env.CARGO_PROFILE_TEST_DEBUG = "0";
process.env.CARGO_INCREMENTAL = "0";
const target =
    process.env.LOCALLORE_D07_TARGET_DIR ??
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
for (const stage of ["initial", "restart"]) {
    const directory = path.join(folder, stage);
    await run(executable, [], {
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_D07_HARNESS: "1",
        LOCALLORE_D02_ARTIFACT_DIR: directory,
        LOCALLORE_TEST_MEMORY: "0",
        LOCALLORE_TEST_WORKSPACE: db,
        LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
    });
    const report = JSON.parse(
        await readFile(path.join(directory, "report.json"), "utf8"),
    );
    if (!report.passed) throw new Error(`EvaluationJourneysFailed:${stage}`);
    reports.push({ stage, report });
    checks.push(...report.checks);
    captures += (await readdir(directory)).filter((f) =>
        f.endsWith(".png"),
    ).length;
}
const files = [
    "ui/EvaluationPanel.tsx",
    "ui/evaluation-controller.ts",
    "ui/evaluation-model.ts",
    "ui/evaluation-journeys.ts",
    "ui/controller.ts",
    "ui/App.tsx",
    "ui/model.ts",
    "ui/main.tsx",
    "ui/style.css",
    "src-tauri/src/evaluation.rs",
    "src-tauri/src/evaluation_commands.rs",
    "src-tauri/src/main.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/src/lease.rs",
    "src-tauri/build.rs",
    "src-tauri/tauri.conf.json",
    "src-tauri/Cargo.toml",
    "src-tauri/Cargo.lock",
    "host-v1.schema.json",
    "ui/host.generated.ts",
    "dist/app.js",
    "evaluation-harness.mjs",
    "check-evaluation-controller.mjs",
    "verify-frontend.mjs",
    "../../crates/locallore-eval/src/lib.rs",
    "../../crates/locallore-eval/build.rs",
    "../../crates/locallore-eval/Cargo.lock",
    "../../fixtures/eval/reference-v1.json",
    "../../crates/locallore/src/host.rs",
    "../../crates/locallore/src/engine.rs",
    "../../crates/locallore/src/play.rs",
    "../../crates/locallore-workspace/src/lib.rs",
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
    `EVALUATION NATIVE PASS: ${checks.length} distinct assertions, ${captures} captures. Local artifacts: ${folder}`,
);
