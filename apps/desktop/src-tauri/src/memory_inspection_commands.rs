// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Bounded native read-only transport. Core owns source, player and cache proof.
use crate::{lease::WindowLease, WorkspaceState};
use locallore::{
    contracts::Scope,
    engine::parse_unique_json,
    host::{memory_inspection::{MemoryInspectionError, MemoryInspectionRequestV1, MemoryInspectionViewV1}, Host},
    inspection_query::Observer,
    memory_coverage::SourceRef,
};
use serde_json::{Map, Value};
use std::sync::{atomic::{AtomicBool, Ordering}, Arc};

const MAX_REQUEST: usize = 4096;
const MAX_REPLY: usize = 65_536;
const MAX_INTEGER: u64 = 9_007_199_254_740_991;
static READING: AtomicBool = AtomicBool::new(false);

// One nonwaiting read across all windows. It bounds concurrent snapshot/hash
// work; it is neither a retained reader capability nor permission to read.
struct ReadPermit;
impl ReadPermit {
    fn acquire() -> Result<Self, String> {
        READING.compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .map(|_| Self).map_err(|_| "Busy".into())
    }
}
impl Drop for ReadPermit {
    fn drop(&mut self) { READING.store(false, Ordering::Release); }
}

struct ReadRequest {
    session: String,
    query: MemoryInspectionRequestV1,
}
fn object<'a>(value: &'a Value, keys: &[&str]) -> Result<&'a Map<String, Value>, String> {
    let value = value.as_object().ok_or("InvalidInput")?;
    if value.len() != keys.len() || !keys.iter().all(|key| value.contains_key(*key)) {
        return Err("InvalidInput".into());
    }
    Ok(value)
}
fn identifier(value: &Value) -> Result<String, String> {
    let value = value.as_str().ok_or("InvalidInput")?;
    if value.is_empty() || value.len() > 64 || !value.bytes().all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b)) {
        return Err("InvalidInput".into());
    }
    Ok(value.into())
}
fn scope(value: &Value) -> Result<Scope, String> {
    let value = object(value, &["story", "branch"])?;
    Ok(Scope { story: identifier(&value["story"])?, branch: identifier(&value["branch"])? })
}
fn integer(value: &Value, minimum: u64, maximum: u64) -> Result<u64, String> {
    let value = value.as_u64().ok_or("InvalidInput")?;
    if value < minimum || value > maximum { return Err("InvalidInput".into()); }
    Ok(value)
}
fn hex(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}
fn binding(value: &Value) -> Result<Option<String>, String> {
    if value.is_null() { return Ok(None); }
    let value = value.as_str().ok_or("InvalidInput")?;
    if !hex(value) { return Err("InvalidInput".into()); }
    Ok(Some(value.into()))
}
fn cursor(value: &Value) -> Result<Option<String>, String> {
    if value.is_null() { return Ok(None); }
    let value = value.as_str().ok_or("InvalidInput")?;
    let parts = value.split(':').collect::<Vec<_>>();
    if value.len() > 128 || parts.len() != 3 || parts[0] != "mp1" || parts[1].starts_with('0')
        || parts[1].is_empty() || !parts[1].bytes().all(|byte| byte.is_ascii_digit())
        || parts[1].parse::<u64>().ok().is_none_or(|offset| offset == 0 || offset > MAX_INTEGER)
        || !hex(parts[2]) {
        return Err("InvalidCursor".into());
    }
    Ok(Some(value.into()))
}
fn observer(value: &Value) -> Result<Observer, String> {
    let map = value.as_object().ok_or("InvalidInput")?;
    match map.get("kind").and_then(Value::as_str) {
        Some("player") => { object(value, &["kind"])?; Ok(Observer::Player) }
        Some("omniscient") => { object(value, &["kind"])?; Err("Forbidden".into()) }
        Some("character") => {
            object(value, &["kind", "id"])?;
            identifier(&map["id"])?;
            Err("Forbidden".into())
        }
        _ => Err("InvalidInput".into()),
    }
}
impl ReadRequest {
    fn parse(action: &str, raw: &str) -> Result<Self, String> {
        if raw.len() > MAX_REQUEST { return Err("TooLarge".into()); }
        let keys: &[&str] = match action {
            "packets" => &["version", "session", "scope", "expected_head", "observer", "binding", "cursor", "limit"],
            "entries" => &["version", "session", "scope", "expected_head", "observer", "binding", "packet_index", "cursor", "limit"],
            "source" => &["version", "session", "scope", "expected_head", "observer", "binding", "packet_index", "source"],
            _ => return Err("InvalidInput".into()),
        };
        let value = parse_unique_json(raw.as_bytes(), MAX_REQUEST).map_err(|_| "InvalidInput")?;
        let value = object(&value, keys)?;
        if integer(&value["version"], 0, MAX_INTEGER)? != 1 { return Err("Version".into()); }
        let session = identifier(&value["session"])?;
        let scope = scope(&value["scope"])?;
        let expected_head = integer(&value["expected_head"], 0, MAX_INTEGER)?;
        let observer = observer(&value["observer"])?;
        let binding = binding(&value["binding"])?;
        let view = match action {
            "packets" | "entries" => {
                let cursor = cursor(&value["cursor"])?;
                if cursor.is_some() && binding.is_none() { return Err("InvalidCursor".into()); }
                let limit = integer(&value["limit"], 1, 64)? as u16;
                if action == "packets" { MemoryInspectionViewV1::Packets { cursor, limit } }
                else {
                    if binding.is_none() { return Err("InvalidInput".into()); }
                    MemoryInspectionViewV1::Entries { packet_index: integer(&value["packet_index"], 0, 31)? as u8, cursor, limit }
                }
            }
            "source" => {
                if binding.is_none() { return Err("InvalidInput".into()); }
                let source = object(&value["source"], &["scope", "sequence"])?;
                MemoryInspectionViewV1::Source {
                    packet_index: integer(&value["packet_index"], 0, 31)? as u8,
                    source: SourceRef { scope: self::scope(&source["scope"])?, sequence: integer(&source["sequence"], 1, expected_head)? },
                }
            }
            _ => return Err("InvalidInput".into()),
        };
        Ok(Self { session, query: MemoryInspectionRequestV1 { version: 1, scope, expected_head, observer, binding, view } })
    }
}
fn category(error: MemoryInspectionError) -> String {
    use MemoryInspectionError::*;
    match error {
        Version => "Version", Forbidden => "Forbidden", Closed => "Closed", Scope => "Scope",
        Stale => "Stale", Unsupported => "Unsupported", InvalidInput => "InvalidInput",
        InvalidCursor => "InvalidCursor", Binding => "Binding", TooLarge => "TooLarge",
        Cancelled => "Cancelled", Integrity => "Integrity", Unavailable => "Unavailable",
        Busy => "Busy", Database => "Database", Full => "Full", Internal => "Internal",
    }.into()
}

