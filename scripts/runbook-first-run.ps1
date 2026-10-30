# PowerShell 7: inspect and test synthetic runbooks without a model or GPU.
[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port = 18092)
$ErrorActionPreference = 'Stop'
$containerId = $null
$containerName = 'build-ai-runbook-first-run'
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
Push-Location (Join-Path $PSScriptRoot '../project-2-runbook-assistant')
try {
    Docker-Checked @('build','--target','test','-t','build-ai-runbook:first-run-test','.')
    Docker-Checked @('run','--rm','--network','none','build-ai-runbook:first-run-test')
    Docker-Checked @('build','--target','runtime','-t','build-ai-runbook:first-run','.')
    $containerId = Docker-Checked @('create','--name',$containerName,'--read-only','--tmpfs','/tmp',
        '--cap-drop','ALL','--security-opt','no-new-privileges:true',
        '-e','MODEL_BASE_URL=http://127.0.0.1:9','-e','MODEL_ID=not-configured',
        '-p',"127.0.0.1:${Port}:8000",'build-ai-runbook:first-run')
    Docker-Checked @('start',$containerId)
    Wait-ForHealth
    $base = "http://127.0.0.1:$Port"
    $ready = Invoke-WebRequest "$base/ready" -SkipHttpErrorCheck -TimeoutSec 5
    if ($ready.StatusCode -ne 503) { throw 'Generation must be not-ready without the model.' }
    $body = @{question='What evidence should I collect for degraded storage redundancy?'} | ConvertTo-Json
    $search = Invoke-RestMethod "$base/v1/search" -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 5
    if (-not $search.has_evidence -or 'storage-pool#evidence-collect' -notin $search.hits.passage_id) { throw 'Expected passage was not retrieved.' }
    if ($search.hits.Count -gt 3) { throw 'Retrieval exceeded its bound.' }
    $search | ConvertTo-Json -Depth 5
    $noEvidenceBody = @{question='How can I calibrate a resin printer exposure profile?'} | ConvertTo-Json
    $abstention = Invoke-RestMethod "$base/v1/answer" -Method Post -Body $noEvidenceBody -ContentType 'application/json' -TimeoutSec 5
    if ($abstention.answerable -ne $false -or $abstention.citations.Count -ne 0) { throw 'Empty evidence did not produce abstention.' }
    $unavailable = Invoke-WebRequest "$base/v1/answer" -Method Post -Body $body -ContentType 'application/json' -SkipHttpErrorCheck -TimeoutSec 5
    if ($unavailable.StatusCode -ne 503) { throw 'Generation did not report the unavailable model.' }
    $badBody = @{question='What evidence should I collect for degraded storage redundancy?'; path='../private.md'} | ConvertTo-Json
    $invalid = Invoke-WebRequest "$base/v1/search" -Method Post -Body $badBody -ContentType 'application/json' -SkipHttpErrorCheck -TimeoutSec 5
    if ($invalid.StatusCode -ne 422) { throw 'Unexpected request fields were not rejected.' }
    Docker-Checked @('restart',$containerId)
    Wait-ForHealth
    $after = Invoke-RestMethod "$base/v1/search" -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 5
    if (($after | ConvertTo-Json -Compress -Depth 5) -ne ($search | ConvertTo-Json -Compress -Depth 5)) { throw 'Retrieval changed after restart.' }
    Write-Output 'PASS: corpus tests, search, abstention, provider failure, input rejection, and restart.'
} finally {
    if ($containerId) {
        & docker logs $containerId
        & docker rm -f $containerId
        if ($LASTEXITCODE -ne 0) { Write-Warning "Cleanup failed; inspect container $containerId." }
    }
    Pop-Location
}
