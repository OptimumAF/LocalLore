// Frozen model-free controller regressions. Transport is mocked, never native evidence.
import {
    MemoryMaintenanceController,
    type MemoryContext,
    type MemoryAction,
} from "./memory-maintenance-controller";

export async function memoryCallbackReviewJourneys() {
    const checks: string[] = [];
    const context: MemoryContext = {
        session: "session-1",
        scope: { story: "memory-controls-synthetic", branch: "main" },
        expected_head: 1,
        player: "rowan",
        observer: "rowan",
        view: "play",
        epoch: 1,
        persistent: true,
    };
    const check = (value: unknown, label: string) => {
        if (!value) throw Error(label);
        checks.push(label);
    };
    for (const action of [
        "status",
        "admit",
        "step",
        "cancel",
        "prune",
    ] as MemoryAction[]) {
        for (const retire of ["context", "dispose"]) {
            let calls = 0,
                next = 0;
            const c = new MemoryMaintenanceController(async (_name, args) => {
                calls++;
                const request = args!.request as { action: MemoryAction };
                const a = request.action;
                const job =
                    a === "admit"
                        ? {
                              status: "ready",
                              basis_revision: 1,
                              next_from: 0,
                              generation: 1,
                              last_error: null,
                          }
                        : a === "cancel"
                          ? {
                                status: "cancelled",
                                basis_revision: 1,
                                next_from: 0,
                                generation: 2,
                                last_error: null,
                            }
                          : null;
                return {
                    version: 1,
                    operation_id: ++next,
                    running: false,
                    phase: "completed",
                    error: null,
                    result: {
                        version: 1,
                        kind: "memory_maintenance",
                        session: context.session,
                        scope: context.scope,
                        expected_head: 1,
                        action: a,
                        maintenance: {
                            version: 1,
                            scope: context.scope,
                            head: 1,
                            action: a,
                            job,
                        },
                    },
                };
            });
            c.contextChanged(context);
            if (action !== "status") await c.act("status");
            if (["step", "cancel", "prune"].includes(action)) {
                c.consent(true);
                await c.act("admit");
            }
            if (action === "prune") await c.act("cancel");
            if (["admit", "prune"].includes(action)) c.consent(true);
            check(c.can(action), `${action}-${retire}-fixture-eligible`);
            const before = calls;
            let armed = true;
            c.subscribe(() => {
                if (armed && c.get().busy) {
                    armed = false;
                    if (retire === "dispose") c.dispose();
                    else
                        c.contextChanged({
                            ...context,
                            session: "session-2",
                            scope: { story: "other-story", branch: "main" },
                            epoch: 2,
                        });
                }
            });
            await c.act(action);
            check(
                calls === before,
                `${action}-${retire}-notification-retires-before-native-dispatch`,
            );
            check(
                c.get().reply === null &&
                    !c.get().busy &&
                    c.get().error === null,
                `${action}-${retire}-no-old-result-or-error`,
            );
        }
    }
    for (const retire of ["context", "dispose"]) {
        let next = 0;
        const c = new MemoryMaintenanceController(async (name, args) => {
            if (name === "archive_cancel")
                return {
                    version: 1,
                    operation_id: 3,
                    running: true,
                    phase: "memory_maintenance",
                    error: null,
                    result: null,
                };
            const action = (args!.request as { action: MemoryAction }).action;
            if (action === "step")
                return {
                    version: 1,
                    operation_id: 3,
                    running: true,
                    phase: "memory_maintenance",
                    error: null,
                    result: null,
                };
            return {
                version: 1,
                operation_id: ++next,
                running: false,
                phase: "completed",
                error: null,
                result: {
                    version: 1,
                    kind: "memory_maintenance",
                    session: context.session,
                    scope: context.scope,
                    expected_head: 1,
                    action,
                    maintenance: {
                        version: 1,
                        scope: context.scope,
                        head: 1,
                        action,
                        job:
                            action === "admit"
                                ? {
                                      status: "ready",
                                      basis_revision: 1,
                                      next_from: 0,
                                      generation: 1,
                                      last_error: null,
                                  }
                                : null,
                    },
                },
            };
        });
        c.contextChanged(context);
        await c.act("status");
        c.consent(true);
        await c.act("admit");
        await c.act("step");
        let armed = true;
        c.subscribe(() => {
            if (armed && !c.get().busy && c.get().operation?.running) {
                armed = false;
                if (retire === "dispose") c.dispose();
                else
                    c.contextChanged({
                        ...context,
                        session: "session-2",
                        epoch: 2,
                    });
            }
        });
        await c.stop();
        check(
            c.get().notice === "" &&
                c.get().reply === null &&
                c.get().error === null,
            `stop-${retire}-terminal-notification-cannot-install-old-followup-notice`,
        );
    }
    return checks;
}
