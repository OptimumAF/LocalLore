param(
    [Parameter(Mandatory = $true)][string]$SourceDir,
    [Parameter(Mandatory = $true)][string]$BuildDir,
    [Parameter(Mandatory = $true)][string]$CmakePath,
    [string]$VisualStudioPath = 'C:/Program Files/Microsoft Visual Studio/2022/Community',
    [switch]$SchemaTest
)
$ErrorActionPreference = 'Stop'
$taskSource = (Resolve-Path -LiteralPath $SourceDir).Path
$taskCmake = (Resolve-Path -LiteralPath $CmakePath).Path
$taskNinja = Join-Path (Split-Path -Parent $taskCmake) 'ninja.exe'
if (-not (Test-Path -LiteralPath $taskNinja)) { throw 'Ninja must accompany CMake' }
Import-Module (Join-Path $VisualStudioPath 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $VisualStudioPath -SkipAutomaticLocation -Arch amd64 -HostArch amd64
& $taskCmake -S $PSScriptRoot -B $BuildDir -G Ninja "-DCMAKE_MAKE_PROGRAM=$taskNinja" "-DLLAMA_SOURCE_DIR=$taskSource" -DCMAKE_BUILD_TYPE=Release
if ($LASTEXITCODE -ne 0) { throw 'llama worker configuration failed' }
& $taskCmake --build $BuildDir --target locallore-llama-worker --parallel 4
if ($LASTEXITCODE -ne 0) { throw 'llama worker build failed' }
if ($SchemaTest) {
    & $taskCmake --build $BuildDir --target locallore-schema-order-test --parallel 2
    if ($LASTEXITCODE -ne 0) { throw 'schema ordering test build failed' }
    & (Join-Path $BuildDir 'locallore-schema-order-test.exe')
    if ($LASTEXITCODE -ne 0) { throw 'schema ordering test failed' }
    & $taskCmake --build $BuildDir --target locallore-worker-launch-test --parallel 2
    if ($LASTEXITCODE -ne 0) { throw 'worker launch test build failed' }
    & (Join-Path $BuildDir 'locallore-worker-launch-test.exe')
    if ($LASTEXITCODE -ne 0) { throw 'worker launch test failed' }
}
