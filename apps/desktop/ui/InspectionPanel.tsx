import type { Controller } from "./controller";
import type { ExportMode, State } from "./model";
declare const __DEV_HARNESS__: boolean;
const displayPath = (path: string) =>
    __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.exporting
        ? `<synthetic selected path>/${path.split(/[\\/]/).at(-1)}`
        : path;
export function InspectionPanel({
    controller: c,
    state: s,
}: {
    controller: Controller;
    state: State;
}) {
    const e = s.exports,
        preview = e.preview;
    if (!e.shown) return null;
    return (
        <section className="export-panel" aria-label="Inspection snapshots">
            <div className="topline">
                <h2>Inspection snapshots</h2>
                <button onClick={() => c.showExports(false)}>
                    Hide snapshot tools
                </button>
            </div>
            <div className="export-actions">
                <button disabled={e.busy} onClick={() => void c.loadExport()}>
                    Open an existing inspection folder
                </button>
            </div>
            <p>
                Derived, read-only views captured at one head. These files are
                not a portable playable archive. Editing them cannot change your
                story.
            </p>
            <label>
                Privacy scope{" "}
                <select
                    value={e.mode}
                    disabled={e.busy}
                    onChange={(event) =>
                        c.setExportMode(event.target.value as ExportMode)
                    }
                >
                    <option value="diagnostics">
                        Shareable diagnostics: counts only
                    </option>
                    <option value="player">Private player-visible story</option>
                    <option value="database" disabled={s.view !== "lab"}>
                        Separate private SQLite copy: ALL stories & drafts
                    </option>
                    <option value="full" disabled={s.view !== "lab"}>
                        Private full story: spoilers (Story Lab)
                    </option>
                </select>
            </label>
            <p
                className={
                    !e.imported && e.mode === "diagnostics"
                        ? "muted"
                        : "export-warning"
                }
                role="note"
            >
                {e.imported
                    ? "Untrusted local inspection: may contain hidden or personal text regardless of its claimed scope. Checksums do not authenticate authorship. Open read-only and review before sharing."
                    : e.mode === "diagnostics"
                      ? "Diagnostics excludes story text, state, prompts, model weights and home paths."
                      : e.mode === "database"
                        ? "Private database copy: includes ALL stories, hidden canon and submitted drafts. This consistent copy is for deliberate SQLite inspection; it is separate from readable views and is not a portable playable archive."
                        : e.mode === "player"
                          ? "Private: includes accepted story text and player-visible state. Story text may contain personal information; review before sharing."
                          : "Private spoilers: includes hidden canon and character knowledge. Review before saving or sharing. Story Lab inspection never changes character permissions."}
            </p>
            <div className="export-actions">
                <button
                    disabled={!s.play || e.busy}
                    onClick={() => void c.previewExport()}
                >
                    Preview snapshot
                </button>
                <button
                    disabled={!preview || e.busy || !!e.savedLocation}
                    onClick={() => void c.saveExport()}
                >
                    Choose folder & save exact preview
                </button>
                <button
                    disabled={!preview}
                    onClick={() => void c.cancelExport()}
                >
                    Discard preview / cancel save
                </button>
            </div>
            {preview && (
                <div className="export-preview">
                    <p>
                        Captured {preview.manifest.scope.story} /{" "}
                        {preview.manifest.scope.branch} at revision{" "}
                        {preview.manifest.revision}. Current revision{" "}
                        {s.play?.revision ?? "unavailable"}. Preview expires in{" "}
                        {preview.expires_seconds} seconds.
                    </p>
                    <table>
                        <caption>Included files</caption>
                        <thead>
                            <tr>
                                <th>File</th>
                                <th>Bytes</th>
                            </tr>
                        </thead>
                        <tbody>
                            {preview.files.map((file) => (
                                <tr key={file.path}>
                                    <td>{file.path}</td>
                                    <td>{file.bytes}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <details>
                        <summary>
                            Manifest, checksums & implemented views
                        </summary>
                        <pre>{JSON.stringify(preview.manifest, null, 2)}</pre>
                    </details>
                </div>
            )}
            {e.savedLocation && (
                <div>
                    <p className="storage-path">
                        Saved locally: {displayPath(e.savedLocation)}
                    </p>
                    <label>
                        Saved inspection file{" "}
                        <select
                            value={e.selectedFile}
                            onChange={(event) =>
                                c.selectExportFile(event.target.value)
                            }
                        >
                            {preview?.files.map((file) => (
                                <option key={file.path} value={file.path}>
                                    {file.path}
                                </option>
                            ))}
                        </select>
                    </label>
                    <button
                        disabled={e.busy}
                        onClick={() => void c.openExport()}
                    >
                        Open exported snapshot read-only
                    </button>
                </div>
            )}
            {e.opened && (
                <div className="export-open">
                    <h3>{e.opened.path} · read-only</h3>
                    {e.opened.truncated && (
                        <p>
                            Preview truncated to 64 KiB. The saved file contains{" "}
                            {e.opened.bytes} bytes.
                        </p>
                    )}
                    <pre tabIndex={0}>{e.opened.text}</pre>
                </div>
            )}
            {e.storage && (
                <div className="storage-reveal">
                    <h3>Storage location</h3>
                    <p className="storage-path">
                        {displayPath(e.storage.location)}
                    </p>
                    <p>
                        Schema {e.storage.schema_version}. This app shows
                        metadata only; no writable live-database connection or
                        external tool is opened.
                    </p>
                </div>
            )}
            {e.notice && <p role="status">{e.notice}</p>}
            {e.error && (
                <p className="export-warning" role="alert">
                    {e.error}. Canon is unchanged.
                </p>
            )}
        </section>
    );
}
