// Independent FIRST at accepted88642b82. SOURCE ONLY / AUTHOR UNRUN.
// Actual trusted launcher decoder/startup/storage/work fences in a VM. Synthetic
// observations only: no launcher import, child, directory, storage or OS probe.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { runInNewContext } from "node:vm";
import path from "node:path";

process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
assert.equal(
    process.argv.length,
    2,
    "ClosedSelectedQualificationBudgetArguments",
);
const sourceUrl = new URL("./selected-evaluation-harness.mjs", import.meta.url);
const source = await readFile(sourceUrl, "utf8");
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const plain = (value) => JSON.parse(JSON.stringify(value));
const checks = [],
    authored = [],
    setup = [];
const MiB = 1024 ** 2,
    cumulative = 512 * MiB;
const revision = "a".repeat(40);
const paths = Object.freeze({
    root: "D:\\synthetic-qualification\\source",
    target: "D:\\synthetic-qualification\\ExistingTarget",
    base: "D:\\synthetic-qualification\\artifacts",
    folder: "D:\\synthetic-qualification\\artifacts\\comparison-reader-native-00000000-0000-0000-0000-000000000001",
    executable: "D:\\synthetic-qualification\\ExistingTarget\\debug\\app.exe",
});
const recordFile = path.win32.join(
    paths.base,
    `selected-scene-budget-v1-${revision}.json`,
);
const targetHash = hash(path.win32.resolve(paths.target).toLowerCase());
function record(changes = {}) {
    return {
        version: 1,
        kind: "selected_scene_budget_v1",
        source_revision: revision,
        target_path_sha256: targetHash,
        original_target_bytes: 11,
        external_evidence_bytes: 13,
        cumulative_limit_bytes: cumulative,
        ...changes,
    };
}
const encode = (value) => Buffer.from(JSON.stringify(value));
function between(start, end) {
    const first = source.indexOf(start),
        last = source.indexOf(end, first + start.length);
    assert(
        first >= 0 &&
            last > first &&
            source.indexOf(start, first + start.length) === -1,
        `UniqueActualMarker:${start}`,
    );
    return {
        text: source.slice(first + start.length, last),
        start: first,
        end: last + end.length,
    };
}
function helper(name, isAsync = true) {
    const start = `${isAsync ? "async " : ""}function ${name}(`;
    const first = source.indexOf(start),
        last = source.indexOf("\n}", first + start.length);
    assert(
        first >= 0 &&
            last > first &&
            source.indexOf(start, first + start.length) === -1,
        `UniqueActualHelper:${name}`,
    );
    return source.slice(first, last + 2);
}
let blocks;
try {
    const limitsStart = source.indexOf("const limits = Object.freeze({"),
        limitsEnd = source.indexOf("\n});", limitsStart);
    assert(
        limitsStart >= 0 &&
            limitsEnd > limitsStart &&
            source.indexOf(
                "const limits = Object.freeze({",
                limitsStart + 1,
            ) === -1,
        "UniqueActualLimits",
    );
    const startup = between(
        "// selected-qualification-budget-v1:start",
        "// selected-qualification-budget-v1:end",
    );
    const packet = "await mkdir(folder, { recursive: false });";
    const packetAt = source.indexOf(packet);
    assert(
        packetAt > startup.end &&
            source.indexOf(packet, packetAt + packet.length) === -1,
        "StartupBeforeActualCreateNewPacket",
    );
    assert(
        /^(?:\s|\/\/[^\n]*(?:\n|$))*$/.test(
            source.slice(startup.end, packetAt),
        ),
        "PacketImmediatelyAfterValidatedStartup",
    );
    const fin = [...source.matchAll(/\bfinally\s*\{/g)];
    assert.equal(fin.length, 1, "UniqueGlobalRestorationFinally");
    const tail = source.slice(fin[0].index + fin[0][0].length),
        end = tail.search(/\n\}(?:\s*\n|$)/);
    assert(end >= 0, "ActualRestorationEnd");
    blocks = {
        limits: source.slice(limitsStart, limitsEnd + 4),
        decoder: helper("checkedSceneBudget", false),
        startup: startup.text,
        packet,
        bounded: helper("boundedBytes"),
        footprint: helper("footprint"),
        measure: helper("measureStorage"),
        git: between(
            "// selected-git-policy-v1:start",
            "// selected-git-policy-v1:end",
        ).text,
        child: between(
            "// selected-child-policy-v1:start",
            "// selected-child-policy-v1:end",
        ).text,
        source: helper("unchangedSource"),
        products: helper("unchangedProducts"),
        restore: tail.slice(0, end),
    };
} catch (error) {
    setup.push({
        stage: "actual-source-extraction",
        classification: "SETUP/UNRUN, not behavioral RED",
        error: String(error?.message ?? error).slice(0, 400),
    });
}

