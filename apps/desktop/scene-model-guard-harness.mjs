// Fixed app-owned Native4 command guards; synthetic staging bytes only.
// SOURCE implementation UNRUN. Root registers the closed native/TS entry first.
import assert from "node:assert/strict";
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import {
    mkdir,
    writeFile,
    readFile,
    lstat,
    realpath,
    readdir,
} from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";
if (process.argv.length !== 2) throw Error("ClosedGuardArgumentsRequired");
const root = fileURLToPath(new URL(".", import.meta.url));
async function ordinaryDirectory(input) {
    assert(input && path.isAbsolute(input), "ExistingOrdinaryRootRequired");
    const result = path.resolve(input);
    assert.equal(
        (await realpath(result)).toLowerCase(),
        result.toLowerCase(),
        "OrdinaryRootIdentity",
    );
    for (let current = result; ; current = path.dirname(current)) {
        const meta = await lstat(current);
        assert(
            meta.isDirectory() && !meta.isSymbolicLink(),
            "OrdinaryRootAncestor",
        );
        if (current === path.dirname(current)) break;
    }
    return result;
}
const base = await ordinaryDirectory(
    process.env.LOCALLORE_SCENE_MODEL_GUARD_ARTIFACT_ROOT,
);
const target = await ordinaryDirectory(
    process.env.LOCALLORE_SCENE_MODEL_GUARD_TARGET_DIR,
);
assert.equal(
    (process.env.LIBSQLITE3_FLAGS ?? "").trim(),
    "",
    "OrdinarySQLiteRequired",
);
const id = randomUUID(),
    outer = path.join(base, `scene-model-guards-${id}`);
await mkdir(outer);
const workspaceParent = path.join(outer, `full-comparison-native-${id}`);
const publication = path.join(outer, `guard-modelpub-${id}`),
    control = path.join(outer, `guard-modelcontrol-${id}`);
for (const dir of [workspaceParent, publication, control]) await mkdir(dir);
const sentinel = `.import-${id}.part`;
const publicBytes = Buffer.from("synthetic-publication-staging-sentinel");
const controlBytes = Buffer.from("synthetic-control-staging-sentinel");
await writeFile(path.join(publication, sentinel), publicBytes, { flag: "wx" });
await writeFile(path.join(control, sentinel), controlBytes, { flag: "wx" });
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const git = promisify(execFile);
const revision = (
    await git("git", ["rev-parse", "HEAD"], { cwd: root })
).stdout.trim();
const inputs = [
    "scene-model-guard-harness.mjs",
    "ui/scene-model-guard-journeys.ts",
    "ui/main.tsx",
    "ui/model.ts",
    "src-tauri/src/scene_model_guard_harness.rs",
    "src-tauri/src/comparison_run_native_harness.rs",
    "src-tauri/src/model_commands.rs",
    "src-tauri/src/models.rs",
    "src-tauri/src/main.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/src/exports.rs",
    "src-tauri/src/lease.rs",
    "src-tauri/Cargo.toml",
    "src-tauri/build.rs",
    "src-tauri/tauri.conf.json",
    "build.mjs",
    "package.json",
    "package-lock.json",
    "../../Cargo.lock",
];
async function hashes(files) {
    const result = {};
    for (const name of files) {
        const file = path.isAbsolute(name) ? name : path.join(root, name);
        await ordinaryDirectory(path.dirname(file));
        const meta = await lstat(file);
        assert(
            meta.isFile() &&
                !meta.isSymbolicLink() &&
                meta.size <= 16 * 1024 * 1024,
            "OrdinaryBoundedInput",
        );
        result[name] = hash(await readFile(file));
    }
    return result;
}
// Source inputs are small. The executable may exceed the source-file budget.
async function productHashes() {
    const result = {};
    for (const name of [
        "dist/app.js",
        "dist/style.css",
        "dist/index.html",
        executable,
    ]) {
        const file = path.isAbsolute(name) ? name : path.join(root, name);
        await ordinaryDirectory(path.dirname(file));
        const meta = await lstat(file);
        assert(
            meta.isFile() &&
                !meta.isSymbolicLink() &&
                meta.size <= 256 * 1024 * 1024,
            "OrdinaryProductRequired",
        );
        result[name] = hash(await readFile(file));
    }
    return result;
}
const sourceHashes = await hashes(inputs);
async function unchangedSource() {
    assert.equal(
        (await git("git", ["rev-parse", "HEAD"], { cwd: root })).stdout.trim(),
        revision,
        "SourceRevisionChanged",
    );
    assert.equal(
        (
            await git("git", ["status", "--porcelain"], { cwd: root })
        ).stdout.trim(),
        "",
        "CleanSourceRequired",
    );
    assert.deepEqual(await hashes(inputs), sourceHashes, "SourceBytesChanged");
}
await unchangedSource();
const executable = path.join(target, "debug", "locallore-desktop-spike.exe");
let harnessProducts = null,
    unknownDrain = false;
const unknownChildren = [],
    executions = [];
