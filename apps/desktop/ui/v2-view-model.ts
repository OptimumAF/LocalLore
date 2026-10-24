// Read-only transport decoding. Rust remains authority for lineage and eligibility.
// No existing app consumer imports this future module yet.
export type ScopeV2 = { story: string; branch: string };
export type ObserverV2 =
    | { kind: "player" }
    | { kind: "character"; id: string }
    | { kind: "omniscient" };
export type ViewV2 =
    | "profiles"
    | "history"
    | "relationships"
    | "knowledge"
    | "promises"
    | "provenance"
    | "turn_diff"
    | "summaries"
    | "retrieval_indexes";
export type RulesV2 = "fantasy_v1" | "narrative_v1";
export type ActorV2 = {
    name: string;
    location: string;
    alive: boolean;
    energy: number;
    abilities: Record<string, number>;
    attributes: Record<string, number>;
    injuries: string[];
    affiliations: string[];
    goals: string[];
};
export type ItemV2 = {
    owner: string;
    quantity: number;
    return_to: string | null;
    healing: boolean;
};
export type PlaySnapshotV2 = {
    version: 2;
    domain_version: 1 | 2;
    scope: ScopeV2;
    revision: number;
    rules: RulesV2;
    player: { observer: string; self_state: ActorV2 };
    inventory: Record<string, ItemV2>;
};
export type InspectionQueryV2 = {
    version: 2;
    scope: ScopeV2;
    expected_head: number;
    at_revision: number | null;
    observer: ObserverV2;
    view: ViewV2;
    cursor: string | null;
    limit: number;
    search: string;
};
export type SourceV2 =
    | { kind: "seed"; value: string }
    | { kind: "withheld" }
    | {
          kind: "scoped_event";
          value: { original_scope: ScopeV2; sequence: number };
      };
export type OriginV2 =
    | "canonical_field"
    | "canonical_truth"
    | "recorded_statement"
    | "subjective_belief"
    | "recorded_discovery"
    | "recorded_observation"
    | "recorded_message"
    | "derived_comparison"
    | "known_as_observed";
export type ConfidenceV2 = "uncertain" | "suspected" | "believed";
type EvidenceV2 =
    { kind: "seed"; value: string } | { kind: "event"; value: number };
type CommitmentV2 = {
    from: string;
    to: string;
    terms: string;
    deadline: number;
    source: EvidenceV2;
    return_item: string | null;
    completed_by: number | null;
};
export type EffectV2 =
    | {
          effect: "given";
          item: string;
          from: string;
          to: string;
          quantity: number;
      }
    | { effect: "consumed"; item: string; actor: string; healed: string | null }
    | { effect: "ability_used"; actor: string; ability: string; cost: number }
    | { effect: "learned"; actor: string; ability: string; rank: number }
    | { effect: "moved"; actor: string; from: string; to: string }
    | {
          effect: "said";
          speaker: string;
          text: string;
          audience: string[];
          source: number;
      }
    | {
          effect: "believed";
          believer: string;
          proposition: string;
          source_claim: number | null;
          source: EvidenceV2;
          confidence: ConfidenceV2;
      }
    | { effect: "discovered"; actor: string; fact: string }
    | { effect: "promised"; id: string; commitment: CommitmentV2 }
    | { effect: "promise_completed"; id: string; return_event: number }
    | { effect: "time_advanced"; from: number; to: number };
export type FieldValueV2 =
    | { type: "text"; value: string }
    | { type: "bool"; value: boolean }
    | { type: "number"; value: number }
    | { type: "texts"; value: string[] }
    | { type: "item"; value: ItemV2 };
