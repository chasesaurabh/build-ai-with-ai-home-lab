# PowerShell 7; run from the repository root. Downloads a local model; no GPU/API key.
[CmdletBinding()]
param(
    [ValidateRange(1024,65535)][int]$ModelPort = 18134,
    [ValidateRange(1024,65535)][int]$AppPort = 18097,
    [ValidatePattern('^[a-z0-9][a-z0-9-]+$')][string]$ModelVolume = 'build-ai-starter-models',
    [string]$OutputDirectory = './results/model-first-run',
    [switch]$KeepRunning
)
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'Use PowerShell 7.' }
if ($ModelPort -eq $AppPort) { throw 'Use different model and application ports.' }
$out = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path $out) { throw "Evidence directory exists: $out. Choose a new directory." }
New-Item -ItemType Directory -Path $out | Out-Null
$network = 'build-ai-starter-network'
$serverName = 'build-ai-starter-model'
$appName = 'build-ai-starter-intake'
$model = 'qwen3:4b-instruct-2507-q4_K_M'
$expectedModelDigest = '0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0'
$image = 'ollama/ollama:0.40.12@sha256:20d1bbfbabe1c97ba4b16301f08a20d8484bcf77047742a3cb71c613d8e12d0b'
$serverId = $null
$appId = $null
$networkId = $null
$record = [ordered]@{ started_utc = [DateTime]::UtcNow.ToString('o'); model = $model; image = $image; result = 'running' }
function DockerChecked {
    param([string[]]$Arguments)
    $value = & docker @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker failed: $($Arguments[0])" }
    return $value
}
function SaveJson($Name, $Value) {
    $Value | ConvertTo-Json -Depth 30 | Set-Content (Join-Path $out "$Name.json") -Encoding utf8
}
function WaitFor($Url) {
    for ($i = 0; $i -lt 60; $i++) {
        try { return Invoke-RestMethod $Url -TimeoutSec 2 } catch { Start-Sleep -Milliseconds 500 }
    }
    throw "Not ready: $Url"
}
function SendExample($Name) {
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $body = @{ description = 'The backup service is offline.' } | ConvertTo-Json
    $response = Invoke-WebRequest "http://127.0.0.1:$AppPort/v1/intake" -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 190 -SkipHttpErrorCheck
    $watch.Stop()
    $result = @{ status = [int]$response.StatusCode; seconds = $watch.Elapsed.TotalSeconds; body = $response.Content | ConvertFrom-Json }
    SaveJson $Name $result
    return $result
}
try {
    $record.docker = (DockerChecked @('version','--format','{{json .Server}}')) | ConvertFrom-Json
    $record.engine = (DockerChecked @('info','--format','{{json .}}')) | ConvertFrom-Json | Select-Object OSType,Architecture,NCPU,MemTotal
    if ($record.engine.OSType -ne 'linux') { throw 'Use a Linux-container Docker engine.' }
    foreach ($name in @($serverName,$appName)) {
        if (DockerChecked @('ps','-aq','--filter',"name=^/$name$")) { throw "Container exists: $name. Inspect it first." }
    }
    if (DockerChecked @('network','ls','-q','--filter',"name=^$network$")) { throw "Network exists: $network. Inspect it first." }
    $record.model_volume_preexisted = [bool](DockerChecked @('volume','ls','-q','--filter',"name=^$ModelVolume$"))
    DockerChecked @('pull',$image)
    SaveJson 'server-image' ((DockerChecked @('image','inspect',$image)) | ConvertFrom-Json)
    DockerChecked @('volume','create',$ModelVolume)
    $networkId = DockerChecked @('network','create',$network)
    $serverId = DockerChecked @('create','--name',$serverName,'--network',$network,
        '--cpus','8','--memory','6g','--memory-swap','6g',
        '-e','OLLAMA_NO_CLOUD=1','-e','OLLAMA_CONTEXT_LENGTH=4096','-e','OLLAMA_NUM_PARALLEL=1',
        '-p',"127.0.0.1:${ModelPort}:11434",'-v',"${ModelVolume}:/root/.ollama",$image)
    DockerChecked @('start',$serverId)
    SaveJson 'server-version' (WaitFor "http://127.0.0.1:$ModelPort/api/version")
    DockerChecked @('exec',$serverId,'ollama','pull',$model)
    $listing = Invoke-RestMethod "http://127.0.0.1:$ModelPort/v1/models" -TimeoutSec 5
    SaveJson 'model-listing' $listing
    if ($model -notin $listing.data.id) { throw 'Expected exact model ID missing.' }
    $tags = Invoke-RestMethod "http://127.0.0.1:$ModelPort/api/tags" -TimeoutSec 5
    SaveJson 'model-tags' $tags
    if (($tags.models | Where-Object name -EQ $model).digest -ne $expectedModelDigest) {
        throw 'The model tag no longer matches the recorded manifest digest. Review the new artifact before changing the expected digest.'
    }
    $project = Join-Path $PSScriptRoot '../project-1-intake-service'
    DockerChecked @('build','--target','runtime','-t','build-ai-intake:starter',$project)
    SaveJson 'application-image' ((DockerChecked @('image','inspect','build-ai-intake:starter')) | ConvertFrom-Json)
    $appId = DockerChecked @('create','--name',$appName,'--network',$network,
        '--read-only','--tmpfs','/tmp','--cap-drop','ALL','--security-opt','no-new-privileges:true',
        '-e','APP_ADAPTER=local','-e',"MODEL_BASE_URL=http://${serverName}:11434",
        '-e',"MODEL_ID=$model",'-e','MODEL_TIMEOUT_SECONDS=180',
        '-p',"127.0.0.1:${AppPort}:8000",'build-ai-intake:starter')
    DockerChecked @('start',$appId)
    SaveJson 'ready-before' (WaitFor "http://127.0.0.1:$AppPort/ready")
    $first = SendExample 'request-before'
    if ($first.status -ne 200 -or $first.body.category -ne 'availability' -or $first.body.urgency -ne 'high' -or
        $first.body.next_step -ne 'escalate' -or $first.body.affected_system -ne 'backup service' -or
        $first.body.requires_human_review -ne $true) { throw 'Representative model request failed the application contract.' }
    SaveJson 'model-loaded' (Invoke-RestMethod "http://127.0.0.1:$ModelPort/api/ps" -TimeoutSec 5)
    DockerChecked @('stats','--no-stream','--format','{{json .}}',$serverId,$appId) | Set-Content (Join-Path $out 'resource-snapshot.jsonl')
    DockerChecked @('stop',$serverId)
    $readyDown = Invoke-WebRequest "http://127.0.0.1:$AppPort/ready" -SkipHttpErrorCheck -TimeoutSec 10
    $healthDown = Invoke-WebRequest "http://127.0.0.1:$AppPort/health" -SkipHttpErrorCheck -TimeoutSec 5
    SaveJson 'provider-stopped' @{ready_status=[int]$readyDown.StatusCode; health_status=[int]$healthDown.StatusCode}
    $failed = SendExample 'request-provider-stopped'
    if ($readyDown.StatusCode -ne 503 -or $healthDown.StatusCode -ne 200 -or $failed.status -ne 503) { throw 'Unexpected stopped-provider behavior.' }
    DockerChecked @('start',$serverId)
    SaveJson 'ready-after' (WaitFor "http://127.0.0.1:$AppPort/ready")
    $after = SendExample 'request-after'
    if ($after.status -ne 200 -or $after.body.urgency -ne 'high' -or $after.body.next_step -ne 'escalate' -or $after.body.requires_human_review -ne $true) { throw 'Recovery request failed.' }
    $record.result = 'pass'
} catch {
    $record.result = 'fail'
    $record.error = $_.Exception.Message
    throw
} finally {
    $retainServices = $KeepRunning -and $record.result -eq 'pass'
    foreach ($entry in @(@('application',$appId),@('server',$serverId))) {
        if ($entry[1]) {
            & docker logs $entry[1] 2>&1 | Set-Content (Join-Path $out ($entry[0]+'-container.log'))
            if (-not $retainServices) {
                & docker rm -f $entry[1]
                if ($LASTEXITCODE -ne 0) { Write-Warning "Inspect cleanup for $($entry[1])." }
            }
        }
    }
    if ($networkId -and -not $retainServices) { & docker network rm $networkId }
    $record.finished_utc = [DateTime]::UtcNow.ToString('o')
    $record.model_volume_retained = $ModelVolume
    $record.services_retained = [bool]$retainServices
    SaveJson 'result' $record
}
Write-Output "PASS: local model, validated request, provider failure and recovery. Evidence: $out"
if ($retainServices) {
    Write-Output "Services remain running by request. Model: http://127.0.0.1:$ModelPort; application: http://127.0.0.1:$AppPort. See docs/local-model-starter.md for cleanup."
} else {
    Write-Output "Model files remain in Docker volume $ModelVolume; the two exercise containers and network were removed."
}
