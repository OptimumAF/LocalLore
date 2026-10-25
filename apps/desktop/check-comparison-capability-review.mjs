// Frozen at a6f9eb4d BEFORE capability-loss production changes; SOURCE ONLY.
// Actual controller/closed decoder, bounded synthetic transport. No native IPC,
// Core Receipt construction, DOM/render, inference, Store or model execution.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("./", import.meta.url));
const files = [
    "ui/comparison-reader-controller.ts",
    "ui/comparison-reader-model.ts",
];
const hashes = Object.fromEntries(
    await Promise.all(
        files.map(async (file) => [
            file,
            createHash("sha256")
                .update(await readFile(new URL(file, import.meta.url)))
                .digest("hex"),
        ]),
    ),
);
const built = await build({
    stdin: {
        contents:
            'export { ComparisonReaderController } from "./ui/comparison-reader-controller";',
        resolveDir: root,
        loader: "ts",
    },
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
const { ComparisonReaderController } = await import(
    `data:text/javascript;base64,${Buffer.from(built.outputFiles[0].text).toString("base64")}`
);
const clone = (v) => structuredClone(v);
const token = "22222222-2222-2222-2222-222222222222";
const hash = "a".repeat(64);
const scope = { story: "synthetic-capability", branch: "main" };
const row = { turn: "gift-0", arm: "left" };
const omni = { kind: "omniscient" };
function turn(arm) {
    return {
        turn: row.turn,
        scene: 0,
        arm,
        policy:
            arm === "left"
                ? "state_recent_transcript_v1"
                : "state_relevant_memory_v1",
        phase: "committed",
        error: null,
        expected: "accepted",
        passed: true,
        failures: [],
        quality_flags: [],
        roles: 2,
        roles_known: true,
        recovered_without_checkpoint: false,
        admission: 1,
        elapsed_ms: 1,
        first_final_response_ms: 1,
        commit_elapsed_ms: 0,
        input_semantic_sha256: hash,
        output_semantic_sha256: hash,
        mechanical_sha256: hash,
        policy_matches: true,
        context_evidence_available: true,
        context_requirement: "synthetic",
        privacy_passed: true,
        fallback: false,
        capture_sha256: hash,
        recording_sha256: hash,
        raw_sha256: [hash, hash],
        role_metrics: null,
        trace: { synthetic: true },
        actual_receipt_sha256: hash,
        source_fallback_reason: null,
        compiler_fallback_reason: null,
        narration: "Synthetic private report fixture",
        repairs: 0,
        stages: [],
        mandatory_sha256: hash,
        optional_detail_selected: false,
        director_private_target_present: false,
        selected_context_bytes: 100,
        estimated_context_tokens: 25,
    };
}
const rows = ["left", "right"].map((arm) => ({
    row: { ...row, arm },
    source: {
        status: "available",
        scope,
        before_head: 0,
        after_head: 1,
        input_semantic_sha256: hash,
    },
    capture_available: true,
    receipt_available: true,
    recording_available: true,
    unavailable: [],
}));
const source = {
    binding: hash,
    protocol_version: 2,
    rows,
    read_only: true,
    execution_available: false,
};
const snapshot = {
    version: 1,
    protocol_version: 2,
    binding: hash,
    rows,
    read_only: true,
    execution_available: false,
    unavailable: [
        "selected_rerun_not_implemented",
        "full_comparison_gui_not_implemented",
    ],
    report: {
        version: 2,
        kind: "paired_snapshots",
        lane: "scripted",
        source_matches: false,
        completed: false,
        completed_scenes: 0,
        turns: [turn("left"), turn("right")],
        human_reviewed: 0,
        human_rubric: "Not reviewed",
        quality_accepted: false,
        physical_setups: 0,
        physical_setup_ms: null,
        native_load: null,
        left_charged_ms: 1,
        right_charged_ms: 1,
        left_reserved_roles: 2,
        right_reserved_roles: 2,
        first_semantic_divergence: null,
        first_mechanical_divergence: null,
        same_input_pairs: 1,
        unavailable: ["selected_rerun_not_implemented"],
        profile: {
            id: "synthetic",
            model_sha256: hash,
            runtime_revision: "b".repeat(40),
            template_sha256: hash,
            worker_sha256: hash,
            profile_manifest_sha256: hash,
            context_tokens: 4096,
            director_tokens: 350,
            narrator_tokens: 350,
            deadline_ms: 120000,
            repair_limit: 1,
        },
        suite_sha256: hash,
        source_sha256: hash,
        reference_sha256: null,
        limitations: [
            "Synthetic transport; no native or human quality evidence",
        ],
    },
};
function wrapper(key, value) {
    return {
        version: 1,
        kind: "comparison_reader",
        run_token: token,
        [key]: clone(value),
    };
}
function status(client, phase = "ready") {
    return {
        version: 1,
        kind: "comparison_reader",
        client_id: client,
        operation_id: phase === "closed" ? null : 1,
        phase,
        running: false,
        run_token: phase === "closed" ? null : token,
        binding: phase === "closed" ? null : hash,
        error: null,
        read_only: true,
        execution_available: false,
    };
}
function receiptEvidence() {
    // The renderer contract intentionally transports receipt as inert bounded JSON;
    // this synthetic object is not a Core accepted Receipt or canonical authority.
    return wrapper("evidence", {
        version: 1,
        binding: hash,
        row,
        scope,
        before_head: 0,
        after_head: 1,
        observer: omni,
        edge: "after",
        read_only: true,
        generation_grant: false,
        body: {
            kind: "receipt",
            receipt: { synthetic_private_display: "old-receipt" },
        },
    });
}
function deferred() {
    let resolve, reject;
    const promise = new Promise((yes, no) => {
        resolve = yes;
        reject = no;
    });
    return { promise, resolve, reject };
}
const settle = async () => {
    await Promise.resolve();
    await Promise.resolve();
};
async function fixture() {
    const calls = [],
        hooks = new Map(),
        errors = [];
    const controller = new ComparisonReaderController(
        async (name, args) => {
            assert.equal(name, "evaluation_comparison");
            calls.push(clone(args));
            if (hooks.has(args.action))
                return hooks.get(args.action)(args.query);
            if (args.action === "pick" || args.action === "status")
                return status(args.query.clientId);
            if (args.action === "source") return wrapper("source", source);
            if (args.action === "summary") return wrapper("snapshot", snapshot);
            if (args.action === "evidence") {
                assert.equal(args.query.request.kind, "receipt");
                return receiptEvidence();
            }
            if (args.action === "close")
                return status(args.query.clientId, "closed");
            assert.fail(`UnexpectedNativeAction:${args.action}`);
        },
        (error) => errors.push(error),
    );
    controller.contextChanged("root/window/session/head/Lab", true);
    await controller.pick();
    await controller.loadSummary();
    controller.select(row);
    await controller.inspect({ kind: "receipt", observer: omni });
    assert.equal(controller.get().error, null, "ValidInitialTransport");
    assert.equal(controller.get().status?.phase, "ready");
    assert(controller.get().summary, "ActualDecoderLoadedFullSummary");
    assert.equal(controller.get().evidence?.body.kind, "receipt");
    return { controller, calls, hooks, errors };
}
const results = [];
async function test(name, work) {
    try {
        await work();
        results.push({ name, passed: true });
    } catch (error) {
        results.push({
            name,
            passed: false,
            error: String(error?.message ?? error),
        });
    }
}
for (const [action, error] of [
    ["summary", "UnknownEvaluationRun"],
    ["evidence", "UnknownEvaluationRun"],
    ["summary", "Forbidden"],
    ["evidence", "Closed"],
]) {
    await test(`${action}-${error}-retires-exact-capability-and-private-presentation`, async () => {
        const f = await fixture();
        try {
            const client = f.controller.get().clientId;
            const originalToken = f.controller.get().status.run_token;
            const before = f.calls.length;
            f.hooks.set(action, () => Promise.reject(error));
            if (action === "summary") await f.controller.loadSummary();
            else
                await f.controller.inspect({ kind: "capture", observer: omni });
            await settle();
            const state = f.controller.get();
            assert.equal(state.error, error, "OriginalBoundedFailureVisible");
            assert.equal(state.busy, false);
            assert.equal(
                state.uncertain,
                false,
                "ConfirmedCapabilityLossIsNotUnknownWrite",
            );
            assert.equal(
                state.summary,
                null,
                "RevokedCapabilityCannotKeepPrivateReportPresentation",
            );
            assert.equal(
                state.evidence,
                null,
                "RevokedCapabilityCannotKeepOldBody",
            );
            assert.equal(
                state.source,
                null,
                "RevokedCapabilityCannotRemainSourceReady",
            );
            assert.equal(state.selected, null);
            assert.equal(state.status, null);
            assert.equal(state.clientId, null);
            assert.deepEqual(
                f.calls.slice(before),
                [
                    {
                        action,
                        query:
                            action === "summary"
                                ? { runToken: originalToken }
                                : {
                                      runToken: originalToken,
                                      binding: hash,
                                      turnId: row.turn,
                                      arm: row.arm,
                                      request: {
                                          kind: "capture",
                                          observer: omni,
                                      },
                                  },
                    },
                    {
                        action: "close",
                        query: { clientId: client, runToken: originalToken },
                    },
                ],
                "OnlyExactReadAndOriginalCleanupNoRepickOrGeneration",
            );
            assert.deepEqual(f.errors, [error]);
        } finally {
            f.controller.dispose();
        }
    });
}
await test("integrity-capture-failure-keeps-lastvalidated-summary-but-clears-prior-receipt", async () => {
    const f = await fixture();
    try {
        const before = f.controller.get();
        const gate = deferred();
        f.hooks.set("evidence", () => gate.promise);
        const callCount = f.calls.length;
        const work = f.controller.inspect({ kind: "capture", observer: omni });
        const pending = f.controller.get();
        gate.reject("EvaluationIntegrity");
        await work;
        const failed = f.controller.get();
        assert.equal(pending.busy, true, "ActualNewReadPending");
        assert.equal(
            pending.evidence,
            null,
            "NewReadDoesNotDisplayOlderReceiptAsCurrentEvidence",
        );
        assert.deepEqual(pending.summary, before.summary);
        assert.deepEqual(pending.source, before.source);
        assert.equal(failed.error, "EvaluationIntegrity");
        assert.equal(
            failed.evidence,
            null,
            "FailedCaptureDoesNotLeaveOldReceiptBody",
        );
        assert.equal(failed.busy, false);
        assert.equal(failed.uncertain, false);
        assert.equal(failed.clientId, before.clientId);
        assert.equal(failed.status?.phase, "ready");
        assert.equal(failed.status?.run_token, before.status.run_token);
        assert.deepEqual(failed.selected, before.selected);
        assert.deepEqual(
            failed.summary,
            before.summary,
            "LastValidatedSnapshotNotFreshHealth",
        );
        assert.deepEqual(failed.source, before.source);
        assert.equal(
            f.calls.length,
            callCount + 1,
            "IntegrityDoesNotCloseOrReopenValidCapability",
        );
        assert.equal(f.calls.at(-1).action, "evidence");
        assert.deepEqual(f.errors, ["EvaluationIntegrity"]);
    } finally {
        f.controller.dispose();
    }
});
assert.equal(results.length, 5, "ExactlyFiveFrozenCases");
console.log(
    JSON.stringify(
        {
            version: 1,
            sourceHashes: hashes,
            syntheticTransport: true,
            actualController: true,
            nativeIpc: false,
            rendering: false,
            modelExecution: false,
            canonicalWrites: false,
            passed: results.filter((v) => v.passed).length,
            failed: results.filter((v) => !v.passed).length,
            results,
        },
        null,
        2,
    ),
);
if (results.some((v) => !v.passed)) process.exitCode = 1;
