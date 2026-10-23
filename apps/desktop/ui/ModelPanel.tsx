import type { Controller } from "./controller";
import type { State } from "./model";
export function ModelPanel({
    controller: c,
    state: s,
}: {
    controller: Controller;
    state: State;
}) {
    if (!s.modelShown) return null;
    const model = s.model;
    return (
        <section className="model-panel" aria-label="Local model management">
            <h2>Local model</h2>
            <p>
                Experimental Windows x64 CPU profile. One verified Qwen3-0.6B
                Q8_0 model serves separate director and narrator contexts.
                Constrained English scene actions only. Quality and offline
                qualification remain pending. No downloads or cloud fallback.
            </p>
            <p>
                Import copies approximately 640 MB into app-local storage. Only
                the approved artifact is accepted; your source file stays
                unchanged.
            </p>
            <div className="export-actions">
                <button
                    disabled={s.modelBusy || model?.loaded}
                    onClick={() => void c.modelAction("model_import")}
                >
                    Choose GGUF & import local copy
                </button>
                <button
                    disabled={s.modelBusy || !model?.imported || model.loaded}
                    onClick={() => void c.modelAction("model_load")}
                >
                    Load CPU model
                </button>
                <button
                    disabled={s.modelBusy || !model?.resident}
                    onClick={() => void c.modelAction("model_unload")}
                >
                    Unload model & cancel local work
                </button>
                <button
                    disabled={!s.modelBusy || !s.modelCancelReady}
                    onClick={() => void c.cancelModel()}
                >
                    Cancel model operation
                </button>
                <button onClick={() => void c.refreshModel()}>
                    Refresh status
                </button>
            </div>
            {["ModelOperationUnknown", "StaleModelOperation"].includes(
                s.visibleError ?? "",
            ) && (
                <p role="alert">
                    Operation status changed or is not yet available. Refresh
                    status and retry cancellation for the current operation.
                </p>
            )}
            <p role="status">
                {model?.phase ?? "Checking status"}
                {s.modelBusy ? ` - ${model?.percent ?? 0}%` : ""}
            </p>
            {s.modelBusy && (
                <progress
                    max={100}
                    value={model?.percent ?? 0}
                    aria-label="Model import progress"
                />
            )}
            {model?.error && (
                <p role="alert">
                    {model.error}. Choose the approved artifact, free disk space
                    or retry loading. Real-model failure never selects a fake
                    provider.
                </p>
            )}
            <details>
                <summary>Verified profile & provenance</summary>
                <pre>
                    {JSON.stringify(
                        model?.profile ?? model?.available_profile,
                        null,
                        2,
                    )}
                </pre>
            </details>
        </section>
    );
}
