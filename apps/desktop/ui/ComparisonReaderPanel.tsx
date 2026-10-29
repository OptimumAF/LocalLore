import { useCallback, useSyncExternalStore } from "react";
import type { ComparisonReaderController } from "./comparison-reader-controller";
import type {
    ComparisonTurnV3,
    ComparisonTurnV4,
    ReaderNarrationDiagnosticV1,
    RowAvailability,
} from "./comparison-reader-model";
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

function NarrationDiagnosticDetails({ result, source, phase, caseError, fallback, receiptAvailable }: {
    result: ReaderNarrationDiagnosticV1["diagnostic"];
    source: RowAvailability["source"];
    phase: string | null;
    caseError: string | null | undefined;
    fallback: boolean | null;
    receiptAvailable: boolean;
}) {
    const labels = {
        no_declaration: "No declaration · legacy absence",
        no_observation: "No saved observation",
        recorded: "Validation decision recorded",
        host_unavailable: "Host unavailable",
        host_rejected: "Stored Host rejection",
    };
    const observation = "observation" in result ? result.observation : null;
    const reply = observation?.host_reply;
    const decision = reply?.status === "ok" && reply.data.status === "recorded"
        ? reply.data.decision : null;
    const reason = decision?.reason === "scene_first_person" ? "First-person claim"
        : decision?.reason === "scene_unapproved_movement" ? "Unapproved movement"
        : decision?.reason === "unclassified" ? "Unclassified by the validator"
        : "No rejection reason";
    return (
        <div className="comparison-evidence comparison-narration-diagnostic"
            data-diagnostic-status={result.status} aria-live="polite">
            <h4>Narration diagnostic · {labels[result.status]}</h4>
            <p>{result.row.turn} · {result.row.arm} · observer omniscient</p>
            <p>Source story {source.scope.story} · branch {source.scope.branch} · Before {source.before_head} · After {source.after_head}</p>
            <p>Selected case phase: {phase ?? "Unavailable — inspect the report"} · Case error: {caseError === undefined ? "Unavailable — inspect the report" : caseError ?? "None"}</p>
            <p>Accepted receipt: {receiptAvailable ? "available" : "unavailable"} · Quality: not established by this metadata.</p>
            <p>{fallback === true ? "Mechanical fallback recorded." : fallback === false ? "No mechanical fallback recorded." : "Fallback status unavailable — inspect the report."}</p>
            {result.status === "no_declaration" && (
                <p>This run has no diagnostic declaration. Older reports cannot supply missing validation causes.</p>
            )}
            {result.status === "no_observation" && (
                <p>No bound observation was saved for this turn. This does not establish whether validation ran.</p>
            )}
            {result.status === "host_unavailable" && (
                <p>The stored Host reply reports unavailable evidence for this attempt. It supplies no validation decision.</p>
            )}
            {result.status === "host_rejected" && (
                <p>The stored reply records rejection of the earlier Host diagnostic read. The current metadata read succeeded; this is separate from rejection of narration.</p>
            )}
            {observation && (
                <dl>
                    <dt>Validation base revision</dt><dd>{observation.host_query.command.base_revision}</dd>
                    <dt>Actual attempt</dt><dd>{observation.host_query.command.attempt}</dd>
                    {decision && <>
                        <dt>Validation outcome</dt><dd>{decision.outcome}</dd>
                        <dt>Validation error</dt><dd>{decision.error?.replaceAll("_", " ") ?? "None"}</dd>
                        <dt>Validation reason</dt><dd>{reason}</dd>
                    </>}
                    {reply?.status === "rejected" && <>
                        <dt>Host read error</dt><dd>{reply.error}</dd>
                    </>}
                </dl>
            )}
            <p>This metadata does not establish a final commit or prose quality. A rejected narration may have a mechanical fallback; a recorded decision may precede cancellation. The selected row's phase and receipt remain separate.</p>
            <details>
                <summary>Inspect bound diagnostic metadata</summary>
                <pre>{display(result)}</pre>
            </details>
        </div>
    );
}

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
    const { edge, view } = s.querySelection;
    if (!s.allowed) return null;
    const selected = s.source?.rows.find((row) => same(row.row, s.selected));
    const turn = s.summary?.report.turns.find((row) => same(row, s.selected));
    const constructionTurn =
        s.summary?.report.version === 3 && turn
            ? (turn as ComparisonTurnV3)
            : null;
    const sceneTurn =
        s.summary?.report.version === 4 && turn
            ? (turn as ComparisonTurnV4)
            : null;
    const literal = sceneTurn
        ? sceneTurn.construction.arm === "literal_scene_v1"
        : constructionTurn?.construction.arm === "literal_player_v1";
    const evidenceStatus =
        sceneTurn?.construction_evidence_status ??
        constructionTurn?.construction_evidence_status;
    const noGeneration =
        evidenceStatus === "not_applicable_guard" ||
        evidenceStatus === "not_applicable_dependency";
    const constructionEvidence =
        evidenceStatus === "validated_committed_scene_narrator_v1"
            ? "Committed narrator input checked"
            : evidenceStatus === "validated_literal"
              ? "Validated literal input"
              : evidenceStatus === "validated_relevant"
                ? "Validated relevant-memory input"
                : evidenceStatus === "not_applicable_guard"
                  ? "Not applicable — guard"
                  : evidenceStatus === "not_applicable_dependency"
                    ? "Not applicable — dependency"
                    : "Unavailable — no validated input";
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
                {s.source?.protocol_version === 4
                    ? "Protocol 4 selected-case rerun unavailable. This reader only inspects recorded scene experiments."
                    : s.source?.protocol_version === 3
                      ? "Read-only Protocol 3 report. Selected experiments use their separate controls."
                      : "Comparison execution unavailable in this reader. Selected experiments use their separate controls."}
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
                            <header
                                className="comparison-report-context"
                                aria-label="Report context"
                            >
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
                                    · {s.summary.report.completed_scenes}{" "}
                                    completed scenes
                                </p>
                                <p>
                                    Read-only cached report · Protocol{" "}
                                    {s.summary.report.version} · observer {lens}
                                </p>
                            </header>
                            {s.summary.report.version !== 2 && (
                                <>
                                    <p>
                                        {s.summary.report.version === 4
                                            ? "Left: Literal scene · Right: Relevant memory scene."
                                            : "Left: Literal player conversation · Right: Relevant memory."}
                                    </p>
                                    <details>
                                        <summary>
                                            Construction contracts
                                        </summary>
                                        <pre>
                                            {display(s.summary.report.arms)}
                                        </pre>
                                    </details>
                                </>
                            )}
                            {s.summary.report.version === 4 && (
                                <p>
                                    {
                                        s.summary.report
                                            .source_bound_committed_rows
                                    }{" "}
                                    committed narrator inputs checked. This
                                    checks fresh Domain1 input consistency; it
                                    does not authenticate Director, compiler,
                                    raw output or model execution. Finite
                                    sentinels are diagnostics, not universal
                                    privacy. The original human assessment
                                    remains needs improvement.
                                </p>
                            )}
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
                            <p>
                                Recorded checks and validated inputs do not
                                establish narration quality or human acceptance.
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
                                            <td>
                                                {row.row.arm}
                                                {s.source?.protocol_version ===
                                                4
                                                    ? row.row.arm === "left"
                                                        ? " · Literal scene"
                                                        : " · Relevant memory scene"
                                                    : s.source
                                                            ?.protocol_version ===
                                                        3
                                                      ? row.row.arm === "left"
                                                          ? " · Literal player conversation"
                                                          : " · Relevant memory"
                                                      : ""}
                                            </td>
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
                            <header
                                className="comparison-selection-context"
                                aria-label="Selected report context"
                            >
                                <h3>
                                    {selected.row.turn} · {selected.row.arm}
                                </h3>
                                <p>
                                    Source story {selected.source.scope.story} ·
                                    branch {selected.source.scope.branch} ·
                                    before {selected.source.before_head} → after{" "}
                                    {selected.source.after_head} · observer{" "}
                                    {lens}
                                </p>
                                <p>
                                    Read-only report ·{" "}
                                    {s.uncertain
                                        ? "acknowledgement unavailable"
                                        : s.busy
                                          ? "read pending"
                                          : (s.status?.phase ?? "ready")}
                                </p>
                                {s.error && (
                                    <p role="alert">Comparison: {s.error}</p>
                                )}
                            </header>
                            {turn && (
                                <>
                                    <dl>
                                        <dt>Expected</dt>
                                        <dd>{turn.expected}</dd>
                                        <dt>Actual phase</dt>
                                        <dd>{turn.phase}</dd>
                                        <dt>Error</dt>
                                        <dd>{turn.error ?? "None"}</dd>
                                        <dt>
                                            {constructionTurn || sceneTurn
                                                ? "Construction"
                                                : "Policy"}
                                        </dt>
                                        <dd>
                                            {sceneTurn
                                                ? literal
                                                    ? "Literal scene"
                                                    : "Relevant memory scene"
                                                : constructionTurn
                                                  ? literal
                                                      ? "Literal player conversation"
                                                      : "Relevant memory"
                                                  : "policy" in turn
                                                    ? turn.policy
                                                    : "Unavailable"}
                                        </dd>
                                        {sceneTurn && (
                                            <>
                                                <dt>Construction evidence</dt>
                                                <dd>{constructionEvidence}</dd>
                                                <dt>Construction reason</dt>
                                                <dd>
                                                    {sceneTurn.construction_evidence_reason ??
                                                        "None recorded"}
                                                </dd>
                                                <dt>
                                                    Recipe metadata agreement
                                                </dt>
                                                <dd>
                                                    {sceneTurn.construction_matches
                                                        ? "Matches recorded recipe"
                                                        : "Not established"}
                                                </dd>
                                                <dt>Privacy evidence</dt>
                                                <dd>
                                                    {sceneTurn.privacy_evidence_status ===
                                                    "checked_finite_sentinels"
                                                        ? "Checked finite sentinels; diagnostic only"
                                                        : sceneTurn.privacy_evidence_status ===
                                                            "not_applicable_guard"
                                                          ? "Not applicable — guard"
                                                          : "Unavailable; inspect failure causes"}
                                                </dd>
                                                <dt>Narrator prompt hash</dt>
                                                <dd className="hash-value">
                                                    {display(
                                                        sceneTurn.narrator_prompt_sha256,
                                                    )}
                                                </dd>
                                                <dt>Narrator schema hash</dt>
                                                <dd className="hash-value">
                                                    {display(
                                                        sceneTurn.narrator_schema_sha256,
                                                    )}
                                                </dd>
                                                <dt>Scene frame hash</dt>
                                                <dd className="hash-value">
                                                    {display(
                                                        sceneTurn.scene_frame_sha256,
                                                    )}
                                                </dd>
                                            </>
                                        )}
                                        {constructionTurn && (
                                            <>
                                                <dt>Construction evidence</dt>
                                                <dd>{constructionEvidence}</dd>
                                                <dt>Construction agreement</dt>
                                                <dd>
                                                    {noGeneration
                                                        ? "Not applicable; no generation"
                                                        : constructionTurn.construction_matches
                                                          ? "Matches accepted construction"
                                                          : "No matching accepted construction"}
                                                </dd>
                                                <dt>Privacy check</dt>
                                                <dd>
                                                    {noGeneration
                                                        ? "Not applicable; no generation"
                                                        : !turn.roles_known ||
                                                            evidenceStatus ===
                                                                "unavailable"
                                                          ? "Unknown — evidence unavailable"
                                                          : "privacy_passed" in
                                                                  turn &&
                                                              turn.privacy_passed
                                                            ? "Passed finite recorded checks"
                                                            : "Not established"}
                                                </dd>
                                                {literal && (
                                                    <>
                                                        <dt>Source units</dt>
                                                        <dd>
                                                            {display(
                                                                constructionTurn.literal_source_units,
                                                            )}
                                                        </dd>
                                                        <dt>Selected start</dt>
                                                        <dd>
                                                            {display(
                                                                constructionTurn.literal_selected_start,
                                                            )}
                                                        </dd>
                                                        <dt>Selected units</dt>
                                                        <dd>
                                                            {display(
                                                                constructionTurn.literal_selected_units,
                                                            )}
                                                        </dd>
                                                    </>
                                                )}
                                            </>
                                        )}
                                        <dt>Role calls</dt>
                                        <dd>
                                            {turn.roles_known
                                                ? turn.roles
                                                : "Unknown; recovered without a complete recording"}
                                        </dd>
                                        <dt>Elapsed</dt>
                                        <dd>
                                            {(constructionTurn || sceneTurn) &&
                                            !turn.roles_known
                                                ? "Unknown; recovered without a complete recording"
                                                : `${turn.elapsed_ms} ms`}
                                        </dd>
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
                                            {literal
                                                ? "Not applicable — no memory package"
                                                : "estimated_context_tokens" in
                                                    turn
                                                  ? display(
                                                        turn.estimated_context_tokens,
                                                    )
                                                  : "Unavailable in this report version"}{" "}
                                            {!literal &&
                                                "estimated_context_tokens" in
                                                    turn &&
                                                "· estimate, not a measured token count"}
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
                                            c.setQuerySelection(
                                                event.target.value as
                                                    "before" | "after",
                                                view,
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
                                            c.setQuerySelection(
                                                edge,
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
                                    {s.source?.protocol_version === 4 && (
                                        <button disabled={s.busy}
                                            onClick={() => void c.inspectNarrationDiagnosticV1()}>
                                            Inspect narration diagnostic
                                        </button>
                                    )}
                                </div>
                            )}
                            {omni && s.diagnostic && (
                                <NarrationDiagnosticDetails result={s.diagnostic.diagnostic}
                                    source={selected.source} phase={turn?.phase ?? null}
                                    caseError={turn?.error} fallback={turn?.fallback ?? null}
                                    receiptAvailable={selected.receipt_available} />
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
                                    <p>
                                        Source story {s.evidence.scope.story} ·
                                        branch {s.evidence.scope.branch} ·
                                        before {s.evidence.before_head} → after{" "}
                                        {s.evidence.after_head}
                                    </p>
                                    {omni && turn ? (
                                        <>
                                            <p>
                                                Case phase: {turn.phase} ·
                                                Error:{" "}
                                                {turn.error ?? "None recorded"}{" "}
                                                · Scenario assertion:{" "}
                                                {turn.passed
                                                    ? "passed"
                                                    : "failed"}{" "}
                                                · Accepted receipt:{" "}
                                                {selected.receipt_available
                                                    ? "available"
                                                    : "unavailable"}
                                            </p>
                                            {turn.fallback === true && (
                                                <p>
                                                    Mechanical fallback
                                                    recorded. The raw model
                                                    response was not used as
                                                    play narration.
                                                </p>
                                            )}
                                        </>
                                    ) : (
                                        <p>
                                            Selected case outcome is unavailable
                                            in this lens.
                                        </p>
                                    )}
                                    <p>
                                        Human quality is not established. Raw
                                        model output is untrusted; commit and
                                        report readiness do not establish prose
                                        quality.
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
