// Fixed app-owned selected journeys; no desktop control, model or generic runner.
// Legacy default/literal journeys stay unchanged. Their launcher admission is
// intentionally strengthened to the same bounded child/Git/storage policy.
import assert from "node:assert/strict";
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
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";

const argumentsV1 = process.argv.slice(2);
assert(
    argumentsV1.length <= 1 &&
        argumentsV1.every((a) => a === "--literal" || a === "--scene"),
    "ClosedHarnessArguments",
);
const literal = argumentsV1.includes("--literal"),
    scene = argumentsV1.includes("--scene");
process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
const root = fileURLToPath(new URL(".", import.meta.url));
const limits = Object.freeze({
    targetGrowth: 2 * 1024 ** 3,
    artifacts: 256 * 1024 ** 2,
    sourceGrowth: 128 * 1024 ** 2,
    sourceFreeze: 1024 ** 2,
    entries: 2_000_000,
    cumulativeEvidence: 512 * 1024 ** 2,
    expectedEvidence: 64 * 1024 ** 2,
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
const base = await ownedDirectory(
    process.env.LOCALLORE_D07_SELECTED_ARTIFACT_ROOT,
);
const target = await ownedDirectory(
    process.env.LOCALLORE_D07_SELECTED_TARGET_DIR ??
        (scene ? undefined : path.join(root, "src-tauri", "target")),
);
const cargoHome = scene ? await ownedDirectory(process.env.CARGO_HOME) : null;
if ((process.env.LIBSQLITE3_FLAGS ?? "").trim())
    throw Error("OrdinaryUncappedSQLiteRequired");
const folder = path.join(base, `comparison-reader-native-${randomUUID()}`);
const contains = (a, b) => {
    const rel = path.relative(a.toLowerCase(), b.toLowerCase());
    return (
        rel === "" ||
        (!path.isAbsolute(rel) &&
            rel !== ".." &&
            !rel.startsWith(`..${path.sep}`))
    );
};
const disjoint = (a, b) => !contains(a, b) && !contains(b, a);
for (const location of [target, ...(scene ? [root, cargoHome] : [])])
    if (!disjoint(folder, location)) throw Error("DisjointPacketRequired");
if (
    scene &&
    (!disjoint(root, target) ||
        !disjoint(root, cargoHome) ||
        !disjoint(target, cargoHome) ||
        !disjoint(base, root) ||
        !disjoint(base, target) ||
        !disjoint(base, cargoHome))
)
    throw Error("SeparateExistingBuildRootsRequired");
const executable = path.join(target, "debug", "locallore-desktop-spike.exe");
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
let ownedDrainUnknown = false,
    storageBreached = false,
    lastStorage = null,
    runNumber = 0;
const unknownChildren = [],
    gitChildren = [],
    processes = [],
    artifacts = {},
    reports = [];
// selected-git-policy-v1:start
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
    if (ownedDrainUnknown || storageBreached)
        throw Error(
            ownedDrainUnknown
                ? "OwnedDrainUnknownBeforeGit"
                : "StorageBudgetLatched",
        );
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
                    ...Object.fromEntries(
                        Object.entries(process.env).filter(
                            ([key]) => !/^LOCALLORE_/i.test(key),
                        ),
                    ),
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
            JSON.stringify({
                kind: "selected_git_admission_failure_v1",
                record,
            }),
        );
        throw Error(
            ownedDrainUnknown ? "OwnedDrainUnknownAfterGit" : "GitReadFailed",
        );
    }
    return buffers.stdout.toString("utf8").trim();
}
// selected-git-policy-v1:end
const revision = await gitRead(["rev-parse", "HEAD"]);
if (!/^[a-f0-9]{40}$/.test(revision))
    throw Error("ExactCommittedRevisionRequired");
if (await gitRead(["status", "--porcelain"]))
    throw Error("CleanCommittedSelectedSceneSourceRequired");