function decoder() {
    try {
        return runInNewContext(
            `(() => { ${blocks.limits}\n${blocks.decoder}\nreturn checkedSceneBudget; })()`,
            {
                Buffer,
                Uint8Array,
                TextDecoder,
                createHash,
                path: path.win32,
                digest: hash,
                assert,
            },
            { timeout: 1000 },
        );
    } catch (error) {
        throw Object.assign(Error(String(error?.message ?? error)), {
            code: "QUALIFICATION_BUDGET_VM_SETUP",
        });
    }
}
// The startup and every later measurement execute their ACTUAL source. Only
// filesystem observations/processes are doubled, with no physical files created.
async function sandbox(options = {}) {
    const reads = [],
        stats = [],
        packets = [],
        spawns = [],
        metadata = [],
        mutations = [];
    const control = { ioError: false };
    const raw = options.bytes ?? encode(record());
    // Include the fixed admission record in the measured base itself. The
    // remaining synthetic file makes the requested aggregate internally exact.
    const recordSize = options.recordSize ?? raw.length;
    const baseBytes = Math.max(
        options.baseBytes ?? 1024,
        options.missing ? 0 : recordSize,
    );
    const dirs = new Map([
        [
            paths.target,
            [{ name: "target.bin", size: options.currentTarget ?? 101 }],
        ],
        [paths.root, [{ name: "source.ts", size: 17 }]],
        [
            paths.base,
            [
                {
                    name: "prior-evidence.bytes",
                    size: baseBytes - (options.missing ? 0 : recordSize),
                },
                ...(options.missing
                    ? []
                    : [
                          {
                              name: path.win32.basename(recordFile),
                              size: recordSize,
                          },
                      ]),
            ],
        ],
        [paths.folder, [{ name: "packet.bytes", size: 0 }]],
    ]);
    async function readdir(directory) {
        if (control.ioError) throw Error("SyntheticInventoryFailure");
        assert(dirs.has(directory), `OnlyFixedSyntheticDirectory:${directory}`);
        return dirs.get(directory).map((entry) => ({ name: entry.name }));
    }
    async function lstat(file) {
        stats.push(file);
        if (file === recordFile) {
            if (options.missing)
                throw Object.assign(Error("SyntheticMissingAdmissionRecord"), {
                    code: "ENOENT",
                });
            return {
                size: recordSize,
                isFile: () => true,
                isDirectory: () => false,
                isSymbolicLink: () => false,
            };
        }
        for (const [parent, entries] of dirs) {
            const entry = entries.find(
                (entry) => path.win32.join(parent, entry.name) === file,
            );
            if (entry)
                return {
                    size: entry.size,
                    isFile: () => true,
                    isDirectory: () => false,
                    isSymbolicLink: () => false,
                };
        }
        throw Object.assign(Error("SyntheticMetadataOutsideFixedRoster"), {
            code: "ENOENT",
        });
    }
    const context = {
        Buffer,
        Uint8Array,
        TextDecoder,
        createHash,
        assert,
        path: path.win32,
        root: paths.root,
        target: paths.target,
        base: paths.base,
        folder: paths.folder,
        executable: paths.executable,
        revision,
        scene: options.scene ?? true,
        literal: options.literal ?? false,
        digest: hash,
        sourceHashes: { fixed: "source-sha" },
        sourceInputs: ["fixed-source"],
        expectedProducts: { fixed: "product-sha" },
        readdir,
        lstat,
        readFile: async (file) => {
            reads.push(file);
            assert.equal(
                file,
                recordFile,
                "ReadOnlySourceDerivedBudgetBasename",
            );
            if (options.missing)
                throw Object.assign(Error("SyntheticMissingAdmissionRecord"), {
                    code: "ENOENT",
                });
            return Buffer.from(raw);
        },
        statfs: async (file) => {
            assert.equal(file, paths.root);
            return { bavail: 10_000_000_000n, bsize: 4096n };
        },
        mkdir: async (file, mode) => {
            mutations.push({ kind: "mkdir", file });
            assert.equal(file, paths.folder);
            assert.equal(mode.recursive, false);
            packets.push(file);
        },
        spawn: (...args) => {
            spawns.push(args);
            throw Object.assign(Error("UnexpectedSyntheticSpawn"), {
                code: "SYNTHETIC_SPAWN",
            });
        },
        setTimeout: () => 1,
        clearTimeout: () => {},
        process: {
            execPath: "D:\\synthetic-tools\\node.exe",
            env: { TEMP: "D:/Dev/_Temp", TMP: "D:/Dev/_Temp" },
        },
        console: { error: () => {}, log: () => {} },
        hashes: async (names) =>
            names.includes("dist/app.js")
                ? { fixed: "product-sha" }
                : { fixed: "source-sha" },
        write: async (name, value) => {
            metadata.push({ name, value: plain(value) });
        },
        writeFile: async (file) => {
            mutations.push({ kind: "writeFile", file });
            throw Error("UnexpectedSyntheticRawWrite");
        },
        buildArgs: () => ["build", "--synthetic-normal-only"],
    };
    const result = {
        api: null,
        error: null,
        reads,
        stats,
        packets,
        spawns,
        metadata,
        mutations,
        dirs,
        control,
    };
    try {
        let pending;
        try {
            pending = runInNewContext(
                `(async () => {
            ${blocks.limits}
            let ownedDrainUnknown=false,storageBreached=false,lastStorage=null,runNumber=0;
            const unknownChildren=[],gitChildren=[],processes=[],artifacts={},reports=[];
            ${blocks.decoder}
            ${blocks.bounded}
            ${blocks.footprint}
            ${blocks.startup}
            ${blocks.packet}
            ${blocks.measure}
            ${blocks.git}
            ${blocks.source}
            let productHashes=expectedProducts;
            ${blocks.products}
            ${blocks.child}
            let originalError=null,restoration=null,workspace=null;
            return {initial:()=>initialStorage,measureStorage,gitRead,run,
                restore:async()=>{${blocks.restore}\nreturn restoration;},
                observe:()=>({storageBreached,lastStorage,ownedDrainUnknown,restoration})};
        })()`,
                context,
                { timeout: 1000 },
            );
        } catch (error) {
            throw Object.assign(Error(String(error?.message ?? error)), {
                code: "QUALIFICATION_BUDGET_VM_SETUP",
            });
        }
        result.api = await pending;
    } catch (error) {
        result.error = error;
        if (
            error?.name === "ReferenceError" ||
            error?.code === "QUALIFICATION_BUDGET_VM_SETUP"
        )
            setup.push({
                stage: "actual-startup-VM-binding",
                classification: "SETUP/UNRUN, not behavioral RED",
                error: String(error.message).slice(0, 400),
            });
    }
    return result;
}
async function check(name, body) {
    authored.push(name);
    if (setup.length) return;
    const priorSetup = setup.length;
    try {
        await body();
        if (setup.length === priorSetup) checks.push({ name, passed: true });
    } catch (error) {
        if (
            error?.name === "ReferenceError" ||
            error?.code === "QUALIFICATION_BUDGET_VM_SETUP"
        )
            setup.push({
                stage: "actual-helper-VM-binding",
                name,
                classification: "SETUP/UNRUN, not behavioral RED",
                error: String(error.message).slice(0, 400),
            });
        else
            checks.push({
                name,
                passed: false,
                error: String(error?.message ?? error).slice(0, 500),
            });
    }
}
function noStartupWork(h) {
    assert.equal(h.packets.length, 0);
    assert.equal(h.spawns.length, 0);
    assert.equal(
        h.mutations.length,
        0,
        "NoRecordRepairOrPacketMutationAttempt",
    );
    assert.equal(h.metadata.length, 0, "NoPreAdmissionMetadataWriteAttempt");
}
async function deniedWork(h) {
    const before = h.spawns.length;
    await assert.rejects(
        h.api.run("D:\\synthetic-tools\\node.exe", ["build.mjs"]),
    );
    await assert.rejects(h.api.gitRead(["status", "--porcelain"]));
    const restored = await h.api.restore();
    assert.equal(
        restored.skipped,
        true,
        "ActualFinallySkipsRestorationAfterLatch",
    );
    assert.equal(restored.reason, "StorageBudgetLatched");
    assert.equal(h.spawns.length, before, "NoLaterChildGitOrRestoreSpawn");
    assert.equal(h.api.observe().storageBreached, true);
}

