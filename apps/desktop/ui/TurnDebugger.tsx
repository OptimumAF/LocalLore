import type { Controller } from "./controller";
import type { State } from "./model";
import { attemptKey, traceStages } from "./trace-model";
const label = (value: string) => value.replaceAll("_", " ");
const duration = (us: number) => `${(us / 1000).toFixed(2)} ms`;
const tokens = (value: { value: number; basis: string } | null) =>
    value ? `${value.value} (${value.basis})` : "Not reported";
const eligibilityReasons = {
    disposed: "This window is closing.",
    hidden: "Open the turn debugger first.",
    not_story_lab: "Open Story Lab and acknowledge spoilers to inspect this metadata.",
    not_omniscient: "Select the omniscient inspection lens. This does not change character knowledge.",
    source_unavailable: "A current native story snapshot is unavailable.",
    fence_unavailable: "The current gameplay context is not ready for a metadata read.",
    gameplay_unresolved: "Resolve the pending or uncertain gameplay operation first.",
    busy: "Wait for the current metadata or control operation, or cancel this pending read locally.",
    trace_unavailable: "Current retained trace metadata is unavailable or collection is disabled.",
    selection_unavailable: "Select a retained original player attempt. Missing attempts are not reconstructed.",
    context_changed: "The selected metadata context changed. Refresh metadata and select an attempt.",
} as const;
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
        receipt = c.debugReceipt(),
        play = s.play ?? s.playV2,
        session = c.selected(),
        eligibility = c.traceNarrationValidationEligibility(),
        diagnostic = t.narrationValidation,
        privateLens = s.view === "lab" && s.observer === "omniscient",
        query = privateLens ? diagnostic.query : null,
        metadataStale = !!reply && (!play || reply.head !== play.revision ||
            reply.scope.story !== play.scope.story || reply.scope.branch !== play.scope.branch ||
            reply.base_revision !== t.baseRevision),
        diagnosticStale = !!query && (!play || !session || query.session !== session.id ||
            query.scope.story !== play.scope.story || query.scope.branch !== play.scope.branch ||
            query.expected_head !== play.revision || !selected ||
            query.base_revision !== t.baseRevision || selected.identity.observer !== play.player.observer ||
            selected.identity.scope.story !== query.scope.story || selected.identity.scope.branch !== query.scope.branch ||
            query.base_revision !== selected.identity.base_revision ||
            query.turn !== selected.identity.turn || query.attempt !== selected.identity.attempt),
        stale = metadataStale || diagnosticStale || t.error === "Stale" || (privateLens && diagnostic.error === "Stale"),
        result = privateLens && !stale && query ? diagnostic.reply : null,
        validation = result?.status === "recorded" ? result.decision : null;
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
                {play?.revision ?? "unavailable"} · captured basis r
                {t.baseRevision}
            </p>
            {stale && (
                <p role="alert">
                    Metadata context is stale. Current head {play ? `r${play.revision}` : "unavailable"}.
                    {query ? ` Requested head r${query.expected_head}.` : ""}{" "}
                    Reconcile gameplay, refresh metadata and select an attempt before reading again.
                </p>
            )}
            <p className="muted">
                This window's Host · capture defaults off · private memory only
                · metadata is separate from explicit private capture/export.
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
                    disabled={!play || t.controlBusy || t.enabled === true}
                    onClick={() => void c.controlTrace("enable")}
                >
                    Enable metadata
                </button>
                <button
                    disabled={!play || t.controlBusy || t.enabled === false}
                    onClick={() => void c.controlTrace("disable")}
                >
                    Disable & delete
                </button>
                <button
                    disabled={!play || t.controlBusy}
                    onClick={() => void c.controlTrace("clear")}
                >
                    Clear window traces
                </button>
                <button
                    disabled={!play || t.busy || t.controlBusy}
                    onClick={() => void c.readTrace()}
                >
                    Refresh metadata
                </button>
                <label>
                    Captured base revision
                    <input
                        type="number"
                        min="0"
                        max={play?.revision}
                        disabled={!play || t.busy || t.controlBusy}
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
            <section className="trace-detail" aria-labelledby="narration-validation-title">
                <h3 id="narration-validation-title">Selected narration validation</h3>
                <div className="trace-controls">
                    <button
                        disabled={!privateLens || !eligibility.allowed}
                        onClick={() => void c.readTraceNarrationValidation()}
                    >
                        Read selected narration validation
                    </button>
                    <button
                        disabled={!privateLens || diagnostic.status !== "pending"}
                        onClick={() => c.cancelTraceNarrationValidation()}
                    >
                        Cancel metadata read locally
                    </button>
                </div>
                {query && (
                    <p className="scope">
                        Story {query.scope.story} · branch {query.scope.branch} · session {query.session}
                        {" · "}current head {play ? `r${play.revision}` : "unavailable"}
                        {" · "}read head r{query.expected_head} · original basis r{query.base_revision}
                        {" · "}turn {query.turn} · attempt {query.attempt}
                        {" · "}original player observer {selected?.identity.observer ?? "unavailable"}
                        {" · "}generation grant false
                    </p>
                )}
                <p role="status">
                    {!privateLens
                        ? "Narration validation metadata is unavailable in this lens. Use acknowledged Story Lab omniscient inspection."
                        : diagnostic.status === "refused"
                          ? `Metadata read refused: ${diagnostic.error ?? "Transport"}. No decision is displayed.`
                        : stale
                          ? "Narration validation is unavailable for the changed context. No old decision is displayed."
                          : diagnostic.status === "pending"
                            ? "Metadata read pending. This does not report model execution or a completed validator."
                            : diagnostic.status === "cancelled"
                              ? "Metadata read cancelled locally. The native read may finish; no gameplay or native cancellation is claimed."
                              : diagnostic.status === "recorded" && validation
                                  ? "Recorded narration validation decision for this exact attempt."
                                  : diagnostic.status === "unavailable" && result?.status === "unavailable"
                                    ? "The Host reports this exact attempt's optional narration validation metadata unavailable. No specific cause is known."
                                    : diagnostic.status === "unavailable"
                                      ? "Narration validation is unavailable in the current local context. No Host cause is inferred."
                                      : "No narration validation read has been requested for this selection."}
                </p>
                {!eligibility.allowed && eligibility.reason && (
                    <p className="muted">{eligibilityReasons[eligibility.reason]}</p>
                )}
                {validation && (
                    <dl className="trace-provenance">
                        <div><dt>Validation outcome</dt><dd>{validation.outcome}</dd></div>
                        <div><dt>Validation error</dt><dd>{validation.error ?? "None"}</dd></div>
                        <div><dt>Retained reason code</dt><dd>{validation.reason ?? "None"}</dd></div>
                    </dl>
                )}
                <p className="muted">
                    This decision is separate from final commit, canonical effects and quality.
                    A rejected narration may commit mechanical fallback; an accepted validation
                    may later cancel. Absence is not reconstructed. Inspection grants no
                    character knowledge or generation access.
                </p>
                {s.playV2 && (
                    <p>Canonical receipt comparison and legacy inspection are unavailable through this metadata debugger for this timeline.</p>
                )}
            </section>
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
                                    linked in this view. A ready
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
                    This metadata API contains no context text, raw proposals,
                    prompts or model output. {s.playV2
                        ? "Private capture and legacy inspection are unavailable through this metadata surface."
                        : "Story Lab omniscient inspection can explicitly opt into separate future-attempt private capture."}
                    Summary maintenance and model hidden reasoning are
                    unavailable.
                </p>
                <p>
                    Private capture and exact export require separate consent.
                    Pause/step and generation rerun are unavailable. Accepted
                    history {s.playV2
                        ? "is not reconstructed by this metadata debugger."
                        : "can be inspected through Memory & evidence without an LLM."}
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