const sourceInputs = [
    "selected-evaluation-harness.mjs",
    "ui/selected-evaluation-journeys.ts",
    "ui/selected-evaluation-controller.ts",
    "ui/selected-evaluation-model.ts",
    "ui/selected-evaluation-view.tsx",
    "ui/comparison-reader-controller.ts",
    "ui/comparison-reader-model.ts",
    "ui/ComparisonReaderPanel.tsx",
    "ui/main.tsx",
    "ui/controller.ts",
    "ui/App.tsx",
    "ui/style.css",
    "ui/model.ts",
    "build.mjs",
    "package.json",
    "package-lock.json",
    "src-tauri/src/main.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/src/selected_harness.rs",
    "src-tauri/src/comparison_reader_harness.rs",
    "src-tauri/src/selected_commands.rs",
    "src-tauri/src/evaluation.rs",
    "src-tauri/src/evaluation/selected.rs",
    "src-tauri/src/evaluation/selected/versioned.rs",
    "src-tauri/src/evaluation/comparison.rs",
    "src-tauri/src/models.rs",
    "src-tauri/src/lease.rs",
    "src-tauri/src/shutdown.rs",
    "src-tauri/Cargo.toml",
    "src-tauri/build.rs",
    "src-tauri/tauri.conf.json",
    "../../Cargo.lock",
    "../../fixtures/lantern_quay.json",
    "../../crates/locallore-eval/src/local_lane/comparison/scene_v4.rs",
    "../../crates/locallore-eval/src/local_lane/comparison/scene_v4/selected_v3.rs",
    "../../crates/locallore-eval/src/local_lane/comparison/scene_v4/selected_v3/desktop_read.rs",
    "../../crates/locallore-eval/src/local_lane/comparison/scene_v4/desktop_api.rs",
    "../../crates/locallore-eval/src/local_lane/comparison/selected.rs",
    "../../crates/locallore-eval/src/local_lane/comparison/turn_execution.rs",
    "../../crates/locallore/src/host.rs",
    "../../crates/locallore/src/engine.rs",
    "../../crates/locallore/src/play.rs",
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
    throw Error("SelectedSceneSourceFreezeBudget");
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
                if (!Number.isSafeInteger(info.size) || info.size < 0)
                    throw Error("StorageInventorySize");
                bytes += info.size;
                if (!Number.isSafeInteger(bytes))
                    throw Error("StorageInventorySize");
            } else throw Error("StorageInventoryOrdinaryEntriesRequired");
        }
    };
    await visit(directory);
    return { entries, bytes };
}
// Only the seven flat admission fields below are accepted. Parse the flat
// record before projection so even escaped/identical duplicate keys refuse.
function checkedSceneBudget(bytes, revision, target, currentTargetBytes) {
    const invalid = () => {
        throw Error("SelectedSceneBudgetInvalid");
    };
    if (
        !Buffer.isBuffer(bytes) ||
        bytes.length > 4096 ||
        typeof revision !== "string" ||
        !/^[a-f0-9]{40}$/.test(revision) ||
        typeof target !== "string" ||
        !path.isAbsolute(target) ||
        !Number.isSafeInteger(currentTargetBytes) ||
        currentTargetBytes < 0
    )
        invalid();
    let text;
    try {
        text = new TextDecoder("utf-8", {
            fatal: true,
            ignoreBOM: true,
        }).decode(bytes);
    } catch {
        invalid();
    }
    let cursor = 0;
    const whitespace = () => {
        while (cursor < text.length && /[ \t\r\n]/.test(text[cursor])) cursor++;
    };
    const string = () => {
        const start = cursor;
        if (text[cursor++] !== '"') invalid();
        while (cursor < text.length) {
            const character = text[cursor++];
            if (character === "\\") {
                cursor++;
                continue;
            }
            if (character === '"') {
                try {
                    return JSON.parse(text.slice(start, cursor));
                } catch {
                    invalid();
                }
            }
        }
        invalid();
    };
    const keys = [
        "version",
        "kind",
        "source_revision",
        "target_path_sha256",
        "original_target_bytes",
        "external_evidence_bytes",
        "cumulative_limit_bytes",
    ];
    const record = Object.create(null);
    whitespace();
    if (text[cursor++] !== "{") invalid();
    whitespace();
    while (text[cursor] !== "}") {
        const key = string();
        if (!keys.includes(key) || Object.hasOwn(record, key)) invalid();
        whitespace();
        if (text[cursor++] !== ":") invalid();
        whitespace();
        if (text[cursor] === '"') record[key] = string();
        else {
            const number =
                /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(
                    text.slice(cursor),
                );
            if (!number) invalid();
            record[key] = Number(number[0]);
            cursor += number[0].length;
        }
        whitespace();
        if (text[cursor] === "}") break;
        if (text[cursor++] !== ",") invalid();
        whitespace();
        if (text[cursor] === "}") invalid();
    }
    if (text[cursor++] !== "}") invalid();
    whitespace();
    const safe = (value) => Number.isSafeInteger(value) && value >= 0;
    if (
        cursor !== text.length ||
        Object.keys(record).length !== keys.length ||
        record.version !== 1 ||
        record.kind !== "selected_scene_budget_v1" ||
        record.source_revision !== revision ||
        record.target_path_sha256 !==
            digest(Buffer.from(path.resolve(target).toLowerCase(), "utf8")) ||
        record.cumulative_limit_bytes !== limits.cumulativeEvidence ||
        !safe(record.original_target_bytes) ||
        record.original_target_bytes > currentTargetBytes ||
        !safe(record.external_evidence_bytes) ||
        record.external_evidence_bytes > limits.cumulativeEvidence
    )
        invalid();
    return {
        originalTargetBytes: record.original_target_bytes,
        externalEvidenceBytes: record.external_evidence_bytes,
    };
}