await check(
    "decoder:exact-closed-return-and-target-case-normalization",
    async () => {
        const fn = decoder(),
            raw = encode(record());
        assert.deepEqual(plain(fn(raw, revision, paths.target, 101)), {
            originalTargetBytes: 11,
            externalEvidenceBytes: 13,
        });
        assert.deepEqual(
            plain(fn(raw, revision, paths.target.toUpperCase(), 101)),
            { originalTargetBytes: 11, externalEvidenceBytes: 13 },
        );
    },
);
await check("decoder:zero-and-safe-original-baseline-boundaries", async () => {
    const fn = decoder();
    for (const value of [0, 101, Number.MAX_SAFE_INTEGER])
        assert.equal(
            fn(
                encode(record({ original_target_bytes: value })),
                revision,
                paths.target,
                value,
            ).originalTargetBytes,
            value,
        );
    assert.equal(
        fn(
            encode(record({ external_evidence_bytes: cumulative })),
            revision,
            paths.target,
            101,
        ).externalEvidenceBytes,
        cumulative,
    );
});
await check("decoder:4096-raw-byte-limit-not-character-count", async () => {
    const fn = decoder(),
        raw = encode(record()),
        padded = Buffer.concat([raw, Buffer.alloc(4096 - raw.length, 32)]);
    assert.equal(padded.length, 4096);
    assert.equal(
        fn(padded, revision, paths.target, 101).originalTargetBytes,
        11,
    );
    assert.throws(() =>
        fn(
            Buffer.concat([padded, Buffer.from(" ")]),
            revision,
            paths.target,
            101,
        ),
    );
    assert.throws(() =>
        fn(
            Buffer.concat([raw, Buffer.from([255])]),
            revision,
            paths.target,
            101,
        ),
    );
});
for (const field of Object.keys(record()))
    await check(`decoder:missing-${field}`, async () => {
        const value = record();
        delete value[field];
        assert.throws(() =>
            decoder()(encode(value), revision, paths.target, 101),
        );
    });
