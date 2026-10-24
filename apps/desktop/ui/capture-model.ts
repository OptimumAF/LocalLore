import type { Command, Scope } from "./model";
export type CaptureQuery = Extract<Command, { op: "trace_capture_read" }>;
export const artifactKinds = [
    "selected_context",
    "generation_request",
    "raw_director_output",
    "parsed_proposal",
    "validated_plan_not_durable_commit",
    "accepted_candidate_not_durable_commit",
    "raw_narrator_output",
] as const;
export interface CaptureReply {
    scope: Scope;
    head: number;
    base_revision: number;
    observer: "private_player_generation_capture";
    details: {
        version: 1;
        status:
            "disabled" | "expired" | "not_retained" | "recorded" | "truncated";
        identity: {
            scope: Scope;
            base_revision: number;
            observer: string;
            turn: string;
            attempt: number;
        } | null;
        artifacts: {
            kind: (typeof artifactKinds)[number];
            ordinal: number;
            value: unknown;
        }[];
        exact_reconstruction: false;
        privacy: string;
    };
}
export interface CapturePreview {
    token: string;
    manifest: {
        format: "locallore-private-trace";
        version: 1;
        mode: "private_trace";
        scope: Scope;
        revision: number;
        privacy: "private_generation_capture";
        files: { path: "capture.json"; bytes: number; sha256: string }[];
    };
    expires_seconds: 300;
    files: { path: string; bytes: number }[];
    text: string;
}
export const object = (v: unknown): v is Record<string, any> =>
    !!v && typeof v === "object" && !Array.isArray(v);
const keys = (v: Record<string, any>, ks: string[]) =>
    Object.keys(v).sort().join() === [...ks].sort().join();
const sameScope = (v: unknown, s: Scope) =>
    object(v) &&
    keys(v, ["story", "branch"]) &&
    v.story === s.story &&
    v.branch === s.branch;
const size = (v: unknown) => new TextEncoder().encode(JSON.stringify(v)).length;
export function checkedCapture(v: unknown, q: CaptureQuery): CaptureReply {
    const fail = () => {
        throw new Error("Wire");
    };
    if (
        !object(v) ||
        !keys(v, ["scope", "head", "base_revision", "observer", "details"]) ||
        !sameScope(v.scope, q.scope) ||
        v.head !== q.expected_head ||
        v.base_revision !== q.base_revision ||
        v.observer !== "private_player_generation_capture" ||
        size(v) > 262144
    )
        return fail();
    const d = v.details;
    if (
        !object(d) ||
        !keys(d, [
            "version",
            "status",
            "identity",
            "artifacts",
            "exact_reconstruction",
            "privacy",
        ]) ||
        d.version !== 1 ||
        ![
            "disabled",
            "expired",
            "not_retained",
            "recorded",
            "truncated",
        ].includes(d.status) ||
        d.exact_reconstruction !== false ||
        typeof d.privacy !== "string" ||
        d.privacy.length > 512 ||
        !Array.isArray(d.artifacts) ||
        d.artifacts.length > 16
    )
        return fail();
    if (d.identity !== null) {
        const i = d.identity;
        if (
            !object(i) ||
            !keys(i, [
                "scope",
                "base_revision",
                "observer",
                "turn",
                "attempt",
            ]) ||
            !sameScope(i.scope, q.scope) ||
            i.base_revision !== q.base_revision ||
            i.turn !== q.turn ||
            i.attempt !== q.attempt ||
            typeof i.observer !== "string" ||
            !/^[A-Za-z0-9_-]{1,64}$/.test(i.observer)
        )
            return fail();
    }
    if (
        ["recorded", "truncated"].includes(d.status) !==
            (d.identity !== null) ||
        (!["recorded", "truncated"].includes(d.status) && d.artifacts.length)
    )
        return fail();
    for (let index = 0; index < d.artifacts.length; index++) {
        const a = d.artifacts[index];
        if (
            !object(a) ||
            !keys(a, ["kind", "ordinal", "value"]) ||
            !artifactKinds.includes(a.kind) ||
            a.ordinal !== index ||
            size(a) > 49152
        )
            return fail();
    }
    return v as CaptureReply;
}
export async function checkedCapturePreview(
    v: unknown,
    q: CaptureQuery,
): Promise<CapturePreview> {
    if (
        !object(v) ||
        !keys(v, ["token", "manifest", "expires_seconds", "files", "text"]) ||
        typeof v.token !== "string" ||
        !/^[A-Za-z0-9-]{1,64}$/.test(v.token) ||
        v.expires_seconds !== 300 ||
        typeof v.text !== "string" ||
        new TextEncoder().encode(v.text).length > 524288 ||
        !Array.isArray(v.files) ||
        v.files.length !== 2
    )
        throw new Error("Wire");
    const m = v.manifest;
    if (
        !object(m) ||
        m.format !== "locallore-private-trace" ||
        m.version !== 1 ||
        m.mode !== "private_trace" ||
        m.privacy !== "private_generation_capture" ||
        !sameScope(m.scope, q.scope) ||
        m.revision !== q.expected_head ||
        !Array.isArray(m.files) ||
        m.files.length !== 1 ||
        m.files[0].path !== "capture.json"
    )
        throw new Error("Wire");
    const bytes = new TextEncoder().encode(v.text),
        file = m.files[0];
    const digest = [
        ...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
    ]
        .map((x) => x.toString(16).padStart(2, "0"))
        .join("");
    if (
        file.bytes !== bytes.length ||
        file.sha256 !== digest ||
        v.files.some(
            (f: any) =>
                !object(f) ||
                !["capture.json", "manifest.json"].includes(f.path) ||
                !Number.isSafeInteger(f.bytes) ||
                f.bytes < 0,
        ) ||
        new Set(v.files.map((f: any) => f.path)).size !== 2 ||
        v.files.reduce((n: number, f: any) => n + f.bytes, 0) > 1048576
    )
        throw new Error("Wire");
    checkedCapture(JSON.parse(v.text), q);
    return v as CapturePreview;
}
