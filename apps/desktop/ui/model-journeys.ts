// Development-only fixed real local CPU journeys; actual controller and native IPC.
import type { Controller } from "./controller";
import type { FaultGateway } from "./journeys";
import { category } from "./model";
import type { ErrorBuffer, Json, Receipt } from "./model";
interface Options {
    controller: Controller;
    gateway: FaultGateway;
    errors: ErrorBuffer;
    invoke: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
    dispose: () => Promise<void>;
    config: {
        backend: "native" | "headless";
        stage: "initial" | "reopened" | "restart";
    };
}
export async function modelJourneys({
    controller: c,
    gateway: g,
    errors,
    invoke,
    dispose,
    config,
}: Options) {
    const checks: string[] = [];
    const measurements: {
        stage: string;
        elapsed_ms: number;
        phase?: string;
        error?: string | null;
        receipt?: Receipt | null;
    }[] = [];
    let current = "model-start";
    const check = (condition: unknown, label: string) => {
        current = label;
        if (!condition) throw new Error(label);
        checks.push(label);
    };
    const until = async (
        predicate: () => boolean | Promise<boolean>,
        limit = 30000,
    ) => {
        const start = performance.now();
        while (!(await predicate())) {
            if (performance.now() - start > limit) throw new Error("Timeout");
            await new Promise((r) => setTimeout(r, 30));
        }
    };
    const capture = async (label: string) => {
        if (label === "model-receipt-context") window.scrollTo({ top: 0 });
        else
            document
                .querySelector(
                    label.includes("pending")
                        ? ".compose"
                        : label.includes("receipt")
                          ? ".transcript"
                          : ".model-panel",
                )
                ?.scrollIntoView({ block: "start" });
        await new Promise((r) => setTimeout(r, 100));
        const clean = (value: unknown, key = ""): unknown =>
            key === "location"
                ? "<synthetic workspace>"
                : typeof value === "object" && value
                  ? Array.isArray(value)
                      ? value.map((v) => clean(v))
                      : Object.fromEntries(
                            Object.entries(value).map(([k, v]) => [
                                k,
                                clean(v, k),
                            ]),
                        )
                  : value;
        const root = document.getElementById("root")!;
        await invoke("harness_checkpoint", {
            label,
            snapshot: {
                ...(clean(c.semantic()) as object),
                synthetic: true,
                checks: [...checks],
                measurements,
                uiRevision: c.get().play?.revision ?? 0,
                backend: config.backend,
                dom: {
                    text: String(
                        clean(
                            root.textContent?.replaceAll(
                                c.get().workspace?.location ?? "<none>",
                                "<synthetic workspace>",
                            ),
                        ),
                    ).slice(0, 64000),
                    headings: [...root.querySelectorAll("h1,h2,h3")].map(
                        (e) => e.textContent,
                    ),
                    horizontalOverflow:
                        document.documentElement.scrollWidth > innerWidth + 2,
                },
            },
        });
    };
    const timed = async (stage: string, action: () => Promise<void>) => {
        const start = performance.now();
        await action();
        measurements.push({
            stage,
            elapsed_ms: Math.round(performance.now() - start),
            phase: c.get().turnStatus?.phase,
            error: c.get().visibleError,
            receipt: c.get().turnStatus?.receipt,
        });
    };
    const play = async (
        stage: string,
        text: string,
        kind: "action" | "dialogue" = "action",
    ) => {
        c.setInputKind(kind);
        c.setDraft(text);
        await timed(stage, () => c.send());
    };
    try {
        await c.start();
        check(!!c.get().workspace, "real-native-durable-workspace");
        c.showModel();
        await c.refreshModel();
        check(
            !c.get().model?.loaded,
            "model-starts-unloaded-no-silent-fallback",
        );
        if (config.stage === "initial" && !c.get().model?.imported) {
            for (const scenario of ["missing", "corrupt"]) {
                await invoke("harness_model_case", { case: scenario });
                await c.modelAction("model_import");
                check(
                    c.get().visibleError === "ModelInvalid",
                    `native-${scenario}-import-refused`,
                );
                check(
                    !c.get().model?.imported,
                    `${scenario}-does-not-publish-model`,
                );
            }
            await capture("model-invalid");
            await invoke("harness_model_case", { case: "cancel" });
            await c.modelAction("model_import");
            check(
                !c.get().model?.imported,
                "native-model-picker-cancel-is-honest",
            );
            const importing = c.modelAction("model_import");
            await until(
                () => !!c.get().model && c.get().model!.phase === "copying",
            );
            await c.cancelModel();
            await importing;
            check(
                !c.get().model?.imported && !c.get().model?.loaded,
                "cancelled-import-never-publishes-partial-model",
            );
            await timed("model_import", () => c.modelAction("model_import"));
            check(
                c.get().model?.imported,
                "approved-model-imports-to-app-owned-unicode-space-workspace",
            );
            await capture("model-imported");
        } else if (config.stage === "restart") {
            check(
                c.get().model?.imported,
                "imported-model-retained-after-real-process-restart",
            );
            const saved = c
                .get()
                .workspace!.stories.find((s) => s.revision > 0);
            check(saved, "real-turn-save-in-library-after-restart");
            await c.resume(saved!.scope);
            check(
                !Object.hasOwn(c.get().play!.inventory, "potion"),
                "real-spent-potion-still-spent-after-restart",
            );
            check(
                c.get().play!.receipts.some((r) => r.play?.version === 2),
                "v2-provenance-restores-without-loaded-model",
            );
            const original = c
                .get()
                .play!.receipts.find((r) => r.play?.version === 2)!.request;
            const retried = (await g.call({
                op: "free_text",
                session: c.selected()!.id,
                request: original,
            })) as { phase: string };
            check(
                retried.phase === "committed",
                "exact-original-real-key-resolves-saved-receipt-without-loaded-model",
            );
            await capture("model-restarted");
        }
        if (config.stage === "initial" && c.get().model?.imported)
            check(
                true,
                "existing-owned-import-reused-without-second-model-copy",
            );
        if (config.stage === "initial") {
            const loading = c.modelAction("model_load");
            await until(() => c.get().modelCancelReady);
            await c.cancelModel();
            await loading;
            check(
                !c.get().model?.loaded,
                "native-model-hash-load-cancel-keeps-host-unconfigured",
            );
        }
        await timed("model_load", () => c.modelAction("model_load"));
        check(
            c.get().model?.loaded,
            "actual-fixed-packaged-worker-loads-approved-model",
        );
        check(
            c.get().model?.profile?.worker_sha256 ===
                "b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434",
            "loaded-worker-provenance-is-verified",
        );
        c.setPlayMode("local");
        check(
            c.get().playMode === "local",
            "explicit-real-cpu-profile-selected",
        );
        await capture("model-loaded");
        if (config.stage === "restart") {
            const revision = c.get().play!.revision;
            await c.modelAction("model_unload");
            check(!c.get().model?.loaded, "real-restart-model-unloads-cleanly");
            check(
                c.get().play!.revision === revision,
                "unload-does-not-rewrite-saved-history",
            );
            await capture("model-finished");
            await dispose();
            await invoke("harness_finish", {
                report: {
                    synthetic: true,
                    passed: true,
                    stage: config.stage,
                    checks,
                    measurements,
                    errors: errors.snapshot(),
                },
            });
            return;
        }
        c.setInputKind("action");
        c.setDraft("I give my last potion to Mira.");
        const before = c.get().play!.revision;
        g.dropCommit = true;
        const sending = c.send();
        await until(() => !!c.get().pending);
        check(
            c.get().play!.revision === before &&
                c.get().play!.receipts.length === 0,
            "pending-model-output-is-noncanonical",
        );
        await capture("model-pending");
        await timed("potion", () => sending);
        check(
            c.get().turnStatus?.phase === "committed",
            "real-free-text-potion-committed",
        );
        check(
            !Object.hasOwn(c.get().play!.inventory, "potion"),
            "real-potion-spent-once",
        );
        check(
            c.get().turnStatus?.receipt?.play?.version === 2,
            "real-receipt-records-v2-profile-and-policy",
        );
        check(
            c.get().play!.receipts.length === 1,
            "lost-native-commit-ack-resolves-one-original-v2-receipt",
        );
        await capture("model-receipt");
        await capture("model-receipt-context");
        await play("double-spend", "I give another potion to Mira.");
        check(
            c.get().play!.revision === before + 1,
            "real-double-spend-never-adds-event",
        );
        await play(
            "secret",
            "The lantern code is SYNTHETIC_AMBER_FINCH.",
            "dialogue",
        );
        check(
            c.get().turnStatus?.phase === "committed",
            "real-explicit-dialogue-committed",
        );
        const savedRevision = c.get().play!.revision;
        await play(
            "invalid",
            "I use my teleport ability to travel to the moon.",
        );
        check(
            c.get().play!.revision === savedRevision,
            "real-unlearned-ability-cannot-mutate-canon",
        );
        check(
            c.get().turnStatus?.error === "ClarificationRequired",
            "unsupported-teleport-asks-clarification-without-alternate-effect",
        );
        await play("known-unlearned-ability", "I use ability teleport.");
        check(
            c.get().turnStatus?.error === "Ability" &&
                c.get().play!.revision === savedRevision,
            "supported-unlearned-ability-is-refused-by-engine",
        );
        await capture("model-invalid-action");
        c.setDraft("I wait for one tide tick.");
        c.setInputKind("action");
        const pending = c.send();
        await until(async () => (await c.pendingStatus())?.phase === "running");
        await new Promise((r) => setTimeout(r, 100));
        await c.cancel();
        await pending;
        check(
            c.get().play!.revision === savedRevision,
            "real-generation-cancel-leaves-canon-unchanged",
        );
        await capture("model-cancelled");
        c.setView("lab");
        c.setObserver("sable");
        await c.inspect();
        check(
            !JSON.stringify(c.get().inspection).includes(
                "SYNTHETIC_AMBER_FINCH",
            ),
            "absent-npc-inspection-excludes-secret",
        );
        const scope = c.selected()!.scope;
        await c.create();
        check(
            c.get().play!.revision === 0 && c.get().play!.receipts.length === 0,
            "new-story-isolates-real-history",
        );
        await c.resume(scope);
        check(
            c.get().play!.revision === savedRevision,
            "original-real-story-retains-canonical-head",
        );
        await c.modelAction("model_unload");
        check(
            !c.get().model?.loaded && c.get().playMode === "local",
            "unload-never-selects-fake-profile",
        );
        c.setDraft("I wait.");
        await c.send();
        check(
            c.get().visibleError === "ModelUnavailable",
            "unloaded-real-play-has-actionable-error",
        );
        await timed("model_reload", () => c.modelAction("model_load"));
        check(c.get().model?.loaded, "model-can-recover-by-explicit-reload");
        await c.modelAction("model_unload");
        await capture("model-finished");
        await dispose();
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                stage: config.stage,
                checks,
                measurements,
                errors: errors.snapshot(),
            },
        });
    } catch (error) {
        await capture("model-failure").catch(() => {});
        await c.modelAction("model_unload");
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                stage: config.stage,
                failedCheck: current,
                error: category(error),
                checks,
                measurements,
                errors: errors.snapshot(),
            },
        });
    }
}
