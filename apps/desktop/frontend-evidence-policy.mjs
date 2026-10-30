// Development runner accounting only. No child execution or filesystem writes.
import { lstat, realpath, readdir, open } from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";

export const FRONTEND_EVIDENCE_LIMITS = Object.freeze({
    outputBytes: 67_108_864,
    cumulativeBytes: 671_088_640,
    productBytes: 16_777_216,
    stepReserveBytes: 4_194_304,
    metadataReserveBytes: 1_048_576,
    entries: 2_000_000,
    streamBytes: 262_144,
    childMs: 240_000,
    stopGraceMs: 5_000,
    consoleBytes: 4_194_304,
    summaryBytes: 32_768,
});
const limits = FRONTEND_EVIDENCE_LIMITS;
const recordKeys = [
    "version",
    "kind",
    "source_revision",
    "output_path_sha256",
    "initial_output_bytes",
    "output_limit_bytes",
    "external_evidence_bytes",
    "cumulative_limit_bytes",
];
const outcomeKeys = [
    "code",
    "closed",
    "timedOut",
    "truncated",
    "error",
    "stdoutBytes",
    "stderrBytes",
];
const categories = new Set([
    "Admission",
    "Path",
    "Inventory",
    "Reserve",
    "Sequence",
    "Outcome",
    "StepBudget",
    "OutputBudget",
    "ProductBudget",
    "AggregateBudget",
    "UnknownChild",
]);
const safe = (value) => Number.isSafeInteger(value) && value >= 0;
const error = (category) => Error("FrontendEvidence" + category);
const demand = (condition, category) => {
    if (!condition) throw error(category);
};
const categoryOf = (value, fallback) => {
    const category = String(value?.message ?? "").slice(
        "FrontendEvidence".length,
    );
    return categories.has(category) ? category : fallback;
};
const same = (a, b) => a.toLowerCase() === b.toLowerCase();
const contains = (parent, child) => {
    const relative = path.relative(parent.toLowerCase(), child.toLowerCase());
    return (
        relative === "" ||
        (!path.isAbsolute(relative) &&
            relative !== ".." &&
            !relative.startsWith(".." + path.sep))
    );
};

export function parseFrontendEvidenceAdmission(
    rawBytes,
    expectedRevision,
    expectedPathDigest,
) {
    try {
        demand(
            rawBytes instanceof Uint8Array && rawBytes.byteLength <= 4096,
            "Admission",
        );
        const text = new TextDecoder("utf-8", {
            fatal: true,
            ignoreBOM: true,
        }).decode(rawBytes);
        const value = JSON.parse(text);
        demand(
            value && !Array.isArray(value) && typeof value === "object",
            "Admission",
        );
        demand(
            Object.keys(value).join("\0") === recordKeys.join("\0"),
            "Admission",
        );
        demand(JSON.stringify(value) + "\n" === text, "Admission");
        demand(
            value.version === 1 &&
                value.kind === "d09_frontend_evidence_admission_v1",
            "Admission",
        );
        demand(
            /^[a-f0-9]{40}$/.test(value.source_revision) &&
                value.source_revision === expectedRevision,
            "Admission",
        );
        demand(
            /^[a-f0-9]{64}$/.test(value.output_path_sha256) &&
                value.output_path_sha256 === expectedPathDigest,
            "Admission",
        );
        demand(
            recordKeys.slice(4).every((key) => safe(value[key])),
            "Admission",
        );
        demand(
            value.output_limit_bytes <= limits.outputBytes &&
                value.cumulative_limit_bytes === limits.cumulativeBytes,
            "Admission",
        );
        const initialReserve =
            value.initial_output_bytes +
            limits.stepReserveBytes +
            limits.metadataReserveBytes;
        demand(
            safe(initialReserve) && initialReserve <= value.output_limit_bytes,
            "Admission",
        );
        return value;
    } catch {
        throw error("Admission");
    }
}

