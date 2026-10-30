# Run from PowerShell 7. This exercise uses synthetic data and no model.
[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port = 18088)
$ErrorActionPreference = 'Stop'
$projectPath = Join-Path $PSScriptRoot '../project-1-intake-service'
$containerId = $null
$containerName = 'build-ai-intake-first-run'

function Invoke-DockerChecked {
    param([string[]]$DockerArguments)
    & docker @DockerArguments
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed: $($DockerArguments[0])" }
}

function Wait-ForReady {
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $ready = Invoke-RestMethod "http://127.0.0.1:$Port/ready" -TimeoutSec 2
            if ($ready.status -eq 'ready' -and $ready.adapter -eq 'deterministic') { return }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    throw 'The service did not become ready. Inspect the captured container logs.'
}

# Inspect prerequisites before creating anything. Existing containers are never removed.
$serverOs = Invoke-DockerChecked @('info', '--format', '{{.OSType}}')
if ($serverOs -ne 'linux') { throw 'Use a running Docker engine configured for Linux containers.' }
$existing = Invoke-DockerChecked @('ps', '-aq', '--filter', "name=^/$containerName$")
if ($existing) { throw "Container $containerName already exists; inspect it before retrying." }

Push-Location $projectPath
try {
    Invoke-DockerChecked @('build', '--target', 'test', '-t', 'build-ai-intake:first-run-test', '.')
    Invoke-DockerChecked @('run', '--rm', '--network', 'none', 'build-ai-intake:first-run-test')
    Invoke-DockerChecked @('build', '--target', 'runtime', '-t', 'build-ai-intake:first-run', '.')
    # Create separately so a start failure still has an owned ID for scoped cleanup.
    $containerId = Invoke-DockerChecked @('create', '--name', $containerName,
        '--read-only', '--tmpfs', '/tmp', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges:true', '-e', 'APP_ADAPTER=deterministic',
        '-p', "127.0.0.1:${Port}:8000", 'build-ai-intake:first-run')
    Invoke-DockerChecked @('start', $containerId)
    Wait-ForReady
    $baseUrl = "http://127.0.0.1:$Port"
    $health = Invoke-RestMethod "$baseUrl/health" -TimeoutSec 5
    if ($health.status -ne 'ok') { throw 'Liveness failed.' }
    $body = @{ description = 'The backup service is offline.' } | ConvertTo-Json
    $decision = Invoke-RestMethod "$baseUrl/v1/intake" -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 5
    if ($decision.urgency -ne 'high' -or $decision.next_step -ne 'escalate' -or
        $decision.affected_system -ne 'backup service' -or $decision.requires_human_review -ne $true) {
        throw 'Representative request did not match the expected decision.'
    }
    $decision | ConvertTo-Json -Depth 5
    $badBody = @{ description = 'The backup service is offline.'; urgency = 'low' } | ConvertTo-Json
    $rejected = Invoke-WebRequest "$baseUrl/v1/intake" -Method Post -ContentType 'application/json' -Body $badBody -SkipHttpErrorCheck -TimeoutSec 5
    if ($rejected.StatusCode -ne 422) { throw 'Unexpected input was not rejected with HTTP 422.' }
    Invoke-DockerChecked @('restart', $containerId)
    Wait-ForReady
    $after = Invoke-RestMethod "$baseUrl/v1/intake" -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 5
    if (($after | ConvertTo-Json -Compress) -ne ($decision | ConvertTo-Json -Compress)) {
        throw 'The response changed after restart.'
    }
    Write-Output 'PASS: tests, liveness, readiness, request, rejection, and restart.'
} finally {
    if ($containerId) {
        & docker logs $containerId
        & docker rm -f $containerId
        if ($LASTEXITCODE -ne 0) { Write-Warning "Cleanup failed; inspect container $containerId." }
    }
    Pop-Location
}
