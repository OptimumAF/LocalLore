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
                        require(name === "fork_start", "only explicit fork start");
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
                require(
                    controller.get().result === null,
                    "old terminal result cannot repopulate replacement/disposed owner",
                );
                require(
                    controller.get().status !== "complete",
                    "old completion cannot label replacement/disposed owner",
                );
                require(!controller.get().consent, "old consent remains cleared");
                require(!controller.get().busy, "no replacement busy state");
                require(refreshes === 0, "no stale post-notification refresh");
                require(
                    calls.filter((name) => name === "fork_start").length === 1,
                    "no replacement or automatic fork start",
                );
                if (action === "switch")
                    require(
                        controller.get().lookupOnly,
                        "saved identity remains lookup-only for replacement",
                    );
                release();
                controller.dispose();
            },
        );
    }
    return { kind: "actual-controller-mock-ipc", results };
}