export type RowV2 =
    | {
          kind: "clock";
          key: string;
          story_time: number;
          source: SourceV2;
          origin: "canonical_field";
      }
    | {
          kind: "field";
          key: string;
          actor: string;
          field: string;
          value: FieldValueV2;
          source: SourceV2;
          origin: "canonical_field";
      }
    | {
          kind: "event";
          key: string;
          event: {
              sequence: number;
              scope: ScopeV2;
              turn: string;
              story_time: number;
              participants: string[];
              witnesses: string[];
              consequence: EffectV2;
          };
          origin: "recorded_observation";
      }
    | {
          kind: "scoped_message";
          key: string;
          original_scope: ScopeV2;
          turn: string;
          message_kind: "original_input" | "narration";
          text: string;
          event_ids: number[];
          origin: "recorded_message";
      }
    | { kind: "author_correction"; revision: number }
    | {
          kind: "relationship";
          key: string;
          from: string;
          to: string;
          dimension: "respect" | "trust" | "obligation";
          value: number;
          source: SourceV2;
          origin: "canonical_field";
      }
    | {
          kind: "knowledge";
          key: string;
          id: string;
          subject: string | null;
          text: string;
          confidence: ConfidenceV2 | null;
          sources: SourceV2[];
          origin: OriginV2;
      }
    | {
          kind: "promise";
          key: string;
          id: string;
          from: string;
          to: string;
          terms: string;
          deadline: number;
          status: "open" | "overdue" | "fulfilled";
          return_item: string | null;
          sources: SourceV2[];
          origin: "derived_comparison";
      }
    | { kind: "provenance"; key: string; sources: SourceV2[]; origin: OriginV2 }
    | {
          kind: "change";
          key: string;
          before_revision: number;
          after_revision: number;
          before: RowV2 | null;
          after: RowV2 | null;
          origin: "derived_comparison";
      };
export type InspectionPageV2 = {
    version: 2;
    scope: ScopeV2;
    head: number;
    revision: number;
    story_time: number;
    observer: ObserverV2;
    view: ViewV2;
    privacy: "player_visible" | "private_character" | "private_omniscient";
    status: "supported" | "unsupported";
    total: number;
    rows: RowV2[];
    next_cursor: string | null;
    unsupported: string[];
};

type ObjectValue = Record<string, unknown>;
const views = [
    "profiles",
    "history",
    "relationships",
    "knowledge",
    "promises",
    "provenance",
    "turn_diff",
    "summaries",
    "retrieval_indexes",
] as const;
const origins = [
    "canonical_field",
    "canonical_truth",
    "recorded_statement",
    "subjective_belief",
    "recorded_discovery",
    "recorded_observation",
    "recorded_message",
    "derived_comparison",
    "known_as_observed",
] as const;
const confidences = ["uncertain", "suspected", "believed"] as const;
const encoder = new TextEncoder();
function wire(): never {
    throw new Error("Wire");
}
function requireWire(condition: unknown): asserts condition {
    if (!condition) wire();
}
function object(value: unknown): ObjectValue {
    requireWire(
        value !== null && typeof value === "object" && !Array.isArray(value),
    );
    return value as ObjectValue;
}
function exact(value: unknown, keys: readonly string[]): ObjectValue {
    const result = object(value);
    const own = Object.keys(result);
    requireWire(
        own.length === keys.length &&
            keys.every((k) => Object.hasOwn(result, k)),
    );
    return result;
}
function text(value: unknown): string {
    requireWire(typeof value === "string");
    return value;
}
function id(value: unknown): string {
    const s = text(value);
    requireWire(/^[a-zA-Z0-9_-]{1,64}$/.test(s));
    return s;
}
function integer(
    value: unknown,
    min = 0,
    max = Number.MAX_SAFE_INTEGER,
): number {
    requireWire(
        typeof value === "number" &&
            Number.isSafeInteger(value) &&
            value >= min &&
            value <= max,
    );
    return value;
}
function bool(value: unknown): void {
    requireWire(typeof value === "boolean");
}
function oneOf(value: unknown, choices: readonly string[]): string {
    const s = text(value);
    requireWire(choices.includes(s));
    return s;
}
function nullable(value: unknown, check: (value: unknown) => unknown): void {
    if (value !== null) check(value);
}
function list(value: unknown, check: (value: unknown) => unknown): unknown[] {
    requireWire(Array.isArray(value));
    value.forEach(check);
    return value;
}
function set(value: unknown, check: (value: unknown) => unknown): unknown[] {
    const values = list(value, check);
    requireWire(new Set(values).size === values.length);
    return values;
}
function scope(value: unknown, story?: string): ScopeV2 {
    const s = exact(value, ["story", "branch"]);
    id(s.story);
    id(s.branch);
    if (story !== undefined) requireWire(s.story === story);
    return s as ScopeV2;
}
function sameScope(a: ScopeV2, b: ScopeV2): boolean {
    return a.story === b.story && a.branch === b.branch;
}
function observer(value: unknown): ObserverV2 {
    const o = object(value);
    if (o.kind === "character") {
        exact(o, ["kind", "id"]);
        id(o.id);
    } else {
        exact(o, ["kind"]);
        oneOf(o.kind, ["player", "omniscient"]);
    }
    return o as ObserverV2;
}
function cursor(value: unknown): void {
    if (value === null) return;
    const c = text(value);
    requireWire(
        encoder.encode(c).length <= 128 &&
            /^2:[1-9][0-9]*:[a-f0-9]{64}$/.test(c),
    );
    integer(Number(c.split(":")[1]), 1);
}
function utf8(value: string): number {
    for (let i = 0; i < value.length; i++) {
        const code = value.charCodeAt(i);
        if (code >= 0xd800 && code <= 0xdbff) {
            const next = value.charCodeAt(++i);
            requireWire(next >= 0xdc00 && next <= 0xdfff);
        } else requireWire(code < 0xdc00 || code > 0xdfff);
    }
    return encoder.encode(value).length;
}

