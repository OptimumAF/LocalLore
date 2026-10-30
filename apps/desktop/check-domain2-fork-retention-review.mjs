// Independent retention FIRST 6cda6305; author SOURCE ONLY / UNRUN.
// Actual future launcher helper + whole try/catch/finally in VM. All filesystem,
// hashes/storage/children are memory doubles, not disk, app or containment proof.
// Frozen seam: d08-fork-diagnostic-retention-v1 markers, two helpers and sticky
// forkDiagnosticProducts/forkDiagnosticFailed. No old tests/policy copied/edited.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";
assert.equal(process.argv.length, 2, "ClosedRetentionArguments");
const file = new URL("v2-inspector-paging-harness.mjs", import.meta.url);
const MiB = 1048576,
    revision = "a".repeat(40),
    setup = [],
    results = [],
    tests = [];
const hash = (x) => createHash("sha256").update(x).digest("hex");
const plain = (x) => JSON.parse(JSON.stringify(x));
const P = {
    root: "D:\\retention\\source",
    target: "D:\\retention\\target",
    folder: "D:\\retention\\packets\\p-00000000-0000-4000-8000-000000000001",
    exe: "D:\\retention\\target\\debug\\locallore-desktop-spike.exe",
    node: "D:\\tools\\node.exe",
};
const js = path.win32.join(P.root, "dist", "app.js"),
    front = path.win32.join(P.folder, "diagnostic-app.js");
