// Fixed synthetic UI/query journey: no local-model or author-control endpoint.
import type { Controller } from "./controller";
import type { FaultGateway } from "./journeys";
import { category, structural } from "./model";
import type { ErrorBuffer, Request, Json } from "./model";
import type { InspectionPage, Row } from "./query-model";
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
    const entered = new Promise<void>((r) => (ready = r)),
        waiting = new Promise<void>((r) => (release = r));
    return { release, ready, entered, waiting };
}
export async function queryJourneys({
    controller: c,
    gateway: g,
    errors,
    invoke,
    dispose,
    config,
}: Options) {
    const checks: string[] = [];
    let failed = "start";
    const check = (v: unknown, name: string) => {
        failed = name;
        if (!v) throw new Error(name);
        checks.push(name);
    };
    const until = async (f: () => boolean) => {
        for (let i = 0; i < 300; i++) {
            if (f()) return;
            await new Promise((r) => setTimeout(r, 15));
        }
        throw new Error("Timeout");
    };
    const page = () => c.get().query.page!;
    const read = async (
        view: Parameters<Controller["browseInspection"]>[0]["view"],
        search = "",
        atRevision: number | null = null,
        limit = 12,
    ) => {
        await c.browseInspection({ view, search, atRevision, limit });
        check(
            !!page(),
            `query-${view}-${search || "all"}-${atRevision ?? "current"}`,
        );
        return page();
    };
    const snap = () =>
        g.call({
            op: "play_snapshot",
            session: c.selected()!.id,
            scope: c.selected()!.scope,
            expected_revision: c.get().play!.revision,
        });
    const capture = async (label: string) => {
        await new Promise((r) => setTimeout(r, 100));
        if (["d05-diff", "d05-source"].includes(label))
            document
                .querySelector(".record-detail")
                ?.scrollIntoView({ block: "start" });
        else if (
            [
                "d05-knowledge",
                "d05-relationships",
                "d05-history",
                "d05-narrow",
            ].includes(label)
        )
            document
                .querySelector(".query-table")
                ?.scrollIntoView({ block: "start" });
        else window.scrollTo({ top: 0 });
        await new Promise((r) => setTimeout(r, 120));
        const root = document.getElementById("root")!;
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            `${label}-no-horizontal-overflow`,
        );
        await invoke("harness_checkpoint", {
            label,
            snapshot: {
                synthetic: true,
                uiRevision: c.get().play?.revision ?? 0,
                query: c.get().query,
                context: {
                    session: c.selected(),
                    view: c.get().view,
                    observer: c.get().observer,
                },
                checks: [...checks],
                dom: {
                    text: root.textContent?.replaceAll(
                        c.get().workspace?.location ?? "<none>",
                        "<synthetic workspace>",
                    ),
                    headings: [...root.querySelectorAll("h1,h2,h3")].map(
                        (n) => n.textContent,
                    ),
                    tables: root.querySelectorAll("table caption").length,
                    horizontalOverflow:
                        document.documentElement.scrollWidth > innerWidth + 2,
                },
            },
        });
    };
    const commit = async (
        turn: string,
        commands: Request["intent"] extends never ? never : unknown[],
    ) => {
        const session = c.selected()!,
            head = c.get().play!.revision;
        const request = {
            version: 1,
            scope: session.scope,
            turn,
            expected_revision: head,
            intent: { kind: "actions", value: commands },
        } as Request;
        const submitted = (await g.call({
            op: "submit",
            session: session.id,
            request,
            mode: "accepted",
        })) as { phase: string };
        check(submitted.phase === "queued", `fixture-${turn}-queued-fake-only`);
        for (const op of ["prepare", "commit"] as const) {
            const status = (await g.call({
                op,
                session: session.id,
                scope: session.scope,
                turn,
            })) as { phase: string };
            check(
                status.phase === (op === "prepare" ? "ready" : "committed"),
                `fixture-${turn}-${op}`,
            );
        }
        await c.refresh();
    };
    try {
        await c.start();
        check(!!c.get().workspace, "query-native-durable-workspace");
        if (config.stage === "restart") {
            const saved = c
                .get()
                .workspace!.stories.find((s) => s.revision >= 3)!;
            check(saved, "saved-inspection-story-exists");
            await c.resume(saved.scope);
            await c.showQuery();
            const before = structural(await snap());
            await read("profiles", "potion", 0);
            check(
                page().rows.some(
                    (r) => r.kind === "field" && r.field === "item/potion",
                ),
                "restart-historical-seed-restores-potion",
            );
            await read("history");
            check(
                page().rows.some((r) => r.kind === "event"),
                "restart-real-history-replays-without-model",
            );
            check(
                structural(await snap()) === before,
                "restart-browsing-never-mutates-canon",
            );
            await capture("d05-restart");
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
        await c.showQuery();
        const seed = await read("profiles");
        check(
            seed.rows.every((r) => r.kind === "field" || r.kind === "clock"),
            "typed-profile-has-no-generated-description",
        );
        check(
            document.querySelector("table caption") &&
                document.querySelector("label select"),
            "table-caption-and-native-labelled-controls",
        );
        await capture("d05-profile");
        await c.showQuery(false);
        c.setAction("give");
        await c.send();
        check(c.get().play?.revision === 1, "fixture-potion-accepted-once");
        await commit("d05-false-claim", [
            {
                op: "say",
                text: "The relic is in old-ruins",
                audience: ["mira"],
            },
        ]);
        await commit("d05-belief", [{ op: "believe", claim_event: 2 }]);
        await c.showQuery();
        const before = structural(await snap()),
            statsBefore = structural(await invoke("harness_stats"));
        const queryBase = {
            version: 1 as const,
            scope: c.selected()!.scope,
            expected_head: c.get().play!.revision,
            at_revision: null,
            observer: { kind: "player" as const },
            view: "history" as const,
            cursor: null,
            limit: 12,
            search: "",
        };
        for (const [patch, expected] of [
            [{ scope: { ...queryBase.scope, branch: "sibling" } }, "Scope"],
            [{ at_revision: queryBase.expected_head + 1 }, "InvalidBoundary"],
            [{ cursor: "edited" }, "InvalidCursor"],
            [{ limit: 65 }, "TooLarge"],
            [{ search: "x".repeat(257) }, "TooLarge"],
            [{ search: "invalid\nsearch" }, "InvalidRequest"],
        ] as const) {
            let rejected = "";
            try {
                await g.call({
                    op: "inspection_query",
                    session: c.selected()!.id,
                    query: { ...queryBase, ...patch },
                });
            } catch (error) {
                rejected = category(error);
            }
            check(
                rejected === expected,
                `native-query-api-denies-${expected}-${Object.keys(patch)[0]}`,
            );
        }

        await read("profiles", "potion", 0);
        check(
            page().rows.some(
                (r) => r.kind === "field" && r.field === "item/potion",
            ),
            "historical-seed-inventory-has-potion",
        );
        await read("profiles", "potion");
        check(
            !page().rows.some(
                (r) => r.kind === "field" && r.field === "item/potion",
            ),
            "current-inventory-potion-remains-spent",
        );
        await read("history");
        check(
            page().rows.some(
                (r) => r.kind === "event" && r.event.sequence === 1,
            ),
            "history-event-links-turn-time-witnesses",
        );
        await capture("d05-history");
        c.selectReceipt(c.get().play!.receipts[0].request.turn);
        await c.traceReceipt();
        check(
            page().view === "turn_diff" && page().revision === 1,
            "chat-receipt-traces-to-completed-historical-turn",
        );
        await read("turn_diff", "", 1);
        const change = page().rows.find(
            (r) =>
                r.kind === "change" &&
                JSON.stringify(r).includes("item/potion"),
        );
        check(
            change &&
                change.kind === "change" &&
                !!change.before &&
                !change.after,
            "historical-turn-diff-potion-before-present-after-absent",
        );
        c.selectInspection(change!.key);
        await capture("d05-diff");
        await read("knowledge");
        check(
            page().rows.some((r) => r.origin === "recorded_statement") &&
                page().rows.some((r) => r.origin === "subjective_belief") &&
                page().rows.some((r) => r.origin === "canonical_truth"),
            "truth-statement-and-belief-are-distinct",
        );
        await capture("d05-knowledge");
        c.requestLab();
        check(
            c.get().labPending && c.get().view === "play",
            "spoiler-request-waits-for-acknowledgement",
        );
        await until(() => !!document.querySelector("dialog[open]"));
        check(
            document.activeElement?.textContent?.includes("I understand"),
            "native-spoiler-dialog-focuses-acknowledgement",
        );
        c.acknowledgeLab(true);
        await until(() => !!page() && !c.get().query.busy);
        c.setObserver("mira");
        await until(() => !!page() && !c.get().query.busy);
        await read("knowledge", "SECRET-TIDE-731");
        check(
            page().total === 0 && !page().next_cursor,
            "npc-secret-search-count-and-page-denied",
        );
        await read("history");
        check(
            !page().rows.some((r) => r.kind === "message"),
            "npc-history-never-has-player-prompt-or-narrator-message",
        );
        check(
            page().rows.some(
                (r) => r.kind === "event" && r.event.sequence === 1,
            ),
            "npc-keeps-actual-witnessed-gift-event",
        );
        await capture("d05-npc");
        await read("relationships");
        check(
            page().rows.every(
                (r) => r.kind === "relationship" && r.from === "mira",
            ),
            "directed-relationship-lens-only-own-outgoing",
        );
        check(
            page().rows.some(
                (r) =>
                    r.kind === "relationship" &&
                    r.dimension === "trust" &&
                    r.value === -3,
            ),
            "independent-trust-dimension-preserved",
        );
        await capture("d05-relationships");
        c.setObserver("sable");
        await until(() => !!page() && !c.get().query.busy);
        await read("history");
        check(
            page().total === 0,
            "unwitnessed-npc-does-not-learn-gift-or-speech",
        );
        c.setObserver("omniscient");
        await until(() => !!page() && !c.get().query.busy);
        await read("profiles", "name", null, 64);
        const names = page().rows.filter(
            (r) => r.kind === "field" && r.field === "name",
        );
        check(
            names.some((r) => r.kind === "field" && r.actor === "oren") &&
                names.some((r) => r.kind === "field" && r.actor === "sable"),
            "duplicate-display-names-retain-distinct-actor-ids",
        );
        c.setView("play");
        await until(() => !!page() && !c.get().query.busy);
        await read("profiles", "", null, 6);
        const first = page().rows.map((r) => r.key);
        check(!!page().next_cursor, "bounded-page-has-continuation");
        await c.nextInspection();
        check(
            page().rows.every((r) => !first.includes(r.key)),
            "pagination-does-not-repeat-visible-records",
        );
        await c.previousInspection();
        check(
            structural(page().rows.map((r) => r.key)) === structural(first),
            "previous-page-preserves-exact-context",
        );
        await capture("d05-pagination");
        const field = page().rows.find((r) => r.kind === "field")!;
        c.selectInspection(field.key);
        let copied = "";
        await c.copyInspection(async (text) => {
            copied = text;
        });
        check(
            JSON.parse(copied).context.observer.kind === "player",
            "copy-selected-record-retains-inspection-context",
        );
        await c.whyInspection(field);
        check(
            page().rows.some(
                (r) => r.kind === "provenance" && r.key === field.key,
            ),
            "why-path-selects-exact-field-provenance",
        );
        await c.followInspectionSource({ kind: "event", value: 1 });
        check(
            page().rows.some(
                (r) => r.kind === "event" && r.event.sequence === 1,
            ),
            "source-link-resolves-accepted-event",
        );
        await capture("d05-source");
        await read("promises");
        check(
            page().rows.some(
                (r) =>
                    r.kind === "promise" &&
                    r.id === "return-key" &&
                    r.status === "open",
            ),
            "seed-promise-keeps-derived-status-and-source",
        );
        await read("summaries");
        check(
            page().status === "unsupported" &&
                page().total === 0 &&
                page().unsupported.length > 0,
            "unimplemented-summary-never-fabricates-content",
        );
        await capture("d05-unsupported");
        await read("retrieval_indexes");
        check(
            page().status === "unsupported",
            "semantic-index-explicitly-unsupported",
        );
        check(
            structural(await snap()) === before,
            "all-browsing-preserves-canon-story-time-and-knowledge",
        );
        check(
            structural(await invoke("harness_stats")) === statsBefore,
            "browsing-does-not-start-provider-worker",
        );
        const held = gate();
        g.heldQuery = held;
        const delayed = c.browseInspection({
            view: "knowledge",
            search: "SECRET-TIDE-731",
        });
        await held.entered;
        c.setView("lab");
        c.setObserver("mira");
        await until(() => !!page() && !c.get().query.busy);
        held.release();
        await delayed;
        check(
            !JSON.stringify(page()).includes("SECRET-TIDE-731") &&
                page().observer.kind === "character",
            "late-private-player-page-cannot-replace-npc-lens",
        );
        c.setView("play");
        await until(() => !!page() && !c.get().query.busy);
        const selected = c.selected()!,
            head = c.get().play!.revision;
        await g.call({
            op: "submit",
            session: selected.id,
            request: {
                version: 1,
                scope: selected.scope,
                turn: "d05-external-wait",
                expected_revision: head,
                intent: { kind: "actions", value: [{ op: "wait", ticks: 1 }] },
            },
            mode: "accepted",
        });
        for (const op of ["prepare", "commit"] as const)
            await g.call({
                op,
                session: selected.id,
                scope: selected.scope,
                turn: "d05-external-wait",
            });
        await c.queryInspection();
        check(
            c.get().query.error === "Stale" && !page(),
            "external-commit-stale-head-shows-no-old-records",
        );
        await capture("d05-stale");
        await c.refresh();
        await read("history");
        check(
            page().head === head + 1,
            "explicit-refresh-reconciles-current-query-head",
        );
        const oldId = selected.id;
        const switchHeld = gate();
        g.heldQuery = switchHeld;
        const oldRead = c.browseInspection({
            view: "knowledge",
            search: "SECRET-TIDE-731",
        });
        await switchHeld.entered;
        await c.create();
        switchHeld.release();
        await oldRead;
        check(
            c.selected()?.id !== oldId &&
                page()?.scope.story === c.selected()?.scope.story &&
                page()?.head === 0,
            "late-page-cannot-cross-new-story-session",
        );
        await read("history");
        check(page().total === 0, "new-story-has-no-prior-history");
        await capture("d05-switch");
        await c.switchSession(oldId);
        await read("history");
        await invoke("harness_viewport", { preset: "narrow" });
        c.layout(0, 0, 150);
        await capture("d05-narrow");
        await invoke("harness_viewport", { preset: "wide" });
        c.layout(1, 1, 100);
        const focus = document.querySelector<HTMLSelectElement>(
            ".query-controls select",
        )!;
        focus.focus();
        check(
            document.activeElement === focus,
            "inspector-native-control-receives-keyboard-focus",
        );
        check(
            document.querySelectorAll(".query-table th[scope]").length > 3,
            "inspection-table-has-row-column-accessibility-semantics",
        );
        check(
            !errors
                .snapshot()
                .some((e) =>
                    ["RenderError", "UnhandledError"].includes(e.category),
                ),
            "query-render-has-no-unhandled-error",
        );
        await capture("d05-finished");
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
        await capture("d05-failure").catch(() => {});
        await dispose().catch(() => {});
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                failedCheck: failed,
                error: String(error),
                checks,
                errors: errors.snapshot(),
            },
        });
    }
}