// Inspect descriptors before reading values or stringify. No getter/toJSON invocation.
// Transport JSON is the boundary; already-overwritten raw duplicate keys are unrecoverable.
function detached(value: unknown, maximum: number): unknown {
    const active = new WeakSet<object>();
    let cost = 0;
    const charge = (n: number) => {
        cost += n;
        requireWire(cost <= maximum);
    };
    const walk = (input: unknown, depth: number): unknown => {
        requireWire(depth <= 16);
        if (typeof input === "string") {
            utf8(input);
            charge(encoder.encode(JSON.stringify(input)).length);
            return input;
        }
        if (typeof input === "number") {
            integer(input, -Number.MAX_SAFE_INTEGER);
            charge(String(input).length);
            return input;
        }
        if (input === null || typeof input === "boolean") {
            charge(input === false ? 5 : 4);
            return input;
        }
        requireWire(typeof input === "object");
        requireWire(!active.has(input));
        active.add(input);
        const array = Array.isArray(input);
        const prototype = Object.getPrototypeOf(input);
        requireWire(
            array
                ? prototype === Array.prototype
                : prototype === Object.prototype || prototype === null,
        );
        const keys = Reflect.ownKeys(input);
        requireWire(keys.every((k) => typeof k === "string"));
        charge(2);
        let result: unknown;
        if (array) {
            const values: unknown[] = [];
            requireWire(keys.length === input.length + 1);
            for (let i = 0; i < input.length; i++) {
                const d = Object.getOwnPropertyDescriptor(input, String(i));
                requireWire(d && "value" in d && d.enumerable);
                if (i > 0) charge(1);
                values.push(walk(d.value, depth + 1));
            }
            result = values;
        } else {
            const values = Object.create(null) as ObjectValue;
            for (const [index, key] of (keys as string[]).entries()) {
                const d = Object.getOwnPropertyDescriptor(input, key);
                requireWire(d && "value" in d && d.enumerable);
                utf8(key);
                charge(
                    encoder.encode(JSON.stringify(key)).length +
                        1 +
                        (index > 0 ? 1 : 0),
                );
                Object.defineProperty(values, key, {
                    value: walk(d.value, depth + 1),
                    enumerable: true,
                });
            }
            result = values;
        }
        active.delete(input);
        return result;
    };
    const copied = walk(value, 0);
    const encoded = JSON.stringify(copied);
    requireWire(encoder.encode(encoded).length <= maximum);
    return JSON.parse(encoded) as unknown;
}
function actor(value: unknown): void {
    const a = exact(value, [
        "name",
        "location",
        "alive",
        "energy",
        "abilities",
        "attributes",
        "injuries",
        "affiliations",
        "goals",
    ]);
    text(a.name);
    text(a.location);
    bool(a.alive);
    integer(a.energy, 0, 100);
    for (const rank of Object.values(object(a.abilities)))
        integer(rank, 1, 65535);
    for (const attribute of Object.values(object(a.attributes)))
        integer(attribute, -100, 100);
    for (const field of ["injuries", "affiliations", "goals"])
        set(a[field], text);
}
function item(value: unknown): void {
    const i = exact(value, ["owner", "quantity", "return_to", "healing"]);
    id(i.owner);
    integer(i.quantity, 1, 65535);
    nullable(i.return_to, id);
    bool(i.healing);
}
export function checkedPlaySnapshotV2(
    value: unknown,
    selected: ScopeV2,
    revision: number,
): PlaySnapshotV2 {
    const binding = scope(detached(selected, 24576));
    integer(revision);
    const p = exact(detached(value, 262144), [
        "version",
        "domain_version",
        "scope",
        "revision",
        "rules",
        "player",
        "inventory",
    ]);
    requireWire(
        p.version === 2 && (p.domain_version === 1 || p.domain_version === 2),
    );
    requireWire(sameScope(scope(p.scope), binding) && p.revision === revision);
    const rules = oneOf(p.rules, ["fantasy_v1", "narrative_v1"]);
    const player = exact(p.player, ["observer", "self_state"]);
    id(player.observer);
    actor(player.self_state);
    const a = object(player.self_state);
    if (rules === "narrative_v1")
        requireWire(
            a.energy === 0 &&
                Object.keys(object(a.abilities)).length === 0 &&
                Object.keys(object(a.attributes)).length === 0,
        );
    for (const [name, entry] of Object.entries(object(p.inventory))) {
        id(name);
        item(entry);
        requireWire(object(entry).owner === player.observer);
    }
    return p as PlaySnapshotV2;
}

