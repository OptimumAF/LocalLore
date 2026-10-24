// Explicit DEVELOPMENT native harness only. Same mounted controllers and IPC.
import type { Controller } from "./controller";
import type { AuthorController } from "./author-controller";
import type { AuthorDraft, AuthorInput } from "./author-model";
import { checkedAuthorStatus } from "./author-model";
import type { V2PlayController } from "./v2-play-controller";
import type { V2BoundPage } from "./v2-play-controller";
import type { BrokerRetention } from "./broker-retention";
import type { FaultGateway } from "./journeys";
import { structural, type ErrorBuffer } from "./model";
type Invoke = (
    command: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
const pause = () => new Promise<void>((resolve) => setTimeout(resolve, 25));
async function until(test: () => boolean | Promise<boolean>, label: string) {
    const deadline = performance.now() + 25000;
    while (performance.now() < deadline) {
        if (await test()) return;
        await pause();
    }
    throw Error(`AuthorDeadline:${label}`);
}
function latch() {
    let enter!: () => void, release!: () => void;
    return {
        entered: new Promise<void>((resolve) => {
            enter = resolve;
        }),
        waiting: new Promise<void>((resolve) => {
            release = resolve;
        }),
        ready: () => enter(),
        release: () => release(),
    };
}
/** Withholds ACTUAL acknowledgements below Root's unchanged retention adapter. */
export class AuthorHarnessTransport {
    private holdPrepare = false;
    private prepareId: number | null = null;
    private held: ReturnType<typeof latch> | null = null;
    private dropStart = false;
    private dropTerminal = false;
    private commitId: number | null = null;
    readonly evidence: { kind: string; operation: number | null }[] = [];
    discards = 0;
    holdPrepareCompletion() {
        if (this.holdPrepare || this.held) throw Error("AuthorHarnessBusy");
        this.holdPrepare = true;
        this.prepareId = null;
        this.held = latch();
    }
    dropCommitStart() {
        if (this.dropStart) throw Error("AuthorHarnessBusy");
        this.dropStart = true;
    }
    dropCommitTerminal() {
        if (this.dropTerminal) throw Error("AuthorHarnessBusy");
        this.dropTerminal = true;
        this.commitId = null;
    }
    async waitHeld() {
        if (!this.held) throw Error("AuthorHarnessNotArmed");
        await Promise.race([
            this.held.entered,
            new Promise<never>((_, reject) =>
                setTimeout(() => reject(Error("AuthorHeldDeadline")), 25000),
            ),
        ]);
    }
    release() {
        const held = this.held;
        this.held = null;
        held?.release();
    }
    async native(
        command: string,
        args: Record<string, unknown>,
        send: () => Promise<unknown>,
    ) {
        const value = await send(); // Never change the command, arguments or result bytes.
        if (command === "author_preview_discard") this.discards++;
        if (command === "author_prepare_start" && this.holdPrepare)
            this.prepareId = checkedAuthorStatus(value).operation_id;
        if (command === "author_commit_start") {
            this.commitId = checkedAuthorStatus(value).operation_id;
            if (this.dropStart) {
                this.dropStart = false;
                this.evidence.push({
                    kind: "actual-commit-start-ack-dropped",
                    operation: null,
                });
                throw Error("Transport");
            }
        }
        const relevantPrepare =
            this.holdPrepare &&
            (command === "author_prepare_start" ||
                (command === "archive_status" &&
                    args.operationId === this.prepareId));
        if (relevantPrepare) {
            const status = checkedAuthorStatus(value);
            if (!status.running) {
                if (status.phase !== "completed" || !this.held)
                    throw Error("AuthorPrepareFixtureFailed");
                this.holdPrepare = false;
                this.evidence.push({
                    kind: "actual-prepare-terminal-ack-held",
                    operation: status.operation_id,
                });
                const held = this.held;
                held.ready();
                await Promise.race([
                    held.waiting,
                    new Promise<never>((_, reject) =>
                        setTimeout(
                            () => reject(Error("AuthorHeldDeadline")),
                            30000,
                        ),
                    ),
                ]);
            }
        }
        if (
            this.dropTerminal &&
            command === "archive_status" &&
            args.operationId === this.commitId
        ) {
            const status = checkedAuthorStatus(value);
            if (!status.running) {
                this.dropTerminal = false;
                this.evidence.push({
                    kind: "actual-known-terminal-ack-dropped",
                    operation: status.operation_id,
                });
                throw Error("Transport");
            }
        }
        return value;
    }
}

const parent = { story: "author-controls-synthetic", branch: "main" };
const other = { story: "author-controls-other", branch: "main" };
const A = "AUTHOR_OBSERVED_A",
    B = "AUTHOR_WORLD_B",
    REASON = "AUTHOR_PRIVATE_REASON";
const draft = (child: string): AuthorDraft => ({
    fork_revision: 1,
    child_branch: child,
    fact: "relic-location",
    expected_proposition: A,
    replacement: B,
    reason: REASON,
});
interface Oracle {
    version: number;
    parent_preserved: boolean;
    parent_head: number;
    parent_sha256: string;
    children: Record<
        string,
        {
            found: boolean;
            head?: number;
            author_records?: number;
            created?: boolean;
            actor_author_observations?: number;
            old_knowers_preserved?: boolean;
        }
    >;
}

export async function authorNativeJourneys({
    controller: c,
    author: a,
    v2,
    brokerRetention: retention,
    gateway,
    errors,
    invoke,
    dispose,
    config,
    transport,
}: {
    controller: Controller;
    author: AuthorController;
    v2: V2PlayController;
    brokerRetention: BrokerRetention;
    gateway: FaultGateway;
    errors: ErrorBuffer;
    invoke: Invoke;
    dispose: () => Promise<void>;
    config: { stage: string };
    transport: AuthorHarnessTransport;
}) {
    const checks: string[] = [],
        probes: { label: string; error: string }[] = [];
    let current = "author-start";
    const check = (condition: unknown, label: string) => {
        current = label;
        if (!condition) throw Error(label);
        checks.push(label);
    };
    const fixture = (
        action:
            "hold-before" | "hold-after" | "release" | "gate-state" | "oracle",
    ) => invoke("harness_author_case", { action });
    const oracle = async () => {
        const value = (await fixture("oracle")) as Oracle;
        check(
            value.version === 1 &&
                value.parent_preserved &&
                value.parent_head === 1,
            "actual-readonly-parent-canonical-history-preserved",
        );
        check(
            !value.children["author-cancelled"].found &&
                !value.children["author-stale"].found,
            "cancelled-and-stale-child-never-created",
        );
        return value;
    };
    const nativeGate = () =>
        until(
            async () =>
                !!((await fixture("gate-state")) as { entered: boolean })
                    .entered,
            "actual-native-gate-entry",
        );
    const lab = async () => {
        c.requestLab();
        c.acknowledgeLab(true);
        c.setObserver("omniscient");
        await until(() => a.get().available, "native-granted-author-context");
    };
    const resumeParent = async () => {
        await c.resume(parent);
        await lab();
    };
    const prepare = async (child: string) => {
        a.setDraft(draft(child));
        a.setAuthorConsent(true);
        await a.prepare();
        check(
            a.get().status === "preview" && !!a.get().preview,
            `${child}-actual-private-preview`,
        );
        a.setPreviewRead(true);
    };
    const saved = (value: Oracle, child: string, head = 2) => {
        const row = value.children[child];
        check(
            row.found &&
                row.head === head &&
                row.author_records === 1 &&
                row.actor_author_observations === 0 &&
                row.old_knowers_preserved,
            `${child}-one-real-author-interval-no-actor-observation`,
        );
    };
    // Native-only malformed-input probes, separate from controller action evidence.
    // The fixed command set reaches the SAME production IPC/manager. No forged reply.
    const probe = async (
        command:
            | "author_prepare_start"
            | "author_commit_start"
            | "author_lookup_start",
        request: string,
        expected: readonly string[],
        label: string,
    ) => {
        let actual = "NoError";
        try {
            let status = checkedAuthorStatus(
                await window.__TAURI__.core.invoke(command, { request }),
            );
            await until(async () => {
                if (!status.running) return true;
                status = checkedAuthorStatus(
                    await window.__TAURI__.core.invoke("archive_status", {
                        operationId: status.operation_id,
                    }),
                );
                return !status.running;
            }, label);
            actual = status.error ?? "NoError";
        } catch (error) {
            actual = error instanceof Error ? error.message : String(error);
        }
        probes.push({ label, error: actual });
        check(expected.includes(actual), label);
    };
    const capture = async (label: string) => {
        await new Promise<void>((resolve) =>
            requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
        );
        const root = document.getElementById("root")!;
        const s = c.get(),
            thin = s.playV2,
            legacy = s.play,
            scope = c.selected()?.scope;
        const revision = thin?.revision ?? legacy?.revision ?? 0;
        check(
            !!scope && !!root.textContent?.includes(scope.story),
            `${label}-selected-story-visible`,
        );
        const panel =
            root.querySelector(".author-panel") ??
            root.querySelector(".v2-play") ??
            root;
        const focus = label === "author-native-observer"
            ? root.querySelector('[aria-label="Read-only V2 inspector"]')
            : label === "author-native-receipt" ? root.querySelector('[aria-label="Actual native receipt"]')
            : label === "author-native-turn-cancelled" ? root.querySelector('[aria-label="Original turn status"]')
            : label === "author-native-preview"
            ? root.querySelector("#author-impact-preview")
            : ["author-native-consent", "author-native-rejected", "author-native-cancelled"].includes(label)
                ? root.querySelector("#author-visible-error")
                : label === "author-native-pending" ? root.querySelector("#author-operation-notice")
                    : ["author-native-saved", "author-native-late-cancel", "author-native-recovered", "author-native-narrow"].includes(label)
                        ? root.querySelector("#author-outcome-title") : null;
        (focus ?? panel).scrollIntoView({ block: "start" });
        await pause();
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            `${label}-no-horizontal-overflow`,
        );
        const location = s.workspace?.location ?? "<none>";
        const text = (root.textContent ?? "")
            .slice(0, 48000)
            .replaceAll(location, "<synthetic-workspace>");
        const visibleReceipt = v2.get().receipt ?? c.receipt();
        const visibleError = v2.get().error ?? a.get().error ?? s.visibleError;
        const result = (await invoke("harness_checkpoint", {
            label,
            snapshot: {
                ...c.semantic(),
                synthetic: true,
                uiRevision: revision,
                workspace: s.workspace
                    ? { ...s.workspace, location: "<synthetic-workspace>" }
                    : null,
                aggregate: {
                    selected: scope,
                    observer: s.view === "play" ? "player" : s.observer,
                    revision,
                    pending: v2.get().pending ?? s.pending,
                    receipt: visibleReceipt,
                    visibleError,
                },
                author: a.get(),
                v2: v2.get(),
                broker: retention.get(),
                checks: [...checks],
                probes: [...probes],
                dom: {
                    userAgent: navigator.userAgent,
                    text,
                    viewport: { width: innerWidth, height: innerHeight },
                    structure: [
                        ...root.querySelectorAll(
                            "button,input,textarea,select,[role],h2,h3,dt,dd",
                        ),
                    ]
                        .slice(0, 256)
                        .map((el) => ({
                            tag: el.tagName,
                            role: el.getAttribute("role"),
                            label:
                                el.getAttribute("aria-label") ??
                                el.textContent?.slice(0, 160),
                            disabled: el.hasAttribute("disabled"),
                            checked:
                                el instanceof HTMLInputElement
                                    ? el.checked
                                    : null,
                            value:
                                el instanceof HTMLInputElement ||
                                el instanceof HTMLTextAreaElement ||
                                el instanceof HTMLSelectElement
                                    ? el.value.slice(0, 2048)
                                    : null,
                        })),
                },
            },
        })) as { rendering: string };
        check(
            result.rendering === "native-webview2",
            `${label}-actual-native-WebView2-image`,
        );
    };
    const refreshV2 = async () => {
        await v2.refresh();
        await until(
            () => !!v2.get().snapshot && !!v2.get().history,
            "actual-scoped-V2-reads",
        );
    };
    const page = async (view: "knowledge" | "history") => {
        await until(() => !!v2.get().snapshot && !v2.get().readBusy,
            "same-visible-query-control-readiness-after-lens-change");
        const result = await v2.readQuery({
            view,
            atRevision: null,
            search: "",
        });
        check(!!result, `actual-${view}-query-returned`);
        return result as V2BoundPage;
    };
    const noPrivateAuthor = (value: unknown, label: string) =>
        check(
            ![B, REASON, "truth_source"].some((secret) =>
                structural(value).includes(secret),
            ),
            label,
        );
    try {
        await c.start();
        if (config.stage === "restart") {
            check(
                a.get().input === null &&
                    a.get().preview === null &&
                    a.get().operation === null &&
                    !a.get().authorConsent &&
                    !a.get().outcome,
                "restart-restores-no-private-author-input-capability-or-consent",
            );
            await c.resume({ ...parent, branch: "author-saved" });
            c.setView("play");
            await refreshV2();
            check(
                c.get().playV2?.domain_version === 2 &&
                    c.get().playV2?.revision === 3,
                "restart-resumes-actual-saved-Domain2-child-head3",
            );
            saved(await oracle(), "author-saved", 3);
            check(
                !Object.hasOwn(v2.get().snapshot!.inventory, "potion"),
                "restart-retains-actual-gift-inventory-transfer",
            );
            check(
                v2
                    .get()
                    .history!.page.rows.some(
                        (row) =>
                            row.kind === "author_correction" &&
                            row.revision === 2,
                    ),
                "restart-retains-neutral-author-boundary",
            );
            noPrivateAuthor(
                v2.get().history,
                "restart-player-history-is-not-private-author-record",
            );
            await capture("author-native-restarted");
            await lab();
            check(
                a.get().input === null &&
                    a.get().preview === null &&
                    !a.get().busy,
                "restart-never-auto-prepares-looks-up-or-applies",
            );
            await capture("author-native-reopened");
        } else {
            await c.resume(parent);
            c.setView("play");
            check(
                !!c.get().workspace?.persistent && c.get().play?.revision === 1,
                "actual-durable-native-parent-selected",
            );
            check(!a.get().available, "Play-has-no-author-permission");
            await lab();
            c.setObserver("mira");
            check(
                !a.get().available,
                "character-inspection-is-not-author-permission",
            );
            c.setObserver("omniscient");
            await until(() => a.get().available, "omniscient-author-available");
            a.setDraft(draft("author-saved"));
            await a.prepare();
            check(
                a.get().error === "AuthorConsentRequired" && !a.get().preview,
                "Story-Lab-acknowledgement-is-not-first-author-consent",
            );
            await oracle();
            await capture("author-native-consent");
            a.setAuthorConsent(true);
            await a.prepare();
            const original = a.get().preview!,
                input = a.get().input!;
            check(
                !!original &&
                    original.preview.before.proposition === A &&
                    original.preview.input.operation.replacement === B &&
                    original.preview.input.reason === REASON,
                "actual-exact-Core-preview-displayed-and-SHA-validated",
            );
            check(
                original.preview.retained_knowers === 2 &&
                    original.preview.original_preserved &&
                    !original.preview.downstream_replayed,
                "actual-preview-retained-knowers-and-original-preservation",
            );
            await a.confirm(true);
            check(
                a.get().error === "ReadPreviewRequired",
                "second-consent-requires-reading-this-exact-preview",
            );
            check(
                !(await oracle()).children["author-saved"].found,
                "preparing-and-unread-confirm-never-create-child",
            );
            await capture("author-native-preview");
            const selected = c.selected()!;
            const prepareRaw = JSON.stringify({
                version: 1,
                session: selected.id,
                input,
                author_consent: true,
            });
            await probe(
                "author_prepare_start",
                prepareRaw.replace('"version":1', '"version":1,"version":1'),
                ["Malformed"],
                "actual-native-duplicate-key-is-rejected",
            );
            await probe(
                "author_prepare_start",
                JSON.stringify({
                    version: 1,
                    session: selected.id,
                    input,
                    author_consent: false,
                }),
                ["AuthorConsentRequired"],
                "actual-native-false-first-consent-is-rejected",
            );
            await probe(
                "author_commit_start",
                JSON.stringify({
                    version: 1,
                    session: selected.id,
                    input,
                    preview_token: original.preview_token,
                    preview_sha256: "0".repeat(64),
                    confirmed: true,
                }),
                ["AuthorPreviewMismatch"],
                "actual-native-preview-digest-mismatch-preserves-capability",
            );
            const discarded = transport.discards;
            a.setDraft({
                ...draft("author-saved"),
                reason: "AUTHOR_EDIT_REVOKES_CONSENT",
            });
            await until(
                () => transport.discards > discarded,
                "actual-unused-preview-discard-ack",
            );
            check(
                !a.get().preview &&
                    !a.get().authorConsent &&
                    !a.get().previewRead,
                "form-edit-revokes-both-consents-and-unused-preview",
            );
            await probe(
                "author_commit_start",
                JSON.stringify({
                    version: 1,
                    session: selected.id,
                    input,
                    preview_token: original.preview_token,
                    preview_sha256: original.preview_sha256,
                    confirmed: true,
                }),
                ["UnknownAuthorPreview"],
                "discarded-native-preview-cannot-be-reused",
            );
            await a.prepare();
            check(
                a.get().error === "AuthorConsentRequired",
                "edited-form-requires-new-first-consent",
            );
            await capture("author-native-rejected");

            await prepare("author-cancelled");
            await fixture("hold-before");
            const cancelled = a.confirm(true);
            await nativeGate();
            check(
                a.get().busy && a.get().operation?.running,
                "actual-native-author-worker-is-pending-before-apply",
            );
            let blocked = false;
            try {
                await invoke("archive_export_preview", { scope: parent });
            } catch (error) {
                blocked = String(error).includes("ArchiveBusy");
            }
            check(
                blocked,
                "pending-author-blocks-other-shared-frontend-admission",
            );
            let nativeBlocked = false;
            try {
                await window.__TAURI__.core.invoke("archive_export_preview", {
                    session: c.selected()!.id,
                    scope: parent,
                    expectedRevision: 1,
                });
            } catch (error) {
                nativeBlocked = String(error).includes("ArchiveBusy");
            }
            check(
                nativeBlocked,
                "actual-native-ArchiveBroker-rejects-concurrent-archive-probe",
            );
            await capture("author-native-pending");
            await a.cancel();
            await fixture("release");
            await cancelled;
            check(
                a.get().error === "Cancelled" && !a.get().outcome,
                "preapply-cancel-is-real-native-terminal-with-no-success",
            );
            await oracle();
            await capture("author-native-cancelled");

            await prepare("author-saved");
            await a.confirm(true);
            check(
                a.get().outcome?.created &&
                    a.get().outcome?.author_revision === 2,
                "second-explicit-confirm-saves-fixed-new-child",
            );
            saved(await oracle(), "author-saved");
            await capture("author-native-saved");
            await a.openConfirmed();
            c.setView("play");
            await refreshV2();
            check(
                c.get().playV2?.domain_version === 2 &&
                    v2.get().snapshot?.revision === 2,
                "confirmed-child-opens-through-actual-root-resume-V2",
            );
            const history = v2.get().history!.page.rows;
            const marker = history.filter(
                (row) => row.kind === "author_correction",
            );
            check(
                structural(marker) ===
                    structural([{ kind: "author_correction", revision: 2 }]),
                "player-author-marker-is-exactly-kind-and-revision",
            );
            check(
                history.some(
                    (row) =>
                        row.kind === "scoped_message" &&
                        row.original_scope.branch === "main" &&
                        row.turn === "author-parent-message" &&
                        row.text === "AUTHOR_PARENT_MIRA_ONLY",
                ),
                "inherited-message-keeps-original-parent-scope",
            );
            noPrivateAuthor(
                history,
                "player-history-excludes-author-truth-and-private-reason",
            );
            await capture("author-native-history");
            await lab();
            let read = await page("knowledge");
            check(
                structural(read.page).includes(B),
                "actual-omniscient-inspector-sees-current-B",
            );
            c.setObserver("mira");
            await refreshV2();
            read = await page("knowledge");
            check(
                read.page.rows.some(
                    (row) =>
                        row.kind === "knowledge" &&
                        row.text === A &&
                        row.origin === "known_as_observed",
                ),
                "Mira-keeps-observed-A-after-author-world-B",
            );
            noPrivateAuthor(
                read.page,
                "Mira-inspection-never-gets-author-reason-or-world-B",
            );
            read = await page("history");
            check(
                read.page.rows.every((row) => row.kind === "event"),
                "Mira-history-is-event-only-no-original-input-or-narration",
            );
            c.setObserver("sable");
            await refreshV2();
            read = await page("knowledge");
            check(
                ![A, B, REASON].some((secret) =>
                    structural(read.page).includes(secret),
                ),
                "Sable-never-inherits-unobserved-A-B-or-author-reason",
            );
            read = await page("history");
            check(
                !structural(read.page).includes("AUTHOR_PARENT_MIRA_ONLY"),
                "Sable-never-receives-Mira-only-original-message",
            );
            c.setObserver("mira");
            await refreshV2();
            read = await page("knowledge");
            check(
                read.page.rows.some(
                    (row) => row.kind === "knowledge" && row.text === A,
                ),
                "inspection-privilege-never-mutates-Mira-knowledge",
            );
            await capture("author-native-observer");

            c.setView("play");
            c.setAction("give");
            c.setFakeMode("accepted");
            await refreshV2();
            await v2.send();
            await until(
                () => c.get().playV2?.revision === 3,
                "actual-V2-gift-root-refresh",
            );
            check(
                v2.get().status?.phase === "committed" &&
                    !!v2.get().receipt &&
                    v2.get().receipt?.request.scope.branch === "author-saved",
                "continued-V2-Play-saves-real-child-receipt",
            );
            check(
                !Object.hasOwn(v2.get().snapshot!.inventory, "potion"),
                "actual-accepted-gift-removes-player-potion",
            );
            check(
                v2
                    .get()
                    .history?.page.rows.some(
                        (row) =>
                            row.kind === "scoped_message" &&
                            row.original_scope.branch === "author-saved" &&
                            row.text === v2.get().receipt?.narration,
                    ),
                "actual-child-narration-retains-child-original-scope-in-player-history",
            );
            noPrivateAuthor(
                v2.get().history?.page,
                "continued-Play-transcript-is-still-not-private-author-history",
            );
            const accepted = structural(v2.get().receipt);
            await v2.send();
            await v2.status();
            check(
                v2.get().status?.phase === "failed" &&
                    ["Inventory", "Rule"].includes(
                        v2.get().status?.error ?? "",
                    ),
                "repeated-gift-is-rejected-by-actual-Rust-rules",
            );
            check(
                c.get().playV2?.revision === 3 &&
                    structural(v2.get().receipt) === accepted,
                "rejection-preserves-head-inventory-and-displayed-accepted-receipt",
            );
            await capture("author-native-receipt");
            c.setAction("wait");
            const held = latch();
            gateway.heldPrepare = held;
            const turn = v2.send();
            await held.entered;
            check(
                !!v2.get().pending,
                "actual-V2-ready-ack-held-pending-is-not-root-legacy-null",
            );
            await v2.cancel();
            held.release();
            await turn;
            await v2.status();
            check(
                v2.get().status?.phase === "cancelled" &&
                    !v2.get().pending &&
                    !v2.get().uncertain &&
                    c.get().playV2?.revision === 3,
                "cancelled-original-V2-turn-never-adds-accepted-head",
            );
            await capture("author-native-turn-cancelled");

            await resumeParent();
            await prepare("author-late");
            await fixture("hold-after");
            const late = a.confirm(true);
            await nativeGate();
            saved(await oracle(), "author-late");
            await a.cancel();
            await fixture("release");
            await late;
            check(
                a.get().outcome?.created && a.get().error === null,
                "late-cancel-cannot-demote-actual-committed-author-outcome",
            );
            await a.lookup();
            check(
                a.get().outcome?.created === false,
                "exact-readonly-lookup-returns-existing-recorded-result",
            );
            saved(await oracle(), "author-late");
            await capture("author-native-late-cancel");

            await prepare("author-known-ack");
            transport.dropCommitTerminal();
            await fixture("hold-after");
            const known = a.confirm(true);
            await nativeGate();
            await fixture("release");
            await known;
            check(
                a.get().uncertain &&
                    a.get().operation !== null &&
                    retention.get()?.unknown,
                "lost-terminal-reply-retains-known-ID-and-global-unknown",
            );
            await a.inspectOperation();
            check(
                a.get().status === "complete" &&
                    a.get().outcome?.scope.branch === "author-known-ack",
                "explicit-known-ID-status-recovers-actual-native-completion",
            );
            saved(await oracle(), "author-known-ack");

            await prepare("author-unknown");
            transport.dropCommitStart();
            await fixture("hold-before");
            await a.confirm(true);
            await nativeGate();
            check(
                a.get().uncertain &&
                    a.get().operation === null &&
                    retention.get()?.unknown,
                "lost-whole-start-ack-never-invents-an-operation-ID",
            );
            await c.resume(other);
            check(
                retention.get()?.unknown && !a.get().preview,
                "session-switch-cannot-clear-shared-unknown-or-install-private-preview",
            );
            await capture("author-native-unknown");
            await fixture("release");
            await until(
                async () => (await oracle()).children["author-unknown"].found,
                "actual-unknown-child-commit-settled",
            );
            await c.resume(parent);
            c.setView("lab");
            c.setObserver("omniscient");
            check(
                retention.acknowledgeUnresolved(true),
                "explicit-uncertainty-acknowledgement-is-required-before-new-admission",
            );
            await until(
                () => a.get().available,
                "read-only-lookup-available-after-explicit-ack",
            );
            await a.lookup();
            check(
                a.get().status === "complete" &&
                    a.get().outcome?.created === false &&
                    a.get().outcome?.scope.branch === "author-unknown",
                "same-window-exact-lookup-recovers-lost-whole-ack-without-apply",
            );
            const exact = a.get().input as AuthorInput;
            await probe(
                "author_lookup_start",
                JSON.stringify({
                    version: 1,
                    input: { ...exact, reason: "AUTHOR_DIFFERENT_INPUT" },
                    author_consent: true,
                }),
                ["RetryMismatch"],
                "changed-full-input-is-not-exact-author-recovery",
            );
            saved(await oracle(), "author-unknown");
            await capture("author-native-recovered");
            await invoke("harness_viewport", { preset: "capture-narrow" });
            await capture("author-native-narrow");
            await invoke("harness_viewport", { preset: "wide" });

            a.setDraft(draft("author-stale"));
            a.setAuthorConsent(true);
            transport.holdPrepareCompletion();
            const stale = a.prepare();
            await transport.waitHeld();
            const priorDiscards = transport.discards;
            await c.resume(other);
            transport.release();
            await stale;
            await until(
                () => transport.discards > priorDiscards,
                "stale-actual-prepared-cap-discarded",
            );
            check(
                c.selected()?.scope.story === other.story &&
                    (c.get().play?.revision ?? c.get().playV2?.revision) ===
                        0 &&
                    !a.get().preview &&
                    !a.get().outcome,
                "late-prepare-never-installs-private-result-in-new-selected-session",
            );
            check(
                !v2.get().receipt &&
                    !a.get().authorConsent &&
                    !a.get().previewRead,
                "session-change-clears-receipt-and-both-author-consents",
            );
            await oracle();
            await capture("author-native-stale-context");
        }
        const errorRecords = errors.snapshot();
        check(
            errorRecords.every(
                (error) =>
                    error.source === "native" &&
                    ["Cancelled", "Inventory", "Rule"].includes(error.category),
            ) && errorRecords.length <= 12,
            "bounded-error-evidence-has-only-explicit-native-rejection-and-cancel-categories",
        );
        if (config.stage === "restart")
            check(
                errorRecords.length === 0,
                "restart-has-zero-native-or-frontend-errors",
            );
        await dispose();
        const stats = (await invoke("harness_stats")) as {
            sessions: number;
            workers: number;
        };
        check(
            stats.sessions === 0 && stats.workers === 0,
            "all-actual-owned-Host-sessions-and-workers-drained",
        );
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                checks,
                probes,
                errors: errorRecords,
                transport: transport.evidence,
                stage: config.stage,
                realModelGeneration: false,
                authorRestartRecovery: false,
            },
        });
    } catch (error) {
        transport.release();
        try {
            await fixture("release");
        } catch {
            /* Finishing retains original failure. */
        }
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                checks,
                probes,
                failedCheck: current,
                error:
                    error instanceof Error
                        ? error.message
                        : String(error).slice(0, 160),
                author: a.get(),
                v2: v2.get(),
                broker: retention.get(),
                errors: errors.snapshot(),
                stage: config.stage,
                realModelGeneration: false,
                authorRestartRecovery: false,
            },
        });
    }
}