for (const field of Object.keys(record()))
    await check(`decoder:duplicate-${field}-even-identical`, async () => {
        const value = record(),
            text = JSON.stringify(value);
        const raw = Buffer.from(
            `{${JSON.stringify(field)}:${JSON.stringify(value[field])},${text.slice(1)}`,
        );
        assert.throws(() => decoder()(raw, revision, paths.target, 101));
    });
await check("decoder:escaped-duplicate-key-and-extra-key-refuse", async () => {
    const text = JSON.stringify(record());
    assert.throws(() =>
        decoder()(
            Buffer.from(`{"\\u0076ersion":1,${text.slice(1)}`),
            revision,
            paths.target,
            101,
        ),
    );
    assert.throws(() =>
        decoder()(
            encode(record({ foreign: true })),
            revision,
            paths.target,
            101,
        ),
    );
    assert.throws(() =>
        decoder()(
            Buffer.from(text.slice(0, -1) + ',"__proto__":1}'),
            revision,
            paths.target,
            101,
        ),
    );
});
for (const [name, value] of [
    ["null", null],
    ["array", []],
    ["nested", { ...record(), external_evidence_bytes: { bytes: 13 } }],
    ["version0", record({ version: 0 })],
    ["version2", record({ version: 2 })],
    ["string-version", record({ version: "1" })],
    ["kind", record({ kind: "foreign" })],
    ["revision", record({ source_revision: "b".repeat(40) })],
    ["revision-uppercase", record({ source_revision: "A".repeat(40) })],
    ["revision-short", record({ source_revision: "a".repeat(39) })],
    ["target-digest", record({ target_path_sha256: "0".repeat(64) })],
    [
        "target-digest-uppercase",
        record({ target_path_sha256: targetHash.toUpperCase() }),
    ],
    ["target-path-substitution", record({ target_path_sha256: paths.target })],
    ["wrong-limit", record({ cumulative_limit_bytes: cumulative - 1 })],
    ["larger-limit", record({ cumulative_limit_bytes: cumulative + 1 })],
    ["string-limit", record({ cumulative_limit_bytes: String(cumulative) })],
])
    await check(`decoder:refuses-${name}`, async () =>
        assert.throws(() =>
            decoder()(encode(value), revision, paths.target, 101),
        ),
    );
