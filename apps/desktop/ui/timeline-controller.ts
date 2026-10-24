import { category, sameScope } from "./model";
import type { Gateway, Scope } from "./model";
import type { Controller } from "./controller";
import { contextIdentity, decodeBranchCatalog } from "./timeline-model";
import type { TimelineCatalog, TimelineContext } from "./timeline-model";

export interface TimelineState {
    shown: boolean;
    busy: boolean;
    status:
        | "idle"
        | "loading"
        | "ready"
        | "empty"
        | "unsupported"
        | "unavailable"
        | "resuming"
        | "error";
    catalog: TimelineCatalog | null;
    error: string | null;
    notice: string;
}
export function timelineContext(
    c: Pick<Controller, "selected" | "get">,
): TimelineContext | null {
    const s = c.get(),
        selected = c.selected();
    return selected && !s.disposed
        ? {
              session: selected.id,
              scope: { ...selected.scope },
              revision: s.play?.revision ?? selected.revision,
              view: s.view,
              observer: s.observer,
              persistent: s.workspace?.persistent === true,
          }
        : null;
}
// Application adapter: use the existing resume/switch path, never a second session owner.
// A successful target snapshot wins over any unrelated preexisting visibleError.
export async function resumeTimeline(
    c: Pick<Controller, "resume" | "selected" | "get">,
    scope: Scope,
): Promise<void> {
    const oldError = c.get().visibleError;
    await c.resume(scope);
    const s = c.get(),
        selected = c.selected();
    if (
        selected &&
        sameScope(selected.scope, scope) &&
        s.play &&
        sameScope(s.play.scope, scope) &&
        selected.revision === s.play.revision
    )
        return;
    throw Error(
        s.visibleError && s.visibleError !== oldError
            ? category(s.visibleError)
            : "NotReady",
    );
}
export class TimelineController {
    private state: TimelineState = {
        shown: false,
        busy: false,
        status: "idle",
        catalog: null,
        error: null,
        notice: "",
    };
    private context: TimelineContext | null = null;
    private key = "none";
    private epoch = 0;
    private disposed = false;
    private listeners = new Set<() => void>();
    constructor(
        private gateway: Gateway,
        private selectScope: (scope: Scope) => Promise<void>,
    ) {}
    get = () => this.state;
    subscribe = (listener: () => void) => {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    };
    private patch(value: Partial<TimelineState>) {
        this.state = { ...this.state, ...value };
        for (const listener of this.listeners) listener();
    }
    matchesContext(context: TimelineContext | null) {
        try {
            return !this.disposed && this.key === contextIdentity(context);
        } catch {
            return false;
        }
    }
    contextChanged(context: TimelineContext | null) {
        if (this.disposed) return;
        let key: string;
        try {
            key = contextIdentity(context);
        } catch {
            this.epoch++;
            this.context = null;
            this.key = "invalid";
            this.patch({
                shown: false,
                busy: false,
                status: "error",
                catalog: null,
                error: "Wire",
                notice: "",
            });
            return;
        }
        if (key === this.key) return;
        this.key = key;
        this.context = context
            ? Object.freeze({
                  ...context,
                  scope: Object.freeze({ ...context.scope }),
              })
            : null;
        this.epoch++;
        this.patch({
            shown: false,
            busy: false,
            status: "idle",
            catalog: null,
            error: null,
            notice: "",
        });
    }
    async show() {
        if (this.disposed) return;
        this.patch({ shown: true });
        await this.refresh();
    }
    hide() {
        this.epoch++;
        this.patch({
            shown: false,
            busy: false,
            status: "idle",
            catalog: null,
            error: null,
            notice: "",
        });
    }
    private live(epoch: number) {
        return !this.disposed && this.state.shown && epoch === this.epoch;
    }
    async refresh() {
        if (
            this.disposed ||
            !this.state.shown ||
            this.state.status === "resuming"
        )
            return;
        const epoch = ++this.epoch,
            context = this.context;
        this.patch({ catalog: null, error: null, notice: "", busy: false });
        if (!context) {
            this.patch({
                status: "unavailable",
                notice: "Open a saved story to browse its timelines.",
            });
            return;
        }
        if (!context.persistent) {
            this.patch({
                status: "unsupported",
                notice: "Saved timeline browsing is unavailable for this in-memory session.",
            });
            return;
        }
        this.patch({ status: "loading", busy: true });
        try {
            const value = await this.gateway.call({
                op: "branches",
                story: context.scope.story,
            });
            if (!this.live(epoch)) return;
            const catalog = decodeBranchCatalog(value, context.scope.story);
            this.patch({
                catalog,
                busy: false,
                status: catalog.branches.length ? "ready" : "empty",
                notice: catalog.branches.length
                    ? "Validated metadata snapshot. Resume opens the latest accepted head; it does not replay future parent or sibling choices."
                    : "No timelines were returned for this saved story.",
            });
        } catch (error) {
            if (!this.live(epoch)) return;
            const name = category(error);
            this.patch({
                busy: false,
                status: name === "Unsupported" ? "unsupported" : "error",
                error: name,
                notice: "No timeline was resumed.",
            });
        }
    }
    async select(branch: string) {
        if (
            this.disposed ||
            !this.state.shown ||
            this.state.busy ||
            !this.context ||
            !this.state.catalog
        )
            return;
        const row = this.state.catalog.branches.find(
            (r) => r.scope.branch === branch,
        );
        if (!row || row.retired) {
            this.patch({
                error: row ? "Closed" : "NotFound",
                notice: row
                    ? "Retired timelines are retained ancestry metadata only."
                    : "Refresh the catalog before choosing a timeline.",
            });
            return;
        }
        if (sameScope(row.scope, this.context.scope)) return;
        const epoch = ++this.epoch;
        this.patch({
            busy: true,
            status: "resuming",
            error: null,
            notice: "Resuming through the shared saved-history owner…",
        });
        try {
            await this.selectScope({ ...row.scope });
            if (this.live(epoch))
                this.patch({
                    busy: false,
                    status: "ready",
                    notice: "Selection completed in the play view.",
                });
        } catch (error) {
            if (this.live(epoch))
                this.patch({
                    busy: false,
                    status: "error",
                    error: category(error),
                    notice: "The timeline could not be resumed. The play view reports the active session.",
                });
        }
    }
    dispose() {
        this.disposed = true;
        this.epoch++;
        this.context = null;
        this.patch({
            shown: false,
            busy: false,
            status: "idle",
            catalog: null,
            error: null,
            notice: "",
        });
        this.listeners.clear();
    }
}