// selected-qualification-budget-v1:start
const disk = await statfs(root, { bigint: true });
const observedTarget = await footprint(target);
const observedBase = scene ? await footprint(base) : { bytes: 0 };
let qualificationBudget = null;
if (scene) {
    const bytes = await boundedBytes(
        path.join(base, `selected-scene-budget-v1-${revision}.json`),
        4096,
    );
    qualificationBudget = {
        ...checkedSceneBudget(bytes, revision, target, observedTarget.bytes),
        recordSHA256: digest(bytes),
    };
}
const qualificationEvidenceBytes =
    observedBase.bytes + (qualificationBudget?.externalEvidenceBytes ?? 0);
if (
    !Number.isSafeInteger(qualificationEvidenceBytes) ||
    qualificationEvidenceBytes < 0
)
    throw Error("CumulativeEvidenceAdmissionBudget");
if (
    scene &&
    observedTarget.bytes - qualificationBudget.originalTargetBytes >
        limits.targetGrowth
)
    throw Error("OriginalTargetAdmissionBudget");
const initialStorage = {
    target: {
        ...observedTarget,
        bytes: qualificationBudget?.originalTargetBytes ?? observedTarget.bytes,
    },
    source: await footprint(root, true),
    evidence: { ...observedBase, bytes: qualificationEvidenceBytes },
    observedTarget,
    observedBase,
    qualificationBudget,
    freeDBytes: String(disk.bavail * disk.bsize),
};
if (
    BigInt(initialStorage.freeDBytes) <
    BigInt(limits.targetGrowth + limits.artifacts + limits.sourceGrowth)
)
    throw Error("DeclaredRunGrowthExceedsFreeD");
if (
    scene &&
    initialStorage.evidence.bytes >
        limits.cumulativeEvidence - limits.expectedEvidence
)
    throw Error("CumulativeEvidenceAdmissionBudget");
