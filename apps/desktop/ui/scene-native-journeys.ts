// FIRST source freeze: UNCOMPILED / UNRUN. Fixed synthetic native app journey.
// Actual mounted handlers/controllers/IPC/Store; no OS input or desktop capture.
import type { Controller } from "./controller";
import type { FaultGateway } from "./journeys";
import { structural, type ErrorBuffer, type Scope } from "./model";
import type { V2PlayController, V2BoundPage } from "./v2-play-controller";
import type { RowV2 } from "./v2-view-model";

type Invoke = (
    command: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
type Oracle = {
    version: number;
    synthetic: boolean;
    case: "literal" | "memory";
    scope: Scope;
    head: number;
    domain_version: number;
    baseline_head: number;
    new_commits: number;
    canonical_sha256: string;
    untouched_preserved: boolean;
    other_preserved: boolean;
    observer_isolated: boolean;
    observer_sha256: Record<string, string>;
    fixture_factories: number;
    fixture_polls: number;
    real_model: boolean;
};
const TEXT = "I wait for one tide tick.";
const A = "SCENE_OBSERVED_A",
    B = "SCENE_UNOBSERVED_B";
const PRIVATE = "SCENE_PARENT_MIRA_ONLY",
    REASON = "SCENE_PRIVATE_AUTHOR_REASON";
function gate() {
    let release!: () => void, ready!: () => void;
    const entered = new Promise<void>((resolve) => {
        ready = resolve;
    });
    const waiting = new Promise<void>((resolve) => {
        release = resolve;
    });
    return { entered, waiting, ready, release };
}
export async function sceneNativeJourneys({
    controller: c,
    v2,
    gateway,
    errors,
    invoke,
    dispose,
    config,
}: {
    controller: Controller;
    v2: V2PlayController;
    gateway: FaultGateway;
    errors: ErrorBuffer;
    invoke: Invoke;
    dispose: () => Promise<void>;
    config: { stage: string; sceneCase: "literal" | "memory" };
}) {
    const checks: string[] = [],
        proofs: { label: string; value: Oracle }[] = [];
    const releases = new Set<() => void>();
    const scope = {
        story: "scene-native-controls",
        branch: config.sceneCase === "literal" ? "main" : "scene-child",
    };
    const baseline = config.sceneCase === "literal" ? 1 : 2;
    const expectedPrompt =
        config.sceneCase === "literal"
            ? "locallore-play-v2.10-literal-director-v1-scene-frame-v1"
            : "locallore-play-v2.9-scene-frame-v1";
    let current = "scene-start";
    let clockComparisonTable: HTMLTableElement | null = null;
    const check = (condition: unknown, label: string) => {
        current = label;
        gateway.diagnosticPhase = label;
        if (!condition) throw Error(label);
        checks.push(label);
    };
    const pause = () => new Promise<void>((resolve) => setTimeout(resolve, 25));
    const until = async (condition: () => boolean, label: string) => {
        current = label;
        gateway.diagnosticPhase = label;
        for (let n = 0; n < 800; n++) {
            if (condition()) return;
            await pause();
        }
        throw Error(`SceneDeadline:${label}`);
    };
    const waitGate = async (held: ReturnType<typeof gate>, label: string) => {
        releases.add(held.release);
        let entered = false;
        void held.entered.then(() => {
            entered = true;
        });
        await until(() => entered, label);
    };
    const release = (held: ReturnType<typeof gate>) => {
        held.release();
        releases.delete(held.release);
    };
    const oracle = async (label: string, commits?: number) => {
        const value = (await invoke("harness_scene_oracle")) as Oracle;
        check(
            value.version === 1 &&
                value.synthetic === true &&
                value.case === config.sceneCase &&
                structural(value.scope) === structural(scope) &&
                value.baseline_head === baseline &&
                value.domain_version ===
                    (config.sceneCase === "literal" ? 1 : 2) &&
                value.untouched_preserved &&
                value.other_preserved &&
                value.observer_isolated &&
                value.real_model === false &&
                /^[a-f0-9]{64}$/.test(value.canonical_sha256),
            `${label}-actual-Store-scope-prefix-other-story-and-observer-proof`,
        );
        if (commits !== undefined)
            check(
                value.new_commits === commits &&
                    value.head === baseline + commits,
                `${label}-exact-actual-canonical-append-count`,
            );
        proofs.push({ label, value });
        return value;
    };
    const unchangedCanon = (before: Oracle, after: Oracle, label: string) =>
        check(
            before.head === after.head &&
                before.canonical_sha256 === after.canonical_sha256 &&
                structural(before.observer_sha256) ===
                    structural(after.observer_sha256),
            label,
        );
    const refresh = async () => {
        await v2.refresh();
        await until(
            () =>
                !!v2.get().snapshot && !!v2.get().history && !v2.get().readBusy,
            "coherent-native-V2-read-ready",
        );
    };
    const namedButton = (root: ParentNode, label: string) => {
        const buttons = [
            ...root.querySelectorAll<HTMLButtonElement>("button"),
        ].filter((button) => button.textContent?.trim() === label);
        check(
            buttons.length === 1 && !buttons[0].disabled,
            `mounted-button-ready-${label}`,
        );
        return buttons[0];
    };
    const checkReceipt = (commits: number) => {
        const state = v2.get(),
            actual = state.receipt;
        check(
            state.status?.phase === "committed" &&
                !!actual &&
                !state.pending &&
                !state.uncertain,
            "actual-committed-acknowledged-receipt",
        );
        const r = actual!;
        check(
            !!r.play && !!r.play.scene && typeof r.play.scene === "object",
            "actual-receipt-has-scene-provenance",
        );
        const play = r.play!,
            frame = play.scene as Record<string, unknown>;
        check(
            structural(r.request.scope) === structural(scope) &&
                r.request.intent.kind === "free_text" &&
                r.request.intent.value.kind === "action" &&
                r.request.intent.value.text === TEXT &&
                r.events.at(-1)?.sequence === baseline + commits &&
                structural(r.proposal.commands) ===
                    structural([{ op: "wait", ticks: 1 }]) &&
                r.events.length === 1 &&
                r.events[0].outcome.effect === "time_advanced",
            "actual-request-wait-proposal-and-single-accepted-clock-event",
        );
        check(
            play.prompt_version === expectedPrompt &&
                play.policy === "grounded-prose-v2.4-scene-frame-v1" &&
                (play.profile as Record<string, unknown>).id ===
                    "scene-native-fixture-v1" &&
                frame.version === 1 &&
                Object.keys(frame).sort().join(",") ===
                    "frame_sha256,version" &&
                /^[a-f0-9]{64}$/.test(String(frame.frame_sha256)),
            "actual-scene-recipe-profile-and-closed-provenance",
        );
        check(
            ![B, REASON].some((secret) => structural(r).includes(secret)),
            "receipt-never-exposes-private-author-truth-or-reason",
        );
        return r;
    };
    const capture = async (label: string) => {
        await new Promise<void>((resolve) =>
            requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
        );
        const root = document.getElementById("root")!,
            state = c.get(),
            view = v2.get();
        const selected = c.selected(),
            context = view.context,
            snapshot = view.snapshot;
        const panel = root.querySelector<HTMLElement>(
            '[aria-label="Scoped timeline Play and inspection"]',
        );
        check(
            root &&
                panel &&
                selected &&
                context &&
                snapshot &&
                selected.id === context.session &&
                structural(selected.scope) === structural(context.scope) &&
                snapshot.revision === context.revision &&
                state.playV2?.revision === context.revision &&
                panel.textContent?.includes(context.scope.story) &&
                panel.textContent?.includes(context.scope.branch) &&
                panel.textContent?.includes(`r${context.revision}`),
            `${label}-coherent-selected-story-session-and-visible-revision`,
        );
        check(
            panel!.textContent?.includes(
                "Synthetic scene fixture · no model loaded",
            ) &&
                panel!.textContent?.includes("Local durable workspace") &&
                state.model?.loaded === false,
            `${label}-truthful-synthetic-provider-and-durable-progress`,
        );
        const visibleError = view.error ?? state.visibleError;
        if (visibleError)
            check(
                [...panel!.querySelectorAll('[role="alert"]')].some((el) =>
                    el.textContent?.includes(visibleError),
                ),
                `${label}-actual-visible-error`,
            );
        if (view.receipt && context!.view === "play")
            check(
                panel!
                    .querySelector('[aria-label="Actual native receipt"]')
                    ?.textContent?.includes(view.receipt.request.turn),
                `${label}-same-displayed-receipt`,
            );
        const originalRequest = (view.pending ?? view.uncertain)?.request;
        if (originalRequest)
            check(
                panel!
                    .querySelector(
                        '[aria-label="Active original request scope"]',
                    )
                    ?.textContent?.includes(
                        `${originalRequest.scope.story} / ${originalRequest.scope.branch}`,
                    ),
                `${label}-visible-original-request-scope`,
            );
        const receiptCapture = [
            "scene-native-receipt",
            "scene-native-recovered",
        ].includes(label);
        let contentTarget: HTMLElement | null = null;
        if (receiptCapture) {
            contentTarget = panel!.querySelector<HTMLElement>(
                '[aria-label="Actual native receipt"]',
            );
            check(
                contentTarget?.textContent?.includes(view.receipt!.narration),
                `${label}-actual-receipt-content-capture-target`,
            );
        } else if (label === "scene-native-observer") {
            contentTarget = panel!.querySelector<HTMLElement>(
                '[aria-label="Read-only V2 inspector"] ol',
            );
            check(
                contentTarget?.textContent?.includes(A) &&
                    ![B, REASON].some((s) =>
                        contentTarget!.textContent?.includes(s),
                    ),
                `${label}-actual-permitted-knowledge-capture-target`,
            );
        }
        const comparisonCapture = [
            "scene-native-receipt-diff",
            "scene-native-recorded-diff",
        ].includes(label);
        if (comparisonCapture) {
            check(
                clockComparisonTable?.isConnected &&
                    panel!.contains(clockComparisonTable),
                `${label}-actual-mounted-clock-table-capture-target`,
            );
            clockComparisonTable!.scrollIntoView({ block: "center" });
        } else if (contentTarget)
            contentTarget.scrollIntoView({ block: "center" });
        else panel!.scrollIntoView({ block: "start" });
        await pause();
        if (contentTarget) {
            const bounds = contentTarget.getBoundingClientRect();
            const header = panel!
                .querySelector("header")!
                .getBoundingClientRect();
            check(
                bounds.top >= header.bottom && bounds.bottom <= innerHeight,
                `${label}-actual-content-visible-below-scope-header`,
            );
        }
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            `${label}-no-horizontal-overflow`,
        );
        const location = state.workspace?.location ?? "<none>";
        const native = await oracle(`${label}-capture`);
        const result = (await invoke("harness_checkpoint", {
            label,
            snapshot: {
                ...c.semantic(),
                synthetic: true,
                uiRevision: context!.revision,
                workspace: state.workspace
                    ? { ...state.workspace, location: "<synthetic-workspace>" }
                    : null,
                aggregate: {
                    selected: selected!.scope,
                    session: selected!.id,
                    observer:
                        context!.view === "play"
                            ? { kind: "player" }
                            : context!.observer,
                    revision: context!.revision,
                    pending: view.pending ?? view.uncertain,
                    receipt: view.receipt,
                    visibleError,
                    fixtureTarget: { scope: native.scope, head: native.head },
                },
                v2: view,
                provider: state.freeTextProvider,
                oracle: native,
                checks: [...checks],
                errors: errors.snapshot(),
                rejectedNativeCalls: gateway.rejectedNativeCalls,
                dom: {
                    userAgent: navigator.userAgent,
                    text: (root.textContent ?? "")
                        .slice(0, 48000)
                        .replaceAll(location, "<synthetic-workspace>"),
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
            `${label}-application-owned-native-WebView2-render`,
        );
    };
    const clockDiff = async (
        button: HTMLButtonElement,
        end: number,
        label: string,
    ) => {
        const old = v2.get().inspection,
            before = await oracle(`${label}-before`);
        button.click(); // Actual mounted application callback, never OS input/private React APIs.
        await until(
            () =>
                !!v2.get().inspection &&
                v2.get().inspection !== old &&
                !v2.get().queryBusy &&
                v2.get().inspection!.query.view === "turn_diff",
            `${label}-mounted-turn-diff-ready`,
        );
        const bound = v2.get().inspection!,
            change = bound.page.rows.find(
                (row) =>
                    row.kind === "change" &&
                    row.before?.kind === "clock" &&
                    row.after?.kind === "clock",
            );
        check(
            bound.query.at_revision === end &&
                bound.query.expected_head === before.head &&
                bound.query.observer.kind === "player" &&
                bound.page.privacy === "player_visible" &&
                bound.page.revision === end &&
                structural(bound.query.scope) === structural(scope) &&
                change?.kind === "change" &&
                change.before_revision === end - 1 &&
                change.after_revision === end &&
                change.before?.kind === "clock" &&
                change.after?.kind === "clock" &&
                change.after.story_time === change.before.story_time + 1,
            `${label}-actual-Rust-clock-before-after-boundary`,
        );
        const beforeValue =
            change?.kind === "change" && change.before?.kind === "clock"
                ? String(change.before.story_time)
                : null;
        const afterValue =
            change?.kind === "change" && change.after?.kind === "clock"
                ? String(change.after.story_time)
                : null;
        const mountedTables = () =>
            [
                ...document.querySelectorAll<HTMLTableElement>(
                    '[data-native-kind="change"] table',
                ),
            ].filter(
                (table) =>
                    table.querySelector("caption")?.textContent?.trim() ===
                    "Recorded change · Story time",
            );
        const exactMountedValues = () => {
            const tables = mountedTables();
            if (
                tables.length !== 1 ||
                beforeValue === null ||
                afterValue === null
            )
                return false;
            const headers = [...tables[0].querySelectorAll("thead th")].map(
                (el) => el.textContent?.trim(),
            );
            const values = [
                ...tables[0].querySelectorAll("tbody td > .record-value"),
            ].map((el) => el.textContent?.trim());
            return (
                structural(headers) ===
                    structural([`Before · r${end - 1}`, `After · r${end}`]) &&
                structural(values) === structural([beforeValue, afterValue])
            );
        };
        await until(exactMountedValues, `${label}-actual-clock-change-mounted`);
        check(
            exactMountedValues(),
            `${label}-mounted-before-after-revisions-and-actual-clock-values`,
        );
        clockComparisonTable = mountedTables()[0];
        unchangedCanon(
            before,
            await oracle(`${label}-after`),
            `${label}-inspection-does-not-write-or-change-observer-knowledge`,
        );
        return bound;
    };
    const draft = async () => {
        v2.setDraft(TEXT);
        await until(
            () =>
                document.querySelector<HTMLTextAreaElement>(".v2-play textarea")
                    ?.value === TEXT,
            "actual-V2-composer-displays-original-free-text",
        );
    };
    let finalOracle: Oracle | null = null;
    try {
        check(
            ["literal", "memory"].includes(config.sceneCase) &&
                ["initial", "restart"].includes(config.stage),
            "closed-scene-case-and-stage",
        );
        await c.start();
        await c.resume(scope);
        await c.refreshFreeTextProvider();
        await c.refreshModel();
        check(
            c.get().freeTextProvider?.kind === "synthetic_fixture" &&
                c.get().model?.loaded === false &&
                c.get().model?.imported === false &&
                c.get().model?.resident === false,
            "native-fixture-capability-is-separate-from-ModelManager-assets",
        );
        c.setPlayMode("local");
        c.setInputKind("action");
        await refresh();
        await invoke("harness_viewport", { preset: "capture-narrow" });
        if (config.stage === "restart") {
            const reopened = await oracle("cold-reopen", 5);
            check(
                v2.get().receipt === null &&
                    c.receipt() === null &&
                    reopened.fixture_factories === 0 &&
                    reopened.fixture_polls === 0,
                "cold-reopen-has-no-invented-raw-receipt-or-generation",
            );
            await capture("scene-native-restarted");
            const history = v2.get().history!;
            const narration = history.page.rows.find(
                (row): row is Extract<RowV2, { kind: "scoped_message" }> =>
                    row.kind === "scoped_message" &&
                    row.message_kind === "narration" &&
                    row.origin === "recorded_message" &&
                    structural(row.original_scope) === structural(scope) &&
                    structural(row.event_ids) === structural([reopened.head]),
            );
            check(
                !!narration && !!narration.text,
                "cold-read-actual-last-narration-row-identity",
            );
            await until(
                () =>
                    [
                        ...document.querySelectorAll<HTMLElement>(
                            '[aria-label="Accepted scoped history"] [data-native-kind="scoped_message"]',
                        ),
                    ].filter(
                        (row) =>
                            row
                                .querySelector("small")
                                ?.textContent?.includes(narration!.turn) &&
                            row.querySelector(".record-value")?.textContent ===
                                narration!.text,
                    ).length === 1,
                "cold-actual-narration-row-mounted",
            );
            const row = [
                ...document.querySelectorAll<HTMLElement>(
                    '[aria-label="Accepted scoped history"] [data-native-kind="scoped_message"]',
                ),
            ].find(
                (row) =>
                    row
                        .querySelector("small")
                        ?.textContent?.includes(narration!.turn) &&
                    row.querySelector(".record-value")?.textContent ===
                        narration!.text,
            )!;
            await clockDiff(
                namedButton(row, "Inspect recorded turn changes"),
                reopened.head,
                "cold-recorded-turn",
            );
            check(
                v2.get().receipt === null,
                "cold-inspection-does-not-fabricate-live-receipt",
            );
            await capture("scene-native-recorded-diff");
            finalOracle = await oracle("cold-final", 5);
            unchangedCanon(
                reopened,
                finalOracle,
                "all-cold-reads-preserve-original-canonical-and-observer-state",
            );
            check(
                finalOracle.fixture_factories === 0 &&
                    finalOracle.fixture_polls === 0,
                "all-cold-reads-call-no-provider",
            );
        } else {
            await oracle("initial", 0);
            await capture("scene-native-ready");
            await draft();
            namedButton(
                document.querySelector('[aria-label="Native turn composer"]')!,
                "Send to Rust",
            ).click();
            await until(
                () =>
                    v2.get().status?.phase === "committed" &&
                    v2.get().snapshot?.revision === baseline + 1 &&
                    !v2.get().pending &&
                    !v2.get().readBusy,
                "mounted-composer-commits-through-actual-controller-and-native-IPC",
            );
            const first = checkReceipt(1);
            await oracle("first-commit", 1);
            await capture("scene-native-receipt");
            await clockDiff(
                namedButton(document, "Inspect accepted turn changes"),
                first.events.at(-1)!.sequence,
                "live-receipt",
            );
            check(
                v2.get().receipt === first,
                "mounted-receipt-inspection-retains-same-actual-object",
            );
            await capture("scene-native-receipt-diff");

            const beforeCancel = await oracle("before-cancel", 1),
                held = gate();
            gateway.heldPrepare = held;
            await draft();
            const pending = v2.send();
            await waitGate(held, "actual-ready-prepare-reply-held");
            check(
                v2.get().pending?.stage === "preparing",
                "actual-pending-operation-visible",
            );
            await capture("scene-native-pending");
            const original = v2.get().pending!.request.turn,
                submissions = gateway.submissions.length;
            await v2.cancel();
            release(held);
            await pending;
            check(
                v2.get().status?.phase === "cancelled" &&
                    v2.get().draft === TEXT &&
                    !v2.get().uncertain,
                "actual-ready-cancel-preserves-draft-and-known-terminal-result",
            );
            unchangedCanon(
                beforeCancel,
                await oracle("after-cancel", 1),
                "cancelled-ready-turn-never-appends-canon",
            );
            const afterCancel = await oracle("cancel-before-terminal-retry", 1);
            await v2.retryExact();
            check(
                v2.get().status?.turn === original &&
                    v2.get().status?.phase === "cancelled" &&
                    gateway.submissions.length === submissions,
                "terminal-retry-reads-original-ID-without-new-admission",
            );
            const cancelled = await oracle("cancel-after-terminal-retry", 1);
            check(
                cancelled.fixture_polls === afterCancel.fixture_polls,
                "terminal-cancel-retry-has-zero-generation",
            );
            await capture("scene-native-cancelled");

            gateway.dropCommit = true;
            await draft();
            await v2.send();
            check(
                !!v2.get().uncertain && v2.get().receipt === first,
                "lost-actual-commit-ack-retains-original-key-and-prior-receipt",
            );
            const unknown = await oracle("unknown-actual-commit", 2),
                sent = gateway.submissions.length;
            await capture("scene-native-unknown");
            await v2.status();
            checkReceipt(2);
            const recovered = await oracle("known-actual-commit", 2);
            unchangedCanon(
                unknown,
                recovered,
                "lost-commit-status-recovers-without-second-canonical-write",
            );
            check(
                gateway.submissions.length === sent &&
                    recovered.fixture_polls === unknown.fixture_polls,
                "lost-commit-status-never-resubmits-or-regenerates",
            );

            gateway.dropSubmit = true;
            await draft();
            await v2.send();
            const retained = v2.get().uncertain;
            check(
                !!retained && retained.request.intent.kind === "free_text",
                "lost-admission-retains-original-free-text-key",
            );
            const admissionID = retained!.request.turn;
            const admitted = gateway.submissions.length;
            await v2.retryExact();
            check(
                checkReceipt(3).request.turn === admissionID &&
                    gateway.submissions.length === admitted,
                "actual-queued-admission-lookup-retry-uses-original-ID-and-commits-once",
            );
            await oracle("recovered-admission", 3);
            await capture("scene-native-recovered");

            const selectedSession = c.selected()!.id,
                otherHold = gate();
            gateway.heldCommit = otherHold;
            await draft();
            const otherPending = v2.send();
            await waitGate(otherHold, "actual-commit-held-before-story-switch");
            await oracle("held-actual-commit", 4);
            await c.resume({ story: "scene-native-other", branch: "main" });
            await refresh();
            release(otherHold);
            await otherPending;
            check(
                c.selected()?.scope.story === "scene-native-other" &&
                    v2.get().receipt === null &&
                    v2.get().status === null,
                "retired-completion-cannot-publish-into-other-story",
            );
            await capture("scene-native-switched");
            await c.switchSession(selectedSession);
            await refresh();
            await v2.status();
            check(
                !v2.get().uncertain && v2.get().receipt === null,
                "old-known-commit-resolves-without-stale-receipt-publication",
            );

            const lensHold = gate();
            gateway.heldCommit = lensHold;
            await draft();
            const lensPending = v2.send();
            await waitGate(lensHold, "actual-commit-held-before-lens-switch");
            c.requestLab();
            c.acknowledgeLab(true);
            c.setObserver("mira");
            await refresh();
            release(lensHold);
            await lensPending;
            check(
                v2.get().receipt === null &&
                    v2.get().context?.observer.kind === "character",
                "retired-completion-cannot-publish-private-receipt-into-character-lens",
            );
            await v2.status();
            const labSubmissions = gateway.submissions.length;
            await v2.send();
            check(
                v2.get().error === "Busy" &&
                    gateway.submissions.length === labSubmissions,
                "actual-Story-Lab-lens-has-no-generation-or-submit-authority",
            );
            const read = async (view: "knowledge" | "history") => {
                const result = await v2.readQuery({
                    view,
                    atRevision: null,
                    search: "",
                });
                check(!!result, `actual-${view}-observer-query`);
                return result as V2BoundPage;
            };
            const beforeInspect = await oracle("before-observer-inspection", 5);
            let actor = await read("knowledge");
            check(
                structural(actor.page).includes(A) &&
                    ![B, REASON].some((s) =>
                        structural(actor.page).includes(s),
                    ),
                "Mira-retains-observed-A-not-world-B-or-author-reason",
            );
            actor = await read("history");
            check(
                ![B, REASON].some((s) => structural(actor.page).includes(s)),
                "Mira-history-excludes-private-author-truth-and-reason",
            );
            c.setObserver("sable");
            await refresh();
            actor = await read("knowledge");
            check(
                ![A, B, REASON, PRIVATE].some((s) =>
                    structural(actor.page).includes(s),
                ),
                "Sable-never-inherits-unobserved-knowledge",
            );
            actor = await read("history");
            check(
                ![B, REASON, PRIVATE].some((s) =>
                    structural(actor.page).includes(s),
                ),
                "Sable-history-excludes-private-original-message-and-author-content",
            );
            c.setObserver("mira");
            await refresh();
            await read("knowledge");
            unchangedCanon(
                beforeInspect,
                await oracle("after-observer-inspection", 5),
                "inspection-privilege-never-mutates-character-knowledge",
            );
            await capture("scene-native-observer");
            c.setView("play");
            await refresh();
            await v2.status();
            actor = await read("knowledge");
            check(
                structural(actor.page).includes(A) &&
                    ![B, REASON].some((s) =>
                        structural(actor.page).includes(s),
                    ),
                "Player-keeps-own-observation-after-character-inspection",
            );
            actor = await read("history");
            check(
                ![B, REASON].some((s) => structural(actor.page).includes(s)),
                "Player-history-never-receives-author-truth-or-reason",
            );
            await invoke("harness_viewport", { preset: "wide" });
            await capture("scene-native-enlarged");
            finalOracle = await oracle("initial-final", 5);
            check(
                finalOracle.fixture_factories === 6 &&
                    finalOracle.fixture_polls === 12,
                "exact-six-synthetic-prepares-and-twelve-role-polls-no-hidden-generation",
            );
        }
        const records = errors.snapshot();
        const refusals = gateway.rejectedNativeCalls;
        // The fifth commit is already durable while its acknowledgement is held.
        // Switching the inspection lens must refuse its old revision read.
        const heldCommitReadFence =
            config.stage === "initial" &&
            finalOracle.head === baseline + 5 &&
            finalOracle.new_commits === 5 &&
            refusals.length === 1 &&
            refusals[0].op === "play_snapshot_v2" &&
            refusals[0].category === "Stale" &&
            refusals[0].phase === "actual-commit-held-before-lens-switch" &&
            structural(refusals[0].scope) === structural(scope) &&
            refusals[0].expectedRevision === baseline + 4 &&
            refusals[0].turn === null &&
            records.filter(
                (r) => r.source === "native" && r.category === "Stale",
            ).length === 1;
        check(
            config.stage === "restart"
                ? refusals.length === 0
                : heldCommitReadFence,
            "only-exact-held-commit-read-revision-is-refused-by-native",
        );
        check(
            records.length <= 8 &&
                records.every(
                    (r) =>
                        r.source === "native" &&
                        (["Transport", "Cancelled"].includes(r.category) ||
                            (heldCommitReadFence && r.category === "Stale")),
                ),
            "bounded-errors-contain-only-explicit-fault-or-cancel-categories",
        );
        if (config.stage === "restart")
            check(
                records.length === 0,
                "cold-restart-has-no-frontend-native-errors",
            );
        await dispose();
        const stats = (await invoke("harness_stats")) as {
            sessions: number;
            workers: number;
        };
        check(
            stats.sessions === 0 && stats.workers === 0,
            "owned-native-Host-sessions-and-workers-drained",
        );
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                stage: config.stage,
                sceneCase: config.sceneCase,
                checks,
                proofs,
                finalOracle,
                errors: records,
                rejectedNativeCalls: gateway.rejectedNativeCalls,
                realModelGeneration: false,
                nativeIpc: true,
                rendering: "native-webview2",
                desktopControl: false,
            },
        });
    } catch (error) {
        for (const release of releases) release();
        try {
            await dispose();
        } catch {
            /* Original failure remains authoritative. */
        }
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                stage: config.stage,
                sceneCase: config.sceneCase,
                failedCheck: current,
                error: String(
                    error instanceof Error ? error.message : error,
                ).slice(0, 500),
                checks,
                proofs,
                v2: v2.get(),
                errors: errors.snapshot(),
                rejectedNativeCalls: gateway.rejectedNativeCalls,
                realModelGeneration: false,
                desktopControl: false,
            },
        });
    }
}
