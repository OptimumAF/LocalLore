//! Generates original synthetic Android shell samples using the real host engine.
//! Run without --check to print JSON; --check verifies the checked-in asset byte-for-byte.
use locallore::{contracts::*, engine::Engine};
use serde_json::{json, Value};

fn case(engine: &Engine, action: &str, command: Command) -> Value {
    let request = engine.request(
        &format!("android-{}-{action}", engine.revision()),
        Intent::Actions(vec![command]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let resolution = match engine.preview(&request, &proposal) {
        Ok(receipt) => {
            let mut staged = engine.clone();
            staged
                .commit(&request, &proposal, receipt.narration())
                .unwrap();
            let owner_id = &staged.state().items["potion"].owner;
            let owner_name = &staged.state().actors[owner_id].name;
            json!({
                "kind": "accepted", "revision": staged.revision(),
                "potion_owner": owner_name, "narration": receipt.narration(), "receipt": receipt,
            })
        }
        Err(error) => json!({"kind": "rejected", "error": error.to_string()}),
    };
    let mut invalid = proposal.clone();
    invalid.commands = vec![Command::UseAbility {
        ability: "invented-teleport".into(),
    }];
    let rejected_error = engine.preview(&request, &invalid).unwrap_err();
    json!({
        "action": action, "from_revision": engine.revision(),
        "request_json": serde_json::to_string(&request).unwrap(),
        "proposal_json": serde_json::to_string(&proposal).unwrap(),
        "resolution": resolution,
        "rejected_proposal_json": serde_json::to_string(&invalid).unwrap(),
        "rejected_error": rejected_error.to_string(),
    })
}

fn main() {
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let mut engine = Engine::new(seed).unwrap();
    let give = Command::Give {
        item: "potion".into(),
        to: "mira".into(),
        quantity: 1,
    };
    let ability = Command::UseAbility {
        ability: "blink".into(),
    };
    let mut cases = vec![
        case(&engine, "GIVE_POTION", give.clone()),
        case(&engine, "TRY_ABILITY", ability.clone()),
    ];
    let request = engine.request("sample-gift", Intent::Actions(vec![give]));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    engine
        .commit(&request, &proposal, preview.narration())
        .unwrap();
    cases.push(case(
        &engine,
        "GIVE_POTION",
        Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        },
    ));
    cases.push(case(&engine, "TRY_ABILITY", ability));
    let fixture = json!({
        "fixture_version": 1, "contract_version": VERSION, "scope": engine.scope(),
        "seed": engine.seed().id, "initial_revision": 0, "initial_potion_owner": "You", "cases": cases,
    });
    let text = format!("{}\n", serde_json::to_string_pretty(&fixture).unwrap());
    if std::env::args().any(|arg| arg == "--check") {
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../../apps/android/app/src/test/lantern_quay_cases.json");
        assert_eq!(
            std::fs::read_to_string(path).unwrap().replace("\r\n", "\n"),
            text,
            "Regenerate Android fixture with this example"
        );
        println!("Android fixtures match Rust engine outcomes (4 cases, contract v1).");
    } else {
        print!("{text}");
    }
}
