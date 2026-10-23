// Development-only journeys run through the actual controller and native IPC.
import { Controller } from "./controller";
import { structural, request } from "./model";
import type { ErrorBuffer, Receipt } from "./model";
import type { FaultGateway } from "./journeys";
interface Options {
    controller: Controller;
    gateway: FaultGateway;
    errors: ErrorBuffer;
    invoke: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
    dispose: () => Promise<void>;
    config: {
        backend: "native" | "headless";
        stage: "initial" | "reopened" | "restart";
        failure?: boolean;
    };
}
export async function durableJourneys({
    controller: c,
    gateway: g,
    errors,
    invoke,
    dispose,
    config,
}: Options) {
    const checks: string[] = [];
    let failedCheck = "workspace-open";
    const check = (value: unknown, label: string) => {
        failedCheck = label;
        if (!value) throw new Error(label);
        checks.push(label);
    };
    const checkpoint = async (label: string) => {
        await new Promise((r) => setTimeout(r, 100));
        const root = document.getElementById("root")!;
        await invoke("harness_checkpoint", {
            label,
            snapshot: {
                ...c.semantic(),
                workspace: c.get().workspace
                    ? {
                          ...c.get().workspace,
                          location: "<synthetic-app-local>/stories-v1.sqlite",
                      }
                    : null,
                checks: [...checks],
                backend: config.backend,
                dom: {
                    text: root.textContent
                        ?.slice(0, 32000)
                        .replaceAll(
                            c.get().workspace?.location ?? "<no-location>",
                            "<synthetic-app-local>/stories-v1.sqlite",
                        ),
                    viewport: { width: innerWidth, height: innerHeight },
                    horizontalOverflow:
                        document.documentElement.scrollWidth > innerWidth + 2,
                },
            },
        });
    };
    const finish = async () => {
        await dispose();
        const stats = (await invoke("harness_stats")) as {
            sessions: number;
            workers: number;
        };
        check(
            stats.sessions === 0 && stats.workers === 0,
            "owned-resources-released",
        );
        await checkpoint("durable-disposed");
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                backend: config.backend,
                stage: config.stage,
                checks,
                errors: errors.snapshot(),
            },
        });
    };
    try {
        if (config.failure) {
            await c.start();
            check(
                c.get().visibleError === "Io" &&
                    c.get().workspace === null &&
                    c.get().sessions.length === 0,
                "storage-open-failure-is-visible-no-memory-fallback",
            );
            check(
                document
                    .getElementById("root")!
                    .textContent?.includes("Storage unavailable"),
                "storage-failure-rendered-in-app",
            );
            await checkpoint("durable-storage-error");
            await dispose();
            await invoke("harness_finish", {
                report: {
                    synthetic: true,
                    passed: true,
                    backend: config.backend,
                    stage: "storage-failure",
                    checks,
                    errors: errors.snapshot(),
                },
            });
            return;
        }
        const library = await c.library();
        check(
            library.persistent && library.schema_version === 1,
            "real-workspace-schema-v1",
        );
        check(
            library.location.endsWith("stories-v1.sqlite"),
            "actual-storage-path-reported",
        );
        if (config.stage !== "initial") {
            await c.start();
            check(
                c.selected()?.scope.story === library.stories[0].scope.story,
                "startup-resumes-first-stable-library-entry",
            );
            const saved = library.stories.find((s) => s.revision > 0);
            check(saved, "saved-story-listed-after-reopen");
            await c.resume(saved!.scope);
            check(
                saved!.drafts === 1 &&
                    c.get().notice.includes("not automatically"),
                "uncommitted-request-survives-with-warning-no-auto-commit",
            );
            check(
                c.get().play!.receipts.length === 2,
                "two-canonical-receipts-survive-reopen",
            );
            check(
                !Object.hasOwn(c.get().play!.inventory, "potion") &&
                    Object.hasOwn(c.get().play!.inventory, "brass-key"),
                "spent-inventory-survives-reopen",
            );
            const receipt = c.get().play!.receipts[0];
            const before = c.get().play!.revision;
            const reply = (await g.base.call({
                op: "submit",
                session: c.selected()!.id,
                request: receipt.request,
                mode: "accepted",
            })) as { phase: string; receipt: Receipt };
            check(
                reply.phase === "committed" &&
                    structural(reply.receipt) === structural(receipt),
                "old-exact-turn-retry-returns-stored-receipt",
            );
            await c.refresh();
            check(
                c.get().play!.revision === before &&
                    c.get().play!.receipts.length === 2,
                "restart-retry-does-not-double-apply",
            );
            const oracle = (await invoke("harness_oracle", {
                receipts: c.get().play!.receipts,
            })) as { equal: boolean };
            check(oracle.equal, "resumed-receipts-equal-direct-engine");
            check(
                c.get().draft === "",
                "unsent-draft-is-explicitly-session-local",
            );
            if (config.stage === "restart") {
                const oldTurns = new Set(
                    c.get().play!.receipts.map((r) => r.request.turn),
                );
                c.setAction("wait");
                await c.send();
                check(
                    c.get().turnStatus?.phase === "committed" &&
                        !oldTurns.has(c.get().turnStatus!.turn),
                    "new-process-uses-distinct-turn-key",
                );
            }
            await checkpoint(
                config.stage === "restart"
                    ? "durable-resumed"
                    : "durable-reopened",
            );
            await finish();
            return;
        }
        check(library.stories.length === 0, "fresh-synthetic-root-is-empty");
        await c.start();
        check(
            c.get().play?.receipts.length === 0,
            "first-start-creates-saved-original-story",
        );
        await checkpoint("durable-initial");
        await c.send();
        check(
            c.get().turnStatus?.phase === "committed",
            "accepted-turn-committed-and-saved",
        );
        check(
            c.get().play?.receipts.length === 1,
            "only-authoritative-receipt-displayed",
        );
        const savedScope = c.selected()!.scope;
        await checkpoint("durable-accepted");
        let staleRejected = false;
        try {
            const stale = structuredClone(c.get().play!.receipts[0].request);
            stale.turn = `stale-${crypto.randomUUID()}`;
            await g.base.call({
                op: "submit",
                session: c.selected()!.id,
                request: stale,
                mode: "accepted",
            });
        } catch (error) {
            staleRejected = error instanceof Error && error.message === "Stale";
        }
        check(staleRejected, "saved-head-rejects-stale-request");
        await c.refresh();
        check(
            c.get().play!.receipts.length === 1,
            "stale-request-does-not-append",
        );
        await checkpoint("durable-stale");
        c.setAction("wait");
        c.setFakeMode("delayed");
        c.setDraft("Synthetic unsent draft");
        const pending = c.send();
        while (!c.get().turnStatus || c.get().turnStatus?.phase === "committed")
            await new Promise((r) => setTimeout(r, 5));
        await c.cancel();
        await pending;
        check(
            c.get().turnStatus?.phase === "cancelled" &&
                c.get().play!.receipts.length === 1,
            "cancel-does-not-create-canonical-receipt",
        );
        check(
            c.get().draft === "Synthetic unsent draft",
            "cancel-retains-unsent-composer-text",
        );
        await checkpoint("durable-cancelled");
        c.setFakeMode("accepted");
        g.dropCommit = true;
        g.failLookup = true;
        await c.send();
        const original = g.submissions.at(-1);
        check(
            c.get().visibleError === "TransportUnknown",
            "lost-commit-ack-is-unknown",
        );
        await c.retry();
        check(
            c.get().turnStatus?.turn === original &&
                c.get().play!.receipts.length === 2,
            "uncertain-retry-resolves-original-key-once",
        );
        await checkpoint("durable-retry");
        const initialSession = c.selected()!;
        await c.closeSession();
        check(
            (await c.library()).stories.some(
                (s) => s.scope.story === savedScope.story,
            ),
            "close-keeps-saved-story",
        );
        await c.resume(savedScope);
        check(
            c.get().play!.receipts.length === 2,
            "explicit-library-resume-restores-transcript",
        );
        await c.create();
        check(
            c.selected()!.scope.story !== initialSession.scope.story,
            "new-creates-distinct-story",
        );
        check(
            c.get().workspace!.stories.length === 2,
            "new-retains-earlier-save",
        );
        await c.reset();
        check(
            c.get().workspace!.stories.length === 3,
            "reset-keeps-previous-saves",
        );
        await checkpoint("durable-new");
        await c.resume(savedScope);
        await g.base.call({
            op: "submit",
            session: c.selected()!.id,
            request: request(
                savedScope,
                `orphan-${crypto.randomUUID()}`,
                c.get().play!.revision,
                "wait",
                "",
            ),
            mode: "accepted",
        });
        check(
            (await c.library()).stories.find(
                (s) => s.scope.story === savedScope.story,
            )?.drafts === 1,
            "submitted-uncommitted-request-is-durable",
        );
        c.setDraft("Synthetic unsent draft");
        await invoke("harness_reopen");
    } catch {
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                failedCheck,
                backend: config.backend,
                stage: config.stage,
                checks,
                errors: errors.snapshot(),
            },
        });
    }
}
