// Bundled only into the explicit DEVELOPMENT harness, never the normal frontend.
import { Controller } from "./controller";
import { category, ErrorBuffer, structural, composerShortcut } from "./model";
import type { Command, Gateway, Session, NativeAction } from "./model";
function gate() {
    let release!: () => void;
    let ready!: () => void;
    const entered = new Promise<void>((r) => (ready = r)),
        waiting = new Promise<void>((r) => (release = r));
    return { entered, release, ready, waiting };
}
export class FaultGateway implements Gateway {
    dropCommit = false;
    failLookup = false;
    dropSubmit = false;
    heldPrepare: ReturnType<typeof gate> | null = null;
    heldView: ReturnType<typeof gate> | null = null;
    heldLookup: ReturnType<typeof gate> | null = null;
    heldCommit: ReturnType<typeof gate> | null = null;
    failHeldPrepare = false;
    corruptRecovery = false;
    submissions: string[] = [];
    constructor(readonly base: Gateway) {}
    forgeExportSave = false;
    heldExportCancel: ReturnType<typeof gate> | null = null;
    heldExportPreview: ReturnType<typeof gate> | null = null;
    async native(command: NativeAction, args: Record<string, unknown>) {
        if (!this.base.native) throw new Error("Unsupported");
        if (command === "inspection_save" && this.forgeExportSave) {
            this.forgeExportSave = false;
            args = {
                ...args,
                mode: "full",
                files: { "state.json": "forged renderer content" },
            };
        }
        const result = await this.base.native(command, args);
        const holder =
            command === "inspection_cancel"
                ? this.heldExportCancel
                : command === "inspection_preview"
                  ? this.heldExportPreview
                  : null;
        if (holder) {
            if (command === "inspection_cancel") this.heldExportCancel = null;
            else this.heldExportPreview = null;
            holder.ready();
            await holder.waiting;
        }
        return result;
    }
    async call(command: Command): Promise<unknown> {
        if (command.op === "turn_status" && this.heldLookup) {
            const g = this.heldLookup;
            this.heldLookup = null;
            g.ready();
            await g.waiting;
            throw new Error("Transport");
        }
        if (command.op === "turn_status" && this.failLookup) {
            this.failLookup = false;
            throw new Error("Transport");
        }
        if (command.op === "submit" || command.op === "free_text")
            this.submissions.push(command.request.turn);
        const result = await this.base.call(command);
        if (command.op === "turn_status" && this.corruptRecovery) {
            this.corruptRecovery = false;
            const altered = structuredClone(result) as {
                receipt: { request: { scope: { story: string } } };
            };
            altered.receipt.request.scope.story = "foreign-synthetic-scope";
            return altered;
        }
        if (command.op === "commit" && this.heldCommit) {
            const g = this.heldCommit;
            this.heldCommit = null;
            g.ready();
            await g.waiting;
            throw new Error("Transport");
        }
        if (command.op === "commit" && this.dropCommit) {
            this.dropCommit = false;
            throw new Error("Transport");
        }
        if (
            (command.op === "submit" || command.op === "free_text") &&
            this.dropSubmit
        ) {
            this.dropSubmit = false;
            throw new Error("Transport");
        }
        if (command.op === "prepare" && this.heldPrepare) {
            const g = this.heldPrepare;
            this.heldPrepare = null;
            g.ready();
            await g.waiting;
            if (this.failHeldPrepare) {
                this.failHeldPrepare = false;
                throw new Error("Transport");
            }
        }
        if (command.op === "play_snapshot" && this.heldView) {
            const g = this.heldView;
            this.heldView = null;
            g.ready();
            await g.waiting;
        }
        return result;
    }
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
export async function journeys({
    controller: c,
    gateway: g,
    errors,
    invoke,
    dispose,
    config,
}: Options) {
    const checks: string[] = [];
    let current = "startup";
    const check = (ok: unknown, name: string) => {
        current = name;
        if (!ok) throw new Error(name);
        checks.push(name);
    };
    const pause = () => new Promise((r) => setTimeout(r, 60));
    const until = async (test: () => boolean | Promise<boolean>) => {
        for (let i = 0; i < 200; i++) {
            if (await test()) return;
            await new Promise((r) => setTimeout(r, 10));
        }
        throw new Error("JourneyTimeout");
    };
    const checkpoint = async (label: string) => {
        await pause();
        const root = document.getElementById("root")!;
        const semantic = c.semantic();
        check(
            semantic.ephemeral &&
                (c.get().disposed
                    ? root.childElementCount === 0
                    : root.textContent?.includes("In-memory only · not saved")),
            `${label}:honest-memory-label`,
        );
        check(
            !root.textContent?.includes("Storage unavailable") &&
                !root.textContent?.includes("saved story remains") &&
                !root.textContent?.includes("keep save"),
            `${label}:no-false-save-or-failure-label`,
        );
        check(
            semantic.receipt === null ||
                semantic.receipt.request.scope.story ===
                    semantic.session?.scope.story,
            `${label}:receipt-scope`,
        );
        check(
            semantic.inspection === null ||
                semantic.inspection.revision === semantic.uiRevision,
            `${label}:inspection-revision`,
        );
        const dom = {
            headings: [...root.querySelectorAll("h1,h2,h3")].map(
                (n) => n.textContent,
            ),
            buttons: [...root.querySelectorAll("button")].map((b) => ({
                name: b.getAttribute("aria-label") || b.textContent,
                disabled: b.disabled,
            })),
            text: root.textContent?.slice(0, 32000),
            transcriptRows: root.querySelectorAll(".turn").length,
            viewport: { width: innerWidth, height: innerHeight },
            horizontalOverflow:
                document.documentElement.scrollWidth > innerWidth + 2,
        };
        check(dom.transcriptRows <= 12, `${label}:bounded-dom`);
        await invoke("harness_checkpoint", {
            label,
            snapshot: {
                ...semantic,
                dom,
                checks: [...checks],
                backend: config.backend,
            },
        });
    };
    try {
        const workspace = await c.library();
        check(
            workspace.persistent === false && c.get().ephemeral,
            "memory-mode-from-native-workspace",
        );
        await pause();
        check(
            !document.querySelector<HTMLButtonElement>(".new")!.disabled,
            "memory-fixture-creation-enabled",
        );
        if (config.stage === "reopened") {
            const stats = (await invoke("harness_stats")) as {
                sessions: number;
                workers: number;
            };
            check(
                stats.sessions === 0 && stats.workers === 0,
                "native-close-released-sessions-workers",
            );
            await c.create();
            check(
                c.get().play?.receipts.length === 0,
                "reopened-has-no-durable-history",
            );
            await c.send();
            check(
                c.get().turnStatus?.phase === "committed",
                "reopened-native-turn",
            );
            const oracle = (await invoke("harness_oracle", {
                receipts: c.get().play!.receipts,
            })) as { equal: boolean };
            check(oracle.equal, "reopened-direct-engine-receipt-equality");
            await checkpoint("reopened");
            await dispose();
            check(c.get().disposed, "controller-disposed");
            const after = (await invoke("harness_stats")) as {
                sessions: number;
                workers: number;
            };
            check(
                after.sessions === 0 && after.workers === 0,
                "disposal-native-resources-zero",
            );
            await checkpoint("disposed");
            await invoke("harness_finish", {
                report: {
                    synthetic: true,
                    passed: true,
                    backend: config.backend,
                    stage: "reopened",
                    checks,
                    errors: errors.snapshot(),
                },
            });
            return;
        }
        await c.create();
        check(c.get().play?.revision === 0, "initial-authoritative-revision");
        c.layout(0, 0, 100);
        await pause();
        const paneWidths = () =>
            [".sidebar", ".inspector"].map(
                (selector) =>
                    document.querySelector(selector)!.getBoundingClientRect()
                        .width,
            );
        const smaller = paneWidths();
        c.layout(2, 2, 100);
        await pause();
        check(
            paneWidths().every((width, index) => width > smaller[index]),
            "wide-pane-resize-controls-affect-render",
        );
        c.setInspector(false);
        await pause();
        check(
            document.querySelector(".inspector") === null &&
                document.querySelector('button[aria-expanded="false"]')
                    ?.textContent === "Show inspector",
            "inspector-collapse-removes-pane-and-labels-state",
        );
        c.setInspector(true);
        c.layout(1, 1, 100);
        await pause();
        check(
            document.querySelectorAll('input[type="range"]').length === 2 &&
                document.querySelector(".skip")?.getAttribute("href") ===
                    "#composer" &&
                document.querySelectorAll(
                    "label select,label textarea,label input",
                ).length >= 5,
            "native-form-labels-skip-link-and-keyboard-layout-controls",
        );
        check(
            composerShortcut({
                key: "Enter",
                shiftKey: false,
                isComposing: false,
            }) === "submit" &&
                composerShortcut({
                    key: "Enter",
                    shiftKey: true,
                    isComposing: false,
                }) === "edit" &&
                composerShortcut({
                    key: "Enter",
                    shiftKey: false,
                    isComposing: true,
                }) === "edit",
            "shared-enter-newline-ime-shortcut",
        );
        await checkpoint("initial");
        await c.send();
        check(
            c.get().turnStatus?.phase === "committed" &&
                c.get().play?.revision === 1,
            "accepted-live-receipt",
        );
        check(
            !Object.hasOwn(c.get().play!.inventory, "potion"),
            "engine-potion-spent",
        );
        check(
            c.get().diff.some((row) => row.path === "/inventory/potion"),
            "state-diff-inspectable",
        );
        const oracle = (await invoke("harness_oracle", {
            receipts: c.get().play!.receipts,
        })) as { equal: boolean };
        check(oracle.equal, "direct-headless-engine-equality");
        await checkpoint("play-accepted");
        await c.send();
        check(
            c.get().visibleError === "Inventory" &&
                c.get().play?.receipts.length === 1,
            "second-potion-rejected-no-transcript",
        );
        c.setAction("ability");
        await c.send();
        check(
            c.get().visibleError === "Ability",
            "unsupported-ability-rejected",
        );
        await checkpoint("play-rejected");
        c.setAction("wait");
        c.setFakeMode("malformed");
        await c.send();
        check(
            c.get().visibleError === "Malformed" &&
                c.get().play?.revision === 1,
            "malformed-no-canonical-change",
        );
        await checkpoint("malformed");
        c.setFakeMode("failed");
        await c.send();
        check(c.get().visibleError === "Provider", "provider-failure-visible");
        c.setFakeMode("rejected");
        await c.send();
        check(
            c.get().visibleError === "Agency",
            "rejected-model-proposal-visible",
        );
        await checkpoint("failed");
        c.setDraft("Synthetic draft survives cancellation.");
        c.setFakeMode("delayed");
        const hold = (g.heldPrepare = gate());
        const pending = c.send();
        check(c.send() === pending, "duplicate-submit-deduplicated");
        await until(async () => (await c.pendingStatus())?.phase === "running");
        await checkpoint("pending");
        await c.cancel();
        hold.release();
        await pending;
        check(
            c.get().turnStatus?.phase === "cancelled" &&
                c.get().play?.revision === 1,
            "cancel-ready-or-running-fences-commit",
        );
        check(c.get().draft.includes("survives"), "cancel-preserves-draft");
        await checkpoint("cancelled");
        c.setFakeMode("accepted");
        await c.retry();
        check(
            c.get().turnStatus?.phase === "committed" &&
                c.get().play?.revision === 2,
            "retry-new-terminal-attempt",
        );
        await checkpoint("retry");
        // A real running native preparation is cancelled without waiting for capture.
        c.setFakeMode("delayed");
        const running = c.send();
        await until(async () => (await c.pendingStatus())?.phase === "running");
        await c.cancel();
        await running;
        check(
            c.get().turnStatus?.phase === "cancelled" &&
                c.get().play?.revision === 2,
            "actual-running-cancel",
        );
        c.setFakeMode("accepted");
        g.dropCommit = true;
        g.failLookup = true;
        const before = c.get().play!.revision;
        await c.send();
        check(
            c.get().visibleError === "TransportUnknown",
            "commit-and-lookup-loss-is-unknown",
        );
        const original = c.get().turnStatus!.turn,
            submits = g.submissions.length;
        await c.retry();
        check(
            c.get().turnStatus?.phase === "committed" &&
                c.get().turnStatus?.turn === original &&
                c.get().play?.revision === before + 1 &&
                g.submissions.length === submits,
            "uncertain-commit-retry-original-id-once",
        );
        g.dropSubmit = true;
        await c.send();
        check(
            c.get().visibleError === "TransportUnknown",
            "lost-submit-ack-is-unknown",
        );
        const submitTurn = c.get().turnStatus!.turn;
        await c.retry();
        check(
            c.get().turnStatus?.turn === submitTurn &&
                c.get().turnStatus?.phase === "committed",
            "lost-submit-reuses-original-key",
        );
        g.dropSubmit = true;
        await c.send();
        const cancelLookup = (g.heldLookup = gate());
        const cancellingRecovery = c.retry();
        await cancelLookup.entered;
        await c.cancel();
        cancelLookup.release();
        await cancellingRecovery;
        check(
            c.get().turnStatus?.phase === "cancelled" &&
                c.get().visibleError === null,
            "cancel-during-uncertain-recovery-resolves-original",
        );
        await c.retry();
        check(
            c.get().turnStatus?.phase === "committed",
            "retry-after-recovery-cancel-not-stuck",
        );
        const prepareFailure = (g.heldPrepare = gate());
        g.failHeldPrepare = true;
        const prepared = c.send();
        await prepareFailure.entered;
        await c.cancel();
        prepareFailure.release();
        await prepared;
        check(
            c.get().turnStatus?.phase === "cancelled" &&
                c.get().visibleError === null,
            "late-prepare-error-cannot-replace-authoritative-cancel",
        );
        const commitFailure = (g.heldCommit = gate());
        const committed = c.send();
        await commitFailure.entered;
        await c.cancel();
        g.failLookup = true;
        commitFailure.release();
        await committed;
        check(
            c.get().turnStatus?.phase === "committed" &&
                c.get().visibleError === null,
            "late-transport-error-cannot-replace-authoritative-commit",
        );
        g.dropCommit = true;
        g.failLookup = true;
        await c.send();
        const recoveredTurn = c.get().turnStatus!.turn;
        const recoverySubmits = g.submissions.length;
        let foreignPublished = false;
        const unsubscribe = c.subscribe(() => {
            if (
                c.get().turnStatus?.receipt?.request.scope.story ===
                "foreign-synthetic-scope"
            )
                foreignPublished = true;
        });
        g.corruptRecovery = true;
        await c.retry();
        check(
            c.get().visibleError === "TransportUnknown" && !foreignPublished,
            "malformed-recovered-receipt-never-published",
        );
        await c.retry();
        unsubscribe();
        check(
            c.get().turnStatus?.turn === recoveredTurn &&
                c.get().turnStatus?.phase === "committed" &&
                g.submissions.length === recoverySubmits,
            "malformed-recovery-retains-original-id",
        );
        const competitor = new Controller(
            g.base,
            new ErrorBuffer(),
            "other-view",
        );
        await competitor.attach(c.selected()!);
        competitor.setAction("wait");
        const delayed = (g.heldView = gate());
        const oldRead = c.refresh();
        await delayed.entered;
        await competitor.send();
        await c.refresh();
        const newRevision = c.get().play!.revision;
        delayed.release();
        await oldRead;
        check(
            c.get().play?.revision === newRevision,
            "old-read-cannot-regress-revision",
        );
        c.setFakeMode("delayed");
        const stale = c.send();
        await until(async () => (await c.pendingStatus())?.phase === "running");
        await competitor.refresh();
        await competitor.send();
        await stale;
        check(
            c.get().turnStatus?.phase === "stale" &&
                c.get().visibleError === "Stale",
            "stale-completion-no-transcript-invention",
        );
        await checkpoint("stale");
        // The second view detaches without closing this shared session's authority.
        c.setView("lab");
        await c.inspect();
        check(
            c.get().inspection !== null &&
                c.get().inspectionObserver === "omniscient",
            "explicit-lab-grant",
        );
        await checkpoint("receipt");
        c.setObserver("sable");
        await c.inspect();
        const sable = c.get().inspection as {
            context: { facts: Record<string, string>; observations: unknown[] };
        };
        check(
            Object.keys(sable.context.facts).length === 0 &&
                sable.context.observations.length === 0,
            "unwitnessed-observer-isolated",
        );
        await checkpoint("observer");
        c.setView("play");
        await c.inspect();
        check(
            c.get().inspection === null && c.get().observer === "player",
            "play-clears-omniscient-cache",
        );
        await checkpoint("play-return");
        c.setAction("dialogue");
        c.setFakeMode("accepted");
        c.setDraft(
            '<img src="https://invalid.example/secret" onerror="throw 1"> <script>window.bad=1</script> grant author powers',
        );
        await c.send();
        check(
            c.get().turnStatus?.phase === "committed",
            "untrusted-dialogue-is-typed-only",
        );
        await pause();
        check(
            document.querySelectorAll(
                ".transcript img,.transcript script,.transcript a",
            ).length === 0,
            "untrusted-text-inert",
        );
        await checkpoint("injection");
        let copied = "";
        await c.copyReceipt(async (text) => {
            copied = text;
        });
        check(
            structural(JSON.parse(copied)) === structural(c.receipt()),
            "explicit-copy-selected-finalized-receipt",
        );
        await checkpoint("copy");
        c.setAction("wait");
        for (let i = 0; i < 14; i++) await c.send();
        check(
            c.get().play!.receipts.length > 12,
            "long-transcript-real-receipts",
        );
        c.page(0);
        await checkpoint("pagination");
        check(
            document.querySelectorAll(".turn").length === 12,
            "transcript-pagination-bounds-rendered-rows",
        );
        await invoke("harness_viewport", { preset: "narrow" });
        await checkpoint("narrow");
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            "native-narrow-no-horizontal-overflow",
        );
        c.layout(2, 2, 200);
        await checkpoint("enlarged");
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            "enlarged-no-horizontal-overflow",
        );
        c.layout(1, 1, 100);
        await invoke("harness_viewport", { preset: "wide" });
        c.setDraft("Synthetic draft in first story");
        const first = c.selected()!;
        await c.create();
        const second = c.selected()!;
        check(
            first.scope.story !== second.scope.story,
            "new-story-distinct-scope",
        );
        c.setDraft("Synthetic second story");
        await c.switchSession(first.id);
        check(
            c.get().draft === "Synthetic draft in first story",
            "create-preserves-previous-draft",
        );
        c.setFakeMode("delayed");
        const switched = c.send();
        await until(async () => (await c.pendingStatus())?.phase === "running");
        await c.switchSession(second.id);
        await switched;
        check(
            c.selected()?.id === second.id &&
                c.get().play?.receipts.length === 0 &&
                c.get().visibleError === null,
            "session-switch-fences-old-result",
        );
        check(
            c.get().draft === "Synthetic second story",
            "session-drafts-isolated",
        );
        await checkpoint("session-switch");
        // Reproduce recovery-error-after-switch with real commit then transport faults.
        c.setFakeMode("accepted");
        c.setAction("wait");
        g.dropCommit = true;
        g.failLookup = true;
        await c.send();
        const lookup = (g.heldLookup = gate());
        const recover = c.retry();
        check(c.retry() === recover, "recovery-deduplicated");
        await lookup.entered;
        await c.switchSession(first.id);
        lookup.release();
        await recover;
        check(
            c.selected()?.id === first.id && c.get().visibleError === null,
            "old-recovery-error-cannot-publish",
        );
        const count = c.get().play!.receipts.length;
        c.setDraft("Reset keeps this synthetic draft");
        await c.reset();
        check(
            c.get().play?.revision === 0 &&
                c.get().play?.receipts.length === 0 &&
                count > 0 &&
                c.get().draft.includes("Reset keeps"),
            "reset-invalidates-progress-preserves-draft",
        );
        check(
            errors.snapshot().length <= 64 &&
                errors
                    .snapshot()
                    .every(
                        (e) =>
                            Object.keys(e).sort().join(",") ===
                            "category,source",
                    ),
            "bounded-enum-errors-no-exception-text",
        );
        check(
            !errors
                .snapshot()
                .some(
                    (e) =>
                        e.category === "UnhandledError" ||
                        e.category === "RenderError",
                ),
            "no-unhandled-frontend-errors",
        );
        c.setAction("wait");
        c.setFakeMode("delayed");
        g.heldPrepare = gate();
        void c.send();
        await until(async () => (await c.pendingStatus())?.phase === "running");
        await checkpoint("close");
        // Native command destroys this app-owned hidden WebView and creates a fresh one.
        // No desktop input/activation, no general navigation/eval API.
        await invoke("harness_reopen");
    } catch (error) {
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                backend: config.backend,
                stage: config.stage,
                failedCheck: current,
                category: category(error),
                checks,
                errors: errors.snapshot(),
            },
        });
    }
}
