# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
# Invoke only from the exact retained evidence copy under a separately admitted decision.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$env:TEMP = 'D:/Dev/_Temp'
$env:TMP = $env:TEMP
$packet = [IO.Path]::GetFullPath($PSScriptRoot)
$artifacts = Split-Path -Parent $packet
$base = Split-Path -Parent $artifacts
$repo = Join-Path $base 'source-desktop-fork-review'
$source = Join-Path $repo 'native/llama-worker'
$node = Join-Path $base 'd09-build-security/node-v24.22.1-win-x64/node.exe'
$target = Join-Path $base 'd07-comparison-reader-native-target'
$normal = Join-Path $target 'debug/locallore-desktop-spike.exe'
$stem = 'b2-worker-artifact-compile-stack-v1-code-'
$collector = Join-Path $packet ($stem + 'collector.mjs')
$utf8 = [Text.UTF8Encoding]::new($false, $true)
$revision = 'a13dc2448f774c93f6ea5994fcfd70ec6674a168'
$priorRoster = '39ae1d968b71aed86061f40d9cc308b21bd28aef37db5064db6aaf6320517e7c'
$nodeHash = 'd702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5'
$normalHash = '7a68992bc35d2e778d71e8db80ef4050a281d65d785a054e77abb569aadaf192'
$prepared = @('owner.json','source-review.json','supervisor.ps1','collector.mjs')
$runLimits = [ordered]@{ 'START.json'=1024; 'stdout.bin'=4096; 'stderr.bin'=4096; 'process.json'=4096; 'result.json'=2048; 'STOP.json'=2048 }
$prepLimits = [ordered]@{ 'owner.json'=2048; 'source-review.json'=2048; 'supervisor.ps1'=20480; 'collector.mjs'=4096 }
$sourcePins = [ordered]@{
    'library_inputs.mjs' = @(17906, 'c6bd3309db944bf431838fd1e98670a6e8ed937f104e66a31735c5cc1372c5dc')
    'worker_artifact_recipe_v1.mjs' = @(6477, '93269f12448f4539c8b1e1ec035cd0d8da522740eff979b38b525db02fbb622b')
    'worker_artifact_output_roots_v1.mjs' = @(15919, 'fc79d4f73e10d2ab628162f08cf95d0c4746017df50eaa4813ce53f43fee5642')
    'worker_artifact_held_outputs_v1.mjs' = @(14590, '9a6147474ad135cce60268d2d80baedce2e2773010b546d33621e93463cdddde')
    'worker_artifact_held_outputs_v1_first.mjs' = @(28144, '7c0aacf20ab82fc566a45c1c3bf404e9a85fd2b3ef40a5e423db19a55e8954ed')
    'worker_artifact_compile_observation_v1.mjs' = @(20678, '8b5b08bb13fb6a18981250eb1b77a12f17cd8b9fdb9d53b983d20ad37f99a75e')
    'worker_artifact_compile_observation_v1_first.mjs' = @(29208, '487c011f586367d766bd6d945cf7d8d0121c069372039ed02e54c6869b60ed56')
    'worker_artifact_compile_host_v1.mjs' = @(12498, 'c194f981d7c07f4036ff7ca202216b8c9ebc60247cdb7f4d2b4e4181c8a51b1f')
    'worker_artifact_compile_supervisor_v1.mjs' = @(22022, '12dd4ded00b6fd6dfe5ff23b8f829e04b7f9b43c61e7065428e963bcbe80353a')
    'worker_artifact_compile_attempt_v1.mjs' = @(13605, '5ac0668f773a6aeffe0e30d09c7ef243276a4e878e0221ddf06836226d406601')
    'worker_artifact_compile_attempt_v1_first.mjs' = @(6737, '41349dbeb1e29d5d2405f918e43fdfff0e605f03a432dc0e10dfe9bc57d30834')
}