const native = path.win32.join(
    P.target,
    `d08-fork-diagnostic-${path.win32.basename(P.folder)}.exe`,
);
const proofFile = path.win32.join(P.folder, "diagnostic-products.json");
const labels = [
    "catalog",
    "rejected",
    "pending",
    "preauthor",
    "authored",
    "recovered",
    "enlarged",
].map((x) => `d08-fork-${x}`);
let source, blocks;
const test = (name, run) => tests.push({ name, run });
function marked(text, start, end) {
    const a = text.indexOf(start),
        b = text.indexOf(end, a + start.length);
    if (a < 0 || b <= a || text.indexOf(start, a + start.length) >= 0)
        throw Error("RetentionMarkersRequired");
    return text.slice(a + start.length, b);
}
const buildArgs = (normal) => [
    "build",
    "--manifest-path",
    "src-tauri/Cargo.toml",
    "--bin",
    "locallore-desktop-spike",
    "--locked",
    "--offline",
    ...(normal ? [] : ["--features", "dev-harness"]),
];
function sandbox(mode = "domain2-fork", options = {}) {
    const fs = new Map([
        [js, Buffer.from("raw-harness-frontend")],
        [P.exe, Buffer.from("raw-owned-native-executable")],
    ]);
    const writes = [],
        reads = [],
        children = [],
        events = [],
        sizes = new Map();
    const control = {
        sourceBad: false,
        productBad: false,
        storageBad: false,
        unknown: false,
        appFail: false,
        failCopy: null,
        corruptCopy: null,
        failProof: false,
        afterNodeTamper: false,
        gap: null,
        ...options,
    };
    const limits = {
        targetGrowth: 2 * 1024 ** 3,
        artifacts: 20 * MiB,
        cumulativeEvidence: 660 * MiB,
        pagingEvidence: 32 * MiB,
        sourceGrowth: 128 * MiB,
    };
    const original = {
        frontend: Buffer.from(fs.get(js)),
        native: Buffer.from(fs.get(P.exe)),
    };
    const processes = [
        {
            sequence: 1,
            command: P.node,
            args: ["build.mjs", "--harness"],
            closed: true,
            code: 0,
            error: null,
            timedOut: false,
            truncated: false,
        },
        {
            sequence: 2,
            command: "cargo",
            args: buildArgs(false),
            closed: true,
            code: 0,
            error: null,
            timedOut: false,
            truncated: false,
        },
    ];
    const meta = (file) => {
        if (!fs.has(file))
            throw Object.assign(Error("missing"), { code: "ENOENT" });
        return {
            isFile: () => true,
            isSymbolicLink: () => false,
            size: sizes.get(file) ?? fs.get(file).length,
        };
    };
    const read = async (file, maximum) => {
        reads.push({ file, maximum });
        events.push("read:" + file);
        const info = meta(file);
        assert(Number.isSafeInteger(maximum) && maximum >= 0);
        if (file === js || file === front)
            assert(maximum <= 8 * MiB, "Frontend8MiBReadBound");
        if (file === P.exe || file === native)
            assert(maximum <= 128 * MiB, "Native128MiBReadBound");
        if (info.size > maximum) throw Error("BoundedOrdinaryArtifactRequired");
        return Buffer.from(fs.get(file));
    };
    const currentHashes = async (names) =>
        Object.fromEntries(
            names.map((name) => {
                const file = path.win32.isAbsolute(name)
                    ? name
                    : path.win32.join(P.root, name);
                return [name, hash(fs.get(file) ?? Buffer.alloc(0))];
            }),
        );
    const writeFile = async (file, bytes, flags) => {
        assert.equal(flags?.flag, "wx", "ExclusiveOrdinaryCopies");
        if (fs.has(file))
            throw Object.assign(Error("collision"), { code: "EEXIST" });
        writes.push(file);
        events.push("write:" + file);
        if (control.failCopy === file) {
            fs.set(file, Buffer.from(bytes).subarray(0, 3));
            throw Error("SyntheticPartialCopy");
        }
        fs.set(file, Buffer.from(bytes));
        if (control.corruptCopy === file)
            fs.set(file, Buffer.from("CORRUPTED-COPY"));
    };
    const write = async (name, value) => {
        const file = path.win32.join(P.folder, name),
            bytes = Buffer.from(JSON.stringify(value, null, 2));
        if (name === "diagnostic-products.json" && control.failProof) {
            if (!fs.has(file)) {
                writes.push(file);
                fs.set(file, bytes.subarray(0, 4));
            }
            throw Error("SyntheticProofWrite");
        }
        await writeFile(file, bytes, { flag: "wx" });
    };
    const context = {
        Buffer,
        TextDecoder,
        TextEncoder,
        path: path.win32,
        mode,
        root: P.root,
        target: P.target,
        folder: P.folder,
        executable: P.exe,
        revision,
        limits,
        buildArgs,
        digest: hash,
        processes,
        labels,
        plan: { labels, reportMode: "domain2_fork_v1" },
        plannedWorkspace: {
            workspace: path.win32.join(P.folder, "workspace"),
            database: path.win32.join(
                P.folder,
                "workspace",
                "stories-v1.sqlite",
            ),
        },
        sourcePaths: ["fixed-source"],
        sourceHashes: { fixed: "source" },
        initialStorage: {
            target: { bytes: 1000 },
            source: { bytes: 100 },
            evidence: { bytes: 0 },
            pagingEvidence: { bytes: 0 },
        },
        process: { execPath: P.node },
        unknownChildren: [],
        gitChildren: [],
        boundedBytes: read,
        readFile: async (file) => {
            events.push("read:" + file);
            meta(file);
            return Buffer.from(fs.get(file));
        },
        lstat: async (file) => meta(file),
        writeFile,
        write,
        readdir: async () => [],
        mkdir: async () => {},
        hashes: currentHashes,
        unchangedSource: async () => {
            events.push("source");
            if (control.sourceBad) throw Error("PagingSourceChanged");
        },
        unchangedProducts: async () => {
            events.push("products");
            if (control.productBad) throw Error("PagingProductChanged");
        },
    };
    const code = `(async()=>{
        let ownedDrainUnknown=false,storageBreached=false,lastStorage=null,productHashes=await hashes(["dist/app.js",executable]);
        let originalError=null,restoration=null,workspace=null,candidate=null;
        ${blocks.helper}
        async function measureStorage(){
            events.push('inventory');
            if(control.storageBad){storageBreached=true;throw Error("StorageInventoryFailure");}
            if(storageBreached)throw Error("StorageBudgetLatched");
            const packet=[...files].filter(([p])=>p.startsWith(folder+path.sep)).reduce((n,[,b])=>n+b.length,0);
            const copied=files.has(nativePath)?files.get(nativePath).length:0;
            lastStorage={target:{bytes:1000+copied},packet:{bytes:packet},source:{bytes:100},targetGrowth:copied,sourceGrowth:0,cumulativeEvidence:packet,pagingEvidence:packet};
            if(control.gap){const key=control.gap; if(key==='target'){lastStorage.targetGrowth=limits.targetGrowth-1;lastStorage.target.bytes=initialStorage.target.bytes+lastStorage.targetGrowth;}
                else if(key==='packet')lastStorage.packet.bytes=limits.artifacts-1048576-1;
                else if(key==='joint')lastStorage.cumulativeEvidence=limits.cumulativeEvidence-1048576-1;
                else lastStorage.pagingEvidence=limits.pagingEvidence-1048576-1;}
            return lastStorage;
        }
        async function run(command,args,additions={}){
            if(ownedDrainUnknown||storageBreached)throw Error('GuardLatched');
            children.push({command,args:[...args],additions:{...additions}});events.push('child:'+command);
            if(command===executable){if(control.appFail)throw Error('KnownClosedAppFailure');return;}
            const normal=command===process.execPath?args.length===1:!args.includes('dev-harness');
            if(command===process.execPath)files.set(frontendPath,Buffer.from(normal?'normal-frontend':'raw-harness-frontend'));
            else if(command==='cargo')files.set(executable,Buffer.from(normal?'normal-native':'raw-owned-native-executable'));
            if(normal&&command===process.execPath&&control.afterNodeTamper)files.set(nativePath,Buffer.from('TAMPERED'));
        }
        return {retain:retainForkDiagnosticProducts,verify:verifyForkDiagnosticProducts,
            whole:async()=>{try{${blocks.tryBody}}catch(error){${blocks.catchBody}}finally{${blocks.finallyBody}}return {candidate,restoration,originalError:originalError?.message};},
            restore:async()=>{${blocks.finallyBody}return restoration;},
            flags:(p)=>{if('unknown'in p)ownedDrainUnknown=p.unknown;if('storage'in p)storageBreached=p.storage;if('snapshot'in p)productHashes=p.snapshot;},
            observe:()=>({retained:forkDiagnosticProducts,failed:forkDiagnosticFailed,ownedDrainUnknown,storageBreached,restoration,originalError:originalError?.message})};
    })()`;
    const ready = vm.runInNewContext(
        code,
        {
            ...context,
            control,
            files: fs,
            frontendPath: js,
            nativePath: native,
            children,
            events,
        },
        { timeout: 1000 },
    );
    return {
        ready,
        fs,
        writes,
        reads,
        children,
        events,
        control,
        sizes,
        processes,
        original,
    };
}
const proof = (h) => JSON.parse(h.fs.get(proofFile).toString("utf8"));
const noNormal = (h) =>
    assert(
        !h.children.some(
            (r) =>
                (r.command === P.node && r.args.length === 1) ||
                (r.command === "cargo" && !r.args.includes("dev-harness")),
        ),
        "NoNormalOverwrite",
    );
