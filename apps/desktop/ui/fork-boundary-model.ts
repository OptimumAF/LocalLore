import type { Scope } from "./model";
import { timelineId, timelineNumber } from "./timeline-model";

export interface ForkBoundaryCatalog {
    readonly version: 2;
    readonly scope: Scope;
    readonly head: number;
    readonly boundaries: readonly number[];
}

// Read only own data properties. Native wire JSON cannot contain accessors,
// inherited fields or symbol keys; do not invoke them while rejecting input.
function fields(
    value: unknown,
    keys: readonly string[],
): Record<string, unknown> {
    if (!value || typeof value !== "object" || Array.isArray(value))
        throw Error("Wire");
    const descriptors = Object.getOwnPropertyDescriptors(value);
    if (Reflect.ownKeys(value).length !== keys.length) throw Error("Wire");
    const result: Record<string, unknown> = {};
    for (const key of keys) {
        const descriptor = descriptors[key];
        if (!descriptor || !Object.hasOwn(descriptor, "value"))
            throw Error("Wire");
        result[key] = descriptor.value;
    }
    return result;
}

export function decodeForkBoundaryCatalog(
    value: unknown,
    scope: Scope,
    head: number,
): ForkBoundaryCatalog {
    if (!timelineId(scope.story) || !timelineId(scope.branch))
        throw Error("Scope");
    if (!timelineNumber(head)) throw Error("Stale");
    const row = fields(value, ["version", "scope", "head", "boundaries"]);
    if (row.version !== 2) throw Error("Version");
    const selected = fields(row.scope, ["story", "branch"]);
    if (selected.story !== scope.story || selected.branch !== scope.branch)
        throw Error("Scope");
    if (!timelineNumber(row.head)) throw Error("Wire");
    if (row.head !== head) throw Error("Stale");
    if (!Array.isArray(row.boundaries)) throw Error("Wire");
    const descriptors = Object.getOwnPropertyDescriptors(row.boundaries);
    const length = Object.getOwnPropertyDescriptor(
        row.boundaries,
        "length",
    )?.value;
    if (!timelineNumber(length)) throw Error("Wire");
    if (length > 4097) throw Error("TooLarge");
    if (!length || Reflect.ownKeys(row.boundaries).length !== length + 1)
        throw Error("Wire");
    const boundaries: number[] = [];
    for (let index = 0; index < length; index++) {
        const descriptor = descriptors[String(index)];
        if (!descriptor || !Object.hasOwn(descriptor, "value"))
            throw Error("Wire");
        const boundary: unknown = descriptor.value;
        if (
            !timelineNumber(boundary) ||
            (index > 0 && boundary <= boundaries[index - 1])
        )
            throw Error("Wire");
        boundaries.push(boundary);
    }
    if (boundaries[0] !== 0 || boundaries.at(-1) !== head) throw Error("Wire");
    const catalog: ForkBoundaryCatalog = {
        version: 2,
        scope: Object.freeze({ story: scope.story, branch: scope.branch }),
        head,
        boundaries: Object.freeze(boundaries),
    };
    const encoder = new TextEncoder();
    if (
        encoder.encode(JSON.stringify(catalog)).byteLength > 65536 ||
        encoder.encode(JSON.stringify(catalog, null, 2)).byteLength > 65536
    )
        throw Error("TooLarge");
    return Object.freeze(catalog);
}
