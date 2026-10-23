import { useEffect, useState, useSyncExternalStore } from "react";
import type { ForkController } from "./fork-controller";
import type { Controller } from "./controller";
import type { TimelineContext } from "./timeline-model";
import { resumeTimeline } from "./timeline-controller";
import { sameScope } from "./model";

export function ForkPanel({
    fork,
    gameplay,
    context,
}: {
    fork: ForkController;
    gameplay: Controller;
    context: TimelineContext | null;
}) {
    const s = useSyncExternalStore(fork.subscribe, fork.get, fork.get);
    const [boundary, setBoundary] = useState(context?.revision ?? 0),
        [consent, setConsent] = useState(false),
        [shown, setShown] = useState(!!s.request),
        [openError, setOpenError] = useState<string | null>(null);
    useEffect(() => {
        setBoundary(context?.revision ?? 0);
        setConsent(false);
        setOpenError(null);
    }, [context?.session, context?.revision, context?.observer, context?.view]);
    useEffect(() => {
        setConsent(false);
        if (s.request) setShown(true);
    }, [s.request]);
    if (!context) return null;
    const boundaries = [
        ...new Set([
            0,
            ...(gameplay.get().play?.receipts ?? []).map(
                (r) => r.events.at(-1)?.sequence ?? 0,
            ),
        ]),
    ].sort((a, b) => a - b);
    const sameParent =
        !!s.request && sameScope(s.request.parent, context.scope);
    if (!shown)
        return (
            <button onClick={() => setShown(true)}>
                {s.request
                    ? "Timeline creation & recovery"
                    : "Create alternate timeline"}
            </button>
        );
    return (
        <section className="fork-panel" aria-labelledby="fork-title">
            <div className="panel-heading">
                <h2 id="fork-title">Alternate timeline</h2>
                <button onClick={() => setShown(false)} disabled={s.busy}>
                    Close timeline creation
                </button>
            </div>
            <p>
                Keep this timeline intact. A new timeline inherits accepted
                history through the chosen boundary; later choices stay here.
            </p>
            <p>
                Selected story <code>{context.scope.story}</code> · parent{" "}
                <code>{context.scope.branch}</code> · head {context.revision} ·
                observer <code>{context.observer}</code>.
            </p>
            {!context.persistent ? (
                <p role="status">
                    Durable timeline creation is unavailable for in-memory
                    progress.
                </p>
            ) : (
                <>
                    <label>
                        Completed boundary
                        <select
                            aria-label="Fork completed boundary"
                            value={boundary}
                            disabled={s.busy}
                            onChange={(e) => {
                                setBoundary(Number(e.target.value));
                                setConsent(false);
                            }}
                        >
                            {boundaries.map((n) => (
                                <option key={n} value={n}>
                                    {n === 0
                                        ? "Before first accepted turn"
                                        : `After accepted revision ${n}`}
                                </option>
                            ))}
                        </select>
                    </label>
                    <button
                        disabled={
                            s.busy ||
                            ["pending", "uncertain"].includes(s.status)
                        }
                        onClick={() =>
                            fork.prepare(boundary, crypto.randomUUID())
                        }
                    >
                        Prepare new timeline
                    </button>
                </>
            )}
            {s.request && (
                <>
                    <dl>
                        <dt>Original parent</dt>
                        <dd>
                            <code>
                                {s.request.parent.story} /{" "}
                                {s.request.parent.branch}
                            </code>
                        </dd>
                        <dt>Parent head / fork point</dt>
                        <dd>
                            {s.request.expected_parent_revision} /{" "}
                            {s.request.at_revision}
                        </dd>
                        <dt>Stable child identity</dt>
                        <dd>
                            <code>{s.request.child_branch}</code>
                        </dd>
                    </dl>
                    <p className="muted">
                        This recovery identity is saved locally before
                        confirmation. Restart recovery only looks up an existing
                        child; it never recreates one automatically.
                    </p>
                    {!s.lookupOnly && sameParent && s.status !== "complete" && (
                        <>
                            <label className="fork-consent">
                                <input
                                    type="checkbox"
                                    checked={consent}
                                    disabled={s.busy}
                                    onChange={(e) =>
                                        setConsent(e.target.checked)
                                    }
                                />
                                Create this new timeline and preserve the
                                original.
                            </label>
                            <button
                                className="primary"
                                disabled={s.busy || !consent}
                                onClick={() => void fork.confirm(consent)}
                            >
                                {s.status === "prepared"
                                    ? "Confirm new timeline"
                                    : "Retry exact original fork"}
                            </button>
                        </>
                    )}
                    <button
                        disabled={s.busy || !sameParent || !context.persistent}
                        onClick={() => void fork.lookup()}
                    >
                        Check saved child only
                    </button>
                    {s.busy && (
                        <button onClick={() => void fork.cancel()}>
                            Cancel pending fork
                        </button>
                    )}
                    <p role="status" className="fork-operation">
                        Fork status: {s.status}
                        {s.operation !== null
                            ? ` · operation ${s.operation}`
                            : ""}
                        {s.lookupOnly ? " · lookup-only recovery" : ""}
                    </p>
                </>
            )}
            {s.error && <p role="alert">Timeline creation: {s.error}</p>}
            {s.notice && <p role="status">{s.notice}</p>}
            {s.result && (
                <div className="fork-result">
                    <h3>Saved child confirmed</h3>
                    <p>
                        <code>{s.result.scope.branch}</code> · fork revision{" "}
                        {s.result.fork_revision} · current child head{" "}
                        {s.result.head_revision}.
                    </p>
                    <button
                        disabled={s.busy}
                        onClick={() => {
                            setOpenError(null);
                            void resumeTimeline(
                                gameplay,
                                s.result!.scope,
                            ).catch(() =>
                                setOpenError(
                                    "The saved child could not be opened. Check the active story and retry explicitly.",
                                ),
                            );
                        }}
                    >
                        Open confirmed child
                    </button>
                </div>
            )}
            {openError && <p role="alert">{openError}</p>}
        </section>
    );
}
