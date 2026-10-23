//! Native-owned retained synthetic evaluation inspection. Never starts a provider or writes.
use super::*;
use locallore::inspection_query::{self, Observer, Query, View};

pub fn catalog() -> Result<Value> {
    let mut value = json!({"version":1,"cases":corpus()?.stories.iter().map(|s|json!({"id":s.id,"turns":s.steps.len(),"sources":s.steps.iter().map(|t|json!({"turn":t.id,"scope":{"story":s.seed.scope.story,"branch":t.branch}})).collect::<Vec<_>>()})).collect::<Vec<_>>(),
        "limits":{"admissions":MAX_ADMISSIONS,"roles":MAX_ROLES,"active_ms":MAX_ACTIVE_MS,"invocations":32,"checkpoint":"four_turn_story"}});
    value["approved_profile"] = {
        #[cfg(feature = "local-model")]
        {
            serde_json::to_value(native_profile()?).map_err(|_| "Encoding")?
        }
        #[cfg(not(feature = "local-model"))]
        {
            Value::Null
        }
    };
    Ok(value)
}
/// Capture the current compiled request binding before native dispatch, even if acknowledgement
/// or process ownership is lost before the runner writes its first invocation.
pub fn request_binding(native: bool, selected: Option<&str>) -> Result<String> {
    let profile = if native {
        #[cfg(feature = "local-model")]
        {
            native_profile()?
        }
        #[cfg(not(feature = "local-model"))]
        {
            return Err("NativeFeatureUnavailable".into());
        }
    } else {
        LaneFactory::ScriptedBaseline.profile()?
    };
    let all = corpus()?.stories;
    if selected.is_some_and(|id| !all.iter().any(|s| s.id == id)) {
        return Err("UnknownCase".into());
    }
    let stories: Vec<_> = all
        .into_iter()
        .filter(|s| selected.is_none_or(|id| id == s.id))
        .collect();
    Ok(digest(&encode(&curated_basis(
        &stories, profile, native, false,
    )?)?))
}
struct Opened {
    _pins: Vec<File>,
    _lock: File,
    basis: Value,
    binding: String,
    stories: Vec<Story>,
    saved: Vec<Option<LocalStored>>,
    ledger: Ledger,
}
fn pin_directory(path: &Path) -> Result<Vec<File>> {
    let absolute = std::path::absolute(path).map_err(|_| "Io")?;
    let mut parents: Vec<_> = absolute.ancestors().collect();
    parents.reverse();
    let mut pins = vec![];
    for parent in parents {
        #[cfg(windows)]
        {
            use std::os::windows::fs::{MetadataExt, OpenOptionsExt};
            let file = OpenOptions::new()
                .read(true)
                .share_mode(3)
                .custom_flags(0x0220_0000)
                .open(parent)
                .map_err(|_| "Io")?;
            if file.metadata().map_err(|_| "Io")?.file_attributes() & 0x400 != 0 {
                return Err("Reparse".into());
            }
            pins.push(file);
        }
        #[cfg(not(windows))]
        {
            ordinary(parent)?;
            pins.push(File::open(parent).map_err(|_| "Io")?);
        }
    }
    Ok(pins)
}
fn open(directory: &Path) -> Result<Opened> {
    let mut pins = pin_directory(directory)?;
    let mut entries = 0;
    // Retain each attempt directory handle before the shared validator reads descendants.
    // Refuse reparse ancestors rather than following a planted directory outside this run.
    for entry in fs::read_dir(directory).map_err(|_| "Io")? {
        entries += 1;
        if entries > 512 {
            return Err("CaseBudget".into());
        }
        let entry = entry.map_err(|_| "Io")?;
        ordinary(&entry.path())?;
        if entry.file_type().map_err(|_| "Io")?.is_dir() {
            pins.extend(pin_directory(&entry.path())?);
        }
    }
    ordinary(directory)?;
    ordinary(&directory.join("run.lock"))?;
    // Existing lock only. Viewing never creates a run, lock, reservation, settlement or report.
    let lock = OpenOptions::new()
        .read(true)
        .open(directory.join("run.lock"))
        .map_err(|_| "Io")?;
    lock.try_lock().map_err(|_| "RunBusy")?;
    let bytes = read(&directory.join("run.json"), 128 * 1024)?;
    let basis: Value = serde_json::from_slice(&bytes).map_err(|_| "CheckpointIntegrity")?;
    if basis["version"] != 1
        || basis["suite"] != "curated-local-v1"
        || basis["suite_sha256"] != digest(FIXTURES)
        || !basis["native"].is_boolean()
        || !basis["preowned_runtime"].is_boolean()
    {
        return Err("CheckpointIntegrity".into());
    }
    let profile: PlayProfile =
        serde_json::from_value(basis["profile"].clone()).map_err(|_| "Profile")?;
    profile.validate().map_err(|_| "Profile")?;
    let ids: Vec<String> = serde_json::from_value(basis["selected_stories"].clone())
        .map_err(|_| "CheckpointIntegrity")?;
    let stories: Vec<_> = corpus()?
        .stories
        .into_iter()
        .filter(|s| ids.contains(&s.id))
        .collect();
    if stories.is_empty()
        || stories.iter().map(|s| &s.id).collect::<Vec<_>>() != ids.iter().collect::<Vec<_>>()
    {
        return Err("CheckpointIntegrity".into());
    }
    let seeds: BTreeMap<_, _> = stories
        .iter()
        .map(|s| Ok((s.id.clone(), digest(&encode(&s.seed)?))))
        .collect::<Result<_>>()?;
    if serde_json::to_value(seeds).map_err(|_| "Encoding")? != basis["seed_sha256"] {
        return Err("CheckpointIntegrity".into());
    }
    let binding = digest(&bytes);
    let ledger = Ledger::load(directory, &binding)?;
    let saved = stories
        .iter()
        .enumerate()
        .map(|(i, s)| restore_case(directory, &binding, i, s))
        .collect::<Result<_>>()?;
    Ok(Opened {
        _pins: pins,
        _lock: lock,
        basis,
        binding,
        stories,
        saved,
        ledger,
    })
}
fn compatible(open: &Opened) -> Result<bool> {
    let native = open.basis["native"] == true;
    let profile = if native {
        #[cfg(feature = "local-model")]
        {
            native_profile()?
        }
        #[cfg(not(feature = "local-model"))]
        {
            return Ok(false);
        }
    } else {
        LaneFactory::ScriptedBaseline.profile()?
    };
    Ok(open.basis == curated_basis(&open.stories, profile, native, false)?)
}
fn budget(ledger: &Ledger) -> Value {
    json!({"admissions_across_attempts":ledger.admissions,"roles_charged":ledger.charged_roles,
        "active_ms_charged":ledger.charged_ms,"invocations":ledger.invocations,
        "max_admissions":MAX_ADMISSIONS,"max_roles":MAX_ROLES,"max_active_ms":MAX_ACTIVE_MS,
        "unknown_work":"conservatively_reserved_not_refunded"})
}
fn snapshot(open: &Opened, directory: &Path) -> Result<Value> {
    let cases: Vec<_> = open
        .saved
        .iter()
        .flatten()
        .map(|s| s.result.clone())
        .collect();
    let metadata: Vec<_> = open
        .saved
        .iter()
        .flatten()
        .map(|s| s.metadata.clone())
        .collect();
    let native = open.basis["native"] == true;
    // Render-only projection from validated immutable checkpoints, not a new evaluator/report file.
    let mut report = json!({"version":1,"lane":if native{"native_curated_shared_host"}else{"scripted_curated_shared_host"},
        "synthetic":true,"quality_accepted":false,"completed":cases.len()==open.stories.len(),"cancelled":false,
        "binding_sha256":open.binding,"cases":cases,"model":if native{open.basis["profile"]["model_sha256"].clone()}else{Value::Null},
        "runtime":if native{open.basis["profile"]["runtime_revision"].clone()}else{Value::Null},"hardware":null,
        "android_parity":"not_run","unsupported_lanes":["human_quality_acceptance","transcript_only_baseline","verified_memory_baseline","full_historical_context","android_parity"],
        "provenance":{"binding":open.basis,"budget":budget(&open.ledger),"local_cases":metadata,"view":"read_only_checkpoint_projection","generation_this_view":false,"artifact_verification_this_view":false}});
    // An existing derived report is checked for its fixed identity, never rewritten or trusted
    // over checkpoints. A crash may leave an older prefix report; all saved checkpoints remain visible.
    let path = directory.join("report.json");
    if path.exists() {
        let stored: Value =
            serde_json::from_slice(&read(&path, MAX_REPORT)?).map_err(|_| "CheckpointIntegrity")?;
        if stored["version"] != 1
            || stored["binding_sha256"] != open.binding
            || stored["provenance"]["binding"] != open.basis
            || stored["lane"] != report["lane"]
            || stored["synthetic"] != true
            || stored["quality_accepted"] != false
        {
            return Err("CheckpointIntegrity".into());
        }
        let old = stored["cases"].as_array().ok_or("CheckpointIntegrity")?;
        let current = report["cases"].as_array().ok_or("CheckpointIntegrity")?;
        if old.len() > current.len() || old.iter().zip(current).any(|(a, b)| a != b) {
            return Err("CheckpointIntegrity".into());
        }
        // Preserve historical load/coverage/quality provenance and cancellation; this view
        // adds an explicit read-only envelope rather than rewriting the original report.
        let verified_cases = report["cases"].clone();
        let verified_metadata = report["provenance"]["local_cases"].clone();
        report = stored;
        report["cases"] = verified_cases;
        report["completed"] = json!(cases.len() == open.stories.len());
        report["provenance"]["local_cases"] = verified_metadata;
        report["provenance"]["view"] = json!("read_only_checkpoint_projection");
        report["provenance"]["generation_this_view"] = json!(false);
        report["provenance"]["artifact_verification_this_view"] = json!(false);
    }
    report["provenance"]["retained_report_coverage"] = report["provenance"]["coverage"].clone();
    report["provenance"]["coverage"] = coverage(&metadata, open.stories.len(), cases.len());
    if encode(&report)?.len() > MAX_REPORT {
        return Err("ReportBudget".into());
    }
    Ok(
        json!({"version":1,"binding_sha256":open.binding,"resume_compatible":compatible(open)?,
        "completed":cases.len()==open.stories.len(),"checkpointed_stories":cases.len(),"budget":budget(&open.ledger),"report":report}),
    )
}
/// Validate stored checkpoints/ledger/raw hashes without admission, model/assets or publication.
pub fn inspect(directory: &Path) -> Result<Value> {
    let open = open(directory)?;
    snapshot(&open, directory)
}

