//! Query2-only lossless display numbers. Canonical rows and Query1 stay numeric.
use super::*;
use serde::ser::{SerializeSeq, SerializeStruct};

pub(super) fn serialize_page<S: serde::Serializer>(
    page: &Page,
    serializer: S,
) -> Result<S::Ok, S::Error> {
    let mut wire = serializer.serialize_struct("Page", 13)?;
    wire.serialize_field("version", &page.version)?;
    wire.serialize_field("scope", &page.scope)?;
    wire.serialize_field("head", &page.head)?;
    wire.serialize_field("revision", &page.revision)?;
    wire.serialize_field("story_time", &page.story_time)?;
    wire.serialize_field("observer", &page.observer)?;
    wire.serialize_field("view", &page.view)?;
    wire.serialize_field("privacy", &page.privacy)?;
    wire.serialize_field("status", &page.status)?;
    wire.serialize_field("total", &page.total)?;
    if page.version == 2 {
        wire.serialize_field("rows", &Query2Rows(&page.rows))?;
    } else {
        wire.serialize_field("rows", &page.rows)?;
    }
    wire.serialize_field("next_cursor", &page.next_cursor)?;
    wire.serialize_field("unsupported", &page.unsupported)?;
    wire.end()
}

struct Query2Rows<'a>(&'a [Row]);
impl Serialize for Query2Rows<'_> {
    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let mut wire = serializer.serialize_seq(Some(self.0.len()))?;
        for row in self.0 {
            wire.serialize_element(&Query2Row(row))?;
        }
        wire.end()
    }
}

// This wrapper is also used before search/cursor hashing/page-byte accounting.
// Serialize fields in their original order: scoped event lookup binds that prefix.
pub(super) struct Query2Row<'a>(pub(super) &'a Row);
impl Serialize for Query2Row<'_> {
    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        match self.0 {
            Row::Promise {
                key,
                id,
                from,
                to,
                terms,
                deadline,
                status,
                return_item,
                sources,
                origin,
            } => {
                let mut wire = serializer.serialize_struct("Row", 11)?;
                wire.serialize_field("kind", "promise")?;
                wire.serialize_field("key", key)?;
                wire.serialize_field("id", id)?;
                wire.serialize_field("from", from)?;
                wire.serialize_field("to", to)?;
                wire.serialize_field("terms", terms)?;
                wire.serialize_field("deadline", &deadline.to_string())?;
                wire.serialize_field("status", status)?;
                wire.serialize_field("return_item", return_item)?;
                wire.serialize_field("sources", sources)?;
                wire.serialize_field("origin", origin)?;
                wire.end()
            }
            Row::Event { key, event, origin }
                if matches!(event.consequence, Effect::Promised { .. }) =>
            {
                let mut wire = serializer.serialize_struct("Row", 4)?;
                wire.serialize_field("kind", "event")?;
                wire.serialize_field("key", key)?;
                wire.serialize_field("event", &Query2Event(event))?;
                wire.serialize_field("origin", origin)?;
                wire.end()
            }
            Row::Change {
                key,
                before_revision,
                after_revision,
                before,
                after,
                origin,
            } => {
                let mut wire = serializer.serialize_struct("Row", 7)?;
                wire.serialize_field("kind", "change")?;
                wire.serialize_field("key", key)?;
                wire.serialize_field("before_revision", before_revision)?;
                wire.serialize_field("after_revision", after_revision)?;
                wire.serialize_field("before", &before.as_deref().map(Query2Row))?;
                wire.serialize_field("after", &after.as_deref().map(Query2Row))?;
                wire.serialize_field("origin", origin)?;
                wire.end()
            }
            row => row.serialize(serializer),
        }
    }
}

struct Query2Event<'a>(&'a EventRow);
impl Serialize for Query2Event<'_> {
    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let mut wire = serializer.serialize_struct("EventRow", 7)?;
        wire.serialize_field("sequence", &self.0.sequence)?;
        wire.serialize_field("scope", &self.0.scope)?;
        wire.serialize_field("turn", &self.0.turn)?;
        wire.serialize_field("story_time", &self.0.story_time)?;
        wire.serialize_field("participants", &self.0.participants)?;
        wire.serialize_field("witnesses", &self.0.witnesses)?;
        wire.serialize_field("consequence", &Query2Consequence(&self.0.consequence))?;
        wire.end()
    }
}

struct Query2Consequence<'a>(&'a Effect);
impl Serialize for Query2Consequence<'_> {
    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        if let Effect::Promised { id, commitment } = self.0 {
            let mut wire = serializer.serialize_struct("Effect", 3)?;
            wire.serialize_field("effect", "promised")?;
            wire.serialize_field("id", id)?;
            wire.serialize_field("commitment", &Query2Commitment(commitment))?;
            wire.end()
        } else {
            self.0.serialize(serializer)
        }
    }
}

struct Query2Commitment<'a>(&'a Commitment);
impl Serialize for Query2Commitment<'_> {
    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let mut wire = serializer.serialize_struct("Commitment", 7)?;
        wire.serialize_field("from", &self.0.from)?;
        wire.serialize_field("to", &self.0.to)?;
        wire.serialize_field("terms", &self.0.terms)?;
        wire.serialize_field("deadline", &self.0.deadline.to_string())?;
        wire.serialize_field("source", &self.0.source)?;
        wire.serialize_field("return_item", &self.0.return_item)?;
        wire.serialize_field("completed_by", &self.0.completed_by)?;
        wire.end()
    }
}
