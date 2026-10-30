import { useSyncExternalStore } from "react";
import { sameScope } from "./model";
import type { TimelineController } from "./timeline-controller";
import { timelineAncestry } from "./timeline-model";
import type { TimelineContext } from "./timeline-model";

export function TimelinePanel({
    timeline,
    context,
}: {
    timeline: TimelineController;
    context: TimelineContext | null;
}) {
    const s = useSyncExternalStore(
        timeline.subscribe,
        timeline.get,
        timeline.get,
    );
    if (!timeline.matchesContext(context)) return null;
    if (!s.shown)
        return (
            <button
                onClick={() => {
                    if (timeline.matchesContext(context)) void timeline.show();
                }}
            >
                Saved timelines
            </button>
        );
    return (
        <section
            className="timeline-panel"
            aria-labelledby="timeline-title"
            style={{ minWidth: 0, overflowWrap: "anywhere" }}
        >
            <div className="panel-heading">
                <h2 id="timeline-title">Saved timelines</h2>
                <button
                    onClick={() => {
                        if (timeline.matchesContext(context)) timeline.hide();
                    }}
                >
                    Close saved timelines
                </button>
            </div>
            <p>
                See where each saved timeline began. Opening a timeline keeps
                its original history intact and preserves what characters know.
            </p>
            <p>
                Alternate timeline creation preserves the original. Replacing
                committed history means starting a new timeline before that
                turn; downstream choices are never replayed automatically.
                Saved drafts stay uncommitted.
            </p>
            <button
                disabled={s.busy || !context?.persistent}
                onClick={() => {
                    if (timeline.matchesContext(context))
                        void timeline.refresh();
                }}
            >
                Refresh timeline catalog
            </button>
            {s.busy && (
                <p role="status">
                    {s.status === "resuming"
                        ? "Resuming timeline…"
                        : "Loading timeline metadata…"}
                </p>
            )}
            {s.error && <p role="alert">Timeline request: {s.error}</p>}
            {s.notice && <p role="status">{s.notice}</p>}
            {s.catalog && (
                <>
                    <h3>{s.catalog.title}</h3>
                    <p>
                        Story <code>{s.catalog.story_id}</code> · catalog
                        version {s.catalog.version}
                    </p>
                    <ul aria-label="Saved timeline metadata">
                        {s.catalog.branches.map((row) => {
                            const current =
                                !!context &&
                                sameScope(context.scope, row.scope);
                            return (
                                <li key={row.scope.branch}>
                                    <h4>
                                        <code>{row.scope.branch}</code>
                                        {row.scope.branch ===
                                        s.catalog!.root_branch
                                            ? " · root"
                                            : ""}
                                        {current ? " · selected" : ""}
                                    </h4>
                                    <p>
                                        Ancestry:{" "}
                                        {timelineAncestry(s.catalog!, row).map(
                                            (id, i) => (
                                                <span key={id}>
                                                    {i > 0 ? " → " : ""}
                                                    <code>{id}</code>
                                                </span>
                                            ),
                                        )}
                                    </p>
                                    <p>
                                        {row.parent_branch === null ? (
                                            "Original root timeline; no fork point."
                                        ) : (
                                            <>
                                                Forked from{" "}
                                                <code>{row.parent_branch}</code>{" "}
                                                at accepted revision{" "}
                                                {row.fork_revision}.
                                            </>
                                        )}
                                    </p>
                                    <p>
                                        Catalogued head: {row.revision} · saved
                                        uncommitted requests: {row.drafts}.
                                    </p>
                                    <p>
                                        {row.retired
                                            ? "Retired · retained ancestry only; cannot resume."
                                            : "Active saved timeline."}
                                    </p>
                                    <button
                                        disabled={
                                            s.busy || row.retired || current
                                        }
                                        onClick={() => {
                                            if (timeline.matchesContext(context))
                                                void timeline.select(
                                                    row.scope.branch,
                                                );
                                        }}
                                    >
                                        {row.retired
                                            ? `Retired timeline ${row.scope.branch}`
                                            : current
                                              ? `Selected timeline ${row.scope.branch}`
                                              : `Resume timeline ${row.scope.branch}`}
                                    </button>
                                </li>
                            );
                        })}
                    </ul>
                </>
            )}
        </section>
    );
}
