//! Closed native adapters; a version tag never replaces a validated Core plan.
use super::*;
use locallore_eval::local_lane::comparison::literal_v3::selected_v2 as literal;
use locallore_eval::local_lane::comparison::scene_v4::selected_v3 as scene;
use locallore_eval::local_lane::comparison::scene_v4::selected_v4 as native_scene;

#[derive(Clone, Copy, PartialEq, Eq)]
pub(super) enum Protocol {
    V1,
    V2,
    V3,
    V4,
}
impl Protocol {
    pub(super) fn from_source(value: u16, lane: SelectedInputLane) -> Option<Self> {
        match (value, lane) {
            (2, _) => Some(Self::V1),
            (3, _) => Some(Self::V2),
            (4, SelectedInputLane::ScriptedBaseline) => Some(Self::V3),
            (4, SelectedInputLane::ApprovedNative) => Some(Self::V4),
            _ => None,
        }
    }
    pub(super) fn selected_version(self) -> u16 {
        match self {
            Self::V1 => 1,
            Self::V2 => 2,
            Self::V3 => 3,
            Self::V4 => 4,
        }
    }
    pub(super) fn source_version(self) -> u16 {
        match self {
            Self::V1 => 2,
            Self::V2 => 3,
            Self::V3 | Self::V4 => 4,
        }
    }
    pub(super) fn requires_source_binding(self) -> bool {
        matches!(self, Self::V3 | Self::V4)
    }
}

// Forward Core-owned cleanup failures. Scripted selected3 has no native route
// and cannot construct a Core ownership payload.
pub(super) enum NativeDispatchFailure<R> {
    Unavailable,
    Owned(producer::SelectedNativeFailure<R>),
}

pub(super) enum Plan {
    V1(Box<producer::PreparedSelectedPlan>),
    V2(Box<literal::PreparedSelectedPlan>),
    V3(Box<scene::PreparedSelectedPlan>),
    V4(Box<native_scene::PreparedSelectedPlan>),
}
impl Plan {
    pub(super) fn protocol(&self) -> Protocol {
        match self {
            Self::V1(_) => Protocol::V1,
            Self::V2(_) => Protocol::V2,
            Self::V3(_) => Protocol::V3,
            Self::V4(_) => Protocol::V4,
        }
    }
    pub(super) fn prepare(
        protocol: Protocol,
        source: &Path,
        binding: &str,
        row: &source_reader::RowId,
        intent: producer::SelectedIntent,
        cancel: &Cancellation,
    ) -> Result<Self> {
        match protocol {
            Protocol::V1 => producer::prepare_selected(source, binding, row, intent, cancel)
                .map(|plan| Self::V1(Box::new(plan))),
            Protocol::V2 => literal::prepare_selected(source, binding, row, intent, cancel)
                .map(|plan| Self::V2(Box::new(plan))),
            Protocol::V3 => scene::prepare_selected(source, binding, row, intent, cancel)
                .map(|plan| Self::V3(Box::new(plan))),
            Protocol::V4 => native_scene::prepare_selected(source, binding, row, intent, cancel)
                .map(|plan| Self::V4(Box::new(plan))),
        }
    }
    pub(super) fn metadata(&self) -> Result<Value> {
        match self {
            Self::V1(plan) => producer::prepared_metadata(plan),
            Self::V2(plan) => literal::prepared_metadata(plan),
            Self::V3(plan) => scene::prepared_metadata(plan),
            Self::V4(plan) => native_scene::prepared_metadata(plan),
        }
    }
    pub(super) fn run(self, path: &Path, cancel: &Cancellation) -> Result<()> {
        match self {
            Self::V1(plan) => producer::run_selected(*plan, path, cancel).map(|_| ()),
            Self::V2(plan) => literal::run_selected(*plan, path, cancel).map(|_| ()),
            Self::V3(plan) => scene::run_selected(*plan, path, cancel).map(|_| ()),
            Self::V4(_) => Err("SelectedLaneMismatch".into()),
        }
    }
    pub(super) fn run_native<R: producer::SelectedNativeReservation>(
        self,
        path: &Path,
        cancel: &Cancellation,
        reserve: impl FnOnce() -> Result<R>,
    ) -> std::result::Result<(), NativeDispatchFailure<R>> {
        match self {
            Self::V1(plan) => producer::run_native_selected(*plan, path, cancel, reserve)
                .map(|_| ())
                .map_err(NativeDispatchFailure::Owned),
            Self::V2(plan) => literal::run_native_selected(*plan, path, cancel, reserve)
                .map(|_| ())
                .map_err(NativeDispatchFailure::Owned),
            Self::V3(_) => Err(NativeDispatchFailure::Unavailable),
            Self::V4(plan) => native_scene::run_native_selected(*plan, path, cancel, reserve)
                .map(|_| ())
                .map_err(NativeDispatchFailure::Owned),
        }
    }
    pub(super) fn resume(
        protocol: Protocol,
        path: &Path,
        source: &Path,
        binding: &str,
        cancel: &Cancellation,
    ) -> Result<()> {
        match protocol {
            Protocol::V1 => producer::resume_selected(path, source, binding, cancel).map(|_| ()),
            Protocol::V2 => literal::resume_selected(path, source, binding, cancel).map(|_| ()),
            Protocol::V3 => scene::resume_selected(path, source, binding, cancel).map(|_| ()),
            Protocol::V4 => Err("SelectedLaneMismatch".into()),
        }
    }
    pub(super) fn resume_native<R: producer::SelectedNativeReservation>(
        protocol: Protocol,
        path: &Path,
        source: &Path,
        binding: &str,
        cancel: &Cancellation,
        reserve: impl FnOnce() -> Result<R>,
    ) -> std::result::Result<(), NativeDispatchFailure<R>> {
        match protocol {
            Protocol::V1 => {
                producer::resume_native_selected(path, source, binding, cancel, reserve)
                    .map(|_| ())
                    .map_err(NativeDispatchFailure::Owned)
            }
            Protocol::V2 => literal::resume_native_selected(path, source, binding, cancel, reserve)
                .map(|_| ())
                .map_err(NativeDispatchFailure::Owned),
            Protocol::V3 => Err(NativeDispatchFailure::Unavailable),
            Protocol::V4 => {
                native_scene::resume_native_selected(path, source, binding, cancel, reserve)
                    .map(|_| ())
                    .map_err(NativeDispatchFailure::Owned)
            }
        }
    }
}