// selected-qualification-budget-v1:end
await mkdir(folder, { recursive: false }); // Create-new packet; never replace/delete a prior attempt.
const write = (name, value) => {
    const encoded = JSON.stringify(value, null, 2);
    if (Buffer.byteLength(encoded) > 262144)
        throw Error("LauncherMetadataBudget");
    return writeFile(path.join(folder, name), encoded, { flag: "wx" });
};
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
    if (Number.isSafeInteger(initialStorage.evidence?.bytes)) {
        lastStorage.cumulativeEvidence =
            initialStorage.evidence.bytes + lastStorage.packet.bytes;
        if (
            !Number.isSafeInteger(lastStorage.cumulativeEvidence) ||
            lastStorage.cumulativeEvidence > 512 * 1024 ** 2 - 1024 ** 2
        )
            storageBreached = true;
    }
    // Reserve 1 MiB for the final three bounded metadata files after this measurement.
    if (
        lastStorage.targetGrowth > limits.targetGrowth ||
        lastStorage.sourceGrowth > limits.sourceGrowth ||
        lastStorage.packet.bytes > limits.artifacts - 1024 ** 2
    )
        storageBreached = true;
    if (storageBreached) throw Error("SelectedSceneStorageBudgetExceeded");
    return lastStorage;
}
async function unchangedSource() {
    if (
        (await gitRead(["rev-parse", "HEAD"])) !== revision ||
        (await gitRead(["status", "--porcelain"])) ||
        JSON.stringify(await hashes(sourceInputs)) !==
            JSON.stringify(sourceHashes)
    )
        throw Error("SelectedSceneSourceChanged");
}
let productHashes = null;
async function unchangedProducts() {
    if (
        !productHashes ||
        JSON.stringify(await hashes(["dist/app.js", executable])) !==
            JSON.stringify(productHashes)
    )
        throw Error("SelectedSceneProductChanged");
}
Object.assign(process.env, {
    ...(cargoHome ? { CARGO_HOME: cargoHome } : {}),
    CARGO_TARGET_DIR: target,
    CARGO_BUILD_JOBS: "1",
    CARGO_PROFILE_DEV_DEBUG: "0",
    CARGO_PROFILE_TEST_DEBUG: "0",
    CARGO_INCREMENTAL: "0",
});
// selected-child-policy-v1:start
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
            command === "cargo"
                ? 900000
                : command === executable
                  ? 960000
                  : 240000,
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
        throw Error(`SelectedSceneChildFailure:${sequence}`);
}
// selected-child-policy-v1:end
const legacyLabels = [
    "selected-resumed",
    "selected-constructions",
    "selected-constructions-narrow",
    ...(literal
        ? [
              "selected-literal-capture",
              "selected-guard-results",
              "selected-relevant-construction",
              "selected-literal-proof-narrow",
          ]
        : []),
    "selected-prepared",
    "selected-completed",
    "selected-summary",
    "selected-left-after",
    "selected-right-after",
    "selected-receipt",
    "selected-capture",
    "selected-outputs",
    "selected-narrow",
    "selected-mira",
    "selected-sable",
    "selected-guard",
    "selected-unknown",
    "selected-recovered",
    "selected-consent-pending",
    "selected-consent-actor",
    "selected-consent-cancelled",
    "selected-consent-denied",
    "selected-context-retired",
    "selected-finished",
];

const sceneLabels = {
    initial: [
        "prepared",
        "completed",
        "summary",
        "left-after",
        "right-after",
        "receipt",
        "capture",
        "outputs",
        "constructions",
        "mira",
        "sable",
        "guard",
        "guard-results",
        "native-unavailable",
        "unknown",
        "recovered",
        "consent-pending",
        "consent-actor",
        "consent-cancelled",
        "consent-denied",
        "context-retired",
        "enlarged-wide",
        "enlarged-narrow",
        "resumed",
        "finished",
    ].map((name) => `selected-scene-${name}`),
    restart: [
        "restarted",
        "restart-receipt",
        "restart-actor",
        "restart-resumed",
        "restart-finished",
    ].map((name) => `selected-scene-${name}`),
};
const hex = (value) =>
    typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
const guid = (value) =>
    typeof value === "string" &&
    /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(
        value,
    );
const exactKeys = (value, keys) =>
    value &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    Object.keys(value).sort().join("|") === [...keys].sort().join("|");
