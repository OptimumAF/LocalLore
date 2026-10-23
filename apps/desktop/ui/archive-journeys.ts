// Fixed synthetic archive journey, actual controller/native IPC. Native picker UI is not automated.
import type { Controller } from "./controller";
import type { ArchiveController } from "./archive-controller";
import type { ErrorBuffer } from "./model";
import { structural, IpcGateway } from "./model";
export async function archiveJourneys({
    controller: c,
    archive: a,
    invoke,
    dispose,
    errors,
    config,
}: {
    controller: Controller;
    archive: ArchiveController;
    invoke: (name: string, args?: Record<string, unknown>) => Promise<unknown>;
    dispose: () => Promise<void>;
    errors: ErrorBuffer;
    config: { archiveStage?: string; stage?: string };
}) {
    const checks: string[] = [];
    const gateway = new IpcGateway(invoke, errors);
    let omittedWorkflowKey: string | undefined;
    let failedCheck = "archive-start";
    const check = (v: unknown, id: string) => {
        failedCheck = id;
        if (!v) throw Error(id);
        checks.push(id);
    };
    const lab = async () => {
        c.requestLab();
        c.acknowledgeLab(true);
        await new Promise((r) => setTimeout(r, 60));
        a.show();
    };
    const fixed = (scenario: string) =>
        invoke("harness_archive_case", { scenario });
    const capture = async (label: string) => {
        await new Promise((r) => setTimeout(r, 100));
        if (label === "finished") window.scrollTo({ top: 0 });
        else
            document
                .querySelector(
                    label === "copy" || label === "narrow"
                        ? ".archive-preview"
                        : label === "failed"
                          ? ".archive-panel [role=alert]"
                          : label === "receipt"
                            ? ".archive-panel .storage-path"
                            : ".archive-panel",
                )
                ?.scrollIntoView({
                    block: label === "failed" ? "center" : "start",
                });
        for (const n of document.querySelectorAll(
            ".archive-panel .storage-path",
        ))
            n.textContent = "<synthetic private archive>";
        check(
            !!document.getElementById("root")?.textContent?.trim(),
            `${label}-nonempty-native-render`,
        );
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            `${label}-no-horizontal-overflow`,
        );
        await invoke("harness_checkpoint", {
            label,
            snapshot: {
                synthetic: true,
                uiRevision: c.get().play?.revision,
                checks: [...checks],
                stage: config.archiveStage,
                omittedWorkflowKey,
                archive: JSON.parse(
                    JSON.stringify(a.get()).replaceAll(
                        a.get().result?.location ?? "<no-location>",
                        "<synthetic private archive>",
                    ),
                ),
                play: c.get().play,
                dom: {
                    text: document.querySelector(".archive-panel")?.textContent,
                    horizontalOverflow:
                        document.documentElement.scrollWidth > innerWidth + 2,
                },
            },
        });
    };
    try {
        await c.start();
        check(c.get().workspace?.persistent, "d08-native-durable-workspace");
        const catalog = (await invoke("archive_catalog")) as {
            version: number;
            archive_version: number;
            privacy: string;
            caps: { bytes: number; tokens: number; workers: number };
        };
        check(
            catalog.version === 1 &&
                catalog.archive_version === 1 &&
                catalog.privacy === "full_private" &&
                catalog.caps.bytes === 32 * 1024 * 1024 &&
                catalog.caps.tokens === 2 &&
                catalog.caps.workers === 1,
            "archive-fixed-native-capability-catalog",
        );
        await lab();
        if (config.archiveStage === "retire") {
            const before = structural(c.get().play);
            const library = await c.library();
            if (config.stage === "reopened") {
                check(
                    library.stories.length === 1,
                    "archive-window-retirement-cancelled-before-destination-import",
                );
                check(
                    a.get().status === null && a.get().preview === null,
                    "archive-reopened-window-has-no-old-preview-or-operation",
                );
                await fixed("release-import");
                await capture("reopened");
                await fixed("normal");
                await a.previewImport();
                a.consent(true);
                await a.confirm();
                check(
                    a.get().result?.status === "imported",
                    "archive-fresh-window-can-confirm-new-import-after-drain",
                );
                check(
                    structural(c.get().play) === before,
                    "archive-reopened-import-keeps-current-player-canon",
                );
                check(
                    errors.snapshot().length === 0,
                    "archive-retirement-zero-render-errors",
                );
                await capture("finished");
                await dispose();
                await invoke("harness_finish", {
                    report: {
                        synthetic: true,
                        passed: true,
                        checks,
                        stage: config.archiveStage,
                        errors: errors.snapshot(),
                    },
                });
                return;
            }
            await fixed("normal");
            await a.previewImport();
            a.consent(true);
            await fixed("hold-import");
            void a.confirm();
            while (a.get().status?.phase !== "importing")
                await new Promise((r) => setTimeout(r, 5));
            await capture("pending");
            await invoke("harness_reopen");
            return;
        }
        if (config.archiveStage === "source") {
            c.setAction("give");
            await c.send();
            check(c.get().play?.revision === 1, "archive-source-accepted-gift");
            c.setAction("dialogue");
            c.setDraft("ARCHIVE_SECRET_MIRA_ONLY");
            await c.send();
            check(
                c.get().play?.revision === 2,
                "archive-source-accepted-private-dialogue",
            );
            c.setAction("wait");
            c.setFakeMode("delayed");
            const pending = c.send();
            while (!c.get().pending) await new Promise((r) => setTimeout(r, 5));
            omittedWorkflowKey = c.get().pending!.turn;
            await c.cancel();
            await pending;
            c.setFakeMode("accepted");
            check(
                c.get().play?.revision === 2 &&
                    c.get().turnStatus?.phase === "cancelled",
                "archive-source-noncommitted-workflow-remains-outside-history",
            );
            for (const scenario of [
                "cancel",
                "unwritable",
                "disk-full",
                "collision",
            ]) {
                await a.previewExport(c.selected()!.id, c.selected()!.scope, 2);
                a.consent(true);
                await fixed(scenario);
                await a.confirm();
                check(
                    scenario === "cancel"
                        ? a.get().result?.status === "cancelled"
                        : !!a.get().error,
                    `archive-export-${scenario}-no-publication`,
                );
            }
            await a.previewExport(
                c.selected()!.id,
                c.selected()!.scope,
                c.get().play!.revision,
            );
            check(
                a.get().preview?.kind === "export" &&
                    a.get().preview?.preview.committed_turns === 2,
                "archive-coherent-private-export-preview",
            );
            await capture("initial");
            await invoke("harness_viewport", { preset: "narrow" });
            await capture("narrow");
            await invoke("harness_viewport", { preset: "wide" });
            a.consent(true);
            await fixed("normal");
            await a.confirm();
            check(
                a.get().result?.status === "exported",
                "archive-exact-private-file-published",
            );
            await capture("receipt");
        } else {
            const before = structural(c.get().play);
            if (
                config.archiveStage === "import" ||
                config.archiveStage === "uncertain"
            ) {
                for (const scenario of [
                    "cancel",
                    "corrupt",
                    "future",
                    "oversize",
                ]) {
                    await fixed(scenario);
                    await a.previewImport();
                    check(
                        scenario === "cancel"
                            ? a.get().result?.status === "cancelled"
                            : !!a.get().error,
                        `archive-${scenario}-refused-before-import`,
                    );
                    check(
                        structural(c.get().play) === before,
                        `archive-${scenario}-keeps-player-canon`,
                    );
                }
                await fixed("normal");
                await a.previewImport();
                check(
                    a.get().preview?.kind === "import",
                    "archive-hostile-file-validated-before-consent",
                );
                const captured = a.get().preview!.preview;
                await capture("copy");
                let consentDenied = false;
                try {
                    await invoke("archive_import", {
                        token: a.get().preview!.token,
                        consent: false,
                    });
                } catch (e) {
                    consentDenied = String(e) === "ArchiveConsentRequired";
                }
                check(
                    consentDenied,
                    "archive-native-requires-explicit-confirmation",
                );
                a.consent(true);
                await fixed("hold-import");
                const cancelled = a.confirm();
                while (a.get().status?.phase !== "importing" && a.get().busy)
                    await new Promise((r) => setTimeout(r, 5));
                check(
                    a.get().busy &&
                        a.get().status?.running &&
                        a.get().status?.phase === "importing",
                    "archive-pending-snapshot-is-actual-running-import",
                );
                await capture("pending");
                await a.cancel();
                await cancelled;
                await fixed("release-import");
                check(
                    a.get().error === "Cancelled",
                    "archive-cancel-after-staging-keeps-destination-untouched",
                );
                check(
                    (await c.library()).stories.length === 1,
                    "archive-cancel-preserves-existing-saved-library",
                );
                await fixed("normal");
                await a.previewImport();
                a.consent(true);
                if (config.archiveStage === "uncertain")
                    await fixed("drop-import-ack");
                await a.confirm();
                if (config.archiveStage === "uncertain") {
                    check(
                        a.get().error === "ArchiveAcknowledgementUnavailable",
                        "archive-lost-ack-is-not-false-import-success",
                    );
                    await capture("failed");
                    const library = await c.library();
                    check(
                        library.stories.some(
                            (s) => s.scope.story === captured.story_id,
                        ),
                        "archive-explicit-library-refresh-recovers-committed-identity",
                    );
                    await c.resume({
                        story: captured.story_id,
                        branch: captured.root_branch,
                    });
                    await lab();
                } else {
                    check(
                        a.get().result?.status === "imported" &&
                            a.get().result?.staging_cleanup_complete === true,
                        "archive-isolated-staging-and-destination-import",
                    );
                    check(
                        structural(c.get().play) === before,
                        "archive-import-does-not-auto-open-or-mutate-current-story",
                    );
                    const root = a.get().result!.root!;
                    await c.resume(root);
                    await lab();
                }
                await c.refreshModel();
                check(
                    c.get().model?.loaded === false,
                    "archive-import-never-loads-a-referenced-model",
                );
            } else {
                const library = await c.library();
                if (!library.persistent) throw Error("ExpectedLibrary");
                const imported = library.stories.find((x) => x.revision === 2);
                if (!imported) throw Error("MissingImportedStory");
                await c.resume(imported.scope);
                await lab();
            }
            check(
                c.get().play?.revision === 2 &&
                    c.get().play?.receipts.length === 2,
                "archive-reopen-retains-original-accepted-receipts",
            );
            const receipt = c.get().play!.receipts[0],
                session = c.selected()!;
            const retry = (await gateway.call({
                op: "submit",
                session: session.id,
                request: receipt.request,
                mode: "accepted",
            })) as { phase: string; receipt: unknown };
            check(
                retry.phase === "committed" &&
                    JSON.stringify(retry.receipt) === JSON.stringify(receipt),
                "archive-exact-committed-key-retry-returns-original-receipt",
            );
            await c.refresh();
            check(
                c.get().play?.revision === 2,
                "archive-explicit-committed-retry-has-no-duplicate-effect",
            );
            const own = JSON.stringify(c.get().play);
            check(
                own.includes("ARCHIVE_SECRET_MIRA_ONLY"),
                "archive-player-retains-transcript",
            );
            c.setObserver("mira");
            await c.inspect();
            check(
                JSON.stringify(c.get().inspection).includes(
                    "ARCHIVE_SECRET_MIRA_ONLY",
                ),
                "archive-mira-preserves-directed-secret",
            );
            c.setObserver("sable");
            await c.inspect();
            check(
                !JSON.stringify(c.get().inspection).includes(
                    "ARCHIVE_SECRET_MIRA_ONLY",
                ),
                "archive-sable-cannot-see-private-dialogue",
            );
            c.setObserver("player");
            await c.inspect();
            a.show();
            if (config.archiveStage === "import") {
                await a.previewExport(c.selected()!.id, c.selected()!.scope, 2);
                a.consent(true);
                await fixed("normal");
                await a.confirm();
                check(
                    a.get().result?.status === "exported",
                    "archive-reexport-reads-actual-imported-store",
                );
            }
            await fixed("normal");
            await a.previewImport();
            a.consent(true);
            await a.confirm();
            check(
                a.get().error === "Conflict",
                "archive-same-story-conflict-never-overwrites",
            );
            if (config.archiveStage !== "uncertain") await capture("failed");
            if (config.archiveStage === "restarted") {
                c.returnToPlay();
                c.setAction("wait");
                await c.send();
                check(
                    c.get().play?.revision === 3,
                    "archive-continues-after-real-restart-without-inference",
                );
            }
        }
        check(
            errors
                .snapshot()
                .every(
                    (e) => e.source === "native" && e.category === "Cancelled",
                ),
            "archive-zero-render-and-unhandled-errors",
        );
        check(
            // Cancelling before admission skips Prepare, so it need not emit
            // a native Cancelled error. Keep the category whitelist and bound.
            config.archiveStage !== "source" || errors.snapshot().length <= 2,
            "archive-cancellation-native-error-count-bounded",
        );
        check(
            !!document.getElementById("root")?.textContent?.trim(),
            "archive-nonempty-final-native-root",
        );
        c.returnToPlay();
        await new Promise((r) => setTimeout(r, 60));
        check(
            !a.get().shown && a.get().preview === null,
            "archive-return-to-play-revokes-private-preview",
        );
        await capture("finished");
        await dispose();
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                checks,
                stage: config.archiveStage,
                errors: errors.snapshot(),
                omittedWorkflowKey,
            },
        });
    } catch {
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                failedCheck,
                checks,
                error: a.get().error,
                stage: config.archiveStage,
                errors: errors.snapshot(),
            },
        });
    }
}
