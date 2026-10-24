import { useEffect, useState, useSyncExternalStore } from "react";
import type { Action, FakeMode } from "./model";
import type { V2BoundPage, V2PlayController } from "./v2-play-controller";
import type { RowV2, SourceV2, ViewV2 } from "./v2-view-model";

const views: ViewV2[] = [
    "profiles",
    "history",
    "relationships",
    "knowledge",
    "promises",
    "provenance",
    "turn_diff",
    "summaries",
    "retrieval_indexes",
];
const words = (value: string) => value.replaceAll("_", " ");
const scopeLabel = (scope: { story: string; branch: string }) =>
    `${scope.story} / ${scope.branch}`;
function sources(row: RowV2): SourceV2[] {
    if (
        row.kind === "clock" ||
        row.kind === "field" ||
        row.kind === "relationship"
    )
        return [row.source];
    if (
        row.kind === "knowledge" ||
        row.kind === "promise" ||
        row.kind === "provenance"
    )
        return row.sources;
    if (row.kind === "change")
        return [
            ...(row.before ? sources(row.before) : []),
            ...(row.after ? sources(row.after) : []),
        ];
    if (row.kind === "event")
        return [
            {
                kind: "scoped_event",
                value: {
                    original_scope: row.event.scope,
                    sequence: row.event.sequence,
                },
            },
        ];
    return [];
}
function NativeRow({
    row,
    controller,
    bound,
}: {
    row: RowV2;
    controller: V2PlayController;
    bound: V2BoundPage;
}) {
    if (row.kind === "author_correction")
        return (
            <li className="scope" aria-label="Timeline correction">
                Timeline correction · r{row.revision}
            </li>
        );
    return (
        <li
            className="record-detail"
            data-native-kind={row.kind}
            data-native-origin={row.origin}
            style={{ scrollMarginTop: "14rem" }}
        >
            <p className="origin">{words(row.origin)}</p>
            {row.kind === "scoped_message" ? (
                <>
                    <small>
                        {scopeLabel(row.original_scope)} · {row.turn} ·{" "}
                        {words(row.message_kind)} · events{" "}
                        {row.event_ids.join(", ")}
                    </small>
                    <p className="record-value">{row.text}</p>
                </>
            ) : row.kind === "event" ? (
                <>
                    <strong>
                        Event {row.event.sequence} ·{" "}
                        {scopeLabel(row.event.scope)}
                    </strong>
                    <p>
                        Turn {row.event.turn} · story time{" "}
                        {row.event.story_time}
                    </p>
                    <p>
                        Participants: {row.event.participants.join(", ")} ·
                        witnesses: {row.event.witnesses.join(", ")}
                    </p>
                    <pre>{JSON.stringify(row.event.consequence, null, 2)}</pre>
                </>
            ) : row.kind === "knowledge" ? (
                <>
                    <strong>
                        {row.id}
                        {row.subject ? ` · ${row.subject}` : ""}
                    </strong>
                    <p className="record-value">{row.text}</p>
                    {row.confidence && <p>Confidence: {row.confidence}</p>}
                </>
            ) : row.kind === "relationship" ? (
                <p>
                    {row.from} → {row.to} · {row.dimension}: {row.value}
                </p>
            ) : row.kind === "field" ? (
                <p>
                    {row.actor} · {words(row.field)}:{" "}
                    {JSON.stringify(row.value)}
                </p>
            ) : row.kind === "promise" ? (
                <>
                    <strong>
                        {row.from} → {row.to} · {row.status}
                    </strong>
                    <p>{row.terms}</p>
                    <small>Deadline {row.deadline}</small>
                </>
            ) : row.kind === "change" ? (
                <>
                    <strong>
                        Comparison r{row.before_revision} → r
                        {row.after_revision}
                    </strong>
                    <pre>
                        {JSON.stringify(
                            { before: row.before, after: row.after },
                            null,
                            2,
                        )}
                    </pre>
                </>
            ) : row.kind === "clock" ? (
                <p>Story time: {row.story_time}</p>
            ) : (
                <p>Permitted provenance</p>
            )}
            <div className="source-links">
                {sources(row).map((source, index) => (
                    <button
                        key={index}
                        disabled={source.kind === "withheld"}
                        onClick={() => void controller.source(source, bound)}
                    >
                        {source.kind === "scoped_event"
                            ? `${scopeLabel(source.value.original_scope)} · event ${source.value.sequence}`
                            : source.kind === "seed"
                              ? `Seed ${source.value}`
                              : "Evidence withheld by lens"}
                    </button>
                ))}
            </div>
        </li>
    );
}
export interface V2PlayControls {
    action?: (value: Action) => void;
    fakeMode?: (value: FakeMode) => void;
    playMode?: (value: "fixture" | "local") => void;
    inputKind?: (value: "action" | "dialogue") => void;
}
export function V2PlayPanel({
    controller,
    controls,
    openExisting,
}: {
    controller: V2PlayController;
    controls?: V2PlayControls;
    openExisting?: (
        panel: "model" | "debugger" | "exports" | "timeline" | "memory",
    ) => void;
}) {
    const state = useSyncExternalStore(controller.subscribe, controller.get),
        c = state.context;
    const [view, setView] = useState<ViewV2>("knowledge");
    const [search, setSearch] = useState("");
    const [at, setAt] = useState("");
    const identity = c
        ? JSON.stringify([
              c.session,
              c.scope,
              c.revision,
              c.view,
              c.observer,
              c.playMode,
              c.inputKind,
              c.action,
              c.fakeMode,
          ])
        : "none";
    useEffect(() => {
        setSearch("");
        setAt("");
        void controller.refresh(false);
    }, [controller, identity]);
    if (!c)
        return (
            <section aria-label="V2 play unavailable">
                <p>
                    Select a coherent native story/session to read its V2 view.
                </p>
            </section>
        );
    const busy = !!state.pending || !!state.uncertain || c.pending || c.blocked;
    const player = state.snapshot?.player;
    const observer =
        c.view === "play"
            ? "Player"
            : c.observer.kind === "character"
              ? `Character ${c.observer.id}`
              : words(c.observer.kind);
    const inspection = state.inspection;
    return (
        <section
            className="v2-play"
            aria-label="Scoped timeline Play and inspection"
        >
            <header className="scope">
                <h2>
                    {c.view === "play" ? "Play" : "Story Lab"} · scoped timeline
                </h2>
                <p>
                    {scopeLabel(c.scope)} · r{c.revision} · session {c.session}
                </p>
                <p>
                    Inspection lens: {observer}. Gameplay actor: {c.player}.
                </p>
                <p>
                    {c.persistent
                        ? "Local durable workspace"
                        : "In-memory progress · closes without durable save"}{" "}
                    ·{" "}
                    {c.playMode === "fixture"
                        ? "Fixture inference · synthetic responses"
                        : "Local model · availability is checked by Rust"}
                </p>
                <p>
                    Operation:{" "}
                    {state.uncertain
                        ? "outcome unknown"
                        : (state.pending?.stage ??
                          state.status?.phase ??
                          "idle")}
                </p>
                {state.error && <p role="alert">{state.error}</p>}
            </header>
            {state.notice && <p role="status">{state.notice}</p>}
            <button
                disabled={state.readBusy}
                onClick={() => void controller.refresh()}
            >
                {state.readBusy
                    ? "Reading native state…"
                    : "Refresh native state"}
            </button>
            {player ? (
                <section aria-label="Native player resources">
                    <h3>
                        {player.self_state.name} · {player.observer}
                    </h3>
                    <p>
                        Native resource snapshot r{state.snapshot!.revision}
                        {state.readBusy ? " · refreshing" : ""}
                    </p>
                    <p>
                        Location {player.self_state.location} ·{" "}
                        {player.self_state.alive ? "alive" : "not alive"} ·
                        energy {player.self_state.energy}
                    </p>
                    <dl>
                        <dt>Attributes</dt>
                        <dd>{JSON.stringify(player.self_state.attributes)}</dd>
                        <dt>Abilities</dt>
                        <dd>{JSON.stringify(player.self_state.abilities)}</dd>
                        <dt>Injuries</dt>
                        <dd>
                            {player.self_state.injuries.join(", ") ||
                                "None recorded"}
                        </dd>
                        <dt>Affiliations</dt>
                        <dd>
                            {player.self_state.affiliations.join(", ") ||
                                "None recorded"}
                        </dd>
                        <dt>Goals</dt>
                        <dd>
                            {player.self_state.goals.join(", ") ||
                                "None recorded"}
                        </dd>
                    </dl>
                    <h4>Player inventory</h4>
                    <ul>
                        {Object.entries(state.snapshot!.inventory).map(
                            ([id, item]) => (
                                <li key={id}>
                                    {id} · quantity {item.quantity}
                                    {item.return_to
                                        ? ` · return to ${item.return_to}`
                                        : ""}
                                    {item.healing ? " · healing" : ""}
                                </li>
                            ),
                        )}
                    </ul>
                    {Object.keys(state.snapshot!.inventory).length === 0 && (
                        <p>No player-owned items recorded.</p>
                    )}
                </section>
            ) : (
                <p>Current native player resources have not been read.</p>
            )}
            <section aria-label="Accepted scoped history">
                <h3>Accepted history · {observer}</h3>
                {state.history ? (
                    <>
                        <p>
                            r{state.history.page.revision} ·{" "}
                            {words(state.history.page.privacy)} ·{" "}
                            {state.history.page.total} permitted rows; one
                            bounded page
                        </p>
                        <ol>
                            {state.history.page.rows.map((row, index) => (
                                <NativeRow
                                    key={
                                        row.kind === "author_correction"
                                            ? `marker-${row.revision}`
                                            : `${row.key}-${index}`
                                    }
                                    row={row}
                                    controller={controller}
                                    bound={state.history!}
                                />
                            ))}
                        </ol>
                        {state.history.page.rows.length === 0 && (
                            <p>No permitted rows at this boundary.</p>
                        )}
                        <button
                            disabled={
                                !state.history.page.next_cursor ||
                                state.readBusy
                            }
                            onClick={() =>
                                state.history?.page.next_cursor &&
                                void controller.page(
                                    state.history.page.next_cursor,
                                    "history",
                                )
                            }
                        >
                            Next history page
                        </button>
                    </>
                ) : (
                    <p>
                        History unavailable until the native scoped query
                        completes.
                    </p>
                )}
            </section>
            {c.view === "play" ? (
                <form
                    aria-label="Native turn composer"
                    onSubmit={(event) => {
                        event.preventDefault();
                        void controller.send();
                    }}
                >
                    <h3>Continue this timeline</h3>
                    <label>
                        Inference{" "}
                        <select
                            value={c.playMode}
                            disabled={busy || !controls?.playMode}
                            onChange={(event) =>
                                controls?.playMode?.(
                                    event.target.value as "fixture" | "local",
                                )
                            }
                        >
                            <option value="fixture">Fixture · synthetic</option>
                            <option value="local">Local model</option>
                        </select>
                    </label>
                    {c.playMode === "fixture" ? (
                        <>
                            <label>
                                Typed action{" "}
                                <select
                                    value={c.action}
                                    disabled={busy || !controls?.action}
                                    onChange={(event) =>
                                        controls?.action?.(
                                            event.target.value as Action,
                                        )
                                    }
                                >
                                    <option value="wait">Wait</option>
                                    <option value="dialogue">
                                        Speak to Mira
                                    </option>
                                    <option value="give">
                                        Give potion to Mira
                                    </option>
                                    <option value="ability">
                                        Try teleport ability
                                    </option>
                                </select>
                            </label>
                            <label>
                                Fixture response{" "}
                                <select
                                    value={c.fakeMode}
                                    disabled={busy || !controls?.fakeMode}
                                    onChange={(event) =>
                                        controls?.fakeMode?.(
                                            event.target.value as FakeMode,
                                        )
                                    }
                                >
                                    {[
                                        "accepted",
                                        "delayed",
                                        "malformed",
                                        "rejected",
                                        "failed",
                                        "cancelled",
                                    ].map((mode) => (
                                        <option key={mode} value={mode}>
                                            {mode}
                                        </option>
                                    ))}
                                </select>
                            </label>
                        </>
                    ) : (
                        <label>
                            Input kind{" "}
                            <select
                                value={c.inputKind}
                                disabled={busy || !controls?.inputKind}
                                onChange={(event) =>
                                    controls?.inputKind?.(
                                        event.target.value as
                                            "action" | "dialogue",
                                    )
                                }
                            >
                                <option value="action">Action</option>
                                <option value="dialogue">Dialogue</option>
                            </select>
                        </label>
                    )}
                    <label>
                        Draft{" "}
                        <textarea
                            value={state.draft}
                            disabled={busy}
                            onChange={(event) =>
                                controller.setDraft(event.target.value)
                            }
                            placeholder="Your intent or spoken words"
                        />
                    </label>
                    <p>
                        Maximum 2,048 UTF-8 bytes. Rust validates the selected
                        action; chat cannot grant author privileges.
                    </p>
                    <button type="submit" disabled={busy || !state.snapshot}>
                        Send to Rust
                    </button>
                </form>
            ) : (
                <p>
                    Story Lab is read-only. Its observer lens does not change
                    who generation may know or speak as.
                </p>
            )}
            {(state.pending || state.uncertain || state.status) && (
                <section aria-label="Original turn status">
                    <h3>Original turn</h3>
                    {c.view === "lab" && (
                        <p>
                            Player-operation metadata is separate from this
                            read-only inspection lens. No request body or
                            private receipt is shown here.
                        </p>
                    )}
                    {state.pending && (
                        <p role="status">
                            {state.pending.stage} ·{" "}
                            {scopeLabel(state.pending.request.scope)} ·{" "}
                            {state.pending.request.turn} · from r
                            {state.pending.request.expected_revision}
                        </p>
                    )}
                    {state.uncertain && (
                        <p>
                            Unresolved original identity:{" "}
                            {scopeLabel(state.uncertain.request.scope)} ·{" "}
                            {state.uncertain.request.turn} · from r
                            {state.uncertain.request.expected_revision}. No new
                            turn is admitted until resolved.
                        </p>
                    )}
                    {(state.pending || state.uncertain) && (
                        <p>
                            Original route:{" "}
                            {(state.pending ?? state.uncertain)!.request.intent
                                .kind === "free_text"
                                ? "local model request"
                                : `typed fixture · ${(state.pending ?? state.uncertain)!.mode}`}
                            . Current composer controls do not replace this
                            request.
                        </p>
                    )}
                    {state.status && (
                        <p>
                            {state.status.phase} ·{" "}
                            {scopeLabel(state.status.scope)} ·{" "}
                            {state.status.turn}
                        </p>
                    )}
                    <button onClick={() => void controller.status()}>
                        Read original status
                    </button>
                    <button
                        disabled={!state.pending && !state.uncertain}
                        onClick={() => void controller.cancel()}
                    >
                        Request cancel for original turn
                    </button>
                    <button
                        disabled={
                            !!state.pending ||
                            !state.uncertain ||
                            c.view !== "play" ||
                            c.pending ||
                            c.blocked
                        }
                        onClick={() => void controller.retryExact()}
                    >
                        Resume exact original request
                    </button>
                </section>
            )}
            {c.view === "play" && state.receipt && (
                <section aria-label="Actual native receipt">
                    <h3>
                        Actual Rust receipt ·{" "}
                        {scopeLabel(state.receipt.request.scope)}
                    </h3>
                    <p>
                        Turn {state.receipt.request.turn} · r
                        {state.receipt.request.expected_revision} → r
                        {state.receipt.events.at(-1)?.sequence}
                    </p>
                    <p className="record-value">{state.receipt.narration}</p>
                    <details>
                        <summary>
                            Request, proposal, accepted events and provenance
                        </summary>
                        <pre>{JSON.stringify(state.receipt, null, 2)}</pre>
                    </details>
                </section>
            )}
            <section aria-label="Read-only V2 inspector">
                <h3>Inspect · {observer}</h3>
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        void controller.readQuery({
                            view,
                            atRevision: at === "" ? null : Number(at),
                            search,
                        });
                    }}
                >
                    <label>
                        View{" "}
                        <select
                            value={view}
                            onChange={(event) =>
                                setView(event.target.value as ViewV2)
                            }
                        >
                            {views.map((value) => (
                                <option key={value} value={value}>
                                    {words(value)}
                                </option>
                            ))}
                        </select>
                    </label>
                    <label>
                        Completed revision{" "}
                        <input
                            type="number"
                            min={0}
                            max={c.revision}
                            value={at}
                            placeholder="Current head"
                            onChange={(event) => setAt(event.target.value)}
                        />
                    </label>
                    <label>
                        Literal search{" "}
                        <input
                            value={search}
                            onChange={(event) => setSearch(event.target.value)}
                        />
                    </label>
                    <button disabled={state.queryBusy || !state.snapshot}>
                        Read permitted view
                    </button>
                </form>
                {inspection && (
                    <>
                        <p>
                            {scopeLabel(inspection.page.scope)} · selected head
                            r{inspection.page.head} · inspected r
                            {inspection.page.revision} ·{" "}
                            {words(inspection.page.privacy)} ·{" "}
                            {inspection.page.total} permitted rows
                        </p>
                        {inspection.page.status === "unsupported" && (
                            <p role="status">
                                This shared view is unavailable. No generated
                                substitute is shown.
                            </p>
                        )}
                        {inspection.page.unsupported.map((notice, index) => (
                            <p key={index}>{notice}</p>
                        ))}
                        <ol>
                            {inspection.page.rows.map((row, index) => (
                                <NativeRow
                                    key={
                                        row.kind === "author_correction"
                                            ? `marker-${row.revision}`
                                            : `${row.key}-${index}`
                                    }
                                    row={row}
                                    controller={controller}
                                    bound={inspection}
                                />
                            ))}
                        </ol>
                        <button
                            disabled={
                                !inspection.page.next_cursor || state.queryBusy
                            }
                            onClick={() =>
                                inspection.page.next_cursor &&
                                void controller.page(
                                    inspection.page.next_cursor,
                                )
                            }
                        >
                            Next inspection page
                        </button>
                    </>
                )}
                {state.source?.kind === "scoped_event" && (
                    <p>
                        Requested source:{" "}
                        {scopeLabel(state.source.value.original_scope)} · event{" "}
                        {state.source.value.sequence}. Query remains in selected
                        timeline {scopeLabel(c.scope)}.{" "}
                        {state.sourceMatched
                            ? "Original scope and sequence matched an actual returned event."
                            : "No permitted exact match is asserted."}
                    </p>
                )}
            </section>
            <footer>
                <p>
                    Model, turn debugger, exports, timelines and memory
                    maintenance use the existing main-app panels.
                </p>
                {openExisting &&
                    (
                        [
                            "model",
                            "debugger",
                            "exports",
                            "timeline",
                            "memory",
                        ] as const
                    ).map((panel) => (
                        <button key={panel} onClick={() => openExisting(panel)}>
                            Open {panel}
                        </button>
                    ))}
            </footer>
        </section>
    );
}
