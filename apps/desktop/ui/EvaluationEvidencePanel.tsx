import { useEffect, useState, useSyncExternalStore } from "react";
import type { EvaluationController } from "./evaluation-controller";
const json = (value: unknown) => JSON.stringify(value, null, 2);
export function EvaluationEvidencePanel({
    controller: c,
    context,
}: {
    controller: EvaluationController;
    context: string;
}) {
    const s = useSyncExternalStore(c.subscribe, c.get, c.get),
        status = s.curatedStatus,
        snapshot = status?.snapshot,
        report = snapshot?.report,
        selected = c.curatedSelected();
    const [lane, setLane] = useState<"scripted" | "native">("scripted"),
        [consent, setConsent] = useState(false);
    useEffect(() => setConsent(false), [context, lane, status?.run_id]);
    const privateLens = context.endsWith("|omniscient"),
        busy = s.busy || s.curatedBusy;
    if (!privateLens)
        return (
            <p>
                Curated private reports require the Story Lab omniscient lens.
                Inspection never grants generation knowledge.
            </p>
        );
    return (
        <section
            className="curated-evaluation"
            aria-label="Curated local evaluations"
        >
            <h3>Curated synthetic stories</h3>
            <p>
                Six stories, four turn cases each. Scripted fake checks
                plumbing; local model execution remains experimental. Neither
                lane is a transcript-only or verified-memory comparison. Human
                quality accepted: false.
            </p>
            <button disabled={busy} onClick={() => void c.curatedShow()}>
                Open curated run library
            </button>
            {s.curatedCatalog && (
                <>
                    <label>
                        Lane{" "}
                        <select
                            disabled={busy}
                            value={lane}
                            onChange={(e) =>
                                setLane(e.target.value as "scripted" | "native")
                            }
                        >
                            <option value="scripted">
                                Curated scripted fake
                            </option>
                            <option value="native">Approved local model</option>
                        </select>
                    </label>
                    {(lane === "native" || status?.lane === "native") && (
                        <>
                            <p>
                                Ordinary Play model must be unloaded. Evaluation
                                owns one isolated worker and uses the approved
                                imported model; there is no fallback to fake
                                inference.
                            </p>
                            <label>
                                <input
                                    type="checkbox"
                                    checked={consent}
                                    onChange={(e) =>
                                        setConsent(e.target.checked)
                                    }
                                />
                                I consent to bounded local inference and private
                                raw output retention for this run/resume.
                            </label>
                            <details>
                                <summary>
                                    Approved model metadata and availability
                                </summary>
                                <pre>
                                    {json({
                                        availability: s.curatedCatalog.model,
                                        approved_profile:
                                            s.curatedCatalog.approved_profile,
                                    })}
                                </pre>
                            </details>
                        </>
                    )}
                    <p>
                        Run limits: 32 admitted attempts, 96 charged roles, 30
                        minutes across invocations, 32 invocations. Unknown
                        interrupted work stays reserved. Reports/checkpoints
                        remain private; quotas block further work rather than
                        deleting them.
                    </p>
                    <div className="evaluation-actions">
                        <button
                            disabled={busy || (lane === "native" && !consent)}
                            onClick={() =>
                                void c.curatedStart(lane, null, "all", consent)
                            }
                        >
                            Run curated suite
                        </button>
                        <button
                            disabled={busy || (lane === "native" && !consent)}
                            onClick={() =>
                                void c.curatedStart(lane, null, "one", consent)
                            }
                        >
                            Run one story checkpoint
                        </button>
                        <button
                            disabled={!status?.running}
                            onClick={() => void c.curatedCancel()}
                        >
                            Cancel curated work
                        </button>
                        <button
                            disabled={
                                busy ||
                                !status ||
                                snapshot?.resume_compatible === false ||
                                (status.lane === "native" &&
                                    !status.completed &&
                                    !consent)
                            }
                            onClick={() => void c.curatedResume(consent)}
                        >
                            Resume / inspect completed cache
                        </button>
                        <button
                            disabled={
                                busy ||
                                !selected ||
                                (lane === "native" && !consent)
                            }
                            onClick={() =>
                                void c.curatedStart(
                                    lane,
                                    selected!.id,
                                    "all",
                                    consent,
                                )
                            }
                        >
                            Rerun selected story in new run
                        </button>
                        {s.pendingClient && (
                            <button
                                disabled={busy}
                                onClick={() => void c.curatedRecover()}
                            >
                                Recover original run acknowledgement
                            </button>
                        )}
                    </div>
                    <details>
                        <summary>Retained curated runs</summary>
                        <ul>
                            {s.curatedCatalog.runs.map((r) => (
                                <li key={r.run_id}>
                                    <button
                                        disabled={busy}
                                        onClick={() =>
                                            void c.curatedOpen(r.run_id)
                                        }
                                    >
                                        {r.lane} ·{" "}
                                        {r.selection ?? "six stories"} ·{" "}
                                        {r.run_id}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </details>
                </>
            )}
            <p role="status">
                {status
                    ? `${status.lane} · run ${status.run_id} · ${status.phase} · operation ${status.operation_id ?? "none"}`
                    : "Choose a curated run."}
            </p>
            {status?.running && (
                <p>
                    Runner active. Current turn/role progress is unavailable;
                    completed checkpoint progress appears when this bounded
                    invocation returns. Cancellation can abandon the current
                    four-turn story attempt; prior checkpoints and charged
                    unknown work remain.
                </p>
            )}
            {snapshot && (
                <>
                    <p>
                        {snapshot.checkpointed_stories} checkpointed stories ·{" "}
                        {snapshot.completed ? "selection complete" : "partial"}{" "}
                        ·{" "}
                        {snapshot.resume_compatible
                            ? "current source binding"
                            : "historical source: view only, resume refused"}
                        . This report view runs no generation or asset
                        verification.
                    </p>
                    <details>
                        <summary>Cumulative budget and source binding</summary>
                        <pre>
                            {json({
                                binding: snapshot.binding_sha256,
                                budget: snapshot.budget,
                                provenance: report?.provenance,
                            })}
                        </pre>
                    </details>
                </>
            )}
            {s.curatedError && (
                <p role="alert">
                    {s.curatedError}. No script substitution or report deletion.
                    Recover the original request if acknowledgement was lost.
                </p>
            )}
            {report && (
                <>
                    <table>
                        <caption>Curated case results</caption>
                        <thead>
                            <tr>
                                <th>Story</th>
                                <th>Result</th>
                                <th>Checks</th>
                            </tr>
                        </thead>
                        <tbody>
                            {report.cases.map((row) => (
                                <tr key={row.id}>
                                    <th>
                                        <button
                                            disabled={busy}
                                            onClick={() =>
                                                c.curatedSelectCase(row.id)
                                            }
                                            aria-pressed={
                                                s.curatedCase === row.id
                                            }
                                        >
                                            {row.id}
                                        </button>
                                    </th>
                                    <td>{row.status}</td>
                                    <td>{row.checks.length}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {selected && (
                        <>
                            <h4>{selected.id}</h4>
                            <ul>
                                {selected.checks
                                    .filter((x) => x.status !== "passed")
                                    .map((x) => (
                                        <li key={x.id}>
                                            <button
                                                disabled={busy || !x.turn}
                                                onClick={() =>
                                                    x.turn &&
                                                    c.curatedSelectTurn(x.turn)
                                                }
                                            >
                                                {x.id}: {x.status}
                                            </button>
                                            <pre>
                                                {json({
                                                    expected: x.expected,
                                                    actual: x.actual,
                                                })}
                                            </pre>
                                        </li>
                                    ))}
                            </ul>
                            <label>
                                Evaluated turn{" "}
                                <select
                                    disabled={busy}
                                    value={s.curatedTurn ?? ""}
                                    onChange={(e) =>
                                        c.curatedSelectTurn(e.target.value)
                                    }
                                >
                                    <option value="">Choose turn</option>
                                    {selected.turns.map((t) => (
                                        <option key={t.id} value={t.id}>
                                            {t.id} · revision {t.revision} ·{" "}
                                            {String(t.phase)}
                                        </option>
                                    ))}
                                </select>
                            </label>
                            <div className="evaluation-actions">
                                <button
                                    disabled={busy || !s.curatedTurn}
                                    onClick={() => void c.curatedInspect()}
                                >
                                    Inspect evaluated turn diff and retained
                                    output
                                </button>
                                <button
                                    disabled={busy || !s.curatedTurn}
                                    onClick={() =>
                                        void c.curatedInspect(
                                            { kind: "player" },
                                            "knowledge",
                                        )
                                    }
                                >
                                    Inspect player-visible evaluated knowledge
                                </button>
                            </div>
                            <p>
                                This opens a read-only evaluated snapshot, never
                                the live story. Full historical context,
                                prompts, schema bytes, staged plans and window
                                traces were not retained.
                            </p>
                        </>
                    )}
                </>
            )}
            {s.curatedEvidence && (
                <div className="curated-evidence">
                    <h4>Bound evaluated evidence</h4>
                    <p>
                        Run {s.curatedEvidence.run_id} · case{" "}
                        {s.curatedEvidence.evidence.case_id} · turn{" "}
                        {s.curatedEvidence.evidence.turn_id} ·{" "}
                        {s.curatedEvidence.evidence.scope.story}/
                        {s.curatedEvidence.evidence.scope.branch} · revision{" "}
                        {s.curatedEvidence.evidence.revision} · observer{" "}
                        {json(s.curatedEvidence.evidence.observer)}.
                    </p>
                    <p>
                        Canonical fingerprint{" "}
                        {s.curatedEvidence.evidence.canonical_sha256}. Exact
                        reconstruction: false. Generation grant: false.
                    </p>
                    <details>
                        <summary>D05 evaluated inspection page</summary>
                        <pre>{json(s.curatedEvidence.evidence.page)}</pre>
                    </details>
                    <details>
                        <summary>
                            Actual accepted receipt, if retained and permitted
                        </summary>
                        <pre>
                            {s.curatedEvidence.evidence.receipt
                                ? json(s.curatedEvidence.evidence.receipt)
                                : "No accepted receipt available for this turn/lens."}
                        </pre>
                    </details>
                    <details>
                        <summary>
                            D06 retained role output / hashes / metrics
                        </summary>
                        <p>
                            Historical copies only. Raw proposal or narrator
                            output is not an accepted canonical effect.
                        </p>
                        <pre>
                            {json({
                                outputs: s.curatedEvidence.evidence.outputs,
                                role_metrics:
                                    s.curatedEvidence.evidence.role_metrics,
                                missing: s.curatedEvidence.evidence.missing,
                            })}
                        </pre>
                    </details>
                </div>
            )}
        </section>
    );
}
