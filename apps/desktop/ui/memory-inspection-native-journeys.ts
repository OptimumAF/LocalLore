// Fixed synthetic native UI journey. No desktop input, alternate transport,
// cache builder, provider, arbitrary query or canonical writer.
import type { Controller } from "./controller";
import type {
    MemoryMaintenanceController,
    MemoryAction,
} from "./memory-maintenance-controller";
import type { MemoryInspectionController } from "./memory-inspection-controller";
import { sameMemoryScope } from "./memory-inspection-model";
import type { MemorySourceRef } from "./memory-inspection-model";
import type { BrokerRetention } from "./broker-retention";
import { structural, type ErrorBuffer } from "./model";
import type { FaultGateway } from "./journeys";

type Invoke = (
    command: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
type ReadFixture = {
    version: 1;
    kind: "memory_inspection_fixture";
    synthetic: true;
    held: boolean;
    entered: boolean;
};
const STORY = "memory-controls-synthetic";
const OTHER = "memory-controls-other";
const ORIGINAL = "MEMORY_ORIGINAL_MIRA_ONLY";

export async function memoryInspectionNativeJourneys({
    controller: c,
    maintenance: m,
    inspection: i,
    brokerRetention: retention,
    gateway,
    errors,
    invoke,
    dispose,
    config,
}: {
    controller: Controller;
    maintenance: MemoryMaintenanceController;
    inspection: MemoryInspectionController;
    brokerRetention: BrokerRetention;
    gateway: FaultGateway;
    errors: ErrorBuffer;
    invoke: Invoke;
    dispose: () => Promise<void>;
    config: { stage: string };
}) {
    // The supplied gateway is Main's existing actual native-backed fake-fixture
    // path. Do not replace it, hold Prepare acknowledgements or install a provider.
    void gateway;
    const checks: string[] = [],
        expectedReadErrors: { action: string; error: string; story: string }[] =
            [];
    const outstanding = new Set<Promise<void>>();
    let current = "memory-inspection-start",
        disposed = false;
    const check = (value: unknown, label: string) => {
        current = label;
        if (!value) throw Error(label);
        checks.push(label);
    };
    const pause = () => new Promise<void>((resolve) => setTimeout(resolve, 25));
    const until = async (test: () => boolean, label: string) => {
        current = label;
        for (let count = 0; count < 800; count++) {
            if (test()) return;
            await pause();
        }
        throw Error(`MemoryInspectionDeadline:${label}`);
    };
    const fixture = async (
        action: "hold-read" | "release-read" | "read-state",
    ): Promise<ReadFixture> => {
        const value = await invoke("harness_memory_case", { action });
        if (!value || typeof value !== "object" || Array.isArray(value))
            throw Error("ReadFixtureWire");
        const v = value as Record<string, unknown>;
        check(
            Object.keys(v).sort().join(",") ===
                "entered,held,kind,synthetic,version" &&
                v.version === 1 &&
                v.kind === "memory_inspection_fixture" &&
                v.synthetic === true &&
                typeof v.held === "boolean" &&
                typeof v.entered === "boolean" &&
                (!v.entered || v.held),
            `fixed-${action}-native-ack`,
        );
        return v as ReadFixture;
    };
    // Return an object containing the promise: an async function returning the
    // promise itself would await the held read before its release is possible.
    const startHeld = async () => {
        check((await fixture("hold-read")).held, "fixed-read-gate-armed");
        const read = i.refresh();
        outstanding.add(read);
        void read.then(
            () => outstanding.delete(read),
            () => outstanding.delete(read),
        );
        for (let count = 0; count < 160; count++) {
            if ((await fixture("read-state")).entered) return { read };
            await pause();
        }
        throw Error("ReadGateDidNotEnter");
    };
    const release = async () => {
        const state = await fixture("release-read");
        check(!state.held && !state.entered, "fixed-read-gate-released");
    };
    const player = async (story = STORY) => {
        if (c.get().view !== "lab") c.setView("lab");
        if (c.get().observer !== "player") c.setObserver("player");
        await until(
            () =>
                c.selected()?.scope.story === story &&
                i.get().allowed &&
                i.get().context?.scope.story === story &&
                c.get().inspectionObserver === "player" &&
                c.get().inspectionRevision === c.get().play?.revision,
            "actual-player-inspection-context-ready",
        );
    };
    const lens = async (observer: string) => {
        c.setObserver(observer);
        await until(
            () =>
                c.get().inspection !== null &&
                c.get().inspectionObserver === observer &&
                c.get().inspectionRevision === c.get().play?.revision,
            `actual-${observer}-inspection-ready`,
        );
        return structural(c.get().inspection);
    };
    const packets = async () => {
        check(i.canRead(), "explicit-packet-read-available");
        await i.refresh();
        check(
            i.get().error === null && i.get().packets !== null,
            "actual-packet-page-read",
        );
        return i.get().packets!;
    };
    const source = async () => {
        const packet = i.get().packets?.rows.find((row) => row.index === 0);
        check(
            !!packet && packet.through_revision === 1,
            "retained-real-packet-through-one",
        );
        await i.selectPacket(packet!.index);
        check(
            i.get().error === null && i.get().entries !== null,
            "actual-extractive-entry-page-read",
        );
        const statement = i
            .get()
            .entries!.rows.find(
                (row) =>
                    row.value.class === "observation" &&
                    row.value.event.outcome.effect === "said" &&
                    row.value.event.outcome.text === ORIGINAL,
            );
        check(
            statement?.value.class === "observation" &&
                statement.value.origin === "statement",
            "actual-original-said-entry-not-canonical-fact-label",
        );
        if (!statement || statement.value.class !== "observation")
            throw Error("OriginalStatementUnavailable");
        const ref: MemorySourceRef = statement.value.source;
        await i.source(ref);
        const actual = i.get().source;
        check(
            i.get().error === null &&
                actual?.matched === true &&
                actual.page.version === 2 &&
                actual.page.head === c.get().play?.revision &&
                actual.page.revision === packet!.through_revision &&
                sameMemoryScope(actual.source.scope, ref.scope) &&
                actual.source.sequence === ref.sequence &&
                actual.page.rows.some(
                    (row) =>
                        row.kind === "event" &&
                        row.event.sequence === ref.sequence &&
                        sameMemoryScope(row.event.scope, ref.scope) &&
                        row.event.consequence.effect === "said" &&
                        row.event.consequence.text === ORIGINAL,
                ),
            "actual-query2-original-scope-sequence-and-text-match",
        );
    };
    const maintenance = async (action: MemoryAction) => {
        check(m.can(action), `explicit-maintenance-${action}-available`);
        await m.act(action);
        for (
            let count = 0;
            count < 800 && m.get().operation?.running;
            count++
        ) {
            await pause();
            check(
                m.can("status"),
                "known-maintenance-operation-status-available",
            );
            await m.act("status");
        }
        check(
            !m.get().busy &&
                !m.get().operation?.running &&
                m.get().error === null &&
                !m.get().uncertain,
            `actual-maintenance-${action}-terminal`,
        );
    };
    const capture = async (suffix: string) => {
        const label = `memory-inspection-native-${suffix}`;
        await new Promise((resolve) => setTimeout(resolve, 100));
        const root = document.getElementById("root"),
            panel = root?.querySelector(
                '[aria-labelledby="memory-inspection-title"]',
            );
        check(!!root && !!panel, `${label}-actual-panel-visible`);
        const context = i.get().context;
        check(
            !!context &&
                panel!.textContent?.includes(context.scope.story) &&
                panel!.textContent?.includes(context.scope.branch) &&
                panel!.textContent?.includes(String(context.expected_head)),
            `${label}-scope-head-visible`,
        );
        if (i.get().error)
            check(
                panel!
                    .querySelector('[role="alert"]')
                    ?.textContent?.includes(i.get().error!),
                `${label}-error-visible`,
            );
        if (i.get().source)
            check(
                panel!.textContent?.includes("Original scope and event") &&
                    panel!.textContent?.includes(ORIGINAL),
                `${label}-actual-source-text-visible`,
            );
        const sourceFocus = [
            "source",
            "restart-source",
            "narrow",
            "restart-narrow",
        ].includes(suffix);
        const entryFocus = ["entries", "restart-entries"].includes(suffix);
        const target = sourceFocus
            ? panel!.querySelector(
                  '[aria-label="Actual shared history source"]',
              )
            : entryFocus
              ? panel!.querySelector('[aria-label="Extractive packet entries"]')
              : panel;
        check(!!target, `${label}-actual-capture-target-exists`);
        target!.scrollIntoView({ block: "start" });
        await pause();
        const targetRect = target!.getBoundingClientRect();
        check(
            targetRect.top >= -2 && targetRect.top < innerHeight - 40,
            `${label}-capture-target-in-viewport`,
        );
        if (sourceFocus) {
            check(target!.querySelector("pre")?.tabIndex === 0,
                `${label}-scrollable-source-is-dom-tab-stop`);
            const quote = target!.querySelector("q"),
                box = quote?.getBoundingClientRect();
            check(
                quote?.textContent === ORIGINAL &&
                    !!box &&
                    box.top >= 0 &&
                    box.bottom <= innerHeight,
                `${label}-actual-original-statement-in-viewport`,
            );
        }
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            `${label}-no-horizontal-overflow`,
        );
        const location = c.get().workspace?.location ?? "<none>";
        const semantic = c.semantic();
        const value = (await invoke("harness_checkpoint", {
            label,
            snapshot: {
                semanticVersion: 2,
                synthetic: true,
                uiRevision: c.get().play?.revision ?? 0,
                selectedStory: c.selected(),
                observer: c.get().observer,
                revision: c.get().play?.revision ?? null,
                pendingOperation: {
                    gameplay: c.get().pending,
                    inspection: { busy: i.get().busy, action: i.get().action },
                    maintenance: m.get().operation,
                },
                displayedReceipt: c.receipt(),
                visibleError: c.get().visibleError,
                controller: {
                    ...semantic,
                    workspace: {
                        ...c.get().workspace,
                        location: "<synthetic-workspace>",
                    },
                },
                inspection: i.get(),
                maintenance: m.get(),
                broker: retention.get(),
                nativeFixture: await fixture("read-state"),
                errors: errors.snapshot(),
                expectedReadErrors: [...expectedReadErrors],
                checks: [...checks],
                dom: {
                    captureTarget: sourceFocus
                        ? "source"
                        : entryFocus
                          ? "entries"
                          : "overview",
                    userAgent: navigator.userAgent,
                    viewport: { width: innerWidth, height: innerHeight },
                    text: root!.textContent
                        ?.slice(0, 40000)
                        .replaceAll(location, "<synthetic-workspace>"),
                    panel: panel!.textContent?.slice(0, 32000),
                    structure: [
                        ...panel!.querySelectorAll("button,input,[role],dt,dd,summary,pre[tabindex]"),
                    ]
                        .slice(0, 160)
                        .map((element) => ({
                            tag: element.tagName,
                            role: element.getAttribute("role"),
                            label:
                                element.getAttribute("aria-label") ??
                                element.textContent?.slice(0, 160),
                            disabled: element.hasAttribute("disabled"),
                            tabIndex: element instanceof HTMLElement ? element.tabIndex : null,
                        })),
                },
            },
        })) as { rendering?: string };
        check(
            value.rendering === "native-webview2",
            `${label}-actual-native-webview2-render`,
        );
    };
    try {
        check(
            config.stage === "initial" || config.stage === "restart",
            "closed-memory-inspection-stage",
        );
        await c.start();
        await c.resume({ story: STORY, branch: "main" });
        check(
            c.get().workspace?.persistent &&
                c.get().play !== null &&
                c.get().playV2 === null &&
                c.get().play?.revision === (config.stage === "initial" ? 1 : 2),
            "actual-domain1-durable-memory-fixture",
        );
        await player();
        const before = structural(c.get().play);
        if (config.stage === "initial") {
            const empty = await packets();
            check(
                empty.coverage.status === "raw_fallback" &&
                    empty.coverage.fallback === "missing" &&
                    empty.total === 0 &&
                    empty.rows.length === 0,
                "actual-empty-cache-raw-fallback-no-packet",
            );
            await capture("empty");
            const playerBefore = structural(c.get().inspection),
                miraBefore = await lens("mira"),
                sableBefore = await lens("sable");
            check(
                miraBefore.includes(ORIGINAL) &&
                    !sableBefore.includes(ORIGINAL),
                "actual-witnessed-mira-and-unwitnessed-sable-baseline",
            );
            await player();
            await maintenance("status");
            check(
                m.get().reply?.maintenance.job === null,
                "passive-status-never-admits-inspection-job",
            );
            m.consent(true);
            await maintenance("admit");
            check(
                m.get().reply?.maintenance.job?.status === "ready",
                "explicit-consented-real-memory-job-ready",
            );
            await maintenance("step");
            check(
                m.get().reply?.maintenance.job?.status === "complete" &&
                    m.get().reply?.maintenance.job?.next_from === 1,
                "explicit-real-memory-packet-complete-through-one",
            );
            const page = await packets();
            check(
                page.coverage.status === "verified" &&
                    page.coverage.covered_through === 1 &&
                    page.coverage.verified_head === 1,
                "actual-verified-packet-at-selected-head",
            );
            await capture("packets");
            const packet = page.rows.find((row) => row.index === 0)!;
            await i.selectPacket(packet.index);
            check(
                i.get().entries !== null && i.get().error === null,
                "actual-entry-read-before-source",
            );
            await capture("entries");
            await source();
            await capture("source");
            check(
                (await lens("mira")) === miraBefore &&
                    !i.canRead() &&
                    i.get().packets === null &&
                    i.get().source === null,
                "mira-lens-clears-and-disables-player-packets",
            );
            const callsBlocked = i.get();
            await i.refresh();
            check(
                i.get() === callsBlocked,
                "mira-context-refuses-inspection-read",
            );
            await capture("mira");
            check(
                (await lens("sable")) === sableBefore &&
                    !i.canRead() &&
                    i.get().entries === null,
                "sable-lens-clears-and-disables-player-packets",
            );
            await capture("sable");
            await player();
            const lensRead = await startHeld();
            await lens("mira");
            check(
                i.get().packets === null &&
                    i.get().source === null &&
                    !i.get().allowed,
                "held-read-lens-retirement-clears-private-content",
            );
            check(
                (await fixture("read-state")).entered,
                "real-read-still-held-during-lens-retirement",
            );
            await capture("held-lens");
            check(
                (await fixture("read-state")).entered &&
                    outstanding.has(lensRead.read),
                "held-lens-capture-did-not-consume-native-read-deadline",
            );
            await release();
            await lensRead.read;
            check(
                i.get().packets === null &&
                    i.get().source === null &&
                    i.get().error === null,
                "late-old-player-read-never-publishes-in-mira-context",
            );
            await player();
            const sessionRead = await startHeld();
            await c.resume({ story: OTHER, branch: "main" });
            await player(OTHER);
            check(
                i.get().packets === null &&
                    i.get().entries === null &&
                    i.get().source === null,
                "actual-session-switch-clears-old-packet-data",
            );
            await i.refresh();
            check(
                i.get().error === "Busy" && i.get().packets === null,
                "actual-one-native-read-slot-busy-in-other-session",
            );
            expectedReadErrors.push({
                action: "packets",
                error: "Busy",
                story: OTHER,
            });
            await capture("other-busy");
            check(
                (await fixture("read-state")).entered &&
                    outstanding.has(sessionRead.read),
                "other-busy-capture-retains-actual-original-read-slot",
            );
            await release();
            await sessionRead.read;
            check(
                i.get().error === "Busy" && i.get().packets === null,
                "late-other-context-read-cannot-clear-current-busy-error",
            );
            check(
                (await packets()).coverage.status === "raw_fallback",
                "explicit-other-session-recovery-is-own-empty-cache",
            );
            await c.resume({ story: STORY, branch: "main" });
            await player();
            await packets();
            await source();
            await capture("session-return");
            check(
                structural(c.get().play) === before &&
                    structural(c.get().inspection) === playerBefore &&
                    (await lens("mira")) === miraBefore &&
                    (await lens("sable")) === sableBefore,
                "inspection-and-explicit-maintenance-preserve-canon-receipts-and-three-observers",
            );
            c.setView("play");
            c.setAction("wait");
            check(
                c.get().playMode === "fixture" &&
                    c.get().fakeMode === "accepted",
                "ordinary-wait-uses-existing-fake-fixture-not-model",
            );
            await c.send();
            check(
                c.get().pending === null &&
                    c.get().visibleError === null &&
                    c.get().turnStatus?.phase === "committed" &&
                    c.get().play?.revision === 2 &&
                    c.get().play?.receipts.length === 2,
                "one-ordinary-typed-wait-accepted-exactly-once",
            );
            await player();
            const afterWait = structural(c.get().play),
                prefix = await packets();
            check(
                prefix.coverage.status === "verified" &&
                    prefix.coverage.verified_head === 2 &&
                    prefix.coverage.covered_through === 1 &&
                    prefix.coverage.raw_delta_after === 1,
                "actual-head-two-honest-verified-prefix-through-one",
            );
            await source();
            await capture("prefix");
            await invoke("harness_viewport", { preset: "capture-narrow" });
            await capture("narrow");
            check(
                structural(c.get().play) === afterWait,
                "prefix-source-and-narrow-reads-preserve-new-canonical-state",
            );
            await invoke("harness_viewport", { preset: "wide" });
            await capture("final");
        } else {
            check(
                m.get().reply === null && m.get().operation === null,
                "restart-no-auto-maintenance-or-job-admission",
            );
            await maintenance("status");
            check(
                m.get().reply?.maintenance.job?.basis_revision === 1 &&
                    m.get().reply?.maintenance.job?.next_from === 1,
                "restart-passive-job-status-retains-actual-old-basis",
            );
            const reopened = await packets();
            check(
                reopened.coverage.status === "verified" &&
                    reopened.coverage.verified_head === 2 &&
                    reopened.coverage.covered_through === 1 &&
                    reopened.coverage.raw_delta_after === 1,
                "restart-actual-durable-prefix-and-current-head",
            );
            await capture("reopened");
            await i.selectPacket(0);
            check(
                i.get().entries !== null && i.get().error === null,
                "restart-actual-durable-entries",
            );
            await capture("restart-entries");
            await source();
            await capture("restart-source");
            await invoke("harness_viewport", { preset: "capture-narrow" });
            await capture("restart-narrow");
            check(
                structural(c.get().play) === before,
                "restart-inspection-does-not-add-or-change-accepted-receipts",
            );
        }
        check(
            errors.snapshot().length === 0,
            "no-unexpected-native-or-frontend-error-records",
        );
        check(
            expectedReadErrors.length === (config.stage === "initial" ? 1 : 0),
            "only-exact-deliberate-current-read-busy-error",
        );
        check(
            !(await fixture("read-state")).held && outstanding.size === 0,
            "all-fixed-read-gates-and-replies-drained",
        );
        await dispose();
        disposed = true;
        const stats = (await invoke("harness_stats")) as {
            sessions?: number;
            workers?: number;
        };
        check(
            stats.sessions === 0 && stats.workers === 0,
            "actual-owned-host-sessions-and-workers-drained",
        );
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                semanticVersion: 2,
                stage: config.stage,
                checks,
                errors: errors.snapshot(),
                expectedReadErrors,
                realModelGeneration: false,
                unavailable: [
                    "genuine model inference/quality",
                    "Domain 2 native visual inspection",
                    "same-head cache replacement",
                ],
            },
        });
    } catch (error) {
        const failedCheck = current;
        let cleanupUnconfirmed = false;
        try {
            await release();
        } catch {
            cleanupUnconfirmed = true;
        }
        const settled = await Promise.allSettled([...outstanding]);
        if (settled.some((value) => value.status === "rejected"))
            cleanupUnconfirmed = true;
        if (!disposed) {
            try {
                await dispose();
                disposed = true;
            } catch {
                cleanupUnconfirmed = true;
            }
        }
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                semanticVersion: 2,
                stage: config.stage,
                checks,
                failedCheck,
                error:
                    error instanceof Error
                        ? error.message
                        : String(error).slice(0, 160),
                inspection: i.get(),
                maintenance: m.get(),
                broker: retention.get(),
                errors: errors.snapshot(),
                expectedReadErrors,
                cleanupUnconfirmed,
                realModelGeneration: false,
            },
        });
    }
}
