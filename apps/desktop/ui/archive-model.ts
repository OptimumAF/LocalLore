import type { Scope } from "./model";
export const archiveErrors = new Set([
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
    version: 1;
    story_id: string;
    title: string;
    root_branch: string;
    branch_heads: Record<string, number>;
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
        v.version !== 1 ||
        !uuid(v.token) ||
        !["export", "import"].includes(String(v.kind)) ||
        !object(v.preview) ||
        typeof v.warning !== "string" ||
        v.warning.length > 2048
    )
        wire();
    const p = v.preview;
    if (
        p.version !== 1 ||
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
    return v as unknown as PreviewToken;
}
export function decodeStatus(v: unknown): ArchiveStatus {
    if (
        !object(v) ||
        v.version !== 1 ||
        !integer(v.operation_id) ||
        v.operation_id === 0 ||
        typeof v.running !== "boolean" ||
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
        if (r.token !== undefined) decodePreview(r);
        else if (
            !["cancelled", "exported", "imported", "failed"].includes(
                String(r.status),
            )
        )
            wire();
        if (
            r.status === "exported" &&
            (typeof r.location !== "string" ||
                r.location.length > 30000 ||
                !hash(r.payload_sha256))
        )
            wire();
        if (
            r.status === "imported" &&
            (!object(r.root) ||
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
            (typeof r.error !== "string" || !archiveErrors.has(r.error))
        )
            wire();
    }
    if (v.running && (v.result !== null || v.error !== null)) wire();
    return v as unknown as ArchiveStatus;
}
