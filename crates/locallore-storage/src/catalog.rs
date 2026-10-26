// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
use crate::{Result, StorageError, Store};
use locallore::{
    contracts::{Scope, Seed},
    engine::Engine,
};
use rusqlite::{OptionalExtension, TransactionBehavior};

#[derive(Clone, Debug)]
pub struct StorySummary {
    pub scope: Scope,
    pub title: String,
    pub revision: u64,
    pub drafts: usize,
}
impl Store {
    /// Trusted caller supplies the fixed scope. An exact retry preserves all
    /// accepted history; it does not recreate or rewind an existing story.
    /// Identity is forgotten by explicit whole-story deletion, not tombstoned.
    pub fn create_workspace_exact(&mut self, title: &str, seed: Seed) -> Result<(Scope, bool)> {
        let (engine, seed_json) = Self::validated_story_input(title, seed)?;
        let seed = engine.seed();
        let scope = seed.scope.clone();
        let transaction = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let existing: Option<(String, String, i64, String)> = transaction
            .query_row(
                "SELECT root_branch,title,seed_version,seed_json FROM stories WHERE story_id=?1",
                [&scope.story],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
            )
            .optional()?;
        if let Some((root, original_title, version, original_json)) = existing {
            let original: Seed =
                serde_json::from_str(&original_json).map_err(|_| StorageError::Integrity)?;
            if original.scope.story != scope.story
                || original.scope.branch != root
                || i64::from(original.version) != version
                || Engine::new(original.clone()).is_err()
            {
                return Err(StorageError::Integrity);
            }
            if original_title != title || &original != seed {
                return Err(StorageError::DuplicateStory);
            }
            transaction.commit()?;
            return Ok((scope, false));
        }
        // A matching retry remains available at capacity. Count and insert
        // share this write transaction, including across separate Store owners.
        if transaction.query_row("SELECT count(*) FROM stories", [], |row| {
            row.get::<_, i64>(0)
        })? >= 256
        {
            return Err(StorageError::InvalidInput);
        }
        Self::insert_story(&transaction, title, &engine, &seed_json)?;
        transaction.commit()?;
        Ok((scope, true))
    }
    /// Bounded metadata only. No mutable projection, private prompt or raw connection escapes.
    pub fn stories(&mut self) -> Result<Vec<StorySummary>> {
        let tx = self.connection.transaction()?;
        let mut result = Vec::new();
        {
            // Random opaque IDs do not encode order. Row creation order is not authoritative;
            // deterministic ordering supports a stable default and explicit library selection.
            let mut q=tx.prepare("SELECT s.story_id,s.root_branch,s.title,b.head_revision,(SELECT count(*) FROM turns t WHERE t.story_id=s.story_id AND t.branch_id=s.root_branch AND t.status='draft') FROM stories s JOIN branches b ON b.story_id=s.story_id AND b.branch_id=s.root_branch ORDER BY s.story_id LIMIT 257")?;
            let mut rows = q.query([])?;
            while let Some(row) = rows.next()? {
                let revision: i64 = row.get(3)?;
                let drafts: i64 = row.get(4)?;
                result.push(StorySummary {
                    scope: Scope {
                        story: row.get(0)?,
                        branch: row.get(1)?,
                    },
                    title: row.get(2)?,
                    revision: revision.try_into().map_err(|_| StorageError::Integrity)?,
                    drafts: drafts.try_into().map_err(|_| StorageError::Integrity)?,
                });
                if result.len() > 256 {
                    return Err(StorageError::InvalidInput);
                }
            }
        }
        tx.commit()?;
        Ok(result)
    }
    /// Opaque story identity is allocated by the trusted owner, not display names or process IDs.
    /// Existing stories are never overwritten, including the improbable random-ID collision.
    pub fn create_workspace(&mut self, title: &str, mut seed: Seed) -> Result<Scope> {
        if self.stories()?.len() >= 256 {
            return Err(StorageError::InvalidInput);
        }
        for _ in 0..4 {
            let suffix: String =
                self.connection
                    .query_row("SELECT lower(hex(randomblob(16)))", [], |r| r.get(0))?;
            seed.scope.story = format!("quay-{suffix}");
            match self.create_story_bounded(title, seed.clone(), true) {
                Ok(()) => return Ok(seed.scope),
                Err(StorageError::DuplicateStory) => continue,
                Err(e) => return Err(e),
            }
        }
        Err(StorageError::DuplicateStory)
    }
}