/// Native token binding supplies directory and expected digest. Renderer supplies only a known
/// case/turn and bounded typed view/observer. No user-story Host or writable Store is opened.
pub fn evidence(
    directory: &Path,
    expected_binding: &str,
    case: &str,
    turn: &str,
    observer: Observer,
    view: View,
) -> Result<Value> {
    let opened = open(directory)?;
    if opened.binding != expected_binding {
        return Err("CheckpointMismatch".into());
    }
    let index = opened
        .stories
        .iter()
        .position(|s| s.id == case)
        .ok_or("UnknownCase")?;
    let saved = opened.saved[index].as_ref().ok_or("CheckpointNotReady")?;
    let n = saved
        .result
        .turns
        .iter()
        .position(|t| t.id == turn)
        .ok_or("UnknownTurn")?;
    let story = &opened.stories[index];
    let step = story
        .steps
        .get(n)
        .filter(|s| s.id == turn)
        .ok_or("CheckpointIntegrity")?;
    let scope = Scope {
        story: story.seed.scope.story.clone(),
        branch: step.branch.clone(),
    };
    let attempt = directory.join(format!("case-{index:02}-attempt-{:02}", saved.attempt));
    let database = attempt.join("synthetic.sqlite");
    ordinary(&database)?;
    let database = fs::canonicalize(database).map_err(|_| "Workspace")?;
    let mut store = Store::open_read_only(&database).map_err(|_| "Workspace")?;
    let engine = store.resume(&scope).map_err(|_| "Workspace")?.engine;
    let row = &saved.result.turns[n];
    let at = engine
        .at_revision(row.revision)
        .map_err(|_| "CheckpointIntegrity")?;
    if digest(&at.canonical_bytes()) != row.canonical_sha256 {
        return Err("CheckpointIntegrity".into());
    }
    let query = Query {
        version: 1,
        scope: scope.clone(),
        expected_head: engine.revision(),
        at_revision: Some(row.revision),
        observer: observer.clone(),
        view,
        cursor: None,
        limit: 32,
        search: String::new(),
    };
    let page =
        inspection_query::query(&engine, &query, true).map_err(|e| format!("Inspection{e}"))?;
    let private = matches!(observer, Observer::Omniscient);
    let receipt = if private {
        at.receipts()
            .iter()
            .find(|r| r.request().scope == scope && r.request().turn == turn)
            .map(serde_json::to_value)
            .transpose()
            .map_err(|_| "Encoding")?
    } else {
        None
    };
    let mut outputs = vec![];
    if private {
        for raw in &saved.metadata.turns[n].raw {
            let bytes = read(&attempt.join(&raw.file), 16384)?;
            if digest(&bytes) != raw.sha256 || bytes.len() != raw.bytes {
                return Err("CheckpointIntegrity".into());
            }
            outputs.push(json!({"role":raw.role,"sha256":raw.sha256,"bytes":raw.bytes,"text":String::from_utf8(bytes).map_err(|_|"CheckpointIntegrity")?}));
        }
    }
    Ok(
        json!({"version":1,"binding_sha256":opened.binding,"case_id":case,"turn_id":turn,"scope":scope,
        "revision":row.revision,"canonical_sha256":row.canonical_sha256,"observer":observer,"page":page,
        "receipt":receipt,"outputs":outputs,"role_metrics":if private{saved.metadata.turns[n].role_metrics.clone()}else{None},
        "missing":["historical_context","full_prompt","schema_bytes","validated_plan","window_host_trace"],
        "exact_reconstruction":false,"read_only":true,"generation_grant":false}),
    )
}

#[cfg(test)]
mod tests;
