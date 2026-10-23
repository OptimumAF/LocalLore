import { useSyncExternalStore } from "react";
import type { ArchiveController } from "./archive-controller";
import type { Controller } from "./controller";
export function ArchivePanel({
    archive: a,
    controller: c,
    context,
    allowed,
}: {
    archive: ArchiveController;
    controller: Controller;
    context: string;
    allowed: boolean;
}) {
    const s = useSyncExternalStore(a.subscribe, a.get, a.get),
        play = c.get().play,
        session = c.selected();
    if (!allowed || !a.matchesContext(context)) return null;
    if (!s.shown)
        return <button onClick={() => a.show()}>Playable story archive</button>;
    const p = s.preview?.preview;
    return (
        <section className="archive-panel" aria-labelledby="archive-title">
            <div className="panel-heading">
                <h2 id="archive-title">Playable story archive</h2>
                <button onClick={() => a.hide()}>Close playable archive</button>
            </div>
            <p>
                Full private, whole story. Includes hidden facts, every branch,
                original accepted requests, narration and provenance. Manual
                transfer is a snapshot, not synchronization. Checksums show
                consistency, not authenticity.
            </p>
            <p>
                Excluded: noncommitted workflow keys/status, drafts, private
                traces, caches and weights. Import never restores pending work
                or loads a model. This is separate from a D03 readable
                inspection snapshot.
            </p>
            <p>
                Versions 1 and 2 · maximum 32 MiB · 32 physical branches ·
                accepted history only. Branch switching and author corrections
                are unavailable in this panel.
            </p>
            <div className="archive-actions">
                <button disabled={s.busy} onClick={() => void c.library()}>
                    Refresh saved story library
                </button>
                <button
                    disabled={s.busy || !session || !play}
                    onClick={() =>
                        session &&
                        play &&
                        void a.previewExport(
                            session.id,
                            session.scope,
                            play.revision,
                        )
                    }
                >
                    Preview private export
                </button>
                <button
                    disabled={s.busy}
                    onClick={() => void a.previewImport()}
                >
                    Choose playable archive to review
                </button>
                <button
                    disabled={!s.status?.running}
                    onClick={() => void a.cancel()}
                >
                    Cancel archive operation
                </button>
            </div>
            {s.status && (
                <p role="status">
                    Operation {s.status.operation_id}: {s.status.phase}
                    {s.busy ? " · working" : ""}
                </p>
            )}
            {p && (
                <div className="archive-preview">
                    <h3>
                        {s.preview!.kind === "import"
                            ? "Review private import"
                            : "Review captured export"}
                        : {p.title}
                    </h3>
                    <dl>
                        <dt>Story identity</dt>
                        <dd>{p.story_id}</dd>
                        <dt>Root branch</dt>
                        <dd>{p.root_branch}</dd>
                        <dt>Archive version</dt>
                        <dd>{p.version}</dd>
                        <dt>Accepted turns</dt>
                        <dd>{p.committed_turns}</dd>
                        <dt>Bytes</dt>
                        <dd>{p.bytes}</dd>
                        <dt>Payload SHA256</dt>
                        <dd>{p.payload_sha256}</dd>
                    </dl>
                    <table>
                        <caption>Captured physical branch heads</caption>
                        <thead>
                            <tr>
                                <th>Branch</th>
                                <th>Revision</th>
                                <th>Availability</th>
                            </tr>
                        </thead>
                        <tbody>
                            {Object.entries(p.branch_heads).map(
                                ([branch, head]) => (
                                    <tr key={branch}>
                                        <td>{branch}</td>
                                        <td>{head}</td>
                                        <td>
                                            {p.retired_branch_ids?.includes(
                                                branch,
                                            )
                                                ? "Retired ancestry only"
                                                : "Playable"}
                                        </td>
                                    </tr>
                                ),
                            )}
                        </tbody>
                    </table>
                    {p.retired_branch_ids && (
                        <p>
                            Reserved retired identities:{" "}
                            {p.retired_branch_ids.join(", ")}. Retained
                            ancestors preserve original history; collected
                            identities remain reserved and cannot be reopened.
                        </p>
                    )}
                    <p>{p.privacy_warning}</p>
                    <p>
                        Import is first validated and replayed in a new private
                        staging Store, then applied atomically to this
                        workspace. Existing story identity always conflicts;
                        there is no overwrite, merge or remap.
                    </p>
                    <label>
                        <input
                            type="checkbox"
                            checked={s.consent}
                            disabled={s.busy}
                            onChange={(e) => a.consent(e.target.checked)}
                        />{" "}
                        I reviewed this full-private snapshot and understand its
                        identity and exclusions.
                    </label>
                    <button
                        disabled={!s.consent || s.busy}
                        onClick={() => void a.confirm()}
                    >
                        {s.preview!.kind === "export"
                            ? "Choose folder and export exact snapshot"
                            : "Confirm staged import"}
                    </button>
                </div>
            )}
            {s.error && (
                <p className="error" role="alert">
                    Archive error: {s.error}.{" "}
                    {s.error === "Conflict"
                        ? "Existing story kept. Keep the original archive; copying to a new identity is unavailable."
                        : ""}
                </p>
            )}
            {s.notice && <p role="status">{s.notice}</p>}
            {s.result?.location && (
                <p className="storage-path">
                    Saved private file: {s.result.location}
                </p>
            )}
            {s.result?.staging_cleanup_complete === false && (
                <p role="alert">
                    Private staging cleanup incomplete. Files remain in the
                    app-owned archive-staging-v1 directory; no automatic
                    deletion or secure-erasure guarantee.
                </p>
            )}
            {s.result?.cleanup_complete === false && (
                <p role="alert">
                    Partial export cleanup incomplete in the selected folder.
                </p>
            )}
            {s.result?.root && (
                <button onClick={() => void c.resume(s.result!.root!)}>
                    Open imported story
                </button>
            )}
            <p>
                Private export files remain where you save them. A process
                interruption can retain private staging files; cleanup is
                limited to known owned filenames. Outside copies and OS backups
                are separate. Unsupported future archives are rejected before
                staging.
            </p>
        </section>
    );
}
