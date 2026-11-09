#requires -Version 7.5
# Review source. Retain under the admitted packet name before an authorized run.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$env:TEMP = 'D:/Dev/_Temp'
$env:TMP = $env:TEMP

if ($args.Count -ne 0 -or -not $IsWindows) { throw 'FixedWindowsPacket' }
$head = '55781755bbe4444b012910027ce5ad48b3ea0dba'
$packetLimit = 512KB
$streamLimit = 4KB
$packet = $PSScriptRoot
$group = Split-Path -Parent $packet
$artifacts = Split-Path -Parent $group
$base = Split-Path -Parent $artifacts
$repo = Join-Path $base 'source-desktop-fork-review'
$desktop = Join-Path $repo 'apps/desktop'
$entry = Join-Path $desktop 'check-inspection-controller.mjs'
$tools = Join-Path $base 'd09-build-security'
$node = Join-Path $tools 'node-v24.22.1-win-x64/node.exe'
$esbuild = Join-Path $tools 'node_modules/esbuild/lib/main.js'
$service = Join-Path $tools 'node_modules/@esbuild/win32-x64/esbuild.exe'
$bundle = Join-Path $packet 'bundle'
$scratch = Join-Path $packet '_tmp'
$utf8 = [Text.UTF8Encoding]::new($false, $true)

function Assert-PhysicalD([string] $Path) {
    $current = [IO.Path]::GetFullPath($Path)
    if ([IO.Path]::GetPathRoot($current) -ine 'D:\') { throw 'DriveBoundary' }
    while ($current) {
        $item = Get-Item -LiteralPath $current -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'ReparseBoundary' }
        $current = [IO.Path]::GetDirectoryName($current)
    }
}

function Bytes-Sha([byte[]] $Bytes) {
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}

function File-Sha([string] $Path) {
    Assert-PhysicalD $Path
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Assert-Input([string] $Path, [long] $Bytes, [string] $Hash) {
    Assert-PhysicalD $Path
    $file = Get-Item -LiteralPath $Path
    if ($file.PSIsContainer -or $file.Length -ne $Bytes -or (File-Sha $Path) -cne $Hash) {
        throw 'PinnedInputChanged'
    }
}

function Read-Record([string] $Name) {
    $file = Join-Path $packet $Name
    Assert-PhysicalD $file
    $stream = [IO.File]::OpenRead($file)
    try {
        if ($stream.Length -lt 1 -or $stream.Length -gt 4096) { throw 'RecordSize' }
        $bytes = [byte[]]::new([int]$stream.Length)
        $stream.ReadExactly($bytes, 0, $bytes.Length)
        if ($stream.ReadByte() -ne -1) { throw 'RecordChanged' }
        $utf8.GetString($bytes) | ConvertFrom-Json -AsHashtable -DateKind String
    } finally {
        $stream.Dispose()
    }
}

function Measure-Tree([string] $Root, [int] $MaxEntries) {
    Assert-PhysicalD $Root
    $count = 0
    [long]$bytes = 0
    Get-ChildItem -LiteralPath $Root -Force -Recurse | ForEach-Object {
        if (++$count -gt $MaxEntries -or ($_.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'InventoryBoundary'
        }
        if (-not $_.PSIsContainer) { $bytes += $_.Length }
    }
    return $bytes
}

function Write-Bytes([string] $Name, [byte[]] $Bytes) {
    if ($Bytes.Length -gt $streamLimit -or
        (Measure-Tree $packet 256) + $Bytes.Length -gt $packetLimit) { throw 'RetentionBoundary' }
    $file = [IO.File]::Open((Join-Path $packet $Name), 'CreateNew', 'Write', 'None')
    try {
        $file.Write($Bytes, 0, $Bytes.Length)
        $file.Flush($true)
    } finally {
        $file.Dispose()
    }
}

function Write-Record([string] $Name, $Value) {
    Write-Bytes $Name ($utf8.GetBytes(($Value | ConvertTo-Json -Compress -Depth 5) + [char]10))
}

function Assert-Source {
    $commit = git --no-optional-locks -C $repo rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $commit -cne $head) { throw 'SourceHead' }
    $dirty = git --no-optional-locks -C $repo status --porcelain
    if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'SourceStatus' }
    if ((File-Sha $entry) -cne 'd3925f50244df03a156141d7b63178fb68fd3970480c24f51bb3db9cdf3af981' -or
        (Test-Path -LiteralPath (Join-Path $desktop 'node_modules'))) { throw 'EntryBoundary' }
}

