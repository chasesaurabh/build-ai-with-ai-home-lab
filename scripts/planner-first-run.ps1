# PowerShell 7. Operator-run synthetic package and disposable harness; no model/GPU.
[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port = 18096, [string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$containerId = $null
$containerName = 'build-ai-planner-first-run'
function Docker-Checked {
    param([string[]]$DockerArguments)
    & docker @DockerArguments
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed: $($DockerArguments[0])" }
}
function Wait-ForHealth {
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        try {
            if ((Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 2).status -eq 'ok') { return }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    throw 'The disposable target did not become healthy.'
}
function New-Target {
    param([string]$Candidate)
    Docker-Checked @('create','--name',$containerName,'--read-only','--tmpfs','/tmp',
        '--cap-drop','ALL','--security-opt','no-new-privileges:true',
        '--mount',"type=bind,source=$taskOutput,target=/review,readonly",
        '-e',"CONFIG_PATH=/review/$Candidate",'-p',"127.0.0.1:${Port}:8000",'build-ai-planner:first-run')
}
if ((Docker-Checked @('info','--format','{{.OSType}}')) -ne 'linux') { throw 'A running Linux-container Docker engine is required.' }
if ((Docker-Checked @('ps','-aq','--filter',"name=^/$containerName$"))) { throw "Container $containerName already exists; inspect it before retrying." }
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $PSScriptRoot "../results/planner-first-run-$([DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss'))-$([Guid]::NewGuid().ToString('N').Substring(0,8))"
}
$taskOutput = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $taskOutput) { throw 'Output directory already exists; choose a new location.' }
New-Item -ItemType Directory -Path $taskOutput | Out-Null
@{changes=@(@{field='replica_count';after=3},@{field='image_tag';after='registry.home.invalid/photo-api:1.4.3'})} |
    ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $taskOutput 'desired.json')
Push-Location (Join-Path $PSScriptRoot '../project-4-sandboxed-change-planner')
try {
    Docker-Checked @('build','--target','test','-t','build-ai-planner:first-run-test','.')
    Docker-Checked @('run','--rm','--network','none','build-ai-planner:first-run-test')
    Docker-Checked @('run','--rm','--network','none','--read-only','--tmpfs','/tmp',
        '--mount',"type=bind,source=$taskOutput,target=/review",
        'build-ai-planner:first-run-test','python','-m','app.cli','--proposal-file','/review/desired.json','--output','/review/package')
    $package = Get-Content -Raw (Join-Path $taskOutput 'package/approval-package.json') | ConvertFrom-Json
    $manifest = Get-Content -Raw (Join-Path $taskOutput 'package/artifact-manifest.json') | ConvertFrom-Json
    foreach ($entry in $manifest.files.PSObject.Properties) {
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $taskOutput "package/$($entry.Name)")).Hash.ToLowerInvariant()
        if ($hash -ne $entry.Value) { throw "Artifact hash mismatch: $($entry.Name)" }
    }
    if ($package.apply_capability -ne 'absent' -or $package.status -ne 'awaiting_human_approval') { throw 'Review-only package boundary failed.' }
    $package | ConvertTo-Json -Depth 8
    Docker-Checked @('build','--target','sandbox-runtime','-t','build-ai-planner:first-run','.')
    $containerId = New-Target 'package/proposed-config.json'
    Docker-Checked @('start',$containerId)
    Wait-ForHealth
    $base="http://127.0.0.1:$Port"
    if ((Invoke-RestMethod "$base/ready").status -ne 'ready') { throw 'Candidate is not ready.' }
    $observed=Invoke-RestMethod "$base/config"
    if ($observed.replica_count -ne 3 -or $observed.image_tag -ne 'registry.home.invalid/photo-api:1.4.3') { throw 'Target configuration differs from the proposed values.' }
    Docker-Checked @('restart',$containerId)
    Wait-ForHealth
    if ((Invoke-RestMethod "$base/config").replica_count -ne 3) { throw 'Candidate did not survive restart.' }
    Docker-Checked @('rm','-f',$containerId); $containerId=$null
    $invalid=$package.proposed_config | ConvertTo-Json | ConvertFrom-Json
    $invalid.replica_count=99
    $invalid | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $taskOutput 'invalid-config.json')
    $containerId=New-Target 'invalid-config.json'
    Docker-Checked @('start',$containerId)
    $state=$null
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        $state=(Docker-Checked @('inspect','--format','{{json .State}}',$containerId)) | ConvertFrom-Json
        if (-not $state.Running) { break }
        Start-Sleep -Milliseconds 200
    }
    if ($state.Running -or $state.ExitCode -ne 1) { throw 'Invalid candidate was not rejected at startup with exit 1.' }
    & docker logs $containerId *> (Join-Path $taskOutput 'expected-invalid-startup.log')
    Docker-Checked @('rm',$containerId); $containerId=$null
    $containerId=New-Target 'package/rollback-config.json'
    Docker-Checked @('start',$containerId)
    Wait-ForHealth
    $restored=Invoke-RestMethod "$base/config"
    foreach ($field in 'service_id','image_tag','replica_count','request_timeout_seconds','maintenance_mode') {
        if ($restored.$field -cne $package.rollback_config.$field) { throw "Rollback mismatch: $field" }
    }
    if ((Invoke-RestMethod "$base/ready").status -ne 'ready') { throw 'Restored baseline is not ready.' }
    Write-Output "PASS: review package, hashes, disposable candidate, restart, invalid-candidate rejection, and exact configuration restoration. Artifacts: $taskOutput"
} finally {
    if ($containerId) {
        & docker rm -f $containerId
        if ($LASTEXITCODE -ne 0) { Write-Warning "Cleanup failed; inspect container $containerId." }
    }
    Pop-Location
}
