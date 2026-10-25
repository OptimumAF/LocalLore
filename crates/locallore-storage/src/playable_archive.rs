// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Full-private, accepted-history-only portable JSON. No file/model/network API.
use crate::{turns, StorageError, Store, TurnError, SCHEMA_VERSION};
use locallore::{
    author_correction::CanonicalRecord,
    contracts::{
        Error, Receipt, Scope, Seed, MAX_HISTORY_BYTES, MAX_HISTORY_RECEIPTS, MAX_RECEIPT_BYTES,
        VERSION,
    },
    engine::{parse_unique_json, AcceptedHistoryBasis, Engine},
    play::PlayProfile,
};
use rusqlite::{params, OptionalExtension, TransactionBehavior};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

/// Latest supported transfer format. Legacy histories still export as V1/V2;
/// accepting a format does not imply every host can open corrected timelines.
pub const ARCHIVE_VERSION: u16 = 3;
pub const SUPPORTED_ARCHIVE_VERSIONS: [u16; 3] = [1, 2, 3];
const ARCHIVE_VERSION_V1: u16 = 1;
const ARCHIVE_VERSION_V2: u16 = 2;
const ARCHIVE_VERSION_V3: u16 = 3;
pub const MAX_ARCHIVE_BYTES: usize = 32 * 1024 * 1024;
pub const MAX_ARCHIVE_BRANCHES: usize = 32;
pub const MAX_MODEL_REFERENCES: usize = 64;
const MAX_SEED_BYTES: usize = 131_072;
const MAX_PROJECTION_BYTES: usize = 262_144;
const FORMAT: &str = "locallore-playable-archive";
const CANONICALIZATION: &str = "locallore-json-v1";
const TRANSCRIPT: &str = "accepted_request_intent_and_narration_v1";
const TRANSCRIPT_V3: &str = "accepted_canonical_records_v2";
const WARNING: &str = "Full private story: all timelines, hidden seed facts, accepted input/narration and model/timing/provenance metadata. No weights, separate traces/raw prompt logs, caches or noncommitted workflow keys/status. Imported sessions must not resume old pending operations.";
const WARNING_V3: &str = "Full private story: all timelines, hidden seed facts, author corrections/reasons/prior truth, private discovery source bindings, accepted input/narration and model/timing/provenance metadata. Accepted records include play and author corrections. No weights, separate traces/raw prompts, caches or noncommitted workflow keys/status. Imported sessions must not resume old pending operations.";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ArchiveError {
    Malformed,
    Unsupported,
    Integrity,
    TooLarge,
    Conflict,
    Cancelled,
    Busy,
    Full,
    Database,
    NotFound,
}
type Result<T> = std::result::Result<T, ArchiveError>;
fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
impl From<rusqlite::Error> for ArchiveError {
    fn from(error: rusqlite::Error) -> Self {
        match error.sqlite_error_code() {
            Some(rusqlite::ErrorCode::DatabaseBusy | rusqlite::ErrorCode::DatabaseLocked) => {
                Self::Busy
            }
            Some(rusqlite::ErrorCode::DiskFull) => Self::Full,
            _ => Self::Database,
        }
    }
}
impl From<TurnError> for ArchiveError {
    fn from(error: TurnError) -> Self {
        match error {
            TurnError::TooLarge | TurnError::Engine(Error::TooLarge) => Self::TooLarge,
            TurnError::Full => Self::Full,
            TurnError::Storage(StorageError::Busy) => Self::Busy,
            TurnError::Storage(StorageError::NotFound) => Self::NotFound,
            TurnError::Engine(Error::Cancelled) => Self::Cancelled,
            TurnError::Integrity | TurnError::Engine(_) => Self::Integrity,
            TurnError::Storage(StorageError::Integrity | StorageError::SchemaMismatch) => {
                Self::Integrity
            }
            _ => Self::Database,
        }
    }
}
fn check(cancel: &dyn Fn() -> bool) -> Result<()> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(ArchiveError::Cancelled)
    } else {
        Ok(())
    }
}
fn valid_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 64
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
fn encode<T: Serialize>(value: &T) -> Result<Vec<u8>> {
    serde_json::to_vec(value).map_err(|_| ArchiveError::Malformed)
}
fn integer(value: u64) -> Result<i64> {
    i64::try_from(value).map_err(|_| ArchiveError::TooLarge)
}

