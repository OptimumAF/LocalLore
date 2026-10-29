// Optional inspection metadata only. Rust owns permission, exact native attempt
// ownership and validation. A retained decision is not final commit or quality.
import type { Command, Scope } from "./model";

export type NarrationValidationQueryV1 = Extract<
    Command,
    {
        op: "trace_narration_validation_read_v1";
    }
>;
const rejectionCategories = [
    "malformed",
    "version",
    "scope",
    "rule",
    "agency",
    "deadline",
    "retry_mismatch",
    "too_large",
    "author_ui_required",
    "clarification_required",
    "unknown_reference",
    "dead_actor",
    "location",
    "inventory",
    "resource",
    "ability",
    "knowledge",
    "provider",
    "corrupt_history",
] as const;
const reasons = [
    "unclassified",
    "scene_first_person",
    "scene_unapproved_movement",
] as const;
export type NarrationValidationDecisionV1 = Readonly<
    | { version: 1; outcome: "accepted"; error: null; reason: null }
    | { version: 1; outcome: "cancelled"; error: "cancelled"; reason: null }
    | { version: 1; outcome: "stale"; error: "stale"; reason: null }
    | {
          version: 1;
          outcome: "rejected";
          error: "narration";
          reason: (typeof reasons)[number];
      }
    | {
          version: 1;
          outcome: "rejected";
          error: (typeof rejectionCategories)[number];
          reason: null;
      }
>;
type Bound = Readonly<{
    version: 1;
    session: string;
    scope: Readonly<Scope>;
    head: number;
    base_revision: number;
    turn: string;
    attempt: number;
    observer: "player";
    generation_grant: false;
}>;
export type NarrationValidationDataV1 = Bound &
    (
        | Readonly<{
              status: "recorded";
              decision: NarrationValidationDecisionV1;
          }>
        | Readonly<{ status: "unavailable" }>
    );

