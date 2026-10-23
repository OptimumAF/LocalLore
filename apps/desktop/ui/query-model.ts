import type { Command, Json } from "./model";
export type InspectionQuery = Extract<
    Command,
    { op: "inspection_query" }
>["query"];
export type InspectionView = InspectionQuery["view"];
export type Source =
    | { kind: "seed"; value: string }
    | { kind: "event"; value: number }
    | { kind: "withheld" };
export type Origin =
    | "canonical_field"
    | "canonical_truth"
    | "recorded_statement"
    | "subjective_belief"
    | "recorded_discovery"
    | "recorded_observation"
    | "recorded_message"
    | "derived_comparison";
type Base = { key: string; origin: Origin };
export type Row = Base &
    (
        | { kind: "clock"; story_time: number; source: Source }
        | {
              kind: "field";
              actor: string;
              field: string;
              value: { type: string; value: Json };
              source: Source;
          }
        | {
              kind: "event";
              event: {
                  sequence: number;
                  scope: InspectionQuery["scope"];
                  turn: string;
                  story_time: number;
                  participants: string[];
                  witnesses: string[];
                  consequence: Record<string, Json>;
              };
          }
        | {
              kind: "message";
              turn: string;
              message_kind: string;
              text: string;
              event_ids: number[];
          }
        | {
              kind: "relationship";
              from: string;
              to: string;
              dimension: string;
              value: number;
              source: Source;
          }
        | {
              kind: "knowledge";
              id: string;
              subject: string | null;
              text: string;
              confidence: string | null;
              sources: Source[];
          }
        | {
              kind: "promise";
              id: string;
              from: string;
              to: string;
              terms: string;
              deadline: number;
              status: string;
              return_item: string | null;
              sources: Source[];
          }
        | { kind: "provenance"; sources: Source[] }
        | {
              kind: "change";
              before_revision: number;
              after_revision: number;
              before: Row | null;
              after: Row | null;
          }
    );
export interface InspectionPage {
    version: 1;
    scope: InspectionQuery["scope"];
    head: number;
    revision: number;
    story_time: number;
    observer: InspectionQuery["observer"];
    view: InspectionView;
    privacy: "player_visible" | "private_character" | "private_omniscient";
    status: "supported" | "unsupported";
    total: number;
    rows: Row[];
    next_cursor: string | null;
    unsupported: string[];
}
export type ChangeTrace = {
    change: Extract<Row, { kind: "change" }>;
    stage: "prior_provenance" | "field_provenance" | "turn_history";
};
export function whyLabel(row: Row): string {
    switch (row.kind) {
        case "change":
            return row.after ? "Why did this change?" : "Why was this removed?";
        case "event":
            return "View accepted source";
        case "message":
            return row.event_ids.length
                ? "View supporting events"
                : "No accepted source available";
        case "provenance":
            return "Source record shown";
        default:
            return "Why is this true?";
    }
}
export function canInspectWhy(row: Row) {
    return (
        row.kind !== "provenance" &&
        (row.kind !== "message" || row.event_ids.length > 0)
    );
}
export interface QueryState {
    trace: ChangeTrace | null;
    shown: boolean;
    view: InspectionView;
    atRevision: number | null;
    search: string;
    limit: number;
    page: InspectionPage | null;
    busy: boolean;
    error: string | null;
    selectedKey: string | null;
    cursors: (string | null)[];
    cursor: string | null;
    notice: string;
}
export const initialQuery = (): QueryState => ({
    trace: null,
    shown: false,
    view: "profiles",
    atRevision: null,
    search: "",
    limit: 12,
    page: null,
    busy: false,
    error: null,
    selectedKey: null,
    cursors: [],
    cursor: null,
    notice: "",
});
export const views: [InspectionView, string][] = [
    ["profiles", "Character state"],
    ["history", "History"],
    ["relationships", "Directed relationships"],
    ["knowledge", "Truth & knowledge"],
    ["promises", "Promises & goals"],
    ["provenance", "Evidence sources"],
    ["turn_diff", "Before & after turn"],
    ["summaries", "Summaries"],
    ["retrieval_indexes", "Retrieval indexes"],
];
export const words = (text: string) =>
    text.replaceAll("_", " ").replaceAll("/", " / ");
