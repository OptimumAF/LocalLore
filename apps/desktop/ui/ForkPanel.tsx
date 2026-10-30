import { useEffect, useState, useSyncExternalStore } from "react";
import type { ForkController } from "./fork-controller";
import type { Controller } from "./controller";
import type { TimelineContext } from "./timeline-model";
import { resumeTimeline, timelineContext } from "./timeline-controller";
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
        [shown, setShown] = useState(!!s.request),
        [openError, setOpenError] = useState<string | null>(null);
    useEffect(() => {
        setBoundary(context?.revision ?? 0);
    }, [context?.session, context?.scope.story, context?.scope.branch,
        context?.revision, context?.observer, context?.view, context?.persistent]);
    useEffect(() => {
        setOpenError(null);
    }, [context?.session, context?.scope.story, context?.scope.branch,
        context?.revision, context?.observer, context?.view, context?.persistent,
        s.request, s.result]);
    useEffect(() => {
        if (s.request) setShown(true);
    }, [s.request]);
    if (!context || !fork.matchesContext(context) ||
        !fork.matchesContext(timelineContext(gameplay))) return null;
    // Event callbacks belong to this exact render and gameplay selection. A
    // retained callback cannot act on a replacement request or operation.
    const currentContext = () => fork.matchesContext(context) &&
        fork.matchesContext(timelineContext(gameplay));
    const current = () => fork.get() === s && currentContext();
    const catalog = s.boundaryCatalog;
    const boundaries = catalog?.boundaries ?? [];
    const canPrepare = !!catalog && !s.boundaryBusy && !s.boundaryError &&
        !s.busy && !s.admissionBlocked && context.persistent &&
        !["pending", "uncertain"].includes(s.status);
    const sameParent =
        !!s.request && sameScope(s.request.parent, context.scope);
    const receipt = gameplay.receipt();
    if (!shown)
        return (
            <button onClick={() => {
                if (!current()) return;
                setShown(true);
                if (current()) void fork.refreshBoundaries(context);
            }}>
                {s.request
                    ? "Timeline creation & recovery"
                    : "Create alternate timeline"}
            </button>
        );
    return (
        <section className="fork-panel" aria-labelledby="fork-title">
            <div className="panel-heading">
                <h2 id="fork-title">Alternate timeline</h2>
                <button onClick={() => {
                    if (current()) setShown(false);
                }} disabled={s.busy}>
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
            <p className="fork-receipt muted">
                Selected player receipt:{" "}
                {receipt ? (
                    <>
                        <code>{receipt.request.turn}</code> · accepted revision{" "}
                        {receipt.events.at(-1)?.sequence} · original scope{" "}
                        <code>
                            {receipt.request.scope.story} /{" "}
                            {receipt.request.scope.branch}
                        </code>
                        .
                    </>
                ) : (
                    "No accepted receipt selected."
                )}
            </p>
            <button onClick={() => {
                if (current()) void fork.refreshBoundaries(context);
            }}>
                Refresh completed boundaries
            </button>
            {s.boundaryBusy ? (
                <p role="status">Loading completed boundaries.</p>
            ) : s.boundaryError ? (
                <p role="alert">Completed boundaries: {s.boundaryError}. Refresh to retry.</p>
            ) : !catalog ? (
                <p role="status">Completed boundaries are unavailable until refreshed.</p>
            ) : (
                <p role="status">Complete boundary list for parent head {catalog.head}.</p>
            )}
            {s.admissionBlocked && (
                <p role="status">Timeline creation is paused while gameplay is pending or its outcome is uncertain.</p>
            )}
            {!context.persistent ? (
                <p role="status">
                    Durable timeline creation is unavailable for in-memory
                    progress.
                </p>
            ) : (
                <>
                    <label>
                        Boundary for next new request
                        <select
                            aria-label="Fork completed boundary"
                            value={boundary}
                            disabled={!canPrepare}
                            onChange={(e) => {
                                if (!current() || !canPrepare) return;
                                const value = Number(e.target.value);
                                if (!current() || !boundaries.includes(value)) return;
                                setBoundary(value);
                                if (current()) fork.setConsent(false);
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
                        disabled={!canPrepare}
                        onClick={() => {
                            if (!current() || !canPrepare || !catalog) return;
                            const child = crypto.randomUUID();
                            if (current()) fork.prepareFromCatalog(boundary, child, context, catalog);
                        }}
                    >
                        Prepare new timeline
                    </button>
                </>
            )}
            {s.request && (
                <>
                    <h3>Exact fork request</h3>
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
                                    checked={s.consent}
                                    disabled={s.busy || s.admissionBlocked}
                                    onChange={(e) => {
                                        if (!current() || s.busy || s.admissionBlocked || !s.request) return;
                                        const checked = e.target.checked;
                                        if (current()) fork.setConsent(checked);
                                    }}
                                />
                                Create this new timeline and preserve the
                                original.
                            </label>
                            <button
                                className="primary"
                                disabled={s.busy || !s.consent || s.admissionBlocked}
                                onClick={() => {
                                    if (current() && s.request) void fork.confirmExact(s.request, context);
                                }}
                            >
                                {s.status === "prepared"
                                    ? "Confirm new timeline"
                                    : "Retry exact original fork"}
                            </button>
                        </>
                    )}
                    <button
                        disabled={s.busy || !sameParent || !context.persistent}
                        onClick={() => {
                            if (current() && s.request && sameParent && context.persistent)
                                void fork.lookup();
                        }}
                    >
                        Check saved child only
                    </button>
                    {s.busy && (
                        <button onClick={() => {
                            if (current() && s.busy) void fork.cancel();
                        }}>
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
                            if (!current() || !s.result || s.busy) return;
                            const result = s.result;
                            setOpenError(null);
                            if (!current()) return;
                            void resumeTimeline(
                                gameplay,
                                result.scope,
                            ).catch(() => {
                                if (currentContext() && fork.get().result === result)
                                    setOpenError(
                                    "The saved child could not be opened. Check the active story and retry explicitly.",
                                    );
                            });
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