if ((Bytes-Sha ($utf8.GetBytes([IO.Path]::GetFullPath($base).ToLowerInvariant()))) -cne
    '49d8c83a7c6766fd0a5817481ddeb9a701d9c39cc578b806660f860eb593c713' -or
    (Split-Path -Leaf $packet) -cne 'd05-inspection-controller-431-v1' -or
    (Split-Path -Leaf $group) -cne 'd09-frontend-evidence-admission-20261030-v1' -or
    (Split-Path -Leaf $artifacts) -cne 'author-integration-artifacts' -or
    (Split-Path -Leaf $PSCommandPath) -cne 'inspection-controller-431-packet.ps1' -or
    (Get-Location).ProviderPath -ine $repo) { throw 'PacketLocation' }
foreach ($directory in $packet, $bundle, $scratch) {
    Assert-PhysicalD $directory
    if (-not (Get-Item -LiteralPath $directory).PSIsContainer) { throw 'PacketDirectory' }
}
$expectedLeaves = @('inspection-controller-431-packet.ps1', 'owner.json', 'stage.json', '_tmp', 'bundle')
$leaves = @(Get-ChildItem -LiteralPath $packet -Force)
if ($leaves.Count -ne $expectedLeaves.Count -or
    ($leaves.Name | Where-Object { $_ -cnotin $expectedLeaves }) -or
    @(Get-ChildItem -LiteralPath $bundle -Force).Count -ne 0 -or
    @(Get-ChildItem -LiteralPath $scratch -Force).Count -ne 0) { throw 'PacketAlreadyUsedOrUnexpected' }

$owner = Read-Record 'owner.json'
$stage = Read-Record 'stage.json'
$self = File-Sha $PSCommandPath
$ownerHash = File-Sha (Join-Path $packet 'owner.json')
$stageHash = File-Sha (Join-Path $packet 'stage.json')
if ($owner.kind -cne 'd05_inspection_431_owner_v1' -or $owner.approved -isnot [bool] -or
    -not $owner.approved -or $owner.approvalRef -isnot [string] -or
    $owner.approvalRef.Length -lt 1 -or $owner.approvalRef.Length -gt 512 -or
    $owner.testHead -cne $head -or $owner.launcherSha256 -cne $self -or
    $stage.kind -cne 'd05_inspection_431_stage_v1' -or $stage.ownerSha256 -cne $ownerHash -or
    $stage.testHead -cne $head -or $stage.launcherSha256 -cne $self -or
    $stage.measuredUtc -isnot [string]) { throw 'AdmissionBinding' }
foreach ($key in 'd09BaseBytes', 'namedBaseBytes', 'crossTrackBaseBytes') {
    $value = $stage[$key]
    if (($value -isnot [int] -and $value -isnot [long]) -or $value -lt 0) { throw 'AdmissionCount' }
}

Assert-Source
Assert-Input $node 93915464 'd702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5'
Assert-Input $esbuild 97463 '61ec0ba144ff93f4bf0e96ad6fab6f430ede0aa13e27ace8063ed63ba416b3cd'
Assert-Input (Join-Path $tools 'node_modules/esbuild/package.json') 3980 '9d0bc453f4e791553c4cc2298ba023b409241fd9801e494741666eb0f6051490'
Assert-Input (Join-Path $tools 'node_modules/@esbuild/win32-x64/package.json') 374 '89382df45735edcd917c492a810ab514920fa07d36c653cdc122bdfd8f526964'
Assert-Input $service 11694592 'c7bee37877d0aa6a046e52783fa0a2cf1a9ce5579d68bb3083bda99d4bff18ef'

