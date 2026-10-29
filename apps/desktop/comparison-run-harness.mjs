// Fixed app-owned comparison journeys; --native explicitly uses installed assets.
import assert from "node:assert/strict";
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
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { createReadStream } from "node:fs";

assert.equal(process.platform, "win32", "WindowsWebView2Required");
const sceneMode = process.argv.length === 3 && process.argv[2] === "--native-scene-v1";
const nativeMode = sceneMode || (process.argv.length === 3 && process.argv[2] === "--native");
assert(process.argv.length === 2 || nativeMode, "ClosedHarnessArguments");
// MXC may replace a launcher's inherited values. Set these in the actual
// project process as well; every child below receives the same D: locations.
process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
const root = fileURLToPath(new URL(".", import.meta.url));
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
const hash = (value) =>
    typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
const guid = (value) =>
    typeof value === "string" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(
        value,
    );
const safe = (value) => Number.isSafeInteger(value) && value >= 0;
const git = async (...args) =>
    (
        await promisify(execFile)("git", args, {
            cwd: root,
            shell: false,
            windowsHide: true,
            timeout: 15000,
            maxBuffer: 1024 * 1024,
        })
    ).stdout.trim();
const revision = await git("rev-parse", "HEAD");
const repository = await git("rev-parse", "--show-toplevel");
assert.equal(await git("status", "--porcelain"), "", "CleanSourceRequired");

async function existingDirectory(name) {
    const value = process.env[name];
    assert(
        value && path.isAbsolute(value),
        `${name}:AbsoluteExistingDirectoryRequired`,
    );
    const metadata = await lstat(value);
    assert(
        metadata.isDirectory() && !metadata.isSymbolicLink(),
        `${name}:OrdinaryDirectoryRequired`,
    );
    return path.resolve(value);
}
const base = await existingDirectory(
    "LOCALLORE_D07_FULL_COMPARISON_ARTIFACT_ROOT",
);
const target = await existingDirectory(
    "LOCALLORE_D07_FULL_COMPARISON_TARGET_DIR",
);
if (sceneMode) {
    for (const directory of [root, repository, base, target]) await ordinarySceneDirectory(directory);
}
const targetRelative = path.relative(repository, target);
assert(
    targetRelative.startsWith(`..${path.sep}`) ||
        path.isAbsolute(targetRelative),
    "ExternalBuildTargetRequired",
);
const folder = path.join(base, `full-comparison-native-${randomUUID()}`);
await mkdir(folder, { recursive: false });
const launcherSha256 = digest(await readFile(fileURLToPath(import.meta.url)));
const executable = path.join(target, "debug", "locallore-desktop-spike.exe");
const executions = [],
    reports = [],
    inventories = [];
const limits = {
    processOutputBytes: 1024 * 1024,
    appWatchdogMs: nativeMode ? 2100000 : 900000,
    launcherWatchdogMs: nativeMode ? 2160000 : 960000,
    captures: 40,
    pngBytes: 16 * 1024 * 1024,
    jsonBytes: 256 * 1024,
    inventoryDepth: 12,
    inventoryEntries: 8192,
    inventoryFileBytes: 8 * 1024 * 1024,
    inventoryTotalBytes: 128 * 1024 * 1024,
};
let expectedInventory = null,
    executableSha256 = null;
let nativeAssets = null;
let sceneSourceHashes = null, sceneHarnessProducts = null, sceneRestoration = null;
let sceneOwnedDrainUnknown = false;
const sceneUnknownChildren = [];
const sceneReviewSlots = ["courier-01", "courier-05", "courier-12", "courier-22"]
    .flatMap((turn) => ["left", "right"].map((arm) => ({ turn, arm, label: `full-scene-${turn}-${arm}` })));
const sceneInputFiles = ["comparison-run-harness.mjs", "ui/comparison-run-native-journeys.ts", "ui/main.tsx",
    "ui/comparison-run-controller.ts", "ui/comparison-run-model.ts", "ui/comparison-run-view.tsx",
    "ui/comparison-reader-controller.ts", "ui/comparison-reader-model.ts", "ui/ComparisonReaderPanel.tsx",
    "src-tauri/src/main.rs", "src-tauri/src/harness.rs", "src-tauri/src/comparison_run_native_harness.rs",
    "src-tauri/src/model_commands.rs", "src-tauri/src/models.rs", "src-tauri/src/evaluation/comparison_run.rs",
    "src-tauri/src/evaluation/comparison_run/native.rs", "src-tauri/src/evaluation/comparison_run/native_for.rs",
    "src-tauri/src/evaluation/comparison_run/versioned.rs", "src-tauri/Cargo.toml", "src-tauri/build.rs",
    "src-tauri/tauri.conf.json", "ui/style.css", "stage-runtime.mjs", "build.mjs", "package.json", "package-lock.json", "../../Cargo.lock"];
async function ordinarySceneDirectory(value) {
    assert(value && path.isAbsolute(value), "SceneOrdinaryExistingDirectoryRequired");
    const resolved = path.resolve(value), actual = path.resolve(await realpath(value));
    assert.equal(actual.toLowerCase(), resolved.toLowerCase(), "SceneDirectoryRedirected");
    assert.equal(path.parse(actual).root.toLowerCase(), "d:\\", "PhysicalDProjectStorageRequired");
    for (let current = resolved; ; current = path.dirname(current)) {
        const metadata = await lstat(current);
        assert(metadata.isDirectory() && !metadata.isSymbolicLink(), "SceneOrdinaryAncestorRequired");
        if (current === path.dirname(current)) break;
    }
    return resolved;
}
async function sceneHashes(files, cap = 16 * 1024 * 1024) {
    const result = {};
    for (const name of files) {
        const file = path.isAbsolute(name) ? name : path.join(root, name);
        await ordinarySceneDirectory(path.dirname(file));
        result[name] = digest(await boundedFile(file, cap));
    }
    return result;
}
const sceneProducts = () => sceneHashes(["dist/app.js", "dist/style.css", "dist/index.html",
    "src-tauri/runtime/locallore-llama-worker.exe", path.join(target, "debug/runtime/locallore-llama-worker.exe"), executable], 256 * 1024 * 1024);

