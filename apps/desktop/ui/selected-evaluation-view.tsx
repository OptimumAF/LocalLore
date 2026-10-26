// Story Lab utility surface: explicit actions, compact recorded state and a
// separate inspector. Root owns execution context, native grants and lifetime.
import { useCallback, useEffect, useState, useSyncExternalStore } from "react";
import type { SelectedEvaluationController } from "./selected-evaluation-controller";
import type {
    ObserverV2,
    RowId,
    SelectedArm,
    SelectedLane,
    SelectedSourceIdentity,
} from "./selected-evaluation-model";
import type { ViewV2 } from "./v2-view-model";
import { sameReaderObserver } from "./comparison-reader-model";

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
const label = (value: string) => value.replaceAll("_", " ");
const laneLabel = (value: string | null | undefined) =>
    value === "approved_native" || value === "native_selected_case"
        ? "Installed native model"
        : value === "scripted_baseline" || value === "scripted_selected_case"
          ? "Scripted baseline · fake inference"
          : "Lane not reported";
const boundedText = (value: string) =>
    value.length > 2048
        ? `${value.slice(0, 2048)} … (display truncated)`
        : value;
function BoundedList({ values, name }: { values: string[]; name: string }) {
    return (
        <>
            <ul aria-label={name}>
                {values.slice(0, 24).map((value, index) => (
                    <li key={index}>{boundedText(value)}</li>
                ))}
            </ul>
            {values.length > 24 && (
                <p>{values.length - 24} further entries are not displayed.</p>
            )}
        </>
    );
}
function BoundedJson({ value }: { value: unknown }) {
    const text = JSON.stringify(value, null, 2) ?? "Unavailable";
    return (
        <>
            <pre>{text.slice(0, 16384)}</pre>
            {text.length > 16384 && (
                <p>
                    Display limited to 16,384 characters. Stored evidence is
                    unchanged.
                </p>
            )}
        </>
    );
}

