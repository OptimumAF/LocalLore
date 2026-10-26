//! Closed native adapters; a version tag never replaces a validated Core plan.
use super::*;
use locallore_eval::local_lane::comparison::literal_v3::selected_v2 as literal;

#[derive(Clone, Copy, PartialEq, Eq)]
pub(super) enum Protocol {
    V1,
    V2,
}
impl Protocol {
    pub(super) fn from_source(value: u16) -> Option<Self> {
        match value {
            2 => Some(Self::V1),
            3 => Some(Self::V2),
            _ => None,
        }
    }
    pub(super) fn selected_version(self) -> u16 {
        match self {
            Self::V1 => 1,
            Self::V2 => 2,
        }
    }
    pub(super) fn source_version(self) -> u16 {
        match self {
            Self::V1 => 2,
            Self::V2 => 3,
        }
    }
}

pub(super) enum Plan {
    V1(producer::PreparedSelectedPlan),
    V2(literal::PreparedSelectedPlan),
}
impl Plan {
    pub(super) fn protocol(&self) -> Protocol {
        match self {
            Self::V1(_) => Protocol::V1,
            Self::V2(_) => Protocol::V2,
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
            Protocol::V1 => {
                producer::prepare_selected(source, binding, row, intent, cancel).map(Self::V1)
            }
            Protocol::V2 => {
                literal::prepare_selected(source, binding, row, intent, cancel).map(Self::V2)
            }
        }
    }
    pub(super) fn metadata(&self) -> Result<Value> {
        match self {
            Self::V1(plan) => producer::prepared_metadata(plan),
            Self::V2(plan) => literal::prepared_metadata(plan),
        }
    }
    pub(super) fn run(self, path: &Path, cancel: &Cancellation) -> Result<()> {
        match self {
            Self::V1(plan) => producer::run_selected(plan, path, cancel).map(|_| ()),
            Self::V2(plan) => literal::run_selected(plan, path, cancel).map(|_| ()),
        }
    }
    pub(super) fn run_native<R: producer::SelectedNativeReservation>(
        self,
        path: &Path,
        cancel: &Cancellation,
        reserve: impl FnOnce() -> Result<R>,
    ) -> std::result::Result<(), producer::SelectedNativeFailure<R>> {
        match self {
            Self::V1(plan) => {
                producer::run_native_selected(plan, path, cancel, reserve).map(|_| ())
            }
            Self::V2(plan) => literal::run_native_selected(plan, path, cancel, reserve).map(|_| ()),
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
        }
    }
    pub(super) fn resume_native<R: producer::SelectedNativeReservation>(
        protocol: Protocol,
        path: &Path,
        source: &Path,
        binding: &str,
        cancel: &Cancellation,
        reserve: impl FnOnce() -> Result<R>,
    ) -> std::result::Result<(), producer::SelectedNativeFailure<R>> {
        match protocol {
            Protocol::V1 => {
                producer::resume_native_selected(path, source, binding, cancel, reserve).map(|_| ())
            }
            Protocol::V2 => {
                literal::resume_native_selected(path, source, binding, cancel, reserve).map(|_| ())
            }
        }
    }
}

pub(super) enum Opened {
    V1(shared::OpenedSelected),
    V2(literal::desktop_read::OpenedSelected),
}
impl Opened {
    pub(super) fn open(protocol: Protocol, path: &Path) -> Result<Self> {
        match protocol {
            Protocol::V1 => shared::open_read_only(path).map(Self::V1),
            Protocol::V2 => literal::desktop_read::open_read_only(path).map(Self::V2),
        }
    }
    pub(super) fn summary(&self) -> Result<Value> {
        match self {
            Self::V1(opened) => shared::summary(opened, true),
            Self::V2(opened) => literal::desktop_read::summary(opened, true),
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
        }
    }
    pub(super) fn diagnostics(&self, binding: &str, observer: Observer) -> Result<Value> {
        match self {
            Self::V1(opened) => shared::diagnostics(opened, binding, observer, true),
            Self::V2(opened) => literal::desktop_read::diagnostics(opened, binding, observer, true),
        }
    }
}

pub(super) fn prepared_protocol(value: &Value) -> Option<Protocol> {
    match value["version"].as_u64()? {
        1 => Some(Protocol::V1),
        2 if value["source_protocol_version"] == 3 => Some(Protocol::V2),
        _ => None,
    }
}