async function approvedNativeAssets() {
    const reuseRoot = sceneMode ? await ordinarySceneDirectory(process.env.LOCALLORE_D04_REUSE_MODEL_ROOT) : null;
    if (reuseRoot) {
        const relative = path.relative(folder, reuseRoot);
        assert(relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative), "ExistingPublicationOutsideNewWorkspaceRequired");
        for (const destination of [root, target, path.join(root, "src-tauri/runtime"), path.join(target, "debug/runtime")]) {
            const relation = path.relative(reuseRoot, destination);
            assert(relation.startsWith(`..${path.sep}`) || path.isAbsolute(relation), "NoStagingInsideReusedPublication");
        }
    }
    const model = sceneMode ? path.join(reuseRoot, "Qwen3-0.6B-Q8_0.gguf") : process.env.LOCALLORE_D07_NATIVE_MODEL_SOURCE;
    const worker = process.env.LOCALLORE_D04_WORKER_SOURCE;
    const specs = [
        [
            "model",
            model,
            639446688,
            "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031",
        ],
        [
            "worker",
            worker,
            null,
            "b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434",
        ],
    ];
    const verified = {};
    for (const [kind, source, size, expected] of specs) {
        assert(
            source && path.isAbsolute(source),
            `${kind}:ExplicitInstalledAssetRequired`,
        );
        if (sceneMode) await ordinarySceneDirectory(path.dirname(source));
        const metadata = await lstat(source);
        assert(
            metadata.isFile() && !metadata.isSymbolicLink(),
            `${kind}:OrdinaryAssetRequired`,
        );
        assert.equal(
            path.resolve(await realpath(source)).toLowerCase(),
            path.resolve(source).toLowerCase(),
            `${kind}:RedirectedAsset`,
        );
        if (size !== null)
            assert.equal(metadata.size, size, `${kind}:ApprovedSize`);
        else
            assert(
                metadata.size > 0 && metadata.size <= 16 * 1024 * 1024,
                "WorkerSize",
            );
        const hasher = createHash("sha256");
        for await (const bytes of createReadStream(source))
            hasher.update(bytes);
        assert.equal(hasher.digest("hex"), expected, `${kind}:ApprovedHash`);
        verified[kind] = { bytes: metadata.size, sha256: expected };
    }
    return { model, worker, verified, ...(sceneMode ? { reuseRoot, weightsCopied: false, importedByHarness: false } : {}) };
}