export async function openFrontendEvidencePolicy({
    sourceRoot,
    outputDir,
    admissionFile,
    sourceRevision,
}) {
    const identities = new Map();
    function resolved(value) {
        demand(typeof value === "string" && path.isAbsolute(value), "Path");
        const result = path.resolve(value);
        demand(same(path.parse(result).root, "D:\\"), "Path");
        return result;
    }
    const source = resolved(sourceRoot),
        output = resolved(outputDir),
        admission = resolved(admissionFile);
    demand(!contains(source, output) && !contains(output, source), "Path");
    demand(
        !contains(source, admission) && !contains(output, admission),
        "Path",
    );
    const temporary = path.join(output, "_tmp");
    const dist = path.join(source, "dist");
    const generated = path.join(source, "ui", "host.generated.ts");

    async function ordinary(
        location,
        expected,
        { optional = false, bind = false } = {},
    ) {
        const chain = [];
        for (let current = location; ; current = path.dirname(current)) {
            chain.push(current);
            if (path.dirname(current) === current) break;
        }
        chain.reverse();
        let result;
        for (let index = 0; index < chain.length; index++) {
            const current = chain[index],
                leaf = index === chain.length - 1;
            try {
                result = await lstat(current, { bigint: true });
            } catch (cause) {
                if (optional && cause?.code === "ENOENT") return null;
                throw error("Path");
            }
            demand(!result.isSymbolicLink(), "Path");
            demand(
                leaf && expected === "file"
                    ? result.isFile()
                    : result.isDirectory(),
                "Path",
            );
            let actual;
            try {
                actual = await realpath(current);
            } catch {
                throw error("Path");
            }
            demand(same(path.resolve(actual), current), "Path");
            if (bind && result.isDirectory()) {
                demand(
                    ["number", "bigint"].includes(typeof result.dev) &&
                        ["number", "bigint"].includes(typeof result.ino),
                    "Path",
                );
                const identity =
                    String(result.dev) +
                    ":" +
                    String(result.ino) +
                    ":" +
                    actual.toLowerCase();
                const key = current.toLowerCase();
                demand(
                    !identities.has(key) || identities.get(key) === identity,
                    "Path",
                );
                identities.set(key, identity);
            }
        }
        return result;
    }
    await ordinary(source, "directory", { bind: true });
    await ordinary(output, "directory", { bind: true });
    await ordinary(temporary, "directory", { bind: true });
    const admissionInfo = await ordinary(admission, "file");
    const admissionSize = Number(admissionInfo.size);
    demand(safe(admissionSize) && admissionSize <= 4096, "Admission");
    let raw;
    try {
        const handle = await open(admission, "r");
        try {
            const buffer = Buffer.alloc(4097);
            const { bytesRead } = await handle.read(
                buffer,
                0,
                buffer.length,
                0,
            );
            demand(
                bytesRead === admissionSize && bytesRead <= 4096,
                "Admission",
            );
            raw = buffer.subarray(0, bytesRead);
        } finally {
            await handle.close();
        }
    } catch {
        throw error("Admission");
    }
    const digest = createHash("sha256")
        .update(output.toLowerCase(), "utf8")
        .digest("hex");
    const record = parseFrontendEvidenceAdmission(raw, sourceRevision, digest);

    async function measure() {
        try {
            const outputInfo = await ordinary(output, "directory", {
                bind: true,
            });
            await ordinary(source, "directory", { bind: true });
            await ordinary(temporary, "directory", { bind: true });
            const distInfo = await ordinary(dist, "directory", {
                optional: true,
                bind: true,
            });
            const generatedInfo = await ordinary(generated, "file", {
                optional: true,
                bind: true,
            });
            let entries = 0;
            function add(a, b) {
                demand(safe(b) && safe(a + b), "Inventory");
                return a + b;
            }
            async function tree(root, initial) {
                if (!initial) return 0;
                const pending = [[root, initial]];
                let bytes = 0;
                while (pending.length) {
                    const [location, provided] = pending.pop();
                    const info =
                        provided ?? (await lstat(location, { bigint: true }));
                    demand(++entries <= limits.entries, "Inventory");
                    demand(
                        !info.isSymbolicLink() &&
                            (info.isDirectory() || info.isFile()),
                        "Path",
                    );
                    demand(
                        same(path.resolve(await realpath(location)), location),
                        "Path",
                    );
                    if (info.isFile()) bytes = add(bytes, Number(info.size));
                    else {
                        for (const name of await readdir(location)) {
                            demand(
                                typeof name === "string" &&
                                    name !== "." &&
                                    name !== ".." &&
                                    path.basename(name) === name &&
                                    !name.includes("/") &&
                                    !name.includes("\\"),
                                "Inventory",
                            );
                            demand(
                                entries + pending.length + 1 <= limits.entries,
                                "Inventory",
                            );
                            pending.push([path.join(location, name), null]);
                        }
                    }
                }
                return bytes;
            }
            const outputBytes = await tree(output, outputInfo);
            let productBytes = await tree(dist, distInfo);
            if (generatedInfo) {
                demand(++entries <= limits.entries, "Inventory");
                productBytes = add(productBytes, Number(generatedInfo.size));
            }
            return { outputBytes, productBytes };
        } catch (cause) {
            throw error(categoryOf(cause, "Inventory"));
        }
    }

    let status = "ready",
        nextIndex = 0,
        activeIndex = null,
        firstError = null;
    let currentBytes = 0,
        productBytes = 0,
        initialBytes = record.initial_output_bytes;
    let busy = false,
        stepStart = null;
    const snapshot = () => ({
        status,
        nextIndex,
        activeIndex,
        initialBytes,
        currentBytes,
        productBytes,
        error: firstError,
    });
    function latch(category) {
        if (status === "failed") throw error(firstError);
        if (status === "finished") throw error("Sequence");
        status = "failed";
        firstError = category;
        if (["Path", "Inventory", "UnknownChild"].includes(category))
            currentBytes = productBytes = null;
        throw error(category);
    }
    function enter(eligible) {
        if (status === "failed") throw error(firstError);
        if (status === "finished") throw error("Sequence");
        if (busy || !eligible) latch("Sequence");
        busy = true;
    }
    function healthy() {
        if (status === "failed") throw error(firstError);
    }
    function accept(measured) {
        healthy();
        currentBytes = measured.outputBytes;
        productBytes = measured.productBytes;
    }
    function caps(reserve) {
        const extra =
            limits.metadataReserveBytes +
            (reserve ? limits.stepReserveBytes : 0);
        demand(productBytes <= limits.productBytes, "ProductBudget");
        demand(currentBytes <= record.output_limit_bytes, "OutputBudget");
        demand(
            safe(currentBytes + extra) &&
                currentBytes + extra <= record.output_limit_bytes,
            reserve ? "Reserve" : "OutputBudget",
        );
        const joint =
            record.external_evidence_bytes +
            currentBytes +
            productBytes +
            extra;
        demand(
            safe(joint) && joint <= record.cumulative_limit_bytes,
            "AggregateBudget",
        );
    }
    const first = await measure();
    accept(first);
    demand(currentBytes === initialBytes, "Admission");
    caps(true);

    async function beforeStep(index) {
        enter(
            status === "ready" &&
                safe(index) &&
                index === nextIndex &&
                activeIndex === null,
        );
        try {
            accept(await measure());
            caps(true);
            stepStart = { output: currentBytes, products: productBytes };
            activeIndex = index;
            status = "running";
            return snapshot();
        } catch (cause) {
            return latch(categoryOf(cause, "Inventory"));
        } finally {
            busy = false;
        }
    }
    async function completeStep(index, outcome) {
        enter(status === "running" && index === activeIndex && safe(index));
        try {
            demand(
                outcome &&
                    typeof outcome === "object" &&
                    !Array.isArray(outcome) &&
                    Reflect.ownKeys(outcome).length === outcomeKeys.length &&
                    outcomeKeys.every((key) => Object.hasOwn(outcome, key)),
                "Outcome",
            );
            demand(
                outcome.code === null || Number.isSafeInteger(outcome.code),
                "Outcome",
            );
            demand(
                ["closed", "timedOut", "truncated", "error"].every(
                    (key) => typeof outcome[key] === "boolean",
                ),
                "Outcome",
            );
            demand(
                safe(outcome.stdoutBytes) && safe(outcome.stderrBytes),
                "Outcome",
            );
            if (!outcome.closed) latch("UnknownChild");
            demand(
                outcome.code === 0 &&
                    !outcome.timedOut &&
                    !outcome.truncated &&
                    !outcome.error &&
                    outcome.stdoutBytes <= limits.streamBytes &&
                    outcome.stderrBytes <= limits.streamBytes,
                "Outcome",
            );
            accept(await measure());
            const growth =
                Math.max(0, currentBytes - stepStart.output) +
                Math.max(0, productBytes - stepStart.products);
            demand(
                safe(growth) && growth <= limits.stepReserveBytes,
                "StepBudget",
            );
            caps(false);
            nextIndex++;
            activeIndex = null;
            stepStart = null;
            status = "ready";
            return snapshot();
        } catch (cause) {
            return latch(categoryOf(cause, "Inventory"));
        } finally {
            busy = false;
        }
    }
    async function finish() {
        enter(status === "ready" && activeIndex === null && nextIndex > 0);
        try {
            accept(await measure());
            caps(false);
            status = "finished";
            return snapshot();
        } catch (cause) {
            return latch(categoryOf(cause, "Inventory"));
        } finally {
            busy = false;
        }
    }
    return { beforeStep, completeStep, finish, snapshot };
}
