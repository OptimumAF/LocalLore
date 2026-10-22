param([string]$AdbPath)

# Read-only inventory of an already authorized Android transport. Never prints a serial.
$ErrorActionPreference = 'Stop'
if (-not $AdbPath) {
    $adbCommand = Get-Command adb -ErrorAction SilentlyContinue
    if ($adbCommand) { $AdbPath = $adbCommand.Source }
}
if (-not $AdbPath) {
    $sdkRoots = @($env:ANDROID_HOME, $env:ANDROID_SDK_ROOT, "$env:LOCALAPPDATA\Android\Sdk")
    foreach ($sdkRoot in $sdkRoots) {
        if ($sdkRoot) {
            $candidate = Join-Path $sdkRoot 'platform-tools\adb.exe'
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { $AdbPath = $candidate; break }
        }
    }
}
if (-not $AdbPath -or -not (Test-Path -LiteralPath $AdbPath -PathType Leaf)) {
    @{ status = 'blocked'; reason = 'adb_unavailable'; device_presence = 'unknown' } | ConvertTo-Json
    exit 2
}

# ADB can start its local daemon; no connect/pair/root/install/reboot/push commands are used.
$deviceLines = @(& $AdbPath devices 2>$null)
if ($LASTEXITCODE -ne 0) { throw 'ADB inventory failed (details omitted to protect device identifiers).' }
$authorized = @($deviceLines | Where-Object { $_ -match '^\S+\s+device\s*$' })
$physicalCandidates = @()
$emulatorCount = 0
foreach ($deviceLine in $authorized) {
    $candidateId = ($deviceLine -split '\s+')[0]
    $qemuIndicator = @(& $AdbPath -s $candidateId shell getprop ro.kernel.qemu 2>$null) -join ''
    if ($LASTEXITCODE -ne 0) { continue }
    if ($qemuIndicator.Trim() -eq '1' -or $candidateId.StartsWith('emulator-')) { $emulatorCount++ }
    else { $physicalCandidates += $candidateId }
}
if ($physicalCandidates.Count -ne 1) {
    @{ status = 'blocked'; reason = 'exactly_one_authorized_physical_candidate_required';
       authorized_count = $authorized.Count; emulator_count = $emulatorCount;
       physical_candidate_count = $physicalCandidates.Count } | ConvertTo-Json
    exit 2
}
$deviceId = $physicalCandidates[0]
function Read-DeviceValue([string[]]$Arguments) {
    $value = @(& $AdbPath -s $deviceId shell @Arguments 2>$null)
    if ($LASTEXITCODE -ne 0) { return $null }
    return ($value -join "`n").Trim()
}
$battery = Read-DeviceValue -Arguments @('dumpsys', 'battery')
$memory = Read-DeviceValue -Arguments @('cat', '/proc/meminfo')
$thermal = Read-DeviceValue -Arguments @('dumpsys', 'thermalservice')
$report = [ordered]@{
    status = 'inventory_only'
    emulator_indicator = Read-DeviceValue -Arguments @('getprop', 'ro.kernel.qemu')
    manufacturer = Read-DeviceValue -Arguments @('getprop', 'ro.product.manufacturer')
    model = Read-DeviceValue -Arguments @('getprop', 'ro.product.model')
    soc_model = Read-DeviceValue -Arguments @('getprop', 'ro.soc.model')
    android_release = Read-DeviceValue -Arguments @('getprop', 'ro.build.version.release')
    sdk = Read-DeviceValue -Arguments @('getprop', 'ro.build.version.sdk')
    build_id = Read-DeviceValue -Arguments @('getprop', 'ro.build.id')
    memory = @($memory -split "`n" | Where-Object { $_ -match '^(MemTotal|MemAvailable):' })
    data_space = Read-DeviceValue -Arguments @('df', '-k', '/data')
    battery = @($battery -split "`n" | Where-Object { $_ -match '^\s*(AC powered|USB powered|Wireless powered|level|status|temperature|voltage):' })
    thermal_status = @($thermal -split "`n" | Where-Object { $_ -match '^\s*Thermal Status:' })
    physical_ram_tier = 'requires independent confirmation; MemTotal is kernel-visible memory'
    measured_inference = $false
    physical_device_confirmation = 'Confirm physical ownership and target before benchmarking; an emulator is not a phone result'
}
$report | ConvertTo-Json -Depth 4
