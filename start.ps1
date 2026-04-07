param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$ForceInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSCommandPath
$BackendDir = Join-Path $ProjectRoot 'backend'
$FrontendDir = Join-Path $ProjectRoot 'frontend'
$RunDir = Join-Path $ProjectRoot '.run'
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Test-CommandExists {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-FileHashSafe {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return '' }
    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash
}

function Get-CompositeHash {
    param([string[]]$Paths)
    $joined = ($Paths | ForEach-Object { Get-FileHashSafe $_ }) -join '|'
    if ([string]::IsNullOrWhiteSpace($joined)) { return '' }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($joined)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { $hash = $sha.ComputeHash($bytes) } finally { $sha.Dispose() }
    return ([System.BitConverter]::ToString($hash)).Replace('-', '')
}

function Read-Stamp {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return '' }
    return (Get-Content -Raw -Path $Path).Trim()
}

function Write-Stamp {
    param([string]$Path, [string]$Value)
    Set-Content -Path $Path -Value $Value -Encoding ascii
}

function Get-ConnectionOnPort {
    param([int]$Port)
    try {
        return Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
    } catch {
        return $null
    }
}

function Wait-PortOpen {
    param([int]$Port, [int]$TimeoutSeconds = 20)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if ($null -ne (Get-ConnectionOnPort -Port $Port)) { return $true }
        Start-Sleep -Milliseconds 400
    }
    return $false
}

function Invoke-WithLocalTemp {
    param([string]$TempRoot, [scriptblock]$ScriptBlock)
    New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null
    $oldTmp = $env:TMP
    $oldTemp = $env:TEMP
    $env:TMP = $TempRoot
    $env:TEMP = $TempRoot
    try { & $ScriptBlock } finally { $env:TMP = $oldTmp; $env:TEMP = $oldTemp }
}

