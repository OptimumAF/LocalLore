// Fixed development-only journey. SOURCE AUTHOR UNCOMPILED / UNRUN.
// Actual mounted panel/controllers/Host IPC. No OS input or desktop capture.
import type { Controller } from "./controller";
import type { FaultGateway } from "./journeys";
import {
    category,
    structural,
    type Command,
    type ErrorBuffer,
    type Scope,
} from "./model";
import type { V2BoundPage, V2PlayController } from "./v2-play-controller";
import {
    checkedPageV2,
    type InspectionQueryV2,
    type RowV2,
    type ViewV2,
} from "./v2-view-model";
import { decodeBranchCatalog } from "./timeline-model";

type Trace = {
    sequence: number;
    channel: "host" | "native";
    command: Command | null;
    nativeAction: string | null;
    settled: boolean;
    replySha256: string | null;
    error: string | null;
    deliveryDropped: boolean;
};
type TracedGateway = FaultGateway & {
    startInspectorPagingTrace(): void;
    readonly inspectorPagingCalls: readonly Trace[];
    dropNextInspectorPagingReply: boolean;
};
type ScopeOracle = {
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
};
type Oracle = {
    version: number;
    kind: string;
    fixture_version: number;
    scopes: ScopeOracle[];
};
type Invoke = (
    name: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
const CHILD: Scope = { story: "d05-inspector-native", branch: "paging" };
const PARENT: Scope = { story: "d05-inspector-native", branch: "main" };
const OTHER: Scope = { story: "d05-inspector-other", branch: "main" };
const LABELS = [
    "first",
    "second",
    "third",
    "back-second",
    "back-first",
    "forward-refetched",
    "pending-next",
    "error",
    "retry-second",
    "search-reset",
    "historical",
    "mira",
    "sable",
    "other-story",
    "same-head-refresh",
    "stale-delivery",
    "unsupported",
    "enlarged-wide",
    "enlarged-narrow",
    "final",
].map((name) => `d05-page-${name}`);
const HEX = /^[a-f0-9]{64}$/;
const forbidden = [
    "D05_UNOBSERVED_AUTHOR_TRUTH_913",
    "D05_AUTHOR_REASON_PRIVATE_914",
    "D05_OTHER_STORY_SEED_515",
    "D05_OTHER_STORY_MESSAGE_516",
];
function gate() {
    let ready!: () => void, release!: () => void;
    const entered = new Promise<void>((resolve) => {
            ready = resolve;
        }),
        waiting = new Promise<void>((resolve) => {
            release = resolve;
        });
    return { ready, release, entered, waiting };
}
async function digest(value: unknown) {
    const bytes = new TextEncoder().encode(JSON.stringify(value));
    return [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))]
        .map((v) => v.toString(16).padStart(2, "0"))
        .join("");
}
function rowIdentity(row: RowV2) {
    return row.kind === "author_correction"
        ? `author_correction:${row.revision}`
        : row.key;
}