for (const field of ["original_target_bytes", "external_evidence_bytes"])
    for (const value of [-1, 0.5, "1", null, Number.MAX_SAFE_INTEGER + 1])
        await check(`decoder:${field}-invalid-${String(value)}`, async () =>
            assert.throws(() =>
                decoder()(
                    encode(record({ [field]: value })),
                    revision,
                    paths.target,
                    101,
                ),
            ),
        );
await check(
    "decoder:original-greater-than-current-and-external-cap-refuse",
    async () => {
        assert.throws(() =>
            decoder()(
                encode(record({ original_target_bytes: 102 })),
                revision,
                paths.target,
                101,
            ),
        );
        assert.throws(() =>
            decoder()(
                encode(record({ external_evidence_bytes: cumulative + 1 })),
                revision,
                paths.target,
                101,
            ),
        );
        assert.throws(() =>
            decoder()(
                encode(record()),
                revision,
                path.win32.join(paths.target, "other"),
                101,
            ),
        );
    },
);
await check(
    "startup:missing-fixed-record-no-packet-or-subsequent-child",
    async () => {
        const h = await sandbox({ missing: true });
        assert(h.error);
        assert.equal(h.api, null);
        noStartupWork(h);
        assert(
            [...h.reads, ...h.stats].includes(recordFile),
            "FixedRevisionDerivedRecordWasRequired",
        );
        assert(h.reads.every((file) => file === recordFile));
    },
);
for (const [name, bytes] of [
    ["malformed", Buffer.from("{")],
    ["foreign-revision", encode(record({ source_revision: "b".repeat(40) }))],
    [
        "duplicate",
        Buffer.from(`{"version":1,${JSON.stringify(record()).slice(1)}`),
    ],
    ["over-cap", Buffer.alloc(4097, 32)],
])
    await check(`startup:${name}-refused-before-packet`, async () => {
        const h = await sandbox({ bytes });
        assert(h.error);
        noStartupWork(h);
    });