async function run(label, command, args, extra = {}, limit = 240000) {
    if (unknownDrain) throw Error("GuardOwnedDrainUnknown");
    await unchangedSource();
    if (command === executable) {
        assert.deepEqual(args, []);
        assert.deepEqual(await productHashes(), harnessProducts);
    }
    const env = { ...process.env };
    for (const key of Object.keys(env))
        if (key.startsWith("LOCALLORE_")) delete env[key];
    const output = { stdout: Buffer.alloc(0), stderr: Buffer.alloc(0) };
    let overflow = false,
        timedOut = false,
        pid = null,
        killAttempted = false,
        killReturned = null,
        killError = null;
    const started = new Date().toISOString();
    const result = await new Promise((resolve) => {
        const child = spawn(command, args, {
            cwd: root,
            shell: false,
            windowsHide: true,
            stdio: ["ignore", "pipe", "pipe"],
            env: {
                ...env,
                CARGO_BUILD_JOBS: "1",
                CARGO_INCREMENTAL: "0",
                CARGO_PROFILE_DEV_DEBUG: "0",
                CARGO_PROFILE_TEST_DEBUG: "0",
                ...extra,
            },
        });
        pid = child.pid ?? null;
        let settled = false,
            grace = null;
        const unknown = (reason) => {
            unknownDrain = true;
            unknownChildren.push({
                label,
                pid,
                reason,
                processTreeContained: false,
            });
        };
        const finish = (value, detach = false) => {
            if (settled) return;
            settled = true;
            clearTimeout(timer);
            if (grace !== null) clearTimeout(grace);
            if (detach) {
                child.stdout.destroy();
                child.stderr.destroy();
                child.unref();
            }
            resolve(value);
        };
        for (const channel of ["stdout", "stderr"])
            child[channel].on("data", (chunk) => {
                const available = 256 * 1024 - output[channel].length;
                if (chunk.length > available) overflow = true;
                if (available > 0)
                    output[channel] = Buffer.concat([
                        output[channel],
                        chunk.subarray(0, available),
                    ]);
            });
        const timer = setTimeout(() => {
            timedOut = true;
            unknown("DirectChildTimeout");
            grace = setTimeout(
                () =>
                    finish(
                        {
                            exit: null,
                            signal: null,
                            closed: false,
                            error: "OwnedDrainUnknown",
                        },
                        true,
                    ),
                5000,
            );
            killAttempted = true;
            try {
                killReturned = child.kill();
            } catch (error) {
                killError = error?.code ?? "KillFailure";
            }
        }, limit);
        child.once("error", (error) => {
            if (settled) return;
            if (pid !== null) unknown("ErrorWithPid");
            finish(
                {
                    exit: null,
                    signal: null,
                    closed: false,
                    error: error.code ?? "SpawnFailure",
                },
                pid !== null,
            );
        });
        child.once("close", (exit, signal) =>
            finish({ exit, signal, closed: true, error: null }),
        );
    });
    await writeFile(path.join(outer, `${label}.stdout.log`), output.stdout, {
        flag: "wx",
    });
    await writeFile(path.join(outer, `${label}.stderr.log`), output.stderr, {
        flag: "wx",
    });
    executions.push({
        label,
        command,
        args,
        started,
        ended: new Date().toISOString(),
        ...result,
        timedOut,
        overflow,
        pid,
        killAttempted,
        killReturned,
        killError,
        unknownDrain,
        processTreeContained: false,
        stdoutBytes: output.stdout.length,
        stderrBytes: output.stderr.length,
    });
    await writeFile(
        path.join(outer, "executions.json"),
        JSON.stringify(executions, null, 2),
    );
    if (unknownDrain) throw Error("GuardOwnedDrainUnknown");
    await unchangedSource();
    if (command === executable)
        assert.deepEqual(await productHashes(), harnessProducts);
    assert(!overflow && !timedOut, `${label}:BoundedProcess`);
    assert.equal(result.exit, 0, `${label}:Exit`);
}
async function inventory(dir) {
    await ordinaryDirectory(dir);
    const names = await readdir(dir);
    assert(names.length <= 1, "ClosedSentinelInventory");
    const result = {};
    for (const name of names) {
        assert.equal(name, sentinel);
        const meta = await lstat(path.join(dir, name));
        assert(
            meta.isFile() && !meta.isSymbolicLink() && meta.size <= 1024,
            "OrdinarySentinel",
        );
        const bytes = await readFile(path.join(dir, name));
        assert(bytes.length <= 1024);
        result[name] = { bytes: bytes.length, sha256: hash(bytes) };
    }
    return result;
}
const expectedPublic = {
    [sentinel]: { bytes: publicBytes.length, sha256: hash(publicBytes) },
};
const expectedControl = {
    [sentinel]: { bytes: controlBytes.length, sha256: hash(controlBytes) },
};
await writeFile(
    path.join(outer, "source-manifest.json"),
    JSON.stringify(
        {
            version: 1,
            source: revision,
            sourceHashes,
            synthetic: true,
            modelExecution: false,
            node: process.version,
        },
        null,
        2,
    ),
    { flag: "wx" },
);
console.log(`SCENE MODEL GUARD local artifacts: ${outer}`);
let failure = null,
    candidate = null,
    restoration = null;
