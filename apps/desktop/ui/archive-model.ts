import type { Scope } from "./model";
export const archiveErrors = new Set([
    "Transport",
    "ArchiveAcknowledgementUnavailable",
    "Malformed",
    "Unsupported",
    "Integrity",
    "TooLarge",
    "Conflict",
    "Cancelled",
    "Busy",
    "Full",
    "Database",
    "NotFound",
    "Stale",
    "Closed",
    "Forbidden",
    "ArchiveIo",
    "ArchiveInternal",
    "ArchiveBudget",
    "ArchiveBusy",
    "ArchiveConsentRequired",
    "InvalidArchiveInput",
    "UnknownArchiveOperation",
    "UnknownArchivePreview",
    "ArchivePreviewLimit",
    "UnsafeArchivePath",
    "ArchiveCleanup",
    "PickerUnavailable",
    "ExportExists",
    "Io",
    "Wire",
    "Scope",
    "Session",
    "StorageUnavailable",
]);
export interface ArchivePreview {
    version: 1 | 2 | 3;
    story_id: string;
    title: string;
    root_branch: string;
    branch_heads: Record<string, number>;
    retired_branch_ids?: string[];
    committed_turns: number;
    bytes: number;
    payload_sha256: string;
    privacy_warning: string;
    noncommitted_workflow_transferred: false;
}
export interface PreviewToken {
    version: 1;
    token: string;
    kind: "export" | "import";
    preview: ArchivePreview;
    warning: string;
}
export interface ArchiveResult {
    version: 1;
    status?: "cancelled" | "exported" | "imported" | "failed";
    token?: string;
    kind?: "export" | "import";
    preview?: ArchivePreview;
    warning?: string;
    location?: string;
    payload_sha256?: string;
    root?: Scope;
    branches?: number;
    committed_turns?: number;
    staging_cleanup_complete?: boolean;
    cleanup_complete?: boolean;
    pending_workflow_resumed?: false;
    model_loaded?: false;
    error?: string;
}
export interface ArchiveStatus {
    version: 1;
    operation_id: number;
    running: boolean;
    phase: string;
    error: string | null;
    result: ArchiveResult | null;
}
export type ArchiveCommand =
    | "archive_export_preview"
    | "archive_import_preview"
    | "archive_export"
    | "archive_import";
export function archiveContextKey(
    selected: { id: string; scope: Scope } | null | undefined,
    view: string,
    observer: string,
) {
    return JSON.stringify([
        selected?.id,
        selected?.scope.story,
        selected?.scope.branch,
        view,
        observer,
    ]);
}
// Retain identifiers only, never the private story preview or filesystem path.
export interface ArchiveBinding {
    token: string;
    kind: "export" | "import";
    story: string;
    branch: string;
    payload_sha256: string;
}
export function decodeArchiveBinding(value: unknown): ArchiveBinding {
    if (
        !object(value) ||
        Object.keys(value).length !== 5 ||
        !uuid(value.token) ||
        typeof value.kind !== "string" ||
        !["export", "import"].includes(String(value.kind)) ||
        !id(value.story) ||
        !id(value.branch) ||
        !hash(value.payload_sha256)
    )
        wire();
    return Object.freeze({ ...value }) as unknown as ArchiveBinding;
}
export function archiveBinding(preview: PreviewToken): ArchiveBinding {
    const p = decodePreview(preview);
    return decodeArchiveBinding({
        token: p.token,
        kind: p.kind,
        story: p.preview.story_id,
        branch: p.preview.root_branch,
        payload_sha256: p.preview.payload_sha256,
    });
}
// Shared by the visible controller and retained broker outcome validation.
export function decodeArchiveCompletion(
    status: ArchiveStatus,
    command: ArchiveCommand,
    binding?: ArchiveBinding,
    exportBasis?: { story?: string; branch?: string; head?: number },
): ArchiveResult {
    if (status.running || status.error || !status.result) wire();
    const result = status.result;
    const isPreview = command.endsWith("_preview");
    const kind = command.startsWith("archive_export") ? "export" : "import";
    if (result.token) {
        const p = decodePreview(result);
        if (!isPreview || p.kind !== kind) wire();
        if (
            command === "archive_export_preview" &&
            exportBasis &&
            (!exportBasis.branch ||
                p.preview.story_id !== exportBasis.story ||
                !Object.hasOwn(p.preview.branch_heads, exportBasis.branch) ||
                p.preview.branch_heads[exportBasis.branch] !== exportBasis.head)
        )
            wire();
    } else if (result.status === "failed") {
        const cleanup =
            kind === "export"
                ? result.cleanup_complete
                : result.staging_cleanup_complete;
        if (isPreview || typeof cleanup !== "boolean") wire();
    } else if (result.status === "exported" || result.status === "imported") {
        if (isPreview || !binding || binding.kind !== kind) wire();
        if (result.status === "exported") {
            if (
                kind !== "export" ||
                result.payload_sha256 !== binding.payload_sha256
            )
                wire();
        } else if (
            kind !== "import" ||
            result.root?.story !== binding.story ||
            result.root.branch !== binding.branch
        )
            wire();
    }
    return result;
}
const object = (v: unknown): v is Record<string, unknown> =>
    !!v && typeof v === "object" && !Array.isArray(v);
const integer = (v: unknown, max = Number.MAX_SAFE_INTEGER): v is number =>
    Number.isSafeInteger(v) && Number(v) >= 0 && Number(v) <= max;
const id = (v: unknown): v is string =>
    typeof v === "string" && /^[a-zA-Z0-9_-]{1,64}$/.test(v);
