//! Closed, model-free AppContainer feasibility qualifier. Never an app launcher.
//! SOURCE ONLY at handoff: no WebView/IPC/approved-worker/offline-app proof.
#[cfg(not(windows))]
fn main() {
    eprintln!("Unsupported");
    std::process::exit(1);
}
#[cfg(windows)]
fn main() {
    if let Err(error) = win::entry() {
        eprintln!("OfflineQualifierFailed:{error}");
        std::process::exit(1);
    }
}

#[cfg(windows)]
mod win {
    use serde_json::{json, Value};
    use sha2::{Digest, Sha256};
    use std::{
        fs::{self, File, OpenOptions},
        io::{Read, Seek, SeekFrom, Write},
        mem::{size_of, size_of_val},
        net::{Ipv4Addr, SocketAddr, SocketAddrV4, TcpListener, TcpStream, UdpSocket},
        os::windows::{
            ffi::OsStrExt,
            fs::{MetadataExt, OpenOptionsExt},
            io::{AsRawHandle, FromRawHandle},
        },
        path::{Component, Path, PathBuf, Prefix},
        sync::{
            atomic::{AtomicBool, Ordering},
            Arc, Mutex,
        },
        thread::{self, JoinHandle},
        time::{Duration, Instant},
    };
    use windows::{
        core::{PCWSTR, PWSTR},
        Win32::{
            Foundation::{
                CloseHandle, LocalFree, SetHandleInformation, HANDLE, HANDLE_FLAGS, HLOCAL,
                WAIT_OBJECT_0,
            },
            NetworkManagement::{
                IpHelper::{
                    GetAdaptersAddresses, GAA_FLAG_SKIP_ANYCAST, GAA_FLAG_SKIP_DNS_SERVER,
                    GAA_FLAG_SKIP_MULTICAST, IP_ADAPTER_ADDRESSES_LH,
                },
                Ndis::IfOperStatusUp,
            },
            Networking::WinSock::{AF_INET, SOCKADDR_IN},
            Security::{
                self,
                Authorization::{
                    ConvertSidToStringSidW, ConvertStringSecurityDescriptorToSecurityDescriptorW,
                    SDDL_REVISION_1, SE_FILE_OBJECT,
                },
                GetTokenInformation,
                Isolation::{
                    CreateAppContainerProfile, DeleteAppContainerProfile,
                    DeriveAppContainerSidFromAppContainerName,
                },
                TokenAppContainerSid, TokenCapabilities, TokenIntegrityLevel, TokenIsAppContainer,
                TokenRestrictedSids, TokenUser, DACL_SECURITY_INFORMATION,
                LABEL_SECURITY_INFORMATION, PROTECTED_DACL_SECURITY_INFORMATION,
                PSECURITY_DESCRIPTOR, PSID, SECURITY_ATTRIBUTES, SECURITY_CAPABILITIES,
                TOKEN_APPCONTAINER_INFORMATION, TOKEN_INFORMATION_CLASS, TOKEN_MANDATORY_LABEL,
                TOKEN_QUERY, TOKEN_USER,
            },
            System::{
                Com::CoCreateGuid,
                JobObjects::{
                    AssignProcessToJobObject, CreateJobObjectW,
                    JobObjectBasicAccountingInformation, JobObjectExtendedLimitInformation,
                    QueryInformationJobObject, SetInformationJobObject,
                    JOBOBJECT_BASIC_ACCOUNTING_INFORMATION, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
                    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
                },
                Pipes::CreatePipe,
                Threading::{
                    CreateProcessW, DeleteProcThreadAttributeList, GetCurrentProcess,
                    GetExitCodeProcess, InitializeProcThreadAttributeList, OpenProcessToken,
                    ResumeThread, TerminateProcess, UpdateProcThreadAttribute, WaitForSingleObject,
                    CREATE_NO_WINDOW, CREATE_SUSPENDED, EXTENDED_STARTUPINFO_PRESENT,
                    LPPROC_THREAD_ATTRIBUTE_LIST, PROCESS_INFORMATION,
                    PROC_THREAD_ATTRIBUTE_HANDLE_LIST, PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES,
                    STARTF_USESTDHANDLES, STARTUPINFOEXW,
                },
            },
        },
    };
    use windows::{
        Wdk::{
            Foundation::OBJECT_ATTRIBUTES,
            Storage::FileSystem::{
                NtCreateFile, FILE_CREATE, FILE_DIRECTORY_FILE, FILE_OPEN_REPARSE_POINT,
                FILE_SYNCHRONOUS_IO_NONALERT,
            },
        },
        Win32::{
            Foundation::{OBJ_CASE_INSENSITIVE, UNICODE_STRING},
            Security::Authorization::SetSecurityInfo,
            Storage::FileSystem::{
                GetFileInformationByHandle, BY_HANDLE_FILE_INFORMATION, FILE_ATTRIBUTE_NORMAL,
                FILE_GENERIC_READ, FILE_READ_ATTRIBUTES, FILE_SHARE_READ, FILE_TRAVERSE,
                SYNCHRONIZE, WRITE_DAC, WRITE_OWNER,
            },
            System::IO::IO_STATUS_BLOCK,
        },
    };

