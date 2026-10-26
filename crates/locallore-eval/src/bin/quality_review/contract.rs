// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Private, source-bound declarations about retained synthetic role outputs.
//!
//! This module performs no I/O or inference. Its caller supplies a freshly
//! verified comparison snapshot and Author-authorized evidence envelopes.
//! Judgments are reviewer declarations, not authenticated human assessments or
//! changes to the engine's outcomes. An ordinal is a zero-based output index.
use serde::de::{self, Deserialize, Deserializer, MapAccess, SeqAccess, Visitor};
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, fmt};

pub const MAX_REVIEW_BYTES: usize = 4 * 1024 * 1024;
const MAX_ROWS: usize = 48;
const MAX_SELECTED: usize = 8;
const MAX_RATIONALE_BYTES: usize = 1024;
const DIRECTOR: &[&str] = &["intent_fidelity", "scope_attribution"];
const NARRATOR: &[&str] = &[
    "outcome_fidelity", "player_agency", "voice", "readability",
    "repetition_pacing", "enjoyment",
];
const RATINGS: &[&str] = &["satisfactory", "concern", "not_assessed"];

pub struct SourceRow {
    pub capture: Value,
    pub outputs: Value,
}

fn error<T>(code: &str) -> Result<T, String> { Err(code.into()) }
fn digest(bytes: &[u8]) -> String { format!("{:x}", Sha256::digest(bytes)) }
fn encoded(v: &Value) -> Result<Vec<u8>, String> {
    serde_json::to_vec(v).map_err(|_| "Encoding".into())
}
fn bounded(v: Value) -> Result<Value, String> {
    if encoded(&v)?.len() > MAX_REVIEW_BYTES { return error("ReviewBudget"); }
    Ok(v)
}
fn hex(v: &Value) -> bool {
    v.as_str().is_some_and(|s| s.len() == 64 &&
        s.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)))
}
fn dimensions(role: &str) -> Result<&'static [&'static str], String> {
    match role { "director" => Ok(DIRECTOR), "narrator" => Ok(NARRATOR), _ => error("Role") }
}
fn exact_keys(value: &Value, keys: &[&str]) -> Result<(), String> {
    let map = value.as_object().ok_or("Shape")?;
    if map.len() != keys.len() || keys.iter().any(|key| !map.contains_key(*key)) {
        return error("Fields");
    }
    Ok(())
}

// Evidence is already verified by the facade. Check the public envelope and
// selected-row/raw identities again, without treating capture as canon.
fn evidence<'a>(v: &'a Value, snapshot: &Value, row: &Value, kind: &str)
    -> Result<&'a Value, String>
{
    exact_keys(v, &["version", "binding", "row", "scope", "before_head", "after_head",
        "observer", "edge", "read_only", "generation_grant", "body"])?;
    if v["version"] != json!(1) || v["binding"] != snapshot["binding"] ||
        v["row"] != json!({"turn":row["turn"],"arm":row["arm"]}) ||
        v["observer"] != json!({"kind":"omniscient"}) ||
        v["edge"] != Value::Null || v["read_only"] != true ||
        v["generation_grant"] != false || v["before_head"].as_u64().is_none() ||
        v["after_head"].as_u64().is_none() || !v["scope"].is_object()
    { return error("EvidenceBinding"); }
    let body = &v["body"];
    if body["kind"] == "missing" {
        exact_keys(body, &["kind", "reason"])?;
        let reason = match kind { "capture" => "capture_unavailable", _ => "recording_unavailable" };
        if body["reason"] != reason { return error("EvidenceMissing"); }
    } else {
        exact_keys(body, &["kind", kind])?;
        if body["kind"] != kind { return error("EvidenceKind"); }
    }
    Ok(body)
}

