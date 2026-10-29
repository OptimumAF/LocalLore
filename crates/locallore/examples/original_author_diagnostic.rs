//! Offline diagnostics for two explicit trusted files. Never creates or repairs a story.
use locallore::{
    engine::parse_unique_json,
    story_authoring::{
        validate_proposal_detailed, InitialProposalFailureV1, InitialStoryInputV1,
        InitialWorldProposalV1, MAX_INPUT_BYTES, MAX_PROPOSAL_BYTES,
    },
};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::{
    ffi::OsString,
    fs::{self, File},
    io::{Read, Write},
    path::Path,
};

#[derive(Clone, Copy, Serialize)]
#[serde(rename_all = "snake_case")]
enum Status {
    Valid,
    Rejected,
    Malformed,
}
#[derive(Clone, Copy, Serialize)]
#[serde(rename_all = "snake_case")]
enum FileCategory {
    InputJson,
    ResponseJson,
    InputRead,
    ResponseRead,
    InputBytes,
    ResponseBytes,
}
#[derive(Serialize)]
#[serde(untagged)]
enum Category {
    Native(InitialProposalFailureV1),
    File(FileCategory),
}
#[derive(Serialize)]
struct Diagnostic {
    version: u16,
    scope: &'static str,
    input_sha256: Option<String>,
    response_sha256: Option<String>,
    input_bytes: Option<usize>,
    response_bytes: Option<usize>,
    status: Status,
    category: Option<Category>,
    error: Option<&'static str>,
}
#[derive(Clone, Copy)]
enum ReadFailure {
    Read,
    Bytes,
}
type Observed = Result<Vec<u8>, ReadFailure>;

