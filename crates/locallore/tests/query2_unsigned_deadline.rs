//! Native accepted values stay u64; only Query2 presentation uses decimal text.
use locallore::{contracts::*, engine::Engine, inspection_query::*};
use serde_json::{json, Value};

fn fixture(deadline: u64) -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.commitments.clear();
    let mut engine = Engine::new(seed).unwrap();
    let request = engine.request(
        "unsigned-deadline",
        Intent::Actions(vec![Command::Promise {
            id: "unsigned-promise".into(),
            to: "mira".into(),
            terms: "Return the brass key.".into(),
            deadline,
            return_item: None,
        }]),
    );
    let receipt = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    engine.commit_prepared(&receipt).unwrap();
    engine
}

fn request(engine: &Engine, version: u16, view: View) -> Query {
    Query {
        version,
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        at_revision: None,
        observer: Observer::Player,
        view,
        cursor: None,
        limit: MAX_ROWS,
        search: String::new(),
    }
}

#[test]
fn query2_promises_history_and_diff_preserve_full_unsigned_deadlines_without_changing_canon() {
    for deadline in [120, i64::MAX as u64, i64::MAX as u64 + 1, u64::MAX] {
        let engine = fixture(deadline);
        let canon = serde_json::to_vec(engine.canonical_records()).unwrap();
        let mut promises = request(&engine, 2, View::Promises);
        let page = query(&engine, &promises, false).unwrap();
        let wire = serde_json::to_value(&page).unwrap();
        let row = wire["rows"]
            .as_array()
            .unwrap()
            .iter()
            .find(|row| row["id"] == "unsigned-promise")
            .unwrap();
        assert_eq!(row["deadline"], json!(deadline.to_string()));
        // Search, count, pagination and output use the same new display representation.
        promises.search = format!("\"deadline\":\"{deadline}\"");
        assert_eq!(query(&engine, &promises, false).unwrap().total, 1);

        let mut history = request(&engine, 2, View::History);
        history.search = format!(
            "\"event\":{{\"sequence\":1,\"scope\":{{\"story\":\"{}\",\"branch\":\"{}\"}}",
            engine.scope().story,
            engine.scope().branch
        );
        let wire = serde_json::to_value(query(&engine, &history, false).unwrap()).unwrap();
        assert_eq!(wire["total"], 1);
        assert_eq!(
            wire["rows"][0]["event"]["consequence"]["commitment"]["deadline"],
            json!(deadline.to_string())
        );

        let wire = serde_json::to_value(
            query(&engine, &request(&engine, 2, View::TurnDiff), false).unwrap(),
        )
        .unwrap();
        let change = wire["rows"]
            .as_array()
            .unwrap()
            .iter()
            .find(|row| row["after"]["id"] == "unsigned-promise")
            .unwrap();
        assert_eq!(change["after"]["deadline"], json!(deadline.to_string()));
        assert_eq!(
            serde_json::to_vec(engine.canonical_records()).unwrap(),
            canon
        );
        assert_eq!(
            engine.state().commitments["unsigned-promise"].deadline,
            deadline
        );
        let receipt = serde_json::to_value(&engine.receipts()[0]).unwrap();
        assert_eq!(
            receipt["request"]["intent"]["value"][0]["deadline"],
            json!(deadline)
        );
    }
}

#[test]
fn query1_serialization_keeps_the_exact_numeric_row_contract() {
    let engine = fixture(u64::MAX);
    for view in [View::Promises, View::History, View::TurnDiff] {
        let page = query(&engine, &request(&engine, 1, view), false).unwrap();
        let encoded = serde_json::to_string(&page).unwrap();
        let rows = serde_json::to_string(&page.rows).unwrap();
        assert!(encoded.contains(&format!("\"rows\":{rows},\"next_cursor\":")));
        assert!(encoded.contains("\"deadline\":18446744073709551615"));
        assert!(!encoded.contains("\"deadline\":\"18446744073709551615\""));
        let decoded: Value = serde_json::from_str(&encoded).unwrap();
        assert_eq!(decoded["version"], 1);
    }
}
