// Frozen independent abort ordering oracles. Actual controller + synthetic IPC;
// no native consent, worker, model, cleanup or generation authority is exercised.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";

const desktop = fileURLToPath(new URL("./", import.meta.url));
const built = await build({
    stdin: {
        contents:
            'export { createNativeComparisonRunController } from "./ui/comparison-run-controller"; export { abortHeldNativeComparisonConsent } from "./ui/comparison-run-native-abort";',
        resolveDir: desktop,
        loader: "ts",
    },
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
const {
    createNativeComparisonRunController,
    abortHeldNativeComparisonConsent,
} = await import(
    `data:text/javascript;base64,${Buffer.from(built.outputFiles[0].contents).toString("base64")}`
);
const CLIENT = "11111111-1111-4111-8111-111111111111";
const RUN = "22222222-2222-4222-8222-222222222222";
const TOKEN = "33333333-3333-4333-8333-333333333333";
const tests = [],
    test = (name, run) => tests.push({ name, run });
const clone = (value) => structuredClone(value);
const tick = async () => {
    for (let index = 0; index < 48; index++) await Promise.resolve();
};
const ack = () => ({
    version: 1,
    kind: "native_full_comparison_fixture",
    synthetic: true,
    active: true,
    held: true,
});
const status = (extra = {}) => ({
    version: 2,
    kind: "comparison_run",
    protocol_version: 3,
    input_lane: "approved_native",
    client_id: CLIENT,
    run_id: RUN,
    run_token: TOKEN,
    operation_id: 1,
    comparison_kind: "paired",
    batch: 1,
    phase: "paused",
    running: false,
    error: null,
    completed_scenes: 1,
    completed: false,
    report_ready: true,
    source_matches: true,
    cleanup_required: false,
    cleanup_running: false,
    cause: null,
    ...extra,
});

async function fixture(options = {}) {
    const events = [],
        nativeCalls = [],
        errors = [],
        disposalStates = [];
    let deny = false,
        held = true,
        backendClosed = false,
        disposed = 0,
        released = 0;
    const wouldGrant = [];
    const controller = createNativeComparisonRunController(
        async (command, args) => {
            assert.equal(command, "evaluation_comparison_native");
            nativeCalls.push({ command, ...clone(args) });
            if (args.action === "cleanup_status")
                return {
                    version: 1,
                    kind: "selected_cleanup",
                    cleanup_required: false,
                    running: false,
                    error: null,
                };
            if (args.action === "open") return status();
            if (args.action === "close") {
                events.push("close-rpc");
                assert.equal(args.query.runToken, TOKEN);
                if (options.closeNotDelivered) throw Error("EvaluationIo");
                backendClosed = true;
                return status({
                    phase: "closed",
                    report_ready: false,
                    ...options.closeStatus,
                });
            }
            throw Error(`UnexpectedSyntheticNativeAction:${args.action}`);
        },
        (error) => errors.push(error),
    );
    controller.setContext("synthetic-native-abort-owner", true);
    // Open binds a real controller owner using metadata only. The independent
    // held-consent booleans below are a mock safety oracle, not an active worker.
    await controller.open(RUN);
    assert.equal(controller.get().status?.run_token, TOKEN);
    events.length = 0;
    const invoke = async (command, args) => {
        assert.equal(command, "harness_native_comparison_case");
        assert.deepEqual(Object.keys(args), ["scenario"]);
        if (args.scenario === "deny-execution-consent") {
            events.push("deny");
            if (options.denyFailure === "before-delivery")
                throw Error("EvaluationIo");
            deny = true;
            if (options.denyFailure === "lost-ack") throw Error("EvaluationIo");
            return Object.hasOwn(options, "denyAck")
                ? clone(options.denyAck)
                : ack();
        }
        if (args.scenario === "release-execution-consent") {
            events.push("release");
            held = false;
            released++;
            wouldGrant.push(!deny && !backendClosed);
            return { ...ack(), active: false, held: false };
        }
        throw Error(`UnexpectedSyntheticFixtureScenario:${args.scenario}`);
    };
    const dispose = async () => {
        events.push("dispose");
        disposed++;
        disposalStates.push(clone(controller.get()));
        controller.dispose();
        await tick();
    };
    const full = options.closeThrows
        ? {
              get: () => controller.get(),
              close: async () => {
                  events.push("close-throws");
                  throw Error("EvaluationIo");
              },
          }
        : controller;
    return {
        controller,
        full,
        invoke,
        dispose,
        events,
        nativeCalls,
        errors,
        disposalStates,
        wouldGrant,
        observation: () => ({ deny, held, backendClosed, disposed, released }),
        finish: async () => {
            controller.dispose();
            await tick();
        },
    };
}
function noGeneration(f) {
    assert(
        !f.nativeCalls.some((call) =>
            ["start", "resume", "retry_cleanup"].includes(call.action),
        ),
        "abort never dispatches inference or cleanup retry",
    );
    assert(
        f.wouldGrant.every((allowed) => allowed === false),
        "mock consent release never becomes affirmative",
    );
}
function resultShape(result) {
    assert.deepEqual(Object.keys(result).sort(), [
        "cleanupUnconfirmed",
        "released",
    ]);
    assert.equal(typeof result.released, "boolean");
    assert.equal(typeof result.cleanupUnconfirmed, "boolean");
}

test("actual controller close not delivered resolves uncertain, but acknowledged denial prevents affirmative release", async () => {
    const f = await fixture({ closeNotDelivered: true });
    try {
        const result = await abortHeldNativeComparisonConsent(f);
        resultShape(result);
        assert(
            f.errors.includes("EvaluationIo"),
            "actual controller consumed the transport failure",
        );
        noGeneration(f);
        assert.equal(
            f.events[0],
            "deny",
            "deny ACK precedes even the attempted close",
        );
        assert(f.events.indexOf("close-rpc") < f.events.indexOf("release"));
        assert(f.events.indexOf("release") < f.events.indexOf("dispose"));
        assert.equal(
            f.observation().backendClosed,
            false,
            "close RPC never reached mock backend",
        );
        assert.equal(f.observation().released, 1);
        assert.equal(f.observation().disposed, 1);
        const beforeDispose = f.disposalStates[0];
        assert(
            beforeDispose.uncertain ||
                beforeDispose.cleanupUncertain ||
                beforeDispose.cleanup?.cleanup_required ||
                beforeDispose.cleanupError,
            "actual controller retains conservative uncertainty rather than proving cleanup",
        );
        assert.equal(result.released, true);
        assert.equal(result.cleanupUnconfirmed, true);
        noGeneration(f);
    } finally {
        await f.finish();
    }
});

for (const denyFailure of ["before-delivery", "lost-ack"]) {
    test(`unknown denial ACK ${denyFailure} retains hold and disposes without releasing consent`, async () => {
        const f = await fixture({ denyFailure });
        try {
            const result = await abortHeldNativeComparisonConsent(f);
            resultShape(result);
            assert.equal(result.released, false);
            assert.equal(result.cleanupUnconfirmed, true);
            assert.equal(f.observation().held, true);
            assert.equal(f.observation().released, 0);
            assert.equal(f.observation().disposed, 1);
            assert.equal(f.events[0], "deny");
            assert(
                !f.events.includes("release"),
                "neither uncertain denial outcome authorizes release",
            );
            noGeneration(f);
        } finally {
            await f.finish();
        }
    });
}

test("explicit close rejection after denial still releases only denied consent and always disposes", async () => {
    const f = await fixture({ closeThrows: true });
    try {
        const result = await abortHeldNativeComparisonConsent(f);
        resultShape(result);
        assert.equal(f.events[0], "deny");
        assert(f.events.indexOf("close-throws") < f.events.indexOf("release"));
        assert(f.events.indexOf("release") < f.events.indexOf("dispose"));
        assert.equal(result.released, true);
        assert.equal(result.cleanupUnconfirmed, true);
        assert.equal(f.observation().disposed, 1);
        noGeneration(f);
    } finally {
        await f.finish();
    }
});

for (const active of [true, false])
    test(`valid denial ACK active=${active} orders denial, captured close, safe release and disposal exactly once`, async () => {
        const f = await fixture({ denyAck: { ...ack(), active } });
        try {
            const result = await abortHeldNativeComparisonConsent(f);
            resultShape(result);
            assert.deepEqual(f.events, [
                "deny",
                "close-rpc",
                "release",
                "dispose",
            ]);
            assert.equal(result.released, true);
            assert.equal(result.cleanupUnconfirmed, false);
            assert.deepEqual(f.observation(), {
                deny: true,
                held: false,
                backendClosed: true,
                disposed: 1,
                released: 1,
            });
            noGeneration(f);
        } finally {
            await f.finish();
        }
    });

for (const [name, mutate] of [
    ["extra-key", (value) => ({ ...value, permission: true })],
    ["coerced-active", (value) => ({ ...value, active: "true" })],
    ["not-held", (value) => ({ ...value, held: false })],
    [
        "missing-synthetic",
        (value) => {
            delete value.synthetic;
            return value;
        },
    ],
]) {
    test(`invalid denial fixture ACK ${name} cannot release held consent`, async () => {
        const f = await fixture({ denyAck: mutate(ack()) });
        try {
            const result = await abortHeldNativeComparisonConsent(f);
            resultShape(result);
            assert.equal(result.released, false);
            assert.equal(result.cleanupUnconfirmed, true);
            assert.equal(f.observation().held, true);
            assert.equal(f.observation().disposed, 1);
            assert(!f.events.includes("release"));
            noGeneration(f);
        } finally {
            await f.finish();
        }
    });
}

for (const [name, closeStatus] of [
    ["running service drain", { running: true }],
    [
        "run cleanup required and running",
        { cleanup_required: true, cleanup_running: true },
    ],
]) {
    test(`closed presentation with ${name} remains cleanup-unconfirmed despite actual generic clean observation`, async () => {
        const f = await fixture({ closeStatus });
        try {
            const result = await abortHeldNativeComparisonConsent(f);
            resultShape(result);
            const beforeDispose = f.disposalStates[0];
            assert(beforeDispose, "actual disposal captured controller state");
            assert.equal(beforeDispose.mode, "approved_native");
            assert.equal(beforeDispose.status?.version, 2);
            assert.equal(beforeDispose.status?.phase, "closed");
            for (const [field, value] of Object.entries(closeStatus))
                assert.equal(beforeDispose.status[field], value, `actual controller retained ${field}`);
            assert.deepEqual(beforeDispose.cleanup, {
                version: 1,
                kind: "selected_cleanup",
                cleanup_required: false,
                running: false,
                error: null,
            }, "one actual generic status reply remains separate from run flags");
            assert.equal(
                f.nativeCalls.filter((call) => call.action === "cleanup_status").length,
                1,
                "actual close performs its bounded independent cleanup observation",
            );
            assert.equal(beforeDispose.uncertain, false, "closed identity acknowledgement is not service quiescence");
            assert.equal(beforeDispose.error, null);
            assert.equal(result.released, true);
            assert.equal(f.observation().disposed, 1);
            assert.equal(f.observation().released, 1);
            assert.deepEqual(f.events, ["deny", "close-rpc", "release", "dispose"]);
            noGeneration(f);
            assert.equal(result.cleanupUnconfirmed, true, "positive run drain/cleanup flags cannot be hidden by a clean generic DTO");
        } finally {
            await f.finish();
        }
    });
}

const checks = [];
for (const { name, run } of tests) {
    let timeout;
    try {
        await Promise.race([
            run(),
            new Promise((_, reject) => {
                timeout = setTimeout(
                    () => reject(Error("SyntheticAbortCaseTimeout")),
                    5000,
                );
            }),
        ]);
        checks.push({ name, passed: true });
    } catch (error) {
        checks.push({
            name,
            passed: false,
            error: String(error?.message ?? error).slice(0, 512),
        });
    } finally {
        clearTimeout(timeout);
    }
}
const sourceHashes = {};
for (const name of [
    "ui/comparison-run-native-abort.ts",
    "ui/comparison-run-controller.ts",
    "ui/comparison-run-native-journeys.ts",
])
    sourceHashes[name] = createHash("sha256")
        .update(await readFile(path.join(desktop, name)))
        .digest("hex");
const report = {
    version: 1,
    synthetic: true,
    evidence:
        "actual native comparison controller and extracted abort helper with synthetic IPC/fixture ACKs",
    sourceHashes,
    checks,
    passed: checks.filter((row) => row.passed).length,
    failed: checks.filter((row) => !row.passed).length,
    nativeIpc: false,
    modelExecution: false,
    rendering: "none",
    desktopInput: false,
    limitations: [
        "captured controller metadata owner only; no actual native worker or consent",
        "mock wouldGrant detects ordering, not real provider/reservation counts",
        "cleanupUnconfirmed is conservative frontend abort observation, not native cleanup authority",
    ],
};
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(desktop, "artifacts/checks");
await mkdir(output, { recursive: true });
const json = JSON.stringify(report, null, 2);
assert(Buffer.byteLength(json) <= 64 * 1024);
await writeFile(
    path.join(output, `native-comparison-abort-${randomUUID()}.json`),
    json,
    { flag: "wx" },
);
console.log(json);
if (report.failed) process.exitCode = 1;