/// Builds an immutable full-denominator packet. Only the first selected.len()
/// rows export private evidence; every other report row remains represented.
pub fn template(snapshot: &Value, selected: &[SourceRow]) -> Result<Value, String> {
    let report = &snapshot["report"];
    let rows = report["turns"].as_array().ok_or("Snapshot")?;
    if rows.is_empty() { return error("NoRows"); }
    if rows.len() > MAX_ROWS || selected.is_empty() || selected.len() > MAX_SELECTED ||
        selected.len() > rows.len() { return error("SelectionBudget"); }
    if snapshot["version"] != json!(1) || snapshot["protocol_version"] != json!(2) ||
        snapshot["read_only"] != true || snapshot["execution_available"] != false ||
        !hex(&snapshot["binding"]) || report["version"] != json!(2) ||
        report["quality_accepted"] != false || report["source_matches"].as_bool().is_none() ||
        !matches!(report["lane"].as_str(), Some("native_current_policy_comparison" |
            "scripted_current_policy_comparison"))
    { return error("Snapshot"); }
    let mut identities = BTreeSet::new();
    let mut entries = Vec::with_capacity(rows.len());
    for (index, row) in rows.iter().enumerate() {
        let turn = row["turn"].as_str().filter(|s| !s.is_empty()).ok_or("Row")?;
        let arm = row["arm"].as_str().ok_or("Row")?;
        if !matches!(arm, "left" | "right") || !identities.insert((turn, arm)) {
            return error("RowIdentity");
        }
        let mut assessments = Vec::new();
        let (capture, outputs) = if let Some(source) = selected.get(index) {
            let capture_body = evidence(&source.capture, snapshot, row, "capture")?;
            let output_body = evidence(&source.outputs, snapshot, row, "outputs")?;
            if capture_body["kind"] == "capture" &&
                (!hex(&row["capture_sha256"]) ||
                 row["capture_sha256"] != digest(&encoded(&capture_body["capture"])?))
            { return error("CaptureHash"); }
            if output_body["kind"] == "outputs" {
                let raw = output_body["outputs"].as_array().ok_or("Outputs")?;
                if raw.len() > 3 { return error("OutputBudget"); }
                for (ordinal, output) in raw.iter().enumerate() {
                    exact_keys(output, &["role", "bytes", "sha256", "text"])?;
                    let role = output["role"].as_str().ok_or("Role")?;
                    let dims = dimensions(role)?;
                    let text = output["text"].as_str().ok_or("OutputText")?;
                    if text.len() > 16384 || output["bytes"].as_u64() != Some(text.len() as u64) ||
                        !hex(&output["sha256"]) || output["sha256"] != digest(text.as_bytes())
                    { return error("OutputHash"); }
                    let judgments: Map<String, Value> = dims.iter().map(|d|
                        (d.to_string(), json!("not_assessed"))).collect();
                    assessments.push(json!({"ordinal":ordinal,"role":role,
                        "bytes":output["bytes"],"sha256":output["sha256"],
                        "judgments":judgments,"rationale":null}));
                }
                // Repaired Director attempts remain distinct; impossible role
                // ordering cannot be interpreted as a valid component run.
                let order: Vec<_> = raw.iter().map(|v| v["role"].as_str().unwrap_or("")).collect();
                if !matches!(order.as_slice(), [] | ["director"] |
                    ["director", "director"] | ["director", "narrator"] |
                    ["director", "director", "narrator"])
                { return error("RoleOrder"); }
            }
            (source.capture.clone(), source.outputs.clone())
        } else { (Value::Null, Value::Null) };
        entries.push(json!({"turn":turn,"arm":arm,"selected":index<selected.len(),
            "source_row":row,"capture":capture,"outputs":outputs,"assessments":assessments}));
    }
    bounded(json!({"version":1,"scope":"locallore_role_review","rubric":"role-quality-v1",
        "source":{"snapshot_binding":snapshot["binding"],"report_sha256":digest(&encoded(report)?),
            "lane":report["lane"],"source_matches":report["source_matches"],
            "total_turns":rows.len(),"selected_turns":selected.len(),"sampling":"first_n_report_rows"},
        "reviewer":null,"quality_accepted":false,"entries":entries,
        "limitations":["Reviewer declarations are self-reported and unverified.",
            "Integrated role outputs are not independent Director-only or Narrator-only executions.",
            "Director failure can censor Narrator availability; unavailable rows remain in denominators.",
            "Fallback is not generated-prose success; scripted output is not native model evidence.",
            "Manual judgments cannot override canonical failures or source/provenance flags.",
            "No composite quality score, human authenticity or quality acceptance is established."]}))
}

