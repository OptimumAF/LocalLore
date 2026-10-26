// SOURCE-ONLY / UNRUN at handoff. Actual application controllers/native IPC;
// fixed synthetic inference, boundary, picker-consent and ACK harness doubles.
import type { Controller } from "./controller";
import type { ComparisonReaderController } from "./comparison-reader-controller";
import type { ComparisonRunController } from "./comparison-run-controller";
import { checkedComparisonRunStatus } from "./comparison-run-model";
import type { EvidenceRequest, ObserverV2 } from "./comparison-reader-model";
import { sameReaderObserver } from "./comparison-reader-model";
import { structural, type ErrorBuffer } from "./model";

export async function comparisonRunJourneys({
    controller: c,
    comparison: r,
    full: f,
    errors,
    invoke,
    dispose,
    config,
}: {
    controller: Controller;
    comparison: ComparisonReaderController;
    full: ComparisonRunController;
    errors: ErrorBuffer;
    invoke: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
    dispose: () => Promise<void>;
    config: { stage: string };
}) {
    const checks: string[] = [],
        captureLabels: string[] = [],
        savedRuns: string[] = [];
    let failedCheck = "full-start",
        failureCategory: string | null = null;
    let boundaryHeld = false,
        disposalStarted = false,
        reopenedRun: string | null = null;
    const inventoryProofs: {
        name: string;
        before: string;
        after: string;
        file_count: number;
        unchanged: boolean;
    }[] = [];
    let finalInventoryDigest: string | null = null,
        finalInventoryCount: number | null = null;
    const check = (condition: unknown, name: string) => {
        failedCheck = name;
        if (!condition) throw Error(name);
        checks.push(name);
    };
    const until = async (
        condition: () => boolean,
        name: string,
        limit = 600_000,
    ) => {
        failedCheck = name;
        const end = Date.now() + limit;
        while (Date.now() < end) {
            if (condition()) return;
            await new Promise((resolve) => setTimeout(resolve, 25));
        }
        throw Error("FullComparisonJourneyTimeout");
    };
    type Scenario =
        | "hold-boundary"
        | "release-boundary"
        | "lose-comparison-start-ack"
        | "deny-comparison-read"
        | "full-comparison-inventory";
    const fixture = (scenario: Scenario) =>
        invoke("harness_evaluation_case", { scenario });
    const hold = async () => {
        await fixture("hold-boundary");
        boundaryHeld = true;
    };
    const release = async () => {
        await fixture("release-boundary");
        boundaryHeld = false;
    };
    // A normal controller stops polling after its own bounded window. One
    // explicit same-client read-only lookup may reconcile that uncertainty;
    // this helper never starts/resumes a new attempt or changes its key.
    const finish = async (work: Promise<void>, name: string) => {
        failedCheck = name;
        await work;
        const identity = f.get().clientId;
        if (f.get().uncertain && identity) await f.lookup();
        check(
            !f.get().uncertain &&
                !f.get().busy &&
                f.get().status?.running === false,
            `${name}-terminal`,
        );
        check(
            f.get().clientId === identity &&
                f.get().error === null &&
                f.get().status?.error === null,
            `${name}-same-client-without-error`,
        );
    };
    const drainRetired = async (
        client: string,
        run: string,
        operation: number,
    ) => {
        // Closing presentation is not positive worker cleanup. Reconcile only
        // this captured identity through existing read-only native operations;
        // never put its old response into a current application controller.
        let status = checkedComparisonRunStatus(
            await invoke("evaluation_comparison_run", {
                action: "lookup",
                query: { clientId: client },
            }),
        );
        const end = Date.now() + 60_000;
        while (status.running && Date.now() < end) {
            await new Promise((resolve) => setTimeout(resolve, 25));
            status = checkedComparisonRunStatus(
                await invoke("evaluation_comparison_run", {
                    action: "status",
                    query: { runToken: status.run_token },
                }),
            );
        }
        check(
            status.client_id === client &&
                status.run_id === run &&
                status.operation_id === operation &&
                status.phase === "closed" &&
                !status.running,
            "captured-retired-native-owner-positively-drained",
        );
        const closed = checkedComparisonRunStatus(
            await invoke("evaluation_comparison_run", {
                action: "close",
                query: { runToken: status.run_token },
            }),
        );
        check(
            closed.client_id === client &&
                closed.run_id === run &&
                closed.run_token === status.run_token &&
                closed.phase === "closed" &&
                !closed.running,
            "retired-recovery-metadata-capability-explicitly-revoked",
        );
    };
    type Inventory = {
        digest: string;
        file_count: number;
        inventory: Record<string, string>;
    };
    const inventory = async (): Promise<Inventory> => {
        check(
            f.get().status?.running !== true && !r.get().busy,
            "inventory-only-quiescent-native-output",
        );
        const raw = (await fixture("full-comparison-inventory")) as Record<
            string,
            unknown
        >;
        const map = raw.inventory;
        check(
            raw.version === 1 &&
                raw.kind === "full_comparison_fixture" &&
                raw.synthetic === true &&
                typeof raw.digest === "string" &&
                /^[0-9a-f]{64}$/.test(raw.digest) &&
                Number.isSafeInteger(raw.file_count) &&
                Number(raw.file_count) >= 0 &&
                map !== null &&
                typeof map === "object" &&
                !Array.isArray(map),
            "native-inventory-envelope",
        );
        const entries = Object.entries(map as Record<string, unknown>);
        check(
            entries.length === raw.file_count &&
                entries.every(
                    ([path, hash]) =>
                        path.length > 0 &&
                        !path.startsWith("/") &&
                        !path.includes("\\") &&
                        !path.includes(":") &&
                        !path.split("/").includes("..") &&
                        typeof hash === "string" &&
                        /^[0-9a-f]{64}$/.test(hash),
                ),
            "native-inventory-relative-synthetic-files",
        );
        return {
            digest: raw.digest as string,
            file_count: Number(raw.file_count),
            inventory: map as Record<string, string>,
        };
    };
    const unchanged = (before: Inventory, after: Inventory, name: string) => {
        const same =
            before.digest === after.digest &&
            before.file_count === after.file_count &&
            structural(before.inventory) === structural(after.inventory);
        inventoryProofs.push({
            name,
            before: before.digest,
            after: after.digest,
            file_count: after.file_count,
            unchanged: same,
        });
        check(same, name);
    };
    const labels = new Set([
        "full-idle",
        "full-running",
        "full-partial",
        "full-completed",
        "full-reader",
        "full-mira",
        "full-sable",
        "full-receipt",
        "full-narrow",
        "full-denied",
        "full-unknown",
        "full-cancelled",
        "full-switched",
        "full-restarted",
        "full-finished",
    ]);
    const capture = async (label: string, selector = "#comparison-run") => {
        check(
            labels.has(label) && !captureLabels.includes(label),
            `${label}-closed-unique-label`,
        );
        // Let normal React subscriptions commit; this observes no fabricated
        // state and does not substitute an application action or native reply.
        await new Promise((resolve) => setTimeout(resolve, 0));
        let panel = document.querySelector<HTMLElement>(selector);
        check(panel, `${label}-actual-app-panel`);
        const targetSelector =
            selector === "#comparison-reader" &&
            !["full-denied"].includes(label)
                ? ["full-receipt", "full-narrow"].includes(label)
                    ? ".comparison-evidence"
                    : ".comparison-selected"
                : selector;
        const target = panel!.matches(targetSelector)
            ? panel!
            : panel!.querySelector<HTMLElement>(targetSelector);
        check(target, `${label}-actual-visible-state-target`);
        target!.scrollIntoView({ block: "start", behavior: "instant" });
        const began = performance.now();
        await new Promise((resolve) => setTimeout(resolve, 150));
        panel = document.querySelector<HTMLElement>(selector);
        check(panel, `${label}-panel-still-mounted`);
        const state = f.get(),
            reader = r.get(),
            play = c.get().play ?? c.get().playV2;
        const current = c.get();
        const observer: ObserverV2 =
            current.view === "play" || current.observer === "player"
                ? { kind: "player" }
                : current.observer === "omniscient"
                  ? { kind: "omniscient" }
                  : { kind: "character", id: current.observer };
        const pageOverflow =
            document.documentElement.scrollWidth > innerWidth + 2;
        const panelOverflow = panel!.scrollWidth > panel!.clientWidth + 2;
        const evidence = reader.evidence;
        const snapshot = {
            synthetic: true,
            semanticVersion: 2,
            uiRevision: play?.revision ?? 0,
            selectedStory: c.selected()?.scope ?? null,
            revision: play?.revision ?? null,
            observer,
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
                  : reader.status?.running
                    ? {
                          id: reader.status.operation_id,
                          client: reader.clientId,
                          phase: reader.status.phase,
                      }
                    : null,
            displayedReceipt:
                evidence?.body.kind === "receipt"
                    ? evidence.body.receipt
                    : null,
            visibleError: state.error ?? reader.error,
            liveGameplayContext: {
                scope: c.selected()?.scope ?? null,
                revision: play?.revision ?? null,
                observer: c.get().observer,
            },
            inspectedStory: evidence?.scope ?? null,
            inspectedObserver: reader.observer,
            inspectedRevision:
                evidence?.body.kind === "query"
                    ? evidence.body.page.revision
                    : evidence?.edge === "before"
                      ? evidence.before_head
                      : evidence?.edge === "after"
                        ? evidence.after_head
                        : null,
            comparisonRun: state,
            comparisonReader: {
                clientId: reader.clientId,
                status: reader.status,
                observer: reader.observer,
                selected: reader.selected,
                querySelection: reader.querySelection,
                busy: reader.busy,
                uncertain: reader.uncertain,
                error: reader.error,
                evidence,
                source: reader.source
                    ? {
                          binding: reader.source.binding,
                          protocol_version: reader.source.protocol_version,
                          rowCount: reader.source.rows.length,
                      }
                    : null,
                summary: reader.summary
                    ? {
                          version: reader.summary.report.version,
                          kind: reader.summary.report.kind,
                          lane: reader.summary.report.lane,
                          completed: reader.summary.report.completed,
                          completed_scenes:
                              reader.summary.report.completed_scenes,
                          human_reviewed: reader.summary.report.human_reviewed,
                          quality_accepted:
                              reader.summary.report.quality_accepted,
                          constructions:
                              reader.summary.report.version === 3
                                  ? reader.summary.report.arms
                                  : null,
                      }
                    : null,
            },
            inventoryProofs,
            checks: [...checks],
            errors: errors.snapshot(),
            semantic: {
                text: panel!.innerText.slice(0, 16384),
                targetText: target!.innerText.slice(0, 12288),
                controls: [...panel!.querySelectorAll("button,select,summary")]
                    .slice(0, 128)
                    .map((node) => ({
                        tag: node.tagName,
                        text: node.textContent?.slice(0, 256),
                        disabled: (node as HTMLButtonElement).disabled ?? false,
                        value:
                            node instanceof HTMLSelectElement
                                ? node.value
                                : null,
                    })),
                width: innerWidth,
                userAgent: navigator.userAgent,
                devicePixelRatio,
                testTimerRequestedMs: 150,
                testTimerObservedMs: performance.now() - began,
                horizontalOverflow: pageOverflow,
                nestedOverflow: panelOverflow,
                captureTarget: {
                    selector,
                    targetSelector,
                    top: target!.getBoundingClientRect().top,
                    bottom: target!.getBoundingClientRect().bottom,
                },
            },
        };
        check(
            new TextEncoder().encode(JSON.stringify(snapshot)).length <=
                256 * 1024,
            `${label}-bounded-semantic`,
        );
        await invoke("harness_checkpoint", { label, snapshot });
        captureLabels.push(label);
        check(
            !pageOverflow && !panelOverflow,
            `${label}-no-horizontal-overflow`,
        );
    };
    const inspectButton = () => {
        const button = [
            ...document.querySelectorAll<HTMLButtonElement>(
                "#comparison-run button",
            ),
        ].find((value) => value.textContent?.includes("Inspect report"));
        check(button && !button.disabled, "actual-app-inspect-button-enabled");
        return button!;
    };
    const managedRead = async (denied = false) => {
        await r.close();
        if (denied) await fixture("deny-comparison-read");
        inspectButton().click(); // Application-owned DOM callback, no OS input.
        await until(
            () =>
                ["ready", "cancelled", "failed"].includes(
                    r.get().status?.phase ?? "",
                ) &&
                !r.get().busy &&
                r.get().status?.running === false,
            denied ? "managed-read-denied-terminal" : "managed-read-terminal",
        );
        if (denied) {
            check(
                r.get().source === null &&
                    r.get().summary === null &&
                    r.get().evidence === null &&
                    r.get().status?.run_token === null &&
                    r.get().status?.phase === "cancelled",
                "native-consent-denial-no-read-capability",
            );
            return;
        }
        check(
            r.get().status?.phase === "ready" &&
                !!r.get().status?.run_token &&
                r.get().source?.protocol_version === 3,
            "managed-native-protocol3-read-capability",
        );
        r.setObserver({ kind: "omniscient" });
        await r.loadSummary();
        const report = r.get().summary?.report;
        check(
            report?.version === 3 &&
                report.source_matches === true &&
                report.completed === true,
            "fresh-actual-producer-full-report",
        );
        check(
            report?.version === 3 &&
                report.arms[0]?.arm === "literal_player_v1" &&
                report.arms[1]?.arm === "relevant_memory_v1",
            "actual-version3-construction-descriptors-not-version2-policies",
        );
        check(
            report?.human_reviewed === 0 && report.quality_accepted === false,
            "no-invented-human-quality-acceptance",
        );
    };
    const read = async (request: EvidenceRequest) => {
        const changed = !sameReaderObserver(r.get().observer, request.observer);
        r.setObserver(request.observer);
        check(
            sameReaderObserver(r.get().observer, request.observer) &&
                (!changed || r.get().evidence === null),
            "read-lens-clears-prior-private-body",
        );
        await r.inspect(request);
        check(
            !r.get().busy &&
                r.get().error === null &&
                r.get().evidence?.body.kind === request.kind,
            `actual-native-${request.kind}-body`,
        );
        check(
            sameReaderObserver(r.get().evidence!.observer, request.observer),
            "evidence-bound-to-actual-observer",
        );
    };
    const readerJourney = async (extended: boolean) => {
        await managedRead();
        const row = r
            .get()
            .source!.rows.find(
                (value) => value.receipt_available && value.row.arm === "right",
            );
        check(row, "actual-accepted-right-source-row");
        r.select(row!.row);
        await capture("full-reader", "#comparison-reader");
        const client = f.get().clientId,
            operation = f.get().status?.operation_id;
        await read({
            kind: "query",
            edge: "before",
            observer: { kind: "player" },
            view: "history",
        });
        const before = r.get().evidence;
        check(
            before?.body.kind === "query" &&
                before.body.page.revision === row!.source.before_head,
            "actual-before-query-head",
        );
        await read({
            kind: "query",
            edge: "after",
            observer: { kind: "player" },
            view: "history",
        });
        check(
            r.get().evidence?.body.kind === "query" &&
                r.get().evidence!.after_head === row!.source.after_head,
            "actual-after-query-head",
        );
        if (extended) {
            const left = r
                .get()
                .source!.rows.find(
                    (value) =>
                        value.row.turn === row!.row.turn &&
                        value.row.arm === "left",
                );
            check(left, "same-original-turn-has-independent-left-source");
            r.select(left!.row);
            for (const edge of ["before", "after"] as const) {
                await read({
                    kind: "query",
                    edge,
                    observer: { kind: "player" },
                    view: "history",
                });
                const evidence = r.get().evidence;
                check(
                    evidence?.body.kind === "query" &&
                        structural(evidence.scope) ===
                            structural(left!.source.scope) &&
                        evidence.body.page.revision ===
                            (edge === "before"
                                ? left!.source.before_head
                                : left!.source.after_head),
                    `actual-left-${edge}-query-keeps-original-arm-scope-and-head`,
                );
            }
            // Changing the lens intentionally cleared summary. Reload it only
            // under explicit Omni, then inspect an actual noncommitted row.
            r.setObserver({ kind: "omniscient" });
            await r.loadSummary();
            const rejected = r
                .get()
                .summary?.report.turns.find(
                    (value) =>
                        value.error !== null && value.phase !== "committed",
                );
            check(
                rejected,
                "actual-full-report-includes-noncommitted-guard-outcome",
            );
            r.select({ turn: rejected!.turn, arm: rejected!.arm });
            await r.inspect({
                kind: "receipt",
                observer: { kind: "omniscient" },
            });
            check(
                r.get().evidence?.body.kind === "missing" &&
                    r.get().error === null,
                "noncommitted-row-reports-missing-receipt-without-fabrication",
            );
            r.select(row!.row);
            for (const id of ["mira", "sable"] as const) {
                await read({
                    kind: "query",
                    edge: "after",
                    observer: { kind: "character", id },
                    view: "history",
                });
                const text = JSON.stringify(r.get().evidence);
                check(
                    !text.includes("SECRET-TIDE-731"),
                    `${id}-no-player-private-secret`,
                );
                check(
                    id === "mira"
                        ? text.includes(
                              "The pennant I carry has an amber stitch.",
                          )
                        : !text.includes(
                              "The pennant I carry has an amber stitch.",
                          ),
                    `${id}-actual-observed-history-isolation`,
                );
                check(
                    f.get().clientId === client &&
                        f.get().status?.operation_id === operation,
                    `${id}-lens-keeps-execution-identity`,
                );
                await capture(
                    id === "mira" ? "full-mira" : "full-sable",
                    "#comparison-reader",
                );
            }
            const nativeStatus = r.get().status!;
            let denied = "";
            try {
                await invoke("evaluation_comparison", {
                    action: "evidence",
                    query: {
                        runToken: nativeStatus.run_token,
                        binding: r.get().source!.binding,
                        turnId: row!.row.turn,
                        arm: row!.row.arm,
                        request: {
                            kind: "capture",
                            observer: { kind: "character", id: "sable" },
                        },
                    },
                });
            } catch (error) {
                denied = String(error);
            }
            check(
                denied === "Forbidden",
                "native-actor-raw-denied-before-presentation",
            );
            check(
                !JSON.stringify(r.get().evidence).includes("SECRET-TIDE-731"),
                "actor-denial-retains-only-filtered-query",
            );
            await read({ kind: "receipt", observer: { kind: "omniscient" } });
            await capture("full-receipt", "#comparison-reader");
            await read({ kind: "capture", observer: { kind: "omniscient" } });
            await read({ kind: "outputs", observer: { kind: "omniscient" } });
            await invoke("harness_viewport", { preset: "capture-narrow" });
            await capture("full-narrow", "#comparison-reader");
            await invoke("harness_viewport", { preset: "wide" });
        } else
            await read({ kind: "receipt", observer: { kind: "omniscient" } });
        r.setObserver({ kind: "player" });
        check(
            r.get().evidence === null && r.get().summary === null,
            "return-player-clears-all-omniscient-body",
        );
        check(
            f.get().clientId === client &&
                f.get().status?.operation_id === operation,
            "all-read-lenses-preserve-run-identity",
        );
    };
    try {
        check(
            config.stage === "initial" || config.stage === "restart",
            "closed-full-comparison-stage",
        );
        await c.start();
        const liveBefore = structural(c.get().play ?? c.get().playV2);
        c.requestLab();
        c.acknowledgeLab(true);
        await until(
            () => f.get().allowed && r.get().allowed,
            "actual-main-lab-native-eligibility",
        );
        await f.loadCatalog();
        check(
            f.get().catalog?.protocol_version === 3 &&
                f.get().catalog?.input_lane === "scripted_baseline",
            "actual-scripted-native-catalog",
        );
        await capture("full-idle");
        if (config.stage === "restart") {
            const paired = f
                .get()
                .catalog!.runs.filter(
                    (run) =>
                        run.comparison_kind === "paired" &&
                        run.initial_batch === 1,
                )
                .sort((a, b) => a.created_ms - b.created_ms)[0];
            check(paired, "cold-catalog-retained-paired-identity");
            const before = await inventory();
            await finish(f.open(paired!.run_id), "cold-open-existing-paired");
            reopenedRun = paired!.run_id;
            check(
                f.get().status?.run_id === reopenedRun &&
                    f.get().status?.completed === true &&
                    f.get().status?.report_ready === true &&
                    f.get().status?.completed_scenes === 4,
                "cold-open-verifies-completed-stored-report",
            );
            await capture("full-restarted");
            await readerJourney(false);
            await r.close();
            await f.close();
            unchanged(
                before,
                await inventory(),
                "cold-open-read-close-no-execution-or-file-mutation",
            );
        } else {
            check(
                f.get().catalog!.runs.length === 0,
                "fresh-owned-workspace-no-existing-full-runs",
            );
            await hold();
            const initial = f.start("paired", 1);
            await until(
                () =>
                    f.get().status?.running === true &&
                    !!f.get().status?.operation_id,
                "paired-actual-running-admission",
            );
            const pairedClient = f.get().clientId,
                firstOperation = f.get().status!.operation_id;
            check(
                pairedClient && f.get().pending !== null,
                "paired-known-client-and-pending-operation",
            );
            await capture("full-running");
            await release();
            await finish(initial, "paired-one-scene");
            const pairedId = f.get().status!.run_id;
            savedRuns.push(pairedId);
            check(
                f.get().status?.completed_scenes === 1 &&
                    f.get().status?.completed === false &&
                    f.get().status?.report_ready === true &&
                    f.get().status?.phase === "paused",
                "paired-partial-report-ready-not-complete",
            );
            await capture("full-partial");
            await r.close();
            await finish(f.resume(3), "explicit-paired-three-scene-resume");
            check(
                f.get().clientId === pairedClient &&
                    f.get().status?.run_id === pairedId &&
                    f.get().status?.operation_id !== firstOperation &&
                    f.get().status?.completed_scenes === 4 &&
                    f.get().status?.completed === true &&
                    f.get().status?.report_ready === true,
                "paired-resume-same-run-four-scenes",
            );
            const beforeRetry = await inventory();
            await finish(f.resume(1), "completed-read-only-resume");
            unchanged(
                beforeRetry,
                await inventory(),
                "completed-resume-entire-output-byte-read-only",
            );
            let stale = "";
            try {
                await invoke("evaluation_comparison_run", {
                    action: "cancel",
                    query: {
                        runToken: f.get().status!.run_token,
                        operationId: firstOperation,
                    },
                });
            } catch (error) {
                stale = String(error);
            }
            check(
                stale === "StaleEvaluationOperation",
                "native-stale-operation-cannot-cancel-new-owner",
            );
            await capture("full-completed");
            const beforeRead = await inventory();
            await readerJourney(true);
            await r.close();
            unchanged(
                beforeRead,
                await inventory(),
                "actual-inspection-does-not-change-durable-comparison",
            );
            await managedRead(true);
            await capture("full-denied", "#comparison-reader");
            await r.close();
            await f.close();
            await finish(f.start("rollout", 4), "separate-four-scene-rollout");
            const rolloutId = f.get().status!.run_id;
            savedRuns.push(rolloutId);
            check(
                rolloutId !== pairedId &&
                    f.get().clientId !== pairedClient &&
                    f.get().status?.comparison_kind === "rollout" &&
                    f.get().status?.completed === true &&
                    f.get().status?.completed_scenes === 4,
                "independent-rollout-client-and-four-scenes",
            );
            await f.close();
            await hold();
            await fixture("lose-comparison-start-ack");
            await f.start("paired", 1);
            const lostClient = f.get().clientId;
            check(
                !!lostClient &&
                    f.get().uncertain &&
                    f.get().error === "EvaluationIo",
                "lost-ack-retains-exact-original-client",
            );
            await capture("full-unknown");
            const recovering = f.lookup();
            await until(
                () => f.get().status?.running === true && !f.get().uncertain,
                "same-client-read-only-lookup-reconciles-ack",
            );
            check(
                f.get().clientId === lostClient,
                "lookup-never-rekeys-or-restarts",
            );
            const lostRun = f.get().status!.run_id;
            await f.cancel();
            await recovering;
            await release();
            check(
                f.get().clientId === lostClient &&
                    f.get().status?.run_id === lostRun &&
                    f.get().status?.completed === false &&
                    f.get().status?.running === false &&
                    f.get().status?.phase === "failed" &&
                    f.get().status?.error === "Cancelled" &&
                    !f.get().status?.report_ready &&
                    !f.get().uncertain,
                "pre-execution-boundary-cancel-keeps-identity-without-invented-report",
            );
            await capture("full-cancelled");
            await f.close();
            // This separately admitted fixed held worker exercises Main's real
            // retirement path; a pre-execution-cancelled run is not resumable.
            await hold();
            const retiring = f.start("paired", 1);
            await until(
                () => f.get().status?.running === true,
                "actual-new-worker-running-before-context-switch",
            );
            const retiringClient = f.get().clientId!,
                retiringRun = f.get().status!.run_id,
                retiringOperation = f.get().status!.operation_id!;
            c.returnToPlay();
            await until(
                () => !f.get().allowed && !r.get().allowed,
                "main-live-context-retirement-observed",
            );
            check(
                f.get().status === null &&
                    r.get().summary === null &&
                    r.get().evidence === null,
                "retirement-synchronously-clears-run-and-private-reads",
            );
            await release();
            await retiring;
            c.requestLab();
            c.acknowledgeLab(true);
            await until(
                () => f.get().allowed && !f.get().busy && !f.get().uncertain,
                "retired-exact-capability-drained-before-reentry",
            );
            await drainRetired(retiringClient, retiringRun, retiringOperation);
            check(
                f.get().status === null && f.get().clientId === null,
                "late-old-reply-cannot-publish-in-new-main-context",
            );
            await capture("full-switched");
            await f.loadCatalog();
            check(
                savedRuns.every((id) =>
                    f.get().catalog?.runs.some((run) => run.run_id === id),
                ),
                "both-completed-run-identities-in-native-catalog",
            );
            check(
                f.get().catalog!.runs.length === 4,
                "lost-ack-and-retirement-each-create-only-one-native-run",
            );
        }
        check(
            structural(c.get().play ?? c.get().playV2) === liveBefore,
            "comparison-never-mutates-selected-live-story",
        );
        await r.close();
        await f.close();
        check(
            r.get().source === null &&
                r.get().summary === null &&
                r.get().evidence === null &&
                (f.get().status === null || f.get().status?.phase === "closed"),
            "explicit-close-clears-all-readable-body",
        );
        const records = errors.snapshot();
        check(
            config.stage === "initial"
                ? records.length === 1 &&
                      records[0].source === "native" &&
                      records[0].category === "Transport"
                : records.length === 0,
            "only-explicit-lost-ack-transport-error-recorded",
        );
        const finalInventory = await inventory();
        finalInventoryDigest = finalInventory.digest;
        finalInventoryCount = finalInventory.file_count;
        await capture("full-finished");
        disposalStarted = true;
        await dispose();
        check(
            errors.snapshot().length === records.length,
            "disposal-adds-no-error-records",
        );
        await invoke("harness_finish", {
            report: {
                version: 1,
                synthetic: true,
                passed: true,
                stage: config.stage,
                checks,
                captureLabels,
                errors: errors.snapshot(),
                savedRuns,
                reopenedRun,
                inventoryProofs,
                finalInventoryDigest,
                finalInventoryCount,
                modelExecution: false,
                nativeIpc: true,
                rendering: "native-webview2",
                desktopInput: false,
                nativeDialogsAutomated: false,
                unavailable: [
                    "approved-native-model-inference",
                    "human-quality-acceptance",
                    "provider-inflight-or-OS-kill-races",
                    "real-OS-picker-interaction",
                ],
            },
        });
    } catch (error) {
        failureCategory =
            error instanceof Error &&
            error.message === "FullComparisonJourneyTimeout"
                ? error.message
                : "FullComparisonJourneyFailed";
        try {
            if (boundaryHeld) await release();
            if (!disposalStarted) {
                disposalStarted = true;
                await dispose();
            }
        } catch {
            failureCategory = "HarnessCleanupUnconfirmed";
        }
        await invoke("harness_finish", {
            report: {
                version: 1,
                synthetic: true,
                passed: false,
                stage: config.stage,
                failedCheck,
                failureCategory,
                checks,
                captureLabels,
                errors: errors.snapshot(),
                savedRuns,
                reopenedRun,
                inventoryProofs,
                finalInventoryDigest,
                finalInventoryCount,
                fullError: f.get().error,
                fullPhase: f.get().status?.phase,
                readerError: r.get().error,
                modelExecution: false,
                nativeIpc: true,
                desktopInput: false,
            },
        });
    }
}
