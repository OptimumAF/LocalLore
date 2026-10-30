// Independent D08 FIRST. SOURCE ONLY / UNRUN at freeze; missing seams are SETUP.
// Actual private launcher blocks run with disclosed memory-only dependencies.
// No OS child, fixture, image, native application, Rust execution or disk quota.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { runInNewContext } from "node:vm";
import path from "node:path";

const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const plain = (value) => JSON.parse(JSON.stringify(value));
const MiB = 1024 ** 2,
    revision = "a".repeat(40);
const pagingLabels = [
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
const browserLabels = [
    "catalog",
    "root",
    "child",
    "observer",
    "enlarged-wide",
    "enlarged-narrow",
].map((name) => `d08-browser-${name}`);
const paths = Object.freeze({
    root: "D:\\virtual-d08\\source",
    base: "D:\\virtual-d08\\base",
    target: "D:\\virtual-d08\\target",
    folder: "D:\\virtual-d08\\base\\p-fixed",
    executable: "D:\\virtual-d08\\target\\debug\\locallore-desktop-spike.exe",
});
const setup = [],
    cases = [],
    results = [];
const register = (group, name, body) => cases.push({ group, name, body });
const sources = {};
for (const [name, relative] of Object.entries({
    launcher: "./v2-inspector-paging-harness.mjs",
    native: "./src-tauri/src/v2_inspection_paging_harness.rs",
    harness: "./src-tauri/src/harness.rs",
})) {
    try {
        sources[name] = await readFile(
            new URL(relative, import.meta.url),
            "utf8",
        );
    } catch (cause) {
        setup.push({
            stage: name,
            error: String(cause?.code ?? "Unavailable"),
            classification: "UNRUN_SETUP",
        });
    }
}
function between(text, start, end) {
    const first = text.indexOf(start),
        last = text.indexOf(end, first + start.length);
    assert(
        first >= 0 &&
            last > first &&
            text.indexOf(start, first + start.length) < 0 &&
            text.indexOf(end, last + end.length) < 0,
        `UniqueActualBlock:${start}`,
    );
    return text.slice(first + start.length, last);
}
let blocks;
if (!setup.length)
    try {
        const source = sources.launcher;
        blocks = {
            mode: between(
                source,
                "// d08-browser-mode-policy-v1:start",
                "// d08-browser-mode-policy-v1:end",
            ),
            budget: between(
                source,
                "// d05-paging-budget-policy-v1:start",
                "// d05-paging-budget-policy-v1:end",
            ),
            process: between(
                source,
                "// d05-paging-process-policy-v1:start",
                "// d05-paging-process-policy-v1:end",
            ),
        };
        for (const helper of ["pagingLauncherMode", "pagingLauncherPlan"])
            assert.match(
                blocks.mode,
                new RegExp(`\\bfunction\\s+${helper}\\s*\\(`),
            );
        const after =
            source.indexOf("// d05-paging-budget-policy-v1:end") +
            "// d05-paging-budget-policy-v1:end".length;
        const next = source.indexOf("const write", after);
        assert(next > after, "ActualPacketCreationBoundary");
        blocks.packet = source.slice(after, next);
        assert.match(blocks.packet, /await\s+mkdir\(folder/);
        const nativeStart = source.search(/await\s+run\(executable,\s*\[\]/);
        const nativeEnd = source.indexOf("\n    });", nativeStart);
        assert(
            nativeStart >= 0 && nativeEnd > nativeStart,
            "ActualClosedNativeCaller",
        );
        blocks.nativeCall = source.slice(
            nativeStart,
            nativeEnd + "\n    });".length,
        );
        for (const helper of [
            "validate_browser_flag",
            "timeline_browser_label",
            "reserve_with_limit",
        ])
            assert.match(
                sources.native + sources.harness,
                new RegExp(`\\bfn\\s+${helper}\\b`),
                `FutureNativeHelper:${helper}`,
            );
    } catch (cause) {
        setup.push({
            stage: "future-private-seams",
            error: String(cause?.message ?? cause).slice(0, 400),
            classification: "UNRUN_SETUP; not behavioral RED",
        });
    }

function modeApi() {
    return runInNewContext(
        `(()=>{${blocks.mode}\nreturn {pagingLauncherMode,pagingLauncherPlan};})()`,
        { path: path.win32, process: { argv: ["node", "launcher"], env: {} } },
        { timeout: 1000 },
    );
}
function limitsFor(mode) {
    const plan = plain(modeApi().pagingLauncherPlan(mode));
    return {
        targetGrowth: 2 * 1024 ** 3,
        sourceGrowth: 128 * MiB,
        entries: 2_000_000,
        cumulativeEvidence: 640 * MiB,
        artifacts: plan.artifacts,
        expectedEvidence: plan.expectedEvidence,
        pagingEvidence: plan.pagingEvidence,
    };
}
function record(mode, patch = {}) {
    return {
        version: 1,
        kind:
            mode === "paging"
                ? "d05_v2_inspector_paging_budget_v1"
                : "d08_domain2_timeline_browser_budget_v1",
        source_revision: revision,
        target_path_sha256: hash(
            Buffer.from(path.win32.resolve(paths.target).toLowerCase(), "utf8"),
        ),
        original_target_bytes: 1000,
        external_evidence_bytes: mode === "paging" ? 480 * MiB : 520 * MiB,
        d05_external_evidence_bytes: mode === "paging" ? 0 : 80 * MiB,
        cumulative_limit_bytes: 640 * MiB,
        ...patch,
    };
}
function sandbox(mode, options = {}) {
    const plan = plain(modeApi().pagingLauncherPlan(mode)),
        limits = limitsFor(mode),
        reads = [],
        mkdirs = [],
        git = [],
        children = [];
    const control = {
        base: options.base ?? 1 * MiB,
        packet: 0,
        target: 1000,
        source: 100,
        broken: false,
    };
    const bytes =
        options.bytes ??
        Buffer.from(JSON.stringify(record(mode, options.patch ?? {})));
    const context = {
        path: path.win32,
        Buffer,
        TextDecoder,
        Date,
        Promise,
        mode,
        plan,
        limits,
        revision,
        root: paths.root,
        base: paths.base,
        target: paths.target,
        folder: paths.folder,
        executable: paths.executable,
        digest: hash,
        statfs: async () => ({ bavail: 10n ** 12n, bsize: 1n }),
        footprint: async (location) => {
            if (control.broken) throw Error("SyntheticInventoryFailure");
            const key =
                location === paths.base
                    ? "base"
                    : location === paths.folder
                      ? "packet"
                      : location === paths.target
                        ? "target"
                        : "source";
            return { entries: 1, bytes: control[key] };
        },
        boundedBytes: async (file, maximum) => {
            reads.push({ file, maximum });
            if (options.missing) throw Error("SyntheticMissingRecord");
            return bytes;
        },
        mkdir: async (file) => mkdirs.push(file),
        gitRead: async (args) => {
            git.push(args);
            return args[0] === "rev-parse" ? revision : "";
        },
        hashes: async () => ({ fixed: "same" }),
        sourcePaths: ["fixed"],
        sourceHashes: { fixed: "same" },
        productHashes: { fixed: "same" },
        spawn: () => {
            children.push("unexpected");
            throw Error("NoChildNeededForStorageOracle");
        },
        process: { env: {}, execPath: "D:\\virtual-installed\\node.exe" },
        write: async () => {},
        writeFile: async () => {},
        setTimeout: () => 1,
        clearTimeout: () => {},
    };
    const api = runInNewContext(
        `(async()=>{
        let ownedDrainUnknown=false,storageBreached=false,lastStorage=null,runNumber=0;
        const unknownChildren=[],gitChildren=[],processes=[];
        ${blocks.budget}
        ${blocks.packet}
        ${blocks.process}
        return {initialStorage,checkedPagingBudget,measureStorage,run,
            observe:()=>({ownedDrainUnknown,storageBreached,lastStorage})};
    })()`,
        context,
        { timeout: 1000 },
    );
    return { ready: api, control, reads, mkdirs, git, children };
}

register("mode", "empty-arguments-preserve-paging", () =>
    assert.equal(modeApi().pagingLauncherMode([]), "paging"),
);
register("mode", "one-literal-selects-browser", () =>
    assert.equal(
        modeApi().pagingLauncherMode(["--timeline-browser-v1"]),
        "timeline-browser",
    ),
);
for (const args of [
    ["--timeline-browser-v1", "--timeline-browser-v1"],
    ["--timeline-browser-v1", "x"],
    ["--timeline-browser-v1=1"],
    ["--timeline-browser-v1 "],
    ["--bounded"],
    ["x"],
    [""],
    ["--timeline-browser-v1", "--scene"],
    ["--scene", "--timeline-browser-v1"],
])
    register("mode", `closed-arguments:${JSON.stringify(args)}`, () =>
        assert.throws(() => modeApi().pagingLauncherMode(args)),
    );
for (const mode of ["paging", "timeline-browser"])
    register("plan", `exact-fixed-plan:${mode}`, () => {
        const plan = plain(modeApi().pagingLauncherPlan(mode)),
            browser = mode !== "paging";
        assert.deepEqual(
            Object.keys(plan).sort(),
            [
                "budgetKind",
                "budgetPrefix",
                "artifacts",
                "expectedEvidence",
                "pagingEvidence",
                "reportMode",
                "labels",
            ].sort(),
        );
        assert.equal(
            plan.budgetKind,
            browser
                ? "d08_domain2_timeline_browser_budget_v1"
                : "d05_v2_inspector_paging_budget_v1",
        );
        assert.equal(
            plan.budgetPrefix,
            browser
                ? "d08-domain2-timeline-browser-budget-v1-"
                : "d05-v2-inspector-paging-budget-v1-",
        );
        assert.equal(plan.artifacts, (browser ? 20 : 64) * MiB);
        assert.equal(plan.expectedEvidence, (browser ? 20 : 64) * MiB);
        assert.equal(plan.pagingEvidence, (browser ? 32 : 128) * MiB);
        assert.equal(
            plan.reportMode,
            browser ? "domain2_timeline_browser_v1" : "v2_inspector_paging_v1",
        );
        assert.deepEqual(plan.labels, browser ? browserLabels : pagingLabels);
    });
for (const mode of [
    "",
    "scene",
    "timeline-browser-v1",
    "--timeline-browser-v1",
])
    register("plan", `closed-plan:${mode}`, () =>
        assert.throws(() => modeApi().pagingLauncherPlan(mode)),
    );

for (const mode of ["paging", "timeline-browser"])
    register("admission", `actual-record-file-and-caps:${mode}`, async () => {
        const h = sandbox(mode),
            api = await h.ready;
        assert.equal(h.reads.length, 1);
        assert.equal(h.reads[0].maximum, 4096);
        assert.equal(
            path.win32.basename(h.reads[0].file),
            plain(modeApi().pagingLauncherPlan(mode)).budgetPrefix +
                revision +
                ".json",
        );
        assert.deepEqual(h.mkdirs, [paths.folder]);
        assert.equal(api.initialStorage.pagingEvidence.bytes, 1 * MiB);
        assert.equal(
            api.initialStorage.evidence.bytes,
            (mode === "paging" ? 481 : 601) * MiB,
        );
        assert.equal(api.initialStorage.target.bytes, 1000);
    });
register(
    "admission",
    "browser-old-D05-charged-once-in-joint-never-new-base",
    async () => {
        const h = sandbox("timeline-browser", {
                patch: { d05_external_evidence_bytes: 83 * MiB },
            }),
            api = await h.ready;
        assert.equal(api.initialStorage.pagingEvidence.bytes, MiB);
        assert.equal(api.initialStorage.evidence.bytes, 604 * MiB);
    },
);
register(
    "admission",
    "legacy-D05-external-still-counts-toward-old-base",
    async () => {
        const h = sandbox("paging", {
                patch: { d05_external_evidence_bytes: 9 * MiB },
            }),
            api = await h.ready;
        assert.equal(api.initialStorage.pagingEvidence.bytes, 10 * MiB);
        assert.equal(api.initialStorage.evidence.bytes, 490 * MiB);
    },
);
for (const [mode, patch] of [
    ["paging", { external_evidence_bytes: 512 * MiB + 1 }],
    ["paging", { kind: "d08_domain2_timeline_browser_budget_v1" }],
    ["timeline-browser", { kind: "d05_v2_inspector_paging_budget_v1" }],
    ["timeline-browser", { cumulative_limit_bytes: 640 * MiB + 1 }],
    ["timeline-browser", { source_revision: "b".repeat(40) }],
    ["timeline-browser", { target_path_sha256: "0".repeat(64) }],
    ["timeline-browser", { external_evidence_bytes: 620 * MiB }],
    [
        "timeline-browser",
        { d05_external_evidence_bytes: Number.MAX_SAFE_INTEGER },
    ],
])
    register(
        "admission",
        `refuse-before-packet:${mode}:${JSON.stringify(patch)}`,
        async () => {
            const h = sandbox(mode, { patch });
            await assert.rejects(h.ready);
            assert.deepEqual(h.mkdirs, []);
            assert.deepEqual(h.children, []);
        },
    );
for (const mode of ["paging", "timeline-browser"])
    register("admission", `missing-record-no-packet:${mode}`, async () => {
        const h = sandbox(mode, { missing: true });
        await assert.rejects(h.ready);
        assert.deepEqual(h.mkdirs, []);
    });
register("admission", "browser-exact20MiB-reserve-fits-base32MiB", async () => {
    await sandbox("timeline-browser", { base: 12 * MiB }).ready;
});
register(
    "admission",
    "browser-one-byte-short-reserve-refuses-before-packet",
    async () => {
        const h = sandbox("timeline-browser", { base: 12 * MiB + 1 });
        await assert.rejects(h.ready);
        assert.deepEqual(h.mkdirs, []);
    },
);
register("decoder", "default-four-arguments-remain-legacy", async () => {
    const h = sandbox("paging"),
        api = await h.ready;
    assert.deepEqual(
        plain(
            api.checkedPagingBudget(
                Buffer.from(JSON.stringify(record("paging"))),
                revision,
                paths.target,
                1000,
            ),
        ),
        {
            originalTargetBytes: 1000,
            externalEvidenceBytes: 480 * MiB,
            d05ExternalEvidenceBytes: 0,
        },
    );
    assert.throws(() =>
        api.checkedPagingBudget(
            Buffer.from(JSON.stringify(record("timeline-browser"))),
            revision,
            paths.target,
            1000,
        ),
    );
});
register(
    "decoder",
    "explicit-browser-allows-over512-only-under-joint-admission",
    async () => {
        const api = await sandbox("timeline-browser").ready;
        assert.equal(
            api.checkedPagingBudget(
                Buffer.from(JSON.stringify(record("timeline-browser"))),
                revision,
                paths.target,
                1000,
                "timeline-browser",
            ).externalEvidenceBytes,
            520 * MiB,
        );
    },
);
register("decoder", "browser-duplicate-key-stays-refused", async () => {
    const bytes = Buffer.from(
        JSON.stringify(record("timeline-browser")).replace(
            '"version":1',
            '"version":1,"version":1',
        ),
    );
    const h = sandbox("timeline-browser", { bytes });
    await assert.rejects(h.ready);
    assert.deepEqual(h.mkdirs, []);
});

register(
    "storage",
    "browser-exact-postchild-packet-and-base-metadata-reserve-fit",
    async () => {
        const h = sandbox("timeline-browser", { base: 12 * MiB }),
            api = await h.ready;
        h.control.packet = 19 * MiB;
        const measured = await api.measureStorage();
        assert.equal(measured.packet.bytes, 19 * MiB);
        assert.equal(measured.pagingEvidence, 31 * MiB);
    },
);
for (const [name, packet] of [
    ["packet-one-byte-over-metadata-reserve", 19 * MiB + 1],
    ["base-and-packet-overlap", 33 * MiB],
    ["joint-and-packet-overlap", 19 * MiB + 1],
])
    register("storage", `browser-permanent:${name}`, async () => {
        const patch =
            name === "joint-and-packet-overlap"
                ? {
                      external_evidence_bytes: 620 * MiB,
                      d05_external_evidence_bytes: 0,
                  }
                : {};
        const h = sandbox("timeline-browser", { base: 0, patch }),
            api = await h.ready;
        // Joint/base failures overlap packet overflow under these coupled fixed
        // caps. Do not report isolated runtime coverage for a redundant bound.
        h.control.packet = packet;
        await assert.rejects(api.measureStorage());
        assert.equal(api.observe().storageBreached, true);
        h.control.packet = 0;
        h.control.base = 0;
        await assert.rejects(api.measureStorage());
        const before = h.git.length;
        await assert.rejects(api.run("node", []));
        assert.equal(h.git.length, before);
        assert.deepEqual(h.children, []);
    });
register(
    "storage",
    "browser-inventory-failure-stays-unavailable-and-sticky",
    async () => {
        const h = sandbox("timeline-browser"),
            api = await h.ready;
        h.control.broken = true;
        await assert.rejects(api.measureStorage());
        assert.equal(api.observe().lastStorage.unavailable, true);
        h.control.broken = false;
        await assert.rejects(api.measureStorage());
    },
);
register("storage", "legacy-retains64MiB-packet-and128MiB-base", async () => {
    const h = sandbox("paging"),
        api = await h.ready;
    h.control.packet = 30 * MiB;
    const observed = await api.measureStorage();
    assert.equal(observed.packet.bytes, 30 * MiB);
    assert.equal(observed.pagingEvidence, 31 * MiB);
});

for (const mode of ["paging", "timeline-browser"])
    register("native-caller", `actual-fixed-environment:${mode}`, async () => {
        const calls = [],
            workspace = "D:\\virtual-d08\\base\\p-fixed\\workspace",
            plannedWorkspace = {
                workspace,
                database: path.win32.join(workspace, "stories-v1.sqlite"),
            };
        await runInNewContext(
            `(async()=>{${blocks.nativeCall}})()`,
            {
                mode,
                plan: plain(modeApi().pagingLauncherPlan(mode)),
                workspace,
                plannedWorkspace,
                path: path.win32,
                executable: paths.executable,
                run: async (...args) => calls.push(args),
            },
            { timeout: 1000 },
        );
        assert.equal(calls.length, 1);
        assert.equal(calls[0][0], paths.executable);
        assert.deepEqual(plain(calls[0][1]), []);
        const env = plain(calls[0][2]);
        assert.deepEqual(
            Object.keys(env).sort(),
            [
                "LOCALLORE_D02_HARNESS",
                "LOCALLORE_D05_INSPECTOR_PAGING_HARNESS",
                "LOCALLORE_TEST_WORKSPACE",
                "LOCALLORE_D02_ARTIFACT_DIR",
                ...(mode === "timeline-browser"
                    ? ["LOCALLORE_D08_TIMELINE_BROWSER_HARNESS"]
                    : []),
            ].sort(),
        );
        assert.equal(env.LOCALLORE_TEST_WORKSPACE, plannedWorkspace.database);
        assert.equal(
            env.LOCALLORE_D02_ARTIFACT_DIR,
            path.win32.join(workspace, "evidence"),
        );
        for (const key of Object.keys(env).filter((key) =>
            key.endsWith("HARNESS"),
        ))
            assert.equal(env[key], "1");
    });
register(
    "source-controls",
    "argument-plan-before-first-child-or-packet",
    () => {
        const start = sources.launcher.indexOf(
            "// d08-browser-mode-policy-v1:start",
        );
        const call = sources.launcher.indexOf(
            "pagingLauncherMode(process.argv.slice(2))",
        );
        assert(start >= 0 && call > start, "ActualClosedModeCaller");
        assert(call < sources.launcher.indexOf('await gitRead(["rev-parse"'));
        assert(call < sources.launcher.indexOf("await mkdir(folder"));
    },
);
register(
    "source-controls",
    "fixture-private-browser-flag-validation-precedes-legacy-mode",
    () => {
        const source = sources.native,
            runtime = source.slice(
                source.indexOf("fn runtime_mode"),
                source.indexOf("pub fn active"),
            );
        assert.match(runtime, /validate_browser_flag\s*\(/);
        assert(
            runtime.indexOf("validate_browser_flag") <
                runtime.indexOf("validate_mode("),
        );
        const missingPagingReturn = runtime.indexOf("let Some(selector)");
        if (missingPagingReturn >= 0)
            assert(
                runtime.indexOf("validate_browser_flag") < missingPagingReturn,
                "BrowserOnlyRequestMustNotDisappearAtMissingPagingEarlyReturn",
            );
        const requested = source.slice(
            source.indexOf("pub fn requested"),
            source.indexOf("fn runtime_mode"),
        );
        assert.match(requested, /LOCALLORE_D08_TIMELINE_BROWSER_HARNESS/);
        // Source-call coverage ONLY. No malformed browser flag Rust execution claim.
    },
);
register(
    "source-controls",
    "real-writer-selects-eight-MiB-and-keeps-old-limit",
    () => {
        const source = sources.harness,
            write = source.slice(
                source.indexOf("fn write(&self"),
                source.indexOf("fn checked_json"),
            );
        assert.match(write, /timeline_browser_active\s*\(/);
        assert.match(write, /reserve_with_limit\s*\(/);
        assert.match(write, /MAX_TIMELINE_BROWSER_ARTIFACT_BYTES/);
        assert.match(write, /budget\.reserve\(bytes\.len\(\)\)/);
    },
);

for (const item of cases) {
    if (setup.length) break;
    try {
        await item.body();
        results.push({ group: item.group, name: item.name, passed: true });
    } catch (cause) {
        results.push({
            group: item.group,
            name: item.name,
            passed: false,
            error: String(cause?.message ?? cause).slice(0, 300),
        });
    }
}
const report = {
    version: 1,
    kind: "d08_timeline_browser_native_mode_first_v1",
    sourceOnlyAtFreeze: true,
    authored: cases.length,
    executed: results.length,
    passed: results.filter((item) => item.passed).length,
    failed: results.filter((item) => !item.passed).length,
    setup,
    sourceSHA256: Object.fromEntries(
        Object.entries(sources).map(([name, text]) => [name, hash(text)]),
    ),
    checks: results,
    limitations: [
        "Actual launcher blocks; VM paths/files/children/budget observations are memory doubles, never OS or runtime admission.",
        "Native flag call/order and writer selection are source controls; malformed browser flags are not Rust runtime-qualified by this checker.",
        "No generated bundle/report file; stdout only<=64KiB. Root captures it in the admitted output directory.",
        "No D05 cohort rerun, image, canonical fixture, actual timer/child, model, SDK, native IPC or whole-D08 acceptance.",
    ],
};
const output = JSON.stringify(report);
assert(Buffer.byteLength(output + "\n") <= 65536, "BoundedFirstReport");
console.log(output);
if (setup.length || report.failed || report.executed !== report.authored)
    process.exitCode = 1;
