import { useState, useSyncExternalStore } from "react";
import type { BrokerRetention } from "./broker-retention";
export function BrokerRetentionPanel({
    retention,
}: {
    retention: BrokerRetention;
}) {
    const r = useSyncExternalStore(retention.subscribe, retention.get),
        [consent, setConsent] = useState({ key: "", value: false });
    if (!r?.unknown) return null;
    const key = JSON.stringify(r.identity),
        approved = consent.key === key && consent.value;
    return (
        <section
            className="broker-retention"
            aria-label="Unresolved saved operation"
        >
            <h2>Saved operation outcome unknown</h2>
            <p role="status">
                {r.identity.surface}: {r.identity.action}. Story{" "}
                {r.identity.story ?? "not selected"} / timeline{" "}
                {r.identity.branch ?? "not selected"}, accepted revision{" "}
                {r.identity.head ?? "unavailable"}.
            </p>
            <p>
                The operation may have completed. Changing the selected story
                does not resolve it. Read status in the original saved
                selection, or explicitly acknowledge this unresolved outcome
                before starting another operation.
            </p>
            {r.acknowledgedUnresolved ? (
                <p>
                    Unresolved outcome acknowledged. This does not cancel or
                    undo saved work. Native storage still decides whether a new
                    operation can start.
                </p>
            ) : (
                <>
                    <label>
                        <input
                            type="checkbox"
                            checked={approved}
                            onChange={(e) =>
                                setConsent({ key, value: e.target.checked })
                            }
                        />{" "}
                        I acknowledge that this original operation remains
                        unresolved and may already be saved.
                    </label>
                    <button
                        disabled={!approved || r.inFlight}
                        onClick={() => {
                            retention.acknowledgeUnresolved(approved);
                            setConsent({ key: "", value: false });
                        }}
                    >
                        Acknowledge unresolved outcome
                    </button>
                </>
            )}
        </section>
    );
}
