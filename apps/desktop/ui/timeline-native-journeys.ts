// Development-only fixed fixture: actual frontend controllers and native IPC.
import type { Controller } from "./controller";
import type { TimelineController } from "./timeline-controller";
import type { FaultGateway } from "./journeys";
import { structural, type ErrorBuffer, type Scope } from "./model";
import { timelineJourneys } from "./timeline-journeys";
function gate() {
    let release!: () => void, ready!: () => void;
    const entered = new Promise<void>((r) => (ready = r)),
        waiting = new Promise<void>((r) => (release = r));
    return { release, ready, entered, waiting };
}
export async function timelineNativeJourneys({
    controller: c,
    timeline: t,
    gateway: g,
    errors,
    invoke,
    dispose,
    config,
}: {
    controller: Controller;
    timeline: TimelineController;
    gateway: FaultGateway;
    errors: ErrorBuffer;
    invoke: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
    dispose: () => Promise<void>;
    config: { stage: string };
}) {
    const checks: string[] = [];
    let current = "timeline-start";
    const scope = (branch: string): Scope => ({
        story: "timeline-native",
        branch,
    });
    const check = (ok: unknown, label: string) => {
        current = label;
        if (!ok) throw Error(label);
        checks.push(label);
    };
    const until = async (test: () => boolean | Promise<boolean>) => {
        for (let i = 0; i < 500; i++) {
            if (await test()) return;
            await new Promise((r) => setTimeout(r, 10));
        }
        throw Error("TimelineNativeTimeout");
    };
    const capture = async (label: string) => {
        await new Promise((r) => setTimeout(r, 100));
        const root = document.getElementById("root")!;
        const panel = document.querySelector(".timeline-panel");
        const rows = [
            ...(panel?.querySelectorAll(
                'ul[aria-label="Saved timeline metadata"] > li',
            ) ?? []),
        ];
        check(
            root.childElementCount > 0 &&
                panel?.querySelector("#timeline-title")?.textContent ===
                    "Saved timelines" &&
                !!t.get().catalog &&
                rows.length === t.get().catalog!.branches.length &&
                rows.some(
                    (row) =>
                        row.querySelector("h4 code")?.textContent ===
                            c.selected()?.scope.branch &&
                        row
                            .querySelector("h4")
                            ?.textContent?.includes("selected"),
                ),
            `${label}-rendered-selected-timeline`,
        );
        document
            .querySelector(".timeline-panel")
            ?.scrollIntoView({ block: "start" });
        await new Promise((r) => setTimeout(r, 60));
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            `${label}-no-horizontal-overflow`,
        );
        const location = c.get().workspace?.location ?? "<absent>";
        const semantic = {
            ...c.semantic(),
            workspace: c.get().workspace
                ? { ...c.get().workspace, location: "<synthetic-workspace>" }
                : null,
        };
        const rendered = (await invoke("harness_checkpoint", {
            label,
            snapshot: {
                ...semantic,
                checks: [...checks],
                timeline: t.get(),
                dom: {
                    text: document
                        .getElementById("root")!
                        .textContent?.slice(0, 48000)
                        .replaceAll(location, "<synthetic-workspace>"),
                    viewport: { width: innerWidth, height: innerHeight },
                },
            },
        })) as { rendering?: unknown };
        check(
            rendered.rendering === "native-webview2",
            `${label}-actual-native-render`,
        );
    };
    try {
        await c.start();
        await c.resume(scope("main"));
        check(
            c.get().workspace?.persistent && c.get().play?.revision === 4,
            "d08-timeline-native-durable-workspace",
        );
        if (config.stage === "initial") {
            checks.push(
                ...(await timelineJourneys({
                    controller: c,
                    timeline: t,
                    fixture: {
                        root: scope("main"),
                        child: scope("child"),
                        sibling: scope("sibling"),
                        retired: scope("parent"),
                        childFork: 4,
                        childHead: 4,
                        inheritedSource: scope("parent"),
                        excludedPlayCanaries: [
                            "PARENT_FUTURE_CANARY",
                            "SIBLING_ONLY_CANARY",
                        ],
                    },
                    checkpoint: async (label) => {
                        await t.show();
                        await capture(
                            (
                                {
                                    catalog: "initial",
                                    child: "receipt",
                                    sibling: "session-switch",
                                    root: "play-return",
                                } as const
                            )[label],
                        );
                    },
                })),
            );
            await t.show();
            await t.select("child");
            c.setAction("wait");
            c.setFakeMode("delayed");
            const hold = (g.heldPrepare = gate()),
                pending = c.send();
            await until(
                async () => (await c.pendingStatus())?.phase === "running",
            );
            await t.show();
            await capture("pending");
            await c.cancel();
            hold.release();
            await pending;
            check(
                c.get().play?.revision === 4 &&
                    c.get().turnStatus?.phase === "cancelled",
                "child-cancel-preserves-inherited-prefix",
            );
            await capture("cancelled");
            c.setFakeMode("accepted");
            await c.retry();
            check(
                c.get().play?.revision === 5 &&
                    c.get().turnStatus?.phase === "committed",
                "child-continuation-accepted-on-own-scope",
            );
            const latest = c.get().play!.receipts.at(-1)!;
            check(
                latest.request.scope.branch === "child" &&
                    latest.events.every((e) => e.scope.branch === "child"),
                "child-new-event-original-scope",
            );
            await t.show();
            await capture("retry");
            const delayed = (g.heldView = gate()),
                refresh = c.refresh();
            await delayed.entered;
            await t.show();
            await t.select("sibling");
            delayed.release();
            await refresh;
            check(
                c.selected()?.scope.branch === "sibling" &&
                    c.get().play?.revision === 2,
                "late-child-view-cannot-replace-sibling",
            );
            await t.show();
            await capture("stale");
        }
        await t.show();
        await t.select("child");
        check(
            c.selected()?.scope.branch === "child" &&
                c.get().play?.revision === 5,
            "restart-or-current-child-head-five",
        );
        const before = structural(c.get().play);
        c.requestLab();
        c.acknowledgeLab(true);
        c.setObserver("sable");
        await until(() => c.get().inspectionObserver === "sable");
        check(
            !structural(c.get().inspection).includes(
                "Original inherited parent statement",
            ),
            "sable-cannot-see-unwitnessed-inherited-dialogue",
        );
        check(
            structural(c.get().play) === before,
            "inspection-does-not-alter-play-or-knowledge",
        );
        await t.show();
        await capture("observer");
        await invoke("harness_viewport", { preset: "capture-narrow" });
        await capture("narrow");
        await invoke("harness_viewport", { preset: "wide" });
        c.setView("play");
        await t.show();
        await capture(config.stage === "restart" ? "reopened" : "finished");
        const recorded = errors.snapshot();
        check(
            recorded.length === (config.stage === "initial" ? 2 : 0) &&
                recorded.every(
                    (e) => e.source === "native" && e.category === "Cancelled",
                ),
            "only-expected-native-cancellation-errors",
        );
        await dispose();
        const stats = (await invoke("harness_stats")) as {
            sessions: number;
            workers: number;
        };
        check(
            stats.sessions === 0 && stats.workers === 0,
            "all-owned-session-workers-released",
        );
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                checks,
                errors: errors.snapshot(),
                stage: config.stage,
                realModelGeneration: false,
            },
        });
    } catch (error) {
        errors.add(
            "frontend",
            error instanceof Error ? error.message : "TimelineFailure",
        );
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                checks,
                failedCheck: current,
                error:
                    error instanceof Error
                        ? error.message
                        : typeof error === "string"
                          ? error.slice(0, 100)
                          : "TimelineFailure",
                errors: errors.snapshot(),
            },
        });
    }
}