await check(
    "startup:oversized-metadata-is-refused-before-reading-record-bytes",
    async () => {
        const h = await sandbox({ recordSize: 4097 });
        assert(h.error);
        assert.equal(h.reads.length, 0);
        noStartupWork(h);
    },
);
await check(
    "startup:record-byte-length-change-refuses-without-packet",
    async () => {
        const h = await sandbox({ recordSize: encode(record()).length - 1 });
        assert(h.error);
        noStartupWork(h);
    },
);
await check(
    "startup:original-target-and-external-plus-base-baselines-are-actual-inputs",
    async () => {
        const h = await sandbox();
        assert.ifError(h.error);
        assert.equal(h.packets.length, 1);
        assert.deepEqual(h.reads, [recordFile]);
        assert.equal(h.spawns.length, 0);
        assert.deepEqual(h.mutations, [{ kind: "mkdir", file: paths.folder }]);
        assert.deepEqual(h.metadata, []);
        const initial = plain(h.api.initial());
        assert.equal(
            initial.target.bytes,
            11,
            "OriginalTargetCannotResetToObserved101",
        );
        assert.equal(
            initial.evidence.bytes,
            13 + 1024,
            "ExternalRootsMustBeAddedToBaseIncludingAdmissionRecord",
        );
        assert.equal(initial.source.bytes, 17);
        h.dirs.set(paths.folder, [{ name: "observed-packet.bytes", size: 23 }]);
        const measured = await h.api.measureStorage();
        assert.equal(measured.targetGrowth, 101 - 11);
        assert.equal(measured.cumulativeEvidence, 13 + 1024 + 23);
    },
);
for (const literal of [false, true])
    await check(
        `startup:legacy-${literal ? "literal" : "default"}-does-not-require-scene-record`,
        async () => {
            const h = await sandbox({ scene: false, literal, missing: true });
            assert.ifError(h.error);
            assert.deepEqual(h.reads, []);
            assert(!h.stats.includes(recordFile));
            assert.equal(h.packets.length, 1);
            assert.equal(h.api.initial().target.bytes, 101);
            assert.equal(h.api.initial().evidence.bytes, 0);
        },
    );
