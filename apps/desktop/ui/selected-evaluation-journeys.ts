// SOURCE-ONLY / UNRUN at handoff. Normal application controllers and native IPC
// in the owned hidden WebView; only fixed consent/ACK faults are harness doubles.
// Requires Root's selected driver, native dev-only consent double and label list.
import type { Controller } from "./controller";
import type { ComparisonReaderController } from "./comparison-reader-controller";
import type { SelectedEvaluationController } from "./selected-evaluation-controller";
import type {
    SelectedArm,
    SelectedSourceIdentity,
    RowId,
    ObserverV2,
} from "./selected-evaluation-model";
import type { ViewV2 } from "./v2-view-model";
import { structural, type ErrorBuffer } from "./model";
import { sameReaderObserver } from "./comparison-reader-model";

export async function selectedEvaluationJourneys({
    controller: c,
    comparison: r,
    selected: s,
    errors,
    invoke,
    dispose,
    config,
}: {
    controller: Controller;
    comparison: ComparisonReaderController;
    selected: SelectedEvaluationController;
    errors: ErrorBuffer;
    invoke: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
    dispose: () => Promise<void>;
    config: { stage: string };
}) {
    const checks: string[] = [];
    let failedCheck = "selected-start",
        failureCategory: string | null = null;
    let sourceInventory: Record<string, string> | null = null;
    let finalInventory: Record<string, string> | null = null;
    let consentHeld = false,
        disposalStarted = false;
    const savedRuns: string[] = [];
    const check = (condition: unknown, name: string) => {
        failedCheck = name;
        if (!condition) throw Error(name);
        checks.push(name);
    };
    const until = async (condition: () => boolean, name: string) => {
        failedCheck = name;
        for (let n = 0; n < 3000; n++) {
            if (condition()) return;
            await new Promise((resolve) => setTimeout(resolve, 10));
        }
        throw Error("SelectedJourneyTimeout");
    };
    const fixture = (scenario: string) =>
        invoke("harness_comparison_reader_case", { scenario });
    const fault = (
        scenario:
            | "hold-consent"
            | "release-consent"
            | "deny-consent"
            | "lose-start-ack",
    ) => invoke("harness_selected_case", { scenario });
    const lens = async (observer: ObserverV2) => {
        r.setObserver(observer); // same normal panel prop route, not a fake controller context
        await until(
            () => sameReaderObserver(s.get().observer, observer),
            "selected-prop-observer-effect",
        );
    };
    const source = async (
        guard = false,
    ): Promise<{ identity: SelectedSourceIdentity; row: RowId }> => {
        await r.close();
        await fixture("choose-paired");
        await r.pick();
        await lens({ kind: "omniscient" });
        await r.loadSummary();
        const current = r.get();
        check(
            current.status?.phase === "ready" &&
                !!current.clientId &&
                !!current.status.run_token &&
                current.summary?.report.source_matches === true,
            "fresh-source-native-reader-ready",
        );
        // courier-05 is the frozen independent Move at original index4. Guards
        // are selected from actual validated report outcomes, not fabricated rows.
        const entry = guard
            ? current.source?.rows.find(
                  (candidate) =>
                      !candidate.receipt_available &&
                      current.summary?.report.turns.some(
                          (turn) =>
                              turn.turn === candidate.row.turn &&
                              turn.arm === candidate.row.arm &&
                              turn.passed &&
                              turn.expected.includes("GuardRejected"),
                      ),
              )
            : current.source?.rows.find(
                  (candidate) =>
                      candidate.row.turn === "courier-05" &&
                      candidate.row.arm === "right" &&
                      candidate.receipt_available &&
                      candidate.capture_available,
              );
        check(
            entry,
            guard
                ? "actual-guard-source-present"
                : "actual-independent-move-source-present",
        );
        if (
            !entry ||
            !current.clientId ||
            !current.status?.run_token ||
            !current.source
        )
            throw Error("SelectedSourceRequired");
        r.select(entry.row);
        return {
            identity: {
                readerClientId: current.clientId,
                runToken: current.status.run_token,
                binding: current.source.binding,
            },
            row: entry.row,
        };
    };
    const inspect = async (
        arm: SelectedArm,
        kind: "query" | "receipt" | "capture" | "outputs",
        edge: "before" | "after" = "after",
        view: ViewV2 = "knowledge",
    ) => {
        failedCheck = `selected-inspect-${arm}-${kind}-${edge}`;
        if (kind === "query")
            await s.readEvidence(arm, {
                kind,
                edge,
                view,
                observer: s.get().observer,
            });
        else await s.readEvidence(arm, { kind, observer: s.get().observer });
    };
    const capture = async (
        label: string,
        selector = "#selected-evaluation",
        includeInventory = false,
    ) => {
        failedCheck = `${label}-capture`;
        const panel = document.querySelector<HTMLElement>(
            "#selected-evaluation",
        );
        check(panel, `${label}-panel-mounted`);
        (
            panel?.querySelector(selector) ??
            document.querySelector(selector) ??
            panel
        )?.scrollIntoView({ block: "start" });
        await new Promise((resolve) => setTimeout(resolve, 150));
        const state = s.get(),
            evidence = state.evidence;
        const inspectedArm = evidence
            ? state.summary?.arms.find((arm) => arm.arm === evidence.row.arm)
            : state.summary?.arms[0];
        const story =
            evidence?.scope ??
            inspectedArm?.scope ??
            state.status?.prepared?.arms[0]?.scope ??
            null;
        const revision = evidence
            ? evidence.body.kind === "query"
                ? evidence.body.page.revision
                : evidence.edge === "before"
                  ? evidence.before_head
                  : evidence.edge === "after"
                    ? evidence.after_head
                    : null
            : (inspectedArm?.after_head ??
              state.status?.prepared?.arms[0]?.before_head ??
              null);
        const overflow = document.documentElement.scrollWidth > innerWidth + 2;
        const nested = !!panel && panel.scrollWidth > panel.clientWidth + 2;
        const snapshot = {
            synthetic: true,
            semanticVersion: 2,
            uiRevision: (c.get().play ?? c.get().playV2)?.revision ?? 0,
            selectedStory: story,
            selectedReport: state.status?.run_id ?? null,
            observer: state.observer,
            revision,
            pendingOperation: state.pending
                ? {
                      id: state.pending.operationId,
                      client: state.pending.clientId,
                      phase: state.pending.action,
                  }
                : state.uncertain
                  ? {
                        id: null,
                        client: state.clientId,
                        phase: "acknowledgement_unknown",
                    }
                  : null,
            displayedReceipt:
                evidence?.body.kind === "receipt"
                    ? evidence.body.receipt
                    : null,
            visibleError: state.error,
            liveGameplayContext: {
                scope: c.selected()?.scope ?? null,
                revision: (c.get().play ?? c.get().playV2)?.revision ?? null,
                observer: c.get().observer,
            },
            selectedEvaluation: {
                clientId: state.clientId,
                status: state.status,
                observer: state.observer,
                pending: state.pending,
                summary: state.summary,
                evidence,
                diagnostics: state.diagnostics,
                cleanup: state.cleanup,
                busy: state.busy,
                uncertain: state.uncertain,
                error: state.error,
            },
            checks: [...checks],
            errors: errors.snapshot(),
            sourceInventory: includeInventory ? sourceInventory : null,
            finalSourceInventory: includeInventory ? finalInventory : null,
            dom: {
                text: panel?.innerText.slice(0, 24576),
                controls: [
                    ...(panel?.querySelectorAll("button,select,summary") ?? []),
                ].map((node) => ({
                    tag: node.tagName,
                    text: node.textContent?.slice(0, 256),
                    disabled: (node as HTMLButtonElement).disabled ?? false,
                    value:
                        node instanceof HTMLSelectElement ? node.value : null,
                })),
                width: innerWidth,
                userAgent: navigator.userAgent,
                devicePixelRatio,
                horizontalOverflow: overflow,
                nestedOverflow: nested,
            },
        };
        check(
            new TextEncoder().encode(JSON.stringify(snapshot)).length <=
                256 * 1024,
            `${label}-bounded-semantic-snapshot`,
        );
        try {
            await invoke("harness_checkpoint", { label, snapshot });
        } catch (error) {
            const known = new Set([
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
                typeof error === "string" && known.has(error)
                    ? error
                    : "CheckpointFailed";
            throw error;
        }
        check(!overflow, `${label}-no-page-overflow`);
        check(!nested, `${label}-no-panel-overflow`);
    };
    const openCurrent = async () => {
        const id = s.get().status?.run_id;
        check(id, "actual-selected-durable-run-id");
        if (!id) throw Error("SelectedRunRequired");
        await s.open(id);
        await s.loadSummary();
        check(
            !!s.get().summary && !!s.get().status?.run_token,
            "explicit-native-read-consent-and-summary",
        );
        return id;
    };
    const ids = async () => {
        await s.catalog();
        return (
            s
                .get()
                .catalog?.runs.map((run) => run.run_id)
                .sort() ?? []
        );
    };
    try {
        check(
            config.stage === "initial" || config.stage === "restart",
            "closed-selected-harness-stage",
        );
        await c.start();
        const gameplayBefore = structural(c.get().play ?? c.get().playV2);
        c.requestLab();
        c.acknowledgeLab(true);
        await until(
            () => s.get().allowed && r.get().allowed,
            "actual-lab-native-eligibility",
        );
        const preparedFixtures = (await fixture("prepare")) as {
            paired_rows: number;
            rollout_rows: number;
            models_executed: boolean;
            fixture_inventory: Record<string, string>;
        };
        check(
            preparedFixtures.paired_rows === 24 &&
                preparedFixtures.rollout_rows === 12 &&
                preparedFixtures.models_executed === false,
            "actual-scripted-paired-rollout-fixtures-no-models",
        );
        sourceInventory = preparedFixtures.fixture_inventory;
        check(
            Object.keys(sourceInventory).length > 0 &&
                Object.keys(sourceInventory).length <= 2048 &&
                Object.values(sourceInventory).every((hash) =>
                    /^[a-f0-9]{64}$/.test(hash),
                ),
            "native-source-hash-inventory-present",
        );
        const accepted = await source();
        if (config.stage === "restart") {
            await s.catalog();
            const prior = s
                .get()
                .catalog?.runs.find(
                    (run) =>
                        run.selection.turn === accepted.row.turn &&
                        run.lane === "scripted_baseline",
                );
            check(prior, "restart-finds-real-durable-earlier-selected-attempt");
            if (!prior) throw Error("SavedAttemptRequired");
            await s.open(prior.run_id);
            await s.loadSummary();
            check(
                s.get().summary?.selection.turn === accepted.row.turn,
                "cold-process-reopens-exact-saved-turn",
            );
            await capture("selected-restarted");
            await s.close();
        }
        await s.prepare(accepted.identity, accepted.row, "scripted_baseline");
        check(
            s.get().status?.phase === "prepared" &&
                s.get().status?.prepared?.selection.index === 4,
            "actual-native-prepared-original-move4",
        );
        check(
            s.get().status?.prepared?.arms.length === 2 &&
                s.get().status?.run_id === null,
            "prepare-no-durable-execution-yet",
        );
        await capture("selected-prepared");
        await s.start();
        check(
            s.get().status?.phase === "completed" && !s.get().status?.running,
            "actual-scripted-selected-both-attempts-finished",
        );
        check(
            s.get().status?.run_token === null &&
                s.get().status?.binding === null,
            "execution-grant-does-not-mint-read-grant",
        );
        await capture("selected-completed");
        savedRuns.push(await openCurrent());
        check(
            s.get().summary?.selection.turn === accepted.row.turn &&
                s.get().summary?.lane === "scripted_selected_case",
            "opened-summary-binds-actual-selected-case",
        );
        await capture("selected-summary");
        for (const arm of ["left", "right"] as const) {
            const bound = s
                .get()
                .summary?.arms.find((entry) => entry.arm === arm);
            check(
                bound &&
                    bound.after_head !== null &&
                    bound.after_head > bound.before_head,
                `${arm}-actual-accepted-head-advanced`,
            );
            if (!bound) throw Error("SelectedArmRequired");
            for (const edge of ["before", "after"] as const) {
                await inspect(arm, "query", edge, "history");
                const e = s.get().evidence;
                check(
                    e?.body.kind === "query" &&
                        e.row.arm === arm &&
                        e.scope.story === bound.scope.story &&
                        e.scope.branch === bound.scope.branch &&
                        e.body.page.revision ===
                            (edge === "before"
                                ? bound.before_head
                                : bound.after_head),
                    `${arm}-${edge}-actual-query2-scope-head`,
                );
            }
            await capture(
                `selected-${arm}-after`,
                "[aria-label='Displayed selected evidence']",
            );
            await inspect(arm, "query", "after", "turn_diff");
            const diff = s.get().evidence;
            check(
                diff?.body.kind === "query" &&
                    diff.body.page.view === "turn_diff",
                `${arm}-actual-turn-diff-query2`,
            );
        }
        for (const kind of ["receipt", "capture", "outputs"] as const) {
            await inspect("right", kind);
            check(
                s.get().evidence?.body.kind === kind,
                `actual-selected-${kind}-from-rust`,
            );
            await capture(
                `selected-${kind}`,
                "[aria-label='Displayed selected evidence']",
            );
        }
        await invoke("harness_viewport", { preset: "capture-narrow" });
        await capture(
            "selected-narrow",
            "[aria-label='Displayed selected evidence']",
        );
        await invoke("harness_viewport", { preset: "wide" });
        await s.readDiagnostics();
        check(
            s.get().diagnostics?.rows.length === 2 &&
                s
                    .get()
                    .diagnostics?.rows.every(
                        (row) =>
                            row.passed && row.roles_known && row.roles === 2,
                    ) &&
                s.get().diagnostics?.physical_setups === 0 &&
                s.get().diagnostics?.physical_setup_ms === null,
            "scripted-two-role-recordings-no-native-load-measurement",
        );
        check(
            s.get().diagnostics?.quality_accepted === false &&
                s.get().diagnostics?.human_reviewed === 0,
            "no-invented-human-quality-acceptance",
        );
        const identity = {
            client: s.get().clientId,
            operation: s.get().status?.operation_id,
            run: s.get().status?.run_id,
        };
        for (const actor of ["mira", "sable"] as const) {
            await lens({ kind: "character", id: actor });
            check(
                s.get().diagnostics === null && s.get().evidence === null,
                `${actor}-lens-clears-old-omni-body`,
            );
            check(
                s.get().clientId === identity.client &&
                    s.get().status?.operation_id === identity.operation &&
                    s.get().status?.run_id === identity.run,
                `${actor}-lens-does-not-cancel-or-rekey-execution`,
            );
            await inspect("right", "query", "after", "history");
            const body = JSON.stringify(s.get().evidence);
            check(
                !body.includes("SECRET-TIDE-731") &&
                    (actor === "mira"
                        ? body.includes(
                              "The pennant I carry has an amber stitch.",
                          )
                        : !body.includes(
                              "The pennant I carry has an amber stitch.",
                          )),
                `${actor}-actual-original-observer-isolation`,
            );
            const beforeErrors = errors.snapshot().length;
            for (const action of ["evidence", "diagnostics"] as const) {
                const state = s.get();
                let denial = "";
                try {
                    await invoke("evaluation_selected", {
                        action,
                        request: JSON.stringify({
                            clientId: state.clientId,
                            runToken: state.status?.run_token,
                            binding: state.status?.binding,
                            ...(action === "evidence"
                                ? {
                                      arm: "right",
                                      request: {
                                          kind: "capture",
                                          observer: state.observer,
                                      },
                                  }
                                : { observer: state.observer }),
                        }),
                    });
                } catch (error) {
                    denial =
                        typeof error === "string"
                            ? error
                            : error instanceof Error
                              ? error.message
                              : "Unknown";
                }
                check(
                    denial === "Forbidden",
                    `${actor}-${action}-actual-native-private-denial`,
                );
            }
            check(
                errors.snapshot().length === beforeErrors,
                `${actor}-handled-denial-not-hidden-or-buffer-cleared`,
            );
            await capture(
                `selected-${actor}`,
                "[aria-label='Displayed selected evidence']",
            );
            check(
                !document
                    .querySelector("#selected-evaluation")
                    ?.textContent?.includes("SECRET-TIDE-731"),
                `${actor}-render-has-no-private-player-canary`,
            );
        }
        await lens({ kind: "omniscient" });
        await s.close();
        const rejected = await source(true);
        await s.prepare(rejected.identity, rejected.row, "scripted_baseline");
        await s.start();
        await openCurrent();
        await s.readDiagnostics();
        check(
            s.get().diagnostics?.rows.length === 2 &&
                s
                    .get()
                    .diagnostics?.rows.every(
                        (row) =>
                            row.phase !== "committed" &&
                            row.passed &&
                            row.roles_known &&
                            row.roles === 0 &&
                            row.actual_receipt_sha256 === null,
                    ),
            "actual-guard-rejections-no-role-calls-or-receipt",
        );
        await inspect("left", "receipt");
        const guardEvidence = s.get().evidence;
        check(
            guardEvidence?.body.kind === "missing" &&
                guardEvidence.body.reason === "no_accepted_receipt",
            "guard-no-invented-receipt",
        );
        await capture("selected-guard");
        await s.close();

        const lost = await source();
        await s.prepare(lost.identity, lost.row, "scripted_baseline");
        const lostClient = s.get().clientId,
            originalToken = s.get().status?.plan_token;
        check(
            errors.snapshot().length === 0,
            "no-unexpected-errors-before-deliberate-lost-start-ack",
        );
        await fault("lose-start-ack");
        await s.start();
        check(
            s.get().uncertain && s.get().clientId === lostClient,
            "lost-start-ack-retains-original-client-not-fake-completion",
        );
        await capture("selected-unknown");
        await s.status();
        check(
            !s.get().uncertain &&
                s.get().clientId === lostClient &&
                s.get().status?.phase === "completed",
            "explicit-same-client-status-recovers-existing-attempt",
        );
        const lostRun = await openCurrent();
        savedRuns.push(lostRun);
        const beforeDuplicate = JSON.stringify(s.get().summary);
        const duplicate = (await invoke("evaluation_selected", {
            action: "start",
            request: JSON.stringify({
                clientId: lostClient,
                planToken: originalToken,
            }),
        })) as { run_id?: string };
        check(
            duplicate.run_id === lostRun,
            "exact-native-start-retry-reuses-admitted-durable-run",
        );
        await s.loadSummary();
        check(
            JSON.stringify(s.get().summary) === beforeDuplicate,
            "duplicate-start-preserves-both-canonical-heads-and-binding",
        );
        await capture("selected-recovered");
        await s.close();

        const beforeConsentRuns = await ids();
        const pendingSource = await source();
        await fault("hold-consent");
        consentHeld = true;
        const pending = s.prepare(
            pendingSource.identity,
            pendingSource.row,
            "scripted_baseline",
        );
        await until(
            () => s.get().status?.running === true,
            "actual-consent-pending-status",
        );
        const consentClient = s.get().clientId,
            consentOp = s.get().status?.operation_id;
        await capture("selected-consent-pending");
        await lens({ kind: "character", id: "mira" });
        check(
            s.get().clientId === consentClient &&
                s.get().status?.operation_id === consentOp &&
                s.get().status?.running,
            "pending-consent-lens-switch-preserves-execution-client-and-op",
        );
        check(
            s.get().evidence === null && s.get().diagnostics === null,
            "pending-consent-actor-has-no-old-omni-body",
        );
        await capture("selected-consent-actor");
        const cancelling = s.cancel();
        await until(
            () => s.get().status?.phase === "cancelling",
            "native-cancel-ack-before-consent-release",
        );
        await fault("release-consent");
        consentHeld = false;
        await Promise.all([pending, cancelling]);
        check(
            !s.get().status?.running &&
                s.get().status?.phase !== "prepared" &&
                s.get().status?.run_id === null,
            "cancelled-consent-never-executes-or-admits-run",
        );
        await capture("selected-consent-cancelled");
        await s.close();
        await lens({ kind: "omniscient" });
        const deniedSource = await source();
        await fault("deny-consent");
        await s.prepare(
            deniedSource.identity,
            deniedSource.row,
            "scripted_baseline",
        );
        check(
            s.get().status?.error === "Cancelled" &&
                s.get().status?.run_id === null &&
                !s.get().status?.running,
            "explicit-native-consent-denial-no-execution",
        );
        await capture("selected-consent-denied");
        await s.close();
        check(
            JSON.stringify(await ids()) === JSON.stringify(beforeConsentRuns),
            "cancel-and-deny-create-no-durable-selected-run",
        );

        const retiringSource = await source();
        await fault("hold-consent");
        consentHeld = true;
        const retiring = s.prepare(
            retiringSource.identity,
            retiringSource.row,
            "scripted_baseline",
        );
        await until(
            () => s.get().status?.running === true,
            "context-retirement-consent-pending",
        );
        c.returnToPlay();
        check(
            s.get().clientId === null &&
                s.get().summary === null &&
                s.get().evidence === null &&
                s.get().diagnostics === null,
            "actual-main-context-retirement-synchronously-clears-private-state",
        );
        await fault("release-consent");
        consentHeld = false;
        await retiring;
        await until(
            () => !s.get().busy && !s.get().uncertain,
            "captured-old-client-drained-after-context-retirement",
        );
        c.requestLab();
        c.acknowledgeLab(true);
        await until(
            () => s.get().allowed && r.get().allowed,
            "lab-reentered-after-retired-client",
        );
        check(
            s.get().status === null &&
                s.get().evidence === null &&
                s.get().diagnostics === null,
            "late-consent-cannot-publish-into-new-context",
        );
        await capture("selected-context-retired");
        await r.close();
        await s.cleanupStatus();
        check(
            s.get().cleanup?.cleanup_required === false &&
                s.get().cleanup?.running === false,
            "actual-no-retained-native-cleanup-after-scripted-journeys",
        );
        const final = (await fixture("prepare")) as {
            fixture_inventory: Record<string, string>;
        };
        finalInventory = final.fixture_inventory;
        check(
            JSON.stringify(finalInventory) === JSON.stringify(sourceInventory),
            "all-real-source-files-byte-identical-after-selected-actions",
        );
        await c.refresh();
        check(
            structural(c.get().play ?? c.get().playV2) === gameplayBefore,
            "live-gameplay-canonical-state-unchanged",
        );
        const recorded = errors.snapshot();
        check(
            recorded.length === 1 &&
                recorded[0].source === "native" &&
                recorded[0].category === "Transport",
            "only-deliberate-lost-start-ack-error-recorded",
        );
        await capture("selected-finished", "#selected-evaluation", true);
        disposalStarted = true;
        await dispose();
        check(
            errors.snapshot().length === 1,
            "disposal-adds-no-unexpected-errors",
        );
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                stage: config.stage,
                checks,
                errors: errors.snapshot(),
                savedRuns,
                sourceInventory,
                finalSourceInventory: finalInventory,
                realModelGeneration: false,
                desktopInput: false,
                rendering: "native-webview2",
                nativeDialogsAutomated: false,
                unavailable: [
                    "approved_native_inference_not_exercised",
                    "quality_not_reviewed",
                    "provider_inflight_or_OS_kill_not_exercised",
                ],
            },
        });
    } catch {
        try {
            if (consentHeld) {
                await fault("release-consent");
                consentHeld = false;
            }
            if (!disposalStarted) {
                disposalStarted = true;
                await dispose();
            }
        } catch {
            failureCategory ??= "HarnessCleanupUnconfirmed";
        }
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                stage: config.stage,
                failedCheck,
                failureCategory,
                checks,
                errors: errors.snapshot(),
                selectedError: s.get().error,
                phase: s.get().status?.phase,
                realModelGeneration: false,
                desktopInput: false,
                sourceInventory,
                finalSourceInventory: finalInventory,
            },
        });
    }
}
