# PowerShell 7. Synthetic fixture observations; no model or GPU required.
[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port = 18093)
$ErrorActionPreference = 'Stop'
$containerId = $null
$containerName = 'build-ai-diagnostic-first-run'
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
    throw 'The service did not become healthy.'
}
if ((Docker-Checked @('info','--format','{{.OSType}}')) -ne 'linux') { throw 'A running Linux-container Docker engine is required.' }
if ((Docker-Checked @('ps','-aq','--filter',"name=^/$containerName$"))) { throw "Container $containerName already exists; inspect it before retrying." }
Push-Location (Join-Path $PSScriptRoot '../project-3-readonly-diagnostic-agent')
try {
    Docker-Checked @('build','--target','test','-t','build-ai-diagnostic:first-run-test','.')
    Docker-Checked @('run','--rm','--network','none','build-ai-diagnostic:first-run-test')
    Docker-Checked @('build','--target','runtime','-t','build-ai-diagnostic:first-run','.')
    $containerId = Docker-Checked @('create','--name',$containerName,'--read-only','--tmpfs','/tmp',
        '--cap-drop','ALL','--security-opt','no-new-privileges:true',
        '-e','MODEL_BASE_URL=http://127.0.0.1:9','-e','MODEL_ID=not-configured',
        '-p',"127.0.0.1:${Port}:8000",'build-ai-diagnostic:first-run')
    Docker-Checked @('start',$containerId)
    Wait-ForHealth
    $base = "http://127.0.0.1:$Port"
    $ready = Invoke-WebRequest "$base/ready" -SkipHttpErrorCheck -TimeoutSec 5
    if ($ready.StatusCode -ne 503) { throw 'The model path must be not-ready without a model.' }
    $body = @{service='media-server'} | ConvertTo-Json
    $run = Invoke-RestMethod "$base/v1/diagnose-fixed" -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 5
    if ($run.tool_results.Count -ne 3 -or -not $run.report.requires_human_review) { throw 'Expected bounded observation trace was not returned.' }
    if ($run.report.summary -notmatch 'CPU saturation') { throw 'Fixture summary did not reflect its metrics.' }
    foreach ($id in $run.report.evidence_ids) {
        if ($id -notin $run.tool_results.evidence_id) { throw 'Report cited evidence absent from this run.' }
    }
    $run | ConvertTo-Json -Depth 8
    $modelBody = @{service='media-server'; question='Why is the media server slow?'} | ConvertTo-Json
    $unavailable = Invoke-WebRequest "$base/v1/diagnose" -Method Post -Body $modelBody -ContentType 'application/json' -SkipHttpErrorCheck -TimeoutSec 5
    if ($unavailable.StatusCode -ne 503) { throw 'The model path did not report its unavailable provider.' }
    $invalid = Invoke-WebRequest "$base/v1/diagnose-fixed" -Method Post -Body '{"service":"media-server","command":"restart"}' -ContentType 'application/json' -SkipHttpErrorCheck -TimeoutSec 5
    if ($invalid.StatusCode -ne 422) { throw 'An extra action field was not rejected.' }
    Docker-Checked @('restart',$containerId)
    Wait-ForHealth
    $after = Invoke-RestMethod "$base/v1/diagnose-fixed" -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 5
    if ($after.report.summary -ne $run.report.summary) { throw 'The fixture observation summary changed after restart.' }
    for ($i=0; $i -lt 3; $i++) {
        if ($after.tool_results[$i].payload_sha256 -ne $run.tool_results[$i].payload_sha256) { throw 'The observed data changed after restart.' }
        if ($after.tool_results[$i].evidence_id -eq $run.tool_results[$i].evidence_id) { throw 'An observation ID was reused.' }
    }
    Write-Output 'PASS: tests, fixed observations, current-run citations, provider failure, input rejection, restart, stable hashes and fresh IDs.'
} finally {
    if ($containerId) {
        & docker logs $containerId
        & docker rm -f $containerId
        if ($LASTEXITCODE -ne 0) { Write-Warning "Cleanup failed; inspect container $containerId." }
    }
    Pop-Location
}
