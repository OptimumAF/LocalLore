// Independent FIRST source freeze: UNCOMPILED / UNFORMATTED / UNRUN.
// Existing synthetic literal provider, actual mounted UI/Main/controllers/IPC/Store.
import type { Controller } from "./controller";
import type { FaultGateway } from "./journeys";
import type { V2PlayController } from "./v2-play-controller";
import { structural, type ErrorBuffer, type Scope } from "./model";
import { attemptKey } from "./trace-model";

type Invoke = (
    command: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
type Oracle = {
    version: number;
    synthetic: boolean;
    case: string;
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
const scope = { story: "scene-native-controls", branch: "main" };
const READ = "Read selected narration validation",
    CANCEL = "Cancel metadata read locally";
const SUCCESS = [
    "ready",
    "recorded",
    "pending",
    "local-cancel",
    "unavailable",
    "refused",
    "observer",
    "switched",
    "enlarged",
    "restarted",
].map((s) => `d06-live-${s}`);
function gate() {
    let ready!: () => void, release!: () => void;
    const entered = new Promise<void>((resolve) => {
        ready = resolve;
    });
    const waiting = new Promise<void>((resolve) => {
        release = resolve;
    });
    return { entered, waiting, ready, release };
}
export async function liveNarrationNativeJourneys({
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
    config: {
        stage: string;
        sceneCase: "literal" | "memory";
        liveNarrationDiagnostic: boolean;
    };
}) {
    const checks: string[] = [],
        proofs: { label: string; value: Oracle }[] = [],
        captures = new Set<string>();
    const releases = new Set<() => void>(),
        outstanding = new Set<Promise<void>>();
    let current = "d06-live-start",
        finalOracle: Oracle | null = null,
        committed = 0;
    let originalTurn: string | null = null,
        originalAttempt: number | null = null;
    let committedReceipt: ReturnType<V2PlayController["get"]>["receipt"] = null;
    const diagnostic = () => c.get().trace.narrationValidation;
    const check = (condition: unknown, label: string) => {
        current = label;
        gateway.diagnosticPhase = label;
        if (!condition) throw Error(label);
        if (checks.length >= 512) throw Error("LiveNarrationAssertionBudget");
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
        throw Error(`LiveNarrationDeadline:${label}`);
    };
    const bounded = async <T>(
        promise: Promise<T>,
        label: string,
    ): Promise<T> => {
        let done = false,
            failed = false,
            failure: unknown,
            value!: T;
        // Observe both outcomes immediately, including after local cancellation.
        const observed = promise.then(
            (result) => {
                value = result;
                done = true;
            },
            (error) => {
                failed = true;
                failure = error;
                done = true;
            },
        );
        outstanding.add(observed);
        void observed.then(() => outstanding.delete(observed));
        await until(() => done, label);
        if (failed) throw failure;
        return value;
    };
    const oracle = async (label: string, count = committed) => {
        const value = (await bounded(
            invoke("harness_scene_oracle"),
            `${label}-Store-proof-returned`,
        )) as Oracle;
        check(
            value.version === 1 &&
                value.synthetic === true &&
                value.case === "literal" &&
                structural(value.scope) === structural(scope) &&
                value.baseline_head === 1 &&
                value.domain_version === 1 &&
                value.new_commits === count &&
                value.head === 1 + count &&
                value.untouched_preserved === true &&
                value.other_preserved === true &&
                value.observer_isolated === true &&
                value.real_model === false &&
                /^[a-f0-9]{64}$/.test(value.canonical_sha256),
            `${label}-actual-Store-canonical-prefix-other-branch-story-and-observer-proof`,
        );
        if (proofs.length >= 64) throw Error("LiveNarrationProofBudget");
        proofs.push({ label, value });
        return value;
    };
    const unchanged = (before: Oracle, after: Oracle, label: string) => {
        check(
            before.head === after.head &&
                before.canonical_sha256 === after.canonical_sha256 &&
                structural(before.observer_sha256) ===
                    structural(after.observer_sha256),
            `${label}-canonical-and-observer-bytes-unchanged`,
        );
        check(
            before.fixture_factories === after.fixture_factories &&
                before.fixture_polls === after.fixture_polls,
            `${label}-no-provider-factory-or-poll`,
        );
    };
    const refreshed = async () => {
        await bounded(v2.refresh(), "actual-current-V2-refresh-returned");
        await until(
            () =>
                !!v2.get().snapshot && !!v2.get().history && !v2.get().readBusy,
            "actual-current-V2-state-ready",
        );
    };
    const buttons = (parent: ParentNode, text: string) =>
        [...parent.querySelectorAll<HTMLButtonElement>("button")].filter(
            (node) => node.textContent?.trim() === text,
        );
    const button = (parent: ParentNode, text: string) => {
        const found = buttons(parent, text);
        check(
            found.length === 1 && !found[0].disabled,
            `mounted-enabled-${text}`,
        );
        return found[0];
    };
    const tracePanel = () =>
        document.querySelector<HTMLElement>(".turn-debugger");
    const metadataPanel = () =>
        document.querySelector<HTMLElement>(
            '[aria-labelledby="narration-validation-title"]',
        );
    const domReady = () => {
        const state = c.get(),
            source = state.play ?? state.playV2,
            panel = tracePanel(),
            detail = metadataPanel();
        if (
            !panel ||
            !detail ||
            !source ||
            state.trace.busy ||
            state.trace.controlBusy ||
            !panel.textContent?.includes(`displayed head r${source.revision}`)
        )
            return false;
        const actual = diagnostic(),
            text = detail.textContent ?? "",
            query = actual.query;
        if (
            query &&
            (!text.includes(query.session) ||
                !text.includes(query.turn) ||
                !text.includes(query.scope.story) ||
                !text.includes(query.scope.branch) ||
                !text.includes(`read head r${query.expected_head}`) ||
                !text.includes(`r${query.base_revision}`) ||
                !text.includes(`attempt ${query.attempt}`))
        )
            return false;
        if (state.view !== "lab" || state.observer !== "omniscient")
            return (
                /unavailable in this lens/i.test(text) &&
                !detail.querySelector("dl")
            );
        if (actual.status === "recorded")
            return (
                /Recorded narration validation decision/.test(text) &&
                text.includes(
                    actual.reply?.status === "recorded"
                        ? actual.reply.decision.outcome
                        : "<absent>",
                )
            );
        if (actual.status === "pending")
            return /Metadata read pending/.test(text);
        if (actual.status === "cancelled")
            return /cancelled locally/.test(text);
        if (actual.status === "refused")
            return text.includes(`Metadata read refused: ${actual.error}`);
        if (actual.status === "unavailable") return /unavailable/i.test(text);
        return buttons(detail, READ).length === 1;
    };
    const frame = () =>
        new Promise<void>((resolve) =>
            requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
        );
    const geometry = (node: HTMLElement | null, role: string) => {
        if (!node)
            return {
                role,
                present: false,
                positiveArea: false,
                inViewport: false,
                hit: false,
                rect: null,
            };
        const rect = node.getBoundingClientRect(),
            positiveArea =
                [rect.x, rect.y, rect.width, rect.height].every(
                    Number.isFinite,
                ) &&
                rect.width > 0 &&
                rect.height > 0;
        const inViewport =
            positiveArea &&
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.right <= innerWidth &&
            rect.bottom <= innerHeight;
        const hit = inViewport
            ? document.elementFromPoint(
                  rect.left + rect.width / 2,
                  rect.top + rect.height / 2,
              )
            : null;
        return {
            role,
            present: true,
            positiveArea,
            inViewport,
            hit: !!hit && (hit === node || node.contains(hit)),
            rect: {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
                top: rect.top,
                bottom: rect.bottom,
            },
        };
    };
    const capture = async (label: string, failure = false) => {
        if (
            (!SUCCESS.includes(label) && label !== "d06-live-failure") ||
            captures.has(label) ||
            captures.size >= 10
        )
            throw Error("ClosedLiveNarrationCaptureRoster");
        if (!failure)
            await until(
                domReady,
                `${label}-actual-DOM-bound-to-current-context-and-diagnostic`,
            );
        await frame();
        const panel = tracePanel(),
            detail = metadataPanel(),
            status =
                detail?.querySelector<HTMLElement>('[role="status"]') ?? null;
        const controls =
            detail?.querySelector<HTMLElement>(".trace-controls") ?? null;
        const context =
            detail?.querySelector<HTMLElement>(".scope") ??
            panel?.querySelectorAll<HTMLElement>("p")[1] ??
            null;
        (detail ?? panel)?.scrollIntoView({ block: "center" });
        await frame();
        const state = c.get(),
            selected = c.selected(),
            source = state.play ?? state.playV2,
            view = v2.get();
        const native = failure ? null : await oracle(`${label}-capture`);
        const root = document.getElementById("root"),
            location = state.workspace?.location ?? "<none>";
        const boxes = [
            geometry(context, "actual-session-source-or-lens-context"),
            geometry(controls, "actual-read-cancel-controls"),
            geometry(status, "actual-diagnostic-status"),
        ];
        const snapshot = {
            version: 1,
            kind: "d06_live_narration_snapshot_v1",
            synthetic: true,
            label,
            uiRevision: source?.revision ?? selected?.revision ?? 0,
            aggregate: {
                session: selected?.id ?? null,
                scope: selected?.scope ?? null,
                observer: state.view === "play" ? "player" : state.observer,
                head: source?.revision ?? selected?.revision ?? 0,
                pendingOperation:
                    view.pending ?? view.uncertain ?? state.pending,
                receipt: view.receipt,
                visibleError:
                    diagnostic().error ?? view.error ?? state.visibleError,
                selectedBase: state.trace.baseRevision,
                selectedTurn: c.traceAttempt()?.identity.turn ?? null,
                selectedAttempt: c.traceAttempt()?.identity.attempt ?? null,
                nativeStoreHead: native?.head ?? null,
            },
            diagnostic: diagnostic(),
            trace: state.trace,
            v2: {
                context: view.context,
                pending: view.pending,
                uncertain: view.uncertain,
                status: view.status,
                receipt: view.receipt,
                error: view.error,
            },
            priorCanonicalEvidence:
                committedReceipt &&
                (state.view === "play" || state.observer === "omniscient")
                    ? {
                          source: "actual-earlier-commit-not-current-display",
                          request: committedReceipt.request,
                          events: committedReceipt.events,
                          narration: committedReceipt.narration,
                      }
                    : null,
            provider: state.freeTextProvider,
            model: state.model,
            oracle: native,
            checks: [...checks],
            diagnosticCommands: gateway.narrationValidationCalls,
            gameplayCancelCalls: gateway.gameplayCancelCalls,
            errors: errors.snapshot(),
            rejectedNativeCalls: gateway.rejectedNativeCalls,
            dom: {
                userAgent: navigator.userAgent,
                viewport: { width: innerWidth, height: innerHeight },
                geometry: boxes,
                text: (root?.textContent ?? "")
                    .slice(0, 48000)
                    .replaceAll(location, "<synthetic-workspace>"),
                structure: [
                    ...(root?.querySelectorAll(
                        "button,input,textarea,select,[role],h2,h3,dt,dd",
                    ) ?? []),
                ]
                    .slice(0, 256)
                    .map((node) => ({
                        tag: node.tagName,
                        role: node.getAttribute("role"),
                        label:
                            node.getAttribute("aria-label") ??
                            node.textContent?.slice(0, 160),
                        disabled: node.hasAttribute("disabled"),
                        value:
                            node instanceof HTMLInputElement ||
                            node instanceof HTMLTextAreaElement ||
                            node instanceof HTMLSelectElement
                                ? node.value.slice(0, 2048)
                                : null,
                    })),
            },
        };
        captures.add(label); // Preserve PNG/snapshot before failing a visibility oracle.
        const result = (await bounded(
            invoke("harness_checkpoint", { label, snapshot }),
            `${label}-native-checkpoint-returned`,
        )) as { rendering: string };
        if (!failure) {
            check(
                result.rendering === "native-webview2",
                `${label}-actual-application-WebView2-CapturePreview`,
            );
            check(
                boxes.every(
                    (box) =>
                        box.present &&
                        box.positiveArea &&
                        box.inViewport &&
                        box.hit,
                ),
                `${label}-positive-visible-unoccluded-context-controls-status`,
            );
            check(
                document.documentElement.scrollWidth <= innerWidth + 2,
                `${label}-no-horizontal-overflow`,
            );
            check(
                !!selected &&
                    !!source &&
                    structural(selected.scope) === structural(source.scope) &&
                    view.context?.session === selected.id &&
                    view.context?.revision === source.revision,
                `${label}-coherent-actual-session-head-and-view`,
            );
        }
    };
    const lab = async () => {
        c.requestLab();
        c.acknowledgeLab(true);
        await refreshed();
        await bounded(c.showTrace(true), "actual-debugger-open");
    };
    const selectOriginal = async (turn: string, base: number) => {
        if (c.get().observer !== "omniscient") c.setObserver("omniscient");
        await bounded(
            c.traceBasis(base),
            "actual-selected-original-basis-read",
        );
        await until(
            () => !c.get().trace.busy && !!c.get().trace.reply,
            "actual-selected-trace-returned",
        );
        const attempts = c
            .get()
            .trace.reply!.snapshot.attempts.filter(
                (entry) =>
                    entry.identity.turn === turn &&
                    entry.identity.base_revision === base &&
                    entry.identity.observer === c.get().playV2?.player.observer,
            );
        check(
            attempts.length === 1,
            "unique-real-retained-attempt-for-exact-receipt-turn-and-base",
        );
        const actual = attempts[0];
        await until(
            () =>
                !!document.querySelector(".trace-attempts") &&
                [
                    ...document.querySelectorAll<HTMLButtonElement>(
                        ".trace-attempts button",
                    ),
                ].some((node) => node.textContent?.trim().startsWith(turn)),
            "actual-original-attempt-button-mounted",
        );
        const found = [
            ...document.querySelectorAll<HTMLButtonElement>(
                ".trace-attempts button",
            ),
        ].filter((node) => node.textContent?.trim().startsWith(turn));
        check(
            found.length === 1 && !found[0].disabled,
            "exact-original-attempt-mounted-selection-handler",
        );
        found[0].click();
        check(
            c.get().trace.selected === attemptKey(actual),
            "mounted-selection-resolves-original-attempt-not-reread-latest",
        );
        return actual.identity.attempt;
    };
    const readMounted = async () => {
        await until(
            () =>
                domReady() &&
                buttons(metadataPanel()!, READ).length === 1 &&
                !buttons(metadataPanel()!, READ)[0].disabled,
            "actual-enabled-selected-read-mounted",
        );
        button(metadataPanel()!, READ).click();
        await until(
            () =>
                ["recorded", "unavailable", "refused"].includes(
                    diagnostic().status,
                ),
            "actual-diagnostic-reply-settled",
        );
        await until(domReady, "actual-diagnostic-reply-mounted");
    };
    const checkAccepted = (turn: string, base: number, attempt: number) => {
        const state = diagnostic(),
            q = state.query,
            reply = state.reply;
        check(
            state.status === "recorded" &&
                !!q &&
                q.session === c.selected()?.id &&
                q.turn === turn &&
                q.attempt === attempt &&
                q.base_revision === base &&
                q.expected_head === c.get().playV2?.revision &&
                structural(q.scope) === structural(scope) &&
                reply?.status === "recorded" &&
                reply.decision.outcome === "accepted" &&
                reply.decision.error === null &&
                reply.decision.reason === null &&
                reply.generation_grant === false,
            "actual-accepted-optional-validator-decision-is-not-canonical-commit-or-quality-proof",
        );
        check(
            c.debugReceipt() === null,
            "thin-metadata-debugger-never-promotes-legacy-receipt-inspection",
        );
    };
    const holdRead = async () => {
        const held = gate();
        releases.add(held.release);
        gateway.heldNarrationValidation = held;
        const promise = c.readTraceNarrationValidation();
        // Observe immediately even when a later assertion fails before release.
        const observed = promise.then(
            () => {},
            () => {},
        );
        outstanding.add(observed);
        void observed.then(() => outstanding.delete(observed));
        let entered = false;
        void held.entered.then(() => {
            entered = true;
        });
        await until(
            () => entered && diagnostic().status === "pending",
            "real-native-response-returned-before-finite-delay-gate",
        );
        return { held, promise };
    };
    const releaseRead = async (value: Awaited<ReturnType<typeof holdRead>>) => {
        value.held.release();
        releases.delete(value.held.release);
        await bounded(value.promise, "delayed-real-native-response-observed");
    };
    try {
        check(
            config.liveNarrationDiagnostic === true &&
                config.sceneCase === "literal" &&
                ["initial", "restart"].includes(config.stage),
            "closed-native-mode-literal-fixture-and-two-stages",
        );
        await bounded(c.start(), "actual-workspace-start");
        await bounded(c.resume(scope), "actual-literal-parent-resume");
        await bounded(
            c.refreshFreeTextProvider(),
            "existing-native-fixture-capability",
        );
        await bounded(c.refreshModel(), "existing-native-model-status");
        check(
            c.get().freeTextProvider?.kind === "synthetic_fixture" &&
                c.get().model?.loaded === false &&
                c.get().model?.imported === false &&
                c.get().model?.resident === false,
            "synthetic-provider-separate-from-unloaded-unimported-model-manager",
        );
        c.setPlayMode("local");
        c.setInputKind("action");
        await refreshed();
        await bounded(
            invoke("harness_viewport", { preset: "capture-narrow" }),
            "actual-narrow-owned-WebView-viewport",
        );
        if (config.stage === "restart") {
            committed = 2;
            const reopened = await oracle("cold-reopen");
            await lab();
            await bounded(c.traceBasis(2), "cold-actual-trace-basis");
            const coldTrace = c.get().trace.reply;
            check(
                coldTrace?.snapshot.status === "disabled" &&
                    coldTrace.snapshot.attempts.length === 0 &&
                    diagnostic().query === null &&
                    diagnostic().reply === null &&
                    v2.get().receipt === null &&
                    c.receipt() === null,
                "cold-restart-default-disabled-empty-private-trace-and-no-invented-receipt",
            );
            const calls = gateway.narrationValidationCalls.length;
            await bounded(
                c.readTraceNarrationValidation(),
                "cold-no-selection-local-refusal",
            );
            check(
                diagnostic().status === "unavailable" &&
                    diagnostic().query === null &&
                    diagnostic().reply === null &&
                    gateway.narrationValidationCalls.length === calls,
                "cold-earlier-optional-decision-is-not-reconstructed-or-queried-with-guessed-identity",
            );
            await capture("d06-live-restarted");
            finalOracle = await oracle("cold-final");
            unchanged(reopened, finalOracle, "cold-all-read-only-work");
            check(
                finalOracle.fixture_factories === 0 &&
                    finalOracle.fixture_polls === 0,
                "cold-zero-provider-factories-and-polls",
            );
        } else {
            const fresh = await oracle("fresh", 0);
            await lab();
            await until(
                () =>
                    buttons(tracePanel()!, "Enable metadata").length === 1 &&
                    !buttons(tracePanel()!, "Enable metadata")[0].disabled,
                "actual-enable-metadata-mounted",
            );
            button(tracePanel()!, "Enable metadata").click();
            await until(
                () =>
                    c.get().trace.enabled === true &&
                    !c.get().trace.controlBusy &&
                    !c.get().trace.busy,
                "explicit-native-metadata-enable-complete",
            );
            await bounded(c.traceBasis(1), "initial-actual-basis-one");
            unchanged(
                fresh,
                await oracle("metadata-enabled", 0),
                "explicit-enable-without-generation",
            );
            await capture("d06-live-ready");
            c.returnToPlay();
            await refreshed();
            v2.setDraft(TEXT);
            await until(
                () =>
                    document.querySelector<HTMLTextAreaElement>(
                        ".v2-play textarea",
                    )?.value === TEXT,
                "actual-composer-original-fixed-text-mounted",
            );
            button(
                document.querySelector('[aria-label="Native turn composer"]')!,
                "Send to Rust",
            ).click();
            await until(
                () =>
                    v2.get().status?.phase === "committed" &&
                    !!v2.get().receipt &&
                    !v2.get().pending &&
                    !v2.get().readBusy &&
                    v2.get().snapshot?.revision === 2,
                "actual-mounted-free-text-commit-r1-to-r2",
            );
            committed = 1;
            committedReceipt = v2.get().receipt;
            originalTurn = committedReceipt!.request.turn;
            check(
                committedReceipt!.request.expected_revision === 1 &&
                    committedReceipt!.events.at(-1)?.sequence === 2 &&
                    structural(committedReceipt!.proposal.commands) ===
                        structural([{ op: "wait", ticks: 1 }]) &&
                    !!committedReceipt!.play?.scene,
                "actual-receipt-canonical-clock-effect-kept-separate-from-validator-metadata",
            );
            const generated = await oracle("first-free-text-commit");
            check(
                generated.fixture_factories === 1 &&
                    generated.fixture_polls === 2,
                "one-explicit-fixed-provider-factory-and-two-role-polls",
            );
            await lab();
            originalAttempt = await selectOriginal(originalTurn, 1);
            await readMounted();
            checkAccepted(originalTurn, 1, originalAttempt);
            check(
                diagnostic().query!.expected_head !==
                    diagnostic().query!.base_revision,
                "current-head-two-original-base-one-distinct",
            );
            await capture("d06-live-recorded");

            const beforeRead = await oracle("before-passive-pending"),
                cancels = gateway.gameplayCancelCalls,
                reads = gateway.narrationValidationCalls.length;
            const delayed = await holdRead(),
                pendingState = c.get();
            await bounded(
                c.readTraceNarrationValidation(),
                "duplicate-pending-read-returned",
            );
            check(
                c.get() === pendingState &&
                    gateway.narrationValidationCalls.length === reads + 1,
                "duplicate-preserves-original-pending-ticket-and-single-native-dispatch",
            );
            await capture("d06-live-pending");
            button(metadataPanel()!, CANCEL).click();
            check(
                diagnostic().status === "cancelled" &&
                    diagnostic().query === null &&
                    diagnostic().reply === null &&
                    diagnostic().error === null,
                "mounted-local-cancel-clears-query-decision-and-error-synchronously",
            );
            await capture("d06-live-local-cancel");
            await releaseRead(delayed);
            check(
                diagnostic().status === "cancelled" &&
                    diagnostic().reply === null &&
                    gateway.gameplayCancelCalls === cancels,
                "late-native-completion-cannot-refill-or-attempt-gameplay-Cancel",
            );
            await readMounted();
            checkAccepted(originalTurn, 1, originalAttempt);
            unchanged(
                beforeRead,
                await oracle("after-passive-retry"),
                "read-duplicate-local-cancel-and-explicit-retry",
            );

            const lensHeld = await holdRead();
            c.setObserver("mira");
            check(
                diagnostic().status === "idle" &&
                    diagnostic().query === null &&
                    diagnostic().reply === null,
                "character-switch-clears-private-diagnostic-before-await",
            );
            await releaseRead(lensHeld);
            await until(
                () => !c.get().trace.busy,
                "actual-character-trace-read-settled",
            );
            const lensCalls = gateway.narrationValidationCalls.length;
            await bounded(
                c.readTraceNarrationValidation(),
                "local-character-admission-refusal",
            );
            check(
                gateway.narrationValidationCalls.length === lensCalls &&
                    diagnostic().status === "unavailable" &&
                    diagnostic().reply === null,
                "character-diagnostic-denial-is-local-no-native-grant-denial-claim",
            );
            await capture("d06-live-observer");
            c.setObserver("player");
            await until(
                () => !c.get().trace.busy,
                "actual-player-lens-metadata-settled",
            );
            await bounded(
                c.readTraceNarrationValidation(),
                "local-player-lens-admission-refusal",
            );
            check(
                gateway.narrationValidationCalls.length === lensCalls &&
                    diagnostic().reply === null,
                "player-lens-has-no-new-diagnostic-IPC",
            );
            c.setObserver("omniscient");
            originalAttempt = await selectOriginal(originalTurn, 1);
            const selectedSession = c.selected()!.id,
                switchHeld = await holdRead();
            await bounded(
                c.resume({ story: "scene-native-other", branch: "main" }),
                "actual-other-story-resume",
            );
            await refreshed();
            await releaseRead(switchHeld);
            check(
                c.selected()?.scope.story === "scene-native-other" &&
                    diagnostic().query === null &&
                    diagnostic().reply === null,
                "late-original-session-completion-cannot-refill-other-story",
            );
            await capture("d06-live-switched");
            await bounded(
                c.switchSession(selectedSession),
                "original-session-reselected",
            );
            await refreshed();
            originalAttempt = await selectOriginal(originalTurn, 1);
            await readMounted();
            checkAccepted(originalTurn, 1, originalAttempt);
            unchanged(
                beforeRead,
                await oracle("after-observer-session-retirements"),
                "observer-player-session-retirement-and-return",
            );

            const keptTrace = c.get().trace.reply,
                keptSelection = c.get().trace.selected;
            await bounded(
                gateway.call({
                    op: "trace_clear",
                    session: c.selected()!.id,
                    scope,
                    expected_head: 2,
                }),
                "explicit-external-native-trace-clear",
            ); // No UI state injection.
            check(
                c.get().trace.reply === keptTrace &&
                    c.get().trace.selected === keptSelection,
                "external-native-clear-leaves-original-checked-frontend-selection",
            );
            await readMounted();
            check(
                diagnostic().status === "unavailable" &&
                    diagnostic().query?.turn === originalTurn &&
                    diagnostic().query?.attempt === originalAttempt &&
                    diagnostic().reply?.status === "unavailable" &&
                    !Object.hasOwn(diagnostic().reply!, "decision"),
                "actual-Host-unavailable-has-no-invented-validator-cause",
            );
            await capture("d06-live-unavailable");
            unchanged(
                beforeRead,
                await oracle("after-external-trace-clear"),
                "external-clear-and-native-unavailable-read",
            );

            const external = {
                version: 1 as const,
                scope,
                turn: "d06-live-external-wait",
                expected_revision: 2,
                intent: {
                    kind: "free_text" as const,
                    value: { kind: "action" as const, text: TEXT },
                },
            };
            const session = c.selected()!.id;
            const queued = (await bounded(
                gateway.call({ op: "free_text", session, request: external }),
                "explicit-external-free-text-submitted",
            )) as { phase: string };
            const ready = (await bounded(
                gateway.call({
                    op: "prepare",
                    session,
                    scope,
                    turn: external.turn,
                }),
                "explicit-external-fixed-provider-prepared",
            )) as { phase: string };
            const accepted = (await bounded(
                gateway.call({
                    op: "commit",
                    session,
                    scope,
                    turn: external.turn,
                }),
                "explicit-external-r3-commit-returned",
            )) as {
                phase: string;
                receipt: {
                    request: { turn: string };
                    events: { sequence: number }[];
                } | null;
            };
            check(
                queued.phase === "queued" &&
                    ready.phase === "ready" &&
                    accepted.phase === "committed" &&
                    accepted.receipt?.request.turn === external.turn &&
                    accepted.receipt.events.at(-1)?.sequence === 3 &&
                    c.get().playV2?.revision === 2,
                "explicit-second-fixed-provider-generation-commits-r2-to-r3-without-refreshing-UI",
            );
            committed = 2;
            const externalOracle = await oracle("external-stale-trigger");
            check(
                externalOracle.fixture_factories === 2 &&
                    externalOracle.fixture_polls === 4,
                "exact-two-intended-generations-four-role-polls-accounted",
            );
            await readMounted();
            check(
                diagnostic().status === "refused" &&
                    diagnostic().error === "Stale" &&
                    diagnostic().reply === null &&
                    diagnostic().query?.turn === originalTurn &&
                    diagnostic().query?.base_revision === 1 &&
                    diagnostic().query?.expected_head === 2,
                "actual-native-Stale-for-original-checked-r2-query-against-current-r3",
            );
            await capture("d06-live-refused");
            await refreshed();
            await bounded(c.traceBasis(2), "reconciled-base-two-metadata-read");
            const externalAttempt = await selectOriginal(external.turn, 2);
            await readMounted();
            checkAccepted(external.turn, 2, externalAttempt);
            await bounded(
                invoke("harness_viewport", { preset: "wide" }),
                "actual-wide-owned-WebView-viewport",
            );
            c.layout(1, 1, 1.5);
            await capture("d06-live-enlarged");
            finalOracle = await oracle("initial-final");
            unchanged(
                externalOracle,
                finalOracle,
                "stale-reconciliation-and-enlarged-read-only-view",
            );
            check(
                gateway.gameplayCancelCalls === 0 &&
                    gateway.submissions.length === 2,
                "exact-two-submissions-and-zero-attempted-native-gameplay-cancel",
            );
        }
        const records = errors.snapshot(),
            refusals = gateway.rejectedNativeCalls;
        check(
            config.stage === "restart"
                ? records.length === 0 && refusals.length === 0
                : records.length === 1 &&
                      records[0].source === "native" &&
                      records[0].category === "Stale" &&
                      refusals.length === 1 &&
                      refusals[0].op === "trace_narration_validation_read_v1" &&
                      refusals[0].category === "Stale",
            "expected-native-Stale-preserved-separately-from-unexpected-errors",
        );
        const expected =
            config.stage === "restart"
                ? ["d06-live-restarted"]
                : SUCCESS.filter((label) => label !== "d06-live-restarted");
        check(
            structural([...captures].sort()) ===
                structural([...expected].sort()),
            "exact-fixed-success-capture-roster",
        );
        await bounded(
            dispose(),
            "owned-Main-controller-and-native-sessions-disposed",
        );
        const stats = (await bounded(
            invoke("harness_stats"),
            "actual-owned-native-drain-statistics",
        )) as { sessions: number; workers: number };
        check(
            stats.sessions === 0 && stats.workers === 0,
            "owned-Host-session-and-worker-drain-observed",
        );
        await invoke("harness_finish", {
            report: {
                version: 1,
                kind: "d06_live_narration_native_v1",
                synthetic: true,
                passed: true,
                stage: config.stage,
                sceneCase: "literal",
                checks,
                proofs,
                finalOracle,
                errors: records,
                rejectedNativeCalls: refusals,
                diagnosticCommands: gateway.narrationValidationCalls,
                gameplayCancelCalls: gateway.gameplayCancelCalls,
                originalTurn,
                originalAttempt,
                nativeIpc: true,
                rendering: "native-webview2",
                desktopControl: false,
                realModelGeneration: false,
            },
        });
    } catch (error) {
        const failedCheck = current;
        for (const release of releases) release();
        releases.clear();
        try {
            await until(
                () => outstanding.size === 0,
                "failure-delayed-native-promises-observed",
            );
        } catch {
            /* Preserve the original failure. */
        }
        try {
            await capture("d06-live-failure", true);
        } catch {
            /* Original failure and any partial checkpoint remain retained. */
        }
        try {
            await bounded(dispose(), "failure-owned-Main-disposal");
        } catch {
            /* Do not replace the original failing oracle. */
        }
        await invoke("harness_finish", {
            report: {
                version: 1,
                kind: "d06_live_narration_native_v1",
                synthetic: true,
                passed: false,
                stage: config.stage,
                sceneCase: "literal",
                failedCheck,
                error: String(
                    error instanceof Error ? error.message : error,
                ).slice(0, 500),
                checks,
                proofs,
                finalOracle,
                errors: errors.snapshot(),
                rejectedNativeCalls: gateway.rejectedNativeCalls,
                diagnosticCommands: gateway.narrationValidationCalls,
                gameplayCancelCalls: gateway.gameplayCancelCalls,
                nativeIpc: true,
                rendering: "native-webview2",
                desktopControl: false,
                realModelGeneration: false,
            },
        });
    }
}
