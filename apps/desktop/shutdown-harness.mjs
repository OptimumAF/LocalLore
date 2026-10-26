// Fixed app-owned native lifecycle cases, using the existing D02 UI journeys.
// No desktop interaction, remote debugger, arbitrary command or model input.
import assert from "node:assert/strict";
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, readdir } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";
const root = fileURLToPath(new URL(".", import.meta.url));
const args = process.argv.slice(2);
assert(
    args.length >= 1 &&
        args.length <= 2 &&
        ["zero", "seven", "window"].includes(args[0]) &&
        (args.length === 1 || args[1] === "--baseline"),
    "ClosedHarnessArguments",
);
const mode = args[0],
    baseline = args[1] === "--baseline";
const base = process.env.LOCALLORE_D09_SHUTDOWN_ARTIFACT_ROOT;
const target = process.env.LOCALLORE_DESKTOP_TARGET_DIR;
assert(
    base && path.isAbsolute(base) && target && path.isAbsolute(target),
    "TrustedExternalRootsRequired",
);
const folder = path.join(base, `shutdown-${mode}-${randomUUID()}`);
await mkdir(folder, { recursive: false });
const git = async (...args) =>
    (await promisify(execFile)("git", args, { cwd: root })).stdout.trim();
const source = await git("rev-parse", "HEAD");
assert.equal(await git("status", "--porcelain"), "", "CleanSourceRequired");
const executions = [];
async function run(
    label,
    command,
    args,
    env = {},
    expected = 0,
    timeout = 240000,
) {
    let stdout = "",
        stderr = "",
        overflow = false,
        timedOut = false;
    const started = new Date().toISOString();
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
            const next = current + chunk.toString("utf8");
            if (Buffer.byteLength(next) > 1024 * 1024) {
                overflow = true;
                return current;
            }
            return next;
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
        }, timeout);
        child.once("error", (error) => {
            clearTimeout(timer);
            reject(error);
        });
        child.once("close", (exit, signal) => {
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
    executions.push({
        label,
        started,
        ended: new Date().toISOString(),
        ...result,
        timedOut,
        overflow,
        stdoutBytes: Buffer.byteLength(stdout),
        stderrBytes: Buffer.byteLength(stderr),
    });
    await writeFile(
        path.join(folder, "executions.json"),
        JSON.stringify(executions, null, 2),
    );
    assert(!timedOut && !overflow, "OwnedChildBounds");
    assert.equal(result.exit, expected, `${label}:exit`);
    return { stdout, stderr };
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
    0,
    900000,
);
const executable = path.join(target, "debug", "locallore-desktop-spike.exe");
const directory = path.join(folder, "app");
// Do not inherit another harness selection. Only the existing fixed D02 lane.
const harnessEnv = Object.fromEntries(
    Object.keys(process.env)
        .filter((key) =>
            /LOCALLORE_.*HARNESS|LOCALLORE_D09_SHUTDOWN_CASE/.test(key),
        )
        .map((key) => [key, "0"]),
);
const actual = await run(
    "app",
    executable,
    [],
    {
        ...harnessEnv,
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_D09_SHUTDOWN_CASE: mode,
        LOCALLORE_TEST_MEMORY: "1",
        LOCALLORE_TEST_STORAGE_FAILURE: "0",
        LOCALLORE_TEST_RESTART: "0",
        LOCALLORE_D02_ARTIFACT_DIR: directory,
        LOCALLORE_TEST_WORKSPACE: path.join(folder, "unused-synthetic.sqlite"),
        WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:
            "--disable-background-timer-throttling",
    },
    mode === "seven" ? 7 : 0,
);
const report = JSON.parse(
    await readFile(path.join(directory, "report.json"), "utf8"),
);
assert(
    report.passed && report.stage === "reopened",
    "ActualInitialAndReopenedJourneysRequired",
);
const phases = actual.stdout
    .split(/\r?\n/)
    .filter((line) => line.startsWith("LOCALLORE_SHUTDOWN "))
    .map((line) => JSON.parse(line.slice("LOCALLORE_SHUTDOWN ".length)));
assert(phases.length > 0 && phases.length <= 96, "BoundedNativePhasesRequired");
const finalEpoch = phases.find(
    (entry) => entry.phase === "finish_requested",
)?.epoch;
assert.equal(finalEpoch, 3, "ActualReopenedEpoch");
const final = phases.filter((entry) => entry.epoch === finalEpoch);
const at = (phase) => final.findIndex((entry) => entry.phase === phase);
const ordered =
    at("cleanup_confirmed") >= 0 &&
    at("destroy_issued") > at("cleanup_confirmed") &&
    at("native_destroyed") > at("destroy_issued") &&
    at("exit_issued") > at("native_destroyed") &&
    at("exit_permitted") > at("exit_issued");
const labels = (await readdir(directory))
    .filter((name) => name.endsWith(".png"))
    .map((name) => name.slice(0, -4));
assert.equal(labels.length, 21, "ActualD02CaptureCount");
for (const label of labels) {
    const capture = JSON.parse(
        await readFile(path.join(directory, `${label}.capture.json`), "utf8"),
    );
    assert.equal(capture.rendering, "native-webview2", `ActualRender:${label}`);
}
const qualification = {
    version: 1,
    source,
    synthetic: true,
    mode,
    baseline,
    journeysPassed: true,
    nativeIpc: true,
    rendering: "actual-hidden-unfocused-webview2",
    desktopControl: false,
    models: false,
    report,
    images: labels,
    phases,
    destructionBeforeExit: ordered,
    sdkStderrBytes: Buffer.byteLength(actual.stderr),
    sdkStderrPresent: actual.stderr.length > 0,
    executableSha256: createHash("sha256")
        .update(await readFile(executable))
        .digest("hex"),
    executions,
};
await writeFile(
    path.join(folder, "qualification.json"),
    JSON.stringify(qualification, null, 2),
    { flag: "wx" },
);
assert.equal(await git("rev-parse", "HEAD"), source, "SourceUnchanged");
assert.equal(
    await git("status", "--porcelain"),
    "",
    "TerminalCleanSourceRequired",
);
assert.equal(
    ordered,
    !baseline,
    baseline
        ? "BaselineMustExposeOrderingFailure"
        : "ObservedNativeDestructionMustPrecedeExit",
);
console.log(
    JSON.stringify({
        folder,
        source,
        baseline,
        mode,
        images: labels.length,
        destructionBeforeExit: ordered,
        sdkStderrBytes: Buffer.byteLength(actual.stderr),
    }),
);
