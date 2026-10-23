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
for (const schedule of ["admitted", "rejected", "lost-ack", "switch"]) {
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
                        if (schedule === "lost-ack")
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
    else await controller.cancel();
    assert.equal(
        calls.filter((c) => c.op === "cancel").length,
        0,
        "no speculative control before submit reply",
    );
    assert.notEqual(controller.get().visibleError, "TransportUnknown");
    release();
    await work;
    if (schedule === "lost-ack") {
        assert.equal(
            controller.get().visibleError,
            "TransportUnknown",
            "lost acknowledgement remains honestly uncertain",
        );
        await controller.retry();
        assert.equal(controller.get().turnStatus.phase, "cancelled");
        assert.equal(controller.get().visibleError, null);
        assert.equal(calls.filter((c) => c.op === "turn_status").length, 1);
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
