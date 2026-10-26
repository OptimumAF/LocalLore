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
const nativeMode = process.argv.length === 3 && process.argv[2] === "--native";
assert(process.argv.length === 2 || nativeMode, "ClosedHarnessArguments");
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

async function approvedNativeAssets() {
    const model = process.env.LOCALLORE_D07_NATIVE_MODEL_SOURCE;
    const worker = process.env.LOCALLORE_D04_WORKER_SOURCE;
    const specs = [
        ["model", model, 639446688, "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"],
        ["worker", worker, null, "b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434"],
    ];
    const verified = {};
    for (const [kind, source, size, expected] of specs) {
        assert(source && path.isAbsolute(source), `${kind}:ExplicitInstalledAssetRequired`);
        const metadata = await lstat(source);
        assert(metadata.isFile() && !metadata.isSymbolicLink(), `${kind}:OrdinaryAssetRequired`);
        assert.equal(path.resolve(await realpath(source)).toLowerCase(), path.resolve(source).toLowerCase(), `${kind}:RedirectedAsset`);
        if (size !== null) assert.equal(metadata.size, size, `${kind}:ApprovedSize`);
        else assert(metadata.size > 0 && metadata.size <= 16 * 1024 * 1024, "WorkerSize");
        const hasher = createHash("sha256");
        for await (const bytes of createReadStream(source)) hasher.update(bytes);
        assert.equal(hasher.digest("hex"), expected, `${kind}:ApprovedHash`);
        verified[kind] = { bytes: metadata.size, sha256: expected };
    }
    return { model, worker, verified };
}

async function sourceUnchanged() {
    assert.equal(
        await git("rev-parse", "HEAD"),
        revision,
        "SourceRevisionChanged",
    );
    assert.equal(await git("status", "--porcelain"), "", "SourceTreeChanged");
}
async function saveExecutions() {
    await writeFile(
        path.join(folder, "executions.json"),
        JSON.stringify(executions, null, 2),
    );
}
async function run(label, command, args, env = {}, timeout = 240000) {
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
const allowedLabels = new Set([...initialLabels, ...restartLabels]);
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
    assert.equal(report.modelExecution, nativeMode && stage === "initial", "ModelExecutionBoundary");
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
            report.checks.length >= (nativeMode ? (stage === "initial" ? 40 : 15) : (stage === "initial" ? 100 : 40)) &&
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
    for (const required of (nativeMode ? [
        "native-full-explicit-cleanup-observed",
        ...(stage === "initial" ? ["native-full-actual-paired-partial", "native-full-actual-completed-proof"] : ["native-full-cold-completed-open"]),
    ] : [
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
    ])) {
        assert(
            report.checks.includes(required),
            `RequiredNativePortCheck:${required}`,
        );
    }
    if (nativeMode) {
        assert.deepEqual(report.doubles, ["execution-consent", "read-consent", "model-picker", "lost-start-ack"], "NativeDoublesExplicit");
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
        [...(stage === "initial" ? initialLabels : restartLabels)].sort(),
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
    if (nativeMode) {
        nativeAssets = await approvedNativeAssets();
        await run("stage-approved-worker", process.execPath, ["stage-runtime.mjs"], {
            LOCALLORE_D04_WORKER_SOURCE: nativeAssets.worker,
            LOCALLORE_D04_TARGET_DIR: target,
        });
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
    for (const stage of (nativeMode ? ["initial", "restart"] : ["denied", "initial", "restart"])) {
        const directory = path.join(folder, stage);
        await run(
            `app-${stage}`,
            executable,
            [],
            {
                LOCALLORE_D02_HARNESS: "1",
                LOCALLORE_D07_FULL_COMPARISON_HARNESS: "1",
                LOCALLORE_D07_NATIVE_FULL_HARNESS: nativeMode ? "1" : "0",
                ...(nativeMode ? { LOCALLORE_D07_NATIVE_MODEL_SOURCE: nativeAssets.model } : {}),
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
    let sourceClean = false,
        terminalSourceUnchanged = false;
    try {
        sourceClean = (await git("status", "--porcelain")) === "";
        terminalSourceUnchanged = (await git("rev-parse", "HEAD")) === revision;
    } catch {}
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
        requestedNativeIpc: true,
        nativeIpc: inventories.length > 0,
        modelExecution: reports.some(({report}) => report.modelExecution === true),
        requestedInputLane: nativeMode ? "approved_native" : "scripted_baseline",
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
            nativeMode ? "Actual installed-model evidence is recorded only after verified generated report outputs; no human quality acceptance" : "Fixed scripted fake inference only; no approved-model execution",
            "Fixed native consent doubles; no OS dialog automation or desktop control",
            "Node checks junction/symlink redirects, not all Windows reparse attributes or universal link races",
            "Images require separate individual visual inspection",
            "No human quality, whole-app performance, leak, phone parity or release qualification",
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
            modelExecution: reports.some(({report}) => report.modelExecution === true),
        }),
    );
}
if (failure) throw Error(failure.message);
