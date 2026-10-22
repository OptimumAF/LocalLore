param(
    [Parameter(Mandatory = $true)][string]$SourceDir,
    [Parameter(Mandatory = $true)][string]$BuildDir,
    [Parameter(Mandatory = $true)][string]$CmakePath,
    [string]$VisualStudioPath = 'C:/Program Files/Microsoft Visual Studio/2022/Community'
)
$ErrorActionPreference = 'Stop'
$taskSource = (Resolve-Path -LiteralPath $SourceDir).Path
$taskCmake = (Resolve-Path -LiteralPath $CmakePath).Path
$taskNinja = Join-Path (Split-Path -Parent $taskCmake) 'ninja.exe'
if (-not (Test-Path -LiteralPath $taskNinja)) { throw 'Ninja must accompany CMake' }
Import-Module (Join-Path $VisualStudioPath 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $VisualStudioPath -SkipAutomaticLocation -Arch amd64 -HostArch amd64
& $taskCmake -S $PSScriptRoot -B $BuildDir -G Ninja "-DCMAKE_MAKE_PROGRAM=$taskNinja" "-DLLAMA_SOURCE_DIR=$taskSource" -DCMAKE_BUILD_TYPE=Release
if ($LASTEXITCODE -ne 0) { throw 'llama spike configuration failed' }
& $taskCmake --build $BuildDir --target locallore-llama-spike --parallel 4
if ($LASTEXITCODE -ne 0) { throw 'llama spike build failed' }
