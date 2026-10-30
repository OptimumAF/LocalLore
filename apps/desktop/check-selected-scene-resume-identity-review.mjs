// Independent POST-PRODUCTION regression, source-only/uncompiled/unrun at handoff.
// Authored after frontend production24de4bac; never pre-implementation FIRST.
// Actual SelectedEvaluationController + synthetic selected status/ACK transport.
// No Core histories, native grants/IPC, UI/DOM/pixels, provider/model/device proof.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID, webcrypto } from "node:crypto";
import { setImmediate as tick } from "node:timers/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

globalThis.crypto ??= webcrypto;
const root = fileURLToPath(new URL(".", import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
const SOURCE_OLD = "a".repeat(64),
    SOURCE_REQUESTED = "b".repeat(64),
    SOURCE_OTHER = "c".repeat(64);
const MANIFEST = "d".repeat(64),
    READ = "e".repeat(64),
    PREFIX = "f".repeat(64);
const RUN = "11111111-1111-1111-1111-111111111111",
    PLAN = "22222222-2222-2222-2222-222222222222";
const READER = "33333333-3333-3333-3333-333333333333",
    READ_TOKEN = "44444444-4444-4444-4444-444444444444";
const selection = { turn: "courier-05", clicked_arm: "left", index: 4 };
const scope = { story: "resume-identity-synthetic", branch: "isolated-main" };
const clone = (value) => structuredClone(value);
const descriptors3 = [
    {
        arm: "literal_player_v1",
        prompt_version: "locallore-play-v2.6-literal-director-v1",
        narration_policy: "grounded-prose-v2.2",
        director_schema_id: "locallore-director-literal-v1",
        context_policy: null,
        compiler_version: null,
        context_version: null,
        literal_source_version: 1,
        literal_render_version: 1,
        literal_schema_version: 1,
        literal_packing_version: 1,
        forwarded_budget_version: 1,
    },
    {
        arm: "relevant_memory_v1",
        prompt_version: "locallore-play-v2.5",
        narration_policy: "grounded-prose-v2.2",
        director_schema_id: "locallore-director-v2",
        context_policy: "state_relevant_memory_v1",
        compiler_version: 2,
        context_version: 2,
        literal_source_version: null,
        literal_render_version: null,
        literal_schema_version: null,
        literal_packing_version: null,
        forwarded_budget_version: 1,
    },
];
const descriptors4 = [
    {
        ...descriptors3[0],
        arm: "literal_scene_v1",
        prompt_version:
            "locallore-play-v2.10-literal-director-v1-scene-frame-v1",
        narration_policy: "grounded-prose-v2.4-scene-frame-v1",
        narrator_schema_id: "locallore-narrator-v2",
        scene_frame_version: 1,
        scene_capture_gate_version: 1,
    },
    {
        ...descriptors3[1],
        arm: "relevant_memory_scene_v1",
        prompt_version: "locallore-play-v2.9-scene-frame-v1",
        narration_policy: "grounded-prose-v2.4-scene-frame-v1",
        narrator_schema_id: "locallore-narrator-v2",
        scene_frame_version: 1,
        scene_capture_gate_version: 1,
    },
];
function prepared(version, binding) {
    return {
        version,
        kind: "selected_prepared",
        binding: MANIFEST,
        lane: "scripted_selected_case",
        selection: clone(selection),
        arms: ["left", "right"].map((arm) => ({
            arm,
            scope: clone(scope),
            before_head: 2,
            prefix_sha256: PREFIX,
            input_semantic_sha256: PREFIX,
        })),
        ...(version === 3 ? { source_binding: binding } : {}),
        ...(version === 1
            ? {}
            : {
                  source_protocol_version: version + 1,
                  constructions: clone(
                      version === 3 ? descriptors4 : descriptors3,
                  ),
              }),
    };
}
let sourceSerial = 500;
function source(binding = SOURCE_OLD) {
    return {
        readerClientId: READER,
        runToken: `${(++sourceSerial).toString(16).padStart(8, "0")}-5555-5555-5555-555555555555`,
        binding,
    };
}

async function main() {
    assert(path.isAbsolute(output), "AbsoluteCheckOutputRequired");
    await mkdir(output, { recursive: true });
    const prefix = `selected-scene-resume-identity-${randomUUID()}`;
    const names = [
        "check-selected-scene-resume-identity-review.mjs",
        "ui/selected-evaluation-controller.ts",
        "ui/selected-evaluation-model.ts",
        "ui/comparison-reader-model.ts",
    ];
    const sourceHashes = Object.fromEntries(
        await Promise.all(
            names.map(async (name) => [
                name,
                createHash("sha256")
                    .update(await readFile(path.join(root, name)))
                    .digest("hex"),
            ]),
        ),
    );
    const cases = [],
        controllers = new Set(),
        holds = new Set();
    const writeReport = async (setupError = null) => {
        const report = {
            version: 1,
            kind: "selected_scene_resume_identity_post_production_regression",
            sourceHashes,
            authorBase: "24de4bacd965ea27f0098cfc5e37526bde3b233a",
            contractPrecision:
                "9ae23b34 retained preparation versus pending resume identity",
            evidence:
                "Actual controller with synthetic selected status/ACK invoke. Post-production independent regression, not earlier FIRST or native evidence.",
            setup: setupError === null ? "ready" : "SETUP_UNRUN",
            setupError,
            executed: cases.length,
            passed: cases.filter((v) => v.passed).length,
            failed: cases.filter((v) => !v.passed).length,
            cases,
            limitations: [
                "These status objects do not construct native plans, histories, grants or receipts.",
                "A synthetic successful changed-source reply exercises controller promotion only. Current native index/source equality normally refuses a genuinely different full source binding; no real source-rebind permission is claimed.",
                "A status ACK loss or held Promise is a synthetic transport condition, not native process death, a held inference worker or real engine cancellation.",
                "No Rust/host_call/native IPC/WebView, rendering, pixels, model, SDK/device or OS execution.",
            ],
        };
        await writeFile(
            path.join(output, `${prefix}.json`),
            JSON.stringify(report, null, 2),
            { flag: "wx" },
        );
        console.log(JSON.stringify(report));
        if (setupError !== null || report.failed || report.executed === 0)
            process.exitCode = 1;
    };
    let Controller;
    try {
        const built = await build({
            stdin: {
                contents:
                    'export {SelectedEvaluationController} from "./ui/selected-evaluation-controller";',
                resolveDir: root,
                loader: "ts",
            },
            bundle: true,
            platform: "node",
            format: "cjs",
            write: false,
        });
        assert.equal(built.outputFiles.length, 1);
        const bundle = path.join(output, `${prefix}.cjs`);
        await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
        Controller = (await import(pathToFileURL(bundle).href)).default
            .SelectedEvaluationController;
        assert.equal(
            typeof Controller,
            "function",
            "ActualSelectedControllerRequired",
        );
        for (const method of [
            "prepare",
            "start",
            "open",
            "resume",
            "status",
            "setContext",
            "get",
            "dispose",
        ])
            assert.equal(
                typeof Controller.prototype[method],
                "function",
                `ActualMethod:${method}`,
            );
    } catch (error) {
        await writeReport(String(error?.message ?? error).slice(0, 1000));
        return;
    }
    async function flush() {
        for (let i = 0; i < 12; i++) await Promise.resolve();
        await tick();
    }
    function hold() {
        let resolve;
        const promise = new Promise((r) => {
            resolve = r;
        });
        const value = {
            promise,
            resolve: (reply) => {
                holds.delete(value);
                resolve(reply);
            },
        };
        holds.add(value);
        return value;
    }
    async function check(name, body) {
        let timer;
        try {
            await Promise.race([
                Promise.resolve().then(body),
                new Promise((_, reject) => {
                    timer = setTimeout(
                        () => reject(Error("FiniteRegressionCaseTimeout")),
                        3000,
                    );
                }),
            ]);
            cases.push({ name, passed: true });
        } catch (error) {
            cases.push({
                name,
                passed: false,
                error: String(error?.message ?? error).slice(0, 600),
            });
        } finally {
            clearTimeout(timer);
            for (const pending of [...holds]) pending.resolve(undefined);
            for (const c of controllers) c.dispose();
            controllers.clear();
            await flush();
        }
    }
    function fixture(version = 3) {
        const calls = [],
            hooks = new Map(),
            errors = [];
        let next = 0,
            live = null,
            currentClient = null;
        const reply = ({
            client = currentClient,
            phase = "completed",
            sourceBinding = SOURCE_OLD,
            present = true,
            error = null,
            operation = ++next,
            reading = phase === "completed" || phase === "paused",
            cleanup = false,
            metadataVersion = version,
        } = {}) => {
            next = Math.max(next, operation ?? 0);
            const value = {
                version: 1,
                kind: "selected_evaluation",
                client_id: client,
                operation_id: operation,
                phase,
                running: ["preparing", "running", "cancelling"].includes(phase),
                lane: phase === "closed" ? null : "scripted_baseline",
                plan_token: phase === "prepared" ? PLAN : null,
                run_id: phase === "prepared" ? null : RUN,
                run_token: reading ? READ_TOKEN : null,
                binding: reading ? READ : null,
                prepared: present
                    ? prepared(metadataVersion, sourceBinding)
                    : null,
                error,
                cause: null,
                cleanup_required: cleanup,
            };
            if (phase === "closed")
                Object.assign(value, {
                    plan_token: null,
                    run_id: null,
                    run_token: null,
                    binding: null,
                    prepared: null,
                });
            live = clone(value);
            return clone(value);
        };
        const c = new Controller(
            async (command, args) => {
                assert.equal(command, "evaluation_selected");
                assert.deepEqual(Object.keys(args).sort(), [
                    "action",
                    "request",
                ]);
                const body = JSON.parse(args.request),
                    action = args.action;
                calls.push({ action, body });
                if (body.clientId) currentClient = body.clientId;
                if (hooks.has(action)) return hooks.get(action)(body);
                if (action === "prepare")
                    return reply({
                        client: body.clientId,
                        phase: "prepared",
                        sourceBinding: body.binding,
                        reading: false,
                    });
                if (action === "start")
                    return reply({ client: body.clientId, reading: false });
                if (action === "open")
                    return reply({ client: body.clientId, present: false });
                if (action === "resume")
                    return reply({
                        client: body.clientId,
                        sourceBinding: body.sourceBinding,
                    });
                if (action === "status") return clone(live);
                if (action === "close")
                    return reply({
                        client: body.clientId,
                        phase: "closed",
                        present: false,
                        reading: false,
                    });
                if (action === "cleanup_status" || action === "retry_cleanup")
                    return {
                        version: 1,
                        kind: "selected_cleanup",
                        cleanup_required: false,
                        running: false,
                        error: null,
                    };
                throw Error("UnexpectedSyntheticResumeAction");
            },
            (error) => {
                errors.push(error);
            },
        );
        controllers.add(c);
        c.setContext("original-session-scope-head", true);
        return {
            c,
            calls,
            hooks,
            errors,
            reply,
            version,
            current: () => clone(live),
        };
    }
    async function baseline(f) {
        // Public lifecycle only; the mock mirrors native Open clearing prepared
        // metadata and successful same-source Resume retaining it again.
        await f.c.prepare(
            source(),
            { turn: selection.turn, arm: selection.clicked_arm },
            "scripted_baseline",
            f.version + 1,
        );
        assert.equal(f.c.get().status.phase, "prepared");
        await f.c.start();
        assert.equal(f.c.get().status.run_token, null);
        await f.c.open(RUN);
        assert.equal(f.c.get().status.prepared, null);
        await f.c.resume(source());
        assert.equal(f.c.get().error, null);
        assert.equal(f.c.get().status.prepared.version, f.version);
        if (f.version === 3)
            assert.equal(f.c.get().status.prepared.source_binding, SOURCE_OLD);
        return {
            client: f.c.get().clientId,
            operation: f.c.get().status.operation_id,
        };
    }
    const boundSource = (f) => f.c.get().status?.prepared?.source_binding;
    function assertNoReplay(f, before, client) {
        assert.equal(f.c.get().clientId, client);
        assert.equal(f.calls.filter((v) => v.action === "prepare").length, 1);
        assert.equal(f.calls.filter((v) => v.action === "start").length, 1);
        for (const call of f.calls
            .slice(before)
            .filter((v) => v.action === "resume")) {
            assert.equal(call.body.clientId, client);
            assert.equal(call.body.runToken, READ_TOKEN);
            assert.deepEqual(Object.keys(call.body).sort(), [
                "clientId",
                "readerClientId",
                "runToken",
                "sourceBinding",
                "sourceToken",
            ]);
        }
    }
    for (const version of [1, 2, 3])
        await check(
            `version${version}: failed different-source resume keeps old prepared identity and honest native mismatch`,
            async () => {
                const f = fixture(version),
                    old = await baseline(f),
                    before = f.calls.length;
                f.hooks.set("resume", () =>
                    f.reply({
                        phase: "failed",
                        sourceBinding: SOURCE_OLD,
                        error: "EvaluationSourceMismatch",
                        reading: false,
                    }),
                );
                await f.c.resume(source(SOURCE_REQUESTED));
                assert.equal(f.c.get().error, "EvaluationSourceMismatch");
                assert.equal(
                    f.c.get().status.error,
                    "EvaluationSourceMismatch",
                );
                assert.equal(f.c.get().uncertain, false);
                if (version === 3) assert.equal(boundSource(f), SOURCE_OLD);
                assertNoReplay(f, before, old.client);
            },
        );
    for (const binding of [SOURCE_REQUESTED, SOURCE_OTHER])
        await check(
            `version3: error metadata with unsolicited ${binding[0]} binding is a wire refusal, not blanket error exemption`,
            async () => {
                const f = fixture(),
                    old = await baseline(f);
                f.hooks.set("resume", () =>
                    f.reply({
                        phase: "failed",
                        sourceBinding: binding,
                        error: "EvaluationSourceMismatch",
                        reading: false,
                    }),
                );
                await f.c.resume(source(SOURCE_REQUESTED));
                assert.equal(f.c.get().error, "SelectedEvaluationWire");
                assert.equal(boundSource(f), SOURCE_OLD);
                const operation = f.current().operation_id;
                f.hooks.set("status", () =>
                    f.reply({
                        phase: "failed",
                        operation,
                        sourceBinding: SOURCE_OLD,
                        error: "EvaluationSourceMismatch",
                        reading: false,
                    }),
                );
                await f.c.status();
                assert.equal(f.c.get().error, "EvaluationSourceMismatch");
                assert.equal(boundSource(f), SOURCE_OLD);
                assert.equal(f.c.get().clientId, old.client);
            },
        );
    for (const mode of ["mismatch", "success"])
        await check(
            `version3: preparing and running retain old metadata before ${mode} terminal reply`,
            async () => {
                const f = fixture();
                await baseline(f);
                const operation = f.current().operation_id + 1;
                const first = hold(),
                    firstEntered = hold(),
                    second = hold(),
                    secondEntered = hold();
                let reads = 0;
                f.hooks.set("resume", () =>
                    f.reply({
                        phase: "preparing",
                        operation,
                        sourceBinding: SOURCE_OLD,
                        reading: false,
                    }),
                );
                f.hooks.set("status", () => {
                    reads++;
                    if (reads === 1) {
                        firstEntered.resolve(true);
                        return first.promise;
                    }
                    secondEntered.resolve(true);
                    return second.promise;
                });
                const pending = f.c.resume(source(SOURCE_REQUESTED));
                await flush();
                assert.equal(f.c.get().status.phase, "preparing");
                assert.equal(boundSource(f), SOURCE_OLD);
                assert.equal(f.c.get().error, null);
                assert.equal(await firstEntered.promise, true);
                first.resolve(
                    f.reply({
                        phase: "running",
                        operation,
                        sourceBinding: SOURCE_OLD,
                        reading: false,
                    }),
                );
                assert.equal(await secondEntered.promise, true);
                assert.equal(f.c.get().status.phase, "running");
                assert.equal(boundSource(f), SOURCE_OLD);
                assert.equal(f.c.get().error, null);
                second.resolve(
                    mode === "mismatch"
                        ? f.reply({
                              phase: "failed",
                              operation,
                              sourceBinding: SOURCE_OLD,
                              error: "EvaluationSourceMismatch",
                              reading: false,
                          })
                        : f.reply({
                              operation,
                              sourceBinding: SOURCE_REQUESTED,
                          }),
                );
                await pending;
                assert.equal(
                    f.c.get().error,
                    mode === "mismatch" ? "EvaluationSourceMismatch" : null,
                );
                assert.equal(
                    boundSource(f),
                    mode === "mismatch" ? SOURCE_OLD : SOURCE_REQUESTED,
                );
            },
        );
    for (const phase of ["completed", "paused"])
        await check(
            `version3: ${phase} success validates requested source then binds later responses to it`,
            async () => {
                const f = fixture();
                await baseline(f);
                const operation = f.current().operation_id + 1;
                f.hooks.set("resume", () =>
                    f.reply({
                        phase,
                        operation,
                        sourceBinding: SOURCE_REQUESTED,
                    }),
                );
                await f.c.resume(source(SOURCE_REQUESTED));
                assert.equal(f.c.get().error, null);
                assert.equal(boundSource(f), SOURCE_REQUESTED);
                f.hooks.set("status", () =>
                    f.reply({ phase, operation, sourceBinding: SOURCE_OLD }),
                );
                await f.c.status();
                assert.equal(f.c.get().error, "SelectedEvaluationWire");
                assert.equal(boundSource(f), SOURCE_REQUESTED);
            },
        );
    for (const mode of ["old", "other", "missing", "wrong-version"])
        await check(
            `version3: terminal resume success rejects ${mode} preparation before promotion`,
            async () => {
                const f = fixture();
                await baseline(f);
                const operation = f.current().operation_id + 1;
                f.hooks.set("resume", () =>
                    f.reply({
                        operation,
                        sourceBinding:
                            mode === "other" ? SOURCE_OTHER : SOURCE_OLD,
                        present: mode !== "missing",
                        metadataVersion: mode === "wrong-version" ? 2 : 3,
                    }),
                );
                await f.c.resume(source(SOURCE_REQUESTED));
                assert.equal(f.c.get().error, "SelectedEvaluationWire");
                assert.equal(boundSource(f), SOURCE_OLD);
                // A correct same-operation recovery must still validate the pending
                // request, rather than treating the rejected reply as an expectation.
                f.hooks.set("status", () =>
                    f.reply({ operation, sourceBinding: SOURCE_REQUESTED }),
                );
                await f.c.status();
                assert.equal(f.c.get().error, null);
                assert.equal(boundSource(f), SOURCE_REQUESTED);
            },
        );
    for (const error of [
        "EvaluationSourceMismatch",
        "Cancelled",
        "EvaluationIntegrity",
    ])
        await check(
            `version3: terminal ${error} clears requested-source expectation; unsolicited later B cannot promote`,
            async () => {
                const f = fixture();
                await baseline(f);
                const operation = f.current().operation_id + 1;
                f.hooks.set("resume", () =>
                    f.reply({
                        phase: "failed",
                        operation,
                        error,
                        sourceBinding: SOURCE_OLD,
                        reading: false,
                    }),
                );
                await f.c.resume(source(SOURCE_REQUESTED));
                assert.equal(f.c.get().error, error);
                assert.equal(boundSource(f), SOURCE_OLD);
                f.hooks.set("status", () =>
                    f.reply({ operation, sourceBinding: SOURCE_REQUESTED }),
                );
                await f.c.status();
                assert.equal(f.c.get().error, "SelectedEvaluationWire");
                assert.equal(boundSource(f), SOURCE_OLD);
            },
        );
    await check(
        "version3: failed resume may omit retained metadata without acquiring a new source expectation",
        async () => {
            const f = fixture();
            await baseline(f);
            const operation = f.current().operation_id + 1;
            f.hooks.set("resume", () =>
                f.reply({
                    phase: "failed",
                    operation,
                    present: false,
                    error: "EvaluationSourceMismatch",
                    reading: false,
                }),
            );
            await f.c.resume(source(SOURCE_REQUESTED));
            assert.equal(f.c.get().error, "EvaluationSourceMismatch");
            assert.equal(f.c.get().status.prepared, null);
            f.hooks.set("status", () =>
                f.reply({ operation, sourceBinding: SOURCE_REQUESTED }),
            );
            await f.c.status();
            assert.equal(f.c.get().error, "SelectedEvaluationWire");
        },
    );
    for (const result of ["success", "mismatch"])
        await check(
            `version3: lost resume ACK recovers ${result} through same-client status without replay`,
            async () => {
                const f = fixture(),
                    old = await baseline(f),
                    before = f.calls.length,
                    operation = old.operation + 1;
                f.hooks.set("resume", () => {
                    throw Error("EvaluationIo");
                });
                const requested = source(SOURCE_REQUESTED);
                await f.c.resume(requested);
                assert.equal(f.c.get().uncertain, true);
                assert.equal(boundSource(f), SOURCE_OLD);
                await f.c.resume(requested);
                assert.equal(
                    f.calls.slice(before).filter((v) => v.action === "resume")
                        .length,
                    1,
                );
                f.hooks.set("status", () =>
                    result === "success"
                        ? f.reply({
                              operation,
                              sourceBinding: SOURCE_REQUESTED,
                          })
                        : f.reply({
                              phase: "failed",
                              operation,
                              sourceBinding: SOURCE_OLD,
                              error: "EvaluationSourceMismatch",
                              reading: false,
                          }),
                );
                await f.c.status();
                assert.equal(f.c.get().uncertain, false);
                assert.equal(
                    f.c.get().error,
                    result === "success" ? null : "EvaluationSourceMismatch",
                );
                assert.equal(
                    boundSource(f),
                    result === "success" ? SOURCE_REQUESTED : SOURCE_OLD,
                );
                assertNoReplay(f, before, old.client);
            },
        );
    await check(
        "version3: old-operation ACK after lost resume never promotes requested binding; later new-operation status may recover it",
        async () => {
            const f = fixture(),
                old = await baseline(f);
            f.hooks.set("resume", () => {
                throw Error("EvaluationIo");
            });
            await f.c.resume(source(SOURCE_REQUESTED));
            f.hooks.set("status", () =>
                f.reply({
                    operation: old.operation,
                    sourceBinding: SOURCE_OLD,
                }),
            );
            await f.c.status();
            assert.equal(boundSource(f), SOURCE_OLD);
            assert.equal(f.c.get().status.operation_id, old.operation);
            f.hooks.set("status", () =>
                f.reply({
                    operation: old.operation + 1,
                    sourceBinding: SOURCE_REQUESTED,
                }),
            );
            await f.c.status();
            assert.equal(f.c.get().error, null);
            assert.equal(boundSource(f), SOURCE_REQUESTED);
        },
    );
    await check(
        "version3: a running resume cannot silently change its acknowledged operation identity",
        async () => {
            const f = fixture();
            await baseline(f);
            const operation = f.current().operation_id + 1;
            f.hooks.set("resume", () =>
                f.reply({
                    phase: "running",
                    operation,
                    sourceBinding: SOURCE_OLD,
                    reading: false,
                }),
            );
            f.hooks.set("status", () =>
                f.reply({
                    operation: operation + 1,
                    sourceBinding: SOURCE_REQUESTED,
                }),
            );
            await f.c.resume(source(SOURCE_REQUESTED));
            assert.equal(f.c.get().error, "SelectedEvaluationWire");
            assert.equal(boundSource(f), SOURCE_OLD);
        },
    );
    for (const stage of [
        "before-dispatch",
        "delayed-success",
        "delayed-failure",
    ])
        await check(
            `version3: context retirement ${stage} cannot publish or promote old resume state`,
            async () => {
                const f = fixture(),
                    old = await baseline(f);
                let retired = false;
                if (stage === "before-dispatch")
                    f.c.subscribe(() => {
                        if (
                            !retired &&
                            f.c.get().pending?.action === "resume"
                        ) {
                            retired = true;
                            f.c.setContext("replacement-context", true);
                        }
                    });
                const pendingReply = hold();
                if (stage !== "before-dispatch")
                    f.hooks.set("resume", () => pendingReply.promise);
                const before = f.calls.length,
                    pending = f.c.resume(source(SOURCE_REQUESTED));
                await flush();
                if (stage === "before-dispatch") {
                    await pending;
                    assert(retired);
                    assert(
                        !f.calls
                            .slice(before)
                            .some((v) => v.action === "resume"),
                    );
                } else {
                    f.c.setContext("replacement-context", true);
                    pendingReply.resolve(
                        stage === "delayed-success"
                            ? f.reply({
                                  operation: old.operation + 1,
                                  sourceBinding: SOURCE_REQUESTED,
                              })
                            : f.reply({
                                  phase: "failed",
                                  operation: old.operation + 1,
                                  sourceBinding: SOURCE_OLD,
                                  error: "EvaluationSourceMismatch",
                                  reading: false,
                              }),
                    );
                    await pending;
                    await flush();
                    assert(
                        f.calls.some(
                            (v) =>
                                v.action === "close" &&
                                v.body.clientId === old.client,
                        ),
                    );
                }
                assert.equal(f.c.get().context, "replacement-context");
                assert.equal(f.c.get().clientId, null);
                assert.equal(f.c.get().status, null);
                assert.equal(f.c.get().summary, null);
            },
        );
    await check(
        "version3: disposal with a held resume cannot resurrect its old source or read capability",
        async () => {
            const f = fixture(),
                old = await baseline(f),
                replyGate = hold();
            f.hooks.set("resume", () => replyGate.promise);
            const pending = f.c.resume(source(SOURCE_REQUESTED));
            await flush();
            f.c.dispose();
            replyGate.resolve(
                f.reply({
                    operation: old.operation + 1,
                    sourceBinding: SOURCE_REQUESTED,
                }),
            );
            await pending;
            await flush();
            assert.equal(f.c.get().allowed, false);
            assert.equal(f.c.get().status, null);
            assert.equal(f.c.get().clientId, null);
        },
    );
    for (const version of [1, 2])
        await check(
            `old selected${version}: valid terminal resume success remains supported without invented V3 source_binding`,
            async () => {
                const f = fixture(version);
                await baseline(f);
                await f.c.resume(source(SOURCE_REQUESTED));
                assert.equal(f.c.get().error, null);
                assert.equal(f.c.get().status.prepared.version, version);
                assert.equal(
                    Object.hasOwn(f.c.get().status.prepared, "source_binding"),
                    false,
                );
            },
        );
    await check(
        "version3: observer-only change preserves pending resume/client while private body stays cleared",
        async () => {
            const f = fixture(),
                old = await baseline(f),
                replyGate = hold();
            f.hooks.set("resume", () => replyGate.promise);
            const before = f.calls.length,
                pending = f.c.resume(source(SOURCE_REQUESTED));
            await flush();
            f.c.setObserver({ kind: "character", id: "mira" });
            assert.equal(f.c.get().clientId, old.client);
            assert.equal(f.c.get().evidence, null);
            assert.equal(f.c.get().diagnostics, null);
            assert(
                !f.calls
                    .slice(before)
                    .some((v) => v.action === "cancel" || v.action === "close"),
            );
            replyGate.resolve(
                f.reply({
                    operation: old.operation + 1,
                    sourceBinding: SOURCE_REQUESTED,
                }),
            );
            await pending;
            assert.equal(f.c.get().error, null);
            assert.equal(boundSource(f), SOURCE_REQUESTED);
        },
    );
    await check(
        "version3: cleanup failure retains old identity, blocks replay and never promotes requested source after recovery",
        async () => {
            const f = fixture();
            await baseline(f);
            const operation = f.current().operation_id + 1;
            f.hooks.set("resume", () =>
                f.reply({
                    phase: "cleanup_required",
                    operation,
                    sourceBinding: SOURCE_OLD,
                    error: "Cleanup",
                    cleanup: true,
                    reading: false,
                }),
            );
            await f.c.resume(source(SOURCE_REQUESTED));
            assert.equal(f.c.get().error, "Cleanup");
            assert.equal(boundSource(f), SOURCE_OLD);
            assert.equal(f.c.get().cleanup.cleanup_required, true);
            const before = f.calls.filter((v) => v.action === "resume").length;
            await f.c.resume(source(SOURCE_REQUESTED));
            assert.equal(
                f.calls.filter((v) => v.action === "resume").length,
                before,
            );
            await f.c.retryCleanup();
            assert.equal(f.c.get().cleanup.cleanup_required, false);
            await f.c.open(RUN);
            f.hooks.set("status", () =>
                f.reply({ operation, sourceBinding: SOURCE_REQUESTED }),
            );
            await f.c.status();
            assert.equal(f.c.get().error, "SelectedEvaluationWire");
        },
    );

    await writeReport();
}
await main();
