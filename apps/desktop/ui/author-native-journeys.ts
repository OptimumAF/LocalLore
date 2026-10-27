// Explicit DEVELOPMENT native harness only. Same mounted controllers and IPC.
import type { Controller } from "./controller";
import type { AuthorController } from "./author-controller";
import type { AuthorDraft, AuthorInput } from "./author-model";
import { checkedAuthorStatus } from "./author-model";
import type { V2PlayController } from "./v2-play-controller";
import type { V2BoundPage } from "./v2-play-controller";
import type { RowV2 } from "./v2-view-model";
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
    let entered = false;
    return {
        entered: new Promise<void>((resolve) => {
            enter = resolve;
        }),
        waiting: new Promise<void>((resolve) => {
            release = resolve;
        }),
        hasEntered: () => entered,
        ready: () => {
            entered = true;
            enter();
        },
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
    // Attempted Query2 calls through Root's unchanged native bridge only. This
    // is a no-dispatch observation, never proof that Rust accepted a request.
    inspectionDispatches = 0;
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
        if (command === "host_call" && typeof args.input === "string" && args.input.length <= 262144) {
            try {
                const envelope = JSON.parse(args.input);
                if (envelope?.version === 1 && envelope.command?.op === "inspection_query" &&
                    envelope.command.query?.version === 2) this.inspectionDispatches++;
            } catch {
                // Diagnostics must not alter forwarding of malformed native input.
            }
        }
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
    const receiptEvidence: Record<string, unknown>[] = [];
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
        const focus =
            label === "author-native-v2-receipt-diff"
                ? [...root.querySelectorAll('[data-native-kind="change"]')].find((row) => row.querySelector("caption")?.textContent?.includes("item/potion"))
                : label === "author-native-v2-receipt-prior-seed"
                  ? [...root.querySelectorAll('[aria-label="Read-only V2 inspector"] [data-native-kind="field"]')]
                      .find((row) => row.textContent?.includes("item/potion"))
                  : label === "author-native-v2-inherited-source"
                    ? root.querySelector('[aria-label="Read-only V2 inspector"] [data-native-kind="event"]')
                    : label === "author-native-observer"
                ? (root.querySelector(
                      '[data-native-kind="knowledge"][data-native-origin="known_as_observed"]',
                  ) ??
                  root.querySelector('[aria-label="Read-only V2 inspector"]'))
                : label === "author-native-receipt"
                  ? root.querySelector('[aria-label="Actual native receipt"]')
                  : label === "author-native-turn-cancelled"
                    ? root.querySelector('[aria-label="Original turn status"]')
                    : label === "author-native-preview"
                      ? root.querySelector("#author-impact-preview")
                      : [
                              "author-native-consent",
                              "author-native-rejected",
                              "author-native-cancelled",
                          ].includes(label)
                        ? root.querySelector("#author-visible-error")
                        : label === "author-native-pending"
                          ? root.querySelector("#author-operation-notice")
                          : [
                                  "author-native-saved",
                                  "author-native-late-cancel",
                                  "author-native-recovered",
                                  "author-native-narrow",
                              ].includes(label)
                            ? root.querySelector("#author-outcome-title")
                            : null;
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
                receiptEvidence: [...receiptEvidence],
                inspectionBridgeAttempts: transport.inspectionDispatches,
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
        await until(
            () => !!v2.get().snapshot && !v2.get().readBusy,
            "same-visible-query-control-readiness-after-lens-change",
        );
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
    const namedButton = (root: ParentNode, label: string) => {
        const matches = [...root.querySelectorAll<HTMLButtonElement>("button")]
            .filter((button) => button.textContent?.trim() === label);
        check(matches.length === 1 && !matches[0].disabled, `mounted-button-available-${label}`);
        return matches[0];
    };
    const mountedReceiptTrace = async (stage: string) => {
        await until(() => !v2.get().readBusy && !v2.get().queryBusy && !!v2.get().snapshot,
            `${stage}-current-V2-read-ready`);
        const receipt = v2.get().receipt, selectedContext = v2.get().context;
        check(receipt && selectedContext?.view === "play" && selectedContext.observer.kind === "player",
            `${stage}-actual-current-Player-receipt`);
        const end = receipt!.events.at(-1)!.sequence;
        const old = v2.get().inspection, attempts = transport.inspectionDispatches;
        const button = namedButton(document, "Inspect accepted turn changes");
        // Application-owned DOM activation invokes the actual mounted React
        // callback. No OS input, desktop automation or private React API.
        button.click();
        await until(() => {
            const current = v2.get(), inspector = document.querySelector('[aria-label="Read-only V2 inspector"]');
            return !!current.inspection && current.inspection !== old && !current.queryBusy &&
                current.inspection.query.view === "turn_diff" && current.inspection.page.revision === end &&
                inspector?.querySelector<HTMLSelectElement>("select")?.value === "turn_diff" &&
                inspector?.querySelector<HTMLInputElement>('input[type="number"]')?.value === String(end) &&
                inspector?.querySelector<HTMLInputElement>('input:not([type="number"])')?.value === "";
        }, `${stage}-mounted-callback-updates-query-and-local-controls`);
        const bound = v2.get().inspection!;
        check(transport.inspectionDispatches === attempts + 1 &&
            bound.query.version === 2 && bound.query.expected_head === 3 && bound.query.at_revision === 3 &&
            bound.query.observer.kind === "player" && bound.page.privacy === "player_visible" &&
            structural(bound.query.scope) === structural({ ...parent, branch: "author-saved" }) &&
            structural(v2.get().receipt) === structural(receipt) && c.get().view === "play",
            `${stage}-actual-Player-Query2-historical-boundary-no-new-grant`);
        const removed = bound.page.rows.find((row): row is Extract<RowV2, { kind: "change" }> =>
            row.kind === "change" && row.before?.kind === "field" && row.before.field === "item/potion" && row.after === null);
        check(removed?.before_revision === 2 && removed.after_revision === 3 && removed.before?.kind === "field" &&
            removed.before.value.type === "item" && removed.before.value.value.owner === selectedContext!.player &&
            removed.before.source.kind === "seed", `${stage}-actual-potion-before-present-after-absent-prior-seed`);
        await until(() => [...document.querySelectorAll('[data-native-kind="change"]')]
            .some((row) => row.querySelector("caption")?.textContent?.includes("item/potion")), `${stage}-actual-change-table-mounted`);
        const record = [...document.querySelectorAll('[data-native-kind="change"]')]
            .find((row) => row.querySelector("caption")?.textContent?.includes("item/potion"))!;
        const headers = [...record.querySelectorAll("th")].map((cell) => cell.textContent ?? "");
        const cells = [...record.querySelectorAll("tbody td")];
        check(headers.length === 2 && /Before\s*·\s*r2/.test(headers[0]) && /After\s*·\s*r3/.test(headers[1]) &&
            cells.length === 2 && cells[0].textContent?.includes("Prior field provenance") &&
            cells[1].textContent?.trim() === "Absent" && !/caused the removal|removed by event/i.test(record.textContent ?? ""),
            `${stage}-mounted-readable-historical-table-and-prior-provenance`);
        noPrivateAuthor(bound.page, `${stage}-Player-diff-excludes-author-private-evidence`);
        receiptEvidence.push({ stage, available: true, kind: "mounted-receipt-turn-diff", selected: selectedContext!.scope,
            head: bound.page.head, historicalRevision: bound.page.revision, originalReceiptTurn: receipt!.request.turn,
            observer: bound.query.observer, source: removed!.before!.kind === "field" ? removed!.before!.source : null,
            nativeBridgeAttempts: transport.inspectionDispatches - attempts, detachedCallbackClaim: false });
        return { receipt: receipt!, bound, removed: removed!, record };
    };
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
            if (v2.get().receipt) {
                await mountedReceiptTrace("restart-current-receipt");
            } else {
                check(!document.querySelector('[aria-label="Actual native receipt"]'),
                    "restart-does-not-invent-an-unavailable-thin-snapshot-receipt-link");
                receiptEvidence.push({ stage: "restart", available: false, kind: "receipt-link-unavailable",
                    reason: "Actual reopened thin snapshot/history does not reconstruct a controller receipt; no link was fabricated.",
                    higherHeadRetainedReceiptTested: false });
            }
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
            const opened = c.get(),
                selectedChild = c.selected(),
                expectedChild = { ...parent, branch: "author-saved" };
            check(
                a.get().error === null &&
                    structural(selectedChild?.scope) ===
                        structural(expectedChild) &&
                    selectedChild?.revision === 2 &&
                    opened.play === null &&
                    opened.playV2?.domain_version === 2 &&
                    structural(opened.playV2.scope) ===
                        structural(expectedChild) &&
                    opened.playV2.revision === 2,
                "confirmed-child-resume-proof-has-no-false-author-error-before-view-change",
            );
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
                    v2.get().status?.error === null &&
                    ["Inventory", "Rule"].includes(v2.get().error ?? "") &&
                    v2
                        .get()
                        .notice.includes(
                            "saved status has no retained cause",
                        ) &&
                    errors
                        .snapshot()
                        .some((error) =>
                            ["Inventory", "Rule"].includes(error.category),
                        ),
                "repeated-gift-is-rejected-by-actual-Rust-rules",
            );
            check(
                c.get().playV2?.revision === 3 &&
                    structural(v2.get().receipt) === accepted,
                "rejection-preserves-head-inventory-and-displayed-accepted-receipt",
            );
            await capture("author-native-receipt");
            const inspectionSnapshot = structural(v2.get().snapshot), inspectionHistory = structural(v2.get().history),
                inspectionOracle = structural(await oracle());
            const traced = await mountedReceiptTrace("accepted-after-rejection");
            await capture("author-native-v2-receipt-diff");
            const prior = traced.removed.before;
            check(prior?.kind === "field" && prior.source.kind === "seed", "mounted-prior-potion-source-is-actual-checked-seed");
            if (!prior || prior.kind !== "field" || prior.source.kind !== "seed") throw Error("PriorSeedUnavailable");
            const seedAttempts = transport.inspectionDispatches;
            namedButton(traced.record, `Seed ${prior.source.value}`).click();
            await until(() => !v2.get().queryBusy && v2.get().inspection?.query.view === "profiles" &&
                v2.get().inspection?.page.revision === 0, "mounted-prior-seed-opens-actual-Query2-seed-era-profiles");
            check(transport.inspectionDispatches === seedAttempts + 1 && v2.get().source?.kind === "seed" &&
                v2.get().sourceMatched === false && v2.get().notice.includes("Seed-era profiles") &&
                v2.get().inspection?.page.rows.some((row) => row.kind === "field" && row.field === "item/potion") &&
                v2.get().context?.revision === 3, "actual-prior-seed-navigation-is-not-removal-cause-or-current-inventory");
            receiptEvidence.push({ stage: "initial", available: true, kind: "mounted-prior-seed-source", selectedHead: 3,
                inspectedRevision: 0, originalSource: prior.source, exactEventMatchClaim: false });
            await capture("author-native-v2-receipt-prior-seed");
            const original = await v2.readQuery({ view: "history", atRevision: 3, search: "" });
            check(!!original, "actual-current-bound-history-ready-for-inherited-source-link");
            const inherited = original!.page.rows.find((row) => row.kind === "event" &&
                row.event.scope.story === parent.story && row.event.scope.branch === "main" && row.event.sequence === 1 &&
                row.event.turn === "author-parent-message");
            check(inherited?.kind === "event", "actual-inherited-event-retains-original-parent-scope-and-sequence");
            await until(() => [...document.querySelectorAll('[aria-label="Read-only V2 inspector"] button')]
                .some((button) => button.textContent?.trim() === `${parent.story} / main · event 1`), "mounted-inherited-source-link-ready");
            const inheritedAttempts = transport.inspectionDispatches;
            namedButton(document.querySelector('[aria-label="Read-only V2 inspector"]')!, `${parent.story} / main · event 1`).click();
            await until(() => !v2.get().queryBusy && v2.get().sourceMatched === true &&
                v2.get().source?.kind === "scoped_event", "mounted-inherited-source-matches-actual-returned-event");
            const originalSource = v2.get().source;
            check(transport.inspectionDispatches === inheritedAttempts + 1 && originalSource?.kind === "scoped_event" &&
                originalSource.value.original_scope.story === parent.story && originalSource.value.original_scope.branch === "main" &&
                originalSource.value.sequence === 1 && v2.get().inspection?.page.revision === 3 &&
                v2.get().inspection?.page.head === 3 && v2.get().inspection?.query.observer.kind === "player" &&
                v2.get().inspection?.page.rows.some((row) => row.kind === "event" && row.event.sequence === 1 &&
                    row.event.scope.branch === "main" && row.event.consequence.effect === "said" &&
                    row.event.consequence.text === "AUTHOR_PARENT_MIRA_ONLY") &&
                v2.get().context?.scope.branch === "author-saved", "actual-source-page-stays-selected-child-Player-and-matches-original-parent-event");
            noPrivateAuthor(v2.get().inspection?.page, "inherited-source-navigation-excludes-private-author-evidence");
            receiptEvidence.push({ stage: "initial", available: true, kind: "mounted-inherited-source", selectedHead: 3,
                inspectedRevision: 3, originalSource, detachedCallbackClaim: false });
            await capture("author-native-v2-inherited-source");
            check(structural(v2.get().snapshot) === inspectionSnapshot && structural(v2.get().history) === inspectionHistory &&
                structural(v2.get().receipt) === accepted && structural(await oracle()) === inspectionOracle,
                "mounted-evidence-navigation-preserves-native-player-history-receipt-and-canonical-oracle");
            c.setAction("wait");
            await refreshV2();
            const held = latch();
            gateway.heldPrepare = held;
            const turn = v2.send();
            await until(held.hasEntered, "actual-V2-prepare-response-held");
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
            check(structural(v2.get().receipt) === accepted, "cancelled-Wait-retains-original-accepted-gift-receipt-at-head3");
            const retainedTrace = await mountedReceiptTrace("retained-after-cancelled-Wait");
            check(structural(retainedTrace.receipt) === accepted && c.get().playV2?.revision === 3,
                "mounted-retained-receipt-trace-adds-no-turn-and-keeps-original-completed-head");

            await resumeParent();
            const retiredAttempts = transport.inspectionDispatches;
            check(await v2.traceReceipt(retainedTrace.receipt) === null &&
                transport.inspectionDispatches === retiredAttempts,
                "actual-old-context-receipt-controller-action-refuses-before-native-bridge");
            receiptEvidence.push({ stage: "initial", available: false, kind: "retired-context-controller-refusal",
                nativeBridgeAttempts: transport.inspectionDispatches - retiredAttempts, detachedCallbackClaim: false,
                note: "Retained React callback rejection is separately tested by the frozen headless handler suite." });
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
            await pause();
            check(
                !a.get().uncertain &&
                    retention.get()?.terminal &&
                    retention.get()?.consumed &&
                    !retention.get()?.unknown &&
                    !retention.get()?.inFlight,
                "confirmed-stale-preview-disposal-releases-shared-admission-without-lookup",
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
                receiptEvidence,
                inspectionBridgeAttempts: transport.inspectionDispatches,
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
                receiptEvidence,
                inspectionBridgeAttempts: transport.inspectionDispatches,
                stage: config.stage,
                realModelGeneration: false,
                authorRestartRecovery: false,
            },
        });
    }
}
