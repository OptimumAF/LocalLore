// Presentation only. Native managers and CloseGate own all cleanup proof.
export type NativeClosePhase =
    "open" | "closing" | "cleanup_required" | "closed";
export class NativeCloseController {
    private phase: NativeClosePhase = "open";
    private listeners = new Set<() => void>();
    constructor(
        private invoke: (name: string) => Promise<unknown>,
        private error: () => void,
    ) {}
    get = (): NativeClosePhase => this.phase;
    subscribe = (listener: () => void): (() => void) => {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    };
    receive = (value: unknown): void => {
        if (!value || typeof value !== "object" || Array.isArray(value)) {
            this.error();
            return;
        }
        const record = value as Record<string, unknown>;
        if (
            Object.keys(record).length !== 2 ||
            record.version !== 1 ||
            !["closing", "cleanup_required", "closed"].includes(
                String(record.phase),
            )
        ) {
            this.error();
            return;
        }
        this.phase = record.phase as NativeClosePhase;
        for (const listener of this.listeners) listener();
    };
    retry = async (): Promise<void> => {
        try {
            await this.invoke("application_close");
        } catch {
            this.error();
        }
    };
}
