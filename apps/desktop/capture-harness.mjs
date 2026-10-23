// Invisible app-owned WebView2 evidence. No desktop control, model or real picker.
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, readdir } from "node:fs/promises";
import { randomUUID, createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL(".", import.meta.url));
const base = process.env.LOCALLORE_D06_CAPTURE_ARTIFACT_ROOT;
const target = process.env.LOCALLORE_D06_CAPTURE_TARGET_DIR;
if (!base || !target) throw Error("TrustedTaskOutputRootsRequired");
const folder = path.join(base, `capture-native-${randomUUID()}`);
await mkdir(folder, { recursive: true });
const destination = path.join(folder, "private-exports");
await mkdir(destination);
const database = path.join(folder, "stories.sqlite");
const executable = path.join(target, "debug", "locallore-desktop-spike.exe");
process.env.CARGO_PROFILE_DEV_DEBUG = "0";
process.env.CARGO_PROFILE_TEST_DEBUG = "0";
process.env.CARGO_INCREMENTAL = "0";
async function run(executable, args, env = {}) {
    await new Promise((resolve, reject) => {
        const child = spawn(executable, args, {
            cwd: root,
            stdio: "inherit",
            shell: false,
            env: { ...process.env, ...env },
        });
        const timer = setTimeout(() => {
            child.kill();
            reject(Error("CaptureHarnessTimeout"));
        }, 360000);
        child.once("error", (error) => {
            clearTimeout(timer);
            reject(error);
        });
        child.once("exit", (code) => {
            clearTimeout(timer);
            code === 0 ? resolve() : reject(Error(`ChildExit${code}`));
        });
    });
}
await run(process.execPath, ["build.mjs", "--harness"]);
await run("cargo", [
    "+1.93.1",
    "build",
    "--manifest-path",
    "src-tauri/Cargo.toml",
    "--features",
    "dev-harness",
    "--locked",
    "--offline",
    "--target-dir",
    target,
]);
const reports = [];
let captures = 0;
for (const stage of ["initial", "restart"]) {
    const directory = path.join(folder, stage);
    await run(executable, [], {
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_D06_CAPTURE_HARNESS: "1",
        LOCALLORE_D02_ARTIFACT_DIR: directory,
        LOCALLORE_TEST_MEMORY: "0",
        LOCALLORE_TEST_WORKSPACE: database,
        LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
        LOCALLORE_D06_CAPTURE_EXPORT_ROOT: destination,
    });
    const report = JSON.parse(
        await readFile(path.join(directory, "report.json"), "utf8"),
    );
    if (!report.passed) throw Error(`CaptureJourneyFailed:${stage}`);
    reports.push(report);
    captures += (await readdir(directory)).filter((f) =>
        f.endsWith(".png"),
    ).length;
}
const exports = await readdir(destination);
if (exports.length !== 1) throw Error("ExpectedOneExactPrivateExport");
const exportPath = path.join(destination, exports[0]);
if ((await readdir(exportPath)).sort().join() !== "capture.json,manifest.json")
    throw Error("UnexpectedPrivateExportFiles");
const bytes = await readFile(path.join(exportPath, "capture.json")),
    manifest = JSON.parse(
        await readFile(path.join(exportPath, "manifest.json"), "utf8"),
    );
if (
    manifest.files[0].bytes !== bytes.length ||
    manifest.files[0].sha256 !==
        createHash("sha256").update(bytes).digest("hex")
)
    throw Error("SavedPrivateBytesMismatch");
const previewSnapshot = JSON.parse(
    await readFile(
        path.join(folder, "initial", "d06-private-preview.json"),
        "utf8",
    ),
);
if (previewSnapshot.capture.preview.text !== bytes.toString("utf8"))
    throw Error("SavedBytesDifferFromVisiblePreview");
const inputs = [
    "ui/capture-model.ts",
    "ui/capture-controller.ts",
    "ui/CapturePanel.tsx",
    "ui/capture-journeys.ts",
    "ui/main.tsx",
    "ui/App.tsx",
    "ui/TurnDebugger.tsx",
    "ui/controller.ts",
    "ui/model.ts",
    "ui/style.css",
    "src-tauri/src/capture_exports.rs",
    "src-tauri/src/exports.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/src/main.rs",
    "src-tauri/src/lease.rs",
    "src-tauri/build.rs",
    "src-tauri/tauri.conf.json",
    "host-v1.schema.json",
    "ui/host.generated.ts",
    "capture-harness.mjs",
    "check-capture-controller.mjs",
    "../../crates/locallore/src/host.rs",
    "../../crates/locallore/src/play.rs",
    "../../crates/locallore/src/turn_capture.rs",
    "../../crates/locallore/src/turn_trace.rs",
    "../../crates/locallore/src/context_compiler.rs",
    "dist/app.js",
];
const hashes = Object.fromEntries(
    await Promise.all(
        inputs.map(async (name) => [
            name,
            createHash("sha256")
                .update(await readFile(path.join(root, name)))
                .digest("hex"),
        ]),
    ),
);
hashes["<own-target>/debug/locallore-desktop-spike.exe"] = createHash("sha256")
    .update(await readFile(executable))
    .digest("hex");
const sourceRevision = (
    await promisify(execFile)("git", ["rev-parse", "HEAD"], { cwd: root })
).stdout.trim();
const sourceDirty =
    (
        await promisify(execFile)("git", ["status", "--porcelain"], {
            cwd: root,
        })
    ).stdout.trim().length !== 0;
const checks = [...new Set(reports.flatMap((r) => r.checks))];
await writeFile(
    path.join(folder, "summary.json"),
    JSON.stringify(
        {
            synthetic: true,
            passed: true,
            backend: "native",
            realModelGeneration: false,
            pickerDouble: true,
            desktopControl: false,
            actualProcessRestart: true,
            sourceRevision,
            sourceDirty,
            nodeVersion: process.version,
            captures,
            checks,
            reports,
            exactSavedExportVerified: true,
            inputSHA256: hashes,
        },
        null,
        2,
    ),
);
console.log(
    `PRIVATE CAPTURE NATIVE PASS: ${checks.length} distinct assertions, ${captures} app-owned PNGs. Artifacts: ${folder}`,
);