// Deserialize every object through this visitor: Value alone silently accepts
// duplicate keys, including duplicates nested in immutable evidence or ratings.
struct Unique(Value);
impl<'de> Deserialize<'de> for Unique {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        struct V;
        impl<'de> Visitor<'de> for V {
            type Value = Unique;
            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result { f.write_str("unique-key JSON") }
            fn visit_bool<E: de::Error>(self, v: bool) -> Result<Unique,E> { Ok(Unique(json!(v))) }
            fn visit_i64<E: de::Error>(self, v: i64) -> Result<Unique,E> { Ok(Unique(json!(v))) }
            fn visit_u64<E: de::Error>(self, v: u64) -> Result<Unique,E> { Ok(Unique(json!(v))) }
            fn visit_f64<E: de::Error>(self, v: f64) -> Result<Unique,E> {
                serde_json::Number::from_f64(v).map(|n| Unique(Value::Number(n)))
                    .ok_or_else(|| E::custom("Number"))
            }
            fn visit_str<E: de::Error>(self, v: &str) -> Result<Unique,E> { Ok(Unique(json!(v))) }
            fn visit_string<E: de::Error>(self, v: String) -> Result<Unique,E> { Ok(Unique(json!(v))) }
            fn visit_none<E: de::Error>(self) -> Result<Unique,E> { Ok(Unique(Value::Null)) }
            fn visit_unit<E: de::Error>(self) -> Result<Unique,E> { Ok(Unique(Value::Null)) }
            fn visit_seq<A: SeqAccess<'de>>(self, mut seq: A) -> Result<Unique,A::Error> {
                let mut out=Vec::new();
                while let Some(Unique(v))=seq.next_element::<Unique>()? { out.push(v); }
                Ok(Unique(Value::Array(out)))
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Unique,A::Error> {
                let mut out=Map::new();
                while let Some(key)=map.next_key::<String>()? {
                    if out.contains_key(&key) { return Err(de::Error::custom("DuplicateKey")); }
                    let Unique(v)=map.next_value::<Unique>()?;
                    out.insert(key,v);
                }
                Ok(Unique(Value::Object(out)))
            }
        }
        d.deserialize_any(V)
    }
}
fn decode(bytes: &[u8]) -> Result<Value, String> {
    if bytes.is_empty() || bytes.len()>MAX_REVIEW_BYTES { return error("ReviewBudget"); }
    let mut d=serde_json::Deserializer::from_slice(bytes);
    let Unique(v)=Unique::deserialize(&mut d).map_err(|_| "ReviewJson")?;
    d.end().map_err(|_| "ReviewJson")?;
    Ok(v)
}

#[derive(Default)]
struct Counts { attempts: usize, reviewed: usize, dimensions: usize, satisfactory: usize,
    concern: usize, not_assessed: usize }
