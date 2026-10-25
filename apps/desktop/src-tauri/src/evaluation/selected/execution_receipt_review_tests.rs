//! A read open revokes unused plans, while an admitted execution stays idempotent.
use super::*;
fn join(f: &Fixture) {
    let old = {
        let _gate = f.manager.registration.lock().unwrap();
        f.manager.worker.lock().unwrap().take()
    };
    if let Some((_, handle)) = old {
        handle.join().unwrap();
    }
    assert!(f.manager.state().unwrap().job.is_none());
}
#[test]
fn original_execution_retry_after_explicit_read_open_returns_same_inert_receipt() {
    let f = Fixture::new();
    let client = uuid().unwrap();
    let plan = f.prepare(&client);
    join(&f);
    let token = plan["plan_token"].as_str().unwrap();
    let admitted = f
        .manager
        .selected_start(&f.lease, &f.models, f.epoch, true, &client, token)
        .unwrap();
    let executed = f.done(&client);
    join(&f);
    let run = executed["run_id"].as_str().unwrap();
    let (path, pins) = f.manager.selected_work_path(run).unwrap();
    drop(pins);
    let before = inventory(&path);
    f.manager
        .selected_open(&f.lease, &f.models, f.epoch, true, (&client, run), |_| {
            Ok(true)
        })
        .unwrap();
    let opened = f.done(&client);
    join(&f);
    let duplicate = f
        .manager
        .selected_start(&f.lease, &f.models, f.epoch, true, &client, token);
    let current = f.status(&client);
    f.manager
        .selected_close(&f.lease, f.epoch, &client)
        .unwrap();
    let after = inventory(&path);
    let revoked = f
        .manager
        .selected_start(&f.lease, &f.models, f.epoch, true, &client, token);
    assert_eq!(
        after, before,
        "inert retry never runs or rewrites canonical evidence"
    );
    assert_eq!(opened["phase"], "completed");
    assert!(opened["run_token"].is_string());
    let duplicate = duplicate.expect("read open must preserve the admitted execution receipt");
    assert_eq!(duplicate["run_id"], admitted["run_id"]);
    assert_eq!(duplicate["operation_id"], admitted["operation_id"]);
    assert_eq!(duplicate["phase"], "completed");
    assert_eq!(
        duplicate["run_token"],
        Value::Null,
        "execution receipt cannot promote a read grant"
    );
    assert_eq!(duplicate["binding"], Value::Null);
    assert_eq!(current["operation_id"], opened["operation_id"]);
    assert_eq!(current["run_token"], opened["run_token"]);
    assert_eq!(current["binding"], opened["binding"]);
    assert!(matches!(revoked, Err(error) if error == "UnknownEvaluationRun"));
}
