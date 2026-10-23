import { useEffect, useState } from "react";
import type { Controller } from "./controller";
import type { State } from "./model";
import { views, words, rowLabel, rowValue, rowSources } from "./query-model";
import type { Row, Source, InspectionView } from "./query-model";
function Sources({ row, c }: { row: Row; c: Controller }) {
    return (
        <span className="source-links">
            {rowSources(row).length
                ? rowSources(row).map((source: Source, i) => (
                      <button
                          key={i}
                          disabled={source.kind === "withheld"}
                          onClick={() => void c.followInspectionSource(source)}
                      >
                          {source.kind === "event"
                              ? `Event ${source.value}`
                              : source.kind === "seed"
                                ? `Seed · ${source.value}`
                                : "Evidence withheld by lens"}
                      </button>
                  ))
                : "No source attached to this derived row"}
        </span>
    );
}
function RecordDetail({ row, c }: { row: Row; c: Controller }) {
    return (
        <section
            className="record-detail"
            aria-label="Selected inspection record"
        >
            <h3>{rowLabel(row)}</h3>
            <p className="origin">{words(row.origin)}</p>
            {row.kind === "change" ? (
                <div className="comparison">
                    <section>
                        <h4>Before · r{row.before_revision}</h4>
                        <p>{row.before ? rowValue(row.before) : "Absent"}</p>
                        {row.before && <Sources row={row.before} c={c} />}
                    </section>
                    <section>
                        <h4>After · r{row.after_revision}</h4>
                        <p>{row.after ? rowValue(row.after) : "Absent"}</p>
                        {row.after && <Sources row={row.after} c={c} />}
                    </section>
                </div>
            ) : (
                <p className="record-value">{rowValue(row)}</p>
            )}
            {row.kind === "event" && (
                <dl>
                    <dt>Turn</dt>
                    <dd>{row.event.turn}</dd>
                    <dt>Story time</dt>
                    <dd>{row.event.story_time}</dd>
                    <dt>Participants</dt>
                    <dd>{row.event.participants.join(", ")}</dd>
                    <dt>Witnesses</dt>
                    <dd>{row.event.witnesses.join(", ")}</dd>
                </dl>
            )}
            {row.kind === "knowledge" && (
                <dl>
                    <dt>Subject</dt>
                    <dd>{row.subject ?? "Not specified"}</dd>
                    <dt>Confidence</dt>
                    <dd>{row.confidence ?? "Not a belief confidence"}</dd>
                </dl>
            )}
            {row.kind === "promise" && (
                <p>
                    Status is a derived comparison at the inspected story time.{" "}
                    {row.return_item ? `Return item: ${row.return_item}.` : ""}
                </p>
            )}
            {row.kind !== "change" && <Sources row={row} c={c} />}
            <details>
                <summary>Exact selected record</summary>
                <pre tabIndex={0}>{JSON.stringify(row, null, 2)}</pre>
            </details>
        </section>
    );
}
export function QueryInspector({
    controller: c,
    state: s,
}: {
    controller: Controller;
    state: State;
}) {
    const q = s.query,
        p = q.page,
        selected = p?.rows.find((row) => row.key === q.selectedKey);
    const [search, setSearch] = useState(q.search),
        [revision, setRevision] = useState(""),
        [customHead, setCustomHead] = useState(
            q.atRevision !== null && q.atRevision > 0,
        );
    useEffect(() => setSearch(q.search), [q.search]);
    useEffect(() => {
        setCustomHead(q.atRevision !== null && q.atRevision > 0);
        setRevision(q.atRevision === null ? "" : String(q.atRevision));
    }, [q.atRevision]);

    return (
        <section
            className="memory-workspace"
            aria-label="Read-only memory inspector"
        >
            <div className="topline">
                <div>
                    <h2>Memory & evidence</h2>
                    <p>
                        Read-only · browsing never changes the player or
                        character knowledge.
                    </p>
                </div>
                <button onClick={() => void c.showQuery(false)}>
                    Return to play
                </button>
            </div>
            <div className="query-context">
                <strong>
                    {s.view === "play"
                        ? "Player-visible inspection"
                        : "Story Lab · private inspection"}
                </strong>
                <span>
                    Story {c.selected()?.scope.story} /{" "}
                    {c.selected()?.scope.branch}
                </span>
                <span>
                    Current head {s.play?.revision ?? "—"} · Inspected{" "}
                    {p?.revision ?? q.atRevision ?? "current"} · Time{" "}
                    {p?.story_time ?? "—"}
                </span>
            </div>
            <div className="query-controls">
                <label>
                    View
                    <select
                        value={q.view}
                        onChange={(e) =>
                            void c.browseInspection({
                                view: e.target.value as InspectionView,
                                search: "",
                            })
                        }
                    >
                        {views.map(([value, name]) => (
                            <option key={value} value={value}>
                                {name}
                            </option>
                        ))}
                    </select>
                </label>
                <label>
                    Inspection lens
                    <select
                        disabled={s.view !== "lab"}
                        value={s.view === "play" ? "player" : s.observer}
                        onChange={(e) => c.setObserver(e.target.value)}
                    >
                        <option value="player">Rowan · player</option>
                        {s.view === "lab" && (
                            <>
                                <option value="mira">
                                    Mira · own knowledge
                                </option>
                                <option value="sable">
                                    Sable · own knowledge
                                </option>
                                <option value="omniscient">
                                    Omniscient · spoilers
                                </option>
                            </>
                        )}
                    </select>
                </label>
                <label>
                    Snapshot
                    <select
                        value={
                            customHead
                                ? "historical"
                                : q.atRevision === null
                                  ? "current"
                                  : q.atRevision === 0
                                    ? "seed"
                                    : "historical"
                        }
                        onChange={(e) => {
                            if (e.target.value !== "historical") {
                                setCustomHead(false);
                                void c.browseInspection({
                                    atRevision:
                                        e.target.value === "current" ? null : 0,
                                });
                            } else {
                                setCustomHead(true);
                                setRevision(String(q.atRevision ?? 0));
                            }
                        }}
                    >
                        <option value="current">Current completed head</option>
                        <option value="seed">Seed · revision 0</option>
                        <option value="historical">
                            Specific completed revision
                        </option>
                    </select>
                </label>
                {customHead && (
                    <form
                        onSubmit={(e) => {
                            e.preventDefault();
                            const n = Number(revision);
                            if (Number.isSafeInteger(n) && n >= 0)
                                void c.browseInspection({ atRevision: n });
                        }}
                    >
                        <label>
                            Completed revision
                            <input
                                type="number"
                                min="0"
                                max={s.play?.revision ?? 0}
                                value={revision}
                                onChange={(e) => setRevision(e.target.value)}
                                placeholder="e.g. 1"
                            />
                        </label>
                        <button disabled={!revision}>Inspect revision</button>
                    </form>
                )}
            </div>
            <form
                className="query-search"
                onSubmit={(e) => {
                    e.preventDefault();
                    void c.browseInspection({ search });
                }}
            >
                <label>
                    Search permitted records
                    <input
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        maxLength={256}
                        placeholder="Literal text or ID"
                    />
                </label>
                <button>Search</button>
                <button
                    type="button"
                    onClick={() => {
                        setSearch("");
                        void c.browseInspection({ search: "" });
                    }}
                >
                    Clear
                </button>
                <label>
                    Rows per page
                    <select
                        value={q.limit}
                        onChange={(e) =>
                            void c.browseInspection({
                                limit: Number(e.target.value),
                            })
                        }
                    >
                        <option>6</option>
                        <option>12</option>
                        <option>32</option>
                        <option>64</option>
                    </select>
                </label>
            </form>
            <p className="query-status" role="status" aria-live="polite">
                {q.busy
                    ? "Reading one scoped snapshot…"
                    : q.error
                      ? `${q.error}. ${q.notice}`
                      : p
                        ? `${p.total} matching permitted records · ${words(p.privacy)} · ${q.search ? `search: ${q.search}` : "no search filter"}`
                        : "No inspection snapshot."}
            </p>
            {q.error && (
                <button onClick={() => void c.refresh()}>
                    Refresh current head & retry
                </button>
            )}
            {p?.unsupported.length ? (
                <details
                    className="unsupported"
                    open={p.status === "unsupported"}
                >
                    <summary>
                        {p.status === "unsupported"
                            ? "This view is not implemented"
                            : "View limits & missing fields"}
                    </summary>
                    <ul>
                        {p.unsupported.map((text) => (
                            <li key={text}>{text}</li>
                        ))}
                    </ul>
                </details>
            ) : null}
            {p && p.status === "supported" && (
                <>
                    <div className="query-table-wrap">
                        <table className="query-table">
                            <caption>
                                {views.find(([v]) => v === q.view)?.[1]} ·
                                inspected revision {p.revision}
                            </caption>
                            <thead>
                                <tr>
                                    <th scope="col">Record</th>
                                    <th scope="col">Value or consequence</th>
                                    <th scope="col">Meaning & evidence</th>
                                </tr>
                            </thead>
                            <tbody>
                                {p.rows.map((row) => (
                                    <tr
                                        key={row.key}
                                        aria-selected={
                                            row.key === q.selectedKey
                                        }
                                    >
                                        <th scope="row">
                                            <button
                                                onClick={() =>
                                                    c.selectInspection(row.key)
                                                }
                                            >
                                                {rowLabel(row)}
                                            </button>
                                        </th>
                                        <td>{rowValue(row)}</td>
                                        <td>
                                            <span className="origin">
                                                {words(row.origin)}
                                            </span>
                                            <Sources row={row} c={c} />
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {!p.rows.length && (
                        <p>
                            No matching records are permitted in this lens and
                            snapshot.
                        </p>
                    )}
                    <nav className="query-pages" aria-label="Inspection pages">
                        <button
                            disabled={q.busy || !q.cursors.length}
                            onClick={() => void c.previousInspection()}
                        >
                            Previous records
                        </button>
                        <span>Page {q.cursors.length + 1}</span>
                        <button
                            disabled={q.busy || !p.next_cursor}
                            onClick={() => void c.nextInspection()}
                        >
                            Next records
                        </button>
                    </nav>
                </>
            )}
            {selected && (
                <>
                    <div className="record-tools">
                        <button
                            onClick={() =>
                                void c.copyInspection((text) =>
                                    navigator.clipboard.writeText(text),
                                )
                            }
                        >
                            Copy selected record
                        </button>
                        <button onClick={() => void c.whyInspection(selected)}>
                            Why is this true?
                        </button>
                        {selected.kind === "event" && (
                            <button
                                onClick={() =>
                                    void c.inspectEventTurn(selected.event.turn)
                                }
                            >
                                Compare completed turn
                            </button>
                        )}
                    </div>
                    <RecordDetail row={selected} c={c} />
                </>
            )}
            {q.notice && !q.error && <p role="status">{q.notice}</p>}
            <p className="muted">
                Sources refer to accepted events or the original seed. A
                recorded statement or belief is not established truth.
                Summaries, semantic retrieval and alternate-branch history
                remain unavailable.
            </p>
        </section>
    );
}