async function sourceUnchanged() {
    assert.equal(
        await git("rev-parse", "HEAD"),
        revision,
        "SourceRevisionChanged",
    );
    assert.equal(await git("status", "--porcelain"), "", "SourceTreeChanged");
    if (sceneMode && sceneSourceHashes) assert.deepEqual(await sceneHashes(sceneInputFiles), sceneSourceHashes, "SceneSourceInputsChanged");
}
async function saveExecutions() {
    await writeFile(
        path.join(folder, "executions.json"),
        JSON.stringify(executions, null, 2),
    );
}
async function run(label, command, args, env = {}, timeout = 240000) {
    if (sceneMode) return runScene(label, command, args, env, timeout);
    await sourceUnchanged();
    const started = new Date().toISOString();
    const output = { stdout: [], stderr: [] },
        sizes = { stdout: 0, stderr: 0 },
        observed = { stdout: 0, stderr: 0 };
    let overflow = false,
        timedOut = false,
        spawnError = null;
    const environment = { ...process.env };
    // A prior task's harness must never silently select another journey.
    for (const key of Object.keys(environment)) {
        if (key.startsWith("LOCALLORE_") && key.includes("HARNESS"))
            delete environment[key];
    }
    Object.assign(environment, {
        LOCALLORE_D09_SHUTDOWN_CASE: "0",
        CARGO_BUILD_JOBS: "1",
        CARGO_INCREMENTAL: "0",
        CARGO_PROFILE_DEV_DEBUG: "0",
        CARGO_PROFILE_TEST_DEBUG: "0",
        LIBSQLITE3_FLAGS: "",
        ...env,
    });
    const result = await new Promise((resolve) => {
        const child = spawn(command, args, {
            cwd: root,
            shell: false,
            windowsHide: true,
            stdio: ["ignore", "pipe", "pipe"],
            env: environment,
        });
        const append = (stream, chunk) => {
            observed[stream] += chunk.length;
            const room = limits.processOutputBytes - sizes[stream];
            if (room > 0) {
                const retained = chunk.subarray(0, room);
                output[stream].push(retained);
                sizes[stream] += retained.length;
            }
            if (observed[stream] > limits.processOutputBytes) {
                overflow = true;
                child.kill();
            }
        };
        child.stdout.on("data", (chunk) => append("stdout", chunk));
        child.stderr.on("data", (chunk) => append("stderr", chunk));
        const timer = setTimeout(() => {
            timedOut = true;
            child.kill();
        }, timeout);
        child.once("error", (error) => {
            spawnError = error.code ?? "SpawnError";
        });
        // close, not exit: pipe data is fully drained before logs are sealed.
        child.once("close", (exit, signal) => {
            clearTimeout(timer);
            resolve({ exit, signal, pid: child.pid ?? null });
        });
    });
    const stdout = Buffer.concat(output.stdout),
        stderr = Buffer.concat(output.stderr);
    await writeFile(path.join(folder, `${label}.stdout.log`), stdout, {
        flag: "wx",
    });
    await writeFile(path.join(folder, `${label}.stderr.log`), stderr, {
        flag: "wx",
    });
    executions.push({
        label,
        command,
        args,
        started,
        ended: new Date().toISOString(),
        ...result,
        timeoutMs: timeout,
        timedOut,
        overflow,
        spawnError,
        stdoutBytes: stdout.length,
        stderrBytes: stderr.length,
        observedStdoutBytes: observed.stdout,
        observedStderrBytes: observed.stderr,
        stdoutSha256: digest(stdout),
        stderrSha256: digest(stderr),
    });
    await saveExecutions();
    await sourceUnchanged();
    assert.equal(spawnError, null, `${label}:spawn`);
    assert(!timedOut, `${label}:owned-process-timeout`);
    assert(!overflow, `${label}:bounded-output-overflow`);
    assert.equal(result.exit, 0, `${label}:exit`);
}
// New mode uses the reviewed bounded direct-child policy. The historical V3
// runner remains above, including its original result/acceptance behavior.
async function runScene(label, command, args, env = {}, timeout = 240000) {
    if (sceneOwnedDrainUnknown) throw Error("SceneOwnedDrainUnknown");
    await sourceUnchanged();
    if (command === executable) {
        assert.deepEqual(args, [], "SceneFixedExecutableArguments");
        assert.deepEqual(await sceneProducts(), sceneHarnessProducts, "SceneHarnessProductsChanged");
    }
    const environment = { ...process.env };
    for (const key of Object.keys(environment)) if (key.startsWith("LOCALLORE_")) delete environment[key];
    Object.assign(environment, { TEMP: "D:/Dev/_Temp", TMP: "D:/Dev/_Temp", CARGO_BUILD_JOBS: "1",
        CARGO_INCREMENTAL: "0", CARGO_PROFILE_DEV_DEBUG: "0", CARGO_PROFILE_TEST_DEBUG: "0", LIBSQLITE3_FLAGS: "", ...env });
    const started = new Date().toISOString(), output = { stdout: [], stderr: [] }, sizes = { stdout: 0, stderr: 0 };
    let overflow = false, timedOut = false, pid = null, killAttempted = false, killReturned = null, killError = null;
    const result = await new Promise((resolve) => {
        const child = spawn(command, args, { cwd: root, shell: false, windowsHide: true,
            stdio: ["ignore", "pipe", "pipe"], env: environment });
        pid = child.pid ?? null;
        let settled = false, grace = null;
        const unknown = (reason) => { sceneOwnedDrainUnknown = true; sceneUnknownChildren.push({ label, pid, reason }); };
        const finish = (value, detach = false) => {
            if (settled) return; settled = true; clearTimeout(timer); if (grace !== null) clearTimeout(grace);
            if (detach) { child.stdout.destroy(); child.stderr.destroy(); child.unref(); }
            resolve(value);
        };
        const stop = (reason) => {
            if (killAttempted) return;
            unknown(reason); killAttempted = true;
            grace = setTimeout(() => finish({ exit: null, signal: null, closed: false, spawnError: "OwnedDrainUnknown" }, true), 5000);
            try { killReturned = child.kill(); } catch (error) { killError = error?.code ?? "KillFailure"; }
        };
        for (const channel of ["stdout", "stderr"]) child[channel].on("data", (chunk) => {
            const room = limits.processOutputBytes - sizes[channel];
            if (room > 0) { const retained = chunk.subarray(0, room); output[channel].push(retained); sizes[channel] += retained.length; }
            if (chunk.length > room) { overflow = true; stop("OutputOverflow"); }
        });
        const timer = setTimeout(() => { timedOut = true; stop("DirectChildTimeout"); }, timeout);
        child.once("error", (error) => { if (settled) return;
            if (pid !== null) stop("ErrorWithPid");
            else finish({ exit: null, signal: null, closed: false, spawnError: error.code ?? "SpawnFailure" }); });
        child.once("close", (exit, signal) => finish({ exit, signal, closed: true, spawnError: null }));
    });
    const stdout = Buffer.concat(output.stdout), stderr = Buffer.concat(output.stderr);
    await writeFile(path.join(folder, `${label}.stdout.log`), stdout, { flag: "wx" });
    await writeFile(path.join(folder, `${label}.stderr.log`), stderr, { flag: "wx" });
    executions.push({ label, command, args, started, ended: new Date().toISOString(), ...result, pid,
        timeoutMs: timeout, timedOut, overflow, killAttempted, killReturned, killError,
        ownedDrainUnknown: sceneOwnedDrainUnknown, processTreeContained: false,
        stdoutBytes: stdout.length, stderrBytes: stderr.length, stdoutSha256: digest(stdout), stderrSha256: digest(stderr) });
    await saveExecutions();
    if (sceneOwnedDrainUnknown) throw Error("SceneOwnedDrainUnknown");
    await sourceUnchanged();
    if (command === executable) assert.deepEqual(await sceneProducts(), sceneHarnessProducts, "SceneHarnessProductsChanged");
    assert(!overflow && !timedOut && result.closed && result.spawnError === null, `${label}:SceneBoundedKnownProcess`);
    assert.equal(result.exit, 0, `${label}:exit`);
}
async function boundedFile(file, cap) {
    const metadata = await lstat(file);
    assert(
        metadata.isFile() && !metadata.isSymbolicLink() && metadata.size <= cap,
        "ArtifactFileBudgetOrLink",
    );
    const data = await readFile(file);
    assert(data.length <= cap, "ArtifactChangedBeyondBudget");
    return data;
}
async function json(file) {
    return JSON.parse(
        (await boundedFile(file, limits.jsonBytes)).toString("utf8"),
    );
}
function boundedJson(value) {
    let entries = 0;
    function walk(item, depth) {
        assert(depth <= 32 && ++entries <= 32768, "SemanticStructureBudget");
        if (item === null || typeof item === "boolean") return;
        if (typeof item === "number") {
            assert(Number.isFinite(item), "SemanticNumber");
            return;
        }
        if (typeof item === "string") {
            assert(
                Buffer.byteLength(item) <= limits.jsonBytes,
                "SemanticString",
            );
            return;
        }
        assert(typeof item === "object", "SemanticValue");
        for (const child of Object.values(item)) walk(child, depth + 1);
    }
    walk(value, 0);
}
function observer(value) {
    assert(
        value && typeof value === "object" && !Array.isArray(value),
        "SnapshotObserver",
    );
    assert(
        ["player", "character", "omniscient"].includes(value.kind),
        "SnapshotObserverKind",
    );
    if (value.kind === "character")
        assert(
            typeof value.id === "string" && value.id.length > 0,
            "SnapshotActor",
        );
}

