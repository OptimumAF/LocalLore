// Frozen independent coordinator-diff review. Actual gate/controller, mocked IPC.
// No native, WebView, SQLite, model, browser or desktop execution.
import { BrokerRetention } from "./broker-retention";
import {
    MemoryMaintenanceController,
    type MemoryContext,
} from "./memory-maintenance-controller";

export async function brokerRetentionIncarnationReviewJourneys() {
    const results: { name: string; passed: boolean; error: string | null }[] =
        [];
    const check = (value: unknown, label: string) => {
        if (!value) throw Error(label);
    };
    async function test(name: string, work: () => Promise<void>) {
        try {
            await work();
            results.push({ name, passed: true, error: null });
        } catch (error) {
            results.push({ name, passed: false, error: String(error) });
        }
    }
    const context: MemoryContext = {
        session: "session-1",
        scope: { story: "memory-gate-incarnation", branch: "main" },
        expected_head: 1,
        player: "player",
        observer: "player",
        view: "play",
        epoch: 1,
        persistent: true,
    };
    const identity = {
        surface: "memory" as const,
        session: context.session,
        story: context.scope.story,
        branch: context.scope.branch,
        head: context.expected_head,
        action: "status",
    };
    const memoryStatus = (operation: number) => ({
        version: 1,
        operation_id: operation,
        running: false,
        phase: "completed",
        error: null,
        result: {
            version: 1,
            kind: "memory_maintenance",
            session: context.session,
            scope: { ...context.scope },
            expected_head: context.expected_head,
            action: "status",
            maintenance: {
                version: 1,
                scope: { ...context.scope },
                head: context.expected_head,
                action: "status",
                job: null,
            },
        },
    });
    // Only gate admission is under test for the second surface. Native fork
    // result validation remains in its existing controller's untouched tests.
    const forkStatus = (operation: number) => ({
        version: 1,
        operation_id: operation,
        running: false,
        phase: "completed",
        error: null,
        result: { kind: "synthetic-gate-only-fork-result" },
    });

    await test("late-known-old-id-cannot-poison-current-consumed-memory-outcome", async () => {
        const gate = new BrokerRetention(() => false);
        await gate.start(identity, async () => memoryStatus(1));
        check(gate.get()?.consumed, "first complete native status consumed");
        await gate.start(identity, async () => memoryStatus(2));
        check(
            gate.get()?.operation === 2 &&
                gate.get()?.consumed &&
                !gate.get()?.unknown,
            "new operation has a known consumed outcome",
        );
        const before = JSON.stringify(gate.get());
        // A real archive_cancel/status request for retired op1 can arrive after
        // op2. Its valid old ID identifies it before current result decoding.
        gate.observe(memoryStatus(1));
        check(
            JSON.stringify(gate.get()) === before,
            "foreign known old operation leaves current identity, certainty and consumption untouched",
        );
        let dispatched = false;
        await gate.start({ surface: "fork", action: "fork" }, async () => {
            dispatched = true;
            return forkStatus(3);
        });
        check(
            dispatched,
            "old late status cannot block a subsequent explicit fork",
        );
    });

    await test("new-passive-recovery-must-consume-its-own-outcome-before-crosssurface-start", async () => {
        let calls = 0;
        let armRecovery = false;
        let sawPendingRecovery = false;
        let inheritedConsumption = false;
        let attemptedDuringDelivery = false;
        let dispatchedDuringDelivery = false;
        let blockedDuringDelivery = false;
        let attempted: Promise<void> | null = null;
        const gate: BrokerRetention = new BrokerRetention(
            (surface) =>
                surface === "memory" &&
                (controller.get().busy || controller.get().uncertain),
        );
        const controller: MemoryMaintenanceController =
            new MemoryMaintenanceController((_command, args) => {
                const action = (args!.request as { action: string }).action;
                if (action === "admit") {
                    // Same existing main-wrapper pre-admission pending-turn
                    // refusal: no new broker operation was registered.
                    throw Error("Busy");
                }
                calls++;
                return calls === 1
                    ? gate.start(identity, async () => memoryStatus(1))
                    : gate.recoverMemory(identity, async () => memoryStatus(2));
            });
        controller.subscribe(gate.refreshConsumption);
        gate.subscribe(() => {
            const retained = gate.get();
            if (!armRecovery || !retained?.recoveringMemory) return;
            if (retained.inFlight) {
                sawPendingRecovery = true;
                inheritedConsumption ||= retained.consumed;
            }
            if (
                !attemptedDuringDelivery &&
                !retained.inFlight &&
                retained.operation === 2 &&
                retained.terminal &&
                controller.get().busy
            ) {
                attemptedDuringDelivery = true;
                attempted = gate
                    .start({ surface: "fork", action: "fork" }, async () => {
                        dispatchedDuringDelivery = true;
                        return forkStatus(3);
                    })
                    .then(
                        () => {},
                        (error) => {
                            blockedDuringDelivery =
                                error instanceof Error &&
                                error.message === "ArchiveBusy";
                        },
                    );
            }
        });
        controller.contextChanged(context);
        await controller.act("status");
        check(
            gate.get()?.consumed,
            "first status latched consumed before new action",
        );
        controller.consent(true);
        await controller.act("admit");
        check(
            controller.get().error === "Busy" &&
                controller.get().uncertain &&
                gate.get()?.operation === 1 &&
                gate.get()?.consumed,
            "actual controller records pending-turn refusal without replacing previous broker status",
        );
        armRecovery = true;
        await controller.act("status");
        if (attempted) await attempted;
        check(
            sawPendingRecovery,
            "new passive status announced as a distinct operation",
        );
        check(
            !inheritedConsumption,
            "new passive status never inherits old operation consumption at pending notification",
        );
        check(
            attemptedDuringDelivery &&
                blockedDuringDelivery &&
                !dispatchedDuringDelivery,
            "crosssurface fork blocked until actual memory controller decodes and accepts its own new status",
        );
        check(
            calls === 2 &&
                controller.get().reply?.action === "status" &&
                controller.get().error === null &&
                !controller.get().uncertain &&
                gate.get()?.operation === 2 &&
                gate.get()?.consumed,
            "new passive result is independently consumed after actual controller acceptance",
        );
        let explicitDispatch = false;
        await gate.start({ surface: "fork", action: "fork" }, async () => {
            explicitDispatch = true;
            return forkStatus(4);
        });
        check(
            explicitDispatch,
            "subsequent explicit fork allowed after new status consumption",
        );
    });
    await test("late-old-status-cannot-adopt-new-unacknowledged-start-operation", async () => {
        let starts = 0;
        let releaseAdmission!: (value: unknown) => void;
        const heldAdmission = new Promise<unknown>(resolve => {
            releaseAdmission = resolve;
        });
        const running2 = {
            version: 1,
            operation_id: 2,
            running: true,
            phase: "memory_maintenance",
            error: null,
            result: null,
        };
        const gate: BrokerRetention = new BrokerRetention(surface =>
            surface === "memory" && (controller.get().busy || controller.get().uncertain),
        );
        const controller: MemoryMaintenanceController = new MemoryMaintenanceController(
            (command) => {
                if (command === "archive_status") {
                    const result = memoryStatus(2);
                    gate.observe(result);
                    return Promise.resolve(result);
                }
                starts++;
                return gate.start(identity, () => starts === 1
                    ? Promise.resolve(memoryStatus(1))
                    : heldAdmission,
                );
            },
        );
        controller.subscribe(gate.refreshConsumption);
        controller.contextChanged(context);
        await controller.act("status");
        check(
            controller.get().reply?.action === "status" && gate.get()?.consumed,
            "first actual controller/native-mock status consumed before new start",
        );
        const pending = controller.act("status");
        const unidentified = gate.get();
        const wasPendingUnidentified = unidentified?.inFlight && unidentified.operation === null && !unidentified.terminal;
        // This is an external status/cancel response from the previous call,
        // not the reply to the currently awaited second start admission.
        gate.observe(memoryStatus(1));
        const afterLate = gate.get();
        const oldReplyWasIgnored = afterLate?.inFlight && afterLate.operation === null && !afterLate.terminal && !afterLate.consumed && !afterLate.unknown;
        // Always release the held mock request before any behavioral assertion,
        // including on the broken source, so no fixture promise is left pending.
        releaseAdmission(running2);
        await pending;
        check(wasPendingUnidentified, "new actual start awaits its own unidentified native acknowledgement");
        check(oldReplyWasIgnored, "late external old status cannot establish identity or terminal state for new unidentified reservation");
        check(
            controller.get().operation?.operation_id === 2 && controller.get().operation?.running &&
            gate.get()?.operation === 2 && !gate.get()?.terminal && !gate.get()?.consumed && !gate.get()?.unknown,
            "own new admission establishes exact running operation2 in both controller and gate",
        );
        let prematureDispatch = false;
        let blocked = false;
        try {
            await gate.start({ surface: "fork", action: "fork" }, async () => {
                prematureDispatch = true;
                return forkStatus(3);
            });
        } catch (error) {
            blocked = error instanceof Error && error.message === "ArchiveBusy";
        }
        check(blocked && !prematureDispatch, "new running operation2 retains unconsumed result against crosssurface start");
        await controller.act("status");
        check(
            starts === 2 && controller.get().reply?.action === "status" &&
            controller.get().operation?.operation_id === 2 && !controller.get().operation?.running &&
            controller.get().error === null && !controller.get().uncertain &&
            gate.get()?.operation === 2 && gate.get()?.terminal && gate.get()?.consumed,
            "own exact terminal operation2 is observed and consumed without restarting it",
        );
        let explicitDispatch = false;
        await gate.start({ surface: "fork", action: "fork" }, async () => {
            explicitDispatch = true;
            return forkStatus(4);
        });
        check(explicitDispatch, "explicit crosssurface start allowed only after new operation2 consumption");
    });
    return results;
}
