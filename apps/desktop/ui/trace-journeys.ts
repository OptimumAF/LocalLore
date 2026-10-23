// Fixed metadata debugger journey. Real frontend/controller/native IPC; fake inference only.
import { attemptKey } from "./trace-model";
import type { Controller } from "./controller";
import type { FaultGateway } from "./journeys";
import { category, structural } from "./model";
import type { ErrorBuffer, Request, TurnStatus } from "./model";
interface Options {
    controller: Controller;
    gateway: FaultGateway;
    errors: ErrorBuffer;
    invoke: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
    dispose: () => Promise<void>;
    config: {
        stage: "initial" | "reopened" | "restart";
        backend: "native" | "headless";
    };
}
function gate() {
    let release!: () => void, ready!: () => void;
    const waiting = new Promise<void>((r) => (release = r)),
        entered = new Promise<void>((r) => (ready = r));
    return { release, ready, waiting, entered };
}
export async function traceJourneys({
    controller: c,
    gateway: g,
    errors,
    invoke,
    dispose,
    config,
}: Options) {
    const releases: (() => void)[] = [];
    const block = () => {
        const value = gate();
        releases.push(value.release);
        return value;
    };
    const checks: string[] = [];
    let failed = "start";
    const check = (v: unknown, name: string) => {
        failed = name;
        if (!v) throw new Error(name);
        checks.push(name);
    };
    const snap = () =>
        g.call({
            op: "play_snapshot",
            session: c.selected()!.id,
            scope: c.selected()!.scope,
            expected_revision: c.get().play!.revision,
        });
    const text = () =>
        document.querySelector(".turn-debugger")?.textContent ?? "";
    const capture = async (label: string) => {
        await new Promise((r) => setTimeout(r, 120));
        if (
            [
                "d06-committed",
                "d06-failed",
                "d06-pending",
                "d06-cancelled",
                "d06-narrow",
            ].includes(label)
        )
            document
                .querySelector(".trace-detail")
                ?.scrollIntoView({ block: "start" });
        else window.scrollTo({ top: 0 });
        await new Promise((r) => setTimeout(r, 120));
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            `${label}-no-horizontal-overflow`,
        );
        const panel = document.querySelector<HTMLElement>(".turn-debugger");
        check(
            !panel || panel.scrollWidth <= panel.clientWidth + 2,
            `${label}-debugger-no-nested-overflow`,
        );
        await invoke("harness_checkpoint", {
            label,
            snapshot: {
                synthetic: true,
                uiRevision: c.get().play?.revision ?? 0,
                trace: c.get().trace,
                context: {
                    session: c.selected(),
                    view: c.get().view,
                    observer: c.get().observer,
                },
                checks: [...checks],
                dom: {
                    text: document
                        .getElementById("root")
                        ?.textContent?.replaceAll(
                            c.get().workspace?.location ?? "<none>",
                            "<synthetic workspace>",
                        ),
                    horizontalOverflow:
                        document.documentElement.scrollWidth > innerWidth + 2,
                },
            },
        });
    };
    try {
        await c.start();
        check(c.get().workspace?.persistent, "d06-native-durable-workspace");
        if (config.stage === "restart") {
            const saved = c
                .get()
                .workspace?.stories.find((story) => story.revision > 0);
            check(saved, "restart-finds-completed-saved-history");
            await c.resume(saved!.scope);
        }
        await c.showTrace();
        check(
            c.get().trace.reply?.snapshot.status === "disabled",
            "d06-native-default-disabled",
        );
        check(
            c.get().trace.reply?.configuration_scope === "window_host",
            "trace-configuration-is-window-host",
        );
        check(
            c.get().trace.reply?.full_capture === "unsupported",
            "full-capture-is-explicitly-unsupported",
        );
        if (config.stage === "restart") {
            const before = structural(await snap());
            check(
                c.get().trace.reply?.snapshot.attempts.length === 0,
                "restart-never-reconstructs-private-traces",
            );
            await c.controlTrace("enable");
            await c.traceBasis(0);
            check(
                c.get().trace.reply?.snapshot.attempts.length === 0,
                "reenabling-does-not-invent-old-attempts",
            );
            check(
                structural(await snap()) === before,
                "restart-metadata-reads-do-not-mutate-saved-canon",
            );
            await capture("d06-restarted");
        } else {
            await capture("d06-disabled");
            const initial = structural(await snap());
            await c.controlTrace("enable");
            check(
                c.get().trace.enabled === true,
                "capture-requires-explicit-enable",
            );
            check(
                structural(await snap()) === initial,
                "enable-capture-does-not-mutate-canon",
            );
            c.setAction("give");
            c.setFakeMode("accepted");
            g.dropCommit = true;
            await c.send();
            check(
                c.get().turnStatus?.phase === "committed" &&
                    c.get().play?.revision === 1,
                "traced-fake-gift-committed-after-lost-ack",
            );
            await c.traceBasis(0);
            const accepted = c.traceAttempt();
            check(
                accepted?.outcome === "committed",
                "actual-host-trace-finishes-committed",
            );
            check(
                accepted?.identity.base_revision === 0 &&
                    c.get().trace.reply?.head === 1,
                "captured-base-and-current-head-distinct",
            );
            check(
                accepted?.identity.turn === c.get().turnStatus?.turn,
                "trace-matches-exact-original-turn",
            );
            check(
                accepted?.stages.some(
                    (r) =>
                        r.stage === "atomic_commit" &&
                        r.outcome === "committed",
                ),
                "actual-atomic-commit-span-visible",
            );
            check(
                accepted?.provenance.profile_label === "deterministic-fake-v1",
                "fake-fixture-provenance-labelled",
            );
            check(
                accepted?.provenance.model_sha256 === null,
                "unknown-model-hash-remains-null",
            );
            check(
                !accepted?.stages.some((r) => r.stage === "director"),
                "typed-fake-does-not-fabricate-production-role-spans",
            );
            const stable = structural(await snap()),
                beforeReads = g.submissions.length;
            const liveBefore = await invoke("harness_stats");
            await c.readTrace();
            check(
                g.submissions.length === beforeReads &&
                    structural(await invoke("harness_stats")) ===
                        structural(liveBefore),
                "metadata-read-never-starts-an-extra-turn-or-worker",
            );
            check(
                structural(await snap()) === stable,
                "trace-refresh-does-not-change-canonical-receipt-or-state",
            );
            check(
                c.debugReceipt()?.request.turn === accepted?.identity.turn,
                "only-exact-canonical-receipt-linked",
            );
            await capture("d06-context");
            await capture("d06-committed");
            await c.traceToInspection();
            check(
                c.get().query.page?.view === "turn_diff" &&
                    c.get().query.page?.revision === 1,
                "trace-links-real-historical-d05-diff",
            );
            check(
                structural(await snap()) === stable,
                "provenance-navigation-remains-read-only",
            );
            await c.showTrace();
            await c.traceBasis(1);
            c.setAction("wait");
            c.setFakeMode("rejected");
            await c.send();
            await c.readTrace();
            check(
                c.get().play?.revision === 1,
                "rejected-fake-proposal-keeps-head",
            );
            check(
                c.traceAttempt()?.stages.some((r) => r.error === "agency"),
                "observed-fake-failure-has-fixed-agency-category",
            );
            check(
                c.debugReceipt() === null,
                "failed-attempt-is-not-an-accepted-receipt",
            );
            await capture("d06-failed");
            c.setFakeMode("accepted");
            const held = block();
            g.heldPrepare = held;
            const sending = c.send();
            await held.entered;
            await c.readTrace();
            const pendingAttempt = c
                .get()
                .trace.reply?.snapshot.attempts.find(
                    (a) => a.identity.turn === c.get().pending?.turn,
                );
            check(
                pendingAttempt,
                "pending-original-turn-has-its-own-retained-attempt",
            );
            c.selectTrace(attemptKey(pendingAttempt!));
            check(
                c.traceAttempt()?.outcome === "running",
                "prepared-candidate-remains-uncommitted-running-trace",
            );
            check(
                c
                    .traceAttempt()
                    ?.stages.some(
                        (r) =>
                            r.stage === "accepted_candidate" &&
                            r.outcome === "accepted",
                    ),
                "actual-ready-candidate-span-not-proof-of-commit",
            );
            check(
                c.get().play?.revision === 1,
                "pending-preparation-noncanonical",
            );
            await capture("d06-pending");
            await c.cancel();
            held.release();
            await sending;
            await c.readTrace();
            check(
                c.traceAttempt()?.outcome === "cancelled",
                "actual-cancelled-trace-labelled",
            );
            check(
                structural(await snap()) === stable,
                "cancelled-candidate-never-changes-saved-canon",
            );
            await capture("d06-cancelled");
            const old = block();
            g.heldTrace = old;
            const oldRead = c.readTrace();
            await old.entered;
            c.requestLab();
            check(
                c.get().labPending,
                "lab-trace-lens-requires-deliberate-ui-ack",
            );
            c.acknowledgeLab(true);
            c.setObserver("mira");
            await c.readTrace();
            old.release();
            await oldRead;
            const characterObserver = c.get().trace.reply?.observer;
            check(
                characterObserver?.kind === "character" &&
                    characterObserver.id === "mira",
                "trace-reply-retains-requested-character-lens",
            );
            check(
                c.get().trace.reply?.snapshot.attempts.length === 0,
                "character-never-inherits-player-attempts",
            );
            check(
                !text().includes(accepted!.identity.turn),
                "old-player-trace-cleared-before-character-presentation",
            );
            await capture("d06-lens");
            c.setObserver("omniscient");
            await c.traceBasis(0);
            check(
                c.traceAttempt()?.identity.observer === "player",
                "omniscient-keeps-original-attempt-observer",
            );
            check(
                c.debugReceipt() === null,
                "private-lens-does-not-implicitly-open-player-receipt",
            );
            c.setView("play");
            await c.traceBasis(1);
            const session = c.selected()!,
                head = c.get().play!.revision;
            const request = {
                version: 1,
                scope: session.scope,
                turn: "d06-external-wait",
                expected_revision: head,
                intent: { kind: "actions", value: [{ op: "wait", ticks: 1 }] },
            } as Request;
            await g.call({
                op: "submit",
                session: session.id,
                request,
                mode: "accepted",
            });
            for (const op of ["prepare", "commit"] as const)
                await g.call({
                    op,
                    session: session.id,
                    scope: session.scope,
                    turn: request.turn,
                });
            await c.readTrace();
            check(
                c.get().trace.error === "Stale" && c.get().trace.reply === null,
                "external-head-change-hides-stale-trace-data",
            );
            await capture("d06-stale");
            await c.refresh();
            check(
                c.get().trace.reply?.head === 2,
                "explicit-gameplay-refresh-reconciles-trace-head",
            );
            const oldSession = session.id;
            const delayed = block();
            g.heldTrace = delayed;
            const oldStoryRead = c.readTrace();
            await delayed.entered;
            await c.create();
            delayed.release();
            await oldStoryRead;
            check(
                c.selected()?.id !== oldSession &&
                    c.get().trace.reply?.scope.story ===
                        c.selected()?.scope.story,
                "late-trace-cannot-cross-new-session",
            );
            check(
                c.get().trace.reply?.snapshot.attempts.length === 0,
                "new-session-cannot-read-old-owner-traces",
            );
            await c.switchSession(oldSession);
            await c.traceBasis(0);
            const beforeClear = structural(await snap());
            await c.controlTrace("clear");
            check(
                c.get().trace.reply?.snapshot.attempts.length === 0 &&
                    c.get().trace.enabled === true,
                "clear-deletes-window-metadata-without-disabling",
            );
            check(
                structural(await snap()) === beforeClear,
                "clear-never-deletes-canonical-receipts",
            );
            await capture("d06-cleared");
            await c.controlTrace("disable");
            check(
                c.get().trace.reply?.snapshot.status === "disabled",
                "disable-deletes-and-stops-capture",
            );
            check(
                structural(await snap()) === beforeClear,
                "disable-never-changes-canon",
            );
            await invoke("harness_viewport", { preset: "narrow" });
            c.layout(0, 0, 150);
            await capture("d06-narrow");
            await invoke("harness_viewport", { preset: "wide" });
            c.layout(1, 1, 100);
            check(
                document.querySelector(".skip")?.getAttribute("href") ===
                    "#trace-controls",
                "keyboard-skip-points-to-visible-debugger-controls",
            );
            const button = document.querySelector<HTMLButtonElement>(
                ".trace-controls button",
            )!;
            button.focus();
            check(
                document.activeElement === button,
                "debugger-native-button-keyboard-focus",
            );
            check(
                text().includes("raw proposals") &&
                    text().includes("summary maintenance") &&
                    text().includes("pause/step"),
                "unavailable-artifacts-are-labelled-without-fabrication",
            );
            check(
                !errors
                    .snapshot()
                    .some((e) =>
                        ["RenderError", "UnhandledError"].includes(e.category),
                    ),
                "trace-render-has-no-unhandled-errors",
            );
            await capture("d06-finished");
        }
        await dispose();
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                stage: config.stage,
                checks,
                errors: errors.snapshot(),
            },
        });
    } catch (error) {
        const failedCheck = failed;
        releases.forEach((release) => release());
        await capture("d06-failure").catch(() => {});
        await dispose().catch(() => {});
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                failedCheck,
                error: category(error),
                checks,
                errors: errors.snapshot(),
            },
        });
    }
}