// Updated only by the coordinator's closed journey contract, never CLI input.
const initialLabels = [
    "full-idle",
    "full-running",
    "full-partial",
    "full-completed",
    "full-reader",
    "full-mira",
    "full-sable",
    "full-receipt",
    "full-narrow",
    "full-denied",
    "full-unknown",
    "full-cancelled",
    "full-switched",
    "full-finished",
];
const restartLabels = [
    "full-idle",
    "full-restarted",
    "full-reader",
    "full-finished",
];
const stageInitialLabels = sceneMode ? [...initialLabels, ...sceneReviewSlots.map(({ label }) => label)] : initialLabels;
const allowedLabels = new Set([...stageInitialLabels, ...restartLabels]);
function checkedReport(report, stage) {
    boundedJson(report);
    assert.equal(report.version, 1, "ReportVersion");
    assert.equal(report.synthetic, true, "SyntheticReportRequired");
    assert.equal(
        report.passed,
        true,
        `Journeys:${stage}:${report.failedCheck ?? "unknown"}`,
    );
    assert.equal(report.nativeIpc, true, "ActualNativeIpcRequired");
    assert.equal(
        report.modelExecution,
        nativeMode && stage === "initial",
        "ModelExecutionBoundary",
    );
    assert.equal(report.rendering, "native-webview2", "ReportNativeRendering");
    assert.equal(report.stage, stage, "ReportStage");
    if (stage === "denied") {
        assert(
            Array.isArray(report.checks) &&
                report.checks.length >= 10 &&
                report.checks.length <= 32,
            "DeniedGrantBoundedChecks",
        );
        for (const required of [
            "native-port-denied-actual-native-context-grant-false",
            "native-port-lab_denied-actual-lab-grant-required",
            "native-port-lab-denied-cleanup_status-actual-empty-cleanup-without-lab",
            "native-port-lab-denied-retry_cleanup-actual-empty-cleanup-without-lab",
            "native-port-lab_denied-query-string-rejected-before-host",
            "native-port-lab_denied-renderer-provider-key-rejected-before-host",
            "native-port-lab_denied-renderer-consent-key-rejected-before-host",
            "native-port-denied-no-unexpected-errors",
            "native-port-denied-disposed-without-error",
        ])
            assert(
                report.checks.includes(required),
                `RequiredDeniedGrantCheck:${required}`,
            );
        assert.deepEqual(report.captureLabels, [], "DeniedGrantNoCaptures");
        assert.deepEqual(report.errors, [], "DeniedGrantNoUnexpectedErrors");
        return;
    }
    assert(
        Array.isArray(report.checks) &&
            report.checks.length >=
                (nativeMode
                    ? stage === "initial"
                        ? 40
                        : 15
                    : stage === "initial"
                      ? 100
                      : 40) &&
            report.checks.length <= 8192,
        "ReportChecks",
    );
    assert(
        report.checks.every(
            (check) =>
                typeof check === "string" &&
                check.length > 0 &&
                check.length <= 512,
        ),
        "CheckLabels",
    );
    for (const required of nativeMode
        ? [
              "native-full-explicit-cleanup-observed",
              ...(stage === "initial"
                  ? [
                        sceneMode ? "native-scene-actual-paired-partial" : "native-full-actual-paired-partial",
                        sceneMode ? "native-scene-actual-completed-proof" : "native-full-actual-completed-proof",
                    ]
                  : ["native-full-cold-completed-open"]),
          ]
        : [
              "native-port-empty_native-catalog-native-version-tags",
              "native-port-empty_native-catalog-has-no-native-execution",
              "native-port-empty_native-unknown-client-lookup",
              "native-port-empty_native-unknown-run-open",
              "native-port-empty_native-unknown-token-status",
              "native-port-empty_native-unknown-token-close",
              "native-port-empty_native-unknown-managed-before-read-consent",
              "native-port-scripted_open-scripted-client-is-not-native",
              "native-port-scripted_open-scripted-token-is-not-native",
              "native-port-scripted_open-native-close-cannot-revoke-scripted-token",
              "native-port-scripted-status-preserved-run_token",
              "native-port-scripted-status-preserved-report_ready",
              "native-port-scripted_open-catalog-has-no-native-execution",
          ]) {
        assert(
            report.checks.includes(required),
            `RequiredNativePortCheck:${required}`,
        );
    }
    if (nativeMode) {
        assert.deepEqual(
            report.doubles,
            sceneMode ? ["execution-consent", "read-consent", "lost-start-ack"] : [
                "execution-consent",
                "read-consent",
                "model-picker",
                "lost-start-ack",
            ],
            "NativeDoublesExplicit",
        );
    }
    assert(
        Array.isArray(report.captureLabels) &&
            report.captureLabels.length <= limits.captures,
        "CaptureLabelBudget",
    );
    assert.equal(
        new Set(report.captureLabels).size,
        report.captureLabels.length,
        "DuplicateCaptureLabel",
    );
    assert(
        report.captureLabels.every((label) => allowedLabels.has(label)),
        "ClosedCaptureLabel",
    );
    assert.deepEqual(
        [...report.captureLabels].sort(),
        [...(stage === "initial" ? stageInitialLabels : restartLabels)].sort(),
        "RequiredStageCaptures",
    );
    assert(
        Array.isArray(report.savedRuns) &&
            report.savedRuns.length <= 32 &&
            report.savedRuns.every(guid),
        "SavedRunIds",
    );
    assert(
        report.reopenedRun === null || guid(report.reopenedRun),
        "ReopenedRunId",
    );
    assert(
        Array.isArray(report.inventoryProofs) &&
            report.inventoryProofs.length <= 32,
        "InventoryProofs",
    );
    assert.deepEqual(
        report.inventoryProofs.map((proof) => proof.name).sort(),
        (stage === "initial"
            ? [
                  "completed-resume-entire-output-byte-read-only",
                  "actual-inspection-does-not-change-durable-comparison",
              ]
            : ["cold-open-read-close-no-execution-or-file-mutation"]
        ).sort(),
        "RequiredStageInventoryProofs",
    );
    for (const proof of report.inventoryProofs) {
        assert(
            typeof proof.name === "string" &&
                proof.name.length > 0 &&
                proof.name.length <= 128,
            "InventoryProofName",
        );
        assert(
            hash(proof.before) &&
                hash(proof.after) &&
                proof.before === proof.after &&
                proof.unchanged === true,
            "UnchangedInventoryProof",
        );
        assert(
            safe(proof.file_count) &&
                proof.file_count <= limits.inventoryEntries,
            "InventoryProofCount",
        );
    }
    if (sceneMode) checkedSceneReport(report, stage);
    assert(
        hash(report.finalInventoryDigest) && safe(report.finalInventoryCount),
        "FinalInventoryProof",
    );
    assert(
        Array.isArray(report.errors) && report.errors.length <= 128,
        "BoundedErrorRecords",
    );
    assert(
        report.errors.every(
            (error) =>
                error && typeof error === "object" && !Array.isArray(error),
        ),
        "ErrorRecords",
    );
    assert(
        Array.isArray(report.unavailable) &&
            report.unavailable.length <= 64 &&
            report.unavailable.every(
                (item) => typeof item === "string" && item.length <= 512,
            ),
        "UnavailableLabels",
    );
}
function checkedSceneReport(report, stage) {
    assert.equal(report.protocolVersion, 4, "ActualSceneProtocolRequired");
    assert.equal(report.originalHumanAssessment, "needs improvement", "PriorHumanAssessmentPreserved");
    assert.equal(report.human_rubric, "not_reviewed", "SceneHumanRubricUnreviewed");
    assert.equal(report.quality_accepted, false, "SceneNoHumanQualityAcceptance");
    const required = stage === "initial" ? [
        "native-scene-existing-approved-publication-retained-unloaded-without-import",
        "native-scene-consent-cancel-deny-retirement-never-reserved-a-model",
        "native-scene-completed-resume-no-consent-or-reservation",
        "native-scene-eight-frozen-review-slots-no-substitution",
    ] : ["native-scene-cold-open-read-completed-resume-no-consent-or-reservation"];
    for (const name of required) assert(report.checks.includes(name), `RequiredSceneCheck:${name}`);
    assert(Array.isArray(report.reviewSlots), "ClosedSceneReviewSlots");
    assert.deepEqual(report.reviewSlots.map(({ turn, arm, label }) => ({ turn, arm, label })),
        stage === "initial" ? sceneReviewSlots : [], "FrozenSceneSlotsWithoutSubstitution");
    for (const slot of report.reviewSlots) {
        assert.equal(slot.original_human_assessment, "needs improvement");
        assert.equal(slot.human_rubric, "not_reviewed"); assert.equal(slot.quality_accepted, false);
        assert(typeof slot.phase === "string" && typeof slot.passed === "boolean", "ActualSlotPhase");
        for (const field of ["receipt_available", "capture_available", "recording_available"]) assert.equal(typeof slot[field], "boolean");
        for (const field of ["receipt_evidence_sha256", "capture_evidence_sha256", "outputs_evidence_sha256"]) assert(hash(slot[field]), "ActualSlotEvidenceHash");
        assert(slot.source && typeof slot.source === "object" && hash(slot.input_semantic_sha256), "ActualSlotSource");
        assert(["validated_committed_scene_narrator_v1", "not_applicable_guard", "not_applicable_dependency", "unavailable"].includes(slot.construction_evidence_status));
        assert(["checked_finite_sentinels", "not_applicable_guard", "unavailable"].includes(slot.privacy_evidence_status));
        if (slot.construction_evidence_status === "validated_committed_scene_narrator_v1") {
            assert.equal(slot.phase, "committed");
            for (const field of ["narrator_prompt_sha256", "narrator_schema_sha256", "scene_frame_sha256"]) assert(hash(slot[field]));
        }
    }
    assert(Array.isArray(report.observationProofs) && report.observationProofs.length === 1, "OneClosedSceneObservationProof");
    const proof = report.observationProofs[0];
    assert.equal(proof.name, stage === "initial" ? "native-scene-completed-resume-no-consent-or-reservation"
        : "native-scene-cold-open-read-completed-resume-no-consent-or-reservation");
    assert.equal(proof.unchanged, true); assert.deepEqual(proof.before, proof.after);
    for (const value of [proof.before, proof.after]) {
        assert.deepEqual(Object.keys(value).sort(), ["consent_calls", "kind", "owner_present", "protocol_version", "reservation_sequence", "retained_evaluations", "version"]);
        assert.equal(value.version, 1); assert.equal(value.kind, "native_scene_execution_observation"); assert.equal(value.protocol_version, 4);
        assert(safe(value.reservation_sequence) && safe(value.consent_calls));
        assert.equal(value.owner_present, false); assert.equal(value.retained_evaluations, 0);
        if (stage === "restart") { assert.equal(value.reservation_sequence, 0); assert.equal(value.consent_calls, 0); }
    }
    assert(Array.isArray(report.outcomeSummaries) && report.outcomeSummaries.length === (stage === "initial" ? 2 : 1), "ActualSceneOutcomeSummaries");
    for (const [index, value] of report.outcomeSummaries.entries()) {
        const completed = stage === "restart" || index === 1;
        assert.equal(value.protocol_version, 4); assert.equal(value.completed, completed);
        assert.equal(value.rows, completed ? 48 : 12); assert.equal(value.completed_scenes, completed ? 4 : 1);
        assert(safe(value.roles_known_sum) && safe(value.unknown_role_rows) && safe(value.physical_setups) && value.physical_setups > 0);
        assert(value.native_load !== null && value.profile && typeof value.profile === "object", "ActualCoreNativeEvidence");
        assert(safe(value.source_bound_committed_rows) && value.source_bound_committed_rows <= value.rows);
        assert.equal(value.human_reviewed, 0); assert.equal(value.human_rubric, "not_reviewed"); assert.equal(value.quality_accepted, false);
        for (const counts of [value.phases, value.construction_statuses, value.privacy_statuses])
            assert(counts && typeof counts === "object" && Object.values(counts).every(safe) && Object.values(counts).reduce((sum, count) => sum + count, 0) === value.rows, "ActualRowStatusCounts");
    }
}
async function captures(directory, report) {
    const entries = await readdir(directory);
    const actual = entries
        .filter((name) => name.endsWith(".png"))
        .map((name) => name.slice(0, -4));
    assert(actual.length <= limits.captures, "CaptureCountBudget");
    assert.deepEqual(
        actual.sort(),
        [...report.captureLabels].sort(),
        "ActualDeclaredPngLabels",
    );
    const records = [];
    for (const label of report.captureLabels) {
        const png = await boundedFile(
            path.join(directory, `${label}.png`),
            limits.pngBytes,
        );
        assert(
            png.length >= 8 &&
                png
                    .subarray(0, 8)
                    .equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])),
            "ActualPngSignature",
        );
        const metadata = await json(
            path.join(directory, `${label}.capture.json`),
        );
        const snapshot = await json(path.join(directory, `${label}.json`));
        boundedJson(snapshot);
        assert.equal(
            metadata.rendering,
            "native-webview2",
            "CaptureNativeRendering",
        );
        assert.equal(metadata.synthetic, true, "CaptureSynthetic");
        assert.equal(metadata.label, label, "CaptureLabel");
        assert.equal(snapshot.semanticVersion, 2, "SemanticVersion");
        assert.equal(snapshot.synthetic, true, "SyntheticSnapshot");
        assert(
            snapshot.comparisonRun &&
                typeof snapshot.comparisonRun === "object" &&
                !Array.isArray(snapshot.comparisonRun),
            "ActualComparisonControllerState",
        );
        assert(
            snapshot.semantic &&
                typeof snapshot.semantic === "object" &&
                !Array.isArray(snapshot.semantic),
            "BoundedAppOwnedDomStructure",
        );
        assert(safe(snapshot.uiRevision), "UiRevision");
        assert.equal(
            metadata.uiRevision,
            snapshot.uiRevision,
            "CaptureRevisionBinding",
        );
        for (const key of [
            "selectedStory",
            "observer",
            "revision",
            "pendingOperation",
            "displayedReceipt",
            "visibleError",
        ])
            assert(
                Object.hasOwn(snapshot, key),
                `CoherentSnapshotField:${key}`,
            );
        observer(snapshot.observer);
        assert(
            snapshot.revision === null || safe(snapshot.revision),
            "InspectionRevision",
        );
        assert(
            snapshot.selectedStory === null ||
                (typeof snapshot.selectedStory === "object" &&
                    !Array.isArray(snapshot.selectedStory)),
            "SelectedStory",
        );
        assert(
            snapshot.pendingOperation === null ||
                (typeof snapshot.pendingOperation === "object" &&
                    !Array.isArray(snapshot.pendingOperation)),
            "PendingOperation",
        );
        assert(
            snapshot.visibleError === null ||
                typeof snapshot.visibleError === "string",
            "VisibleError",
        );
        if (sceneMode && label.startsWith("full-scene-")) {
            const expected = report.reviewSlots.find((slot) => slot.label === label), retained = snapshot.sceneReview;
            assert(expected && retained, "ActualFrozenSlotCheckpoint");
            for (const [key, value] of Object.entries(expected)) assert.deepEqual(retained[key], value, `SceneCheckpoint:${key}`);
            const selected = snapshot.comparisonReader.selected;
            assert(selected?.turn === expected.turn && selected?.arm === expected.arm, "ActualSelectedFrozenRow");
            assert.equal(snapshot.comparisonReader.observer.kind, "omniscient", "PrivateSlotInspectionLens");
            assert.equal(digest(JSON.stringify(retained.receiptEvidence)), expected.receipt_evidence_sha256);
            assert.equal(digest(JSON.stringify(retained.outputsEvidence)), expected.outputs_evidence_sha256);
            assert.deepEqual(snapshot.comparisonReader.evidence, retained.outputsEvidence, "ActualDisplayedSlotEvidence");
        }
        records.push({
            label,
            pngBytes: png.length,
            pngSha256: digest(png),
            snapshotSha256: digest(
                await boundedFile(
                    path.join(directory, `${label}.json`),
                    limits.jsonBytes,
                ),
            ),
        });
    }
    return records;
}

