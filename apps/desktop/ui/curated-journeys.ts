// Fixed synthetic application-owned native IPC journey; no model, desktop input or dialogs.
import type { Controller } from "./controller";
import type { EvaluationController } from "./evaluation-controller";
import type { ErrorBuffer } from "./model";
import { structural } from "./model";
export async function curatedJourneys({
    controller: c,
    evaluation: e,
    invoke,
    dispose,
    errors,
    config,
}: {
    controller: Controller;
    evaluation: EvaluationController;
    invoke: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
    dispose: () => Promise<void>;
    errors: ErrorBuffer;
    config: { stage: string };
}) {
    const checks: string[] = [];
    let failedCheck = "curated-initial";
    const check = (value: unknown, label: string) => {
        failedCheck = label;
        if (!value) throw Error(label);
        checks.push(label);
    };
    const until = async (fn: () => boolean) => {
        for (let n = 0; n < 1500; n++) {
            if (fn()) return;
            await new Promise((r) => setTimeout(r, 10));
        }
        throw Error("CuratedJourneyTimeout");
    };
    const capture = async (label: string, selector = ".curated-evaluation") => {
        await new Promise((r) => setTimeout(r, 100));
        document.querySelector(selector)?.scrollIntoView({ block: "start" });
        await new Promise((r) => setTimeout(r, 100));
        const panel = document.querySelector<HTMLElement>(
                ".curated-evaluation",
            ),
            s = e.get(),
            run = s.curatedStatus;
        const overflow = document.documentElement.scrollWidth > innerWidth + 2,
            nested = !!panel && panel.scrollWidth > panel.clientWidth + 2;
        await invoke("harness_checkpoint", {
            label,
            snapshot: {
                synthetic: true,
                uiRevision: c.get().play?.revision ?? 0,
                checks: [...checks],
                selectedStory: c.selected()?.scope,
                observer: c.get().observer,
                revision: c.get().play?.revision,
                pendingOperation: run?.operation_id ?? null,
                displayedReceipt: s.curatedEvidence?.evidence.receipt ?? null,
                visibleError: s.curatedError,
                evaluation: {
                    run_id: run?.run_id,
                    lane: run?.lane,
                    phase: run?.phase,
                    completed: run?.completed,
                    checkpointed: run?.completed_cases,
                    binding: run?.source_binding,
                    budget: run?.snapshot?.budget,
                    selectedCase: s.curatedCase,
                    selectedTurn: s.curatedTurn,
                    evidence: s.curatedEvidence?.evidence,
                },
                dom: {
                    text: panel?.innerText.slice(0, 24576),
                    controls: [
                        ...(panel?.querySelectorAll("button,select,summary") ??
                            []),
                    ].map((n) => ({
                        tag: n.tagName,
                        text: n.textContent?.slice(0, 256),
                        disabled: (n as HTMLButtonElement).disabled ?? false,
                    })),
                    width: innerWidth,
                    horizontalOverflow: overflow,
                    nestedOverflow: nested,
                },
            },
        });
        check(!overflow, `${label}-no-overflow`);
        check(!nested, `${label}-no-nested-overflow`);
    };
    try {
        await c.start();
        const before = structural(c.get().play);
        c.requestLab();
        c.acknowledgeLab(true);
        await e.show();
        await e.curatedShow();
        check(
            e.get().curatedCatalog?.cases.length === 6,
            "actual-native-curated-catalog",
        );
        if (config.stage !== "initial") {
            const saved = e
                .get()
                .curatedCatalog!.runs.find(
                    (r) => r.batch === "one" && r.selection === null,
                );
            check(saved, "retained-original-run-present");
            await e.curatedOpen(saved!.run_id);
            check(
                e.get().curatedStatus?.completed === true,
                "restart-open-completed-without-execution",
            );
            const budget = JSON.stringify(
                e.get().curatedStatus!.snapshot!.budget,
            );
            await e.curatedResume(false);
            check(
                JSON.stringify(e.get().curatedStatus!.snapshot!.budget) ===
                    budget,
                "completed-cache-no-new-reservation",
            );
            await capture(
                config.stage === "restart"
                    ? "curated-restarted"
                    : "curated-retired",
            );
        } else {
            await capture("curated-library");
            await invoke("harness_evaluation_case", {
                scenario: "lose-curated-start-ack",
            });
            await e.curatedStart("scripted", null, "one");
            check(
                e.get().curatedError === "EvaluationIo" &&
                    !!e.get().pendingClient,
                "actual-start-ack-lost-original-id-retained",
            );
            await capture("curated-lost-ack");
            await e.curatedRecover();
            check(
                e.get().curatedStatus?.completed_cases === 1,
                "original-start-recovered-one-checkpoint",
            );
            const id = e.get().curatedStatus!.run_id;
            await e.curatedResume();
            check(
                e.get().curatedStatus?.completed_cases === 6 &&
                    e.get().curatedStatus?.completed,
                "same-run-resumes-six-checkpoints",
            );
            check(
                e.get().curatedStatus?.run_id === id,
                "lost-ack-never-creates-another-run",
            );
            check(
                e
                    .get()
                    .curatedStatus!.snapshot!.report.cases.every(
                        (row) => row.status === "passed",
                    ),
                "scripted-curated-hard-checks-pass",
            );
            await capture("curated-completed");
            const selected = e.curatedSelected()!;
            e.curatedSelectTurn(selected.turns[0].id);
            await e.curatedInspect();
            check(
                !!e.get().curatedEvidence?.evidence.receipt,
                "actual-evaluated-accepted-receipt",
            );
            check(
                e.get().curatedEvidence?.evidence.read_only === true &&
                    e.get().curatedEvidence?.evidence.generation_grant ===
                        false,
                "evaluated-snapshot-is-read-only-not-live-grant",
            );
            const details = document.querySelectorAll<HTMLDetailsElement>(
                ".curated-evidence details",
            );
            details[0].open = true;
            details[2].open = true;
            await capture("curated-evidence", ".curated-evidence");
            await invoke("harness_viewport", { preset: "capture-narrow" });
            await capture(
                "curated-output-narrow",
                ".curated-evidence details:last-child",
            );
            await invoke("harness_viewport", { preset: "wide" });
            await e.curatedInspect({ kind: "player" }, "knowledge");
            check(
                e.get().curatedEvidence?.evidence.outputs.length === 0 &&
                    e.get().curatedEvidence?.evidence.receipt === null,
                "player-query-withholds-private-role-output-and-receipt",
            );
            await capture("curated-player", ".curated-evidence");
            c.setObserver("mira");
            check(
                e.get().curatedEvidence === null &&
                    e.get().curatedStatus === null,
                "lens-switch-clears-report-and-evidence-immediately",
            );
            await capture("curated-lens");
            c.setObserver("omniscient");
            await e.show();
            await e.curatedShow();
            await e.curatedOpen(id);
            await invoke("harness_evaluation_case", {
                scenario: "hold-boundary",
            });
            const pending = e.curatedStart("scripted", null, "all");
            await until(() => !!e.get().curatedStatus?.running);
            await capture("curated-pending");
            await e.curatedCancel();
            await pending;
            check(
                !e.get().curatedStatus?.running &&
                    e.get().curatedStatus?.completed_cases === 0,
                "cancel-before-first-story-keeps-no-fictional-results",
            );
            await invoke("harness_evaluation_case", {
                scenario: "release-boundary",
            });
            await capture("curated-cancelled");
            await c.refresh();
            check(
                structural(c.get().play) === before,
                "curated-runs-evidence-and-cancel-preserve-live-canon",
            );
            await invoke("harness_evaluation_case", {
                scenario: "hold-boundary",
            });
            void e.curatedStart("scripted", null, "all");
            await until(() => !!e.get().curatedStatus?.running);
            await invoke("harness_reopen");
            return;
        }
        await c.refresh();
        check(
            structural(c.get().play) === before,
            "restart-and-cache-preserve-live-story",
        );
        const bad = errors
            .snapshot()
            .filter(
                (x) =>
                    !(x.source === "native" && x.category === "EvaluationIo"),
            );
        check(
            bad.length === 0,
            "no-unexpected-native-render-or-unhandled-errors",
        );
        await capture("curated-finished");
        await dispose();
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                stage: config.stage,
                checks,
                errors: errors.snapshot(),
                realModelGeneration: false,
            },
        });
    } catch {
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                stage: config.stage,
                failedCheck,
                checks,
                errors: errors.snapshot(),
                curatedError: e.get().curatedError,
                realModelGeneration: false,
            },
        });
    }
}
