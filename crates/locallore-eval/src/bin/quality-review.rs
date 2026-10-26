// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Explicit private assessment packets for existing synthetic comparison evidence.
//! Never runs inference, changes a comparison, or accepts model quality.
#[path = "quality_review/contract.rs"]
mod contract;

use locallore::inspection_query::Observer;
use locallore_eval::{
    digest,
    local_lane::comparison::desktop_api::{self as reader, Arm, EvidenceRequest, RowId},
};
use serde_json::{json, Value};
use std::{
    ffi::{OsStr, OsString},
    fs::{self, Metadata, OpenOptions},
    io::{Read, Write},
    path::{Component, Path, PathBuf},
};

const CONSENT: &str = "--allow-synthetic-author-evidence";
type Result<T> = std::result::Result<T, &'static str>;

struct Arguments {
    run: PathBuf,
    file: PathBuf,
    max_turns: Option<usize>,
}

fn arguments(args: Vec<OsString>) -> Result<Arguments> {
    // Refuse before querying even the existence of a source or destination.
    let consent_count = args.iter().filter(|s| *s == OsStr::new(CONSENT)).count();
    if consent_count == 0 {
        return Err("ConsentRequired");
    }
    if consent_count != 1 || !(4..=6).contains(&args.len()) {
        return Err("Usage");
    }
    let template = match args[0].to_str() {
        Some("template") => true,
        Some("summarize") => false,
        _ => return Err("Usage"),
    };
    if args[1].is_empty()
        || args[2].is_empty()
        || args[1].to_string_lossy().starts_with("--")
        || args[2].to_string_lossy().starts_with("--")
    {
        return Err("Usage");
    }
    let mut maximum = None;
    let mut index = 3;
    while index < args.len() {
        if args[index] == OsStr::new(CONSENT) {
            index += 1;
        } else if template && args[index] == OsStr::new("--max-turns") && maximum.is_none() {
            let value = args
                .get(index + 1)
                .and_then(|s| s.to_str())
                .ok_or("Usage")?;
            if value.len() != 1 || !(b'1'..=b'8').contains(&value.as_bytes()[0]) {
                return Err("TurnBudget");
            }
            maximum = Some(usize::from(value.as_bytes()[0] - b'0'));
            index += 2;
        } else {
            return Err("Usage");
        }
    }
    Ok(Arguments {
        run: args[1].clone().into(),
        file: args[2].clone().into(),
        max_turns: template.then_some(maximum.unwrap_or(4)),
    })
}

fn is_reparse(metadata: &Metadata) -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        metadata.file_attributes() & 0x400 != 0
    }
    #[cfg(not(windows))]
    {
        let _ = metadata;
        false
    }
}

fn absolute(path: &Path) -> Result<PathBuf> {
    if path.components().any(|part| {
        matches!(part, Component::ParentDir)
            || matches!(part, Component::Normal(name) if name.to_string_lossy().contains(':'))
    }) {
        return Err("Path");
    }
    #[cfg(windows)]
    for component in path.components() {
        match component {
            Component::Prefix(prefix)
                if !matches!(
                    prefix.kind(),
                    std::path::Prefix::Disk(_) | std::path::Prefix::VerbatimDisk(_)
                ) =>
            {
                return Err("Path");
            }
            Component::Normal(name) => {
                let token = name.to_string_lossy();
                let stem = token
                    .split('.')
                    .next()
                    .unwrap_or("")
                    .trim_end()
                    .to_ascii_uppercase();
                if matches!(
                    stem.as_str(),
                    "CON" | "PRN" | "AUX" | "NUL" | "CONIN$" | "CONOUT$"
                ) || (stem.len() == 4
                    && (stem.starts_with("COM") || stem.starts_with("LPT"))
                    && (b'1'..=b'9').contains(&stem.as_bytes()[3]))
                {
                    return Err("Path");
                }
            }
            _ => {}
        }
    }
    std::path::absolute(path).map_err(|_| "Path")
}

fn checked_existing(path: &Path, directory: bool) -> Result<PathBuf> {
    let path = absolute(path)?;
    for (index, ancestor) in path.ancestors().enumerate() {
        let metadata = fs::symlink_metadata(ancestor).map_err(|_| "Path")?;
        if metadata.file_type().is_symlink()
            || is_reparse(&metadata)
            || if index == 0 && !directory {
                !metadata.is_file()
            } else {
                !metadata.is_dir()
            }
        {
            return Err("Path");
        }
    }
    path.canonicalize().map_err(|_| "Path")
}

fn same_observed_metadata(left: &Metadata, right: &Metadata) -> bool {
    if !left.is_file()
        || !right.is_file()
        || left.len() != right.len()
        || left.modified().ok() != right.modified().ok()
    {
        return false;
    }
    #[cfg(unix)]
    {
        use std::os::unix::fs::MetadataExt;
        left.dev() == right.dev() && left.ino() == right.ino()
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        left.creation_time() == right.creation_time()
            && left.file_attributes() == right.file_attributes()
            && left.last_write_time() == right.last_write_time()
    }
    #[cfg(not(any(unix, windows)))]
    {
        false
    }
}

