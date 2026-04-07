param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$Force,
    [switch]$CleanLogs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSCommandPath
$RunDir = Join-Path $ProjectRoot '.run'

function Get-ListenerPid {
    param([int]$Port)

    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        return [int]$conn.OwningProcess
    } catch {
        return $null
    }
}

function Get-ProcessSafe {
    param([int]$ProcessId)

    try {
        return Get-Process -Id $ProcessId -ErrorAction Stop
    } catch {
        return $null
    }
}

function Stop-ByPort {
    param(
        [string]$Name,
        [int]$Port,
        [switch]$ForceStop
    )

    $ownerPid = Get-ListenerPid -Port $Port
    if ($null -eq $ownerPid) {
        Write-Host "[$Name] No listener found on port $Port." -ForegroundColor Yellow
        return
    }

    $proc = Get-ProcessSafe -ProcessId $ownerPid
    if ($null -eq $proc) {
        Write-Host "[$Name] Port $Port was owned by PID $ownerPid, but process no longer exists." -ForegroundColor Yellow
        return
    }

    $allowed = @('python', 'node', 'cmd', 'powershell', 'pwsh')
    $safe = $allowed -contains $proc.ProcessName.ToLowerInvariant()

    if (-not $safe -and -not $ForceStop) {
        Write-Host "[$Name] Port $Port is owned by '$($proc.ProcessName)' (PID $ownerPid). Skipping. Use -Force to stop anyway." -ForegroundColor Red
        return
    }

    try {
        if ($ForceStop) {
            Stop-Process -Id $ownerPid -Force -ErrorAction Stop
        } else {
            Stop-Process -Id $ownerPid -ErrorAction Stop
        }
        Write-Host "[$Name] Stopped PID $ownerPid ($($proc.ProcessName)) on port $Port." -ForegroundColor Green
    } catch {
        Write-Host "[$Name] Failed to stop PID $ownerPid on port ${Port}: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Test-PortClosed {
    param([int]$Port, [int]$TimeoutSeconds = 8)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if ($null -eq (Get-ListenerPid -Port $Port)) {
            return $true
        }
        Start-Sleep -Milliseconds 300
    }
    return $false
}

Write-Host '=== CrowdGuard Stopper ===' -ForegroundColor Magenta
Write-Host "Project root: $ProjectRoot"

Stop-ByPort -Name 'backend' -Port $BackendPort -ForceStop:$Force
Stop-ByPort -Name 'frontend' -Port $FrontendPort -ForceStop:$Force

$backendClosed = Test-PortClosed -Port $BackendPort
$frontendClosed = Test-PortClosed -Port $FrontendPort

Write-Host ''
if ($backendClosed -and $frontendClosed) {
    Write-Host 'All target service ports are closed.' -ForegroundColor Green
} else {
    if (-not $backendClosed) { Write-Host "Backend port $BackendPort is still open." -ForegroundColor Yellow }
    if (-not $frontendClosed) { Write-Host "Frontend port $FrontendPort is still open." -ForegroundColor Yellow }
}

if ($CleanLogs -and (Test-Path $RunDir)) {
    try {
        Get-ChildItem $RunDir -File -ErrorAction Stop | Remove-Item -Force
        Write-Host "Cleaned log files in $RunDir" -ForegroundColor Green
    } catch {
        Write-Host "Could not clean logs in ${RunDir}: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}



