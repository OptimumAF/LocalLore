// Independent FIRST source freeze: UNCOMPILED / UNFORMATTED / UNRUN.
// Fixed synthetic application-owned WebView2 cohort; never desktop automation.
import { spawn } from "node:child_process";
import {
    mkdir,
    readFile,
    writeFile,
    readdir,
    lstat,
    realpath,
    statfs,
} from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash, randomUUID } from "node:crypto";

if (process.argv.length !== 2)
    throw Error("ClosedLiveNarrationArgumentsRequired");
process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
const root = fileURLToPath(new URL(".", import.meta.url));
const limits = Object.freeze({
    targetGrowth: 2 * 1024 ** 3,
    artifacts: 256 * 1024 ** 2,
    sourceGrowth: 128 * 1024 ** 2,
    sourceFreeze: 1024 ** 2,
    entries: 2_000_000,
});
async function ownedDirectory(value) {
    if (!value || !path.isAbsolute(value))
        throw Error("ExistingOwnedDirectoryRequired");
    const resolved = path.resolve(value);
    if (
        path.parse(resolved).root.toLowerCase() !== "d:\\" ||
        (await realpath(resolved)).toLowerCase() !== resolved.toLowerCase()
    )
        throw Error("PhysicalDRequired");
    for (let current = resolved; ; current = path.dirname(current)) {
        const info = await lstat(current);
        if (!info.isDirectory() || info.isSymbolicLink())
            throw Error("OrdinaryOwnedDirectoryRequired");
        if (path.dirname(current) === current) break;
    }
    return resolved;
}
await ownedDirectory(root);
await ownedDirectory(process.env.TEMP);
const base = await ownedDirectory(process.env.LOCALLORE_D06_LIVE_ARTIFACT_ROOT);
const target = await ownedDirectory(process.env.LOCALLORE_D06_LIVE_TARGET_DIR);
const cargoHome = await ownedDirectory(process.env.CARGO_HOME);
if ((process.env.LIBSQLITE3_FLAGS ?? "").trim())
    throw Error("OrdinaryUncappedSQLiteRequired");
const disjoint = (left, right) => {
    const contains = (a, b) => {
        const relative = path.relative(a.toLowerCase(), b.toLowerCase());
        return (
            relative === "" ||
            (!path.isAbsolute(relative) &&
                relative !== ".." &&
                !relative.startsWith(`..${path.sep}`))
        );
    };
    return !contains(left, right) && !contains(right, left);
};
const folder = path.join(base, `d06-live-narration-native-${randomUUID()}`);
for (const location of [root, target, cargoHome])
    if (!disjoint(folder, location)) throw Error("DisjointPacketRequired");
if (
    !disjoint(root, target) ||
    !disjoint(root, cargoHome) ||
    !disjoint(target, cargoHome)
)
    throw Error("SeparateExistingBuildRootsRequired");
const executable = path.join(target, "debug", "locallore-desktop-spike.exe");
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
let ownedDrainUnknown = false;
const unknownChildren = [],
    gitChildren = [];