const uuid = (v: unknown): v is string =>
    typeof v === "string" &&
    /^[a-fA-F0-9]{8}(-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}$/.test(v);
const hash = (v: unknown): v is string =>
    typeof v === "string" && /^[a-f0-9]{64}$/.test(v);
function wire(): never {
    throw Error("Wire");
}
export function decodePreview(v: unknown): PreviewToken {
    if (
        !object(v) ||
        Object.keys(v).length !== 5 ||
        ["version", "token", "kind", "preview", "warning"].some(
            (key) => !Object.hasOwn(v, key),
        ) ||
        v.version !== 1 ||
        !uuid(v.token) ||
        typeof v.kind !== "string" ||
        !["export", "import"].includes(String(v.kind)) ||
        !object(v.preview) ||
        typeof v.warning !== "string" ||
        v.warning.length > 2048
    )
        wire();
    const p = v.preview;
    if (
        ![1, 2, 3].includes(Number(p.version)) ||
        typeof p.version !== "number" ||
        !id(p.story_id) ||
        !id(p.root_branch) ||
        typeof p.title !== "string" ||
        [...p.title].length > 256 ||
        !object(p.branch_heads) ||
        Object.keys(p.branch_heads).length < 1 ||
        Object.keys(p.branch_heads).length > 32 ||
        Object.entries(p.branch_heads).some(
            ([k, h]) => !id(k) || !integer(h),
        ) ||
        !integer(p.branch_heads[p.root_branch]) ||
        !integer(p.committed_turns, 4096) ||
        !integer(p.bytes, 32 * 1024 * 1024) ||
        !hash(p.payload_sha256) ||
        typeof p.privacy_warning !== "string" ||
        p.privacy_warning.length > 2048 ||
        p.noncommitted_workflow_transferred !== false
    )
        wire();
    const fields = [
        "version",
        "story_id",
        "title",
        "root_branch",
        "branch_heads",
        "committed_turns",
        "bytes",
        "payload_sha256",
        "privacy_warning",
        "noncommitted_workflow_transferred",
    ];
    const hasRetired = Object.hasOwn(p, "retired_branch_ids");
    if (p.version === 2 || (p.version === 3 && hasRetired))
        fields.push("retired_branch_ids");
    if (
        Object.keys(p).length !== fields.length ||
        fields.some((key) => !Object.hasOwn(p, key))
    )
        wire();
    // V1 omits retirement metadata; V2 requires a nonempty list. V3's
    // producer omits an empty vector, but an explicit empty array is valid too.
    if (hasRetired) {
        const retired = p.retired_branch_ids;
        if (
            !Array.isArray(retired) ||
            (p.version === 2 && retired.length === 0) ||
            retired.length > 256 ||
            retired.some(
                (value, index) =>
                    !id(value) ||
                    value === p.root_branch ||
                    (index > 0 && retired[index - 1] >= value),
            ) ||
            new Set([...Object.keys(p.branch_heads), ...retired]).size > 256
        )
            wire();
    }
    return v as unknown as PreviewToken;
}
export function decodeStatus(v: unknown): ArchiveStatus {
    if (
        !object(v) ||
        Object.keys(v).length !== 6 ||
        !["version", "operation_id", "running", "phase", "error", "result"].every(
            (key) => Object.hasOwn(v, key),
        ) ||
        v.version !== 1 ||
        !integer(v.operation_id) ||
        v.operation_id === 0 ||
        typeof v.running !== "boolean" ||
        typeof v.phase !== "string" ||
        ![
            "starting",
            "capturing",
            "choosing_input",
            "validating",
            "choosing_destination",
            "writing",
            "staging",
            "importing",
            "completed",
            "error",
        ].includes(String(v.phase)) ||
        !(
            v.error === null ||
            (typeof v.error === "string" && archiveErrors.has(v.error))
        ) ||
        !(v.result === null || object(v.result))
    )
        wire();
    if (object(v.result)) {
        const r = v.result;
        if (r.version !== 1) wire();
        if (Object.hasOwn(r, "token")) decodePreview(r);
        else if (
            typeof r.status !== "string" ||
            !["cancelled", "exported", "imported", "failed"].includes(
                String(r.status),
            )
        )
            wire();
        if (r.status === "cancelled" && Object.keys(r).length !== 2) wire();
        if (
            r.status === "exported" &&
            (Object.keys(r).length !== 4 ||
                typeof r.location !== "string" ||
                r.location.length > 30000 ||
                !hash(r.payload_sha256))
        )
            wire();
        if (
            r.status === "imported" &&
            (Object.keys(r).length !== 8 ||
                !object(r.root) ||
                Object.keys(r.root).length !== 2 ||
                !id(r.root.story) ||
                !id(r.root.branch) ||
                !integer(r.branches, 32) ||
                !integer(r.committed_turns, 4096) ||
                r.staging_cleanup_complete !== true ||
                r.pending_workflow_resumed !== false ||
                r.model_loaded !== false)
        )
            wire();
        if (
            r.status === "failed" &&
            (Object.keys(r).length !== 4 ||
                typeof r.error !== "string" ||
                !archiveErrors.has(r.error) ||
                !(
                    typeof r.staging_cleanup_complete === "boolean" ||
                    typeof r.cleanup_complete === "boolean"
                ))
        )
            wire();
    }
    if (v.running && (v.result !== null || v.error !== null)) wire();
    if (v.running && ["completed", "error"].includes(String(v.phase))) wire();
    if (
        !v.running &&
        !(
            (v.phase === "completed" &&
                v.result !== null &&
                v.error === null) ||
            (v.phase === "error" && v.result === null && v.error !== null)
        )
    )
        wire();
    return v as unknown as ArchiveStatus;
}
