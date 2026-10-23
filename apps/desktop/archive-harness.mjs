// Fixed synthetic native archive transfer. Pickers are fixed doubles; no dialog/desktop automation.
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import {
    mkdir,
    readFile,
    writeFile,
    readdir,
    copyFile,
    open,
} from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { randomUUID, createHash } from "node:crypto";
import assert from "node:assert/strict";
const root = fileURLToPath(new URL(".", import.meta.url));
const base = process.env.LOCALLORE_D08_ARTIFACT_ROOT,
    target = process.env.LOCALLORE_D08_TARGET_DIR;
if (!base || !target) throw Error("TrustedTaskRootsRequired");
const folder = path.join(base, `archive-native-${randomUUID()}`);
await mkdir(folder, { recursive: true });
const picker = path.join(folder, "picker"),
    exported = path.join(picker, "exports");
await mkdir(exported, { recursive: true });
await writeFile(path.join(picker, "blocked"), "synthetic blocked directory");
await writeFile(path.join(picker, "corrupt.json"), '{"truncated":');
const huge = await open(path.join(picker, "oversize.json"), "wx");
await huge.truncate(32 * 1024 * 1024 + 1);
await huge.close();
process.env.CARGO_PROFILE_DEV_DEBUG = "0";
process.env.CARGO_PROFILE_TEST_DEBUG = "0";
process.env.CARGO_INCREMENTAL = "0";
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
            code === 0 ? resolve() : reject(Error(`ChildExit${code}`));
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
const executable = path.join(target, "debug/locallore-desktop-spike.exe");
const sourceRevision = (
    await promisify(execFile)("git", ["rev-parse", "HEAD"], { cwd: root })
).stdout.trim();
const sourceDirty = !!(
    await promisify(execFile)("git", ["status", "--porcelain"], { cwd: root })
).stdout.trim();
const reports = [];
let checks = [],
    captures = 0;
let transferSHA;
for (const stage of ["source", "import", "restarted"]) {
    const workspace = path.join(
        folder,
        stage === "source" ? "source-workspace" : "destination-workspace",
    );
    await mkdir(workspace, { recursive: true });
    if (stage === "import") {
        const names = (await readdir(exported)).filter((n) =>
            n.endsWith(".locallore-story.json"),
        );
        assert.equal(names.length, 1);
        const bytes = await readFile(path.join(exported, names[0]));
        transferSHA = createHash("sha256").update(bytes).digest("hex");
        await writeFile(path.join(picker, "transfer.json"), bytes);
        const future = JSON.parse(bytes);
        future.version = 2;
        await writeFile(
            path.join(picker, "future.json"),
            JSON.stringify(future),
        );
    }
    const directory = path.join(folder, stage);
    await run(executable, [], {
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_D08_HARNESS: "1",
        LOCALLORE_D08_STAGE: stage,
        LOCALLORE_D08_PICKER_ROOT: picker,
        LOCALLORE_D02_ARTIFACT_DIR: directory,
        LOCALLORE_TEST_MEMORY: "0",
        LOCALLORE_TEST_WORKSPACE: path.join(workspace, "stories-v1.sqlite"),
        LOCALLORE_TEST_RESTART: stage === "restarted" ? "1" : "0",
    });
    const report = JSON.parse(
        await readFile(path.join(directory, "report.json"), "utf8"),
    );
    assert.equal(report.passed, true, JSON.stringify(report));
    assert.deepEqual(report.errors, []);
    reports.push({ stage, report });
    checks.push(...report.checks);
    for (const name of await readdir(directory)) {
        if (name.endsWith(".png")) captures++;
        if (name.endsWith(".json") && !name.endsWith(".capture.json")) {
            const j = JSON.parse(
                await readFile(path.join(directory, name), "utf8"),
            );
            checks.push(...(j.checks ?? []));
        }
    }
}
assert.equal(
    createHash("sha256")
        .update(await readFile(path.join(picker, "transfer.json")))
        .digest("hex"),
    transferSHA,
    "original archive unchanged",
);
const stages = path.join(folder, "destination-workspace/archive-staging-v1");
assert.deepEqual(
    await readdir(stages),
    [],
    "all exact synthetic staging directories cleaned",
);
const files = [
    "ui/ArchivePanel.tsx",
    "ui/archive-model.ts",
    "ui/archive-controller.ts",
    "ui/archive-journeys.ts",
    "ui/main.tsx",
    "ui/App.tsx",
    "ui/controller.ts",
    "ui/style.css",
    "src-tauri/src/archive.rs",
    "src-tauri/src/archive_commands.rs",
    "src-tauri/src/main.rs",
    "src-tauri/src/lease.rs",
    "src-tauri/Cargo.toml",
    "src-tauri/Cargo.lock",
    "src-tauri/build.rs",
    "src-tauri/tauri.conf.json",
    "archive-harness.mjs",
    "check-archive-controller.mjs",
    "verify-frontend.mjs",
    "dist/app.js",
    "../../crates/locallore-storage/src/playable_archive.rs",
    "../../crates/locallore-storage/src/lib.rs",
    "../../crates/locallore-storage/src/turns.rs",
    "../../crates/locallore-storage/src/branches.rs",
    "../../crates/locallore/src/host.rs",
    "../../crates/locallore/src/engine.rs",
    "../../crates/locallore-workspace/src/lib.rs",
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
            sourceRevision,
            sourceDirty,
            backend: "native",
            nativeDialogUIAutomated: false,
            desktopControl: false,
            realModelGeneration: false,
            actualProcessRestart: true,
            captures,
            checks,
            reports,
            transferSHA256: transferSHA,
            inputSHA256: hashes,
        },
        null,
        2,
    ),
);
console.log(
    `ARCHIVE NATIVE PASS: ${checks.length} distinct assertions, ${captures} captures. Local artifacts: ${folder}`,
);
