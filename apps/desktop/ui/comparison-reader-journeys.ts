// Same application controller/native IPC in a hidden WebView2; no desktop input.
import type { Controller } from "./controller";
import type { ComparisonReaderController } from "./comparison-reader-controller";
import { structural, type ErrorBuffer } from "./model";
import type { ViewV2 } from "./v2-view-model";
export async function comparisonReaderJourneys({
    controller: c,
    comparison: r,
    errors,
    invoke,
    dispose,
    config,
}: {
    controller: Controller;
    comparison: ComparisonReaderController;
    errors: ErrorBuffer;
    invoke: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
    dispose: () => Promise<void>;
    config: { stage: string };
}) {
    const checks: string[] = [];
    let failedCheck = "comparison-start";
    let failureCategory: string | null = null;
    let fixtureInventory: Record<string, string> | null = null;
    const check = (value: unknown, label: string) => {
        failedCheck = label;
        if (!value) throw Error(label);
        checks.push(label);
    };
    const until = async (fn: () => boolean) => {
        for (let n = 0; n < 3000; n++) {
            if (fn()) return;
            await new Promise((resolve) => setTimeout(resolve, 10));
        }
        throw Error("ComparisonJourneyTimeout");
    };
    const scenario = async (name: string) => {
        failedCheck = `native-fixture-${name}`;
        return invoke("harness_comparison_reader_case", { scenario: name });
    };
    const inspect = async (
        kind: "query" | "receipt" | "capture" | "outputs",
        edge: "before" | "after" = "after",
        view: ViewV2 = "knowledge",
    ) => {
        failedCheck = `comparison-inspect-${kind}-${edge}`;
        if (kind === "query")
            await r.inspect({
                kind,
                edge,
                observer: r.get().observer,
                view,
            });
        else await r.inspect({ kind, observer: r.get().observer });
    };
    const capture = async (
        label: string,
        selector = "#comparison-reader",
        includeSummary = false,
    ) => {
        failedCheck = `${label}-capture`;
        document.querySelector(selector)?.scrollIntoView({ block: "start" });
        await new Promise((resolve) => setTimeout(resolve, 150));
        const state = r.get(),
            panel = document.querySelector<HTMLElement>("#comparison-reader");
        const selected = state.source?.rows.find(
            (row) =>
                row.row.turn === state.selected?.turn &&
                row.row.arm === state.selected?.arm,
        );
        const overflow = document.documentElement.scrollWidth > innerWidth + 2;
        const nested = !!panel && panel.scrollWidth > panel.clientWidth + 2;
        const evidence = state.evidence;
        const inspectedRevision = evidence
            ? evidence.body.kind === "query"
                ? evidence.body.page.revision
                : evidence.edge === "before"
                  ? evidence.before_head
                  : evidence.edge === "after"
                    ? evidence.after_head
                    : null
            : (selected?.source.after_head ?? null);
        const pendingOperation = state.status?.running
            ? {
                  id: state.status.operation_id,
                  phase: state.status.phase,
                  client: state.clientId,
              }
            : state.busy
              ? { id: null, phase: "awaiting_reply", client: state.clientId }
              : null;
        const summaryProjection =
            includeSummary && state.summary
                ? {
                      kind: "summary_projection",
                      binding: state.summary.binding,
                      report: {
                          version: state.summary.report.version,
                          kind: state.summary.report.kind,
                          lane: state.summary.report.lane,
                          source_matches: state.summary.report.source_matches,
                          completed: state.summary.report.completed,
                          completed_scenes:
                              state.summary.report.completed_scenes,
                          profile: state.summary.report.profile,
                          unavailable: state.summary.report.unavailable,
                          limitations: state.summary.report.limitations,
                          turns: state.summary.report.turns.map((row) => ({
                              turn: row.turn,
                              arm: row.arm,
                              phase: row.phase,
                              error: row.error,
                              expected: row.expected,
                              passed: row.passed,
                              failures: row.failures,
                              roles: row.roles,
                              roles_known: row.roles_known,
                              input_semantic_sha256: row.input_semantic_sha256,
                              output_semantic_sha256:
                                  row.output_semantic_sha256,
                          })),
                      },
                  }
                : null;
        try {
            await invoke("harness_checkpoint", {
                label,
                snapshot: {
                    synthetic: true,
                    semanticVersion: 2,
                    uiRevision: (c.get().play ?? c.get().playV2)?.revision ?? 0,
                    checks: [...checks],
                    errors: errors.snapshot(),
                    fixtureInventory: includeSummary ? fixtureInventory : null,
                    selectedStory: selected?.source.scope ?? null,
                    selectedReport: state.status?.run_token ?? null,
                    observer: state.observer,
                    revision: inspectedRevision,
                    pendingOperation,
                    gameplayContext: {
                        scope: c.selected()?.scope ?? null,
                        revision:
                            (c.get().play ?? c.get().playV2)?.revision ?? null,
                        observer: c.get().observer,
                    },
                    displayedReceipt:
                        state.evidence?.body.kind === "receipt"
                            ? state.evidence.body.receipt
                            : null,
                    visibleError: state.error,
                    comparison: {
                        status: state.status,
                        source: state.source,
                        selected: state.selected,
                        querySelection: state.querySelection,
                        summaryProjection,
                        evidence: state.evidence,
                        uncertain: state.uncertain,
                        busy: state.busy,
                        error: state.error,
                    },
                    dom: {
                        text: panel?.innerText.slice(0, 24576),
                        controls: [
                            ...(panel?.querySelectorAll(
                                "button,select,summary",
                            ) ?? []),
                        ].map((node) => ({
                            tag: node.tagName,
                            text: node.textContent?.slice(0, 256),
                            disabled:
                                (node as HTMLButtonElement).disabled ?? false,
                            value:
                                node instanceof HTMLSelectElement
                                    ? node.value
                                    : null,
                        })),
                        width: innerWidth,
                        userAgent: navigator.userAgent,
                        devicePixelRatio,
                        horizontalOverflow: overflow,
                        nestedOverflow: nested,
                    },
                },
            });
        } catch (error) {
            const categories = new Set([
                "ArtifactTooLarge",
                "ArtifactInvalid",
                "CheckpointInvalid",
                "CheckpointLimit",
                "CheckpointDuplicate",
                "RevisionRequired",
                "SyntheticFixtureRequired",
                "Forbidden",
                "Closed",
                "CaptureUnavailable",
                "CaptureFailed",
                "CaptureTimeout",
            ]);
            failureCategory =
                typeof error === "string" && categories.has(error)
                    ? error
                    : "CheckpointFailed";
            throw error;
        }
        check(!overflow, `${label}-no-page-overflow`);
        check(!nested, `${label}-no-panel-overflow`);
    };
    try {
        await c.start();
        const before = structural(c.get().play ?? c.get().playV2);
        c.requestLab();
        c.acknowledgeLab(true);
        await until(() => r.get().allowed);
        const prepared = (await scenario("prepare")) as {
            paired_rows: number;
            rollout_rows: number;
            fixture_inventory: Record<string, string>;
        };
        fixtureInventory = prepared.fixture_inventory;
        check(
            prepared.paired_rows === 24 && prepared.rollout_rows === 12,
            "actual-scripted-paired-and-rollout-fixtures",
        );
        await scenario("choose-paired");
        failedCheck = "native-comparison-pick";
        await r.pick();
        await r.loadSummary();
        check(
            r.get().status?.phase === "ready" &&
                r.get().source?.rows.length === 24,
            "actual-comparison-reader-native-open",
        );
        check(
            r.get().summary?.report.version === 2,
            "actual-report2-decoded-through-controller",
        );
        check(
            r.get().summary?.report.source_matches === true,
            "fresh-compiled-source-match",
        );
        await capture(
            config.stage === "restart"
                ? "comparison-restarted"
                : "comparison-open",
            "#comparison-reader",
            true,
        );
        const first = r
            .get()
            .source!.rows.find((row) => row.receipt_available)!;
        check(first, "real-accepted-turn-source-present");
        r.select(first.row);
        await inspect("receipt");
        check(
            r.get().evidence?.body.kind === "receipt",
            "actual-rust-accepted-receipt",
        );
        await capture("comparison-receipt", ".comparison-selected");
        await inspect("capture");
        check(
            r.get().evidence?.body.kind === "capture",
            "actual-recorded-context-not-reconstruction",
        );
        await capture("comparison-capture", ".comparison-evidence");
        await inspect("outputs");
        check(
            r.get().evidence?.body.kind === "outputs",
            "actual-recorded-role-outputs",
        );
        await capture("comparison-outputs", ".comparison-evidence");
        await invoke("harness_viewport", { preset: "capture-narrow" });
        await capture("comparison-narrow", ".comparison-evidence");
        await invoke("harness_viewport", { preset: "wide" });
        r.setObserver({ kind: "character", id: "mira" });
        check(
            r.get().summary === null && r.get().evidence === null,
            "mira-transition-clears-all-raw-presentation",
        );
        await inspect("query", "after", "history");
        check(
            JSON.stringify(r.get().evidence).includes(
                "The pennant I carry has an amber stitch.",
            ) && !JSON.stringify(r.get().evidence).includes("SECRET-TIDE-731"),
            "mira-observed-dialogue-without-player-private-secret",
        );
        await capture("comparison-mira", ".comparison-selected");
        r.setObserver({ kind: "character", id: "sable" });
        await inspect("query", "after", "history");
        check(
            !JSON.stringify(r.get().evidence).includes(
                "The pennant I carry has an amber stitch.",
            ) && !JSON.stringify(r.get().evidence).includes("SECRET-TIDE-731"),
            "sable-withholds-unseen-dialogue-and-player-secret",
        );
        await capture("comparison-sable", ".comparison-selected");
        const status = r.get().status!,
            binding = r.get().source!.binding;
        let denial = "";
        try {
            await invoke("evaluation_comparison", {
                action: "evidence",
                query: {
                    runToken: status.run_token,
                    binding,
                    turnId: first.row.turn,
                    arm: first.row.arm,
                    request: {
                        kind: "capture",
                        observer: { kind: "character", id: "sable" },
                    },
                },
            });
        } catch (error) {
            denial = String(error);
        }
        check(denial === "Forbidden", "actual-native-raw-actor-denial");
        r.setObserver({ kind: "player" });
        await inspect("query", "before");
        check(
            JSON.stringify(r.get().evidence).includes("SECRET-TIDE-731"),
            "player-before-state-preserves-own-original-seed-knowledge",
        );
        r.setObserver({ kind: "omniscient" });
        await r.loadSummary();
        const guard = r
            .get()
            .source!.rows.find((row) => !row.receipt_available)!;
        check(guard, "real-guard-only-turn-present");
        r.select(guard.row);
        await inspect("receipt");
        check(
            r.get().evidence?.body.kind === "missing",
            "guard-does-not-invent-receipt",
        );
        await capture("comparison-guard", ".comparison-selected");
        await r.close();
        check(r.get().source === null, "explicit-close-clears-private-source");
        await scenario("hold-picker");
        const opening = r.pick();
        await until(() => r.get().status?.running === true);
        await capture("comparison-pending");
        const closing = r.close();
        await until(
            () =>
                r.get().status?.phase === "closing" || r.get().source === null,
        );
        await scenario("release-picker");
        await closing;
        await opening;
        check(
            r.get().source === null && r.get().summary === null,
            "late-picker-success-not-published-after-close",
        );
        await capture("comparison-closed");
        check(
            errors.snapshot().length === 0,
            "no-unexpected-errors-before-deliberate-lost-ack",
        );
        await scenario("lose-pick-ack");
        await r.pick();
        check(
            r.get().uncertain && !!r.get().clientId,
            "lost-open-ack-keeps-exact-client-for-recovery",
        );
        const client = r.get().clientId;
        await r.recover();
        check(
            r.get().status?.phase === "ready" && r.get().clientId === client,
            "same-client-recovers-existing-native-source",
        );
        await capture("comparison-recovered");
        await r.close();
        await scenario("choose-rollout");
        await r.pick();
        await r.loadSummary();
        check(
            r.get().source?.rows.length === 12 &&
                r.get().summary?.report.kind === "continuous_rollout",
            "separate-actual-rollout-source",
        );
        await capture("comparison-rollout", "#comparison-reader", true);
        c.returnToPlay();
        await until(() => r.get().source === null);
        check(
            r.get().summary === null && r.get().evidence === null,
            "surrounding-play-context-retires-all-private-data",
        );
        c.requestLab();
        c.acknowledgeLab(true);
        await until(() => r.get().allowed);
        await capture("comparison-switched");
        await c.refresh();
        check(
            structural(c.get().play ?? c.get().playV2) === before,
            "all-comparison-actions-preserve-live-gameplay-canon",
        );
        const recorded = errors.snapshot();
        check(
            recorded.length === 1 &&
                recorded[0].source === "native" &&
                recorded[0].category === "Transport",
            "only-deliberately-lost-open-ack-error-recorded",
        );
        await capture("comparison-finished");
        await dispose();
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                stage: config.stage,
                checks,
                errors: errors.snapshot(),
                realModelGeneration: false,
                desktopInput: false,
                rendering: "native-webview2",
                nativeDialogsAutomated: false,
            },
        });
    } catch {
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                stage: config.stage,
                failedCheck,
                failureCategory,
                checks,
                errors: errors.snapshot(),
                comparisonError: r.get().error,
                phase: r.get().status?.phase,
                realModelGeneration: false,
            },
        });
    }
}
