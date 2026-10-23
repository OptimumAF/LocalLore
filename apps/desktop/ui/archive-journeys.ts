// Fixed synthetic archive journey, actual controller/native IPC. Native picker UI is not automated.
import type { Controller } from "./controller";
import type { ArchiveController } from "./archive-controller";
import type { ErrorBuffer } from "./model";
import { structural } from "./model";
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
    config: { archiveStage?: string };
}) {
    const checks: string[] = [];
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
        document
            .querySelector(".archive-panel")
            ?.scrollIntoView({ block: "start" });
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
                archive: {
                    ...a.get(),
                    result: a.get().result?.location
                        ? {
                              ...a.get().result,
                              location: "<synthetic private archive>",
                          }
                        : a.get().result,
                },
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
        await lab();
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
            if (config.archiveStage === "import") {
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
                await capture("copy");
                a.consent(true);
                await a.confirm();
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
            await fixed("normal");
            await a.previewImport();
            a.consent(true);
            await a.confirm();
            check(
                a.get().error === "Conflict",
                "archive-same-story-conflict-never-overwrites",
            );
            await capture("failed");
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
            errors.snapshot().length === 0,
            "archive-zero-render-and-unhandled-errors",
        );
        check(
            !!document.getElementById("root")?.textContent?.trim(),
            "archive-nonempty-final-native-root",
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