try {
    assert.deepEqual(await inventory(publication), expectedPublic);
    assert.deepEqual(await inventory(control), expectedControl);
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
    harnessProducts = await productHashes();
    await writeFile(
        path.join(outer, "product-manifest.json"),
        JSON.stringify({ source: revision, harnessProducts }, null, 2),
        { flag: "wx" },
    );
    await run("app-guard", executable, [], {
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_TEST_MEMORY: "1",
        LOCALLORE_D07_FULL_COMPARISON_HARNESS: "1",
        LOCALLORE_D07_NATIVE_FULL_HARNESS: "1",
        LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS: "1",
        LOCALLORE_D07_SCENE_MODEL_GUARD_HARNESS: "1",
        LOCALLORE_D04_HARNESS: "0",
        LOCALLORE_D04_MODEL_ROOT: publication,
        LOCALLORE_TEST_WORKSPACE: path.join(
            workspaceParent,
            "stories-v1.sqlite",
        ),
        LOCALLORE_D02_ARTIFACT_DIR: path.join(outer, "initial"),
    });
    const reportFile = path.join(outer, "initial", "report.json"),
        info = await lstat(reportFile);
    assert(info.isFile() && !info.isSymbolicLink() && info.size <= 256 * 1024);
    const reportBytes = await readFile(reportFile);
    assert(reportBytes.length <= 256 * 1024);
    const report = JSON.parse(reportBytes.toString("utf8"));
    assert.equal(report.passed, true);
    assert.equal(report.kind, "scene_model_guard_cohort");
    assert.equal(report.nativeIpc, true);
    assert.equal(report.modelExecution, false);
    assert.equal(report.rendering, "unqualified-no-images");
    assert.deepEqual(report.refusals, {
        model_import: "Forbidden",
        model_load: "Forbidden",
    });
    for (const key of ["before", "after", "control"])
        assert.deepEqual(report[key].publication, expectedPublic);
    assert.deepEqual(report.before.control, expectedControl);
    assert.deepEqual(report.after.control, expectedControl);
    assert.deepEqual(report.control.control, {});
    assert.equal(report.control.picker_calls, 1);
    assert.deepEqual(await inventory(publication), expectedPublic);
    assert.deepEqual(await inventory(control), {});
    assert.deepEqual(
        (await readdir(path.join(outer, "initial"))).sort(),
        ["report.json"],
        "NoRenderOrAdditionalArtifactClaim",
    );
    candidate = {
        version: 1,
        passed: true,
        source: revision,
        nativeIpc: true,
        modelExecution: false,
        rendering: "unqualified-no-images",
        reportSha256: hash(reportBytes),
        report,
        harnessProducts,
        sourceHashes,
        publicationInventory: expectedPublic,
        controlInventory: {},
        executions,
        limitations: [
            "Synthetic private staging roots only; no approved assets",
            "Command-entry guard and actual tiny-file reap control only",
            "No inference, UI render, native-dialog, Android or human-quality qualification",
            "No Job/process-tree containment or timeout-drain qualification",
        ],
    };
} catch (error) {
    failure = error;
} finally {
    if (unknownDrain)
        restoration = {
            passed: false,
            skipped: true,
            launched: false,
            reason: "OwnedDrainUnknown",
            unknownChildren,
        };
    else {
        try {
            await run("normal-frontend-restoration", process.execPath, [
                "build.mjs",
            ]);
            await run(
                "normal-native-restoration",
                "cargo",
                [
                    "build",
                    "--manifest-path",
                    "src-tauri/Cargo.toml",
                    "--locked",
                    "--offline",
                    "--no-default-features",
                    "--bin",
                    "locallore-desktop-spike",
                    "--jobs",
                    "1",
                    "--target-dir",
                    target,
                ],
                {},
                900000,
            );
            restoration = {
                passed: true,
                launched: false,
                products: await productHashes(),
            };
        } catch (error) {
            restoration = {
                passed: false,
                launched: false,
                error: String(error).slice(0, 256),
                unknownDrain,
                unknownChildren,
            };
            failure ??= error;
        }
    }
    await writeFile(
        path.join(outer, "normal-restoration.json"),
        JSON.stringify(restoration, null, 2),
        { flag: "wx" },
    );
}
const outcome =
    failure || !candidate || restoration?.passed !== true
        ? {
              source: revision,
              passed: false,
              error: String(failure ?? "IncompleteGuardCohort").slice(0, 500),
              executions,
              unknownDrain,
              unknownChildren,
              restoration,
          }
        : { ...candidate, restoration };
await writeFile(
    path.join(
        outer,
        outcome.passed ? "qualification.json" : "failure-observation.json",
    ),
    JSON.stringify(outcome, null, 2),
    { flag: "wx" },
);
if (!outcome.passed) throw failure ?? Error("IncompleteGuardCohort");
console.log(
    JSON.stringify({
        passed: true,
        artifactDirectory: outer,
        source: revision,
        nativeIpc: true,
        modelExecution: false,
    }),
);
