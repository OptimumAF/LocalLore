// Plain Story Lab utility surface. Native execution, canonical histories,
// permissions and worker cleanup remain with the shared Rust owners.
import { useCallback, useState, useSyncExternalStore } from "react";
import type { ComparisonRunController } from "./comparison-run-controller";
import type { ComparisonRunKind } from "./comparison-run-model";
export function ComparisonRunView({
    controller: c,
    onInspect,
}: {
    controller: ComparisonRunController;
    onInspect: (runId: string) => void | Promise<void>;
}) {
    const subscribe = useCallback(
        (listener: () => void) => c.subscribe(listener),
        [c],
    );
    const get = useCallback(() => c.get(), [c]);
    const s = useSyncExternalStore(subscribe, get, get);
    const [kind, setKind] = useState<ComparisonRunKind>("paired");
    const [batch, setBatch] = useState(1);
    const [savedId, setSavedId] = useState("");
    const status = s.allowed ? s.status : null;
    const ready =
        !!status &&
        status.report_ready &&
        !status.running &&
        status.phase !== "closed" &&
        !s.uncertain;
    const idle = s.allowed && !s.busy && !s.uncertain;
    const canInspect = () => {
        const now = c.get(),
            current = now.status;
        return now.allowed &&
            !now.uncertain &&
            !now.busy &&
            current?.report_ready &&
            !current.running &&
            current.phase !== "closed"
            ? current.run_id
            : null;
    };
    return (
        <section
            id="comparison-run"
            className="comparison-run"
            aria-labelledby="comparison-run-title"
            data-phase={status?.phase ?? "idle"}
            data-pending-action={s.pending?.action ?? ""}
        >
            <h2 id="comparison-run-title">Run full comparison</h2>
            <p>
                Scripted baseline · fake inference. Native execution is
                unavailable here. Human quality is not established.
            </p>
            <p>
                Compare literal player conversation with relevant memory using
                isolated Rust-owned histories. A completed run does not grant
                private inspection access.
            </p>
            {!s.allowed && (
                <p className="comparison-unavailable">
                    Story Lab access is unavailable. Captured presentation can
                    still be closed.
                </p>
            )}
            <div
                className="comparison-controls"
                role="group"
                aria-label="New scripted comparison"
            >
                <label>
                    Comparison kind{" "}
                    <select
                        aria-label="Full comparison kind"
                        value={kind}
                        disabled={!idle || !!s.clientId}
                        onChange={(event) => {
                            if (
                                !c.get().busy &&
                                (event.target.value === "paired" ||
                                    event.target.value === "rollout")
                            )
                                setKind(event.target.value);
                        }}
                    >
                        <option value="paired">
                            Paired snapshots · fixed reference
                        </option>
                        <option value="rollout">
                            Continuous rollout · separate arm histories
                        </option>
                    </select>
                </label>
                <label>
                    New scenes per chunk{" "}
                    <select
                        aria-label="Comparison scene batch"
                        value={batch}
                        disabled={!idle}
                        onChange={(event) => {
                            const value = Number(event.target.value);
                            if (
                                !c.get().busy &&
                                Number.isInteger(value) &&
                                value >= 1 &&
                                value <= 4
                            )
                                setBatch(value);
                        }}
                    >
                        {[1, 2, 3, 4].map((value) => (
                            <option key={value} value={value}>
                                {value}
                            </option>
                        ))}
                    </select>
                </label>
                <button
                    disabled={!idle || !!s.clientId}
                    onClick={() => void c.start(kind, batch)}
                >
                    Start scripted comparison
                </button>
            </div>
            <h3>Current run</h3>
            <p role="status">
                {s.pending
                    ? `Pending ${s.pending.action}${s.pending.operationId === null ? " · operation not acknowledged" : ` · operation ${s.pending.operationId}`}`
                    : s.uncertain
                      ? "Acknowledgement unknown. Check this exact client; no automatic retry or resume."
                      : status
                        ? `Phase: ${status.phase.replaceAll("_", " ")}`
                        : "No comparison is open."}
            </p>
            {s.error && (
                <p role="alert" className="error">
                    Comparison: {s.error}.
                </p>
            )}
            {status && (
                <>
                    <dl>
                        <dt>Kind</dt>
                        <dd>{status.comparison_kind}</dd>
                        <dt>Last verified completed scenes</dt>
                        <dd>
                            {status.source_matches === null
                                ? "Not verified"
                                : `${status.completed_scenes} / 4`}
                        </dd>
                        <dt>Last verified completion</dt>
                        <dd>
                            {status.source_matches === null
                                ? "Not verified"
                                : status.completed
                                  ? "Yes; quality remains unreviewed"
                                  : "No"}
                        </dd>
                        <dt>Verified report ready</dt>
                        <dd>{status.report_ready ? "Yes" : "Not yet"}</dd>
                        <dt>Source matching</dt>
                        <dd>
                            {status.source_matches === null
                                ? "Not verified"
                                : status.source_matches
                                  ? "Current source"
                                  : "Historical or mismatched source; resume may be refused"}
                        </dd>
                        <dt>Worker running</dt>
                        <dd>
                            {status.running
                                ? "Yes · native owner still active"
                                : "No running work reported"}
                        </dd>
                        <dt>Last admitted operation</dt>
                        <dd>{status.operation_id ?? "Not admitted"}</dd>
                    </dl>
                    <p className="hash-value">
                        Run {status.run_id} · client {status.client_id}
                    </p>
                    {status.phase === "closed" && (
                        <p>
                            Presentation access is closed. A draining worker
                            remains owned by Rust; this is not a cleanup
                            guarantee.
                        </p>
                    )}
                </>
            )}
            <div
                className="comparison-controls"
                role="group"
                aria-label="Comparison status and continuation"
            >
                <button
                    disabled={!s.allowed || !s.clientId || !!s.pending}
                    onClick={() => void c.lookup()}
                >
                    Look up exact client
                </button>
                <button
                    disabled={
                        !s.allowed ||
                        s.busy ||
                        s.uncertain ||
                        !status ||
                        status.phase === "closed"
                    }
                    onClick={() => void c.status()}
                >
                    Check status
                </button>
                <button
                    disabled={
                        !idle ||
                        !status ||
                        status.phase === "closed" ||
                        status.source_matches === false
                    }
                    onClick={() => void c.resume(batch)}
                >
                    Resume next chunk explicitly
                </button>
                <button
                    disabled={
                        !s.allowed ||
                        s.uncertain ||
                        !status?.running ||
                        !status.operation_id ||
                        status.phase === "closed"
                    }
                    onClick={() => void c.cancel()}
                >
                    Stop at boundary
                </button>
                <button
                    disabled={!s.clientId && !s.uncertain && !status}
                    onClick={() => void c.close()}
                >
                    Close captured access
                </button>
            </div>
            <p>
                Status, lookup and opening saved metadata never start or resume
                inference. Stop requests take effect at a shared boundary;
                accepted work is retained.
            </p>
            <p>
                Counts describe the last verified report. Close an open report
                in the reader before resuming its comparison.
            </p>
            <h3>Saved comparisons</h3>
            <div className="comparison-controls">
                <button disabled={!idle} onClick={() => void c.loadCatalog()}>
                    Refresh saved metadata
                </button>
                <label className="comparison-saved-run">
                    Saved run{" "}
                    <select
                        aria-label="Saved full comparison"
                        value={savedId}
                        disabled={!idle}
                        onChange={(event) => {
                            if (!c.get().busy) setSavedId(event.target.value);
                        }}
                    >
                        <option value="">Choose saved metadata</option>
                        {(s.allowed ? (s.catalog?.runs ?? []) : []).map(
                            (run) => (
                                <option key={run.run_id} value={run.run_id}>
                                    {run.comparison_kind} · {run.run_id}
                                </option>
                            ),
                        )}
                    </select>
                </label>
                <button
                    disabled={
                        !idle ||
                        !s.catalog?.runs.some((run) => run.run_id === savedId)
                    }
                    onClick={() => void c.open(savedId)}
                >
                    Open saved comparison
                </button>
            </div>
            {s.allowed && s.catalog?.runs.length === 0 && (
                <p>No saved run metadata was reported.</p>
            )}
            <p>
                The catalog is native-owned metadata, not a verified report or a
                quality result.
            </p>
            <h3>Inspect results</h3>
            <button
                disabled={!s.allowed || s.busy || !ready}
                onClick={() => {
                    const id = canInspect();
                    if (id) void onInspect(id);
                }}
            >
                Inspect report · asks permission
            </button>
            <p>
                Inspection opens the existing read-only reader with independent
                native spoiler consent. Observer lenses do not change this run's
                execution actor, identity or permissions.
            </p>
        </section>
    );
}