// Actual command and native service tests share this exact read/publication path.
fn read_owned(host: Arc<Host>, lease: Arc<WindowLease>, epoch: u64, request: ReadRequest, _permit: ReadPermit) -> Result<Value, String> {
    if !lease.valid(epoch) { return Err("Closed".into()); }
    let result = host.memory_inspection(&request.session, &request.query, &|| !lease.valid(epoch));
    if !lease.valid(epoch) { return Err("Closed".into()); }
    let reply = result.map_err(category)?;
    let bytes = serde_json::to_vec(&reply).map_err(|_| "Internal")?;
    if bytes.len() > MAX_REPLY { return Err("TooLarge".into()); }
    let value = serde_json::from_slice(&bytes).map_err(|_| "Internal")?;
    // Only bounded publication runs under dispatch, never Host/Store IO or hash.
    lease.dispatch(epoch, || Ok(value))
}

#[tauri::command]
pub async fn memory_inspection(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    action: String,
    request: String,
) -> Result<Value, String> {
    let epoch = workspace.lease.capture(window.label()).map_err(str::to_owned)?;
    let request = ReadRequest::parse(&action, &request)?;
    let permit = ReadPermit::acquire()?;
    let host = workspace.get(epoch).await?;
    let lease = workspace.lease.clone();
    if !lease.valid(epoch) { return Err("Closed".into()); }
    tauri::async_runtime::spawn_blocking(move || read_owned(host, lease, epoch, request, permit))
        .await.map_err(|_| "Internal".to_owned())?
}

#[cfg(test)]
mod tests;