const normalChildren = (h) =>
    h.children.filter(
        (r) =>
            (r.command === P.node && r.args.length === 1) ||
            (r.command === "cargo" && !r.args.includes("dev-harness")),
    );

test("actual-fork-exclusive-copies-proof-and-idempotence", async () => {
    const h = sandbox(),
        a = await h.ready;
    await a.retain();
    await a.verify();
    assert(h.fs.get(front).equals(h.original.frontend));
    assert(h.fs.get(native).equals(h.original.native));
    const p = proof(h);
    assert.deepEqual(Object.keys(p).sort(), [
        "builds",
        "frontend",
        "interpretation",
        "kind",
        "native",
        "revision",
        "version",
    ]);
    assert.equal(p.version, 1);
    assert.equal(p.kind, "d08_fork_diagnostic_products_v1");
    assert.equal(p.revision, revision);
    assert.equal(p.interpretation, "current-products-at-retention");
    for (const [key, file, original] of [
        ["frontend", front, h.original.frontend],
        ["native", native, h.original.native],
    ]) {
        assert.deepEqual(p[key], {
            present: true,
            path: path.win32.basename(file),
            bytes: original.length,
            sha256: hash(original),
        });
        assert.deepEqual(p.builds[key], {
            sequence: key === "frontend" ? 1 : 2,
            closed: true,
            code: 0,
            error: null,
            timedOut: false,
            truncated: false,
        });
        assert(
            h.reads.some((x) => x.file === file),
            "ReadBackEachOrdinaryCopy",
        );
    }
    const before = [...h.writes];
    await a.retain();
    await a.verify();
    assert.deepEqual(h.writes, before, "NoRewriteOrRepair");
    assert(
        h.reads.some((x) => x.file === proofFile),
        "ProofReadBack",
    );
    assert.equal(
        a.observe().retained.proofSHA256,
        hash(h.fs.get(proofFile)),
        "StoredProofByteIdentity",
    );
    for (const file of [front, native, proofFile]) {
        const at = h.events.indexOf("write:" + file),
            next = h.events.findIndex(
                (event, i) => i > at && event.startsWith("write:"),
            );
        assert(
            h.events.slice(0, at).includes("inventory") &&
                h.events
                    .slice(at + 1, next < 0 ? undefined : next)
                    .includes("inventory"),
            "ChargeBeforeAfterEachCopyAndProof",
        );
    }
});
test("partial-collision-size-proof-and-hash-failures-latch", async () => {
    for (const fault of [
        "front-collision",
        "native-collision",
        "front-partial",
        "native-partial",
        "proof-partial",
        "front-corrupt",
        "native-corrupt",
        "front-size",
        "native-size",
    ]) {
        const h = sandbox(),
            a = await h.ready;
        if (fault.endsWith("collision"))
            h.fs.set(
                fault.startsWith("front") ? front : native,
                Buffer.from("PREEXISTING"),
            );
        if (fault.endsWith("partial") && fault !== "proof-partial")
            h.control.failCopy = fault.startsWith("front") ? front : native;
        if (fault === "proof-partial") h.control.failProof = true;
        if (fault.endsWith("corrupt"))
            h.control.corruptCopy = fault.startsWith("front") ? front : native;
        if (fault.endsWith("size"))
            h.sizes.set(
                fault.startsWith("front") ? js : P.exe,
                (fault.startsWith("front") ? 8 : 128) * MiB + 1,
            );
        await assert.rejects(a.retain());
        assert.equal(a.observe().failed, true, fault);
        const kept = [...h.fs].map(([p, b]) => [p, b.toString("hex")]);
        h.control.failCopy = null;
        h.control.failProof = false;
        h.control.corruptCopy = null;
        h.sizes.clear();
        await assert.rejects(a.retain());
        await a.restore();
        noNormal(h);
        assert.deepEqual(
            [...h.fs]
                .filter(([p]) => p === front || p === native || p === proofFile)
                .map(([p, b]) => [p, b.toString("hex")]),
            kept.filter(
                ([p]) => p === front || p === native || p === proofFile,
            ),
        );
    }
});
test("prewrite-storage-headroom-and-unknown-guards", async () => {
    for (const fault of [
        "packet",
        "joint",
        "group",
        "target",
        "inventory",
        "unknown",
    ]) {
        const h = sandbox(),
            a = await h.ready;
        if (["packet", "joint", "group", "target"].includes(fault))
            h.control.gap = fault;
        if (fault === "inventory") h.control.storageBad = true;
        if (fault === "unknown") a.flags({ unknown: true });
        await assert.rejects(a.retain());
        await a.restore();
        noNormal(h);
        assert(!h.fs.has(native), "NoTargetWriteAfterRefusedForecast");
        if (fault !== "target")
            assert(!h.fs.has(front), "NoPacketCopyAfterRefusedForecast");
    }
});
test("actual-try-known-app-failure-keeps-copies-before-restore", async () => {
    assert.equal(
        hash(
            marked(
                source,
                "// d05-paging-process-policy-v1:start",
                "// d05-paging-process-policy-v1:end",
            ).replaceAll("\r\n", "\n"),
        ),
        "eabc72a0858c651186cb1fcab2b7d917667444667c3f8c01bf282de1728f289a",
        "OriginalProcessPolicyByteIdentity",
    );
    const h = sandbox("domain2-fork", { appFail: true }),
        a = await h.ready;
    const value = await a.whole();
    assert.equal(value.originalError, "KnownClosedAppFailure");
    assert.equal(value.restoration.passed, true);
    assert.equal(value.restoration.launched, false);
    assert.equal(h.children.filter((x) => x.command === P.exe).length, 1);
    assert.equal(normalChildren(h).length, 2);
    assert(h.fs.get(front).equals(h.original.frontend));
    assert(h.fs.get(native).equals(h.original.native));
    assert.notEqual(hash(h.fs.get(js)), proof(h).frontend.sha256);
    assert.notEqual(hash(h.fs.get(P.exe)), proof(h).native.sha256);
    assert(
        h.events.indexOf("write:" + proofFile) <
            h.events.indexOf("child:" + P.exe),
        "VerifiedRetentionBeforeActualAppCaller",
    );
    for (const file of [front, native, proofFile])
        assert(
            h.events.indexOf("read:" + file) >= 0 &&
                h.events.indexOf("read:" + file) <
                    h.events.indexOf("child:" + P.exe),
            "ReadbackBeforeNativeChild",
        );
    for (const mode of ["paging", "timeline-browser"]) {
        const old = sandbox(mode, { appFail: true }),
            api = await old.ready;
        await api.whole();
        assert(
            !old.fs.has(front) && !old.fs.has(native) && !old.fs.has(proofFile),
        );
        assert.equal(normalChildren(old).length, 2);
    }
});
test("actual-finally-rechecks-before-each-normal-overwrite", async () => {
    for (const fault of [
        "copy",
        "proof",
        "source",
        "products",
        "unknown",
        "storage",
        "after-node",
    ]) {
        const h = sandbox(),
            a = await h.ready;
        await a.retain();
        await a.verify();
        if (fault === "copy") h.fs.set(native, Buffer.from("CHANGED"));
        if (fault === "proof") h.fs.set(proofFile, Buffer.from("{}"));
        if (fault === "source") h.control.sourceBad = true;
        if (fault === "products") h.control.productBad = true;
        if (fault === "unknown") a.flags({ unknown: true });
        if (fault === "storage") a.flags({ storage: true });
        if (fault === "after-node") h.control.afterNodeTamper = true;
        await a.restore();
        assert.equal(a.observe().restoration.passed, false, fault);
        assert.equal(
            normalChildren(h).length,
            fault === "after-node" ? 1 : 0,
            "NoLaterOverwritingChild",
        );
    }
});
test("partial-build-outcomes-and-explicit-absence-are-honest", async () => {
    const h = sandbox(),
        a = await h.ready;
    a.flags({ snapshot: null });
    h.processes[0].code = 1;
    h.processes.splice(1);
    h.fs.delete(P.exe);
    await a.retain();
    await a.verify();
    const p = proof(h);
    assert.equal(p.builds.frontend.code, 1);
    assert.equal(p.builds.native, null);
    assert.deepEqual(p.native, {
        present: false,
        path: path.win32.basename(native),
        bytes: null,
        sha256: null,
    });
    assert(h.fs.get(front).equals(h.original.frontend));
    await a.restore();
    assert.equal(a.observe().restoration.passed, true);
    const missing = sandbox(),
        api = await missing.ready;
    missing.fs.delete(js);
    await assert.rejects(api.retain());
    await api.restore();
    noNormal(missing);
});