function Test-VenvHealthy {
    param([string]$VenvPython)
    if (-not (Test-Path $VenvPython)) { return $false }
    try {
        & $VenvPython -m pip --version 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Test-BackendDepsInstalled {
    param([string]$VenvPython)
    try {
        & $VenvPython -c "import fastapi, uvicorn, pydantic" 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Ensure-BackendReady {
    if (-not (Test-Path $BackendDir)) { throw "Missing backend directory: $BackendDir" }
    if (-not (Test-CommandExists 'python')) { throw 'Python was not found on PATH. Install Python 3.11+ and retry.' }

    $reqFile = Join-Path $BackendDir 'requirements.txt'
    $venvDir = Join-Path $BackendDir '.venv'
    $venvPython = Join-Path $venvDir 'Scripts\python.exe'
    $stampPath = Join-Path $BackendDir '.requirements.hash'
    $localTemp = Join-Path $BackendDir '.tmp'

    if (-not (Test-Path $reqFile)) { throw "Missing backend requirements file: $reqFile" }

    $targetHash = Get-CompositeHash @($reqFile)
    $savedHash = Read-Stamp $stampPath
    $venvRebuilt = $false

    if ((Test-Path $venvDir) -and -not (Test-VenvHealthy -VenvPython $venvPython)) {
        Write-Host '[backend] Existing .venv is broken, recreating it...' -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvDir
        $venvRebuilt = $true
    }

    if (-not (Test-Path $venvPython)) {
        Write-Host '[backend] Creating virtual environment (.venv)...' -ForegroundColor Cyan
        Push-Location $BackendDir
        try { Invoke-WithLocalTemp -TempRoot $localTemp -ScriptBlock { python -m venv .venv } }
        finally { Pop-Location }
        $venvRebuilt = $true

        if (-not (Test-VenvHealthy -VenvPython $venvPython)) {
            Write-Host '[backend] Bootstrapping pip with ensurepip...' -ForegroundColor Cyan
            Invoke-WithLocalTemp -TempRoot $localTemp -ScriptBlock { & $venvPython -m ensurepip --upgrade }
        }
    }

    if (-not (Test-VenvHealthy -VenvPython $venvPython)) {
        throw '[backend] Virtual environment is not healthy (pip unavailable) after repair attempts.'
    }

    $needsInstall = $ForceInstall -or $venvRebuilt -or ($targetHash -ne $savedHash)
    if (-not $needsInstall -and -not (Test-BackendDepsInstalled -VenvPython $venvPython)) {
        Write-Host '[backend] Required modules missing, reinstalling dependencies...' -ForegroundColor Yellow
        $needsInstall = $true
    }

    if ($needsInstall) {
        Write-Host '[backend] Installing/updating Python dependencies...' -ForegroundColor Cyan
        Invoke-WithLocalTemp -TempRoot $localTemp -ScriptBlock { & $venvPython -m pip install --upgrade pip }
        Invoke-WithLocalTemp -TempRoot $localTemp -ScriptBlock { & $venvPython -m pip install -r $reqFile }
        Write-Stamp $stampPath $targetHash
    } else {
        Write-Host '[backend] Dependencies unchanged, skipping install.' -ForegroundColor Green
    }

    return $venvPython
}

function Ensure-FrontendReady {
    if (-not (Test-Path $FrontendDir)) { throw "Missing frontend directory: $FrontendDir" }
    if (-not (Test-CommandExists 'npm')) { throw 'npm was not found on PATH. Install Node.js and retry.' }

    $packageJson = Join-Path $FrontendDir 'package.json'
    $packageLock = Join-Path $FrontendDir 'package-lock.json'
    $nodeModules = Join-Path $FrontendDir 'node_modules'
    $stampPath = Join-Path $FrontendDir '.npm-deps.hash'

    if (-not (Test-Path $packageJson)) { throw "Missing frontend package.json: $packageJson" }

    $targetHash = Get-CompositeHash @($packageJson, $packageLock)
    $savedHash = Read-Stamp $stampPath
    $needsInstall = $ForceInstall -or -not (Test-Path $nodeModules) -or ($targetHash -ne $savedHash)

    if ($needsInstall) {
        Write-Host '[frontend] Installing/updating npm dependencies...' -ForegroundColor Cyan
        Push-Location $FrontendDir
        try { & npm install } finally { Pop-Location }
        $targetHash = Get-CompositeHash @($packageJson, $packageLock)
        Write-Stamp $stampPath $targetHash
    } else {
        Write-Host '[frontend] Dependencies unchanged, skipping install.' -ForegroundColor Green
    }
}

function Start-Backend {
    param([string]$VenvPython, [int]$Port)

    if ($null -ne (Get-ConnectionOnPort -Port $Port)) {
        Write-Host "[backend] Port $Port already in use. Assuming backend is already running." -ForegroundColor Yellow
        return
    }

    $outLog = Join-Path $RunDir 'backend.out.log'
    $errLog = Join-Path $RunDir 'backend.err.log'
    Remove-Item $outLog,$errLog -ErrorAction SilentlyContinue

    $cmdLine = "cd /d `"$BackendDir`" && `"$VenvPython`" -m uvicorn app.main:app --host 127.0.0.1 --port $Port 1>> `"$outLog`" 2>> `"$errLog`""
    $p = Start-Process -FilePath cmd.exe -ArgumentList @('/c', $cmdLine) -PassThru -WindowStyle Hidden

    if (-not (Wait-PortOpen -Port $Port -TimeoutSeconds 25)) {
        if (-not $p.HasExited) { $p | Stop-Process -Force }
        Write-Host '[backend] Failed to start. Error log:' -ForegroundColor Red
        if (Test-Path $errLog) { Get-Content $errLog | Select-Object -Last 80 }
        throw "Backend failed to bind port $Port"
    }

    Write-Host "[backend] Running on port $Port (PID $($p.Id))." -ForegroundColor Green
}

function Start-Frontend {
    param([int]$Port)

    if ($null -ne (Get-ConnectionOnPort -Port $Port)) {
        Write-Host "[frontend] Port $Port already in use. Assuming frontend is already running." -ForegroundColor Yellow
        return
    }

    $outLog = Join-Path $RunDir 'frontend.out.log'
    $errLog = Join-Path $RunDir 'frontend.err.log'
    Remove-Item $outLog,$errLog -ErrorAction SilentlyContinue

    $cmdLine = "cd /d `"$FrontendDir`" && npm run dev -- --host 127.0.0.1 --port $Port 1>> `"$outLog`" 2>> `"$errLog`""
    $p = Start-Process -FilePath cmd.exe -ArgumentList @('/c', $cmdLine) -PassThru -WindowStyle Hidden

    if (-not (Wait-PortOpen -Port $Port -TimeoutSeconds 30)) {
        if (-not $p.HasExited) { $p | Stop-Process -Force }
        Write-Host '[frontend] Failed to start. Error log:' -ForegroundColor Red
        if (Test-Path $errLog) { Get-Content $errLog | Select-Object -Last 120 }
        throw "Frontend failed to bind port $Port"
    }

    Write-Host "[frontend] Running on port $Port (PID $($p.Id))." -ForegroundColor Green
}

Write-Host '=== CrowdGuard Launcher ===' -ForegroundColor Magenta
Write-Host "Project root: $ProjectRoot"

$venvPythonPath = Ensure-BackendReady
Ensure-FrontendReady
Start-Backend -VenvPython $venvPythonPath -Port $BackendPort
Start-Frontend -Port $FrontendPort

Write-Host ''
Write-Host 'CrowdGuard launch sequence completed.' -ForegroundColor Magenta
Write-Host "Backend URL:  http://127.0.0.1:$BackendPort"
Write-Host "Frontend URL: http://127.0.0.1:$FrontendPort"
Write-Host "API docs:     http://127.0.0.1:$BackendPort/docs"
Write-Host "Logs:         $RunDir"
