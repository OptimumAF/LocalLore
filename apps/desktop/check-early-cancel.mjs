// Deferred actual-controller admission, not a second cancellation implementation.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { randomUUID } from "node:crypto";
const directory =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("artifacts/checks/", import.meta.url));
await mkdir(directory, { recursive: true });
const target = path.join(directory, `early-cancel-${randomUUID()}.mjs`);
const compiled = await build({
    entryPoints: [fileURLToPath(new URL("ui/controller.ts", import.meta.url))],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
await writeFile(target, compiled.outputFiles[0].contents);
const { Controller } = await import(pathToFileURL(target).href);
for (const schedule of [
    "admitted",
    "rejected",
    "lost-ack",
    "recovery-cancel",
    "switch",
]) {
    const first = {
        id: "a",
        name: "Synthetic A",
        scope: { story: "early-a", branch: "main" },
        revision: 0,
    };
    const second = {
        id: "b",
        name: "Synthetic B",
        scope: { story: "early-b", branch: "main" },
        revision: 0,
    };
    const calls = [];
    let release;
    let admitted = false;
    let request;
    let releaseLookup;
    let lookupCount = 0;
    const terminal = (phase) => ({
        scope: request.scope,
        turn: request.turn,
        expected_revision: 0,
        phase,
        error: null,
        receipt: null,
    });
    const gateway = {
        async call(command) {
            calls.push(command);
            if (command.op === "open") return { revision: 0 };
            if (command.op === "play_snapshot")
                return {
                    scope: command.scope,
                    revision: 0,
                    rules: "fantasy_v1",
                    inventory: { potion: { quantity: 1 } },
                    receipts: [],
                    player: {
                        scope: command.scope,
                        revision: 0,
                        observer: "player",
                        self_state: {
                            name: "Rowan",
                            energy: 2,
                            location: "quay",
                        },
                        facts: {},
                        beliefs: [],
                        observations: [],
                    },
                };
            if (command.op === "inspect" || command.op === "close") return {};
            if (command.op === "submit") {
                assert.equal(
                    request,
                    undefined,
                    "a known admitted key is never resubmitted",
                );
                request = command.request;
                return new Promise((resolve, reject) => {
                    release = () => {
                        if (schedule === "rejected") {
                            reject(new Error("Rule"));
                            return;
                        }
                        admitted = true;
                        if (["lost-ack", "recovery-cancel"].includes(schedule))
                            reject(new Error("Transport"));
                        else resolve(terminal("queued"));
                    };
                });
            }
            if (command.op === "cancel" || command.op === "turn_status") {
                assert.equal(
                    admitted,
                    true,
                    "native control must follow admission acknowledgement or recovery",
                );
                assert.equal(command.session, first.id);
                assert.equal(command.turn, request.turn);
                if (
                    schedule === "recovery-cancel" &&
                    command.op === "turn_status" &&
                    ++lookupCount === 1
                )
                    return new Promise((_resolve, reject) => {
                        releaseLookup = () => reject(new Error("Transport"));
                    });
                return terminal(
                    command.op === "cancel" ? "cancelled" : "queued",
                );
            }
            throw new Error(`Unexpected ${command.op}`);
        },
    };
    const controller = new Controller(gateway);
    await controller.attach(first);
    controller.setAction("wait");
    const work = controller.send();
    assert(controller.get().pending);
    assert.equal(typeof release, "function");
    if (schedule === "switch") await controller.attach(second);
    else if (schedule !== "recovery-cancel") await controller.cancel();
    assert.equal(
        calls.filter((c) => c.op === "cancel").length,
        0,
        "no speculative control before submit reply",
    );
    assert.notEqual(controller.get().visibleError, "TransportUnknown");
    release();
    await work;
    if (["lost-ack", "recovery-cancel"].includes(schedule)) {
        assert.equal(
            controller.get().visibleError,
            "TransportUnknown",
            "lost acknowledgement remains honestly uncertain",
        );
        if (schedule === "recovery-cancel") {
            const recovery = controller.retry();
            assert.equal(typeof releaseLookup, "function");
            await controller.cancel();
            assert.equal(controller.get().turnStatus.phase, "cancelled");
            releaseLookup();
            await recovery;
        } else await controller.retry();
        assert.equal(controller.get().turnStatus.phase, "cancelled");
        assert.equal(controller.get().visibleError, null);
        assert.equal(
            calls.filter((c) => c.op === "turn_status").length,
            schedule === "recovery-cancel" ? 2 : 1,
        );
    } else if (schedule === "rejected") {
        assert.equal(controller.get().turnStatus.phase, "rejected");
        assert.equal(controller.get().visibleError, "Rule");
        assert.equal(calls.filter((c) => c.op === "cancel").length, 0);
    } else if (schedule === "switch") {
        assert.equal(controller.selected().id, second.id);
        assert.equal(controller.get().turnStatus, null);
        assert.equal(controller.get().visibleError, null);
    } else {
        assert.equal(controller.get().turnStatus.phase, "cancelled");
        assert.equal(controller.get().visibleError, null);
        assert.deepEqual(controller.errors.snapshot(), []);
    }
    assert.equal(controller.get().play.revision, 0);
    assert.equal(
        calls.filter((c) => c.op === "prepare" || c.op === "commit").length,
        0,
    );
    await controller.dispose();
}
console.log(
    "PASS: early cancel/context switch wait for admission; rejection and unknown acknowledgement keep truthful original-key recovery.",
);


for (const scenario of [
    "foreign-submit",
    "foreign-prepare",
    "coercible-recovery",
    "nonterminal-commit",
    "foreign-receipt-event",
    "ready-listener-cancel",
    "late-pending-status",
    "terminal-poll-only",
    "cancelled-lost-ack-committed",
]) {
    const session = {
        id: "binding",
        name: "Synthetic binding story",
        scope: { story: "binding-story", branch: "main" },
        revision: 0,
    };
    const turnCalls = [];
    let request;
    let saved = false;
    let receipt;
    let lookups = 0;
    let enterPrepare, releasePrepare, enterRefresh, releaseRefresh, releasePoll;
    const prepareEntered = new Promise((resolve) => (enterPrepare = resolve));
    const heldPrepare = new Promise((resolve) => (releasePrepare = resolve));
    const refreshEntered = new Promise((resolve) => (enterRefresh = resolve));
    const heldRefresh = new Promise((resolve) => (releaseRefresh = resolve));
    const heldPoll = new Promise((resolve) => (releasePoll = resolve));
    let enterCommit, releaseCommit;
    const commitEntered = new Promise((resolve) => (enterCommit = resolve));
    const heldCommit = new Promise((resolve) => (releaseCommit = resolve));
    const status = (phase, patch = {}) => ({
        scope: session.scope,
        turn: request.turn,
        expected_revision: request.expected_revision,
        phase,
        error: null,
        receipt: phase === "committed" ? receipt : null,
        ...patch,
    });
    const committed = () => {
        saved = true;
        return status("committed");
    };
    const wrongEvent = () =>
        status("committed", {
            receipt: {
                ...receipt,
                events: [{ ...receipt.events[0], turn: "foreign-event-turn" }],
            },
        });
    const gateway = {
        async call(command) {
            if (command.op === "open") {
                if (scenario === "late-pending-status" && saved) {
                    enterRefresh();
                    await heldRefresh;
                }
                return { revision: saved ? 1 : 0 };
            }
            if (command.op === "play_snapshot") {
                const revision = saved ? 1 : 0;
                return {
                    scope: session.scope,
                    revision,
                    inventory: {},
                    receipts: saved ? [receipt] : [],
                    player: {
                        scope: session.scope,
                        revision,
                        observer: "player",
                        self_state: { name: "Rowan", location: "quay" },
                        facts: {},
                        beliefs: [],
                        observations: [],
                    },
                };
            }
            if (command.op === "inspect" || command.op === "close") return {};
            turnCalls.push(command.op);
            if (command.op === "submit") {
                assert.equal(request, undefined, "recovery keeps the first key");
                request = command.request;
                receipt = {
                    request,
                    events: [
                        {
                            sequence: 1,
                            scope: session.scope,
                            turn: request.turn,
                            outcome: { kind: "synthetic" },
                        },
                    ],
                    narration: "Synthetic committed receipt.",
                };
                if (
                    scenario === "coercible-recovery" ||
                    scenario === "cancelled-lost-ack-committed"
                )
                    throw new Error("Transport");
                return scenario === "foreign-submit"
                    ? status("queued", {
                          scope: { ...session.scope, branch: "sibling" },
                      })
                    : status("queued");
            }
            assert.equal(command.session, session.id);
            assert.deepEqual(command.scope, session.scope);
            assert.equal(command.turn, request.turn);
            if (command.op === "prepare") {
                if (scenario === "late-pending-status") {
                    enterPrepare();
                    await heldPrepare;
                }
                return scenario === "foreign-prepare"
                    ? status("ready", { turn: "unrelated-turn" })
                    : status("ready");
            }
            if (command.op === "commit") {
                const accepted = committed();
                if (scenario === "terminal-poll-only") {
                    enterCommit();
                    await heldCommit;
                }
                if (scenario === "foreign-receipt-event") return wrongEvent();
                return scenario === "nonterminal-commit"
                    ? status("ready")
                    : accepted;
            }
            if (command.op === "cancel") return status("cancelled");
            assert.equal(command.op, "turn_status");
            lookups++;
            if (scenario === "late-pending-status") {
                await heldPoll;
                return status("running");
            }
            if (scenario === "foreign-receipt-event" && lookups === 1)
                return wrongEvent();
            if (
                scenario === "foreign-submit" ||
                scenario === "cancelled-lost-ack-committed" ||
                saved
            )
                return committed();
            if (scenario === "coercible-recovery" && lookups === 1)
                return status("ready", { expected_revision: "0" });
            return status("ready");
        },
    };
    const controller = new Controller(gateway);
    await controller.attach(session);
    controller.setAction("wait");
    let cancellation;
    let requested = false;
    const unsubscribe = controller.subscribe(() => {
        const state = controller.get();
        const cancelReady =
            scenario === "ready-listener-cancel" &&
            state.turnStatus?.phase === "ready";
        const cancelSubmit =
            scenario === "cancelled-lost-ack-committed" &&
            state.pending?.stage === "submitting";
        if (!requested && (cancelReady || cancelSubmit)) {
            requested = true;
            cancellation = controller.cancel();
        }
    });
    const sending = controller.send();
    if (scenario === "late-pending-status") {
        await prepareEntered;
        const oldPoll = controller.pendingStatus();
        releasePrepare();
        await refreshEntered;
        assert.equal(controller.get().turnStatus.phase, "committed");
        releasePoll();
        assert.equal(await oldPoll, null);
        assert.equal(controller.get().turnStatus.phase, "committed");
        releaseRefresh();
    } else if (scenario === "terminal-poll-only") {
        await commitEntered;
        assert.equal((await controller.pendingStatus()).phase, "committed");
        assert.equal(controller.get().turnStatus.phase, "ready");
        assert.equal(controller.get().play.revision, 0);
        releaseCommit();
    }
    await sending;
    if (scenario === "foreign-submit" || scenario === "cancelled-lost-ack-committed") {
        assert.deepEqual(turnCalls, ["submit"]);
        assert.equal(controller.get().visibleError, "TransportUnknown");
        await controller.retry();
        assert.deepEqual(turnCalls, ["submit", "turn_status"]);
    } else if (scenario === "foreign-prepare") {
        assert.deepEqual(turnCalls, ["submit", "prepare"]);
        assert.equal(controller.get().visibleError, "TransportUnknown");
        await controller.retry();
        assert.deepEqual(turnCalls, [
            "submit",
            "prepare",
            "turn_status",
            "commit",
        ]);
    } else if (scenario === "coercible-recovery") {
        await controller.retry();
        assert.deepEqual(turnCalls, ["submit", "turn_status"]);
        assert.equal(controller.get().visibleError, "TransportUnknown");
        await controller.retry();
        assert.deepEqual(turnCalls, [
            "submit",
            "turn_status",
            "turn_status",
            "commit",
        ]);
    } else if (
        scenario === "nonterminal-commit" ||
        scenario === "terminal-poll-only"
    ) {
        assert.deepEqual(turnCalls, [
            "submit",
            "prepare",
            "commit",
            "turn_status",
        ]);
    } else if (scenario === "foreign-receipt-event") {
        assert.equal(controller.get().visibleError, "TransportUnknown");
        assert.equal(controller.get().play.revision, 0);
        await controller.retry();
        assert.deepEqual(turnCalls, [
            "submit",
            "prepare",
            "commit",
            "turn_status",
            "turn_status",
        ]);
    } else if (scenario === "late-pending-status") {
        assert.deepEqual(turnCalls, [
            "submit",
            "prepare",
            "turn_status",
            "commit",
        ]);
    } else {
        assert(cancellation, "subscriber cancels before a commit offer");
        await cancellation;
        assert.deepEqual(turnCalls, ["submit", "prepare", "cancel"]);
        assert.equal(controller.get().turnStatus.phase, "cancelled");
        assert.equal(controller.get().play.revision, 0);
    }
    if (scenario !== "ready-listener-cancel") {
        assert.equal(controller.get().turnStatus.phase, "committed");
        assert.equal(controller.get().visibleError, null);
        assert.equal(controller.get().play.revision, 1);
        assert.deepEqual(controller.receipt(), receipt);
    }
    unsubscribe();
    await controller.dispose();
}
console.log(
    "PASS: mismatched turn replies cannot advance a turn; recovery uses the original key and checks terminal acknowledgements.",
);
