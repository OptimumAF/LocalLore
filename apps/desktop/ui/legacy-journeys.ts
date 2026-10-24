// Fixed reconstructed synthetic-v1 migration qualification; no generic fixture endpoint.
import type { Controller } from "./controller";
import type { FaultGateway } from "./journeys";
import { structural } from "./model";
import type { ErrorBuffer, Receipt } from "./model";
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
export async function legacyJourneys({
    controller: c,
    gateway: g,
    errors,
    invoke,
    dispose,
    config,
}: Options) {
    const checks: string[] = [];
    let failedCheck = "legacy-start";
    const check = (value: unknown, name: string) => {
        failedCheck = name;
        if (!value) throw new Error(name);
        checks.push(name);
    };
    const capture = async (label: string, inspector = false) => {
        await new Promise((r) => setTimeout(r, 100));
        // Fixed app-owned details, no injected input or generic selector interface.
        const workspace = [...document.querySelectorAll("aside details")].find(
            (node) =>
                node.querySelector("summary")?.textContent ===
                "Saved workspace",
        ) as HTMLDetailsElement | undefined;
        if (workspace) {
            workspace.open = true;
            const displayedPath = workspace.querySelector(".storage-path");
            if (displayedPath)
                displayedPath.textContent =
                    "<synthetic legacy workspace>/stories-v1.sqlite";
        }
        if (inspector)
            document
                .querySelector(".query-table")
                ?.scrollIntoView({ block: "start" });
        else window.scrollTo({ top: 0 });
        await new Promise((r) => setTimeout(r, 100));
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            `${label}-no-horizontal-overflow`,
        );
        const location = c.get().workspace?.location ?? "<none>";
        await invoke("harness_checkpoint", {
            label,
            snapshot: {
                ...c.semantic(),
                workspace: c.get().workspace
                    ? {
                          ...c.get().workspace,
                          location:
                              "<synthetic legacy workspace>/stories-v1.sqlite",
                      }
                    : null,
                checks: [...checks],
                reconstructedV1: true,
                stage: config.stage,
                dom: {
                    text: document
                        .getElementById("root")!
                        .textContent?.replaceAll(
                            location,
                            "<synthetic legacy workspace>/stories-v1.sqlite",
                        ),
                    horizontalOverflow:
                        document.documentElement.scrollWidth > innerWidth + 2,
                },
            },
        });
    };
    try {
        await c.start();
        check(
            config.backend === "native" && c.get().workspace?.persistent,
            "legacy-v1-native-migrated-resume",
        );
        check(
            c.get().workspace?.database_schema_version === 5 &&
                c.get().workspace?.schema_version === 1,
            "legacy-actual-db5-workspace-contract1",
        );
        check(
            c.get().workspace!.stories.length === 1 &&
                c.selected()?.scope.story === "quay" &&
                c.selected()?.scope.branch === "main",
            "legacy-original-scope-and-library-retained",
        );
        check(
            c.get().play?.revision === 1 && c.get().play?.receipts.length === 1,
            "legacy-one-original-accepted-turn",
        );
        const receipt = c.get().play!.receipts[0];
        check(
            receipt.request.turn === "legacy-original-gift" &&
                receipt.request.expected_revision === 0,
            "legacy-original-turn-key-and-basis-retained",
        );
        check(
            !Object.hasOwn(c.get().play!.inventory, "potion") &&
                Object.hasOwn(c.get().play!.inventory, "brass-key"),
            "legacy-spent-last-potion-and-other-item-retained",
        );
        check(
            c.get().draft === "" && c.get().pending === null,
            "legacy-resume-does-not-invent-draft-work",
        );
        const before = structural(c.get().play);
        const reply = (await g.base.call({
            op: "submit",
            session: c.selected()!.id,
            request: receipt.request,
            mode: "accepted",
        })) as { phase: string; receipt: Receipt };
        check(
            reply.phase === "committed" &&
                structural(reply.receipt) === structural(receipt),
            "legacy-exact-old-key-retry-returns-original-receipt",
        );
        const status = (await g.base.call({
            op: "turn_status",
            session: c.selected()!.id,
            scope: c.selected()!.scope,
            turn: receipt.request.turn,
        })) as { phase: string; receipt: Receipt };
        check(
            status.phase === "committed" &&
                structural(status.receipt) === structural(receipt),
            "legacy-exact-status-resolves-original-receipt",
        );
        await c.refresh();
        check(
            structural(c.get().play) === before,
            "legacy-retry-does-not-double-spend-or-append",
        );
        const oracle = (await invoke("harness_oracle", {
            receipts: c.get().play!.receipts,
        })) as { equal: boolean };
        check(
            oracle.equal,
            "legacy-native-receipt-replays-through-direct-engine",
        );
        check(
            document
                .getElementById("root")!
                .textContent?.includes(
                    "SQLite schema 5 | Workspace contract 1 | Domain contract domain-v1",
                ),
            "legacy-render-labels-distinguish-actual-db-contract-domain",
        );
        await capture("durable-resumed");
        await c.showQuery(true);
        await c.browseInspection({
            view: "history",
            search: "",
            atRevision: null,
            limit: 12,
        });
        check(
            c
                .get()
                .query.page?.rows.some(
                    (r) => r.kind === "event" && r.event.sequence === 1,
                ),
            "legacy-player-sees-original-accepted-gift",
        );
        c.requestLab();
        c.acknowledgeLab(true);
        c.setObserver("mira");
        await c.browseInspection({
            view: "history",
            search: "",
            atRevision: null,
            limit: 12,
        });
        check(
            c
                .get()
                .query.page?.rows.some(
                    (r) => r.kind === "event" && r.event.sequence === 1,
                ) &&
                !c.get().query.page?.rows.some((r) => r.kind === "message"),
            "legacy-mira-keeps-witnessed-event-without-player-messages",
        );
        await capture("d05-npc", true);
        c.setObserver("sable");
        await c.browseInspection({
            view: "history",
            search: "",
            atRevision: null,
            limit: 12,
        });
        check(
            c.get().query.page?.rows.length === 0 &&
                c.get().query.page?.next_cursor === null,
            "legacy-uninvolved-sable-cannot-see-private-gift-history",
        );
        await capture("d05-history", true);
        c.returnToPlay();
        await c.refresh();
        check(
            structural(c.get().play) === before,
            "legacy-observer-browsing-never-mutates-canon",
        );
        await capture("durable-retry");
        check(
            errors.snapshot().length === 0,
            "legacy-native-render-has-no-errors",
        );
        await dispose();
        const stats = (await invoke("harness_stats")) as {
            sessions: number;
            workers: number;
        };
        check(
            stats.sessions === 0 && stats.workers === 0,
            "legacy-no-owned-session-or-generation-worker-after-close",
        );
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                reconstructedV1: true,
                passed: true,
                stage: config.stage,
                backend: config.backend,
                checks,
                errors: errors.snapshot(),
            },
        });
    } catch {
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                reconstructedV1: true,
                passed: false,
                failedCheck,
                stage: config.stage,
                backend: config.backend,
                checks,
                errors: errors.snapshot(),
            },
        });
    }
}
