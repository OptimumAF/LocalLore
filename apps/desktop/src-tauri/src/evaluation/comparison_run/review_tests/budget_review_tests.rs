// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY at7e0423d8. UNCOMPILED / UNRUN.
//! Real native-service scripted prefix; padding is an explicitly synthetic
//! local capacity fault, not measured storage exhaustion or native inference.
use super::*;

#[test]
fn oversized_existing_run_refuses_resume_before_any_shared_write() {
    let (f, run, _) = copied();
    let ready = f.opened(&run);
    published(&ready, 1, false);
    let cap = token(&ready).to_owned();
    let leaf = f.root().join(id(&ready));

    // Three bounded real files exceed the existing32MiB per-run cap while
    // staying below this fixture's16MiB/file and128MiB inventory limits.
    // This does not alter any producer manifest/checkpoint/receipt bytes.
    for n in 0..3 {
        let file = fs::File::create(leaf.join(format!("owned-budget-padding-{n}.bin"))).unwrap();
        file.set_len(12 * 1024 * 1024).unwrap();
        file.sync_all().unwrap();
    }
    let before = inventory(&leaf);
    let total: usize = before
        .values()
        .filter_map(Option::as_ref)
        .map(Vec::len)
        .sum();
    assert!(total > 32 * 1024 * 1024 && total < 128 * 1024 * 1024);

    match f
        .manager
        .full_comparison_resume(&f.lease, f.epoch, true, &cap, 1)
    {
        Err(error) => {
            assert_eq!(error, "EvaluationBudget");
            // A direct pre-admission refusal may retain the already inspected
            // previous report; it must not claim another running operation.
            assert_eq!(f.status(&cap)["running"], false);
        }
        Ok(started) => {
            let failed = f.done(token(&started));
            assert_eq!(failed["phase"], "failed");
            assert_eq!(failed["error"], "EvaluationBudget");
            assert_eq!(failed["running"], false);
            assert_eq!(failed["report_ready"], false);
        }
    }

    // Complete inventory includes both canonical DBs/WALs and all existing
    // invocation/admission/checkpoint files: no work may precede the refusal.
    assert!(inventory(&leaf) == before);
    assert!(f.manager.cleanup_complete());
    f.close(&cap);
}
