//! Typed native protocol selection over the one existing run lifecycle.
use super::*;
use crate::models::ModelManager;

impl EvaluationManager {
    pub(crate) fn full_comparison_catalog_native_for(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        protocol: FullComparisonProtocol,
    ) -> Result<Value> {
        if protocol == FullComparisonProtocol::LiteralV3 {
            return self.full_comparison_catalog_native(lease, epoch, granted);
        }
        self.full_catalog_lane(lease, epoch, granted, protocol.lane())
    }
    pub(crate) fn full_comparison_lookup_native_for(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        protocol: FullComparisonProtocol,
        client: &str,
    ) -> Result<Value> {
        if protocol == FullComparisonProtocol::LiteralV3 {
            return self.full_comparison_lookup_native(lease, epoch, granted, client);
        }
        self.full_lookup_lane(lease, epoch, granted, client, protocol.lane())
    }
    pub(crate) fn full_comparison_status_native_for(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        protocol: FullComparisonProtocol,
        token: &str,
    ) -> Result<Value> {
        if protocol == FullComparisonProtocol::LiteralV3 {
            return self.full_comparison_status_native(lease, epoch, granted, token);
        }
        self.full_status_lane(lease, epoch, granted, token, protocol.lane())
    }
    pub(crate) fn full_comparison_open_native_for(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        protocol: FullComparisonProtocol,
        run: &str,
    ) -> Result<Value> {
        if protocol == FullComparisonProtocol::LiteralV3 {
            return self.full_comparison_open_native(lease, epoch, granted, run);
        }
        self.full_open_lane(lease, epoch, granted, run, protocol.lane())
    }
    pub(crate) fn full_comparison_cancel_native_for(
        &self,
        lease: &WindowLease,
        epoch: u64,
        granted: bool,
        protocol: FullComparisonProtocol,
        token: &str,
        operation: u64,
    ) -> Result<Value> {
        if protocol == FullComparisonProtocol::LiteralV3 {
            return self.full_comparison_cancel_native(lease, epoch, granted, token, operation);
        }
        self.full_cancel_lane(lease, epoch, granted, token, operation, protocol.lane())
    }
    pub(crate) fn full_comparison_close_native_for(
        &self,
        lease: &WindowLease,
        epoch: u64,
        _granted: bool,
        protocol: FullComparisonProtocol,
        token: &str,
    ) -> Result<Value> {
        if protocol == FullComparisonProtocol::LiteralV3 {
            return self.full_comparison_close_native(lease, epoch, _granted, token);
        }
        self.full_close_lane(lease, epoch, token, protocol.lane())
    }
    // Preserve the existing explicit native arguments at this typed boundary.
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn full_comparison_pick_native_for(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        granted: bool,
        protocol: FullComparisonProtocol,
        client: &str,
        run: &str,
        consent: impl FnOnce() -> Result<bool> + Send + 'static,
    ) -> Result<Value> {
        if protocol == FullComparisonProtocol::LiteralV3 {
            return self.full_comparison_pick_native(lease, epoch, granted, client, run, consent);
        }
        self.full_pick_lane(
            lease,
            epoch,
            granted,
            (client, run),
            consent,
            protocol.lane(),
        )
    }
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn full_comparison_start_native_for(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        protocol: FullComparisonProtocol,
        input: FullComparisonStart,
        consent: impl FnOnce(&Value) -> Result<bool> + Send + 'static,
    ) -> Result<Value> {
        if protocol == FullComparisonProtocol::LiteralV3 {
            return self
                .full_comparison_start_native(lease, models, epoch, granted, input, consent);
        }
        let native = NativeExecution {
            models: models.clone(),
            consent: Box::new(consent),
        };
        let execution = match protocol {
            FullComparisonProtocol::LiteralV3 => Execution::Native(native),
            FullComparisonProtocol::SceneV4 => Execution::SceneNative(native),
        };
        self.full_start_execution(lease, epoch, granted, input, execution)
    }
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn full_comparison_resume_native_for(
        self: &Arc<Self>,
        lease: &Arc<WindowLease>,
        models: &Arc<ModelManager>,
        epoch: u64,
        granted: bool,
        protocol: FullComparisonProtocol,
        input: FullComparisonNativeResume,
        consent: impl FnOnce(&Value) -> Result<bool> + Send + 'static,
    ) -> Result<Value> {
        if protocol == FullComparisonProtocol::LiteralV3 {
            return self
                .full_comparison_resume_native(lease, models, epoch, granted, input, consent);
        }
        let native = NativeExecution {
            models: models.clone(),
            consent: Box::new(consent),
        };
        let execution = match protocol {
            FullComparisonProtocol::LiteralV3 => Execution::Native(native),
            FullComparisonProtocol::SceneV4 => Execution::SceneNative(native),
        };
        self.full_resume_execution(
            lease,
            epoch,
            granted,
            (&input.run_token, input.max_new_scenes),
            execution,
        )
    }
}
