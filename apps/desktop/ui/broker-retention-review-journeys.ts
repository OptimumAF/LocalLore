// Actual gate/controller, mocked IPC. Frozen before coordinator repair.
import { BrokerRetention } from "./broker-retention";
import { MemoryMaintenanceController, type MemoryContext } from "./memory-maintenance-controller";

export async function brokerRetentionReviewJourneys() {
    const results: { name: string; passed: boolean; error: string | null }[] = [];
    async function test(name: string, work: () => Promise<void>) {
        try { await work(); results.push({ name, passed: true, error: null }); }
        catch (error) { results.push({ name, passed: false, error: String(error) }); }
    }
    function check(value: unknown, label: string): asserts value {
        if (!value) throw Error(label);
    }
    const context: MemoryContext = { session: "session-1", scope: { story: "memory-review", branch: "main" }, expected_head: 1, player: "player", observer: "player", view: "play", epoch: 1, persistent: true };
    const identity = { surface: "memory" as const, session: context.session, story: context.scope.story, branch: context.scope.branch, head: 1, action: "status" };
    const valid = () => ({ version: 1, kind: "memory_maintenance", session: context.session, scope: context.scope, expected_head: 1, action: "status", maintenance: { version: 1, scope: context.scope, head: 1, action: "status", job: null } });
    for (const [name, payload] of [
        ["missing-memory-result-fields", {}],
        ["foreign-memory-result-scope", { ...valid(), scope: { story: "foreign", branch: "main" } }],
        ["wrong-memory-result-action", { ...valid(), action: "step" }],
        ["malformed-memory-job", { ...valid(), maintenance: { ...valid().maintenance, job: { status: "ready" } } }],
    ] as const) await test(name, async () => {
        const gate = new BrokerRetention(() => controller.get().busy || controller.get().uncertain);
        const controller = new MemoryMaintenanceController(() => gate.start(identity, async () => ({ version: 1, operation_id: 1, running: false, phase: "completed", error: null, result: payload })));
        controller.contextChanged(context);
        await controller.act("status");
        check(controller.get().error === "Wire" && controller.get().uncertain, "actual decoder rejects malformed acknowledgement");
        controller.contextChanged({ ...context, session: "session-2", epoch: 2 });
        check(!controller.get().uncertain, "old presentation cleared by selection change");
        check(gate.get()?.unknown, "malformed acknowledgement remains unresolved across selection change");
        let dispatched = false;
        try { await gate.start({ surface: "fork", action: "fork" }, async () => { dispatched = true; throw Error("unexpected dispatch"); }); }
        catch (error) { check(error instanceof Error && error.message === "ArchiveBusy", "retained barrier rejects next start"); }
        check(!dispatched, "different surface never dispatched");
    });
    for (const phase of ["choosing_input", "choosing_destination"]) await test(`archive-${phase}-is-known-pending`, async () => {
        const gate = new BrokerRetention(() => false);
        await gate.start({ surface: "archive", action: "archive_import_preview" }, async () => ({ version: 1, operation_id: 7, running: true, phase, error: null, result: null }));
        check(gate.get()?.operation === 7 && !gate.get()?.unknown && !gate.get()?.terminal, "valid native picker phase retains exact known operation");
    });
    return results;
}
