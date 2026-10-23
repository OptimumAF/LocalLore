// Native invisible application WebView; fixed synthetic inference through production Play.
import type { Controller } from "./controller";
import type { CaptureController } from "./capture-controller";
import type { FaultGateway } from "./journeys";
import { category, structural } from "./model";
import type { ErrorBuffer } from "./model";
interface Options {
    controller: Controller;
    capture: CaptureController;
    gateway: FaultGateway;
    errors: ErrorBuffer;
    invoke: (command: string, args?: Record<string, unknown>) => Promise<any>;
    dispose: () => Promise<void>;
    config: { stage: string };
}
export async function captureJourneys({
    controller: c,
    capture: privateCapture,
    gateway: g,
    errors,
    invoke,
    dispose,
    config,
}: Options) {
    const checks: string[] = [];
    let failed = "start",
        next = 0;
    const check = (value: unknown, name: string) => {
        failed = name;
        if (!value) throw Error(name);
        checks.push(name);
    };
    const settled = async () => {
        for (let n = 0; n < 100 && privateCapture.get().controlBusy; n++)
            await new Promise((r) => setTimeout(r, 10));
        check(!privateCapture.get().controlBusy, "private-control-settled");
    };
    const snap = () =>
        g.call({
            op: "play_snapshot",
            session: c.selected()!.id,
            scope: c.selected()!.scope,
            expected_revision: c.get().play!.revision,
        });
    const checkpoint = async (label: string) => {
        await new Promise((r) => setTimeout(r, 150));
        document
            .querySelector(".private-capture")
            ?.scrollIntoView({ block: "start" });
        await new Promise((r) => setTimeout(r, 100));
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            `${label}-no-overflow`,
        );
        await invoke("harness_checkpoint", {
            label,
            snapshot: {
                synthetic: true,
                uiRevision: c.get().play?.revision ?? 0,
                checks: [...checks],
                capture: {
                    ...privateCapture.get(),
                    reply: privateCapture.get().reply
                        ? {
                              ...privateCapture.get().reply,
                              details: {
                                  ...privateCapture.get().reply!.details,
                                  artifacts: privateCapture
                                      .get()
                                      .reply!.details.artifacts.map((a) => ({
                                          kind: a.kind,
                                          ordinal: a.ordinal,
                                      })),
                              },
                          }
                        : null,
                },
                trace: c.get().trace,
                dom: {
                    text: document
                        .getElementById("root")
                        ?.textContent?.slice(0, 16384),
                    text_limit: 16384,
                },
            },
        });
    };
    const lens = async () => {
        c.requestLab();
        c.acknowledgeLab(true);
        await c.showTrace();
        await settled();
    };
    const selected = async (base: number) => {
        await c.traceBasis(base);
        await settled();
        await privateCapture.read();
        check(
            privateCapture.get().reply !== null,
            "private-selected-metadata-attempt-read",
        );
        return privateCapture.get().reply!;
    };
    const stage = async (mode: string) => {
        await invoke("harness_capture_case", { case: mode });
        const s = c.selected()!,
            base = c.get().play!.revision,
            turn = `capture-${mode}-${++next}`;
        const request = {
            version: 1,
            scope: s.scope,
            turn,
            expected_revision: base,
            intent: {
                kind: "free_text" as const,
                value: {
                    kind: "action" as const,
                    text:
                        mode === "wait" || mode === "pending"
                            ? "I wait."
                            : "I give my last potion to Mira.",
                },
            },
        };
        const submit = (await g.call({
            op: "free_text",
            session: s.id,
            request,
        })) as any;
        check(submit.phase === "queued", `${mode}-real-host-admitted`);
        const control = (op: "prepare" | "commit" | "cancel" | "turn_status") =>
            g.call({ op, session: s.id, scope: s.scope, turn }) as Promise<any>;
        return {
            base,
            turn,
            control,
            prepared: mode === "pending" ? null : await control("prepare"),
        };
    };
    try {
        await c.start();
        check(
            c.get().workspace?.persistent,
            "private-capture-native-production-play",
        );
        if (config.stage === "restart") {
            const saved = c
                .get()
                .workspace?.stories.find((s) => s.revision > 0);
            check(saved, "private-restart-accepted-history-exists");
            await c.resume(saved!.scope);
            await lens();
            check(
                c.get().trace.reply?.snapshot.attempts.length === 0,
                "private-restart-no-attempt-reconstruction",
            );
            const receipt = c.get().play!.receipts[0];
            const absent = (await g.call({
                op: "trace_capture_read",
                session: c.selected()!.id,
                scope: c.selected()!.scope,
                expected_head: c.get().play!.revision,
                base_revision: receipt.request.expected_revision,
                turn: receipt.request.turn,
                attempt: 1,
            })) as any;
            check(
                absent.details.status === "disabled" &&
                    absent.details.artifacts.length === 0,
                "private-restart-consent-default-off",
            );
            await checkpoint("d06-private-restarted");
        } else {
            await lens();
            check(
                privateCapture.get().enabled === null &&
                    privateCapture.get().reply === null,
                "private-default-no-consent-or-details",
            );
            await checkpoint("d06-private-disabled");
            const before = structural(await snap());
            await privateCapture.configure(false);
            check(
                privateCapture.get().enabled !== true,
                "private-future-opt-in-required",
            );
            await privateCapture.configure(true);
            check(
                privateCapture.get().enabled === true,
                "private-explicit-consent-enabled",
            );
            check(
                structural(await snap()) === before,
                "private-consent-does-not-mutate-canon",
            );
            const repair = await stage("repair");
            check(repair.prepared.phase === "ready", "private-repair-ready");
            let reply = await selected(repair.base);
            check(
                reply.details.status === "recorded" &&
                    reply.details.exact_reconstruction === false,
                "private-recorded-not-exact-reconstruction",
            );
            const artifacts = reply.details.artifacts,
                ctx = artifacts.find((a) => a.kind === "selected_context")
                    ?.value as any;
            check(
                ctx?.observer === c.get().play!.player.observer &&
                    ctx?.role === "director" &&
                    Array.isArray(ctx.records),
                "private-actual-player-context-not-lab-context",
            );
            check(
                !JSON.stringify(ctx).includes("smuggler") &&
                    !JSON.stringify(ctx).includes("SECRET_CANARY"),
                "private-captured-context-actor-filtered",
            );
            check(
                artifacts.filter((a) => a.kind === "raw_director_output")
                    .length === 2 &&
                    JSON.stringify(artifacts).includes(
                        "MALFORMED_SYNTHETIC_DIRECTOR",
                    ),
                "private-malformed-and-repaired-raw-output-retained",
            );
            check(
                artifacts.some(
                    (a) => a.kind === "validated_plan_not_durable_commit",
                ) &&
                    artifacts.some(
                        (a) =>
                            a.kind === "accepted_candidate_not_durable_commit",
                    ),
                "private-plan-candidate-not-durable-commit-labels",
            );
            await checkpoint("d06-private-repair");
            const committed = await repair.control("commit");
            check(committed.phase === "committed", "private-real-host-commit");
            await c.refresh();
            reply = await selected(repair.base);
            check(
                privateCapture.get().enabled === true,
                "private-head-advance-keeps-future-consent",
            );
            check(
                c
                    .get()
                    .play!.receipts.some((r) => r.request.turn === repair.turn),
                "private-separate-durable-receipt-present",
            );
            const canonical = structural(await snap());
            await privateCapture.preview();
            check(
                privateCapture.get().preview !== null,
                "private-native-preview-captured-read",
            );
            check(
                JSON.parse(privateCapture.get().preview!.text).details.identity
                    .turn === repair.turn,
                "private-native-preview-exact-selected-turn",
            );
            await checkpoint("d06-private-preview");
            await privateCapture.save(false);
            check(
                privateCapture.get().saved === null,
                "private-second-export-consent-required",
            );
            await invoke("harness_capture_case", { case: "export-cancel" });
            await privateCapture.save(true);
            check(
                privateCapture.get().saved === null &&
                    privateCapture.get().error === null,
                "private-native-picker-cancel-double",
            );
            await invoke("harness_capture_case", { case: "export-save" });
            await privateCapture.save(true);
            check(
                privateCapture.get().saved !== null,
                "private-exact-native-save",
            );
            check(
                structural(await snap()) === canonical,
                "private-read-preview-export-do-not-mutate-canon",
            );
            await checkpoint("d06-private-saved");
            c.setObserver("mira");
            check(
                privateCapture.get().reply === null &&
                    privateCapture.get().preview === null,
                "private-npc-lens-clears-immediately",
            );
            await settled();
            check(
                !document.querySelector(".private-capture"),
                "private-npc-no-detail-panel",
            );
            await checkpoint("d06-private-lens");
            c.setObserver("omniscient");
            await c.readTrace();
            await settled();
            await privateCapture.configure(true);
            await c.create();
            await lens();
            await privateCapture.configure(true);
            const agency = await stage("agency");
            check(
                agency.prepared.error === "Agency" &&
                    agency.prepared.phase === "failed",
                "private-actual-agency-rejected",
            );
            reply = await selected(agency.base);
            check(
                reply.details.artifacts.some(
                    (a) => a.kind === "parsed_proposal",
                ) &&
                    !reply.details.artifacts.some(
                        (a) =>
                            a.kind === "accepted_candidate_not_durable_commit",
                    ),
                "private-agency-proposal-without-accepted-candidate",
            );
            await checkpoint("d06-private-agency");
            const fallback = await stage("fallback");
            check(
                fallback.prepared.phase === "ready",
                "private-fallback-candidate-ready",
            );
            reply = await selected(fallback.base);
            check(
                reply.details.artifacts.some(
                    (a) =>
                        a.kind === "accepted_candidate_not_durable_commit" &&
                        (a.value as any)?.play?.fallback === true,
                ),
                "private-narrator-fallback-captured-honestly",
            );
            check(
                JSON.stringify(reply.details.artifacts).includes(
                    "Mira is healed and gains a sword.",
                ),
                "private-original-rejected-narration-retained",
            );
            await checkpoint("d06-private-fallback");
            await fallback.control("cancel");
            const pending = await stage("pending");
            const preparing = pending.control("prepare");
            let running = false;
            for (let n = 0; n < 100; n++) {
                if (
                    (await pending.control("turn_status")).phase === "running"
                ) {
                    running = true;
                    break;
                }
                await new Promise((r) => setTimeout(r, 5));
            }
            check(running, "private-actual-production-generation-running");
            await pending.control("cancel");
            const cancelled = await preparing;
            check(
                cancelled.phase === "cancelled",
                "private-actual-cancellation-terminal",
            );
            reply = await selected(pending.base);
            check(
                !reply.details.artifacts.some(
                    (a) => a.kind === "accepted_candidate_not_durable_commit",
                ),
                "private-cancel-no-invented-candidate",
            );
            await privateCapture.disable();
            check(
                privateCapture.get().reply === null &&
                    privateCapture.get().enabled === false,
                "private-explicit-revoke-clears-presentation",
            );
            await checkpoint("d06-private-cleared");
            await invoke("harness_viewport", { width: 620, height: 900 });
            await checkpoint("d06-private-narrow");
        }
        check(
            !errors
                .snapshot()
                .some((e) =>
                    ["UnhandledError", "RenderError"].includes(e.category),
                ),
            "private-no-render-or-unhandled-errors",
        );
        await checkpoint("d06-private-finished");
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
        const failedCheck = failed;
        await checkpoint("d06-private-failure").catch(() => {});
        await dispose().catch(() => {});
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                failedCheck,
                error: category(error),
                checks,
                errors: errors.snapshot(),
            },
        });
    }
}