assert.equal(tests.length, 6, "FrozenSixRetentionGroups");
try {
    source = await readFile(file, "utf8");
    const helper = marked(
        source,
        "// d08-fork-diagnostic-retention-v1:start",
        "// d08-fork-diagnostic-retention-v1:end",
    );
    for (const name of [
        "retainForkDiagnosticProducts",
        "verifyForkDiagnosticProducts",
        "forkDiagnosticProducts",
        "forkDiagnosticFailed",
    ])
        assert(helper.includes(name));
    const begin = source.search(/^try\s*\{/m),
        boundary = /\n\} catch \(error\) \{([\s\S]*?)\n\} finally \{/.exec(
            source.slice(begin),
        );
    assert(begin >= 0 && boundary, "ActualGlobalTryCatchFinallyRequired");
    const cut = begin + boundary.index,
        fin = cut + boundary[0].length,
        end = source.indexOf("\n}\nif (originalError", fin);
    assert(end > fin, "ActualGlobalFinallyEnd");
    blocks = {
        helper,
        tryBody: source.slice(
            begin + source.slice(begin).indexOf("{") + 1,
            cut,
        ),
        catchBody: boundary[1],
        finallyBody: source.slice(fin, end),
    };
} catch (error) {
    blocks = null;
    setup.push({
        status: "UNRUN_SETUP",
        reason: String(error.message).slice(0, 200),
    });
}
for (const item of tests) {
    if (!blocks) {
        results.push({ name: item.name, status: "UNRUN_SETUP" });
        continue;
    }
    try {
        await item.run();
        results.push({ name: item.name, status: "PASS" });
    } catch (error) {
        results.push({
            name: item.name,
            status: "FAIL",
            error: String(error.message).slice(0, 400),
        });
    }
}
if (source)
    assert.equal(
        hash(await readFile(file, "utf8")),
        hash(source),
        "ActualLauncherSourceUnchanged",
    );
const output = {
    kind: "d08_domain2_fork_retention_first_v1",
    authored: tests.length,
    executed: results.filter((x) => x.status !== "UNRUN_SETUP").length,
    passed: results.filter((x) => x.status === "PASS").length,
    failed: results.filter((x) => x.status === "FAIL").length,
    unrun: results.filter((x) => x.status === "UNRUN_SETUP").length,
    setup,
    results,
    sourceSHA256: source ? hash(source) : null,
    evidence:
        "Actual helper and global try/finally; memory FS/process/storage doubles only; no app or physical copies; author UNRUN",
};
const encoded = JSON.stringify(output);
assert(Buffer.byteLength(encoded) + 1 <= 8192, "RetentionStdout8KiB");
console.log(encoded);
process.exitCode =
    setup.length || output.unrun
        ? 2
        : output.failed || !output.executed
          ? 1
          : 0;