/// Canonical checksum bytes: recursively sort object keys by Rust UTF-8 string
/// order, retain arrays, use serde_json scalar escaping/number encoding, no space.
/// Independent of serde_json's optional preserve_order feature. Not a signature.
fn canonical(value: &Value) -> Result<Vec<u8>> {
    fn append(value: &Value, out: &mut Vec<u8>) -> Result<()> {
        match value {
            Value::Object(map) => {
                out.push(b'{');
                let mut keys: Vec<_> = map.keys().collect();
                keys.sort_unstable();
                for (index, key) in keys.into_iter().enumerate() {
                    if index != 0 {
                        out.push(b',')
                    }
                    serde_json::to_writer(&mut *out, key).map_err(|_| ArchiveError::Malformed)?;
                    out.push(b':');
                    append(&map[key], out)?;
                }
                out.push(b'}');
            }
            Value::Array(values) => {
                out.push(b'[');
                for (index, value) in values.iter().enumerate() {
                    if index != 0 {
                        out.push(b',')
                    }
                    append(value, out)?;
                }
                out.push(b']');
            }
            _ => serde_json::to_writer(&mut *out, value).map_err(|_| ArchiveError::Malformed)?,
        }
        if out.len() > MAX_ARCHIVE_BYTES {
            return Err(ArchiveError::TooLarge);
        }
        Ok(())
    }
    let mut out = Vec::new();
    append(value, &mut out)?;
    Ok(out)
}
fn digest<T: Serialize>(value: &T) -> Result<String> {
    Ok(sha256(&canonical(
        &serde_json::to_value(value).map_err(|_| ArchiveError::Malformed)?,
    )?))
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Envelope {
    format: String,
    version: u16,
    canonicalization: String,
    privacy: String,
    payload: Payload,
    integrity: Integrity,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Payload {
    domain_version: u16,
    source_database_schema_version: u32,
    story: Story,
    transcript: String,
    branches: Vec<Branch>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    retired_branch_ids: Option<Vec<String>>,
    required_policies: Vec<Policy>,
    model_references: Vec<ModelReference>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Story {
    id: String,
    title: String,
    seed: Seed,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Branch {
    id: String,
    parent: Option<String>,
    fork_revision: Option<u64>,
    head_revision: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    local_receipts: Option<Vec<Value>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    local_records: Option<Vec<Value>>,
}
impl Branch {
    fn records(&self) -> &[Value] {
        // Version-specific field presence is checked before deserialization.
        self.local_records
            .as_deref()
            .or(self.local_receipts.as_deref())
            .unwrap_or_default()
    }
}
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Policy {
    policy: String,
    prompt_version: String,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct ModelReference {
    sha256: String,
    profile: PlayProfile,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Integrity {
    payload_sha256: String,
    seed_sha256: String,
    branches: Vec<BranchIntegrity>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct BranchIntegrity {
    id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    receipts_sha256: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    records_sha256: Option<String>,
    canonical_state_sha256: String,
}
impl BranchIntegrity {
    fn records_hash(&self) -> Option<&str> {
        self.records_sha256
            .as_deref()
            .or(self.receipts_sha256.as_deref())
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct ArchivePreview {
    pub version: u16,
    pub story_id: String,
    pub title: String,
    pub root_branch: String,
    pub branch_heads: BTreeMap<String, u64>,
    /// Retired physical rows are ancestry only; absent IDs remain deletion tombstones.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub retired_branch_ids: Vec<String>,
    /// Committed canonical records; v1/v2 contain only ordinary accepted turns.
    pub committed_turns: usize,
    pub bytes: usize,
    pub payload_sha256: String,
    pub privacy_warning: String,
    pub noncommitted_workflow_transferred: bool,
}
pub struct PlayableArchive {
    bytes: Vec<u8>,
    preview: ArchivePreview,
}
impl PlayableArchive {
    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }
    pub fn preview(&self) -> &ArchivePreview {
        &self.preview
    }
}
struct ValidatedBranch {
    branch: Branch,
    records: Vec<CanonicalRecord>,
    projection: Vec<u8>,
    basis: Option<AcceptedHistoryBasis>,
}
/// Opaque native capability: no public construction, mutation or Deserialize.
/// Carries validated original native canonical records, not supplied projections.
pub struct ValidatedArchive {
    story: Story,
    branches: Vec<ValidatedBranch>,
    retired_branch_ids: Vec<String>,
    preview: ArchivePreview,
}
impl ValidatedArchive {
    pub fn preview(&self) -> &ArchivePreview {
        &self.preview
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ImportOutcome {
    pub root: Scope,
    pub branches: usize,
    /// Committed canonical records, including author rows for Archive3.
    pub committed_turns: usize,
}

/// Keep v1/v2 field sets closed even though their native plan shares v3 types.
/// Explicit null or a second alternative is never a downgrade mechanism.
fn validate_version_fields(raw: &Value, version: u16) -> Result<()> {
    let payload = raw["payload"].as_object().ok_or(ArchiveError::Malformed)?;
    match version {
        ARCHIVE_VERSION_V1 if payload.contains_key("retired_branch_ids") => {
            return Err(ArchiveError::Malformed);
        }
        ARCHIVE_VERSION_V2
            if payload
                .get("retired_branch_ids")
                .and_then(Value::as_array)
                .is_none_or(Vec::is_empty) =>
        {
            return Err(ArchiveError::Malformed);
        }
        ARCHIVE_VERSION_V3
            if payload
                .get("retired_branch_ids")
                .and_then(Value::as_array)
                .is_none() =>
        {
            return Err(ArchiveError::Malformed);
        }
        _ => {}
    }
    let mixed = version == ARCHIVE_VERSION_V3;
    let (records, forbidden, checksum, forbidden_checksum) = if mixed {
        (
            "local_records",
            "local_receipts",
            "records_sha256",
            "receipts_sha256",
        )
    } else {
        (
            "local_receipts",
            "local_records",
            "receipts_sha256",
            "records_sha256",
        )
    };
    for branch in raw["payload"]["branches"]
        .as_array()
        .ok_or(ArchiveError::Malformed)?
    {
        let fields = branch.as_object().ok_or(ArchiveError::Malformed)?;
        if fields.contains_key(forbidden) || fields.get(records).and_then(Value::as_array).is_none()
        {
            return Err(ArchiveError::Malformed);
        }
    }
    for branch in raw["integrity"]["branches"]
        .as_array()
        .ok_or(ArchiveError::Malformed)?
    {
        let fields = branch.as_object().ok_or(ArchiveError::Malformed)?;
        if fields.contains_key(forbidden_checksum)
            || fields.get(checksum).and_then(Value::as_str).is_none()
        {
            return Err(ArchiveError::Malformed);
        }
    }
    Ok(())
}

fn request_bytes(record: &CanonicalRecord) -> Result<Vec<u8>> {
    if let Some(receipt) = record.receipt() {
        encode(receipt.request())
    } else {
        encode(&crate::author_correction::request_index(record)?)
    }
}

// Untrusted prefix selection only. Each complete physical branch is separately
// regenerated and raw-compared; this field cannot establish canonical authority.
fn expected_revision(raw: &Value, mixed: bool) -> Option<u64> {
    if mixed && raw.get("record_version").is_some() {
        if raw["kind"] == "author_correction" {
            raw["receipt"]["input"]["fork_revision"].as_u64()
        } else {
            raw["receipt"]["request"]["expected_revision"].as_u64()
        }
    } else {
        raw["request"]["expected_revision"].as_u64()
    }
}

fn path(branches: &[Branch], index: usize, root: &str) -> Result<Vec<usize>> {
    let mut out = Vec::new();
    let mut seen = BTreeSet::new();
    let mut index = index;
    loop {
        if out.len() >= crate::MAX_BRANCH_DEPTH || !seen.insert(index) {
            return Err(ArchiveError::Integrity);
        }
        out.push(index);
        let branch = &branches[index];
        if let Some(parent) = &branch.parent {
            let parent_index = branches
                .binary_search_by(|b| b.id.as_str().cmp(parent))
                .map_err(|_| ArchiveError::Integrity)?;
            if branch
                .fork_revision
                .is_none_or(|fork| fork > branches[parent_index].head_revision)
            {
                return Err(ArchiveError::Integrity);
            }
            index = parent_index;
        } else {
            if branch.id != root || branch.fork_revision.is_some() {
                return Err(ArchiveError::Integrity);
            }
            break;
        }
    }
    out.reverse();
    Ok(out)
}
fn replay(payload: &Payload, index: usize, cancel: &dyn Fn() -> bool) -> Result<Engine> {
    let path = path(&payload.branches, index, &payload.story.seed.scope.branch)?;
    let mut engine = None::<Engine>;
    let mut owner_bytes = 0usize;
    let mut owner_count = 0usize;
    for (position, index) in path.iter().copied().enumerate() {
        check(cancel)?;
        let branch = &payload.branches[index];
        let leaf = position + 1 == path.len();
        let cap = if leaf {
            branch.head_revision
        } else {
            branch.fork_revision.unwrap_or(0).max(
                payload.branches[path[position + 1]]
                    .fork_revision
                    .ok_or(ArchiveError::Integrity)?,
            )
        };
        let mut history = Vec::new();
        for receipt in branch.records() {
            check(cancel)?;
            if leaf
                || expected_revision(receipt, payload.domain_version == 2).is_some_and(|r| r < cap)
            {
                let encoded = encode(receipt)?;
                owner_bytes = owner_bytes
                    .checked_add(encoded.len())
                    .ok_or(ArchiveError::TooLarge)?;
                if payload.domain_version == VERSION {
                    // Preserve legacy accounting exactly. V3 counts its actual
                    // native request indexes after replay, never a null request.
                    owner_bytes = owner_bytes
                        .checked_add(encode(&receipt["request"])?.len())
                        .ok_or(ArchiveError::TooLarge)?;
                }
                owner_count += 1;
                if owner_bytes > MAX_HISTORY_BYTES || owner_count > MAX_HISTORY_RECEIPTS {
                    return Err(ArchiveError::TooLarge);
                }
                history.push(String::from_utf8(encoded).map_err(|_| ArchiveError::Malformed)?);
            }
        }
        let restored = if let Some(parent) = engine {
            parent
                .fork(
                    &branch.id,
                    branch.fork_revision.ok_or(ArchiveError::Integrity)?,
                )
                .and_then(|fork| fork.restore_continuation(&history))
        } else {
            Engine::restore(payload.story.seed.clone(), &history)
        }
        .map_err(|error| {
            if error == Error::TooLarge {
                ArchiveError::TooLarge
            } else {
                ArchiveError::Integrity
            }
        })?;
        if payload.domain_version == 2 {
            for record in restored
                .canonical_records()
                .iter()
                .filter(|record| record.original_scope().branch == branch.id)
            {
                check(cancel)?;
                owner_bytes = owner_bytes
                    .checked_add(request_bytes(record)?.len())
                    .ok_or(ArchiveError::TooLarge)?;
                if owner_bytes > MAX_HISTORY_BYTES {
                    return Err(ArchiveError::TooLarge);
                }
            }
        }
        if restored.revision() != cap {
            return Err(ArchiveError::Integrity);
        }
        engine = Some(restored);
    }
    engine.ok_or(ArchiveError::Integrity)
}

/// Retired physical branches carry only the ancestry required by active branches.
/// Garbage-collected identities remain in the separate list, never as invented history.
fn validate_retirement(payload: &Payload, cancel: &dyn Fn() -> bool) -> Result<()> {
    let retired = payload.retired_branch_ids.as_deref().unwrap_or_default();
    if retired.len() > crate::MAX_BRANCHES_PER_STORY {
        return Err(ArchiveError::TooLarge);
    }
    if retired.iter().any(|id| !valid_id(id))
        || retired.windows(2).any(|pair| pair[0] >= pair[1])
        || retired.contains(&payload.story.seed.scope.branch)
    {
        return Err(ArchiveError::Integrity);
    }
    let retired_set: BTreeSet<_> = retired.iter().map(String::as_str).collect();
    let union: BTreeSet<_> = retired_set
        .iter()
        .copied()
        .chain(payload.branches.iter().map(|branch| branch.id.as_str()))
        .collect();
    if union.len() > crate::MAX_BRANCHES_PER_STORY {
        return Err(ArchiveError::TooLarge);
    }
    let mut required_ancestors = BTreeSet::new();
    for (index, branch) in payload.branches.iter().enumerate() {
        check(cancel)?;
        if !retired_set.contains(branch.id.as_str()) {
            let ancestry = path(&payload.branches, index, &payload.story.seed.scope.branch)?;
            required_ancestors.extend(ancestry.into_iter().filter(|ancestor| *ancestor != index));
        }
    }
    for (index, branch) in payload.branches.iter().enumerate() {
        check(cancel)?;
        if !retired_set.contains(branch.id.as_str()) {
            continue;
        }
        if !required_ancestors.contains(&index) {
            return Err(ArchiveError::Integrity);
        }
        // A child may rewind before this parent's birth. Keep that birth floor
        // so the original fork remains verifiable without re-scoping any receipt.
        let mut cap = branch.fork_revision.unwrap_or_default();
        for child in &payload.branches {
            if child.parent.as_deref() == Some(branch.id.as_str()) {
                cap = cap.max(child.fork_revision.ok_or(ArchiveError::Integrity)?);
            }
        }
        if branch.head_revision != cap {
            return Err(ArchiveError::Integrity);
        }
    }
    Ok(())
}

fn references<'a>(
    receipts: impl Iterator<Item = &'a Receipt>,
) -> Result<(Vec<Policy>, Vec<ModelReference>)> {
    let mut policies = BTreeSet::new();
    let mut models = BTreeMap::new();
    for receipt in receipts {
        if let Some(play) = receipt.play() {
            policies.insert(Policy {
                policy: play.policy.clone(),
                prompt_version: play.prompt_version.clone(),
            });
            let hash = digest(&play.profile)?;
            models.insert(
                hash.clone(),
                ModelReference {
                    sha256: hash,
                    profile: play.profile.clone(),
                },
            );
            if models.len() > MAX_MODEL_REFERENCES {
                return Err(ArchiveError::TooLarge);
            }
        }
    }
    Ok((
        policies.into_iter().collect(),
        models.into_values().collect(),
    ))
}

/// Strict untrusted data validation; no database connection or file path is opened.
pub fn validate_archive(bytes: &[u8], cancel: &dyn Fn() -> bool) -> Result<ValidatedArchive> {
    check(cancel)?;
    let raw = parse_unique_json(bytes, MAX_ARCHIVE_BYTES).map_err(|e| {
        if e == Error::TooLarge {
            ArchiveError::TooLarge
        } else {
            ArchiveError::Malformed
        }
    })?;
    let version = raw["version"].as_u64().ok_or(ArchiveError::Unsupported)?;
    if raw["format"] != FORMAT
        || !matches!(version, 1 | 2 | 3)
        || raw["canonicalization"] != CANONICALIZATION
    {
        return Err(ArchiveError::Unsupported);
    }
    if version == u64::from(ARCHIVE_VERSION_V3)
        && (raw["payload"]["domain_version"] != 2
            || raw["payload"]["source_database_schema_version"] != 5
            || raw["payload"]["transcript"] != TRANSCRIPT_V3)
    {
        return Err(ArchiveError::Unsupported);
    }
    validate_version_fields(&raw, version as u16)?;
    let envelope: Envelope = serde_json::from_value(raw).map_err(|_| ArchiveError::Malformed)?;
    let payload = &envelope.payload;
    let mixed = envelope.version == ARCHIVE_VERSION_V3;
    if envelope.privacy != "full_private"
        || if mixed {
            payload.domain_version != 2 || payload.source_database_schema_version != 5
        } else {
            payload.domain_version != VERSION
                || !(1..=SCHEMA_VERSION).contains(&payload.source_database_schema_version)
                || envelope.version == ARCHIVE_VERSION_V2
                    && !(3..=5).contains(&payload.source_database_schema_version)
        }
        || payload.story.seed.version != VERSION
        || payload.transcript != if mixed { TRANSCRIPT_V3 } else { TRANSCRIPT }
    {
        return Err(ArchiveError::Unsupported);
    }
    if !valid_id(&payload.story.id)
        || payload.story.id != payload.story.seed.scope.story
        || !valid_id(&payload.story.seed.scope.branch)
        || payload.story.title.is_empty()
        || payload.story.title.chars().count() > 256
        || payload.story.title.contains('\0')
    {
        return Err(ArchiveError::Malformed);
    }
    if payload.branches.is_empty()
        || payload.branches.len() > MAX_ARCHIVE_BRANCHES
        || payload.model_references.len() > MAX_MODEL_REFERENCES
        || payload.required_policies.len() > MAX_MODEL_REFERENCES
        || encode(&payload.story.seed)?.len() > MAX_SEED_BYTES
    {
        return Err(ArchiveError::TooLarge);
    }
    if payload
        .retired_branch_ids
        .as_ref()
        .is_some_and(|ids| ids.len() > crate::MAX_BRANCHES_PER_STORY)
    {
        return Err(ArchiveError::TooLarge);
    }
    if envelope.integrity.payload_sha256 != digest(payload)?
        || envelope.integrity.seed_sha256 != digest(&payload.story.seed)?
        || envelope.integrity.branches.len() != payload.branches.len()
    {
        return Err(ArchiveError::Integrity);
    }
    let mut count = 0usize;
    let mut receipt_bytes = 0usize;
    for (index, branch) in payload.branches.iter().enumerate() {
        check(cancel)?;
        if !valid_id(&branch.id)
            || branch.parent.as_ref().is_some_and(|p| !valid_id(p))
            || index > 0 && payload.branches[index - 1].id >= branch.id
            || branch.parent.is_some() != branch.fork_revision.is_some()
            || branch
                .fork_revision
                .is_some_and(|fork| fork > branch.head_revision)
        {
            return Err(ArchiveError::Integrity);
        }
        if branch.head_revision > i64::MAX as u64 {
            return Err(ArchiveError::TooLarge);
        }
        path(&payload.branches, index, &payload.story.seed.scope.branch)?;
        for receipt in branch.records() {
            check(cancel)?;
            let size = encode(receipt)?.len();
            if size > MAX_RECEIPT_BYTES {
                return Err(ArchiveError::TooLarge);
            }
            receipt_bytes = receipt_bytes
                .checked_add(size)
                .ok_or(ArchiveError::TooLarge)?;
            count += 1;
            if receipt_bytes > MAX_HISTORY_BYTES || count > MAX_HISTORY_RECEIPTS {
                return Err(ArchiveError::TooLarge);
            }
        }
        let integrity = &envelope.integrity.branches[index];
        if integrity.id != branch.id
            || integrity.records_hash() != Some(digest(&branch.records())?.as_str())
        {
            return Err(ArchiveError::Integrity);
        }
    }
    validate_retirement(payload, cancel)?;
    let mut validated = Vec::new();
    let mut has_domain_two = false;
    let mut persisted_bytes = 0usize;
    for (index, branch) in payload.branches.iter().enumerate() {
        check(cancel)?;
        let engine = replay(payload, index, cancel)?;
        if !mixed && engine.domain_version() != VERSION {
            return Err(ArchiveError::Unsupported);
        }
        has_domain_two |= engine.domain_version() == 2;
        let local: Vec<_> = engine
            .canonical_records()
            .iter()
            .filter(|r| r.original_scope().branch == branch.id)
            .cloned()
            .collect();
        if local.len() != branch.records().len()
            || local
                .iter()
                .zip(branch.records())
                .any(|(r, v)| serde_json::to_value(r).ok().as_ref() != Some(v))
        {
            return Err(ArchiveError::Integrity);
        }
        if mixed {
            for record in &local {
                check(cancel)?;
                let input_size = request_bytes(record)?.len();
                persisted_bytes = persisted_bytes
                    .checked_add(encode(record)?.len())
                    .and_then(|total| total.checked_add(input_size))
                    .ok_or(ArchiveError::TooLarge)?;
                if persisted_bytes > MAX_HISTORY_BYTES {
                    return Err(ArchiveError::TooLarge);
                }
            }
        }
        let projection = engine.canonical_bytes();
        if projection.len() > MAX_PROJECTION_BYTES {
            return Err(ArchiveError::TooLarge);
        }
        if sha256(&projection) != envelope.integrity.branches[index].canonical_state_sha256 {
            return Err(ArchiveError::Integrity);
        }
        validated.push(ValidatedBranch {
            branch: branch.clone(),
            records: local,
            projection,
            // Do not add a new native-basis byte bound to historical v1/v2
            // admission. V3 explicitly requires complete source identity.
            basis: if mixed {
                Some(
                    engine
                        .accepted_history_basis()
                        .map_err(|error| ArchiveError::from(TurnError::Engine(error)))?,
                )
            } else {
                None
            },
        });
    }
    if mixed && !has_domain_two {
        return Err(ArchiveError::Unsupported);
    }
    let (policies, models) = references(
        validated
            .iter()
            .flat_map(|b| b.records.iter())
            .filter_map(CanonicalRecord::receipt),
    )?;
    if policies != payload.required_policies || models != payload.model_references {
        return Err(ArchiveError::Integrity);
    }
    check(cancel)?;
    let preview = ArchivePreview {
        version: envelope.version,
        story_id: payload.story.id.clone(),
        title: payload.story.title.clone(),
        root_branch: payload.story.seed.scope.branch.clone(),
        branch_heads: payload
            .branches
            .iter()
            .map(|b| (b.id.clone(), b.head_revision))
            .collect(),
        retired_branch_ids: payload.retired_branch_ids.clone().unwrap_or_default(),
        committed_turns: count,
        bytes: bytes.len(),
        payload_sha256: envelope.integrity.payload_sha256,
        privacy_warning: if mixed { WARNING_V3 } else { WARNING }.into(),
        noncommitted_workflow_transferred: false,
    };
    Ok(ValidatedArchive {
        story: payload.story.clone(),
        branches: validated,
        retired_branch_ids: payload.retired_branch_ids.clone().unwrap_or_default(),
        preview,
    })
}

impl Store {
    /// Capture every branch at one coherent SQLite snapshot. No file is written.
    pub fn export_archive(
        &mut self,
        story: &str,
        cancel: &dyn Fn() -> bool,
    ) -> Result<PlayableArchive> {
        check(cancel)?;
        if !valid_id(story) {
            return Err(ArchiveError::Malformed);
        }
        let tx = self.connection.transaction()?;
        let row: Option<(String, String)> = tx
            .query_row(
                "SELECT title,seed_json FROM stories WHERE story_id=?1",
                [story],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .optional()?;
        let (title, seed_json) = row.ok_or(ArchiveError::NotFound)?;
        let seed: Seed = serde_json::from_value(
            parse_unique_json(seed_json.as_bytes(), MAX_SEED_BYTES)
                .map_err(|_| ArchiveError::Integrity)?,
        )
        .map_err(|_| ArchiveError::Integrity)?;
        let source_database_schema_version =
            crate::identity(&tx).map_err(|_| ArchiveError::Database)?.1;
        let retired_branch_ids = if source_database_schema_version >= 3 {
            let mut query = tx.prepare(
                "SELECT branch_id FROM branch_retention WHERE story_id=?1 ORDER BY branch_id LIMIT ?2",
            )?;
            let ids = query
                .query_map(
                    params![story, (crate::MAX_BRANCHES_PER_STORY + 1) as i64],
                    |row| row.get::<_, String>(0),
                )?
                .collect::<std::result::Result<Vec<_>, _>>()?;
            if ids.len() > crate::MAX_BRANCHES_PER_STORY {
                return Err(ArchiveError::TooLarge);
            }
            ids
        } else {
            Vec::new()
        };
        let mut branches = Vec::new();
        let mut integrity = Vec::new();
        let mut records = Vec::new();
        let mut receipt_bytes = 0usize;
        let mut persisted_bytes = 0usize;
        let mut mixed = false;
        {
            let mut query=tx.prepare("SELECT branch_id,parent_branch,fork_revision,head_revision FROM branches WHERE story_id=?1 ORDER BY branch_id LIMIT ?2")?;
            let mut rows = query.query(params![story, (MAX_ARCHIVE_BRANCHES + 1) as i64])?;
            while let Some(row) = rows.next()? {
                check(cancel)?;
                if branches.len() >= MAX_ARCHIVE_BRANCHES {
                    return Err(ArchiveError::TooLarge);
                }
                let id: String = row.get(0)?;
                let parent: Option<String> = row.get(1)?;
                let fork: Option<i64> = row.get(2)?;
                let head: i64 = row.get(3)?;
                let scope = Scope {
                    story: story.into(),
                    branch: id.clone(),
                };
                let engine = turns::read_engine_retained(&tx, &scope)?.engine;
                mixed |= engine.domain_version() == 2;
                for record in engine
                    .canonical_records()
                    .iter()
                    .filter(|r| r.original_scope() == &scope)
                {
                    check(cancel)?;
                    let response_size = encode(record)?.len();
                    let input_size = request_bytes(record)?.len();
                    receipt_bytes = receipt_bytes
                        .checked_add(response_size)
                        .ok_or(ArchiveError::TooLarge)?;
                    persisted_bytes = persisted_bytes
                        .checked_add(response_size)
                        .and_then(|bytes| bytes.checked_add(input_size))
                        .ok_or(ArchiveError::TooLarge)?;
                    if receipt_bytes > MAX_HISTORY_BYTES {
                        return Err(ArchiveError::TooLarge);
                    }
                }
                let local_count = engine
                    .canonical_records()
                    .iter()
                    .filter(|r| r.original_scope() == &scope)
                    .count();
                if records.len().saturating_add(local_count) > MAX_HISTORY_RECEIPTS {
                    return Err(ArchiveError::TooLarge);
                }
                let local: Vec<_> = engine
                    .canonical_records()
                    .iter()
                    .filter(|r| r.original_scope() == &scope)
                    .cloned()
                    .collect();
                let values = local
                    .iter()
                    .map(serde_json::to_value)
                    .collect::<std::result::Result<Vec<_>, _>>()
                    .map_err(|_| ArchiveError::Integrity)?;
                integrity.push(BranchIntegrity {
                    id: id.clone(),
                    receipts_sha256: None,
                    records_sha256: Some(digest(&values)?),
                    canonical_state_sha256: sha256(&engine.canonical_bytes()),
                });
                records.extend(local);
                branches.push(Branch {
                    id,
                    parent,
                    fork_revision: fork
                        .map(u64::try_from)
                        .transpose()
                        .map_err(|_| ArchiveError::Integrity)?,
                    head_revision: u64::try_from(head).map_err(|_| ArchiveError::Integrity)?,
                    local_receipts: None,
                    local_records: Some(values),
                });
            }
        }
        if mixed && source_database_schema_version != 5 {
            return Err(ArchiveError::Unsupported);
        }
        if mixed && persisted_bytes > MAX_HISTORY_BYTES {
            return Err(ArchiveError::TooLarge);
        }
        let (policies, models) = references(records.iter().filter_map(CanonicalRecord::receipt))?;
        check(cancel)?;
        tx.commit()?;
        let version = if mixed {
            ARCHIVE_VERSION_V3
        } else if retired_branch_ids.is_empty() {
            ARCHIVE_VERSION_V1
        } else {
            ARCHIVE_VERSION_V2
        };
        if !mixed {
            for branch in &mut branches {
                branch.local_receipts = branch.local_records.take();
            }
            for branch in &mut integrity {
                branch.receipts_sha256 = branch.records_sha256.take();
            }
        }
        let payload = Payload {
            domain_version: if mixed { 2 } else { VERSION },
            source_database_schema_version,
            story: Story {
                id: story.into(),
                title,
                seed,
            },
            transcript: if mixed { TRANSCRIPT_V3 } else { TRANSCRIPT }.into(),
            branches,
            retired_branch_ids: if retired_branch_ids.is_empty() && !mixed {
                None
            } else {
                Some(retired_branch_ids)
            },
            required_policies: policies,
            model_references: models,
        };
        let envelope = Envelope {
            format: FORMAT.into(),
            version,
            canonicalization: CANONICALIZATION.into(),
            privacy: "full_private".into(),
            integrity: Integrity {
                payload_sha256: digest(&payload)?,
                seed_sha256: digest(&payload.story.seed)?,
                branches: integrity,
            },
            payload,
        };
        let bytes =
            canonical(&serde_json::to_value(envelope).map_err(|_| ArchiveError::Malformed)?)?;
        // Validate the captured immutable artifact outside the source read lock,
        // using exactly the same import contract. No source DB write occurs.
        let validated = validate_archive(&bytes, cancel)?;
        Ok(PlayableArchive {
            bytes,
            preview: validated.preview,
        })
    }

    /// Consume a validated native token. Existing identity ALWAYS conflicts,
    /// including identical data after an uncertain first acknowledgement.
    pub fn import_archive(
        &mut self,
        validated: ValidatedArchive,
        cancel: &dyn Fn() -> bool,
    ) -> Result<ImportOutcome> {
        check(cancel)?;
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        if tx
            .query_row(
                "SELECT 1 FROM stories WHERE story_id=?1",
                [&validated.story.id],
                |r| r.get::<_, i64>(0),
            )
            .optional()?
            .is_some()
        {
            return Err(ArchiveError::Conflict);
        }
        let count: i64 = tx.query_row("SELECT count(*) FROM stories", [], |r| r.get(0))?;
        if count >= 256 {
            return Err(ArchiveError::TooLarge);
        }
        let story = &validated.story;
        let seed = &story.seed;
        tx.execute("INSERT INTO stories(story_id,root_branch,title,seed_version,seed_json) VALUES(?1,?2,?3,1,?4)",params![story.id,seed.scope.branch,story.title,String::from_utf8(encode(seed)?).map_err(|_|ArchiveError::Malformed)?])?;
        for retired in &validated.retired_branch_ids {
            check(cancel)?;
            tx.execute(
                "INSERT INTO branch_retention(story_id,branch_id) VALUES(?1,?2)",
                params![story.id, retired],
            )?;
        }
        check(cancel)?;
        // Topological insertion, independent of canonical archive ID order.
        let mut pending: Vec<_> = (0..validated.branches.len()).collect();
        let mut inserted = BTreeSet::new();
        while !pending.is_empty() {
            let index = pending
                .iter()
                .position(|i| {
                    validated.branches[*i]
                        .branch
                        .parent
                        .as_ref()
                        .is_none_or(|p| inserted.contains(p))
                })
                .ok_or(ArchiveError::Integrity)?;
            let branch = &validated.branches[pending.remove(index)].branch;
            tx.execute("INSERT INTO branches(story_id,branch_id,parent_branch,fork_revision,head_revision) VALUES(?1,?2,?3,?4,?5)",params![story.id,branch.id,branch.parent,branch.fork_revision.map(integer).transpose()?,integer(branch.head_revision)?])?;
            inserted.insert(branch.id.clone());
            check(cancel)?;
        }
        for (kind, ids) in [
            ("actor", seed.actors.keys().collect::<Vec<_>>()),
            ("item", seed.items.keys().collect()),
            ("location", seed.locations.iter().collect()),
            ("ability", seed.abilities.keys().collect()),
            ("fact", seed.facts.keys().collect()),
            ("commitment", seed.commitments.keys().collect()),
        ] {
            for id in ids {
                check(cancel)?;
                tx.execute(
                    "INSERT INTO entities(story_id,kind,entity_id) VALUES(?1,?2,?3)",
                    params![story.id, kind, id],
                )?;
                for branch in &validated.branches {
                    tx.execute("INSERT INTO branch_entities(story_id,branch_id,kind,entity_id) VALUES(?1,?2,?3,?4)",params![story.id,branch.branch.id,kind,id])?;
                }
            }
        }
        for branch in &validated.branches {
            check(cancel)?;
            for record in &branch.records {
                check(cancel)?;
                if matches!(record, CanonicalRecord::AuthorV1(_)) {
                    crate::author_correction::insert_author_record(&tx, record)?;
                    continue;
                }
                let receipt = record.receipt().ok_or(ArchiveError::Integrity)?;
                let request = receipt.request();
                tx.execute("INSERT INTO turns(story_id,branch_id,turn_id,expected_revision,status,request_json,response_json,canonical_kind) VALUES(?1,?2,?3,?4,'committed',?5,?6,?7)",params![story.id,branch.branch.id,request.turn,integer(request.expected_revision)?,String::from_utf8(encode(request)?).map_err(|_|ArchiveError::Malformed)?,String::from_utf8(encode(record)?).map_err(|_|ArchiveError::Malformed)?,turns::canonical_kind(record)])?;
                turns::insert_play_events(
                    &tx,
                    receipt,
                    &|| check(cancel).map_err(|_| TurnError::Engine(Error::Cancelled)),
                    &|| Ok(()),
                )?;
            }
        }
        for branch in &validated.branches {
            check(cancel)?;
            let scope = Scope {
                story: story.id.clone(),
                branch: branch.branch.id.clone(),
            };
            let restored = turns::read_engine_retained(&tx, &scope)?;
            let retired = validated
                .retired_branch_ids
                .binary_search(&scope.branch)
                .is_ok();
            if restored.engine.canonical_bytes() != branch.projection
                || restored.engine.revision() != branch.branch.head_revision
                || !restored
                    .engine
                    .canonical_records()
                    .iter()
                    .filter(|record| record.original_scope() == &scope)
                    .eq(branch.records.iter())
            {
                return Err(ArchiveError::Integrity);
            }
            if let Some(basis) = &branch.basis {
                if restored
                    .engine
                    .accepted_history_basis()
                    .map_err(|error| ArchiveError::from(TurnError::Engine(error)))?
                    != *basis
                {
                    return Err(ArchiveError::Integrity);
                }
            }
            // Rebuild only active caches from the just-verified actual Store
            // engine. Retired ancestry stays cache-free, as with real deletion.
            if !retired {
                turns::write_projection(&tx, &restored.engine)?;
                let cached: (i64, u16, String) = tx.query_row(
                    "SELECT revision,projection_version,projection_json FROM branch_projections WHERE story_id=?1 AND branch_id=?2",
                    params![scope.story, scope.branch],
                    |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
                )?;
                if cached.0 != integer(branch.branch.head_revision)?
                    || cached.1 != restored.engine.domain_version()
                    || cached.2.as_bytes() != branch.projection
                {
                    return Err(ArchiveError::Integrity);
                }
            }
        }
        check(cancel)?;
        tx.commit()?;
        Ok(ImportOutcome {
            root: seed.scope.clone(),
            branches: validated.branches.len(),
            committed_turns: validated.preview.committed_turns,
        })
    }
}