fn sha(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn regular_bytes(path: &Path, cap: usize) -> Observed {
    let before = fs::symlink_metadata(path).map_err(|_| ReadFailure::Read)?;
    if !before.is_file() || before.file_type().is_symlink() {
        return Err(ReadFailure::Read);
    }
    if before.len() > cap as u64 {
        return Err(ReadFailure::Bytes);
    }
    let mut file = File::open(path).map_err(|_| ReadFailure::Read)?;
    let held = file.metadata().map_err(|_| ReadFailure::Read)?;
    if !held.is_file() {
        return Err(ReadFailure::Read);
    }
    if held.len() > cap as u64 {
        return Err(ReadFailure::Bytes);
    }
    let mut bytes = Vec::new();
    (&mut file)
        .take(cap as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| ReadFailure::Read)?;
    if bytes.len() > cap {
        return Err(ReadFailure::Bytes);
    }
    let after = file.metadata().map_err(|_| ReadFailure::Read)?;
    let path_after = fs::symlink_metadata(path).map_err(|_| ReadFailure::Read)?;
    if !path_after.is_file()
        || path_after.file_type().is_symlink()
        || bytes.len() as u64 != held.len()
        || held.len() != before.len()
        || held.len() != after.len()
        || held.len() != path_after.len()
        || held.modified().ok() != before.modified().ok()
        || held.modified().ok() != after.modified().ok()
        || held.modified().ok() != path_after.modified().ok()
    {
        return Err(ReadFailure::Read);
    }
    Ok(bytes)
}
impl Diagnostic {
    fn malformed(mut self, category: FileCategory, error: &'static str) -> Self {
        self.status = Status::Malformed;
        self.category = Some(Category::File(category));
        self.error = Some(error);
        self
    }
    fn exit_code(&self) -> i32 {
        match self.status {
            Status::Valid => 0,
            Status::Rejected => 1,
            Status::Malformed => 2,
        }
    }
}
fn diagnose(input: Observed, response: Observed) -> Diagnostic {
    let mut report = Diagnostic {
        version: 1,
        scope: "original_author_native_diagnostic_v1",
        input_sha256: input.as_ref().ok().map(|bytes| sha(bytes)),
        response_sha256: response.as_ref().ok().map(|bytes| sha(bytes)),
        input_bytes: input.as_ref().ok().map(Vec::len),
        response_bytes: response.as_ref().ok().map(Vec::len),
        status: Status::Valid,
        category: None,
        error: None,
    };
    let input = match input {
        Ok(bytes) => bytes,
        Err(ReadFailure::Read) => return report.malformed(FileCategory::InputRead, "InvalidInput"),
        Err(ReadFailure::Bytes) => return report.malformed(FileCategory::InputBytes, "TooLarge"),
    };
    let response = match response {
        Ok(bytes) => bytes,
        Err(ReadFailure::Read) => {
            return report.malformed(FileCategory::ResponseRead, "InvalidInput")
        }
        Err(ReadFailure::Bytes) => {
            return report.malformed(FileCategory::ResponseBytes, "TooLarge")
        }
    };
    let input: InitialStoryInputV1 = match parse_unique_json(&input, MAX_INPUT_BYTES)
        .ok()
        .and_then(|value| serde_json::from_value(value).ok())
    {
        Some(input) => input,
        None => return report.malformed(FileCategory::InputJson, "Malformed"),
    };
    let response: InitialWorldProposalV1 = match parse_unique_json(&response, MAX_PROPOSAL_BYTES)
        .ok()
        .and_then(|value| serde_json::from_value(value).ok())
    {
        Some(response) => response,
        None => return report.malformed(FileCategory::ResponseJson, "Malformed"),
    };
    if let Err(reason) = validate_proposal_detailed(&input, &response) {
        report.status = Status::Rejected;
        report.category = Some(Category::Native(reason));
        report.error = Some(reason.legacy_error());
    }
    report
}
fn run(args: &[OsString]) -> Diagnostic {
    if args.len() != 2 {
        return diagnose(Err(ReadFailure::Read), Err(ReadFailure::Read));
    }
    // Both reads are attempted, so complete observations remain hash-bound even
    // when the other trusted file is unreadable. No prefix digest is published.
    diagnose(
        regular_bytes(Path::new(&args[0]), MAX_INPUT_BYTES),
        regular_bytes(Path::new(&args[1]), MAX_PROPOSAL_BYTES),
    )
}
fn main() {
    let report = run(&std::env::args_os().skip(1).collect::<Vec<_>>());
    let code = report.exit_code();
    let Ok(mut encoded) = serde_json::to_vec(&report) else {
        std::process::exit(2);
    };
    encoded.push(b'\n');
    if std::io::stdout().lock().write_all(&encoded).is_err() {
        std::process::exit(2);
    }
    std::process::exit(code);
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{json, Value};
    use std::time::{SystemTime, UNIX_EPOCH};

    fn input() -> Vec<u8> {
        serde_json::to_vec(&json!({"version":1,"premise":"A bell keeper asks about a reed ferry.",
            "player_name":"Mira","player_description":"","cast":[{"name":"Neri","description":""}],
            "profile":"narrative_v1","presentation":{"version":1,"tone":"plain","excluded_phrases":[]}})).unwrap()
    }
    fn response() -> Vec<u8> {
        serde_json::to_vec(&json!({"version":1,"locations":[{"name":"Reed landing","description":"A rope crosses the water."}],
            "player_location":0,"characters":[{"name":"Neri","description":"A bell keeper.","location":0,"known_by":[1]}],
            "routes":[],"facts":[],"beliefs":[],"possessions":[]})).unwrap()
    }
    fn value(report: Diagnostic) -> Value {
        serde_json::to_value(report).unwrap()
    }
    #[test]
    fn complete_valid_bytes_have_exact_nine_fields_and_raw_hashes() {
        let a = input();
        let b = response();
        let report = diagnose(Ok(a.clone()), Ok(b.clone()));
        assert_eq!(report.exit_code(), 0);
        let report = value(report);
        assert_eq!(report.as_object().unwrap().len(), 9);
        assert_eq!(report["status"], "valid");
        assert_eq!(report["scope"], "original_author_native_diagnostic_v1");
        assert_eq!(report["input_sha256"], sha(&a));
        assert_eq!(report["response_sha256"], sha(&b));
        assert_eq!(report["input_bytes"], a.len());
        assert_eq!(report["response_bytes"], b.len());
        assert!(report["category"].is_null() && report["error"].is_null());
        let mut whitespace = b.clone();
        whitespace.push(b' ');
        let spaced = value(diagnose(Ok(a), Ok(whitespace.clone())));
        assert_eq!(spaced["status"], "valid");
        assert_eq!(spaced["response_sha256"], sha(&whitespace));
        assert_ne!(spaced["response_sha256"], report["response_sha256"]);
    }
    #[test]
    fn domain_rejection_is_detailed_without_echo_or_repair() {
        let mut b: Value = serde_json::from_slice(&response()).unwrap();
        b["characters"][0]["known_by"] = json!([0]);
        b["characters"][0]["description"] = json!("secret_weather_note");
        let bytes = serde_json::to_vec(&b).unwrap();
        let report = diagnose(Ok(input()), Ok(bytes.clone()));
        assert_eq!(report.exit_code(), 1);
        let report = value(report);
        assert_eq!(report["status"], "rejected");
        assert_eq!(report["category"], "character_self_knowledge");
        assert_eq!(report["error"], "InvalidProposal");
        assert_eq!(report["response_sha256"], sha(&bytes));
        assert!(!report.to_string().contains("secret_weather_note"));
    }
    #[test]
    fn malformed_duplicate_unknown_non_utf8_and_nonfinite_keep_complete_raw_bindings() {
        let mut extra: Value = serde_json::from_slice(&response()).unwrap();
        extra["grant_stats"] = json!({"power":999});
        for bytes in [
            b"{\"version\":1,\"version\":1}".to_vec(),
            serde_json::to_vec(&extra).unwrap(),
            b"{\"version\":NaN}".to_vec(),
            vec![0xff],
            b"{\"version\":\"secret_weather_note\"}".to_vec(),
        ] {
            let report = diagnose(Ok(input()), Ok(bytes.clone()));
            assert_eq!(report.exit_code(), 2);
            let report = value(report);
            assert_eq!(report["status"], "malformed");
            assert_eq!(report["category"], "response_json");
            assert_eq!(report["error"], "Malformed");
            assert_eq!(report["response_sha256"], sha(&bytes));
            assert_eq!(report["response_bytes"], bytes.len());
            assert!(!report.to_string().contains("secret_weather_note"));
        }
        let report = value(diagnose(
            Ok(b"{\"version\":1,\"version\":1}".to_vec()),
            Ok(response()),
        ));
        assert_eq!(report["category"], "input_json");
        let report = value(diagnose(Ok(Vec::new()), Ok(response())));
        assert_eq!(report["input_sha256"], sha(&[]));
        assert_eq!(report["input_bytes"], 0);
    }
    #[test]
    fn invalid_typed_input_projects_the_legacy_error() {
        let mut a: Value = serde_json::from_slice(&input()).unwrap();
        a["version"] = json!(2);
        let report = value(diagnose(
            Ok(serde_json::to_vec(&a).unwrap()),
            Ok(response()),
        ));
        assert_eq!(report["status"], "rejected");
        assert_eq!(report["category"], "invalid_input");
        assert_eq!(report["error"], "InvalidInput");
    }
    #[test]
    fn incomplete_reads_never_publish_prefix_hashes_or_lengths() {
        let report = value(diagnose(Err(ReadFailure::Bytes), Ok(response())));
        assert_eq!(report["category"], "input_bytes");
        assert_eq!(report["error"], "TooLarge");
        assert!(report["input_sha256"].is_null() && report["input_bytes"].is_null());
        assert!(report["response_sha256"].is_string());
        let report = value(diagnose(Ok(input()), Err(ReadFailure::Read)));
        assert_eq!(report["category"], "response_read");
        assert_eq!(report["error"], "InvalidInput");
        assert!(report["response_sha256"].is_null() && report["response_bytes"].is_null());
    }
    #[test]
    fn explicit_regular_file_reads_refuse_oversize_missing_and_directory_inputs() {
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "locallore-author-diagnostic-{}-{unique}",
            std::process::id()
        ));
        fs::create_dir(&root).unwrap();
        let a = root.join("input.json");
        let b = root.join("response.json");
        fs::write(&a, input()).unwrap();
        fs::write(&b, response()).unwrap();
        assert_eq!(run(&[a.clone().into(), b.clone().into()]).exit_code(), 0);
        fs::write(&b, vec![b' '; MAX_PROPOSAL_BYTES + 1]).unwrap();
        let report = value(run(&[a.clone().into(), b.clone().into()]));
        assert_eq!(report["category"], "response_bytes");
        assert!(report["response_sha256"].is_null() && report["response_bytes"].is_null());
        let report = value(run(&[root.clone().into(), b.clone().into()]));
        assert_eq!(report["category"], "input_read");
        let report = value(run(&[
            root.join("secret-path-not-echoed").into(),
            b.clone().into(),
        ]));
        assert_eq!(report["category"], "input_read");
        assert!(!report.to_string().contains("secret-path-not-echoed"));
        assert_eq!(run(&[]).exit_code(), 2);
        fs::remove_file(a).unwrap();
        fs::remove_file(b).unwrap();
        fs::remove_dir(root).unwrap();
    }
}
