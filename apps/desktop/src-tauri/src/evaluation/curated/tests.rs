use super::*;
#[test]
fn missing_native_assets_are_unavailable_without_scripted_substitution() {
    let (_root, m, l, e, models) = setup();
    let started = m
        .curated_start(
            &l,
            e,
            models,
            CuratedStart {
                client: &uuid().unwrap(),
                chosen_lane: "native",
                selection: None,
                batch: "one",
                consent: true,
            },
        )
        .unwrap();
    let token = started["run_token"].as_str().unwrap();
    let failed = done(&m, &l, e, token);
    assert_eq!(failed["error"], "EvaluationModelUnavailable");
    assert_eq!(failed["completed_cases"], 0);
    assert_eq!(failed["lane"], "native");
    let opened = m
        .curated_open(&l, e, started["run_id"].as_str().unwrap())
        .unwrap();
    assert_eq!(opened["snapshot"]["budget"]["roles_charged"], 0);
    assert_eq!(opened["snapshot"]["report"]["cases"], json!([]));
    m.drain(e);
}
struct Root(PathBuf);
impl Root {
    fn new() -> Self {
        let p = std::env::temp_dir().join(format!("curated-native-{}", uuid().unwrap()));
        fs::create_dir(&p).unwrap();
        Self(p)
    }
}
impl Drop for Root {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.0).unwrap();
    }
}
fn setup() -> (
    Root,
    Arc<EvaluationManager>,
    Arc<WindowLease>,
    u64,
    Arc<ModelManager>,
) {
    let root = Root::new();
    let m = Arc::new(EvaluationManager::new(root.0.join("runs")));
    let l = Arc::new(WindowLease::default());
    let e = l.begin().unwrap();
    let model = Arc::new(ModelManager::new(
        root.0.join("no-models"),
        root.0.join("no-worker"),
    ));
    (root, m, l, e, model)
}
fn done(m: &EvaluationManager, l: &WindowLease, e: u64, t: &str) -> Value {
    let start = Instant::now();
    loop {
        let s = m.curated_status(l, e, t).unwrap();
        if s["running"] == false {
            return s;
        }
        assert!(
            start.elapsed() < Duration::from_secs(20),
            "curated worker did not settle: {s}"
        );
        std::thread::sleep(Duration::from_millis(5));
    }
}
fn bytes_at(path: &Path) -> BTreeMap<PathBuf, Vec<u8>> {
    let mut all = BTreeMap::new();
    for item in fs::read_dir(path).unwrap() {
        let p = item.unwrap().path();
        if p.is_dir() {
            all.extend(bytes_at(&p));
        } else {
            all.insert(p.clone(), fs::read(p).unwrap());
        }
    }
    all
}
#[test]
fn actual_runner_lost_ack_restart_read_only_cache_and_bound_evidence() {
    let (_root, m, l, e, model) = setup();
    assert_eq!(
        m.curated_catalog(&l, e).unwrap()["cases"]
            .as_array()
            .unwrap()
            .len(),
        6
    );
    let client = uuid().unwrap();
    let started = m
        .curated_start(
            &l,
            e,
            model.clone(),
            CuratedStart {
                client: &client,
                chosen_lane: "scripted",
                selection: None,
                batch: "one",
                consent: false,
            },
        )
        .unwrap();
    let token = started["run_token"].as_str().unwrap();
    let paused = done(&m, &l, e, token);
    assert_eq!(paused["completed_cases"], 1, "{paused}");
    let retry = m
        .curated_start(
            &l,
            e,
            model.clone(),
            CuratedStart {
                client: &client,
                chosen_lane: "scripted",
                selection: None,
                batch: "one",
                consent: false,
            },
        )
        .unwrap();
    assert_eq!(retry["run_id"], started["run_id"]);
    assert_eq!(retry["running"], false);
    let work = m
        .curated_root()
        .join(started["run_id"].as_str().unwrap())
        .join("work");
    let first = fs::read(work.join("case-00.json")).unwrap();
    m.curated_resume(&l, e, model.clone(), token, "all", false)
        .unwrap();
    let completed = done(&m, &l, e, token);
    assert_eq!(completed["completed_cases"], 6);
    assert_eq!(fs::read(work.join("case-00.json")).unwrap(), first);
    let before = bytes_at(&m.curated_root());
    let excluded = model.reserve_evaluation().unwrap();
    let cached = m
        .curated_resume(&l, e, model.clone(), token, "all", false)
        .unwrap();
    assert_eq!(cached["running"], false);
    assert_eq!(cached["completed"], true);
    assert_eq!(bytes_at(&m.curated_root()), before);
    drop(excluded);
    let binding = completed["snapshot"]["binding_sha256"].as_str().unwrap();
    let case = completed["snapshot"]["report"]["cases"][0]["id"]
        .as_str()
        .unwrap();
    let turn = completed["snapshot"]["report"]["cases"][0]["turns"][0]["id"]
        .as_str()
        .unwrap();
    let evidence = m
        .curated_evidence(
            &l,
            e,
            CuratedEvidenceRequest {
                token,
                case,
                turn,
                binding,
                observer: locallore::inspection_query::Observer::Omniscient,
                view: locallore::inspection_query::View::TurnDiff,
            },
        )
        .unwrap();
    assert!(evidence["evidence"]["receipt"].is_object());
    assert_eq!(bytes_at(&m.curated_root()), before);
    assert!(m
        .curated_evidence(
            &l,
            e,
            CuratedEvidenceRequest {
                token,
                case,
                turn,
                binding: &"0".repeat(64),
                observer: locallore::inspection_query::Observer::Omniscient,
                view: locallore::inspection_query::View::TurnDiff
            }
        )
        .is_err());
    m.drain(e);
    let reopened = Arc::new(EvaluationManager::new(m.root.clone()));
    let recovered = reopened.curated_lookup(&l, e, &client).unwrap();
    assert_eq!(recovered["run_id"], started["run_id"]);
    assert_eq!(recovered["completed"], true);
    assert_ne!(recovered["run_token"], token);
    assert!(reopened.curated_status(&l, e, token).is_err());
    assert_eq!(bytes_at(&m.curated_root()), before);
}
#[test]
fn cancel_exclusion_spawn_panic_and_retired_owner_settle_without_another_evaluator() {
    let (_root, m, l, e, model) = setup();
    m.hold.store(true, std::sync::atomic::Ordering::SeqCst);
    let started = m
        .curated_start(
            &l,
            e,
            model.clone(),
            CuratedStart {
                client: &uuid().unwrap(),
                chosen_lane: "scripted",
                selection: None,
                batch: "all",
                consent: false,
            },
        )
        .unwrap();
    let token = started["run_token"].as_str().unwrap();
    assert_eq!(m.start(&l, e, None, "all").unwrap_err(), "EvaluationBusy");
    m.cancel(&l, e, token, started["operation_id"].as_u64().unwrap())
        .unwrap();
    let stopped = done(&m, &l, e, token);
    assert_eq!(stopped["completed_cases"], 0);
    assert_eq!(stopped["phase"], "paused");
    m.hold.store(false, std::sync::atomic::Ordering::SeqCst);
    m.drain(e);
    m.fail_spawn
        .store(true, std::sync::atomic::Ordering::SeqCst);
    assert_eq!(
        m.curated_start(
            &l,
            e,
            model.clone(),
            CuratedStart {
                client: &uuid().unwrap(),
                chosen_lane: "scripted",
                selection: None,
                batch: "one",
                consent: false
            }
        )
        .unwrap_err(),
        "EvaluationInternal"
    );
    assert!(m.state().unwrap().job.is_none());
    m.panic_worker
        .store(true, std::sync::atomic::Ordering::SeqCst);
    let started = m
        .curated_start(
            &l,
            e,
            model.clone(),
            CuratedStart {
                client: &uuid().unwrap(),
                chosen_lane: "scripted",
                selection: None,
                batch: "one",
                consent: false,
            },
        )
        .unwrap();
    let failed = done(&m, &l, e, started["run_token"].as_str().unwrap());
    assert_eq!(failed["error"], "EvaluationInternal");
    m.drain(e);
    m.hold.store(true, std::sync::atomic::Ordering::SeqCst);
    let _started = m
        .curated_start(
            &l,
            e,
            model.clone(),
            CuratedStart {
                client: &uuid().unwrap(),
                chosen_lane: "scripted",
                selection: None,
                batch: "one",
                consent: false,
            },
        )
        .unwrap();
    let closed = l.invalidate("main-1").unwrap();
    m.retire(e);
    m.drain(e);
    l.finish_close(closed, || {});
    let before = bytes_at(&m.curated_root());
    assert_eq!(
        m.curated_start(
            &l,
            e,
            model,
            CuratedStart {
                client: &uuid().unwrap(),
                chosen_lane: "scripted",
                selection: None,
                batch: "one",
                consent: false
            }
        )
        .unwrap_err(),
        "Closed"
    );
    assert_eq!(bytes_at(&m.curated_root()), before);
    assert!(m.state().unwrap().job.is_none());
}
