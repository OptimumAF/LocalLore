//! Closed native adapters; a version tag never replaces a validated Core plan.
use super::*;
use locallore_eval::local_lane::comparison::literal_v3::selected_v2 as literal;
use locallore_eval::local_lane::comparison::scene_v4::selected_v3 as scene;

#[derive(Clone, Copy, PartialEq, Eq)]
pub(super) enum Protocol {
    V1,
    V2,
    V3,
}
impl Protocol {
    pub(super) fn from_source(value: u16) -> Option<Self> {
        match value {
            2 => Some(Self::V1),
            3 => Some(Self::V2),
            4 => Some(Self::V3),
            _ => None,
        }
    }
    pub(super) fn selected_version(self) -> u16 {
        match self {
            Self::V1 => 1,
            Self::V2 => 2,
            Self::V3 => 3,
        }
    }
    pub(super) fn source_version(self) -> u16 {
        match self {
            Self::V1 => 2,
            Self::V2 => 3,
            Self::V3 => 4,
        }
    }
}

// This adapter carries legacy cleanup ownership without inventing a Core
// native selected3 route or constructing its private failure payload.
pub(super) enum NativeDispatchFailure<R> {
    Unavailable,
    Owned(producer::SelectedNativeFailure<R>),
}

pub(super) enum Plan {
    V1(Box<producer::PreparedSelectedPlan>),
    V2(Box<literal::PreparedSelectedPlan>),
    V3(Box<scene::PreparedSelectedPlan>),
}
impl Plan {
    pub(super) fn protocol(&self) -> Protocol {
        match self {
            Self::V1(_) => Protocol::V1,
            Self::V2(_) => Protocol::V2,
            Self::V3(_) => Protocol::V3,
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
        }
    }
    pub(super) fn metadata(&self) -> Result<Value> {
        match self {
            Self::V1(plan) => producer::prepared_metadata(plan),
            Self::V2(plan) => literal::prepared_metadata(plan),
            Self::V3(plan) => scene::prepared_metadata(plan),
        }
    }
    pub(super) fn run(self, path: &Path, cancel: &Cancellation) -> Result<()> {
        match self {
            Self::V1(plan) => producer::run_selected(*plan, path, cancel).map(|_| ()),
            Self::V2(plan) => literal::run_selected(*plan, path, cancel).map(|_| ()),
            Self::V3(plan) => scene::run_selected(*plan, path, cancel).map(|_| ()),
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
        }
    }
}

pub(super) enum Opened {
    V1(Box<shared::OpenedSelected>),
    V2(Box<literal::desktop_read::OpenedSelected>),
    V3(Box<scene::desktop_read::OpenedSelected>),
}
impl Opened {
    pub(super) fn open(protocol: Protocol, path: &Path) -> Result<Self> {
        match protocol {
            Protocol::V1 => shared::open_read_only(path).map(|opened| Self::V1(Box::new(opened))),
            Protocol::V2 => {
                literal::desktop_read::open_read_only(path).map(|opened| Self::V2(Box::new(opened)))
            }
            Protocol::V3 => {
                scene::desktop_read::open_read_only(path).map(|opened| Self::V3(Box::new(opened)))
            }
        }
    }
    pub(super) fn summary(&self) -> Result<Value> {
        match self {
            Self::V1(opened) => shared::summary(opened, true),
            Self::V2(opened) => literal::desktop_read::summary(opened, true),
            Self::V3(opened) => scene::desktop_read::summary(opened, true),
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
        }
    }
    pub(super) fn diagnostics(&self, binding: &str, observer: Observer) -> Result<Value> {
        match self {
            Self::V1(opened) => shared::diagnostics(opened, binding, observer, true),
            Self::V2(opened) => literal::desktop_read::diagnostics(opened, binding, observer, true),
            Self::V3(opened) => scene::desktop_read::diagnostics(opened, binding, observer, true),
        }
    }
}

pub(super) fn prepared_protocol(value: &Value) -> Option<Protocol> {
    match value["version"].as_u64()? {
        1 => Some(Protocol::V1),
        2 if value["source_protocol_version"] == 3 => Some(Protocol::V2),
        3 if value["source_protocol_version"] == 4 => Some(Protocol::V3),
        _ => None,
    }
}
