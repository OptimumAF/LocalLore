import type { Controller } from "./controller";
import type { State } from "./model";
import { attemptKey, traceStages } from "./trace-model";
const label = (value: string) => value.replaceAll("_", " ");
const duration = (us: number) => `${(us / 1000).toFixed(2)} ms`;
const tokens = (value: { value: number; basis: string } | null) =>
    value ? `${value.value} (${value.basis})` : "Not reported";
export function TurnDebugger({
    controller: c,
    state: s,
}: {
    controller: Controller;
    state: State;
}) {
    if (!s.trace.shown) return null;
    const t = s.trace,
        reply = t.reply,
        attempts = reply?.snapshot.attempts ?? [],
        selected = c.traceAttempt(),
        receipt = c.debugReceipt();
    const lens =
        s.view === "play"
            ? "Player"
            : s.observer === "omniscient"
              ? "Story Lab · omniscient"
              : `Story Lab · character ${s.observer}`;
    return (
        <section className="turn-debugger" aria-labelledby="debugger-title">
            <div className="topline">
                <h2 id="debugger-title">Turn debugger</h2>
                <button onClick={() => void c.showTrace(false)}>
                    Close debugger
                </button>
            </div>
            <p>
                Passive metadata · reads never generate, replay or change
                accepted history.
            </p>
            <p>
                <strong>{lens}</strong> · actual head r
                {s.play?.revision ?? "unavailable"} · captured basis r
                {t.baseRevision}
            </p>
            <p className="muted">
                This window's Host · capture defaults off · private memory only
                · nothing written to saves or exports.
            </p>
            <div className="trace-controls" id="trace-controls" tabIndex={-1}>
                <strong>
                    {t.enabled === null
                        ? "Capture status unknown"
                        : t.enabled
                          ? "Metadata capture enabled"
                          : "Metadata capture disabled"}
                </strong>
                <button
                    disabled={!s.play || t.controlBusy || t.enabled === true}
                    onClick={() => void c.controlTrace("enable")}
                >
                    Enable metadata
                </button>
                <button
                    disabled={!s.play || t.controlBusy || t.enabled === false}
                    onClick={() => void c.controlTrace("disable")}
                >
                    Disable & delete
                </button>
                <button
                    disabled={!s.play || t.controlBusy}
                    onClick={() => void c.controlTrace("clear")}
                >
                    Clear window traces
                </button>
                <button
                    disabled={!s.play || t.busy || t.controlBusy}
                    onClick={() => void c.readTrace()}
                >
                    Refresh metadata
                </button>
                <label>
                    Captured base revision
                    <input
                        type="number"
                        min="0"
                        max={s.play?.revision ?? 0}
                        step="1"
                        value={t.baseRevision}
                        onChange={(e) =>
                            void c.traceBasis(e.target.valueAsNumber)
                        }
                    />
                </label>
                {s.view === "lab" && (
                    <label>
                        Trace inspection lens
                        <select
                            value={s.observer}
                            onChange={(e) => c.setObserver(e.target.value)}
                        >
                            <option value="omniscient">
                                Omniscient · original player attempts
                            </option>
                            <option value="player">Player</option>
                            {["mira", "sable", "oren"].map((id) => (
                                <option key={id} value={id}>
                                    {id} · own attempts only
                                </option>
                            ))}
                        </select>
                    </label>
                )}
            </div>
            <p role="status">
                {t.error
                    ? `Metadata unavailable: ${t.error}. Refresh gameplay to reconcile a stale head, then retry.`
                    : t.controlBusy
                      ? "Updating this window's capture settings..."
                      : t.busy
                        ? "Reading scoped metadata..."
                        : reply?.snapshot.status === "disabled"
                          ? "Capture is off. Earlier work cannot be reconstructed as an exact trace."
                          : attempts.length
                            ? "Bounded metadata window; absent stages and evicted attempts are not reconstructed."
                            : "No retained attempts match this session, observer and base revision. This does not prove the turn did not run."}
            </p>
            {reply && attempts.length > 0 && (
                <>
                    <table className="query-table trace-attempts">
                        <caption>
                            Retained attempts · basis r{reply.base_revision} ·
                            current head r{reply.head}
                        </caption>
                        <thead>
                            <tr>
                                <th scope="col">Original turn / observer</th>
                                <th scope="col">Attempt</th>
                                <th scope="col">Outcome</th>
                                <th scope="col">Elapsed</th>
                            </tr>
                        </thead>
                        <tbody>
                            {attempts.map((a) => (
                                <tr key={attemptKey(a)}>
                                    <th scope="row">
                                        <button
                                            aria-pressed={
                                                attemptKey(a) === t.selected
                                            }
                                            onClick={() =>
                                                c.selectTrace(attemptKey(a))
                                            }
                                        >
                                            {a.identity.turn}
                                            <small>
                                                {a.identity.observer} ·{" "}
                                                {a.identity.scope.story} /{" "}
                                                {a.identity.scope.branch}
                                            </small>
                                        </button>
                                    </th>
                                    <td>{a.identity.attempt}</td>
                                    <td>
                                        {label(a.outcome)}
                                        {a.truncated ? " · truncated" : ""}
                                    </td>
                                    <td>{duration(a.elapsed_us)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {selected && (
                        <div className="trace-detail">
                            <h3>Observed stages · {selected.identity.turn}</h3>
                            <p>
                                Attempt {selected.identity.attempt} · original
                                observer {selected.identity.observer} · basis r
                                {selected.identity.base_revision} ·{" "}
                                {label(selected.outcome)}
                                {selected.truncated
                                    ? " · capture truncated"
                                    : ""}
                            </p>
                            <table className="query-table">
                                <caption>
                                    Recorded intervals and counts; zero counts
                                    are displayed as reported
                                </caption>
                                <thead>
                                    <tr>
                                        <th scope="col">Stage</th>
                                        <th scope="col">Outcome / category</th>
                                        <th scope="col">Interval</th>
                                        <th scope="col">Counts</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {selected.stages.map((r, i) => (
                                        <tr key={i}>
                                            <th scope="row">
                                                {label(r.stage)}
                                            </th>
                                            <td>
                                                {label(r.outcome)}
                                                <small>
                                                    {r.error
                                                        ? `Category: ${label(r.error)}`
                                                        : "No recorded error category"}
                                                </small>
                                            </td>
                                            <td>
                                                Start {duration(r.started_us)}
                                                <small>
                                                    Duration{" "}
                                                    {duration(r.duration_us)}
                                                </small>
                                            </td>
                                            <td>
                                                {r.counts.eligible_records}{" "}
                                                eligible · {r.counts.operations}{" "}
                                                operations · {r.counts.repairs}{" "}
                                                repairs
                                                <small>
                                                    Input:{" "}
                                                    {tokens(
                                                        r.counts.input_tokens,
                                                    )}{" "}
                                                    · Output:{" "}
                                                    {tokens(
                                                        r.counts.output_tokens,
                                                    )}
                                                </small>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            <details>
                                <summary>
                                    Stages with no retained capture
                                </summary>
                                <p>
                                    {traceStages
                                        .filter(
                                            (stage) =>
                                                !selected.stages.some(
                                                    (r) => r.stage === stage,
                                                ),
                                        )
                                        .map(label)
                                        .join(", ") ||
                                        "All stage kinds have a retained record."}{" "}
                                    Missing records do not prove why work was
                                    skipped.
                                </p>
                            </details>
                            <details>
                                <summary>Runtime and prompt provenance</summary>
                                <dl className="trace-provenance">
                                    {Object.entries(selected.provenance).map(
                                        ([k, v]) => (
                                            <div key={k}>
                                                <dt>{label(k)}</dt>
                                                <dd>{v ?? "Not captured"}</dd>
                                            </div>
                                        ),
                                    )}
                                </dl>
                            </details>
                            {receipt ? (
                                <div>
                                    <h3>Separate accepted evidence</h3>
                                    <p>
                                        Matching canonical receipt at r
                                        {receipt.events.at(-1)?.sequence}.{" "}
                                        {receipt.events.length} accepted
                                        event(s). Narration is display text,
                                        separate from canonical effects.
                                    </p>
                                    <p>{receipt.narration}</p>
                                    <button
                                        onClick={() =>
                                            void c.traceToInspection()
                                        }
                                    >
                                        Compare accepted turn & provenance
                                    </button>
                                </div>
                            ) : (
                                <p>
                                    No matching permitted canonical receipt is
                                    linked in this Player view. A ready
                                    candidate or trace is not proof of commit.
                                </p>
                            )}
                        </div>
                    )}
                </>
            )}
            <details className="trace-limits" open>
                <summary>Unavailable evidence & retention</summary>
                <p>
                    Selected context records, ranks, omission reasons, raw
                    proposals, prompts, model output and summary maintenance are
                    not captured by this API. Their absence cannot diagnose a
                    retrieval miss, an invented rule violation or stale summary.
                </p>
                <p>
                    Full capture, trace export, pause/step and generation rerun
                    are unavailable. Accepted history can be inspected through
                    Memory & evidence without an LLM.
                </p>
                <p>
                    At most 32 attempts / 24 stages per attempt / 64 KiB per
                    reply. Traces are session-owned in this window's Host;
                    close/restart, disable, clear or eviction can remove them.
                    No exact reconstruction. Character inspection never relabels
                    a player attempt.
                </p>
            </details>
        </section>
    );
}