type Binding = {
    story: string;
    revision: number;
    observer: ObserverV2;
    view: ViewV2;
    selectedPlayerId?: string;
};
function source(value: unknown, b: Binding): void {
    const s = object(value);
    switch (s.kind) {
        case "withheld":
            exact(s, ["kind"]);
            return;
        case "seed":
            exact(s, ["kind", "value"]);
            id(s.value);
            return;
        case "scoped_event": {
            exact(s, ["kind", "value"]);
            const v = exact(s.value, ["original_scope", "sequence"]);
            scope(v.original_scope, b.story);
            integer(v.sequence, 1, b.revision);
            return;
        }
        default:
            wire();
    }
}
function sources(value: unknown, b: Binding): void {
    list(value, (s) => source(s, b));
}
function evidence(value: unknown, b: Binding): void {
    const e = exact(value, ["kind", "value"]);
    if (e.kind === "seed") id(e.value);
    else {
        requireWire(e.kind === "event");
        integer(e.value, 1, b.revision);
    }
}
function effect(value: unknown, b: Binding): void {
    const e = object(value);
    const shape = (fields: string[]) => exact(e, ["effect", ...fields]);
    switch (e.effect) {
        case "given":
            shape(["item", "from", "to", "quantity"]);
            id(e.item);
            id(e.from);
            id(e.to);
            integer(e.quantity, 1, 65535);
            break;
        case "consumed":
            shape(["item", "actor", "healed"]);
            id(e.item);
            id(e.actor);
            nullable(e.healed, text);
            break;
        case "ability_used":
            shape(["actor", "ability", "cost"]);
            id(e.actor);
            text(e.ability);
            integer(e.cost, 0, 100);
            break;
        case "learned":
            shape(["actor", "ability", "rank"]);
            id(e.actor);
            text(e.ability);
            integer(e.rank, 1, 65535);
            break;
        case "moved":
            shape(["actor", "from", "to"]);
            id(e.actor);
            text(e.from);
            text(e.to);
            break;
        case "said":
            shape(["speaker", "text", "audience", "source"]);
            id(e.speaker);
            text(e.text);
            set(e.audience, id);
            integer(e.source, 1, b.revision);
            break;
        case "believed":
            shape([
                "believer",
                "proposition",
                "source_claim",
                "source",
                "confidence",
            ]);
            id(e.believer);
            text(e.proposition);
            nullable(e.source_claim, (v) => integer(v, 1, b.revision));
            evidence(e.source, b);
            oneOf(e.confidence, confidences);
            break;
        case "discovered":
            shape(["actor", "fact"]);
            id(e.actor);
            id(e.fact);
            break;
        case "promised": {
            shape(["id", "commitment"]);
            id(e.id);
            const c = exact(e.commitment, [
                "from",
                "to",
                "terms",
                "deadline",
                "source",
                "return_item",
                "completed_by",
            ]);
            id(c.from);
            id(c.to);
            text(c.terms);
            integer(c.deadline);
            evidence(c.source, b);
            nullable(c.return_item, id);
            nullable(c.completed_by, (v) => integer(v, 1, b.revision));
            break;
        }
        case "promise_completed":
            shape(["id", "return_event"]);
            id(e.id);
            integer(e.return_event, 1, b.revision);
            break;
        case "time_advanced":
            shape(["from", "to"]);
            integer(e.from);
            requireWire(integer(e.to) >= (e.from as number));
            break;
        default:
            wire();
    }
}
function fieldValue(value: unknown): void {
    const v = exact(value, ["type", "value"]);
    switch (v.type) {
        case "text":
            text(v.value);
            break;
        case "bool":
            bool(v.value);
            break;
        case "number":
            integer(v.value, -Number.MAX_SAFE_INTEGER);
            break;
        case "texts":
            set(v.value, text);
            break;
        case "item":
            item(v.value);
            break;
        default:
            wire();
    }
}
function row(value: unknown, b: Binding, nested = false): string {
    const r = object(value);
    const keys = (fields: string[]) =>
        exact(r, ["kind", "key", ...fields, "origin"]);
    const origin = (choices: readonly string[]) => oneOf(r.origin, choices);
    if (r.kind === "author_correction") {
        exact(r, ["kind", "revision"]);
        requireWire(
            !nested && b.view === "history" && b.observer.kind === "player",
        );
        integer(r.revision, 1, b.revision);
        return JSON.stringify(["author_correction", r.revision]);
    }
    text(r.key);
    requireWire((r.key as string).length > 0);
    switch (r.kind) {
        case "clock":
            requireWire(nested);
            keys(["story_time", "source"]);
            integer(r.story_time);
            source(r.source, b);
            origin(["canonical_field"]);
            break;
        case "field":
            requireWire(nested || b.view === "profiles");
            keys(["actor", "field", "value", "source"]);
            id(r.actor);
            text(r.field);
            fieldValue(r.value);
            source(r.source, b);
            origin(["canonical_field"]);
            break;
        case "event": {
            requireWire(!nested && b.view === "history");
            keys(["event"]);
            origin(["recorded_observation"]);
            const e = exact(r.event, [
                "sequence",
                "scope",
                "turn",
                "story_time",
                "participants",
                "witnesses",
                "consequence",
            ]);
            integer(e.sequence, 1, b.revision);
            const original = scope(e.scope, b.story);
            id(e.turn);
            integer(e.story_time);
            set(e.participants, id);
            set(e.witnesses, id);
            effect(e.consequence, b);
            return JSON.stringify([
                "event",
                original.story,
                original.branch,
                e.sequence,
            ]);
        }
        case "scoped_message": {
            requireWire(
                !nested &&
                    b.view === "history" &&
                    (b.observer.kind !== "character" ||
                        (b.selectedPlayerId !== undefined &&
                            b.observer.id === b.selectedPlayerId)),
            );
            // Optional ID must come from a coherent native thin snapshot, never the query.
            keys([
                "original_scope",
                "turn",
                "message_kind",
                "text",
                "event_ids",
            ]);
            origin(["recorded_message"]);
            const original = scope(r.original_scope, b.story);
            id(r.turn);
            oneOf(r.message_kind, ["original_input", "narration"]);
            text(r.text);
            const ids = list(r.event_ids, (v) =>
                integer(v, 1, b.revision),
            ) as number[];
            requireWire(
                ids.length > 0 &&
                    ids.length <= 8 &&
                    ids.every((v, i) => i === 0 || v > ids[i - 1]),
            );
            return JSON.stringify([
                "scoped_message",
                original.story,
                original.branch,
                r.turn,
                r.message_kind,
            ]);
        }
        case "relationship":
            requireWire(nested || b.view === "relationships");
            keys(["from", "to", "dimension", "value", "source"]);
            id(r.from);
            id(r.to);
            oneOf(r.dimension, ["respect", "trust", "obligation"]);
            integer(r.value, -100, 100);
            source(r.source, b);
            origin(["canonical_field"]);
            break;
        case "knowledge": {
            keys(["id", "subject", "text", "confidence", "sources"]);
            requireWire(nested || b.view === "knowledge");
            text(r.id);
            nullable(r.subject, id);
            text(r.text);
            nullable(r.confidence, (v) => oneOf(v, confidences));
            sources(r.sources, b);
            origin([
                "canonical_truth",
                "recorded_statement",
                "subjective_belief",
                "recorded_discovery",
                "known_as_observed",
            ]);
            if (r.origin === "canonical_truth")
                requireWire(
                    b.observer.kind === "omniscient" && r.subject === null,
                );
            if (r.origin === "known_as_observed")
                requireWire(
                    b.observer.kind !== "omniscient" && r.subject !== null,
                );
            break;
        }
        case "promise":
            requireWire(nested || b.view === "promises");
            keys([
                "id",
                "from",
                "to",
                "terms",
                "deadline",
                "status",
                "return_item",
                "sources",
            ]);
            id(r.id);
            id(r.from);
            id(r.to);
            text(r.terms);
            integer(r.deadline);
            oneOf(r.status, ["open", "overdue", "fulfilled"]);
            nullable(r.return_item, id);
            sources(r.sources, b);
            origin(["derived_comparison"]);
            break;
        case "provenance":
            requireWire(!nested && b.view === "provenance");
            keys(["sources"]);
            sources(r.sources, b);
            origin(origins);
            break;
        case "change": {
            requireWire(!nested && b.view === "turn_diff");
            keys(["before_revision", "after_revision", "before", "after"]);
            origin(["derived_comparison"]);
            integer(r.before_revision, 0, b.revision);
            requireWire(
                r.after_revision === b.revision &&
                    (r.before_revision as number) < b.revision &&
                    (r.before !== null || r.after !== null),
            );
            if (r.before !== null)
                row(
                    r.before,
                    { ...b, revision: r.before_revision as number },
                    true,
                );
            if (r.after !== null) row(r.after, b, true);
            break;
        }
        default:
            wire();
    }
    return JSON.stringify(["key", r.key]);
}
export function checkedPageV2(
    value: unknown,
    requested: InspectionQueryV2,
    selectedPlayerId?: string,
): InspectionPageV2 {
    if (selectedPlayerId !== undefined) id(selectedPlayerId);
    const q = exact(detached(requested, 24576), [
        "version",
        "scope",
        "expected_head",
        "at_revision",
        "observer",
        "view",
        "cursor",
        "limit",
        "search",
    ]);
    requireWire(q.version === 2);
    const selected = scope(q.scope);
    const head = integer(q.expected_head);
    nullable(q.at_revision, (v) => integer(v, 0, head));
    const lens = observer(q.observer);
    const view = oneOf(q.view, views) as ViewV2;
    cursor(q.cursor);
    const limit = integer(q.limit, 1, 64);
    const search = text(q.search);
    requireWire(
        utf8(search) <= 256 && !/[\u0000-\u001f\u007f-\u009f]/.test(search),
    );
    const p = exact(detached(value, 65536), [
        "version",
        "scope",
        "head",
        "revision",
        "story_time",
        "observer",
        "view",
        "privacy",
        "status",
        "total",
        "rows",
        "next_cursor",
        "unsupported",
    ]);
    const revision = (q.at_revision ?? head) as number;
    requireWire(
        p.version === 2 &&
            sameScope(scope(p.scope), selected) &&
            p.head === head &&
            p.revision === revision &&
            p.view === view,
    );
    const actualObserver = observer(p.observer);
    requireWire(
        actualObserver.kind === lens.kind &&
            (actualObserver.kind !== "character" ||
                (lens.kind === "character" && actualObserver.id === lens.id)),
    );
    integer(p.story_time);
    const total = integer(p.total, 0, 65536);
    requireWire(
        p.privacy ===
            (lens.kind === "player"
                ? "player_visible"
                : lens.kind === "character"
                  ? "private_character"
                  : "private_omniscient"),
    );
    const unsupported = view === "summaries" || view === "retrieval_indexes";
    requireWire(p.status === (unsupported ? "unsupported" : "supported"));
    list(p.unsupported, text);
    cursor(p.next_cursor);
    requireWire(
        Array.isArray(p.rows) &&
            p.rows.length <= limit &&
            p.rows.length <= total &&
            (!unsupported || total === 0),
    );
    const b: Binding = {
        story: selected.story,
        revision,
        observer: lens,
        view,
        selectedPlayerId,
    };
    const identities = p.rows.map((r) => row(r, b));
    requireWire(new Set(identities).size === identities.length);
    const keys = p.rows
        .map((r) => object(r))
        .filter((r) => r.kind !== "author_correction")
        .map((r) => r.key);
    requireWire(new Set(keys).size === keys.length);
    if (p.next_cursor !== null) {
        requireWire(p.rows.length > 0);
        const offset = Number((p.next_cursor as string).split(":")[1]);
        requireWire(offset >= p.rows.length && offset < total);
    }
    if (total === 0) requireWire(p.rows.length === 0 && p.next_cursor === null);
    return p as InspectionPageV2;
}
