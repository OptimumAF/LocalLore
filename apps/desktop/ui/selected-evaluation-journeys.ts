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
    SelectedPrepared,
    SelectedSummary,
    SelectedDiagnostics,
} from "./selected-evaluation-model";
import type { ViewV2 } from "./v2-view-model";
import { structural, type ErrorBuffer } from "./model";
import { sameReaderObserver, type ReaderSource, type Json } from "./comparison-reader-model";

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
    let sourceProtocol: 2 | 3 = 2,
        selectedVersion: 1 | 2 = 1,
        constructionIdentity: string | null = null,
        reopenedRun: string | null = null;
    const check = (condition: unknown, name: string) => {
        failedCheck = name;
        if (!condition) throw Error(name);
        checks.push(name);
    };
    const checkVersion = (
        metadata:
            | SelectedPrepared
            | SelectedSummary
            | SelectedDiagnostics
            | null
            | undefined,
        name: string,
    ) => {
        check(
            metadata?.version === selectedVersion,
            `${name}-selected-version`,
        );
        if (metadata?.version === 2)
            check(
                metadata.source_protocol_version === 3 &&
                    structural(metadata.constructions) === constructionIdentity,
                `${name}-source3-exact-constructions`,
            );
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
            | "lose-start-ack"
            | "consent-status",
    ) => invoke("harness_selected_case", { scenario });
    const heldConsent = async (name: string) => {
        failedCheck = name;
        const deadline = Date.now() + 60_000;
        while (Date.now() < deadline) {
            const state = (await fault("consent-status")) as {
                version?: number;
                kind?: string;
                synthetic?: boolean;
                active?: boolean;
                held?: boolean;
            };
            if (
                state.version !== 1 ||
                state.kind !== "selected_fixture" ||
                state.synthetic !== true ||
                typeof state.active !== "boolean" ||
                typeof state.held !== "boolean"
            )
                throw Error("SelectedConsentObservationInvalid");
            if (state.active && state.held) {
                check(true, name);
                return;
            }
            await new Promise((resolve) => setTimeout(resolve, 10));
        }
        throw Error("SelectedConsentEntryTimeout");
    };
    const lens = async (observer: ObserverV2) => {
        r.setObserver(observer); // same normal panel prop route, not a fake controller context
        await until(
            () => sameReaderObserver(s.get().observer, observer),
            "selected-prop-observer-effect",
        );
    };
    const source = async (
        guard = false,
        forResume = false,
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
        check(
            current.source?.protocol_version === sourceProtocol,
            "actual-native-source-protocol",
        );
        if (sourceProtocol === 3) {
            check(
                current.summary?.report.version === 3,
                "actual-typed-literal-source-report",
            );
            if (current.summary?.report.version !== 3)
                throw Error("LiteralSourceRequired");
            const identity = structural(current.summary.report.arms);
            check(
                constructionIdentity === null ||
                    identity === constructionIdentity,
                "source-constructions-stable",
            );
            constructionIdentity = identity;
        }
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
        await until(
            () =>
                [
                    ...document.querySelectorAll<HTMLButtonElement>(
                        "#selected-evaluation button",
                    ),
                ].some(
                    (button) =>
                        button.textContent?.trim() ===
                            (forResume
                                ? "Resume / verify with linked source"
                                : "Prepare selected case") && !button.disabled,
                ),
            "actual-app-source-prop-enables-selected-control",
        );
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
        const target =
            panel?.querySelector(selector) ?? document.querySelector(selector);
        check(target, `${label}-capture-target-present`);
        target?.scrollIntoView({ block: "start" });
        const timerStarted = performance.now();
        await new Promise((resolve) => setTimeout(resolve, 150));
        const testTimerObservedMs = Math.round(
            performance.now() - timerStarted,
        );
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
                testTimerRequestedMs: 150,
                testTimerObservedMs,
                horizontalOverflow: overflow,
                nestedOverflow: nested,
                captureTarget: {
                    selector,
                    top: target?.getBoundingClientRect().top,
                    bottom: target?.getBoundingClientRect().bottom,
                },
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
        checkVersion(s.get().summary, "opened-summary");
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
            protocol_version: number;
            paired_rows: number;
            rollout_rows: number;
            models_executed: boolean;
            fixture_inventory: Record<string, string>;
        };
        if (preparedFixtures.protocol_version === 4) {
            await selectedSceneJourneys(
                { controller: c, comparison: r, selected: s, errors, invoke, dispose, config },
                preparedFixtures,
                gameplayBefore,
            );
            return;
        }
        check(
            preparedFixtures.protocol_version === 2 ||
                preparedFixtures.protocol_version === 3,
            "closed-fixture-protocol",
        );
        sourceProtocol = preparedFixtures.protocol_version as 2 | 3;
        selectedVersion = sourceProtocol === 3 ? 2 : 1;
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
            checkVersion(s.get().summary, "cold-reopened-summary");
            reopenedRun = prior.run_id;
            check(
                s.get().summary?.selection.turn === accepted.row.turn,
                "cold-process-reopens-exact-saved-turn",
            );
            await capture("selected-restarted");
            await s.close();
        }
        await s.prepare(accepted.identity, accepted.row, "scripted_baseline");
        checkVersion(s.get().status?.prepared, "prepared-original-case");
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
        await capture(
            "selected-summary",
            "[aria-label='Selected experiment summary']",
        );
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
        const beforeResume = structural(s.get().summary),
            oldReadToken = s.get().status?.run_token,
            resumeRun = s.get().status?.run_id;
        const linked = await source(false, true);
        await s.resume(linked.identity);
        await s.loadSummary();
        checkVersion(s.get().summary, "explicit-completed-resume");
        check(
            s.get().status?.phase === "completed" &&
                s.get().status?.run_id === resumeRun &&
                s.get().status?.run_token !== oldReadToken &&
                structural(s.get().summary) === beforeResume,
            "explicit-fresh-source-resume-preserves-heads-and-read-binding",
        );
        await capture(
            "selected-resumed",
            "[aria-label='Selected experiment summary']",
        );
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
        checkVersion(s.get().diagnostics, "committed-diagnostics");
        if (selectedVersion === 2) {
            const diagnostics = s.get().diagnostics;
            check(
                diagnostics?.version === 2 &&
                    diagnostics.rows.every(
                        (row) =>
                            row.construction_matches &&
                            row.fallback === false &&
                            row.construction_evidence_status ===
                                (row.arm === "left"
                                    ? "validated_literal"
                                    : "validated_relevant") &&
                            (row.arm === "left"
                                ? row.literal_source_units !== null &&
                                  row.literal_selected_units !== null
                                : row.literal_source_units === null),
                    ),
                "actual-recorded-literal-relevant-construction-proof",
            );
        }
        await capture(
            "selected-constructions",
            "[aria-label='Selected expected and actual results']",
        );
        await invoke("harness_viewport", { preset: "capture-narrow" });
        await capture(
            "selected-constructions-narrow",
            "[aria-label='Selected expected and actual results']",
        );
        if (selectedVersion === 2)
            await capture(
                "selected-literal-proof-narrow",
                "[aria-label='Selected expected and actual results'] > .comparison-selected:first-of-type dt:nth-of-type(9)",
            );
        await invoke("harness_viewport", { preset: "wide" });
        if (selectedVersion === 2) {
            await capture(
                "selected-relevant-construction",
                "[aria-label='Selected expected and actual results'] > .comparison-selected:last-of-type",
            );
            await inspect("left", "capture");
            check(
                s.get().diagnostics === null &&
                    s.get().evidence?.body.kind === "capture",
                "literal-capture-replaces-diagnostics",
            );
            await capture(
                "selected-literal-capture",
                "[aria-label='Displayed selected evidence']",
            );
        }
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
        checkVersion(s.get().diagnostics, "guard-diagnostics");
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
        if (selectedVersion === 2) {
            const diagnostics = s.get().diagnostics;
            check(
                diagnostics?.version === 2 &&
                    diagnostics.rows.every(
                        (row) =>
                            row.construction_evidence_status ===
                                "not_applicable_guard" &&
                            row.literal_source_units === null &&
                            row.literal_selected_units === null &&
                            row.fallback === null,
                    ),
                "guard-construction-and-privacy-honestly-not-applicable",
            );
            await capture(
                "selected-guard-results",
                "[aria-label='Selected expected and actual results']",
            );
            check(
                document
                    .querySelector("#selected-evaluation")
                    ?.textContent?.includes("Not applicable · engine guard"),
                "guard-visible-not-applicable-label",
            );
        }
        await inspect("left", "receipt");
        const guardEvidence = s.get().evidence;
        check(
            guardEvidence?.body.kind === "missing" &&
                guardEvidence.body.reason === "no_accepted_receipt",
            "guard-no-invented-receipt",
        );
        await capture(
            "selected-guard",
            "[aria-label='Displayed selected evidence']",
        );
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
        await heldConsent("native-consent-callback-actually-entered-and-held");
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
        await heldConsent(
            "native-context-retirement-consent-actually-entered-and-held",
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
                reopenedRun,
                sourceProtocol,
                selectedVersion,
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

type SceneFreezeRef = {
    version: 1;
    kind: "selected_scene_source_freeze_ref_v1";
    sha256: string;
    source_protocol_version: 4;
    file_count: number;
    entry_count: number;
    total_bytes: number;
};
type SceneLinkedSource = {
    identity: SelectedSourceIdentity;
    row: RowId;
    source: ReaderSource;
    requests: Partial<Record<SelectedArm, Json>>;
};

// This branch is selected only by the actual native prepare protocol. It does
// not change legacy selected1/literal2 journeys or turn a UI flag into authority.
async function selectedSceneJourneys(
    { controller: c, comparison: r, selected: s, errors, invoke, dispose, config }: Parameters<typeof selectedEvaluationJourneys>[0],
    initialProof: unknown,
    gameplayBefore: string,
): Promise<void> {
    const checks: string[] = [];
    const savedRuns: string[] = [];
    const reopenedIDs: string[] = [];
    const runRoles: { paired: string | null; rollout: string | null; guard: string | null } = { paired: null, rollout: null, guard: null };
    let failedCheck = "selected-scene-start";
    let failureCategory: string | null = null;
    let sourceInventory: SceneFreezeRef | null = null;
    let finalSourceInventory: SceneFreezeRef | null = null;
    let constructionIdentity: string | null = null;
    let lastSource: SceneLinkedSource | null = null;
    let reopenedRun: string | null = null;
    let resumedRun: string | null = null;
    let consentHeld = false;
    let disposalStarted = false;
    let failureCaptured = false;
    let nativeCaptures = 0;
    const omni: ObserverV2 = { kind: "omniscient" };
    const check = (value: unknown, name: string) => {
        failedCheck = name;
        if (!value) throw Error(name);
        checks.push(name);
    };
    const until = async (predicate: () => boolean, name: string) => {
        failedCheck = name;
        for (let n = 0; n < 3000; n++) {
            if (predicate()) return;
            await new Promise((resolve) => setTimeout(resolve, 10));
        }
        throw Error("SelectedSceneJourneyTimeout");
    };
    const frames = () => new Promise<void>((resolve,reject) => {
        let settled = false;
        const timer = setTimeout(() => { settled = true; reject(Error("SelectedSceneRenderFramesTimeout")); },5000);
        requestAnimationFrame(() => requestAnimationFrame(() => {
            if (settled) return;
            settled = true; clearTimeout(timer); resolve();
        }));
    });
    const fixture = (scenario: "prepare" | "choose-paired" | "choose-rollout") => invoke("harness_comparison_reader_case", { scenario });
    const fault = (scenario: "hold-consent" | "release-consent" | "deny-consent" | "lose-start-ack" | "consent-status") => invoke("harness_selected_case", { scenario });
    const object = (value: unknown): Record<string, unknown> | null => value !== null && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : null;
    const freezeRef = (value: unknown): SceneFreezeRef => {
        const ref = object(value);
        check(ref && structural(Object.keys(ref).sort()) === structural(["version", "kind", "sha256", "source_protocol_version", "file_count", "entry_count", "total_bytes"].sort()), "scene-fixture-ref-exact-closed-keys");
        if (!ref) throw Error("SceneFreezeReferenceRequired");
        check(ref.version === 1 && ref.kind === "selected_scene_source_freeze_ref_v1" && ref.source_protocol_version === 4 && typeof ref.sha256 === "string" && /^[a-f0-9]{64}$/.test(ref.sha256), "scene-fixture-ref-version-and-raw-digest");
        const validCount = (value: unknown, max: number) => typeof value === "number" && Number.isSafeInteger(value) && value > 0 && value <= max;
        check(validCount(ref.file_count, 2048) && validCount(ref.entry_count, 8192) && validCount(ref.total_bytes, 64 * 1024 * 1024) && (ref.entry_count as number) >= (ref.file_count as number), "scene-fixture-ref-bounded-counts-and-bytes");
        return ref as SceneFreezeRef;
    };
    const proof = (value: unknown): SceneFreezeRef => {
        const reply = object(value);
        check(reply?.synthetic === true && reply.protocol_version === 4 && reply.paired_rows === 24 && reply.rollout_rows === 12 && reply.models_executed === false, "actual-scene4-scripted-fixture-roster");
        const scene = object(reply?.scene_proof);
        for (const [name, rows] of [["paired", 24], ["rollout", 12]] as const) {
            const item = object(scene?.[name]);
            check(item?.rows === rows && item.source_matches === true && item.read_only === true && item.execution_available === false && item.models_executed === false && item.human_reviewed === 0 && item.human_rubric === "not_reviewed" && item.quality_accepted === false, `${name}-actual-source-scene-proof-no-quality-claim`);
        }
        return freezeRef(reply?.fixture_inventory);
    };
    const version = (metadata: SelectedPrepared | SelectedSummary | SelectedDiagnostics | null | undefined, name: string) => {
        check(metadata?.version === 3 && metadata.source_protocol_version === 4 && metadata.lane === "scripted_selected_case" && structural(metadata.constructions) === constructionIdentity, `${name}-exact-selected3-source4-constructions`);
    };
    const lens = async (observer: ObserverV2) => {
        r.setObserver(observer);
        await until(() => sameReaderObserver(s.get().observer, observer), "scene-observer-prop-committed-to-controller");
    };
    const held = async (name: string) => {
        for (let n = 0; n < 3000; n++) {
            const state = object(await fault("consent-status"));
            if (!(state?.version === 1 && state.kind === "selected_fixture" && state.synthetic === true && typeof state.active === "boolean" && typeof state.held === "boolean")) check(false, "scene-closed-consent-status");
            if (state?.active === true && state.held === true) { check(true, name); return; }
            await new Promise((resolve) => setTimeout(resolve, 10));
        }
        failedCheck = name;
        throw Error("SelectedSceneConsentEntryTimeout");
    };
    const source = async (kind: "paired" | "rollout", guard = false, forResume = false): Promise<SceneLinkedSource> => {
        await r.close();
        await fixture(kind === "paired" ? "choose-paired" : "choose-rollout");
        await r.pick();
        await lens(omni);
        await r.loadSummary();
        const current = r.get();
        check(current.status?.phase === "ready" && !!current.clientId && !!current.status.run_token && current.source?.protocol_version === 4 && current.summary?.report.version === 4 && current.summary.report.source_matches === true, `${kind}-actual-source4-native-ready`);
        if (!current.clientId || !current.status?.run_token || current.source?.protocol_version !== 4 || current.summary?.report.version !== 4) throw Error("SceneSourceRequired");
        check(current.summary.report.kind === (kind === "paired" ? "paired_snapshots" : "continuous_rollout"), `${kind}-actual-source-kind`);
        const constructions = structural(current.summary.report.arms);
        check(constructionIdentity === null || constructionIdentity === constructions, "scene-source-constructions-stable");
        constructionIdentity = constructions;
        const clicked: SelectedArm = kind === "rollout" ? "left" : "right";
        const entry = guard
            ? current.source.rows.find((candidate) => !candidate.receipt_available && current.summary?.report.turns.some((turn) => turn.turn === candidate.row.turn && turn.arm === candidate.row.arm && turn.passed && turn.expected.includes("GuardRejected")))
            : current.source.rows.find((candidate) => candidate.row.turn === "courier-05" && candidate.row.arm === clicked && candidate.receipt_available && candidate.capture_available && current.summary?.report.turns.some((turn) => turn.turn === candidate.row.turn && turn.arm === candidate.row.arm && turn.phase === "committed" && turn.passed));
        check(entry, guard ? "scene-actual-guard-row-selected-from-report" : `${kind}-actual-original-index4-row`);
        if (!entry) throw Error("SceneRowRequired");
        const requests: Partial<Record<SelectedArm, Json>> = {};
        if (!guard) {
            for (const arm of ["left", "right"] as const) {
                r.select({ turn: entry.row.turn, arm });
                await r.inspect({ kind: "receipt", observer: omni });
                const evidence = r.get().evidence;
                const receipt = evidence?.body.kind === "receipt" ? object(evidence.body.receipt) : null;
                check(receipt && object(receipt.request), `${kind}-${arm}-actual-source-receipt-request`);
                if (!receipt || !object(receipt.request)) throw Error("SceneSourceReceiptRequired");
                requests[arm] = receipt.request as Json;
            }
        }
        r.select(entry.row);
        await until(() => [...document.querySelectorAll<HTMLButtonElement>("#selected-evaluation button")].some((button) => button.textContent?.trim() === (forResume ? "Resume / verify with linked source" : "Prepare selected case") && !button.disabled), "scene-actual-App-source-prop-enables-action");
        const nativeOption = document.querySelector<HTMLOptionElement>("#selected-evaluation select[aria-label='Selected experiment lane'] option[value='approved_native']");
        check(nativeOption?.disabled === true, "scene-native-option-visibly-unavailable");
        const linked = { identity: { readerClientId: current.clientId, runToken: current.status.run_token, binding: current.source.binding }, row: entry.row, source: current.source, requests };
        lastSource = linked;
        return linked;
    };
    const prepared = (linked: SceneLinkedSource, name: string) => {
        const metadata = s.get().status?.prepared;
        version(metadata, name);
        check(metadata?.version === 3 && metadata.source_binding === linked.identity.binding && metadata.selection.turn === linked.row.turn && metadata.selection.clicked_arm === linked.row.arm && metadata.arms.length === 2, `${name}-original-source-binding-and-row`);
        if (metadata?.version !== 3) throw Error("ScenePreparedRequired");
        if (linked.row.turn === "courier-05") check(metadata.selection.index === 4, `${name}-original-index4`);
        for (const arm of metadata.arms) {
            const original = linked.source.rows.find((row) => row.row.turn === linked.row.turn && row.row.arm === arm.arm);
            check(original && structural(arm.scope) === structural(original.source.scope) && arm.before_head === original.source.before_head && arm.input_semantic_sha256 === original.source.input_semantic_sha256, `${name}-${arm.arm}-actual-original-input-and-head`);
        }
        check(s.get().status?.phase === "prepared" && s.get().status?.run_id === null, `${name}-prepare-separate-from-durable-Start`);
    };
    const inspect = async (arm: SelectedArm, kind: "query" | "receipt" | "capture" | "outputs", edge: "before" | "after" = "after", view: ViewV2 = "history") => {
        if (kind === "query") await s.readEvidence(arm, { kind, edge, view, observer: s.get().observer });
        else await s.readEvidence(arm, { kind, observer: s.get().observer });
        const evidence = s.get().evidence;
        check(evidence?.read_only === true && evidence.generation_grant === false && evidence.row.arm === arm, `scene-${arm}-${kind}-actual-read-only-envelope`);
        return evidence;
    };
    const open = async (id: string) => {
        await s.open(id);
        await s.loadSummary();
        version(s.get().summary, "scene-opened-summary");
        check(s.get().status?.run_id === id && !!s.get().status?.run_token && s.get().summary?.read_only === true && s.get().summary?.execution_available === false, "scene-explicit-native-read-consent");
    };
    const openCurrent = async () => {
        const id = s.get().status?.run_id;
        check(id, "scene-actual-created-run-ID");
        if (!id) throw Error("SceneRunRequired");
        await open(id);
        return id;
    };
    const ids = async () => {
        await s.catalog();
        check(s.get().catalog !== null, "scene-actual-catalog-reply");
        return s.get().catalog?.runs.map((run) => run.run_id).sort() ?? [];
    };
    type Region = "status" | "prepared" | "summary" | "evidence" | "diagnostics";
    const selector = (region: Region) => region === "prepared" ? "[aria-label='Prepared experiment identity']" : region === "summary" ? "[aria-label='Selected experiment summary']" : region === "evidence" ? "[aria-label='Displayed selected evidence']" : region === "diagnostics" ? "[aria-label='Selected expected and actual results']" : "#selected-evaluation";
    const capture = async (label: string, region: Region = "status", failure = false) => {
        if (!failure) failedCheck = `${label}-capture`;
        const panel = document.querySelector<HTMLElement>("#selected-evaluation");
        const getTarget = () => region === "status" ? panel : panel?.querySelector<HTMLElement>(selector(region));
        if (!failure) await until(() => {
            const target = getTarget();
            const context = target?.querySelector<HTMLElement>(".selected-attempt-context[aria-label='Selected attempt context']");
            const state = s.get();
            const observer = state.observer.kind === "character" ? state.observer.id : state.observer.kind;
            return !!panel && panel.dataset.phase === (state.status?.phase ?? "idle") && panel.dataset.observer === observer && !!context && !!context.innerText.trim() && (!state.error || context.innerText.includes(state.error)) && (!state.evidence || region !== "evidence" || !!target?.textContent?.includes(state.evidence.row.turn));
        }, `${label}-actual-mounted-context-state`);
        const target = getTarget();
        const context = target?.querySelector<HTMLElement>(".selected-attempt-context[aria-label='Selected attempt context']");
        const heading = context?.querySelector<HTMLElement>("h2,h3,h4,strong") ?? target?.querySelector<HTMLElement>("h2,h3,h4");
        const displayed = s.get().evidence;
        const controlText = region === "prepared" ? "Start prepared experiment"
            : region === "summary" ? "Read selected scope and heads"
            : region === "diagnostics" ? "Read expected / actual results"
            : region === "evidence" ? displayed?.body.kind === "query" ? "Read observer-filtered state" : displayed?.body.kind === "capture" ? "Read capture" : displayed?.body.kind === "outputs" ? "Read model outputs" : "Read receipt"
            : "Check same request status";
        const control = [...(panel?.querySelectorAll<HTMLButtonElement>("button") ?? [])].find((button) => button.textContent?.trim() === controlText);
        const nodes = [...new Set([heading,context,control].filter((node): node is HTMLElement => !!node))];
        const first = nodes.reduce<HTMLElement | null>((before,node) => !before || node.getBoundingClientRect().top < before.getBoundingClientRect().top ? node : before, null);
        (first ?? target)?.scrollIntoView({ block: "start" });
        await frames();
        const state = s.get();
        const evidence = state.evidence;
        const arm = evidence?.row.arm ?? state.summary?.arms[0]?.arm ?? state.status?.prepared?.arms[0]?.arm ?? lastSource?.row.arm ?? null;
        const identity = evidence ?? state.summary?.arms.find((item) => item.arm === arm) ?? state.status?.prepared?.arms.find((item) => item.arm === arm) ?? null;
        const observer = state.observer.kind === "character" ? state.observer.id : state.observer.kind;
        const contextText = context?.innerText ?? "";
        const geometryFailures: string[] = [];
        const geometryCheck = (value: unknown, name: string) => { if (!value) geometryFailures.push(name); };
        geometryCheck(target && context && heading && control, "actual-product-region-heading-context-and-control-present");
        geometryCheck(contextText.includes(observer), "actual-context-observer");
        geometryCheck(contextText.toLowerCase().includes((state.status?.phase ?? "idle").replaceAll("_", " ")), "actual-context-attempt-phase");
        geometryCheck(/receipt/i.test(contextText), "actual-context-receipt-availability");
        if (state.error) geometryCheck(contextText.includes(state.error), "actual-context-visible-error-code");
        if (identity) {
            geometryCheck(contextText.includes(identity.scope.story) && contextText.includes(identity.scope.branch), "actual-context-story-and-branch");
            geometryCheck(new RegExp(`before(?: head| revision)?\\s*:?\\s*${identity.before_head}\\b`, "i").test(contextText), "actual-context-before-head");
            if ("after_head" in identity && identity.after_head !== null) geometryCheck(new RegExp(`after(?: head| revision)?\\s*:?\\s*${identity.after_head}\\b`, "i").test(contextText), "actual-context-after-head");
        }
        if (evidence) geometryCheck(contextText.includes(evidence.row.turn) && contextText.includes(evidence.row.arm), "actual-context-evidence-row-and-arm");
        const headers = [...document.querySelectorAll<HTMLElement>(".comparison-selection-context,.comparison-report-context")].filter((node) => ["sticky", "fixed"].includes(getComputedStyle(node).position));
        const boxes = nodes.map((node) => {
            const b = node.getBoundingClientRect();
            const positive = [b.x,b.y,b.width,b.height].every(Number.isFinite) && b.width > 0 && b.height > 0;
            const visible = positive && b.left >= -2 && b.top >= -2 && b.right <= innerWidth+2 && b.bottom <= innerHeight+2;
            const hits = [0.05,0.5,0.95].map((fraction) => {
                if (!visible) return false;
                const hit = document.elementFromPoint(b.left + b.width/2, b.top + Math.min(b.height-1, Math.max(1,b.height*fraction)));
                return !!hit && (hit === node || node.contains(hit));
            });
            const covered = headers.some((header) => {
                if (header === node || header.contains(node) || node.contains(header)) return false;
                const h = header.getBoundingClientRect();
                return h.width > 0 && h.height > 0 && b.left < h.right && b.right > h.left && b.top < h.bottom && b.bottom > h.top;
            });
            geometryCheck(visible && hits.every(Boolean) && !covered, "positive-visible-unoccluded-top-middle-bottom");
            return { text: node.innerText.slice(0,4096), rect: {x:b.x,y:b.y,width:b.width,height:b.height,top:b.top,bottom:b.bottom,left:b.left,right:b.right}, positive, visible, hits, covered };
        });
        const pageOverflow = document.documentElement.scrollWidth > innerWidth+2;
        const panelOverflow = !!panel && panel.scrollWidth > panel.clientWidth+2;
        geometryCheck(!pageOverflow && !panelOverflow, "actual-no-page-or-panel-overflow");
        const app = document.querySelector<HTMLElement>(".app");
        const appFont = app ? Number.parseFloat(getComputedStyle(app).fontSize) : null;
        const rootFont = Number.parseFloat(getComputedStyle(document.documentElement).fontSize);
        const snapshot = {
            synthetic: true, semanticVersion: 3, mode: "selected_scene_v4", stage: config.stage,
            uiRevision: (c.get().play ?? c.get().playV2)?.revision ?? 0,
            selectedStory: identity?.scope ?? null, selectedReport: state.status?.run_id ?? null,
            observer: state.observer, revision: evidence?.body.kind === "query" ? evidence.body.page.revision : identity?.before_head ?? null,
            beforeRevision: identity?.before_head ?? null, afterRevision: identity && "after_head" in identity ? identity.after_head : null,
            pendingOperation: state.pending ? {id:state.pending.operationId,client:state.pending.clientId,phase:state.pending.action} : state.uncertain ? {id:null,client:state.clientId,phase:"acknowledgement_unknown"} : null,
            displayedReceipt: evidence?.body.kind === "receipt" ? evidence.body.receipt : null,
            visibleError: state.error,
            liveGameplayContext:{scope:c.selected()?.scope ?? null,revision:(c.get().play ?? c.get().playV2)?.revision ?? null,observer:c.get().observer},
            sourceProtocol: 4, selectedVersion: 3, sourceInventory, finalSourceInventory,
            selectedRow: evidence?.row ?? (state.summary ? {turn:state.summary.selection.turn,arm:state.summary.selection.clicked_arm} : state.status?.prepared ? {turn:state.status.prepared.selection.turn,arm:state.status.prepared.selection.clicked_arm} : null),
            retainedRequestContext: lastSource ? {presentationOnly:true,sourceBinding:lastSource.identity.binding,row:lastSource.row} : null,
            selectedEvaluation: state, checks: [...checks], errors: errors.snapshot(),
            dom: {text:panel?.innerText.slice(0,24576),contextText,region,selector:selector(region),width:innerWidth,height:innerHeight,userAgent:navigator.userAgent,devicePixelRatio,textScale:c.get().textScale,appFont,rootFont,pageOverflow,panelOverflow,geometry:boxes,geometryFailures,controls:[...(target?.querySelectorAll("button,select,summary") ?? [])].map((node) => ({tag:node.tagName,text:node.textContent?.slice(0,256),disabled:(node as HTMLButtonElement).disabled ?? false,value:node instanceof HTMLSelectElement ? node.value : null}))},
        };
        check(new TextEncoder().encode(JSON.stringify(snapshot)).length <= 256*1024, `${label}-bounded-semantic-snapshot`);
        const captured = object(await invoke("harness_checkpoint", {label,snapshot}));
        if (captured?.rendering === "native-webview2") nativeCaptures++;
        if (!failure) {
            check(captured?.rendering === "native-webview2", `${label}-actual-native-CapturePreview`);
            for (const reason of geometryFailures) check(false, `${label}-${reason}`);
            check(true, `${label}-actual-product-context-visible`);
        }
    };
    const result = (role: "accepted" | "guard") => {
        const diagnostics = s.get().diagnostics;
        version(diagnostics, `${role}-diagnostics`);
        check(diagnostics?.version === 3 && diagnostics.rows.length === 2 && diagnostics.physical_setups === 0 && diagnostics.physical_setup_ms === null && diagnostics.human_reviewed === 0 && diagnostics.human_rubric === "not_reviewed" && diagnostics.quality_accepted === false, `${role}-scripted-typed-results-not-model-quality`);
        if (diagnostics?.version !== 3) throw Error("SceneDiagnosticsRequired");
        for (const row of diagnostics.rows) {
            check(row.passed && row.roles_known && row.construction_matches, `${role}-${row.arm}-actual-result-and-construction`);
            if (role === "accepted") check(row.phase === "committed" && row.roles === 2 && row.actual_receipt_sha256 !== null && row.construction_evidence_status === "validated_committed_scene_narrator_v1" && row.privacy_evidence_status === "checked_finite_sentinels" && row.recovered_without_checkpoint === false && row.fallback !== null, `${row.arm}-validated-scene-input-not-prose-quality`);
            else check(row.phase !== "committed" && row.roles === 0 && row.actual_receipt_sha256 === null && row.construction_evidence_status === "not_applicable_guard" && row.privacy_evidence_status === "not_applicable_guard" && row.fallback === null, `${row.arm}-guard-no-model-calls-or-receipt`);
        }
    };
    const resume = async (kind: "paired" | "rollout", expectedId: string) => {
        const before = structural(s.get().summary);
        const token = s.get().status?.run_token;
        const linked = await source(kind, false, true);
        await s.resume(linked.identity);
        await s.loadSummary();
        version(s.get().summary, "scene-completed-resume-summary");
        check(s.get().status?.phase === "completed" && s.get().status?.run_id === expectedId && s.get().status?.run_token !== token && structural(s.get().summary) === before, "scene-explicit-completed-resume-same-ID-and-canonical-heads");
        resumedRun = s.get().status?.run_id ?? null;
    };
    const preserve = async () => {
        finalSourceInventory = proof(await fixture("prepare"));
        check(structural(finalSourceInventory) === structural(sourceInventory), "scene-full-source-freeze-reference-unchanged");
        await c.refresh();
        check(structural(c.get().play ?? c.get().playV2) === gameplayBefore, "scene-live-gameplay-canonical-state-unchanged");
        await s.cleanupStatus();
        check(s.get().cleanup?.cleanup_required === false && s.get().cleanup?.running === false, "scene-no-retained-native-cleanup-owner");
    };
    try {
        sourceInventory = proof(initialProof);
        check(config.stage === "initial" || config.stage === "restart", "scene-closed-stage");
        const initialCatalog = await ids();
        if (config.stage === "restart") {
            check(initialCatalog.length === 3, "restart-exact-isolated-three-saved-IDs");
            savedRuns.push(...initialCatalog);
            const candidates = s.get().catalog?.runs.filter((run) => run.selection.turn === "courier-05" && run.selection.index === 4 && run.selection.clicked_arm === "left" && run.lane === "scripted_baseline") ?? [];
            check(candidates.length === 1, "restart-one-exact-rollout-catalog-tuple-no-guess");
            if (candidates.length !== 1) throw Error("SceneRestartIdentityAmbiguous");
            reopenedRun = candidates[0].run_id;
            // Establish constructions through the actual retained source, never
            // invent them from a mode flag or source-less catalog entry.
            await source("rollout");
            for (const id of initialCatalog.filter((id) => id !== reopenedRun)) {
                await open(id);
                reopenedIDs.push(id);
                await s.close();
            }
            await open(reopenedRun);
            reopenedIDs.push(reopenedRun);
            check(structural([...reopenedIDs].sort()) === structural(initialCatalog), "restart-opens-every-exact-saved-ID-without-new-work");
            check(s.get().summary?.selection.turn === "courier-05" && s.get().summary?.selection.index === 4 && s.get().summary?.selection.clicked_arm === "left", "restart-actual-opened-rollout-selection");
            await s.readDiagnostics();
            result("accepted");
            await capture("selected-scene-restarted", "summary");
            const receipt = await inspect("right", "receipt");
            check(receipt?.body.kind === "receipt", "restart-real-accepted-receipt");
            await capture("selected-scene-restart-receipt", "evidence");
            await lens({kind:"character",id:"mira"});
            const actor = await inspect("right", "query");
            check(actor?.body.kind === "query" && !JSON.stringify(actor).includes("SECRET-TIDE-731"), "restart-actual-observer-filtered-query2");
            await capture("selected-scene-restart-actor", "evidence");
            await lens(omni);
            await resume("rollout", reopenedRun);
            await capture("selected-scene-restart-resumed", "summary");
            check(structural(await ids()) === structural(initialCatalog), "restart-no-new-Start-or-selected-ID");
            await s.close();
            await r.close();
            await preserve();
            check(errors.snapshot().length === 0, "restart-no-native-errors-or-deliberate-ACK-fault");
            await capture("selected-scene-restart-finished");
        } else {
            check(initialCatalog.length === 0, "initial-fresh-isolated-selected-library");
            const accepted = await source("paired");
            await s.prepare(accepted.identity, accepted.row, "scripted_baseline", 4);
            prepared(accepted, "paired-prepared");
            await capture("selected-scene-prepared", "prepared");
            await s.start();
            check(s.get().status?.phase === "completed" && !s.get().status?.running && s.get().status?.run_token === null && s.get().status?.binding === null, "scene-real-Start-completes-without-inspection-grant");
            await capture("selected-scene-completed", "prepared");
            runRoles.paired = await openCurrent();
            await capture("selected-scene-summary", "summary");
            for (const arm of ["left", "right"] as const) {
                const bound = s.get().summary?.arms.find((item) => item.arm === arm);
                check(bound && bound.after_head !== null && bound.after_head > bound.before_head, `${arm}-scene-real-accepted-head-advance`);
                if (!bound) throw Error("SceneArmRequired");
                for (const edge of ["before", "after"] as const) {
                    const evidence = await inspect(arm, "query", edge);
                    check(evidence?.body.kind === "query" && structural(evidence.scope) === structural(bound.scope) && evidence.body.page.revision === (edge === "before" ? bound.before_head : bound.after_head), `${arm}-${edge}-actual-Query2-scope-and-head`);
                }
                await capture(`selected-scene-${arm}-after`, "evidence");
                const diff = await inspect(arm, "query", "after", "turn_diff");
                check(diff?.body.kind === "query" && diff.body.page.view === "turn_diff", `${arm}-scene-actual-turn-diff`);
                const receipt = await inspect(arm, "receipt");
                check(receipt?.body.kind === "receipt" && structural(receipt.body.receipt.request) === structural(accepted.requests[arm]), `${arm}-scene-selected-executes-exact-original-source-request`);
            }
            for (const kind of ["receipt", "capture", "outputs"] as const) {
                const evidence = await inspect("right", kind);
                check(evidence?.body.kind === kind, `scene-actual-selected-${kind}`);
                await capture(`selected-scene-${kind}`, "evidence");
            }
            await s.readDiagnostics();
            result("accepted");
            await capture("selected-scene-constructions", "diagnostics");
            const identity = {client:s.get().clientId,operation:s.get().status?.operation_id,run:s.get().status?.run_id};
            await lens({kind:"player"});
            const knowledge = await inspect("right", "query", "after", "knowledge");
            check(knowledge?.body.kind === "query" && JSON.stringify(knowledge).includes("SECRET-TIDE-731"), "scene-actual-seed-authorized-Player-knowledge-positive");
            for (const actor of ["mira", "sable"] as const) {
                await lens({kind:"character",id:actor});
                check(s.get().evidence === null && s.get().diagnostics === null && s.get().clientId === identity.client && s.get().status?.operation_id === identity.operation && s.get().status?.run_id === identity.run, `${actor}-scene-lens-clears-private-without-execution-change`);
                const evidence = await inspect("right", "query");
                const text = JSON.stringify(evidence);
                check(evidence?.body.kind === "query" && !text.includes("SECRET-TIDE-731") && (actor === "mira" ? text.includes("The pennant I carry has an amber stitch.") : !text.includes("The pennant I carry has an amber stitch.")), `${actor}-scene-actual-Query2-history-isolation`);
                for (const action of ["evidence", "diagnostics"] as const) {
                    let denial = "";
                    const state = s.get();
                    try {
                        await invoke("evaluation_selected", {action,request:JSON.stringify({clientId:state.clientId,runToken:state.status?.run_token,binding:state.status?.binding,...(action === "evidence" ? {arm:"right",request:{kind:"capture",observer:state.observer}} : {observer:state.observer})})});
                    } catch (error) { denial = typeof error === "string" ? error : error instanceof Error ? error.message : "Unknown"; }
                    check(denial === "Forbidden", `${actor}-${action}-scene-actual-native-private-denial`);
                }
                await capture(`selected-scene-${actor}`, "evidence");
                check(!document.querySelector("#selected-evaluation")?.textContent?.includes("SECRET-TIDE-731"), `${actor}-scene-render-no-private-canary`);
            }
            await lens(omni);
            await s.close();
            const guarded = await source("paired", true);
            await s.prepare(guarded.identity, guarded.row, "scripted_baseline", 4);
            prepared(guarded, "guard-prepared");
            await s.start();
            runRoles.guard = await openCurrent();
            const absent = await inspect("left", "receipt");
            check(absent?.body.kind === "missing" && absent.body.reason === "no_accepted_receipt", "scene-guard-no-invented-accepted-receipt");
            await capture("selected-scene-guard", "evidence");
            await s.readDiagnostics();
            result("guard");
            await capture("selected-scene-guard-results", "diagnostics");
            await s.close();

            // Hold continuously across the negative and positive calibration.
            // Native refusal alone is not a universal callback-entry counter.
            await fault("hold-consent");
            consentHeld = true;
            const native = await source("paired");
            const runsBeforeRefusal = await ids();
            await s.prepare(native.identity, native.row, "approved_native", 4);
            const nativeStatus = s.get().status;
            const observation = object(await fault("consent-status"));
            check(nativeStatus?.phase === "failed" && nativeStatus.error === "NativeUnavailable" && nativeStatus.plan_token === null && nativeStatus.run_id === null && !nativeStatus.running && observation?.held === true && observation.active === false, "scene-actual-native-refusal-while-consent-remains-held");
            await capture("selected-scene-native-unavailable");
            check(structural(await ids()) === structural(runsBeforeRefusal), "scene-native-refusal-creates-no-selected-run");
            await s.close();
            const pendingSource = await source("paired");
            const pending = s.prepare(pendingSource.identity, pendingSource.row, "scripted_baseline", 4);
            await until(() => s.get().status?.running === true, "scene-scripted-calibration-pending-status");
            await held("scene-same-held-control-actually-enters-scripted-consent");
            const client = s.get().clientId, operation = s.get().status?.operation_id;
            await capture("selected-scene-consent-pending");
            await lens({kind:"character",id:"mira"});
            check(s.get().clientId === client && s.get().status?.operation_id === operation && s.get().status?.running && s.get().evidence === null && s.get().diagnostics === null, "scene-held-consent-actor-keeps-client-and-operation-no-private-body");
            await capture("selected-scene-consent-actor");
            const cancelling = s.cancel();
            await until(() => s.get().status?.phase === "cancelling", "scene-native-cancel-ACK-before-held-release");
            await fault("release-consent");
            consentHeld = false;
            await Promise.all([pending,cancelling]);
            check(!s.get().status?.running && s.get().status?.phase !== "prepared" && s.get().status?.run_id === null, "scene-consent-cancel-no-plan-or-run");
            await capture("selected-scene-consent-cancelled");
            await s.close();
            await lens(omni);
            const denied = await source("paired");
            await fault("deny-consent");
            await s.prepare(denied.identity, denied.row, "scripted_baseline", 4);
            check(s.get().status?.error === "Cancelled" && s.get().status?.run_id === null && s.get().status?.plan_token === null && !s.get().status?.running, "scene-consent-denial-no-plan-or-run");
            await capture("selected-scene-consent-denied");
            await s.close();
            check(structural(await ids()) === structural(runsBeforeRefusal), "scene-native-refusal-cancel-deny-no-durable-admission");

            const lost = await source("rollout");
            check(lost.row.turn === "courier-05" && lost.row.arm === "left", "scene-rollout-index4-left-unique-public-restart-tuple");
            await s.prepare(lost.identity, lost.row, "scripted_baseline", 4);
            prepared(lost, "rollout-prepared");
            const lostClient = s.get().clientId, planToken = s.get().status?.plan_token;
            check(typeof lostClient === "string" && typeof planToken === "string", "scene-lost-ACK-retains-actual-client-and-original-plan-token");
            check(errors.snapshot().length === 0, "scene-no-errors-before-deliberate-lost-ACK");
            await fault("lose-start-ack");
            await s.start();
            check(s.get().uncertain && s.get().clientId === lostClient, "scene-lost-Start-ACK-keeps-original-client");
            await capture("selected-scene-unknown");
            await s.status();
            check(!s.get().uncertain && s.get().status?.phase === "completed" && s.get().clientId === lostClient, "scene-explicit-same-client-status-recovers-real-attempt");
            const originalStartOperation = s.get().status?.operation_id;
            check(typeof originalStartOperation === "number" && Number.isSafeInteger(originalStartOperation), "scene-recovered-original-Start-operation-ID");
            runRoles.rollout = await openCurrent();
            const beforeRetry = structural(s.get().summary);
            const retried = object(await invoke("evaluation_selected", {action:"start",request:JSON.stringify({clientId:lostClient,planToken})}));
            check(retried?.run_id === runRoles.rollout && retried.operation_id === originalStartOperation, "scene-exact-original-Start-token-reuses-operation-and-durable-run");
            await s.loadSummary();
            check(structural(s.get().summary) === beforeRetry, "scene-duplicate-Start-unchanged-canonical-heads-and-binding");
            for (const arm of ["left","right"] as const) {
                const evidence = await inspect(arm,"receipt");
                check(evidence?.body.kind === "receipt" && structural(evidence.body.receipt.request) === structural(lost.requests[arm]), `${arm}-rollout-exact-original-source-request`);
            }
            await capture("selected-scene-recovered", "evidence");
            await s.close();

            const retiringSource = await source("paired");
            await fault("hold-consent");
            consentHeld = true;
            const retiring = s.prepare(retiringSource.identity, retiringSource.row, "scripted_baseline", 4);
            await held("scene-context-retirement-callback-actually-held");
            c.returnToPlay();
            check(s.get().clientId === null && s.get().status === null && s.get().summary === null && s.get().evidence === null && s.get().diagnostics === null, "scene-actual-Main-retirement-synchronously-clears-private-context");
            await fault("release-consent");
            consentHeld = false;
            await retiring;
            await until(() => !s.get().busy && !s.get().uncertain, "scene-retired-native-client-drained");
            c.requestLab(); c.acknowledgeLab(true);
            await until(() => s.get().allowed && r.get().allowed, "scene-Lab-reentered-after-retirement");
            check(s.get().status === null && s.get().evidence === null && s.get().diagnostics === null, "scene-late-consent-cannot-republish-private-state");
            await capture("selected-scene-context-retired");

            if (!runRoles.paired || !runRoles.rollout || !runRoles.guard) throw Error("SceneRoleRunRequired");
            const all = await ids();
            check(all.length === 3 && structural(all) === structural([runRoles.paired,runRoles.rollout,runRoles.guard].sort()), "scene-exact-three-role-labeled-actual-run-IDs");
            savedRuns.push(...all);
            await open(runRoles.paired);
            await inspect("right","receipt");
            c.layout(c.get().sidebarSize,c.get().inspectorSize,150);
            const enlarged = async () => {
                await until(() => {
                    const app = document.querySelector<HTMLElement>(".app.text-150");
                    if (!app || c.get().textScale !== 150) return false;
                    const appFont = Number.parseFloat(getComputedStyle(app).fontSize), rootFont = Number.parseFloat(getComputedStyle(document.documentElement).fontSize);
                    return appFont > 0 && rootFont > 0 && Number.isFinite(appFont) && Number.isFinite(rootFont) && Math.abs(appFont/rootFont-1.5) <= 0.000001;
                }, "scene-actual-150-percent-state-class-and-computed-font-ratio");
                check(c.get().textScale === 150 && !!document.querySelector(".app.text-150"), "scene-real-150-percent-not-viewport-only");
            };
            await invoke("harness_viewport",{preset:"wide"});
            await enlarged();
            await capture("selected-scene-enlarged-wide","evidence");
            await invoke("harness_viewport",{preset:"capture-narrow"});
            await enlarged();
            await capture("selected-scene-enlarged-narrow","evidence");
            c.layout(c.get().sidebarSize,c.get().inspectorSize,100);
            await until(() => c.get().textScale === 100 && !!document.querySelector(".app.text-100"), "scene-original-100-percent-restored");
            await invoke("harness_viewport",{preset:"wide"});
            await resume("paired",runRoles.paired);
            await capture("selected-scene-resumed","summary");
            await s.close(); await r.close();
            await preserve();
            const recorded = errors.snapshot();
            check(recorded.length === 1 && recorded[0].source === "native" && recorded[0].category === "Transport", "scene-only-deliberate-lost-Start-ACK-buffered-error");
            await capture("selected-scene-finished");
        }
        disposalStarted = true;
        await dispose();
        check(errors.snapshot().length === (config.stage === "restart" ? 0 : 1), "scene-disposal-no-additional-errors");
        check(nativeCaptures === (config.stage === "restart" ? 5 : 25), "scene-exact-success-native-capture-roster-count");
        await invoke("harness_finish", {report:{synthetic:true,passed:true,mode:"selected_scene_v4",stage:config.stage,checks,errors:errors.snapshot(),runRoles,savedRuns,reopenedRun,reopenedIDs,resumedRun,sourceProtocol:4,selectedVersion:3,sourceInventory,finalSourceInventory,realModelGeneration:false,desktopInput:false,rendering:"native-webview2",nativeCaptures,nativeDialogsAutomated:false,unavailable:["approved_native_selected_scene_execution_unavailable","quality_not_reviewed","provider_inflight_between_arm_or_OS_kill_not_exercised","ordinary_shutdown_absent_model_candidate_metadata_probe_not_zero_path_probes","model_observation_not_independent_SDK_load_measurement"]}});
    } catch (error) {
        const originalFailedCheck = failedCheck;
        failureCategory = error instanceof Error ? error.message.slice(0,256) : typeof error === "string" ? error.slice(0,256) : "SelectedSceneJourneyFailed";
        if (!failureCaptured) {
            failureCaptured = true;
            try { await capture("selected-scene-failure","status",true); }
            catch { failureCategory += ":FailureCaptureUnavailable"; }
            finally { failedCheck = originalFailedCheck; }
        }
        try {
            if (consentHeld) { await fault("release-consent"); consentHeld = false; }
            if (!disposalStarted) { disposalStarted = true; await dispose(); }
        } catch { failureCategory += ":CleanupUnconfirmed"; }
        await invoke("harness_finish", {report:{synthetic:true,passed:false,mode:"selected_scene_v4",stage:config.stage,failedCheck,failureCategory,checks,errors:errors.snapshot(),runRoles,savedRuns,reopenedRun,reopenedIDs,resumedRun,sourceProtocol:4,selectedVersion:3,sourceInventory,finalSourceInventory,realModelGeneration:false,desktopInput:false,rendering:nativeCaptures > 0 ? "native-webview2_partial" : "unavailable",nativeCaptures,selectedError:s.get().error,phase:s.get().status?.phase}});
    }
}
