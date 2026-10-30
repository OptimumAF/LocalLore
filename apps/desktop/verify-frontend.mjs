import { spawn } from "node:child_process";
import { readFile, lstat, realpath } from "node:fs/promises";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import path from "node:path";
import {
    FRONTEND_EVIDENCE_LIMITS as limits,
    openFrontendEvidencePolicy,
} from "./frontend-evidence-policy.mjs";
const root = new URL(".", import.meta.url);
const bounded = process.argv.length === 3 && process.argv[2] === "--bounded";
assert(
    process.argv.length === 2 || bounded,
    "ClosedFrontendVerificationArguments",
);
const passMessage =
    "PASS: strict TypeScript, current request/schema checks, and no development journey/control hooks in normal frontend.";
let policy = null,
    sourceRevision = null,
    completedSteps = 0,
    consoleBytes = 0;
let runnerReason = null,
    lastChild = null;

function printJson(value, final = false, keep = 0) {
    const line = JSON.stringify(value) + "\n";
    const size = Buffer.byteLength(line);
    const ceiling = limits.consoleBytes - (final ? keep : limits.summaryBytes);
    if (consoleBytes + size > ceiling) return false;
    consoleBytes += size;
    process.stdout.write(line);
    return true;
}
function outcome(result) {
    return Object.fromEntries(
        [
            "code",
            "closed",
            "timedOut",
            "truncated",
            "error",
            "stdoutBytes",
            "stderrBytes",
        ].map((key) => [key, result[key]]),
    );
}
// Private fixed callers below are the only command sources. No command API.
async function capture(command, args, env, duration, maximum) {
    return new Promise((resolve) => {
        let child = null,
            deadline = null,
            grace = null,
            done = false,
            stopping = false;
        let timedOut = false,
            truncated = false,
            failed = false,
            killAttempted = false;
        const counts = { stdout: 0, stderr: 0 };
        const buffers = { stdout: Buffer.alloc(0), stderr: Buffer.alloc(0) };
        const finish = (code, signal, closed, noChildCreated = false) => {
            if (done) return;
            done = true;
            clearTimeout(deadline);
            clearTimeout(grace);
            if (!closed && child) {
                // Release coordinator handles, while ownership remains unknown.
                // Each attempt is independent; none proves process termination.
                try {
                    child.stdout.destroy();
                } catch {
                    failed = true;
                }
                try {
                    child.stderr.destroy();
                } catch {
                    failed = true;
                }
                try {
                    child.unref();
                } catch {
                    failed = true;
                }
            }
            resolve({
                code,
                closed,
                timedOut,
                truncated,
                error: failed || !!signal,
                stdoutBytes: counts.stdout,
                stderrBytes: counts.stderr,
                stdout: buffers.stdout.toString("utf8"),
                stderr: buffers.stderr.toString("utf8"),
                signal,
                killAttempted,
                noChildCreated,
            });
        };
        const stop = (reason) => {
            if (done || stopping) return;
            stopping = true;
            if (reason === "timeout") timedOut = true;
            if (reason === "overflow") truncated = true;
            if (reason === "error") failed = true;
            clearTimeout(deadline);
            grace = setTimeout(
                () => finish(null, null, false),
                limits.stopGraceMs,
            );
            killAttempted = true;
            try {
                child.kill();
            } catch {
                failed = true;
            }
        };
        try {
            child = spawn(command, args, {
                cwd: root,
                shell: false,
                windowsHide: true,
                stdio: ["ignore", "pipe", "pipe"],
                env,
            });
        } catch {
            failed = true;
            finish(null, null, true, true);
            return;
        }
        for (const channel of ["stdout", "stderr"]) {
            child[channel].on("data", (value) => {
                if (done) return;
                const bytes = Buffer.isBuffer(value)
                    ? value
                    : Buffer.from(value);
                counts[channel] += bytes.length;
                if (!Number.isSafeInteger(counts[channel])) {
                    counts[channel] = Number.MAX_SAFE_INTEGER;
                    failed = true;
                }
                const left = maximum - buffers[channel].length;
                if (left > 0)
                    buffers[channel] = Buffer.concat([
                        buffers[channel],
                        bytes.subarray(0, left),
                    ]);
                if (counts[channel] > maximum) stop("overflow");
            });
            child[channel].on("error", () => stop("error"));
        }
        child.on("error", () => stop("error"));
        child.once("close", (code, signal) => finish(code, signal, true));
        deadline = setTimeout(() => stop("timeout"), duration);
    });
}
async function cleanRevision() {
    const head = await capture(
        "git",
        ["rev-parse", "HEAD"],
        { ...process.env },
        15000,
        65536,
    );
    if (
        !head.closed ||
        head.code !== 0 ||
        head.error ||
        head.truncated ||
        head.timedOut
    )
        throw Error("Source");
    const revision = head.stdout.trim();
    if (!/^[a-f0-9]{40}$/.test(revision)) throw Error("Source");
    const status = await capture(
        "git",
        ["status", "--porcelain"],
        { ...process.env },
        15000,
        65536,
    );
    if (
        !status.closed ||
        status.code !== 0 ||
        status.error ||
        status.truncated ||
        status.timedOut ||
        status.stdout.trim()
    )
        throw Error("Source");
    return revision;
}
async function physicalDirectory(value) {
    try {
        if (typeof value !== "string" || !path.isAbsolute(value))
            throw Error("Path");
        const resolved = path.resolve(value);
        if (path.parse(resolved).root.toLowerCase() !== "d:\\")
            throw Error("Path");
        for (let current = resolved; ; current = path.dirname(current)) {
            const info = await lstat(current);
            if (
                !info.isDirectory() ||
                info.isSymbolicLink() ||
                path.resolve(await realpath(current)).toLowerCase() !==
                    current.toLowerCase()
            )
                throw Error("Path");
            if (path.dirname(current) === current) break;
        }
    } catch {
        throw Error("Path");
    }
}
function finalRecord(passed, error = null) {
    return {
        kind: "d09_frontend_evidence_run_v1",
        passed,
        completedSteps,
        sourceRevision,
        error,
        policy: policy?.snapshot() ?? null,
        lastChild,
        processTreeContained: false,
        accounting:
            "designated evidence and fixed build products; cooperative, not an OS quota",
    };
}
async function verifyFrontend() {
    if (bounded) {
        if (
            !process.env.LOCALLORE_CHECK_OUTPUT_DIR ||
            !process.env.LOCALLORE_CHECK_BUDGET_FILE ||
            process.env.ESBUILD_BINARY_PATH
        )
            throw Error("Admission");
        await physicalDirectory(fileURLToPath(root));
        await physicalDirectory(process.env.TEMP);
        await physicalDirectory(process.env.TMP);
        sourceRevision = await cleanRevision();
        policy = await openFrontendEvidencePolicy({
            sourceRoot: fileURLToPath(root),
            outputDir: process.env.LOCALLORE_CHECK_OUTPUT_DIR,
            admissionFile: process.env.LOCALLORE_CHECK_BUDGET_FILE,
            sourceRevision,
        });
    }
    for (const args of [
        ["check-frontend-evidence-policy-review.mjs"],
        ["comparison-run-process-policy-check.mjs"],
        ["comparison-reader-process-policy-check.mjs"],
        ["check-live-narration-process-policy-review.mjs"],
        ["build.mjs"],
        ["node_modules/typescript/bin/tsc", "--noEmit"],
        ["check-contract.mjs"],
        ["check-v2-view-model.mjs"],
        ["check-v2-routing.mjs"],
        ["check-v2-play-controller.mjs"],
        ["check-v2-inspector-paging-review.mjs"],
        ["check-v2-inspector-paging-focus-review.mjs"],
        ["check-v2-inspector-paging-process-review.mjs"],
        ["check-v2-inspector-paging-path-review.mjs"],
        ["check-v2-receipt-evidence-review.mjs"],
        ["check-v2-recorded-turn-review.mjs"],
        ["check-v2-provenance-fields-review.mjs"],
        ["check-scene-bootstrap-review.mjs"],
        ["check-author-controller.mjs"],
        ["check-author-callback-review.mjs"],
        ["check-author-panel-recovery-review.mjs"],
        ["check-author-broker-retention.mjs"],
        ["check-main-author-context-review.mjs"],
        ["check-export-controller.mjs"],
        ["check-model-controller.mjs"],
        ["check-early-cancel.mjs"],
        ["check-model-refresh.mjs"],
        ["check-model-cleanup-panel.mjs"],
        ["check-inspection-controller.mjs"],
        ["check-trace-controller.mjs"],
        ["check-live-narration-diagnostic-review.mjs"],
        ["check-main-live-narration-diagnostic-review.mjs"],
        ["check-capture-controller.mjs"],
        ["check-capture-review.mjs"],
        ["check-capture-session-close-review.mjs"],
        ["check-evaluation-controller.mjs"],
        ["check-selected-evaluation-controller.mjs"],
        ["check-literal-selected-evaluation.mjs"],
        ["check-selected-scene-v4-review.mjs"],
        ["check-selected-scene-resume-identity-review.mjs"],
        ["check-selected-scene-process-policy-review.mjs"],
        ["check-selected-scene-context-review.mjs"],
        ["check-selected-scene-qualification-budget-review.mjs"],
        ["check-selected-source-freshness-review.mjs"],
        ["check-comparison-run.mjs"],
        ["check-comparison-run-native.mjs"],
        ["check-scene-native-transport-review.mjs"],
        ["check-comparison-reader-native.mjs"],
        ["check-main-comparison-run-native.mjs"],
        ["check-native-comparison-admission-review.mjs"],
        ["check-main-comparison-inspect-lens-review.mjs"],
        ["check-native-close-controller-review.mjs"],
        ["check-native-comparison-abort-review.mjs"],
        ["check-comparison-reader.mjs"],
        ["check-literal-comparison-reader.mjs"],
        ["check-scene-reader-review.mjs"],
        ["check-narration-diagnostic-reader-review.mjs"],
        ["check-comparison-main-review.mjs"],
        ["check-comparison-capability-review.mjs"],
        ["check-archive-controller.mjs"],
        ["check-archive-v3.mjs"],
        ["check-archive-v3-ack.mjs"],
        ["check-archive-v3-selection.mjs"],
        ["check-timeline-controller.mjs"],
        ["check-domain2-timeline-resume-review.mjs"],
        ["check-fork-controller.mjs"],
        ["check-fork-callback-review.mjs"],
        ["check-fork-independent-review.mjs"],
        ["check-memory-maintenance-controller.mjs"],
        ["check-memory-inspection.mjs"],
        ["check-main-memory-inspection-review.mjs"],
        ["check-memory-callback-review.mjs"],
        ["check-broker-retention.mjs"],
        ["check-broker-retention-review.mjs"],
        ["check-broker-retention-incarnation-review.mjs"],
        ["check-broker-surface-review.mjs"],
        ["check-broker-fork-error-review.mjs"],
    ]) {
        if (bounded) {
            await policy.beforeStep(completedSteps);
            const result = await capture(
                process.execPath,
                args,
                {
                    ...process.env,
                    LOCALLORE_CHECK_OUTPUT_DIR:
                        process.env.LOCALLORE_CHECK_OUTPUT_DIR,
                    TEMP: path.join(
                        process.env.LOCALLORE_CHECK_OUTPUT_DIR,
                        "_tmp",
                    ),
                    TMP: path.join(
                        process.env.LOCALLORE_CHECK_OUTPUT_DIR,
                        "_tmp",
                    ),
                },
                limits.childMs,
                limits.streamBytes,
            );
            lastChild = {
                index: completedSteps,
                args,
                ...outcome(result),
                signal: result.signal,
                killAttempted: result.killAttempted,
                noChildCreated: result.noChildCreated,
            };
            if (
                !printJson({
                    kind: "d09_frontend_evidence_step_v1",
                    ...lastChild,
                    stdout: result.stdout,
                    stderr: result.stderr,
                })
            ) {
                runnerReason = "ConsoleBudget";
                await policy.completeStep(completedSteps, {
                    ...outcome(result),
                    truncated: true,
                });
                throw Error("ConsoleBudget");
            }
            await policy.completeStep(completedSteps, outcome(result));
            completedSteps++;
            continue;
        }
        const code = await new Promise((resolve, reject) => {
            const child = spawn(process.execPath, args, {
                cwd: root,
                stdio: "inherit",
                shell: false,
                env: {
                    ...process.env,
                    LOCALLORE_CHECK_OUTPUT_DIR:
                        process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
                        fileURLToPath(new URL("artifacts/checks/", root)),
                },
            });
            child.on("error", reject);
            child.on("close", resolve);
        });
        assert.equal(code, 0, `Frontend check ${args[0]}`);
        completedSteps++;
    }
    if (bounded) {
        if ((await cleanRevision()) !== sourceRevision) throw Error("Source");
        await policy.finish();
    }
    const normal = await readFile(new URL("dist/app.js", root), "utf8");
    for (const marker of [
        "harness_checkpoint",
        "harness_scene_oracle",
        "harness_v2_inspection_paging",
        "timelineBrowser",
        "d08-browser-catalog",
        "D08BrowserDeadline:",
        "d05-page-pending-next",
        "startInspectorPagingTrace",
        "dropNextInspectorPagingReply",
        "D05_PAGING_ROW_",
        "d06-live-recorded",
        "heldNarrationValidation",
        "scene-native-pending",
        "SceneDeadline:",
        "memory-inspection-native-empty",
        "memory_inspection_fixture",
        "harness_reopen",
        "harness_finish",
        "NativeComparisonPortPhaseInvalid",
        "NativeConsentAbortAckInvalid",
        "__D07_MAIN_REVIEW_PROPS",
        "harness_native_comparison_case",
        "harness_scene_model_guards",
        "native_full_comparison_fixture",
        "native-port-denied-actual-native-context-grant-false",
        "uncertain-commit-retry-original-id-once",
        "heldPrepare",
        "harness:durable",
        "restart-retry-does-not-double-apply",
        "harness_oracle",
        "harness_export_case",
        "harness_model_case",
        "real-free-text-potion-committed",
        "query-native-durable-workspace",
        "d05-external-wait",
        "d06-native-default-disabled",
        "d06-external-wait",
        "d07-native-evaluation-checkpoints",
        "actual-native-curated-catalog",
        "lose-curated-start-ack",
        "harness_evaluation_case",
        "full-comparison-inventory",
        "captured-retired-native-owner-positively-drained",
        "harness_comparison_reader_case",
        "harness_selected_case",
        "actual-comparison-reader-native-open",
        "comparison-open",
        "harness_archive_case",
        "harness_archive_v3_fixture",
        "v3-fixed-native-fixture-metadata",
        "ARCHIVE_V3_OBSERVED_A",
        "harness_capture_case",
        "private-capture-native-production-play",
        "MALFORMED_SYNTHETIC_DIRECTOR",
        "d08-native-durable-workspace",
        "d08-timeline-native-durable-workspace",
        "d08-fork-native-durable-workspace",
        "harness_fork_case",
        "harness_memory_case",
        "harness_author_case",
        "AUTHOR_PARENT_MIRA_ONLY",
        "AuthorHeldDeadline",
        "actual-commit-start-ack-dropped",
        "author-native-pending",
        "mounted-evidence-navigation-preserves-native-player-history-receipt-and-canonical-oracle",
        "cold-recorded-turn-actual-reopened-Player-head3-history-without-raw-receipt",
        "memory-native-durable-selected-fixture",
        "MEMORY_ORIGINAL_MIRA_ONLY",
        "legacy-v1-native-migrated-resume",
        "export-snapshot-independent-of-later-turn",
    ])
        assert(
            !normal.includes(marker),
            `Test hook leaked into normal bundle: ${marker}`,
        );
    if (bounded) {
        const line = passMessage + "\n";
        if (!printJson(finalRecord(true), true, Buffer.byteLength(line)))
            throw Error("ConsoleBudget");
        consoleBytes += Buffer.byteLength(line);
        process.stdout.write(line);
    } else console.log(passMessage);
}
try {
    await verifyFrontend();
} catch (cause) {
    if (!bounded) throw cause;
    process.exitCode = 1;
    const category =
        runnerReason ??
        String(cause?.message ?? "Failure")
            .replace(/^FrontendEvidence/, "")
            .slice(0, 64);
    printJson(finalRecord(false, category), true);
}
