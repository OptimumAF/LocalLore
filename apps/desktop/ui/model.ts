import type { TraceState } from "./trace-model";
import type { QueryState } from "./query-model";
import type { Envelope as HostEnvelope } from "./host.generated";
export type Command = HostEnvelope["command"];
export type Request = Extract<Command, { op: "submit" }>["request"];
export type Scope = Request["scope"];
export type FakeMode = Extract<Command, { op: "submit" }>["mode"];
export type Action = "give" | "ability" | "wait" | "dialogue";
export type Json =
    null | boolean | number | string | Json[] | { [key: string]: Json };
export interface ModelState {
    operation_id: number;
    resident: boolean;
    phase: string;
    percent: number;
    imported: boolean;
    loaded: boolean;
    error: string | null;
    profile: Record<string, Json> | null;
    available_profile: {
        id: string;
        model_bytes: number;
        model_sha256: string;
        runtime_revision: string;
        device: string;
        qualification: string;
    };
}
export interface Receipt {
    version?: number;
    play?: {
        version: number;
        policy: string;
        prompt_version: string;
        fallback: boolean;
        repairs: number;
        profile: Record<string, Json>;
        stages: { stage: string; elapsed_ms: number }[];
        scene?: { version: 1; frame_sha256: string };
        story_presentation?: { version: 1; presentation_sha256: string };
    };
    request: Request;
    proposal: Json;
    events: { sequence: number; scope: Scope; turn: string; outcome: Json }[];
    narration: string;
}
export interface Context {
    revision: number;
    scope: Scope;
    observer: string;
    self_state: { name: string; energy: number; location: string };
    observations: Json[];
    facts: Record<string, string>;
    beliefs: Json[];
}
export interface PlayView {
    rules?: string;
    revision: number;
    scope: Scope;
    player: Context;
    inventory: Record<string, Json>;
    receipts: Receipt[];
}
export interface SavedStory {
    scope: Scope;
    title: string;
    revision: number;
    drafts: number;
}
export interface Workspace {
    persistent: true;
    location: string;
    schema_version: number;
    database_schema_version?: number;
    stories: SavedStory[];
}
export interface Session {
    id: string;
    scope: Scope;
    name: string;
    revision: number;
}
export interface TurnStatus {
    turn: string;
    scope: Scope;
    expected_revision: number;
    phase: string;
    error: string | null;
    receipt: Receipt | null;
}
export interface Pending {
    session: string;
    scope: Scope;
    turn: string;
    expectedRevision: number;
    stage: string;
}
export interface ErrorRecord {
    source: "native" | "frontend";
    category: string;
}
export interface Diff {
    path: string;
    before: Json;
    after: Json;
}
export type ExportMode = "diagnostics" | "player" | "full" | "database";
export interface ExportPreview {
    token: string;
    manifest: {
        scope: Scope;
        revision: number;
        mode: ExportMode;
        [key: string]: unknown;
    };
    expires_seconds: number;
    files: { path: string; bytes: number }[];
}
export interface ExportState {
    shown: boolean;
    imported: boolean;
    mode: ExportMode;
    busy: boolean;
    preview: ExportPreview | null;
    savedLocation: string | null;
    selectedFile: string;
    opened: {
        text: string;
        truncated: boolean;
        bytes: number;
        path: string;
    } | null;
    storage: { location: string; schema_version: number } | null;
    error: string | null;
    notice: string;
}
export interface State {
    trace: TraceState;
    query: QueryState;
    labPending: boolean;
    model: ModelState | null;
    freeTextProvider: null | {
        provider: "scene-native-fixture-v1";
        kind: "synthetic_fixture";
    };
    modelBusy: boolean;
    modelCancelReady: boolean;
    modelShown: boolean;
    playMode: "fixture" | "local";
    inputKind: "action" | "dialogue";
    exports: ExportState;
    workspace: Workspace | null;
    ephemeral: boolean;
    starting: boolean;
    sessions: Session[];
    selectedId: string | null;
    view: "play" | "lab";
    observer: string;
    play: PlayView | null;
    playV2?: import("./v2-view-model").PlaySnapshotV2 | null;
    inspection: Json;
    inspectionRevision: number | null;
    inspectionObserver: string | null;
    pending: Pending | null;
    turnStatus: TurnStatus | null;
    visibleError: string | null;
    draft: string;
    action: Action;
    fakeMode: FakeMode;
    inspectorOpen: boolean;
    receiptTurn: string | null;
    page: number;
    sidebarSize: number;
    inspectorSize: number;
    textScale: number;
    diff: Diff[];
    diffRevision: number | null;
    notice: string;
    disposed: boolean;
}
export const PAGE_SIZE = 12;
export const categories = new Set([
    "CaptureConsentRequired",
    "CaptureNotRetained",
    "TraceUnavailable",
    "UnknownObserver",
    "InvalidBoundary",
    "InvalidCursor",
    "InvalidRequest",
    "UnsupportedBranch",
    "ModelOperationUnknown",
    "StaleModelOperation",
    "ClarificationRequired",
    "ModelInvalid",
    "ModelUnavailable",
    "ModelLoaded",
    "ModelExists",
    "WorkerUnavailable",
    "Protocol",
    "Runtime",
    "Cleanup",
    "Timeout",
    "InsufficientSpace",
    "InvalidExport",
    "PreviewLimit",
    "UnknownExport",
    "ExpiredExport",
    "AlreadySaved",
    "NotSaved",
    "ChangedExport",
    "ExportExists",
    "UnsafeDestination",
    "PickerUnavailable",
    "ForeignDatabase",
    "BackupRequired",
    "BackupExists",
    "InvalidSeed",
    "DuplicateStory",
    "NotFound",
    "Database",
    "Integrity",
    "Full",
    "Io",
    "InvalidInput",
    "FutureVersion",
    "SchemaMismatch",
    "Storage",
    "StorageUnavailable",
    "Corrupt",
    "Conflict",
    "Version",
    "Scope",
    "Stale",
    "RetryMismatch",
    "Malformed",
    "TooLarge",
    "Agency",
    "AuthorUiRequired",
    "ClarificationRequired",
    "UnknownReference",
    "DeadActor",
    "Location",
    "Inventory",
    "Resource",
    "Ability",
    "Knowledge",
    "Rule",
    "Cancelled",
    "Provider",
    "Timeout",
    "Narration",
    "CorruptHistory",
    "Closed",
    "UnknownTurn",
    "NotReady",
    "TurnLimit",
    "SessionLimit",
    "WorkerLimit",
    "Busy",
    "Forbidden",
    "Unsupported",
    "Transport",
    "TransportUnknown",
    "Wire",
    "UnhandledError",
    "RenderError",
    "CopyFailed",
    "SessionRequired",
    "DraftRequired",
    "Disposed",
]);
export function category(error: unknown): string {
    const value =
        error instanceof Error
            ? error.message
            : typeof error === "string"
              ? error
              : "";
    return categories.has(value) ? value : "Transport";
}
export class ErrorBuffer {
    private records: ErrorRecord[] = [];
    add(source: ErrorRecord["source"], value: unknown) {
        this.records = [
            ...this.records.slice(-63),
            { source, category: category(value) },
        ];
    }
    snapshot() {
        return this.records.map((value) => ({ ...value }));
    }
}
export interface Gateway {
    readonly playSnapshotV2?: boolean;
    call(command: Command): Promise<unknown>;
    native?(
        command: NativeAction,
        args: Record<string, unknown>,
    ): Promise<unknown>;
}
export type NativeAction =
    | "capture_preview"
    | "capture_save"
    | "capture_revoke"
    | "model_status"
    | "model_import"
    | "model_load"
    | "model_unload"
    | "model_cancel"
    | "inspection_database_preview"
    | "inspection_preview"
    | "inspection_save"
    | "inspection_cancel"
    | "inspection_open"
    | "inspection_storage"
    | "inspection_load";
