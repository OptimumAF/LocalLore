// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent frozen historical read regression. No migration or app SQL path.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{Store, TurnPhase};
use rusqlite::{params, Connection};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture {
    directory: PathBuf,
    path: PathBuf,
    engine: Engine,
    receipt: Receipt,
    draft: Request,
}
impl Fixture {
    fn historical(version: u32) -> Self {
        assert!((1..=4).contains(&version));
        let directory = std::env::temp_dir().join(format!(
            "locallore-m08-historical-read-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        let path = directory.join("synthetic.sqlite");
        let seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        let mut engine = Engine::new(seed).unwrap();
        let request = engine.request(
            "completed",
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        let proposal = Engine::proposal(&request).unwrap();
        let preview = engine.preview(&request, &proposal).unwrap();
        let receipt = engine.commit_prepared(&preview).unwrap();
        let draft = engine.request(
            "interrupted-draft",
            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
        );
        {
            let mut db = Connection::open(&path).unwrap();
            db.pragma_update(None, "foreign_keys", true).unwrap();
            db.execute_batch(include_str!("../migrations/001_initial.sql"))
                .unwrap();
            if version >= 2 {
                db.execute_batch(include_str!("../migrations/002_derived_memory.sql"))
                    .unwrap();
            }
            if version >= 3 {
                db.execute_batch(include_str!("../migrations/003_branch_retention.sql"))
                    .unwrap();
            }
            if version >= 4 {
                db.execute_batch(include_str!("../migrations/004_memory_jobs.sql"))
                    .unwrap();
            }
            db.pragma_update(None, "application_id", 0x4c4c4f52_u32)
                .unwrap();
            db.pragma_update(None, "user_version", version).unwrap();
            let tx = db.transaction().unwrap();
            let seed = engine.seed();
            let scope = engine.scope();
            tx.execute("INSERT INTO stories(story_id,root_branch,title,seed_version,seed_json) VALUES(?1,?2,'Synthetic historical read',1,?3)",params![scope.story,scope.branch,serde_json::to_string(seed).unwrap()]).unwrap();
            tx.execute(
                "INSERT INTO branches(story_id,branch_id,head_revision) VALUES(?1,?2,1)",
                params![scope.story, scope.branch],
            )
            .unwrap();
            for (kind, ids) in [
                ("actor", seed.actors.keys().collect::<Vec<_>>()),
                ("item", seed.items.keys().collect()),
                ("location", seed.locations.iter().collect()),
                ("ability", seed.abilities.keys().collect()),
                ("fact", seed.facts.keys().collect()),
                ("commitment", seed.commitments.keys().collect()),
            ] {
                for id in ids {
                    tx.execute(
                        "INSERT INTO entities(story_id,kind,entity_id) VALUES(?1,?2,?3)",
                        params![scope.story, kind, id],
                    )
                    .unwrap();
                    tx.execute("INSERT INTO branch_entities(story_id,branch_id,kind,entity_id) VALUES(?1,?2,?3,?4)",params![scope.story,scope.branch,kind,id]).unwrap();
                }
            }
            // Fixture data comes only from actual Core generation/validation.
            // No current Store migration is run to manufacture an old schema.
            tx.execute("INSERT INTO turns(story_id,branch_id,turn_id,expected_revision,status,request_json,response_json) VALUES(?1,?2,?3,0,'committed',?4,?5)",params![scope.story,scope.branch,request.turn,serde_json::to_string(&request).unwrap(),serde_json::to_string(&receipt).unwrap()]).unwrap();
            tx.execute("INSERT INTO turns(story_id,branch_id,turn_id,expected_revision,status,request_json,response_json) VALUES(?1,?2,?3,1,'draft',?4,NULL)",params![scope.story,scope.branch,draft.turn,serde_json::to_string(&draft).unwrap()]).unwrap();
            for event in receipt.events() {
                tx.execute("INSERT INTO accepted_events(story_id,branch_id,sequence,turn_id,event_version,envelope_json) VALUES(?1,?2,?3,?4,1,?5)",params![scope.story,scope.branch,event.sequence(),request.turn,serde_json::to_string(event).unwrap()]).unwrap();
                for observer in event.witnesses() {
                    tx.execute("INSERT INTO event_witnesses(story_id,branch_id,sequence,observer_id) VALUES(?1,?2,?3,?4)",params![scope.story,scope.branch,event.sequence(),observer]).unwrap();
                }
            }
            tx.execute("INSERT INTO branch_projections(story_id,branch_id,revision,projection_version,projection_json) VALUES(?1,?2,1,1,?3)",params![scope.story,scope.branch,String::from_utf8(engine.canonical_bytes()).unwrap()]).unwrap();
            tx.commit().unwrap();
            assert_eq!(
                db.query_row("PRAGMA foreign_key_check", [], |_| Ok(()))
                    .optional()
                    .unwrap(),
                None
            );
        }
        Self {
            directory,
            path,
            engine,
            receipt,
            draft,
        }
    }
    fn bytes(&self) -> Vec<u8> {
        std::fs::read(&self.path).unwrap()
    }
    fn read(&self, version: u32) -> Store {
        let mut store = Store::open_read_only(&self.path).unwrap();
        assert_eq!(store.info().unwrap().schema_version, version);
        assert_eq!(
            store
                .resume(self.engine.scope())
                .unwrap()
                .engine
                .accepted_history_basis()
                .unwrap(),
            self.engine.accepted_history_basis().unwrap()
        );
        store
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.directory).unwrap();
    }
}
use rusqlite::OptionalExtension;

#[test]
fn known_historical_versions_completed_status_retains_original_receipt_without_migration() {
    for version in 1..=4 {
        let fixture = Fixture::historical(version);
        let before = fixture.bytes();
        let mut store = fixture.read(version);
        let result = store.turn_status(fixture.receipt.request()).unwrap();
        assert_eq!(result.phase, TurnPhase::Committed);
        assert_eq!(result.request, *fixture.receipt.request());
        assert_eq!(result.receipt, Some(fixture.receipt.clone()));
        drop(store);
        assert_eq!(
            fixture.bytes(),
            before,
            "schema{version} read must not migrate or rewrite"
        );
    }
}

#[test]
fn known_historical_versions_completed_lookup_retains_original_receipt_without_migration() {
    for version in 1..=4 {
        let fixture = Fixture::historical(version);
        let before = fixture.bytes();
        let mut store = fixture.read(version);
        let result = store
            .lookup_turn(fixture.engine.scope(), "completed")
            .unwrap();
        assert_eq!(result.phase, TurnPhase::Committed);
        assert_eq!(result.request, *fixture.receipt.request());
        assert_eq!(result.receipt, Some(fixture.receipt.clone()));
        drop(store);
        assert_eq!(
            fixture.bytes(),
            before,
            "schema{version} read must not migrate or rewrite"
        );
    }
}

#[test]
fn known_historical_versions_draft_status_lookup_and_listing_remain_read_only() {
    for version in 1..=4 {
        let fixture = Fixture::historical(version);
        let before = fixture.bytes();
        let mut store = fixture.read(version);
        let status = store.turn_status(&fixture.draft).unwrap();
        assert_eq!(status.phase, TurnPhase::Draft);
        assert_eq!(status.request, fixture.draft);
        assert!(status.receipt.is_none());
        let found = store
            .lookup_turn(fixture.engine.scope(), &fixture.draft.turn)
            .unwrap();
        assert_eq!(found.phase, TurnPhase::Draft);
        assert_eq!(found.request, fixture.draft);
        assert!(found.receipt.is_none());
        let drafts = store.drafts(fixture.engine.scope()).unwrap();
        assert_eq!(drafts.len(), 1);
        assert_eq!(drafts[0].request, fixture.draft);
        assert_eq!(drafts[0].phase, TurnPhase::Draft);
        assert!(drafts[0].receipt.is_none());
        drop(store);
        assert_eq!(
            fixture.bytes(),
            before,
            "schema{version} read must not migrate or rewrite"
        );
    }
}