fn read_review(path: &Path) -> Result<Vec<u8>> {
    let path = checked_existing(path, false)?;
    let before = fs::symlink_metadata(&path).map_err(|_| "ReviewRead")?;
    if before.len() == 0 || before.len() > contract::MAX_REVIEW_BYTES as u64 {
        return Err("ReviewBudget");
    }
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        // Hold a read-only share: cooperative writers/replacements cannot change
        // this review while it is being decoded. This is not reviewer identity.
        options.share_mode(1).custom_flags(0x0020_0000);
    }
    let mut source = options.open(&path).map_err(|_| "ReviewRead")?;
    if !same_observed_metadata(&before, &source.metadata().map_err(|_| "ReviewRead")?) {
        return Err("ReviewChanged");
    }
    let mut bytes = Vec::with_capacity(before.len() as usize);
    Read::by_ref(&mut source)
        .take(before.len() + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| "ReviewRead")?;
    if bytes.len() as u64 != before.len()
        || !same_observed_metadata(&before, &source.metadata().map_err(|_| "ReviewRead")?)
        || !same_observed_metadata(
            &before,
            &fs::symlink_metadata(&path).map_err(|_| "ReviewRead")?,
        )
    {
        return Err("ReviewChanged");
    }
    checked_existing(&path, false)?;
    Ok(bytes)
}

fn write_new(path: &Path, run: &Path, bytes: &[u8]) -> Result<()> {
    if bytes.len() > contract::MAX_REVIEW_BYTES {
        return Err("ReviewBudget");
    }
    let path = absolute(path)?;
    let parent = checked_existing(path.parent().ok_or("Path")?, true)?;
    if parent.starts_with(run) {
        return Err("DestinationInsideRun");
    }
    let destination = parent.join(path.file_name().ok_or("Path")?);
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(destination)
        .map_err(|_| "DestinationExistsOrUnavailable")?;
    // An interrupted/failed export stays retained; it is never reused or deleted.
    file.write_all(bytes).map_err(|_| "ReviewWrite")?;
    file.sync_all().map_err(|_| "ReviewWrite")?;
    if file.metadata().map_err(|_| "ReviewWrite")?.len() != bytes.len() as u64 {
        return Err("ReviewWrite");
    }
    Ok(())
}

fn expected_packet(
    run: &reader::OpenedComparison,
    snapshot: &Value,
    maximum: usize,
) -> Result<Value> {
    let binding = snapshot["binding"].as_str().ok_or("SourceUnavailable")?;
    let turns = snapshot["report"]["turns"]
        .as_array()
        .ok_or("SourceUnavailable")?;
    if turns.is_empty() {
        return Err("NoRows");
    }
    let mut selected = Vec::new();
    for turn in turns.iter().take(maximum) {
        let id = RowId {
            turn: turn["turn"].as_str().ok_or("SourceUnavailable")?.to_owned(),
            arm: match turn["arm"].as_str() {
                Some("left") => Arm::Left,
                Some("right") => Arm::Right,
                _ => return Err("SourceUnavailable"),
            },
        };
        let capture = reader::evidence(
            run,
            binding,
            &id,
            EvidenceRequest::Capture {
                observer: Observer::Omniscient,
            },
            true,
        )
        .map_err(|_| "SourceUnavailable")?;
        let outputs = reader::evidence(
            run,
            binding,
            &id,
            EvidenceRequest::Outputs {
                observer: Observer::Omniscient,
            },
            true,
        )
        .map_err(|_| "SourceUnavailable")?;
        selected.push(contract::SourceRow { capture, outputs });
    }
    contract::template(snapshot, &selected).map_err(|_| "SourceUnavailable")
}

fn execute(args: Arguments) -> Result<Value> {
    let run_path = checked_existing(&args.run, true)?;
    let run = reader::open_read_only(&run_path).map_err(|_| "SourceUnavailable")?;
    let snapshot = reader::summary(&run, true).map_err(|_| "SourceUnavailable")?;
    if let Some(maximum) = args.max_turns {
        let packet = expected_packet(&run, &snapshot, maximum)?;
        let bytes = serde_json::to_vec_pretty(&packet).map_err(|_| "Encoding")?;
        write_new(&args.file, &run_path, &bytes)?;
        Ok(
            json!({"version":1,"scope":"locallore_role_review_cli","status":"created",
            "bytes":bytes.len(),"sha256":digest(&bytes),"binding":snapshot["binding"],
            "total_turns":packet["source"]["total_turns"],
            "selected_turns":packet["source"]["selected_turns"],"quality_accepted":false}),
        )
    } else {
        let bytes = read_review(&args.file)?;
        // Only the reviewed prefix length selects evidence. The contract validates
        // all other fields, including its equality to the fresh bound snapshot.
        let count = contract::selected_count(&bytes).map_err(|_| "InvalidReview")?;
        let expected = expected_packet(&run, &snapshot, count)?;
        contract::summarize(&expected, &bytes).map_err(|_| "InvalidReview")
    }
}

fn main() {
    let result = arguments(std::env::args_os().skip(1).collect()).and_then(execute);
    match result {
        Ok(value) => println!("{value}"),
        Err(reason) => {
            println!(
                "{}",
                json!({"version":1,"scope":"locallore_role_review_cli", "status":"refused", "reason":reason,"quality_accepted":false})
            );
            std::process::exit(2);
        }
    }
}
