// Frozen source review: actual ForkController/BrokerRetention, fixed mocked IPC.
// No native, SQLite, WebView, model, device or desktop execution.
import { BrokerRetention } from "./broker-retention";
import { ForkController } from "./fork-controller";
import type { TimelineContext } from "./timeline-model";

export async function brokerForkErrorReviewJourneys() {
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
    const context: TimelineContext = {
        session: "session-1",
        scope: { story: "fork-error-review", branch: "main" },
        revision: 1,
        view: "play",
        observer: "player",
        persistent: true,
    };
    const identity = {
        surface: "fork" as const,
        session: context.session,
        story: context.scope.story,
        branch: context.scope.branch,
        head: context.revision,
        action: "fork",
        child: "fixed-child",
        at: 0,
    };
    const memoryIdentity = {
        surface: "memory" as const,
        session: context.session,
        story: context.scope.story,
        branch: context.scope.branch,
        head: context.revision,
        action: "status",
    };
    const memoryStatus = () => ({
        version: 1,
        operation_id: 2,
        running: false,
        phase: "completed",
        error: null,
        result: {
            version: 1,
            kind: "memory_maintenance",
            session: context.session,
            scope: context.scope,
            expected_head: context.revision,
            action: "status",
            maintenance: {
                version: 1,
                scope: context.scope,
                head: context.revision,
                action: "status",
                job: null,
            },
        },
    });
    function setup(error: string) {
        let starts = 0,
            lookups = 0;
        const gate: BrokerRetention = new BrokerRetention(
            () =>
                controller.get().busy ||
                controller.get().status === "uncertain",
        );
        const controller: ForkController = new ForkController(
            (command) => {
                if (command === "fork_lookup") {
                    lookups++;
                    return Promise.resolve({
                        version: 1,
                        kind: "fork_lookup",
                        found: false,
                        outcome: null,
                    });
                }
                starts++;
                return gate.start(identity, async () => ({
                    version: 1,
                    operation_id: 1,
                    running: false,
                    phase: "error",
                    error,
                    result: null,
                }));
            },
            async () => {},
            () => {},
        );
        controller.subscribe(gate.refreshConsumption);
        controller.contextChanged(context);
        controller.prepare(0, "fixed-child");
        return {
            gate,
            controller,
            get starts() {
                return starts;
            },
            get lookups() {
                return lookups;
            },
        };
    }
    await test("unknown-fork-terminal-error-retains-global-uncertainty", async () => {
        const s = setup("SyntheticUnknownCategory");
        await s.controller.confirm(true);
        const actualWire =
            s.controller.get().error === "Wire" &&
            s.controller.get().status === "uncertain";
        s.controller.contextChanged({ ...context, session: "session-2" });
        const localUncertaintyPreserved =
            s.controller.get().status === "uncertain" &&
            s.controller.get().error === null;
        const globalUnknown = s.gate.get()?.unknown === true;
        let dispatched = false,
            blocked = false;
        try {
            await s.gate.start(memoryIdentity, async () => {
                dispatched = true;
                return memoryStatus();
            });
        } catch (error) {
            blocked = error instanceof Error && error.message === "ArchiveBusy";
        }
        check(
            actualWire,
            "actual ForkController maps unrecognized native category to Wire",
        );
        check(
            localUncertaintyPreserved,
            "context change preserves existing local lookup-only uncertainty",
        );
        check(
            globalUnknown,
            "unrecognized terminal category remains globally unresolved independent of local presentation",
        );
        check(
            blocked && !dispatched && s.starts === 1,
            "unknown category never authorizes another surface or reruns fork",
        );
    });
    await test("known-fork-cancelled-category-keeps-native-meaning-and-explicit-lookup-recovery", async () => {
        const s = setup("Cancelled");
        await s.controller.confirm(true);
        check(
            s.controller.get().error === "Cancelled" &&
                s.controller.get().status === "uncertain",
            "known native Cancelled category is not relabelled Wire or successful rollback",
        );
        check(
            s.gate.get()?.terminal &&
                !s.gate.get()?.unknown &&
                !s.gate.get()?.consumed,
            "known error outcome waits for owning controller recovery",
        );
        s.controller.contextChanged({ ...context, session: "session-2" });
        check(
            s.controller.get().status === "uncertain" &&
                s.controller.get().lookupOnly,
            "selection change never automatically resolves or repeats cancelled fork",
        );
        await s.controller.lookup();
        check(
            s.starts === 1 &&
                s.lookups === 1 &&
                s.controller.get().status === "not_found",
            "explicit exact-child lookup remains readonly and never recreates absence",
        );
        check(
            s.gate.get()?.consumed && !s.gate.get()?.unknown,
            "known error outcome consumed after explicit lookup presentation",
        );
        let dispatched = false;
        await s.gate.start(memoryIdentity, async () => {
            dispatched = true;
            return memoryStatus();
        });
        check(
            dispatched,
            "subsequent explicit other-surface start works after known-error recovery",
        );
    });
    return results;
}
