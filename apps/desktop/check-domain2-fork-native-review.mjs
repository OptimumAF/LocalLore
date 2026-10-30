// Independent SOURCE FIRST 7c8f3417; author UNRUN. Actual launcher JS in VM;
// memory-only filesystem/Git/child observations. Native/TS checks are disclosed
// source controls, not Rust execution, IPC, rendering or resource admission.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { runInNewContext } from "node:vm";
import path from "node:path";
assert.equal(process.argv.length, 2, "ClosedForkNativeReviewArguments");
const hash = (v) => createHash("sha256").update(v).digest("hex"),
    plain = (v) => JSON.parse(JSON.stringify(v));
const MiB = 1048576,
    revision = "a".repeat(40),
    source = {},
    setup = [],
    cases = [],
    results = [];
const P = {
    root: "D:\\virtual-fork\\source",
    base: "D:\\virtual-fork\\evidence",
    target: "D:\\virtual-fork\\target",
    packet: "D:\\virtual-fork\\evidence\\p-00000000-0000-4000-8000-000000000001",
    exe: "D:\\virtual-fork\\target\\debug\\locallore-desktop-spike.exe",
};
const labels = [
    "catalog",
    "rejected",
    "pending",
    "preauthor",
    "authored",
    "recovered",
    "enlarged",
].map((s) => `d08-fork-${s}`);
const test = (need, name, run) => cases.push({ need, name, run });
function block(text, start, end) {
    const a = text.indexOf(start),
        b = text.indexOf(end, a + start.length);
    if (a < 0 || b <= a || text.indexOf(start, a + start.length) >= 0)
        throw Error(`UNRUN_SETUP:ActualBlock:${start}`);
    return text.slice(a + start.length, b);
}
const files = {
    launcher: "v2-inspector-paging-harness.mjs",
    native: "src-tauri/src/domain2_fork_harness.rs",
    fork: "src-tauri/src/fork_harness.rs",
    harness: "src-tauri/src/harness.rs",
    main: "src-tauri/src/main.rs",
    frontend: "ui/main.tsx",
    journey: "ui/domain2-fork-native-journeys.ts",
    build: "build.mjs",
    verifier: "verify-frontend.mjs",
};
const missing = {};
for (const [name, file] of Object.entries(files)) {
    try {
        source[name] = await readFile(new URL(file, import.meta.url), "utf8");
    } catch (e) {
        missing[name] = String(e.code ?? "Unavailable");
    }
}
let B = null;
try {
    if (missing.launcher) throw Error("UNRUN_SETUP:LauncherMissing");
    const s = source.launcher;
    const limitsStart = s.indexOf("const limits = Object.freeze({"),
        limitsEnd = s.indexOf("\n});", limitsStart);
    assert(
        limitsStart >= 0 && limitsEnd > limitsStart,
        "UNRUN_SETUP:ActualLimits",
    );
    const start = s.search(/await\s+run\(executable,\s*\[\]/),
        end = s.indexOf("\n    });", start);
    assert(start >= 0 && end > start, "UNRUN_SETUP:ActualNativeCaller");
    B = {
        mode: block(
            s,
            "// d08-browser-mode-policy-v1:start",
            "// d08-browser-mode-policy-v1:end",
        ),
        budget: block(
            s,
            "// d05-paging-budget-policy-v1:start",
            "// d05-paging-budget-policy-v1:end",
        ),
        process: block(
            s,
            "// d05-paging-process-policy-v1:start",
            "// d05-paging-process-policy-v1:end",
        ),
        workspace: block(
            s,
            "// d05-paging-path-policy-v1:start",
            "// d05-paging-path-policy-v1:end",
        ),
        limits: s.slice(limitsStart, limitsEnd + 4),
        nativeCall: s.slice(start, end + "\n    });".length),
    };
} catch (e) {
    setup.push({
        stage: "launcher",
        classification: "UNRUN_SETUP",
        error: String(e).slice(0, 300),
    });
}
function modeApi() {
    return runInNewContext(
        `(()=>{${B.mode}\nreturn {pagingLauncherMode,pagingLauncherPlan};})()`,
        {},
        { timeout: 1000 },
    );
}
function limitsFor(mode) {
    const plan = plain(modeApi().pagingLauncherPlan(mode));
    return plain(
        runInNewContext(
            `(()=>{${B.limits};return limits;})()`,
            { mode, plan },
            { timeout: 1000 },
        ),
    );
}
function record(mode = "domain2-fork", patch = {}) {
    return {
        version: mode === "timeline-browser" ? 3 : 1,
        kind:
            mode === "domain2-fork"
                ? "d08_domain2_fork_budget_v1"
                : mode === "paging"
                  ? "d05_v2_inspector_paging_budget_v1"
                  : "d08_domain2_timeline_browser_budget_v3",
        source_revision: revision,
        target_path_sha256: hash(
            Buffer.from(path.win32.resolve(P.target).toLowerCase()),
        ),
        original_target_bytes: 1000,
        external_evidence_bytes: 500 * MiB,
        d05_external_evidence_bytes: 20 * MiB,
        cumulative_limit_bytes: (mode === "paging" ? 640 : 660) * MiB,
        ...patch,
    };
}
function sandbox(mode = "domain2-fork", options = {}) {
    const plan = plain(modeApi().pagingLauncherPlan(mode)),
        limits = limitsFor(mode),
        reads = [],
        mkdirs = [],
        git = [],
        children = [];
    const control = {
        base: options.base ?? MiB,
        packet: 0,
        target: 1000,
        source: 100,
        broken: false,
    };
    const bytes =
        options.bytes ??
        Buffer.from(JSON.stringify(record(mode, options.patch)));
    const context = {
        mode,
        plan,
        limits,
        revision,
        path: path.win32,
        Buffer,
        TextDecoder,
        root: P.root,
        base: P.base,
        target: P.target,
        folder: P.packet,
        executable: P.exe,
        digest: hash,
        statfs: async () => ({ bavail: 10n ** 12n, bsize: 1n }),
        footprint: async (location) => {
            if (control.broken) throw Error("SyntheticInventory");
            const key =
                location === P.base
                    ? "base"
                    : location === P.packet
                      ? "packet"
                      : location === P.target
                        ? "target"
                        : "source";
            return { entries: 1, bytes: control[key] };
        },
        boundedBytes: async (file, maximum) => {
            reads.push({ file, maximum });
            if (options.missing) throw Error("MissingRecord");
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
            children.push("forbidden");
            throw Error("NoChildForInventoryOracle");
        },
        process: { env: {}, execPath: "D:\\installed-tool\\node.exe" },
        write: async () => {},
        writeFile: async () => {},
        setTimeout: () => 1,
        clearTimeout: () => {},
    };
    const packet = source.launcher.slice(
        source.launcher.indexOf("// d05-paging-budget-policy-v1:end") +
            "// d05-paging-budget-policy-v1:end".length,
        source.launcher.indexOf("const write ="),
    );
    const ready = runInNewContext(
        `(async()=>{let ownedDrainUnknown=false,storageBreached=false,lastStorage=null,runNumber=0;const unknownChildren=[],gitChildren=[],processes=[];${B.budget}\n${packet}\n${B.process}\nreturn {initialStorage,measureStorage,checkedPagingBudget,run,observe:()=>({storageBreached,lastStorage})};})()`,
        context,
        { timeout: 1000 },
    );
    return { ready, control, reads, mkdirs, git, children };
}
test("launcher", "actual-closed-three-mode-arguments", () => {
    const a = modeApi();
    assert.equal(a.pagingLauncherMode([]), "paging");
    assert.equal(
        a.pagingLauncherMode(["--timeline-browser-v1"]),
        "timeline-browser",
    );
    assert.equal(a.pagingLauncherMode(["--domain2-fork-v1"]), "domain2-fork");
    for (const args of [
        ["--domain2-fork-v1", "--timeline-browser-v1"],
        ["--domain2-fork-v1", "--scene"],
        ["--domain2-fork-v1", "--domain2-fork-v1"],
        ["--domain2-fork-v1=1"],
        ["--Domain2-fork-v1"],
        ["--domain2-fork-v1 "],
        [""],
    ])
        assert.throws(() => a.pagingLauncherMode(args));
});
test("launcher", "actual-fork-plan-closed-fields-no-resource-admission", () => {
    const p = plain(modeApi().pagingLauncherPlan("domain2-fork"));
    assert.deepEqual(p, {
        budgetKind: "d08_domain2_fork_budget_v1",
        budgetPrefix: "d08-domain2-fork-budget-v1-",
        artifacts: 20 * MiB,
        expectedEvidence: 20 * MiB,
        pagingEvidence: 32 * MiB,
        reportMode: "domain2_fork_v1",
        labels,
    });
    assert.deepEqual(limitsFor("domain2-fork"), {
        targetGrowth: 2 * 1024 ** 3,
        sourceGrowth: 128 * MiB,
        artifacts: 20 * MiB,
        entries: 2000000,
        cumulativeEvidence: 660 * MiB,
        expectedEvidence: 20 * MiB,
        pagingEvidence: 32 * MiB,
    });
});
test("launcher", "legacy-paging-and-browser-v3-plans-unchanged", () => {
    for (const [mode, kind, prefix, packet, base, joint, growth, count] of [
        [
            "paging",
            "d05_v2_inspector_paging_budget_v1",
            "d05-v2-inspector-paging-budget-v1-",
            64,
            128,
            640,
            2,
            20,
        ],
        [
            "timeline-browser",
            "d08_domain2_timeline_browser_budget_v3",
            "d08-domain2-timeline-browser-budget-v3-",
            20,
            52,
            660,
            4,
            6,
        ],
    ]) {
        const p = plain(modeApi().pagingLauncherPlan(mode));
        assert.equal(p.budgetKind, kind);
        assert.equal(p.budgetPrefix, prefix);
        assert.equal(p.artifacts, packet * MiB);
        assert.equal(p.expectedEvidence, packet * MiB);
        assert.equal(p.pagingEvidence, base * MiB);
        assert.equal(p.labels.length, count);
        assert.equal(limitsFor(mode).cumulativeEvidence, joint * MiB);
        assert.equal(limitsFor(mode).targetGrowth, growth * 1024 ** 3);
    }
});
test(
    "launcher",
    "actual-fixed-workspace-mode-prefix-and-legacy-default",
    () => {
        const a = runInNewContext(
                `(()=>{${B.workspace};return {fixedPagingWorkspace};})()`,
                { path: path.win32 },
                { timeout: 1000 },
            ),
            id = "00000000-0000-4000-8000-000000000002";
        for (const mode of ["paging", "timeline-browser", "domain2-fork"]) {
            const expected = path.win32.join(
                    P.packet,
                    (mode === "domain2-fork"
                        ? "d08-domain2-fork-native-"
                        : "d05-v2-inspector-paging-native-") + id,
                ),
                value = {
                    workspace: expected,
                    database: path.win32.join(expected, "stories-v1.sqlite"),
                };
            assert.deepEqual(
                plain(a.fixedPagingWorkspace(P.packet, id, mode)),
                value,
            );
            const start = source.launcher.indexOf(
                    "const plannedWorkspace = fixedPagingWorkspace(",
                ),
                end = source.launcher.indexOf(";", start);
            assert(
                start >= 0 && end > start,
                "UNRUN_SETUP:ActualWorkspaceCaller",
            );
            const actual = runInNewContext(
                `(()=>{${B.workspace}\n${source.launcher.slice(start, end + 1)}\nreturn plannedWorkspace;})()`,
                {
                    path: path.win32,
                    mode,
                    folder: P.packet,
                    randomUUID: () => id,
                },
                { timeout: 1000 },
            );
            assert.deepEqual(
                plain(actual),
                value,
                "ActualStartupUsesClosedMode",
            );
        }
        assert.deepEqual(
            plain(a.fixedPagingWorkspace(P.packet, id)),
            plain(a.fixedPagingWorkspace(P.packet, id, "paging")),
        );
        for (const bad of [
            "",
            "A0000000-0000-4000-8000-000000000002",
            "../escape",
            "00000000-0000-4000-8000-00000000000Z",
        ])
            assert.throws(() =>
                a.fixedPagingWorkspace(P.packet, bad, "domain2-fork"),
            );
        assert.throws(() =>
            a.fixedPagingWorkspace(
                "D:\\" + "p".repeat(240),
                id,
                "domain2-fork",
            ),
        );
    },
);
test("launcher", "actual-eight-field-bound-record-before-packet", async () => {
    const h = sandbox(),
        a = await h.ready;
    assert.equal(h.reads.length, 1);
    assert.equal(h.reads[0].maximum, 4096);
    assert.equal(
        path.win32.basename(h.reads[0].file),
        "d08-domain2-fork-budget-v1-" + revision + ".json",
    );
    assert.deepEqual(h.mkdirs, [P.packet]);
    assert.equal(a.initialStorage.target.bytes, 1000);
    assert.equal(a.initialStorage.evidence.bytes, 521 * MiB);
    assert.equal(a.initialStorage.pagingEvidence.bytes, MiB);
});
test("launcher", "actual-record-refusals-never-mkdir-or-child", async () => {
    const patches = [
        { version: 2 },
        { kind: "d08_domain2_timeline_browser_budget_v3" },
        { kind: "d05_v2_inspector_paging_budget_v1" },
        { source_revision: "b".repeat(40) },
        { target_path_sha256: "0".repeat(64) },
        { cumulative_limit_bytes: 660 * MiB + 1 },
        { original_target_bytes: 1001 },
        { extra: 1 },
    ];
    for (const patch of patches) {
        const h = sandbox("domain2-fork", { patch });
        await assert.rejects(h.ready);
        assert.deepEqual(h.mkdirs, []);
        assert.deepEqual(h.children, []);
    }
    for (const options of [
        { missing: true },
        {
            bytes: Buffer.from(
                JSON.stringify(record()).replace(
                    '"version":1',
                    '"version":1,"version":1',
                ),
            ),
        },
    ]) {
        const h = sandbox("domain2-fork", options);
        await assert.rejects(h.ready);
        assert.deepEqual(h.mkdirs, []);
    }
});
test(
    "launcher",
    "actual-thirtytwo-group-and-twenty-packet-reservation",
    async () => {
        await sandbox("domain2-fork", { base: 12 * MiB }).ready;
        const h = sandbox("domain2-fork", { base: 12 * MiB + 1 });
        await assert.rejects(h.ready);
        assert.deepEqual(h.mkdirs, []);
        const exact = sandbox("domain2-fork", {
            base: 0,
            patch: {
                external_evidence_bytes: 640 * MiB,
                d05_external_evidence_bytes: 0,
            },
        });
        await exact.ready;
        const over = sandbox("domain2-fork", {
            base: 1,
            patch: {
                external_evidence_bytes: 640 * MiB,
                d05_external_evidence_bytes: 0,
            },
        });
        await assert.rejects(over.ready);
        assert.deepEqual(over.mkdirs, []);
    },
);
test(
    "launcher",
    "actual-sticky-storage-target-and-metadata-ceilings",
    async () => {
        for (const fault of ["target", "packet", "inventory"]) {
            const h = sandbox("domain2-fork", { base: 12 * MiB }),
                a = await h.ready;
            h.control.packet = 19 * MiB;
            assert.equal((await a.measureStorage()).pagingEvidence, 31 * MiB);
            if (fault === "target") h.control.target = 1000 + 2 * 1024 ** 3 + 1;
            if (fault === "packet") h.control.packet++;
            if (fault === "inventory") h.control.broken = true;
            await assert.rejects(a.measureStorage());
            assert(a.observe().storageBreached);
            h.control.target = 1000;
            h.control.packet = 0;
            h.control.broken = false;
            await assert.rejects(a.measureStorage());
            const before = h.git.length;
            await assert.rejects(a.run("node", []));
            assert.equal(h.git.length, before);
            assert.deepEqual(h.children, []);
        }
    },
);
test(
    "launcher",
    "actual-native-caller-only-fork-mode-flag-and-owned-path",
    async () => {
        const plannedWorkspace = {
            workspace: path.win32.join(
                P.packet,
                "d08-domain2-fork-native-00000000-0000-4000-8000-000000000002",
            ),
        };
        plannedWorkspace.database = path.win32.join(
            plannedWorkspace.workspace,
            "stories-v1.sqlite",
        );
        const calls = [];
        await runInNewContext(
            `(async()=>{${B.nativeCall}})()`,
            {
                mode: "domain2-fork",
                plan: plain(modeApi().pagingLauncherPlan("domain2-fork")),
                workspace: plannedWorkspace.workspace,
                plannedWorkspace,
                path: path.win32,
                executable: P.exe,
                run: async (...args) => calls.push(plain(args)),
            },
            { timeout: 1000 },
        );
        assert.equal(calls.length, 1);
        assert.equal(calls[0][0], P.exe);
        assert.deepEqual(calls[0][1], []);
        assert.deepEqual(calls[0][2], {
            LOCALLORE_D02_HARNESS: "1",
            LOCALLORE_D08_DOMAIN2_FORK_HARNESS: "1",
            LOCALLORE_TEST_WORKSPACE: plannedWorkspace.database,
            LOCALLORE_D02_ARTIFACT_DIR: path.win32.join(
                plannedWorkspace.workspace,
                "evidence",
            ),
        });
    },
);
test(
    "native",
    "actual-new-mode-env-wrapper-routes-alias-conflicts-before-seeding",
    () => {
        const s = source.native;
        for (const name of [
            "validate_mode",
            "allowed_action",
            "seed",
            "oracle",
        ])
            assert.match(s, new RegExp(`\\bfn\\s+${name}\\s*\\(`));
        assert.match(s, /vars_os\s*\(/);
        assert.match(s, /LOCALLORE_D08_DOMAIN2_FORK_HARNESS/);
        assert.match(s, /to_ascii_uppercase\s*\(/);
        assert.match(s, /to_str\s*\(/);
        const legacy = source.fork;
        assert.match(legacy, /domain2_fork_harness/);
        assert.match(legacy, /allowed_action\s*\(/);
        assert.match(legacy, /domain2-oracle/);
        // Source order/interface evidence only. Rust tests exercise the pure flag/action API.
    },
);
test("native", "fixed-labels-and-eight-MiB-writer-route-source-control", () => {
    const s = source.harness;
    const start = s.indexOf("fn domain2_fork_label("),
        end = s.indexOf("\n}", start);
    if (start < 0 || end < start) throw Error("UNRUN_SETUP:domain2_fork_label");
    const body = s.slice(start, end);
    for (const label of [...labels, "d08-fork-failure"])
        assert(body.includes(JSON.stringify(label)), label);
    assert(!body.includes('"d08-browser-'));
    const write = s.slice(
        s.indexOf("fn write(&self"),
        s.indexOf("fn checked_json"),
    );
    assert.match(write, /domain2_fork_active\s*\(/);
    assert.match(write, /reserve_with_limit\s*\(/);
    assert.match(write, /MAX_DOMAIN2_FORK_ARTIFACT_BYTES/);
    assert.match(
        s,
        /MAX_DOMAIN2_FORK_ARTIFACT_BYTES[^;]*8\s*\*\s*1024\s*\*\s*1024/,
    );
});
test(
    "journey",
    "fixed-journey-registration-normal-exclusion-and-report-source",
    () => {
        const s = source.journey;
        assert.match(source.frontend, /domain2Fork/);
        assert.match(source.frontend, /domain2-fork-native-journeys/);
        assert.match(source.build, /__DEV_HARNESS__:\s*String\(harness\)/);
        assert.match(source.verifier, /"domain2Fork"/);
        assert.match(source.verifier, /"d08-fork-catalog"/);
        for (const label of labels)
            assert(
                s.includes(JSON.stringify(label)) ||
                    s.includes(label.slice("d08-fork-".length)),
                label,
            );
        assert.match(s, /domain2_fork_v1/);
        assert.match(s, /fork_boundaries/);
        assert.match(s, /fork_start/);
        assert.match(s, /fork_lookup/);
        assert.match(s, /archive_cancel/);
        assert.match(s, /archive_status/);
        // Finite trace/report/single-flight behavior needs independent actual journey
        // FIRST before that producer; mere source tokens are NOT execution proof.
    },
);

for (const item of cases) {
    const absent =
        item.need === "launcher"
            ? !B
            : item.need === "native"
              ? missing.native || missing.fork || missing.harness
              : missing.journey ||
                missing.frontend ||
                missing.build ||
                missing.verifier;
    if (absent) {
        results.push({ name: item.name, status: "UNRUN_SETUP" });
        continue;
    }
    try {
        await item.run();
        results.push({ name: item.name, status: "PASS" });
    } catch (e) {
        const message = String(e);
        results.push({
            name: item.name,
            status: message.includes("UNRUN_SETUP:") ? "UNRUN_SETUP" : "FAIL",
            error: message.slice(0, 220),
        });
    }
}
const report = {
    kind: "d08_domain2_fork_native_independent_first_v1",
    authored: cases.length,
    executed: results.filter((v) => v.status !== "UNRUN_SETUP").length,
    passed: results.filter((v) => v.status === "PASS").length,
    failed: results.filter((v) => v.status === "FAIL").length,
    unrun: results.filter((v) => v.status === "UNRUN_SETUP").length,
    setup,
    results,
    sourceSHA256: Object.fromEntries(
        Object.entries(source).map(([k, v]) => [k, hash(v)]),
    ),
    limits: [
        "Author UNRUN; new mode/resource numbers prospective, not app admission",
        "Actual launcher JS uses memory-only FS/Git/children/clock; no child/runtime/storage qualification",
        "Native flags/labels/writer and TS routing are source controls; Rust and future independent journey FIRST remain separate",
        "No model/provider/SDK/OS/browser/nativeIPC/rendering/focus/permissions or whole task acceptance",
        "No files/bundles/roots; stdout8KiB; all historical evidence/failed caps retained",
    ],
};
const out = JSON.stringify(report);
assert(Buffer.byteLength(out) + 1 <= 8192, "BoundedEightKiBForkNativeReport");
console.log(out);
process.exitCode =
    setup.length || report.unrun
        ? 2
        : report.failed || !report.executed
          ? 1
          : 0;
