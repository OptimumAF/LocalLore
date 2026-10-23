// Development-only fixed synthetic journeys: actual app controllers/native IPC.
import type { Controller } from "./controller";
import type { ForkController } from "./fork-controller";
import type { TimelineController } from "./timeline-controller";
import { resumeTimeline } from "./timeline-controller";
import { structural, type ErrorBuffer, type Scope } from "./model";
type Invoke = (
    name: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
export async function forkNativeJourneys({
    controller: c,
    fork: f,
    timeline: t,
    errors,
    invoke,
    dispose,
    config,
}: {
    controller: Controller;
    fork: ForkController;
    timeline: TimelineController;
    errors: ErrorBuffer;
    invoke: Invoke;
    dispose: () => Promise<void>;
    config: { stage: string };
}) {
    const checks: string[] = [];
    let current = "fork-start";
    const scope = (branch: string): Scope => ({ story: "fork-native", branch });
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
        throw Error("ForkNativeTimeout");
    };
    const fixture = (action: string) => invoke("harness_fork_case", { action });
    const catalog = async () => {
        await t.show();
        return t.get().catalog!;
    };
    const capture = async (label: string) => {
        await new Promise((r) => setTimeout(r, 100));
        const root = document.getElementById("root")!,
            panel = root.querySelector(".fork-panel");
        check(
            !!panel &&
                root.textContent?.includes("Synthetic alternate timelines"),
            `${label}-story-and-panel-visible`,
        );
        check(
            panel?.textContent?.includes(c.selected()!.scope.branch) &&
                panel?.textContent?.includes(
                    `head ${c.get().play!.revision}`,
                ) &&
                panel?.textContent?.includes(
                    c.get().view === "play" ? "player" : c.get().observer,
                ),
            `${label}-selected-branch-observer-revision-visible`,
        );
        if (f.get().request)
            check(
                panel?.textContent?.includes(f.get().request!.child_branch),
                `${label}-fixed-identity-visible`,
            );
        if (f.get().error)
            check(
                panel
                    ?.querySelector('[role="alert"]')
                    ?.textContent?.includes(f.get().error!),
                `${label}-error-visible`,
            );
        if (f.get().operation !== null)
            check(
                panel
                    ?.querySelector(".fork-operation")
                    ?.textContent?.includes(`operation ${f.get().operation}`),
                `${label}-operation-visible`,
            );
        panel?.scrollIntoView({ block: "start" });
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
        const reply = (await invoke("harness_checkpoint", {
            label,
            snapshot: {
                ...semantic,
                fork: f.get(),
                checks: [...checks],
                dom: {
                    text: root.textContent
                        ?.slice(0, 48000)
                        .replaceAll(location, "<synthetic-workspace>"),
                    fork: panel?.textContent,
                    roles: [
                        ...panel!.querySelectorAll(
                            "button,select,input,[role]",
                        ),
                    ].map((el) => ({
                        tag: el.tagName,
                        role: el.getAttribute("role"),
                        label:
                            el.getAttribute("aria-label") ??
                            el.textContent?.slice(0, 140),
                        disabled: el.hasAttribute("disabled"),
                    })),
                    viewport: { width: innerWidth, height: innerHeight },
                },
            },
        })) as { rendering: string };
        check(
            reply.rendering === "native-webview2",
            `${label}-actual-native-webview-render`,
        );
    };
    try {
        await c.start();
        await c.resume(scope("main"));
        check(
            c.get().workspace?.persistent &&
                c.selected()?.name === "Synthetic alternate timelines",
            "d08-fork-native-durable-workspace",
        );
        if (config.stage === "initial") {
            check(
                c.get().play?.revision === 3 &&
                    c.get().play?.receipts[0].events.length === 2,
                "fixed-two-event-completed-prefix-and-later-parent",
            );
            f.prepare(1, "midturn-child");
            await capture("fork-prepared");
            const options = [
                ...document.querySelectorAll(".fork-panel select option"),
            ].map((el) => (el as HTMLOptionElement).value);
            check(
                options.join(",") === "0,2,3",
                "UI-offers-only-completed-receipt-boundaries",
            );
            await f.confirm(true);
            check(
                f.get().error === "Rule",
                "actual-Store-rejects-midturn-boundary",
            );
            await capture("fork-rejected");
            await f.lookup();
            check(
                f.get().status === "not_found",
                "rejected-midturn-child-absent",
            );
            f.prepare(2, "stale-child");
            await fixture("advance-parent");
            await f.confirm(true);
            check(
                f.get().error === "Stale",
                "actual-Store-rejects-stale-creation-head",
            );
            await f.lookup();
            check(f.get().status === "not_found", "stale-child-absent");
            await c.refresh();
            check(
                c.get().play?.revision === 4,
                "actual-external-parent-advance-refreshed",
            );
            const canonical = structural(c.get().play);
            f.prepare(2, "accepted-child");
            await f.confirm(true);
            check(
                f.get().result?.created && f.get().result?.head_revision === 2,
                "actual-fork-accepted-at-completed-prefix",
            );
            check(
                c.selected()?.scope.branch === "main" &&
                    structural(c.get().play) === canonical,
                "fork-preserves-original-canonical-view-and-selection",
            );
            await capture("fork-accepted");
            await f.confirm(true);
            check(
                f.get().result?.created === false &&
                    f.get().result?.scope.branch === "accepted-child",
                "explicit-exact-child-retry-no-duplicate",
            );
            f.prepare(2, "cancel-child");
            await fixture("hold");
            const pending = f.confirm(true);
            await until(() => f.get().busy && f.get().operation !== null);
            await capture("fork-pending");
            let busy = "";
            try {
                await invoke("fork_start", {
                    session: c.selected()!.id,
                    input: { ...f.get().request, child_branch: "busy-child" },
                    consent: true,
                });
            } catch (e) {
                busy = String(e);
            }
            check(
                busy === "ArchiveBusy",
                "existing-single-native-worker-refuses-concurrent-fork",
            );
            await f.cancel();
            await fixture("release");
            await pending;
            check(
                f.get().error === "Cancelled" &&
                    structural(c.get().play) === canonical,
                "pending-cancel-keeps-parent-canonical-state",
            );
            await capture("fork-cancelled");
            await f.lookup();
            check(
                f.get().status === "not_found",
                "cancelled-child-absent-in-actual-catalog",
            );
            f.prepare(2, "switch-child");
            await fixture("hold");
            const switching = f.confirm(true);
            await until(() => f.get().operation !== null && f.get().busy);
            const staleOperation = f.get().operation!;
            await resumeTimeline(c, scope("accepted-child"));
            await until(async () => {
                const status = (await invoke("archive_status", {
                    operationId: staleOperation,
                })) as { running: boolean };
                return !status.running;
            });
            await fixture("release");
            await switching;
            check(
                c.selected()?.scope.branch === "accepted-child" &&
                    c.get().play?.revision === 2 &&
                    f.get().result === null &&
                    f.get().lookupOnly,
                "session-switch-suppresses-stale-fork-completion",
            );
            check(
                !structural(c.get().play).includes("PARENT_FUTURE_EXCLUDED") &&
                    c.get().play!.receipts[0].request.scope.branch === "main",
                "child-rebuild-preserves-original-scope-excludes-later-parent",
            );
            await capture("fork-switched");
            await resumeTimeline(c, scope("main"));
            await f.lookup();
            check(
                f.get().status === "not_found",
                "session-switch-cancelled-child-not-created",
            );
            f.prepare(2, "uncertain-child");
            await fixture("lose-ack");
            await f.confirm(true);
            check(
                f.get().error === "Transport" && f.get().result === null,
                "actual-commit-withheld-ack-is-uncertain",
            );
            await capture("fork-unknown");
            await f.confirm(true);
            check(
                f.get().result?.created === false &&
                    f.get().result?.scope.branch === "uncertain-child",
                "lost-ack-explicit-exact-retry-finds-committed-child",
            );
            await capture("fork-retry");
            await resumeTimeline(c, scope("uncertain-child"));
            const before = structural(c.get().play);
            c.selectReceipt("fork-prefix");
            c.requestLab();
            c.acknowledgeLab(true);
            c.setObserver("mira");
            await until(() => c.get().inspectionObserver === "mira");
            check(
                structural(c.get().inspection).includes(
                    "ORIGINAL_PREFIX_MIRA_ONLY",
                ),
                "witness-Mira-retains-inherited-statement",
            );
            c.setObserver("sable");
            await until(() => c.get().inspectionObserver === "sable");
            check(
                !structural(c.get().inspection).includes(
                    "ORIGINAL_PREFIX_MIRA_ONLY",
                ),
                "absent-Sable-cannot-access-inherited-statement",
            );
            check(
                structural(c.get().play) === before &&
                    c.receipt()?.request.scope.branch === "main",
                "inspection-grant-does-not-change-player-canon-or-receipt-source",
            );
            await capture("fork-observer");
            await invoke("harness_viewport", { preset: "capture-narrow" });
            await capture("fork-narrow");
            await invoke("harness_viewport", { preset: "wide" });
            c.setView("play");
            await resumeTimeline(c, scope("main"));
            await f.lookup();
            f.prepare(2, "restart-child");
            await fixture("lose-ack");
            await f.confirm(true);
            check(
                f.get().error === "Transport" &&
                    f.get().request?.child_branch === "restart-child",
                "saved-original-identity-survives-final-lost-ack",
            );
            const names = (await catalog()).branches
                .map((r) => r.scope.branch)
                .sort();
            check(
                names.join(",") ===
                    "accepted-child,main,restart-child,uncertain-child",
                "only-four-intended-canonical-branches-exist",
            );
            await capture("fork-finished");
        } else {
            check(
                c.get().play?.revision === 4 &&
                    f.get().lookupOnly &&
                    f.get().request?.child_branch === "restart-child",
                "actual-process-restart-restores-fixed-identity-lookup-only",
            );
            const before = (await catalog()).branches.length;
            await f.confirm(true);
            check(f.get().result === null, "restart-confirm-never-reexecutes");
            await f.lookup();
            check(
                f.get().result?.created === false &&
                    f.get().result?.head_revision === 2,
                "restart-lookup-finds-current-existing-child",
            );
            await capture("fork-restarted");
            const saved = f.get().request!;
            f.restore({ ...saved, child_branch: "restart-missing" });
            await f.lookup();
            await f.confirm(true);
            check(
                f.get().status === "not_found" &&
                    (await catalog()).branches.length === before,
                "restart-missing-identity-never-creates-after-lookup",
            );
            await capture("fork-missing");
            f.restore(saved);
            await f.lookup();
            await resumeTimeline(c, scope("restart-child"));
            check(
                c.get().play?.revision === 2 &&
                    !structural(c.get().play).includes(
                        "PARENT_FUTURE_EXCLUDED",
                    ),
                "restart-explicit-resume-validates-prefix-no-future",
            );
            await capture("fork-reopened");
        }
        check(
            errors.snapshot().length === 0,
            "zero-unexpected-frontend-or-gameplay-native-errors",
        );
        await dispose();
        const stats = (await invoke("harness_stats")) as {
            sessions: number;
            workers: number;
        };
        check(
            stats.sessions === 0 && stats.workers === 0,
            "all-owned-host-sessions-and-workers-released",
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
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                checks,
                failedCheck: current,
                error:
                    error instanceof Error
                        ? error.message
                        : String(error).slice(0, 100),
                errors: errors.snapshot(),
            },
        });
    }
}
