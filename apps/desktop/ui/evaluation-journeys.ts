// Fixed synthetic built-in runner through the actual evaluation controller/native IPC.
import type { Controller } from "./controller";
import type { EvaluationController } from "./evaluation-controller";
import type { ErrorBuffer } from "./model";
import { structural } from "./model";
export async function evaluationJourneys({
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
    let failedCheck = "evaluation-start";
    const check = (v: unknown, id: string) => {
        failedCheck = id;
        if (!v) throw Error(id);
        checks.push(id);
    };
    const until = async (f: () => boolean) => {
        for (let i = 0; i < 1000; i++) {
            if (f()) return;
            await new Promise((r) => setTimeout(r, 10));
        }
        throw Error("EvaluationTimeout");
    };
    const capture = async (label: string) => {
        await new Promise((r) => setTimeout(r, 120));
        document
            .querySelector(
                label === "copy"
                    ? ".evaluation-source"
                    : ["receipt", "failed", "narrow"].includes(label)
                      ? ".evaluation-case"
                      : ".evaluation-panel",
            )
            ?.scrollIntoView({ block: "start" });
        for (const n of document.querySelectorAll(
            ".evaluation-panel .storage-path",
        ))
            n.textContent = "<synthetic evaluation storage>";
        await new Promise((r) => setTimeout(r, 100));
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            `${label}-no-horizontal-overflow`,
        );
        await invoke("harness_checkpoint", {
            label,
            snapshot: {
                synthetic: true,
                uiRevision: c.get().play?.revision,
                checks: [...checks],
                evaluation: {
                    ...e.get(),
                    catalog: e.get().catalog
                        ? {
                              ...e.get().catalog,
                              location: "<synthetic evaluation storage>",
                          }
                        : null,
                },
                dom: {
                    text: document.querySelector(".evaluation-panel")
                        ?.textContent,
                    horizontalOverflow:
                        document.documentElement.scrollWidth > innerWidth + 2,
                },
            },
        });
    };
    try {
        await c.start();
        const before = structural(c.get().play);
        c.requestLab();
        c.acknowledgeLab(true);
        await new Promise((r) => setTimeout(r, 100));
        await e.show();
        check(
            e.get().catalog?.cases.length === 12,
            "d07-native-evaluation-checkpoints",
        );
        if (config.stage === "reopened") {
            const latest = e
                .get()
                .catalog!.runs.filter((r) => r.selection === null)
                .sort((a, b) => b.created - a.created)[0];
            await e.open(latest.run_id);
            check(
                e.get().report?.cases.length === 1 && !e.get().status?.running,
                "evaluation-window-retirement-drains-at-boundary",
            );
            check(
                e.get().report?.completed === false,
                "evaluation-reopen-never-auto-resumes-an-interrupted-suite",
            );
            await invoke("harness_evaluation_case", {
                scenario: "release-boundary",
            });
            await capture("reopened");
            await c.refresh();
            check(
                structural(c.get().play) === before,
                "evaluation-reopen-keeps-selected-player-canon",
            );
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
            return;
        }
        if (config.stage === "restart") {
            check(
                e.get().catalog!.runs.length >= 2,
                "evaluation-restart-lists-private-retained-runs",
            );
            const run = e
                .get()
                .catalog!.runs.filter((r) => r.selection === null)
                .sort((a, b) => a.created - b.created)[0];
            await e.open(run.run_id);
            check(
                e.get().report?.cases.length === 12 &&
                    e.get().report?.completed,
                "evaluation-explicit-recovery-rebuilds-checkpointed-report",
            );
        } else {
            await invoke("harness_evaluation_case", {
                scenario: "hold-boundary",
            });
            const pending = e.start();
            await until(() => e.get().status?.completed_cases === 1);
            check(
                e.get().status?.running,
                "evaluation-worker-is-responsive-at-fixed-boundary",
            );
            await e.cancel();
            await pending;
            check(
                !e.get().busy &&
                    e.get().report?.cases.length === 1 &&
                    !e.get().report?.completed,
                "evaluation-cancel-keeps-one-completed-scenario",
            );
            await capture("pending");
            await invoke("harness_evaluation_case", {
                scenario: "release-boundary",
            });
            await e.resume();
            check(
                e.get().report?.cases.length === 12 &&
                    e.get().report?.completed,
                "evaluation-resume-completes-without-double-count",
            );
            const original = e.get().status!.run_id;
            await e.rerun();
            check(
                e.get().status!.run_id !== original &&
                    e.get().report?.cases.length === 1,
                "evaluation-selected-builtin-rerun-uses-new-private-run",
            );
            await e.show();
            await e.open(original);
        }
        const report = e.get().report!;
        check(
            report.cases.filter((x) => x.status === "passed").length === 9 &&
                report.cases.filter((x) => x.status === "failed").length ===
                    0 &&
                report.cases.filter((x) => x.status === "unsupported")
                    .length === 3,
            "evaluation-real-native-nine-pass-three-unsupported",
        );
        check(
            report.cases.reduce((n, x) => n + x.checks.length, 0) === 196,
            "evaluation-real-native-196-checks",
        );
        check(
            report.quality_accepted === false &&
                report.model === null &&
                report.android_parity === "not_run",
            "evaluation-unmeasured-lanes-not-fabricated",
        );
        await capture("initial");
        e.selectCase("spent-potion");
        const anchor = e.selected()!.checks.find((x) => x.turn)?.turn!;
        e.selectTurn(anchor);
        check(
            e.get().selectedTurn === anchor,
            "evaluation-source-anchor-stays-report-local",
        );
        await capture("receipt");
        await capture("copy");
        e.selectCase("portable-archive");
        await capture("failed");
        check(
            e.selected()?.status === "unsupported",
            "evaluation-archive-is-explicitly-unsupported",
        );
        e.selectCase("spent-potion");
        await invoke("harness_viewport", { preset: "narrow" });
        await capture("narrow");
        await invoke("harness_viewport", { preset: "wide" });
        c.returnToPlay();
        await new Promise((r) => setTimeout(r, 100));
        check(
            e.get().report === null && !e.get().shown,
            "evaluation-return-play-clears-results-and-source",
        );
        await c.refresh();
        check(
            structural(c.get().play) === before,
            "evaluation-never-mutates-selected-player-story",
        );
        check(
            errors.snapshot().length === 0,
            "evaluation-no-unhandled-render-errors",
        );
        if (config.stage === "initial") {
            c.requestLab();
            c.acknowledgeLab(true);
            await new Promise((r) => setTimeout(r, 50));
            await e.show();
            await invoke("harness_evaluation_case", {
                scenario: "hold-boundary",
            });
            void e.start();
            await until(() => e.get().status?.completed_cases === 1);
            await invoke("harness_reopen");
            return;
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
    } catch {
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                failedCheck,
                stage: config.stage,
                checks,
                errors: errors.snapshot(),
                evaluation_error: e.get().error,
            },
        });
    }
}