function Physical([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith('D:\', [StringComparison]::OrdinalIgnoreCase)) { throw 'PhysicalD' }
    $current = $full
    while ($current) {
        if ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse' }
        $current = [IO.Path]::GetDirectoryName($current)
    }
    return $full
}

function HashFile([string]$Path) {
    $full = Physical $Path
    if (-not [IO.File]::Exists($full)) { throw 'FileRequired' }
    return (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
}

function HashBytes([byte[]]$Bytes) {
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}

function TreeBytes([string]$Root) {
    $full = Physical $Root
    $count = 0
    $total = 0L
    foreach ($entry in Get-ChildItem -LiteralPath $full -Force -Recurse) {
        if (++$count -gt 200000 -or ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'TreeBoundary' }
        if (-not $entry.PSIsContainer) { $total += $entry.Length }
    }
    return $total
}

function Audit([bool]$Active, [int]$Reserve) {
    $old = [Collections.Generic.List[string]]::new()
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $own = 0L
    foreach ($entry in Get-ChildItem -LiteralPath (Physical $packet) -Force) {
        if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'EvidenceReparse' }
        if ($entry.Name.StartsWith($stem, [StringComparison]::OrdinalIgnoreCase)) {
            if ($entry.PSIsContainer -or -not $entry.Name.StartsWith($stem, [StringComparison]::Ordinal)) { throw 'OwnLeaf' }
            $suffix = $entry.Name.Substring($stem.Length)
            $limit = if ($prepLimits.Contains($suffix)) { $prepLimits[$suffix] }
                     elseif ($Active -and $runLimits.Contains($suffix)) { $runLimits[$suffix] }
                     else { throw 'OwnLeaf' }
            if ($entry.Length -gt $limit -or -not $seen.Add($suffix)) { throw 'OwnLimit' }
            $own += $entry.Length
        } elseif (-not $entry.PSIsContainer) {
            $old.Add($entry.Name)
        } elseif ($entry.Name -cnotmatch '^p-[0-9a-f-]{36}$') {
            throw 'PriorDirectory'
        }
    }
    if ($old.Count -ne 877 -or @($prepared | Where-Object { -not $seen.Contains($_) }).Count) { throw 'PriorRoster' }
    $names = $old.ToArray()
    [Array]::Sort($names,[StringComparer]::Ordinal)
    $sha = [Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
    $metadata = 42616L + $own
    try {
        foreach ($name in $names) {
            $file = Get-Item -LiteralPath (Join-Path $packet $name) -Force
            if ($file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'PriorRoster' }
            $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            $sha.AppendData($utf8.GetBytes($name + [char]9 + $file.Length + [char]9 + $hash + [char]10))
            if ($name -cne 'normal-1779b0bd.js') { $metadata += $file.Length }
        }
        if ([Convert]::ToHexString($sha.GetHashAndReset()).ToLowerInvariant() -cne $priorRoster) { throw 'PriorRoster' }
    } finally { $sha.Dispose() }

    $group = TreeBytes $packet
    $oldBytes = TreeBytes (Join-Path $artifacts 'd08-fork-checks-20261030-v1')
    $browser = TreeBytes (Join-Path $artifacts 'd08-browser-20261030-v1')
    $targetBytes = TreeBytes $target
    $runtime = 0L
    foreach ($entry in Get-ChildItem -LiteralPath (Physical $env:TEMP) -Force) {
        if ($entry.Name -match '^(locallore-protocol-fixture-|locallore-runtime-|locallore-runtime-resource-)') {
            $runtime += TreeBytes $entry.FullName
        }
    }
    $joint = $group + $browser + 560014573 + 79500962 + $oldBytes + 671744 + $runtime
    if ($metadata -ne 3060788 + $own -or $group -ne 55230062 + $own -or $joint -ne 737551587 + $own -or
        $oldBytes -ne 549989 -or $browser -ne 41584016 -or $targetBytes -ne 12356228504 -or $runtime -ne 241 -or
        $metadata + $Reserve -gt 3125248 -or $group + 31791 + $Reserve -gt 67108864 -or
        $joint + 31791 + $Reserve -gt 759169024 -or [IO.DriveInfo]::new('D').AvailableFreeSpace -lt 1048576) {
        throw 'StorageBoundary'
    }
    return [ordered]@{ metadata=$metadata; group=$group; joint=$joint; target=$targetBytes; runtime=$runtime }
}

function ReadRecord([string]$Leaf) {
    $path = Physical (Join-Path $packet ($stem + $Leaf))
    $file = Get-Item -LiteralPath $path
    if ($file.PSIsContainer -or $file.Length -lt 2 -or $file.Length -gt $prepLimits[$Leaf]) { throw 'OwnerRecord' }
    return ($utf8.GetString([IO.File]::ReadAllBytes($path)) | ConvertFrom-Json -AsHashtable -ErrorAction Stop)
}

function ExactKeys($Value, [string[]]$Expected) {
    if ($Value -isnot [System.Collections.IDictionary] -or $Value.Count -ne $Expected.Length -or
        @($Value.Keys | Where-Object { $_ -cnotin $Expected }).Count) { throw 'RecordShape' }
}

function Save([string]$Leaf,[byte[]]$Bytes) {
    if (-not $runLimits.Contains($Leaf) -or $Bytes.Length -gt $runLimits[$Leaf]) { throw 'RecordLimit' }
    $null = Audit $true $Bytes.Length
    $path = Join-Path $packet ($stem + $Leaf)
    $file = [IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $file.Write($Bytes,0,$Bytes.Length); $file.Flush($true) } finally { $file.Dispose() }
    if ((HashFile $path) -cne (HashBytes $Bytes)) { throw 'Readback' }
}

function SaveJson([string]$Leaf,$Data) {
    Save $Leaf ($utf8.GetBytes(($Data | ConvertTo-Json -Compress -Depth 10) + [char]10))
}

function GuardSources {
    if ((HashFile $node) -cne $nodeHash -or (HashFile $normal) -cne $normalHash -or
        (HashFile $PSCommandPath) -cne $review.supervisor -or (HashFile $collector) -cne $review.collector -or
        (HashFile (Join-Path $source 'worker_artifact_compile_stack_v1_code_supervisor.ps1')) -cne $review.supervisor -or
        (HashFile (Join-Path $source 'worker_artifact_compile_stack_v1_code_first.mjs')) -cne $review.collector -or
        (HashFile (Join-Path $packet ($stem+'owner.json'))) -cne $review.owner -or
        (HashFile (Join-Path $packet ($stem+'source-review.json'))) -cne $reviewHash) { throw 'PinnedSource' }
    foreach ($name in $sourcePins.Keys) {
        $file = Get-Item -LiteralPath (Physical (Join-Path $source $name))
        if ($file.Length -ne $sourcePins[$name][0] -or (HashFile $file.FullName) -cne $sourcePins[$name][1]) {
            throw 'PinnedSource'
        }
    }
}

function Capture {
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $node
    $info.WorkingDirectory = $repo
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.Environment.Clear()
    $windows = Split-Path -Parent ([Environment]::SystemDirectory)
    $info.Environment['SystemRoot'] = $windows
    $info.Environment['WINDIR'] = $windows
    $info.Environment['SystemDrive'] = [IO.Path]::GetPathRoot($windows).TrimEnd('\')
    $info.Environment['PATH'] = [Environment]::SystemDirectory
    $info.Environment['TEMP'] = $env:TEMP
    $info.Environment['TMP'] = $env:TMP
    $info.ArgumentList.Add('--permission')
    $info.ArgumentList.Add('--allow-fs-read=' + [IO.Path]::GetFullPath($collector))
    foreach ($name in $sourcePins.Keys) { $info.ArgumentList.Add('--allow-fs-read=' + [IO.Path]::GetFullPath((Join-Path $source $name))) }
    $info.ArgumentList.Add([IO.Path]::GetFullPath($collector))

    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $info
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $startedUtc = [DateTime]::UtcNow.ToString('o')
    $id = $null; $code = $null; $exited = $false; $handleClosed = $false; $inputClosed = $false
    $timedOut = $false; $overflow = $false; $ioError = $false; $killAttempted = $false; $killAccepted = $false
    $drainDeadline = 35000L
    $streams = @()
    $buffers = @([byte[]]::new(4097),[byte[]]::new(4097))
    $captures = @([IO.MemoryStream]::new(),[IO.MemoryStream]::new())
    $eof = @($false,$false); $done = @($false,$false); $closed = @($false,$false); $reads = @($null,$null)
    try {
        if (-not $process.Start()) { throw 'Spawn' }
        $id = $process.Id
        $streams = @($process.StandardOutput.BaseStream,$process.StandardError.BaseStream)
        $process.StandardInput.Close()
        $inputClosed = $true
        for ($i=0;$i -lt 2;$i++) { $reads[$i]=$streams[$i].ReadAsync($buffers[$i],0,$buffers[$i].Length) }
        while ($true) {
            for ($i=0;$i -lt 2;$i++) {
                if ($done[$i] -or -not $reads[$i].IsCompleted) { continue }
                try { $n=$reads[$i].GetAwaiter().GetResult() } catch { $ioError=$true;$done[$i]=$true;continue }
                if ($n -eq 0) { $eof[$i]=$true;$done[$i]=$true;continue }
                $take=[Math]::Min($n,4096-[int]$captures[$i].Length)
                if ($take -gt 0) { $captures[$i].Write($buffers[$i],0,$take) }
                if ($take -ne $n) { $overflow=$true;$done[$i]=$true;continue }
                $reads[$i]=$streams[$i].ReadAsync($buffers[$i],0,$buffers[$i].Length)
            }
            if (-not $exited -and $process.HasExited) { $code=$process.ExitCode;$exited=$true }
            $now = $timer.ElapsedMilliseconds
            if ($now -ge 30000) { $timedOut=$true }
            if ($exited -and $done[0] -and $done[1]) { break }
            if (($timedOut -or $overflow -or $ioError) -and -not $killAttempted -and -not $exited) {
                $killAttempted=$true
                $drainDeadline=[Math]::Min($now,30000L)+5000
                try { $process.Kill();$killAccepted=$true } catch { $ioError=$true }
            }
            if ($now -ge $drainDeadline) { break }
            Start-Sleep -Milliseconds 10
        }
    } catch {
        $ioError = $true
        if ($null -ne $id -and -not $exited -and -not $killAttempted) {
            $killAttempted=$true
            try {
                if (-not $process.HasExited) { $process.Kill();$killAccepted=$true }
                if ($process.WaitForExit([int][Math]::Max(0,[Math]::Min(5000,35000-$timer.ElapsedMilliseconds)))) {
                    $code=$process.ExitCode;$exited=$true
                }
            } catch { $ioError=$true }
        }
    } finally {
        for ($i=0;$i -lt $streams.Count;$i++) {
            try { $streams[$i].Dispose();$closed[$i]=$true } catch { $ioError=$true }
        }
        try { $process.Dispose();$handleClosed=$true } catch { $ioError=$true }
    }
    $timer.Stop()
    if ($timer.ElapsedMilliseconds -ge 30000) { $timedOut=$true }
    $out = $captures[0].ToArray();$err = $captures[1].ToArray()
    foreach ($capture in $captures) { $capture.Dispose() }
    return [ordered]@{
        stdout=$out;stderr=$err
        facts=[ordered]@{ pid=$id;exitCode=$code;exited=$exited;processHandleClosed=$handleClosed;stdinClosed=$inputClosed
            stdoutEof=$eof[0];stderrEof=$eof[1];stdoutClosed=$closed[0];stderrClosed=$closed[1]
            knownClosed=($exited -and $handleClosed -and $inputClosed -and $eof[0] -and $eof[1] -and $closed[0] -and $closed[1] -and -not $ioError)
            timedOut=$timedOut;overflow=$overflow;ioError=$ioError;killAttempted=$killAttempted;killAccepted=$killAccepted
            processTreeContained=$false;beganUtc=$startedUtc;endedUtc=[DateTime]::UtcNow.ToString('o');elapsedMs=$timer.ElapsedMilliseconds }
    }
}

if ((Split-Path -Leaf $packet) -cne 'd08-fork-native-20261030-v1' -or
    (Split-Path -Leaf $artifacts) -cne 'author-integration-artifacts' -or
    [IO.Path]::GetFullPath($PSCommandPath) -cne (Join-Path $packet ($stem+'supervisor.ps1')) -or
    $PSVersionTable.PSVersion.ToString() -ne '7.6.9' -or [Environment]::Version.ToString() -ne '10.0.14' -or
    [Environment]::OSVersion.Version.ToString() -ne '10.0.26300.0') { throw 'PacketEnvironment' }

$owner = ReadRecord 'owner.json'
$review = ReadRecord 'source-review.json'
$reviewHash = HashFile (Join-Path $packet ($stem+'source-review.json'))
ExactKeys $owner @('version','kind','decision','approved','cap','runCount','roster','testRevision','codeOnly')
ExactKeys $review @('version','kind','owner','collector','supervisor','testRevision','release','independent','retained')
if ($owner.version -ne 1 -or $owner.kind -cne 'compile_stack_code_owner_v1' -or
    $owner.approved -isnot [bool] -or -not $owner.approved -or $owner.codeOnly -isnot [bool] -or -not $owner.codeOnly -or
    $owner.decision -isnot [string] -or $owner.decision.Length -lt 1 -or $owner.decision.Length -gt 256 -or
    $owner.cap -ne 3125248 -or $owner.runCount -ne 1 -or $owner.roster -cne $priorRoster -or
    $owner.testRevision -cne $revision -or $review.version -ne 1 -or $review.kind -cne 'compile_stack_code_review_v1' -or
    $review.independent -isnot [bool] -or -not $review.independent -or $review.retained -isnot [bool] -or -not $review.retained -or
    $review.testRevision -cne $revision -or $review.release -cnotmatch '\A[0-9a-f]{40}\z') { throw 'DecisionBinding' }

$launched = $false
$startHash = $null
try {
    GuardSources
    $before = Audit $false 17408
    SaveJson 'START.json' ([ordered]@{version=1;kind='compile_stack_code_start_v1';owner=$review.owner;review=$reviewHash
        supervisor=$review.supervisor;collector=$review.collector;testRevision=$revision;release=$review.release;parentPid=$PID})
    $startPath = Join-Path $packet ($stem+'START.json')
    $startHash = HashFile $startPath
    $null = Audit $true (17408-(Get-Item -LiteralPath $startPath).Length)
    GuardSources
    if ((HashFile $startPath) -cne $startHash) { throw 'StartChanged' }

    $launched = $true
    $capture = Capture
    Save 'stdout.bin' $capture.stdout
    Save 'stderr.bin' $capture.stderr
    $facts = $capture.facts
    SaveJson 'process.json' ([ordered]@{version=1;kind='compile_stack_code_process_v1';start=$startHash
        facts=$facts;stdoutBytes=$capture.stdout.Length;stderrBytes=$capture.stderr.Length
        stdoutHash=(HashBytes $capture.stdout);stderrHash=(HashBytes $capture.stderr)})
    $expected = @(
        '{"version":1,"kind":"worker_artifact_held_outputs_first_v1","executed":14,"passed":14,"failed":0,"failed_case_ids":[]}',
        '{"version":1,"kind":"worker_artifact_compile_observation_first_v1","executed":11,"passed":11,"failed":0,"failed_case_ids":[]}',
        '{"kind":"compile_attempt_first_v1","groups":12}'
    ) -join [char]10
    if (-not $facts.knownClosed -or $facts.timedOut -or $facts.overflow -or $facts.killAttempted -or
        $facts.exitCode -ne 0 -or $capture.stderr.Length -ne 0 -or
        $utf8.GetString($capture.stdout) -cne ($expected+[char]10)) { throw 'CodeGate' }
    GuardSources
    if ((HashFile $startPath) -cne $startHash) { throw 'StartChanged' }
    $after = Audit $true 4096
    SaveJson 'result.json' ([ordered]@{version=1;kind='compile_stack_code_result_v1';start=$startHash
        process=(HashFile (Join-Path $packet ($stem+'process.json')));groups=@(14,11,12);passed=37
        before=$before;after=$after;nativeQualified=$false})
} catch {
    $failure = $_
    $reason = $failure.Exception.Message
    if ($reason -cnotin @('PhysicalD','Reparse','EvidenceReparse','OwnLeaf','OwnLimit','PriorDirectory',
        'PriorRoster','TreeBoundary','StorageBoundary','PinnedSource','RecordLimit','Readback','StartChanged','CodeGate')) {
        $reason = 'Unhandled'
    }
    try { SaveJson 'STOP.json' ([ordered]@{version=1;kind='compile_stack_code_stop_v1';start=$startHash
        offerAttempted=$launched;review=$reviewHash;parentPid=$PID;reason=$reason}) } catch { }
    throw $failure
}
