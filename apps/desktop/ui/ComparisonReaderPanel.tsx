import { useCallback, useState, useSyncExternalStore } from "react";
import type { ComparisonReaderController } from "./comparison-reader-controller";
import type { ObserverV2, ViewV2 } from "./v2-view-model";

const display = (value: unknown) =>
    value === null || value === undefined
        ? "Unavailable"
        : typeof value === "string"
          ? value
          : JSON.stringify(value, null, 2);
const same = (
    a: { turn: string; arm: string },
    b: { turn: string; arm: string } | null,
) => !!b && a.turn === b.turn && a.arm === b.arm;
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

export function ComparisonReaderPanel({
    controller: c,
}: {
    controller: ComparisonReaderController;
}) {
    const subscribe = useCallback(
        (listener: () => void) => c.subscribe(listener),
        [c],
    );
    const get = useCallback(() => c.get(), [c]);
    const s = useSyncExternalStore(subscribe, get, get);
    const [edge, setEdge] = useState<"before" | "after">("after");
    const [view, setView] = useState<ViewV2>("knowledge");
    if (!s.allowed) return null;
    const selected = s.source?.rows.find((row) => same(row.row, s.selected));
    const turn = s.summary?.report.turns.find((row) => same(row, s.selected));
    const omni = s.observer.kind === "omniscient";
    const lens =
        s.observer.kind === "character" ? s.observer.id : s.observer.kind;
    const inspect = (kind: "query" | "receipt" | "capture" | "outputs") => {
        if (kind === "query")
            void c.inspect({ kind, edge, observer: s.observer, view });
        else void c.inspect({ kind, observer: s.observer });
    };
    return (
        <section
            id="comparison-reader"
            className="comparison-reader"
            aria-labelledby="comparison-reader-title"
            data-phase={s.status?.phase ?? "idle"}
            data-observer={lens}
            data-turn={s.selected?.turn ?? ""}
            data-arm={s.selected?.arm ?? ""}
        >
            <div className="topline">
                <h2 id="comparison-reader-title">Memory comparison reports</h2>
                <button
                    disabled={s.busy || !!s.clientId}
                    onClick={() => void c.pick()}
                >
                    Choose comparison report folder
                </button>
            </div>
            <p>
                Inspect an existing local experiment. The app's folder picker
                asks for permission to reveal private inputs, character truth,
                prompts and outputs. This reader never modifies or resumes a
                story.
            </p>
            <p>
                Reader progress and handles are in memory. After restarting the
                app, choose the report again.
            </p>
            <p className="comparison-unavailable">
                Selected-case rerun unavailable — shared runner prerequisite
                pending. Comparison execution unavailable in this reader.
            </p>
            <div className="comparison-controls">
                <button
                    disabled={!s.clientId || (s.busy && !s.uncertain)}
                    onClick={() => void c.recover()}
                >
                    Check opening status
                </button>
                <button disabled={!s.clientId} onClick={() => void c.close()}>
                    Close report / stop opening
                </button>
                <span role="status">
                    {s.busy && !s.status?.running
                        ? "Waiting for report data"
                        : (s.status?.phase ?? "No report open")}
                    {s.status?.running ? " · work pending" : ""}
                    {s.uncertain
                        ? " · acknowledgement unavailable; check the same opening request"
                        : ""}
                </span>
            </div>
            {s.status?.phase === "closing" && (
                <p>
                    Closing was requested. A pending folder picker or disk read
                    may finish before its handles are released; no late result
                    will be displayed.
                </p>
            )}
            {s.error && (
                <p role="alert" className="error">
                    Comparison: {s.error}
                </p>
            )}
            {s.source && (
                <>
                    <p>
                        Read-only, last fully validated snapshot. Selected
                        evidence is checked again when requested. This is not a
                        live health check of every experiment file.
                    </p>
                    <details>
                        <summary>Source binding and lifetime</summary>
                        <p className="hash-value">{s.source.binding}</p>
                        <p>
                            Opening holds the experiment's cooperative run lock.
                            Close this report before running it elsewhere. Idle
                            expiry is checked on access after 15 minutes; an
                            untouched open window can keep the lock until
                            access, close or window shutdown.
                        </p>
                    </details>
                    <label>
                        Inspection lens{" "}
                        <select
                            aria-label="Comparison observer"
                            value={lens}
                            disabled={s.busy}
                            onChange={(event) => {
                                const value = event.target.value;
                                const observer: ObserverV2 =
                                    value === "omniscient" || value === "player"
                                        ? { kind: value }
                                        : { kind: "character", id: value };
                                c.setObserver(observer);
                            }}
                        >
                            <option value="omniscient">
                                Omniscient · spoilers
                            </option>
                            <option value="player">Player-visible</option>
                            <option value="mira">
                                Mira · private character
                            </option>
                            <option value="sable">
                                Sable · private character
                            </option>
                        </select>
                    </label>
                    {!omni && (
                        <p>
                            Full report, receipt, captures and model outputs are
                            hidden in this lens. The state query below is
                            filtered by the engine for this observer. Inspection
                            does not change anyone's knowledge or generation
                            context.
                        </p>
                    )}
                    {omni && !s.summary && (
                        <button
                            disabled={s.busy}
                            onClick={() => void c.loadSummary()}
                        >
                            Show private report
                        </button>
                    )}
                    {s.summary && (
                        <>
                            <p>
                                <strong>
                                    {s.summary.report.kind ===
                                    "paired_snapshots"
                                        ? "Paired snapshots"
                                        : "Continuous rollout"}
                                </strong>{" "}
                                · {s.summary.report.lane} ·{" "}
                                {s.summary.report.completed
                                    ? "Completed"
                                    : "Partial"}{" "}
                                · {s.summary.report.completed_scenes} completed
                                scenes
                            </p>
                            <p>
                                {s.summary.report.source_matches
                                    ? "Source fingerprint matches this build."
                                    : "Historical source fingerprint: does not match this build; read-only inspection remains available."}{" "}
                                Source match does not enable execution.
                            </p>
                            <p>
                                {s.summary.report.lane.includes("scripted")
                                    ? "Synthetic scripted inference: plumbing and hard-invariant checks; no real model or prose-quality result."
                                    : "Recorded native-model experiment: inspect its actual profile and limitations; this reader runs no inference."}
                            </p>
                            <details>
                                <summary>
                                    Experiment profile, measurements and
                                    limitations
                                </summary>
                                <pre>{display(s.summary.report.profile)}</pre>
                                <dl>
                                    <dt>Left charged time</dt>
                                    <dd>
                                        {s.summary.report.left_charged_ms} ms
                                    </dd>
                                    <dt>Right charged time</dt>
                                    <dd>
                                        {s.summary.report.right_charged_ms} ms
                                    </dd>
                                    <dt>Physical setups</dt>
                                    <dd>{s.summary.report.physical_setups}</dd>
                                    <dt>Setup time</dt>
                                    <dd>
                                        {display(
                                            s.summary.report.physical_setup_ms,
                                        )}
                                        {s.summary.report.physical_setup_ms ===
                                        null
                                            ? ""
                                            : " ms"}
                                    </dd>
                                    <dt>Human review</dt>
                                    <dd>
                                        {s.summary.report.human_reviewed} ·{" "}
                                        {s.summary.report.human_rubric}
                                    </dd>
                                </dl>
                                <ul>
                                    {s.summary.report.limitations.map(
                                        (item, index) => (
                                            <li key={index}>{item}</li>
                                        ),
                                    )}
                                    {s.summary.report.unavailable.map(
                                        (item, index) => (
                                            <li key={`unavailable-${index}`}>
                                                Unavailable: {item}
                                            </li>
                                        ),
                                    )}
                                </ul>
                            </details>
                        </>
                    )}
                    <div
                        className="comparison-table"
                        tabIndex={0}
                        aria-label="Comparison turns"
                    >
                        <table>
                            <thead>
                                <tr>
                                    <th>Turn</th>
                                    <th>Arm</th>
                                    <th>Revision</th>
                                    {omni && (
                                        <>
                                            <th>Result</th>
                                            <th>Roles</th>
                                        </>
                                    )}
                                    <th>Inspect</th>
                                </tr>
                            </thead>
                            <tbody>
                                {s.source.rows.map((row) => {
                                    const report = s.summary?.report.turns.find(
                                        (item) => same(item, row.row),
                                    );
                                    return (
                                        <tr
                                            key={`${row.row.turn}:${row.row.arm}`}
                                            aria-selected={same(
                                                row.row,
                                                s.selected,
                                            )}
                                        >
                                            <td>{row.row.turn}</td>
                                            <td>{row.row.arm}</td>
                                            <td>
                                                {row.source.before_head} →{" "}
                                                {row.source.after_head}
                                            </td>
                                            {omni && (
                                                <>
                                                    <td>
                                                        {report
                                                            ? report.passed
                                                                ? "Passed"
                                                                : "Failed"
                                                            : "Private report hidden"}
                                                    </td>
                                                    <td>
                                                        {report
                                                            ? report.roles_known
                                                                ? report.roles
                                                                : "Unknown"
                                                            : "Unavailable"}
                                                    </td>
                                                </>
                                            )}
                                            <td>
                                                <button
                                                    disabled={s.busy}
                                                    onClick={() =>
                                                        c.select(row.row)
                                                    }
                                                    aria-label={`Inspect ${row.row.arm} ${row.row.turn}`}
                                                >
                                                    {same(row.row, s.selected)
                                                        ? "Selected"
                                                        : "Inspect turn"}
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                    {selected && (
                        <div
                            className="comparison-selected"
                            aria-label="Selected comparison turn"
                        >
                            <h3>
                                {selected.row.turn} · {selected.row.arm}
                            </h3>
                            <p>
                                Source story {selected.source.scope.story} ·
                                branch {selected.source.scope.branch} · before{" "}
                                {selected.source.before_head} → after{" "}
                                {selected.source.after_head} · observer {lens}
                            </p>
                            {turn && (
                                <>
                                    <dl>
                                        <dt>Expected</dt>
                                        <dd>{turn.expected}</dd>
                                        <dt>Actual phase</dt>
                                        <dd>{turn.phase}</dd>
                                        <dt>Error</dt>
                                        <dd>{display(turn.error)}</dd>
                                        <dt>Policy</dt>
                                        <dd>{turn.policy}</dd>
                                        <dt>Role calls</dt>
                                        <dd>
                                            {turn.roles_known
                                                ? turn.roles
                                                : "Unknown; recovered without a complete recording"}
                                        </dd>
                                        <dt>Elapsed</dt>
                                        <dd>{turn.elapsed_ms} ms</dd>
                                        <dt>First final response</dt>
                                        <dd>
                                            {display(
                                                turn.first_final_response_ms,
                                            )}
                                            {turn.first_final_response_ms ===
                                            null
                                                ? ""
                                                : " ms"}
                                        </dd>
                                        <dt>Estimated context tokens</dt>
                                        <dd>
                                            {display(
                                                turn.estimated_context_tokens,
                                            )}{" "}
                                            · estimate, not a measured token
                                            count
                                        </dd>
                                    </dl>
                                    {turn.failures.length > 0 && (
                                        <ul>
                                            {turn.failures.map(
                                                (value, index) => (
                                                    <li key={index}>{value}</li>
                                                ),
                                            )}
                                        </ul>
                                    )}
                                    {turn.quality_flags.length > 0 && (
                                        <ul>
                                            {turn.quality_flags.map(
                                                (value, index) => (
                                                    <li key={index}>
                                                        Quality flag: {value}
                                                    </li>
                                                ),
                                            )}
                                        </ul>
                                    )}
                                </>
                            )}
                            <div className="comparison-controls">
                                <label>
                                    State edge{" "}
                                    <select
                                        value={edge}
                                        disabled={s.busy}
                                        onChange={(event) => {
                                            if (c.get().busy) return;
                                            c.clearEvidence();
                                            setEdge(
                                                event.target.value as
                                                    "before" | "after",
                                            );
                                        }}
                                    >
                                        <option value="before">
                                            Before turn
                                        </option>
                                        <option value="after">
                                            After turn
                                        </option>
                                    </select>
                                </label>
                                <label>
                                    State view{" "}
                                    <select
                                        value={view}
                                        disabled={s.busy}
                                        onChange={(event) => {
                                            if (c.get().busy) return;
                                            c.clearEvidence();
                                            setView(
                                                event.target.value as ViewV2,
                                            );
                                        }}
                                    >
                                        {views.map((value) => (
                                            <option key={value} value={value}>
                                                {value.replaceAll("_", " ")}
                                            </option>
                                        ))}
                                    </select>
                                </label>
                                <button
                                    disabled={s.busy}
                                    onClick={() => inspect("query")}
                                >
                                    Inspect filtered state
                                </button>
                            </div>
                            {omni && (
                                <div className="comparison-controls">
                                    <button
                                        disabled={s.busy}
                                        onClick={() => inspect("receipt")}
                                    >
                                        Inspect accepted receipt
                                    </button>
                                    <button
                                        disabled={s.busy}
                                        onClick={() => inspect("capture")}
                                    >
                                        Inspect actual context capture
                                    </button>
                                    <button
                                        disabled={s.busy}
                                        onClick={() => inspect("outputs")}
                                    >
                                        Inspect recorded role outputs
                                    </button>
                                </div>
                            )}
                            {s.evidence && (
                                <div
                                    className="comparison-evidence"
                                    aria-live="polite"
                                >
                                    <h4>
                                        Displayed evidence ·{" "}
                                        {s.evidence.body.kind}
                                    </h4>
                                    <p>
                                        {s.evidence.row.turn} ·{" "}
                                        {s.evidence.row.arm} ·{" "}
                                        {s.evidence.edge ?? "recorded artifact"}{" "}
                                        · Observer {s.evidence.observer.kind}
                                    </p>
                                    {s.evidence.body.kind === "missing" ? (
                                        <p>
                                            Unavailable:{" "}
                                            {s.evidence.body.reason}
                                        </p>
                                    ) : (
                                        <pre>{display(s.evidence.body)}</pre>
                                    )}
                                    {s.evidence.body.kind === "query" &&
                                        s.evidence.body.page.next_cursor !==
                                            null && (
                                            <p>
                                                More rows exist; paging is
                                                unavailable in this reader.
                                            </p>
                                        )}
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}
        </section>
    );
}