impl Counts {
    fn value(&self) -> Value { json!({"attempts":self.attempts,"reviewed_attempts":self.reviewed,
        "dimensions":self.dimensions,"satisfactory":self.satisfactory,"concern":self.concern,
        "not_assessed":self.not_assessed}) }
}
fn mutable(v: &mut Value, mut counts: Option<&mut [Counts;2]>) -> Result<bool,String> {
    exact_keys(v,&["version","scope","rubric","source","reviewer","quality_accepted",
        "entries","limitations"])?;
    let reviewer=&v["reviewer"];
    if !reviewer.is_null() && !reviewer.as_str().is_some_and(|s| !s.is_empty() && s.len()<=48 &&
        s.bytes().all(|b| b.is_ascii_alphanumeric() || matches!(b,b'_'|b'-'|b'.')))
    { return error("Reviewer"); }
    let declared=!reviewer.is_null();
    v["reviewer"]=Value::Null;
    let entries=v["entries"].as_array_mut().ok_or("Entries")?;
    let mut changed=false;
    for entry in entries {
        for assessment in entry["assessments"].as_array_mut().ok_or("Assessments")? {
            exact_keys(assessment,&["ordinal","role","bytes","sha256","judgments","rationale"])?;
            let role=assessment["role"].as_str().ok_or("Role")?;
            let dims=dimensions(role)?;
            let role_index=usize::from(role=="narrator");
            exact_keys(&assessment["judgments"],dims)?;
            let mut reviewed=false;
            for dimension in dims {
                let rating=assessment["judgments"][dimension].as_str().ok_or("Rating")?;
                if !RATINGS.contains(&rating) { return error("Rating"); }
                if rating!="not_assessed" { changed=true; reviewed=true; }
                if let Some(c)=counts.as_deref_mut() {
                    c[role_index].dimensions+=1;
                    match rating { "satisfactory"=>c[role_index].satisfactory+=1,
                        "concern"=>c[role_index].concern+=1,_=>c[role_index].not_assessed+=1 }
                }
                assessment["judgments"][dimension]=json!("not_assessed");
            }
            if let Some(c)=counts.as_deref_mut() {
                c[role_index].attempts+=1;
                c[role_index].reviewed+=usize::from(reviewed);
            }
            let rationale=&assessment["rationale"];
            if !rationale.is_null() {
                if !rationale.as_str().is_some_and(|s| s.len()<=MAX_RATIONALE_BYTES &&
                    !s.chars().any(char::is_control)) { return error("Rationale"); }
                changed=true;
            }
            assessment["rationale"]=Value::Null;
        }
    }
    if changed && !declared { return error("ReviewerRequired"); }
    Ok(changed)
}

/// Reads only the bounded selection count needed to obtain fresh evidence.
/// This is not validation of the review: summarize must still compare every
/// immutable field after the caller rebuilds the actual source packet.
pub fn selected_count(review_bytes: &[u8]) -> Result<usize, String> {
    let review=decode(review_bytes)?;
    let source=review.as_object().and_then(|v|v.get("source"))
        .and_then(Value::as_object).ok_or("Selection")?;
    let count=source.get("selected_turns").and_then(Value::as_u64).ok_or("Selection")?;
    if !(1..=MAX_SELECTED as u64).contains(&count) { return error("SelectionBudget"); }
    Ok(count as usize)
}

