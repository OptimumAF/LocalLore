// Source-only at handoff. Actual native service/model owners; fixed synthetic
// stories and closed consent/picker/ACK doubles. No desktop input or OS dialogs.
import type { Controller } from "./controller";
import type { ComparisonReaderController } from "./comparison-reader-controller";
import type { ComparisonRunController } from "./comparison-run-controller";
import { checkedNativeComparisonRunStatus } from "./comparison-run-model";
import type { EvidenceRequest, ObserverV2 } from "./comparison-reader-model";
import { sameReaderObserver } from "./comparison-reader-model";
import { structural, type ErrorBuffer } from "./model";

export async function comparisonRunNativeJourneys({
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
    let failedCheck = "native-full-start",
        held = false,
        disposalStarted = false;
    let reopenedRun: string | null = null,
        actualGenerationObserved = false;
    let accountedErrors = 0,
        timeoutRecoveries = 0;
    const errorEvidence: { boundary: string; added: number }[] = [];
    let finalInventoryDigest: string | null = null,
        finalInventoryCount: number | null = null;
    const inventoryProofs: {
        name: string;
        before: string;
        after: string;
        file_count: number;
        unchanged: boolean;
    }[] = [];
    const outcomeSummaries: unknown[] = [];
    const check = (condition: unknown, name: string) => {
        failedCheck = name;
        if (!condition) throw Error(name);
        checks.push(name);
    };
    const until = async (
        condition: () => boolean,
        name: string,
        limit = 60_000,
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
        | "hold-execution-consent"
        | "release-execution-consent"
        | "deny-execution-consent"
        | "deny-read-consent"
        | "lose-start-ack"
        | "consent-status";
    const fixture = (scenario: Scenario) =>
        invoke("harness_native_comparison_case", { scenario });
    const hold = async () => {
        await fixture("hold-execution-consent");
        held = true;
    };
    const release = async () => {
        await fixture("release-execution-consent");
        held = false;
    };
    const fixtureStatus = async (record = true) => {
        const value = (await fixture("consent-status")) as Record<
            string,
            unknown
        >;
        const valid =
            value.version === 1 &&
            value.kind === "native_full_comparison_fixture" &&
            value.synthetic === true &&
            typeof value.active === "boolean" &&
            typeof value.held === "boolean";
        if (!valid) {
            failedCheck = "native-full-closed-fixture-status";
            throw Error(failedCheck);
        }
        if (record) check(valid, "native-full-closed-fixture-status");
        return value;
    };
    const heldConsentEntered = async () => {
        failedCheck = "native-full-actual-held-consent-entered";
        const end = Date.now() + 60_000;
        while (Date.now() < end) {
            const state = await fixtureStatus(false);
            if (state.active === true && state.held === true) {
                check(true, "native-full-actual-held-consent-entered");
                return;
            }
            await new Promise((resolve) => setTimeout(resolve, 25));
        }
        throw Error("FullComparisonJourneyTimeout");
    };
    const cleanup = async () => {
        await f.cleanupStatus();
        const state = f.get();
        check(
            state.mode === "approved_native" &&
                state.cleanup !== null &&
                !state.cleanupPending &&
                !state.cleanupUncertain &&
                state.cleanupError === null &&
                state.cleanup.error === null &&
                !state.cleanup.cleanup_required &&
                !state.cleanup.running,
            "native-full-explicit-cleanup-observed",
        );
    };
    const accountTransport = (boundary: string) => {
        const added = errors.snapshot().slice(accountedErrors);
        check(
            added.length === 1 &&
                added[0].source === "native" &&
                added[0].category === "Transport",
            `${boundary}-one-observed-native-transport`,
        );
        accountedErrors += added.length;
        errorEvidence.push({ boundary, added: added.length });
    };
    const terminal = async (
        work: Promise<void>,
        name: string,
        success = true,
    ) => {
        failedCheck = name;
        await work;
        const client = f.get().clientId;
        // Explicit read-only same-client recovery after the controller's finite
        // polling window. No new start/resume, provider choice or UUID is made.
        for (
            let reads = 0;
            reads < 4 && (f.get().uncertain || f.get().status?.running);
            reads++
        ) {
            check(
                !!client &&
                    f.get().clientId === client &&
                    f.get().uncertain &&
                    f.get().error === "EvaluationIo" &&
                    f.get().status?.running === true,
                `${name}-observed-poll-uncertainty`,
            );
            accountTransport(`${name}-poll-${reads}`);
            timeoutRecoveries++;
            await f.lookup();
            check(f.get().clientId === client, `${name}-retains-client`);
        }
        check(
            !f.get().busy &&
                !f.get().uncertain &&
                f.get().status?.running === false,
            `${name}-terminal`,
        );
        check(
            f.get().clientId === client &&
                f.get().status?.version === 2 &&
                f.get().status?.input_lane === "approved_native",
            `${name}-native-v2-identity`,
        );
        if (success)
            check(
                f.get().error === null && f.get().status?.error === null,
                `${name}-no-service-error`,
            );
    };
    const close = async () => {
        await r.close();
        await f.close();
        await until(
            () => !f.get().busy && !f.get().uncertain,
            "native-full-close-identity-settled",
        );
        await cleanup();
    };
    const drainRetired = async (
        client: string,
        run: string,
        operation: number,
    ) => {
        let value = checkedNativeComparisonRunStatus(
            await invoke("evaluation_comparison_native", {
                action: "lookup",
                query: { clientId: client },
            }),
        );
        const end = Date.now() + 60_000;
        while (value.running && Date.now() < end) {
            await new Promise((resolve) => setTimeout(resolve, 25));
            value = checkedNativeComparisonRunStatus(
                await invoke("evaluation_comparison_native", {
                    action: "status",
                    query: { runToken: value.run_token },
                }),
            );
        }
        check(
            value.client_id === client &&
                value.run_id === run &&
                value.operation_id === operation &&
                value.phase === "closed" &&
                !value.running,
            "native-full-retired-exact-owner-drained",
        );
        const revoked = checkedNativeComparisonRunStatus(
            await invoke("evaluation_comparison_native", {
                action: "close",
                query: { runToken: value.run_token },
            }),
        );
        check(
            revoked.client_id === client &&
                revoked.run_id === run &&
                revoked.phase === "closed" &&
                !revoked.running,
            "native-full-retired-capability-revoked",
        );
        await cleanup();
    };
    type Inventory = {
        digest: string;
        file_count: number;
        inventory: Record<string, string>;
    };
    const inventory = async (): Promise<Inventory> => {
        check(
            f.get().status?.running !== true && !r.get().busy,
            "native-full-inventory-quiescent",
        );
        const raw = (await invoke("harness_evaluation_case", {
            scenario: "full-comparison-inventory",
        })) as Record<string, unknown>;
        check(
            raw.version === 1 &&
                raw.kind === "full_comparison_fixture" &&
                raw.synthetic === true &&
                typeof raw.digest === "string" &&
                /^[0-9a-f]{64}$/.test(raw.digest) &&
                Number.isSafeInteger(raw.file_count) &&
                Number(raw.file_count) >= 0 &&
                raw.inventory !== null &&
                typeof raw.inventory === "object" &&
                !Array.isArray(raw.inventory),
            "native-full-inventory-envelope",
        );
        const entries = Object.entries(
            raw.inventory as Record<string, unknown>,
        );
        check(
            entries.length === raw.file_count &&
                entries.every(
                    ([key, value]) =>
                        key.length > 0 &&
                        !key.startsWith("/") &&
                        !key.includes("\\") &&
                        !key.includes(":") &&
                        !key.split("/").includes("..") &&
                        typeof value === "string" &&
                        /^[0-9a-f]{64}$/.test(value),
                ),
            "native-full-inventory-bounded-relative-files",
        );
        return {
            digest: raw.digest as string,
            file_count: Number(raw.file_count),
            inventory: raw.inventory as Record<string, string>,
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
    const capture = async (
        label: string,
        selector = "#comparison-run-native",
    ) => {
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
        const savedSelect = panel!.querySelector<HTMLSelectElement>(
            ".comparison-saved-run select",
        );
        if (savedSelect && savedSelect.value === "") {
            const style = getComputedStyle(savedSelect);
            const context = document.createElement("canvas").getContext("2d");
            check(context, `${label}-placeholder-font-measurement`);
            context!.font = style.font;
            const textWidth = context!.measureText(
                savedSelect.selectedOptions[0]?.text ?? "",
            ).width;
            check(
                savedSelect.clientWidth >=
                    textWidth +
                        parseFloat(style.paddingLeft) +
                        parseFloat(style.paddingRight) +
                        24,
                `${label}-saved-placeholder-fits-control`,
            );
        }
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
            nativeCleanup:
                state.mode === "approved_native" ? state.cleanup : null,
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
                        selectedText:
                            node instanceof HTMLSelectElement
                                ? (node.selectedOptions[0]?.text ?? null)
                                : null,
                        width: node.getBoundingClientRect().width,
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
                "#comparison-run-native button",
            ),
        ].find((value) => value.textContent?.includes("Inspect report"));
        check(
            button && !button.disabled,
            "native-full-actual-App-inspect-enabled",
        );
        return button!;
    };
    const managedRead = async (completed: boolean, denied = false) => {
        await r.close();
        if (denied) await fixture("deny-read-consent");
        inspectButton().click(); // Same application DOM callback as the UI.
        await until(
            () =>
                ["ready", "cancelled", "failed"].includes(
                    r.get().status?.phase ?? "",
                ) &&
                !r.get().busy &&
                r.get().status?.running === false,
            "native-full-managed-read-terminal",
            120_000,
        );
        if (denied) {
            check(
                r.get().source === null &&
                    r.get().summary === null &&
                    r.get().evidence === null &&
                    r.get().status?.run_token === null &&
                    r.get().status?.phase === "cancelled",
                "native-full-independent-read-consent-denied",
            );
            return;
        }
        check(
            r.get().status?.phase === "ready" &&
                !!r.get().status?.run_token &&
                r.get().source?.protocol_version === 3,
            "native-full-managed-protocol3-reader",
        );
        r.setObserver({ kind: "omniscient" });
        await r.loadSummary();
        const report = r.get().summary?.report;
        check(
            report?.version === 3 &&
                report.kind === "paired_snapshots" &&
                report.source_matches === true &&
                report.completed === completed &&
                report.completed_scenes === (completed ? 4 : 1) &&
                report.turns.length === (completed ? 48 : 12),
            completed
                ? "native-full-actual-completed-proof"
                : "native-full-actual-paired-partial",
        );
        check(
            report?.version === 3 &&
                report.arms[0]?.arm === "literal_player_v1" &&
                report.arms[1]?.arm === "relevant_memory_v1",
            "native-full-actual-construction-descriptors",
        );
        check(
            report?.human_reviewed === 0 && report.quality_accepted === false,
            "native-full-no-invented-quality-acceptance",
        );
        check(
            !!report &&
                report.physical_setups > 0 &&
                report.native_load !== null,
            "native-full-actual-native-load-evidence",
        );
        if (report) {
            const roles = report.turns.reduce(
                (sum, row) => sum + (row.roles_known ? row.roles : 0),
                0,
            );
            if (config.stage === "initial")
                actualGenerationObserved ||= roles > 0;
            outcomeSummaries.push({
                completed: report.completed,
                completed_scenes: report.completed_scenes,
                rows: report.turns.length,
                roles_known_sum: roles,
                unknown_role_rows: report.turns.filter(
                    (row) => !row.roles_known,
                ).length,
                physical_setups: report.physical_setups,
                phases: report.turns.reduce<Record<string, number>>(
                    (counts, row) => {
                        counts[row.phase] = (counts[row.phase] ?? 0) + 1;
                        return counts;
                    },
                    {},
                ),
                failures: report.turns.filter((row) => !row.passed).length,
                human_reviewed: report.human_reviewed,
                quality_accepted: report.quality_accepted,
            });
        }
    };
    const read = async (request: EvidenceRequest) => {
        const changed = !sameReaderObserver(r.get().observer, request.observer);
        r.setObserver(request.observer);
        check(
            sameReaderObserver(r.get().observer, request.observer) &&
                (!changed || r.get().evidence === null),
            "native-full-lens-clears-prior-body",
        );
        await r.inspect(request);
        check(
            !r.get().busy &&
                r.get().error === null &&
                r.get().evidence?.body.kind === request.kind,
            `native-full-actual-${request.kind}-evidence`,
        );
        check(
            sameReaderObserver(r.get().evidence!.observer, request.observer),
            "native-full-evidence-observer-bound",
        );
    };
    const readerJourney = async (extended: boolean) => {
        const client = f.get().clientId,
            operation = f.get().status?.operation_id;
        await managedRead(true);
        const row = r
            .get()
            .source!.rows.find(
                (entry) =>
                    entry.receipt_available &&
                    entry.capture_available &&
                    entry.recording_available,
            );
        check(row, "native-full-actual-committed-captured-row");
        r.select(row!.row);
        await read({
            kind: "query",
            edge: "before",
            observer: { kind: "player" },
            view: "history",
        });
        let body = r.get().evidence;
        check(
            body?.body.kind === "query" &&
                body.body.page.head === row!.source.before_head &&
                body.body.page.revision === row!.source.before_head &&
                structural(body.scope) === structural(row!.source.scope),
            "native-full-before-actual-Store-cut",
        );
        await read({
            kind: "query",
            edge: "after",
            observer: { kind: "player" },
            view: "history",
        });
        body = r.get().evidence;
        check(
            body?.body.kind === "query" &&
                body.body.page.head === row!.source.after_head &&
                body.body.page.revision === row!.source.after_head,
            "native-full-after-actual-Store-cut",
        );
        await capture("full-reader", "#comparison-reader");
        if (extended) {
            const knowledgeRow = r
                .get()
                .source!.rows.find(
                    (entry) =>
                        entry.row.turn === "courier-01" &&
                        entry.row.arm === "left",
                );
            check(
                knowledgeRow,
                "native-full-original-player-only-knowledge-cut",
            );
            r.select(knowledgeRow!.row);
            await read({
                kind: "query",
                edge: "before",
                observer: { kind: "player" },
                view: "knowledge",
            });
            const playerKnowledge = r.get().evidence;
            check(
                playerKnowledge?.body.kind === "query" &&
                    playerKnowledge.body.page.head ===
                        knowledgeRow!.source.before_head &&
                    structural(playerKnowledge.scope) ===
                        structural(knowledgeRow!.source.scope) &&
                    JSON.stringify(playerKnowledge.body.page).includes(
                        "SECRET-TIDE-731",
                    ),
                "native-full-player-positive-private-knowledge-canary",
            );
            for (const id of ["mira", "sable"] as const) {
                r.select(row!.row);
                await read({
                    kind: "query",
                    edge: "after",
                    observer: { kind: "character", id },
                    view: "history",
                });
                r.select(knowledgeRow!.row);
                await read({
                    kind: "query",
                    edge: "before",
                    observer: { kind: "character", id },
                    view: "knowledge",
                });
                check(
                    !JSON.stringify(r.get().evidence).includes(
                        "SECRET-TIDE-731",
                    ),
                    `native-full-${id}-no-player-private-secret`,
                );
                // Actual model outcomes may reject Say. Record the actual
                // observer-filtered page, not an assumed utterance or quality.
                check(
                    f.get().clientId === client &&
                        f.get().status?.operation_id === operation,
                    `native-full-${id}-lens-does-not-rekey-generation`,
                );
                await capture(
                    id === "mira" ? "full-mira" : "full-sable",
                    "#comparison-reader",
                );
            }
            r.select(row!.row);
            const nativeStatus = r.get().status!;
            for (const kind of ["receipt", "capture", "outputs"] as const) {
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
                                kind,
                                observer: { kind: "character", id: "sable" },
                            },
                        },
                    });
                } catch (error) {
                    denied = String(error);
                }
                check(
                    denied === "Forbidden",
                    `native-full-actor-${kind}-refused`,
                );
            }
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
            "native-full-return-player-clears-private-body",
        );
        check(
            f.get().clientId === client &&
                f.get().status?.operation_id === operation,
            "native-full-reader-keeps-execution-identity",
        );
    };
    const report = (passed: boolean, failureCategory?: string) => ({
        version: 1,
        synthetic: true,
        passed,
        stage: config.stage,
        checks,
        captureLabels,
        errors: errors.snapshot(),
        errorEvidence,
        timeoutRecoveries,
        savedRuns,
        reopenedRun,
        inventoryProofs,
        finalInventoryDigest,
        finalInventoryCount,
        outcomeSummaries,
        modelExecution: actualGenerationObserved,
        nativeIpc: true,
        rendering: "native-webview2",
        desktopInput: false,
        nativeDialogsAutomated: false,
        doubles: [
            "execution-consent",
            "read-consent",
            "model-picker",
            "lost-start-ack",
        ],
        unavailable: [
            "human-quality-acceptance",
            "real-OS-dialog-interaction",
            "physical-phone-qualification",
            "whole-process-resource-qualification",
            "independent-no-asset-call-counter-on-restart",
            "presentation-poll-deadline-is-not-native-execution-budget",
        ],
        ...(!passed
            ? {
                  failedCheck,
                  failureCategory,
                  fullError: f.get().error,
                  fullPhase: f.get().status?.phase,
                  readerError: r.get().error,
              }
            : {}),
    });
    try {
        check(
            config.stage === "initial" || config.stage === "restart",
            "native-full-closed-stage",
        );
        check(
            f.mode === "approved_native",
            "native-full-stable-native-controller",
        );
        await fixtureStatus();
        await c.start();
        const liveBefore = structural(c.get().play ?? c.get().playV2);
        c.requestLab();
        c.acknowledgeLab(true);
        await until(
            () => f.get().allowed && r.get().allowed,
            "native-full-actual-lab-eligibility",
        );
        await cleanup();
        await new Promise((resolve) => setTimeout(resolve, 0));
        const lane = document.querySelector<HTMLSelectElement>(
            'select[aria-label="Full comparison inference lane"]',
        );
        check(lane && !lane.disabled, "native-full-actual-App-lane-selector");
        lane!.value = "approved_native";
        lane!.dispatchEvent(new Event("change", { bubbles: true }));
        await until(
            () => document.querySelector("#comparison-run-native") !== null,
            "native-full-App-native-lane-mounted",
        );
        check(
            lane!.value === "approved_native",
            "native-full-App-lane-selected",
        );
        if (config.stage === "initial") {
            await c.modelAction("model_import");
            check(
                c.get().model?.imported === true &&
                    c.get().model?.loaded === false &&
                    !c.get().modelBusy &&
                    c.get().model?.error === null,
                "native-full-ordinary-import-without-model-load",
            );
        } else {
            await c.refreshModel();
            check(
                c.get().model?.imported === true &&
                    c.get().model?.loaded === false,
                "native-full-restart-import-retained-unloaded",
            );
        }
        await f.loadCatalog();
        check(
            f.get().catalog?.version === 2 &&
                f.get().catalog?.input_lane === "approved_native",
            "native-full-actual-v2-native-catalog",
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
                .sort((a, b) => b.created_ms - a.created_ms)[0];
            check(paired, "native-full-cold-catalog-paired-identity");
            const before = await inventory();
            await terminal(f.open(paired!.run_id), "native-full-cold-open");
            reopenedRun = paired!.run_id;
            check(
                f.get().status?.completed === true &&
                    f.get().status?.report_ready === true &&
                    f.get().status?.completed_scenes === 4,
                "native-full-cold-completed-open",
            );
            await capture("full-restarted");
            await terminal(f.resume(1), "native-full-cold-completed-resume");
            await readerJourney(false);
            await close();
            unchanged(
                before,
                await inventory(),
                "cold-open-read-close-no-execution-or-file-mutation",
            );
            check(
                (await fixtureStatus()).held === false &&
                    actualGenerationObserved === false,
                "native-full-restart-no-held-consent-or-new-generation-claim",
            );
        } else {
            check(
                f.get().catalog!.runs.length === 0,
                "native-full-fresh-owned-catalog",
            );
            await hold();
            const cancelled = f.start("paired", 1);
            await until(
                () =>
                    f.get().status?.version === 2 &&
                    f.get().status?.phase === "awaiting_confirmation",
                "native-full-held-execution-consent",
            );
            await heldConsentEntered();
            check(
                (await fixtureStatus()).held === true &&
                    f.get().status?.running === true,
                "native-full-pending-actual-worker-and-held-consent",
            );
            await capture("full-running");
            const stopping = f.cancel();
            await until(
                () =>
                    f.get().status?.phase === "stopping_at_boundary" ||
                    f.get().status?.error === "Cancelled",
                "native-full-cancel-reaches-actual-owner-before-release",
            );
            await release();
            await stopping;
            await terminal(
                cancelled,
                "native-full-cancel-before-reservation",
                false,
            );
            check(
                f.get().status?.phase === "failed" &&
                    f.get().status?.error === "Cancelled" &&
                    !f.get().status?.report_ready,
                "native-full-cancelled-no-invented-report",
            );
            await capture("full-cancelled");
            await close();

            await fixture("deny-execution-consent");
            await terminal(
                f.start("paired", 1),
                "native-full-denied-execution",
                false,
            );
            check(
                f.get().status?.phase === "failed" &&
                    !f.get().status?.report_ready &&
                    !f.get().status?.completed,
                "native-full-execution-denial-no-generated-result",
            );
            await capture("full-denied");
            await close();

            await hold();
            await fixture("lose-start-ack");
            await f.start("paired", 1);
            const lostClient = f.get().clientId;
            check(
                !!lostClient &&
                    f.get().uncertain &&
                    f.get().error === "EvaluationIo",
                "native-full-lost-successful-ACK-keeps-exact-client",
            );
            accountTransport("native-full-deliberate-lost-start-ACK");
            await capture("full-unknown");
            const lookup = f.lookup();
            await until(
                () =>
                    !f.get().uncertain &&
                    f.get().status?.phase === "awaiting_confirmation",
                "native-full-same-client-lookup-recovers-actual-owner",
            );
            await heldConsentEntered();
            check(
                f.get().clientId === lostClient,
                "native-full-no-duplicate-start-on-ACK-recovery",
            );
            const lostRun = f.get().status!.run_id;
            const cancelLost = f.cancel();
            await until(
                () =>
                    f.get().status?.phase === "stopping_at_boundary" ||
                    f.get().status?.error === "Cancelled",
                "native-full-recovered-owner-cancel-before-release",
            );
            await release();
            await cancelLost;
            await terminal(lookup, "native-full-lost-ACK-cancelled", false);
            check(
                f.get().status?.run_id === lostRun &&
                    f.get().clientId === lostClient &&
                    f.get().status?.error === "Cancelled",
                "native-full-recovery-keeps-original-run",
            );
            await close();

            await hold();
            const retiring = f.start("paired", 1);
            await until(
                () =>
                    f.get().status?.version === 2 &&
                    f.get().status?.phase === "awaiting_confirmation",
                "native-full-retiring-held-owner",
            );
            await heldConsentEntered();
            const old = f.get().status!,
                client = f.get().clientId!;
            check(
                old.operation_id !== null,
                "native-full-retiring-known-operation",
            );
            c.returnToPlay();
            await until(
                () => !f.get().allowed && !r.get().allowed,
                "native-full-context-retirement",
            );
            check(
                f.get().status === null &&
                    r.get().evidence === null &&
                    r.get().summary === null,
                "native-full-retirement-clears-private-presentation",
            );
            // Observe the actual captured close/cancellation before allowing
            // consent to return; frontend eligibility alone proves no stop.
            let retiredClosed = false;
            const retirementDeadline = Date.now() + 30_000;
            while (Date.now() < retirementDeadline) {
                const observed = checkedNativeComparisonRunStatus(
                    await invoke("evaluation_comparison_native", {
                        action: "lookup",
                        query: { clientId: client },
                    }),
                );
                check(
                    observed.client_id === client &&
                        observed.run_id === old.run_id &&
                        observed.operation_id === old.operation_id,
                    "native-full-retirement-observes-only-captured-owner",
                );
                if (observed.phase === "closed") {
                    retiredClosed = true;
                    break;
                }
                await new Promise((resolve) => setTimeout(resolve, 25));
            }
            check(
                retiredClosed && (await fixtureStatus()).held === true,
                "native-full-native-close-before-held-consent-release",
            );
            await release();
            await retiring;
            await drainRetired(client, old.run_id, old.operation_id!);
            c.requestLab();
            c.acknowledgeLab(true);
            await until(
                () => f.get().allowed && !f.get().uncertain && !f.get().busy,
                "native-full-clean-reentry",
            );
            check(
                f.get().status === null && f.get().clientId === null,
                "native-full-no-late-old-owner-publication",
            );
            await capture("full-switched");

            await terminal(
                f.start("paired", 1),
                "native-full-genuine-paired-first-scene",
            );
            const paired = f.get().status!,
                pairedClient = f.get().clientId;
            check(
                paired.phase === "paused" &&
                    paired.completed_scenes === 1 &&
                    !paired.completed &&
                    paired.report_ready,
                "native-full-service-partial-not-complete",
            );
            savedRuns.push(paired.run_id);
            await managedRead(false);
            await r.close();
            await capture("full-partial");
            await terminal(
                f.resume(3),
                "native-full-explicit-three-scene-resume",
            );
            check(
                f.get().clientId === pairedClient &&
                    f.get().status?.run_id === paired.run_id &&
                    f.get().status?.operation_id !== paired.operation_id &&
                    f.get().status?.completed_scenes === 4 &&
                    f.get().status?.completed === true &&
                    f.get().status?.report_ready === true,
                "native-full-resume-keeps-actual-paired-run",
            );
            await cleanup();
            const beforeRetry = await inventory();
            await terminal(
                f.resume(1),
                "native-full-completed-readonly-resume",
            );
            unchanged(
                beforeRetry,
                await inventory(),
                "completed-resume-entire-output-byte-read-only",
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
            await managedRead(true, true);
            await r.close();
            await close();
            await f.loadCatalog();
            check(
                f.get().catalog!.runs.length === 5 &&
                    f
                        .get()
                        .catalog!.runs.some(
                            (run) => run.run_id === paired.run_id,
                        ),
                "native-full-consent-ACK-retirement-no-duplicate-runs",
            );
            check(
                actualGenerationObserved,
                "native-full-actual-role-bearing-native-model-evidence",
            );
        }
        check(
            structural(c.get().play ?? c.get().playV2) === liveBefore,
            "native-full-live-story-unchanged",
        );
        await close();
        check(
            r.get().source === null &&
                r.get().summary === null &&
                r.get().evidence === null,
            "native-full-final-private-reader-cleared",
        );
        const records = errors.snapshot();
        check(
            config.stage === "initial"
                ? records.length === accountedErrors &&
                      accountedErrors === 1 + timeoutRecoveries
                : records.length === 0,
            "native-full-only-boundary-accounted-errors",
        );
        const final = await inventory();
        finalInventoryDigest = final.digest;
        finalInventoryCount = final.file_count;
        await capture("full-finished");
        check(
            captureLabels.length === (config.stage === "initial" ? 14 : 4),
            "native-full-exact-bounded-captures",
        );
        disposalStarted = true;
        await dispose();
        check(
            errors.snapshot().length === records.length,
            "native-full-disposal-adds-no-errors",
        );
        await invoke("harness_finish", { report: report(true) });
    } catch (error) {
        let failureCategory =
            error instanceof Error &&
            error.message === "FullComparisonJourneyTimeout"
                ? error.message
                : "FullComparisonJourneyFailed";
        try {
            if (held) await release();
            if (!disposalStarted) {
                disposalStarted = true;
                await dispose();
            }
        } catch {
            failureCategory = "HarnessCleanupUnconfirmed";
        }
        await invoke("harness_finish", {
            report: report(false, failureCategory),
        });
    }
}