export function valueText(value: unknown): string {
    if (value === null || value === undefined) return "Absent";
    if (Array.isArray(value)) return value.map(valueText).join(", ") || "None";
    if (typeof value === "object")
        return Object.entries(value)
            .map(([k, v]) => `${words(k)}: ${valueText(v)}`)
            .join(" · ");
    return String(value);
}
export function rowLabel(row: Row): string {
    switch (row.kind) {
        case "clock":
            return `Story time ${row.story_time}`;
        case "field":
            return `${row.actor} · ${words(row.field)}`;
        case "event":
            return `Event ${row.event.sequence} · ${words(String(row.event.consequence.effect))}`;
        case "message":
            return `${words(row.message_kind)} · ${row.turn}`;
        case "relationship":
            return `${row.from} → ${row.to} · ${words(row.dimension)}`;
        case "knowledge":
            return `${words(row.origin)} · ${row.id}`;
        case "promise":
            return `${row.from} → ${row.to} · ${row.id}`;
        case "provenance":
            return words(row.key);
        case "change":
            return (
                rowLabel(row.after ?? row.before!) +
                ` · r${row.before_revision} → r${row.after_revision}`
            );
    }
}
export function rowValue(row: Row): string {
    switch (row.kind) {
        case "clock":
            return String(row.story_time);
        case "field":
            return valueText(row.value.value);
        case "event":
            return valueText(row.event.consequence);
        case "message":
        case "knowledge":
            return row.text;
        case "relationship":
            return String(row.value);
        case "promise":
            return `${row.terms} · ${row.status} · due ${row.deadline}`;
        case "provenance":
            return `${row.sources.length} permitted source(s)`;
        case "change":
            return `${row.before ? rowValue(row.before) : "Absent"} → ${row.after ? rowValue(row.after) : "Absent"}`;
    }
}
export function rowSources(row: Row): Source[] {
    if ("source" in row) return [row.source];
    if ("sources" in row) return row.sources;
    if (row.kind === "event")
        return [{ kind: "event", value: row.event.sequence }];
    if (row.kind === "message")
        return row.event_ids.map((value) => ({ kind: "event", value }));
    return [];
}
export function checkedPage(
    value: unknown,
    q: InspectionQuery,
): InspectionPage {
    const p = value as InspectionPage;
    const integer = (v: unknown) => Number.isSafeInteger(v) && Number(v) >= 0;
    const source = (s: Source) =>
        s &&
        (s.kind === "withheld" ||
            (s.kind === "seed" && typeof s.value === "string") ||
            (s.kind === "event" && integer(s.value) && s.value <= p.revision));
    const row = (r: Row, depth = 0): boolean =>
        !!r &&
        typeof r.key === "string" &&
        r.key.length <= 8192 &&
        [
            "canonical_field",
            "canonical_truth",
            "recorded_statement",
            "subjective_belief",
            "recorded_discovery",
            "recorded_observation",
            "recorded_message",
            "derived_comparison",
        ].includes(r.origin) &&
        depth < 3 &&
        (() => {
            switch (r.kind) {
                case "clock":
                    return integer(r.story_time) && source(r.source);
                case "field":
                    return (
                        typeof r.actor === "string" &&
                        typeof r.field === "string" &&
                        !!r.value &&
                        typeof r.value.type === "string" &&
                        source(r.source)
                    );
                case "event":
                    return (
                        !!r.event &&
                        integer(r.event.sequence) &&
                        r.event.sequence <= p.revision &&
                        r.event.scope?.story === p.scope.story &&
                        r.event.scope.branch === p.scope.branch &&
                        Array.isArray(r.event.participants) &&
                        r.event.participants.every(
                            (v) => typeof v === "string",
                        ) &&
                        Array.isArray(r.event.witnesses) &&
                        r.event.witnesses.every((v) => typeof v === "string") &&
                        typeof r.event.turn === "string" &&
                        !!r.event.consequence
                    );
                case "message":
                    return (
                        typeof r.text === "string" &&
                        typeof r.turn === "string" &&
                        Array.isArray(r.event_ids) &&
                        r.event_ids.every(integer) &&
                        q.observer.kind !== "character"
                    );
                case "relationship":
                    return (
                        typeof r.from === "string" &&
                        typeof r.to === "string" &&
                        typeof r.dimension === "string" &&
                        Number.isSafeInteger(r.value) &&
                        source(r.source)
                    );
                case "knowledge":
                    return (
                        typeof r.text === "string" &&
                        typeof r.id === "string" &&
                        Array.isArray(r.sources) &&
                        r.sources.every(source)
                    );
                case "promise":
                    return (
                        typeof r.id === "string" &&
                        typeof r.terms === "string" &&
                        typeof r.from === "string" &&
                        typeof r.to === "string" &&
                        integer(r.deadline) &&
                        typeof r.status === "string" &&
                        Array.isArray(r.sources) &&
                        r.sources.every(source)
                    );
                case "provenance":
                    return Array.isArray(r.sources) && r.sources.every(source);
                case "change":
                    return (
                        (!!r.before || !!r.after) &&
                        integer(r.before_revision) &&
                        integer(r.after_revision) &&
                        (!r.before || row(r.before, depth + 1)) &&
                        (!r.after || row(r.after, depth + 1))
                    );
                default:
                    return false;
            }
        })();
    if (
        !p ||
        p.version !== 1 ||
        p.scope?.story !== q.scope.story ||
        p.scope.branch !== q.scope.branch ||
        p.head !== q.expected_head ||
        p.revision !== (q.at_revision ?? q.expected_head) ||
        p.observer?.kind !== q.observer.kind ||
        (q.observer.kind === "character" &&
            (p.observer as { id?: string }).id !== q.observer.id) ||
        p.view !== q.view ||
        !integer(p.story_time) ||
        !integer(p.total) ||
        p.privacy !==
            (q.observer.kind === "player"
                ? "player_visible"
                : q.observer.kind === "character"
                  ? "private_character"
                  : "private_omniscient") ||
        !["supported", "unsupported"].includes(p.status) ||
        !Array.isArray(p.rows) ||
        p.rows.length > q.limit ||
        p.rows.length > p.total ||
        !p.rows.every((r) => row(r)) ||
        new Set(p.rows.map((r) => r.key)).size !== p.rows.length ||
        !(
            p.next_cursor === null ||
            (typeof p.next_cursor === "string" && p.next_cursor.length <= 128)
        ) ||
        !Array.isArray(p.unsupported) ||
        !p.unsupported.every((s) => typeof s === "string") ||
        new TextEncoder().encode(JSON.stringify(p)).length > 65536
    )
        throw new Error("Wire");
    return p;
}