export async function v2InspectorPagingNativeJourneys({
    controller: c,
    v2,
    gateway,
    errors,
    invoke,
    dispose,
}: {
    controller: Controller;
    v2: V2PlayController;
    gateway: FaultGateway;
    errors: ErrorBuffer;
    invoke: Invoke;
    dispose: () => Promise<void>;
}): Promise<void> {
    const g = gateway as TracedGateway,
        checks: string[] = [],
        captures: string[] = [],
        proofs: { label: string; oracle: Oracle }[] = [];
    const releases = new Set<() => void>(),
        pageProofs: {
            label: string;
            sequence: number;
            sha256: string;
            first: string | null;
            last: string | null;
            count: number;
        }[] = [];
    const focusObservations: {
        label: string;
        expected: string;
        actual: string;
        disabledBoundary: boolean;
    }[] = [];
    const negativeProbes: { expected: string; actual: string }[] = [];
    const checkNames = new Set<string>();
    let current = "d05-paging-setup",
        baseline: Oracle | null = null,
        finalOracle: Oracle | null = null,
        disposing = false,
        assertions = 0;
    const deadline = performance.now() + 150000;
    const check = (ok: unknown, name: string) => {
        current = name;
        gateway.diagnosticPhase = name;
        if (!ok) throw Error(name);
        assertions++;
        if (!checkNames.has(name)) {
            checkNames.add(name);
            checks.push(name);
        }
    };
    const until = async (test: () => boolean, name: string) => {
        current = name;
        for (let n = 0; n < 1500 && performance.now() < deadline; n++) {
            if (test()) return;
            await new Promise((r) => setTimeout(r, 10));
        }
        throw Error(`D05PagingDeadline:${name}`);
    };
    const frames = () =>
        new Promise<void>((resolve, reject) => {
            const timer = setTimeout(
                () => reject(Error("D05PagingRenderFramesTimeout")),
                5000,
            );
            requestAnimationFrame(() =>
                requestAnimationFrame(() => {
                    clearTimeout(timer);
                    resolve();
                }),
            );
        });
    const trace = () => g.inspectorPagingCalls;
    const queryCalls = () =>
        trace().filter(
            (item) =>
                item.channel === "host" &&
                item.command?.op === "inspection_query",
        );
    const traceBound = () => {
        const calls = trace();
        check(
            calls.length <= 256 && queryCalls().length <= 192,
            "bounded256-metadata192-query-attempts",
        );
        for (let i = 0; i < calls.length; i++) {
            const item = calls[i];
            check(
                item.sequence === i + 1 &&
                    Object.keys(item).sort().join(",") ===
                        "channel,command,deliveryDropped,error,nativeAction,replySha256,sequence,settled",
                "closed-ordered-real-call-trace",
            );
            check(
                item.channel === "host"
                    ? item.command !== null && item.nativeAction === null
                    : item.command === null &&
                          typeof item.nativeAction === "string",
                "separate-host-native-trace-channels",
            );
            if (item.replySha256 !== null)
                check(HEX.test(item.replySha256), "actual-reply-digest-format");
        }
    };
    const idle = async () => {
        await until(
            () =>
                !v2.get().readBusy &&
                !v2.get().queryBusy &&
                trace().every((item) => item.settled),
            "native-reads-and-delivery-idle",
        );
        await frames();
    };
    const panel = () =>
        document.querySelector<HTMLElement>(
            '[aria-label="Read-only V2 inspector"]',
        );
    const button = (name: "previous" | "next" | "read") => {
        const label =
            name === "previous"
                ? "Previous inspection page"
                : name === "next"
                  ? "Next inspection page"
                  : "Read permitted view";
        const found = [
            ...(panel()?.querySelectorAll<HTMLButtonElement>("button") ?? []),
        ].filter((item) => item.textContent?.trim() === label);
        check(found.length === 1, `actual-mounted-unique-${name}-button`);
        return found[0];
    };
    const active = () => {
        const element = document.activeElement;
        return element instanceof HTMLElement
            ? `${element.tagName}:${element.getAttribute("aria-label") ?? element.textContent?.trim().slice(0, 120) ?? ""}`
            : "Unavailable";
    };
    const oracle = async (label: string) => {
        const value = (await invoke("harness_v2_inspection_paging")) as Oracle;
        check(
            value &&
                Object.keys(value).sort().join(",") ===
                    "fixture_version,kind,scopes,version" &&
                value.version === 1 &&
                value.kind === "v2_inspection_paging_oracle_v1" &&
                value.fixture_version === 1 &&
                value.scopes.length === 3,
            `${label}-actual-closed-oracle`,
        );
        const expected = [
            [PARENT, 1, 0],
            [CHILD, 2, 44],
            [OTHER, 1, 1],
        ] as const;
        value.scopes.forEach((item, index) => {
            check(
                structural(item.scope) === structural(expected[index][0]) &&
                    item.domain_version === expected[index][1] &&
                    item.head === expected[index][2] &&
                    item.story_time === 100,
                `${label}-scope${index}-actual-head-domain-clock`,
            );
            for (const field of [
                "seed_sha256",
                "projection_sha256",
                "records_sha256",
                "receipts_sha256",
                "turns_sha256",
                "actors_sha256",
            ] as const)
                check(HEX.test(item[field]), `${label}-${index}-${field}`);
        });
        if (baseline)
            check(
                structural(value) === structural(baseline),
                `${label}-all-canonical-fixed-turn-and-actor-fingerprints-unchanged`,
            );
        proofs.push({ label, oracle: value });
        return value;
    };
    const proof = async (
        label: string,
        bound: V2BoundPage,
        afterSequence = 0,
    ) => {
        check(
            v2.get().inspection === bound,
            `${label}-actual-current-page-reference`,
        );
        const context = v2.get().context;
        check(
            context &&
                bound.page.head === context.revision &&
                structural(bound.page.scope) === structural(context.scope),
            `${label}-actual-current-context`,
        );
        const calls = queryCalls().filter(
            (item) =>
                item.sequence > afterSequence &&
                item.command?.op === "inspection_query" &&
                structural(item.command.query) === structural(bound.query) &&
                item.command.session === context!.session &&
                item.settled &&
                item.error === null &&
                !item.deliveryDropped,
        );
        check(calls.length > 0, `${label}-matching-completed-real-host-call`);
        const call = calls.at(-1)!;
        const sha256 = await digest(bound.page);
        check(
            call.replySha256 === sha256,
            `${label}-displayed-page-equals-actual-native-reply-digest`,
        );
        const ids = bound.page.rows.map(rowIdentity);
        check(
            new Set(ids).size === ids.length,
            `${label}-unique-real-wire-identities`,
        );
        for (const row of bound.page.rows)
            if (row.kind === "author_correction")
                check(
                    !Object.hasOwn(row, "key") && row.revision === 1,
                    `${label}-marker-kind-revision-without-invented-key`,
                );
        pageProofs.push({
            label,
            sequence: call.sequence,
            sha256,
            first: ids[0] ?? null,
            last: ids.at(-1) ?? null,
            count: ids.length,
        });
        return sha256;
    };
    const mountedPage = async (bound: V2BoundPage) => {
        await until(() => {
            const section = panel(),
                rows = section?.querySelectorAll<HTMLElement>("ol > li");
            return (
                !!section &&
                !!rows &&
                rows.length === bound.page.rows.length &&
                section.textContent?.includes(
                    `${bound.page.total} permitted rows`,
                ) === true
            );
        }, "actual-native-page-mounted-count-and-total");
        const rows = [...panel()!.querySelectorAll<HTMLElement>("ol > li")];
        bound.page.rows.forEach((row, index) => {
            const node = rows[index];
            check(
                row.kind === "author_correction"
                    ? node.getAttribute("aria-label") ===
                          "Timeline correction" &&
                          node.textContent?.includes(`r${row.revision}`)
                    : node.dataset.nativeKind === row.kind,
                `mounted-row${index}-actual-kind`,
            );
            if (row.kind === "scoped_message")
                check(
                    node.textContent?.includes(row.turn) &&
                        node.querySelector(".record-value")?.textContent ===
                            row.text,
                    `mounted-row${index}-actual-turn-text`,
                );
            if (row.kind === "event")
                check(
                    node.textContent?.includes(`Event ${row.event.sequence}`),
                    `mounted-row${index}-actual-event-identity`,
                );
        });
    };
    const expectedPage = async (
        label: string,
        count: number,
        total: number,
        revision = 44,
    ) => {
        const bound = v2.get().inspection;
        check(
            bound &&
                bound.page.rows.length === count &&
                bound.page.total === total &&
                bound.page.head === 44 &&
                bound.page.revision === revision &&
                bound.page.story_time === 100,
            `${label}-actual-expected-page-counts`,
        );
        await mountedPage(bound!);
        await proof(label, bound!);
        return bound!;
    };
    const setForm = async (
        view: ViewV2,
        search = "",
        at: number | null = null,
    ) => {
        const section = panel();
        check(section, "actual-V2-form-present");
        const controls = [
            [section!.querySelector<HTMLSelectElement>("form select"), view],
            [
                section!.querySelector<HTMLInputElement>(
                    'form input[type="number"]',
                ),
                at === null ? "" : String(at),
            ],
            [
                section!.querySelector<HTMLInputElement>(
                    'form input:not([type="number"])',
                ),
                search,
            ],
        ] as const;
        for (const [element, value] of controls) {
            check(element, "fixed-native-form-control-present");
            if (element!.value === value) continue;
            const prototype =
                element instanceof HTMLSelectElement
                    ? HTMLSelectElement.prototype
                    : HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(
                prototype,
                "value",
            )?.set;
            check(setter, "native-DOM-value-setter-present");
            setter!.call(element, value);
            element!.dispatchEvent(new Event("input", { bubbles: true }));
            element!.dispatchEvent(new Event("change", { bubbles: true }));
            await frames();
            check(
                element!.value === value,
                "actual-React-form-draft-matches-fixed-edit",
            );
            check(
                !v2.get().inspectionPaging.bound,
                "form-edit-retires-old-paging",
            );
        }
    };
    const read = async (
        view: ViewV2 = "history",
        search = "",
        at: number | null = null,
    ) => {
        await idle();
        await setForm(view, search, at);
        const before = queryCalls().length,
            sequence = trace().length;
        const submit = button("read");
        check(!submit.disabled, "actual-read-form-enabled");
        submit.form!.requestSubmit(submit);
        await until(
            () => queryCalls().length > before && !v2.get().queryBusy,
            "mounted-form-read-completed",
        );
        await idle();
        const bound = v2.get().inspection;
        check(
            bound &&
                bound.query.view === view &&
                bound.query.search === search &&
                bound.query.at_revision === at &&
                bound.query.cursor === null,
            "actual-form-values-own-fresh-first-page",
        );
        check(
            queryCalls().length === before + 1,
            "fresh-form-read-exactly-one-query",
        );
        await proof("fresh-read", bound!, sequence);
        await mountedPage(bound!);
        return bound!;
    };
    const navigate = async (direction: "previous" | "next", label: string) => {
        await idle();
        const control = button(direction),
            before = queryCalls().length,
            sequence = trace().length;
        check(!control.disabled, `${label}-actual-pager-enabled`);
        control.focus();
        check(
            document.activeElement === control,
            `${label}-actual-DOM-focus-before`,
        );
        control.click();
        await until(
            () => queryCalls().length > before && !v2.get().queryBusy,
            `${label}-native-navigation-completed`,
        );
        await idle();
        check(
            queryCalls().length === before + 1,
            `${label}-exactly-one-native-query`,
        );
        const bound = v2.get().inspection;
        check(bound, `${label}-page-returned`);
        await proof(label, bound!, sequence);
        await mountedPage(bound!);
        const still = button(direction),
            peer = button(direction === "previous" ? "next" : "previous");
        focusObservations.push({
            label,
            expected: control.textContent!.trim(),
            actual: active(),
            disabledBoundary: still.disabled,
        });
        check(still === control, `${label}-same-control-remains-mounted`);
        check(
            document.activeElement === still ||
                document.activeElement === peer ||
                (still.disabled && document.activeElement === document.body),
            `${label}-no-row-or-unrelated-panel-focus-steal`,
        );
        return bound!;
    };
    const lens = async (value: "player" | "omniscient" | "mira" | "sable") => {
        if (c.get().view !== "lab") {
            c.requestLab();
            c.acknowledgeLab(true);
        }
        c.setObserver(value);
        await until(
            () =>
                v2.get().context?.view === "lab" &&
                (v2.get().context?.observer.kind === "character"
                    ? (v2.get().context?.observer as { id: string }).id ===
                      value
                    : v2.get().context?.observer.kind === value),
            "actual-Main-lens-routed-to-V2",
        );
        await idle();
        check(
            v2.get().inspection === null &&
                !v2.get().inspectionPaging.bound &&
                v2.get().source === null,
            "lens-clears-private-page-chain-and-source",
        );
    };
    const noPrivate = (value: string, actor: "player" | "mira" | "sable") => {
        check(
            !forbidden.some((text) => value.includes(text)),
            `${actor}-no-other-story-or-unobserved-author-payload`,
        );
        if (actor !== "player")
            check(
                !value.includes("D05_PLAYER_SEED_SECRET_731") &&
                    !value.includes("_PLAYER_ONLY"),
                `${actor}-no-Player-only-observations`,
            );
        if (actor !== "mira")
            check(
                !value.includes("D05_MIRA_PRIVATE_BELIEF_812"),
                `${actor}-no-Mira-private-belief`,
            );
        if (actor === "sable")
            check(
                !value.includes("D05_PAGING_ROW_"),
                "Sable-no-unwitnessed-dialogue",
            );
    };
    const holdNext = async () => {
        await idle();
        const held = gate();
        releases.add(held.release);
        g.heldQuery = held;
        const old = v2.get().inspection;
        check(old?.page.next_cursor, "pending-next-has-real-cursor");
        const sequence = trace().length,
            session = v2.get().context!.session;
        const expectedQuery = { ...old!.query, cursor: old!.page.next_cursor };
        const control = button("next");
        check(!control.disabled, "pending-actual-next-enabled");
        control.focus();
        control.click();
        let entered = false;
        void held.entered.then(() => {
            entered = true;
        });
        await until(() => entered, "post-real-native-read-delivery-held");
        const call = queryCalls().find(
            (item) =>
                item.sequence > sequence &&
                item.command?.op === "inspection_query" &&
                item.command.session === session &&
                structural(item.command.query) === structural(expectedQuery),
        );
        check(
            call?.settled &&
                call.error === null &&
                call.replySha256 !== null &&
                HEX.test(call.replySha256) &&
                v2.get().queryBusy &&
                v2.get().inspection === old &&
                v2.get().inspectionPaging.navigating === "next",
            "actual-held-read-bound-cursor-settlement-digest-and-old-page",
        );
        const count = queryCalls().length;
        button("next").click();
        button("previous").click();
        await frames();
        check(
            queryCalls().length === count,
            "pending-disabled-duplicate-actions-do-not-dispatch",
        );
        return { held, old: old!, call: call! };
    };
    const release = (held: ReturnType<typeof gate>) => {
        held.release();
        releases.delete(held.release);
        if (g.heldQuery === held) g.heldQuery = null;
    };
    const capture = async (label: string, failure = false) => {
        if (!failure)
            check(
                LABELS.includes(label) && !captures.includes(label),
                `${label}-fixed-unique-capture-label`,
            );
        await frames();
        const state = v2.get(),
            section = panel(),
            root = document.querySelector<HTMLElement>(".v2-play"),
            legacy = !root;
        const header =
            root?.querySelector<HTMLElement>("header.scope") ??
            document.querySelector<HTMLElement>(".scene-head");
        const nav = section?.querySelector<HTMLElement>(
                '[aria-label="Inspection page navigation"]',
            ),
            status = nav?.querySelector<HTMLElement>('[role="status"]');
        const selected = c.selected();
        check(selected, `${label}-actual-selected-session`);
        if (!failure) {
            if (label === "d05-page-other-story")
                check(
                    legacy &&
                        !section &&
                        structural(selected!.scope) === structural(OTHER) &&
                        header?.textContent?.includes(
                            `${OTHER.story} / ${OTHER.branch}`,
                        ) &&
                        header.textContent.includes("Revision 1"),
                    "actual-Domain1-header-boundary-has-no-V2-pager",
                );
            else
                check(
                    root &&
                        section &&
                        nav &&
                        status &&
                        structural(selected!.scope) === structural(CHILD),
                    `${label}-actual-V2-pager-region`,
                );
        }
        if (nav) nav.scrollIntoView({ block: "center" });
        else header?.scrollIntoView({ block: "start" });
        await frames();
        const nodes = legacy
            ? [header]
            : [header, nav, status, button("previous"), button("next")];
        const geometry = nodes
            .filter((node): node is HTMLElement => !!node)
            .map((node) => {
                const bounds = node.getBoundingClientRect(),
                    visible =
                        bounds.width > 0 &&
                        bounds.height > 0 &&
                        [
                            bounds.top,
                            bounds.left,
                            bounds.right,
                            bounds.bottom,
                        ].every(Number.isFinite) &&
                        bounds.top >= -2 &&
                        bounds.left >= -2 &&
                        bounds.right <= innerWidth + 2 &&
                        bounds.bottom <= innerHeight + 2;
                const hits = [0.05, 0.5, 0.95].map((point) => {
                    if (!visible) return false;
                    const hit = document.elementFromPoint(
                        bounds.left + bounds.width / 2,
                        bounds.top +
                            Math.max(
                                1,
                                Math.min(
                                    bounds.height - 1,
                                    bounds.height * point,
                                ),
                            ),
                    );
                    return !!hit && (hit === node || node.contains(hit));
                });
                if (!failure)
                    check(
                        visible && hits.every(Boolean),
                        `${label}-actual-positive-fit-unoccluded-top-middle-bottom`,
                    );
                return {
                    text: node.innerText.slice(0, 1024),
                    rect: {
                        x: bounds.x,
                        y: bounds.y,
                        width: bounds.width,
                        height: bounds.height,
                        bottom: bounds.bottom,
                        right: bounds.right,
                    },
                    visible,
                    hits,
                };
            });
        const text =
            root?.textContent ??
            document.getElementById("root")?.textContent ??
            "";
        if (!failure) {
            check(
                document.documentElement.scrollWidth <= innerWidth + 2 &&
                    (!root || root.scrollWidth <= root.clientWidth + 2),
                `${label}-no-page-panel-horizontal-overflow`,
            );
            if (!legacy) {
                const context = state.context!;
                check(
                    header?.textContent?.includes(context.scope.story) &&
                        header.textContent.includes(context.scope.branch) &&
                        header.textContent.includes(context.session),
                    `${label}-actual-story-branch-session-header`,
                );
                const actor =
                    context.observer.kind === "character"
                        ? context.observer.id
                        : context.observer.kind;
                check(
                    header?.textContent?.includes(actor),
                    `${label}-actual-current-observer-header`,
                );
                if (state.error)
                    check(
                        root
                            ?.querySelector('[role="alert"]')
                            ?.textContent?.includes(state.error),
                        `${label}-visible-finite-error`,
                    );
                if (actor === "player" || actor === "mira" || actor === "sable")
                    noPrivate(text, actor);
            }
        }
        const bound = state.inspection,
            app = document.querySelector<HTMLElement>(".app");
        const snapshot = {
            synthetic: true,
            semanticVersion: 1,
            mode: "v2_inspector_paging_v1",
            uiRevision: selected!.revision,
            selectedStory: selected!.scope,
            session: selected!.id,
            observer: state.context?.observer ?? { kind: "player" },
            player: state.context?.player ?? "player",
            revision: bound?.page.revision ?? selected!.revision,
            head: state.context?.revision ?? selected!.revision,
            inspectedRevision: bound?.page.revision ?? null,
            pendingOperation: state.queryBusy
                ? {
                      phase: state.inspectionPaging.navigating ?? "query",
                      session: state.context?.session ?? null,
                  }
                : null,
            displayedReceipt:
                state.context?.view === "play" ? state.receipt : null,
            visibleError: state.error ?? c.get().visibleError,
            query: bound?.query ?? null,
            page: bound
                ? {
                      total: bound.page.total,
                      rows: bound.page.rows.map(rowIdentity),
                      first: bound.page.rows[0]
                          ? rowIdentity(bound.page.rows[0])
                          : null,
                      last: bound.page.rows.at(-1)
                          ? rowIdentity(bound.page.rows.at(-1)!)
                          : null,
                  }
                : null,
            paging: state.inspectionPaging,
            source: state.source,
            sourceMatched: state.sourceMatched,
            queryBusy: state.queryBusy,
            readBusy: state.readBusy,
            dom: {
                text: text.slice(0, 16000),
                active: active(),
                width: innerWidth,
                height: innerHeight,
                textScale: c.get().textScale,
                appFont: app ? getComputedStyle(app).fontSize : null,
                rootFont: getComputedStyle(document.documentElement).fontSize,
                geometry,
                userAgent: navigator.userAgent,
                legacy,
            },
            traceCount: trace().length,
            queryAttempts: queryCalls().length,
            errors: errors.snapshot(),
            pageProofs: pageProofs.slice(-4),
            checks: checks.slice(-160),
        };
        check(
            new TextEncoder().encode(JSON.stringify(snapshot)).length <=
                256 * 1024,
            `${label}-bounded-semantic-snapshot`,
        );
        const result = (await invoke("harness_checkpoint", {
            label,
            snapshot,
        })) as { rendering?: string };
        if (!failure) {
            check(
                result?.rendering === "native-webview2",
                `${label}-actual-app-owned-WebView2-CapturePreview`,
            );
            captures.push(label);
        }
    };
    const finish = async (value: { report: Record<string, unknown> }) => {
        value.report.assertions = assertions;
        value.report.distinctChecks = checks.length;
        if (
            new TextEncoder().encode(JSON.stringify(value.report)).length >
            256 * 1024
        )
            throw Error("D05PagingFinalReportBudget");
        await invoke("harness_finish", value);
    };

    try {
        check(
            typeof g.startInspectorPagingTrace === "function" &&
                typeof g.dropNextInspectorPagingReply === "boolean",
            "SETUP-fixed-dev-trace-interface-required",
        );
        g.startInspectorPagingTrace();
        check(
            Array.isArray(g.inspectorPagingCalls),
            "SETUP-bounded-real-call-trace-required",
        );
        baseline = await oracle("baseline-before-navigation");
        const workspace = await c.library();
        check(
            workspace?.stories.length === 2 &&
                workspace.stories.some(
                    (item) => structural(item.scope) === structural(PARENT),
                ) &&
                workspace.stories.some(
                    (item) => structural(item.scope) === structural(OTHER),
                ),
            "actual-library-two-root-stories-no-guessed-child",
        );
        const catalog = decodeBranchCatalog(
            await g.call({ op: "branches", story: PARENT.story }),
            PARENT.story,
        );
        check(
            catalog.version === 2 &&
                catalog.branches.length === 2 &&
                catalog.branches.some(
                    (item) =>
                        structural(item.scope) === structural(CHILD) &&
                        item.revision === 44 &&
                        item.fork_revision === 0 &&
                        !item.retired,
                ),
            "actual-primary-branch-catalog-exact-child-fork-zero",
        );
        await c.resume(CHILD);
        await idle();
        check(
            v2.get().context?.revision === 44 &&
                v2.get().snapshot?.domain_version === 2 &&
                !c.get().freeTextProvider,
            "actual-Domain2-main-route-no-scene-provider",
        );
        c.setView("play");
        await idle();
        await read();
        const first = await expectedPage("first", 64, 130),
            firstHash = await digest(first.page);
        check(
            !v2.get().inspectionPaging.canPrevious,
            "first-page-no-predecessor",
        );
        const noneBefore = queryCalls().length;
        button("previous").click();
        await frames();
        check(
            queryCalls().length === noneBefore,
            "disabled-first-Previous-does-not-probe-native",
        );
        await capture("d05-page-first");
        const sourceButton = [
            ...panel()!.querySelectorAll<HTMLButtonElement>(
                ".source-links button",
            ),
        ].find(
            (item) =>
                item.textContent?.trim() ===
                `${CHILD.story} / ${CHILD.branch} · event 2`,
        );
        check(
            sourceButton && !sourceButton.disabled,
            "actual-mounted-original-event-source-link",
        );
        const sourceCalls = queryCalls().length;
        sourceButton!.click();
        await until(
            () =>
                queryCalls().length === sourceCalls + 1 &&
                !v2.get().queryBusy &&
                v2.get().sourceMatched === true,
            "actual-source-link-read-and-permitted-match",
        );
        await idle();
        const linked = v2.get().source;
        check(
            linked?.kind === "scoped_event" &&
                linked.value.sequence === 2 &&
                structural(linked.value.original_scope) === structural(CHILD),
            "actual-source-identity-not-inferred-from-prose",
        );
        await proof("actual-source-filter", v2.get().inspection!);
        await read();
        check(
            v2.get().source === null &&
                v2.get().sourceMatched === null &&
                !v2.get().inspectionPaging.canPrevious,
            "fresh-Read-clears-source-and-restarts-chain",
        );
        await navigate("next", "next-second");
        const second = await expectedPage("second", 64, 130),
            secondHash = await digest(second.page);
        await capture("d05-page-second");
        await navigate("next", "next-third");
        const third = await expectedPage("third", 2, 130);
        check(
            third.page.next_cursor === null &&
                !v2.get().inspectionPaging.canNext,
            "third-page-final-boundary",
        );
        await capture("d05-page-third");
        await navigate("previous", "back-second");
        check(
            (await digest(
                (await expectedPage("back-second", 64, 130)).page,
            )) === secondHash,
            "Previous-refetches-actual-same-second-page",
        );
        await capture("d05-page-back-second");
        await navigate("previous", "back-first");
        check(
            (await digest((await expectedPage("back-first", 64, 130)).page)) ===
                firstHash && !v2.get().inspectionPaging.canPrevious,
            "Previous-null-cursor-restores-real-first-page",
        );
        await capture("d05-page-back-first");
        await navigate("next", "forward-refetch");
        await expectedPage("forward-refetch", 64, 130);
        await capture("d05-page-forward-refetched");
        await navigate("previous", "pending-base-first");
        const pending = await holdNext();
        await capture("d05-page-pending-next");
        release(pending.held);
        await idle();
        const delivered = await expectedPage("held-delivery", 64, 130);
        check(
            (await digest(delivered.page)) === pending.call.replySha256,
            "held-actual-reply-digest-becomes-displayed-page",
        );
        await navigate("previous", "error-base-first");
        const old = v2.get().inspection!,
            errorBefore = queryCalls().length;
        g.dropNextInspectorPagingReply = true;
        button("next").click();
        await until(
            () => !v2.get().queryBusy && v2.get().error === "Transport",
            "one-post-native-delivery-drop-visible",
        );
        await idle();
        check(
            queryCalls().length === errorBefore + 1 &&
                v2.get().inspection === old &&
                v2.get().inspectionPaging.retainedPrevious === 0 &&
                !g.dropNextInspectorPagingReply,
            "delivery-drop-keeps-old-page-chain-and-consumes-flag",
        );
        const dropped = queryCalls().at(-1)!;
        check(
            dropped.deliveryDropped &&
                dropped.settled &&
                dropped.replySha256 !== null &&
                HEX.test(dropped.replySha256),
            "drop-keeps-real-successful-native-reply-digest",
        );
        await capture("d05-page-error");
        await navigate("next", "explicit-retry");
        await expectedPage("retry-second", 64, 130);
        check(
            structural(queryCalls().at(-1)!.command) ===
                structural(dropped.command),
            "explicit-retry-reissues-exact-query-and-cursor",
        );
        await capture("d05-page-retry-second");
        await setForm("history", "D05_PAGING_ROW_043_MIRA");
        check(
            !v2.get().inspectionPaging.bound &&
                button("next").disabled &&
                button("previous").disabled,
            "search-edit-disables-old-bound-chain",
        );
        await read("history", "D05_PAGING_ROW_043_MIRA");
        await expectedPage("search", 2, 2);
        await capture("d05-page-search-reset");
        await read("history", "", 23);
        await expectedPage("historical", 64, 67, 23);
        await capture("d05-page-historical");
        await navigate("next", "historical-next");
        await expectedPage("historical-last", 3, 67, 23);
        await lens("mira");
        const mira = await read();
        check(
            mira.page.total === 22 &&
                mira.page.rows.length === 22 &&
                mira.page.rows.every((row) => row.kind === "event"),
            "Mira-actual22-witnessed-events-no-private-messages",
        );
        noPrivate(JSON.stringify(mira.page), "mira");
        await capture("d05-page-mira");
        const miraKnowledge = await read("knowledge");
        check(
            JSON.stringify(miraKnowledge.page).includes(
                "D05_MIRA_PRIVATE_BELIEF_812",
            ),
            "Mira-own-seed-belief-positive",
        );
        noPrivate(JSON.stringify(miraKnowledge.page), "mira");
        for (const [sequence, expected] of [
            [2, 1],
            [3, 0],
        ] as const) {
            const query: InspectionQueryV2 = {
                ...mira.query,
                view: "history",
                cursor: null,
                search: `"sequence":${sequence},`,
            };
            const filtered = checkedPageV2(
                await g.call({
                    op: "inspection_query",
                    session: v2.get().context!.session,
                    query,
                }),
                query,
                "player",
            );
            check(
                filtered.total === expected &&
                    filtered.rows.length === expected,
                `Mira-actual-source-sequence${sequence}-eligibility-${expected}`,
            );
            noPrivate(JSON.stringify(filtered), "mira");
        }
        await lens("sable");
        const sable = await read();
        check(
            sable.page.total === 0 &&
                sable.page.rows.length === 0 &&
                !v2.get().inspectionPaging.canPrevious &&
                !v2.get().inspectionPaging.canNext,
            "Sable-empty-permitted-history-not-padded",
        );
        noPrivate(JSON.stringify(sable.page), "sable");
        await capture("d05-page-sable");
        await lens("player");
        const knowledge = await read("knowledge");
        check(
            JSON.stringify(knowledge.page).includes(
                "D05_PLAYER_SEED_SECRET_731",
            ),
            "Player-seed-authorized-secret-positive",
        );
        noPrivate(JSON.stringify(knowledge.page), "player");
        await lens("omniscient");
        await read();
        await expectedPage("Omni-first", 64, 129);
        await navigate("next", "Omni-second");
        await expectedPage("Omni-second", 64, 129);
        await navigate("next", "Omni-third");
        await expectedPage("Omni-third", 1, 129);
        const truth = await read("knowledge");
        check(
            JSON.stringify(truth.page).includes(
                "D05_UNOBSERVED_AUTHOR_TRUTH_913",
            ),
            "Omni-truth-inspection-positive-without-actor-transfer",
        );
        await oracle("after-all-observer-queries");
        await c.resume(OTHER);
        await until(
            () =>
                c.selected()?.scope.story === OTHER.story &&
                v2.get().context === null &&
                !document.querySelector(".v2-play"),
            "actual-Domain1-story-clears-mounted-V2-route",
        );
        await frames();
        check(
            !document
                .getElementById("root")
                ?.textContent?.includes("D05_PAGING_ROW_"),
            "other-story-no-old-private-V2-body",
        );
        await capture("d05-page-other-story");
        const otherQuery: InspectionQueryV2 = {
            version: 2,
            scope: OTHER,
            expected_head: 1,
            at_revision: null,
            observer: { kind: "player" },
            view: "history",
            search: "",
            cursor: null,
            limit: 64,
        };
        const otherActual = checkedPageV2(
            await g.call({
                op: "inspection_query",
                session: c.selected()!.id,
                query: otherQuery,
            }),
            otherQuery,
            "player",
        );
        check(
            otherActual.total === 3 &&
                otherActual.rows.length === 3 &&
                JSON.stringify(otherActual).includes(
                    "D05_OTHER_STORY_MESSAGE_516",
                ) &&
                !JSON.stringify(otherActual).includes("D05_PAGING_ROW_"),
            "actual-Domain1-Host-read-separate-from-mounted-V2-proof",
        );
        await c.resume(CHILD);
        await idle();
        await lens("player");
        await read();
        await navigate("next", "before-same-head-refresh");
        const oldSnapshot = v2.get().snapshot;
        await v2.refresh(false);
        await idle();
        check(
            v2.get().snapshot !== oldSnapshot &&
                v2.get().snapshot?.revision === 44 &&
                !v2.get().inspectionPaging.bound &&
                button("previous").disabled &&
                button("next").disabled,
            "actual-same-head-snapshot-replacement-retires-chain",
        );
        await capture("d05-page-same-head-refresh");
        const retained = v2.get().inspection,
            invalidCalls = queryCalls().length;
        await setForm("history", "x".repeat(257));
        const invalidSubmit = button("read");
        invalidSubmit.form!.requestSubmit(invalidSubmit);
        await until(
            () => v2.get().error === "InvalidRequest" && !v2.get().queryBusy,
            "actual-fresh-form-validation-refusal",
        );
        await frames();
        check(
            v2.get().inspection === retained &&
                retained?.query.search === "" &&
                !v2.get().inspectionPaging.bound &&
                button("previous").disabled &&
                button("next").disabled &&
                queryCalls().length === invalidCalls,
            "failed-fresh-Read-retains-own-bound-body-no-old-chain-no-native-dispatch",
        );
        await read();
        const stale = await holdNext();
        await lens("sable");
        check(
            v2.get().inspection === null && v2.get().source === null,
            "actor-prop-retires-held-private-presentation",
        );
        release(stale.held);
        await idle();
        check(
            v2.get().inspection === null &&
                !v2.get().inspectionPaging.bound &&
                v2.get().source === null,
            "late-native-read-cannot-republish-old-page-chain-source",
        );
        await read();
        await capture("d05-page-stale-delivery");
        await read("summaries");
        check(
            v2.get().inspection?.page.status === "unsupported" &&
                v2.get().inspection?.page.total === 0,
            "actual-shared-unsupported-view-no-substitute",
        );
        await capture("d05-page-unsupported");
        await lens("player");
        await read();
        const bound = v2.get().inspection!,
            baseQuery = bound.query;
        for (const [expected, patch] of [
            ["Scope", { scope: OTHER }],
            ["Stale", { expected_head: 43 }],
            [
                "UnknownObserver",
                { observer: { kind: "character", id: "d05-unknown-actor" } },
            ],
            ["InvalidCursor", { cursor: "invalid-fixed-cursor" }],
        ] as const) {
            let actual = "NoRefusal";
            try {
                await g.call({
                    op: "inspection_query",
                    session: v2.get().context!.session,
                    query: { ...baseQuery, ...patch } as InspectionQueryV2,
                });
            } catch (error) {
                actual = category(error);
            }
            negativeProbes.push({ expected, actual });
            check(
                actual === expected && v2.get().inspection === bound,
                `direct-actual-host-${expected}-refusal-no-UI-page-relabel`,
            );
        }
        await oracle("after-session-reset-negative-and-stale-delivery");
        c.layout(c.get().sidebarSize, c.get().inspectorSize, 150);
        for (const [preset, label] of [
            ["wide", "d05-page-enlarged-wide"],
            ["capture-narrow", "d05-page-enlarged-narrow"],
        ] as const) {
            await invoke("harness_viewport", { preset });
            await until(() => {
                const app =
                    document.querySelector<HTMLElement>(".app.text-150");
                return (
                    !!app &&
                    c.get().textScale === 150 &&
                    Math.abs(
                        Number.parseFloat(getComputedStyle(app).fontSize) /
                            Number.parseFloat(
                                getComputedStyle(document.documentElement)
                                    .fontSize,
                            ) -
                            1.5,
                    ) < 0.000001
                );
            }, "actual150-state-class-computed-font-ratio");
            await capture(label);
        }
        c.layout(c.get().sidebarSize, c.get().inspectorSize, 100);
        await invoke("harness_viewport", { preset: "wide" });
        await until(
            () =>
                !!document.querySelector(".app.text-100") &&
                c.get().textScale === 100,
            "actual100-scale-restored",
        );
        await idle();
        traceBound();
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
        ]);
        check(
            trace().every((item) =>
                item.channel === "host"
                    ? !!item.command && allowed.has(item.command.op)
                    : ["model_status", "inspection_storage"].includes(
                          item.nativeAction ?? "",
                      ),
            ),
            "no-gameplay-generation-author-memory-export-or-model-execution-dispatch",
        );
        const reported = errors.snapshot();
        check(
            reported.every(
                (item) =>
                    item.source === "native" &&
                    [
                        "Scope",
                        "Stale",
                        "UnknownObserver",
                        "InvalidCursor",
                        "Transport",
                    ].includes(item.category),
            ),
            "bounded-only-deliberate-probe-or-delivery-errors",
        );
        for (const probe of negativeProbes)
            check(
                reported.filter((item) => item.category === probe.expected)
                    .length === 1,
                `exactly-one-buffered-explicit-${probe.expected}-probe`,
            );
        check(
            reported.filter((item) => item.category === "Transport").length <=
                1,
            "delivery-double-not-inferred-as-real-native-failure",
        );
        await oracle("before-final-mounted-capture");
        await capture("d05-page-final");
        check(
            structural(captures) === structural(LABELS),
            "exact20-actual-native-success-capture-roster",
        );
        disposing = true;
        await dispose();
        finalOracle = await oracle("after-dispose-before-window-exit");
        traceBound();
        check(
            structural(errors.snapshot()) === structural(reported),
            "dispose-adds-no-unexpected-buffered-error",
        );
        check(
            trace().every((item) =>
                item.channel === "host"
                    ? !!item.command && allowed.has(item.command.op)
                    : ["model_status", "inspection_storage"].includes(
                          item.nativeAction ?? "",
                      ),
            ),
            "closure-roster-has-no-new-gameplay-model-or-provider-dispatch",
        );
        await finish({
            report: {
                synthetic: true,
                passed: true,
                mode: "v2_inspector_paging_v1",
                checks,
                captures,
                nativeCaptures: captures.length,
                baseline,
                finalOracle,
                proofs,
                pageProofs,
                focusObservations,
                negativeProbes,
                calls: trace(),
                errors: errors.snapshot(),
                realModelGeneration: false,
                desktopInput: false,
                rendering: "native-webview2",
                unavailable: [
                    "physical-keyboard-and-screenreader-not-qualified",
                    "disabled-boundary-DOM-focus-observed-not-repaired",
                    "delivery-hold-drop-are-post-IPC-doubles-not-Rust-worker-cancellation",
                    "no-native-restart-process-death-model-SDK-or-OS-isolation",
                    "normal-model-status-metadata-is-not-zero-path-probe-or-SDK-load-telemetry",
                    "images-require-individual-Root-review",
                ],
            },
        });
    } catch (error) {
        const failedCheck = current,
            failureCategory =
                error instanceof Error
                    ? error.message.slice(0, 256)
                    : category(error);
        for (const releaseGate of releases) releaseGate();
        releases.clear();
        g.heldQuery = null;
        g.dropNextInspectorPagingReply = false;
        if (!disposing) {
            try {
                await capture("d05-page-failure", true);
            } catch {
                /* Preserve original failure; failure capture may itself be unavailable. */
            }
            try {
                disposing = true;
                await dispose();
            } catch {
                /* Root supervises unresolved native/child ownership. */
            }
        }
        await finish({
            report: {
                synthetic: true,
                passed: false,
                mode: "v2_inspector_paging_v1",
                failedCheck,
                failureCategory,
                checks,
                captures,
                baseline,
                finalOracle,
                proofs,
                pageProofs,
                focusObservations,
                negativeProbes,
                calls:
                    typeof g.startInspectorPagingTrace === "function"
                        ? trace()
                        : [],
                errors: errors.snapshot(),
                realModelGeneration: false,
                desktopInput: false,
                rendering: captures.length ? "native-webview2" : "unavailable",
                unavailable: [
                    "source-review-is-not-native-or-visual-acceptance",
                    "failed-capture-or-dispose-may-be-unavailable",
                ],
            },
        });
    } finally {
        for (const releaseGate of releases) releaseGate();
        releases.clear();
        g.heldQuery = null;
        g.dropNextInspectorPagingReply = false;
    }
}
