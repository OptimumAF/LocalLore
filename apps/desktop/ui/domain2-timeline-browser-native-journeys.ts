// Fixed development-only D08 browser journey; independent source author UNRUN.
// Actual Main/controllers/DOM/IPC. No desktop input, window activation or model.
import type { Controller } from "./controller";
import type { TimelineController } from "./timeline-controller";
import { timelineContext } from "./timeline-controller";
import { decodeBranchCatalog } from "./timeline-model";
import type { V2PlayController } from "./v2-play-controller";
import type { FaultGateway } from "./journeys";
import {
    category,
    structural,
    type Command,
    type ErrorBuffer,
    type Scope,
} from "./model";

type Invoke = (
    name: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
type Oracle = {
    version: number;
    kind: string;
    fixture_version: number;
    scopes: {
        scope: Scope;
        domain_version: number;
        head: number;
        story_time: number;
        seed_sha256: string;
        projection_sha256: string;
        records_sha256: string;
        receipts_sha256: string;
        turns_sha256: string;
        actors_sha256: string;
    }[];
};
type Delivery = {
    kind: "error" | "hold";
    entered: boolean;
    delivered: boolean;
    command: Command | null;
    replySha256: string | null;
    release: () => void;
    waiting: Promise<void>;
};
const PARENT: Scope = { story: "d05-inspector-native", branch: "main" };
const CHILD: Scope = { story: "d05-inspector-native", branch: "paging" };
const OTHER: Scope = { story: "d05-inspector-other", branch: "main" };
const MODE = "domain2_timeline_browser_v1";
const LABELS = [
    "catalog",
    "root",
    "child",
    "observer",
    "enlarged-wide",
    "enlarged-narrow",
].map((name) => `d08-browser-${name}`);
const HEX = /^[a-f0-9]{64}$/;
async function digest(value: unknown) {
    const bytes = new TextEncoder().encode(JSON.stringify(value));
    return [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))]
        .map((byte) => byte.toString(16).padStart(2, "0"))
        .join("");
}

