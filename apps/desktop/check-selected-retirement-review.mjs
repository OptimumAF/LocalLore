// Frozen SOURCE ONLY / UNRUN. Actual controller through Root's existing mock
// transport helpers; no native IPC, worker, cleanup proof, renderer or model.
import assert from "node:assert/strict";

export async function selectedRetirementReview({ test, fixture, status, deferred, tick, source, row }) {
    await test("retired initial admission requires a stable exact postreply close acknowledgement", async () => {
        const f = fixture(), entered = deferred(), admission = deferred();
        const firstEntered = deferred(), firstClose = deferred();
        const secondEntered = deferred(), secondClose = deferred();
        let old, closes = 0;
        f.hooks.set("prepare", (body) => {
            old = body.clientId; entered.resolve(); return admission.promise;
        });
        f.hooks.set("close", (body) => {
            assert.equal(body.clientId, old);
            if (++closes === 1) { firstEntered.resolve(); return firstClose.promise; }
            if (closes === 2) { secondEntered.resolve(); return secondClose.promise; }
            return status(old, "closed");
        });
        const work = f.c.prepare(source, row, "scripted_baseline");
        await entered.promise;
        f.c.setContext("retired-initial-admission-context", true);
        await firstEntered.promise;
        // The first close was sent while the original admission was in flight.
        // Its closed reply must not certify the later original reply generation.
        admission.resolve(status(old, "prepared"));
        await tick();
        firstClose.resolve(status(old, "closed"));
        await secondEntered.promise;
        const beforeStableAck = f.c.get();
        secondClose.resolve(status(old, "closed"));
        await work; await tick();
        assert.equal(beforeStableAck.uncertain, true);
        assert.equal(beforeStableAck.clientId, null);
        assert.equal(beforeStableAck.status, null);
        assert.equal(f.c.get().uncertain, false);
        assert.equal(f.c.get().status, null);
        assert.equal(f.c.get().summary, null);
        assert.equal(f.c.get().evidence, null);
        assert.equal(f.calls.filter((v) => v.action === "prepare").length, 1);
        assert.ok(closes >= 2);
        f.hooks.delete("prepare");
        await f.c.prepare(source, row, "scripted_baseline");
        assert.notEqual(f.c.get().clientId, old);
        assert.equal(f.calls.filter((v) => v.action === "prepare").length, 2);
        f.c.dispose();
    });

    await test("retired close polls running truth but never clears it as an actual worker acknowledgement", async () => {
        const f = fixture(); await f.c.prepare(source, row, "scripted_baseline");
        const old = f.c.get().clientId, first = deferred(), second = deferred(), terminal = deferred();
        let calls = 0;
        f.hooks.set("close", (body) => {
            assert.equal(body.clientId, old);
            if (++calls === 1) { first.resolve(); return status(old, "closed", { running: true }); }
            second.resolve(); return terminal.promise;
        });
        f.c.setContext("retired-running-native-owner", true);
        await first.promise; await second.promise;
        const waiting = f.c.get();
        const cleared = deferred();
        const stop = f.c.subscribe(() => { if (!f.c.get().uncertain) cleared.resolve(); });
        terminal.resolve(status(old, "closed"));
        // Existing controller notifications provide the exact terminal handshake.
        // Root's existing test wrapper bounds this mock case if none arrives.
        await cleared.promise; stop();
        assert.equal(waiting.uncertain, true);
        assert.equal(waiting.status, null);
        assert.equal(f.c.get().uncertain, false);
        assert.equal(f.calls.filter((v) => v.action === "prepare").length, 1);
        assert.ok(calls >= 2);
        f.c.dispose();
    });

    for (const fault of ["transport", "cleanup_required", "wrong_client"]) {
        await test(`retired ${fault} close remains a barrier without replacing its private client`, async () => {
            const f = fixture(); await f.c.prepare(source, row, "scripted_baseline");
            const old = f.c.get().clientId;
            f.hooks.set("close", (body) => {
                assert.equal(body.clientId, old);
                if (fault === "transport") throw Error("EvaluationIo");
                return status(fault === "wrong_client" ? crypto.randomUUID() : old, "closed",
                    fault === "cleanup_required" ? { cleanup_required: true, error: "Cleanup" } : {});
            });
            f.c.setContext(`retired-${fault}`, true); await tick();
            assert.equal(f.c.get().uncertain, true);
            assert.equal(f.c.get().clientId, null);
            assert.equal(f.c.get().status, null);
            await f.c.prepare(source, row, "scripted_baseline");
            assert.equal(f.calls.filter((v) => v.action === "prepare").length, 1);
            assert.equal(f.calls.filter((v) => v.action === "retry_cleanup").length, 0);
            assert.equal(f.c.get().uncertain, true);
            // Only a later exact native no-owner/terminal reply can release it.
            f.hooks.set("close", (body) => {
                assert.equal(body.clientId, old); return status(old, "closed");
            });
            await f.c.prepare(source, row, "scripted_baseline");
            const replacement = f.c.get().clientId;
            assert.notEqual(replacement, old); assert.ok(replacement);
            assert.equal(f.calls.filter((v) => v.action === "prepare").length, 2);
            assert.ok(f.calls.filter((v) => v.action === "close").every((v) => v.body.clientId === old));
            f.c.dispose();
        });
    }

    await test("same-client cancel during status sleep never becomes retired-client close", async () => {
        const f = fixture(); await f.c.prepare(source, row, "scripted_baseline");
        const client = f.c.get().clientId, startEntered = deferred();
        f.hooks.set("start", () => { startEntered.resolve(); return status(client, "running"); });
        const work = f.c.start(); await startEntered.promise; await tick();
        // Initial running reply is owned, and the operation is sleeping before
        // its next poll. Cancel changes lifecycle serial, not client/context.
        await f.c.cancel(); await work;
        assert.equal(f.c.get().clientId, client);
        assert.equal(f.c.get().status.phase, "completed");
        assert.equal(f.c.get().uncertain, false);
        assert.equal(f.calls.filter((v) => v.action === "close").length, 0);
        assert.equal(f.calls.filter((v) => v.action === "cancel").length, 1);
        f.c.dispose();
    });
}

export default selectedRetirementReview;