const relativeFile = (value) =>
    typeof value === "string" &&
    value.length > 0 &&
    !/[\\:\x00-\x1f\x7f]/.test(value) &&
    value.split("/").every((part) => part && part !== "." && part !== "..");
async function boundedBytes(file, maximum) {
    const info = await lstat(file);
    if (
        !info.isFile() ||
        info.isSymbolicLink() ||
        !Number.isSafeInteger(info.size) ||
        info.size < 0 ||
        info.size > maximum
    )
        throw Error("RetainedFileBudget");
    const bytes = await readFile(file);
    if (bytes.length > maximum || bytes.length !== info.size)
        throw Error("RetainedFileChanged");
    return bytes;
}
async function jsonFile(file, maximum = 262144) {
    return JSON.parse((await boundedBytes(file, maximum)).toString("utf8"));
}
async function inventory(directory, sourceFixture = true) {
    const files = [],
        fileCap = sourceFixture ? 2048 : 8192;
    let entries = 0,
        total = 0;
    async function visit(current, depth) {
        if (++entries > 8192 || depth > 8) throw Error("FixtureEntryBudget");
        const info = await lstat(current);
        if (info.isSymbolicLink()) throw Error("FixtureLink");
        if (info.isDirectory()) {
            for (const name of (await readdir(current)).sort())
                await visit(path.join(current, name), depth + 1);
        } else {
            if (files.length >= fileCap || !info.isFile())
                throw Error("FixtureFileBudget");
            const bytes = await boundedBytes(
                current,
                (sourceFixture ? 8 : 32) * 1024 ** 2,
            );
            total += bytes.length;
            if (
                !Number.isSafeInteger(total) ||
                total > (sourceFixture ? 64 : 256) * 1024 ** 2
            )
                throw Error("FixtureTotalBudget");
            const name = path
                .relative(directory, current)
                .replaceAll(path.sep, "/");
            if (!relativeFile(name)) throw Error("FixtureRelativePath");
            files.push([name, digest(bytes)]);
        }
    }
    await visit(directory, 0);
    return {
        files: Object.fromEntries(files),
        file_count: files.length,
        entry_count: entries,
        total_bytes: total,
    };
}
async function sourceFreeze(expected = null) {
    const bytes = await boundedBytes(
        path.join(folder, "selected-scene-source-freeze-v1.json"),
        1024 ** 2,
    );
    const freeze = JSON.parse(bytes.toString("utf8"));
    assert(
        exactKeys(freeze, [
            "version",
            "kind",
            "source_protocol_version",
            "files",
            "file_count",
            "entry_count",
            "total_bytes",
        ]),
        "ClosedFreezeKeys",
    );
    assert(
        freeze.version === 1 &&
            freeze.kind === "selected_scene_source_freeze_v1" &&
            freeze.source_protocol_version === 4,
        "FreezeVersion",
    );
    assert(
        freeze.files &&
            !Array.isArray(freeze.files) &&
            typeof freeze.files === "object",
        "FreezeFiles",
    );
    assert(
        Object.entries(freeze.files).every(
            ([name, hash]) => relativeFile(name) && hex(hash),
        ),
        "FreezePathsAndHashes",
    );
    const observed = await inventory(path.join(folder, "comparison-fixtures"));
    assert.deepEqual(
        {
            files: freeze.files,
            file_count: freeze.file_count,
            entry_count: freeze.entry_count,
            total_bytes: freeze.total_bytes,
        },
        observed,
        "CompleteSourceFreezeBytes",
    );
    const reference = {
        version: 1,
        kind: "selected_scene_source_freeze_ref_v1",
        sha256: digest(bytes),
        source_protocol_version: 4,
        file_count: observed.file_count,
        entry_count: observed.entry_count,
        total_bytes: observed.total_bytes,
    };
    if (expected)
        assert.deepEqual(reference, expected, "RetainedFreezeByteIdentity");
    return { bytes, reference };
}
async function absentModelRoot() {
    try {
        await lstat(path.join(folder, "models"));
    } catch (error) {
        if (error.code === "ENOENT") return;
        throw error;
    }
    throw Error("ScriptedModelRootMustRemainAbsent");
}
async function proof(name, value) {
    const bytes = Buffer.from(JSON.stringify(value));
    if (bytes.length > 1024 ** 2) throw Error("LauncherProofBudget");
    await writeFile(path.join(folder, name), bytes, { flag: "wx" });
    return { sha256: digest(bytes), bytes: bytes.length };
}
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
const runtimeUserAgents = new Set();
let originalError = null,
    restoration = null,
    candidate = null,
    workspace = null;
