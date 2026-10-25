//! Read-only selected-native setup evidence. No assets, approval or runtime owner.
use super::{
    decode, ordinary, read, shared_setup_shares, Ledger, Reservation, Result, Settlement,
    SetupRecord, PREPARATION_MS,
};
use serde::{de, Deserialize, Deserializer};
use serde_json::Value;
use std::{collections::BTreeMap, collections::BTreeSet, fs, io::ErrorKind, path::Path};

// Preserve raw member uniqueness before Value can collapse duplicate metrics.
// This decoder only reads retained diagnostics; it grants no runtime authority.
struct UniqueLoad(Value);
impl<'de> Deserialize<'de> for UniqueLoad {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> std::result::Result<Self, D::Error> {
        struct Visitor;
        impl<'de> de::Visitor<'de> for Visitor {
            type Value = UniqueLoad;
            fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                formatter.write_str("unique load metric members")
            }
            fn visit_map<M: de::MapAccess<'de>>(
                self,
                mut map: M,
            ) -> std::result::Result<Self::Value, M::Error> {
                let mut fields = serde_json::Map::new();
                while let Some(key) = map.next_key::<String>()? {
                    if fields.len() >= 9 || fields.contains_key(&key) {
                        return Err(de::Error::custom("SetupIntegrity"));
                    }
                    fields.insert(key, map.next_value::<Value>()?);
                }
                Ok(UniqueLoad(Value::Object(fields)))
            }
        }
        deserializer.deserialize_map(Visitor)
    }
}

#[derive(Deserialize)]
struct LoadField {
    #[serde(deserialize_with = "required_load")]
    load: Option<UniqueLoad>,
}
fn required_load<'de, D: Deserializer<'de>>(
    deserializer: D,
) -> std::result::Result<Option<UniqueLoad>, D::Error> {
    Option::<UniqueLoad>::deserialize(deserializer)
}

fn valid_load(load: &Value) -> bool {
    let Some(fields) = load.as_object() else {
        return false;
    };
    let durations = ["load_ms", "prefill_ms", "decode_ms", "total_ms"];
    let counts = [
        "input_tokens",
        "output_tokens",
        "model_loads",
        "contexts_created",
        "abort_callbacks",
    ];
    fields.len() == durations.len() + counts.len()
        && durations.iter().all(|key| {
            fields
                .get(*key)
                .and_then(Value::as_f64)
                .is_some_and(|value| value.is_finite() && value >= 0.0)
        })
        && counts.iter().all(|key| {
            fields
                .get(*key)
                .and_then(Value::as_u64)
                .is_some_and(|value| u32::try_from(value).is_ok())
        })
        // Same reply limits as LocalRuntime::parse_reply, without requiring a
        // runtime dependency merely to inspect retained native diagnostics.
        && fields["input_tokens"].as_u64().is_some_and(|value| value <= 4096)
        && fields["output_tokens"].as_u64().is_some_and(|value| value <= 350)
}

fn invocation(dir: &Path, binding: &str, index: usize, minimum_share: u64) -> Result<()> {
    let path = dir.join(format!("invocation-{index:02}.json"));
    let reservation: Reservation = decode(&path, 4096).map_err(|_| "SetupIntegrity")?;
    if reservation.version != 1
        || reservation.binding != binding
        || reservation.index != index
        || reservation.story != "preparation"
        || reservation.turn != "preparation"
        || reservation.ms != PREPARATION_MS
        || reservation.roles != 0
    {
        return Err("SetupIntegrity".into());
    }
    let settled = dir.join(format!("invocation-{index:02}-settled.json"));
    ordinary(&settled).map_err(|_| "SetupIntegrity")?;
    match fs::symlink_metadata(&settled) {
        Err(error) if error.kind() == ErrorKind::NotFound => {
            // An interrupted finish can leave only the other arm known. Never
            // create a settlement or refund this full unknown reservation.
            return Ok(());
        }
        Err(_) => return Err("SetupIntegrity".into()),
        Ok(metadata) if !metadata.is_file() => return Err("SetupIntegrity".into()),
        Ok(_) => {}
    }
    let settlement: Settlement = decode(&settled, 4096).map_err(|_| "SetupIntegrity")?;
    if settlement.version != 1
        || settlement.binding != binding
        || settlement.index != index
        || settlement.roles != 0
        || settlement.ms < minimum_share
    {
        return Err("SetupIntegrity".into());
    }
    Ok(())
}

pub(super) fn read_setups(dir: &Path, binding: &str, native: bool) -> Result<Vec<SetupRecord>> {
    ordinary(dir).map_err(|_| "SetupIntegrity")?;
    for arm in ["left", "right"] {
        let path = dir.join(arm);
        ordinary(&path).map_err(|_| "SetupIntegrity")?;
        if !fs::metadata(&path).map_err(|_| "SetupIntegrity")?.is_dir() {
            return Err("SetupIntegrity".into());
        }
        // Reuse the real bounded ledger decoder for gaps, orphan settlements,
        // admission limits and arithmetic, without admitting or settling work.
        Ledger::load(&path, binding).map_err(|_| "SetupIntegrity")?;
    }
    let mut setups = BTreeMap::new();
    let mut right_ids = BTreeSet::new();
    // The closed selected root allows 32 setups, four root files and two arms.
    // This extra scan bound also protects direct private reader calls.
    for (count, entry) in fs::read_dir(dir)
        .map_err(|_| "SetupIntegrity")?
        .take(65)
        .enumerate()
    {
        if count >= 64 {
            return Err("SetupIntegrity".into());
        }
        let entry = entry.map_err(|_| "SetupIntegrity")?;
        let name = entry.file_name();
        let name = name.to_str().ok_or("SetupIntegrity")?;
        if !name.to_ascii_lowercase().starts_with("setup") {
            continue;
        }
        let index = name
            .strip_prefix("setup-")
            .and_then(|value| value.strip_suffix(".json"))
            .and_then(|value| value.parse::<usize>().ok())
            .filter(|index| *index < 32)
            .ok_or("SetupIntegrity")?;
        if name != format!("setup-{index:02}.json") || !native {
            return Err("SetupIntegrity".into());
        }
        let bytes = read(&entry.path(), 64 * 1024).map_err(|_| "SetupIntegrity")?;
        // The first typed decoder rejects unknown/duplicate root fields. The
        // second requires the nullable load field and raw metric uniqueness
        // from the SAME bounded bytes, before any Value interpretation.
        let setup: SetupRecord = serde_json::from_slice(&bytes).map_err(|_| "SetupIntegrity")?;
        let strict: LoadField = serde_json::from_slice(&bytes).map_err(|_| "SetupIntegrity")?;
        if setup.version != 2
            || setup.binding != binding
            || setup.left_invocation != index
            || setup.right_invocation >= 32
            || !setup.native
            || !matches!(setup.status.as_str(), "loaded" | "failed")
            || (setup.status == "loaded" && setup.load.is_none())
            || (setup.status == "loaded" && setup.physical_ms > PREPARATION_MS)
            || strict
                .load
                .as_ref()
                .is_some_and(|load| !valid_load(&load.0))
            || !right_ids.insert(setup.right_invocation)
        {
            return Err("SetupIntegrity".into());
        }
        let (left_share, right_share) = shared_setup_shares(setup.physical_ms);
        invocation(&dir.join("left"), binding, index, left_share)?;
        invocation(
            &dir.join("right"),
            binding,
            setup.right_invocation,
            right_share,
        )?;
        if setups.insert(index, setup).is_some() {
            return Err("SetupIntegrity".into());
        }
    }
    Ok(setups.into_values().collect())
}
