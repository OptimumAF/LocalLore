// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual connection-local SQLite FULL, never a forged return code or production knob.
use super::*;
use locallore::contracts::{Command, Intent, Seed};

#[test]
fn real_full_packet_publication_preserves_checkpoint_and_retry_publishes_once() {
    let root = std::env::temp_dir().join(format!(
        "locallore-memory-job-full-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir(&root).unwrap();
    let path = root.join("synthetic.sqlite");
    let mut store = Store::open(&path, None).unwrap();
    let seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
    let scope = seed.scope.clone();
    store.create_story("Synthetic job FULL", seed).unwrap();
    for turn in 0..4 {
        let engine = store.resume(&scope).unwrap().engine;
        let request = engine.request(
            &format!("job-full-{turn}"),
            Intent::Actions(
                (0..8)
                    .map(|event| Command::Say {
                        text: format!(
                            "Synthetic checkpoint pressure {turn}/{event}: {}",
                            "x".repeat(1800)
                        ),
                        audience: ["mira".into()].into(),
                    })
                    .collect(),
            ),
        );
        let receipt = engine
            .preview(&request, &Engine::proposal(&request).unwrap())
            .unwrap();
        store.begin_turn(&request).unwrap();
        store.commit_prepared(&receipt).unwrap();
    }
    let engine = store.resume(&scope).unwrap().engine;
    let canon = engine.canonical_bytes();
    let receipts = serde_json::to_vec(engine.receipts()).unwrap();
    let request = MemoryJobRequest {
        scope: scope.clone(),
        observer: "mira".into(),
        expected_head: engine.revision(),
    };
    let job = store.ensure_memory_job(&request, &|| false).unwrap();
    let prepared = store
        .prepare_memory_job_step(&job.handle, &|| false)
        .unwrap();
    let Step::Packet { bytes, .. } = &prepared.step else {
        panic!("fixture must prepare actual packet")
    };
    assert!(bytes.len() > 16 * 1024 && bytes.len() <= coverage::MAX_PACKET_BYTES);
    let pages: i64 = store
        .connection
        .pragma_query_value(None, "page_count", |r| r.get(0))
        .unwrap();
    let free: i64 = store
        .connection
        .pragma_query_value(None, "freelist_count", |r| r.get(0))
        .unwrap();
    assert_eq!(free, 0, "fixed fixture must need new packet overflow pages");
    store
        .connection
        .pragma_update(None, "max_page_count", pages)
        .unwrap();
    assert_eq!(
        store.publish_memory_job_step(prepared, &|| false).err(),
        Some(MemoryError::Full)
    );
    assert_eq!(
        store.memory_job_status(&job.handle, &|| false).unwrap(),
        job
    );
    assert_eq!(packets(&store.connection, &job.handle).unwrap().len(), 0);
    let after = store.resume(&scope).unwrap().engine;
    assert_eq!(after.canonical_bytes(), canon);
    assert_eq!(serde_json::to_vec(after.receipts()).unwrap(), receipts);
    drop(store);
    // The page cap is connection-local. Reopen normal Store, reissue native
    // capability and retry the same persisted boundary, without modifying canon.
    let mut store = Store::open(&path, None).unwrap();
    assert_eq!(
        store.memory_job_status(&job.handle, &|| false).err(),
        Some(MemoryError::NotFound)
    );
    let resumed = store.ensure_memory_job(&request, &|| false).unwrap();
    assert_eq!(
        (resumed.handle.id(), resumed.next_from, resumed.generation),
        (job.handle.id(), 0, job.generation)
    );
    let prepared = store
        .prepare_memory_job_step(&resumed.handle, &|| false)
        .unwrap();
    let published = store.publish_memory_job_step(prepared, &|| false).unwrap();
    assert!(published.next_from > 0);
    assert_eq!(published.generation, job.generation + 1);
    assert_eq!(
        packets(&store.connection, &resumed.handle).unwrap().len(),
        1
    );
    let proof = store.context_snapshot(&request, &|| false).unwrap();
    assert!(matches!(proof.coverage, CoverageRead::Verified(_)));
    assert_eq!(proof.engine.canonical_bytes(), canon);
    assert_eq!(
        serde_json::to_vec(proof.engine.receipts()).unwrap(),
        receipts
    );
    assert!(std::fs::metadata(&path).unwrap().len() < 1024 * 1024);
    // Keep bounded synthetic roots for inspection; no recursive cleanup hook.
}