async function inventory(directory) {
    const files = [],
        budget = { entries: 0, bytes: 0 };
    const ordinary = async (file) => {
        const stat = await lstat(file);
        // Node checks junction/symlink redirects. It does not independently
        // inspect every Windows reparse attribute; the native fixture inventory
        // separately pins paths, and its digest is compared after app exit.
        assert(!stat.isSymbolicLink(), "InventoryLink");
        assert.equal(
            path.resolve(await realpath(file)).toLowerCase(),
            path.resolve(file).toLowerCase(),
            "InventoryRedirectedPath",
        );
        return stat;
    };
    async function visit(current, depth) {
        assert(
            depth <= limits.inventoryDepth &&
                ++budget.entries <= limits.inventoryEntries,
            "InventoryStructureBudget",
        );
        const stat = await ordinary(current);
        if (stat.isDirectory()) {
            for (const name of (await readdir(current)).sort())
                await visit(path.join(current, name), depth + 1);
        } else {
            assert(
                stat.isFile() && stat.size <= limits.inventoryFileBytes,
                "InventoryFileBudget",
            );
            budget.bytes += stat.size;
            assert(
                budget.bytes <= limits.inventoryTotalBytes,
                "InventoryTotalBudget",
            );
            const bytes = await boundedFile(current, limits.inventoryFileBytes);
            assert.equal(bytes.length, stat.size, "InventoryChangedDuringRead");
            files.push([
                path.relative(directory, current).split(path.sep).join("/"),
                digest(bytes),
            ]);
        }
    }
    await visit(directory, 0);
    files.sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
    const map = Object.fromEntries(files);
    return {
        digest: digest(JSON.stringify(map)),
        file_count: files.length,
        bytes: budget.bytes,
        files: map,
    };
}

