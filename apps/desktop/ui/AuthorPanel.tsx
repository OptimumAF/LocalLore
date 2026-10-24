import { useEffect, useSyncExternalStore } from "react";
import type { AuthorController } from "./author-controller";
import {
    authorAvailable,
    type AuthorContext,
    type AuthorDraft,
} from "./author-model";

// Root owns navigation, native spoiler grant, broker retention and actual context.
export function AuthorPanel({
    author,
    context,
}: {
    author: AuthorController;
    context: AuthorContext | null;
}) {
    const state = useSyncExternalStore(
        author.subscribe,
        author.get,
        author.get,
    );
    useEffect(() => {
        author.contextChanged(context);
    }, [author, context]);
    if (
        !context ||
        !author.matchesContext(context) ||
        !authorAvailable(context)
    )
        return (
            <section aria-labelledby="author-unavailable-title">
                <h2 id="author-unavailable-title">Author corrections</h2>
                <p role="status">
                    {!context && "Native author context is unavailable. "}
                    Available only for a saved story in Story Lab, after the
                    private spoiler grant, with the omniscient lens and no
                    pending gameplay or unresolved shared operation.
                </p>
            </section>
        );
    const disabled = state.busy || state.uncertain;
    const edit = (change: Partial<AuthorDraft>) =>
        author.setDraft({ ...state.draft, ...change });
    const preview = state.preview?.preview;
    return (
        <section
            className="author-panel"
            aria-labelledby="author-title"
            style={{ minWidth: 0, overflowWrap: "anywhere" }}
        >
            <h2 id="author-title">Author correction — out of story</h2>
            <p>
                These private controls create a new timeline. The original
                remains intact. This is separate from dialogue or a character
                learning new information.
            </p>
            <p className="muted">
                Unresolved author requests remain in this window's memory only.
                Author-operation recovery after restart is unavailable. Saved
                timelines can still be reopened from the story library.
            </p>
            <dl>
                <dt>Selected story / timeline</dt>
                <dd>
                    <code>
                        {context.scope.story} / {context.scope.branch}
                    </code>
                </dd>
                <dt>Accepted revision</dt>
                <dd>{context.head}</dd>
                <dt>Inspection lens</dt>
                <dd>{context.observer}</dd>
                <dt>Operation</dt>
                <dd>
                    {state.status}
                    {state.operation
                        ? ` · ${state.operation.operation_id} · ${state.operation.phase}`
                        : ""}
                </dd>
            </dl>
            <fieldset disabled={disabled}>
                <legend>New correction request</legend>
                <label>
                    Completed fork revision{" "}
                    <input
                        aria-label="Author fork revision"
                        inputMode="numeric"
                        value={state.draft.fork_revision}
                        onChange={(event) =>
                            edit({
                                fork_revision: Number(
                                    event.currentTarget.value,
                                ),
                            })
                        }
                    />
                </label>
                <p className="muted">
                    Rust checks the completed boundary and retained ancestry. A
                    receipt-only page is not the entire canonical history.
                </p>
                <label>
                    Fixed new timeline identity{" "}
                    <input
                        aria-label="Author child identity"
                        maxLength={64}
                        value={state.draft.child_branch}
                        onChange={(event) =>
                            edit({ child_branch: event.currentTarget.value })
                        }
                    />
                </label>
                <button
                    type="button"
                    onClick={() => edit({ child_branch: crypto.randomUUID() })}
                >
                    Choose new timeline identity
                </button>
                <label>
                    Existing fact ID{" "}
                    <input
                        aria-label="Author fact ID"
                        maxLength={64}
                        value={state.draft.fact}
                        onChange={(event) =>
                            edit({ fact: event.currentTarget.value })
                        }
                    />
                </label>
                <label>
                    Expected proposition at the fork{" "}
                    <textarea
                        aria-label="Author expected proposition"
                        maxLength={2048}
                        value={state.draft.expected_proposition}
                        onChange={(event) =>
                            edit({
                                expected_proposition: event.currentTarget.value,
                            })
                        }
                    />
                </label>
                <label>
                    Replacement proposition{" "}
                    <textarea
                        aria-label="Author replacement proposition"
                        maxLength={2048}
                        value={state.draft.replacement}
                        onChange={(event) =>
                            edit({ replacement: event.currentTarget.value })
                        }
                    />
                </label>
                <label>
                    Private reason{" "}
                    <textarea
                        aria-label="Author reason"
                        maxLength={2048}
                        value={state.draft.reason}
                        onChange={(event) =>
                            edit({ reason: event.currentTarget.value })
                        }
                    />
                </label>
                <label>
                    <input
                        type="checkbox"
                        checked={state.authorConsent}
                        onChange={(event) =>
                            author.setAuthorConsent(event.currentTarget.checked)
                        }
                    />
                    I understand this opens private author information and
                    prepares an alternate timeline. Preparing does not apply the
                    correction.
                </label>
                <button
                    type="button"
                    disabled={!state.authorConsent}
                    onClick={() => void author.prepare()}
                >
                    Prepare private impact preview
                </button>
            </fieldset>
            {preview && state.preview && (
                <section aria-labelledby="author-preview-title">
                    <h3 id="author-preview-title">
                        Exact private impact preview
                    </h3>
                    <dl>
                        <dt>Parent / original head</dt>
                        <dd>
                            <code>
                                {preview.input.parent.story} /{" "}
                                {preview.input.parent.branch}
                            </code>{" "}
                            · {preview.input.expected_parent_revision}
                        </dd>
                        <dt>Fork / new child revision</dt>
                        <dd>
                            {preview.input.fork_revision} /{" "}
                            {preview.creation_revision}
                        </dd>
                        <dt>New timeline</dt>
                        <dd>
                            <code>{preview.child.branch}</code>
                        </dd>
                        <dt>Fact</dt>
                        <dd>
                            <code>{preview.before.fact}</code>
                        </dd>
                        <dt>Before</dt>
                        <dd style={{ whiteSpace: "pre-wrap" }}>
                            {preview.before.proposition}
                        </dd>
                        <dt>Replacement</dt>
                        <dd style={{ whiteSpace: "pre-wrap" }}>
                            {preview.input.operation.replacement}
                        </dd>
                        <dt>Private reason</dt>
                        <dd style={{ whiteSpace: "pre-wrap" }}>
                            {preview.input.reason}
                        </dd>
                        <dt>Retained knowers</dt>
                        <dd>{preview.retained_knowers}</dd>
                        <dt>Excluded parent suffix</dt>
                        <dd>
                            {preview.excluded_suffix_events} events ·{" "}
                            {preview.excluded_suffix_records} canonical records
                        </dd>
                        <dt>Original preserved / downstream replay</dt>
                        <dd>Yes / none</dd>
                        <dt>Derived data</dt>
                        <dd>
                            Fresh data required. Automatic summary rebuilding is
                            unavailable here.
                        </dd>
                        <dt>Display digest</dt>
                        <dd>
                            <code>{state.preview.preview_sha256}</code>
                        </dd>
                    </dl>
                    <p>
                        No character observation is created. A character who
                        observed the previous value keeps that observation until
                        an actual in-story re-observation.
                    </p>
                    <details>
                        <summary>Exact private Core preview JSON</summary>
                        <pre
                            style={{
                                whiteSpace: "pre-wrap",
                                maxHeight: "24rem",
                                overflow: "auto",
                            }}
                        >
                            {state.preview.preview_json}
                        </pre>
                    </details>
                    <label>
                        <input
                            type="checkbox"
                            disabled={state.busy}
                            checked={state.previewRead}
                            onChange={(event) =>
                                author.setPreviewRead(
                                    event.currentTarget.checked,
                                )
                            }
                        />
                        I have read this exact private preview, including the
                        preserved original and excluded later choices.
                    </label>
                    <button
                        type="button"
                        disabled={state.busy || !state.previewRead}
                        onClick={() => void author.confirm(true)}
                    >
                        Confirm author correction in new timeline
                    </button>
                    <button
                        type="button"
                        disabled={state.busy}
                        onClick={() => void author.cancel()}
                    >
                        Discard unused preview
                    </button>
                </section>
            )}
            {(state.busy || state.uncertain) && (
                <p role="status">
                    {state.uncertain
                        ? "Outcome unknown. Inspect only; this action will not be retried automatically."
                        : "Waiting for the native operation. Cancellation does not undo an already committed correction."}
                </p>
            )}
            {state.busy && (
                <button type="button" onClick={() => void author.cancel()}>
                    Request cancellation
                </button>
            )}
            {state.operation && state.uncertain && (
                <button
                    type="button"
                    disabled={state.busy}
                    onClick={() => void author.inspectOperation()}
                >
                    Inspect known native operation
                </button>
            )}
            {state.input && (
                <div>
                    <p>
                        Captured child for inspection:{" "}
                        <code>
                            {state.input.parent.story} /{" "}
                            {state.input.child_branch}
                        </code>
                        . Exact input remains only in this window's memory;
                        restart recovery is unavailable.
                    </p>
                    <button
                        type="button"
                        disabled={state.busy}
                        onClick={() => void author.lookup()}
                    >
                        Check saved child only
                    </button>
                </div>
            )}
            {state.outcome && (
                <section aria-labelledby="author-outcome-title">
                    <h3 id="author-outcome-title">Saved child confirmed</h3>
                    <p>
                        <code>
                            {state.outcome.scope.story} /{" "}
                            {state.outcome.scope.branch}
                        </code>{" "}
                        · author revision {state.outcome.author_revision} ·
                        current head {state.outcome.head_revision} ·{" "}
                        {state.outcome.created
                            ? "created by this operation"
                            : "existing recorded outcome"}
                        .
                    </p>
                    <button
                        type="button"
                        disabled={state.busy}
                        onClick={() => void author.openConfirmed()}
                    >
                        Open confirmed child
                    </button>
                </section>
            )}
            {state.error && (
                <p role="alert">Author correction: {state.error}</p>
            )}
            {state.notice && <p role="status">{state.notice}</p>}
        </section>
    );
}
