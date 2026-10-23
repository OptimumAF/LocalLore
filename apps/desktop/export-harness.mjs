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
    `export-native-${randomUUID()}`,
);
await mkdir(folder, { recursive: true });
const db = path.join(folder, "stories-v1.sqlite");
const exportRoot = path.join(folder, "exports");
await mkdir(exportRoot);
await writeFile(path.join(exportRoot, "blocked"), "synthetic not a directory");
process.env.CARGO_PROFILE_DEV_DEBUG = "0";
process.env.CARGO_PROFILE_TEST_DEBUG = "0";
process.env.CARGO_INCREMENTAL = "0";
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
for (const stage of ["initial", "restart"]) {
    const directory = path.join(folder, stage);
    let opened;
    if (stage === "restart") {
        const saved = [];
        for (const name of await readdir(exportRoot)) {
            try {
                const manifest = JSON.parse(
                    await readFile(
                        path.join(exportRoot, name, "manifest.json"),
                        "utf8",
                    ),
                );
                if (manifest.mode === "full")
                    saved.push(path.join(exportRoot, name));
            } catch {}
        }
        if (saved.length !== 1) throw new Error("ExpectedOneFullSavedSnapshot");
        opened = saved[0];
    }
    await run(executable, [], {
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_D03_HARNESS: "1",
        LOCALLORE_D02_ARTIFACT_DIR: directory,
        LOCALLORE_TEST_MEMORY: "0",
        LOCALLORE_TEST_WORKSPACE: db,
        LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
        LOCALLORE_D03_EXPORT_ROOT: exportRoot,
        ...(opened ? { LOCALLORE_D03_OPEN_ROOT: opened } : {}),
    });
    captures += (await readdir(directory)).filter((f) =>
        f.endsWith(".png"),
    ).length;
    const report = JSON.parse(
        await readFile(path.join(directory, "report.json"), "utf8"),
    );
    if (!report.passed) throw new Error(`ExportJourneysFailed:${stage}`);
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
let publications = 0;
for (const name of await readdir(exportRoot)) {
    if (name.startsWith(".locallore-staging-"))
        throw new Error("LeakedStaging");
    let manifest;
    try {
        manifest = JSON.parse(
            await readFile(
                path.join(exportRoot, name, "manifest.json"),
                "utf8",
            ),
        );
    } catch {
        continue;
    }
    const inventory = [
        "manifest.json",
        ...manifest.files.map((f) => f.path),
    ].sort();
    if (
        JSON.stringify((await readdir(path.join(exportRoot, name))).sort()) !==
        JSON.stringify(inventory)
    )
        throw new Error("UnexpectedPublishedInventory");
    for (const entry of manifest.files) {
        const bytes = await readFile(path.join(exportRoot, name, entry.path));
        if (
            bytes.length !== entry.bytes ||
            createHash("sha256").update(bytes).digest("hex") !== entry.sha256
        )
            throw new Error("PublishedDigestMismatch");
    }
    publications++;
}
if (publications !== 4)
    throw new Error(`UnexpectedPublicationCount${publications}`);
const files = [
    "ui/controller.ts",
    "ui/model.ts",
    "ui/export-journeys.ts",
    "ui/InspectionPanel.tsx",
    "src-tauri/src/exports.rs",
    "src-tauri/src/export_commands.rs",
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
    "export-harness.mjs",
    "../../crates/locallore/src/inspection.rs",
    "../../crates/locallore-storage/src/lib.rs",
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
            publications,
            checks,
            reports,
            inputSHA256,
        },
        null,
        2,
    ),
);
console.log(
    `EXPORT NATIVE PASS: ${checks.length} assertions; same synthetic SQLite database across real executable restart. Local artifacts: ${folder}`,
);