await check(
    "startup:cumulative-admission-exact-expected-reserve-and-plus-one",
    async () => {
        const external = cumulative - 64 * MiB - 1024;
        const at = await sandbox({
            bytes: encode(record({ external_evidence_bytes: external })),
        });
        assert.ifError(at.error);
        assert.equal(at.packets.length, 1);
        assert.equal(at.api.initial().evidence.bytes, cumulative - 64 * MiB);
        const over = await sandbox({
            bytes: encode(record({ external_evidence_bytes: external + 1 })),
        });
        assert(over.error);
        noStartupWork(over);
    },
);
await check(
    "startup:external-plus-base-overflow-refuses-before-packet",
    async () => {
        const h = await sandbox({
            baseBytes: Number.MAX_SAFE_INTEGER,
            bytes: encode(record({ external_evidence_bytes: 1 })),
        });
        assert(h.error);
        noStartupWork(h);
    },
);
await check(
    "measure:original-target-growth-exact-cap-then-permanent-refusal",
    async () => {
        const original = 11,
            current = original + 2 * 1024 ** 3;
        const h = await sandbox({ currentTarget: current });
        assert.ifError(h.error);
        const at = await h.api.measureStorage();
        assert.equal(at.targetGrowth, 2 * 1024 ** 3);
        h.dirs.set(paths.target, [
            { name: "too-much.bytes", size: current + 1 },
        ]);
        await assert.rejects(h.api.measureStorage());
        assert.equal(h.api.observe().storageBreached, true);
        h.dirs.set(paths.target, [
            { name: "later-small.bytes", size: original },
        ]);
        await deniedWork(h);
    },
);
await check(
    "measure:external-base-packet-final-metadata-reserve-is-checked-every-time",
    async () => {
        const external = 400 * MiB,
            base = 40 * MiB;
        const h = await sandbox({
            baseBytes: base,
            bytes: encode(record({ external_evidence_bytes: external })),
        });
        assert.ifError(h.error);
        h.dirs.set(paths.folder, [
            { name: "packet.bytes", size: cumulative - MiB - external - base },
        ]);
        const at = await h.api.measureStorage();
        assert.equal(at.cumulativeEvidence, cumulative - MiB);
        h.dirs.set(paths.folder, [
            {
                name: "packet.bytes",
                size: cumulative - MiB - external - base + 1,
            },
        ]);
        await assert.rejects(h.api.measureStorage());
        assert.equal(h.api.observe().storageBreached, true);
        h.dirs.set(paths.folder, []);
        await deniedWork(h);
    },
);
await check(
    "measure:unsafe-packet-total-and-prior-good-observation-remain-latched",
    async () => {
        const h = await sandbox();
        assert.ifError(h.error);
        await h.api.measureStorage();
        const known = plain(h.api.observe().lastStorage);
        h.dirs.set(paths.folder, [
            { name: "max.bytes", size: Number.MAX_SAFE_INTEGER },
            { name: "overflow.bytes", size: 1 },
        ]);
        await assert.rejects(h.api.measureStorage());
        assert.equal(h.api.observe().storageBreached, true);
        assert.equal(h.api.observe().lastStorage.unavailable, true);
        assert.deepEqual(plain(h.api.observe().lastStorage.lastKnown), known);
        h.dirs.set(paths.folder, []);
        await deniedWork(h);
    },
);
await check(
    "measure:failed-inventory-never-reopens-work-after-a-good-later-observation",
    async () => {
        const h = await sandbox();
        assert.ifError(h.error);
        await h.api.measureStorage();
        const known = plain(h.api.observe().lastStorage);
        h.control.ioError = true;
        await assert.rejects(h.api.measureStorage());
        h.control.ioError = false;
        assert.equal(h.api.observe().lastStorage.unavailable, true);
        assert.deepEqual(plain(h.api.observe().lastStorage.lastKnown), known);
        await assert.rejects(h.api.measureStorage());
        await deniedWork(h);
    },
);

assert.equal(
    hash(await readFile(sourceUrl, "utf8")),
    hash(source),
    "ActualLauncherSourceUnchanged",
);
assert.equal(authored.length, 61, "FrozenFiniteQualificationBudgetCaseRoster");
const report = {
    version: 1,
    kind: "d07_selected_scene_qualification_budget_first_v1",
    contractSource:
        "88642b82 private decoder/startup and original-baseline binding",
    sourceSHA256: hash(source),
    extractedSHA256: blocks
        ? Object.fromEntries(
              Object.entries(blocks).map(([name, text]) => [name, hash(text)]),
          )
        : null,
    setup,
    authored: authored.length,
    passed: checks.filter((item) => item.passed).length,
    failed: checks.filter((item) => !item.passed).length,
    checks,
    simulation:
        "actual trusted launcher decoder/startup/footprint/measureStorage/Git/child/finally; fixed synthetic observations only",
    osChildExecution: false,
    nativeIpc: false,
    rendering: false,
    modelExecution: false,
    limits: [
        "No launcher import or top-level execution, real child, directory creation, disk measurement, elapsed timeout, OS probe or asset access",
        "Initial source-authority Git checks precede this source-bound admission; no zero-Git claim for the complete launcher",
        "Checked metadata and SHA binding are consistency checks, not authenticated origin or an execution grant",
        "Old155 policy tests remain unchanged; positive process/unknown-child behavior is qualified separately",
        "Admission-record provenance hash attachment and actual retained external-root roster still require source/evidence review",
        "No real512MiB or2GiB allocations; boundary sizes are finite synthetic metadata observations",
    ],
};
console.log(JSON.stringify(report));
if (setup.length || report.failed) process.exitCode = 1;
