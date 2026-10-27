//! Closed run metadata and report dispatch. Deserialization is never execution authority.
use super::*;
use locallore_eval::memory_comparison_v4::{self as scene_wire, ComparisonReportV4, CurrentBindingV4};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum FullComparisonProtocol { LiteralV3, SceneV4 }
impl FullComparisonProtocol {
    pub(super) fn lane(self) -> ComparisonLane {
        match self { Self::LiteralV3 => ComparisonLane::Native, Self::SceneV4 => ComparisonLane::SceneNative }
    }
    fn number(self)->u16 { match self {Self::LiteralV3=>3,Self::SceneV4=>4} }
}

#[derive(Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct IndexWire<B> {
    version: u16,
    protocol_version: u16,
    input_lane: String,
    run_id: String,
    client_id: String,
    kind: core::ComparisonKind,
    initial_batch: usize,
    created_ms: u64,
    binding: B,
}
#[derive(Clone, PartialEq, Serialize)]
#[serde(untagged)]
pub(super) enum Index {
    Literal(IndexWire<CurrentBindingV3>),
    Scene(IndexWire<CurrentBindingV4>),
}
impl Index {
    pub(super) fn decode(value: Value) -> Result<Self> {
        // Select the exact closed schema by its declared tuple, never by which
        // binding happens to deserialize or by a renderer policy field.
        match (value["version"].as_u64(), value["protocol_version"].as_u64()) {
            (Some(1 | 2), Some(3)) => serde_json::from_value(value).map(Self::Literal),
            (Some(3), Some(4)) => serde_json::from_value(value).map(Self::Scene),
            _ => return Err("EvaluationIntegrity".into()),
        }.map_err(|_| "EvaluationIntegrity".into())
    }
    pub(super) fn new(lane: ComparisonLane, run_id: String, input: FullComparisonStart, created_ms: u64) -> Result<Self> {
        if lane == ComparisonLane::SceneNative {
            Ok(Self::Scene(IndexWire { version:3, protocol_version:4, input_lane:lane.name().into(), run_id, client_id:input.client_id, kind:input.kind, initial_batch:input.max_new_scenes, created_ms, binding:scene_wire::current_binding(true).map_err(failure)? }))
        } else {
            Ok(Self::Literal(IndexWire { version:lane.version(), protocol_version:3, input_lane:lane.name().into(), run_id, client_id:input.client_id, kind:input.kind, initial_batch:input.max_new_scenes, created_ms, binding:wire::current_binding(lane.native()).map_err(failure)? }))
        }
    }
    pub(super) fn lane(&self) -> Result<ComparisonLane> {
        match self {
            Self::Literal(i) => match (i.version, i.protocol_version, i.input_lane.as_str(), i.binding.native) {
                (1,3,"scripted_baseline",false) => Ok(ComparisonLane::Scripted),
                (2,3,"approved_native",true) => Ok(ComparisonLane::Native),
                _ => Err("EvaluationIntegrity".into()),
            },
            Self::Scene(i) if i.version==3 && i.protocol_version==4 && i.input_lane=="approved_native" && i.binding.native => Ok(ComparisonLane::SceneNative),
            _ => Err("EvaluationIntegrity".into()),
        }
    }
    pub(super) fn run_id(&self) -> &str { match self { Self::Literal(i)=>&i.run_id, Self::Scene(i)=>&i.run_id } }
    pub(super) fn client_id(&self) -> &str { match self { Self::Literal(i)=>&i.client_id, Self::Scene(i)=>&i.client_id } }
    pub(super) fn kind(&self) -> core::ComparisonKind { match self { Self::Literal(i)=>i.kind, Self::Scene(i)=>i.kind } }
    pub(super) fn initial_batch(&self) -> usize { match self { Self::Literal(i)=>i.initial_batch, Self::Scene(i)=>i.initial_batch } }
    pub(super) fn created_ms(&self) -> u64 { match self { Self::Literal(i)=>i.created_ms, Self::Scene(i)=>i.created_ms } }
    pub(super) fn source_sha256(&self) -> &str { match self { Self::Literal(i)=>&i.binding.source_sha256, Self::Scene(i)=>&i.binding.source_sha256 } }
    fn suite_sha256(&self) -> &str { match self { Self::Literal(i)=>&i.binding.suite_sha256, Self::Scene(i)=>&i.binding.suite_sha256 } }
    pub(super) fn protocol_version(&self) -> u16 {
        let protocol=match self { Self::Literal(_)=>FullComparisonProtocol::LiteralV3, Self::Scene(_)=>FullComparisonProtocol::SceneV4 };
        protocol.number()
    }
    fn input_lane(&self)->&str {match self {Self::Literal(i)=>&i.input_lane,Self::Scene(i)=>&i.input_lane}}
    pub(super) fn binding_value(&self) -> Result<Value> {
        match self { Self::Literal(i)=>serde_json::to_value(&i.binding), Self::Scene(i)=>serde_json::to_value(&i.binding) }.map_err(|_| "EvaluationInternal".into())
    }
    pub(super) fn validate_shape(&self) -> Result<()> {
        self.lane()?;
        let hex=|s:&str| s.len()==64 && s.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b));
        if !hex(self.source_sha256()) || !hex(self.suite_sha256()) { return Err("EvaluationIntegrity".into()); }
        let valid=match self {
            Self::Literal(i)=> { let mut shape=wire::current_binding(i.binding.native).map_err(failure)?; shape.source_sha256=i.binding.source_sha256.clone(); shape.suite_sha256=i.binding.suite_sha256.clone(); shape==i.binding },
            Self::Scene(i)=> { let mut shape=scene_wire::current_binding(true).map_err(failure)?; shape.source_sha256=i.binding.source_sha256.clone(); shape.suite_sha256=i.binding.suite_sha256.clone(); shape==i.binding },
        };
        if valid { Ok(()) } else { Err("EvaluationIntegrity".into()) }
    }
    pub(super) fn matches_current(&self) -> Result<bool> {
        Ok(match self { Self::Literal(i)=>i.binding==wire::current_binding(i.binding.native).map_err(failure)?, Self::Scene(i)=>i.binding==scene_wire::current_binding(true).map_err(failure)? })
    }
    pub(super) fn metadata(&self) -> Value {
        json!({"run_id":self.run_id(),"client_id":self.client_id(),"comparison_kind":kind_name(self.kind()),"initial_batch":self.initial_batch(),"created_ms":self.created_ms(),"protocol_version":self.protocol_version(),"input_lane":self.input_lane()})
    }
    pub(super) fn execution_metadata(&self, batch:usize) -> Value {
        let (admissions,roles,active)=match self { Self::Literal(i)=>(i.binding.max_admissions,i.binding.max_roles,i.binding.max_active_ms), Self::Scene(i)=>(i.binding.max_admissions,i.binding.max_roles,i.binding.max_active_ms) };
        json!({"version":1,"kind":"full_comparison_execution","protocol_version":self.protocol_version(),"input_lane":"approved_native","run_id":self.run_id(),"client_id":self.client_id(),"comparison_kind":kind_name(self.kind()),"batch":batch,"max_admissions":admissions,"max_roles":roles,"max_active_ms":active})
    }
    pub(super) fn inspect(&self,path:&Path)->Result<Report> {
        match self { Self::Literal(_)=>literal_v3::inspect_comparison(path).map(Report::Literal), Self::Scene(_)=>core::scene_v4::inspect_comparison(path).map(Report::Scene) }.map_err(failure)
    }
}
pub(super) enum Report { Literal(ComparisonReportV3), Scene(ComparisonReportV4) }
impl Report {
    pub(super) fn completed_scenes(&self)->usize { match self {Self::Literal(r)=>r.completed_scenes,Self::Scene(r)=>r.completed_scenes} }
    pub(super) fn completed(&self)->bool { match self {Self::Literal(r)=>r.completed,Self::Scene(r)=>r.completed} }
    pub(super) fn source_matches(&self)->bool { match self {Self::Literal(r)=>r.source_matches,Self::Scene(r)=>r.source_matches} }
}
