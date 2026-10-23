import { useState, useSyncExternalStore, useEffect } from "react";
import type { CaptureController } from "./capture-controller";
import type { Controller } from "./controller";
import type { Receipt } from "./model";
import { object } from "./capture-model";
const scalar = (value: unknown) =>
    typeof value === "string" || typeof value === "number"
        ? String(value)
        : "Not captured";
export function CapturePanel({
    controller: c,
    gameplay,
    receipts,
}: {
    controller: CaptureController;
    gameplay: Controller;
    receipts: Receipt[];
}) {
    const s = useSyncExternalStore(c.subscribe, c.get);
    const [consent, setConsent] = useState(false),
        [exportConsent, setExportConsent] = useState(false);
    useEffect(() => {
        setConsent(false);
        setExportConsent(false);
    }, [s.permitted]);
    useEffect(() => {
        setExportConsent(false);
    }, [s.preview?.token]);
    const identity = s.reply?.details.identity;
    const receipt =
        identity &&
        receipts.find(
            (r) =>
                r.request.turn === identity.turn &&
                r.request.expected_revision === identity.base_revision &&
                r.request.scope.story === identity.scope.story &&
                r.request.scope.branch === identity.scope.branch,
        );
    const context = s.reply?.details.artifacts.find(
        (a) => a.kind === "selected_context",
    )?.value;
    if (!s.permitted)
        return s.cleanup ? <p role="status">{s.cleanup}</p> : null;
    return (
        <section
            className="private-capture"
            aria-labelledby="private-capture-title"
        >
            <h3 id="private-capture-title">
                Private production capture · Story Lab only
            </h3>
            <p>
                Original input, selected actor context, prompts, raw outputs and
                staged proposals can contain private text and spoilers. This
                observes the same Play attempt. It never reveals hidden
                reasoning or changes character knowledge.
            </p>
            <p>
                Future-attempt consent:{" "}
                {s.enabled === true
                    ? "enabled"
                    : s.enabled === false
                      ? "disabled or expired"
                      : "not confirmed"}
                . Default off; this session only. Ten minutes from consent,
                checked on access; three attempts / 512 KiB retained encoded
                data. No immediate physical-erasure or OS paging guarantee.
            </p>
            <label>
                <input
                    type="checkbox"
                    checked={consent}
                    onChange={(e) => setConsent(e.target.checked)}
                />{" "}
                I consent to capture future attempts in this session.
            </label>
            <div className="trace-controls">
                <button
                    disabled={!consent || s.busy || s.controlBusy}
                    onClick={() => void c.configure(consent)}
                >
                    Enable private future capture
                </button>
                <button
                    disabled={s.controlBusy}
                    onClick={() => void c.disable()}
                >
                    Revoke & clear private capture
                </button>
                <button
                    disabled={s.busy || s.controlBusy}
                    onClick={() => void c.read()}
                >
                    Read selected metadata attempt
                </button>
            </div>
            {s.controlBusy && (
                <p role="status">Updating native capture consent…</p>
            )}
            {s.error && (
                <p role="alert">
                    Private capture unavailable: {s.error}. No exact
                    reconstruction was invented.
                </p>
            )}
            {s.cleanup && <p role="status">{s.cleanup}</p>}
            {s.reply && (
                <>
                    {object(context) && (
                        <details className="capture-context">
                            <summary>
                                Captured context selection and budget
                            </summary>
                            <p>
                                Actor {scalar(context.observer)} · role{" "}
                                {scalar(context.role)} · source revision{" "}
                                {scalar(context.revision)} ·{" "}
                                {scalar(context.serialized_bytes)} serialized
                                bytes · {scalar(context.estimated_tokens)}{" "}
                                estimated tokens plus{" "}
                                {scalar(context.reserved_tokens)} reserved.{" "}
                                {scalar(context.token_accounting)}. Historical
                                eligibility was applied before these records
                                reached the model.
                            </p>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Selected source</th>
                                        <th>Revision / reason</th>
                                        <th>Score / allocation</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {Array.isArray(context.records) &&
                                        context.records
                                            .filter(object)
                                            .map((r: any, index: number) => (
                                                <tr key={index}>
                                                    <td>
                                                        {scalar(r.id)}
                                                        <pre>
                                                            {JSON.stringify(
                                                                r.sources,
                                                            )}
                                                        </pre>
                                                    </td>
                                                    <td>
                                                        {scalar(
                                                            r.source_revision,
                                                        )}{" "}
                                                        / {scalar(r.reason)}
                                                    </td>
                                                    <td>
                                                        {scalar(r.score)} ·{" "}
                                                        {r.mandatory === true
                                                            ? "mandatory"
                                                            : "optional"}
                                                    </td>
                                                </tr>
                                            ))}
                                </tbody>
                            </table>
                            <p>
                                Scores describe the recorded deterministic
                                selection, not model attention or reasoning.
                                Per-record tokenizer counts are unavailable.
                            </p>
                            <pre>
                                {JSON.stringify(context.diagnostics, null, 2)}
                            </pre>
                        </details>
                    )}
                    <p>
                        <strong>
                            {s.reply.details.status.replaceAll("_", " ")}
                        </strong>{" "}
                        · historical captured basis r{s.reply.base_revision} ·
                        current head r{s.reply.head} · actor{" "}
                        {s.reply.details.identity?.observer ?? "not retained"} ·
                        exact reconstruction: false.
                    </p>
                    <p>{s.reply.details.privacy}</p>
                    {s.reply.details.artifacts.map((a) => (
                        <details key={a.ordinal}>
                            <summary>
                                {a.ordinal + 1}. {a.kind.replaceAll("_", " ")}
                            </summary>
                            <p>
                                Captured historical value. Validated plan and
                                accepted candidate are staged evidence, not
                                proof of durable commit. Raw narrator text is
                                separate from accepted canonical effects. Source
                                IDs here refer to the captured context, not
                                today's memory snapshot.
                            </p>
                            <pre>{JSON.stringify(a.value, null, 2)}</pre>
                        </details>
                    ))}
                    <p>
                        Missing artifacts may be disabled, expired, evicted,
                        dropped or truncated. Current facts and today's context
                        cannot reconstruct missing prompt bytes.
                    </p>
                    {receipt ? (
                        <div>
                            <h4>Separate durable accepted receipt</h4>
                            <p>
                                Turn {receipt.request.turn} · completed r
                                {receipt.events.at(-1)?.sequence}. This accepted
                                receipt is separate from the captured staged
                                plan/candidate.
                            </p>
                            <p>{receipt.narration}</p>
                            <details>
                                <summary>
                                    Compare recorded accepted operations and
                                    canonical events
                                </summary>
                                <pre>
                                    {JSON.stringify(
                                        {
                                            proposal: receipt.proposal,
                                            events: receipt.events,
                                        },
                                        null,
                                        2,
                                    )}
                                </pre>
                            </details>
                            <button
                                onClick={() =>
                                    void gameplay.capturedEvidence(
                                        receipt.request.turn,
                                        receipt.request.expected_revision,
                                    )
                                }
                            >
                                Open accepted field diff & provenance
                            </button>
                        </div>
                    ) : (
                        <p>
                            No matching durable accepted receipt in the current
                            snapshot. A captured candidate never proves commit.
                        </p>
                    )}
                    <button
                        disabled={
                            s.busy ||
                            s.controlBusy ||
                            !["recorded", "truncated"].includes(
                                s.reply.details.status,
                            )
                        }
                        onClick={() => void c.preview()}
                    >
                        Preview native exact private export
                    </button>
                </>
            )}
            {s.preview && (
                <div className="capture-export">
                    <h4>Exact private plaintext export preview</h4>
                    <p>
                        The native owner captured this read. Saving writes these
                        exact capture.json bytes plus its manifest. Access-time
                        token expiry: five minutes from creation; at most two
                        previews / 1 MiB encoded files total. Ordinary story
                        archives exclude these traces.
                    </p>
                    <p>SHA256 {s.preview.manifest.files[0].sha256}</p>
                    <details>
                        <summary>Review exact capture.json text</summary>
                        <pre>{s.preview.text}</pre>
                    </details>
                    <label>
                        <input
                            type="checkbox"
                            checked={exportConsent}
                            onChange={(e) => setExportConsent(e.target.checked)}
                        />{" "}
                        I consent to export this private plaintext, including
                        input, prompts and outputs, to a folder I choose.
                    </label>
                    <button
                        disabled={
                            !exportConsent ||
                            s.busy ||
                            s.controlBusy ||
                            !!s.saved
                        }
                        onClick={() => void c.save(exportConsent)}
                    >
                        Choose folder & save exact preview
                    </button>
                    {s.saved && (
                        <p role="status">
                            Saved exact private preview: {s.saved}
                        </p>
                    )}
                </div>
            )}
        </section>
    );
}
