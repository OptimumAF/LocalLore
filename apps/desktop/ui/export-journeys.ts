// Explicit development-only synthetic export journeys through the real controller/native IPC.
import type { Controller } from "./controller";
import { category } from "./model";
import type { ErrorBuffer } from "./model";
import type { FaultGateway } from "./journeys";
function gate() {
    let ready!: () => void, release!: () => void;
    return {
        entered: new Promise<void>((r) => (ready = r)),
        waiting: new Promise<void>((r) => (release = r)),
        ready: () => ready(),
        release: () => release(),
    };
}
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
export async function exportJourneys({
    controller: c,
    gateway: g,
    errors,
    invoke,
    dispose,
    config,
}: Options) {
    const checks: string[] = [];
    let current = "export-startup";
    const check = (value: unknown, label: string) => {
        current = label;
        if (!value) throw new Error(label);
        checks.push(label);
    };
    const capture = async (label: string) => {
        await new Promise((r) => setTimeout(r, 100));
        const privatePaths = [
            c.get().workspace?.location,
            c.get().exports.savedLocation,
            c.get().exports.storage?.location,
        ].filter((p): p is string => !!p);
        const clean = (value: unknown, key = ""): unknown => {
            if (key === "token") return "<native-held-preview>";
            if (typeof value === "string")
                return privatePaths.reduce(
                    (text, path) =>
                        text.replaceAll(path, "<synthetic selected path>"),
                    value,
                );
            if (Array.isArray(value)) return value.map((v) => clean(v));
            if (value && typeof value === "object")
                return Object.fromEntries(
                    Object.entries(value).map(([k, v]) => [k, clean(v, k)]),
                );
            return value;
        };
        const root = document.getElementById("root")!;
        await invoke("harness_checkpoint", {
            label,
            snapshot: {
                ...(clean(c.semantic()) as object),
                synthetic: true,
                uiRevision: c.get().play?.revision ?? 0,
                checks: [...checks],
                backend: config.backend,
                dom: clean({
                    text: root.textContent?.slice(0, 64000),
                    headings: [...root.querySelectorAll("h1,h2,h3")].map(
                        (n) => n.textContent,
                    ),
                    buttons: [...root.querySelectorAll("button")].map((n) => ({
                        name: n.textContent,
                        disabled: n.disabled,
                    })),
                    injectedElements: root.querySelectorAll(
                        ".export-open img,.export-open script,.export-open iframe,.export-open a",
                    ).length,
                    horizontalOverflow:
                        document.documentElement.scrollWidth > innerWidth + 2,
                    viewport: { width: innerWidth, height: innerHeight },
                }),
            },
        });
    };
    const finish = async () => {
        await capture("export-finished");
        await dispose();
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
        await c.start();
        check(!!c.get().workspace, "export-real-durable-workspace");
        if (config.stage === "restart") {
            const saved = c
                .get()
                .workspace!.stories.find((s) => s.revision > 0);
            check(saved, "export-restart-library-retained");
            await c.resume(saved!.scope);
            const before = c.get().play!.revision;
            check(
                !Object.hasOwn(c.get().play!.inventory, "potion"),
                "export-restart-spent-potion-retained",
            );
            await c.loadExport();
            check(
                c.get().exports.imported && !!c.get().exports.preview,
                "native-picker-bound-existing-snapshot-reopened-after-process-restart",
            );
            check(
                c.get().exports.preview!.manifest.revision === before,
                "reopened-snapshot-identifies-same-canonical-head",
            );
            c.selectExportFile("transcript.jsonl");
            await c.openExport();
            check(
                c
                    .get()
                    .exports.opened?.text.includes("PRIVATE_SYNTHETIC_CANARY"),
                "private-saved-transcript-reopened-read-only",
            );
            await c.refresh();
            check(
                c.get().play!.revision === before,
                "open-existing-snapshot-never-mutates-canon",
            );
            await capture("export-restarted");
            await finish();
            return;
        }
        await c.send();
        check(
            c.get().turnStatus?.phase === "committed",
            "export-last-potion-committed",
        );
        c.setAction("dialogue");
        c.setDraft("PRIVATE_SYNTHETIC_CANARY <img src=x onerror=alert(1)>");
        await c.send();
        check(
            c.get().play!.receipts.length === 2,
            "export-private-synthetic-story-created",
        );
        c.showExports();
        check(
            c.get().exports.mode === "diagnostics",
            "export-default-is-structural-diagnostics",
        );
        await c.previewExport();
        check(
            c.get().exports.preview?.manifest.mode === "diagnostics",
            "export-diagnostics-captured-native-head",
        );
        check(
            c
                .get()
                .exports.preview!.files.map((f) => f.path)
                .sort()
                .join(",") === "diagnostics.json,manifest.json",
            "diagnostics-has-no-story-state-files",
        );
        await capture("export-diagnostics-preview");
        g.forgeExportSave = true;
        await c.saveExport();
        check(
            !!c.get().exports.savedLocation,
            "native-destination-save-publishes-exact-preview",
        );
        await c.openExport();
        check(
            JSON.parse(c.get().exports.opened!.text).mode === "diagnostics",
            "renderer-mode-and-file-forgery-cannot-change-native-held-bundle",
        );
        c.selectExportFile("diagnostics.json");
        await c.openExport();
        check(
            !c.get().exports.opened!.text.includes("PRIVATE_SYNTHETIC_CANARY"),
            "diagnostics-excludes-private-story-canary",
        );
        await capture("export-diagnostics-saved");
        c.setExportMode("player");
        c.setAction("wait");
        c.setFakeMode("delayed");
        const pending = gate();
        g.heldPrepare = pending;
        const generating = c.send();
        await pending.entered;
        await c.previewExport();
        const head = c.get().exports.preview!.manifest.revision;
        pending.release();
        await generating;
        check(
            c.get().play!.revision > head,
            "play-advanced-after-inspection-capture",
        );
        await c.saveExport();
        c.selectExportFile("state.json");
        await c.openExport();
        check(
            c.get().exports.preview!.manifest.revision === head &&
                JSON.parse(c.get().exports.opened!.text).source_revision ===
                    head,
            "export-snapshot-independent-of-later-turn",
        );
        await capture("export-player-preview");
        c.setView("lab");
        c.setExportMode("full");
        await c.previewExport();
        check(
            c.get().exports.preview?.manifest.mode === "full",
            "private-full-preview-requires-explicit-mode",
        );
        await capture("export-full-preview");
        const held = gate();
        g.heldExportCancel = held;
        c.setView("play");
        check(
            c.get().exports.mode === "diagnostics" &&
                c.get().exports.preview === null,
            "full-preview-cleared-before-delayed-native-cancel-in-play",
        );
        await held.entered;
        held.release();
        await c.previewExport();
        await invoke("harness_export_case", { case: "cancel" });
        await c.saveExport();
        check(
            !c.get().exports.savedLocation && !c.get().exports.error,
            "native-folder-cancel-keeps-preview-and-canon",
        );
        await capture("export-cancelled");
        const originalRevision = c.get().play!.revision;
        for (const [scenario, expected] of [
            ["unwritable", "UnsafeDestination"],
            ["hostile", "UnsafeDestination"],
            ["disk-full", "Full"],
            ["collision", "ExportExists"],
        ]) {
            await c.cancelExport();
            await c.previewExport();
            await invoke("harness_export_case", { case: scenario });
            await c.saveExport();
            check(
                c.get().exports.error === expected,
                `export-${scenario}-refuses-publication`,
            );
            await c.refresh();
            check(
                c.get().play!.revision === originalRevision,
                `export-${scenario}-leaves-canon-unchanged`,
            );
        }
        await capture("export-faults");
        await c.cancelExport();
        const heldPreview = gate();
        g.heldExportPreview = heldPreview;
        const late = c.previewExport();
        await heldPreview.entered;
        const originalScope = c.selected()!.scope;
        await c.create();
        heldPreview.release();
        await late;
        check(
            c.get().exports.preview === null,
            "late-export-preview-cannot-cross-story-selection",
        );
        await capture("export-stale");
        await c.resume(originalScope);
        c.setView("lab");
        c.setExportMode("database");
        await c.previewExport();
        check(
            c.get().exports.preview?.manifest.mode === "database" &&
                c
                    .get()
                    .exports.preview!.files.some(
                        (f) => f.path === "stories-snapshot.sqlite",
                    ),
            "explicit-private-all-stories-sqlite-copy-preview",
        );
        await c.saveExport();
        check(
            !!c.get().exports.savedLocation,
            "consistent-sqlite-copy-published-separately",
        );
        await capture("export-database");
        c.setExportMode("full");
        await c.previewExport();
        await c.saveExport();
        await c.loadExport();
        check(
            c.get().exports.imported,
            "existing-local-snapshot-is-always-labeled-untrusted",
        );
        c.selectExportFile("transcript.jsonl");
        await c.openExport();
        check(
            c.get().exports.opened!.text.includes("PRIVATE_SYNTHETIC_CANARY"),
            "private-export-retains-explicit-story-content",
        );
        check(
            document.querySelectorAll(
                ".export-open img,.export-open script,.export-open iframe,.export-open a",
            ).length === 0,
            "opened-inspection-text-is-inert",
        );
        await c.refresh();
        check(
            c.get().play!.revision === originalRevision,
            "read-only-open-and-database-copy-have-no-canonical-effects",
        );
        await capture("export-open-readonly");
        await c.revealStorage();
        check(
            c.get().exports.storage?.location.endsWith("stories-v1.sqlite"),
            "reveal-storage-returns-only-app-owned-metadata",
        );
        await capture("export-storage");
        await invoke("harness_viewport", { preset: "narrow" });
        c.layout(1, 1, 150);
        await capture("export-narrow");
        await finish();
    } catch (error) {
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                backend: config.backend,
                stage: config.stage,
                failedCheck: current,
                error: category(error),
                checks,
                errors: errors.snapshot(),
            },
        });
    }
}
