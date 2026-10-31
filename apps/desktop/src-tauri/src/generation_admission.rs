pub(crate) fn requires_generation_permit(input: &str) -> bool {
    matches!(
        serde_json::from_str::<locallore::host::Envelope>(input),
        Ok(locallore::host::Envelope {
            command: locallore::host::HostCommand::Prepare { .. }
                | locallore::host::HostCommand::AuthoringGenerate { .. },
            ..
        })
    )
}

pub(crate) fn dispatch<T>(
    lease: &crate::lease::WindowLease,
    epoch: u64,
    generation: bool,
    action: impl FnOnce() -> Result<T, String>,
) -> Result<T, String> {
    if generation {
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        action()
    } else {
        lease.dispatch(epoch, action)
    }
}
