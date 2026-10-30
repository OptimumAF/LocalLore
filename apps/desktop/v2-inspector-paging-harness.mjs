// Fixed development-only V2 inspector journey. No desktop control or model.
// Private coordinator launcher, zero CLI arguments; never a remote service.
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

if (process.argv.length !== 2) throw Error("ClosedPagingArgumentsRequired");
process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
const root = fileURLToPath(new URL(".", import.meta.url));
const limits = Object.freeze({
    targetGrowth: 2147483648,
    sourceGrowth: 134217728,
    artifacts: 67108864,
    entries: 2000000,
    cumulativeEvidence: 671088640,
    expectedEvidence: 67108864,
    pagingEvidence: 134217728,
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
const base = await ownedDirectory(process.env.LOCALLORE_D05_ARTIFACT_ROOT);
const target = await ownedDirectory(process.env.LOCALLORE_D05_TARGET_DIR);
const cargoHome = await ownedDirectory(process.env.CARGO_HOME);
if ((process.env.LIBSQLITE3_FLAGS ?? "").trim())
    throw Error("OrdinaryUncappedSQLiteRequired");
const folder = path.join(base, `v2-inspector-paging-native-${randomUUID()}`);
const contains = (a, b) => {
    const rel = path.relative(a.toLowerCase(), b.toLowerCase());
    return (
        rel === "" ||
        (!path.isAbsolute(rel) &&
            rel !== ".." &&
            !rel.startsWith(`..${path.sep}`))
    );
};
const locations = [root, base, target, cargoHome];
for (let i = 0; i < locations.length; i++)
    for (let j = i + 1; j < locations.length; j++)
        if (
            contains(locations[i], locations[j]) ||
            contains(locations[j], locations[i])
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
    artifacts = {};
// d05-paging-git-policy-v1:start

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
// d05-paging-git-policy-v1:end
// d05-paging-git-admission-v1:start
const revision = await gitRead(["rev-parse", "HEAD"]);
if (!/^[a-f0-9]{40}$/.test(revision))
    throw Error("ExactCommittedRevisionRequired");
if (await gitRead(["status", "--porcelain"]))
    throw Error("CleanCommittedPagingSourceRequired");
// d05-paging-git-admission-v1:end
const sourcePaths = (await gitRead(["ls-files", "--full-name", "../.."]))
    .split("\n")
    .filter(
        (name) =>
            /^(?:apps\/desktop\/|crates\/|fixtures\/|Cargo\.|\.cargo\/)/.test(
                name,
            ) && /\.(?:rs|ts|tsx|css|html|json|mjs|toml|lock)$/.test(name),
    )
    .map((name) => path.resolve(root, "../..", name));
if (!sourcePaths.length || sourcePaths.length > 2048)
    throw Error("SourceRosterBudget");
async function hashes(files) {
    return Object.fromEntries(
        await Promise.all(
            files.map(async (file) => [
                file,
                digest(
                    await readFile(
                        path.isAbsolute(file) ? file : path.join(root, file),
                    ),
                ),
            ]),
        ),
    );
}
const sourceHashes = await hashes(sourcePaths);
async function boundedBytes(file, maximum) {
    const info = await lstat(file);
    if (
        !info.isFile() ||
        info.isSymbolicLink() ||
        !Number.isSafeInteger(info.size) ||
        info.size < 0 ||
        info.size > maximum
    )
        throw Error("BoundedOrdinaryArtifactRequired");
    const bytes = await readFile(file);
    if (bytes.length > maximum) throw Error("ArtifactReadBudget");
    return bytes;
}
// d05-paging-footprint-v1:start
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
// d05-paging-footprint-v1:end
// d05-paging-budget-policy-v1:start
function checkedPagingBudget(bytes, revision, target, currentTargetBytes) {
    const invalid = () => {
        throw Error("PagingBudgetInvalid");
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
        "d05_external_evidence_bytes",
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
        record.kind !== "d05_v2_inspector_paging_budget_v1" ||
        record.source_revision !== revision ||
        record.target_path_sha256 !==
            digest(Buffer.from(path.resolve(target).toLowerCase(), "utf8")) ||
        record.cumulative_limit_bytes !== limits.cumulativeEvidence ||
        !safe(record.original_target_bytes) ||
        record.original_target_bytes > currentTargetBytes ||
        !safe(record.external_evidence_bytes) ||
        record.external_evidence_bytes > 536870912 ||
        !safe(record.d05_external_evidence_bytes)
    )
        invalid();
    return {
        originalTargetBytes: record.original_target_bytes,
        externalEvidenceBytes: record.external_evidence_bytes,
        d05ExternalEvidenceBytes: record.d05_external_evidence_bytes,
    };
}

const disk = await statfs(root, { bigint: true });
const observedTarget = await footprint(target);
const observedBase = await footprint(base);
const budgetBytes = await boundedBytes(
    path.join(base, "d05-v2-inspector-paging-budget-v1-" + revision + ".json"),
    4096,
);
const qualificationBudget = {
    ...checkedPagingBudget(budgetBytes, revision, target, observedTarget.bytes),
    recordSHA256: digest(budgetBytes),
};
const pagingEvidenceBytes =
    observedBase.bytes + qualificationBudget.d05ExternalEvidenceBytes;
const qualificationEvidenceBytes =
    pagingEvidenceBytes + qualificationBudget.externalEvidenceBytes;
if (
    !Number.isSafeInteger(pagingEvidenceBytes) ||
    pagingEvidenceBytes < 0 ||
    !Number.isSafeInteger(qualificationEvidenceBytes) ||
    qualificationEvidenceBytes < 0
)
    throw Error("CumulativeEvidenceAdmissionBudget");
if (
    observedTarget.bytes - qualificationBudget.originalTargetBytes >
    limits.targetGrowth
)
    throw Error("OriginalTargetAdmissionBudget");
const initialStorage = {
    target: {
        ...observedTarget,
        bytes: qualificationBudget.originalTargetBytes,
    },
    source: await footprint(root, true),
    evidence: { ...observedBase, bytes: qualificationEvidenceBytes },
    pagingEvidence: { ...observedBase, bytes: pagingEvidenceBytes },
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
    initialStorage.evidence.bytes >
        limits.cumulativeEvidence - limits.expectedEvidence ||
    initialStorage.pagingEvidence.bytes >
        limits.pagingEvidence - limits.expectedEvidence
)
    throw Error("CumulativeEvidenceAdmissionBudget");
// d05-paging-budget-policy-v1:end
await mkdir(folder, { recursive: false });
const write = (name, value) => {
    const bytes = Buffer.from(JSON.stringify(value, null, 2));
    if (bytes.length > 262144) throw Error("LauncherMetadataBudget");
    return writeFile(path.join(folder, name), bytes, { flag: "wx" });
};
let productHashes = null;
Object.assign(process.env, {
    CARGO_HOME: cargoHome,
    CARGO_TARGET_DIR: target,
    CARGO_NET_OFFLINE: "true",
    CARGO_BUILD_JOBS: "1",
    CARGO_INCREMENTAL: "0",
    CARGO_PROFILE_DEV_DEBUG: "0",
    CARGO_PROFILE_TEST_DEBUG: "0",
});
// d05-paging-process-policy-v1:start

async function measureStorage() {
    if (storageBreached) throw Error("StorageBudgetLatched");
    try {
        lastStorage = {
            target: await footprint(target),
            source: await footprint(root, true),
            packet: await footprint(folder),
        };
    } catch (error) {
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
    lastStorage.cumulativeEvidence =
        initialStorage.evidence.bytes + lastStorage.packet.bytes;
    lastStorage.pagingEvidence =
        initialStorage.pagingEvidence.bytes + lastStorage.packet.bytes;
    if (
        !Number.isSafeInteger(lastStorage.cumulativeEvidence) ||
        lastStorage.cumulativeEvidence < 0 ||
        !Number.isSafeInteger(lastStorage.pagingEvidence) ||
        lastStorage.pagingEvidence < 0 ||
        lastStorage.cumulativeEvidence > limits.cumulativeEvidence - 1048576 ||
        lastStorage.pagingEvidence > limits.pagingEvidence - 1048576 ||
        lastStorage.targetGrowth > limits.targetGrowth ||
        lastStorage.sourceGrowth > limits.sourceGrowth ||
        lastStorage.packet.bytes > limits.artifacts - 1048576
    )
        storageBreached = true;
    if (storageBreached) throw Error("PagingStorageBudgetExceeded");
    return lastStorage;
}
async function unchangedSource() {
    if (
        (await gitRead(["rev-parse", "HEAD"])) !== revision ||
        (await gitRead(["status", "--porcelain"])) ||
        JSON.stringify(await hashes(sourcePaths)) !==
            JSON.stringify(sourceHashes)
    )
        throw Error("PagingSourceChanged");
}

async function unchangedProducts() {
    if (
        !productHashes ||
        JSON.stringify(await hashes(["dist/app.js", executable])) !==
            JSON.stringify(productHashes)
    )
        throw Error("PagingProductChanged");
}

async function run(command, args, additions = {}) {
    if (ownedDrainUnknown || storageBreached)
        throw Error(
            ownedDrainUnknown ? "OwnedDrainUnknown" : "StorageBudgetLatched",
        );
    if (processes.length >= 64) throw Error("ChildProcessRecordBudget");
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
                  ? 180000
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
        throw Error(`PagingChildFailure:${sequence}`);
}
// d05-paging-process-policy-v1:end
function buildArgs(normal = false) {
    return [
        "build",
        "--manifest-path",
        "src-tauri/Cargo.toml",
        "--bin",
        "locallore-desktop-spike",
        "--locked",
        "--offline",
        ...(normal ? [] : ["--features", "dev-harness"]),
    ];
}
const labels = [
    "first",
    "second",
    "third",
    "back-second",
    "back-first",
    "forward-refetched",
    "pending-next",
    "error",
    "retry-second",
    "search-reset",
    "historical",
    "mira",
    "sable",
    "other-story",
    "same-head-refresh",
    "stale-delivery",
    "unsupported",
    "enlarged-wide",
    "enlarged-narrow",
    "final",
].map((name) => `d05-page-${name}`);
let originalError = null,
    restoration = null,
    workspace = null,
    candidate = null;
try {
    await write("source-freeze.json", {
        revision,
        sourcePaths,
        sourceHashes,
        limits,
        initialStorage,
    });
    await run(process.execPath, ["build.mjs", "--harness"]);
    await run("cargo", buildArgs());
    productHashes = await hashes(["dist/app.js", executable]);
    workspace = path.join(
        folder,
        `d05-v2-inspector-paging-native-${randomUUID()}`,
    );
    await mkdir(workspace, { recursive: false });
    await run(executable, [], {
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_D05_INSPECTOR_PAGING_HARNESS: "1",
        LOCALLORE_TEST_WORKSPACE: path.join(workspace, "stories-v1.sqlite"),
        LOCALLORE_D02_ARTIFACT_DIR: path.join(workspace, "evidence"),
    });
    const report = JSON.parse(
        (
            await boundedBytes(
                path.join(workspace, "evidence", "report.json"),
                262144,
            )
        ).toString("utf8"),
    );
    if (
        report.passed !== true ||
        report.mode !== "v2_inspector_paging_v1" ||
        report.nativeCaptures !== 20 ||
        JSON.stringify(report.captures) !== JSON.stringify(labels)
    )
        throw Error("NativePagingJourneyIncomplete");
    for (const label of labels) {
        const semantic = JSON.parse(
            (
                await boundedBytes(
                    path.join(workspace, "evidence", label + ".json"),
                    262144,
                )
            ).toString("utf8"),
        );
        const png = await boundedBytes(
            path.join(workspace, "evidence", label + ".png"),
            16777216,
        );
        const capture = JSON.parse(
            (
                await boundedBytes(
                    path.join(workspace, "evidence", label + ".capture.json"),
                    262144,
                )
            ).toString("utf8"),
        );
        if (
            !semantic.synthetic ||
            semantic.mode !== "v2_inspector_paging_v1" ||
            capture.rendering !== "native-webview2" ||
            !png
                .subarray(0, 8)
                .equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))
        )
            throw Error("NativePagingCaptureIncomplete");
    }
    candidate = {
        revision,
        passed: true,
        report,
        productHashes,
        rendering: "native-webview2",
        imageReview: "pending-individual-Root-review",
        limitations: [
            "No physical keyboard/screen-reader qualification",
            "Delivery hold/drop are after actual IPC, not Rust worker cancellation",
            "No native restart, real inference, SDK, device or OS isolation qualification",
            "Direct-child supervision only; no process-tree containment",
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
    if (workspace && !ownedDrainUnknown && !storageBreached) {
        try {
            const directory = path.join(workspace, "evidence");
            for (const name of await readdir(directory))
                if (name.endsWith(".json") || name.endsWith(".png")) {
                    const bytes = await boundedBytes(
                        path.join(directory, name),
                        name.endsWith(".png") ? 16777216 : 262144,
                    );
                    artifacts[name] = {
                        bytes: bytes.length,
                        sha256: digest(bytes),
                    };
                }
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
        unknownChildren,
        gitChildren,
        retained: true,
        cleanupAttempted: false,
        processTreeContained: false,
    });
}
if (originalError || !candidate || restoration?.passed !== true) {
    await write("failure-observation.json", {
        revision,
        passed: false,
        error: String(
            originalError?.message ?? "PagingHarnessIncomplete",
        ).slice(0, 500),
        candidate,
        artifacts,
        processes,
        gitChildren,
        restoration,
        ownedDrainUnknown,
        storageBreached,
    });
    process.exitCode = 1;
} else
    await write("qualification.json", {
        ...candidate,
        artifacts,
        processes,
        gitChildren,
        restoration,
        limits,
        lastStorage,
    });
console.log(
    JSON.stringify({
        passed: !process.exitCode,
        artifactDirectory: folder,
        sourceRevision: revision,
        normalRestored: restoration?.passed === true,
        ownedDrainUnknown,
        storageBreached,
    }),
);
