// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Public target admission, separate from private original-ancestry replay.
use crate::{Result, StorageError};
use locallore::contracts::Scope;
use rusqlite::Connection;

pub(crate) const SCHEMA_SQL: &str = include_str!("../migrations/003_branch_retention.sql");

pub(crate) fn retired(connection: &Connection, scope: &Scope) -> Result<bool> {
    // Historical read-only inspection remains available without migrating it.
    if crate::identity(connection)?.1 < 3 {
        return Ok(false);
    }
    Ok(connection.query_row(
        "SELECT EXISTS(SELECT 1 FROM branch_retention WHERE story_id=?1 AND branch_id=?2)",
        (&scope.story, &scope.branch),
        |row| row.get(0),
    )?)
}

pub(crate) fn admit(connection: &Connection, scope: &Scope) -> Result<()> {
    if retired(connection, scope)? {
        return Err(StorageError::NotFound);
    }
    Ok(())
}
