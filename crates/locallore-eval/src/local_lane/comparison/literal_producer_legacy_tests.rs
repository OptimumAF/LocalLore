//! Actual V2 producer semantic reference captured before shared mechanics move.
use super::*;

#[test]
fn original_v2_actual_scene_semantics_survive_shared_execution_and_checkpoint_extraction() {
    let path = std::env::temp_dir().join(format!(
        "locallore-v2-producer-reference-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    let original = run_comparison(
        &path,
        false,
        ComparisonKind::ContinuousRollout,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
        None,
    )
    .unwrap();
    let reopened = inspect_comparison(&path).unwrap();
    assert_eq!(
        encode(&original.turns).unwrap(),
        encode(&reopened.turns).unwrap()
    );
    assert_eq!(original.turns.len(), 12);
    assert!(original.turns.iter().all(|r| r.passed));
    let rows: Vec<_> = original
        .turns
        .iter()
        .map(|row| {
            let mut value = serde_json::to_value(row).unwrap();
            let object = value.as_object_mut().unwrap();
            // These contain actual live elapsed/deadline/stage bytes. This projection
            // is all OTHER row fields, not the full timing-bearing report/evidence.
            for key in [
                "elapsed_ms",
                "first_final_response_ms",
                "commit_elapsed_ms",
                "trace",
                "stages",
                "actual_receipt_sha256",
                "capture_sha256",
                "recording_sha256",
                "role_metrics",
            ] {
                assert!(object.remove(key).is_some());
            }
            value
        })
        .collect();
    let bytes = encode(&json!({"projection_version":1,"base":"97d1f670","rows":rows})).unwrap();
    let hash = digest(&bytes);
    eprintln!(
        "ORIGINAL_V2_PRODUCER_SEMANTICS rows=12 bytes={} sha256={hash}",
        bytes.len()
    );
    assert_eq!(
        hash, "9134ccc9609b3f9c5942c04f8c2c9fe1e008e962bcae537b42139e0e4642a065",
        "first run captures original production; anchor before extraction"
    );
}
