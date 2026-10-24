// Actual frontend controller; MOCK IPC only. No native/browser/model execution.
import { ForkController } from "./fork-controller";
import type { ForkRequest } from "./fork-controller";
import type { TimelineContext } from "./timeline-model";

const original: TimelineContext = {
    session: "review-original",
    scope: { story: "review-story", branch: "main" },
    revision: 4,
    view: "play",
    observer: "player",
    persistent: true,
};
const replacement: TimelineContext = {
    ...original,
    session: "review-replacement",
    scope: { story: "other-review-story", branch: "main" },
};
function require(value: boolean, label: string): void {
    if (!value) throw Error(label);
}
function completed(request: ForkRequest) {
    return {
        version: 1,
        operation_id: 17,
        running: false,
        phase: "completed",
        error: null,
        result: {
            kind: "fork",
            outcome: {
                version: 1,
                scope: {
                    story: request.parent.story,
                    branch: request.child_branch,
                },
                parent: request.parent,
                fork_revision: request.at_revision,
                head_revision: request.at_revision,
                created: true,
            },
        },
    };
}

export async function runForkIndependentReview() {
    const results: {
        name: string;
        passed: boolean;
        error: string | null;
    }[] = [];
    const run = async (name: string, body: () => Promise<void>) => {
        try {
            await body();
            results.push({ name, passed: true, error: null });
        } catch (error) {
            results.push({
                name,
                passed: false,
                error: error instanceof Error ? error.message : "ReviewFailure",
            });
        }
    };

    for (const action of ["switch", "dispose"] as const) {
        await run(
            `terminal operation notification ${action} cannot install stale result`,
            async () => {
                const calls: string[] = [];
                let refreshes = 0;
                let starts = 0;
                const controller = new ForkController(
                    async (name, args) => {
                        calls.push(name);
                        if (name === "archive_cancel") return {};
                        require(name ===
                            "fork_start", "only explicit fork start");
                        starts++;
                        return completed(args!.input as ForkRequest);
                    },
                    async () => {
                        refreshes++;
                    },
                    () => {},
                );
                controller.contextChanged(original);
                controller.prepare(2, "review-child");
                let notified = false;
                const release = controller.subscribe(() => {
                    // The initial pending notification has no operation. Trigger
                    // only when poll presents this actual terminal reply's ID.
                    if (
                        !notified &&
                        controller.get().busy &&
                        controller.get().operation === 17
                    ) {
                        notified = true;
                        if (action === "switch")
                            controller.contextChanged(replacement);
                        else controller.dispose();
                    }
                });
                await controller.confirm(true);
                require(starts === 1, "one originally authorized start");
                require(notified, "terminal operation notification exercised");
                require(controller.get().result ===
                    null, "old terminal result cannot repopulate replacement/disposed owner");
                require(controller.get().status !==
                    "complete", "old completion cannot label replacement/disposed owner");
                require(!controller.get()
                    .consent, "old consent remains cleared");
                require(!controller.get().busy, "no replacement busy state");
                require(refreshes === 0, "no stale post-notification refresh");
                require(calls.filter((name) => name === "fork_start").length ===
                    1, "no replacement or automatic fork start");
                if (action === "switch")
                    require(controller.get()
                        .lookupOnly, "saved identity remains lookup-only for replacement");
                release();
                controller.dispose();
            },
        );
    }
    for (const action of ["confirm", "lookup", "restore"] as const) {
        await run(
            `second recovery save blocks nested ${action} admission`,
            async () => {
                const calls: string[] = [];
                const saved: string[] = [];
                const nested: Promise<void>[] = [];
                let unchangedDuringSave = false;
                const controller = new ForkController(
                    async (name) => {
                        calls.push(name);
                        throw Error("UnexpectedIPC");
                    },
                    async () => {},
                    (request) => {
                        saved.push(request.child_branch);
                        if (saved.length !== 2) return;
                        const before = controller.get();
                        if (action === "confirm")
                            nested.push(controller.confirm(true));
                        else if (action === "lookup")
                            nested.push(controller.lookup());
                        else
                            controller.restore({
                                parent: original.scope,
                                child_branch: "nested-restored-child",
                                expected_parent_revision: 4,
                                at_revision: 1,
                            });
                        unchangedDuringSave = controller.get() === before;
                    },
                );
                controller.contextChanged(original);
                controller.prepare(2, "first-review-child");
                controller.prepare(1, "second-review-child");
                await Promise.all(nested);
                require(saved.length === 2, "both explicit saves exercised");
                require(saved[0] === "first-review-child" &&
                    saved[1] ===
                        "second-review-child", "no nested recovery identity save");
                require(unchangedDuringSave, "nested control cannot publish during synchronous save");
                require(calls.length === 0, "no nested start or lookup IPC");
                require(controller.get().request?.child_branch ===
                    saved[1], "final presentation matches the durably saved identity");
                require(controller.get().status === "prepared" &&
                    !controller.get().busy &&
                    !controller.get().lookupOnly &&
                    !controller.get().consent &&
                    controller.get().result ===
                        null, "new request needs its own explicit consent");
                controller.dispose();
            },
        );
    }

    for (const path of ["confirm", "lookup"] as const) {
        for (const action of ["switch", "dispose"] as const) {
            await run(
                `${path} result notification ${action} prevents stale refresh`,
                async () => {
                    const calls: string[] = [];
                    let refreshes = 0;
                    const controller = new ForkController(
                        async (name, args) => {
                            calls.push(name);
                            if (name === "archive_cancel") return {};
                            const reply = completed(args!.input as ForkRequest);
                            if (name === "fork_start") return reply;
                            require(name ===
                                "fork_lookup", "closed lookup path");
                            return {
                                version: 1,
                                kind: "fork_lookup",
                                found: true,
                                outcome: {
                                    ...reply.result.outcome,
                                    created: false,
                                },
                            };
                        },
                        async () => {
                            refreshes++;
                        },
                        () => {},
                    );
                    controller.contextChanged(original);
                    controller.prepare(2, "review-child");
                    let notified = false;
                    const release = controller.subscribe(() => {
                        if (!notified && controller.get().result !== null) {
                            notified = true;
                            if (action === "switch")
                                controller.contextChanged(replacement);
                            else controller.dispose();
                        }
                    });
                    if (path === "confirm") await controller.confirm(true);
                    else await controller.lookup();
                    require(notified, "result subscriber exercised");
                    require(controller.get().result === null &&
                        !controller.get()
                            .consent, "replacement/disposed presentation stays cleared");
                    require(refreshes ===
                        0, "result notification retirement fences later refresh");
                    require(calls.filter((name) => name === "fork_start")
                        .length ===
                        (path === "confirm"
                            ? 1
                            : 0), "lookup and selection change never create a child");
                    require(calls.filter((name) => name === "fork_lookup")
                        .length ===
                        (path === "lookup" ? 1 : 0), "no reentrant lookup");
                    release();
                    controller.dispose();
                },
            );
        }
    }
    return { kind: "actual-controller-mock-ipc", results };
}