/// Validates declarations against a freshly rebuilt packet. The summary never
/// copies prose, identity tokens or rationale, and never changes quality status.
pub fn summarize(expected: &Value, review_bytes: &[u8]) -> Result<Value, String> {
    bounded(expected.clone())?;
    let mut review=decode(review_bytes)?;
    let mut basis=expected.clone();
    mutable(&mut basis,None)?;
    let mut counts=[Counts::default(),Counts::default()];
    mutable(&mut review,Some(&mut counts))?;
    if review!=basis { return error("ImmutableMismatch"); }
    let entries=expected["entries"].as_array().ok_or("Entries")?;
    let selected=entries.iter().filter(|e| e["selected"]==true).count();
    let mut missing_capture=0; let mut missing_outputs=0; let mut no_outputs=0;
    let mut unselected=0; let mut failed=0; let mut passed=0; let mut passed_unknown=0;
    let mut fallback=0; let mut no_fallback=0; let mut fallback_unknown=0;
    let mut privacy_failed=0; let mut policy_failed=0; let mut quality_flag_rows=0;
    let mut phases=Map::new();
    for entry in entries {
        let row=&entry["source_row"];
        match row["passed"].as_bool() { Some(true)=>passed+=1,Some(false)=>failed+=1,_=>passed_unknown+=1 }
        match row["fallback"].as_bool() { Some(true)=>fallback+=1,Some(false)=>no_fallback+=1,_=>fallback_unknown+=1 }
        privacy_failed+=usize::from(row["privacy_passed"]==false);
        policy_failed+=usize::from(row["policy_matches"]==false);
        quality_flag_rows+=usize::from(row["quality_flags"].as_array().is_some_and(|v|!v.is_empty()));
        let phase=row["phase"].as_str().ok_or("Phase")?;
        if !matches!(phase,"committed"|"failed"|"rejected"|"cancelled"|"stale"|
            "not_run_dependency"|"guard_only"|"unavailable"|"pending"|"prepared")
        { return error("Phase"); }
        let old=phases.get(phase).and_then(Value::as_u64).unwrap_or(0);
        phases.insert(phase.into(),json!(old+1));
        if entry["selected"]==true {
            missing_capture+=usize::from(entry["capture"]["body"]["kind"]=="missing");
            missing_outputs+=usize::from(entry["outputs"]["body"]["kind"]=="missing");
            no_outputs+=usize::from(entry["assessments"].as_array().is_some_and(Vec::is_empty));
        } else { unselected+=1; }
    }
    bounded(json!({"version":1,"scope":"locallore_role_review_summary","rubric":"role-quality-v1",
        "source":expected["source"],"review_sha256":digest(review_bytes),
        "review_origin":"reviewer_declared","quality_accepted":false,
        "coverage":{"total_turns":entries.len(),"selected_turns":selected,"unselected_turns":unselected,
            "selected_missing_capture":missing_capture,"selected_missing_outputs":missing_outputs,
            "selected_without_outputs":no_outputs},
        "original_outcomes":{"passed":passed,"failed":failed,"passed_unknown":passed_unknown,
            "fallback":fallback,"no_fallback":no_fallback,"fallback_unknown":fallback_unknown,
            "privacy_failed":privacy_failed,"policy_failed":policy_failed,
            "quality_flag_rows":quality_flag_rows,"phases":phases},
        "roles":{"director":counts[0].value(),"narrator":counts[1].value()},
        "limitations":expected["limitations"]}))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn envelope(snapshot: &Value,row: &Value,body: Value)->Value {
        json!({"version":1,"binding":snapshot["binding"],
            "row":{"turn":row["turn"],"arm":row["arm"]},
            "scope":{"story":"synthetic","branch":"root"},"before_head":0,"after_head":1,
            "observer":{"kind":"omniscient"},"edge":null,"read_only":true,
            "generation_grant":false,"body":body})
    }
    fn raw(role:&str,text:&str)->Value {
        json!({"role":role,"text":text,"bytes":text.len(),"sha256":digest(text.as_bytes())})
    }
    fn input(native:bool)->(Value,Vec<SourceRow>) {
        let capture=json!({"version":2,"artifacts":[]});
        let rows:Vec<Value>=(0..12).map(|i|json!({"turn":format!("turn-{}",i/2),
            "arm":if i%2==0{"left"}else{"right"},
            "phase":if i<4{"committed"}else{"not_run_dependency"},"passed":i<4,
            "fallback":if i==0{json!(true)}else if i<4{json!(false)}else{Value::Null},
            "capture_sha256":digest(&encoded(&capture).unwrap()),
            "privacy_passed":i!=8,"policy_matches":i!=10,"quality_flags":[],
            "failures":if i<4{json!([])}else{json!(["DependentFailure"])}})).collect();
        let snapshot=json!({"version":1,"protocol_version":2,"binding":"a".repeat(64),
            "read_only":true,"execution_available":false,"report":{"version":2,
            "lane":if native{"native_current_policy_comparison"}else{"scripted_current_policy_comparison"},
            "source_matches":false,"quality_accepted":false,"turns":rows}});
        let selected=(0..2).map(|i|SourceRow{
            capture:envelope(&snapshot,&snapshot["report"]["turns"][i],
                json!({"kind":"capture","capture":capture})),
            outputs:envelope(&snapshot,&snapshot["report"]["turns"][i],json!({"kind":"outputs",
                "outputs":if i==0 {json!([raw("director","original-director"),
                    raw("director","repaired-director"),raw("narrator","RAW_SENTINEL")])}
                else {json!([raw("director","other-director")])}})),
        }).collect();
        (snapshot,selected)
    }
    fn packet()->Value { let(s,r)=input(true);template(&s,&r).unwrap() }
    fn summarize_value(expected:&Value,review:&Value)->Result<Value,String> {
        summarize(expected,&encoded(review).unwrap())
    }

    #[test]
    fn pending_keeps_full_denominators_and_original_failures() {
        let p=packet();let s=summarize_value(&p,&p).unwrap();
        assert_eq!(p["entries"].as_array().unwrap().len(),12);
        assert_eq!(p["entries"][2]["capture"],Value::Null);
        assert_eq!(s["coverage"],json!({"total_turns":12,"selected_turns":2,
            "unselected_turns":10,"selected_missing_capture":0,"selected_missing_outputs":0,
            "selected_without_outputs":0}));
        assert_eq!(s["roles"]["director"],json!({"attempts":3,"reviewed_attempts":0,
            "dimensions":6,"satisfactory":0,"concern":0,"not_assessed":6}));
        assert_eq!(s["roles"]["narrator"]["dimensions"],6);
        assert_eq!(s["original_outcomes"]["failed"],8);
        assert_eq!(s["original_outcomes"]["fallback"],1);
        assert_eq!(s["original_outcomes"]["fallback_unknown"],8);
        assert_eq!(s["source"]["source_matches"],false);
        assert_eq!(s["original_outcomes"]["privacy_failed"],1);
        assert_eq!(s["original_outcomes"]["policy_failed"],1);
        assert_eq!(s["quality_accepted"],false);
    }
    #[test]
    fn partial_review_counts_original_attempts_and_does_not_echo_private_fields() {
        let p=packet();let mut r=p.clone();r["reviewer"]=json!("PRIVATE_REVIEWER");
        r["entries"][0]["assessments"][1]["judgments"]["intent_fidelity"]=json!("concern");
        r["entries"][0]["assessments"][2]["judgments"]["readability"]=json!("satisfactory");
        r["entries"][0]["assessments"][2]["rationale"]=json!("PRIVATE_RATIONALE");
        let s=summarize_value(&p,&r).unwrap();
        assert_eq!(s["roles"]["director"]["reviewed_attempts"],1);
        assert_eq!(s["roles"]["director"]["concern"],1);
        assert_eq!(s["roles"]["narrator"]["not_assessed"],5);
        assert_eq!(s["original_outcomes"]["fallback"],1);
        let text=String::from_utf8(encoded(&s).unwrap()).unwrap();
        for private in ["RAW_SENTINEL","PRIVATE_REVIEWER","PRIVATE_RATIONALE"] {
            assert!(!text.contains(private));
        }
        assert_eq!(s["review_origin"],"reviewer_declared");
        assert_eq!(s["quality_accepted"],false);
        assert_eq!(s["review_sha256"],digest(&encoded(&r).unwrap()));
    }
    #[test]
    fn scripted_and_native_remain_distinct_and_no_manual_quality_acceptance() {
        for native in [false,true] {
            let(s,rows)=input(native);let p=template(&s,&rows).unwrap();
            let result=summarize_value(&p,&p).unwrap();
            assert_eq!(result["source"]["lane"],s["report"]["lane"]);
            assert_eq!(result["quality_accepted"],false);
            let mut changed=p.clone();changed["quality_accepted"]=json!(true);
            assert!(summarize_value(&p,&changed).is_err());
        }
    }
    #[test]
    fn missing_capture_and_output_are_not_zero_or_success_substitutes() {
        let(s,mut rows)=input(true);
        rows[0].capture["body"]=json!({"kind":"missing","reason":"capture_unavailable"});
        rows[0].outputs["body"]=json!({"kind":"missing","reason":"recording_unavailable"});
        let p=template(&s,&rows).unwrap();let result=summarize_value(&p,&p).unwrap();
        assert_eq!(p["entries"][0]["assessments"],json!([]));
        assert_eq!(p["entries"][0]["outputs"],rows[0].outputs);
        assert_eq!(result["coverage"]["selected_missing_outputs"],1);
        assert_eq!(result["coverage"]["selected_without_outputs"],1);
        assert_eq!(result["coverage"]["total_turns"],12);
        assert_eq!(result["roles"]["director"]["attempts"],1);
    }
    #[test]
    fn immutable_tampering_including_bool_counter_and_nested_evidence_is_refused() {
        let p=packet();
        for (path,replacement) in [
            ("/source/snapshot_binding",json!("b".repeat(64))),
            ("/source/report_sha256",json!("c".repeat(64))),
            ("/source/source_matches",json!(true)),
            ("/source/total_turns",json!(true)),
            ("/source/lane",json!("scripted_current_policy_comparison")),
            ("/entries/0/source_row/fallback",json!(false)),
            ("/entries/8/source_row/passed",json!(true)),
            ("/entries/0/assessments/0/ordinal",json!(1)),
            ("/entries/0/assessments/0/role",json!("narrator")),
            ("/entries/0/assessments/0/bytes",json!(true)),
            ("/entries/0/assessments/0/sha256",json!("d".repeat(64))),
            ("/entries/0/outputs/body/outputs/0/text",json!("changed")),
            ("/entries/0/capture/body/capture/version",json!(99)),
        ] {
            let mut changed=p.clone();
            *changed.pointer_mut(path).unwrap()=replacement;
            assert!(summarize_value(&p,&changed).is_err(),"{path}");
        }
    }
    #[test]
    fn omitted_extra_repeated_or_reordered_rows_and_attempts_are_refused() {
        let p=packet();
        for operation in 0..6 {
            let mut r=p.clone();
            match operation {
                0=>{r["entries"].as_array_mut().unwrap().pop();},
                1=>{let row=r["entries"][0].clone();r["entries"].as_array_mut().unwrap().push(row);},
                2=>r["entries"].as_array_mut().unwrap().swap(0,1),
                3=>{r["entries"][0]["assessments"].as_array_mut().unwrap().pop();},
                4=>r["entries"][0]["assessments"].as_array_mut().unwrap().swap(0,1),
                _=>{let a=r["entries"][0]["assessments"][0].clone();
                    r["entries"][0]["assessments"].as_array_mut().unwrap().push(a);},
            }
            assert!(summarize_value(&p,&r).is_err());
        }
    }
    #[test]
    fn unknown_fields_at_every_mutable_and_immutable_level_are_refused() {
        let p=packet();
        for path in ["","/source","/entries/0","/entries/0/source_row",
            "/entries/0/outputs/body","/entries/0/assessments/0",
            "/entries/0/assessments/0/judgments"] {
            let mut r=p.clone();r.pointer_mut(path).unwrap().as_object_mut().unwrap()
                .insert("unknown".into(),json!(0));
            assert!(summarize_value(&p,&r).is_err(),"{path}");
        }
        let mut r=p.clone();r.as_object_mut().unwrap().remove("reviewer");
        assert!(summarize_value(&p,&r).is_err());
        let mut r=p.clone();r["entries"][0]["assessments"][0].as_object_mut().unwrap().remove("rationale");
        assert!(summarize_value(&p,&r).is_err());
    }
    #[test]
    fn duplicate_keys_are_refused_recursively_including_escaped_names() {
        let p=packet();let text=String::from_utf8(encoded(&p).unwrap()).unwrap();
        for (needle,replacement) in [
            ("\"reviewer\":null","\"reviewer\":null,\"reviewer\":null"),
            ("\"intent_fidelity\":\"not_assessed\"",
                "\"intent_fidelity\":\"not_assessed\",\"intent_fidelit\\u0079\":\"concern\""),
            ("\"kind\":\"omniscient\"","\"kind\":\"omniscient\",\"kind\":\"omniscient\""),
        ] {
            let changed=text.replacen(needle,replacement,1);
            assert_ne!(changed,text);
            assert!(summarize(&p,changed.as_bytes()).is_err());
        }
    }
    #[test]
    fn ratings_identity_control_and_rationale_limits_are_enforced() {
        let p=packet();
        for bad in [json!(true),json!(1),json!(null),json!("excellent"),json!(["concern"])] {
            let mut r=p.clone();r["reviewer"]=json!("reviewer");
            r["entries"][0]["assessments"][0]["judgments"]["intent_fidelity"]=bad;
            assert!(summarize_value(&p,&r).is_err());
        }
        for bad in [json!(""),json!("a".repeat(49)),json!("name with spaces"),json!("é"),json!(true)] {
            let mut r=p.clone();r["reviewer"]=bad;assert!(summarize_value(&p,&r).is_err());
        }
        for bad in [json!("\n"),json!("\u{7f}"),json!("x".repeat(1025)),json!(false)] {
            let mut r=p.clone();r["reviewer"]=json!("reviewer");
            r["entries"][0]["assessments"][0]["rationale"]=bad;
            assert!(summarize_value(&p,&r).is_err());
        }
        let mut r=p.clone();r["entries"][0]["assessments"][0]["judgments"]["intent_fidelity"]=json!("concern");
        assert_eq!(summarize_value(&p,&r).unwrap_err(),"ReviewerRequired");
        let mut r=p.clone();r["reviewer"]=json!("R-1._");
        r["entries"][0]["assessments"][0]["rationale"]=json!("x".repeat(1024));
        let s=summarize_value(&p,&r).unwrap();assert_eq!(s["roles"]["director"]["reviewed_attempts"],0);
    }
    #[test]
    fn count_is_only_an_integer_bounded_prefix_hint_not_review_validation() {
        assert_eq!(selected_count(br#"{"source":{"selected_turns":8}}"#).unwrap(),8);
        for bytes in [br#"{"source":{"selected_turns":true}}"#.as_slice(),
            br#"{"source":{"selected_turns":1.0}}"#,br#"{"source":{"selected_turns":0}}"#,
            br#"{"source":{"selected_turns":9}}"#,br#"{"source":{"selected_turns":-1}}"#,
            br#"{"source":{"selected_turns":1,"selected_turns":2}}"#,
            br#"{"source":null}"#,br#"[]"#,br#"{} trailing"#] {
            assert!(selected_count(bytes).is_err());
        }
        assert!(selected_count(&vec![b' ';MAX_REVIEW_BYTES+1]).is_err());
        let p=packet();assert!(summarize(&p,br#"{"source":{"selected_turns":8}}"#).is_err());
    }
    #[test]
    fn source_envelope_binding_hash_budget_role_and_no_rows_checks() {
        let(s,rows)=input(true);
        for operation in 0..7 {
            let mut copies:Vec<_>=rows.iter().map(|r|SourceRow{capture:r.capture.clone(),outputs:r.outputs.clone()}).collect();
            match operation {
                0=>copies[0].outputs["binding"]=json!("b".repeat(64)),
                1=>copies[0].outputs["observer"]=json!({"kind":"player"}),
                2=>copies[0].outputs["generation_grant"]=json!(true),
                3=>copies[0].capture["body"]["capture"]["version"]=json!(99),
                4=>copies[0].outputs["body"]["outputs"][0]["bytes"]=json!(true),
                5=>copies[0].outputs["body"]["outputs"][0]["role"]=json!("narrator"),
                _=>copies[0].outputs["body"]["outputs"][0]["text"]=json!("changed"),
            }
            assert!(template(&s,&copies).is_err());
        }
        let mut empty=s.clone();empty["report"]["turns"]=json!([]);
        assert_eq!(template(&empty,&[]).unwrap_err(),"NoRows");
        assert!(template(&s,&[]).is_err());
        let mut duplicate=s.clone();duplicate["report"]["turns"][1]=duplicate["report"]["turns"][0].clone();
        assert!(template(&duplicate,&rows).is_err());
        let mut r=packet();r["reviewer"]=json!("x".repeat(MAX_REVIEW_BYTES));
        assert!(summarize_value(&packet(),&r).is_err());
    }
}
