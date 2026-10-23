// Actual frontend controller with MOCK IPC and synthetic synchronous persistence.
import { ForkController } from "./fork-controller";
import type { TimelineContext } from "./timeline-model";

const original: TimelineContext = {
    session: "session-original", scope: { story: "synthetic", branch: "main" },
    revision: 4, view: "play", observer: "player", persistent: true,
};
const replacement: TimelineContext = {
    ...original, session: "session-replacement", scope: { story: "replacement", branch: "main" },
};
function require(value: boolean, label: string): void {
    if (!value) throw Error(label);
}
export async function runForkCallbackReview() {
    const results: { name: string; passed: boolean; error: string | null }[] = [];
    const run = async (name: string, body: () => Promise<void>) => {
        try { await body(); results.push({ name, passed: true, error: null }); }
        catch (error) { results.push({ name, passed: false, error: error instanceof Error ? error.message : "ReviewFailure" }); }
    };
    await run("saved identity after selection switch is lookup-only", async () => {
        const calls: string[] = [];
        const controller = new ForkController(async (name) => { calls.push(name); throw Error("UnexpectedIPC"); },
            async () => {}, () => controller.contextChanged(replacement));
        controller.contextChanged(original);
        controller.prepare(2, "original-child");
        require(controller.get().request?.parent.story === original.scope.story, "exact saved identity retained");
        require(controller.get().lookupOnly, "replacement selection cannot execute old identity");
        require(controller.get().status !== "prepared", "old request cannot appear newly prepared in replacement");
        await controller.confirm(true);
        require(calls.length === 0, "selection switch dispatches no old native work");
        controller.dispose();
    });
    await run("selection switch plus save error cannot label replacement", async () => {
        const calls: string[] = [];
        const controller = new ForkController(async (name) => { calls.push(name); throw Error("UnexpectedIPC"); },
            async () => {}, () => { controller.contextChanged(replacement); throw Error("SyntheticSaveFailure"); });
        controller.contextChanged(original);
        controller.prepare(2, "original-child");
        require(controller.get().request === null && controller.get().status === "idle", "replacement presentation remains clear");
        require(controller.get().error === null, "old save error does not label replacement");
        await controller.confirm(true);
        require(calls.length === 0, "save failure dispatches nothing");
        controller.dispose();
    });
    await run("dispose during save cannot resurrect prepared request", async () => {
        const calls: string[] = [];
        const controller = new ForkController(async (name) => { calls.push(name); throw Error("UnexpectedIPC"); },
            async () => {}, () => controller.dispose());
        controller.contextChanged(original);
        controller.prepare(2, "original-child");
        require(controller.get().request === null && controller.get().status === "idle", "disposed presentation stays clear");
        await controller.confirm(true);
        require(calls.length === 0, "disposed owner cannot dispatch");
    });
    await run("nested prepare cannot replace durable recovery identity", async () => {
        const saved: string[] = [];
        const controller = new ForkController(async () => { throw Error("UnexpectedIPC"); }, async () => {}, (request) => {
            saved.push(request.child_branch);
            if (saved.length === 1) controller.prepare(1, "nested-child");
        });
        controller.contextChanged(original);
        controller.prepare(2, "original-child");
        require(saved.length === 1 && saved[0] === "original-child", "one exact synchronous save admission");
        require(controller.get().request?.child_branch === saved[0], "displayed identity equals saved identity");
        controller.dispose();
    });
    await run("pending presentation selection switch prevents registration", async () => {
        const calls: string[] = [];
        const controller = new ForkController(async (name) => { calls.push(name); throw Error("UnexpectedIPC"); }, async () => {}, () => {});
        controller.contextChanged(original);
        controller.prepare(2, "original-child");
        const release = controller.subscribe(() => {
            if (controller.get().busy) controller.contextChanged(replacement);
        });
        await controller.confirm(true);
        require(calls.length === 0, "stale pending presentation cannot register native work");
        require(controller.get().lookupOnly && !controller.get().busy, "replacement retains only recovery identity");
        release(); controller.dispose();
    });
    await run("lookup presentation selection switch prevents stale read", async () => {
        const calls: string[] = [];
        const controller = new ForkController(async (name) => { calls.push(name); throw Error("UnexpectedIPC"); }, async () => {}, () => {});
        controller.contextChanged(original);
        controller.restore({ parent: original.scope, child_branch: "original-child", expected_parent_revision: 4, at_revision: 2 });
        const release = controller.subscribe(() => {
            if (controller.get().busy) controller.contextChanged(replacement);
        });
        await controller.lookup();
        require(calls.length === 0, "stale pending lookup cannot read old selection");
        require(controller.get().lookupOnly && !controller.get().busy, "new selection stays lookup-only");
        release(); controller.dispose();
    });
    return { kind: "actual-controller-mock-ipc", results };
}