    type Result<T> = std::result::Result<T, String>;
    const CAP: usize = 8192;
    const CHILD_MS: u32 = 20_000;
    const IO_WAIT: Duration = Duration::from_secs(2);
    #[derive(Clone, Copy)]
    enum ChildMode {
        Canary,
        #[cfg(test)]
        LowFileReadProbe,
    }
    fn fail<T>(name: &str) -> Result<T> {
        Err(name.into())
    }
    fn io<T>(value: std::io::Result<T>) -> Result<T> {
        value.map_err(|e| format!("Io:{}", e.raw_os_error().unwrap_or(-1)))
    }
    fn api<T>(value: windows::core::Result<T>) -> Result<T> {
        value.map_err(|e| format!("Win32:{:08x}", e.code().0 as u32))
    }
    fn wide(value: impl AsRef<std::ffi::OsStr>) -> Vec<u16> {
        value.as_ref().encode_wide().chain(Some(0)).collect()
    }
    fn guid() -> Result<String> {
        Ok(format!("{:?}", api(unsafe { CoCreateGuid() })?)
            .trim_matches(['{', '}'])
            .to_lowercase())
    }
    fn valid_id(s: &str) -> bool {
        s.len() == 36
            && s.bytes().enumerate().all(|(i, b)| {
                if [8, 13, 18, 23].contains(&i) {
                    b == b'-'
                } else {
                    b.is_ascii_digit() || (b'a'..=b'f').contains(&b)
                }
            })
    }
    struct Handle(HANDLE);
    impl Drop for Handle {
        fn drop(&mut self) {
            unsafe {
                let _ = CloseHandle(self.0);
            }
        }
    }
    struct Sid(PSID);
    impl Drop for Sid {
        fn drop(&mut self) {
            unsafe {
                Security::FreeSid(self.0);
            }
        }
    }
    fn sid_text(sid: PSID) -> Result<String> {
        let mut text = PWSTR::null();
        api(unsafe { ConvertSidToStringSidW(sid, &mut text) })?;
        let value = unsafe { text.to_string() }.map_err(|_| "SidEncoding".to_owned());
        unsafe {
            LocalFree(Some(HLOCAL(text.0.cast())));
        }
        value
    }
    fn fixture_from_self(executable: &Path, id: &str) -> Result<PathBuf> {
        if !valid_id(id)
            || !executable.is_absolute()
            || executable
                .components()
                .any(|p| matches!(p, Component::ParentDir | Component::CurDir))
            || !matches!(executable.components().next(), Some(Component::Prefix(p)) if matches!(p.kind(), Prefix::Disk(_) | Prefix::VerbatimDisk(_)))
            || executable.file_name() != Some(std::ffi::OsStr::new("offline-qualifier.exe"))
        {
            return fail("CanaryFixtureBinding");
        }
        let fixture = executable.parent().ok_or("CanaryFixtureBinding")?;
        if fixture.file_name() != Some(std::ffi::OsStr::new(&format!("fixture-{id}"))) {
            return fail("CanaryFixtureBinding");
        }
        Ok(fixture.to_path_buf())
    }
    fn challenge_marker(id: &str, sid: &str, challenge: &str) -> Result<Vec<u8>> {
        encode(&json!({"version":1,"run_id":id,"package_sid":sid,"challenge":challenge}))
    }
    fn pin_directory(path: &Path) -> Result<Vec<File>> {
        if !path.is_absolute()
            || path
                .components()
                .any(|p| matches!(p, Component::ParentDir | Component::CurDir))
            || !matches!(path.components().next(), Some(Component::Prefix(p)) if matches!(p.kind(), Prefix::Disk(_) | Prefix::VerbatimDisk(_)))
        {
            return fail("LocalOrdinaryPathRequired");
        }
        let mut pins = vec![];
        let mut current = PathBuf::new();
        for component in path.components() {
            current.push(component.as_os_str());
            if matches!(component, Component::Prefix(_)) {
                continue;
            }
            let file = io(OpenOptions::new()
                .access_mode(FILE_READ_ATTRIBUTES.0 | FILE_TRAVERSE.0 | SYNCHRONIZE.0)
                .custom_flags(0x02000000 | 0x00200000)
                .share_mode(1)
                .open(&current))?;
            let metadata = io(file.metadata())?;
            if !metadata.is_dir() || metadata.file_attributes() & 0x400 != 0 {
                return fail("ReparseFixturePath");
            }
            pins.push(file); // No write/delete sharing: reparse mutation and replacement refuse.
        }
        if pins.is_empty() {
            return fail("PinnedParentMissing");
        }
        Ok(pins)
    }
    struct PinnedDirectory {
        path: PathBuf,
        file: File,
        _parents: Vec<File>,
    }
    fn create_owned_directory(parent: &Path, name: &str) -> Result<PinnedDirectory> {
        if !name
            .strip_prefix("fixture-")
            .or_else(|| name.strip_prefix("locallore-offline-proof-"))
            .is_some_and(valid_id)
        {
            return fail("GeneratedComponentRequired");
        }
        let parents = pin_directory(parent)?;
        let root = HANDLE(parents.last().ok_or("PinnedParentMissing")?.as_raw_handle());
        let mut name_wide = wide(name);
        let length =
            u16::try_from((name_wide.len() - 1) * 2).map_err(|_| "GeneratedComponentRequired")?;
        let text = UNICODE_STRING {
            Length: length,
            MaximumLength: length + 2,
            Buffer: PWSTR(name_wide.as_mut_ptr()),
        };
        let attributes = OBJECT_ATTRIBUTES {
            Length: size_of::<OBJECT_ATTRIBUTES>() as u32,
            RootDirectory: root,
            ObjectName: &text,
            Attributes: OBJ_CASE_INSENSITIVE,
            ..Default::default()
        };
        let mut status = IO_STATUS_BLOCK::default();
        let mut raw = HANDLE::default();
        let returned = unsafe {
            NtCreateFile(
                &mut raw,
                FILE_GENERIC_READ | WRITE_DAC | WRITE_OWNER | SYNCHRONIZE,
                &attributes,
                &mut status,
                None,
                FILE_ATTRIBUTE_NORMAL,
                FILE_SHARE_READ,
                FILE_CREATE,
                FILE_DIRECTORY_FILE | FILE_OPEN_REPARSE_POINT | FILE_SYNCHRONOUS_IO_NONALERT,
                None,
                0,
            )
        };
        // FILE_CREATED=2 is the documented IO_STATUS_BLOCK.Information result.
        // Even an informational/pending return is not adopted as owned creation.
        if returned.0 != 0
            || unsafe { status.Anonymous.Status }.0 != 0
            || status.Information != 2
            || raw.is_invalid()
        {
            if !raw.is_invalid() {
                unsafe {
                    let _ = CloseHandle(raw);
                }
            }
            return Err(format!("CreateOwnedDirectory:{:08x}", returned.0 as u32));
        }
        let file = into_file(Handle(raw));
        let metadata = io(file.metadata())?;
        if !metadata.is_dir() || metadata.file_attributes() & 0x400 != 0 {
            return fail("CreatedDirectoryIdentity");
        }
        Ok(PinnedDirectory {
            path: parent.join(name),
            file,
            _parents: parents,
        })
    }
    fn file_identity(file: &File) -> Result<(u32, u32, u32)> {
        let mut info = BY_HANDLE_FILE_INFORMATION::default();
        api(unsafe { GetFileInformationByHandle(HANDLE(file.as_raw_handle()), &mut info) })?;
        if info.dwFileAttributes & (0x400 | 0x10) != 0
            || info.nNumberOfLinks == 0
            || (info.nFileIndexHigh == 0 && info.nFileIndexLow == 0)
        {
            return fail("OrdinaryFileRequired");
        }
        Ok((
            info.dwVolumeSerialNumber,
            info.nFileIndexHigh,
            info.nFileIndexLow,
        ))
    }
    fn hash_image(file: &mut File) -> Result<String> {
        const MAX_IMAGE: u64 = 256 * 1024 * 1024;
        let expected = io(file.metadata())?.len();
        if expected == 0 || expected > MAX_IMAGE {
            return fail("SelfImageBudget");
        }
        io(file.seek(SeekFrom::Start(0)))?;
        let mut hash = Sha256::new();
        let mut total = 0u64;
        let mut bytes = [0u8; 65536];
        loop {
            let read = io(file.read(&mut bytes))?;
            if read == 0 {
                break;
            }
            total = total
                .checked_add(read as u64)
                .filter(|n| *n <= MAX_IMAGE)
                .ok_or("SelfImageBudget")?;
            hash.update(&bytes[..read]);
        }
        if total != expected {
            return fail("SelfImageChanged");
        }
        io(file.seek(SeekFrom::Start(0)))?;
        Ok(format!("{:x}", hash.finalize()))
    }
    struct PinnedExecutable {
        path: PathBuf,
        sha256: String,
        _pins: Vec<File>,
    }
    fn copy_self_to_new(root: &PinnedDirectory) -> Result<PinnedExecutable> {
        let source_path = io(std::env::current_exe())?;
        let mut pins = pin_directory(source_path.parent().ok_or("SelfImageParent")?)?;
        let mut source = io(OpenOptions::new()
            .read(true)
            .custom_flags(0x00200000)
            .share_mode(1)
            .open(&source_path))?;
        file_identity(&source)?;
        let expected = hash_image(&mut source)?;
        let path = root.path.join("offline-qualifier.exe");
        let mut writer = io(OpenOptions::new()
            .read(true)
            .write(true)
            .create_new(true)
            .custom_flags(0x00200000)
            .share_mode(3)
            .open(&path))?;
        let identity = file_identity(&writer)?;
        io(std::io::copy(&mut source, &mut writer))?;
        io(writer.sync_all())?;
        // Attribute-only guard preserves name/object identity without retaining
        // write access during the transition to a loader-compatible read pin.
        let guard = io(OpenOptions::new()
            .access_mode(FILE_READ_ATTRIBUTES.0)
            .custom_flags(0x00200000)
            .share_mode(3)
            .open(&path))?;
        if file_identity(&guard)? != identity {
            return fail("SelfImageIdentity");
        }
        drop(writer);
        let mut destination = io(OpenOptions::new()
            .read(true)
            .custom_flags(0x00200000)
            .share_mode(1)
            .open(&path))?;
        if file_identity(&destination)? != identity || hash_image(&mut destination)? != expected {
            return fail("SelfImageChanged");
        }
        pins.extend([source, guard, destination]);
        Ok(PinnedExecutable {
            path,
            sha256: expected,
            _pins: pins,
        })
    }
    fn token_buffer(
        token: HANDLE,
        class: TOKEN_INFORMATION_CLASS,
        minimum: usize,
    ) -> Result<Vec<usize>> {
        let mut bytes = 0;
        unsafe {
            let _ = GetTokenInformation(token, class, None, 0, &mut bytes);
        }
        if bytes == 0 || bytes as usize > CAP {
            return fail("TokenSize");
        }
        let mut data = vec![0usize; (bytes as usize).div_ceil(size_of::<usize>())];
        api(unsafe {
            GetTokenInformation(
                token,
                class,
                Some(data.as_mut_ptr().cast()),
                bytes,
                &mut bytes,
            )
        })?;
        if (bytes as usize) < minimum || bytes as usize > data.len() * size_of::<usize>() {
            return fail("MalformedTokenInformation");
        }
        Ok(data)
    }
    fn process_token(process: HANDLE) -> Result<Handle> {
        let mut token = HANDLE::default();
        api(unsafe { OpenProcessToken(process, TOKEN_QUERY, &mut token) })?;
        Ok(Handle(token))
    }
    fn token_observation(process: HANDLE) -> Result<Value> {
        let token = process_token(process)?;
        let boxed = token_buffer(token.0, TokenIsAppContainer, size_of::<u32>())?;
        let is_boxed = unsafe { *(boxed.as_ptr().cast::<u32>()) } != 0;
        // Only the fixed count is read: a zero-capability result need not include
        // TOKEN_GROUPS' placeholder one-element SID array.
        let capabilities = token_buffer(token.0, TokenCapabilities, size_of::<u32>())?;
        let count = unsafe { *(capabilities.as_ptr().cast::<u32>()) };
        let sid = if is_boxed {
            let data = token_buffer(
                token.0,
                TokenAppContainerSid,
                size_of::<TOKEN_APPCONTAINER_INFORMATION>(),
            )?;
            Some(sid_text(unsafe {
                (*(data.as_ptr().cast::<TOKEN_APPCONTAINER_INFORMATION>())).TokenAppContainer
            })?)
        } else {
            None
        };
        Ok(json!({"is_appcontainer":is_boxed,"capability_count":count,"package_sid":sid}))
    }
    fn current_user() -> Result<String> {
        let token = process_token(unsafe { GetCurrentProcess() })?;
        let user = token_buffer(token.0, TokenUser, size_of::<TOKEN_USER>())?;
        sid_text(unsafe { (*(user.as_ptr().cast::<TOKEN_USER>())).User.Sid })
    }
    fn token_diagnostic(process: HANDLE) -> Result<Value> {
        let token = process_token(process)?;
        let user = token_buffer(token.0, TokenUser, size_of::<TOKEN_USER>())?;
        let integrity = token_buffer(
            token.0,
            TokenIntegrityLevel,
            size_of::<TOKEN_MANDATORY_LABEL>(),
        )?;
        let restricted = token_buffer(token.0, TokenRestrictedSids, size_of::<u32>())?;
        Ok(json!({
            "user_sid":sid_text(unsafe { (*(user.as_ptr().cast::<TOKEN_USER>())).User.Sid })?,
            "integrity_sid":sid_text(unsafe { (*(integrity.as_ptr().cast::<TOKEN_MANDATORY_LABEL>())).Label.Sid })?,
            "restricted_sid_count":unsafe { *(restricted.as_ptr().cast::<u32>()) },
        }))
    }
    fn grant_new_fixture(root: &PinnedDirectory, package: PSID) -> Result<()> {
        // Only the private atomic-create constructor can supply this new object.
        let descriptor = wide(format!(
            "D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;{})(A;OICI;FA;;;{})S:(ML;OICI;NW;;;LW)",
            current_user()?,
            sid_text(package)?
        ));
        let mut security = PSECURITY_DESCRIPTOR::default();
        api(unsafe {
            ConvertStringSecurityDescriptorToSecurityDescriptorW(
                PCWSTR(descriptor.as_ptr()),
                SDDL_REVISION_1,
                &mut security,
                None,
            )
        })?;
        let result = (|| {
            let (mut present, mut defaulted) = (windows::core::BOOL(0), windows::core::BOOL(0));
            let (mut dacl, mut sacl) = (std::ptr::null_mut(), std::ptr::null_mut());
            api(unsafe {
                Security::GetSecurityDescriptorDacl(
                    security,
                    &mut present,
                    &mut dacl,
                    &mut defaulted,
                )
            })?;
            if !present.as_bool() {
                return fail("MissingFixtureDacl");
            }
            api(unsafe {
                Security::GetSecurityDescriptorSacl(
                    security,
                    &mut present,
                    &mut sacl,
                    &mut defaulted,
                )
            })?;
            if !present.as_bool() {
                return fail("MissingFixtureLabel");
            }
            api(unsafe {
                SetSecurityInfo(
                    HANDLE(root.file.as_raw_handle()),
                    SE_FILE_OBJECT,
                    DACL_SECURITY_INFORMATION
                        | LABEL_SECURITY_INFORMATION
                        | PROTECTED_DACL_SECURITY_INFORMATION,
                    None,
                    None,
                    Some(dacl),
                    Some(sacl),
                )
                .ok()
            })
        })();
        unsafe {
            LocalFree(Some(HLOCAL(security.0)));
        }
        result
    }
    fn write_new(path: &Path, bytes: &[u8]) -> Result<()> {
        if bytes.len() > CAP {
            return fail("EvidenceSize");
        }
        let mut file = io(OpenOptions::new()
            .write(true)
            .create_new(true)
            .custom_flags(0x00200000)
            .share_mode(1)
            .open(path))?;
        io(file.write_all(bytes))?;
        io(file.sync_all())
    }
    fn encode(value: &Value) -> Result<Vec<u8>> {
        serde_json::to_vec(value).map_err(|_| "Encoding".into())
    }
    fn read_small(path: &Path) -> Result<Vec<u8>> {
        let mut bytes = vec![];
        let file = io(OpenOptions::new()
            .read(true)
            .custom_flags(0x00200000)
            .share_mode(1)
            .open(path))
        .map_err(|e| format!("ReadSmallOpen:{e}"))?;
        file_identity(&file)?;
        io(file.take(CAP as u64 + 1).read_to_end(&mut bytes))
            .map_err(|e| format!("ReadSmallData:{e}"))?;
        if bytes.len() > CAP {
            return fail("FixtureReadBudget");
        }
        Ok(bytes)
    }
    fn own_address() -> Result<Ipv4Addr> {
        let flags = GAA_FLAG_SKIP_ANYCAST | GAA_FLAG_SKIP_MULTICAST | GAA_FLAG_SKIP_DNS_SERVER;
        let mut bytes = 0;
        unsafe {
            GetAdaptersAddresses(AF_INET.0 as u32, flags, None, None, &mut bytes);
        }
        if bytes == 0 || bytes > 1024 * 1024 {
            return fail("AdapterSize");
        }
        let mut data = vec![0usize; (bytes as usize).div_ceil(size_of::<usize>())];
        let head = data.as_mut_ptr().cast::<IP_ADAPTER_ADDRESSES_LH>();
        if unsafe { GetAdaptersAddresses(AF_INET.0 as u32, flags, None, Some(head), &mut bytes) }
            != 0
        {
            return fail("AdaptersUnavailable");
        }
        let mut addresses = vec![];
        let mut adapter = head;
        let mut traversed = 0;
        while !adapter.is_null() {
            traversed += 1;
            if traversed > 128 {
                return fail("AdapterCount");
            }
            let a = unsafe { &*adapter };
            if a.OperStatus == IfOperStatusUp && a.IfType != 24 {
                let mut unicast = a.FirstUnicastAddress;
                let mut n = 0;
                while !unicast.is_null() {
                    n += 1;
                    if n > 128 {
                        return fail("AddressCount");
                    }
                    let u = unsafe { &*unicast };
                    if !u.Address.lpSockaddr.is_null()
                        && u.Address.iSockaddrLength as usize >= size_of::<SOCKADDR_IN>()
                    {
                        let s = unsafe { &*u.Address.lpSockaddr.cast::<SOCKADDR_IN>() };
                        if s.sin_family == AF_INET {
                            let ip =
                                Ipv4Addr::from(unsafe { s.sin_addr.S_un.S_addr }.to_ne_bytes());
                            if !ip.is_loopback()
                                && !ip.is_unspecified()
                                && !ip.is_multicast()
                                && ip != Ipv4Addr::BROADCAST
                            {
                                addresses.push(ip);
                            }
                        }
                    }
                    unicast = u.Next;
                }
            }
            adapter = a.Next;
        }
        addresses.sort();
        addresses.dedup();
        addresses
            .first()
            .copied()
            .ok_or("OwnNonloopbackIpv4Unavailable".into())
    }
    struct Listeners {
        tcp: SocketAddr,
        udp: SocketAddr,
        stop: Arc<AtomicBool>,
        seen: Arc<Mutex<Vec<String>>>,
        threads: Vec<JoinHandle<()>>,
    }
    impl Listeners {
        fn start(nonce: &str) -> Result<Self> {
            let ip = own_address()?;
            let tcp = io(TcpListener::bind((ip, 0)))?;
            let udp = io(UdpSocket::bind((ip, 0)))?;
            io(tcp.set_nonblocking(true))?;
            io(udp.set_read_timeout(Some(Duration::from_millis(100))))?;
            let mut this = Self {
                tcp: io(tcp.local_addr())?,
                udp: io(udp.local_addr())?,
                stop: Arc::new(AtomicBool::new(false)),
                seen: Arc::new(Mutex::new(vec![])),
                threads: vec![],
            };
            let stop = this.stop.clone();
            let seen = this.seen.clone();
            let nonce = nonce.to_owned();
            let udp_nonce = nonce.clone();
            this.threads.push(
                thread::Builder::new()
                    .name("offline-tcp-canary".into())
                    .spawn(move || {
                        while !stop.load(Ordering::SeqCst) {
                            match tcp.accept() {
                                Ok((mut socket, _)) => {
                                    if socket.set_read_timeout(Some(IO_WAIT)).is_err()
                                        || socket.set_write_timeout(Some(IO_WAIT)).is_err()
                                    {
                                        break;
                                    }
                                    let mut message = [0u8; 37];
                                    if socket.read_exact(&mut message).is_ok() {
                                        let text = String::from_utf8_lossy(&message);
                                        if text == format!("{nonce}B")
                                            || text == format!("{nonce}X")
                                        {
                                            if let Ok(mut records) = seen.lock() {
                                                if records.len() < 16 {
                                                    records.push(format!("tcp:{}", &text[36..]));
                                                }
                                            }
                                            let _ = socket.write_all(b"ok\n");
                                        }
                                    }
                                }
                                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                                    thread::sleep(Duration::from_millis(10))
                                }
                                Err(_) => break,
                            }
                        }
                    })
                    .map_err(|_| "TcpListenerThreadUnavailable")?,
            );
            let stop = this.stop.clone();
            let seen = this.seen.clone();
            let udp_thread = thread::Builder::new()
                .name("offline-udp-canary".into())
                .spawn(move || {
                    while !stop.load(Ordering::SeqCst) {
                        let mut message = [0u8; 96];
                        match udp.recv_from(&mut message) {
                            Ok((37, from)) => {
                                let text = String::from_utf8_lossy(&message[..37]);
                                if text == format!("{udp_nonce}B")
                                    || text == format!("{udp_nonce}X")
                                {
                                    if let Ok(mut records) = seen.lock() {
                                        if records.len() < 16 {
                                            records.push(format!("udp:{}", &text[36..]));
                                        }
                                    }
                                    let _ = udp.send_to(b"ok\n", from);
                                }
                            }
                            Err(e)
                                if matches!(
                                    e.kind(),
                                    std::io::ErrorKind::WouldBlock | std::io::ErrorKind::TimedOut
                                ) => {}
                            Ok(_) => {}
                            Err(_) => break,
                        }
                    }
                });
            match udp_thread {
                Ok(worker) => this.threads.push(worker),
                Err(_) => {
                    this.stop.store(true, Ordering::SeqCst);
                    for worker in this.threads {
                        let _ = worker.join();
                    }
                    return fail("UdpListenerThreadUnavailable");
                }
            }
            Ok(this)
        }
        fn finish(mut self) -> Result<Vec<String>> {
            self.stop.store(true, Ordering::SeqCst);
            let mut panicked = false;
            for thread in self.threads.drain(..) {
                panicked |= thread.join().is_err();
            }
            if panicked {
                return fail("ListenerThreadPanic");
            }
            self.seen
                .lock()
                .map(|v| v.clone())
                .map_err(|_| "ListenerPoison".into())
        }
    }

    struct Attributes {
        storage: Vec<usize>,
        list: LPPROC_THREAD_ATTRIBUTE_LIST,
    }
    impl Attributes {
        fn new(count: u32) -> Result<Self> {
            let mut bytes = 0;
            unsafe {
                let _ = InitializeProcThreadAttributeList(None, count, Some(0), &mut bytes);
            }
            if bytes == 0 || bytes > CAP {
                return fail("AttributeSize");
            }
            let mut storage = vec![0usize; bytes.div_ceil(size_of::<usize>())];
            let list = LPPROC_THREAD_ATTRIBUTE_LIST(storage.as_mut_ptr().cast());
            api(unsafe {
                InitializeProcThreadAttributeList(Some(list), count, Some(0), &mut bytes)
            })?;
            Ok(Self { storage, list })
        }
        fn set<T>(&mut self, key: u32, value: &T) -> Result<()> {
            let _keep_alive = &self.storage;
            api(unsafe {
                UpdateProcThreadAttribute(
                    self.list,
                    0,
                    key as usize,
                    Some((value as *const T).cast()),
                    size_of_val(value),
                    None,
                    None,
                )
            })
        }
    }
    impl Drop for Attributes {
        fn drop(&mut self) {
            unsafe {
                DeleteProcThreadAttributeList(self.list);
            }
        }
    }
    fn pipe() -> Result<(Handle, Handle)> {
        let mut read = HANDLE::default();
        let mut write = HANDLE::default();
        let security = SECURITY_ATTRIBUTES {
            nLength: size_of::<SECURITY_ATTRIBUTES>() as u32,
            lpSecurityDescriptor: std::ptr::null_mut(),
            bInheritHandle: true.into(),
        };
        api(unsafe { CreatePipe(&mut read, &mut write, Some(&security), CAP as u32) })?;
        Ok((Handle(read), Handle(write)))
    }
    fn into_file(handle: Handle) -> File {
        let raw = handle.0 .0;
        std::mem::forget(handle);
        unsafe { File::from_raw_handle(raw) }
    }
    fn reader(file: File) -> Result<JoinHandle<std::io::Result<Vec<u8>>>> {
        thread::Builder::new()
            .name("offline-canary-pipe".into())
            .spawn(move || {
                let mut bytes = vec![];
                file.take(CAP as u64 + 1).read_to_end(&mut bytes)?;
                Ok(bytes)
            })
            .map_err(|_| "PipeReaderThreadUnavailable".into())
    }
    fn reader_ready<T>(worker: &JoinHandle<T>, deadline: Instant) -> bool {
        while !worker.is_finished() {
            let remaining = deadline.saturating_duration_since(Instant::now());
            if remaining.is_zero() {
                return false;
            }
            thread::sleep(remaining.min(Duration::from_millis(10)));
        }
        true
    }
    fn run_child(
        executable: &Path,
        package: Option<PSID>,
        request: &Value,
        evidence: &Path,
        label: &str,
    ) -> Value {
        run_child_fixed(executable, package, request, evidence, label, ChildMode::Canary)
    }
    fn run_child_fixed(
        executable: &Path,
        package: Option<PSID>,
        request: &Value,
        evidence: &Path,
        label: &str,
        mode: ChildMode,
    ) -> Value {
        let mut record = json!({"case":label,"phase":"prepare","passed":false,"child_created":false,"cleanup_known":true,"threads_drained":true});
        #[cfg(test)]
        if matches!(mode, ChildMode::LowFileReadProbe) {
            record["child_mode"] = json!("unit-test-low-file-read-probe");
        }
        let mut process: Option<Handle> = None;
        let mut main_thread: Option<Handle> = None;
        let mut job: Option<Handle> = None;
        let mut output = None;
        let mut errors = None;
        let result: Result<Value> = (|| {
            let j = Handle(api(unsafe { CreateJobObjectW(None, PCWSTR::null()) })?);
            let mut limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION::default();
            limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            api(unsafe {
                SetInformationJobObject(
                    j.0,
                    JobObjectExtendedLimitInformation,
                    (&limits as *const JOBOBJECT_EXTENDED_LIMIT_INFORMATION).cast(),
                    size_of_val(&limits) as u32,
                )
            })?;
            job = Some(j);
            let (child_in, parent_in) = pipe()?;
            let (parent_out, child_out) = pipe()?;
            let (parent_err, child_err) = pipe()?;
            for handle in [&parent_in, &parent_out, &parent_err] {
                api(unsafe { SetHandleInformation(handle.0, 1, HANDLE_FLAGS(0)) })?;
            }
            let inherited = [child_in.0, child_out.0, child_err.0];
            let mut attributes = Attributes::new(if package.is_some() { 2 } else { 1 })?;
            attributes.set(PROC_THREAD_ATTRIBUTE_HANDLE_LIST, &inherited)?;
            let capabilities = SECURITY_CAPABILITIES {
                AppContainerSid: package.unwrap_or_default(),
                Capabilities: std::ptr::null_mut(),
                CapabilityCount: 0,
                Reserved: 0,
            };
            if package.is_some() {
                attributes.set(PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES, &capabilities)?;
            }
            let mut startup = STARTUPINFOEXW::default();
            startup.StartupInfo.cb = size_of::<STARTUPINFOEXW>() as u32;
            startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES;
            startup.StartupInfo.hStdInput = child_in.0;
            startup.StartupInfo.hStdOutput = child_out.0;
            startup.StartupInfo.hStdError = child_err.0;
            startup.lpAttributeList = attributes.list;
            let name = wide(executable);
            let mut command = wide(match mode {
                ChildMode::Canary => format!("\"{}\" --self-canary", executable.display()),
                #[cfg(test)]
                ChildMode::LowFileReadProbe => format!("\"{}\" --exact win::tests::low_integrity_file_probe_child --ignored --nocapture --test-threads=1", executable.display()),
            });
            let cwd = wide(executable.parent().ok_or("FixtureParent")?);
            let mut info = PROCESS_INFORMATION::default();
            record["phase"] = json!("create_suspended");
            api(unsafe {
                CreateProcessW(
                    PCWSTR(name.as_ptr()),
                    Some(PWSTR(command.as_mut_ptr())),
                    None,
                    None,
                    true,
                    CREATE_SUSPENDED | CREATE_NO_WINDOW | EXTENDED_STARTUPINFO_PRESENT,
                    None,
                    PCWSTR(cwd.as_ptr()),
                    &startup.StartupInfo,
                    &mut info,
                )
            })?;
            process = Some(Handle(info.hProcess));
            main_thread = Some(Handle(info.hThread));
            record["child_created"] = json!(true);
            record["pid"] = json!(info.dwProcessId);
            record["cleanup_known"] = json!(false);
            record["phase"] = json!("assign_job");
            // Establish ownership immediately, even if assignment/token checks fail.
            api(unsafe {
                AssignProcessToJobObject(job.as_ref().ok_or("JobMissing")?.0, info.hProcess)
            })?;
            record["phase"] = json!("verify_suspended_token");
            let observed = token_observation(info.hProcess)?;
            record["parent_token"] = observed.clone();
            record["child_token_diagnostic"] = token_diagnostic(info.hProcess)?;
            record["qualifier_token_diagnostic"] =
                token_diagnostic(unsafe { GetCurrentProcess() })?;
            if observed["is_appcontainer"] != package.is_some() || observed["capability_count"] != 0
            {
                return fail("ActualChildTokenMismatch");
            }
            if let Some(sid) = package {
                if observed["package_sid"] != sid_text(sid)? {
                    return fail("ActualPackageSidMismatch");
                }
            }
            drop(child_in);
            drop(child_out);
            drop(child_err);
            output = Some(reader(into_file(parent_out))?);
            errors = Some(reader(into_file(parent_err))?);
            let mut input = into_file(parent_in);
            record["phase"] = json!("run_canary");
            if unsafe { ResumeThread(info.hThread) } == u32::MAX {
                return fail("ResumeFailed");
            }
            let bytes = encode(request)?;
            if bytes.len() > 4096 {
                return fail("RequestBudget");
            }
            io(input.write_all(&bytes))?;
            drop(input);
            if unsafe { WaitForSingleObject(info.hProcess, CHILD_MS) } != WAIT_OBJECT_0 {
                return fail("CanaryDeadlineOrWaitFailure");
            }
            let mut exit = 0;
            api(unsafe { GetExitCodeProcess(info.hProcess, &mut exit) })?;
            record["exit"] = json!(exit);
            if exit != 0 {
                return fail("CanaryExit");
            }
            Ok(observed)
        })();
        // Always positively terminate/reap before interpreting child assertions.
        // One original five-second budget covers process, Job and pipe drain.
        let cleanup_deadline = Instant::now() + Duration::from_secs(5);
        let mut known = true;
        if let Some(p) = &process {
            if unsafe { WaitForSingleObject(p.0, 0) } != WAIT_OBJECT_0 {
                unsafe {
                    let _ = TerminateProcess(p.0, 1);
                }
            }
            let remaining = cleanup_deadline.saturating_duration_since(Instant::now());
            known = unsafe { WaitForSingleObject(p.0, remaining.as_millis().min(5000) as u32) }
                == WAIT_OBJECT_0;
            record["process_reaped"] = json!(known);
        }
        if let Some(j) = &job {
            let mut observations = 0u32;
            loop {
                let mut count = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION::default();
                let observed = unsafe {
                    QueryInformationJobObject(
                        Some(j.0),
                        JobObjectBasicAccountingInformation,
                        (&mut count as *mut JOBOBJECT_BASIC_ACCOUNTING_INFORMATION).cast(),
                        size_of_val(&count) as u32,
                        None,
                    )
                };
                observations += 1;
                record["job_observations"] = json!(observations);
                match observed {
                    Err(error) => {
                        record["job_query_hresult"] = json!(error.code().0);
                        known = false;
                        break;
                    }
                    Ok(()) => record["job_active_processes"] = json!(count.ActiveProcesses),
                }
                if count.ActiveProcesses == 0 {
                    break;
                }
                let remaining = cleanup_deadline.saturating_duration_since(Instant::now());
                if remaining.is_zero() {
                    known = false;
                    break;
                }
                thread::sleep(remaining.min(Duration::from_millis(10)));
            }
        }
        record["cleanup_known"] = json!(known);
        drop(main_thread);
        drop(process);
        drop(job); // Job also kills on last close.
        let mut child_reply = None;
        for (stream, thread) in [("stdout", output), ("stderr", errors)] {
            if let Some(thread) = thread {
                // Diagnostic capture remains valuable when Job drain is unknown.
                // Never turn that capture into cleanup authority or block join
                // beyond the same finite cleanup observation budget.
                if !reader_ready(&thread, cleanup_deadline) {
                    record["threads_drained"] = json!(false);
                    std::mem::forget(thread);
                    continue;
                }
                match thread.join() {
                    Ok(Ok(bytes)) => {
                        if write_new(
                            &evidence.join(format!("{label}.{stream}.bin")),
                            &bytes[..bytes.len().min(CAP)],
                        )
                        .is_err()
                        {
                            record["capture_error"] = json!(true);
                        }
                        if bytes.len() > CAP {
                            record["capture_error"] = json!(true);
                            record["capture_truncated"] = json!(true);
                        } else if stream == "stdout" {
                            child_reply = match mode {
                                ChildMode::Canary => serde_json::from_slice::<Value>(&bytes).ok(),
                                #[cfg(test)]
                                ChildMode::LowFileReadProbe => decode_low_file_probe_reply(&bytes).ok(),
                            };
                        } else if !bytes.is_empty() {
                            record["unexpected_stderr"] = json!(true);
                        }
                    }
                    _ => record["threads_drained"] = json!(false),
                }
            }
        }
        if let Err(error) = &result {
            record["error"] = json!(error);
        }
        if let Some(reply) = child_reply {
            let coherent = match mode {
                ChildMode::Canary => result
                .as_ref()
                .is_ok_and(|parent| reply["token"] == *parent)
                && reply["version"] == 1
                && reply["kind"] == "offline_self_canary"
                && reply["case"] == label
                && reply["challenge"] == request["challenge"]
                && reply["file_roundtrip"] == true
                && reply["passed"] == true,
                #[cfg(test)]
                ChildMode::LowFileReadProbe => result.as_ref().is_ok_and(|parent| reply["token"] == *parent)
                    && reply["version"] == 1 && reply["kind"] == "low_file_read_probe"
                    && reply["case"] == label && reply["run_id"] == request["run_id"]
                    && reply["challenge"] == request["challenge"]
                    && reply["measurement_complete"] == true && reply["passed"] == true,
            };
            record["reply"] = reply;
            record["passed"] = json!(
                coherent
                    && known
                    && record["threads_drained"] == true
                    && record.get("capture_error").is_none()
                    && record.get("unexpected_stderr").is_none()
            );
            if record["passed"] == true {
                record["phase"] = json!("complete");
            }
        }
        record
    }

    fn canary() -> Result<()> {
        let mut bytes = vec![];
        io(std::io::stdin().take(4097).read_to_end(&mut bytes))
            .map_err(|e| format!("CanaryStdin:{e}"))?;
        if bytes.len() > 4096 {
            return fail("CanaryInputBudget");
        }
        let request: Value = serde_json::from_slice(&bytes).map_err(|_| "CanaryInputEncoding")?;
        let keys = ["version", "run_id", "case", "challenge", "tcp", "udp"];
        let object = request.as_object().ok_or("CanaryInputShape")?;
        if object.len() != keys.len()
            || object.keys().any(|k| !keys.contains(&k.as_str()))
            || request["version"] != 1
        {
            return fail("CanaryInputShape");
        }
        let id = request["run_id"]
            .as_str()
            .filter(|s| valid_id(s))
            .ok_or("CanaryIdentity")?;
        let challenge = request["challenge"]
            .as_str()
            .filter(|s| valid_id(s))
            .ok_or("CanaryChallenge")?;
        let label = request["case"]
            .as_str()
            .filter(|s| ["baseline", "boxed"].contains(s))
            .ok_or("CanaryCase")?;
        let profile = wide(format!("locallore.offline.{id}"));
        let sid = Sid(api(unsafe {
            DeriveAppContainerSidFromAppContainerName(PCWSTR(profile.as_ptr()))
        })
        .map_err(|e| format!("CanarySid:{e}"))?);
        let fixture = fixture_from_self(
            &io(std::env::current_exe()).map_err(|e| format!("CanarySelfImage:{e}"))?,
            id,
        )?;
        // Parent checked every ancestor before creation/launch. The restricted
        // child only needs access to its own new fixture, not ancestor listing.
        let metadata =
            io(fs::symlink_metadata(&fixture)).map_err(|e| format!("CanaryFixtureMetadata:{e}"))?;
        if !metadata.is_dir() || metadata.file_attributes() & 0x400 != 0 {
            return fail("ReparseFixturePath");
        }
        if read_small(&fixture.join("challenge.txt")).map_err(|e| {
            format!(
                "CanaryMarkerRead:{e}:ChildToken:{}",
                token_diagnostic(unsafe { GetCurrentProcess() })
                    .unwrap_or_else(|diagnostic| json!({"diagnostic_error":diagnostic}))
            )
        })? != challenge_marker(id, &sid_text(sid.0)?, challenge)?
        {
            return fail("CanaryFixtureBinding");
        }
        let token = token_observation(unsafe { GetCurrentProcess() })
            .map_err(|e| format!("CanaryToken:{e}"))?;
        if token["is_appcontainer"] != (label == "boxed")
            || token["capability_count"] != 0
            || (label == "boxed" && token["package_sid"] != sid_text(sid.0)?)
        {
            return fail("CanaryActualToken");
        }
        let marker = format!("{challenge}{}", if label == "baseline" { "B" } else { "X" });
        let file = fixture.join(format!("{label}.txt"));
        write_new(&file, marker.as_bytes()).map_err(|e| format!("CanaryFileCreate:{e}"))?;
        let file_ok =
            read_small(&file).map_err(|e| format!("CanaryFileRead:{e}"))? == marker.as_bytes();
        let host_ip = own_address().map_err(|e| format!("CanaryAdapters:{e}"))?;
        let address = |key: &str| -> Result<SocketAddr> {
            let addr: SocketAddrV4 = request[key]
                .as_str()
                .ok_or("EndpointType")?
                .parse()
                .map_err(|_| "EndpointEncoding")?;
            if *addr.ip() != host_ip
                || addr.ip().is_loopback()
                || addr.ip().is_unspecified()
                || addr.ip().is_multicast()
                || addr.port() == 0
            {
                return fail("OwnedNonloopbackEndpointRequired");
            }
            Ok(addr.into())
        };
        let tcp = match TcpStream::connect_timeout(&address("tcp")?, IO_WAIT) {
            Ok(mut socket) => {
                io(socket.set_read_timeout(Some(IO_WAIT)))?;
                io(socket.set_write_timeout(Some(IO_WAIT)))?;
                io(socket.write_all(marker.as_bytes()))?;
                let mut ack = [0; 3];
                io(socket.read_exact(&mut ack))?;
                json!({"success":ack==*b"ok\n","stage":"connect","os_error":null})
            }
            Err(e) => json!({"success":false,"stage":"connect","os_error":e.raw_os_error()}),
        };
        let udp = match UdpSocket::bind((Ipv4Addr::UNSPECIFIED, 0)) {
            Err(e) => json!({"success":false,"stage":"bind","os_error":e.raw_os_error()}),
            Ok(socket) => {
                io(socket.set_read_timeout(Some(IO_WAIT)))?;
                match socket.send_to(marker.as_bytes(), address("udp")?) {
                    Err(e) => json!({"success":false,"stage":"send","os_error":e.raw_os_error()}),
                    Ok(_) => {
                        let mut ack = [0; 3];
                        let received = socket.recv_from(&mut ack);
                        let expected = address("udp")?;
                        let success = received
                            .as_ref()
                            .is_ok_and(|(n, peer)| *n == 3 && *peer == expected)
                            && ack == *b"ok\n";
                        json!({"success":success,"stage":"send","os_error":received.err().and_then(|e|e.raw_os_error())})
                    }
                }
            }
        };
        let passed = file_ok
            && if label == "baseline" {
                tcp["success"] == true && udp["success"] == true
            } else {
                tcp["os_error"] == 10013
                    && tcp["stage"] == "connect"
                    && udp["os_error"] == 10013
                    && udp["stage"] == "send"
            };
        let response = json!({"version":1,"kind":"offline_self_canary","case":label,"challenge":challenge,"token":token,"file_roundtrip":file_ok,"tcp":tcp,"udp":udp,"passed":passed});
        io(std::io::stdout().write_all(&encode(&response)?))?;
        // Failed assertions remain in stdout; parent captures before evaluating.
        Ok(())
    }

    fn profile_delete_allowed(proof: &Value) -> bool {
        proof["profile_created"] == true
            && proof["child_cleanup_known"] == true
            && proof["listener_threads_drained"] == true
            && ["baseline", "boxed"].into_iter().all(|case| {
                proof.get(case).is_none_or(|child| {
                    child["cleanup_known"] == true && child["threads_drained"] == true
                })
            })
    }
    pub fn entry() -> Result<()> {
        let args: Vec<_> = std::env::args_os().skip(1).collect();
        if args.len() == 1 && args[0] == "--self-canary" {
            return canary();
        }
        if !args.is_empty() {
            return fail("ClosedArgumentsRequired");
        }
        let id = guid()?;
        let challenge = guid()?;
        let temporary = std::env::temp_dir();
        let evidence =
            create_owned_directory(&temporary, &format!("locallore-offline-proof-{id}"))?;
        eprintln!(
            "LOCALLORE_OFFLINE_FEASIBILITY_ARTIFACT={}",
            evidence.path.display()
        );
        let mut proof = json!({"version":1,"kind":"appcontainer_feasibility","phase":"profile_create","passed":false,"run_id":id,"profile_created":false,"profile_delete_api_succeeded":false,"profile_storage_absence_checked":false,"child_cleanup_known":true,"listener_threads_drained":true,"webview_executed":false,"native_ipc_executed":false,"approved_worker_executed":false,"model_executed":false,"ipv6_tested":false,"dns_tested":false});
        let name = wide(format!("locallore.offline.{id}"));
        let mut sid = None;
        let mut listeners = None;
        let mut fixture = None;
        let mut executable_pins = vec![];
        let result: Result<()> = (|| {
            // Never derive/adopt on AlreadyExists. Only this success owns deletion.
            let package = Sid(api(unsafe {
                CreateAppContainerProfile(
                    PCWSTR(name.as_ptr()),
                    PCWSTR(name.as_ptr()),
                    PCWSTR(name.as_ptr()),
                    None,
                )
            })?);
            proof["profile_created"] = json!(true);
            sid = Some(package);
            let package = sid.as_ref().ok_or("ProfileMissing")?.0;
            proof["package_sid"] = json!(sid_text(package)?);
            proof["phase"] = json!("fixture_prepare");
            // This sibling of evidence is unrelated to managed profile storage.
            // Retain its identity pins through deletion; never open the latter.
            fixture = Some(create_owned_directory(
                &temporary,
                &format!("fixture-{id}"),
            )?);
            let root = fixture.as_ref().ok_or("FixtureMissing")?;
            grant_new_fixture(root, package)?;
            executable_pins.push(copy_self_to_new(root)?);
            let executable = executable_pins.last().ok_or("SelfImageMissing")?;
            proof["copied_self_sha256"] = json!(executable.sha256);
            write_new(
                &root.path.join("challenge.txt"),
                &challenge_marker(&id, &sid_text(package)?, &challenge)?,
            )?;
            if read_small(&root.path.join("challenge.txt"))?
                != challenge_marker(&id, &sid_text(package)?, &challenge)?
            {
                return fail("ParentChallengeReadback");
            }
            proof["parent_challenge_readback"] = json!(true);
            proof["phase"] = json!("listener_prepare");
            listeners = Some(Listeners::start(&challenge)?);
            let server = listeners.as_ref().ok_or("ListenersMissing")?;
            let request = |label: &str| json!({"version":1,"run_id":id,"case":label,"challenge":challenge,"tcp":server.tcp.to_string(),"udp":server.udp.to_string()});
            proof["phase"] = json!("baseline");
            let baseline = run_child(
                &executable.path,
                None,
                &request("baseline"),
                &evidence.path,
                "baseline",
            );
            proof["child_cleanup_known"] = baseline["cleanup_known"].clone();
            proof["baseline"] = baseline;
            if proof["baseline"]["passed"] != true {
                return fail("PositiveControlFailed");
            }
            proof["phase"] = json!("boxed");
            let boxed = run_child(
                &executable.path,
                Some(package),
                &request("boxed"),
                &evidence.path,
                "boxed",
            );
            proof["child_cleanup_known"] = boxed["cleanup_known"].clone();
            proof["boxed"] = boxed;
            if proof["boxed"]["passed"] != true {
                return fail("ExplicitNetworkDenialFailed");
            }
            Ok(())
        })();
        if let Some(server) = listeners.take() {
            match server.finish() {
                Ok(seen) => {
                    let expected = vec!["tcp:B".to_owned(), "udp:B".to_owned()];
                    let mut sorted = seen.clone();
                    sorted.sort();
                    proof["listener_observations"] = json!(seen);
                    proof["listener_expected_only"] = json!(sorted == expected);
                }
                Err(e) => {
                    proof["listener_threads_drained"] = json!(false);
                    proof["listener_error"] = json!(e);
                }
            }
        }
        if let Some(root) = fixture.as_ref() {
            for label in ["baseline", "boxed"] {
                let path = root.path.join(format!("{label}.txt"));
                match read_small(&path) {
                    Ok(bytes) => {
                        let suffix = if label == "baseline" { "B" } else { "X" };
                        let matches = bytes == format!("{challenge}{suffix}").as_bytes();
                        let captured = write_new(
                            &evidence.path.join(format!("{label}.file-proof.bin")),
                            &bytes,
                        )
                        .is_ok();
                        proof[format!("{label}_parent_file_readback")] = json!(matches && captured);
                    }
                    Err(_) => {
                        proof[format!("{label}_parent_file_readback")] = json!(false);
                    }
                }
            }
        }
        proof["profile_delete_eligible"] = json!(profile_delete_allowed(&proof));
        if let Some(package) = sid {
            if profile_delete_allowed(&proof) {
                match unsafe { DeleteAppContainerProfile(PCWSTR(name.as_ptr())) } {
                    Ok(()) => proof["profile_delete_api_succeeded"] = json!(true),
                    Err(e) => proof["profile_delete_hresult"] = json!(e.code().0),
                }
            }
            drop(package);
        }
        if let Err(error) = result {
            proof["error"] = json!(error);
        }
        proof["passed"] = json!(
            proof.get("error").is_none()
                && proof["baseline"]["passed"] == true
                && proof["boxed"]["passed"] == true
                && proof["baseline_parent_file_readback"] == true
                && proof["boxed_parent_file_readback"] == true
                && proof["listener_expected_only"] == true
                && proof["child_cleanup_known"] == true
                && proof["listener_threads_drained"] == true
                && proof["profile_delete_api_succeeded"] == true
        );
        // Evidence and all fixture/image identity pins are still live here,
        // including across the profile deletion attempt. Never follow a root
        // after releasing its ownership guard merely to write a final outcome.
        write_new(&evidence.path.join("proof.json"), &encode(&proof)?)?;
        if proof["passed"] != true {
            return fail("FeasibilityNotEstablished");
        }
        println!("AppContainerSelfCanaryFeasibilityPassed;NoWebViewOrModelQualification");
        Ok(())
    }

    // Unit-test-only fixed child protocol; production canary replies remain
    // raw JSON and never use this libtest marker decoder.
    #[cfg(test)]
    const LOW_FILE_PROBE_MARKER: &str = "LOCALLORE_LOW_FILE_PROBE_JSON=";
    #[cfg(test)]
    fn decode_low_file_probe_reply(bytes: &[u8]) -> Result<Value> {
        if bytes.len() > CAP { return fail("LowFileProbeReplyBudget"); }
        let text = std::str::from_utf8(bytes).map_err(|_| "LowFileProbeReplyEncoding")?;
        // libtest --nocapture may prefix the marker with its fixed test roster.
        // Retain its original bytes; accept exactly one complete diagnostic line.
        let mut lines = text.lines().filter_map(|line| line.split_once(LOW_FILE_PROBE_MARKER).map(|(_, value)| value));
        let value = lines.next().ok_or("LowFileProbeReplyMissing")?;
        if lines.next().is_some() { return fail("LowFileProbeReplyDuplicate"); }
        let reply: Value = serde_json::from_str(value).map_err(|_| "LowFileProbeReplyEncoding")?;
        let keys = ["version", "kind", "case", "run_id", "challenge", "token", "token_diagnostic",
            "fixture_binding", "rows", "measurement_complete", "passed"];
        let object = reply.as_object().ok_or("LowFileProbeReplyShape")?;
        if object.len() != keys.len() || object.keys().any(|key| !keys.contains(&key.as_str())) {
            return fail("LowFileProbeReplyShape");
        }
        Ok(reply)
    }
    #[cfg(test)]
    mod tests {
        use super::*;
        use std::os::windows::io::AsRawHandle;
        use windows::Win32::Security::Authorization::{
            ConvertSecurityDescriptorToStringSecurityDescriptorW, GetSecurityInfo,
        };
        // Fixed WinNT/file access bits. GENERIC_READ intentionally uses the
        // exact existing OpenOptions.read(true) path, not a reduced permission.
        const READ_MASKS: [(&str, u32); 5] = [
            ("FILE_READ_ATTRIBUTES", 0x0000_0080),
            ("FILE_READ_DATA|SYNCHRONIZE", 0x0010_0001),
            ("READ_CONTROL", 0x0002_0000),
            ("FILE_READ_EA", 0x0000_0008),
            ("GENERIC_READ", 0x8000_0000),
        ];
        fn read_mask_observations(path: &Path, expected: &[u8]) -> Value {
            let rows: Vec<Value> = READ_MASKS.into_iter().map(|(name, mask)| {
                let mut row = json!({"name":name,"access_mask":mask,"open_succeeded":false,
                    "open_error":null,"identity":null,"identity_error":null,
                    "read_attempted":false,"read_error":null,"read_bytes":0,
                    "read_sha256":null,"over_budget":false,"matches_expected":false});
                let mut options = OpenOptions::new();
                options.custom_flags(0x00200000).share_mode(1);
                if name == "GENERIC_READ" { options.read(true); }
                else { options.access_mode(mask); }
                let file = match options.open(path) {
                    Ok(file) => file,
                    Err(error) => {
                        row["open_error"] = json!({"os_error":error.raw_os_error(),"kind":format!("{:?}",error.kind())});
                        return row;
                    }
                };
                row["open_succeeded"] = json!(true);
                match file_identity(&file) {
                    Ok(identity) => row["identity"] = json!(identity),
                    Err(error) => row["identity_error"] = json!(error),
                }
                // Observe read denial even for a handle opened only for
                // metadata/control. Identity failure never hides read evidence.
                let mut bytes = vec![];
                row["read_attempted"] = json!(true);
                let result = file.take(CAP as u64 + 1).read_to_end(&mut bytes);
                row["read_bytes"] = json!(bytes.len());
                row["read_sha256"] = json!(format!("{:x}", Sha256::digest(&bytes)));
                row["over_budget"] = json!(bytes.len() > CAP);
                row["matches_expected"] = json!(result.is_ok() && bytes.len() <= CAP && bytes == expected);
                if let Err(error) = result {
                    row["read_error"] = json!({"os_error":error.raw_os_error(),"kind":format!("{:?}",error.kind())});
                }
                row
            }).collect();
            json!(rows)
        }
        fn full_read_row(rows: &Value) -> Option<&Value> {
            let rows = rows.as_array()?;
            if rows.len() != READ_MASKS.len() || rows.iter().zip(READ_MASKS).any(|(row, (name, mask))|
                row["name"] != name || row["access_mask"] != mask) { return None; }
            rows.last()
        }
        fn full_read_passed(rows: &Value) -> bool {
            full_read_row(rows).is_some_and(|row| row["open_succeeded"] == true &&
                row["open_error"].is_null() && !row["identity"].is_null() && row["identity_error"].is_null() &&
                row["read_attempted"] == true && row["read_error"].is_null() &&
                row["over_budget"] == false && row["matches_expected"] == true)
        }
        fn low_file_probe_request() -> Result<Value> {
            let mut bytes = vec![];
            io(std::io::stdin().take(4097).read_to_end(&mut bytes))?;
            if bytes.len() > 4096 { return fail("LowFileProbeInputBudget"); }
            let request: Value = serde_json::from_slice(&bytes).map_err(|_| "LowFileProbeInputEncoding")?;
            let keys = ["version", "kind", "case", "run_id", "challenge"];
            let object = request.as_object().ok_or("LowFileProbeInputShape")?;
            if object.len() != keys.len() || object.keys().any(|key| !keys.contains(&key.as_str())) ||
                request["version"] != 1 || request["kind"] != "low_file_read_probe" || request["case"] != "low-file-read" ||
                !request["run_id"].as_str().is_some_and(valid_id) || !request["challenge"].as_str().is_some_and(valid_id) ||
                encode(&request)? != bytes { return fail("LowFileProbeInputShape"); }
            Ok(request)
        }
        #[test]
        #[ignore = "fixed child only; Root runs the ignored parent diagnostic, never this without its owned bounded stdin"]
        fn low_integrity_file_probe_child() {
            let request = low_file_probe_request().unwrap();
            let id = request["run_id"].as_str().unwrap();
            let challenge = request["challenge"].as_str().unwrap();
            let image = std::env::current_exe().unwrap();
            let root = fixture_from_self(&image, id).unwrap();
            let moniker = wide(format!("locallore.offline.{id}"));
            // Derive only: no managed profile creation/deletion/storage access.
            let package = Sid(unsafe { DeriveAppContainerSidFromAppContainerName(PCWSTR(moniker.as_ptr())) }.unwrap());
            let package_sid = sid_text(package.0).unwrap();
            let expected = challenge_marker(id, &package_sid, challenge).unwrap();
            let token = token_observation(unsafe { GetCurrentProcess() }).unwrap_or_else(|error| json!({"observation_error":error}));
            let diagnostic = token_diagnostic(unsafe { GetCurrentProcess() }).unwrap_or_else(|error| json!({"diagnostic_error":error}));
            let rows = read_mask_observations(&root.join("challenge.txt"), &expected);
            let passed = full_read_passed(&rows) && token["is_appcontainer"] == true &&
                token["capability_count"] == 0 && token["package_sid"] == package_sid &&
                diagnostic["integrity_sid"] == "S-1-16-4096";
            let report = json!({"version":1,"kind":"low_file_read_probe","case":"low-file-read",
                "run_id":id,"challenge":challenge,"token":token,"token_diagnostic":diagnostic,
                "fixture_binding":{"component":format!("fixture-{id}"),"self_image_name":"offline-qualifier.exe"},
                "rows":rows,"measurement_complete":true,"passed":passed});
            let encoded = encode(&report).unwrap();
            assert!(encoded.len() <= CAP, "fixed diagnostic output must remain bounded");
            // Always preserve all five mask results before asserting the
            // unchanged required full GENERIC_READ result or token condition.
            println!("{LOW_FILE_PROBE_MARKER}{}", std::str::from_utf8(&encoded).unwrap());
            std::io::stdout().flush().unwrap();
            assert!(passed, "Required low-token GENERIC_READ failed; five-mask diagnostic was emitted before this assertion");
        }
        #[test]
        #[ignore = "explicit Root-only owned child diagnostic; no profile/network; requires prior source review and serial execution slot"]
        fn low_integrity_file_read_mask_diagnostic() {
            let id = guid().unwrap();
            let challenge = guid().unwrap();
            let temporary = std::env::temp_dir();
            let evidence = create_owned_directory(&temporary, &format!("locallore-offline-proof-{id}")).unwrap();
            let root = create_owned_directory(&temporary, &format!("fixture-{id}")).unwrap();
            eprintln!("LOCALLORE_LOW_FILE_READ_ARTIFACT={}", evidence.path.display());
            let moniker = wide(format!("locallore.offline.{id}"));
            let package = Sid(unsafe { DeriveAppContainerSidFromAppContainerName(PCWSTR(moniker.as_ptr())) }.unwrap());
            grant_new_fixture(&root, package.0).unwrap();
            let image = copy_self_to_new(&root).unwrap(); // The unit-test self image, never an arbitrary executable.
            let marker = challenge_marker(&id, &sid_text(package.0).unwrap(), &challenge).unwrap();
            let marker_path = root.path.join("challenge.txt");
            write_new(&marker_path, &marker).unwrap();
            // Not inheritable and absent from the fixed three-pipe handle list.
            // Pin original bytes/native identity without sharing writes/deletes.
            let marker_pin = OpenOptions::new().read(true).custom_flags(0x00200000).share_mode(1).open(&marker_path).unwrap();
            let identity = file_identity(&marker_pin).unwrap();
            let medium_rows = read_mask_observations(&marker_path, &marker);
            let medium_token = token_observation(unsafe { GetCurrentProcess() }).unwrap_or_else(|error| json!({"observation_error":error}));
            let medium_diagnostic = token_diagnostic(unsafe { GetCurrentProcess() }).unwrap_or_else(|error| json!({"diagnostic_error":error}));
            let medium_passed = full_read_passed(&medium_rows) && medium_token["is_appcontainer"] == false &&
                medium_diagnostic["integrity_sid"] == "S-1-16-8192" &&
                full_read_row(&medium_rows).is_some_and(|row| row["identity"] == json!(identity));
            write_new(&evidence.path.join("medium-control.json"), &encode(&json!({"version":1,
                "kind":"medium_file_read_control","run_id":id,"token":medium_token,"token_diagnostic":medium_diagnostic,
                "rows":medium_rows,"passed":medium_passed,"profile_created":false,"network_tested":false})).unwrap()).unwrap();
            assert!(medium_passed, "Original medium GENERIC_READ control failed; original evidence retained before any child launch");
            let request = json!({"version":1,"kind":"low_file_read_probe","case":"low-file-read","run_id":id,"challenge":challenge});
            let child = run_child_fixed(&image.path, Some(package.0), &request, &evidence.path, "low-file-read", ChildMode::LowFileReadProbe);
            write_new(&evidence.path.join("child-process.json"), &encode(&child).unwrap()).unwrap();
            let low_rows = &child["reply"]["rows"];
            let same_identity = full_read_row(low_rows).is_some_and(|row| row["identity"] == json!(identity));
            let passed = medium_passed && child["passed"] == true && child["cleanup_known"] == true &&
                child["threads_drained"] == true && full_read_passed(low_rows) && same_identity;
            write_new(&evidence.path.join("summary.json"), &encode(&json!({"version":1,"kind":"low_file_read_mask_diagnostic",
                "run_id":id,"passed":passed,"medium_control_passed":medium_passed,"required_generic_read_passed":full_read_passed(low_rows),
                "same_marker_identity":same_identity,"marker_identity":identity,
                "marker_identity_fields":["volume_serial","file_index_high","file_index_low"],
                "self_image_sha256":image.sha256,"marker_sha256":format!("{:x}",Sha256::digest(&marker)),
                "child_cleanup_known":child["cleanup_known"],"child_threads_drained":child["threads_drained"],
                "profile_created":false,"profile_deleted":false,"network_tested":false,"inherited_marker_handle":false,
                "production_canary_executed":false,"webview_executed":false,"model_executed":false})).unwrap()).unwrap();
            // Child failure is diagnostic evidence, never an expected-pass waiver.
            // Keep all directory/image/marker guards through final evidence.
            assert!(passed, "Required unchanged GENERIC_READ/identity/token/cleanup failed; retained five-mask diagnostic does not waive it");
        }
        // Frozen filesystem/ACL ownership tests below never launch a child,
        // model, network request, or WebView. The ignored diagnostic above
        // launches only its fixed unit-test child after explicit review.
        fn fixture() -> PinnedDirectory {
            let root = create_owned_directory(
                &std::env::temp_dir(),
                &format!("fixture-{}", guid().unwrap()),
            )
            .unwrap();
            eprintln!(
                "LOCALLORE_OFFLINE_PIN_REVIEW_ARTIFACT={}",
                root.path.display()
            );
            root // Retain tiny synthetic evidence on success/failure; no cleanup of computed roots.
        }
        fn dacl(file: &File) -> String {
            let mut security = PSECURITY_DESCRIPTOR::default();
            unsafe {
                GetSecurityInfo(
                    HANDLE(file.as_raw_handle()),
                    SE_FILE_OBJECT,
                    DACL_SECURITY_INFORMATION,
                    None,
                    None,
                    None,
                    None,
                    Some(&mut security),
                )
                .ok()
            }
            .unwrap();
            let mut text = PWSTR::null();
            let converted = unsafe {
                ConvertSecurityDescriptorToStringSecurityDescriptorW(
                    security,
                    SDDL_REVISION_1,
                    DACL_SECURITY_INFORMATION,
                    &mut text,
                    None,
                )
            };
            let result = converted.map(|()| unsafe { text.to_string() });
            unsafe {
                LocalFree(Some(HLOCAL(security.0)));
            }
            if !text.is_null() {
                unsafe {
                    LocalFree(Some(HLOCAL(text.0.cast())));
                }
            }
            result.unwrap().unwrap()
        }
        #[test]
        fn canary_self_location_and_marker_bind_exact_run_sid_and_challenge() {
            let id = "11111111-2222-3333-4444-555555555555";
            let other = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";
            let fixture = PathBuf::from(format!("C:\\synthetic-task-temp\\fixture-{id}"));
            assert_eq!(
                fixture_from_self(&fixture.join("offline-qualifier.exe"), id).unwrap(),
                fixture
            );
            for path in [
                fixture.join("other.exe"),
                fixture.join("nested").join("offline-qualifier.exe"),
                PathBuf::from(format!(
                    "C:\\synthetic-task-temp\\fixture-{other}\\offline-qualifier.exe"
                )),
                PathBuf::from(format!("fixture-{id}\\offline-qualifier.exe")),
                PathBuf::from(format!(
                    "C:\\synthetic-task-temp\\..\\fixture-{id}\\offline-qualifier.exe"
                )),
                PathBuf::from(format!(
                    "\\\\server\\share\\fixture-{id}\\offline-qualifier.exe"
                )),
            ] {
                assert!(fixture_from_self(&path, id).is_err());
            }
            assert!(fixture_from_self(&fixture.join("offline-qualifier.exe"), "invalid").is_err());
            let marker = challenge_marker(id, "S-1-15-2-123", other).unwrap();
            assert_ne!(
                marker,
                challenge_marker(other, "S-1-15-2-123", other).unwrap()
            );
            assert_ne!(marker, challenge_marker(id, "S-1-15-2-456", other).unwrap());
            assert_ne!(marker, challenge_marker(id, "S-1-15-2-123", id).unwrap());
            assert_eq!(
                serde_json::from_slice::<Value>(&marker).unwrap(),
                json!({
                    "version":1,"run_id":id,"package_sid":"S-1-15-2-123","challenge":other
                })
            );
        }
        #[test]
        fn held_new_root_cannot_redirect_acl_and_outside_sentinel_stays_exact() {
            let parent = fixture();
            let outside =
                create_owned_directory(&parent.path, &format!("fixture-{}", guid().unwrap()))
                    .unwrap();
            let sentinel = outside.path.join("sentinel.txt");
            write_new(&sentinel, b"outside-owned-sentinel").unwrap();
            let outside_acl = dacl(&outside.file);
            let name = format!("fixture-{}", guid().unwrap());
            let owned = create_owned_directory(&parent.path, &name).unwrap();
            assert!(
                fs::rename(&owned.path, parent.path.join("renamed")).is_err(),
                "live no-delete handle blocks root replacement"
            );
            let write_attempt = OpenOptions::new()
                .write(true)
                .custom_flags(0x02000000 | 0x00200000)
                .share_mode(3)
                .open(&owned.path);
            assert!(
                matches!(write_attempt, Err(error) if error.raw_os_error() == Some(32)),
                "live no-write-sharing root rejects the handle needed for reparse mutation"
            );
            let moniker = wide(format!("locallore.offline.{}", guid().unwrap()));
            let package =
                Sid(
                    unsafe { DeriveAppContainerSidFromAppContainerName(PCWSTR(moniker.as_ptr())) }
                        .unwrap(),
                );
            grant_new_fixture(&owned, package.0).unwrap();
            assert_eq!(dacl(&outside.file), outside_acl);
            assert_eq!(read_small(&sentinel).unwrap(), b"outside-owned-sentinel");
            assert!(
                create_owned_directory(&parent.path, &name).is_err(),
                "collision never adopts the existing object"
            );
            assert_eq!(dacl(&outside.file), outside_acl);
        }
        #[test]
        fn existing_destination_never_overwrites_or_changes_bytes_or_acl() {
            let root = fixture();
            let target = root.path.join("offline-qualifier.exe");
            write_new(&target, b"existing-object-not-a-canary").unwrap();
            let before = io(File::open(&target)).unwrap();
            let acl = dacl(&before);
            assert!(copy_self_to_new(&root).is_err());
            assert_eq!(
                read_small(&target).unwrap(),
                b"existing-object-not-a-canary"
            );
            assert_eq!(dacl(&before), acl);
        }
        #[test]
        #[ignore = "explicit Windows symbolic-link privilege required; opt-in must create the real link"]
        fn existing_reparse_parent_and_collision_never_touch_outside_acl_or_bytes() {
            let parent = fixture();
            let outside =
                create_owned_directory(&parent.path, &format!("fixture-{}", guid().unwrap()))
                    .unwrap();
            let sentinel = outside.path.join("sentinel.txt");
            write_new(&sentinel, b"outside-reparse-sentinel").unwrap();
            let before = dacl(&outside.file);
            let name = format!("fixture-{}", guid().unwrap());
            let link = parent.path.join(&name);
            std::os::windows::fs::symlink_dir(&outside.path, &link)
                .expect("actual reparse setup; never silent skip");
            assert!(create_owned_directory(&parent.path, &name).is_err());
            assert!(
                create_owned_directory(&link, &format!("fixture-{}", guid().unwrap())).is_err()
            );
            assert_eq!(dacl(&outside.file), before);
            assert_eq!(read_small(&sentinel).unwrap(), b"outside-reparse-sentinel");
            assert_eq!(fs::read_dir(&outside.path).unwrap().count(), 1);
        }
        #[test]
        fn new_fixture_challenge_is_readable_before_any_child_or_profile_creation() {
            let root = fixture();
            let moniker = wide(format!("locallore.offline.{}", guid().unwrap()));
            let package =
                Sid(
                    unsafe { DeriveAppContainerSidFromAppContainerName(PCWSTR(moniker.as_ptr())) }
                        .unwrap(),
                );
            grant_new_fixture(&root, package.0).unwrap();
            let marker = root.path.join("challenge.txt");
            write_new(&marker, b"fixed-synthetic-challenge").unwrap();
            assert_eq!(read_small(&marker).unwrap(), b"fixed-synthetic-challenge");
            let verbatim = fs::canonicalize(&marker).unwrap();
            assert!(
                matches!(verbatim.components().next(), Some(Component::Prefix(p)) if matches!(p.kind(), Prefix::VerbatimDisk(_)))
            );
            assert_eq!(read_small(&verbatim).unwrap(), b"fixed-synthetic-challenge");
        }
        #[test]
        fn actual_pipe_deadline_retains_completed_diagnostics_without_inventing_eof() {
            let (input, output) = pipe().unwrap();
            let worker = reader(into_file(input)).unwrap();
            assert!(
                !reader_ready(&worker, Instant::now()),
                "an open empty pipe is not drained"
            );
            let mut writer = into_file(output);
            writer
                .write_all(b"OfflineQualifierFailed:fixed-synthetic-error")
                .unwrap();
            drop(writer);
            assert!(reader_ready(
                &worker,
                Instant::now() + Duration::from_secs(5)
            ));
            assert_eq!(
                worker.join().unwrap().unwrap(),
                b"OfflineQualifierFailed:fixed-synthetic-error"
            );
        }
        #[test]
        fn profile_deletion_requires_every_attempted_child_and_all_threads_known_drained() {
            let proof = json!({"profile_created":true,"child_cleanup_known":true,"listener_threads_drained":true,
                "baseline":{"cleanup_known":true,"threads_drained":true},
                "boxed":{"cleanup_known":true,"threads_drained":true}});
            assert!(profile_delete_allowed(&proof));
            for child in ["baseline", "boxed"] {
                for field in ["cleanup_known", "threads_drained"] {
                    let mut bad = proof.clone();
                    bad[child][field] = json!(false);
                    assert!(
                        !profile_delete_allowed(&bad),
                        "positive process cleanup cannot mask undrained pipes"
                    );
                    bad[child].as_object_mut().unwrap().remove(field);
                    assert!(
                        !profile_delete_allowed(&bad),
                        "missing proof is not success"
                    );
                }
            }
            for field in [
                "child_cleanup_known",
                "listener_threads_drained",
                "profile_created",
            ] {
                let mut bad = proof.clone();
                bad[field] = json!(false);
                assert!(!profile_delete_allowed(&bad));
            }
        }
    }
}