export class IpcGateway implements Gateway {
    readonly playSnapshotV2 = true;
    constructor(
        private invoke: (
            command: string,
            args: Record<string, unknown>,
        ) => Promise<unknown>,
        readonly errors: ErrorBuffer,
    ) {}
    async native(
        command: NativeAction,
        args: Record<string, unknown>,
    ): Promise<unknown> {
        try {
            return await this.invoke(command, args);
        } catch (error) {
            const value = category(error);
            this.errors.add("native", value);
            throw new Error(value);
        }
    }
    async call(command: Command): Promise<unknown> {
        try {
            const reply = (await this.invoke("host_call", {
                input: JSON.stringify({ version: 1, command }),
            })) as {
                version?: number;
                status?: string;
                data?: unknown;
                error?: unknown;
            };
            if (reply?.version !== 1) throw new Error("Wire");
            if (reply.status !== "ok") throw new Error(category(reply.error));
            if (
                reply.data &&
                typeof reply.data === "object" &&
                "error" in reply.data &&
                typeof reply.data.error === "string"
            )
                this.errors.add("native", reply.data.error);
            return reply.data;
        } catch (error) {
            const value = category(error);
            this.errors.add("native", value);
            throw new Error(value);
        }
    }
}
export function request(
    scope: Scope,
    turn: string,
    revision: number,
    action: Action,
    draft: string,
): Request {
    return {
        version: 1,
        scope,
        turn,
        expected_revision: revision,
        intent:
            action === "dialogue"
                ? {
                      kind: "dialogue",
                      value: { text: draft, audience: ["mira"] },
                  }
                : {
                      kind: "actions",
                      value:
                          action === "give"
                              ? [
                                    {
                                        op: "give",
                                        item: "potion",
                                        to: "mira",
                                        quantity: 1,
                                    },
                                ]
                              : action === "ability"
                                ? [{ op: "use_ability", ability: "teleport" }]
                                : [{ op: "wait", ticks: 1 }],
                  },
    };
}
export function sameScope(a: Scope, b: Scope) {
    return a.story === b.story && a.branch === b.branch;
}
export function composerShortcut(event: {
    key: string;
    shiftKey: boolean;
    isComposing: boolean;
}) {
    return event.key === "Enter" && !event.shiftKey && !event.isComposing
        ? "submit"
        : "edit";
}
export function structural(value: unknown): string {
    if (Array.isArray(value)) return `[${value.map(structural).join(",")}]`;
    if (value && typeof value === "object")
        return `{${Object.entries(value)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([key, v]) => `${JSON.stringify(key)}:${structural(v)}`)
            .join(",")}}`;
    return JSON.stringify(value);
}
export function playView(
    value: unknown,
    scope: Scope,
    revision: number,
): PlayView {
    const view = value as PlayView;
    // Rust owns inherited-history eligibility. Preserve each accepted receipt's
    // original scope instead of relabelling parent history as the selected child.
    const originalScope = (s: unknown): s is Scope => {
        if (!s || typeof s !== "object" || Array.isArray(s)) return false;
        const v = s as Record<string, unknown>;
        return (
            Object.keys(v).length === 2 &&
            v.story === scope.story &&
            typeof v.branch === "string" &&
            /^[A-Za-z0-9_-]{1,64}$/.test(v.branch)
        );
    };
    if (
        !view ||
        view.revision !== revision ||
        !view.scope ||
        !sameScope(view.scope, scope) ||
        view.player?.revision !== revision ||
        !view.player.scope ||
        !sameScope(view.player.scope, scope) ||
        view.player.observer !== "player" ||
        !view.player.self_state ||
        (view.rules !== undefined && typeof view.rules !== "string") ||
        !view.inventory ||
        typeof view.inventory !== "object" ||
        !Array.isArray(view.receipts) ||
        view.receipts.some(
            (r) =>
                !r ||
                !originalScope(r.request?.scope) ||
                !Array.isArray(r.events) ||
                r.events.some(
                    (e) =>
                        !e ||
                        !e.scope ||
                        !Number.isSafeInteger(e.sequence) ||
                        e.sequence < 1 ||
                        e.sequence > revision ||
                        !sameScope(e.scope, r.request.scope),
                ) ||
                typeof r.narration !== "string",
        )
    )
        throw new Error("Wire");
    return view;
}
// Presentation-only comparison of two server snapshots. Never applies a gameplay effect.
export function difference(
    before: unknown,
    after: unknown,
    path = "",
    output: Diff[] = [],
): Diff[] {
    if (
        output.length >= 128 ||
        JSON.stringify(before) === JSON.stringify(after)
    )
        return output;
    if (
        before &&
        after &&
        typeof before === "object" &&
        typeof after === "object" &&
        !Array.isArray(before) &&
        !Array.isArray(after)
    ) {
        const a = before as Record<string, unknown>,
            b = after as Record<string, unknown>;
        for (const key of new Set([...Object.keys(a), ...Object.keys(b)]))
            difference(a[key], b[key], `${path}/${key}`, output);
    } else
        output.push({
            path,
            before: (before ?? null) as Json,
            after: (after ?? null) as Json,
        });
    return output;
}
