import type { Scope } from "./model";

export interface TimelineBranch {
    readonly scope: Scope;
    readonly parent_branch: string | null;
    readonly fork_revision: number | null;
    readonly revision: number;
    readonly drafts: number;
    readonly retired: boolean;
}
export interface TimelineCatalog {
    readonly version: 2;
    readonly story_id: string;
    readonly title: string;
    readonly root_branch: string;
    readonly branches: readonly TimelineBranch[];
}
export interface TimelineContext {
    readonly session: string;
    readonly scope: Scope;
    readonly revision: number;
    readonly view: "play" | "lab";
    readonly observer: string;
    readonly persistent: boolean;
}
export const timelineId = (v: unknown): v is string =>
    typeof v === "string" && /^[A-Za-z0-9_-]{1,64}$/.test(v);
export const timelineNumber = (v: unknown): v is number =>
    typeof v === "number" && Number.isSafeInteger(v) && v >= 0;
function object(v: unknown): v is Record<string, unknown> {
    return !!v && typeof v === "object" && !Array.isArray(v);
}
function keys(v: Record<string, unknown>, expected: string[]) {
    return (
        Object.keys(v).length === expected.length &&
        expected.every((k) => Object.hasOwn(v, k))
    );
}
// Shape/admission checks only. Rust's coherent replay owns ancestry and canon.
export function decodeBranchCatalog(
    value: unknown,
    story: string,
): TimelineCatalog {
    if (!timelineId(story)) throw Error("Scope");
    if (
        !object(value) ||
        !keys(value, [
            "version",
            "story_id",
            "title",
            "root_branch",
            "branches",
        ])
    )
        throw Error("Wire");
    if (value.version !== 2) throw Error("Version");
    if (value.story_id !== story || !timelineId(value.root_branch))
        throw Error("Scope");
    if (
        typeof value.title !== "string" ||
        !value.title ||
        value.title.includes("\0") ||
        [...value.title].length > 256
    )
        throw Error("Wire");
    if (!Array.isArray(value.branches) || value.branches.length > 256)
        throw Error("TooLarge");
    const branches: TimelineBranch[] = value.branches.map((row: unknown) => {
        if (
            !object(row) ||
            !keys(row, [
                "scope",
                "parent_branch",
                "fork_revision",
                "revision",
                "drafts",
                "retired",
            ]) ||
            !object(row.scope) ||
            !keys(row.scope, ["story", "branch"])
        )
            throw Error("Wire");
        if (
            row.scope.story !== story ||
            !timelineId(row.scope.branch) ||
            (row.parent_branch !== null && !timelineId(row.parent_branch))
        )
            throw Error("Scope");
        if (
            !timelineNumber(row.revision) ||
            !timelineNumber(row.drafts) ||
            typeof row.retired !== "boolean" ||
            (row.fork_revision !== null && !timelineNumber(row.fork_revision))
        )
            throw Error("Wire");
        if (
            (row.parent_branch === null) !== (row.fork_revision === null) ||
            (row.fork_revision !== null && row.fork_revision > row.revision)
        )
            throw Error("Wire");
        return Object.freeze({
            scope: Object.freeze({ story, branch: row.scope.branch }),
            parent_branch: row.parent_branch,
            fork_revision: row.fork_revision,
            revision: row.revision,
            drafts: row.drafts,
            retired: row.retired,
        });
    });
    const byId = new Map(branches.map((row) => [row.scope.branch, row]));
    if (byId.size !== branches.length) throw Error("Wire");
    if (branches.length) {
        const root = byId.get(value.root_branch);
        if (!root || root.parent_branch !== null || root.fork_revision !== null)
            throw Error("Wire");
        for (const row of branches) {
            const seen = new Set<string>();
            let current = row;
            for (;;) {
                if (seen.size >= 32 || seen.has(current.scope.branch))
                    throw Error("Wire");
                seen.add(current.scope.branch);
                if (current.parent_branch === null) {
                    if (current.scope.branch !== value.root_branch)
                        throw Error("Wire");
                    break;
                }
                const parent = byId.get(current.parent_branch);
                if (
                    !parent ||
                    current.fork_revision === null ||
                    current.fork_revision > parent.revision
                )
                    throw Error("Wire");
                current = parent;
            }
        }
    }
    const catalog: TimelineCatalog = Object.freeze({
        version: 2,
        story_id: story,
        title: value.title,
        root_branch: value.root_branch,
        branches: Object.freeze(branches),
    });
    if (new TextEncoder().encode(JSON.stringify(catalog)).length > 60 * 1024)
        throw Error("TooLarge");
    return catalog;
}
export function contextIdentity(c: TimelineContext | null): string {
    if (c === null) return "none";
    if (
        typeof c.session !== "string" ||
        !c.session ||
        c.session.length > 128 ||
        !timelineId(c.scope?.story) ||
        !timelineId(c.scope?.branch) ||
        !timelineNumber(c.revision) ||
        !["play", "lab"].includes(c.view) ||
        !timelineId(c.observer) ||
        typeof c.persistent !== "boolean"
    )
        throw Error("Wire");
    return JSON.stringify([
        c.session,
        c.scope.story,
        c.scope.branch,
        c.revision,
        c.view,
        c.observer,
        c.persistent,
    ]);
}
export function timelineAncestry(
    catalog: TimelineCatalog,
    row: TimelineBranch,
): string[] {
    const result = [row.scope.branch];
    let parent = row.parent_branch;
    while (parent !== null && result.length < 32) {
        result.unshift(parent);
        parent =
            catalog.branches.find((b) => b.scope.branch === parent)
                ?.parent_branch ?? null;
    }
    return result;
}