export type SelectedEvaluationViewProps = {
    controller: SelectedEvaluationController;
    source: SelectedSourceIdentity | null;
    row: RowId | null;
    observer: ObserverV2;
    sourceUnavailable?: boolean;
};
export function SelectedEvaluationView({
    controller: c,
    source,
    row,
    observer,
    sourceUnavailable = false,
}: SelectedEvaluationViewProps) {
    const subscribe = useCallback(
        (listener: () => void) => c.subscribe(listener),
        [c],
    );
    const get = useCallback(() => c.get(), [c]);
    const s = useSyncExternalStore(subscribe, get, get);
    const [lane, setLane] = useState<SelectedLane>("scripted_baseline");
    const [savedId, setSavedId] = useState("");
    const [arm, setArm] = useState<SelectedArm>("left");
    const [edge, setEdge] = useState<"before" | "after">("after");
    const [view, setView] = useState<ViewV2>("knowledge");
    // No cleanup/dispose here: changing an inspector or unmounting this view
    // must not cancel/rekey generation. Root owns actual lifecycle retirement.
    useEffect(() => {
        c.setObserver(observer);
    }, [c, observer]);
    const lensMatches = sameReaderObserver(s.observer, observer);
    const omni = lensMatches && observer.kind === "omniscient";
    const lens = observer.kind === "character" ? observer.id : observer.kind;
    const status = s.status;
    const blocked =
        s.busy ||
        s.uncertain ||
        s.cleanup?.cleanup_required === true ||
        s.cleanup?.running === true;
    const readReady =
        s.allowed &&
        lensMatches &&
        !blocked &&
        !!status?.run_token &&
        !!status.binding;
    const prepared = status?.prepared;
    const summary = s.allowed ? s.summary : null;
    // Render fence precedes effects: an actor prop never gets one render of an
    // old omniscient body while setObserver is waiting for its React effect.
    const evidence =
        s.allowed &&
        lensMatches &&
        s.evidence &&
        sameReaderObserver(s.evidence.observer, observer) &&
        (s.evidence.body.kind === "query" ||
            s.evidence.body.kind === "missing" ||
            omni)
            ? s.evidence
            : null;
    const diagnostics = s.allowed && omni ? s.diagnostics : null;
    const saved = s.catalog?.runs.find((run) => run.run_id === savedId);
    const controlsIdle = () => {
        const now = c.get();
        return !now.busy && !now.uncertain;
    };
    const inspect = (kind: "query" | "receipt" | "capture" | "outputs") => {
        const now = c.get();
        if (
            !now.allowed ||
            now.busy ||
            now.uncertain ||
            !sameReaderObserver(now.observer, observer)
        )
            return;
        if (kind === "query")
            void c.readEvidence(arm, {
                kind,
                edge,
                view,
                observer: now.observer,
            });
        else if (now.observer.kind === "omniscient")
            void c.readEvidence(arm, { kind, observer: now.observer });
    };
    return (
        <section
            id="selected-evaluation"
            className="comparison-reader"
            aria-labelledby="selected-evaluation-title"
            data-phase={status?.phase ?? "idle"}
            data-observer={lens}
            data-turn={
                summary?.selection.turn ?? prepared?.selection.turn ?? ""
            }
            data-pending-action={s.pending?.action ?? ""}
        >
            <h2 id="selected-evaluation-title">Selected-case experiment</h2>
            <p>
                Attempt one original turn in both isolated policy arms. Source
                stories remain unchanged; each arm has its own copied history.
            </p>
            {!s.allowed && (
                <p className="comparison-unavailable">
                    Story Lab access is unavailable. Worker cleanup controls
                    remain available below.
                </p>
            )}

            <div
                className="comparison-controls"
                role="group"
                aria-label="Prepare selected experiment"
            >
                <label>
                    New experiment lane{" "}
                    <select
                        aria-label="Selected experiment lane"
                        value={lane}
                        disabled={!s.allowed || blocked || !!s.clientId}
                        onChange={(event) => {
                            if (!controlsIdle() || c.get().clientId) return;
                            const value = event.target.value;
                            if (
                                value === "scripted_baseline" ||
                                value === "approved_native"
                            )
                                setLane(value);
                        }}
                    >
                        <option value="scripted_baseline">
                            Scripted baseline · fake inference
                        </option>
                        <option value="approved_native">
                            Installed native model · approved assets required
                        </option>
                    </select>
                </label>
                <button
                    disabled={
                        !s.allowed || blocked || !!s.clientId || !source || !row
                    }
                    onClick={() => {
                        if (source && row) void c.prepare(source, row, lane);
                    }}
                >
                    Prepare selected case
                </button>
                <button
                    disabled={
                        !s.allowed ||
                        blocked ||
                        status?.phase !== "prepared" ||
                        !status.plan_token
                    }
                    onClick={() => void c.start()}
                >
                    Start prepared experiment
                </button>
            </div>
            <p>
                {source && row
                    ? `Reader selection for a new experiment: ${row.turn} · clicked ${row.arm} arm.`
                    : sourceUnavailable
                      ? "Selected-case reruns are unavailable for this literal/relevant report. Read-only inspection remains available above."
                      : "Choose a comparison report and a source turn in the reader before preparing an experiment."}
            </p>
            <p>
                {lane === "scripted_baseline"
                    ? "Scripted inference is a synthetic plumbing check; it does not measure model quality."
                    : "Native execution requires installed approved model assets and fresh native confirmation. Availability is checked on admission."}
            </p>
            {s.clientId && (
                <p>
                    Close this attempt before preparing another. Retrying a
                    finished failed or cancelled attempt requires a new
                    experiment.
                </p>
            )}

            <div
                className="comparison-controls"
                role="group"
                aria-label="Experiment status and cancellation"
            >
                <button
                    disabled={
                        !s.allowed || !s.clientId || (s.busy && !s.uncertain)
                    }
                    onClick={() => void c.status()}
                >
                    Check same request status
                </button>
                <button
                    disabled={
                        !s.allowed ||
                        s.uncertain ||
                        !status?.running ||
                        status.operation_id === null ||
                        status.phase === "completed" ||
                        status.phase === "closed"
                    }
                    onClick={() => void c.cancel()}
                >
                    Cancel current operation
                </button>
                <button
                    disabled={!s.allowed || !s.clientId}
                    onClick={() => void c.close()}
                >
                    Close attempt / stop work
                </button>
            </div>
            <p role="status">
                {status ? label(status.phase) : "No attempt open"}
                {status ? ` · ${laneLabel(status.lane)}` : ""}
                {status?.running ? " · native work still pending" : ""}
                {s.uncertain
                    ? " · acknowledgement unavailable; check or close the same request"
                    : ""}
            </p>
            {s.pending && (
                <p data-operation-id={s.pending.operationId ?? "unknown"}>
                    Pending: {label(s.pending.action)} · operation{" "}
                    {s.pending.operationId ??
                        "unknown — awaiting native acknowledgement"}
                    .
                </p>
            )}
            {!s.pending &&
                status?.operation_id !== null &&
                status?.operation_id !== undefined && (
                    <p>Last acknowledged operation: {status.operation_id}.</p>
                )}
            {status?.phase === "completed" && (
                <p>
                    Attempts finished. This does not establish success or
                    quality; inspect the recorded results.
                </p>
            )}
            {s.error && (
                <p role="alert" className="error">
                    Selected experiment: {s.error}
                    {status?.cause && status.cause !== s.error
                        ? ` · original cause ${status.cause}`
                        : ""}
                    .
                </p>
            )}

            {s.allowed && prepared && (
                <div
                    className="comparison-selected"
                    aria-label="Prepared experiment identity"
                >
                    <h3>Prepared original turn: {prepared.selection.turn}</h3>
                    <p>
                        {laneLabel(prepared.lane)} · original index{" "}
                        {prepared.selection.index} · clicked{" "}
                        {prepared.selection.clicked_arm} arm.
                    </p>
                    {prepared.arms.map((item) => (
                        <p key={item.arm}>
                            {item.arm}: story {item.scope.story} · branch{" "}
                            {item.scope.branch} · before head {item.before_head}
                            .
                        </p>
                    ))}
                    <details>
                        <summary>Prepared identity hashes</summary>
                        <p className="hash-value">{prepared.binding}</p>
                        {prepared.arms.map((item) => (
                            <p key={item.arm} className="hash-value">
                                {item.arm} prefix {item.prefix_sha256} · input{" "}
                                {item.input_semantic_sha256}
                            </p>
                        ))}
                    </details>
                </div>
            )}

            <h3>Saved attempts and read access</h3>
            <p>
                Saved experiments are durable. Opening private results requires
                separate native inspection permission; completing execution does
                not grant it.
            </p>
            <div className="comparison-controls">
                <button
                    disabled={!s.allowed || s.busy}
                    onClick={() => void c.catalog()}
                >
                    List saved attempts
                </button>
                <label>
                    Saved attempt{" "}
                    <select
                        aria-label="Saved selected experiment"
                        value={saved ? savedId : ""}
                        disabled={!s.allowed || blocked || !!s.clientId}
                        onChange={(event) => {
                            if (controlsIdle() && !c.get().clientId)
                                setSavedId(event.target.value);
                        }}
                    >
                        <option value="">Choose a saved attempt</option>
                        {s.catalog?.runs.map((run) => (
                            <option key={run.run_id} value={run.run_id}>
                                {run.selection.turn} ·{" "}
                                {run.selection.clicked_arm} ·{" "}
                                {laneLabel(run.lane)} · {run.run_id}
                            </option>
                        ))}
                    </select>
                </label>
                <button
                    disabled={!s.allowed || blocked || !!s.clientId || !saved}
                    onClick={() => {
                        if (saved) void c.open(saved.run_id);
                    }}
                >
                    Open saved attempt · asks permission
                </button>
                <button
                    disabled={!s.allowed || blocked || !status?.run_id}
                    onClick={() => {
                        if (status?.run_id) void c.open(status.run_id);
                    }}
                >
                    Open this attempt for inspection · asks permission
                </button>
            </div>
            {s.catalog && s.catalog.runs.length === 0 && (
                <p>
                    No saved attempts were reported. Missing work is not
                    recreated automatically.
                </p>
            )}
            <div className="comparison-controls">
                <button
                    disabled={
                        !s.allowed || blocked || !status?.run_token || !source
                    }
                    onClick={() => {
                        if (source) void c.resume(source);
                    }}
                >
                    Resume / verify with linked source
                </button>
                <button
                    disabled={!readReady}
                    onClick={() => void c.loadSummary()}
                >
                    Read selected scope and heads
                </button>
            </div>
            {!source && status?.run_id && (
                <p>
                    Choose the matching source report again before requesting
                    resume.
                </p>
            )}
            <p>
                Resume is explicit and revalidates the source. Checking status
                never restarts inference. Completed attempts can be verified
                without repeating their committed work.
            </p>

            {summary && (
                <div
                    className="comparison-selected"
                    aria-label="Selected experiment summary"
                >
                    <h3>Opened original turn: {summary.selection.turn}</h3>
                    <p>
                        {laneLabel(summary.lane)} · index{" "}
                        {summary.selection.index} · originally clicked{" "}
                        {summary.selection.clicked_arm}.
                    </p>
                    <div
                        className="comparison-table"
                        role="region"
                        tabIndex={0}
                        aria-label="Selected arm revisions"
                    >
                        <table>
                            <thead>
                                <tr>
                                    <th>Arm</th>
                                    <th>Story / branch</th>
                                    <th>Before → after</th>
                                    <th>Checkpoint</th>
                                </tr>
                            </thead>
                            <tbody>
                                {summary.arms.map((item) => (
                                    <tr key={item.arm}>
                                        <td>{item.arm}</td>
                                        <td>
                                            {item.scope.story} /{" "}
                                            {item.scope.branch}
                                        </td>
                                        <td>
                                            {item.before_head} →{" "}
                                            {item.after_head ?? "Unavailable"}
                                        </td>
                                        <td>
                                            {item.available
                                                ? "Available"
                                                : "Unavailable"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <details>
                        <summary>Last validated read binding</summary>
                        <p className="hash-value">{summary.binding}</p>
                        <p>
                            Evidence is validated again on explicit reads. This
                            binding grants no execution or generation access.
                        </p>
                    </details>
                </div>
            )}

            <h3>Inspect recorded evidence</h3>
            <p>
                Observer: {lens}. Inspection never changes character knowledge
                or generation context.
            </p>
            {!lensMatches && (
                <p role="status">
                    Updating the inspection lens; old private content is hidden.
                </p>
            )}
            {!omni && (
                <p>
                    Receipts, captures, model outputs and diagnostic results are
                    hidden. State queries use the engine's observer filter.
                </p>
            )}
            <div
                className="comparison-controls"
                role="group"
                aria-label="Next selected state query"
            >
                <label>
                    Next query arm{" "}
                    <select
                        aria-label="Next selected query arm"
                        value={arm}
                        disabled={!readReady || !summary}
                        onChange={(event) => {
                            if (!controlsIdle()) return;
                            const value = event.target.value;
                            if (value === "left" || value === "right")
                                setArm(value);
                        }}
                    >
                        <option value="left">Left policy arm</option>
                        <option value="right">Right policy arm</option>
                    </select>
                </label>
                <label>
                    Next query edge{" "}
                    <select
                        aria-label="Next selected query edge"
                        value={edge}
                        disabled={!readReady || !summary}
                        onChange={(event) => {
                            if (!controlsIdle()) return;
                            const value = event.target.value;
                            if (value === "before" || value === "after")
                                setEdge(value);
                        }}
                    >
                        <option value="before">Before turn</option>
                        <option value="after">After turn</option>
                    </select>
                </label>
                <label>
                    Next query view{" "}
                    <select
                        aria-label="Next selected query view"
                        value={view}
                        disabled={!readReady || !summary}
                        onChange={(event) => {
                            if (
                                controlsIdle() &&
                                views.includes(event.target.value as ViewV2)
                            )
                                setView(event.target.value as ViewV2);
                        }}
                    >
                        {views.map((item) => (
                            <option key={item} value={item}>
                                {label(item)}
                            </option>
                        ))}
                    </select>
                </label>
                <button
                    disabled={!readReady || !summary}
                    onClick={() => inspect("query")}
                >
                    Read observer-filtered state
                </button>
            </div>
            <div
                className="comparison-controls"
                role="group"
                aria-label="Explicit private selected evidence"
            >
                <button
                    disabled={!readReady || !summary || !omni}
                    onClick={() => inspect("receipt")}
                >
                    Read receipt
                </button>
                <button
                    disabled={!readReady || !summary || !omni}
                    onClick={() => inspect("capture")}
                >
                    Read capture
                </button>
                <button
                    disabled={!readReady || !summary || !omni}
                    onClick={() => inspect("outputs")}
                >
                    Read model outputs
                </button>
                <button
                    disabled={!readReady || !summary || !omni}
                    onClick={() => {
                        if (
                            sameReaderObserver(c.get().observer, observer) &&
                            observer.kind === "omniscient"
                        )
                            void c.readDiagnostics();
                    }}
                >
                    Read expected / actual results
                </button>
            </div>
            {!status?.run_token && (
                <p>
                    No inspection handle is available. Open an attempt with
                    native permission before requesting evidence.
                </p>
            )}
            {evidence && (
                <div
                    className="private-capture"
                    aria-label="Displayed selected evidence"
                >
                    <h4>
                        Displayed evidence: {evidence.row.turn} ·{" "}
                        {evidence.row.arm} · {evidence.body.kind}
                    </h4>
                    <p>
                        Story {evidence.scope.story} · branch{" "}
                        {evidence.scope.branch} · before {evidence.before_head}{" "}
                        → after {evidence.after_head ?? "Unavailable"} ·
                        observer{" "}
                        {evidence.observer.kind === "character"
                            ? evidence.observer.id
                            : evidence.observer.kind}
                        {evidence.edge ? ` · ${evidence.edge}` : ""}
                        {evidence.body.kind === "query"
                            ? ` · ${label(evidence.body.page.view)}`
                            : ""}
                        .
                    </p>
                    {evidence.body.kind === "missing" ? (
                        <p className="comparison-unavailable">
                            Unavailable: {label(evidence.body.reason)}. No
                            replacement evidence is invented.
                        </p>
                    ) : evidence.body.kind === "query" ? (
                        <>
                            <p>
                                {evidence.body.page.total} matching rows ·{" "}
                                {evidence.body.page.status}.
                                {evidence.body.page.next_cursor
                                    ? " More rows exist; paging is unavailable in this panel."
                                    : ""}
                            </p>
                            <BoundedJson value={evidence.body.page} />
                        </>
                    ) : (
                        <BoundedJson value={evidence.body} />
                    )}
                </div>
            )}
            {diagnostics && (
                <div aria-label="Selected expected and actual results">
                    <h4>Recorded results · {laneLabel(diagnostics.lane)}</h4>
                    <p>
                        Human reviews: {diagnostics.human_reviewed} · quality
                        acceptance: not established. Physical setups:{" "}
                        {diagnostics.physical_setups} · setup time{" "}
                        {diagnostics.physical_setup_ms === null
                            ? "Unavailable"
                            : `${diagnostics.physical_setup_ms} ms`}
                        .
                    </p>
                    <p>
                        Recorded charges: left {diagnostics.left_charged_ms} ms
                        / {diagnostics.left_reserved_roles} reserved roles;{" "}
                        right {diagnostics.right_charged_ms} ms /{" "}
                        {diagnostics.right_reserved_roles} reserved roles.
                        Reservations are not measured model calls.
                    </p>
                    {diagnostics.rows.map((item) => (
                        <div
                            key={`${item.turn}:${item.arm}`}
                            className="comparison-selected"
                        >
                            <h4>
                                {item.turn} · {item.arm}
                            </h4>
                            <dl>
                                <dt>Expected</dt>
                                <dd>{boundedText(item.expected)}</dd>
                                <dt>Actual phase</dt>
                                <dd>{label(item.phase)}</dd>
                                <dt>Recorded checks</dt>
                                <dd>{item.passed ? "Passed" : "Not passed"}</dd>
                                <dt>Error</dt>
                                <dd>
                                    {item.error
                                        ? boundedText(item.error)
                                        : "None recorded"}
                                </dd>
                                <dt>Recorded role calls</dt>
                                <dd>
                                    {item.roles_known
                                        ? item.roles
                                        : "Unknown; historical calls were not recovered"}
                                </dd>
                                <dt>Recorded elapsed</dt>
                                <dd>
                                    {item.roles_known
                                        ? `${item.elapsed_ms} ms`
                                        : "Unavailable after recovery"}
                                </dd>
                                <dt>Privacy check</dt>
                                <dd>
                                    {item.privacy_passed
                                        ? "Passed"
                                        : "Not established"}
                                </dd>
                                <dt>Context check flag</dt>
                                <dd>
                                    {item.context_evidence_available
                                        ? "Available"
                                        : "Unavailable"}
                                </dd>
                            </dl>
                            {item.actual_receipt_sha256 && (
                                <p className="hash-value">
                                    Actual receipt hash:{" "}
                                    {item.actual_receipt_sha256}
                                </p>
                            )}
                            {item.failures.length > 0 && (
                                <BoundedList
                                    name={`${item.arm} failures`}
                                    values={item.failures}
                                />
                            )}
                            {item.quality_flags.length > 0 && (
                                <BoundedList
                                    name={`${item.arm} quality flags`}
                                    values={item.quality_flags}
                                />
                            )}
                        </div>
                    ))}
                    {diagnostics.rows.length === 0 && (
                        <p>No finished attempt rows are available.</p>
                    )}
                    {diagnostics.unavailable.length > 0 && (
                        <details>
                            <summary>
                                Unavailable measurements and limitations
                            </summary>
                            <BoundedList
                                name="Unavailable selected measurements"
                                values={diagnostics.unavailable}
                            />
                        </details>
                    )}
                </div>
            )}

            <h3>Worker cleanup</h3>
            <p>
                Cleanup status contains no story evidence. Retry only requests
                confirmation from the same retained native owner.
            </p>
            <div className="comparison-controls">
                <button
                    disabled={s.busy}
                    onClick={() => void c.cleanupStatus()}
                >
                    Check worker cleanup
                </button>
                <button
                    disabled={
                        s.busy ||
                        s.cleanup?.running ||
                        !s.cleanup?.cleanup_required
                    }
                    onClick={() => void c.retryCleanup()}
                >
                    Retry retained worker cleanup
                </button>
            </div>
            <p role="status">
                {s.cleanup
                    ? s.cleanup.running
                        ? "Cleanup work pending"
                        : s.cleanup.cleanup_required
                          ? "Cleanup is unconfirmed; another model must not be admitted"
                          : "No retained cleanup is reported"
                    : "Cleanup has not been checked"}
                {s.cleanup?.error ? ` · ${s.cleanup.error}` : ""}.
            </p>
        </section>
    );
}