// live-git-policy-v1:start
function latchUnknown(reason, details) {
    ownedDrainUnknown = true;
    if (unknownChildren.length < 64)
        unknownChildren.push({
            reason,
            ...details,
            processTreeContained: false,
        });
}
async function gitRead(args) {
    if (ownedDrainUnknown) throw Error("OwnedDrainUnknownBeforeGit");
    if (gitChildren.length >= 128) throw Error("GitProcessRecordBudget");
    const started = new Date().toISOString(),
        buffers = { stdout: Buffer.alloc(0), stderr: Buffer.alloc(0) };
    let pid = null,
        timedOut = false,
        truncated = false,
        overflowLatched = false,
        killAttempted = false,
        killReturned = null,
        killError = null;
    const result = await new Promise((resolve) => {
        let child;
        try {
            child = spawn("git", args, {
                cwd: root,
                shell: false,
                windowsHide: true,
                stdio: ["ignore", "pipe", "pipe"],
                env: {
                    ...process.env,
                    TEMP: "D:/Dev/_Temp",
                    TMP: "D:/Dev/_Temp",
                },
            });
        } catch (error) {
            resolve({
                code: null,
                signal: null,
                error: error?.code ?? "GitSpawnFailure",
                closed: false,
                noChildCreated: true,
            });
            return;
        }
        pid = child.pid ?? null;
        let settled = false,
            grace = null;
        const finish = (value, detach = false) => {
            if (settled) return;
            settled = true;
            clearTimeout(timer);
            if (grace) clearTimeout(grace);
            if (detach) {
                child.stdout.destroy();
                child.stderr.destroy();
                child.unref();
            }
            resolve(value);
        };
        for (const channel of ["stdout", "stderr"])
            child[channel].on("error", () => {
                if (settled) return;
                latchUnknown("GitPipeError", { pid, args, channel });
                // Keep the pipe failure as the primary observation even if a
                // best-effort stop synchronously emits close. No drain is claimed.
                finish(
                    {
                        code: null,
                        signal: null,
                        error: "GitPipeError",
                        closed: false,
                    },
                    true,
                );
                if (!killAttempted) {
                    killAttempted = true;
                    try {
                        killReturned = child.kill();
                    } catch (error) {
                        killError = error?.code ?? "KillFailure";
                    }
                }
            });
        for (const channel of ["stdout", "stderr"])
            child[channel].on("data", (chunk) => {
                const left = 262144 - buffers[channel].length;
                if (chunk.length > left) {
                    truncated = true;
                    if (!overflowLatched) {
                        overflowLatched = true;
                        latchUnknown("GitOutputOverflow", { pid, args });
                    }
                }
                if (left > 0)
                    buffers[channel] = Buffer.concat([
                        buffers[channel],
                        chunk.subarray(0, left),
                    ]);
            });
        const timer = setTimeout(() => {
            timedOut = true;
            latchUnknown("GitTimeoutDirectChildOnly", { pid, args });
            grace = setTimeout(
                () =>
                    finish(
                        {
                            code: null,
                            signal: null,
                            error: "OwnedDrainUnknown",
                            closed: false,
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
        }, 15000);
        child.once("error", (error) => {
            if (settled) return;
            if (pid !== null)
                latchUnknown("GitChildErrorWithPid", { pid, args });
            finish(
                {
                    code: null,
                    signal: null,
                    error: error?.code ?? "GitSpawnFailure",
                    closed: false,
                    noChildCreated: pid === null,
                },
                pid !== null,
            );
        });
        child.once("close", (code, signal) =>
            finish({ code, signal, error: null, closed: true }),
        );
    });
    const record = {
        ...result,
        started,
        ended: new Date().toISOString(),
        command: "git",
        args,
        pid,
        timedOut,
        truncated,
        killAttempted,
        killReturned,
        killError,
        ownedDrainUnknown,
        processTreeContained: false,
        stdoutBytes: buffers.stdout.length,
        stderrBytes: buffers.stderr.length,
        stdoutSHA256: digest(buffers.stdout),
        stderrSHA256: digest(buffers.stderr),
    };
    gitChildren.push(record);
    if (
        ownedDrainUnknown ||
        result.code !== 0 ||
        !result.closed ||
        timedOut ||
        truncated
    ) {
        // Before packet admission this bounded caller log is the only evidence;
        // never manufacture a clean packet after failed/uncertain admission.
        console.error(
            JSON.stringify({ kind: "live_git_admission_failure_v1", record }),
        );
        throw Error(
            ownedDrainUnknown ? "OwnedDrainUnknownAfterGit" : "GitReadFailed",
        );
    }
    return buffers.stdout.toString("utf8").trim();
}
// live-git-policy-v1:end
const revision = await gitRead(["rev-parse", "HEAD"]);
if (!/^[a-f0-9]{40}$/.test(revision))
    throw Error("ExactCommittedRevisionRequired");
if (await gitRead(["status", "--porcelain"]))
    throw Error("CleanCommittedLiveNarrationSourceRequired");
const sourceInputs = [
    "live-narration-harness.mjs",
    "ui/live-narration-native-journeys.ts",
    "ui/main.tsx",
    "ui/journeys.ts",
    "ui/controller.ts",
    "ui/trace-model.ts",
    "ui/narration-diagnostic-model.ts",
    "ui/TurnDebugger.tsx",
    "ui/App.tsx",
    "ui/model.ts",
    "ui/v2-play-controller.ts",
    "ui/v2-view-model.ts",
    "ui/V2PlayPanel.tsx",
    "ui/style.css",
    "build.mjs",
    "package.json",
    "package-lock.json",
    "src-tauri/src/main.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/src/scene_harness.rs",
    "src-tauri/src/models.rs",
    "src-tauri/src/lease.rs",
    "src-tauri/src/shutdown.rs",
    "src-tauri/Cargo.toml",
    "src-tauri/build.rs",
    "src-tauri/tauri.conf.json",
    "../../Cargo.lock",
    "../../fixtures/lantern_quay.json",
    "../../crates/locallore/src/host.rs",
    "../../crates/locallore/src/turn_trace.rs",
    "../../crates/locallore/src/engine.rs",
    "../../crates/locallore/src/engine/staged_scene_play.rs",
    "../../crates/locallore/src/play.rs",
    "../../crates/locallore/src/play/scene_narration.rs",
    "../../crates/locallore/src/play/scene_narration/renderer.rs",
    "../../crates/locallore-workspace/src/lib.rs",
    "../../crates/locallore-storage/src/lib.rs",
];
async function hashes(files) {
    const entries = await Promise.all(
        files.map(async (file) => {
            const full = path.isAbsolute(file) ? file : path.join(root, file);
            return [file, digest(await readFile(full))];
        }),
    );
    return Object.fromEntries(entries);
}
const sourceHashes = await hashes(sourceInputs);
const freezeBytes =
    (await readFile(path.join(root, sourceInputs[0]))).length +
    (await readFile(path.join(root, sourceInputs[1]))).length;
if (freezeBytes >= limits.sourceFreeze)
    throw Error("LiveNarrationSourceFreezeBudget");
async function footprint(directory, source = false) {
    let entries = 0,
        bytes = 0;
    const visit = async (current) => {
        for (const entry of await readdir(current, { withFileTypes: true })) {
            if (
                source &&
                [".git", "node_modules", "artifacts", "target"].includes(
                    entry.name,
                )
            )
                continue;
            if (++entries > limits.entries)
                throw Error("StorageInventoryEntryBudget");
            const full = path.join(current, entry.name),
                info = await lstat(full);
            if (info.isSymbolicLink())
                throw Error("StorageInventoryOrdinaryEntriesRequired");
            if (info.isDirectory()) await visit(full);
            else if (info.isFile()) {
                bytes += info.size;
                if (!Number.isSafeInteger(bytes))
                    throw Error("StorageInventorySize");
            } else throw Error("StorageInventoryOrdinaryEntriesRequired");
        }
    };
    await visit(directory);
    return { entries, bytes };
}
const disk = await statfs(root, { bigint: true });
const initialStorage = {
    target: await footprint(target),
    source: await footprint(root, true),
    freeDBytes: String(disk.bavail * disk.bsize),
};
if (
    BigInt(initialStorage.freeDBytes) <
    BigInt(limits.targetGrowth + limits.artifacts + limits.sourceGrowth)
)
    throw Error("DeclaredRunGrowthExceedsFreeD");
await mkdir(folder, { recursive: false }); // Create-new packet; never replace/delete a prior attempt.
const write = (name, value) => {
    const encoded = JSON.stringify(value, null, 2);
    if (Buffer.byteLength(encoded) > 262144)
        throw Error("LauncherMetadataBudget");
    return writeFile(path.join(folder, name), encoded, { flag: "wx" });
};
let storageBreached = false,
    lastStorage = null,
    runNumber = 0;
const processes = [],
    artifacts = {},
    reports = [];
async function measureStorage() {
    if (storageBreached) throw Error("StorageBudgetLatched");
    try {
        lastStorage = {
            target: await footprint(target),
            source: await footprint(root, true),
            packet: await footprint(folder),
        };
    } catch (error) {
        // A failed observation cannot later become permission to build again.
        storageBreached = true;
        lastStorage = {
            unavailable: true,
            reason: "StorageInventoryFailure",
            lastKnown: lastStorage,
        };
        throw error;
    }
    lastStorage.targetGrowth = Math.max(
        0,
        lastStorage.target.bytes - initialStorage.target.bytes,
    );
    lastStorage.sourceGrowth = Math.max(
        0,
        lastStorage.source.bytes - initialStorage.source.bytes,
    );
    // Reserve 1 MiB for the final three bounded metadata files after this measurement.
    if (
        lastStorage.targetGrowth > limits.targetGrowth ||
        lastStorage.sourceGrowth > limits.sourceGrowth ||
        lastStorage.packet.bytes > limits.artifacts - 1024 ** 2
    )
        storageBreached = true;
    if (storageBreached) throw Error("LiveNarrationStorageBudgetExceeded");
    return lastStorage;
}
async function unchangedSource() {
    if (
        (await gitRead(["rev-parse", "HEAD"])) !== revision ||
        (await gitRead(["status", "--porcelain"])) ||
        JSON.stringify(await hashes(sourceInputs)) !==
            JSON.stringify(sourceHashes)
    )
        throw Error("LiveNarrationSourceChanged");
}
let productHashes = null;
async function unchangedProducts() {
    if (
        !productHashes ||
        JSON.stringify(await hashes(["dist/app.js", executable])) !==
            JSON.stringify(productHashes)
    )
        throw Error("LiveNarrationProductChanged");
}
Object.assign(process.env, {
    CARGO_HOME: cargoHome,
    CARGO_TARGET_DIR: target,
    CARGO_BUILD_JOBS: "1",
    CARGO_PROFILE_DEV_DEBUG: "0",
    CARGO_PROFILE_TEST_DEBUG: "0",
    CARGO_INCREMENTAL: "0",
});
// live-child-policy-v1:start
async function run(command, args, additions = {}) {
    if (ownedDrainUnknown || storageBreached)
        throw Error(
            ownedDrainUnknown ? "OwnedDrainUnknown" : "StorageBudgetLatched",
        );
    await unchangedSource();
    await measureStorage();
    if (command === executable) {
        if (args.length) throw Error("ClosedNativeArgumentsRequired");
        await unchangedProducts();
    }
    const inherited = Object.fromEntries(
        Object.entries(process.env).filter(
            ([key]) => !/^LOCALLORE_/i.test(key),
        ),
    );
    const sequence = ++runNumber,
        started = new Date().toISOString(),
        buffers = { stdout: Buffer.alloc(0), stderr: Buffer.alloc(0) };
    let timedOut = false,
        truncated = false,
        overflowLatched = false,
        pid = null,
        killAttempted = false,
        killReturned = null,
        killError = null;
    const result = await new Promise((resolve) => {
        let child;
        try {
            child = spawn(command, args, {
                cwd: root,
                shell: false,
                windowsHide: true,
                stdio: ["ignore", "pipe", "pipe"],
                env: {
                    ...inherited,
                    ...additions,
                    TEMP: "D:/Dev/_Temp",
                    TMP: "D:/Dev/_Temp",
                },
            });
        } catch (error) {
            resolve({
                code: null,
                signal: null,
                error: error?.code ?? "SpawnFailure",
                closed: false,
                noChildCreated: true,
            });
            return;
        }
        pid = child.pid ?? null;
        let settled = false,
            grace = null;
        const unknown = (reason) => latchUnknown(reason, { sequence, pid });
        const finish = (value, detach = false) => {
            if (settled) return;
            settled = true;
            clearTimeout(timer);
            if (grace) clearTimeout(grace);
            if (detach) {
                child.stdout.destroy();
                child.stderr.destroy();
                child.unref();
            }
            resolve(value);
        };
        for (const channel of ["stdout", "stderr"])
            child[channel].on("error", () => {
                if (settled) return;
                latchUnknown("ChildPipeError", { sequence, pid, channel });
                finish(
                    {
                        code: null,
                        signal: null,
                        error: "ChildPipeError",
                        closed: false,
                    },
                    true,
                );
                if (!killAttempted) {
                    killAttempted = true;
                    try {
                        killReturned = child.kill();
                    } catch (error) {
                        killError = error?.code ?? "KillFailure";
                    }
                }
            });
        for (const channel of ["stdout", "stderr"])
            child[channel].on("data", (chunk) => {
                const left = 262144 - buffers[channel].length;
                if (chunk.length > left) {
                    truncated = true;
                    if (!overflowLatched) {
                        overflowLatched = true;
                        unknown("ChildOutputOverflow");
                    }
                }
                if (left > 0)
                    buffers[channel] = Buffer.concat([
                        buffers[channel],
                        chunk.subarray(0, left),
                    ]);
            });
        const timer = setTimeout(
            () => {
                timedOut = true;
                unknown("TimeoutDirectChildOnly");
                grace = setTimeout(
                    () =>
                        finish(
                            {
                                code: null,
                                signal: null,
                                error: "OwnedDrainUnknown",
                                closed: false,
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
            },
            command === "cargo" ? 900000 : 240000,
        );
        child.once("error", (error) => {
            if (settled) return;
            if (pid !== null) unknown("ChildErrorWithPid");
            finish(
                {
                    code: null,
                    signal: null,
                    error: error.code ?? "SpawnFailure",
                    closed: false,
                },
                pid !== null,
            );
        });
        child.once("close", (code, signal) =>
            finish({ code, signal, error: null, closed: true }),
        );
    });
    for (const channel of ["stdout", "stderr"])
        await writeFile(
            path.join(folder, `run-${sequence}-${channel}.log`),
            buffers[channel],
            { flag: "wx" },
        );
    const record = {
        sequence,
        ...result,
        started,
        ended: new Date().toISOString(),
        timedOut,
        truncated,
        pid,
        killAttempted,
        killReturned,
        killError,
        ownedDrainUnknown,
        processTreeContained: false,
        command:
            command === executable
                ? "<owned-target>/debug/locallore-desktop-spike.exe"
                : command,
        args,
        revision,
    };
    processes.push(record);
    await write(`run-${sequence}-process.json`, record);
    if (ownedDrainUnknown) throw Error("OwnedDrainUnknown");
    await unchangedSource();
    if (command === executable) await unchangedProducts();
    await measureStorage();
    if (result.code !== 0 || !result.closed || timedOut || truncated)
        throw Error(`LiveNarrationChildFailure:${sequence}`);
}
// live-child-policy-v1:end
const labels = {
    initial: [
        "ready",
        "recorded",
        "pending",
        "local-cancel",
        "unavailable",
        "refused",
        "observer",
        "switched",
        "enlarged",
    ].map((s) => `d06-live-${s}`),
    restart: ["d06-live-restarted"],
};
await write("source-manifest.json", {
    version: 1,
    kind: "d06_live_narration_native_v1",
    revision,
    inputSHA256: sourceHashes,
    sourceDirty: false,
    freezeBytes,
    node: process.version,
    budgets: limits,
    initialStorage,
    synthetic: true,
    plannedNativeIpc: true,
    nativeIpc: false,
    rendering: "pending",
    desktopControl: false,
    realModelGeneration: false,
    gitChildren,
});
const buildArgs = (normal) => [
    "build",
    "--manifest-path",
    "src-tauri/Cargo.toml",
    "--locked",
    "--offline",
    ...(normal ? ["--no-default-features"] : ["--features", "dev-harness"]),
    "--bin",
    "locallore-desktop-spike",
    "--jobs",
    "1",
    "--target-dir",
    target,
];
let originalError = null,
    restoration = null,
    candidate = null,
    workspace = null;
try {
    await run(process.execPath, ["build.mjs", "--harness"]);
    await run("cargo", buildArgs(false));
    productHashes = await hashes(["dist/app.js", executable]);
    await write("product-manifest.json", {
        revision,
        productSHA256: productHashes,
    });
    workspace = path.join(folder, `scene-native-${randomUUID()}`);
    await mkdir(workspace);
    const database = path.join(workspace, "stories-v1.sqlite");
    let first = null;
    for (const stage of ["initial", "restart"]) {
        const directory = path.join(workspace, stage);
        await run(executable, [], {
            LOCALLORE_D02_HARNESS: "1",
            LOCALLORE_D04_SCENE_HARNESS: "literal",
            LOCALLORE_D06_LIVE_NARRATION_HARNESS: "1",
            LOCALLORE_TEST_MEMORY: "0",
            LOCALLORE_TEST_WORKSPACE: database,
            LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
            LOCALLORE_D02_ARTIFACT_DIR: directory,
        });
        const names = await readdir(directory),
            bytes = await readFile(path.join(directory, "report.json"));
        if (bytes.length > 262144) throw Error("LiveNarrationReportBudget");
        const report = JSON.parse(bytes.toString("utf8")),
            proof = report.finalOracle;
        if (
            report.version !== 1 ||
            report.kind !== "d06_live_narration_native_v1" ||
            report.synthetic !== true ||
            report.passed !== true ||
            report.stage !== stage ||
            report.sceneCase !== "literal" ||
            report.nativeIpc !== true ||
            report.rendering !== "native-webview2" ||
            report.desktopControl !== false ||
            report.realModelGeneration !== false ||
            !Array.isArray(report.checks) ||
            report.checks.some((s) => typeof s !== "string") ||
            !proof ||
            proof.case !== "literal" ||
            proof.new_commits !== 2 ||
            proof.head !== 3 ||
            proof.untouched_preserved !== true ||
            proof.other_preserved !== true ||
            proof.observer_isolated !== true ||
            proof.real_model !== false
        )
            throw Error("LiveNarrationActualJourneyFailed");
        if (stage === "initial") {
            if (proof.fixture_factories !== 2 || proof.fixture_polls !== 4)
                throw Error("LiveNarrationExplicitGenerationCount");
            first = proof;
            if (
                report.errors.length !== 1 ||
                report.errors[0].source !== "native" ||
                report.errors[0].category !== "Stale" ||
                report.rejectedNativeCalls.length !== 1 ||
                report.rejectedNativeCalls[0].op !==
                    "trace_narration_validation_read_v1" ||
                report.rejectedNativeCalls[0].category !== "Stale"
            )
                throw Error("LiveNarrationExpectedNativeRefusalRoster");
        } else if (
            proof.fixture_factories !== 0 ||
            proof.fixture_polls !== 0 ||
            proof.canonical_sha256 !== first.canonical_sha256 ||
            JSON.stringify(proof.observer_sha256) !==
                JSON.stringify(first.observer_sha256) ||
            report.errors.length ||
            report.rejectedNativeCalls.length
        )
            throw Error("LiveNarrationColdRestartMismatch");
        const allowed = new Set([
            "report.json",
            ...labels[stage].flatMap((label) => [
                `${label}.json`,
                `${label}.png`,
                `${label}.capture.json`,
            ]),
        ]);
        if (
            names.length !== allowed.size ||
            names.some((name) => !allowed.has(name))
        )
            throw Error("LiveNarrationClosedArtifactRoster");
        for (const name of allowed) {
            const content = await readFile(path.join(directory, name));
            if (content.length > (name.endsWith(".png") ? 16777216 : 262144))
                throw Error("LiveNarrationArtifactBudget");
            artifacts[`${stage}/${name}`] = {
                bytes: content.length,
                sha256: digest(content),
            };
            if (name.endsWith(".png")) {
                if (
                    !content
                        .subarray(0, 8)
                        .equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))
                )
                    throw Error("NativePngHeader");
            } else if (name.endsWith(".capture.json")) {
                const capture = JSON.parse(content);
                if (
                    capture.synthetic !== true ||
                    capture.rendering !== "native-webview2" ||
                    !labels[stage].includes(capture.label)
                )
                    throw Error("ActualNativeRenderingRequired");
            } else if (name !== "report.json") {
                const snapshot = JSON.parse(content);
                if (
                    snapshot.synthetic !== true ||
                    snapshot.kind !== "d06_live_narration_snapshot_v1" ||
                    !Number.isSafeInteger(snapshot.uiRevision) ||
                    snapshot.aggregate?.head !== snapshot.uiRevision ||
                    !snapshot.diagnostic ||
                    !snapshot.trace ||
                    !snapshot.oracle ||
                    !Array.isArray(snapshot.dom?.structure) ||
                    snapshot.dom.structure.length > 256 ||
                    typeof snapshot.dom.text !== "string" ||
                    snapshot.dom.text.length > 48000 ||
                    !Array.isArray(snapshot.dom.geometry) ||
                    snapshot.dom.geometry.length > 8
                )
                    throw Error("CoherentLiveNarrationSnapshotRequired");
            }
        }
        reports.push({
            stage,
            checks: report.checks.length,
            proof,
            path: path.relative(folder, directory),
        });
    }
    await unchangedSource();
    await unchangedProducts();
    await measureStorage();
    candidate = {
        version: 1,
        kind: "d06_live_narration_native_v1",
        synthetic: true,
        nativeIpc: true,
        rendering: "native-webview2",
        desktopControl: false,
        realModelGeneration: false,
        revision,
        actualProcessRestart: true,
        captures: 10,
        reports,
        artifacts,
        inputSHA256: sourceHashes,
        harnessProductSHA256: productHashes,
        limitations: [
            "Fixed scripted literal scene provider; no real-model quality",
            "Actor denial is local UI admission, not native grant proof",
            "Native rejected narration tuples remain unqualified",
            "Direct-child closure only; no Job/process-tree containment",
            "Images require individual Root review; signatures and geometry are not visual acceptance",
            "Ordinary model status/shutdown may inspect the absent task-owned model candidate; no independent SDK-load counter",
            "No offline-qualifier/SDK/device/targeted OS boundary probes",
        ],
    };
} catch (error) {
    originalError = error;
} finally {
    if (ownedDrainUnknown || storageBreached)
        restoration = {
            passed: false,
            launched: false,
            skipped: true,
            reason: ownedDrainUnknown
                ? "OwnedDrainUnknown"
                : "StorageBudgetLatched",
            unknownChildren,
            processTreeContained: false,
        };
    else
        try {
            await run(process.execPath, ["build.mjs"]);
            await run("cargo", buildArgs(true));
            restoration = {
                passed: true,
                launched: false,
                productSHA256: await hashes(["dist/app.js", executable]),
            };
        } catch (error) {
            restoration = {
                passed: false,
                launched: false,
                reason: String(error?.message ?? error).slice(0, 500),
                ownedDrainUnknown,
                storageBreached,
            };
            originalError ??= error;
        }
    await write("normal-restoration.json", restoration);
    // Hash original success/failure checkpoint files only after known owned
    // closure. WebView/database files are retained and included in byte counts.
    if (!ownedDrainUnknown && workspace)
        for (const stage of ["initial", "restart"]) {
            const directory = path.join(workspace, stage);
            let names;
            try {
                names = await readdir(directory);
            } catch (error) {
                if (error.code === "ENOENT") continue;
                originalError ??= error;
                continue;
            }
            for (const name of names)
                if (name.endsWith(".json") || name.endsWith(".png"))
                    try {
                        const full = path.join(directory, name),
                            info = await lstat(full);
                        if (
                            !info.isFile() ||
                            info.isSymbolicLink() ||
                            info.size >
                                (name.endsWith(".png") ? 16777216 : 262144)
                        )
                            throw Error("RetainedCheckpointBudget");
                        const bytes = await readFile(full);
                        artifacts[`${stage}/${name}`] = {
                            bytes: bytes.length,
                            sha256: digest(bytes),
                        };
                    } catch (error) {
                        originalError ??= error;
                    }
        }
    if (!ownedDrainUnknown)
        try {
            await measureStorage();
        } catch (error) {
            originalError ??= error;
        }
    await write("retention-measurement.json", {
        initialStorage,
        final:
            ownedDrainUnknown || lastStorage?.unavailable ? null : lastStorage,
        lastKnown: lastStorage?.unavailable
            ? lastStorage.lastKnown
            : lastStorage,
        finalObservation: ownedDrainUnknown
            ? "unavailable-owned-drain-unknown"
            : lastStorage?.unavailable
              ? "unavailable-storage-inventory"
              : "observed-after-owned-closure",
        limits,
        storageBreached,
        retained: true,
        cleanupAttempted: false,
        unknownChildren,
        gitChildren,
        sourceMeasurement:
            "desktop checkout excluding .git/node_modules/artifacts/target; packet and existing target measured separately",
        processTreeContained: false,
    });
}
if (originalError || !candidate || restoration?.passed !== true) {
    await write("failure-observation.json", {
        revision,
        passed: false,
        error: String(
            originalError?.message ?? "LiveNarrationIncomplete",
        ).slice(0, 500),
        reports,
        artifacts,
        processes,
        gitChildren,
        restoration,
        ownedDrainUnknown,
        storageBreached,
        retained: true,
        cleanupAttempted: false,
    });
    throw originalError ?? Error("LiveNarrationIncomplete");
}
await write("summary.json", {
    ...candidate,
    passed: true,
    normalRestoration: restoration,
    storage: lastStorage,
});
console.log(
    `D06 LIVE NARRATION NATIVE PASS: 10 application-owned captures retained at ${folder}`,
);
