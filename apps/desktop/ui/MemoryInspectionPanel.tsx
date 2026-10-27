import { useSyncExternalStore } from "react";
import type { MemoryInspectionController } from "./memory-inspection-controller";
import type { MemoryInspectionContext } from "./memory-inspection-model";

const words = (value: string) => value.replaceAll("_", " ");
const inert = {
    whiteSpace: "pre-wrap" as const,
    overflowWrap: "anywhere" as const,
    maxWidth: "100%",
};
export function MemoryInspectionPanel({
    inspection: c,
    context,
}: {
    inspection: MemoryInspectionController;
    context: MemoryInspectionContext | null;
}) {
    const state = useSyncExternalStore(c.subscribe, c.get, c.get);
    if (!context || !c.matchesContext(context)) return null;
    const coverage = state.packets?.coverage,
        selected = state.selected;
    return (
        <section
            aria-labelledby="memory-inspection-title"
            style={{ minWidth: 0, overflowWrap: "anywhere" }}
        >
            <h2 id="memory-inspection-title">Verified memory packets</h2>
            <p>
                Read extractive observations derived from accepted history. This
                does not change events, what characters know, or a memory job.
            </p>
            <dl>
                <dt>Selected story / timeline</dt>
                <dd>
                    <code>
                        {context.scope.story} / {context.scope.branch}
                    </code>
                </dd>
                <dt>Accepted head</dt>
                <dd>{context.expected_head}</dd>
                <dt>Native player / current observer</dt>
                <dd>
                    {context.player} / {context.observer}
                </dd>
                <dt>Read</dt>
                <dd>
                    {state.busy
                        ? "Waiting for acknowledgement"
                        : state.packets
                          ? "Snapshot read"
                          : "Not read"}
                </dd>
            </dl>
            {!state.allowed && (
                <p role="status">
                    {context.domainVersion === 2
                        ? "Domain 2 memory packet inspection is unavailable."
                        : "Open a saved Domain 1 story in Story Lab with the player lens to read these packets."}
                </p>
            )}
            <button disabled={!c.canRead()} onClick={() => void c.refresh()}>
                Read packets / refresh
            </button>
            {state.notice && <p role="status">{state.notice}</p>}
            {state.error && (
                <p role="alert">
                    Memory read: {state.error}. Read packets again for a fresh
                    snapshot.
                </p>
            )}
            {coverage?.status === "raw_fallback" && (
                <p role="status">
                    No verified packets available: {words(coverage.fallback!)}.
                    No rejected cache content is shown; this read did not
                    prepare or repair it.
                </p>
            )}
            {coverage?.status === "verified" && (
                <>
                    <p>
                        Verified against accepted head {coverage.verified_head}.
                        Packet coverage through revision{" "}
                        {coverage.covered_through}.
                    </p>
                    {coverage.covered_through! < context.expected_head && (
                        <p role="status">
                            Verified prefix only. Exact raw observations after{" "}
                            {coverage.raw_delta_after} through{" "}
                            {context.expected_head} are not included in these
                            packets.
                        </p>
                    )}
                    <ol aria-label="Verified packet descriptors">
                        {state.packets!.rows.map((packet) => (
                            <li key={packet.index}>
                                <h3>Packet {packet.index + 1}</h3>
                                <p>
                                    Version {packet.version} · {packet.method} ·
                                    revisions ({packet.from_exclusive},{" "}
                                    {packet.through_revision}] ·{" "}
                                    {packet.receipt_count} receipts ·{" "}
                                    {packet.entry_count} entries ·{" "}
                                    {packet.source_event_count} source events
                                </p>
                                <p>
                                    Closure: {words(packet.closure.kind)}
                                    {"next_turn_end" in packet.closure
                                        ? ` · next complete turn ${packet.closure.next_turn_end}`
                                        : ""}
                                </p>
                                <button
                                    disabled={!c.canRead()}
                                    onClick={() =>
                                        void c.selectPacket(packet.index)
                                    }
                                >
                                    Read packet {packet.index + 1} entries
                                </button>
                            </li>
                        ))}
                    </ol>
                    <button
                        disabled={!c.canRead() || !state.packets?.next_cursor}
                        onClick={() =>
                            state.packets?.next_cursor &&
                            void c.packetPage(state.packets.next_cursor)
                        }
                    >
                        Next packet page
                    </button>
                </>
            )}
            {selected && (
                <p>
                    Selected packet {selected.index + 1} · revisions (
                    {selected.from_exclusive}, {selected.through_revision}].
                    Selection remains bound to this snapshot.
                </p>
            )}
            {state.entries && (
                <div aria-label="Extractive packet entries">
                    <h3>Packet entries</h3>
                    {state.entries.total === 0 && (
                        <p>No eligible entries in this packet.</p>
                    )}
                    <ol>
                        {state.entries.rows.map((row) => {
                            const value = row.value,
                                refs =
                                    value.class === "observation"
                                        ? [value.source]
                                        : value.source_events;
                            return (
                                <li key={`${row.packet_index}-${row.index}`}>
                                    <h4>
                                        {value.class === "observation"
                                            ? words(value.origin)
                                            : "Observed time span"}
                                    </h4>
                                    <pre style={inert}>
                                        {JSON.stringify(value, null, 2)}
                                    </pre>
                                    <ul>
                                        {refs.map((ref) => (
                                            <li
                                                key={`${ref.scope.story}/${ref.scope.branch}/${ref.sequence}`}
                                            >
                                                <button
                                                    disabled={!c.canRead()}
                                                    onClick={() =>
                                                        void c.source(ref)
                                                    }
                                                >
                                                    Read source{" "}
                                                    {ref.scope.story} /{" "}
                                                    {ref.scope.branch} · event{" "}
                                                    {ref.sequence}
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                </li>
                            );
                        })}
                    </ol>
                    <button
                        disabled={!c.canRead() || !state.entries.next_cursor}
                        onClick={() =>
                            state.entries?.next_cursor &&
                            void c.entryPage(state.entries.next_cursor)
                        }
                    >
                        Next entry page
                    </button>
                </div>
            )}
            {state.source && (
                <div aria-label="Actual shared history source">
                    <h3>Original scope and event</h3>
                    <p>
                        {state.source.source.scope.story} /{" "}
                        {state.source.source.scope.branch} · event{" "}
                        {state.source.source.sequence}. Exact scope and sequence
                        matched an actual returned event.
                    </p>
                    <p>
                        Selected head {state.source.head}; inspected completed
                        revision {state.source.page.revision}. Observer: Player
                        ({state.source.observer}).
                    </p>
                    <ol>
                        {state.source.page.rows.map((row, index) => (
                            <li key={`${row.kind}-${index}`}>
                                <pre style={inert}>
                                    {JSON.stringify(row, null, 2)}
                                </pre>
                            </li>
                        ))}
                    </ol>
                    {state.source.page.next_cursor && (
                        <p>
                            More eligible matching rows exist. This source read
                            shows the first bounded page.
                        </p>
                    )}
                </div>
            )}
            <p>
                Job status is separate and is not inferred from these packets.
                No automatic reads, generated summaries or retries.
            </p>
        </section>
    );
}
