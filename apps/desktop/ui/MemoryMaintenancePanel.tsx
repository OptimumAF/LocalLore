import { useSyncExternalStore } from "react";
import type {
    MemoryContext,
    MemoryMaintenanceController,
} from "./memory-maintenance-controller";

export function MemoryMaintenancePanel({
    maintenance,
    context,
    receipt,
}: {
    maintenance: MemoryMaintenanceController;
    context: MemoryContext | null;
    receipt?: {turn:string;revision:number};
}) {
    const s = useSyncExternalStore(
        maintenance.subscribe,
        maintenance.get,
        maintenance.get,
    );
    if (!context || !maintenance.matchesContext(context)) return null;
    const job = s.reply?.maintenance.job;
    return (
        <section
            className="memory-maintenance-panel"
            aria-labelledby="memory-maintenance-title"
            style={{ minWidth: 0, overflowWrap: "anywhere" }}
        >
            <h2 id="memory-maintenance-title">Derived memory</h2>
            <p>
                Summaries and search data derived from accepted history. These
                controls do not change events or what characters know.
            </p>
            <dl>
                <dt>Selected story / timeline</dt>
                <dd>
                    <code>
                        {context.scope.story} / {context.scope.branch}
                    </code>
                </dd>
                <dt>Accepted revision</dt>
                <dd>{context.expected_head}</dd>
                <dt>Player</dt>
                <dd>
                    <code>{context.player}</code>
                </dd>
                <dt>Inspection observer</dt>
                <dd><code>{context.observer}</code> ({context.view})</dd>
                <dt>Job status</dt>
                <dd>{job?.status ?? (s.reply ? "No job" : "Not read")}</dd>
                {job && (
                    <>
                        <dt>Processed through revision</dt>
                        <dd>
                            {job.next_from} of {job.basis_revision}
                        </dd>
                        {job.last_error && (
                            <>
                                <dt>Recorded limit / failure</dt>
                                <dd>
                                    {job.last_error}
                                    {job.status === "stale"
                                        ? " (from the earlier job)"
                                        : ""}
                                </dd>
                            </>
                        )}
                    </>
                )}
                <dt>Operation</dt>
                <dd>
                    {s.busy
                        ? "Waiting for acknowledgement"
                        : s.operation?.running
                          ? `${s.action} — ${s.operation.phase}`
                          : s.uncertain
                            ? "Outcome unknown"
                            : "Idle"}
                </dd>
            </dl>
            {receipt&&<p className="memory-receipt">Displayed player receipt: <code>{receipt.turn}</code>, accepted revision {receipt.revision}.</p>}
            {(!context.persistent ||
                (context.view !== "play" &&
                    context.observer !== context.player)) && (
                <p>
                    Open a saved story in the player view to use these controls.
                    Inspector access does not grant maintenance access.
                </p>
            )}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                <button
                    disabled={!maintenance.can("status")}
                    onClick={() => void maintenance.act("status")}
                >
                    Read memory status
                </button>
                <button
                    disabled={!maintenance.can("admit")}
                    onClick={() => void maintenance.act("admit")}
                >
                    Prepare derived memory
                </button>
                <button
                    disabled={!maintenance.can("step")}
                    onClick={() => void maintenance.act("step")}
                >
                    Process one chunk
                </button>
                <button
                    disabled={!maintenance.can("cancel")}
                    onClick={() => void maintenance.act("cancel")}
                >
                    Cancel memory job
                </button>
                <button
                    disabled={!maintenance.can("prune")}
                    onClick={() => void maintenance.act("prune")}
                >
                    Prune finished job
                </button>
                <button
                    disabled={s.busy || !s.operation?.running}
                    onClick={() => void maintenance.stop()}
                >
                    Stop current operation
                </button>
            </div>
            <label style={{ display: "block", marginBlock: "0.75rem" }}>
                <input
                    type="checkbox"
                    checked={s.consent}
                    disabled={s.busy || !!s.operation?.running || s.uncertain}
                    onChange={(e) => maintenance.consent(e.target.checked)}
                />{" "}
                I approve preparing derived data or pruning this finished job.
                Canonical history is preserved.
            </label>
            <p>
                Each step processes one bounded chunk. Cancelled jobs require
                explicit pruning and a new admission to restart. Model-generated
                summaries are unavailable.
            </p>
            {job?.status === "stale" && (
                <p>
                    Cancel this stale job first, then read its saved outcome
                    before pruning. A stale view alone does not mark a pending
                    job finished.
                </p>
            )}
            {s.error && <p role="alert">Memory operation: {s.error}</p>}
            {s.notice && <p role="status">{s.notice}</p>}
            {s.uncertain && (
                <p role="status">
                    The outcome is unknown. Only status recovery is available;
                    no maintenance action will be repeated automatically.
                </p>
            )}
        </section>
    );
}