let failure = null;
try {
    if (sceneMode) {
        sceneSourceHashes = await sceneHashes(sceneInputFiles);
        await writeFile(path.join(folder, "source-manifest.json"), JSON.stringify({ version: 1, protocolVersion: 4,
            sourceRevision: revision, sourceHashes: sceneSourceHashes, node: process.version,
            platform: process.platform, arch: process.arch, temp: process.env.TEMP, tmp: process.env.TMP }, null, 2), { flag: "wx" });
    }
    if (nativeMode) {
        nativeAssets = await approvedNativeAssets();
        await run(
            "stage-approved-worker",
            process.execPath,
            ["stage-runtime.mjs"],
            {
                LOCALLORE_D04_WORKER_SOURCE: nativeAssets.worker,
                LOCALLORE_D04_TARGET_DIR: target,
            },
        );
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
        900000,
    );
    executableSha256 = digest(await readFile(executable));
    if (sceneMode) {
        sceneHarnessProducts = await sceneProducts();
        await writeFile(path.join(folder, "product-manifest.json"), JSON.stringify({ sourceRevision: revision,
            harnessProducts: sceneHarnessProducts }, null, 2), { flag: "wx" });
    }
    for (const stage of nativeMode
        ? ["initial", "restart"]
        : ["denied", "initial", "restart"]) {
        const directory = path.join(folder, stage);
        await run(
            `app-${stage}`,
            executable,
            [],
            {
                LOCALLORE_D02_HARNESS: "1",
                LOCALLORE_D07_FULL_COMPARISON_HARNESS: "1",
                LOCALLORE_D07_NATIVE_FULL_HARNESS: nativeMode ? "1" : "0",
                ...(sceneMode ? {
                    LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS: "1",
                    LOCALLORE_D04_HARNESS: "0", LOCALLORE_D04_MODEL_ROOT: nativeAssets.reuseRoot,
                } : nativeMode
                    ? { LOCALLORE_D07_NATIVE_MODEL_SOURCE: nativeAssets.model }
                    : {}),
                LOCALLORE_D07_NATIVE_DENIED_GRANT:
                    stage === "denied" ? "1" : "0",
                LOCALLORE_TEST_MEMORY: "1",
                LOCALLORE_TEST_STORAGE_FAILURE: "0",
                LOCALLORE_TEST_WORKSPACE: path.join(
                    stage === "denied"
                        ? path.join(folder, "denied-workspace")
                        : folder,
                    "stories-v1.sqlite",
                ),
                LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
                LOCALLORE_D02_ARTIFACT_DIR: directory,
                WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:
                    "--disable-background-timer-throttling",
            },
            limits.launcherWatchdogMs,
        );
        const report = await json(path.join(directory, "report.json"));
        reports.push({ stage, report });
        checkedReport(report, stage);
        if (stage === "denied") {
            assert.deepEqual(
                (await readdir(directory)).sort(),
                ["report.json"],
                "DeniedGrantOnlyBoundedReport",
            );
            await sourceUnchanged();
            continue;
        }
        const images = await captures(directory, report);
        const actual = await inventory(
            path.join(folder, "comparison-evaluations"),
        );
        assert.equal(
            actual.digest,
            report.finalInventoryDigest,
            "IndependentCoreInventoryDigest",
        );
        assert.equal(
            actual.file_count,
            report.finalInventoryCount,
            "IndependentCoreInventoryCount",
        );
        if (expectedInventory) {
            assert.deepEqual(
                actual.files,
                expectedInventory,
                "RestartPreservesAllCoreBytes",
            );
            const initialReport = reports.find(
                (entry) => entry.stage === "initial",
            )?.report;
            assert(
                Array.isArray(initialReport?.savedRuns) &&
                    initialReport.savedRuns.includes(report.reopenedRun),
                "RestartReopensInitialSavedRun",
            );
        }
        expectedInventory = actual.files;
        inventories.push({
            stage,
            digest: actual.digest,
            file_count: actual.file_count,
            bytes: actual.bytes,
            captures: images,
        });
        assert.equal(
            digest(await readFile(executable)),
            executableSha256,
            "ExecutableChanged",
        );
        await sourceUnchanged();
    }
} catch (error) {
    failure = {
        name: error?.name ?? "Error",
        message: String(error?.message ?? error).slice(0, 2048),
    };
} finally {
    if (sceneMode) {
        if (sceneOwnedDrainUnknown) {
            sceneRestoration = { passed: false, skipped: true, launched: false,
                reason: "SceneOwnedDrainUnknown", unknownChildren: sceneUnknownChildren };
        } else {
            try {
                await run("normal-frontend-restoration", process.execPath, ["build.mjs"]);
                await run("normal-native-restoration", "cargo", ["build", "--manifest-path", "src-tauri/Cargo.toml",
                    "--locked", "--offline", "--no-default-features", "--bin", "locallore-desktop-spike", "--jobs", "1", "--target-dir", target], {}, 900000);
                sceneRestoration = { passed: true, launched: false, products: await sceneProducts() };
            } catch (error) {
                sceneRestoration = { passed: false, launched: false, ownedDrainUnknown: sceneOwnedDrainUnknown,
                    unknownChildren: sceneUnknownChildren, error: String(error?.message ?? error).slice(0, 2048) };
                failure ??= { name: error?.name ?? "Error", message: String(error?.message ?? error).slice(0, 2048) };
            }
        }
        if (!sceneRestoration.passed) failure ??= { name: "Error", message: "SceneNormalRestorationUnqualified" };
        await writeFile(path.join(folder, "normal-restoration.json"), JSON.stringify(sceneRestoration, null, 2), { flag: "wx" });
    }
    let sourceClean = false,
        terminalSourceUnchanged = false;
    if (!sceneMode || !sceneOwnedDrainUnknown) {
        try {
            sourceClean = (await git("status", "--porcelain")) === "";
            terminalSourceUnchanged = (await git("rev-parse", "HEAD")) === revision;
        } catch {}
    }
    if (!sourceClean || !terminalSourceUnchanged)
        failure ??= { name: "Error", message: "TerminalSourceChanged" };
    const qualification = {
        version: 1,
        passed: failure === null,
        synthetic: true,
        sourceRevision: revision,
        sourceClean,
        terminalSourceUnchanged,
        executableSha256,
        launcherSha256,
        ...(sceneMode ? { protocolVersion: 4, reuseModelRoot: nativeAssets?.reuseRoot ?? null,
            weightsCopied: false, importedByHarness: false, sourceHashes: sceneSourceHashes,
            harnessProducts: sceneHarnessProducts, restoration: sceneRestoration,
            ownedDrainUnknown: sceneOwnedDrainUnknown, unknownChildren: sceneUnknownChildren,
            terminalSourceInspectionSkipped: sceneOwnedDrainUnknown,
            processTreeContained: false, reviewSlots: sceneReviewSlots, originalHumanAssessment: "needs improvement",
            human_rubric: "not_reviewed", quality_accepted: false } : {}),
        requestedNativeIpc: true,
        nativeIpc: inventories.length > 0,
        modelExecution: reports.some(
            ({ report }) => report.modelExecution === true,
        ),
        requestedInputLane: nativeMode
            ? "approved_native"
            : "scripted_baseline",
        approvedInstalledAssets: nativeAssets?.verified ?? null,
        rendering:
            inventories.length > 0 ? "actual-hidden-unfocused-webview2" : null,
        desktopInput: false,
        nativeDialogsAutomated: false,
        executions,
        reports,
        inventories,
        limits,
        failure,
        limitations: [
            nativeMode
                ? "Actual installed-model evidence is recorded only after verified generated report outputs; no human quality acceptance"
                : "Fixed scripted fake inference only; no approved-model execution",
            "Fixed native consent doubles; no OS dialog automation or desktop control",
            "Node checks junction/symlink redirects, not all Windows reparse attributes or universal link races",
            "Images require separate individual visual inspection",
            "No human quality, whole-app performance, leak, phone parity or release qualification",
            ...(sceneMode ? ["Counter equality supports completed resume; it does not independently count SDK loads",
                "One direct-child kill and five-second grace; no Job/process-tree containment or timeout-drain qualification",
                "Scene rows, rejections and missing frozen slots are retained; completion does not imply every row passed"] : []),
        ],
    };
    await writeFile(
        path.join(folder, "qualification.json"),
        JSON.stringify(qualification, null, 2),
        { flag: "wx" },
    );
    console.log(
        JSON.stringify({
            passed: failure === null,
            artifactDirectory: folder,
            sourceRevision: revision,
            stages: reports.length,
            modelExecution: reports.some(
                ({ report }) => report.modelExecution === true,
            ),
        }),
    );
}
if (failure) throw Error(failure.message);
