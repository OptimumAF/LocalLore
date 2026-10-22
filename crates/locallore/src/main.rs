use locallore::{contracts::*, engine::Engine, inference::*};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))?;
    let mut engine = Engine::new(seed.clone())?;
    let request = engine.request(
        "give-potion",
        Intent::Actions(vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }]),
    );
    let mut provider = FakeProvider::new(FakeMode::Accepted);
    let receipt = execute(
        &mut engine,
        &request,
        &mut provider,
        &Cancellation::default(),
        Budget::default(),
    )?;
    println!("FAKE PROVIDER / HOST ONLY: {}", receipt.narration());
    let replayed = Engine::replay(seed, engine.receipts())?;
    assert_eq!(engine.canonical_bytes(), replayed.canonical_bytes());
    let mira = engine.character_context("mira", engine.scope(), engine.revision())?;
    let sable = engine.character_context("sable", engine.scope(), engine.revision())?;
    assert_eq!(mira.observations.len(), 1);
    assert!(sable.observations.is_empty());
    println!("Verified: potion owner=mira; deterministic replay matches; Mira observed gift; Sable did not.");
    println!("No disk persistence, Android, physical device, or real model was exercised.");
    Ok(())
}