export async function domain2TimelineBrowserNativeJourneys({
    controller: c,
    timeline,
    v2,
    gateway,
    errors,
    invoke,
    dispose,
}: {
    controller: Controller;
    timeline: TimelineController;
    v2: V2PlayController;
    gateway: FaultGateway;
    errors: ErrorBuffer;
    invoke: Invoke;
    dispose: () => Promise<void>;
}): Promise<void> {
    const checks: string[] = [],
        names = new Set<string>(),
        captures: string[] = [],
        proofs: { label: string; oracle: Oracle }[] = [];
    const deliveries: {
        kind: string;
        command: Command;
        replySha256: string;
        outcome: string;
    }[] = [];
    const observations: Record<string, unknown>[] = [],
        fonts: Record<string, unknown>[] = [];
    const originalCall = gateway.call;
    let delivery: Delivery | null = null,
        baseline: Oracle | null = null,
        finalOracle: Oracle | null = null;
    let assertions = 0,
        current = "browser-setup",
        disposing = false;
    const deadline = performance.now() + 150000;
    const check = (value: unknown, name: string) => {
        current = name;
        gateway.diagnosticPhase = name;
        if (!value) throw Error(name);
        assertions++;
        if (!names.has(name)) {
            names.add(name);
            checks.push(name);
        }
    };
    const until = async (predicate: () => boolean, name: string) => {
        current = name;
        for (
            let count = 0;
            count < 1500 && performance.now() < deadline;
            count++
        ) {
            if (predicate()) return;
            await new Promise((resolve) => setTimeout(resolve, 10));
        }
        throw Error(`D08BrowserDeadline:${name}`);
    };
    const frames = () =>
        new Promise<void>((resolve, reject) => {
            const timer = setTimeout(
                () => reject(Error("D08BrowserRenderFramesTimeout")),
                5000,
            );
            requestAnimationFrame(() =>
                requestAnimationFrame(() => {
                    clearTimeout(timer);
                    resolve();
                }),
            );
        });
    const trace = () => gateway.inspectorPagingCalls;
    const branches = () =>
        trace().filter(
            (item) =>
                item.channel === "host" && item.command?.op === "branches",
        );
    const idle = async () => {
        await until(
            () =>
                !c.get().starting &&
                !timeline.get().busy &&
                !v2.get().readBusy &&
                !v2.get().queryBusy &&
                trace().every((item) => item.settled),
            "actual-Main-native-reads-and-delivery-idle",
        );
        await frames();
    };
    const panel = () =>
        document.querySelector<HTMLElement>(
            '[aria-labelledby="timeline-title"]',
        );
    const button = (text: string, parent: ParentNode = document) => {
        const matches = [
            ...parent.querySelectorAll<HTMLButtonElement>("button"),
        ].filter((node) => node.textContent?.trim() === text);
        check(matches.length === 1, `actual-unique-mounted-button:${text}`);
        return matches[0];
    };
    const click = (node: HTMLButtonElement, name: string) => {
        check(
            node.isConnected && !node.disabled,
            `${name}-connected-enabled-real-control`,
        );
        node.click();
    };
    const assertOwner = (scope: Scope, head: number, domain: 1 | 2) => {
        const selected = c.selected(),
            state = c.get(),
            play = state.play ?? state.playV2;
        check(
            selected &&
                play &&
                structural(selected.scope) === structural(scope) &&
                structural(play.scope) === structural(scope) &&
                selected.revision === head &&
                play.revision === head,
            "actual-selected-session-scope-and-snapshot-head",
        );
        if (domain === 2) {
            check(
                !state.play &&
                    state.playV2?.domain_version === 2 &&
                    v2.get().context?.revision === 44 &&
                    structural(v2.get().context?.scope) === structural(CHILD),
                "actual-Domain2-thin-Main-and-V2-child44",
            );
            check(
                !document.querySelector(".fork-panel") &&
                    ![...document.querySelectorAll("button")].some((node) =>
                        /^(Create alternate timeline|Timeline creation & recovery)$/.test(
                            node.textContent?.trim() ?? "",
                        ),
                    ),
                "Domain2-Fork-panel-and-entry-control-remain-unavailable",
            );
        } else
            check(
                state.play && !state.playV2,
                "actual-root0-legacy-snapshot-route",
            );
        const context = timelineContext(c);
        check(
            context &&
                context.session === selected!.id &&
                context.revision === head &&
                structural(context.scope) === structural(scope) &&
                context.view === state.view &&
                context.observer === state.observer &&
                context.persistent &&
                timeline.matchesContext(context),
            "actual-browser-context-owned-by-current-Main-selection",
        );
    };
    const catalog = () => {
        const s = timeline.get();
        check(
            s.shown && !s.busy && s.status === "ready" && !s.error && s.catalog,
            "actual-browser-ready-metadata",
        );
        const checked = decodeBranchCatalog(s.catalog, CHILD.story);
        check(
            checked.version === 2 &&
                checked.branches.length === 2 &&
                checked.root_branch === "main",
            "fixed-fixture-real-catalog2-two-branches",
        );
        const root = checked.branches.find(
                (row) => row.scope.branch === "main",
            ),
            child = checked.branches.find(
                (row) => row.scope.branch === "paging",
            );
        check(
            root &&
                root.revision === 0 &&
                root.parent_branch === null &&
                root.fork_revision === null &&
                !root.retired &&
                child &&
                child.revision === 44 &&
                child.parent_branch === "main" &&
                child.fork_revision === 0 &&
                !child.retired,
            "actual-root0-child44-immutable-ancestry",
        );
        const list = panel()?.querySelector(
            '[aria-label="Saved timeline metadata"]',
        );
        check(
            list && list.querySelectorAll(":scope > li").length === 2,
            "mounted-actual-two-catalog-rows",
        );
        for (const row of checked.branches) {
            const active =
                structural(row.scope) === structural(c.selected()!.scope);
            const node = button(
                `${active ? "Selected" : "Resume"} timeline ${row.scope.branch}`,
                panel()!,
            );
            check(
                node.disabled === active,
                `actual-${row.scope.branch}-current-or-resumable-control`,
            );
            const text = node.closest("li")?.textContent ?? "";
            check(
                text.includes("Catalogued head:") &&
                    text.includes(String(row.revision)) &&
                    text.includes("Ancestry:"),
                `actual-${row.scope.branch}-visible-head-and-ancestry`,
            );
        }
        check(
            !/Author corrections remain unavailable|Domain2 timeline navigation[^.]*unavailable/i.test(
                panel()!.innerText,
            ),
            "browser-copy-does-not-deny-existing-author-or-navigation-capability",
        );
        return checked;
    };
    const show = async () => {
        if (!timeline.get().shown)
            click(button("Saved timelines"), "open-actual-browser");
        await until(
            () =>
                timeline.get().shown &&
                !timeline.get().busy &&
                timeline.get().status === "ready",
            "mounted-browser-catalog-completed",
        );
        await idle();
        catalog();
    };
    const oracle = async (label: string) => {
        const value = (await invoke("harness_v2_inspection_paging")) as Oracle;
        check(
            value &&
                Object.keys(value).sort().join(",") ===
                    "fixture_version,kind,scopes,version" &&
                value.version === 1 &&
                value.fixture_version === 1 &&
                value.kind === "v2_inspection_paging_oracle_v1" &&
                Array.isArray(value.scopes) &&
                value.scopes.length === 3,
            `${label}-actual-existing-closed-Rust-oracle`,
        );
        const expected = [
            [PARENT, 1, 0],
            [CHILD, 2, 44],
            [OTHER, 1, 1],
        ] as const;
        value.scopes.forEach((scope, index) => {
            check(
                structural(scope.scope) === structural(expected[index][0]) &&
                    scope.domain_version === expected[index][1] &&
                    scope.head === expected[index][2] &&
                    scope.story_time === 100,
                `${label}-scope${index}-original-head-domain-clock`,
            );
            for (const field of [
                "seed_sha256",
                "projection_sha256",
                "records_sha256",
                "receipts_sha256",
                "turns_sha256",
                "actors_sha256",
            ] as const)
                check(
                    HEX.test(scope[field]),
                    `${label}-scope${index}-${field}`,
                );
        });
        if (baseline)
            check(
                structural(value) === structural(baseline),
                `${label}-all3-canonical-and-observer-fingerprints-unchanged`,
            );
        proofs.push({ label, oracle: value });
        return value;
    };
    const safeText = () => {
        const text = panel()?.innerText ?? "";
        check(
            ![
                "D05_UNOBSERVED_AUTHOR_TRUTH_913",
                "D05_AUTHOR_REASON_PRIVATE_914",
                "D05_PLAYER_SEED_SECRET_731",
                "D05_MIRA_PRIVATE_BELIEF_812",
                "D05_OTHER_STORY_SEED_515",
                "D05_OTHER_STORY_MESSAGE_516",
            ].some((secret) => text.includes(secret)),
            "catalog-metadata-never-renders-story-or-observer-secret-bodies",
        );
        return text;
    };
    const active = () =>
        document.activeElement instanceof HTMLElement
            ? `${document.activeElement.tagName}:${document.activeElement.getAttribute("aria-label") ?? document.activeElement.textContent?.trim().slice(0, 120) ?? ""}`
            : "Unavailable";
    const semantic = () => {
        const state = c.get(),
            scoped = v2.get(),
            selected = c.selected(),
            t = timeline.get();
        const receiptRegion = document.querySelector<HTMLElement>(
            '[aria-label="Actual native receipt"]',
        );
        return {
            synthetic: true,
            semanticVersion: 1,
            mode: MODE,
            uiRevision: selected?.revision ?? 0,
            selectedStory: selected?.scope ?? null,
            session: selected?.id ?? null,
            observer: state.view === "play" ? "player" : state.observer,
            view: state.view,
            player: (state.play ?? state.playV2)?.player.observer ?? null,
            revision: (state.play ?? state.playV2)?.revision ?? null,
            pendingOperation: t.busy
                ? { phase: t.status, session: selected?.id ?? null }
                : null,
            gameplayPending: scoped.pending
                ? {
                      stage: scoped.pending.stage,
                      turn: scoped.pending.request.turn,
                  }
                : state.pending
                  ? { stage: state.pending.stage }
                  : null,
            displayedReceipt: receiptRegion
                ? {
                      displayed: true,
                      text: receiptRegion.innerText.slice(0, 2048),
                      turn: scoped.receipt?.request.turn ?? null,
                  }
                : {
                      displayed: false,
                      reason: "No mounted actual-native-receipt region; no receipt inferred from navigation",
                  },
            visibleError: t.error ?? scoped.error ?? state.visibleError,
            browser: {
                shown: t.shown,
                busy: t.busy,
                status: t.status,
                notice: t.notice,
                catalog: t.catalog,
            },
            dom: {
                text: safeText().slice(0, 16000),
                active: active(),
                width: innerWidth,
                height: innerHeight,
                textScale: state.textScale,
                userAgent: navigator.userAgent,
            },
            errors: errors.snapshot(),
            traceCount: trace().length,
        };
    };
    const observe = (label: string) => {
        const value = { label, ...semantic() };
        check(
            new TextEncoder().encode(JSON.stringify(value)).length <= 65536,
            `${label}-bounded-semantic-observation`,
        );
        observations.push(value);
    };
    const capture = async (label: string, failure = false) => {
        if (!failure)
            check(
                LABELS[captures.length] === label,
                `${label}-fixed-six-roster-order`,
            );
        const region = panel();
        if (!failure) check(region, `${label}-actual-mounted-browser-required`);
        region?.scrollIntoView({ block: "start" });
        await frames();
        const nodes = region
            ? [
                  region.querySelector<HTMLElement>(".panel-heading"),
                  region.querySelector<HTMLElement>("h3"),
                  ...region.querySelectorAll<HTMLButtonElement>("button"),
              ]
            : [];
        const geometry = nodes
            .filter((node): node is HTMLElement => !!node)
            .map((node) => {
                const r = node.getBoundingClientRect();
                const visible =
                    r.width > 0 &&
                    r.height > 0 &&
                    [r.left, r.top, r.right, r.bottom].every(Number.isFinite) &&
                    r.left >= -2 &&
                    r.top >= -2 &&
                    r.right <= innerWidth + 2 &&
                    r.bottom <= innerHeight + 2;
                const hits = [0.05, 0.5, 0.95].map((point) => {
                    if (!visible) return false;
                    const found = document.elementFromPoint(
                        r.left + r.width / 2,
                        r.top +
                            Math.max(
                                1,
                                Math.min(r.height - 1, r.height * point),
                            ),
                    );
                    return !!found && (node === found || node.contains(found));
                });
                if (!failure)
                    check(
                        visible && hits.every(Boolean),
                        `${label}-actual-control-heading-fit-and-unoccluded`,
                    );
                return {
                    tag: node.tagName,
                    text: node.innerText.slice(0, 1024),
                    rect: {
                        x: r.x,
                        y: r.y,
                        width: r.width,
                        height: r.height,
                        right: r.right,
                        bottom: r.bottom,
                    },
                    visible,
                    hits,
                };
            });
        if (!failure)
            check(
                document.documentElement.scrollWidth <= innerWidth + 2 &&
                    region!.scrollWidth <= region!.clientWidth + 2,
                `${label}-no-document-or-browser-horizontal-overflow`,
            );
        const snapshot = {
            ...semantic(),
            geometry,
            fontMeasurements: fonts,
            checks: checks.slice(-120),
        };
        check(
            new TextEncoder().encode(JSON.stringify(snapshot)).length <= 262144,
            `${label}-bounded-semantic-checkpoint`,
        );
        const result = (await invoke("harness_checkpoint", {
            label,
            snapshot,
        })) as { rendering?: string };
        if (!failure) {
            check(
                result?.rendering === "native-webview2",
                `${label}-actual-app-owned-native-CapturePreview`,
            );
            captures.push(label);
        }
    };
    const finish = async (report: Record<string, unknown>) => {
        const value = {
            synthetic: true,
            mode: MODE,
            checks,
            assertions,
            distinctChecks: checks.length,
            captures,
            nativeCaptures: captures.length,
            baseline,
            finalOracle,
            proofs,
            observations,
            deliveries,
            fontMeasurements: fonts,
            calls: trace(),
            errors: errors.snapshot(),
            realModelGeneration: false,
            desktopInput: false,
            rendering: captures.length ? "native-webview2" : "unavailable",
            unavailable: [
                "Source author did not execute; Root must individually review every actual image",
                "Branches hold/error are post-real-IPC delivery doubles, not native Host refusal or worker cancellation",
                "No physical keyboard/screenreader, restart/process death, Android, model, offline/network or OS isolation qualification",
            ],
            ...report,
        };
        if (new TextEncoder().encode(JSON.stringify(value)).length > 262144)
            throw Error("D08BrowserFinalReportBudget");
        await invoke("harness_finish", { report: value });
    };
    const armDelivery = (kind: Delivery["kind"]) => {
        check(delivery === null, "one-fixed-local-branches-delivery-at-a-time");
        let release!: () => void;
        const waiting = new Promise<void>((resolve) => {
            release = resolve;
        });
        delivery = {
            kind,
            entered: false,
            delivered: false,
            command: null,
            replySha256: null,
            release,
            waiting,
        };
        return delivery;
    };
    const releaseDelivery = () => {
        const held = delivery;
        if (held) held.release();
        delivery = null;
    };
    gateway.call = async function (command: Command): Promise<unknown> {
        const value = await originalCall.call(gateway, command);
        const held = delivery;
        if (command.op !== "branches" || !held || held.entered) return value;
        check(
            command.story === CHILD.story,
            "delivery-double-binds-only-fixed-real-story-branches-read",
        );
        held.command = structuredClone(command);
        held.replySha256 = await digest(value);
        held.entered = true;
        await held.waiting;
        held.delivered = true;
        deliveries.push({
            kind: held.kind,
            command: held.command,
            replySha256: held.replySha256,
            outcome:
                held.kind === "error"
                    ? "local-Transport-after-native-success"
                    : "delivered-after-context-retirement",
        });
        if (held.kind === "error") throw Error("Transport");
        return value;
    };
    const resumeButton = async (
        branch: "main" | "paging",
        scope: Scope,
        head: number,
        domain: 1 | 2,
    ) => {
        const before = trace().length;
        click(
            button(`Resume timeline ${branch}`, panel()!),
            `actual-Resume-${branch}`,
        );
        await until(
            () =>
                structural(c.selected()?.scope) === structural(scope) &&
                (c.get().play ?? c.get().playV2)?.revision === head &&
                !c.get().starting,
            `real-selected-${branch}-normal-resume-completed`,
        );
        await idle();
        assertOwner(scope, head, domain);
        await show();
        const calls = trace()
            .slice(before)
            .filter(
                (item) =>
                    item.channel === "host" &&
                    (item.command?.op === "resume" ||
                        item.command?.op === "open"),
            );
        check(
            calls.length > 0 &&
                calls.every(
                    (item) =>
                        (item.command?.op === "resume" ||
                            item.command?.op === "open") &&
                        structural(item.command.scope) === structural(scope),
                ),
            `${branch}-actual-open-or-resume-has-no-different-or-recent-fallback`,
        );
    };
    const assertCalls = (afterDispose: boolean) => {
        const allowed = new Set([
            "workspace",
            "branches",
            "resume",
            "open",
            "close",
            "play_snapshot",
            "play_snapshot_v2",
            "inspection_query",
            "inspect",
            "trace_capture_revoke",
        ]);
        check(
            trace().length <= 256 && branches().length <= 16,
            "bounded256-call-metadata16-catalog-reads",
        );
        check(
            trace().every(
                (item, index) =>
                    item.sequence === index + 1 &&
                    item.settled &&
                    (item.error === null || item.error === "InspectVersion") &&
                    (item.replySha256 === null || HEX.test(item.replySha256)),
            ),
            "native-call-records-ordered-settled-finite-errors-digests",
        );
        check(
            trace().every((item) =>
                item.channel === "host"
                    ? !!item.command && allowed.has(item.command.op)
                    : [
                          "model_status",
                          "inspection_storage",
                          ...(afterDispose ? ["capture_revoke"] : []),
                      ].includes(item.nativeAction ?? ""),
            ),
            "normal-read-close-roster-no-gameplay-author-fork-model-load-or-provider-dispatch",
        );
        check(
            c.get().playMode === "fixture" &&
                !c.get().freeTextProvider &&
                gateway.submissions.length === 0,
            "synthetic-existing-fixture-no-generation-submissions",
        );
    };
    let baselineTargets: { element: HTMLElement; px: number; text: string }[] =
        [];
    const fontTargets = () => {
        const region = panel();
        check(region, "actual-browser-required-for-target-fonts");
        const targets = [
            region!,
            region!.querySelector<HTMLElement>("h2"),
            region!.querySelector<HTMLElement>("h3"),
            region!.querySelector<HTMLElement>(
                '[aria-label="Saved timeline metadata"]',
            ),
            ...region!.querySelectorAll<HTMLButtonElement>("button"),
        ];
        check(
            targets.every((node) => node?.isConnected),
            "all-fixed-browser-font-targets-connected-no-omissions",
        );
        return targets as HTMLElement[];
    };
    const measureFonts = async (
        label: string,
        ratio: 1 | 1.5,
        establish = false,
    ) => {
        await frames();
        const targets = fontTargets();
        if (establish) {
            check(
                c.get().textScale === 100 &&
                    !!document.querySelector(".app.text-100"),
                "actual100-browser-font-baseline",
            );
            baselineTargets = targets.map((element) => ({
                element,
                px: Number.parseFloat(getComputedStyle(element).fontSize),
                text: element.textContent ?? "",
            }));
        }
        check(
            targets.length === baselineTargets.length,
            `${label}-same-browser-font-target-count`,
        );
        const measured: Record<string, unknown>[] = [];
        fonts.push({
            label,
            expectedRatio: ratio,
            pixelTolerance: 0.05,
            width: innerWidth,
            height: innerHeight,
            targets: measured,
        });
        targets.forEach((element, index) => {
            const base = baselineTargets[index],
                px = Number.parseFloat(getComputedStyle(element).fontSize);
            measured.push({
                tag: element.tagName,
                text: element.textContent?.slice(0, 120),
                baselinePx: base.px,
                actualPx: px,
                ratio: px / base.px,
            });
            check(
                element === base.element &&
                    element.textContent === base.text &&
                    Number.isFinite(base.px) &&
                    base.px > 0 &&
                    Number.isFinite(px) &&
                    px > 0 &&
                    Math.abs(px - base.px * ratio) <= 0.05,
                `${label}-same-actual-browser-target-font-ratio`,
            );
        });
    };

    try {
        check(
            typeof gateway.startInspectorPagingTrace === "function",
            "SETUP-existing-fixed-call-trace-interface",
        );
        gateway.startInspectorPagingTrace();
        await until(
            () => !!c.get().workspace && !!c.selected(),
            "actual-Main-existing-workspace-ready",
        );
        baseline = await oracle("before-browser-navigation");
        await c.resume(CHILD);
        await idle();
        assertOwner(CHILD, 44, 2);
        click(
            button(
                "Play",
                document.querySelector('[aria-label="Workspace mode"]')!,
            ),
            "actual-Play-mode",
        );
        await idle();
        await show();
        await capture("d08-browser-catalog");
        const fault = armDelivery("error"),
            beforeFault = branches().length;
        click(
            button("Refresh timeline catalog", panel()!),
            "real-catalog-read-before-local-delivery-error",
        );
        await until(
            () => fault.entered,
            "actual-native-catalog-reply-held-before-error-delivery",
        );
        check(
            timeline.get().busy &&
                timeline.get().status === "loading" &&
                timeline.get().catalog === null &&
                !panel()?.querySelector(
                    '[aria-label="Saved timeline metadata"]',
                ),
            "pending-real-catalog-has-no-old-visible-metadata",
        );
        check(
            fault.command?.op === "branches" &&
                HEX.test(fault.replySha256 ?? "") &&
                branches().length === beforeFault + 1,
            "held-local-error-has-one-settled-real-native-read-digest",
        );
        check(
            branches().at(-1)?.settled &&
                branches().at(-1)?.error === null &&
                branches().at(-1)?.replySha256 === fault.replySha256 &&
                structural(branches().at(-1)?.command) ===
                    structural(fault.command),
            "held-delivery-exact-command-and-digest-match-actual-native-trace",
        );
        observe("pending-real-catalog-before-delivery-error");
        const pendingRefresh = button("Refresh timeline catalog", panel()!);
        check(pendingRefresh.disabled, "pending-refresh-disabled");
        pendingRefresh.click();
        check(
            branches().length === beforeFault + 1,
            "pending-disabled-refresh-does-not-duplicate-native-read",
        );
        fault.release();
        await until(
            () => !timeline.get().busy && timeline.get().error === "Transport",
            "local-post-native-delivery-error-visible",
        );
        delivery = null;
        await frames();
        check(
            panel()
                ?.querySelector('[role="alert"]')
                ?.textContent?.includes("Transport"),
            "actual-browser-visible-local-delivery-error",
        );
        observe("local-error-native-success-distinguished");
        const retryBefore = branches().length;
        click(
            button("Refresh timeline catalog", panel()!),
            "explicit-retry-real-catalog",
        );
        await show();
        check(
            branches().length === retryBefore + 1,
            "explicit-retry-exactly-one-real-native-read",
        );
        await resumeButton("main", PARENT, 0, 1);
        await capture("d08-browser-root");
        await resumeButton("paging", CHILD, 44, 2);
        await capture("d08-browser-child");
        const stale = armDelivery("hold");
        click(
            button("Refresh timeline catalog", panel()!),
            "real-catalog-read-before-lens-retirement",
        );
        await until(
            () => stale.entered,
            "actual-native-catalog-reply-held-for-stale-context",
        );
        check(
            branches().at(-1)?.settled &&
                branches().at(-1)?.error === null &&
                branches().at(-1)?.replySha256 === stale.replySha256 &&
                structural(branches().at(-1)?.command) ===
                    structural(stale.command),
            "stale-delivery-exact-command-and-digest-match-actual-native-trace",
        );
        observe("pending-real-catalog-before-context-retirement");
        click(
            button(
                "Story Lab · spoilers",
                document.querySelector('[aria-label="Workspace mode"]')!,
            ),
            "actual-Story-Lab-request",
        );
        await until(
            () =>
                c.get().labPending &&
                !!document.querySelector("dialog.spoiler-dialog"),
            "actual-spoiler-acknowledgement-dialog",
        );
        click(
            button(
                "I understand; reveal spoilers",
                document.querySelector("dialog.spoiler-dialog")!,
            ),
            "explicit-real-spoiler-acknowledgement",
        );
        await until(
            () => c.get().view === "lab" && !c.get().labPending,
            "actual-acknowledged-Lab-mode",
        );
        const lens = [
            ...document.querySelectorAll<HTMLSelectElement>("label select"),
        ].filter((node) =>
            node.parentElement?.textContent?.includes("Inspection lens"),
        );
        check(lens.length === 1, "actual-unique-Domain2-inspection-lens");
        Object.getOwnPropertyDescriptor(
            HTMLSelectElement.prototype,
            "value",
        )!.set!.call(lens[0], "mira");
        lens[0].dispatchEvent(new Event("input", { bubbles: true }));
        lens[0].dispatchEvent(new Event("change", { bubbles: true }));
        await until(
            () =>
                c.get().observer === "mira" &&
                v2.get().context?.observer.kind === "character" &&
                !timeline.get().shown &&
                timeline.get().catalog === null,
            "actual-Main-Mira-context-retires-pending-old-catalog",
        );
        stale.release();
        await until(
            () => stale.delivered,
            "old-real-catalog-delivery-released",
        );
        delivery = null;
        await idle();
        check(
            !timeline.get().shown &&
                timeline.get().catalog === null &&
                !panel(),
            "old-catalog-promise-cannot-republish-after-actual-context-switch",
        );
        observe("stale-catalog-after-actual-context-switch");
        await show();
        assertOwner(CHILD, 44, 2);
        check(
            c.get().observer === "mira" &&
                v2.get().context?.observer.kind === "character",
            "actual-Mira-lens-preserved-by-catalog-browsing",
        );
        await oracle("after-actual-observer-and-resume-journeys");
        await capture("d08-browser-observer");
        c.layout(c.get().sidebarSize, c.get().inspectorSize, 100);
        await invoke("harness_viewport", { preset: "wide" });
        await idle();
        await measureFonts("100-baseline", 1, true);
        c.layout(c.get().sidebarSize, c.get().inspectorSize, 150);
        for (const [preset, label] of [
            ["wide", "d08-browser-enlarged-wide"],
            ["capture-narrow", "d08-browser-enlarged-narrow"],
        ] as const) {
            await invoke("harness_viewport", { preset });
            await until(
                () =>
                    c.get().textScale === 150 &&
                    !!document.querySelector(".app.text-150"),
                `${label}-actual150-state-and-class`,
            );
            await idle();
            const app = document.querySelector<HTMLElement>(".app.text-150")!;
            check(
                Math.abs(
                    Number.parseFloat(getComputedStyle(app).fontSize) /
                        Number.parseFloat(
                            getComputedStyle(document.documentElement).fontSize,
                        ) -
                        1.5,
                ) < 1e-6,
                `${label}-actual-app-root-font-ratio150`,
            );
            await measureFonts(label, 1.5);
            await capture(label);
        }
        c.layout(c.get().sidebarSize, c.get().inspectorSize, 100);
        await invoke("harness_viewport", { preset: "wide" });
        await idle();
        await measureFonts("100-restored", 1);
        assertOwner(CHILD, 44, 2);
        check(
            structural(captures) === structural(LABELS),
            "exact-six-new-native-browser-captures-no-old-paging-roster",
        );
        assertCalls(false);
        finalOracle = await oracle("after-all-browser-captures-before-dispose");
        const errorBeforeDispose = errors.snapshot();
        check(
            errorBeforeDispose.length <= 1 &&
                errorBeforeDispose.every(
                    (item) => item.category === "Transport",
                ),
            "bounded-errors-only-disclosed-local-delivery-Transport-if-buffered",
        );
        const closeStart = trace().length;
        disposing = true;
        await dispose();
        check(
            trace()
                .slice(closeStart)
                .every(
                    (item) =>
                        item.settled &&
                        (item.channel === "host"
                            ? !!item.command &&
                              ["close", "trace_capture_revoke"].includes(
                                  item.command.op,
                              )
                            : item.nativeAction === "capture_revoke"),
                ),
            "dispose-only-established-settled-close-revoke-roster",
        );
        finalOracle = await oracle("after-dispose-before-window-exit");
        check(
            structural(errors.snapshot()) === structural(errorBeforeDispose),
            "dispose-adds-no-buffered-errors",
        );
        // Controller disposal retires snapshots; validate the final dispatch roster
        // directly rather than pretending a live gameplay state still exists.
        check(
            trace().length <= 256 && trace().every((item) => item.settled),
            "final-bounded-known-settled-native-dispatches",
        );
        await finish({ passed: true });
    } catch (error) {
        const failedCheck = current,
            failureCategory =
                error instanceof Error
                    ? error.message.slice(0, 256)
                    : category(error);
        releaseDelivery();
        if (!disposing) {
            try {
                await capture("d08-browser-failure", true);
            } catch {
                /* Original failure is authoritative. */
            }
            try {
                disposing = true;
                await dispose();
            } catch {
                /* Root supervises unresolved native lifetime. */
            }
        }
        await finish({ passed: false, failedCheck, failureCategory });
    } finally {
        releaseDelivery();
        gateway.call = originalCall;
    }
}