type ObjectData = Record<string, unknown>;
const encoder = new TextEncoder();
function wire(condition: unknown): asserts condition {
    if (!condition) throw Error("Wire");
}
function utf8(value: string): number {
    for (let i = 0; i < value.length; i++) {
        const c = value.charCodeAt(i);
        if (c >= 0xd800 && c <= 0xdbff) {
            const n = value.charCodeAt(++i);
            wire(n >= 0xdc00 && n <= 0xdfff);
        } else wire(c < 0xdc00 || c > 0xdfff);
    }
    return encoder.encode(value).length;
}
// The closed DTOs contain no arrays. Read descriptors rather than properties;
// charge the detached JSON encoding while walking, never call input toJSON.
function detached(value: unknown): unknown {
    let bytes = 0;
    const active = new Set<object>();
    const charge = (count: number) => {
        bytes += count;
        wire(bytes <= 4096);
    };
    const visit = (v: unknown, depth: number): unknown => {
        wire(depth <= 8);
        if (typeof v === "string") {
            wire(v.length <= 4096);
            utf8(v);
            charge(utf8(JSON.stringify(v)));
            return v;
        }
        if (typeof v === "number") {
            wire(Number.isSafeInteger(v));
            charge(String(v).length);
            return v;
        }
        if (v === null || typeof v === "boolean") {
            charge(v === false ? 5 : 4);
            return v;
        }
        wire(
            v !== null &&
                typeof v === "object" &&
                !Array.isArray(v) &&
                !active.has(v),
        );
        const prototype = Object.getPrototypeOf(v);
        wire(prototype === Object.prototype || prototype === null);
        const keys = Reflect.ownKeys(v);
        wire(keys.every((key) => typeof key === "string"));
        active.add(v);
        charge(2);
        const copy = Object.create(null) as ObjectData;
        keys.forEach((key, index) => {
            wire(typeof key === "string");
            const descriptor = Object.getOwnPropertyDescriptor(v, key);
            wire(descriptor && "value" in descriptor && descriptor.enumerable);
            wire(key.length <= 4096);
            utf8(key);
            charge(utf8(JSON.stringify(key)) + 1 + (index ? 1 : 0));
            Object.defineProperty(copy, key, {
                value: visit(descriptor.value, depth + 1),
                enumerable: true,
            });
        });
        active.delete(v);
        return Object.freeze(copy);
    };
    return visit(value, 0);
}
function exact(value: unknown, names: readonly string[]): ObjectData {
    wire(value !== null && typeof value === "object" && !Array.isArray(value));
    const object = value as ObjectData;
    wire(
        Object.keys(object).length === names.length &&
            names.every((key) => Object.hasOwn(object, key)),
    );
    return object;
}
function id(value: unknown): asserts value is string {
    wire(typeof value === "string" && /^[A-Za-z0-9_-]{1,64}$/.test(value));
}
function integer(
    value: unknown,
    maximum = Number.MAX_SAFE_INTEGER,
): asserts value is number {
    wire(
        typeof value === "number" &&
            Number.isSafeInteger(value) &&
            value >= 0 &&
            value <= maximum,
    );
}
function scope(value: unknown): Scope {
    const object = exact(value, ["story", "branch"]);
    id(object.story);
    id(object.branch);
    return { story: object.story, branch: object.branch };
}
function decision(value: unknown): NarrationValidationDecisionV1 {
    const object = exact(value, ["version", "outcome", "error", "reason"]);
    wire(object.version === 1);
    if (object.outcome === "accepted")
        wire(object.error === null && object.reason === null);
    else if (object.outcome === "cancelled")
        wire(object.error === "cancelled" && object.reason === null);
    else if (object.outcome === "stale")
        wire(object.error === "stale" && object.reason === null);
    else {
        wire(object.outcome === "rejected");
        if (object.error === "narration")
            wire(reasons.some((reason) => reason === object.reason));
        else
            wire(
                object.reason === null &&
                    rejectionCategories.some((error) => error === object.error),
            );
    }
    return object as NarrationValidationDecisionV1;
}
/** Exactly 25 closed tuples; future/unsupported input is Wire, never a guessed cause. */
export function checkedNarrationValidationDecisionV1(
    value: unknown,
): NarrationValidationDecisionV1 {
    try {
        return decision(detached(value));
    } catch {
        throw Error("Wire");
    }
}
/** Bounds detached DATA only. The existing Rust Host owns its 4096 total-envelope cap. */
export function checkedNarrationValidationDataV1(
    value: unknown,
    query: NarrationValidationQueryV1,
): NarrationValidationDataV1 {
    try {
        const q = exact(detached(query), [
            "op",
            "session",
            "scope",
            "expected_head",
            "base_revision",
            "turn",
            "attempt",
        ]);
        wire(q.op === "trace_narration_validation_read_v1");
        id(q.session);
        id(q.turn);
        integer(q.expected_head);
        integer(q.base_revision);
        integer(q.attempt, 0xffff_ffff);
        const expectedScope = scope(q.scope);
        const data = detached(value) as ObjectData;
        // detached has checked all descriptors before this first property access.
        wire(data !== null && typeof data === "object");
        const recorded = data.status === "recorded";
        exact(data, [
            "version",
            "session",
            "scope",
            "head",
            "base_revision",
            "turn",
            "attempt",
            "observer",
            "generation_grant",
            "status",
            ...(recorded ? ["decision"] : []),
        ]);
        wire(data.version === 1 && (recorded || data.status === "unavailable"));
        id(data.session);
        id(data.turn);
        integer(data.head);
        integer(data.base_revision);
        integer(data.attempt, 0xffff_ffff);
        const actualScope = scope(data.scope);
        wire(
            data.session === q.session &&
                actualScope.story === expectedScope.story &&
                actualScope.branch === expectedScope.branch &&
                data.head === q.expected_head &&
                data.base_revision === q.base_revision &&
                data.turn === q.turn &&
                data.attempt === q.attempt &&
                data.observer === "player" &&
                data.generation_grant === false,
        );
        if (recorded) decision(data.decision);
        return data as NarrationValidationDataV1;
    } catch {
        throw Error("Wire");
    }
}
