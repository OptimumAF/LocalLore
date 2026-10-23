import { useSyncExternalStore } from "react";
import { Controller } from "./controller";
import { ModelPanel } from "./ModelPanel";
import { InspectionPanel } from "./InspectionPanel";
import { PAGE_SIZE, composerShortcut } from "./model";
import type { Action, FakeMode, Receipt } from "./model";
const actions: Record<Action, string> = {
    give: "Give last potion to Mira",
    wait: "Wait one tide tick",
    ability: "Attempt unlearned teleport",
    dialogue: "Say draft aloud to Mira",
};
function intent(r: Receipt) {
    return r.request.intent.kind === "free_text"
        ? r.request.intent.value.text
        : r.request.intent.kind === "dialogue"
          ? r.request.intent.value.text
          : r.request.intent.kind === "actions"
            ? r.request.intent.value
                  .map((c) => c.op.replaceAll("_", " "))
                  .join(", ")
            : r.request.intent.kind;
}
export function App({ controller: c }: { controller: Controller }) {
    const s = useSyncExternalStore(c.subscribe, c.get),
        selected = c.selected(),
        receipt = c.receipt();
    const receipts = s.play?.receipts ?? [],
        rows = receipts.slice(s.page * PAGE_SIZE, (s.page + 1) * PAGE_SIZE);
    return (
        <div
            className={`app text-${s.textScale} side-${s.sidebarSize} detail-${s.inspectorSize}`}
        >
            <a href="#composer" className="skip">
                Skip to composer
            </a>
            <header className="brandbar">
                <strong className="brand">LocalLore</strong>
                <nav className="mode-tabs" aria-label="Workspace mode">
                    <button
                        aria-pressed={s.view === "play"}
                        onClick={() => c.setView("play")}
                    >
                        Play
                    </button>
                    <button
                        aria-pressed={s.view === "lab"}
                        onClick={() => c.setView("lab")}
                    >
                        Story Lab · spoilers
                    </button>
                </nav>
                <span className="limitation">
                    Local Rust |{" "}
                    {s.playMode === "local"
                        ? "Experimental local CPU"
                        : "Fake fixture inference"}{" "}
                    |{" "}
                    {s.workspace
                        ? "Saved locally"
                        : s.ephemeral
                          ? "In-memory only · not saved"
                          : s.starting
                            ? "Opening storage..."
                            : "Storage unavailable"}
                </span>
            </header>
            <div className={`workspace ${s.inspectorOpen ? "" : "collapsed"}`}>
                <aside className="sidebar" aria-label="Story sessions">
                    <h2>
                        {s.ephemeral ? "Fixture sessions" : "Saved stories"}
                    </h2>
                    {s.workspace?.stories.map((story) => (
                        <button
                            className="session"
                            key={`${story.scope.story}/${story.scope.branch}`}
                            onClick={() => void c.resume(story.scope)}
                            disabled={s.starting}
                        >
                            <span>{story.title}</span>
                            <small>
                                {story.scope.story} / {story.scope.branch} |
                                revision {story.revision}
                            </small>
                        </button>
                    ))}
                    <div className="export-actions">
                        <button onClick={() => c.showModel()}>
                            Local model management
                        </button>
                        <button onClick={() => c.showExports()}>
                            Inspection snapshots
                        </button>
                        <button onClick={() => void c.revealStorage()}>
                            Reveal storage in app
                        </button>
                    </div>
                    <h3>Open in this window</h3>
                    <button
                        className="new"
                        disabled={
                            s.sessions.length >= 4 ||
                            s.starting ||
                            (!s.workspace && !s.ephemeral)
                        }
                        onClick={() => void c.create()}
                    >
                        ＋ New Lantern Quay
                    </button>
                    <div className="session-list">
                        {s.sessions.map((session) => (
                            <button
                                className="session"
                                key={session.id}
                                aria-current={session.id === s.selectedId}
                                onClick={() => void c.switchSession(session.id)}
                            >
                                <span>{session.name}</span>
                                <small>
                                    {session.scope.branch} · revision{" "}
                                    {session.revision}
                                </small>
                            </button>
                        ))}
                    </div>
                    <p>
                        {s.ephemeral
                            ? "Progress stays in memory. Closing or resetting discards this fixture session; nothing is saved."
                            : "Close releases this window's session; the saved story remains. New and Reset create a separate saved story."}
                    </p>
                    <p>
                        Unsubmitted composer text stays in this session only.
                        Arbitrary story creation remains unavailable. Local
                        inference is an explicit experimental CPU profile.
                    </p>
                    {s.workspace && (
                        <details>
                            <summary>Saved workspace</summary>
                            <p className="storage-path">
                                {s.workspace.location}
                            </p>
                            <p>
                                Schema {s.workspace.schema_version} | Contract
                                domain-v1 | Rules{" "}
                                {s.play?.rules ?? "unavailable"} | Canonical
                                receipts and validated replay
                            </p>
                        </details>
                    )}
                    {!s.workspace && !s.ephemeral && !s.starting && (
                        <button onClick={() => void c.start()}>
                            Retry opening saved workspace
                        </button>
                    )}
                    <details className="layout-controls">
                        <summary>Layout & text</summary>
                        <label>
                            Session pane width
                            <input
                                type="range"
                                min="0"
                                max="2"
                                value={s.sidebarSize}
                                onChange={(e) =>
                                    c.layout(
                                        +e.target.value,
                                        s.inspectorSize,
                                        s.textScale,
                                    )
                                }
                            />
                        </label>
                        <label>
                            Inspector width
                            <input
                                type="range"
                                min="0"
                                max="2"
                                value={s.inspectorSize}
                                onChange={(e) =>
                                    c.layout(
                                        s.sidebarSize,
                                        +e.target.value,
                                        s.textScale,
                                    )
                                }
                            />
                        </label>
                        <label>
                            Text size
                            <select
                                value={s.textScale}
                                onChange={(e) =>
                                    c.layout(
                                        s.sidebarSize,
                                        s.inspectorSize,
                                        +e.target.value,
                                    )
                                }
                            >
                                {[100, 125, 150, 200].map((n) => (
                                    <option key={n} value={n}>
                                        {n}%
                                    </option>
                                ))}
                            </select>
                        </label>
                    </details>
                </aside>
                <main className="play">
                    <div className="scene-head">
                        <div className="topline">
                            <div>
                                <h1>
                                    {selected?.name ?? "Open an original scene"}
                                </h1>
                                <small>
                                    {selected
                                        ? `${selected.scope.story} / ${selected.scope.branch}`
                                        : "Choose New Lantern Quay to begin."}
                                </small>
                            </div>
                            <button
                                aria-expanded={s.inspectorOpen}
                                onClick={() => c.setInspector(!s.inspectorOpen)}
                            >
                                {s.inspectorOpen
                                    ? "Hide inspector"
                                    : "Show inspector"}
                            </button>
                        </div>
                        <div
                            className="scene-status"
                            aria-label="Engine status"
                        >
                            <span>Revision {s.play?.revision ?? "—"}</span>
                            <span>Rules: {s.play?.rules ?? "unavailable"}</span>
                            <span>
                                Provider:{" "}
                                {s.playMode === "local"
                                    ? s.model?.loaded
                                        ? "Qwen3 local CPU (experimental)"
                                        : "Local model unavailable"
                                    : "deterministic fake v1"}
                            </span>
                            <span>
                                Turn:{" "}
                                {s.pending?.stage ??
                                    s.turnStatus?.phase ??
                                    "idle"}
                            </span>
                        </div>
                    </div>
                    {s.view === "lab" && (
                        <div className="lab-warning" role="note">
                            Story Lab shows spoilers. Its inspection lens does
                            not change character knowledge or permissions.
                        </div>
                    )}
                    <ModelPanel controller={c} state={s} />
                    <InspectionPanel controller={c} state={s} />
                    <div
                        className="transcript"
                        aria-label="Finalized transcript"
                        aria-live="polite"
                    >
                        {!rows.length && (
                            <div className="empty">
                                <h2>Lantern Quay</h2>
                                <p>
                                    {s.playMode === "local"
                                        ? "Write an attempted action or speak dialogue through the local director and narrator. Only approved engine receipts enter this transcript."
                                        : "Exercise the original fixture with explicit actions or dialogue. Only accepted engine receipts enter this transcript."}
                                </p>
                                <p className="muted">
                                    Rowan has one potion. Mira is nearby; Sable
                                    is unwitnessed.
                                </p>
                            </div>
                        )}
                        {rows.map((r) => (
                            <article className="turn" key={r.request.turn}>
                                <div className="turn-head">
                                    <small>
                                        {r.request.turn} · accepted revision{" "}
                                        {r.events.at(-1)?.sequence}
                                    </small>
                                    <button
                                        onClick={() =>
                                            c.selectReceipt(r.request.turn)
                                        }
                                        aria-label={`Inspect receipt ${r.request.turn}`}
                                    >
                                        Inspect receipt
                                    </button>
                                </div>
                                <p className="intent">You: {intent(r)}</p>
                                <p>{r.narration}</p>
                                {r.play && (
                                    <p className="muted">
                                        Local play v{r.play.version} -{" "}
                                        {r.play.fallback
                                            ? "Engine fallback narration after validation"
                                            : "Generated narration accepted by shared policy"}
                                        ; repairs {r.play.repairs}. Profile{" "}
                                        {String(r.play.profile.id)}
                                    </p>
                                )}
                            </article>
                        ))}
                    </div>
                    {receipts.length > PAGE_SIZE && (
                        <nav
                            className="pagination"
                            aria-label="Transcript pages"
                        >
                            <button
                                disabled={s.page === 0}
                                onClick={() => c.page(s.page - 1)}
                            >
                                Previous
                            </button>
                            <span>
                                Page {s.page + 1} /{" "}
                                {Math.ceil(receipts.length / PAGE_SIZE)} ·{" "}
                                {receipts.length} accepted turns
                            </span>
                            <button
                                disabled={
                                    (s.page + 1) * PAGE_SIZE >= receipts.length
                                }
                                onClick={() => c.page(s.page + 1)}
                            >
                                Next
                            </button>
                        </nav>
                    )}
                    {s.visibleError && (
                        <div className="message error" role="alert">
                            {s.visibleError} ·{" "}
                            {s.visibleError === "TransportUnknown"
                                ? "Outcome uncertain. Retry checks the original turn; no rollback is assumed."
                                : "No new transcript entry was added by this failed attempt."}
                        </div>
                    )}
                    <div className="message notice" role="status">
                        {s.pending ? (
                            <span className="pending">
                                {s.pending.stage} · {s.pending.turn} - Not
                                canonical until accepted
                            </span>
                        ) : (
                            s.notice ||
                            (s.turnStatus?.phase === "cancelled"
                                ? "Cancelled before commit. Draft preserved."
                                : "")
                        )}
                    </div>
                    <form
                        id="composer"
                        className="compose"
                        onSubmit={(e) => {
                            e.preventDefault();
                            void c.send();
                        }}
                    >
                        <label>
                            Inference profile{" "}
                            <select
                                value={s.playMode}
                                disabled={!!s.pending}
                                onChange={(e) =>
                                    c.setPlayMode(
                                        e.target.value as "fixture" | "local",
                                    )
                                }
                            >
                                <option value="fixture">
                                    Deterministic fake fixture
                                </option>
                                <option
                                    value="local"
                                    disabled={!s.model?.loaded}
                                >
                                    Experimental local Qwen CPU
                                </option>
                            </select>
                        </label>
                        {s.playMode === "local" ? (
                            <label>
                                Player input{" "}
                                <select
                                    value={s.inputKind}
                                    disabled={!!s.pending}
                                    onChange={(e) =>
                                        c.setInputKind(
                                            e.target.value as
                                                "action" | "dialogue",
                                        )
                                    }
                                >
                                    <option value="action">
                                        Attempt an action
                                    </option>
                                    <option value="dialogue">
                                        Speak dialogue
                                    </option>
                                </select>
                            </label>
                        ) : (
                            <div className="compose-row">
                                <label>
                                    Explicit fixture action
                                    <select
                                        value={s.action}
                                        disabled={!!s.pending}
                                        onChange={(e) =>
                                            c.setAction(
                                                e.target.value as Action,
                                            )
                                        }
                                    >
                                        {Object.entries(actions).map(
                                            ([key, label]) => (
                                                <option key={key} value={key}>
                                                    {label}
                                                </option>
                                            ),
                                        )}
                                    </select>
                                </label>
                                <label>
                                    Fake provider behavior
                                    <select
                                        value={s.fakeMode}
                                        disabled={!!s.pending}
                                        onChange={(e) =>
                                            c.setFakeMode(
                                                e.target.value as FakeMode,
                                            )
                                        }
                                    >
                                        <option value="accepted">
                                            Accepted plumbing
                                        </option>
                                        <option value="delayed">
                                            Delayed plumbing
                                        </option>
                                        <option value="malformed">
                                            Malformed output
                                        </option>
                                        <option value="rejected">
                                            Invalid proposal
                                        </option>
                                        <option value="failed">
                                            Provider failure
                                        </option>
                                        <option value="cancelled">
                                            Provider cancellation
                                        </option>
                                    </select>
                                </label>
                            </div>
                        )}
                        <label className="sr-only" htmlFor="draft">
                            Dialogue draft
                        </label>
                        <textarea
                            id="draft"
                            value={s.draft}
                            maxLength={2048}
                            placeholder={
                                s.playMode === "local"
                                    ? "Describe an attempted action, or choose Dialogue to speak. Your text cannot grant author powers."
                                    : "Draft dialogue for Mira. Select Say draft aloud to submit it."
                            }
                            onChange={(e) => c.setDraft(e.target.value)}
                            onKeyDown={(e) => {
                                if (
                                    composerShortcut({
                                        key: e.key,
                                        shiftKey: e.shiftKey,
                                        isComposing: e.nativeEvent.isComposing,
                                    }) === "submit"
                                ) {
                                    e.preventDefault();
                                    if (!s.pending) void c.send();
                                }
                            }}
                        />
                        <p className="hint">
                            Enter submits the selected action · Shift+Enter adds
                            a newline. Pending generation is not canonical; only
                            finalized approved receipts change the story.
                            Dialogue never grants author powers.
                        </p>
                        <div className="send-row">
                            <button
                                className="primary"
                                disabled={!selected || !!s.pending}
                            >
                                Submit action
                            </button>
                            <button
                                type="button"
                                disabled={
                                    !s.pending ||
                                    s.pending.stage === "cancelling"
                                }
                                onClick={() => void c.cancel()}
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                disabled={
                                    !!s.pending ||
                                    !s.turnStatus ||
                                    s.turnStatus.phase === "committed"
                                }
                                onClick={() => void c.retry()}
                            >
                                Retry
                            </button>
                            <button
                                type="button"
                                disabled={!selected}
                                onClick={() => void c.reset()}
                            >
                                {s.ephemeral
                                    ? "Reset fixture"
                                    : "Reset as new story"}
                            </button>
                        </div>
                    </form>
                </main>
                {s.inspectorOpen && (
                    <aside
                        className="inspector"
                        aria-label="Revision inspector"
                    >
                        <div className="head">
                            <h2>
                                {s.view === "lab"
                                    ? "Story Lab inspector"
                                    : "Player & receipt"}
                            </h2>
                            <button
                                disabled={!receipt}
                                onClick={() =>
                                    void c.copyReceipt((text) =>
                                        navigator.clipboard.writeText(text),
                                    )
                                }
                            >
                                Copy receipt
                            </button>
                        </div>
                        <p className="scope">
                            {selected?.scope.story ?? "No session"} · revision{" "}
                            {s.play?.revision ?? "—"}
                        </p>
                        {s.view === "lab" && (
                            <label>
                                Inspection lens
                                <select
                                    value={s.observer}
                                    onChange={(e) =>
                                        c.setObserver(e.target.value)
                                    }
                                >
                                    <option value="omniscient">
                                        Omniscient developer
                                    </option>
                                    <option value="player">
                                        Rowan · player
                                    </option>
                                    <option value="mira">Mira</option>
                                    <option value="sable">
                                        Sable · unwitnessed
                                    </option>
                                </select>
                            </label>
                        )}
                        <section>
                            <h3>Player sheet</h3>
                            <dl>
                                <dt>Name</dt>
                                <dd>{s.play?.player.self_state.name ?? "—"}</dd>
                                <dt>Location</dt>
                                <dd>
                                    {s.play?.player.self_state.location ?? "—"}
                                </dd>
                                <dt>Energy</dt>
                                <dd>
                                    {s.play?.player.self_state.energy ?? "—"}
                                </dd>
                                <dt>Owned items</dt>
                                <dd>
                                    {Object.keys(s.play?.inventory ?? {}).join(
                                        ", ",
                                    ) || "None"}
                                </dd>
                            </dl>
                        </section>
                        <section>
                            <h3>Finalized receipt</h3>
                            {receipt ? (
                                <>
                                    <p className="scope">
                                        {receipt.request.turn} · revision{" "}
                                        {receipt.events.at(-1)?.sequence}
                                    </p>
                                    <details>
                                        <summary>
                                            Accepted events (
                                            {receipt.events.length})
                                        </summary>
                                        <pre tabIndex={0}>
                                            {JSON.stringify(
                                                receipt.events,
                                                null,
                                                2,
                                            )}
                                        </pre>
                                    </details>
                                    <details>
                                        <summary>Request & proposal</summary>
                                        <pre tabIndex={0}>
                                            {JSON.stringify(
                                                {
                                                    request: receipt.request,
                                                    proposal: receipt.proposal,
                                                },
                                                null,
                                                2,
                                            )}
                                        </pre>
                                    </details>
                                </>
                            ) : (
                                <p className="muted">No accepted turn yet.</p>
                            )}
                        </section>
                        <section>
                            <h3>
                                Latest state diff{" "}
                                {s.diffRevision === null
                                    ? ""
                                    : `→ r${s.diffRevision}`}
                            </h3>
                            <p className="muted">
                                Compared player snapshots from Rust.
                            </p>
                            <ul className="diff">
                                {s.diff.map((row) => (
                                    <li key={row.path}>
                                        <code>{row.path}</code>
                                        {JSON.stringify(row.before)} →{" "}
                                        {JSON.stringify(row.after)}
                                    </li>
                                ))}
                            </ul>
                        </section>
                        {s.view === "lab" && (
                            <section>
                                <h3>Scoped inspection</h3>
                                <p className="scope">
                                    {s.inspectionObserver ?? "Loading"} ·
                                    revision {s.inspectionRevision ?? "—"}
                                </p>
                                <pre tabIndex={0}>
                                    {s.inspection === null
                                        ? "No inspection snapshot."
                                        : JSON.stringify(s.inspection, null, 2)}
                                </pre>
                                <p className="muted">
                                    Summaries, retrieval traces and advanced
                                    memory views await their shared features.
                                </p>
                            </section>
                        )}
                        <button
                            className="danger"
                            disabled={!selected}
                            onClick={() => void c.closeSession()}
                        >
                            {s.ephemeral
                                ? "Close fixture session"
                                : "Close session | keep save"}
                        </button>
                    </aside>
                )}
            </div>
            <footer className="footer">
                <span>
                    {s.playMode === "local"
                        ? "Experimental local CPU"
                        : "Fake fixture inference"}{" "}
                    |{" "}
                    {s.workspace
                        ? "Accepted progress saved locally"
                        : s.ephemeral
                          ? "In-memory progress · lost on close"
                          : "Storage must open before play"}
                </span>
                <span>
                    {s.model?.loaded
                        ? "One local model loaded; no cloud fallback"
                        : "No model loaded; fake fixtures require explicit selection"}
                </span>
            </footer>
        </div>
    );
}