pub(super) enum Opened {
    V1(Box<shared::OpenedSelected>),
    V2(Box<literal::desktop_read::OpenedSelected>),
    V3(Box<scene::desktop_read::OpenedSelected>),
    V4 {
        opened: Box<native_scene::desktop_read::OpenedSelected>,
        index: Box<Index>,
    },
}
impl Opened {
    pub(super) fn open(protocol: Protocol, path: &Path, index: &Index) -> Result<Self> {
        match protocol {
            Protocol::V1 => shared::open_read_only(path).map(|opened| Self::V1(Box::new(opened))),
            Protocol::V2 => {
                literal::desktop_read::open_read_only(path).map(|opened| Self::V2(Box::new(opened)))
            }
            Protocol::V3 => {
                scene::desktop_read::open_read_only(path).map(|opened| Self::V3(Box::new(opened)))
            }
            Protocol::V4 => native_scene::desktop_read::open_indexed_read_only(
                path,
                &index.client_id,
                &index.prepared,
            )
            .map(|opened| Self::V4 {
                opened: Box::new(opened),
                index: Box::new(index.clone()),
            }),
        }
    }
    pub(super) fn verify_resume_index(&self, current: &Index) -> Result<()> {
        // A renderer run token covers the snapshot originally opened. Check
        // that exact V4 index and the still-held read before re-preparing it.
        match self {
            Self::V4 { opened, index } if index.as_ref() == current => {
                native_scene::desktop_read::summary(opened, true).map(|_| ())
            }
            Self::V4 { .. } => Err("EvaluationSourceMismatch".into()),
            _ if current.version == Protocol::V4.selected_version() => {
                Err("EvaluationSourceMismatch".into())
            }
            _ => Ok(()),
        }
    }
    pub(super) fn summary(&self) -> Result<Value> {
        match self {
            Self::V1(opened) => shared::summary(opened, true),
            Self::V2(opened) => literal::desktop_read::summary(opened, true),
            Self::V3(opened) => scene::desktop_read::summary(opened, true),
            Self::V4 { opened, .. } => native_scene::desktop_read::summary(opened, true),
        }
    }
    pub(super) fn evidence(
        &self,
        binding: &str,
        arm: Arm,
        request: EvidenceRequest,
    ) -> Result<Value> {
        match self {
            Self::V1(opened) => shared::evidence(opened, binding, arm, request, true),
            Self::V2(opened) => {
                literal::desktop_read::evidence(opened, binding, arm, request, true)
            }
            Self::V3(opened) => scene::desktop_read::evidence(opened, binding, arm, request, true),
            Self::V4 { opened, .. } => {
                native_scene::desktop_read::evidence(opened, binding, arm, request, true)
            }
        }
    }
    pub(super) fn diagnostics(&self, binding: &str, observer: Observer) -> Result<Value> {
        match self {
            Self::V1(opened) => shared::diagnostics(opened, binding, observer, true),
            Self::V2(opened) => literal::desktop_read::diagnostics(opened, binding, observer, true),
            Self::V3(opened) => scene::desktop_read::diagnostics(opened, binding, observer, true),
            Self::V4 { opened, .. } => {
                native_scene::desktop_read::diagnostics(opened, binding, observer, true)
            }
        }
    }
}

pub(super) fn prepared_protocol(value: &Value) -> Option<Protocol> {
    match value["version"].as_u64()? {
        1 => Some(Protocol::V1),
        2 if value["source_protocol_version"] == 3 => Some(Protocol::V2),
        3 if value["source_protocol_version"] == 4 => Some(Protocol::V3),
        4 if value["source_protocol_version"] == 4
            && value["lane"] == SelectedInputLane::ApprovedNative.stored() =>
        {
            Some(Protocol::V4)
        }
        _ => None,
    }
}
