// Future app-owned harness integration: ACTUAL gateway/Controller, fixed synthetic
// Store fixture supplied by the native owner. This module never creates a branch.
import type { Controller } from "./controller";
import type { Scope } from "./model";
import { sameScope, structural } from "./model";
import { timelineContext } from "./timeline-controller";
import type { TimelineController } from "./timeline-controller";
export interface TimelineJourneyFixture {
    root: Scope;
    child: Scope;
    sibling: Scope;
    retired: Scope;
    childFork: number;
    childHead: number;
    inheritedSource: Scope;
    excludedPlayCanaries: string[];
}
export async function timelineJourneys({
    controller: c,
    timeline: t,
    fixture: f,
    checkpoint,
}: {
    controller: Controller;
    timeline: TimelineController;
    fixture: TimelineJourneyFixture;
    checkpoint?: (
        label: "catalog" | "child" | "sibling" | "root",
    ) => Promise<void>;
}): Promise<string[]> {
    const checks: string[] = [];
    const check = (value: unknown, label: string) => {
        if (!value) throw Error(`timeline-${label}`);
        checks.push(`timeline-${label}`);
    };
    check(
        c.get().workspace?.persistent === true,
        "actual-durable-workspace-required",
    );
    check(
        [f.root, f.child, f.sibling, f.retired].every(
            (s) => s.story === f.root.story,
        ),
        "fixture-one-story",
    );
    check(
        !!c.selected() && sameScope(c.selected()!.scope, f.root),
        "fixture-root-selected",
    );
    t.contextChanged(timelineContext(c));
    const before = structural(c.get().play);
    await t.show();
    const catalog = t.get().catalog;
    check(
        !!catalog && catalog.version === 2 && catalog.story_id === f.root.story,
        "actual-shared-catalog-v2",
    );
    const child = catalog!.branches.find((r) => sameScope(r.scope, f.child)),
        retired = catalog!.branches.find((r) => sameScope(r.scope, f.retired));
    check(
        child?.fork_revision === f.childFork && child.revision === f.childHead,
        "exact-child-fork-and-head",
    );
    check(
        retired?.retired === true && child?.parent_branch === f.retired.branch,
        "retired-parent-metadata-preserved",
    );
    check(
        structural(c.get().play) === before,
        "catalog-read-does-not-change-play",
    );
    await checkpoint?.("catalog");
    await t.select(f.retired.branch);
    check(
        !!c.selected() &&
            sameScope(c.selected()!.scope, f.root) &&
            structural(c.get().play) === before,
        "retired-not-resumed",
    );
    await t.select(f.child.branch);
    check(
        !!c.selected() &&
            sameScope(c.selected()!.scope, f.child) &&
            c.get().play?.revision === f.childHead,
        "actual-child-resumed",
    );
    check(
        c
            .get()
            .play!.receipts.some((r) =>
                sameScope(r.request.scope, f.inheritedSource),
            ),
        "original-inherited-receipt-scope-preserved",
    );
    check(
        c
            .get()
            .play!.receipts.every((r) =>
                r.events.every((e) => sameScope(e.scope, r.request.scope)),
            ),
        "events-retain-original-request-scope",
    );
    check(
        f.excludedPlayCanaries.every(
            (word) => !structural(c.get().play).includes(word),
        ),
        "no-future-parent-sibling-prose",
    );
    await checkpoint?.("child");
    t.contextChanged(timelineContext(c));
    await t.show();
    await t.select(f.sibling.branch);
    check(
        !!c.selected() && sameScope(c.selected()!.scope, f.sibling),
        "actual-sibling-resumed",
    );
    await checkpoint?.("sibling");
    t.contextChanged(timelineContext(c));
    await t.show();
    await t.select(f.root.branch);
    check(
        !!c.selected() &&
            sameScope(c.selected()!.scope, f.root) &&
            structural(c.get().play) === before,
        "root-reopen-preserves-original-play",
    );
    await checkpoint?.("root");
    return checks;
}