$startingBytes = Measure-Tree $packet 256
$d09Before = (Measure-Tree $group 4096) - $startingBytes
if ($startingBytes -gt 32KB -or $d09Before -ne $stage.d09BaseBytes -or
    $d09Before + $packetLimit -gt 64MB -or
    $stage.namedBaseBytes -lt $d09Before + 581145615 -or
    $stage.namedBaseBytes -gt 640MB - $packetLimit -or
    $stage.crossTrackBaseBytes -lt $stage.namedBaseBytes -or
    $stage.crossTrackBaseBytes -gt 724MB - $packetLimit) { throw 'FreshReserve' }

# A fixed resolver changes one import edge, then delegates to Node's normal resolver.
$entryUrl = ([uri]::new($entry)).AbsoluteUri | ConvertTo-Json -Compress
$moduleUrl = ([uri]::new($esbuild)).AbsoluteUri | ConvertTo-Json -Compress
$servicePath = $service | ConvertTo-Json -Compress
$hook = @"
import { registerHooks } from 'node:module';
import childProcess from 'node:child_process';
import { win32 } from 'node:path';

const hook = registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === 'esbuild' && context.parentURL === $entryUrl)
      return nextResolve($moduleUrl, context);
    return nextResolve(specifier, context);
  }
});
const spawn = childProcess.spawn;
let service;
let serviceClosed;
childProcess.spawn = function (file, args, options) {
  if (service || typeof file !== 'string' ||
      win32.normalize(file).toLowerCase() !== win32.normalize($servicePath).toLowerCase() ||
      !Array.isArray(args) || args.length !== 2 || args[0] !== '--service=0.28.2' || args[1] !== '--ping' ||
      options?.windowsHide !== true || options.stdio?.join(',') !== 'pipe,pipe,inherit' ||
      options.cwd !== process.cwd()) {
    throw Error('UnexpectedBuildToolOffer');
  }
  service = spawn.call(this, file, args, options);
  serviceClosed = new Promise(resolve => service.once('close', () => resolve(service.pid)));
  return service;
};
try {
  const esbuild = await import($moduleUrl);
  try {
    await import($entryUrl);
  } finally {
    if (service) {
      await esbuild.stop();
      let timer;
      try {
        const pid = await Promise.race([
          serviceClosed,
          new Promise(resolve => { timer = setTimeout(resolve, 3000); }),
        ]);
        if (!Number.isSafeInteger(pid) || pid < 1) throw Error('BuildToolClosureUnknown');
        console.log('ESBUILD_CLOSED ' + pid);
      } finally {
        clearTimeout(timer);
      }
    }
  }
} finally {
  childProcess.spawn = spawn;
  hook.deregister();
}
"@
$preload = 'data:text/javascript;base64,' + [Convert]::ToBase64String($utf8.GetBytes($hook))
$startInfo = [Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $node
$startInfo.WorkingDirectory = $desktop
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.RedirectStandardInput = $true
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$startInfo.ArgumentList.Add("--import=$preload")
$startInfo.ArgumentList.Add('--input-type=module')
$startInfo.ArgumentList.Add('--eval')
$startInfo.ArgumentList.Add('')
$startInfo.Environment.Clear()
$startInfo.Environment['SystemRoot'] = $env:SystemRoot
$startInfo.Environment['TEMP'] = $scratch
$startInfo.Environment['TMP'] = $scratch
$startInfo.Environment['NODE_DISABLE_COMPILE_CACHE'] = '1'
$startInfo.Environment['LOCALLORE_CHECK_OUTPUT_DIR'] = $bundle

$measured = [DateTimeOffset]::ParseExact($stage.measuredUtc, 'o', [Globalization.CultureInfo]::InvariantCulture)
$age = [DateTimeOffset]::UtcNow - $measured
if ($age.TotalSeconds -lt 0 -or $age.TotalSeconds -gt 120 -or
    (File-Sha (Join-Path $packet 'stage.json')) -cne $stageHash -or
    (File-Sha (Join-Path $packet 'owner.json')) -cne $ownerHash) { throw 'StaleStage' }
Write-Record 'start.json' ([ordered]@{
    kind = 'd05_inspection_431_start_v1'
    testHead = $head
    launcherSha256 = $self
    ownerSha256 = $ownerHash
    stageSha256 = $stageHash
    preloadSha256 = Bytes-Sha ($utf8.GetBytes($hook))
    beganUtc = [DateTimeOffset]::UtcNow.ToString('o')
})

$child = [Diagnostics.Process]::new()
$child.StartInfo = $startInfo
$buffers = [byte[][]]@([byte[]]::new($streamLimit + 1), [byte[]]::new($streamLimit + 1))
$counts = [int[]]@(0, 0)
$eof = [bool[]]@($false, $false)
$reads = [Threading.Tasks.Task[int][]]::new(2)
$processStarted = $false
$disposed = $false
$stdinClosed = $false
$inputWriter = $null
$outputReaders = [IO.StreamReader[]]::new(2)
$readersReleased = [bool[]]::new(2)
$pidObserved = $null
$exitCode = $null
$reason = $null
$stopAt = $null
$killRequested = $false
$clock = [Diagnostics.Stopwatch]::StartNew()
try {
    $processStarted = $child.Start()
    if (-not $processStarted) { throw 'StartRefused' }
    $pidObserved = $child.Id
    $inputWriter = $child.StandardInput
    $inputWriter.Close()
    $stdinClosed = $true
    $outputReaders[0] = $child.StandardOutput
    $outputReaders[1] = $child.StandardError
    $streams = @($outputReaders[0].BaseStream, $outputReaders[1].BaseStream)
    for ($i = 0; $i -lt 2; $i++) {
        $reads[$i] = $streams[$i].ReadAsync($buffers[$i], 0, $buffers[$i].Length)
    }
    while ($true) {
        if ($null -ne $stopAt -and $clock.ElapsedMilliseconds -ge $stopAt + 5000) { break }
        for ($i = 0; $i -lt 2; $i++) {
            if ($null -eq $reads[$i] -or -not $reads[$i].IsCompleted) { continue }
            try {
                $n = $reads[$i].GetAwaiter().GetResult()
                $counts[$i] += $n
                if ($n -eq 0) {
                    $eof[$i] = $true
                    $reads[$i] = $null
                } elseif ($counts[$i] -gt $streamLimit) {
                    $reason ??= 'StreamLimit'
                    $reads[$i] = $null
                } else {
                    $reads[$i] = $streams[$i].ReadAsync(
                        $buffers[$i], $counts[$i], $buffers[$i].Length - $counts[$i])
                }
            } catch {
                $reason ??= 'StreamReadFailed'
                $reads[$i] = $null
            }
        }
        if ($clock.ElapsedMilliseconds -ge 30000) { $reason ??= 'Deadline' }
        if ($child.HasExited) {
            $exitCode = $child.ExitCode
            if ($eof[0] -and $eof[1]) { break }
        }
        if ($reason -and $null -eq $stopAt) {
            $stopAt = [Math]::Min($clock.ElapsedMilliseconds, 30000)
            if (-not $child.HasExited) {
                $killRequested = $true
                try { $child.Kill($true) } catch { $reason = 'StopUnconfirmed' }
            }
        }
        if ($null -ne $stopAt -and $clock.ElapsedMilliseconds -ge $stopAt + 5000) { break }
        Start-Sleep -Milliseconds 5
    }
} catch {
    $reason ??= 'ProcessObservationFailed'
    if ($processStarted) {
        $stopAt ??= [Math]::Min($clock.ElapsedMilliseconds, 30000)
        try {
            if (-not $child.HasExited -and -not $killRequested) {
                $killRequested = $true
                $child.Kill($true)
            }
            $remaining = [int][Math]::Max(0, $stopAt + 5000 - $clock.ElapsedMilliseconds)
            if ($child.WaitForExit($remaining)) { $exitCode = $child.ExitCode }
        } catch { $reason = 'StopUnconfirmed' }
    }
} finally {
    if ($inputWriter -and -not $stdinClosed) {
        try {
            $inputWriter.Dispose()
            $stdinClosed = $true
        } catch { $reason ??= 'ProcessCloseFailed' }
    }
    foreach ($i in 0..1) {
        if ($outputReaders[$i]) {
            try {
                $outputReaders[$i].Dispose()
                $readersReleased[$i] = $true
            } catch { $reason ??= 'ProcessCloseFailed' }
        }
    }
    try {
        $child.Dispose()
        $disposed = $true
    } catch { $reason ??= 'ProcessCloseFailed' }
    $clock.Stop()
}
if ($clock.ElapsedMilliseconds -ge 30000) { $reason ??= 'Deadline' }

$closed = $disposed -and $stdinClosed -and $null -ne $exitCode -and
    $eof[0] -and $eof[1] -and $readersReleased[0] -and $readersReleased[1]
$logs = [ordered]@{}
foreach ($i in 0..1) {
    $name = @('stdout.bin', 'stderr.bin')[$i]
    $bytes = [byte[]]::new([Math]::Min($streamLimit, $counts[$i]))
    [Array]::Copy($buffers[$i], $bytes, $bytes.Length)
    $hash = Bytes-Sha $bytes
    $retained = $false
    try {
        Write-Bytes $name $bytes
        $retained = (File-Sha (Join-Path $packet $name)) -ceq $hash
    } catch { $reason ??= 'StreamRetentionRefused' }
    if (-not $retained) { $reason ??= 'StreamRetentionRefused' }
    $logs[$name] = @{ bytes = $bytes.Length; sha256 = $hash; retained = $retained }
}
$reason ??= if (-not $closed) { 'UnknownClosure' }
    elseif ($exitCode -ne 0 -or $counts[1] -ne 0) { 'ControllerCheckFailed' }
    else { $null }

$lines = @()
$servicePid = $null
if ($eof[0] -and $counts[0] -le $streamLimit) {
    try {
        $lines = $utf8.GetString($buffers[0], 0, $counts[0]).Replace([string][char]13, '').TrimEnd().Split([char]10)
        if ($lines[-1] -cmatch '^ESBUILD_CLOSED ([1-9][0-9]{0,9})$' -and [long]$Matches[1] -ne $pidObserved) {
            $servicePid = [long]$Matches[1]
        }
    } catch { $reason ??= 'InvalidControllerOutput' }
}
if ($null -eq $servicePid) { $reason ??= 'BuildToolClosureUnknown' }
$bundleFact = $null
if (-not $reason) {
    try {
        Assert-Source
        Assert-PhysicalD $bundle
        $resultFiles = @(Get-ChildItem -LiteralPath $bundle -Force)
        if ($resultFiles.Count -ne 1 -or $resultFiles[0].Name -cnotmatch '^inspection-controller-[a-f0-9-]{36}\.mjs$' -or
            $resultFiles[0].PSIsContainer -or $resultFiles[0].Length -gt 256KB -or
            (Measure-Tree $scratch 128) -gt 64KB -or
            (Measure-Tree $group 4096) - (Measure-Tree $packet 256) -ne $d09Before) { throw 'Postflight' }
        if ($lines.Count -ne 3 -or
            $lines[0] -cne 'PASS: inspection context is atomic across observer, revision, story and Play changes; delayed and wrong-privacy replies are fenced.' -or
            $lines[1] -cne 'PASS: removed-field prior provenance and permitted turn sources; event/message routing; hidden-cause refusal; Return to Play and story/lens parameter clearing.') {
            throw 'UnexpectedCheckOutput'
        }
        $bundleFact = @{ name = $resultFiles[0].Name; bytes = $resultFiles[0].Length; sha256 = File-Sha $resultFiles[0].FullName }
    } catch {
        $reason = 'PostflightRefused'
    }
}
Write-Record 'result.json' ([ordered]@{
    kind = 'd05_inspection_431_result_v1'
    testHead = $head
    ownerSha256 = $ownerHash
    stageSha256 = $stageHash
    passed = $null -eq $reason
    reason = $reason
    pid = $pidObserved
    directChildAndPipesClosed = $closed
    esbuildPid = $servicePid
    esbuildClosureReported = $null -ne $servicePid
    quarantineRequired = -not $closed -or $null -eq $servicePid
    stdinClosed = $stdinClosed
    stdoutEof = $eof[0]
    stderrEof = $eof[1]
    stdoutReleased = $readersReleased[0]
    stderrReleased = $readersReleased[1]
    processDisposed = $disposed
    killRequested = $killRequested
    processTreeContained = $false
    exitCode = $exitCode
    elapsedMs = $clock.ElapsedMilliseconds
    bundle = $bundleFact
    logs = $logs
    packetBytesBeforeResult = Measure-Tree $packet 256
})
if ($reason) { throw $reason }
