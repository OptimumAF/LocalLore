import { EvaluationEvidencePanel } from "./EvaluationEvidencePanel";
import { useEffect, useState, useSyncExternalStore } from "react";
import type { EvaluationController } from "./evaluation-controller";
const display = (v: unknown) => {
    const text = typeof v === "string" ? v : JSON.stringify(v);
    const value = text ?? "Not reported";
    return value.length > 4096
        ? `${value.slice(0, 4096)} … (truncated)`
        : value;
};
export function EvaluationPanel({
    controller: c,
    context,
    allowed,
}: {
    controller: EvaluationController;
    context: string;
    allowed: boolean;
}) {
    const s = useSyncExternalStore(c.subscribe, c.get, c.get),
        selected = c.selected(),
        turn = selected?.turns.find((t) => t.id === s.selectedTurn);
    const [copyNotice, setCopyNotice] = useState("");
    useEffect(() => c.contextChanged(context, allowed), [c, context, allowed]);
    useEffect(() => setCopyNotice(""), [context]);
    if (!allowed || !c.matchesContext(context)) return null;
    return (
        <section
            className="evaluation-panel"
            aria-labelledby="evaluation-title"
        >
            <div className="topline">
                <h2 id="evaluation-title">Synthetic evaluations</h2>
                <button onClick={() => (s.shown ? c.hide() : void c.show())}>
                    {s.shown
                        ? "Close evaluation results"
                        : "Open evaluation results"}
                </button>
            </div>
            {s.shown && (
                <>
                    <EvaluationEvidencePanel controller={c} context={context} />
                    <p>
                        Isolated built-in scenarios · deterministic fake
                        inference. No model, semantic quality, human acceptance
                        or Android parity measurement.
                    </p>
                    <p>
                        Private output: local JSON, inert HTML and synthetic
                        case databases. {s.catalog?.retention}
                    </p>
                    <details>
                        <summary>Local evaluation storage & limits</summary>
                        <p className="storage-path">{s.catalog?.location}</p>
                        <p>
                            32 retained runs; one worker. Budgets checked at
                            scenario boundaries: 32 MiB per run, 256 MiB total,
                            64 MiB free before work. A current scenario may
                            exceed the boundary budget. No automatic report
                            deletion.
                        </p>
                    </details>
                    <div className="evaluation-actions">
                        <button
                            disabled={s.busy}
                            onClick={() => void c.start()}
                        >
                            Run built-in suite
                        </button>
                        <button
                            disabled={s.busy}
                            onClick={() => void c.start(null, "one")}
                        >
                            Run one scenario
                        </button>
                        <button
                            disabled={!s.status?.running}
                            onClick={() => void c.cancel()}
                        >
                            Stop after current scenario
                        </button>
                        <button
                            disabled={s.busy || !s.status || s.status.completed}
                            onClick={() => void c.resume()}
                        >
                            Resume remaining scenarios
                        </button>
                        <button
                            disabled={s.busy || !selected}
                            onClick={() => void c.rerun()}
                        >
                            Rerun selected built-in case
                        </button>
                        <button
                            disabled={!s.report || s.busy}
                            onClick={() => {
                                const report = s.report,
                                    version = c.presentationVersion();
                                if (report)
                                    void navigator.clipboard
                                        .writeText(
                                            JSON.stringify(report, null, 2),
                                        )
                                        .then(
                                            () => {
                                                if (
                                                    c.matchesContext(context) &&
                                                    version ===
                                                        c.presentationVersion()
                                                )
                                                    setCopyNotice(
                                                        "Private synthetic report JSON copied.",
                                                    );
                                            },
                                            () => {
                                                if (
                                                    c.matchesContext(context) &&
                                                    version ===
                                                        c.presentationVersion()
                                                )
                                                    setCopyNotice(
                                                        "Clipboard unavailable; report JSON remains in local evaluation storage.",
                                                    );
                                            },
                                        );
                            }}
                        >
                            Copy synthetic report JSON
                        </button>
                    </div>
                    {copyNotice && <p role="status">{copyNotice}</p>}
                    <p role="status">
                        {s.busy
                            ? "Working in an isolated evaluation. Cancellation waits for the current scenario boundary."
                            : (s.status?.phase ?? "Choose a run.")}{" "}
                        {s.status &&
                            `${s.status.completed_cases} completed cases`}
                    </p>
                    {s.error && (
                        <p role="alert">
                            {s.error}. Retained files are not automatically
                            removed. Source/checkpoint mismatch requires a new
                            run.
                        </p>
                    )}
                    <details>
                        <summary>Retained runs</summary>
                        <p>
                            Opening validates stored checkpoints without
                            rerunning scenarios and rebuilds the derived
                            JSON/HTML report. Changed sources refuse resume.
                            Checksums show consistency, not authorship.
                        </p>
                        <button disabled={s.busy} onClick={() => void c.show()}>
                            Refresh run library
                        </button>
                        <ul>
                            {s.catalog?.runs.map((r) => (
                                <li key={r.run_id}>
                                    <button
                                        disabled={s.busy}
                                        onClick={() => void c.open(r.run_id)}
                                    >
                                        {r.selection ?? "Built-in suite"} ·{" "}
                                        {r.run_id}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </details>
                    {s.report && (
                        <>
                            <p>
                                {
                                    s.report.cases.filter(
                                        (c) => c.status === "passed",
                                    ).length
                                }{" "}
                                passed ·{" "}
                                {
                                    s.report.cases.filter(
                                        (c) => c.status === "failed",
                                    ).length
                                }{" "}
                                failed ·{" "}
                                {
                                    s.report.cases.filter(
                                        (c) => c.status === "unsupported",
                                    ).length
                                }{" "}
                                unsupported. Quality accepted: false.{" "}
                                {s.report.completed
                                    ? "Suite selection complete."
                                    : "Incomplete; completed checkpoints retained."}
                            </p>
                            <p className="evaluation-binding">
                                Run {s.status?.run_id} · binding{" "}
                                {s.report.binding_sha256}
                            </p>
                            <table>
                                <caption>Evaluation cases</caption>
                                <thead>
                                    <tr>
                                        <th>Case</th>
                                        <th>Result</th>
                                        <th>Checks</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {s.report.cases.map((item) => (
                                        <tr key={item.id}>
                                            <th>
                                                <button
                                                    onClick={() =>
                                                        c.selectCase(item.id)
                                                    }
                                                    aria-pressed={
                                                        selected?.id === item.id
                                                    }
                                                >
                                                    {item.id}
                                                </button>
                                            </th>
                                            <td>{item.status}</td>
                                            <td>{item.checks.length}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </>
                    )}
                    {selected && (
                        <div className="evaluation-case">
                            <h3>
                                {selected.id} · {selected.status}
                            </h3>
                            {selected.unsupported && (
                                <p>Unsupported: {selected.unsupported}</p>
                            )}
                            <table>
                                <caption>
                                    Expected versus actual · declared assertions
                                </caption>
                                <thead>
                                    <tr>
                                        <th>Assertion / stage</th>
                                        <th>Expected</th>
                                        <th>Actual</th>
                                        <th>Result / source</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {selected.checks.map((x, i) => (
                                        <tr key={`${x.id}-${i}`}>
                                            <th>
                                                {x.id}
                                                <small>{x.stage}</small>
                                            </th>
                                            <td>{display(x.expected)}</td>
                                            <td>{display(x.actual)}</td>
                                            <td>
                                                {x.status}
                                                {x.turn && (
                                                    <button
                                                        onClick={() =>
                                                            c.selectTurn(
                                                                x.turn!,
                                                            )
                                                        }
                                                    >
                                                        {x.turn}
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            <p>
                                D05 story-inspector bridge unavailable: this
                                report has no app-session, scope or receipt
                                binding. D06 trace unavailable: the runner does
                                not retain window Host traces. Source links
                                select this report only.
                            </p>
                            {s.selectedTurn && (
                                <div className="evaluation-source">
                                    <h4>Report source: {s.selectedTurn}</h4>
                                    {turn ? (
                                        <>
                                            <p>
                                                Phase {display(turn.phase)} ·
                                                error {display(turn.error)} ·
                                                revision {turn.revision}
                                            </p>
                                            <p>
                                                Original input:{" "}
                                                {display(turn.intent)}
                                            </p>
                                            <p>{turn.narration}</p>
                                            <p>
                                                Canonical fingerprint{" "}
                                                {turn.canonical_sha256}
                                            </p>
                                        </>
                                    ) : (
                                        <p>
                                            Seed or assertion anchor; no
                                            recorded turn details are available.
                                        </p>
                                    )}
                                </div>
                            )}
                            <details>
                                <summary>
                                    Compiler/provider fingerprints and source
                                    binding · synthetic only
                                </summary>
                                <pre>
                                    {JSON.stringify(
                                        {
                                            provider_requests:
                                                selected.provider_requests,
                                            provenance: s.report?.provenance,
                                        },
                                        null,
                                        2,
                                    )}
                                </pre>
                            </details>
                        </div>
                    )}
                </>
            )}
        </section>
    );
}