let expectedFixtures = null,
    expectedLibrary = null,
    initialRoles = null,
    sourceProof = null,
    libraryProof = null;
await write("source-manifest.json", {
    version: 1,
    kind: "selected_native_harness_v1",
    revision,
    inputSHA256: sourceHashes,
    sourceDirty: false,
    node: process.version,
    budgets: limits,
    initialStorage,
    sourceProtocol: scene ? 4 : literal ? 3 : 2,
    selectedVersion: scene ? 3 : literal ? 2 : 1,
    synthetic: true,
    nativeIpc: false,
    rendering: "pending",
    modelExecution: false,
    gitChildren,
});
try {
    await run(process.execPath, ["build.mjs", "--harness"]);
    await run("cargo", buildArgs(false));
    productHashes = await hashes(["dist/app.js", executable]);
    await write("product-manifest.json", {
        revision,
        productSHA256: productHashes,
    });
    workspace = folder;
    for (const stage of ["initial", "restart"]) {
        const directory = path.join(folder, stage);
        const flags = {
            LOCALLORE_D02_HARNESS: "1",
            LOCALLORE_D07_COMPARISON_READER_HARNESS: "1",
            LOCALLORE_D07_SELECTED_HARNESS: "1",
            ...(scene
                ? { LOCALLORE_D07_SCENE_COMPARISON_READER: "1" }
                : {
                      LOCALLORE_D07_LITERAL_COMPARISON_READER: literal
                          ? "1"
                          : "0",
                  }),
            LOCALLORE_D02_ARTIFACT_DIR: directory,
            LOCALLORE_TEST_WORKSPACE: path.join(folder, "stories-v1.sqlite"),
            LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
            WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:
                "--disable-background-timer-throttling",
        };
        await run(executable, [], flags);
        const report = await jsonFile(path.join(directory, "report.json"));
        reports.push({ stage, report });
        assert.equal(
            report.passed,
            true,
            `Journeys:${stage}:${report.failedCheck}`,
        );
        assert.equal(report.stage, stage, "ActualStage");
        assert.equal(
            report.sourceProtocol,
            scene ? 4 : literal ? 3 : 2,
            `ActualProtocol:${stage}`,
        );
        assert.equal(
            report.selectedVersion,
            scene ? 3 : literal ? 2 : 1,
            `ActualSelectedVersion:${stage}`,
        );
        assert.equal(
            report.realModelGeneration,
            false,
            "NoRealModelGeneration",
        );
        if (!scene) {
            if (stage === "restart")
                assert(
                    reports[0].report.savedRuns.includes(report.reopenedRun),
                    "ColdOpenIsInitialDurableRun",
                );
            assert(
                Array.isArray(report.checks) &&
                    report.checks.length >= (stage === "restart" ? 160 : 154),
                `FrozenCheckCount:${stage}`,
            );
        } else
            assert(
                Array.isArray(report.checks) && report.checks.length > 0,
                "ActualSceneChecksRequired",
            );
        const expectedLabels = scene
            ? sceneLabels[stage]
            : stage === "restart"
              ? [...legacyLabels, "selected-restarted"]
              : legacyLabels;
        const names = await readdir(directory);
        assert.deepEqual(
            names
                .filter((name) => name.endsWith(".png"))
                .map((name) => name.slice(0, -4))
                .sort(),
            [...expectedLabels].sort(),
            `ActualWebViewImages:${stage}`,
        );
        for (const label of expectedLabels) {
            const capture = await jsonFile(
                path.join(directory, `${label}.capture.json`),
            );
            assert.equal(
                capture.rendering,
                "native-webview2",
                `ActualNativeRendering:${label}`,
            );
            const snapshot = await jsonFile(
                path.join(directory, `${label}.json`),
            );
            assert.equal(
                snapshot.semanticVersion,
                scene ? 3 : 2,
                `SemanticVersion:${label}`,
            );
            assert(snapshot.selectedEvaluation, `SelectedSnapshot:${label}`);
            assert(
                [
                    "selectedStory",
                    "observer",
                    "revision",
                    "pendingOperation",
                    "displayedReceipt",
                    "visibleError",
                ].every((key) => Object.hasOwn(snapshot, key)),
                `CoherentSnapshotFields:${label}`,
            );
            const userAgent = snapshot.dom?.userAgent;
            if (
                typeof userAgent === "string" &&
                userAgent.length > 0 &&
                userAgent.length <= 1024
            )
                runtimeUserAgents.add(userAgent);
            const image = await boundedBytes(
                path.join(directory, `${label}.png`),
                16777216,
            );
            assert(
                image
                    .subarray(0, 8)
                    .equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])),
                `ActualPngSignature:${label}`,
            );
        }
        if (scene) {
            const freeze = await sourceFreeze(expectedFixtures);
            assert.deepEqual(
                report.sourceInventory,
                freeze.reference,
                `InitialSourceReference:${stage}`,
            );
            assert.deepEqual(
                report.finalSourceInventory,
                freeze.reference,
                `FinalSourceReference:${stage}`,
            );
            if (stage === "initial") {
                expectedFixtures = freeze.reference;
                sourceProof = await proof(
                    "source-fixture-inventory.json",
                    JSON.parse(freeze.bytes.toString("utf8")),
                );
                const roles = report.runRoles;
                assert(
                    exactKeys(roles, ["paired", "rollout", "guard"]) &&
                        Object.values(roles).every(guid),
                    "ActualRoleLabeledRunIds",
                );
                assert.equal(
                    new Set(Object.values(roles)).size,
                    3,
                    "ExactlyThreeDistinctRunRoles",
                );
                assert.deepEqual(
                    [...report.savedRuns].sort(),
                    Object.values(roles).sort(),
                    "AllSavedRoleIds",
                );
                initialRoles = roles;
                for (const role of ["paired", "rollout", "guard"]) {
                    const index = await jsonFile(
                        path.join(
                            folder,
                            "selected-evaluations",
                            roles[role],
                            "native.json",
                        ),
                        32768,
                    );
                    assert(
                        index.version === 3 &&
                            index.run_id === roles[role] &&
                            index.lane === "scripted_baseline" &&
                            index.prepared.version === 3 &&
                            index.prepared.source_protocol_version === 4 &&
                            index.prepared.lane === "scripted_selected_case" &&
                            hex(index.source_binding) &&
                            index.source_binding ===
                                index.prepared.source_binding,
                        "ActualSavedSelected3Index",
                    );
                    if (role !== "guard")
                        assert(
                            index.prepared.selection.turn === "courier-05" &&
                                index.prepared.selection.index === 4 &&
                                index.prepared.selection.clicked_arm ===
                                    (role === "paired" ? "right" : "left"),
                            "ExactPairedAndRolloutTuple",
                        );
                }
            } else {
                const initialIDs = [...reports[0].report.savedRuns].sort();
                assert.deepEqual(
                    [...report.savedRuns].sort(),
                    initialIDs,
                    "RestartSavedExactInitialIds",
                );
                assert.deepEqual(
                    [...report.reopenedIDs].sort(),
                    initialIDs,
                    "RestartOpenedEveryExactInitialId",
                );
                assert.equal(
                    report.reopenedRun,
                    initialRoles.rollout,
                    "ColdOpenExactInitialRollout",
                );
                assert.equal(
                    report.resumedRun,
                    initialRoles.rollout,
                    "CompletedResumeExactInitialRollout",
                );
            }
            assert.deepEqual(
                (
                    await readdir(path.join(folder, "selected-evaluations"))
                ).sort(),
                Object.values(initialRoles).sort(),
                "ExactDurableSelectedRunSet",
            );
            const library = await inventory(
                path.join(folder, "selected-evaluations"),
                false,
            );
            if (expectedLibrary)
                assert.deepEqual(
                    library,
                    expectedLibrary,
                    "RestartPreservesEntireSelectedLibrary",
                );
            else {
                expectedLibrary = library;
                libraryProof = await proof(
                    "selected-library-inventory.json",
                    library,
                );
            }
            await absentModelRoot();
        } else {
            const actual = (
                await inventory(path.join(folder, "comparison-fixtures"))
            ).files;
            const finalSnapshot = await jsonFile(
                path.join(directory, "selected-finished.json"),
            );
            assert.deepEqual(
                actual,
                finalSnapshot.finalSourceInventory,
                `CompleteSourceFixtureBytesUnchanged:${stage}`,
            );
            assert.deepEqual(
                actual,
                finalSnapshot.sourceInventory,
                `OriginalSourceFixtureBytesUnchanged:${stage}`,
            );
            if (expectedFixtures)
                assert.deepEqual(
                    actual,
                    expectedFixtures,
                    "RestartPreservesEverySourceFixtureByte",
                );
            expectedFixtures = actual;
        }
        await unchangedSource();
        await measureStorage();
    }
    assert(runtimeUserAgents.size > 0, "ActualWebViewUserAgentRequired");
    candidate = {
        version: 1,
        passed: true,
        sourceRevision: revision,
        synthetic: true,
        sourceProtocol: scene ? 4 : literal ? 3 : 2,
        selectedVersion: scene ? 3 : literal ? 2 : 1,
        nativeIpc: true,
        rendering: "actual-hidden-unfocused-webview2",
        desktopInput: false,
        nativeDialogsAutomated: false,
        modelExecution: false,
        runtimeUserAgents: [...runtimeUserAgents],
        requestedTestBrowserArguments: [
            "--disable-background-timer-throttling",
        ],
        reports,
        sourceInventory: expectedFixtures,
        sourceProof,
        libraryProof,
        runRoles: initialRoles,
        productSHA256: productHashes,
        imageReview: "pending-individual-Root-review",
        limitations: [
            "Scripted fake inference only; no real model execution",
            "Fixed consent/picker/lostACK controls are synthetic doubles",
            "No native between-arm inference interruption or process-death evidence",
            "Direct-child closure only, no process-tree containment",
            "Ordinary status/shutdown may inspect absent task model candidate; no SDK-load counter",
            "Images require individual review; signatures/geometry are not visual acceptance",
            "No human quality, phone runtime, SDK, OS isolation or release qualification",
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
                        const bytes = await boundedBytes(
                            path.join(directory, name),
                            name.endsWith(".png") ? 16777216 : 262144,
                        );
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
            originalError?.message ?? "SelectedHarnessIncomplete",
        ).slice(0, 500),
        reports,
        artifacts,
        processes,
        gitChildren,
        restoration,
        ownedDrainUnknown,
        storageBreached,
        modelExecution: false,
    });
    process.exitCode = 1;
    console.error(
        JSON.stringify({
            passed: false,
            artifactDirectory: folder,
            sourceRevision: revision,
            ownedDrainUnknown,
            storageBreached,
            normalRestored: restoration?.passed === true,
        }),
    );
} else {
    await write("qualification.json", {
        ...candidate,
        processes,
        gitChildren,
        artifacts,
        restoration,
        retention: lastStorage,
    });
    console.log(
        JSON.stringify({
            passed: true,
            artifactDirectory: folder,
            sourceRevision: revision,
            stages: reports.length,
            nativeIpc: true,
            modelExecution: false,
            normalRestored: true,
            imageReview: "pending",
        }),
    );
}
